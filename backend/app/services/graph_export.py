"""
Graph persistence and export utilities.
Serialize and export the technical knowledge graph.
"""
import json
import csv
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from app.schemas.technical_entity import TechnicalEntity, ExtractionResult
from app.services.entity_registry import EntityRegistry, Relationship, RelationshipEngine


class GraphExporter:
    """Export graph data in various formats."""

    def __init__(self, registry: EntityRegistry, engine: RelationshipEngine):
        self.registry = registry
        self.engine = engine

    def to_json(self, output_path: str) -> str:
        """Export graph as JSON."""
        data = {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "entity_count": len(self.registry.entities),
                "relationship_count": len(self.registry.relationships)
            },
            "entities": [self._entity_to_dict(e) for e in self.registry.entities.values()],
            "relationships": [self._relationship_to_dict(r) for r in self.registry.relationships]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        return output_path

    def to_csv_entities(self, output_path: str) -> str:
        """Export entities as CSV."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'type', 'measure', 'source_file', 'confidence', 'properties'])
            for entity in self.registry.entities.values():
                writer.writerow([
                    entity.id,
                    entity.type.value,
                    entity.measure.value,
                    entity.provenance.source_file,
                    entity.confidence,
                    json.dumps(entity.properties)
                ])
        return output_path

    def to_csv_relationships(self, output_path: str) -> str:
        """Export relationships as CSV."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'source_id', 'target_id', 'type', 'confidence'])
            for rel in self.registry.relationships:
                writer.writerow([
                    rel.id,
                    rel.source_entity_id,
                    rel.target_entity_id,
                    rel.type.value,
                    rel.confidence
                ])
        return output_path

    def to_parquet(self, output_dir: str) -> Dict[str, str]:
        """Export as Parquet files (requires pyarrow)."""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq

            # Entities table
            entities_data = [self._entity_to_dict(e) for e in self.registry.entities.values()]
            if entities_data:
                table = pa.Table.from_pylist(entities_data)
                pq.write_table(table, f"{output_dir}/entities.parquet")

            # Relationships table
            rels_data = [self._relationship_to_dict(r) for r in self.registry.relationships]
            if rels_data:
                table = pa.Table.from_pylist(rels_data)
                pq.write_table(table, f"{output_dir}/relationships.parquet")

            return {
                "entities": f"{output_dir}/entities.parquet",
                "relationships": f"{output_dir}/relationships.parquet"
            }
        except ImportError:
            raise ImportError("pyarrow required for parquet export")

    def _entity_to_dict(self, entity: TechnicalEntity) -> Dict[str, Any]:
        return {
            "id": entity.id,
            "type": entity.type.value,
            "measure": entity.measure.value,
            "discipline": entity.discipline.value,
            "source_file": entity.provenance.source_file,
            "source_layer": entity.provenance.source_layer,
            "parser_used": entity.provenance.parser_used,
            "extraction_method": entity.provenance.extraction_method,
            "extracted_at": entity.provenance.extracted_at,
            "confidence": entity.confidence,
            "properties": entity.properties,
            "coordinates": entity.coordinates
        }

    def _relationship_to_dict(self, rel: Relationship) -> Dict[str, Any]:
        return {
            "id": rel.id,
            "source_id": rel.source_entity_id,
            "target_id": rel.target_entity_id,
            "type": rel.type.value,
            "source_file": rel.source_file,
            "confidence": rel.confidence,
            "properties": rel.properties
        }


class ProjectKnowledgeFingerprint:
    """Generate signature fingerprints for projects."""

    def __init__(self, registry: EntityRegistry):
        self.registry = registry

    def generate(self) -> Dict[str, Any]:
        """Generate project signature."""
        luminaries = self.registry.get_by_type("luminaire") if hasattr(self.registry, 'get_by_type') else []
        panels = self.registry.get_by_type("panel") if hasattr(self.registry, 'get_by_type') else []

        total_watts = sum(e.properties.get("watts", 0) for e in luminaries)
        total_lumens = sum(e.properties.get("lumens", 0) for e in luminaries)
        efficacy = total_lumens / total_watts if total_watts > 0 else 0

        return {
            "lighting_density_avg": self._calc_avg_density(luminaries),
            "hvac_efficiency": self._calc_hvac_efficiency(),
            "water_savings": self._calc_water_savings(),
            "panel_load_distribution": self._calc_panel_distribution(panels),
            "total_entities": len(self.registry.entities),
            "total_relationships": len(self.registry.relationships)
        }

    def _calc_avg_density(self, luminaries: List) -> float:
        if not luminaries:
            return 0.0
        densities = [l.properties.get("lumens", 0) / max(l.properties.get("watts", 1), 1) for l in luminaries]
        return sum(densities) / len(densities) if densities else 0.0

    def _calc_hvac_efficiency(self) -> float:
        hvac = self.registry.get_by_type("hvac_unit") if hasattr(self.registry, 'get_by_type') else []
        cop_values = [h.properties.get("cop", 0) for h in hvac if h.properties.get("cop")]
        return sum(cop_values) / len(cop_values) if cop_values else 0.0

    def _calc_water_savings(self) -> float:
        fixtures = self.registry.get_by_type("fixture") if hasattr(self.registry, 'get_by_type') else []
        savings = [f.properties.get("saving_percent", 0) for f in fixtures if f.properties.get("saving_percent")]
        return sum(savings) / len(savings) if savings else 0.0

    def _calc_panel_distribution(self, panels: List) -> Dict[str, Any]:
        if not panels:
            return {}
        loads = [p.properties.get("total_load", 0) for p in panels]
        return {
            "count": len(panels),
            "total_kw": sum(loads),
            "avg_kw": sum(loads) / len(loads) if loads else 0
        }