"""
Semantic relationships for technical graph reasoning.
Extended relationship types for technical inference.
"""
from enum import Enum
from typing import Dict, Any, Optional


class SemanticRelationshipType(str, Enum):
    """Extended semantic relationship types."""
    # Original relationships
    ILLUMINATES = "illuminates"
    FEEDS = "feeds"
    CONNECTED_TO = "connected_to"
    LOCATED_IN = "located_in"
    PART_OF = "part_of"
    CONTROLS = "controls"
    SUPPLIES = "supplies"
    REFERENCES = "references"

    # Semantic relationships
    DEPENDS_ON = "depends_on"
    REDUNDANT_WITH = "redundant_with"
    CONFLICTS_WITH = "conflicts_with"
    DERIVED_FROM = "derived_from"
    CALCULATED_FROM = "calculated_from"
    VERIFIED_BY = "verified_by"
    AFFECTS = "affects"
    TRIGGERS = "triggers"


class SemanticRelationship:
    """Semantic relationship with inference capabilities."""

    def __init__(self, 
                 source_id: str, 
                 target_id: str, 
                 rel_type: SemanticRelationshipType,
                 confidence: float = 0.95,
                 properties: Optional[Dict[str, Any]] = None):
        self.source_id = source_id
        self.target_id = target_id
        self.rel_type = rel_type
        self.confidence = confidence
        self.properties = properties or {}

    def infer_rule_violation(self, graph_state: Dict[str, Any]) -> Optional[str]:
        """Infer potential rule violations from relationship."""
        if self.rel_type == SemanticRelationshipType.CONFLICTS_WITH:
            return f"Conflict detected between {self.source_id} and {self.target_id}"
        if self.rel_type == SemanticRelationshipType.DEPENDS_ON:
            if self.target_id not in graph_state:
                return f"Missing dependency: {self.target_id} for {self.source_id}"
        return None


# Semantic rules for inference
SEMANTIC_INFERENCE_RULES = [
    {
        "name": "missing_dependency_detection",
        "condition": {
            "relationship": "depends_on",
            "target_exists": False
        },
        "action": "create_validation_issue",
        "severity": "error"
    },
    {
        "name": "conflict_detection",
        "condition": {
            "relationship": "conflicts_with",
        },
        "action": "create_validation_issue",
        "severity": "warning"
    },
    {
        "name": "redundancy_check",
        "condition": {
            "relationship": "redundant_with",
        },
        "action": "create_info_issue",
        "severity": "info"
    }
]