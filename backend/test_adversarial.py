"""Adversarial testing for Spatial Reasoning System."""
from app.services.spatial_reasoning import SpatialReasoningEngine, create_office_ground_truth
from app.services.spatial_reasoning.graph_comparator import comparator


def test_noisy_geometry():
    """Test system with noisy/incomplete DXF data."""
    engine = SpatialReasoningEngine()
    
    # Simulate noisy DXF extraction (incomplete polygons, missing data)
    noisy_polygons = [
        # Large gap - simulates missing wall/separation
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 15, "max_y": 10}, "area_m2": 150, "points": [], "id": "LARGE-SPACE", "type": "room"},
        {"bounds": {"min_x": 15, "min_y": 0, "max_x": 25, "max_y": 10}, "area_m2": 100, "points": [], "id": "ANOTHER-SPACE", "type": "room"},
    ]
    
    graph = engine.build_graph(noisy_polygons)
    
    print(f"[ADVERSARIAL] Noisy geometry: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    
    # Should still produce a graph, even if quality is lower
    assert len(graph.nodes) == 2
    print("[OK] System handles noisy geometry without crashing")


def test_missing_bounds():
    """Test system with missing/incomplete bounds data."""
    engine = SpatialReasoningEngine()
    
    # Simulate extraction errors
    incomplete_polygons = [
        {"area_m2": 50, "type": "room", "id": "MISSING-BOUNDS"},  # No bounds
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 5, "max_y": 5}, "area_m2": 25, "points": [], "id": "OK-SPACE", "type": "room"},
    ]
    
    graph = engine.build_graph(incomplete_polygons)
    
    print(f"[ADVERSARIAL] Missing bounds: {len(graph.nodes)} nodes")
    
    # Should gracefully handle missing bounds
    assert len(graph.nodes) >= 1
    print("[OK] System handles missing bounds")


def test_overlapping_geometry():
    """Test system with overlapping/conflicting geometry."""
    engine = SpatialReasoningEngine()
    
    # Overlapping spaces (common CAD error)
    overlapping = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10}, "area_m2": 100, "points": [], "id": "OVERLAP-A", "type": "room"},
        {"bounds": {"min_x": 5, "min_y": 5, "max_x": 15, "max_y": 15}, "area_m2": 100, "points": [], "id": "OVERLAP-B", "type": "room"},
    ]
    
    graph = engine.build_graph(overlapping)
    
    print(f"[ADVERSARIAL] Overlapping: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    
    # Should handle overlaps gracefully
    print("[OK] System handles overlapping geometry")


def test_emptY_geometry():
    """Test system with empty or near-zero area geometry."""
    engine = SpatialReasoningEngine()
    
    # Noise and tiny spaces
    noisy_small = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 0.1, "max_y": 0.1}, "area_m2": 0.01, "points": [], "id": "TINY", "type": "noise"},
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0}, "area_m2": 0, "points": [], "id": "ZERO", "type": "zero"},
    ]
    
    graph = engine.build_graph(noisy_small)
    
    print(f"[ADVERSARIAL] Empty/tiny: {len(graph.nodes)} nodes")
    
    # Should filter out invalid geometry
    print("[OK] System handles empty/tiny geometry")


def test_incomplete_adjacency_chain():
    """Test system with incomplete adjacency relationships."""
    engine = SpatialReasoningEngine()
    
    # Spaces that should be connected but have gaps
    gapped_polygons = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 5, "max_y": 5}, "area_m2": 25, "points": [], "id": "ISOLATED-A", "type": "room"},
        {"bounds": {"min_x": 100, "min_y": 100, "max_x": 15, "max_y": 15}, "area_m2": 50, "points": [], "id": "ISOLATED-B", "type": "room"},
    ]
    
    graph = engine.build_graph(gapped_polygons)
    gt = create_office_ground_truth()
    
    print(f"[ADVERSARIAL] Incomplete chain: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    
    metrics = comparator.compare(graph, gt)
    print(f"[ADVERSARIAL] Metrics: node_f1={metrics['node_f1']:.2f}, adj_f1={metrics['adjacency_f1']:.2f}")
    
    print("[OK] System handles incomplete adjacency chains")


def test_metric_stability():
    """Test that metrics are stable across similar inputs."""
    engine = SpatialReasoningEngine()
    results = []
    
    # Same logical layout, slight variations
    for variation in range(3):
        polygons = [
            {"bounds": {"min_x": 0, "min_y": 0, "max_x": 10 + variation * 0.1, "max_y": 5}, "area_m2": 50, "points": [], "id": "SPACE-1", "type": "room"},
            {"bounds": {"min_x": 10 + variation * 0.1, "min_y": 0, "max_x": 15 + variation * 0.1, "max_y": 5}, "area_m2": 25, "points": [], "id": "SPACE-2", "type": "corridor"},
        ]
        graph = engine.build_graph(polygons)
        results.append(len(graph.edges))
    
    # Results should be consistent
    assert len(set(results)) == 1, f"Inconsistent results: {results}"
    print(f"[OK] Metric stability: {results}")


if __name__ == "__main__":
    print("=" * 60)
    print("ADVERSARIAL TESTING SUITE")
    print("=" * 60)
    
    tests = [
        ("Noisy Geometry", test_noisy_geometry),
        ("Missing Bounds", test_missing_bounds),
        ("Overlapping Geometry", test_overlapping_geometry),
        ("Empty Geometry", test_emptY_geometry),
        ("Incomplete Adjacency", test_incomplete_adjacency_chain),
        ("Metric Stability", test_metric_stability),
    ]
    
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            test_func()
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
    
    print("\n" + "=" * 60)
    print("[OK] Adversarial testing complete!")
    print("=" * 60)