"""
Multi-factor entity matching with weighted confidence scoring.
"""
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
from difflib import SequenceMatcher

from app.schemas.technical_entity import TechnicalEntity, EntityType


class MatchFactor(BaseModel):
    """Single factor in entity matching."""
    name: str
    weight: float
    score: float
    contribution: float


class EntityMatch(BaseModel):
    """Result of entity matching."""
    canonical_id: str
    confidence: float
    factors: List[MatchFactor]


class MultiFactorMatcher:
    """Match entities using multiple weighted factors."""

    FACTORS = {
        "name": 0.30,
        "power": 0.20,
        "coordinates": 0.15,
        "layer": 0.10,
        "area": 0.10,
        "type": 0.10,
        "schedule_ref": 0.05,
    }

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize name for comparison."""
        import re
        name = name.upper()
        name = re.sub(r'[\s\-_]+', '', name)
        name = re.sub(r'[A-Z]{1,2}\d{1,2}[A-Z]{1,2}\d{1,2}', '', name)
        return name

    @staticmethod
    def _calculate_similarity(a: str, b: str) -> float:
        """Calculate string similarity score."""
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    def match_entities(self, entity: TechnicalEntity, candidates: List[Tuple[str, TechnicalEntity]]) -> Optional[EntityMatch]:
        """Find best matching entity from candidates."""
        if not candidates:
            return None

        best_match = None
        best_confidence = 0.0

        for canon_id, candidate in candidates:
            factors = []
            total_score = 0.0

            # Name matching
            name_score = 0.0
            entity_name = self._get_entity_name(entity)
            candidate_name = self._get_entity_name(candidate)
            if entity_name and candidate_name:
                name_score = self._calculate_similarity(
                    self._normalize_name(entity_name),
                    self._normalize_name(candidate_name)
                )
            factors.append(MatchFactor(
                name="name", weight=self.FACTORS["name"],
                score=name_score, contribution=name_score * self.FACTORS["name"]
            ))
            total_score += name_score * self.FACTORS["name"]

            # Power matching
            power_score = 0.0
            entity_watts = entity.properties.get("watts") or entity.properties.get("lumens", 0)
            candidate_watts = candidate.properties.get("watts") or candidate.properties.get("lumens", 0)
            if entity_watts and candidate_watts:
                diff = abs(entity_watts - candidate_watts) / max(entity_watts, candidate_watts)
                power_score = max(0, 1 - diff)
            factors.append(MatchFactor(
                name="power", weight=self.FACTORS["power"],
                score=power_score, contribution=power_score * self.FACTORS["power"]
            ))
            total_score += power_score * self.FACTORS["power"]

            # Type matching
            type_score = 1.0 if entity.type == candidate.type else 0.0
            factors.append(MatchFactor(
                name="type", weight=self.FACTORS["type"],
                score=type_score, contribution=type_score * self.FACTORS["type"]
            ))
            total_score += type_score * self.FACTORS["type"]

            # Layer matching
            layer_score = 0.0
            entity_layer = entity.provenance.source_layer or ""
            candidate_layer = candidate.provenance.source_layer or ""
            if entity_layer and candidate_layer:
                layer_score = 1.0 if entity_layer == candidate_layer else 0.5
            factors.append(MatchFactor(
                name="layer", weight=self.FACTORS["layer"],
                score=layer_score, contribution=layer_score * self.FACTORS["layer"]
            ))
            total_score += layer_score * self.FACTORS["layer"]

            # Coordinates (spatial proximity)
            coord_score = 0.0
            entity_coords = entity.coordinates or {}
            candidate_coords = candidate.coordinates or {}
            if entity_coords.get("centroid_x") and candidate_coords.get("centroid_x"):
                coord_score = 1.0  # Simplified - could calculate actual distance
            factors.append(MatchFactor(
                name="coordinates", weight=self.FACTORS["coordinates"],
                score=coord_score, contribution=coord_score * self.FACTORS["coordinates"]
            ))
            total_score += coord_score * self.FACTORS["coordinates"]

            if total_score > best_confidence:
                best_confidence = total_score
                best_match = EntityMatch(
                    canonical_id=canon_id,
                    confidence=total_score,
                    factors=factors
                )

        return best_match

    def _get_entity_name(self, entity: TechnicalEntity) -> str:
        """Extract name/identifier from entity properties."""
        return (entity.properties.get("modelo") or
                entity.properties.get("catalogo") or
                entity.properties.get("id") or
                entity.properties.get("name") or "")