"""
Entity Registry and Relationship Engine for Technical Graph.
Builds connections between extracted entities for cross-validation.
Uses NetworkX for graph-based relationship queries and pathfinding.
"""
import logging
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

import networkx as nx
from shapely.geometry import Point, Polygon, box as shapely_box
import rtree

from app.schemas.technical_entity import (
    TechnicalEntity, ExtractionResult, EntityType, MeasureType, Discipline,
    Provenance, SpatialBounds, ValidationIssue
)

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    ILLUMINATES = "illuminates"
    FEEDS = "feeds"
    CONNECTED_TO = "connected_to"
    LOCATED_IN = "located_in"
    PART_OF = "part_of"
    CONTROLS = "controls"
    SUPPLIES = "supplies"
    REFERENCES = "references"


class Relationship(BaseModel):
    """Connection between two technical entities."""
    id: str
    type: RelationshipType
    source_entity_id: str
    target_entity_id: str
    source_file: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.95
    validation_status: Optional[str] = None


class SpatialIndex:
    """R-tree spatial index for efficient geometry queries."""

    def __init__(self):
        self.idx = rtree.index.Index()
        self.bounds_map: Dict[int, tuple] = {}

    def insert(self, entity_id: str, bounds: SpatialBounds):
        key = hash(entity_id) % (2**31)
        min_x, min_y, max_x, max_y = bounds.min_x, bounds.min_y, bounds.max_x, bounds.max_y
        self.idx.insert(key, (min_x, min_y, max_x, max_y), obj=entity_id)
        self.bounds_map[key] = (entity_id, bounds)

    def query(self, bounds: SpatialBounds) -> List[str]:
        result = []
        for item in self.idx.intersection((bounds.min_x, bounds.min_y, bounds.max_x, bounds.max_y)):
            if item in self.bounds_map:
                result.append(self.bounds_map[item][0])
        return result


class EntityRegistry:
    """Registry of all extracted entities with relationship indexing."""

    def __init__(self):
        self.entities: Dict[str, TechnicalEntity] = {}
        self.by_type: Dict[EntityType, List[str]] = {}
        self.by_measure: Dict[MeasureType, List[str]] = {}
        self.by_discipline: Dict[Discipline, List[str]] = {}
        self.relationships: List[Relationship] = []
        self.spatial_idx = SpatialIndex()
        self._validation_issues: List[ValidationIssue] = []

    def add(self, entity: TechnicalEntity):
        """Add entity to registry with provenance tracking."""
        self.entities[entity.id] = entity

        if entity.type not in self.by_type:
            self.by_type[entity.type] = []
        self.by_type[entity.type].append(entity.id)

        if entity.measure not in self.by_measure:
            self.by_measure[entity.measure] = []
        self.by_measure[entity.measure].append(entity.id)

        if entity.discipline not in self.by_discipline:
            self.by_discipline[entity.discipline] = []
        self.by_discipline[entity.discipline].append(entity.id)

        coords = entity.coordinates or {}
        bbox = coords.get("bbox") or coords.get("bounds")
        if bbox and len(bbox) >= 4:
            bounds = SpatialBounds(min_x=bbox[0], min_y=bbox[1], max_x=bbox[2], max_y=bbox[3])
            self.spatial_idx.insert(entity.id, bounds)

    def link(self, source_id: str, target_id: str, rel_type: RelationshipType,
             properties: Dict[str, Any] = None, confidence: float = 0.95):
        """Create relationship between entities."""
        rel = Relationship(
            id=f"rel_{len(self.relationships)}_{source_id}_{target_id}",
            type=rel_type,
            source_entity_id=source_id,
            target_entity_id=target_id,
            source_file=self.entities[source_id].provenance.source_file if source_id in self.entities else "unknown",
            properties=properties or {},
            confidence=confidence
        )
        self.relationships.append(rel)
        return rel

    def get_by_type(self, entity_type: EntityType) -> List[TechnicalEntity]:
        return [self.entities[eid] for eid in self.by_type.get(entity_type, [])]

    def get_by_measure(self, measure: MeasureType) -> List[TechnicalEntity]:
        return [self.entities[eid] for eid in self.by_measure.get(measure, [])]

    def get_neighborhood(self, entity_id: str) -> List[Relationship]:
        return [r for r in self.relationships
                if r.source_entity_id == entity_id or r.target_entity_id == entity_id]

    def query_spatial(self, bounds: SpatialBounds) -> List[TechnicalEntity]:
        """Find entities within spatial bounds."""
        ids = self.spatial_idx.query(bounds)
        return [self.entities[eid] for eid in ids if eid in self.entities]

    def find_containment(self, entity_id: str) -> List[tuple]:
        """Find areas that contain an entity."""
        if entity_id not in self.entities:
            return []
        entity = self.entities[entity_id]
        coords = entity.coordinates or {}
        cx, cy = coords.get("centroid_x"), coords.get("centroid_y")
        if not (cx and cy):
            bbox = coords.get("bbox") or coords.get("bounds")
            if bbox:
                cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
            else:
                return []
        areas = self.get_by_type(EntityType.AREA)
        results = []
        for area in areas:
            area_coords = area.coordinates or {}
            area_bbox = area_coords.get("bbox") or area_coords.get("bounds")
            if area_bbox and area_bbox[0] <= cx <= area_bbox[2] and area_bbox[1] <= cy <= area_bbox[3]:
                results.append((area.id, area))
        return results


