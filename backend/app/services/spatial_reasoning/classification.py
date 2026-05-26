"""Space type classification based on geometric properties."""
from typing import Dict, Any
from app.services.spatial_reasoning.graph import SpatialNode, SpatialNodeType


class SpaceClassifier:
    """Classify spatial nodes into architectural space types."""

    SHAPE_RATIO_THRESHOLDS = {
        "corridor_ratio": 5.0,  # length/width ratio for corridors
        "office_min_area": 8.0,
        "office_max_area": 200.0,
    }

    KEYWORD_MAP = {
        "wc": SpatialNodeType.SERVICE_AREA,
        "bathroom": SpatialNodeType.SERVICE_AREA,
        "restroom": SpatialNodeType.SERVICE_AREA,
        "mechanical": SpatialNodeType.SERVICE_AREA,
        "hvac": SpatialNodeType.SERVICE_AREA,
        "electrical": SpatialNodeType.SERVICE_AREA,
        "storage": SpatialNodeType.SERVICE_AREA,
        "corridor": SpatialNodeType.CORRIDOR,
        "circulation": SpatialNodeType.CORRIDOR,
    }

    def classify(self, node: SpatialNode) -> SpatialNode:
        """
        Classify a spatial node based on area, shape, and properties.
        
        Args:
            node: SpatialNode to classify
            
        Returns:
            Node with updated node_type
        """
        layer = node.source_layer or ""
        layer_lower = layer.lower()
        
        for keyword, node_type in self.KEYWORD_MAP.items():
            if keyword in layer_lower:
                node.node_type = node_type
                return node

        area = node.area_m2
        shape_ratio = self._calculate_shape_ratio(node)
        
        if area < 1.0:
            node.node_type = SpatialNodeType.SPACE
        elif area < 4.0 and shape_ratio > self.SHAPE_RATIO_THRESHOLDS["corridor_ratio"]:
            node.node_type = SpatialNodeType.CORRIDOR
        elif self.SHAPE_RATIO_THRESHOLDS["office_min_area"] <= area <= self.SHAPE_RATIO_THRESHOLDS["office_max_area"]:
            node.node_type = SpatialNodeType.SPACE
        else:
            node.node_type = SpatialNodeType.ZONE

        node.properties["classified_by"] = "geometry_heuristic"
        node.properties["shape_ratio"] = shape_ratio
        
        return node

    def _calculate_shape_ratio(self, node: SpatialNode) -> float:
        """Calculate length/width ratio to detect elongated shapes."""
        bounds = node.bounds
        width = bounds.max_x - bounds.min_x
        height = bounds.max_y - bounds.min_y
        
        if width == 0 or height == 0:
            return 1.0
            
        return max(width, height) / min(width, height)