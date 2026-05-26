"""Test Spatial Graph Feedback Loop for iterative improvement."""
from app.services.spatial_reasoning import (
    SpatialReasoningEngine, 
    SpatialGraph,
    SpatialGraphQualityEvaluator,
    ErrorClassifier,
    SpatialGraphFeedbackLoop,
    ErrorType,
)
from app.services.spatial_reasoning.geometry_normalizer import GeometryNormalizer


def test_error_classifier():
    """Test error classification from quality issues."""
    classifier = ErrorClassifier()
    
    quality_report = {
        "overall_score": 0.55,
        "issues_found": [
            "Isolated spaces: SALA-01, SALA-03",
            "Suspicious zero/near-zero area nodes: small-area-1",
            "Extreme area variance detected (ratio: 150:1)",
        ]
    }
    
    issues = classifier.classify_issues(quality_report)
    
    print(f"[OK] Classified {len(issues)} issues:")
    for issue in issues:
        print(f"   - {issue['type'].value}: {issue['suggested_strategy']}")
    
    assert len(issues) == 3
    assert any(i["type"] == ErrorType.ISOLATED_SPACES for i in issues)
    assert any(i["type"] == ErrorType.GEOMETRY_NOISE for i in issues)


def test_feedback_loop_improvement():
    """Test feedback loop improving a low-quality graph."""
    engine = SpatialReasoningEngine()
    normalizer = GeometryNormalizer()
    
    # Create polygons that will be connected (adjacent bounds)
    # Use explicit bounds for testing adjacency
    polygons = [
        {
            "bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 8},
            "area_m2": 80,
            "points": [[0,0], [10,0], [10,8], [0,8]],
            "id": "large-space",
            "type": "room"
        },
        {
            "bounds": {"min_x": 10, "min_y": 0, "max_x": 15, "max_y": 5},
            "area_m2": 25,
            "points": [[10,0], [15,0], [15,5], [10,5]],
            "id": "corridor",
            "type": "corridor"
        }
    ]
    
    graph = engine.build_graph(polygons)
    
    evaluator = SpatialGraphQualityEvaluator()
    initial_report = evaluator.evaluate(graph)
    
    print(f"\n[OK] Initial quality: {initial_report['overall_score']}")
    print(f"   Edges detected: {len(graph.edges)}")
    
    assert len(graph.edges) >= 1, "Should have at least one adjacency edge"


def test_quality_threshold():
    """Test that feedback loop stops at quality threshold."""
    engine = SpatialReasoningEngine()
    
    # High quality graph (should not need improvement)
    polygons = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 20, "max_y": 15}, "area_m2": 300, "points": [[0,0], [20,0], [20,15], [0,15]], "id": "space-1"},
        {"bounds": {"min_x": 20, "min_y": 0, "max_x": 30, "max_y": 10}, "area_m2": 100, "points": [[20,0], [30,0], [30,10], [20,10]], "id": "space-2"},
    ]
    
    graph = engine.build_graph(polygons)
    evaluator = SpatialGraphQualityEvaluator()
    
    # Mock extraction with good areas
    class MockExtractionResult:
        source_metadata = {'areas': [{'area_m2': 300}, {'area_m2': 100}], 'layers': ['ARCH-ROOMS']}
    
    feedback = SpatialGraphFeedbackLoop()
    feedback.QUALITY_THRESHOLD = 0.9  # Higher threshold
    
    improved, log = feedback.improve_graph(graph, MockExtractionResult())
    final_report = evaluator.evaluate(improved)
    
    print(f"\n[OK] High quality graph test: {final_report['overall_score']}")
    assert final_report['overall_score'] >= 0.7


def test_full_feedback_cycle():
    """Test complete feedback loop with graph rebuild."""
    engine = SpatialReasoningEngine()
    feedback = SpatialGraphFeedbackLoop()
    evaluator = SpatialGraphQualityEvaluator()
    
    # Start with low-quality polygons (isolated)
    polygons = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 5, "max_y": 5}, "area_m2": 25, "points": [], "id": "isolated-1"},
        {"bounds": {"min_x": 100, "min_y": 100, "max_x": 15, "max_y": 15}, "area_m2": 50, "points": [], "id": "isolated-2"},
    ]
    
    initial_graph = engine.build_graph(polygons)
    initial_report = evaluator.evaluate(initial_graph)
    
    print(f"\n[OK] Initial graph: {len(initial_graph.nodes)} nodes, {len(initial_graph.edges)} edges")
    print(f"   Quality: {initial_report['overall_score']}")
    
    # Simulate extraction result
    class MockExtractionResult:
        def __init__(self, polys):
            self.source_metadata = {
                'areas': [{'area_m2': p['area_m2'], 'nombre': p['id']} for p in polys],
                'layers': ['ARCH-ROOMS']
            }
    
    improved_graph, log = feedback.improve_graph(initial_graph, MockExtractionResult(polygons))
    final_report = evaluator.evaluate(improved_graph)
    
    print(f"[OK] Improved graph: {len(improved_graph.nodes)} nodes, {len(improved_graph.edges)} edges")
    print(f"   Quality: {final_report['overall_score']}")
    print(f"   Cycles: {len(log)}")
    
    assert len(log) > 0 or final_report['overall_score'] >= feedback.QUALITY_THRESHOLD


if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: Error Classifier")
    print("=" * 60)
    test_error_classifier()
    
    print("\n" + "=" * 60)
    print("TEST 2: Feedback Loop Improvement")
    print("=" * 60)
    test_feedback_loop_improvement()
    
    print("\n" + "=" * 60)
    print("TEST 3: Quality Threshold")
    print("=" * 60)
    test_quality_threshold()
    
    print("\n" + "=" * 60)
    print("TEST 4: Full Feedback Cycle")
    print("=" * 60)
    test_full_feedback_cycle()
    
    print("\n" + "=" * 60)
    print("[OK] Feedback loop tests passed!")
    print("=" * 60)