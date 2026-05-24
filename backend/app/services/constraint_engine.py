"""
Constraint Engine for technical ontology validation.
Enforces relationship constraints, cardinality rules, and geometry constraints.
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from enum import Enum

from app.services.technical_ontology import EntityType, RelationshipType


class ConstraintType(str, Enum):
    CARDINALITY = "cardinality"
    MANDATORY = "mandatory"
    FORBIDDEN = "forbidden"
    GEOMETRY = "geometry"


class CardinalityRule(BaseModel):
    """Cardinality constraint for relationships."""
    min_count: int = 0
    max_count: int = 999
    exact: Optional[int] = None


CONSTRAINTS = {
    EntityType.CIRCUIT: {
        "FED_BY": CardinalityRule(min_count=1, max_count=1),
        "POWERS": CardinalityRule(min_count=1, max_count=999),
    },
    EntityType.LUMINAIRE: {
        "ILLUMINATES": CardinalityRule(min_count=0, max_count=1),
    },
    EntityType.AREA: {
        "CONTAINS": CardinalityRule(min_count=0, max_count=999),
    },
    EntityType.PANEL: {
        "FEEDS": CardinalityRule(min_count=1, max_count=999),
    },
}

ALLOWED_RELATIONSHIPS = {
    EntityType.PANEL: [RelationshipType.FEEDS],
    EntityType.LUMINAIRE: [RelationshipType.ILLUMINATES],
    EntityType.CIRCUIT: [RelationshipType.POWERS, RelationshipType.SUPPLIED_BY],
    EntityType.HVAC_UNIT: [RelationshipType.SERVES, RelationshipType.EXHAUSTS, RelationshipType.RETURNS_AIR_TO],
    EntityType.HVAC_ZONE: [RelationshipType.SERVES],
    EntityType.AREA: [RelationshipType.CONTAINS],
    EntityType.WATER_HEATER: [RelationshipType.SUPPLIES],
    EntityType.FIXTURE: [RelationshipType.WATER_SERVED_TO],
}


class ConstraintViolation(BaseModel):
    """Violation of a constraint."""
    constraint_type: ConstraintType
    entity_id: str
    message: str
    severity: str = "warning"


class ConstraintEngine:
    """Enforce technical constraints on the knowledge graph."""
    
    @classmethod
    def check_cardinality(cls, entity_id: str, entity_type: str, 
                        relationship_type: str, current_count: int) -> List[ConstraintViolation]:
        """Check cardinality constraints for a relationship."""
        violations = []
        
        try:
            type_enum = EntityType(entity_type)
            rel_enum = RelationshipType(relationship_type)
        except ValueError:
            return []
        
        rules = CONSTRAINTS.get(type_enum, {})
        rule = rules.get(relationship_type)
        
        if rule:
            if rule.exact and current_count != rule.exact:
                violations.append(ConstraintViolation(
                    constraint_type=ConstraintType.CARDINALITY,
                    entity_id=entity_id,
                    message=f"Expected exactly {rule.exact} {relationship_type} relationships, found {current_count}"
                ))
            elif current_count < rule.min_count:
                violations.append(ConstraintViolation(
                    constraint_type=ConstraintType.CARDINALITY,
                    entity_id=entity_id,
                    message=f"Minimum {rule.min_count} {relationship_type} relationships required, found {current_count}"
                ))
            elif current_count > rule.max_count:
                violations.append(ConstraintViolation(
                    constraint_type=ConstraintType.CARDINALITY,
                    entity_id=entity_id,
                    message=f"Maximum {rule.max_count} {relationship_type} relationships allowed, found {current_count}"
                ))
        
        return violations
    
    @classmethod
    def check_allowed_relationship(cls, source_type: str, rel_type: str) -> List[ConstraintViolation]:
        """Check if relationship is allowed for entity type."""
        violations = []
        
        try:
            source_enum = EntityType(source_type)
            rel_enum = RelationshipType(rel_type)
        except ValueError:
            violations.append(ConstraintViolation(
                constraint_type=ConstraintType.FORBIDDEN,
                entity_id=source_type,
                message=f"Invalid entity type or relationship: {source_type} -> {rel_type}"
            ))
            return violations
        
        allowed = ALLOWED_RELATIONSHIPS.get(source_enum, [])
        if rel_enum not in allowed and allowed:
            violations.append(ConstraintViolation(
                constraint_type=ConstraintType.FORBIDDEN,
                entity_id=source_type,
                message=f"Relationship {rel_type} not allowed for {source_type}"
            ))
        
        return violations
    
    @classmethod
    def validate_graph(cls, registry) -> List[ConstraintViolation]:
        """Validate entire graph against constraints."""
        violations = []
        
        for entity_id, entity in registry.entities.items():
            entity_type = entity.type.value if hasattr(entity.type, 'value') else str(entity.type)
            
            outbound = [r for r in registry.relationships if r.source_entity_id == entity_id]
            for rel in outbound:
                violations.extend(cls.check_cardinality(entity_id, entity_type, rel.type, 1))
                violations.extend(cls.check_allowed_relationship(entity_type, rel.type))
        
        return violations


constraint_engine = ConstraintEngine()