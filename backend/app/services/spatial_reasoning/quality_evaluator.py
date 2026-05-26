"""
Spatial Graph Quality Evaluator.
Validates geometric robustness and graph completeness from real plan inputs.
"""
import math
from typing import Dict, Any, List, Optional
from app.services.spatial_reasoning import SpatialGraph, SpatialNodeType


class SpatialGraphQualityEvaluator:
    """
    Evaluates the quality of a Spatial Graph for reality validation.
    
    Computes metrics:
    - Completeness: % of expected spaces detected
    - Adjacency confidence: distribution of edge confidences  
    - Geometry validity: closed polygons, consistent topology
    - Layout coherence: realistic space arrangements
    """
    
    def evaluate(self, graph: SpatialGraph) -> Dict[str, Any]:
        """
        Run full quality assessment on a SpatialGraph.
        
        Returns dict with:
        - completeness_score (0-1)
        - adjacency_confidence_avg
        - geometry_validity_score
        - layout_coherence_score
        - issues_found: list of problems
        """
        adj_quality = self._compute_adjacency_quality(graph)
        
        scores = {
            "completeness": self._compute_completeness(graph),
            "adjacency_quality": adj_quality[0] if adj_quality else 0.0,
            "geometry_validity": self._compute_geometry_validity(graph),
            "layout_coherence": self._compute_layout_coherence(graph),
        }
        
        issues = self._find_issues(graph)
        
        overall = sum(scores.values()) / len(scores)
        
        return {
            "completeness_score": scores["completeness"],
            "adjacency_confidence_avg": scores["adjacency_quality"],
            "adjacency_edge_count": adj_quality[1] if adj_quality else 0,
            "geometry_validity_score": scores["geometry_validity"],
            "layout_coherence_score": scores["layout_coherence"],
            "overall_score": round(overall, 2),
            "issues_found": issues,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "node_types": self._count_node_types(graph),
        }
    
    def _compute_completeness(self, graph: SpatialGraph) -> float:
        """
        Estimate completeness based on space count and area distribution.
        
        A complete floor plan typically has multiple connected spaces.
        """
        node_count = len(graph.nodes)
        if node_count == 0:
            return 0.0
        if node_count == 1:
            return 0.5  # Might be incomplete
        return min(1.0, node_count / 5.0)  # Expect ~5+ spaces typically
    
    def _compute_adjacency_quality(self, graph: SpatialGraph) -> tuple:
        """
        Compute adjacency quality metrics.
        Returns (avg_confidence, edge_count).
        """
        edges = graph.edges
        if not edges:
            return (0.0, 0)
        
        confidences = [e.confidence for e in edges]
        return (sum(confidences) / len(confidences), len(edges))
    
    def _compute_geometry_validity(self, graph: SpatialGraph) -> float:
        """
        Check geometric validity of nodes.
        
        Valid if:
        - Bounds are properly ordered
        - Area > 0
        - Centroid inside bounds
        """
        valid_count = 0
        for node in graph.nodes:
            bounds = node.bounds
            if not bounds:
                continue
            
            # Check bounds consistency
            if bounds.min_x >= bounds.max_x or bounds.min_y >= bounds.max_y:
                continue
            
            # Check area positive
            if node.area_m2 <= 0:
                continue
            
            # Check centroid inside bounds
            cx, cy = node.centroid
            if bounds.min_x <= cx <= bounds.max_x and bounds.min_y <= cy <= bounds.max_y:
                valid_count += 1
        
        return valid_count / len(graph.nodes) if graph.nodes else 0.0
    
    def _compute_layout_coherence(self, graph: SpatialGraph) -> float:
        """
        Check if layout is physically plausible.
        
        Penalize:
        - Nodes too far apart (isolated spaces)
        - Nodes with overlapping extents (duplicate detection)
        """
        nodes = graph.nodes
        if len(nodes) < 2:
            return 1.0
        
        # Check for isolated nodes (no edges)
        isolated = 0
        for node in nodes:
            edges = graph.get_edges_for_node(node.uid)
            if not edges:
                isolated += 1
        
        isolation_penalty = isolated / len(nodes)
        
        # Check for extreme overlaps
        overlaps = 0
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i+1:]:
                if self._bounds_overlap(n1.bounds, n2.bounds):
                    overlaps += 1
        
        overlap_penalty = min(1.0, overlaps / max(1, len(nodes) * 0.5))
        
        coherence = 1.0 - (isolation_penalty * 0.5) - (overlap_penalty * 0.5)
        return max(0.0, coherence)
    
    def _bounds_overlap(self, b1, b2) -> bool:
        """Check if two bounds significantly overlap."""
        if not b1 or not b2:
            return False
        overlap_x = min(b1.max_x, b2.max_x) - max(b1.min_x, b2.min_x)
        overlap_y = min(b1.max_y, b2.max_y) - max(b1.min_y, b2.min_y)
        return overlap_x > 0 and overlap_y > 0
    
    def _find_issues(self, graph: SpatialGraph) -> List[str]:
        """Identify specific issues with the graph."""
        issues = []
        
        # Check for empty graph
        if not graph.nodes:
            issues.append("Empty graph - no spaces detected")
            return issues
        
        # Check for isolated nodes
        isolated = []
        for node in graph.nodes:
            if not graph.get_edges_for_node(node.uid):
                isolated.append(node.uid)
        if isolated:
            issues.append(f"Isolated spaces: {', '.join(isolated[:3])}")
        
        # Check for zero-area nodes
        zero_area = [n.uid for n in graph.nodes if n.area_m2 <= 0.1]
        if zero_area:
            issues.append(f"Suspicious zero/near-zero area nodes: {', '.join(zero_area[:3])}")
        
        # Check for wide range of areas (might indicate error)
        areas = [n.area_m2 for n in graph.nodes if n.area_m2 > 0.1]
        if areas:
            area_ratio = max(areas) / min(areas) if min(areas) > 0 else 1
            if area_ratio > 100:
                issues.append(f"Extreme area variance detected (ratio: {area_ratio:.0f}:1)")
        
        return issues
    
    def _count_node_types(self, graph: SpatialGraph) -> Dict[str, int]:
        """Count nodes by type."""
        counts = {}
        for node in graph.nodes:
            t = node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type)
            counts[t] = counts.get(t, 0) + 1
        return counts


# Singleton instance for easy access
evaluator = SpatialGraphQualityEvaluator()