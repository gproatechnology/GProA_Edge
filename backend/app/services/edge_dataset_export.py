"""
EDGE Dataset Export Layer for EOSIS Edge v1.0.
Exports structured datasets ready for EDGE calculators.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class EDGEProjectDataset:
    """
    Structured export of extracted entities with full traceability.
    Ready for EDGE calculators and TAL/UAKG processing.
    """
    
    def __init__(self, project_id: str, revision: str = "v1"):
        self.project_id = project_id
        self.revision = revision
        self.entities: List[Dict[str, Any]] = []
        self.relations: List[Dict[str, Any]] = []
        self.strategy_mappings: Dict[str, List[str]] = {}
        self.validation_evidence: List[Dict[str, Any]] = []
        self.extraction_metadata: Dict[str, Any] = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "schema_version": "1.0",
            "total_entities": 0,
            "entities_by_type": {},
            "entities_by_strategy": {},
        }
    
    def add_entity(self, entity: Dict[str, Any], 
                   strategy: Optional[str] = None,
                   validation_issues: Optional[List[Dict]] = None):
        """Add an entity with optional strategy mapping and validation."""
        entity_copy = self._sanitize_entity(entity)
        
        # Add strategy mapping if provided
        if strategy:
            entity_copy["edge_strategy"] = strategy
            if strategy not in self.strategy_mappings:
                self.strategy_mappings[strategy] = []
            self.strategy_mappings[strategy].append(entity.get("uid", "unknown"))
        
        # Add validation evidence
        if validation_issues:
            for issue in validation_issues:
                issue_copy = issue
                if hasattr(issue, 'to_dict'):
                    issue_copy = issue.to_dict()
                self.validation_evidence.append({
                    "entity_uid": entity.get("uid"),
                    "issue": issue_copy
                })
        
        self.entities.append(entity_copy)
    
    def _sanitize_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive/internal fields from entity."""
        result = entity.copy()
        
        # Remove internal fields if present
        internal_fields = ["_internal", "__class__", "__dict__"]
        for field in internal_fields:
            result.pop(field, None)
        
        return result
    
    def add_relation(self, source_uid: str, target_uid: str, 
                     rel_type: str, confidence: float = 0.95):
        """Add a relationship between entities."""
        self.relations.append({
            "source_uid": source_uid,
            "target_uid": target_uid,
            "type": rel_type,
            "confidence": confidence,
        })
    
    def finalize(self) -> Dict[str, Any]:
        """
        Generate final dataset structure.
        
        Returns:
            Complete EDGEProjectDataset structure ready for export.
        """
        # Update metadata
        self.extraction_metadata["total_entities"] = len(self.entities)
        
        # Count by type
        type_counts = {}
        strategy_counts = {}
        for entity in self.entities:
            etype = entity.get("type", "unknown")
            type_counts[etype] = type_counts.get(etype, 0) + 1
            
            strategy = entity.get("edge_strategy")
            if strategy:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        self.extraction_metadata["entities_by_type"] = type_counts
        self.extraction_metadata["entities_by_strategy"] = strategy_counts
        
        return {
            "project_id": self.project_id,
            "revision": self.revision,
            "entities": self.entities,
            "relations": self.relations,
            "strategy_mappings": self.strategy_mappings,
            "validation_evidence": self.validation_evidence,
            "metadata": self.extraction_metadata,
        }
    
    def to_json(self) -> str:
        """Export dataset as JSON string."""
        return json.dumps(self.finalize(), indent=2)


def export_to_edge_dataset(
    entities: List[Dict[str, Any]], 
    project_id: str,
    strategy_mapper=None,
    validator=None
) -> EDGEProjectDataset:
    """
    Convenience function to export entities to EDGE dataset.
    
    Args:
        entities: List of extracted TechnicalEntity dicts
        project_id: Project identifier
        strategy_mapper: Optional EDGEStraategyMapper instance
        validator: Optional SemanticValidator instance
        
    Returns:
        EDGEProjectDataset ready for export
    """
    from app.services.edge_strategy_mapper import strategy_mapper as default_mapper
    from app.services.semantic_validator import validator as default_validator
    
    mapper = strategy_mapper or default_mapper
    val = validator or default_validator
    
    dataset = EDGEProjectDataset(project_id)
    
    for entity in entities:
        # Map to EDGE strategy
        strategy = mapper.map_entity(entity)
        
        # Validate
        issues = val.validate_entity(entity)
        validation_dicts = []
        for issue in issues:
            if hasattr(issue, 'to_dict'):
                validation_dicts.append(issue.to_dict())
            else:
                validation_dicts.append({
                    "issue_type": issue.issue_type.value if hasattr(issue.issue_type, 'value') else issue.issue_type,
                    "severity": issue.severity,
                    "confidence": issue.confidence,
                    **issue.details
                })
        
        dataset.add_entity(
            entity, 
            strategy=strategy.value if strategy else None,
            validation_issues=validation_dicts if validation_dicts else None
        )
    
    return dataset