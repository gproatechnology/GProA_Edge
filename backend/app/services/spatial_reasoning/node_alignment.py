"""Node matching and identity alignment for spatial graphs."""
from typing import Dict, Any, List, Tuple, Optional
from app.services.spatial_reasoning import SpatialGraph, SpatialNode
from app.services.spatial_reasoning.ground_truth import GroundTruthSpace


class NodeMatcher:
    """
    Match predicted nodes to ground truth for identity stability.
    
    Matching criteria:
    - Geometric overlap (IoU)
    - Centroid distance
    - Area similarity
    """
    
    def match_nodes(
        self,
        predicted_nodes: List[SpatialNode],
        ground_truth_spaces: List[GroundTruthSpace]
    ) -> Dict[str, str]:
        """
        Match predicted nodes to ground truth spaces.
        
        Returns dict mapping predicted node uid -> ground truth space id
        """
        matches = {}
        
        for node in predicted_nodes:
            best_match = self._find_best_match(node, ground_truth_spaces)
            if best_match:
                matches[node.uid] = best_match.id
        
        return matches
    
    def _find_best_match(
        self,
        node: SpatialNode,
        spaces: List[GroundTruthSpace]
    ) -> Optional[GroundTruthSpace]:
        """Find best matching ground truth space for a node."""
        scores = []
        
        for space in spaces:
            score = self._compute_match_score(node, space)
            scores.append((score, space))
        
        scores.sort(reverse=True)
        best_score, best_space = scores[0] if scores else (0, None)
        
        return best_space if best_score > 0.3 else None
    
    def _compute_match_score(self, node: SpatialNode, space: GroundTruthSpace) -> float:
        """Compute combined match score."""
        overlap_score = self._compute_overlap(node, space)
        centroid_score = self._compute_centroid_similarity(node, space)
        area_score = self._compute_area_similarity(node, space)
        
        return (overlap_score * 0.5 + centroid_score * 0.3 + area_score * 0.2)
    
    def _compute_overlap(self, node: SpatialNode, space: GroundTruthSpace) -> float:
        """Compute IoU-style overlap between node bounds and space bounds."""
        bounds = node.bounds
        gt_bounds = space.expected_bounds
        
        x_overlap = max(0, min(bounds.max_x, gt_bounds["max_x"]) - max(bounds.min_x, gt_bounds["min_x"]))
        y_overlap = max(0, min(bounds.max_y, gt_bounds["max_y"]) - max(bounds.min_y, gt_bounds["min_y"]))
        intersection = x_overlap * y_overlap
        
        node_area = (bounds.max_x - bounds.min_x) * (bounds.max_y - bounds.min_y)
        gt_area = (gt_bounds["max_x"] - gt_bounds["min_x"]) * (gt_bounds["max_y"] - gt_bounds["min_y"])
        union = node_area + gt_area - intersection
        
        return intersection / union if union > 0 else 0
    
    def _compute_centroid_similarity(self, node: SpatialNode, space: GroundTruthSpace) -> float:
        """Compute centroid proximity score."""
        cx, cy = node.centroid
        gt_cx = (space.expected_bounds["min_x"] + space.expected_bounds["max_x"]) / 2
        gt_cy = (space.expected_bounds["min_y"] + space.expected_bounds["max_y"]) / 2
        
        distance = ((cx - gt_cx) ** 2 + (cy - gt_cy) ** 2) ** 0.5
        max_dist = max(space.expected_bounds["max_x"], space.expected_bounds["max_y"])
        
        return max(0, 1 - distance / max(1, max_dist))
    
    def _compute_area_similarity(self, node: SpatialNode, space: GroundTruthSpace) -> float:
        """Compute area ratio similarity."""
        node_area = node.area_m2
        gt_area = space.expected_area_m2
        
        if gt_area == 0:
            return 0
        
        ratio = min(node_area, gt_area) / max(node_area, gt_area)
        return ratio


class NodeAlignmentEvaluator:
    """
    Evaluate node identity alignment independently from structural correctness.
    """
    
    def __init__(self):
        self.matcher = NodeMatcher()
    
    def evaluate(
        self,
        predicted: SpatialGraph,
        ground_truth: Any
    ) -> Dict[str, Any]:
        """
        Evaluate node alignment between prediction and ground truth.
        
        Returns detailed alignment metrics.
        """
        matches = self.matcher.match_nodes(predicted.nodes, ground_truth.spaces)
        
        matched_count = len(matches)
        predicted_count = len(predicted.nodes)
        expected_count = len(ground_truth.spaces)
        
        precision = matched_count / max(1, predicted_count)
        recall = matched_count / max(1, expected_count)
        f1 = 2 * precision * recall / max(0.001, precision + recall)
        
        return {
            "alignment_score": f1,
            "matched_nodes": matched_count,
            "predicted_nodes": predicted_count,
            "expected_nodes": expected_count,
            "matches": matches
        }


node_matcher = NodeMatcher()
alignment_evaluator = NodeAlignmentEvaluator()