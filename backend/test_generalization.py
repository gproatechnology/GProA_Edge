"""Cross-tipology validation testing."""
from app.services.spatial_reasoning import (
    SpatialReasoningEngine,
    GROUND_TRUTH_DATASETS,
    comparator,
)


def test_cross_tipology_validation():
    """Test system across multiple building tipologies."""
    engine = SpatialReasoningEngine()
    
    results = []
    
    for gt_factory in GROUND_TRUTH_DATASETS:
        gt = gt_factory()
        
        # Build polygons matching the ground truth layout
        polygons = []
        for space in gt.spaces:
            bounds = space.expected_bounds
            polygons.append({
                "bounds": bounds,
                "area_m2": space.expected_area_m2,
                "points": [],
                "id": space.id,
                "type": space.expected_type,
            })
        
        graph = engine.build_graph(polygons)
        metrics = comparator.compare(graph, gt)
        
        results.append({
            "plan_id": gt.plan_id,
            "building_type": gt.metadata.get("building_type", "unknown"),
            "node_f1": metrics["node_f1"],
            "adjacency_f1": metrics["adjacency_f1"],
            "overall_accuracy": metrics["overall_accuracy"],
        })
        
        print(f"[CROSS] {gt.plan_id}: node={metrics['node_f1']:.2f}, adj={metrics['adjacency_f1']:.2f}, acc={metrics['overall_accuracy']:.2f}")
    
    # Check if accuracy is consistent across tipologies
    accuracies = [r["overall_accuracy"] for r in results]
    avg_accuracy = sum(accuracies) / len(accuracies)
    
    print(f"\n[CROSS] Average accuracy across tipologies: {avg_accuracy:.2f}")
    
    # Minimum threshold check
    for r in results:
        assert r["overall_accuracy"] >= 0.5, f"Low accuracy for {r['plan_id']}"
    
    print("[OK] Cross-tipology validation passed")


def test_generalization_score():
    """Calculate generalization score across all tipologies."""
    engine = SpatialReasoningEngine()
    
    total_node_f1 = 0
    total_adj_f1 = 0
    count = 0
    
    for gt_factory in GROUND_TRUTH_DATASETS:
        gt = gt_factory()
        
        polygons = []
        for space in gt.spaces:
            bounds = space.expected_bounds
            polygons.append({
                "bounds": bounds,
                "area_m2": space.expected_area_m2,
                "points": [],
                "id": space.id,
                "type": space.expected_type,
            })
        
        graph = engine.build_graph(polygons)
        metrics = comparator.compare(graph, gt)
        
        total_node_f1 += metrics["node_f1"]
        total_adj_f1 += metrics["adjacency_f1"]
        count += 1
    
    avg_node = total_node_f1 / count
    avg_adj = total_adj_f1 / count
    
    print(f"\n[GENERALIZATION] Avg Node F1: {avg_node:.2f}")
    print(f"[GENERALIZATION] Avg Adj F1: {avg_adj:.2f}")
    
    generalization_score = (avg_node + avg_adj) / 2
    print(f"[GENERALIZATION] Score: {generalization_score:.2f}")
    
    return generalization_score


if __name__ == "__main__":
    print("=" * 60)
    print("CROSS-TIPOLOGY VALIDATION")
    print("=" * 60)
    test_cross_tipology_validation()
    
    print("\n" + "=" * 60)
    print("GENERALIZATION SCORE")
    print("=" * 60)
    score = test_generalization_score()
    print(f"\n[OK] Generalization score: {score:.2f}")