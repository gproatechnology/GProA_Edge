"""Graph comparator for ground truth validation."""
from typing import Dict, Any, List, Tuple
from app.services.spatial_reasoning import SpatialGraph, SpatialNode
from app.services.spatial_reasoning.ground_truth import GroundTruthDataset
from app.services.spatial_reasoning.node_alignment import NodeMatcher


class SpatialGraphComparator:
    """
    Compare predicted SpatialGraph against ground truth.
    
    Computes:
    - Node precision/recall (with geometric matching)
    - Adjacency precision/recall  
    - Geometry reconstruction error (IoU style)
    """
    
    def __init__(self):
        self.matcher = NodeMatcher()
    
    def compare(
        self, 
        predicted: SpatialGraph, 
        ground_truth: GroundTruthDataset
    ) -> Dict[str, Any]:
        """
        Compare predicted graph against ground truth.
        
        Returns dict with accuracy metrics.
        """
        node_metrics = self._compare_nodes(predicted.nodes, ground_truth)
        adjacency_metrics = self._compare_adjacencies(predicted, ground_truth)
        
        geometry_error = self._compute_geometry_error(predicted.nodes, ground_truth)
        
        return {
            "node_precision": node_metrics["precision"],
            "node_recall": node_metrics["recall"],
            "node_f1": node_metrics["f1"],
            "node_count_predicted": len(predicted.nodes),
            "node_count_expected": len(ground_truth.spaces),
            "adjacency_precision": adjacency_metrics["precision"],
            "adjacency_recall": adjacency_metrics["recall"],
            "adjacency_f1": adjacency_metrics["f1"],
            "edge_count_predicted": len(predicted.edges),
            "edge_count_expected": len(ground_truth.get_expected_adjacency_pairs()),
            "geometry_error_m2": geometry_error,
            "overall_accuracy": self._compute_overall_accuracy(
                node_metrics, adjacency_metrics, geometry_error
            )
        }
    
    def _compare_nodes(
        self, 
        predicted_nodes: List[SpatialNode], 
        ground_truth: GroundTruthDataset
    ) -> Dict[str, float]:
        """Compute node-level precision/recall using geometric matching."""
        # Use geometric matching instead of ID matching
        matches = self.matcher.match_nodes(predicted_nodes, ground_truth.spaces)
        
        true_positives = len(matches)
        predicted_count = len(predicted_nodes)
        expected_count = len(ground_truth.spaces)
        
        precision = true_positives / max(1, predicted_count)
        recall = true_positives / max(1, expected_count)
        f1 = 2 * precision * recall / max(0.001, precision + recall)
        
        return {"precision": precision, "recall": recall, "f1": f1}
    
    def _compare_adjacencies(
        self, 
        graph: SpatialGraph, 
        ground_truth: GroundTruthDataset
    ) -> Dict[str, float]:
        """Compute adjacency precision/recall."""
        expected_pairs = set(ground_truth.get_expected_adjacency_pairs())
        
        # Build mapping from node uid to geometry_ref for lookup
        node_to_ref = {}
        for node in graph.nodes:
            node_to_ref[node.uid] = node.geometry_ref or node.uid
        
        predicted_pairs = set()
        for edge in graph.edges:
            # Convert UIDs to geometry_refs for comparison
            ref_a = node_to_ref.get(edge.source_uid, edge.source_uid)
            ref_b = node_to_ref.get(edge.target_uid, edge.target_uid)
            
            pair = tuple(sorted([ref_a, ref_b]))
            predicted_pairs.add(pair)
        
        true_positives = len(predicted_pairs & expected_pairs)
        false_positives = len(predicted_pairs - expected_pairs)
        false_negatives = len(expected_pairs - predicted_pairs)
        
        precision = true_positives / max(1, true_positives + false_positives)
        recall = true_positives / max(1, true_positives + false_negatives)
        f1 = 2 * precision * recall / max(0.001, precision + recall)
        
        return {"precision": precision, "recall": recall, "f1": f1}
    
    def _compute_geometry_error(
        self, 
        nodes: List[SpatialNode], 
        ground_truth: GroundTruthDataset
    ) -> float:
        """Compute total geometry error using area difference."""
        total_error = 0.0
        
        for node in nodes:
            # Use geometry_ref to find matching ground truth
            space_id = node.geometry_ref or node.uid
            expected = ground_truth.get_space_by_id(space_id)
            
            if expected:
                error = abs(node.area_m2 - expected.expected_area_m2)
                total_error += error
        
        return total_error
    
    def _compute_overall_accuracy(
        self, 
        node_metrics: Dict[str, float],
        adjacency_metrics: Dict[str, float],
        geometry_error: float
    ) -> float:
        """Compute weighted overall accuracy."""
        node_score = node_metrics["f1"]
        adj_score = adjacency_metrics["f1"]
        
        # Normalize geometry error (assume 100m2 max acceptable error)
        geometry_score = max(0, 1 - geometry_error / 100)
        
        return round((node_score * 0.4 + adj_score * 0.4 + geometry_score * 0.2), 2)


comparator = SpatialGraphComparator()