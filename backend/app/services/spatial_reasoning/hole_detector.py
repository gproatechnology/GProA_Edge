"""Hole detection for nested polygon topology."""
import math
from typing import List, Tuple, Dict, Any


class HoleDetector:
    """
    Detect inner loops, voids, courtyards, shafts, and nested polygons.
    
    Generates PolygonWithHoles containing exterior and interior boundaries.
    """
    
    @staticmethod
    def detect_holes(polygons: List[Dict[str, Any]], tolerance: float = 1.0) -> List[Dict[str, Any]]:
        """
        Detect holes by checking which polygons are contained within others.
        
        Args:
            polygons: List of PrecisePolygon dictionaries
            tolerance: Containment tolerance
            
        Returns:
            List of PolygonWithHoles (exterior + interior rings)
        """
        if not polygons:
            return []
        
        result = []
        processed = set()
        
        polygons_with_centroids = []
        for i, poly in enumerate(polygons):
            bounds = poly.get("bounds", {})
            if bounds:
                centroid = (
                    (bounds.get("min_x", 0) + bounds.get("max_x", 0)) / 2,
                    (bounds.get("min_y", 0) + bounds.get("max_y", 0)) / 2
                )
                polygons_with_centroids.append((poly, centroid, i))
        
        for i, (poly, (cx, cy), idx) in enumerate(polygons_with_centroids):
            if idx in processed:
                continue
            
            polygon_with_holes = {
                "polygon_id": poly.get("polygon_id", f"poly-{idx}"),
                "exterior": poly.get("vertices", []),
                "interior": [],
                "bounds": poly.get("bounds", {}),
                "area_m2": poly.get("area_m2", 0),
                "source": poly.get("source", "unknown")
            }
            
            for j, (other_poly, (ocx, ocy), other_idx) in enumerate(polygons_with_centroids):
                if other_idx in processed or other_idx == idx:
                    continue
                
                if HoleDetector._point_in_polygon((cx, cy), other_poly.get("vertices", [])):
                    if hole_bounds := other_poly.get("bounds"):
                        ext_bounds = poly.get("bounds", {})
                        if (hole_bounds.get("min_x", 0) >= ext_bounds.get("min_x", 0) and
                            hole_bounds.get("max_x", 0) <= ext_bounds.get("max_x", 0) and
                            hole_bounds.get("min_y", 0) >= ext_bounds.get("min_y", 0) and
                            hole_bounds.get("max_y", 0) <= ext_bounds.get("max_y", 0)):
                            polygon_with_holes["interior"].append(other_poly.get("vertices", []))
                            processed.add(other_idx)
            
            result.append(polygon_with_holes)
            processed.add(idx)
        
        return result
    
    @staticmethod
    def _point_in_polygon(point: Tuple[float, float], vertices: List[List[float]]) -> bool:
        """Ray casting algorithm to check if point is inside polygon."""
        if len(vertices) < 3:
            return False
        
        x, y = point
        n = len(vertices)
        inside = False
        
        p1x, p1y = vertices[0]
        for i in range(1, n + 1):
            p2x, p2y = vertices[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside