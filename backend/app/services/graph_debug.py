"""
Graph debugging and visualization tools.
"""
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from app.services.entity_registry import EntityRegistry, RelationshipEngine

logger = logging.getLogger(__name__)


class GraphDebugger:
    """Debug and analyze technical relationship graphs."""
    
    def __init__(self, registry: EntityRegistry):
        self.registry = registry
        self.engine = RelationshipEngine(registry)
    
    def find_orphans(self) -> List[str]:
        """Find entities without relationships."""
        orphans = []
        for entity_id in self.registry.entities:
            neighbors = self.engine.get_downstream_entities(entity_id)
            upstream = self.engine.get_upstream_entities(entity_id)
            if not neighbors and not upstream:
                orphans.append(entity_id)
        return orphans
    
    def find_missing_relationships(self) -> List[Dict[str, Any]]:
        """Find entities that should have relationships but don't."""
        issues = []
        
        # Luminaires without areas
        for entity in self.registry.get_by_type("luminaire"):
            if not self.engine.find_path(entity.id, "area"):
                issues.append({
                    "entity": entity.id,
                    "type": "luminaire_without_area"
                })
        
        # Circuits without panels
        for entity in self.registry.get_by_type("circuit"):
            if not self.engine.find_path(entity.id, "panel"):
                issues.append({
                    "entity": entity.id,
                    "type": "circuit_without_panel"
                })
        
        return issues
    
    def export_graphviz(self, output_path: str = None) -> str:
        """Export graph as GraphViz DOT format."""
        lines = ["digraph TechnicalGraph {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box];")
        
        for entity_id, entity in self.registry.entities.items():
            label = f"{entity_id}\\n{entity.type}"
            lines.append(f'  "{entity_id}" [label="{label}"];')
        
        for rel in self.registry.relationships:
            lines.append(f'  "{rel.source_entity_id}" -> "{rel.target_entity_id}" [label="{rel.type}"];')
        
        lines.append("}")
        
        content = "\n".join(lines)
        
        if output_path:
            Path(output_path).write_text(content)
        
        return content
    
    def to_json(self) -> Dict[str, Any]:
        """Export graph as JSON."""
        return {
            "entities": {
                eid: {
                    "type": e.type.value,
                    "measure": e.measure.value,
                    "discipline": e.discipline.value,
                    "confidence": e.confidence
                }
                for eid, e in self.registry.entities.items()
            },
            "relationships": [
                {
                    "source": r.source_entity_id,
                    "target": r.target_entity_id,
                    "type": r.type.value,
                    "confidence": r.confidence
                }
                for r in self.registry.relationships
            ],
            "stats": {
                "total_entities": len(self.registry.entities),
                "total_relationships": len(self.registry.relationships),
                "orphan_count": len(self.find_orphans())
            }
        }


class TechnicalReplay:
    """Technical replay engine for debugging pipeline stages."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
    
    def get_stage_data(self, stage_name: str, revision: str = "latest"):
        """Get persisted stage data for replay."""
        from app.services.pipeline.artifacts import artifact_store
        return artifact_store.load(self.project_id, f"{stage_name}.json", revision)
    
    def compare_revisions(self, rev_a: str, rev_b: str) -> Dict[str, Any]:
        """Compare two pipeline revisions."""
        differences = {}
        
        artifacts_a = ["entities", "relationships", "validation"]
        for artifact in artifacts_a:
            data_a = self.get_stage_data(artifact, rev_a)
            data_b = self.get_stage_data(artifact, rev_b)
            
            if data_a != data_b:
                differences[artifact] = {
                    "changed": True,
                    "count_a": len(str(data_a)) if data_a else 0,
                    "count_b": len(str(data_b)) if data_b else 0
                }
        
        return differences