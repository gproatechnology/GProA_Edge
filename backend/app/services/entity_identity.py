"""
Entity Identity Resolution for canonical entity management.
Handles matching of entities with different naming conventions.
"""
import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from difflib import SequenceMatcher

from app.schemas.technical_entity import TechnicalEntity, EntityType


class CanonicalEntity(BaseModel):
    """Canonical representation of an entity with multiple identifiers."""
    canonical_id: str
    entity_type: EntityType
    aliases: List[str] = []
    properties: Dict = {}
    confidence: float = 0.95


class EntityIdentityResolver:
    """Resolve entity identity across different naming conventions."""

    def __init__(self):
        self.canonical_entities: Dict[str, CanonicalEntity] = {}
        self.alias_to_canonical: Dict[str, str] = {}

    def normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison."""
        name = name.upper()
        name = re.sub(r'[\s\-_]+', '', name)
        name = re.sub(r'[A-Z]{1,2}\d{1,2}[A-Z]{1,2}\d{1,2}', '', name)
        return name

    def similarity(self, a: str, b: str) -> float:
        """Calculate string similarity."""
        return SequenceMatcher(None, a, b).ratio()

    def find_match(self, entity: TechnicalEntity, threshold: float = 0.85) -> Optional[str]:
        """Find canonical ID for an entity based on properties."""
        candidates = []
        # Use uid for stable mapping if name properties are missing
        entity_key = f"{entity.type.value}_{entity.properties.get('watts', 0)}_{entity.properties.get('lumens', 0)}"

        for canon_id, canon in self.canonical_entities.items():
            if canon.entity_type != entity.type:
                continue

            similarity_score = 0.0
            name_prop = entity.properties.get("modelo") or entity.properties.get("catalogo") or ""

            for alias in canon.aliases:
                sim = self.similarity(self.normalize_name(name_prop), self.normalize_name(alias))
                similarity_score = max(similarity_score, sim)

            if similarity_score >= threshold:
                candidates.append((canon_id, similarity_score))

        if candidates:
            return max(candidates, key=lambda x: x[1])[0]
        return None

    def register_entity(self, entity: TechnicalEntity, canonical_id: str = None) -> str:
        """Register an entity and return its canonical ID."""
        if canonical_id is None:
            canonical_id = f"canon_{len(self.canonical_entities) + 1}"

        name = entity.properties.get("modelo") or entity.properties.get("catalogo") or ""
        normalized = self.normalize_name(name)

        if canonical_id not in self.canonical_entities:
            self.canonical_entities[canonical_id] = CanonicalEntity(
                canonical_id=canonical_id,
                entity_type=entity.type,
                aliases=[normalized],
                properties=entity.properties.copy(),
                confidence=entity.confidence
            )
        else:
            canon = self.canonical_entities[canonical_id]
            if normalized and normalized not in canon.aliases:
                canon.aliases.append(normalized)

        self.alias_to_canonical[normalized] = canonical_id
        return canonical_id

    def resolve(self, entity: TechnicalEntity) -> Tuple[str, bool]:
        """Resolve entity to canonical ID. Returns (canonical_id, is_new)."""
        existing = self.find_match(entity)
        if existing:
            return existing, False

        canonical_id = f"canon_{len(self.canonical_entities) + 1}"
        self.register_entity(entity, canonical_id)
        return canonical_id, True

    def get_by_canonical(self, canonical_id: str) -> Optional[CanonicalEntity]:
        return self.canonical_entities.get(canonical_id)


class EntityMatcher:
    """Match entities by various criteria."""

    LUMINAIRE_PATTERNS = [
        (r'LHBS|LIGHT\s*HIGH\s*BAY|INDUSTRIAL', 'high_bay'),
        (r'LED|LOW\s*BAY', 'led_fixture'),
        (r'WALLPACK|WP', 'wallpack'),
        (r'CANOPY|CN', 'canopy'),
        (r'EMERGENCY|EXIT|APC', 'emergency'),
    ]

    @classmethod
    def match_luminaire_type(cls, modelo: str) -> Optional[str]:
        """Match luminaire model to type."""
        if not modelo:
            return None
        modelo_upper = modelo.upper()
        for pattern, lum_type in cls.LUMINAIRE_PATTERNS:
            if re.search(pattern, modelo_upper):
                return lum_type
        return None

    @classmethod
    def match_power_range(cls, watts: float) -> str:
        """Categorize power range."""
        if watts <= 50:
            return "low"
        elif watts <= 150:
            return "medium"
        elif watts <= 300:
            return "high"
        return "very_high"


# Singleton
resolver = EntityIdentityResolver()