from app.schemas.technical_entity import TechnicalEntity, Provenance, EntityType, MeasureType, Discipline, SCHEMA_VERSION

def test_unified_contract():
    print(f"Testing Unified Entity Contract v{SCHEMA_VERSION}...")
    
    prov = Provenance(
        source_file="test.pdf",
        parser_used="test_parser",
        extraction_method="manual"
    )
    
    # Test 1: New uid field
    e1 = TechnicalEntity(
        uid="LUM-001",
        type=EntityType.LUMINAIRE,
        provenance=prov,
        properties={"watts": 100}
    )
    assert e1.uid == "LUM-001"
    assert e1.schema_version == "1.0"
    print("✅ Test 1: Direct uid assignment passed.")
    
    # Test 2: Legacy entity_id alias
    e2 = TechnicalEntity(
        entity_id="LUM-002",
        type=EntityType.LUMINAIRE,
        provenance=prov,
        properties={"watts": 150}
    )
    assert e2.uid == "LUM-002"
    print("✅ Test 2: entity_id alias passed.")
    
    # Test 3: Legacy 'id' field handling
    e3 = TechnicalEntity(
        id="LUM-003",
        type=EntityType.LUMINAIRE,
        provenance=prov,
        properties={"watts": 200}
    )
    assert e3.uid == "LUM-003"
    print("✅ Test 3: Legacy 'id' field migration passed.")
    
    # Test 4: Auto-generation of UID
    e4 = TechnicalEntity(
        type=EntityType.AREA,
        provenance=prov,
        properties={"name": "Production Area", "area_m2": 500}
    )
    assert e4.uid.startswith("ARE-")
    print(f"✅ Test 4: Auto-generation passed (Generated UID: {e4.uid})")
    
    print("\n🚀 All Contract v1.0 Tests Passed!")

if __name__ == "__main__":
    try:
        test_unified_contract()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
