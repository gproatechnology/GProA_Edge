import asyncio
from app.schemas.technical_entity import (
    TechnicalEntity, Provenance, EntityType, EntityStatus, AdjudicationStatus
)
from app.services.truth_arbitrator import arbitrator

def test_truth_arbitration():
    print("Testing Truth Arbitration Layer (TAL v1.0)...")
    
    uid = "LUM-TEST-001"
    
    # Version A: CONFIRMED (CAD)
    v_cad = TechnicalEntity(
        uid=uid,
        type=EntityType.LUMINAIRE,
        status=EntityStatus.CONFIRMED,
        provenance=Provenance(
            source_file="layout.dxf",
            parser_used="cad_parser",
            extraction_method="geometry"
        ),
        properties={"area": "Production", "watts": 100}
    )
    
    # Version B: INFERRED (PDF)
    v_pdf = TechnicalEntity(
        uid=uid,
        type=EntityType.LUMINAIRE,
        status=EntityStatus.INFERRED,
        provenance=Provenance(
            source_file="spec.pdf",
            parser_used="pdf_parser",
            extraction_method="ai_specialized"
        ),
        properties={"area": "Warehouse", "watts": 120} # Conflict!
    )
    
    # Run Arbitration
    winner = arbitrator.arbitrate(uid, [v_cad, v_pdf])
    
    print(f"Decision: {winner.adjudication.decision}")
    print(f"Winner Source: {winner.adjudication.winning_source}")
    print(f"Logic: {winner.adjudication.logic_applied}")
    
    assert winner.adjudication.decision == AdjudicationStatus.ADJUDICATED
    assert winner.provenance.source_file == "layout.dxf"
    assert winner.status == EntityStatus.CONFIRMED
    
    print("\n✅ TAL v1.0 Verification Passed: Source Dominance (FACT > INFERENCE) worked.")

if __name__ == "__main__":
    test_truth_arbitration()
