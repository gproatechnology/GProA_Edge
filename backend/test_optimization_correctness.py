"""Verify optimized detector produces identical results to naive."""
import sys
sys.path.insert(0, "backend")

from app.services.spatial_reasoning import SpatialReasoningEngine
from app.services.spatial_reasoning.adjacency import AdjacencyDetector
from app.services.spatial_reasoning.adjacency_optimized import OptimizedAdjacencyDetector

def test_equivalence():
    """Verify both detectors produce same adjacencies."""
    engine = SpatialReasoningEngine()
    naive = AdjacencyDetector()
    optimized = OptimizedAdjacencyDetector()
    
    # Test with 100 rooms
    polygons = []
    for i in range(100):
        row = i // 10
        col = i % 10
        x = col * 4
        y = row * 4
        polygons.append({
            "bounds": {"min_x": x, "min_y": y, "max_x": x + 4, "max_y": y + 4},
            "area_m2": 16,
            "points": [],
            "id": f"R{i:03d}",
            "type": "room"
        })
    
    nodes = engine.clusterer.cluster_from_polygons(polygons)
    
    naive_edges = naive.detect_adjacencies(nodes)
    opt_edges = optimized.detect_adjacencies(nodes)
    
    naive_pairs = {(e.source_uid, e.target_uid) for e in naive_edges}
    opt_pairs = {(e.source_uid, e.target_uid) for e in opt_edges}
    
    print(f"Naive edges: {len(naive_edges)}")
    print(f"Optimized edges: {len(opt_edges)}")
    print(f"Match: {naive_pairs == opt_pairs}")
    
    if naive_pairs != opt_pairs:
        missing = naive_pairs - opt_pairs
        extra = opt_pairs - naive_pairs
        if missing:
            print(f"Missing edges: {missing}")
        if extra:
            print(f"Extra edges: {extra}")
    
    return naive_pairs == opt_pairs

if __name__ == "__main__":
    test_equivalence()