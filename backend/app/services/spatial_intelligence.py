"""
Spatial Intelligence Layer for technical entity reasoning.
Provides containment, proximity, and geometric queries.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

try:
    import rtree
    import shapely.geometry as geom
    import shapely.ops as ops
    SPATIAL_AVAILABLE = True
except ImportError:
    SPATIAL_AVAILABLE = False

from app.schemas.technical_entity import TechnicalEntity

logger = logging.getLogger(__name__)


@dataclass
class SpatialQuery:
    """Result of spatial query."""
    entity_id: str
    distance: Optional[float] = None
    contained_in: Optional[str] = None
    intersects: List[str] = None
    
    def __post_init__(self):
        if self.intersects is None:
            self.intersects = []


class SpatialIndex:
    """R-tree spatial index for technical entities."""
    
    def __init__(self):
        if not SPATIAL_AVAILABLE:
            logger.warning("Spatial libraries not available - spatial queries disabled")
            self.enabled = False
            return
        
        self.enabled = True
        self.index = rtree.index.Index()
        self.entities: Dict[str, TechnicalEntity] = {}
        self.bboxes: Dict[str, Tuple[float, float, float, float]] = {}
    
    def insert(self, entity: TechnicalEntity):
        """Insert entity into spatial index."""
        if not self.enabled:
            return
        
        bbox = self._get_bbox(entity)
        if bbox:
            minx, miny, maxx, maxy = bbox
            self.index.insert(entity.id, (minx, miny, maxx, maxy))
            self.entities[entity.id] = entity
            self.bboxes[entity.id] = bbox
    
    def _get_bbox(self, entity: TechnicalEntity) -> Optional[Tuple[float, float, float, float]]:
        """Extract bounding box from entity coordinates."""
        coords = entity.coordinates or {}
        source_coords = entity.source_coordinates or {}
        
        # Try various coordinate formats
        if "bbox" in coords:
            bbox = coords["bbox"]
            return (bbox["min_x"], bbox["min_y"], bbox["max_x"], bbox["max_y"])
        
        if "insert" in source_coords:
            pt = source_coords["insert"]
            return (pt[0], pt[1], pt[0] + 1, pt[1] + 1)  # Point bbox
        
        if "origin" in coords:
            x, y = coords["origin"]
            return (x, y, x + 1, y + 1)
        
        return None
    
    def contains(self, container_id: str, entity_id: str) -> bool:
        """Check if container contains entity."""
        if not self.enabled:
            return False
        
        if container_id not in self.bboxes or entity_id not in self.bboxes:
            return False
        
        container_bbox = self.bboxes[container_id]
        entity_bbox = self.bboxes[entity_id]
        
        c_minx, c_miny, c_maxx, c_maxy = container_bbox
        e_minx, e_miny, e_maxx, e_maxy = entity_bbox
        
        return c_minx <= e_minx and c_miny <= e_miny and c_maxx >= e_maxx and c_maxy >= e_maxy
    
    def find_entities_in_polygon(self, polygon_coords: List[Tuple[float, float]]) -> List[str]:
        """Find all entities inside a polygon."""
        if not self.enabled:
            return []
        
        poly = geom.Polygon(polygon_coords)
        hits = []
        
        for entity_id, bbox in self.bboxes.items():
            minx, miny, maxx, maxy = bbox
            rect = geom.box(minx, miny, maxx, maxy)
            if poly.contains(rect):
                hits.append(entity_id)
        
        return hits
    
    def analyze_containment(self, entities: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Analyze containment relationships between areas and entities."""
        results = []
        
        areas = {e["id"]: e for e in entities if e.get("type") == "area"}
        others = [e for e in entities if e.get("type") != "area" and "coordinates" in e]
        
        for area_id, area in areas.items():
            area_coords = area.get("coordinates", {})
            area_bbox = area_coords.get("bbox") or area_coords.get("bounds")
            
            if not area_bbox or len(area_bbox) < 4:
                continue
            
            min_x, min_y, max_x, max_y = area_bbox[0], area_bbox[1], area_bbox[2], area_bbox[3]
            
            for entity in others:
                entity_coords = entity.get("coordinates", {})
                entity_bbox = entity_coords.get("bbox") or entity_coords.get("bounds")
                
                if not entity_bbox or len(entity_bbox) < 4:
                    continue
                
                e_min_x, e_min_y, e_max_x, e_max_y = entity_bbox[0], entity_bbox[1], entity_bbox[2], entity_bbox[3]
                
                if min_x <= e_min_x and min_y <= e_min_y and max_x >= e_max_x and max_y >= e_max_y:
                    results.append({
                        "area_id": area_id,
                        "entity_id": entity["id"],
                        "relationship": "contains"
                    })
        
        return results
    
    def infer_luminaire_area_coverage(self, entities: List[Dict[str, Any]], 
                                      tolerance: float = 2.0) -> List[Dict[str, Any]]:
        """Infer which areas are illuminated by which luminaires based on proximity."""
        luminaires = [e for e in entities if e.get("type") == "luminaire"]
        areas = [e for e in entities if e.get("type") == "area"]
        inferred = []
        
        for lum in luminaires:
            lum_coords = lum.get("coordinates", {})
            lum_bbox = lum_coords.get("bbox") or lum_coords.get("bounds")
            
            if not lum_bbox:
                points = lum_coords.get("points", [])
                if points:
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    lum_bbox = [min(xs), min(ys), max(xs), max(ys)]
            
            if not lum_bbox:
                continue
            
            lum_center = ((lum_bbox[0] + lum_bbox[2]) / 2, (lum_bbox[1] + lum_bbox[3]) / 2)
            
            for area in areas:
                area_coords = area.get("coordinates", {})
                area_bbox = area_coords.get("bbox") or area_coords.get("bounds")
                
                if not area_bbox:
                    continue
                
                distance = self._distance_to_bbox(lum_center, area_bbox)
                
                if distance <= tolerance or self._point_in_bbox(lum_center, area_bbox):
                    inferred.append({
                        "source": lum["id"],
                        "target": area["id"],
                        "relationship": "illuminates",
                        "confidence": max(0.5, 1.0 - distance / 10.0)
                    })
        
        return inferred
    
    def infer_panel_circuit_mapping(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Infer panel-to-circuit relationships based on naming conventions and proximity."""
        panels = [e for e in entities if e.get("type") == "panel"]
        circuits = [e for e in entities if e.get("type") == "circuit"]
        inferred = []
        
        for panel in panels:
            panel_props = panel.get("properties", {})
            panel_name = panel_props.get("panel_name", "")
            panel_id = panel["id"]
            
            for circuit in circuits:
                circuit_props = circuit.get("properties", {})
                circuit_name = circuit_props.get("circuit_name", "")
                
                if not circuit_name:
                    continue
                
                if panel_name and circuit_name.lower().startswith(panel_name.lower()):
                    inferred.append({
                        "source": panel_id,
                        "target": circuit["id"],
                        "relationship": "feeds",
                        "confidence": 0.85
                    })
                    continue
                
                panel_coords = panel.get("coordinates", {})
                circuit_coords = circuit.get("coordinates", {})
                panel_bbox = panel_coords.get("bbox") or panel_coords.get("bounds")
                circuit_bbox = circuit_coords.get("bbox") or circuit_coords.get("bounds")
                
                if panel_bbox and circuit_bbox:
                    area_iou = self._bbox_iou(panel_bbox, circuit_bbox)
                    if area_iou > 0.1:
                        inferred.append({
                            "source": panel_id,
                            "target": circuit["id"],
                            "relationship": "feeds",
                            "confidence": 0.7
                        })
        
        return inferred
    
    def infer_hvac_zone_mapping(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Infer which HVAC units serve which zones based on area containment."""
        hvac_units = [e for e in entities if e.get("type") == "hvac_unit"]
        zones = [e for e in entities if e.get("type") == "hvac_zone"]
        areas = [e for e in entities if e.get("type") == "area"]
        inferred = []
        
        for hvac in hvac_units:
            hvac_coords = hvac.get("coordinates", {})
            hvac_bbox = hvac_coords.get("bbox") or hvac_coords.get("bounds")
            
            if not hvac_bbox:
                continue
            
            hvac_center = ((hvac_bbox[0] + hvac_bbox[2]) / 2, (hvac_bbox[1] + hvac_bbox[3]) / 2)
            
            for zone in zones:
                zone_props = zone.get("properties", {})
                zone_area_id = zone_props.get("area_id")
                
                if zone_area_id:
                    zone_area = next((a for a in areas if a["id"] == zone_area_id), None)
                    if zone_area:
                        zone_coords = zone_area.get("coordinates", {})
                        zone_bbox = zone_coords.get("bbox") or zone_coords.get("bounds")
                        
                        if zone_bbox and self._point_in_bbox(hvac_center, zone_bbox):
                            inferred.append({
                                "source": hvac["id"],
                                "target": zone["id"],
                                "relationship": "serves",
                                "confidence": 0.8
                            })
        
        return inferred
    
    def _distance_to_bbox(self, point: tuple, bbox: list) -> float:
        """Calculate distance from point to bounding box."""
        px, py = point
        min_x, min_y, max_x, max_y = bbox
        
        dx = max(min_x - px, 0, px - max_x)
        dy = max(min_y - py, 0, py - max_y)
        
        return (dx ** 2 + dy ** 2) ** 0.5
    
    def _point_in_bbox(self, point: tuple, bbox: list) -> bool:
        """Check if point is inside bounding box."""
        px, py = point
        min_x, min_y, max_x, max_y = bbox
        return min_x <= px <= max_x and min_y <= py <= max_y
    
    def _bbox_iou(self, bbox1: list, bbox2: list) -> float:
        """Calculate IoU between two bounding boxes."""
        min_x1, min_y1, max_x1, max_y1 = bbox1
        min_x2, min_y2, max_x2, max_y2 = bbox2
        
        intersection_min_x = max(min_x1, min_x2)
        intersection_min_y = max(min_y1, min_y2)
        intersection_max_x = min(max_x1, max_x2)
        intersection_max_y = min(max_y1, max_y2)
        
        if intersection_max_x <= intersection_min_x or intersection_max_y <= intersection_min_y:
            return 0.0
        
        intersection_area = (intersection_max_x - intersection_min_x) * (intersection_max_y - intersection_min_y)
        area1 = (max_x1 - min_x1) * (max_y1 - min_y1)
        area2 = (max_x2 - min_x2) * (max_y2 - min_y2)
        
        return intersection_area / (area1 + area2 - intersection_area)
    
    def within_distance(self, entity_id: str, distance: float) -> List[str]:
        """Find entities within given distance."""
        if not self.enabled:
            return []
        
        if entity_id not in self.bboxes:
            return []
        
        minx, miny, maxx, maxy = self.bboxes[entity_id]
        buffer = distance
        
        nearby = []
        for hit_id in self.index.intersection((minx - buffer, miny - buffer, maxx + buffer, maxy + buffer)):
            if hit_id != entity_id:
                nearby.append(hit_id)
        
        return nearby
    
    def query_by_polygon(self, polygon_coords: List[Tuple[float, float]]) -> List[str]:
        """Find entities intersecting with polygon."""
        if not self.enabled:
            return []
        
        poly = geom.Polygon(polygon_coords)
        hits = []
        
        for entity_id, bbox in self.bboxes.items():
            minx, miny, maxx, maxy = bbox
            rect = geom.box(minx, miny, maxx, maxy)
            if poly.intersects(rect):
                hits.append(entity_id)
        
        return hits


class SpatialReasoning:
    """High-level spatial reasoning for technical entities."""
    
    def __init__(self, spatial_index=None):
        self.index = spatial_index
    
    def luminaires_in_area(self, area_id: str) -> List[str]:
        """Find all luminaires contained in an area."""
        from app.schemas.technical_entity import EntityType
        
        results = []
        for ent_id, ent in self.index.entities.items():
            if ent.type == EntityType.LUMINAIRE:
                if self.index.contains(area_id, ent_id):
                    results.append(ent_id)
        
        return results
    
    def circuits_fed_by_panel(self, panel_id: str, circuit_ids: List[str]) -> List[str]:
        """Check which circuits are properly spatially located near panel."""
        if not self.index.enabled:
            return circuit_ids  # Assume all if no spatial data
        
        return circuit_ids  # Spatial validation placeholder
    
    def nearest_entities(self, entity_id: str, entity_type: str, limit: int = 5) -> List[str]:
        """Find nearest entities of given type."""
        from app.schemas.technical_entity import EntityType
        
        try:
            target_type = EntityType(entity_type)
        except ValueError:
            return []
        
        candidates = [
            eid for eid, ent in self.index.entities.items() 
            if ent.type == target_type and eid != entity_id
        ]
        
        return candidates[:limit]
    
    def infer_luminaire_area_coverage(self, entities: List[Dict], 
                                      tolerance: float = 2.0) -> List[Dict[str, Any]]:
        """Infer which areas are illuminated by which luminaires based on proximity."""
        luminaires = [e for e in entities if e.get("type") == "luminaire"]
        areas = [e for e in entities if e.get("type") == "area"]
        inferred = []
        
        for lum in luminaires:
            lum_coords = lum.get("coordinates", {})
            lum_bbox = lum_coords.get("bbox") or lum_coords.get("bounds")
            
            if not lum_bbox:
                points = lum_coords.get("points", [])
                if points:
                    xs = [p[0] for p in points]
                    ys = [p[1] for p in points]
                    lum_bbox = [min(xs), min(ys), max(xs), max(ys)]
            
            if not lum_bbox:
                continue
            
            lum_center = ((lum_bbox[0] + lum_bbox[2]) / 2, (lum_bbox[1] + lum_bbox[3]) / 2)
            
            for area in areas:
                area_coords = area.get("coordinates", {})
                area_bbox = area_coords.get("bbox") or area_coords.get("bounds")
                
                if not area_bbox:
                    continue
                
                distance = self._distance_to_bbox(lum_center, area_bbox)
                
                if distance <= tolerance or self._point_in_bbox(lum_center, area_bbox):
                    inferred.append({
                        "source": lum["id"],
                        "target": area["id"],
                        "relationship": "illuminates",
                        "confidence": max(0.5, 1.0 - distance / 10.0)
                    })
        
        return inferred
    
    def infer_panel_circuit_mapping(self, entities: List[Dict]) -> List[Dict[str, Any]]:
        """Infer panel-to-circuit relationships based on naming conventions and proximity."""
        panels = [e for e in entities if e.get("type") == "panel"]
        circuits = [e for e in entities if e.get("type") == "circuit"]
        inferred = []
        
        for panel in panels:
            panel_props = panel.get("properties", {})
            panel_name = panel_props.get("panel_name", "")
            panel_id = panel["id"]
            
            for circuit in circuits:
                circuit_props = circuit.get("properties", {})
                circuit_name = circuit_props.get("circuit_name", "")
                
                if not circuit_name:
                    continue
                
                if panel_name and circuit_name.lower().startswith(panel_name.lower()):
                    inferred.append({
                        "source": panel_id,
                        "target": circuit["id"],
                        "relationship": "feeds",
                        "confidence": 0.85
                    })
                    continue
                
                panel_coords = panel.get("coordinates", {})
                circuit_coords = circuit.get("coordinates", {})
                panel_bbox = panel_coords.get("bbox") or panel_coords.get("bounds")
                circuit_bbox = circuit_coords.get("bbox") or circuit_coords.get("bounds")
                
                if panel_bbox and circuit_bbox:
                    area_iou = self._bbox_iou(panel_bbox, circuit_bbox)
                    if area_iou > 0.1:
                        inferred.append({
                            "source": panel_id,
                            "target": circuit["id"],
                            "relationship": "feeds",
                            "confidence": 0.7
                        })
        
        return inferred
    
    def infer_hvac_zone_mapping(self, entities: List[Dict]) -> List[Dict[str, Any]]:
        """Infer which HVAC units serve which zones based on area containment."""
        hvac_units = [e for e in entities if e.get("type") == "hvac_unit"]
        zones = [e for e in entities if e.get("type") == "hvac_zone"]
        areas = [e for e in entities if e.get("type") == "area"]
        inferred = []
        
        for hvac in hvac_units:
            hvac_coords = hvac.get("coordinates", {})
            hvac_bbox = hvac_coords.get("bbox") or hvac_coords.get("bounds")
            
            if not hvac_bbox:
                continue
            
            hvac_center = ((hvac_bbox[0] + hvac_bbox[2]) / 2, (hvac_bbox[1] + hvac_bbox[3]) / 2)
            
            for zone in zones:
                zone_props = zone.get("properties", {})
                zone_area_id = zone_props.get("area_id")
                
                if zone_area_id:
                    zone_area = next((a for a in areas if a["id"] == zone_area_id), None)
                    if zone_area:
                        zone_coords = zone_area.get("coordinates", {})
                        zone_bbox = zone_coords.get("bbox") or zone_coords.get("bounds")
                        
                        if zone_bbox and self._point_in_bbox(hvac_center, zone_bbox):
                            inferred.append({
                                "source": hvac["id"],
                                "target": zone["id"],
                                "relationship": "serves",
                                "confidence": 0.8
                            })
        
        return inferred
    
    def _distance_to_bbox(self, point: tuple, bbox: list) -> float:
        """Calculate distance from point to bounding box."""
        px, py = point
        min_x, min_y, max_x, max_y = bbox
        
        dx = max(min_x - px, 0, px - max_x)
        dy = max(min_y - py, 0, py - max_y)
        
        return (dx ** 2 + dy ** 2) ** 0.5
    
    def _point_in_bbox(self, point: tuple, bbox: list) -> bool:
        """Check if point is inside bounding box."""
        px, py = point
        min_x, min_y, max_x, max_y = bbox
        return min_x <= px <= max_x and min_y <= py <= max_y
    
    def _bbox_iou(self, bbox1: list, bbox2: list) -> float:
        """Calculate IoU between two bounding boxes."""
        min_x1, min_y1, max_x1, max_y1 = bbox1
        min_x2, min_y2, max_x2, max_y2 = bbox2
        
        intersection_min_x = max(min_x1, min_x2)
        intersection_min_y = max(min_y1, min_y2)
        intersection_max_x = min(max_x1, max_x2)
        intersection_max_y = min(max_y1, max_y2)
        
        if intersection_max_x <= intersection_min_x or intersection_max_y <= intersection_min_y:
            return 0.0
        
        intersection_area = (intersection_max_x - intersection_min_x) * (intersection_max_y - intersection_min_y)
        area1 = (max_x1 - min_x1) * (max_y1 - min_y1)
        area2 = (max_x2 - min_x2) * (max_y2 - min_y2)
        
        return intersection_area / (area1 + area2 - intersection_area)


# Singleton instance
spatial_index = SpatialIndex()
spatial_reasoning = SpatialReasoning(spatial_index) if SPATIAL_AVAILABLE else None