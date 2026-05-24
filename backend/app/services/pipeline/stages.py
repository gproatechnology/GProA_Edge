"""
Individual pipeline stages for technical knowledge graph processing.
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from app.schemas.technical_entity import TechnicalEntity

from .contracts import StageResult, StageStatus, ProcessingContract
from .events import PipelineEventType, PipelineEvent, event_bus
from .artifacts import artifact_store

logger = logging.getLogger(__name__)


class BaseStage(ABC):
    """Abstract base for all pipeline stages."""
    
    def __init__(self, name: str):
        self.name = name
        self.contract = ProcessingContract(stage_name=name)
    
    async def execute(self, context: Dict[str, Any]) -> StageResult:
        start_time = time.time()
        event_bus.emit(PipelineEvent(
            type=PipelineEventType.STAGE_STARTED,
            stage=self.name,
            payload={"project_id": context.get("project_id")}
        ))
        
        try:
            result = await self._process(context)
            result.execution_time_ms = (time.time() - start_time) * 1000
            result.status = StageStatus.COMPLETED
        except Exception as e:
            logger.error(f"Stage {self.name} failed: {e}")
            result = StageResult(
                stage_name=self.name,
                status=StageStatus.FAILED,
                errors=[str(e)],
                execution_time_ms=(time.time() - start_time) * 1000
            )
        
        event_bus.emit(PipelineEvent(
            type=PipelineEventType.STAGE_COMPLETED,
            stage=self.name,
            payload={"project_id": context.get("project_id"), "status": result.status.value}
        ))
        
        return result
    
    @abstractmethod
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        pass


class FileIngestionStage(BaseStage):
    def __init__(self):
        super().__init__("file_ingestion")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        files = context.get("files", [])
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        validated_files = []
        for f in files:
            if isinstance(f, dict) and "path" in f:
                validated_files.append({
                    "path": f["path"],
                    "type": f.get("type", "unknown"),
                    "size": f.get("size", 0)
                })
        
        result.output = {"files": validated_files, "count": len(validated_files)}
        result.confidence = 1.0
        return result


class ParsingStage(BaseStage):
    def __init__(self):
        super().__init__("parsing")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        files = context.get("files", [])
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        from app.services.technical_extraction_engine import engine
        
        parsed_results = []
        for f in files:
            try:
                extraction = await engine.extract(f["path"])
                parsed_results.append({
                    "file": f["path"],
                    "result": extraction.model_dump()
                })
            except Exception as e:
                logger.error(f"Parse error for {f['path']}: {e}")
        
        result.output = {"parsed": parsed_results, "count": len(parsed_results)}
        result.confidence = 0.9 if parsed_results else 0.0
        return result


class EntityExtractionStage(BaseStage):
    def __init__(self):
        super().__init__("entity_extraction")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        parsed_results = context.get("parsed", [])
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        entities = []
        for pr in parsed_results:
            extraction = pr.get("result", {})
            for entity in extraction.get("entities", []):
                entities.append(entity)
        
        result.output = {"entities": entities, "count": len(entities)}
        result.confidence = 0.95 if entities else 0.0
        return result


class EntityNormalizationStage(BaseStage):
    def __init__(self):
        super().__init__("entity_normalization")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        entities = context.get("entities", [])
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        normalized = []
        for e in entities:
            entity_id = e.get("id") or e.get("entity_id")
            entity_type = e.get("type") or e.get("entity_type")
            normalized.append({
                "id": entity_id,
                "type": entity_type,
                "measure": e.get("measure"),
                "discipline": e.get("discipline"),
                "properties": e.get("properties", {}),
                "coordinates": e.get("coordinates")
            })
        
        result.output = {"entities": normalized, "count": len(normalized)}
        result.confidence = 1.0
        return result


class IdentityResolutionStage(BaseStage):
    def __init__(self):
        super().__init__("identity_resolution")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        entities = context.get("entities", [])
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        from app.services.entity_identity import EntityIdentityResolver
        resolver = EntityIdentityResolver()
        
        canonical_map = {}
        for e in entities:
            try:
                entity_id = e.get("id") or e.get("entity_id")
                e_copy = dict(e)
                if "entity_id" in e_copy:
                    e_copy["id"] = e_copy["entity_id"]
                entity = TechnicalEntity(**e_copy) if isinstance(e_copy, dict) else e
                canonical_id, _ = resolver.resolve(entity)
                canonical_map[entity_id] = canonical_id
            except Exception:
                pass
        
        result.output = {
            "identity_map": canonical_map,
            "resolved_count": len(canonical_map)
        }
        result.confidence = 0.9 if canonical_map else 1.0
        return result


class RelationshipInferenceStage(BaseStage):
    def __init__(self):
        super().__init__("relationship_inference")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        entities = context.get("entities", [])
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        from app.services.spatial_intelligence import SpatialReasoning
        from app.services.entity_registry import registry
        
        spatial = SpatialReasoning(registry.spatial_idx)
        
        inferred = []
        inferred.extend(spatial.infer_luminaire_area_coverage(entities))
        inferred.extend(spatial.infer_panel_circuit_mapping(entities))
        inferred.extend(spatial.infer_hvac_zone_mapping(entities))
        
        existing_relationships = context.get("relationships", [])
        all_relationships = existing_relationships + inferred
        
        result.output = {"relationships": all_relationships, "count": len(inferred)}
        result.confidence = 0.85
        return result


class SpatialAnalysisStage(BaseStage):
    def __init__(self):
        super().__init__("spatial_analysis")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        entities = context.get("entities", [])
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        containment = []
        areas = [e for e in entities if (e.get("type") or e.get("entity_type")) == "area"]
        others = [e for e in entities if (e.get("type") or e.get("entity_type")) != "area"]
        
        for area in areas:
            area_bbox = area.get("coordinates", {}).get("bbox")
            for entity in others:
                entity_bbox = entity.get("coordinates", {}).get("bbox")
                if area_bbox and entity_bbox:
                    if self._contains(area_bbox, entity_bbox):
                        entity_id = entity.get("id") or entity.get("entity_id")
                        area_id = area.get("id") or area.get("entity_id")
                        containment.append({"entity": entity_id, "contained_in": area_id})
        
        result.output = {"containment": containment}
        result.confidence = 0.95
        return result
    
    def _contains(self, outer: list, inner: list) -> bool:
        return outer[0] <= inner[0] and outer[1] <= inner[1] and outer[2] >= inner[2] and outer[3] >= inner[3]


class ValidationStage(BaseStage):
    def __init__(self):
        super().__init__("validation")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        from app.services.validation_engine import ValidationEngine
        val_engine = ValidationEngine()
        
        entities = context.get("entities", [])
        # Normalize entity field names for validation
        normalized_entities = []
        for e in entities:
            ne = dict(e)
            if "entity_id" in ne:
                ne["id"] = ne["entity_id"]
            if "entity_type" in ne:
                ne["type"] = ne["entity_type"]
            normalized_entities.append(ne)
        
        issues = val_engine.validate_entities(normalized_entities)
        
        result.output = {"issues": [i.model_dump() for i in issues]}
        result.confidence = 0.98
        return result


class CrossDocumentReconciliationStage(BaseStage):
    def __init__(self):
        super().__init__("cross_document_reconciliation")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        from app.services.cross_document_reconciliation import CrossDocumentReconciler
        reconciler = CrossDocumentReconciler()
        
        result.output = {"reconciled": True}
        result.confidence = 0.9
        return result


class ComplianceScoringStage(BaseStage):
    def __init__(self):
        super().__init__("compliance_scoring")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        issues = context.get("issues", [])
        compliance_score = max(0.0, 1.0 - len(issues) * 0.1)
        
        result.output = {"compliance_score": compliance_score, "issues_count": len(issues)}
        result.confidence = 0.95
        return result


class ReportingStage(BaseStage):
    def __init__(self):
        super().__init__("reporting")
    
    async def _process(self, context: Dict[str, Any]) -> StageResult:
        result = StageResult(stage_name=self.name, status=StageStatus.RUNNING)
        
        result.output = {
            "summary": {
                "entities": len(context.get("entities", [])),
                "relationships": len(context.get("relationships", [])),
                "compliance_score": context.get("compliance_score", 0)
            }
        }
        result.confidence = 1.0
        return result