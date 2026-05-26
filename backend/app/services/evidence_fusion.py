"""
Cross-Document Evidence Fusion Layer for EOSIS Edge v1.0.
Consolidates evidence from multiple sources (PDF, CAD, Excel) for the same entities.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FusionStrategy(str, Enum):
    """How to handle conflicting evidence."""
    FIRST_WINS = "first_wins"
    HIGHEST_CONFIDENCE = "highest_confidence"
    MOST_COMPLETE = "most_complete"


@dataclass
class ConsolidatedEntity:
    """Entity consolidated from multiple sources."""
    uid: str
    primary_entity: Dict[str, Any]
    source_entities: List[Dict[str, Any]]
    confidence: float
    fusion_strategy: str
    evidence_count: int


class EvidenceFusion:
    """
    Fuses evidence from multiple documents for the same entities.
    
    Example:
        PDF: "LED 120W"
        Ficha: "120 watts"  
        Plano: símbolo luminaria
        → misma entidad consolidada con múltiples fuentes de evidencia
    """
    
    # Similarity thresholds for entity matching
    NAME_SIMILARITY_THRESHOLD = 0.8
    VALUE_TOLERANCE = 0.10  # 10% tolerance for numeric values
    
    @classmethod
    def fusion_key(cls, entity: Dict[str, Any]) -> Optional[str]:
        """
        Generate a key for entity matching.
        
        Uses type, normalized name, and approximate value.
        """
        props = entity.get("properties", {})
        entity_type = entity.get("type", "")
        
        # Get name identifier
        name = props.get("nombre") or props.get("name") or ""
        name = cls._normalize_name(name)
        
        # Get area value if present
        area = props.get("area_m2")
        
        # Create key
        if area:
            area_bucket = round(area, -1)  # Round to nearest 10
            return f"{entity_type}|{name}|{area_bucket}"
        
        return f"{entity_type}|{name}"
    
    @classmethod
    def _normalize_name(cls, name: str) -> str:
        """Normalize entity name for matching."""
        if not name:
            return ""
        import re
        name = name.lower()
        name = re.sub(r'[^a-z0-9\s]', ' ', name)
        name = ' '.join(name.split())
        return name.strip()
    
    @classmethod
    def consolidate_entities(
        cls, 
        entities_by_source: Dict[str, List[Dict[str, Any]]],
        strategy: FusionStrategy = FusionStrategy.HIGHEST_CONFIDENCE
    ) -> List[ConsolidatedEntity]:
        """
        Consolidate entities from multiple sources.
        
        Args:
            entities_by_source: Dict mapping source name to list of entities
            strategy: How to handle conflicts between entities
            
        Returns:
            List of ConsolidatedEntity objects
        """
        # Flatten all entities with source tracking
        all_entities = []
        for source, entities in entities_by_source.items():
            for entity in entities:
                all_entities.append((source, entity))
        
        # Group by fusion key
        groups = {}
        for source, entity in all_entities:
            key = cls.fusion_key(entity)
            if key:
                if key not in groups:
                    groups[key] = []
                groups[key].append((source, entity))
        
        # Consolidate each group
        consolidated = []
        for key, group in groups.items():
            if len(group) == 1:
                source, entity = group[0]
                consolidated.append(ConsolidatedEntity(
                    uid=entity.get("uid", "unknown"),
                    primary_entity=entity,
                    source_entities=[{"source": source, "entity": entity}],
                    confidence=entity.get("confidence", 0.5),
                    fusion_strategy="single_source",
                    evidence_count=1
                ))
            else:
                # Multiple sources - consolidate
                consolidated.append(
                    cls._consolidate_group(group, strategy)
                )
        
        return consolidated
    
    @classmethod
    def _consolidate_group(
        cls, 
        group: List[Tuple[str, Dict[str, Any]]],
        strategy: FusionStrategy
    ) -> ConsolidatedEntity:
        """Consolidate a group of matching entities."""
        sources_entities = [
            {"source": src, "entity": ent} for src, ent in group
        ]
        
        # Select primary based on strategy
        if strategy == FusionStrategy.FIRST_WINS:
            primary = group[0][1]
        elif strategy == FusionStrategy.HIGHEST_CONFIDENCE:
            primary = max(group, key=lambda x: x[1].get("confidence", 0))[1]
        else:  # MOST_COMPLETE
            primary = max(group, key=lambda x: len(x[1].get("properties", {})))[1]
        
        # Calculate combined confidence
        confidences = [e.get("confidence", 0.5) for _, e in group]
        combined_confidence = min(1.0, sum(confidences) / len(confidences) * 1.1)
        
        return ConsolidatedEntity(
            uid=primary.get("uid", "unknown"),
            primary_entity=primary,
            source_entities=sources_entities,
            confidence=combined_confidence,
            fusion_strategy=strategy.value,
            evidence_count=len(group)
        )
    
    @classmethod
    def to_export_format(
        cls, 
        consolidated: ConsolidatedEntity
    ) -> Dict[str, Any]:
        """Convert ConsolidatedEntity to export format."""
        entity = consolidated.primary_entity.copy()
        
        entity["_fusion"] = {
            "strategy": consolidated.fusion_strategy,
            "evidence_count": consolidated.evidence_count,
            "sources": [
                {"source": src_ent["source"], "uid": src_ent["entity"].get("uid")}
                for src_ent in consolidated.source_entities
            ]
        }
        
        return entity


fusion = EvidenceFusion()