"""Spatial Graph Feedback Loop for iterative improvement."""
import logging
from typing import Dict, Any, List, Optional
from app.services.spatial_reasoning import SpatialGraph
from app.services.spatial_reasoning.quality_evaluator import SpatialGraphQualityEvaluator
from app.services.spatial_reasoning.graph_comparator import SpatialGraphComparator
from app.services.spatial_reasoning.error_classifier import ErrorClassifier, ErrorType
from app.services.spatial_reasoning.ground_truth import GroundTruthDataset
from app.services.spatial_reasoning.geometry_normalizer import GeometryNormalizer

logger = logging.getLogger(__name__)


class SpatialGraphFeedbackLoop:
    """
    Feedback loop for self-improving Spatial Graph.
    
    Process:
    1. Evaluate graph quality
    2. Classify issues by severity
    3. Apply correction strategies
    4. Rebuild graph if needed
    5. Re-evaluate until quality threshold met or max cycles reached
    """
    
    QUALITY_THRESHOLD = 0.75
    ACCURACY_THRESHOLD = 0.85
    MAX_CYCLES = 2
    
    def __init__(self):
        self.evaluator = SpatialGraphQualityEvaluator()
        self.error_classifier = ErrorClassifier()
        self.comparator = SpatialGraphComparator()
        self.normalizer = GeometryNormalizer()
    
    def improve_graph(
        self, 
        graph: SpatialGraph, 
        extraction_result: Any = None,
        ground_truth: GroundTruthDataset = None
    ) -> tuple:
        """
        Improve spatial graph through feedback loop.
        
        Args:
            graph: Initial spatial graph
            extraction_result: Original extraction data for geometry regeneration
            ground_truth: Optional ground truth for accuracy-based optimization
            
        Returns:
            tuple: (improved_graph, improvement_report)
        """
        current_graph = graph
        improvement_log = []
        best_graph = graph
        best_score = 0.0
        
        for cycle in range(self.MAX_CYCLES):
            report = self.evaluator.evaluate(current_graph)
            score = report["overall_score"]
            
            # Check ground truth accuracy if provided
            accuracy = 0.0
            if ground_truth:
                comparison = self.comparator.compare(current_graph, ground_truth)
                accuracy = comparison["overall_accuracy"]
                threshold = self.ACCURACY_THRESHOLD
            else:
                threshold = self.QUALITY_THRESHOLD
            
            if score >= threshold or accuracy >= threshold:
                improvement_log.append({
                    "cycle": cycle + 1,
                    "action": "threshold_met",
                    "quality_score": score,
                    "accuracy": accuracy,
                })
                return current_graph, improvement_log
            
            if score > best_score:
                best_score = score
                best_graph = current_graph
            
            issues = self.error_classifier.classify_issues(report)
            
            if not issues:
                improvement_log.append({
                    "cycle": cycle + 1,
                    "action": "no_correctable_issues",
                    "score": score,
                })
                break
            
            improved_polygons = self._apply_corrections(
                extraction_result, issues, current_graph
            )
            
            if improved_polygons and len(improved_polygons) > 0:
                from app.services.spatial_reasoning.engine import SpatialReasoningEngine
                engine = SpatialReasoningEngine()
                current_graph = engine.build_graph(improved_polygons)
                
                improvement_log.append({
                    "cycle": cycle + 1,
                    "action": "graph_rebuilt",
                    "polygon_count": len(improved_polygons),
                    "issues_addressed": len(issues),
                })
            else:
                improvement_log.append({
                    "cycle": cycle + 1,
                    "action": "no_improvement_possible",
                    "score": score,
                })
                break
        
        return best_graph, improvement_log
    
    def _apply_corrections(
        self, 
        extraction_result: Any, 
        issues: List[Dict[str, Any]], 
        current_graph: SpatialGraph
    ) -> Optional[List[Dict[str, Any]]]:
        """Apply correction strategies based on classified issues."""
        
        if not extraction_result:
            return None
        
        areas = extraction_result.source_metadata.get("areas", [])
        corrected_areas = list(areas)
        
        strategies_applied = set()
        
        for issue in issues:
            strategy = issue.get("suggested_strategy", "")
            
            if strategy == "filter_small_areas" and strategy not in strategies_applied:
                corrected_areas = self._filter_small_areas(corrected_areas)
                strategies_applied.add(strategy)
            elif strategy == "regenerate_geometry_from_source" and strategy not in strategies_applied:
                corrected_areas = areas
                strategies_applied.add(strategy)
        
        if corrected_areas:
            return self.normalizer.normalize_dxf_areas(corrected_areas)
        
        return None
    
    def _filter_small_areas(self, areas: List[Dict]) -> List[Dict]:
        """Filter out suspiciously small areas."""
        return [a for a in areas if a.get("area_m2", 0) > 0.5]
    
    def _expand_bounds_for_isolated(
        self, 
        areas: List[Dict], 
        graph: SpatialGraph, 
        issue: Dict[str, Any]
    ) -> List[Dict]:
        """Adjust layout to reduce isolated spaces by regenerating with tighter spacing."""
        adjusted_areas = []
        for area in areas:
            area_copy = dict(area)
            adjusted_areas.append(area_copy)
        
        return self.normalizer.normalize_dxf_areas(
            adjusted_areas, 
            layers=[a.get("nombre") for a in adjusted_areas]
        )


feedback_loop = SpatialGraphFeedbackLoop()