"""Test Spatial Truth Validation Layer."""
from app.services.spatial_reasoning import (
    SpatialReasoningEngine,
    SpatialGraphQualityEvaluator,
    GroundTruthDataset,
    create_office_ground_truth,
    SpatialGraphComparator,
    comparator,
)


def test_ground_truth_dataset():
    """Test ground truth dataset creation."""
    gt = create_office_ground_truth()
    
    print(f"[OK] Ground truth created: {gt.plan_id}")
    print(f"   Spaces: {len(gt.spaces)}")
    for space in gt.spaces:
        print(f"   - {space.id}: {space.expected_area_m2}m2, adjacencies: {space.expected_adjacencies}")
    
    assert len(gt.spaces) == 3
    assert gt.get_expected_adjacency_pairs() is not None


def test_graph_comparator():
    """Test graph comparison against ground truth."""
    engine = SpatialReasoningEngine()
    
    # Create predicted graph matching ground truth layout
    polygons = [
        {
            "bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 5},
            "area_m2": 50.0,
            "points": [[0,0], [10,0], [10,5], [0,5]],
            "id": "SALA-01",
            "type": "office"
        },
        {
            "bounds": {"min_x": 10, "min_y": 0, "max_x": 15, "max_y": 5},
            "area_m2": 20.0,
            "points": [[10,0], [15,0], [15,5], [10,5]],
            "id": "CORRIDOR-01",
            "type": "corridor"
        },
        {
            "bounds": {"min_x": 15, "min_y": 0, "max_x": 20, "max_y": 4},
            "area_m2": 8.0,
            "points": [[15,0], [20,0], [20,4], [15,4]],
            "id": "WC-01",
            "type": "service"
        }
    ]
    
    predicted_graph = engine.build_graph(polygons)
    gt = create_office_ground_truth()
    
    print(f"\n[OK] Predicted graph: {len(predicted_graph.nodes)} nodes, {len(predicted_graph.edges)} edges")
    
    # Compare against ground truth
    metrics = comparator.compare(predicted_graph, gt)
    
    print(f"[OK] Comparison metrics:")
    print(f"   Node F1: {metrics['node_f1']}")
    print(f"   Adjacency F1: {metrics['adjacency_f1']}")
    print(f"   Geometry error: {metrics['geometry_error_m2']}m2")
    print(f"   Overall accuracy: {metrics['overall_accuracy']}")
    
    assert metrics['node_f1'] >= 0.5
    assert metrics['overall_accuracy'] >= 0.5


def test_feedback_loop_with_ground_truth():
    """Test that feedback loop optimizes against ground truth."""
    from app.services.spatial_reasoning.feedback_loop import SpatialGraphFeedbackLoop
    
    engine = SpatialReasoningEngine()
    
    # Create a graph with missing adjacency
    polygons = [
        {
            "bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 5},
            "area_m2": 50.0,
            "points": [],
            "id": "SALA-01",
            "type": "office"
        },
        {
            "bounds": {"min_x": 10, "min_y": 0, "max_x": 15, "max_y": 5},  # Should touch first
            "area_m2": 20.0,
            "points": [],
            "id": "CORRIDOR-01",
            "type": "corridor"
        }
    ]
    
    initial_graph = engine.build_graph(polygons)
    gt = create_office_ground_truth()
    
    initial_metrics = comparator.compare(initial_graph, gt)
    print(f"\n[OK] Initial accuracy: {initial_metrics['overall_accuracy']}")
    
    # The feedback loop should help improve adjacency detection
    feedback = SpatialGraphFeedbackLoop()
    improved_graph, _ = feedback.improve_graph(initial_graph)
    
    final_metrics = comparator.compare(improved_graph, gt)
    print(f"[OK] Final accuracy: {final_metrics['overall_accuracy']}")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: Ground Truth Dataset")
    print("=" * 60)
    test_ground_truth_dataset()
    
    print("\n" + "=" * 60)
    print("TEST 2: Graph Comparator")
    print("=" * 60)
    test_graph_comparator()
    
    print("\n" + "=" * 60)
    print("TEST 3: Feedback Loop with Ground Truth")
    print("=" * 60)
    test_feedback_loop_with_ground_truth()
    
    print("\n" + "=" * 60)
    print("[OK] Truth validation tests passed!")
    print("=" * 60)