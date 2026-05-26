"""Adjacency detection for spatial relationships."""
from typing import List, Tuple
from app.services.spatial_reasoning.graph import (
    SpatialNode, SpatialEdge, SpatialEdgeType
)


class AdjacencyDetector:
    """Detect adjacency relationships between spatial nodes."""

    DEFAULT_DISTANCE_THRESHOLD = 0.5  # meters at scale
    MIN_SHARED_BOUNDARY_RATIO = 0.1   # 10% of smaller perimeter

    def detect_adjacencies(
        self, 
        nodes: List[SpatialNode],
        distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD
    ) -> List[SpatialEdge]:
        """
        Detect adjacency relationships between all node pairs.
        
        Args:
            nodes: List of spatial nodes
            distance_threshold: Maximum distance for adjacency (in model units)
            
        Returns:
            List of SpatialEdge objects representing adjacencies
        """
        edges = []
        
        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                edge = self._check_adjacency(node_a, node_b, distance_threshold)
                if edge:
                    edges.append(edge)
                    
        return edges

    def _check_adjacency(
        self, 
        node_a: SpatialNode, 
        node_b: SpatialNode,
        distance_threshold: float
    ) -> SpatialEdge:
        """Check if two nodes are adjacent and return edge if so."""
        
        boundary_dist = node_a.bounds.boundary_distance(node_b.bounds)
        
        if boundary_dist > distance_threshold:
            return None
            
        shared = node_a.bounds.shared_boundary_length(node_b.bounds)
        perimeter_a = self._perimeter(node_a.bounds)
        perimeter_b = self._perimeter(node_b.bounds)
        min_perimeter = min(perimeter_a, perimeter_b)
        
        if min_perimeter == 0:
            return None
            
        boundary_ratio = shared / min_perimeter
        
        if boundary_ratio >= self.MIN_SHARED_BOUNDARY_RATIO:
            confidence = self._calculate_confidence(
                boundary_dist, boundary_ratio, shared
            )
            
            return SpatialEdge(
                source_uid=node_a.uid,
                target_uid=node_b.uid,
                edge_type=SpatialEdgeType.ADJACENT_TO,
                confidence=confidence,
                evidence={
                    "boundary_distance": boundary_dist,
                    "shared_boundary": shared,
                    "boundary_ratio": boundary_ratio,
                    "method": "boundary_intersection"
                }
            )
            
        return None

    def _perimeter(self, bounds) -> float:
        """Calculate perimeter of bounds."""
        w = bounds.max_x - bounds.min_x
        h = bounds.max_y - bounds.min_y
        return 2 * (w + h)

    def _calculate_confidence(
        self, 
        distance: float, 
        boundary_ratio: float, 
        shared_length: float
    ) -> float:
        """Calculate confidence based on geometric evidence."""
        distance_factor = max(0, 1 - distance / self.DEFAULT_DISTANCE_THRESHOLD)
        ratio_factor = min(1.0, boundary_ratio / self.MIN_SHARED_BOUNDARY_RATIO)
        
        confidence = (distance_factor * 0.3 + ratio_factor * 0.7)
        return round(min(1.0, max(0.5, confidence)), 2)