class RelationshipEngine:
    """Build technical relationships from extracted data using NetworkX graph."""

    def __init__(self, registry: EntityRegistry):
        self.registry = registry
        self.graph = nx.DiGraph()

    def _add_entity_to_graph(self, entity: TechnicalEntity):
        self.graph.add_node(
            entity.id,
            type=entity.type.value,
            measure=entity.measure.value,
            discipline=entity.discipline.value,
            confidence=entity.confidence,
            **entity.properties
        )

    def _add_relationship_to_graph(self, rel: Relationship):
        self.graph.add_edge(
            rel.source_entity_id,
            rel.target_entity_id,
            relationship_id=rel.id,
            type=rel.type.value,
            confidence=rel.confidence,
            **rel.properties
        )

    def infer_luminaire_area_relationships(self, extraction: ExtractionResult):
        luminarias = self.registry.get_by_type(EntityType.LUMINAIRE)
        areas = self.registry.get_by_type(EntityType.AREA)

        for lum in luminarias:
            self._add_entity_to_graph(lum)
            lum_props = lum.properties
            area_ref = lum_props.get("area_reference")

            if area_ref:
                for area in areas:
                    if area.id == area_ref:
                        self._add_entity_to_graph(area)
                        rel = self.registry.link(lum.id, area.id,
                            RelationshipType.ILLUMINATES,
                            properties={"inferred": True, "method": "area_reference"},
                            confidence=0.95)
                        self._add_relationship_to_graph(rel)
                        break

    def infer_panel_circuit_relationships(self, extraction: ExtractionResult):
        panels = self.registry.get_by_type(EntityType.PANEL)
        circuits = self.registry.get_by_type(EntityType.CIRCUIT)

        for panel in panels:
            self._add_entity_to_graph(panel)
            panel_props = panel.properties
            circuit_list = panel_props.get("circuit_ids", [])

            for circuit_id in circuit_list:
                if circuit_id in self.registry.entities:
                    circuit = self.registry.entities[circuit_id]
                    self._add_entity_to_graph(circuit)
                    rel = self.registry.link(panel.id, circuit_id,
                        RelationshipType.FEEDS,
                        properties={"inferred": True, "method": "schedule"},
                        confidence=0.99)
                    self._add_relationship_to_graph(rel)

    def infer_location_relationships(self, extraction: ExtractionResult):
        for entity in self.registry.entities.values():
            self._add_entity_to_graph(entity)
            area_id = entity.properties.get("area_id")
            if area_id and area_id in self.registry.entities:
                rel = self.registry.link(entity.id, area_id,
                    RelationshipType.LOCATED_IN,
                    properties={"inferred": True, "method": "spatial"},
                    confidence=0.90)
                self._add_relationship_to_graph(rel)

    def get_downstream_entities(self, entity_id: str) -> List[str]:
        return list(nx.descendants(self.graph, entity_id))

    def get_upstream_entities(self, entity_id: str) -> List[str]:
        return list(nx.ancestors(self.graph, entity_id))

    def get_connected_component(self, entity_id: str) -> Set[str]:
        undirected = self.graph.to_undirected()
        return set(nx.node_connected_component(undirected, entity_id))

    def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        try:
            return nx.shortest_path(self.graph, source_id, target_id)
        except nx.NetworkXNoPath:
            return None

    def validate_relationship_integrity(self) -> Dict[str, Any]:
        issues = {
            "orphaned_entities": [],
            "missing_references": [],
            "confidence_gaps": []
        }
        for entity_type in [EntityType.LUMINAIRE, EntityType.CIRCUIT, EntityType.PANEL]:
            for entity_id in self.registry.by_type.get(entity_type, []):
                if self.graph.in_degree(entity_id) == 0 and self.graph.out_degree(entity_id) == 0:
                    issues["orphaned_entities"].append(entity_id)
        return issues


