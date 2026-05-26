"""Test Spatial Reasoning Engine integration with geometry normalization."""
import asyncio
from app.services.spatial_reasoning import SpatialReasoningEngine, SpatialGraph
from app.services.spatial_reasoning.geometry_normalizer import GeometryNormalizer
from app.schemas.technical_entity import ExtractionResult, TechnicalEntity, MeasureType, Discipline, EntityType
from app.services.spatial_reasoning import normalize_extraction_to_polygons


def test_geometry_normalizer():
    """Test the geometry normalizer with simulated DXF areas."""
    normalizer = GeometryNormalizer()
    
    # Simulate DXF extraction output (areas without full geometry)
    areas = [
        {"area_m2": 50.0, "type": "polyline", "nombre": "SALA-01"},
        {"area_m2": 25.0, "type": "hatch", "nombre": "CORRIDOR-01"},
        {"area_m2": 15.0, "type": "circle", "nombre": "WC-01"},
    ]
    
    polygons = normalizer.normalize_dxf_areas(areas, ["ARCH-ROOMS"])
    
    print(f"[OK] Normalized {len(areas)} areas into {len(polygons)} polygons")
    for p in polygons:
        print(f"   Polygon: bounds={p['bounds']}, area={p['area_m2']}m2")
    
    assert len(polygons) == 3
    assert all("bounds" in p and "points" in p for p in polygons)
    return polygons


def test_basic_graph_construction():
    """Test building graph from simple polygons."""
    engine = SpatialReasoningEngine()
    
    polygons = [
        {
            "bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 8},
            "area_m2": 80,
            "points": [[0,0], [10,0], [10,8], [0,8]],
            "id": "poly-001",
            "type": "room"
        },
        {
            "bounds": {"min_x": 10, "min_y": 0, "max_x": 15, "max_y": 5},
            "area_m2": 25,
            "points": [[10,0], [15,0], [15,5], [10,5]],
            "id": "poly-002",
            "type": "corridor"
        }
    ]
    
    graph = engine.build_graph(polygons, {"layer": "ARCH-ROOMS"})
    
    print(f"[OK] Graph built: {len(graph.nodes)} nodes")
    print(f"[OK] Edges detected: {len(graph.edges)}")
    
    for node in graph.nodes:
        print(f"   Node {node.uid}: type={node.node_type}, area={node.area_m2}m2")
    
    for edge in graph.edges:
        print(f"   Edge: {edge.source_uid} --[{edge.edge_type}]--> {edge.target_uid}")
    
    assert len(graph.nodes) == 2
    assert len(graph.edges) >= 1


def test_extraction_result_to_graph():
    """Test the full pipeline: ExtractionResult -> SpatialGraph."""
    engine = SpatialReasoningEngine()
    
    # Create a simulated ExtractionResult with smaller areas that fit together
    areas = [
        {"area_m2": 25.0, "type": "polyline", "nombre": "SALA-01"},
        {"area_m2": 16.0, "type": "polyline", "nombre": "SALA-02"},
        {"area_m2": 8.0, "type": "hatch", "nombre": "CORRIDOR-01"},
    ]
    
    metadata = {
        "layers": ["ARCH-ROOMS", "ARCH-CORRIDORS"],
        "units": "Meters",
        "areas": areas,
        "entities": {}
    }
    
    result = ExtractionResult(
        measure=MeasureType.DESIGN,
        discipline=Discipline.ARCHITECTURAL,
        entities=[],
        source_metadata=metadata
    )
    
    # Normalize geometry
    polygons = normalize_extraction_to_polygons(result)
    print(f"\n[OK] Normalized {len(polygons)} polygons from ExtractionResult")
    for p in polygons[:2]:  # Show first 2
        print(f"   Polygon: x={p['bounds']['min_x']:.1f}-{p['bounds']['max_x']:.1f}, area={p['area_m2']}m2")
    
    # Build graph
    graph = engine.build_graph_from_extraction_result(result)
    
    print(f"[OK] Graph built: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    
    for node in graph.nodes:
        print(f"   Node {node.uid}: type={node.node_type.value}, area={node.area_m2}m2")
    
    for edge in graph.edges:
        print(f"   Edge: {edge.source_uid} --[{edge.edge_type.value}]--> {edge.target_uid}")
    
    assert len(graph.nodes) >= 1, "Should have at least one node"
    print(f"[OK] Detected {len(graph.edges)} adjacencies")


def test_edge_mapping_from_graph():
    """Test EDGE strategy mapping from spatial graph."""
    from app.services.edge_strategy_mapper import EDGEStraategyMapper
    
    engine = SpatialReasoningEngine()
    
    # Create a graph with various space types
    polygons = [
        {"bounds": {"min_x": 0, "min_y": 0, "max_x": 20, "max_y": 15}, "area_m2": 300, "points": [], "id": "large-space"},
        {"bounds": {"min_x": 20, "min_y": 0, "max_x": 25, "max_y": 20}, "area_m2": 15, "points": [], "id": "corridor"},
        {"bounds": {"min_x": 0, "min_y": 15, "max_x": 10, "min_y": 25}, "area_m2": 5, "points": [], "id": "restroom"},
    ]
    
    graph = engine.build_graph(polygons, {"layer": "ARCH-ROOMS"})
    
    # Map to EDGE strategies
    mapping = EDGEStraategyMapper.map_spatial_graph(graph)
    
    print(f"\n[OK] EDGE mapping: {mapping['strategies']}")
    print(f"[OK] Spaces for EDesign: {len(mapping['spaces_for_edesign'])}")
    
    assert "strategies" in mapping


if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: Geometry Normalizer")
    print("=" * 60)
    test_geometry_normalizer()
    
    print("\n" + "=" * 60)
    print("TEST 2: Basic Graph Construction")
    print("=" * 60)
    test_basic_graph_construction()
    
    print("\n" + "=" * 60)
    print("TEST 3: ExtractionResult -> Graph Pipeline")
    print("=" * 60)
    test_extraction_result_to_graph()
    
    print("\n" + "=" * 60)
    print("TEST 4: EDGE Strategy Mapping")
    print("=" * 60)
    test_edge_mapping_from_graph()
    
    print("\n" + "=" * 60)
    print("[OK] All tests passed!")
    print("=" * 60)