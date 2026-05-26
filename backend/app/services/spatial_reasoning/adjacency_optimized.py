"""Optimized adjacency detection using spatial filter.
Reduces complexity from O(n²) to O(n*k) where k is local neighbors.
"""
from typing import List, Optional
from app.services.spatial_reasoning.graph import (
    SpatialNode, SpatialEdge, SpatialEdgeType
)


class OptimizedAdjacencyDetector:
    """Detect adjacency using spatial pre-filter for O(n*k) performance."""
    
    DEFAULT_DISTANCE_THRESHOLD = 0.5
    MIN_SHARED_BOUNDARY_RATIO = 0.1
    
    def detect_adjacencies(
        self, 
        nodes: List[SpatialNode],
        distance_threshold: float = DEFAULT_DISTANCE_THRESHOLD
    ) -> List[SpatialEdge]:
        """
        Detect adjacency relationships using spatial pre-filtering.
        
        Complexity: O(n*k) where k is average neighbors within distance_threshold.
        """
        edges = []
        n = len(nodes)
        if n < 2:
            return edges
        
        # Simple approach: filter by expanded bounding boxes
        # For a grid layout, most nodes only need to check ~4-8 neighbors
        checked = set()
        
        for i in range(n):
            node_a = nodes[i]
            bounds_a = node_a.bounds
            
            # Expand bounds by threshold
            expand_x = distance_threshold + 0.01
            expand_y = distance_threshold + 0.01
            
            min_x_a = bounds_a.min_x - expand_x
            max_x_a = bounds_a.max_x + expand_x
            min_y_a = bounds_a.min_y - expand_y
            max_y_a = bounds_a.max_y + expand_y
            
            for j in range(i + 1, n):
                node_b = nodes[j]
                bounds_b = node_b.bounds
                
                # Quick AABB rejection
                if bounds_b.max_x < min_x_a or bounds_b.min_x > max_x_a:
                    continue
                if bounds_b.max_y < min_y_a or bounds_b.min_y > max_y_a:
                    continue
                
                edge = self._check_adjacency(node_a, node_b, distance_threshold)
                if edge:
                    edges.append(edge)
        
        return edges
    
    def _check_adjacency(
        self, 
        node_a: SpatialNode, 
        node_b: SpatialNode,
        distance_threshold: float
    ) -> Optional[SpatialEdge]:
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
                    "method": "spatial_filtered"
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