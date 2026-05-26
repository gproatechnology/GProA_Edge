"""
Truth Arbitration Service (TAL v1.0) for EOSIS Edge.
Resolves conflicts between competing technical realities using source dominance policies.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.schemas.technical_entity import (
    TechnicalEntity, EntityStatus, AdjudicationStatus, ArbitrationResult
)

logger = logging.getLogger(__name__)

class TruthArbitrator:
    """
    Deterministic judge of technical truth.
    Implements Source Dominance: FACT (CAD) > INFERENCE (PDF) > HYPOTHETICAL (AI).
    """
    
    # Priority mapping for EntityStatus (Lower is higher priority/more dominant)
    STATUS_PRIORITY = {
        EntityStatus.CONFIRMED: 1,
        EntityStatus.INFERRED: 2,
        EntityStatus.INCOMPLETE: 3,
        EntityStatus.CONTRADICTORY: 4
    }
    
    @classmethod
    def arbitrate(cls, uid: str, versions: List[TechnicalEntity]) -> TechnicalEntity:
        """
        Choose the best version of reality for a given entity UID.
        """
        if not versions:
            raise ValueError(f"No versions provided for arbitration of {uid}")
            
        if len(versions) == 1:
            # Automatic adjudication for single source
            winner = versions[0]
            winner.adjudication = ArbitrationResult(
                decision=AdjudicationStatus.ADJUDICATED,
                winning_source=winner.provenance.source_file,
                dominant_status=winner.status,
                logic_applied="Single source auto-adjudication"
            )
            return winner

        # 1. Sort by Status Priority and then by Confidence
        # Higher status priority (lower number) wins first. 
        # If tied, higher confidence wins.
        sorted_versions = sorted(
            versions, 
            key=lambda x: (cls.STATUS_PRIORITY.get(x.status, 99), -x.confidence)
        )
        
        winner = sorted_versions[0]
        others = sorted_versions[1:]
        
        # 2. Conflict Detection
        # Check if the winner and the next best version have same priority but different properties
        # This indicates an AMBIGUITY that needs manual review.
        if len(sorted_versions) > 1:
            next_best = sorted_versions[1]
            if cls.STATUS_PRIORITY.get(winner.status) == cls.STATUS_PRIORITY.get(next_best.status):
                # If they have different critical properties, mark as AMBIGUOUS
                if winner.properties != next_best.properties:
                    logger.warning(f"TAL conflict detected for {uid} between {winner.provenance.source_file} and {next_best.provenance.source_file}")
                    winner.status = EntityStatus.CONTRADICTORY
                    winner.adjudication = ArbitrationResult(
                        decision=AdjudicationStatus.AMBIGUOUS,
                        winning_source="None",
                        dominant_status=EntityStatus.CONTRADICTORY,
                        rejected_sources=[v.provenance.source_file for v in versions],
                        logic_applied="Conflicting sources with equal priority"
                    )
                    return winner

        # 3. Successful Adjudication
        winner.adjudication = ArbitrationResult(
            decision=AdjudicationStatus.ADJUDICATED,
            winning_source=winner.provenance.source_file,
            dominant_status=winner.status,
            rejected_sources=[v.provenance.source_file for v in others],
            logic_applied=f"Source dominance: {winner.status.value} (conf={winner.confidence}) prevails"
        )
        
        return winner

    @classmethod
    def adjudicate_all(cls, entities: List[TechnicalEntity]) -> List[TechnicalEntity]:
        """Group entities by UID and arbitrate conflicts."""
        from collections import defaultdict
        grouped = defaultdict(list)
        for e in entities:
            grouped[e.uid].append(e)
            
        adjudicated = []
        for uid, versions in grouped.items():
            adjudicated.append(cls.arbitrate(uid, versions))
            
        return adjudicated

# Singleton
arbitrator = TruthArbitrator()
