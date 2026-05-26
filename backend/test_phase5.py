"""Test Phase 5 integration without affecting Spatial Core."""
from app.services.spatial_reasoning import (
    SpatialReasoningEngine,
    create_office_ground_truth,
    comparator,
)
from app.services.edge_strategy_mapper import EDGEStraategyMapper
from app.services.spatial_reasoning.quality_evaluator import SpatialGraphQualityEvaluator


def test_edge_mapping_no_regression():
    """Test that EDGE mapping doesn't affect spatial core metrics."""
    engine = SpatialReasoningEngine()
    mapper = EDGEStraategyMapper()
    
    # Build a graph
    polygons = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 5}, "area_m2": 50.0, "points": [], "id": "SALA-01", "type": "office"},
        {"bounds": {"min_x": 10, "min_y": 0, "max_x": 15, "max_y": 5}, "area_m2": 25.0, "points": [], "id": "CORRIDOR-01", "type": "corridor"},
    ]
    
    graph = engine.build_graph(polygons)
    gt = create_office_ground_truth()
    
    # Evaluate BEFORE any EDGE mapping
    before_metrics = comparator.compare(graph, gt)
    before_quality = SpatialGraphQualityEvaluator().evaluate(graph)
    
    # Run EDGE mapping (should NOT modify graph)
    edge_result = mapper.map_spatial_graph(graph)
    
    # Evaluate AFTER (should be identical)
    after_metrics = comparator.compare(graph, gt)
    after_quality = SpatialGraphQualityEvaluator().evaluate(graph)
    
    print("BEFORE EDGE mapping:")
    print(f"  Node F1: {before_metrics['node_f1']}, Adj F1: {before_metrics['adjacency_f1']}")
    print(f"  Quality: {before_quality['overall_score']}")
    
    print("\nAFTER EDGE mapping:")
    print(f"  Node F1: {after_metrics['node_f1']}, Adj F1: {after_metrics['adjacency_f1']}")
    print(f"  Quality: {after_quality['overall_score']}")
    
    print(f"\nEDGE strategies: {edge_result['strategies']}")
    
    # Verify no regression
    assert before_metrics['node_f1'] == after_metrics['node_f1'], "Node F1 changed!"
    assert before_quality['overall_score'] == after_quality['overall_score'], "Quality changed!"
    
    print("\n[OK] No regression - Spatial Core preserved!")


def test_full_phase5_pipeline():
    """Test complete Phase 5 pipeline."""
    engine = SpatialReasoningEngine()
    mapper = EDGEStraategyMapper()
    
    polygons = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 5}, "area_m2": 50.0, "points": [], "id": "SALA-01", "type": "office"},
        {"bounds": {"min_x": 10, "min_y": 0, "max_x": 15, "max_y": 5}, "area_m2": 25.0, "points": [], "id": "CORRIDOR-01", "type": "corridor"},
    ]
    
    graph = engine.build_graph(polygons)
    
    # Spatial core delivers graph
    summary = {
        "nodes": len(graph.nodes),
        "edges": len(graph.edges),
        "node_types": [n.node_type.value for n in graph.nodes]
    }
    print(f"\nSpatial Graph: {summary}")
    
    # EDGE mapper consumes graph (read-only)
    edge_result = mapper.map_spatial_graph(graph)
    print(f"EDGE strategies: {edge_result['strategies']}")
    print(f"Spaces for EDesign: {len(edge_result['spaces_for_edesign'])}")
    
    assert "strategies" in edge_result
    assert "spaces_for_edesign" in edge_result


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 5: NO REGRESSION TEST")
    print("=" * 60)
    test_edge_mapping_no_regression()
    
    print("\n" + "=" * 60)
    print("PHASE 5: FULL PIPELINE TEST")
    print("=" * 60)
    test_full_phase5_pipeline()
    
    print("\n[OK] Phase 5 integration tests passed!")