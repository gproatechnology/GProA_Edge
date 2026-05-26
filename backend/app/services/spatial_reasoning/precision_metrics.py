"""Precision metrics for geometric fidelity measurement."""
import math
from typing import List, Dict, Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .topology_validator import TopologyStatus


class PrecisionMetrics:
    """
    Measure contour fidelity, topology integrity, hole detection accuracy,
    polygon validity rate, and geometry degradation.
    """
    
    @staticmethod
    def compute_metrics(polygons, validation_result=None):
        """Compute precision metrics for reconstructed polygons."""
        metrics = {
            "total_polygons": len(polygons),
            "valid_polygons": 0,
            "degraded_polygons": 0,
            "invalid_polygons": 0,
            "total_vertices": 0,
            "avg_vertices_per_polygon": 0.0,
            "total_holes_detected": 0,
            "avg_area_preservation": 0.0,
            "geometry_degradation_pct": 0.0
        }
        
        if not polygons:
            return metrics
        
        total_vertices = 0
        total_area_ratio = 0.0
        hole_count = 0
        
        for poly in polygons:
            vertices = poly.get("exterior", poly.get("vertices", []))
            total_vertices += len(vertices)
            
            if "interior" in poly:
                hole_count += len(poly["interior"])
            
            if "area_preservation" in poly:
                total_area_ratio += poly.get("area_preservation", 1.0)
        
        metrics["total_vertices"] = total_vertices
        metrics["avg_vertices_per_polygon"] = total_vertices / len(polygons)
        metrics["total_holes_detected"] = hole_count
        metrics["avg_area_preservation"] = total_area_ratio / len(polygons)
        
        if validation_result:
            failures = validation_result.get("failures", [])
            for f in failures:
                if f.get("severity") == "critical":
                    metrics["invalid_polygons"] += 1
                elif f.get("severity") == "warning":
                    metrics["degraded_polygons"] += 1
        
        metrics["valid_polygons"] = len(polygons) - metrics["invalid_polygons"] - metrics["degraded_polygons"]
        
        if polygons and "original_vertex_count" in polygons[0]:
            total_original = sum(
                p.get("original_vertex_count", len(p.get("vertices", p.get("exterior", []))))
                for p in polygons
            )
            total_simplified = sum(
                p.get("simplified_vertex_count", len(p.get("vertices", p.get("exterior", []))))
                for p in polygons
            )
            if total_original > 0:
                metrics["geometry_degradation_pct"] = round(
                    (total_original - total_simplified) / total_original * 100, 2
                )
        
        return metrics
    
    @staticmethod
    def measure_contour_accuracy(original, reconstructed):
        """Measure contour fidelity between original and reconstructed polygon."""
        if not original or not reconstructed:
            INF = float('inf')
            return {"hausdorff": INF, "vertex_match": 0.0}
        
        HAUSDORFF_INF = float('inf')
        hausdorff_a = HAUSDORFF_INF
        hausdorff_b = HAUSDORFF_INF
        
        for o in original:
            min_dist = HAUSDORFF_INF
            for r in reconstructed:
                dist = math.sqrt((o[0] - r[0])**2 + (o[1] - r[1])**2)
                min_dist = min(min_dist, dist)
            hausdorff_a = max(hausdorff_a, min_dist)
        
        for r in reconstructed:
            min_dist = HAUSDORFF_INF
            for o in original:
                dist = math.sqrt((r[0] - o[0])**2 + (r[1] - o[1])**2)
                min_dist = min(min_dist, dist)
            hausdorff_b = max(hausdorff_b, min_dist)
        
        hausdorff = max(hausdorff_a, hausdorff_b)
        vertex_match = min(len(original), len(reconstructed)) / max(len(original), len(reconstructed))
        
        return {
            "hausdorff": round(hausdorff, 4),
            "vertex_match": round(vertex_match, 4)
        }