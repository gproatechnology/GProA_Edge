"""
Rule DSL for declarative validation rules.
YAML-based rule definitions with policy-based validation.
"""
from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
import yaml

from app.schemas.technical_entity import TechnicalEntity, EntityType
from app.services.entity_registry import RelationshipEngine, RelationshipType, EntityRegistry


class RuleSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class RuleCondition(BaseModel):
    """Condition for rule evaluation."""
    relationship: Optional[str] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    property_key: Optional[str] = None
    values: Optional[List[str]] = None


class RuleDSL(BaseModel):
    """Rule definition in DSL format."""
    name: str
    description: str
    when: Dict[str, str]
    then: Dict[str, Any]
    severity: RuleSeverity = RuleSeverity.WARNING
    enabled: bool = True


class RuleResult(BaseModel):
    passed: bool
    message: str
    entity_id: Optional[str] = None
    severity: str = "warning"


class RuleDSLParser:
    """Parse YAML rules into executable validation rules."""

    def __init__(self, registry: EntityRegistry):
        self.registry = registry

    def parse_yaml(self, yaml_content: str) -> RuleDSL:
        """Parse YAML rule definition."""
        data = yaml.safe_load(yaml_content)
        return RuleDSL(**data)

    def evaluate(self, rule: RuleDSL, entity: TechnicalEntity) -> RuleResult:
        """Evaluate rule against entity."""
        entity_type_str = rule.when.get("entity_type", "")
        entity_type = EntityType(entity_type_str)

        if entity.type != entity_type:
            return RuleResult(passed=True, message="Entity type mismatch")

        then_action = rule.then.get("requires_relationship")
        if then_action:
            rel_type = then_action.get("type", "")
            rel_enum = RelationshipType(rel_type)
            rels = self.registry.get_neighborhood(entity.uid)
            rel_types = [r.type for r in rels]

            if rel_enum in rel_types:
                return RuleResult(
                    passed=True,
                    message=f"Has required relationship: {rel_type}",
                    severity=rule.severity
                )
            return RuleResult(
                passed=False,
                message=f"Missing required relationship: {rel_type}",
                entity_id=entity.uid,
                severity=rule.severity
            )

        return RuleResult(passed=True, message="No action specified")


class RuleManager:
    """Manage and execute rules from DSL definitions."""

    def __init__(self, registry: EntityRegistry):
        self.registry = registry
        self.parser = RuleDSLParser(registry)
        self.rules: List[RuleDSL] = []

    def load_rules_from_yaml(self, yaml_content: str):
        """Load multiple rules from YAML."""
        data = yaml.safe_load(yaml_content)
        for rule_data in data.get("rules", []):
            rule = RuleDSL(**rule_data)
            self.rules.append(rule)

    def evaluate_all(self) -> List[RuleResult]:
        """Evaluate all rules against matching entities."""
        results = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            entity_type_str = rule.when.get("entity_type", "")
            entity_type = EntityType(entity_type_str)
            for entity in self.registry.entities.values():
                if entity.type == entity_type:
                    result = self.parser.evaluate(rule, entity)
                    results.append(result)
        return results

    def get_failed_rules(self) -> List[RuleResult]:
        return [r for r in self.evaluate_all() if not r.passed]


DEFAULT_RULES_YAML = """
rules:
  - name: area_must_have_lighting
    description: "Each area must have associated luminaries"
    when:
      entity_type: area
    then:
      requires_relationship:
        type: illuminates
        target_type: luminaire
    severity: warning
    enabled: true

  - name: panel_must_feed_circuit
    description: "Each panel must feed at least one circuit"
    when:
      entity_type: panel
    then:
      requires_relationship:
        type: feeds
        target_type: circuit
    severity: error
    enabled: true

  - name: luminaire_requires_area
    description: "Luminaire must illuminate an area"
    when:
      entity_type: luminaire
    then:
      requires_relationship:
        type: illuminates
        target_type: area
    severity: warning
    enabled: true
"""