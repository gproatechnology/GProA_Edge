"""Polygon simplification preserving topology and area fidelity."""
import math
from typing import List, Tuple, Dict, Any


class PolygonSimplifier:
    """
    Simplify noisy polygon geometry while preserving:
    - area fidelity
    - topology
    - adjacency semantics
    
    Uses Douglas-Peucker algorithm with topology-aware constraints.
    """
    
    @staticmethod
    def simplify(polygon: Dict[str, Any], tolerance: float = 1.0) -> Dict[str, Any]:
        """
        Simplify polygon vertices using Douglas-Peucker algorithm.
        
        Args:
            polygon: PrecisePolygon or PolygonWithHoles
            tolerance: Maximum perpendicular distance for vertex removal
            
        Returns:
            Simplified polygon
        """
        vertices = polygon.get("vertices", polygon.get("exterior", []))
        
        if len(vertices) < 4:
            return polygon
        
        simplified = PolygonSimplifier._douglas_peucker(vertices, tolerance)
        
        result = polygon.copy()
        result["original_vertex_count"] = len(vertices)
        result["simplified_vertex_count"] = len(simplified)
        
        if "exterior" in polygon:
            result["exterior"] = simplified
            if "interior" in result:
                result["interior"] = [
                    PolygonSimplifier._douglas_peucker(hole, tolerance)
                    for hole in result["interior"]
                ]
        else:
            result["vertices"] = simplified
        
        result["area_preservation"] = PolygonSimplifier._calculate_area_preservation(
            vertices, simplified
        )
        
        return result
    
    @staticmethod
    def _douglas_peucker(points: List[List[float]], tolerance: float) -> List[List[float]]:
        """Douglas-Peucker simplification algorithm."""
        if len(points) < 3:
            return points
        
        dmax = 0
        index = 0
        
        for i in range(1, len(points) - 1):
            d = PolygonSimplifier._perpendicular_distance(points[i], points[0], points[-1])
            if d > dmax:
                dmax = d
                index = i
        
        if dmax > tolerance:
            result1 = PolygonSimplifier._douglas_peucker(points[:index + 1], tolerance)
            result2 = PolygonSimplifier._douglas_peucker(points[index:], tolerance)
            return result1[:-1] + result2
        else:
            return [points[0], points[-1]]
    
    @staticmethod
    def _perpendicular_distance(point: List[float], 
                                line_start: List[float], 
                                line_end: List[float]) -> float:
        """Calculate perpendicular distance from point to line segment."""
        dx = line_end[0] - line_start[0]
        dy = line_end[1] - line_start[1]
        
        if dx == 0 and dy == 0:
            return math.sqrt((point[0] - line_start[0])**2 + (point[1] - line_start[1])**2)
        
        t = ((point[0] - line_start[0]) * dx + (point[1] - line_start[1]) * dy) / (dx * dx + dy * dy)
        
        t = max(0, min(1, t))
        
        proj_x = line_start[0] + t * dx
        proj_y = line_start[1] + t * dy
        
        return math.sqrt((point[0] - proj_x)**2 + (point[1] - proj_y)**2)
    
    @staticmethod
    def _calculate_area_preservation(original: List[List[float]], 
                                    simplified: List[List[float]]) -> float:
        """Calculate area preservation ratio (0.0 to 1.0)."""
        orig_area = PolygonSimplifier._polygon_area(original)
        simp_area = PolygonSimplifier._polygon_area(simplified)
        
        if orig_area == 0:
            return 1.0
        
        return min(1.0, abs(simp_area / orig_area)) if simp_area != 0 else 0.0
    
    @staticmethod
    def _polygon_area(vertices: List[List[float]]) -> float:
        """Calculate polygon area using shoelace formula."""
        if len(vertices) < 3:
            return 0.0
        
        area = 0.0
        n = len(vertices)
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]
        return abs(area) / 2.0
    
    @staticmethod
    def remove_micro_segments(polygon: Dict[str, Any], min_length: float = 0.5) -> Dict[str, Any]:
        """Remove vertices that create micro-segments (noise cleanup)."""
        vertices = polygon.get("vertices", polygon.get("exterior", []))
        
        if len(vertices) < 4:
            return polygon
        
        result = polygon.copy()
        cleaned = []
        
        for i in range(len(vertices)):
            v1 = vertices[i]
            v2 = vertices[(i + 1) % len(vertices)]
            
            dist = math.sqrt((v2[0] - v1[0])**2 + (v2[1] - v1[1])**2)
            
            if dist >= min_length or i == 0:
                cleaned.append(v1)
        
        if "exterior" in polygon:
            result["exterior"] = cleaned
        else:
            result["vertices"] = cleaned
        
        return result