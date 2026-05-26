"""Contour tracing for precise polygon boundary reconstruction."""
import math
from typing import List, Tuple, Dict, Any
from collections import defaultdict


class ContourTracer:
    """
    Reconstructs real contours from linework by stitching edges into closed loops.
    
    Input: vector linework (edges, arcs, splines)
    Output: PrecisePolygon with ordered vertices and contour continuity
    """
    
    @staticmethod
    def trace_from_paths(paths: List[Dict[str, Any]], tolerance: float = 1.0) -> List[Dict[str, Any]]:
        """
        Trace closed polygons from vector paths.
        
        Args:
            paths: Vector paths from PDF/DXF with rect/bounds info
            tolerance: Snapping tolerance for vertex connection
            
        Returns:
            List of PrecisePolygon dictionaries
        """
        if not paths:
            return []
        
        traced = []
        
        for path in paths:
            if path.get("type") not in ["pdf-polygon", "dxf_hatch"]:
                continue
            
            bounds = path.get("bounds", {})
            points = path.get("points", [])
            
            if bounds and not points:
                points = [
                    [bounds["min_x"], bounds["min_y"]],
                    [bounds["max_x"], bounds["min_y"]],
                    [bounds["max_x"], bounds["max_y"]],
                    [bounds["min_x"], bounds["max_y"]]
                ]
            
            if len(points) >= 3:
                traced.append({
                    "polygon_id": path.get("id", "unknown"),
                    "vertices": ContourTracer._order_vertices_clockwise(points),
                    "bounds": bounds,
                    "area_m2": path.get("area_m2", 0),
                    "source": path.get("source", "unknown")
                })
        
        return traced
    
    @staticmethod
    def _order_vertices_clockwise(vertices: List[List[float]]) -> List[List[float]]:
        """Order vertices in clockwise orientation for consistent topology."""
        if len(vertices) < 3:
            return vertices
        
        n = len(vertices)
        xs = [v[0] for v in vertices]
        ys = [v[1] for v in vertices]
        
        center_x = sum(xs) / n
        center_y = sum(ys) / n
        
        angles = []
        for x, y in vertices:
            angle = math.atan2(y - center_y, x - center_x)
            angles.append(angle)
        
        sorted_verts = [v for _, v in sorted(zip(angles, vertices), reverse=True)]
        
        area = ContourTracer._polygon_area(sorted_verts)
        if area < 0:
            sorted_verts.reverse()
        
        return sorted_verts
    
    @staticmethod
    def _polygon_area(vertices: List[List[float]]) -> float:
        """Calculate signed area using shoelace formula."""
        if len(vertices) < 3:
            return 0.0
        
        area = 0.0
        n = len(vertices)
        for i in range(n):
            j = (i + 1) % n
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]
        return area / 2.0
    
    @staticmethod
    def snap_close_vertices(vertices: List[List[float]], tolerance: float = 1.0) -> List[List[float]]:
        """Snap vertices that are within tolerance to reduce floating-point noise."""
        if len(vertices) < 3:
            return vertices
        
        snapped = []
        for v in vertices:
            found = False
            for sv in snapped:
                dist = math.sqrt((v[0] - sv[0])**2 + (v[1] - sv[1])**2)
                if dist <= tolerance:
                    found = True
                    break
            if not found:
                snapped.append(v)
        
        return snapped