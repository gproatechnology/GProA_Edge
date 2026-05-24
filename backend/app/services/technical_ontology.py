"""
Technical Ontology for Engineering Disciplines.
Defines entity schemas, relationships, and validation rules.
"""
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class RelationshipType(str, Enum):
    FEEDS = "feeds"
    POWERS = "powers"
    ILLUMINATES = "illuminates"
    SERVES = "serves"
    CONTAINS = "contains"
    LOCATED_IN = "located_in"
    SUPPLIED_BY = "supplied_by"
    CONNECTED_TO = "connected_to"
    PROTECTS = "protects"
    EXHAUSTS = "exhausts"
    RETURNS_AIR_TO = "returns_air_to"
    COOLS = "cools"
    HEATS = "heats"
    WATER_SERVED_TO = "water_served_to"
    DRAINS_TO = "drains_to"
    SUPPLIES = "supplies"


class EntityType(str, Enum):
    LUMINAIRE = "luminaire"
    PANEL = "panel"
    CIRCUIT = "circuit"
    AREA = "area"
    HVAC_UNIT = "hvac_unit"
    FIXTURE = "fixture"
    DIMENSION = "dimension"
    HVAC_ZONE = "hvac_zone"
    WATER_HEATER = "water_heater"
    PUMP = "pump"


ENTITY_ONTOLOGY = {
    EntityType.LUMINAIRE: {
        "required": ["watts", "lumens", "modelo"],
        "optional": ["efficacy", "color_temp", "cri"],
        "relationships": [RelationshipType.ILLUMINATES],
        "validations": ["min_efficacy_lm_per_w", "max_watts_per_circuit"],
        "unit_normalizations": {
            "watts": "W",
            "lumens": "lm"
        }
    },
    EntityType.PANEL: {
        "required": ["panel_kw", "amps", "voltage"],
        "optional": ["circuits", "location"],
        "relationships": [RelationshipType.FEEDS],
        "validations": ["panel_load_consistency"]
    },
    EntityType.CIRCUIT: {
        "required": ["amps", "voltage"],
        "optional": ["panel_id", "load_kw"],
        "relationships": [RelationshipType.POWERS, RelationshipType.SUPPLIED_BY],
        "validations": ["circuit_ampacity"]
    },
    EntityType.AREA: {
        "required": ["area_m2"],
        "optional": ["type", "name", "height"],
        "relationships": [RelationshipType.CONTAINS],
        "validations": []
    },
    EntityType.HVAC_UNIT: {
        "required": ["cop", "seer", "capacity_btuh"],
        "optional": ["refrigerant", "voltage"],
        "relationships": [RelationshipType.SERVES, RelationshipType.EXHAUSTS, RelationshipType.RETURNS_AIR_TO],
        "validations": ["min_cop", "min_seer"]
    },
    EntityType.HVAC_ZONE: {
        "required": ["area_m2", "occupancy"],
        "optional": ["cooling_load", "heating_load"],
        "relationships": [RelationshipType.SERVES],
        "validations": ["zone_load_balance"]
    },
    EntityType.WATER_HEATER: {
        "required": ["capacity_l", "efficiency"],
        "optional": ["voltage", "recovery_rate"],
        "relationships": [RelationshipType.SUPPLIES],
        "validations": ["min_efficiency"]
    },
    EntityType.FIXTURE: {
        "required": ["gpm", "type"],
        "optional": ["pressure_loss", "manufacturer"],
        "relationships": [RelationshipType.WATER_SERVED_TO],
        "validations": ["max_gpm_per_fixture"]
    }
}


RELATIONSHIP_RULES = {
    RelationshipType.FEEDS: {
        "source": EntityType.PANEL,
        "target": EntityType.CIRCUIT,
        "bidirectional": RelationshipType.SUPPLIED_BY
    },
    RelationshipType.ILLUMINATES: {
        "source": EntityType.LUMINAIRE,
        "target": EntityType.AREA
    },
    RelationshipType.SERVES: {
        "source": [EntityType.HVAC_UNIT, EntityType.HVAC_ZONE],
        "target": EntityType.AREA
    },
    RelationshipType.CONTAINS: {
        "source": EntityType.AREA,
        "target": [EntityType.LUMINAIRE, EntityType.FIXTURE, EntityType.HVAC_UNIT]
    },
    RelationshipType.LOCATED_IN: {
        "source": None,
        "target": EntityType.AREA,
        "inferred_from": "spatial_containment"
    }
}


class OntologyValidator:
    """Validate entities against technical ontology."""
    
    @classmethod
    def validate_entity(cls, entity: Dict[str, Any]) -> List[str]:
        """Validate entity has required fields per ontology."""
        entity_type = entity.get("type") or entity.get("entity_type")
        if not entity_type:
            return ["Missing entity type"]
        
        try:
            type_enum = EntityType(entity_type)
        except ValueError:
            return [f"Unknown entity type: {entity_type}"]
        
        schema = ENTITY_ONTOLOGY.get(type_enum, {})
        required = schema.get("required", [])
        
        errors = []
        for field in required:
            if field not in entity.get("properties", {}) and field not in entity:
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    @classmethod
    def validate_relationship(cls, source_type: str, target_type: str, 
                               rel_type: RelationshipType) -> bool:
        """Validate relationship is valid per ontology."""
        if rel_type not in RELATIONSHIP_RULES:
            return False
        
        rule = RELATIONSHIP_RULES[rel_type]
        valid_sources = rule.get("source")
        valid_targets = rule.get("target")
        
        source_valid = valid_sources is None or source_type in valid_sources
        target_valid = valid_targets is None or target_type in valid_targets
        
        return source_valid and target_valid


ontology = OntologyValidator()