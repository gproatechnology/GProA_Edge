"""
Graph Rules Engine for EDGE Certification.
Declarative rules for relationship validation and integrity checks.
"""
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from pydantic import BaseModel
from dataclasses import dataclass

from app.schemas.technical_entity import TechnicalEntity, EntityType
from app.services.entity_registry import RelationshipEngine, RelationshipType


class RuleSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class RuleResult:
    passed: bool
    message: str
    entity_id: Optional[str] = None


class Rule(BaseModel):
    """Declarative validation rule."""
    name: str
    description: str
    entity_type: EntityType
    rule_type: str
    condition: Optional[Dict[str, Any]] = None
    action: Optional[str] = None

    def evaluate(self, engine: RelationshipEngine, entity: TechnicalEntity) -> RuleResult:
        raise NotImplementedError


class RequiresRelationship(Rule):
    """Entity must have a specific relationship type."""

    def evaluate(self, engine: RelationshipEngine, entity: TechnicalEntity) -> RuleResult:
        rels = engine.registry.get_neighborhood(entity.uid)
        rel_types = [r.type for r in rels]
        required = self.condition.get("relationship", RelationshipType.ILLUMINATES)

        if required in rel_types:
            return RuleResult(passed=True, message=f"Has required relationship: {required}")
        return RuleResult(
            passed=False,
            message=f"Missing required relationship: {required}",
            entity_id=entity.uid
        )


class AreaMustHaveLighting(Rule):
    """Area entities must be illuminated by luminaries."""

    def evaluate(self, engine: RelationshipEngine, entity: TechnicalEntity) -> RuleResult:
        if entity.type != EntityType.AREA:
            return RuleResult(passed=True, message="Not an area entity")

        downstream = engine.get_downstream_entities(entity.uid)
        luminaries = [eid for eid in downstream if engine.registry.entities.get(eid, {}).get("type") == EntityType.LUMINAIRE]

        if luminaries:
            return RuleResult(passed=True, message=f"Area has {len(luminaries)} luminaries")
        return RuleResult(
            passed=False,
            message="Area has no associated luminaries",
            entity_id=entity.uid
        )


class PanelMustFeedCircuit(Rule):
    """Panel must feed at least one circuit."""

    def evaluate(self, engine: RelationshipEngine, entity: TechnicalEntity) -> RuleResult:
        if entity.type != EntityType.PANEL:
            return RuleResult(passed=True, message="Not a panel entity")

        downstream = engine.get_downstream_entities(entity.uid)
        circuits = [eid for eid in downstream if engine.registry.entities.get(eid, {}).get("type") == EntityType.CIRCUIT]

        if circuits:
            return RuleResult(passed=True, message=f"Panel feeds {len(circuits)} circuits")
        return RuleResult(
            passed=False,
            message="Panel has no associated circuits",
            entity_id=entity.uid
        )


class GraphRulesEngine:
    """Engine to evaluate rules against the technical graph."""

    def __init__(self, engine: RelationshipEngine):
        self.engine = engine
        self.rules: List[Rule] = []
        self._load_default_rules()

    def _load_default_rules(self):
        self.rules = [
            AreaMustHaveLighting(
                name="area_must_have_lighting",
                description="Each area must have associated luminaries",
                entity_type=EntityType.AREA,
                rule_type="integrity"
            ),
            PanelMustFeedCircuit(
                name="panel_must_feed_circuit",
                description="Each panel must feed at least one circuit",
                entity_type=EntityType.PANEL,
                rule_type="integrity"
            ),
        ]

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def evaluate_all(self) -> List[RuleResult]:
        results = []
        for rule in self.rules:
            for entity in self.engine.registry.entities.values():
                if entity.type == rule.entity_type:
                    results.append(rule.evaluate(self.engine, entity))
        return results

    def evaluate_by_type(self, entity_type: EntityType) -> List[RuleResult]:
        results = []
        for rule in self.rules:
            if rule.entity_type == entity_type:
                for entity in self.engine.registry.entities.values():
                    if entity.type == entity_type:
                        results.append(rule.evaluate(self.engine, entity))
        return results

    def get_failed_rules(self) -> List[RuleResult]:
        return [r for r in self.evaluate_all() if not r.passed]


# Rules registry
DEFAULT_RULES = [
    RequiresRelationship(
        name="luminaire_requires_area",
        description="Luminaire must illuminate an area",
        entity_type=EntityType.LUMINAIRE,
        rule_type="integrity",
        condition={"relationship": RelationshipType.ILLUMINATES}
    ),
    AreaMustHaveLighting(
        name="area_has_lighting",
        description="Area must have associated luminaries",
        entity_type=EntityType.AREA,
        rule_type="integrity"
    ),
]