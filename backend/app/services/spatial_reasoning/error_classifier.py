"""Error Classification System for Spatial Graph Quality Issues."""
from typing import Dict, Any, List
from enum import Enum


class ErrorType(Enum):
    GEOMETRY_NOISE = "geometry_noise"
    MISSING_BOUNDARIES = "missing_boundaries"
    ADJACENCY_ERRORS = "adjacency_errors"
    CLASSIFICATION_CONFLICTS = "classification_conflicts"
    ISOLATED_SPACES = "isolated_spaces"


class ErrorClassifier:
    """
    Classify issues found in SpatialGraph for targeted correction.
    
    Maps quality issues to correction strategies:
    - geometry_noise: apply smoothing/filtering
    - missing_boundaries: regenerate coordinates
    - adjacency_errors: adjust gap thresholds
    - isolated_spaces: expand bounds or adjust layout
    """
    
    def classify_issues(self, quality_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze quality report and classify issues with severity.
        
        Returns list of issue dicts with:
        - type: ErrorType
        - severity: float 0-1
        - affected_nodes: list of node IDs
        - suggested_strategy: str
        """
        issues = []
        issues_found = quality_report.get("issues_found", [])
        
        for issue_text in issues_found:
            issue = self._classify_issue_text(issue_text, quality_report)
            if issue:
                issues.append(issue)
        
        return issues
    
    def _classify_issue_text(self, issue_text: str, quality_report: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a single issue string."""
        
        if "Isolated spaces" in issue_text:
            node_ids = self._extract_node_ids(issue_text)
            return {
                "type": ErrorType.ISOLATED_SPACES,
                "severity": 0.8,
                "affected_nodes": node_ids,
                "suggested_strategy": "expand_bounds_with_adjacent_search",
            }
        
        if "zero/near-zero area" in issue_text:
            node_ids = self._extract_node_ids(issue_text)
            return {
                "type": ErrorType.GEOMETRY_NOISE,
                "severity": 0.6,
                "affected_nodes": node_ids,
                "suggested_strategy": "filter_small_areas",
            }
        
        if "Extreme area variance" in issue_text:
            return {
                "type": ErrorType.GEOMETRY_NOISE,
                "severity": 0.7,
                "affected_nodes": [],
                "suggested_strategy": "normalize_area_distribution",
            }
        
        if "Empty graph" in issue_text:
            return {
                "type": ErrorType.MISSING_BOUNDARIES,
                "severity": 1.0,
                "affected_nodes": [],
                "suggested_strategy": "regenerate_geometry_from_source",
            }
        
        return None
    
    def _extract_node_ids(self, text: str) -> List[str]:
        """Extract node IDs from issue text."""
        parts = text.split(":")
        if len(parts) > 1:
            ids_part = parts[1].strip()
            return [i.strip() for i in ids_part.split(",") if i.strip()]
        return []
    
    def get_correction_strategy(self, error_type: ErrorType) -> str:
        """Map error type to specific correction strategy."""
        strategies = {
            ErrorType.GEOMETRY_NOISE: "filter_small_areas",
            ErrorType.MISSING_BOUNDARIES: "regenerate_geometry_from_source",
            ErrorType.ADJACENCY_ERRORS: "adjust_adjacency_threshold",
            ErrorType.CLASSIFICATION_CONFLICTS: "reclassify_with_context",
            ErrorType.ISOLATED_SPACES: "expand_bounds_with_adjacent_search",
        }
        return strategies.get(error_type, "no_correction")