"""Phase 7-A-C - Real World Industrial Validation
Validates Spatial Intelligence Engine on real architectural datasets from Documentos_EOSIS.
Focus: Failure discovery, not just "works well".
"""
import json
import asyncio
import time
import tracemalloc
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.services.technical_extraction_engine import engine as extraction_engine
from app.services.spatial_reasoning import SpatialReasoningEngine


class IndustrialValidationReport:
    """Report generator for Phase 7-A-C validation."""
    
    def __init__(self):
        self.results = []
        self.spatial_engine = SpatialReasoningEngine()
    
    async def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Run full pipeline on a single file."""
        result = {
            "file": str(file_path.name),
            "success": False,
            "parse_time_ms": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
            "node_survival_rate": 0.0,
            "failure_mode": None,
            "topology_integrity": "unknown"
        }
        
        tracemalloc.start()
        start = time.time()
        
        try:
            # Extract entities (async)
            extraction = await extraction_engine.extract(str(file_path))
            
            # Build spatial graph
            graph = self.spatial_engine.build_graph_from_extraction_result(extraction)
            
            result["success"] = True
            result["graph_nodes"] = len(graph.nodes)
            result["graph_edges"] = len(graph.edges)
            
            # Calculate integrity metrics
            if result["graph_nodes"] > 0:
                result["node_survival_rate"] = result["graph_nodes"] / max(1, len(extraction.entities))
                result["topology_integrity"] = "intact" if result["graph_edges"] > 0 else "fragmented"
            
        except Exception as e:
            result["failure_mode"] = type(e).__name__
            result["error"] = str(e)[:200]
        
        result["parse_time_ms"] = round((time.time() - start) * 1000, 2)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result["memory_kb"] = peak // 1024
        
        return result
    
    async def run_validation(self, doc_path: Path) -> List[Dict[str, Any]]:
        """Run validation on Documentos_EOSIS corpus."""
        results = []
        
        pdf_files = list(doc_path.rglob("*.pdf"))[:10]  # Limit to 10 for testing
        
        print(f"\n{'='*70}")
        print(f"PHASE 7-A-C - REAL WORLD INDUSTRIAL VALIDATION")
        print(f"{'='*70}")
        print(f"Documents to validate: {len(pdf_files)}")
        
        for pdf_path in pdf_files:
            print(f"\nValidating: {pdf_path.name}")
            result = await self.validate_file(pdf_path)
            results.append(result)
            
            status = "OK" if result["success"] else "FAIL"
            print(f"  {status} Nodes: {result['graph_nodes']} | Edges: {result['graph_edges']} | Time: {result['parse_time_ms']}ms")
            
            if result.get("failure_mode"):
                print(f"  Failure: {result['failure_mode']} - {result.get('error', '')}")
        
        return results
    
    def generate_report(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate validation report."""
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        failure_modes = {}
        for r in failed:
            mode = r.get("failure_mode", "unknown")
            failure_modes[mode] = failure_modes.get(mode, 0) + 1
        
        avg_nodes = sum(r["graph_nodes"] for r in successful) / max(1, len(successful))
        avg_edges = sum(r["graph_edges"] for r in successful) / max(1, len(successful))
        
        report = {
            "summary": {
                "total_documents": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / max(1, len(results))
            },
            "performance": {
                "avg_nodes_per_doc": round(avg_nodes, 1),
                "avg_edges_per_doc": round(avg_edges, 1)
            },
            "failure_taxonomy": failure_modes,
            "detailed_results": results
        }
        
        return report


async def main():
    doc_path = Path(__file__).parent.parent / "docs" / "Documentos_EOSIS"
    validator = IndustrialValidationReport()
    
    results = await validator.run_validation(doc_path)
    report = validator.generate_report(results)
    
    # Save report
    output_path = Path(__file__).parent / "phase7_validation_report.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*70}")
    print("VALIDATION SUMMARY")
    print(f"{'='*70}")
    print(f"Success rate: {report['summary']['success_rate']*100:.1f}%")
    print(f"Failure modes: {report['failure_taxonomy']}")
    print(f"\nReport saved: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())