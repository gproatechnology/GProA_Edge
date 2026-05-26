"""
Entity Builder service - The Single Gate for TechnicalEntity construction.
Implements GPT Point 9: Parsers propose, Builder constructs.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.schemas.technical_entity import (
    TechnicalEntity, RawDataProposal, EntityType, MeasureType, Discipline, SCHEMA_VERSION
)
from app.services.semantic_id import id_generator


logger = logging.getLogger(__name__)


class EntityBuilder:
    """
    Centralized gatekeeper for technical entities.
    Ensures all entities meet contract requirements and maintain immutability.
    """
    
    @staticmethod
    def build(proposal: RawDataProposal) -> TechnicalEntity:
        """
        Construct a TechnicalEntity from a RawDataProposal.
        This is the ONLY way to create a valid TechnicalEntity in the system.
        """
        # 1. Determine Measure and Discipline if not provided
        measure = proposal.measure or MeasureType.GENERAL
        discipline = proposal.discipline or Discipline.DESIGN
        
        # 2. Generate Semantic UID
        type_val = proposal.type.value if hasattr(proposal.type, 'value') else proposal.type
        uid = id_generator.generate(type_val, proposal.properties)
        
        # 3. Build semantic_metadata from evidence
        semantic_metadata = {}
        if proposal.semantic_evidence:
            semantic_metadata["semantic_evidence"] = proposal.semantic_evidence
            # Propagate confidence adjustment from evidence
            evidence_conf = proposal.semantic_evidence.get("confidence", 1.0)
            # Degrade confidence if evidence suggests low trust
            if proposal.semantic_evidence.get("candidate_type") in ["dimension", "global_area"]:
                # Evidence suggests this may not be a real space
                pass  # TAL will use this
        
        # 4. Construct the Immutable Entity with Schema Versioning (GPT Point 8)
        entity = TechnicalEntity(
            uid=uid,
            type=proposal.type,
            measure=measure,
            discipline=discipline,
            provenance=proposal.provenance,
            coordinates=proposal.coordinates,
            properties=proposal.properties,
            confidence=proposal.confidence,
            schema_version=SCHEMA_VERSION,
            semantic_metadata=semantic_metadata,
            processing_history=[{
                "action": "constructed",
                "timestamp": datetime.utcnow().isoformat(),
                "gatekeeper": "EntityBuilder_v1.0",
                "schema": SCHEMA_VERSION
            }]
        )
        
        logger.debug(f"Entity constructed: {uid} type={proposal.type.value} [v{SCHEMA_VERSION}]")
        return entity
    
    @classmethod
    def build_batch(cls, proposals: List[RawDataProposal]) -> List[TechnicalEntity]:
        """Process a batch of proposals."""
        return [cls.build(p) for p in proposals]


# Singleton instance
builder = EntityBuilder()
