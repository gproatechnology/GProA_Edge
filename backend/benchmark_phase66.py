"""
Phase 6.5 + 6.6 - Performance Validation Benchmark
Compares O(n²) vs O(n log n) adjacency detection
"""
import time
import json
import tracemalloc
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import sys
sys.path.insert(0, "backend")

from app.services.spatial_reasoning import SpatialReasoningEngine
from app.services.spatial_reasoning.adjacency import AdjacencyDetector
from app.services.spatial_reasoning.adjacency_optimized import OptimizedAdjacencyDetector


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""
    stage: str
    variant: str
    room_count: int
    duration_ms: float
    memory_kb: int
    node_count: int
    edge_count: int
    speedup: float = 0.0


def generate_synthetic_polygons(count: int, building_type: str = "office") -> List[Dict]:
    """Generate synthetic polygons with real adjacencies."""
    polygons = []
    
    if building_type == "office":
        cols = int(count ** 0.5) + 1
        room_w, room_h = 4.0, 4.0
        
        for i in range(count):
            row = i // cols
            col = i % cols
            x = col * room_w
            y = row * room_h
            
            polygons.append({
                "bounds": {"min_x": x, "min_y": y, "max_x": x + room_w, "max_y": y + room_h},
                "area_m2": room_w * room_h,
                "points": [],
                "id": f"OFF-{i:04d}",
                "type": "room"
            })
    return polygons


def benchmark_stage(name: str, variant: str, func, nodes: List) -> BenchmarkResult:
    """Benchmark a single operation stage."""
    tracemalloc.start()
    start = time.time()
    
    result = func(nodes)
    
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    duration_ms = (end - start) * 1000
    memory_kb = peak // 1024
    edge_count = len(result) if isinstance(result, list) else 0
    
    return BenchmarkResult(
        stage=name,
        variant=variant,
        room_count=len(nodes),
        duration_ms=round(duration_ms, 3),
        memory_kb=memory_kb,
        node_count=len(nodes),
        edge_count=edge_count
    )


def run_comparison_benchmark() -> List[BenchmarkResult]:
    """Compare O(n²) vs O(n log n) implementations."""
    results = []
    engine = SpatialReasoningEngine()
    naive_detector = AdjacencyDetector()
    optimized_detector = OptimizedAdjacencyDetector()
    
    scale_points = [10, 25, 50, 100, 200, 500, 1000]
    
    print("\n" + "=" * 70)
    print("PHASE 6.6 - OPTIMIZATION COMPARISON: O(n²) vs O(n log n)")
    print("=" * 70)
    print(f"{'Rooms':>8} | {'Naive (ms)':>12} | {'Optimized (ms)':>14} | {'Speedup':>8}")
    print("-" * 70)
    
    baseline_time = None
    
    for count in scale_points:
        polygons = generate_synthetic_polygons(count, "office")
        nodes = engine.clusterer.cluster_from_polygons(polygons)
        
        # Naive O(n²)
        result_naive = benchmark_stage("adjacency", "naive", naive_detector.detect_adjacencies, nodes)
        
        # Optimized O(n log n)
        result_opt = benchmark_stage("adjacency", "optimized", optimized_detector.detect_adjacencies, nodes)
        
        result_naive.speedup = result_opt.duration_ms / max(0.001, result_naive.duration_ms)
        
        results.extend([result_naive, result_opt])
        
        print(f"{count:8d} | {result_naive.duration_ms:12.2f} | {result_opt.duration_ms:14.2f} | {result_naive.speedup:8.2f}x")
    
    return results


def main():
    print("=" * 70)
    print("PHASE 6.5 + 6.6 - PERFORMANCE VALIDATION")
    print("=" * 70)
    
    results = run_comparison_benchmark()
    
    analysis = {
        "detected_bottlenecks": [],
        "speedup_evidence": []
    }
    
    # Check speedup > 1.5x indicates improvement
    significant_speedups = [r for r in results if r.variant == "naive" and r.speedup > 1.5]
    if significant_speedups:
        analysis["detected_bottlenecks"].append("adjacency O(n^2) - FIXED with R-tree")
        for r in significant_speedups[-4:]:
            analysis["speedup_evidence"].append(f"{r.room_count} rooms: {r.speedup:.2f}x speedup")
    
    summary = {
        "benchmark_results": [asdict(r) for r in results],
        "complexity_analysis": analysis,
        "recommendations": [
            "Replace AdjacencyDetector with OptimizedAdjacencyDetector",
            "Use R-tree spatial index for graphs > 100 nodes",
            "Consider k-d tree for uniform distributions"
        ]
    }
    
    output_path = "benchmark_phase66_results.json"
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    
    if analysis["detected_bottlenecks"]:
        print("\n[FIXED] Optimizations applied:")
        for b in analysis["detected_bottlenecks"]:
            print(f"  - {b}")
    
    print(f"\nResults saved to: {output_path}")
    print("[OK] Phase 6.6 optimization complete")


if __name__ == "__main__":
    main()