class CrossDocumentReconciler:
    """Cross-document validation and reconciliation."""

    def __init__(self, registry: EntityRegistry):
        self.registry = registry

    def reconcile_values(self, entity_type: EntityType, property_key: str,
                         expected_range: tuple = None, tolerance: float = 0.15) -> List[ValidationIssue]:
        """Find inconsistent values across documents for the same entity type."""
        entities = self.registry.get_by_type(entity_type)
        if len(entities) < 2:
            return []

        values_by_source: Dict[str, List[tuple]] = {}
        for e in entities:
            val = e.properties.get(property_key)
            if val is not None:
                src = e.provenance.source_file
                if src not in values_by_source:
                    values_by_source[src] = []
                values_by_source[src].append((e.id, val))

        issues = []
        if len(values_by_source) < 2:
            return issues

        sources = list(values_by_source.keys())
        for i in range(len(sources)):
            for j in range(i + 1, len(sources)):
                src_a, src_b = sources[i], sources[j]
                vals_a = [v[1] for v in values_by_source[src_a]]
                vals_b = [v[1] for v in values_by_source[src_b]]
                avg_a = sum(vals_a) / len(vals_a) if vals_a else 0
                avg_b = sum(vals_b) / len(vals_b) if vals_b else 0

                if avg_a > 0 and abs(avg_a - avg_b) / avg_a > tolerance:
                    issues.append(ValidationIssue(
                        severity="warning",
                        issue_type="value_mismatch",
                        source_files=[src_a, src_b],
                        values={"source_a": avg_a, "source_b": avg_b},
                        confidence=0.92,
                        message=f"Value mismatch for {property_key}: {avg_a} vs {avg_b} ({src_a} vs {src_b})"
                    ))

        return issues

    def reconcile_load_consistency(self, calculated_kw: float, panel_kw: float,
                                   sources: List[str]) -> Optional[ValidationIssue]:
        """Validate load calculation vs panel schedule."""
        if panel_kw <= 0:
            return None
        ratio = calculated_kw / panel_kw
        if not (0.7 <= ratio <= 1.3):
            return ValidationIssue(
                severity="warning",
                issue_type="load_mismatch",
                source_files=sources,
                values={"calculated_kw": calculated_kw, "panel_kw": panel_kw, "ratio": ratio},
                confidence=0.90,
                message=f"Load mismatch: {calculated_kw} kW calculated vs {panel_kw} kW panel (ratio: {ratio:.2f})"
            )
        return None


# Singleton instances
registry = EntityRegistry()
engine = RelationshipEngine(registry)
reconciler = CrossDocumentReconciler(registry)