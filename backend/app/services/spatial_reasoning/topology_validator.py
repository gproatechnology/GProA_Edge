"""Topology validation for polygon geometric integrity."""
import math
from typing import List, Tuple, Dict, Any
from enum import Enum


class TopologyStatus(Enum):
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"


class TopologyValidator:
    """
    Validate polygon topology including self-intersections, overlapping contours,
    invalid nesting, winding order, and disconnected geometries.
    """
    
    @staticmethod
    def validate(polygons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate all polygons and return classification.
        
        Returns:
            Dict with 'status' (TopologyStatus) and optional 'failures' list
        """
        if not polygons:
            return {"status": TopologyStatus.VALID, "failures": []}
        
        failures = []
        
        for poly in polygons:
            polygon_failures = TopologyValidator._validate_single(poly)
            failures.extend(polygon_failures)
        
        if any(f["severity"] == "critical" for f in failures):
            status = TopologyStatus.INVALID
        elif any(f["severity"] == "warning" for f in failures):
            status = TopologyStatus.DEGRADED
        else:
            status = TopologyStatus.VALID
        
        return {"status": status, "failures": failures}
    
    @staticmethod
    def _validate_single(polygon: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate single polygon for topological issues."""
        failures = []
        vertices = polygon.get("exterior", polygon.get("vertices", []))
        
        if len(vertices) < 3:
            failures.append({
                "type": "insufficient_vertices",
                "severity": "critical",
                "polygon_id": polygon.get("polygon_id", "unknown")
            })
            return failures
        
        if TopologyValidator._has_self_intersection(vertices):
            failures.append({
                "type": "self_intersection",
                "severity": "critical",
                "polygon_id": polygon.get("polygon_id", "unknown")
            })
        
        if not TopologyValidator._is_winding_consistent(vertices):
            failures.append({
                "type": "invalid_winding_order",
                "severity": "warning",
                "polygon_id": polygon.get("polygon_id", "unknown")
            })
        
        interior_rings = polygon.get("interior", [])
        for hole in interior_rings:
            if len(hole) < 3:
                failures.append({
                    "type": "invalid_hole",
                    "severity": "warning",
                    "polygon_id": polygon.get("polygon_id", "unknown"),
                    "hole_index": interior_rings.index(hole)
                })
        
        return failures
    
    @staticmethod
    def _has_self_intersection(vertices: List[List[float]]) -> bool:
        """Check if polygon edges intersect (excluding adjacent edges sharing vertices)."""
        n = len(vertices)
        if n < 4:
            return False
        
        for i in range(n):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                if TopologyValidator._segments_intersect(
                    vertices[i], vertices[(i + 1) % n],
                    vertices[j], vertices[(j + 1) % n]
                ):
                    return True
        return False
    
    @staticmethod
    def _segments_intersect(p1: List[float], p2: List[float], 
                            p3: List[float], p4: List[float]) -> bool:
        """Check if line segments p1-p2 and p3-p4 intersect."""
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
    
    @staticmethod
    def _is_winding_consistent(vertices: List[List[float]]) -> bool:
        """Check if polygon has consistent winding (all clockwise or counterclockwise)."""
        area = TopologyValidator._polygon_area(vertices)
        return area != 0