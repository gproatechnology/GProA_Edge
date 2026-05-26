"""
Phase 6.5 - Performance Validation Benchmark
Measures latency, memory, and scalability for Spatial Intelligence Engine.
NO architecture changes - ONLY measurement and bottleneck detection.
"""
import time
import json
import tracemalloc
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import sys
sys.path.insert(0, "backend")

from app.services.spatial_reasoning import SpatialReasoningEngine
from app.services.spatial_reasoning.scale_extensions import FloorProcessor, LegacyPlanCleaner


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""
    stage: str
    room_count: int
    duration_ms: float
    memory_kb: int
    node_count: int
    edge_count: int
    time_per_node_ms: float
    time_per_edge_ms: float


def generate_synthetic_polygons(count: int, building_type: str = "office") -> List[Dict]:
    """Generate synthetic polygons for benchmarking (simulating real plans).
    Creates polygons with REAL adjacencies (shared edges), not just touching corners.
    """
    polygons = []
    
    if building_type == "office":
        # Office: grid layout with shared walls
        cols = int(count ** 0.5) + 1
        room_w, room_h = 4.0, 4.0
        
        for i in range(count):
            row = i // cols
            col = i % cols
            # NO spacing - adjacent rooms share edges
            x = col * room_w
            y = row * room_h
            
            polygons.append({
                "bounds": {"min_x": x, "min_y": y, "max_x": x + room_w, "max_y": y + room_h},
                "area_m2": room_w * room_h,
                "points": [],
                "id": f"OFF-{i:04d}",
                "type": "room"
            })
    
    elif building_type == "hospital":
        # Hospital: corridor + rooms layout
        room_w, room_h = 8.0, 8.0
        corridor_w = 3.0
        
        for i in range(count):
            if i == 0:
                # Corridor down middle
                x, y = 0, 0
                w, h = corridor_w, (count // 2) * room_h
            else:
                side = 0 if i % 2 == 1 else 1
                idx = (i - 1) // 2
                x = corridor_w + side * room_w
                y = (idx % (count // 4)) * room_h
                w, h = room_w, room_h
            
            polygons.append({
                "bounds": {"min_x": x, "min_y": y, "max_x": x + w, "max_y": y + h},
                "area_m2": w * h,
                "points": [],
                "id": f"HOSP-{i:04d}",
                "type": "corridor" if i == 0 else "room"
            })
    
    elif building_type == "retail":
        # Retail: irregular shop layout
        for i in range(count):
            x = i * 5
            w = 3 + (i % 3)  # Varying widths
            h = 8
            y = 0
            
            polygons.append({
                "bounds": {"min_x": x, "min_y": y, "max_x": x + w, "max_y": y + h},
                "area_m2": w * h,
                "points": [],
                "id": f"RET-{i:04d}",
                "type": "retail"
            })
    
    elif building_type == "factory":
        # Factory: large bays with some divisions
        bay_w, bay_h = 15.0, 15.0
        bays = (count + 3) // 4  # 4 rooms per bay roughly
        
        for i in range(count):
            bay = i // 4
            row, col = bay % 3, bay // 3
            x = col * bay_w
            y = row * bay_h
            # Split bay into sub-rooms
            sub = i % 4
            sub_w = bay_w / 2
            sub_h = bay_h / 2
            x += (sub % 2) * sub_w
            y += (sub // 2) * sub_h
            
            polygons.append({
                "bounds": {"min_x": x, "min_y": y, "max_x": x + sub_w, "max_y": y + sub_h},
                "area_m2": sub_w * sub_h,
                "points": [],
                "id": f"FACT-{i:04d}",
                "type": "bay"
            })
    
    return polygons


def benchmark_stage(name: str, func, *args, **kwargs) -> BenchmarkResult:
    """Benchmark a single operation stage."""
    tracemalloc.start()
    start = time.time()
    
    result = func(*args, **kwargs)
    
    end = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    duration_ms = (end - start) * 1000
    memory_kb = peak // 1024
    
    # Extract counts from result
    if hasattr(result, 'nodes'):
        node_count = len(result.nodes)
        edge_count = len(result.edges)
    else:
        node_count = result if isinstance(result, int) else 0
        edge_count = 0
    
    return BenchmarkResult(
        stage=name,
        room_count=len(args[0]) if args else 0,
        duration_ms=round(duration_ms, 3),
        memory_kb=memory_kb,
        node_count=node_count,
        edge_count=edge_count,
        time_per_node_ms=round(duration_ms / max(1, node_count), 4),
        time_per_edge_ms=round(duration_ms / max(1, edge_count), 4)
    )


def run_scaling_benchmark() -> List[BenchmarkResult]:
    """Run benchmarks at different scales to detect O(n²) behavior."""
    results = []
    engine = SpatialReasoningEngine()
    
    scale_points = [10, 25, 50, 100, 200, 500]
    
    print("\n" + "=" * 60)
    print("PHASE 6.5 BENCHMARK - SCALING TEST")
    print("=" * 60)
    
    for count in scale_points:
        polygons = generate_synthetic_polygons(count, "office")
        
        # Geometry parsing (clustering)
        result1 = benchmark_stage("clustering", engine.clusterer.cluster_from_polygons, polygons)
        results.append(result1)
        
        # Adjacency detection (THE SUSPECTED O(n²) BOTTLENECK)
        graph_before = engine.build_graph(polygons)
        result2 = benchmark_stage("adjacency", engine.adjacency_detector.detect_adjacencies, graph_before.nodes)
        results.append(result2)
        
        # Full graph build
        result3 = benchmark_stage("full_graph", engine.build_graph, polygons)
        results.append(result3)
        
        print(f"  [{count:4d} rooms] nodes: {result3.node_count:4d} | edges: {result3.edge_count:4d} | time: {result3.duration_ms:7.2f}ms")
    
    return results


def run_building_type_benchmark() -> List[BenchmarkResult]:
    """Benchmark different building types."""
    results = []
    engine = SpatialReasoningEngine()
    
    types = ["office", "hospital", "retail", "factory"]
    count = 100
    
    print("\n" + "=" * 60)
    print("PHASE 6.5 BENCHMARK - BUILDING TYPES")
    print("=" * 60)
    
    for btype in types:
        polygons = generate_synthetic_polygons(count, btype)
        result = benchmark_stage(f"graph_{btype}", engine.build_graph, polygons)
        results.append(result)
        print(f"  [{btype:10s}] nodes: {result.node_count:4d} | edges: {result.edge_count:4d} | time: {result.duration_ms:7.2f}ms")
    
    return results


def analyze_complexity(results: List[BenchmarkResult]) -> Dict[str, Any]:
    """Analyze results to detect O(n²) complexity."""
    adjacency_results = [r for r in results if r.stage == "adjacency"]
    
    analysis = {
        "detected_bottlenecks": [],
        "scaling_evidence": []
    }
    
    if len(adjacency_results) >= 3:
        times = [r.duration_ms for r in adjacency_results]
        counts = [r.room_count for r in adjacency_results]
        
        # Check if time grows quadratically
        for i in range(2, len(times)):
            ratio_n = counts[i] / counts[i-1]
            ratio_t = times[i] / times[i-1]
            expected_linear = ratio_n
            expected_quadratic = ratio_n ** 2
            
            if ratio_t > (expected_linear * 1.5):
                evidence = f"[{counts[i-1]}->{counts[i]} rooms] time ratio {ratio_t:.2f}x vs linear {expected_linear:.2f}x"
                analysis["scaling_evidence"].append(evidence)
                if "adjacency O(n^2)" not in analysis["detected_bottlenecks"]:
                    analysis["detected_bottlenecks"].append("adjacency O(n^2)")
    
    return analysis


def main():
    print("=" * 60)
    print("PHASE 6.5 - PERFORMANCE VALIDATION")
    print("=" * 60)
    
    scaling_results = run_scaling_benchmark()
    type_results = run_building_type_benchmark()
    
    all_results = scaling_results + type_results
    
    analysis = analyze_complexity(all_results)
    
    summary = {
        "benchmark_results": [asdict(r) for r in all_results],
        "complexity_analysis": analysis,
        "recommendations": [
            "Detect O(n^2) in adjacency - use spatial index (R-tree/k-d tree)",
            "Consider batching for graphs > 200 nodes",
            "Profile memory for large floor plates"
        ]
    }
    
    output_path = "benchmark_phase65_results.json"
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    
    if analysis["detected_bottlenecks"]:
        print("\n[CRITICAL] Bottlenecks detected:")
        for b in analysis["detected_bottlenecks"]:
            print(f"  - {b}")
    
    print(f"\nResults saved to: {output_path}")
    print("[OK] Phase 6.5 benchmark complete")


if __name__ == "__main__":
    main()