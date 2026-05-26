"""Boundary semantics inference (geometry-only, no architectural semantics)."""
import math
from typing import List, Dict, Any, Tuple


class BoundarySemantics:
    """
    Infer shared boundaries, wall adjacency, and interior/exterior edges.
    
    NO architectural inference (no room inference, no semantic guessing).
    Pure geometric topology operations only.
    """
    
    @staticmethod
    def compute_shared_edges(polygons: List[Dict[str, Any]], 
                           tolerance: float = 1.0) -> List[Dict[str, Any]]:
        """
        Compute shared boundaries between adjacent polygons.
        
        Returns edges that are shared between exactly 2 polygons.
        """
        if len(polygons) < 2:
            return []
        
        all_edges = []
        edge_owners = {}
        
        for poly in polygons:
            vertices = poly.get("exterior", poly.get("vertices", []))
            poly_id = poly.get("polygon_id", "unknown")
            
            if len(vertices) < 3:
                continue
            
            for i in range(len(vertices)):
                v1 = tuple(vertices[i])
                v2 = tuple(vertices[(i + 1) % len(vertices)])
                edge = BoundarySemantics._normalize_edge(v1, v2)
                
                key = (edge[0], edge[1])
                if key not in edge_owners:
                    edge_owners[key] = []
                edge_owners[key].append(poly_id)
        
        shared_edges = []
        for edge, owners in edge_owners.items():
            if len(owners) == 2:
                shared_edges.append({
                    "edge": edge,
                    "polygon_a": owners[0],
                    "polygon_b": owners[1],
                    "length": math.sqrt(
                        (edge[1][0] - edge[0][0])**2 + (edge[1][1] - edge[0][1])**2
                    )
                })
        
        return shared_edges
    
    @staticmethod
    def _normalize_edge(v1: Tuple[float, float], v2: Tuple[float, float]) -> Tuple[Tuple, Tuple]:
        """Normalize edge so endpoints are consistently ordered."""
        if v1 <= v2:
            return (v1, v2)
        return (v2, v1)
    
    @staticmethod
    def classify_edge_types(polygon: Dict[str, Any], 
                           shared_edges: List[Dict[str, Any]]) -> Dict[str, List]:
        """
        Classify edges as interior (shared) or exterior (boundary).
        
        Returns dict with 'interior' and 'exterior' edge lists.
        """
        vertices = polygon.get("exterior", polygon.get("vertices", []))
        poly_id = polygon.get("polygon_id", "unknown")
        
        interior = []
        exterior = []
        
        for i in range(len(vertices)):
            v1 = tuple(vertices[i])
            v2 = tuple(vertices[(i + 1) % len(vertices)])
            edge = BoundarySemantics._normalize_edge(v1, v2)
            
            is_shared = any(
                e["edge"] == edge and poly_id in (e["polygon_a"], e["polygon_b"])
                for e in shared_edges
            )
            
            edge_info = {"edge": edge, "vertex_indices": [i, (i + 1) % len(vertices)]}
            
            if is_shared:
                interior.append(edge_info)
            else:
                exterior.append(edge_info)
        
        return {"interior": interior, "exterior": exterior}
    
    @staticmethod
    def compute_wall_thickness(polygons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Estimate wall thickness from edge proximity.
        
        For adjacent polygons, compute minimum distance between parallel edges.
        """
        results = []
        
        for i, poly_a in enumerate(polygons):
            for j, poly_b in enumerate(polygons[i + 1:], i + 1):
                min_dist = BoundarySemantics._min_edge_distance(
                    poly_a.get("exterior", poly_a.get("vertices", [])),
                    poly_b.get("exterior", poly_b.get("vertices", []))
                )
                
                if 0 < min_dist < 100:
                    results.append({
                        "polygon_a": poly_a.get("polygon_id"),
                        "polygon_b": poly_b.get("polygon_id"),
                        "estimated_thickness": min_dist
                    })
        
        return results
    
    @staticmethod
    def _min_edge_distance(vertices_a: List[List[float]], 
                          vertices_b: List[List[float]]) -> float:
        """Compute minimum distance between any two edges from each polygon."""
        min_dist = float('inf')
        
        for i in range(len(vertices_a)):
            for j in range(len(vertices_b)):
                dist = BoundarySemantics._point_to_segment_distance(
                    vertices_a[i], vertices_a[(i + 1) % len(vertices_a)],
                    vertices_b[j]
                )
                min_dist = min(min_dist, dist)
        
        return min_dist if min_dist != float('inf') else 0.0
    
    @staticmethod
    def _point_to_segment_distance(p1: List[float], p2: List[float], 
                                    point: List[float]) -> float:
        """Calculate distance from point to line segment."""
        x, y = point
        x1, y1 = p1
        x2, y2 = p2
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return math.sqrt((x - x1)**2 + (y - y1)**2)
        
        t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        return math.sqrt((x - proj_x)**2 + (y - proj_y)**2)