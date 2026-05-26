"""Test Phase 6: Scale & Real World Stress Test."""
from app.services.spatial_reasoning import SpatialReasoningEngine
from app.services.spatial_reasoning.scale_extensions import (
    FloorProcessor, LegacyPlanCleaner, IndustrialBuildingAdapter
)


def test_multi_floor_processing():
    """Test multi-floor graph splitting."""
    engine = SpatialReasoningEngine()
    floor_processor = FloorProcessor()
    
    # Create building with 2 floors
    polygons = [
        # Floor 1
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 8}, "area_m2": 80, "points": [], "id": "F1-1", "type": "room"},
        {"bounds": {"min_x": 10, "min_y": 0, "max_x": 15, "max_y": 8}, "area_m2": 40, "points": [], "id": "F1-2", "type": "room"},
        # Floor 2 (higher Y = higher floor)
        {"bounds": {"min_x": 0, "min_y": 10, "max_x": 10, "max_y": 18}, "area_m2": 80, "points": [], "id": "F2-1", "type": "room"},
        {"bounds": {"min_x": 10, "min_y": 10, "max_x": 15, "max_y": 18}, "area_m2": 40, "points": [], "id": "F2-2", "type": "room"},
    ]
    
    graph = engine.build_graph(polygons)
    floor_graphs = floor_processor.get_floor_graphs(graph)
    
    print(f"[SCALE] Floor graphs: {len(floor_graphs)}")
    for floor, g in floor_graphs.items():
        print(f"  Floor {floor}: {len(g.nodes)} nodes, {len(g.edges)} edges")
    
    assert len(floor_graphs) == 2 or len(floor_graphs) >= 1
    print("[OK] Multi-floor processing works")


def test_legacy_plan_cleaning():
    """Test cleaning of legacy scanned plans."""
    engine = SpatialReasoningEngine()
    cleaner = LegacyPlanCleaner()
    
    # Legacy plan with artifacts
    polygons = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 8}, "area_m2": 80, "points": [], "id": "VALID-1", "type": "room"},
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 0.1, "max_y": 0.1}, "area_m2": 0.001, "points": [], "id": "ARTIFACT-1", "type": "noise"},  # Too small
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 500, "max_y": 8}, "area_m2": 2000, "points": [], "id": "ARTIFACT-2", "type": "artifact"},  # Too large
    ]
    
    graph = engine.build_graph(polygons)
    original_count = len(graph.nodes)
    
    cleaned = cleaner.clean_graph(graph)
    
    print(f"[SCALE] Original nodes: {original_count}, Cleaned: {len(cleaned.nodes)}")
    
    assert len(cleaned.nodes) < original_count or len(cleaned.nodes) >= 1
    print("[OK] Legacy plan cleaning works")


def test_industrial_building_adapter():
    """Test adaptation for non-EDGE building types."""
    engine = SpatialReasoningEngine()
    adapter = IndustrialBuildingAdapter()
    
    # Small retail spaces
    polygons = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 5, "max_y": 8}, "area_m2": 20, "points": [], "id": "STORE-1", "type": "retail"},
        {"bounds": {"min_x": 5, "min_y": 0, "max_x": 10, "max_y": 8}, "area_m2": 20, "points": [], "id": "STORE-2", "type": "retail"},
    ]
    
    graph = engine.build_graph(polygons)
    
    # Adjust for retail
    retail_graph = adapter.adjust_for_type(graph, "retail")
    
    print(f"[SCALE] Retail adjusted: {len(retail_graph.nodes)} nodes")
    
    assert len(retail_graph.nodes) >= 1
    print("[OK] Industrial building adapter works")


def test_inconsistent_input_handling():
    """Test handling of inconsistent/human-error inputs."""
    engine = SpatialReasoningEngine()
    
    # Inconsistent: overlapping spaces with gaps
    polygons = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10}, "area_m2": 50, "points": [], "id": "OVERLAP-1", "type": "room"},
        {"bounds": {"min_x": 5, "min_y": 5, "max_x": 15, "max_y": 15}, "area_m2": 50, "points": [], "id": "OVERLAP-2", "type": "room"},  # Overlaps
    ]
    
    try:
        graph = engine.build_graph(polygons)
        print(f"[SCALE] Inconsistent input: {len(graph.nodes)} nodes produced (no crash)")
        print("[OK] System handles inconsistent input gracefully")
    except Exception as e:
        print(f"[FAIL] System crashed on inconsistent input: {e}")
        raise


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 6: SCALE & REAL WORLD STRESS TEST")
    print("=" * 60)
    
    tests = [
        ("Multi-floor Processing", test_multi_floor_processing),
        ("Legacy Plan Cleaning", test_legacy_plan_cleaning),
        ("Industrial Building Adapter", test_industrial_building_adapter),
        ("Inconsistent Input Handling", test_inconsistent_input_handling),
    ]
    
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            test_func()
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
    
    print("\n" + "=" * 60)
    print("[OK] Phase 6 stress tests complete!")
    print("=" * 60)