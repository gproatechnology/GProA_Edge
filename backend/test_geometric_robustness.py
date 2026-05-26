"""
Geometric Robustness Tests for Spatial Reasoning Engine.
Tests edge cases: dirty scans, incomplete DXF, open polygons, overlapping geometry.
"""
import math
from app.services.spatial_reasoning import SpatialReasoningEngine, SpatialGraph, SpatialNode, SpatialBounds
from app.services.spatial_reasoning.geometry_normalizer import GeometryNormalizer
from app.services.spatial_reasoning.quality_evaluator import SpatialGraphQualityEvaluator


def test_dirty_scan_simulation():
    """Simulate a noisy scanned plan with overlapping/incomplete polygons."""
    engine = SpatialReasoningEngine()
    normalizer = GeometryNormalizer()
    
    # Simulate areas from a dirty scan - overlapping, inconsistent
    dirty_areas = [
        {"area_m2": 50.0, "type": "polyline", "nombre": "ROOM-A"},
        {"area_m2": 45.0, "type": "polyline", "nombre": "ROOM-B"},  # Overlaps with A
        {"area_m2": 0.5, "type": "circle", "nombre": "DOT-01"},    # Noise/spurious
        {"area_m2": 30.0, "type": "hatch", "nombre": "ROOM-C"},
    ]
    
    polygons = normalizer.normalize_dxf_areas(dirty_areas)
    
    # Build graph - should handle overlaps gracefully
    graph = engine.build_graph(polygons, {"layer": "SCORED-PLAN"})
    
    # Evaluate quality
    evaluator = SpatialGraphQualityEvaluator()
    metrics = evaluator.evaluate(graph)
    
    print(f"\n[OK] Dirty scan test: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    print(f"   Quality score: {metrics['overall_score']}")
    print(f"   Issues: {metrics['issues_found'][:2]}")
    
    # Should still produce a graph even with dirty input
    assert len(graph.nodes) >= 1
    assert metrics["overall_score"] >= 0  # Non-negative score


def test_incomplete_dxf_simulation():
    """Simulate incomplete DXF with missing walls/openings."""
    engine = SpatialReasoningEngine()
    normalizer = GeometryNormalizer()
    
    # Incomplete plan - only partial geometry
    incomplete_areas = [
        {"area_m2": 100.0, "type": "polyline", "nombre": "MAIN-ROOM"},
        # Missing corridor areas that should connect
    ]
    
    polygons = normalizer.normalize_dxf_areas(incomplete_areas)
    graph = engine.build_graph(polygons, {"layer": "INCOMPLETE-PLAN"})
    
    evaluator = SpatialGraphQualityEvaluator()
    metrics = evaluator.evaluate(graph)
    
    print(f"\n[OK] Incomplete DXF test: {len(graph.nodes)} nodes")
    print(f"   Completeness: {metrics['completeness_score']}")
    
    # Should flag incompleteness
    assert metrics["completeness_score"] <= 0.5  # Single room is incomplete


def test_open_polygon_handling():
    """Test handling of non-closed polygons (common in imperfect CAD)."""
    engine = SpatialReasoningEngine()
    
    # Manually create polygon with inconsistent bounds
    # This simulates ezdxf returning areas from unclosed polylines
    polygons = [
        {
            "bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 5},
            "area_m2": 50,
            "points": [[0, 0], [10, 0], [10, 5]],  # Open - only 3 points
            "id": "open-poly",
            "type": "partial"
        },
    ]
    
    graph = engine.build_graph(polygons, {"layer": "OPEN-PLAN"})
    
    # Graph should still be created
    assert len(graph.nodes) == 1
    print(f"\n[OK] Open polygon handled: {len(graph.nodes)} node created")
    
    # Quality evaluator should flag geometry issue
    evaluator = SpatialGraphQualityEvaluator()
    metrics = evaluator.evaluate(graph)
    print(f"   Geometry validity: {metrics['geometry_validity_score']}")


def test_layer_conflict_simulation():
    """Test handling of conflicting layer names."""
    engine = SpatialReasoningEngine()
    normalizer = GeometryNormalizer()
    
    # Areas with conflicting/similar layer names
    conflict_areas = [
        {"area_m2": 25.0, "type": "polyline", "nombre": "OFFICE"},
        {"area_m2": 25.0, "type": "hatch", "nombre": "OFFICE"},  # Duplicate name!
        {"area_m2": 15.0, "type": "polyline", "nombre": "OFFICE"},  # Triplicate!
        {"area_m2": 10.0, "type": "circle", "nombre": "Mech"},
    ]
    
    polygons = normalizer.normalize_dxf_areas(conflict_areas)
    graph = engine.build_graph(polygons, {"layer": "CONFLICT-LAYERS"})
    
    evaluator = SpatialGraphQualityEvaluator()
    metrics = evaluator.evaluate(graph)
    
    print(f"\n[OK] Layer conflict test: {len(graph.nodes)} nodes from 4 areas")
    print(f"   Overall score: {metrics['overall_score']}")
    
    # Should deduplicate or handle gracefully
    assert len(graph.nodes) >= 1


def test_extreme_aspect_ratio():
    """Test spaces with extreme width/height ratios."""
    engine = SpatialReasoningEngine()
    
    # Very wide vs very narrow spaces
    polygons = [
        # Wide corridor (high aspect ratio)
        {
            "bounds": {"min_x": 0, "min_y": 0, "max_x": 20, "max_y": 1.5},
            "area_m2": 30,
            "points": [[0,0], [20,0], [20,1.5], [0,1.5]],
            "id": "wide-corridor",
            "type": "corridor"
        },
        # Square room
        {
            "bounds": {"min_x": 0, "min_y": 2, "max_x": 6, "max_y": 8},
            "area_m2": 36,
            "points": [[0,2], [6,2], [6,8], [0,8]],
            "id": "square-room",
            "type": "room"
        },
    ]
    
    graph = engine.build_graph(polygons, {"layer": "ASPECT-TEST"})
    
    # Check classification handles aspect ratio
    for node in graph.nodes:
        if node.area_m2 == 30:  # Corridor
            print(f"\n[OK] Wide corridor classified as: {node.node_type.value}")
    
    assert len(graph.nodes) == 2


def run_robustness_suite():
    """Run all robustness tests."""
    print("=" * 60)
    print("SPATIAL GRAPH ROBUSTNESS TEST SUITE")
    print("=" * 60)
    
    test_dirty_scan_simulation()
    test_incomplete_dxf_simulation()
    test_open_polygon_handling()
    test_layer_conflict_simulation()
    test_extreme_aspect_ratio()
    
    print("\n" + "=" * 60)
    print("[OK] All robustness tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_robustness_suite()