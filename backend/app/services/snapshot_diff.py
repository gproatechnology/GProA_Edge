"""
Snapshot diffing for technical revisions.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class EntityDiff:
    entity_id: str
    change_type: str  # added, removed, modified
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]


@dataclass
class SnapshotDiff:
    revision_a: str
    revision_b: str
    entities_added: int = 0
    entities_removed: int = 0
    entities_modified: int = 0
    relationships_added: int = 0
    relationships_removed: int = 0
    power_changes: List[EntityDiff] = None
    area_changes: List[EntityDiff] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "revision_a": self.revision_a,
            "revision_b": self.revision_b,
            "entities_added": self.entities_added,
            "entities_removed": self.entities_removed,
            "entities_modified": self.entities_modified,
            "relationships_added": self.relationships_added,
            "relationships_removed": self.relationships_removed,
            "power_changes": [{"entity_id": e.entity_id, "old_values": e.old_values, "new_values": e.new_values} for e in (self.power_changes or [])],
            "area_changes": [{"entity_id": e.entity_id, "old_values": e.old_values, "new_values": e.new_values} for e in (self.area_changes or [])]
        }


class SnapshotDiffer:
    """Compare technical snapshots across revisions."""
    
    def __init__(self, artifact_store):
        self.artifact_store = artifact_store
    
    def diff_entities(self, project_id: str, rev_a: str, rev_b: str) -> SnapshotDiff:
        """Compare entity snapshots between revisions."""
        from app.services.pipeline.artifacts import artifact_store
        
        entities_a = artifact_store.load(project_id, "entity.extraction.json", rev_a) or []
        entities_b = artifact_store.load(project_id, "entity.extraction.json", rev_b) or []
        
        ids_a = {e.get("id") or e.get("entity_id"): e for e in entities_a if isinstance(e, dict)}
        ids_b = {e.get("id") or e.get("entity_id"): e for e in entities_b if isinstance(e, dict)}
        
        diff = SnapshotDiff(revision_a=rev_a, revision_b=rev_b)
        
        for eid in set(ids_a.keys()) | set(ids_b.keys()):
            in_a = eid in ids_a
            in_b = eid in ids_b
            
            if in_a and not in_b:
                diff.entities_removed += 1
            elif in_b and not in_a:
                diff.entities_added += 1
            elif in_a and in_b:
                if ids_a[eid] != ids_b[eid]:
                    diff.entities_modified += 1
                    
                    props_a = ids_a[eid].get("properties", {})
                    props_b = ids_b[eid].get("properties", {})
                    
                    if "watts" in props_a or "watts" in props_b:
                        diff.power_changes.append(EntityDiff(
                            entity_id=eid,
                            change_type="modified",
                            old_values={"watts": props_a.get("watts")},
                            new_values={"watts": props_b.get("watts")}
                        ))
                    
                    if "area_m2" in props_a or "area_m2" in props_b:
                        diff.area_changes.append(EntityDiff(
                            entity_id=eid,
                            change_type="modified",
                            old_values={"area_m2": props_a.get("area_m2")},
                            new_values={"area_m2": props_b.get("area_m2")}
                        ))
        
        relationships_a = artifact_store.load(project_id, "relationships.json", rev_a) or []
        relationships_b = artifact_store.load(project_id, "relationships.json", rev_b) or []
        
        rels_a = {(r.get("source"), r.get("target")) for r in relationships_a if isinstance(r, dict)}
        rels_b = {(r.get("source"), r.get("target")) for r in relationships_b if isinstance(r, dict)}
        
        diff.relationships_added = len(rels_b - rels_a)
        diff.relationships_removed = len(rels_a - rels_b)
        
        return diff