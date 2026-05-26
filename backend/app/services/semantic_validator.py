"""
Semantic Consistency Validation Layer for EOSIS Edge v1.0.
Detects inconsistencies and anomalies in extracted entities.
No blocking - emits ValidationEvidence for TAL/UAKG.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class ValidationIssueType(str, Enum):
    """Types of semantic validation issues."""
    NEGATIVE_AREA = "negative_area"
    MISSING_LIGHTING = "missing_lighting_power"
    WWR_EXCEEDS_100 = "wwr_exceeds_100_percent"
    DUPLICATE_ENTITY = "duplicate_entity"
    MISSING_PROVENANCE = "missing_provenance"
    UNIT_INCONSISTENCY = "unit_inconsistency"
    EXTREME_VALUE = "extreme_value"


@dataclass
class ValidationEvidence:
    """Evidence of a semantic validation issue."""
    issue_type: ValidationIssueType
    severity: str  # "warning", "error", "info"
    entity_uid: str
    details: Dict[str, Any]
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["issue_type"] = self.issue_type.value
        return result
    

class SemanticValidator:
    """
    Validates semantic consistency of extracted entities.
    
    Does not block extraction - emits ValidationEvidence for downstream handling.
    """
    
    # Thresholds for validation
    MIN_AREA = 0.0
    MAX_AREA = 100000.0
    MAX_WWR = 1.0  # 100%
    
    @classmethod
    def validate_entity(cls, entity: Dict[str, Any]) -> List[ValidationEvidence]:
        """
        Validate a single entity for semantic consistency.
        
        Returns:
            List of ValidationEvidence objects for any issues found.
        """
        issues = []
        props = entity.get("properties", {})
        uid = entity.get("uid", "unknown")
        
        # Check for negative area
        area = props.get("area_m2")
        if area is not None and area < cls.MIN_AREA:
            issues.append(ValidationEvidence(
                issue_type=ValidationIssueType.NEGATIVE_AREA,
                severity="error",
                entity_uid=uid,
                details={"area_m2": area},
                confidence=0.95
            ))
        
        # Check for extreme area values
        if area is not None and area > cls.MAX_AREA:
            issues.append(ValidationEvidence(
                issue_type=ValidationIssueType.EXTREME_VALUE,
                severity="warning",
                entity_uid=uid,
                details={"area_m2": area, "threshold": cls.MAX_AREA},
                confidence=0.90
            ))
        
        # Check for missing provenance
        if not entity.get("provenance"):
            issues.append(ValidationEvidence(
                issue_type=ValidationIssueType.MISSING_PROVENANCE,
                severity="warning",
                entity_uid=uid,
                details={"provenance": None},
                confidence=0.85
            ))
        
        # Check for entity type specific validations
        entity_type = entity.get("type", "")
        
        if entity_type == "luminaire":
            if not props.get("watts") and not props.get("value"):
                issues.append(ValidationEvidence(
                    issue_type=ValidationIssueType.MISSING_LIGHTING,
                    severity="warning",
                    entity_uid=uid,
                    details={"luminaire_missing_power": True},
                    confidence=0.80
                ))
        
        return issues
    
    @classmethod
    def validate_collection(cls, entities: List[Dict[str, Any]]) -> List[ValidationEvidence]:
        """
        Validate a collection of entities for consistency.
        
        Checks for duplicates and cross-entity consistency.
        """
        issues = []
        
        # Validate individual entities
        for entity in entities:
            issues.extend(cls.validate_entity(entity))
        
        # Check for duplicates (same area + name within tolerance)
        seen = {}
        for entity in entities:
            props = entity.get("properties", {})
            uid = entity.get("uid", "")
            
            area = props.get("area_m2")
            name = props.get("nombre") or props.get("name", "")
            
            if area and name:
                key = f"{name.lower()}_{area:.2f}"
                if key in seen:
                    issues.append(ValidationEvidence(
                        issue_type=ValidationIssueType.DUPLICATE_ENTITY,
                        severity="info",
                        entity_uid=uid,
                        details={
                            "duplicate_of": seen[key],
                            "name": name,
                            "area_m2": area
                        },
                        confidence=0.90
                    ))
                else:
                    seen[key] = uid
        
        return issues


validator = SemanticValidator()