"""Geometry clustering for spatial nodes."""
import math
from typing import List, Dict, Any, Tuple
from app.services.spatial_reasoning.graph import (
    SpatialNode, SpatialBounds, SpatialNodeType
)


class GeometryClusterer:
    """Clusters geometry into spatial nodes."""

    def cluster_from_polygons(
        self, 
        polygons: List[Dict[str, Any]], 
        layer: str = None
    ) -> List[SpatialNode]:
        """
        Cluster polygon geometry into spatial nodes.
        
        Args:
            polygons: List of dicts with 'bounds', 'area_m2', 'points'
            layer: Source layer name
            
        Returns:
            List of SpatialNode objects
        """
        nodes = []
        
        for i, poly in enumerate(polygons):
            bounds_data = poly.get("bounds", {})
            bounds = SpatialBounds(
                min_x=bounds_data.get("min_x", 0),
                min_y=bounds_data.get("min_y", 0),
                max_x=bounds_data.get("max_x", 0),
                max_y=bounds_data.get("max_y", 0),
            )
            
            node = SpatialNode(
                uid=f"SPATIAL-{i:04d}",
                node_type=SpatialNodeType.SPACE,
                geometry_ref=poly.get("id", f"poly-{i}"),
                centroid=(
                    bounds.min_x + (bounds.max_x - bounds.min_x) / 2,
                    bounds.min_y + (bounds.max_y - bounds.min_y) / 2
                ),
                bounds=bounds,
                area_m2=poly.get("area_m2", 0),
                confidence=0.90,
                source_layer=layer,
                properties={
                    "type": poly.get("type", "polygon"),
                    "layer": layer,
                    "point_count": len(poly.get("points", []))
                }
            )
            nodes.append(node)
            
        return nodes

    def calculate_perimeter(self, bounds: SpatialBounds) -> float:
        """Calculate perimeter of bounding box."""
        w = bounds.max_x - bounds.min_x
        h = bounds.max_y - bounds.min_y
        return 2 * (w + h)

    def merge_overlapping(
        self, 
        nodes: List[SpatialNode], 
        threshold_m2: float = 1.0
    ) -> List[SpatialNode]:
        """Merge nodes that overlap significantly."""
        merged = []
        
        for node in nodes:
            found = False
            for existing in merged:
                if self._significant_overlap(node.bounds, existing.bounds, threshold_m2):
                    existing.area_m2 += node.area_m2
                    self._expand_bounds(existing.bounds, node.bounds)
                    found = True
                    break
            if not found:
                merged.append(node)
                
        return merged

    def _significant_overlap(
        self, 
        b1: SpatialBounds, 
        b2: SpatialBounds, 
        threshold: float
    ) -> bool:
        """Check if bounds overlap significantly."""
        x_overlap = max(0, min(b1.max_x, b2.max_x) - max(b1.min_x, b2.min_x))
        y_overlap = max(0, min(b1.max_y, b2.max_y) - max(b1.min_y, b2.min_y))
        overlap_area = x_overlap * y_overlap
        return overlap_area > threshold

    def _expand_bounds(self, target: SpatialBounds, source: SpatialBounds) -> None:
        """Expand target bounds to include source."""
        target.min_x = min(target.min_x, source.min_x)
        target.min_y = min(target.min_y, source.min_y)
        target.max_x = max(target.max_x, source.max_x)
        target.max_y = max(target.max_y, source.max_y)