"""
Main pipeline orchestrator for Technical Knowledge Graph processing.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .stages import (
    FileIngestionStage, ParsingStage, EntityExtractionStage,
    EntityNormalizationStage, IdentityResolutionStage, RelationshipInferenceStage,
    SpatialAnalysisStage, ValidationStage, CrossDocumentReconciliationStage,
    TruthArbitrationStage, ComplianceScoringStage, ReportingStage
)
from .contracts import StageResult, StageStatus
from .events import PipelineEvent, PipelineEventType, event_bus
from .artifacts import artifact_store

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Orchestrates deterministic processing stages."""
    
    def __init__(self, project_id: str, revision: str = "latest"):
        self.project_id = project_id
        self.revision = revision
        self.context: Dict[str, Any] = {"project_id": project_id}
        self._stage_results: List[StageResult] = []
        self._stages = [
            FileIngestionStage(),
            ParsingStage(),
            EntityExtractionStage(),
            EntityNormalizationStage(),
            IdentityResolutionStage(),
            RelationshipInferenceStage(),
            SpatialAnalysisStage(),
            ValidationStage(),
            CrossDocumentReconciliationStage(),
            TruthArbitrationStage(),
            ComplianceScoringStage(),
            ReportingStage(),
        ]
    
    async def run(self, files: List[Dict[str, Any]], use_cache: bool = True) -> Dict[str, Any]:
        """Execute full pipeline with Semantic GC and Inter-stage Caching (GPT Point 10 & 13)."""
        self.context["files"] = files
        
        event_bus.emit(PipelineEvent(
            type=PipelineEventType.PIPELINE_STARTED,
            project_id=self.project_id,
            payload={"stage_count": len(self._stages)}
        ))
        
        for stage in self._stages:
            # ── INTER-STAGE CACHING (GPT Point 13) ──
            if use_cache:
                cached_data = artifact_store.load(self.project_id, f"{stage.name}.json", self.revision)
                if cached_data:
                    logger.info(f"🚀 Cache hit: Skipping stage '{stage.name}' for project {self.project_id}")
                    # Update context with cached data
                    for key, value in cached_data.items():
                        if key not in self.context:
                            self.context[key] = value
                    
                    # Create a mock result for the summary
                    result = StageResult(
                        stage_name=stage.name,
                        status=StageStatus.COMPLETED,
                        output=cached_data,
                        confidence=1.0, # Cached results are trusted
                        execution_time_ms=0
                    )
                    self._stage_results.append(result)
                    continue

            result = await stage.execute(self.context)
            self._stage_results.append(result)
            
            # Update context with stage output
            for key, value in result.output.items():
                if key not in self.context:
                    self.context[key] = value
            
            self._persist_artifact(stage.name, result.output)
            
            # ── SEMANTIC GC (GPT Point 10) ──
            if stage.name == "entity_extraction":
                if "parsed" in self.context:
                    logger.debug("Semantic GC: Clearing 'parsed' data from pipeline context.")
                    del self.context["parsed"]
        
        event_bus.emit(PipelineEvent(
            type=PipelineEventType.PIPELINE_COMPLETED,
            project_id=self.project_id,
            payload={"stages_completed": len(self._stage_results)}
        ))
        
        return self._build_final_output()
    
    def _persist_artifact(self, stage_name: str, data: Dict[str, Any]):
        artifact_name = stage_name.replace("_", ".") + ".json"
        artifact_store.save(self.project_id, artifact_name, data, self.revision)
        
        event_bus.emit(PipelineEvent(
            type=PipelineEventType.ARTIFACT_SAVED,
            project_id=self.project_id,
            payload={"artifact": artifact_name}
        ))
    
    def _build_final_output(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "revision": self.revision,
            "timestamp": datetime.now().isoformat(),
            "stage_results": [r.model_dump() for r in self._stage_results],
            "summary": {
                "total_stages": len(self._stage_results),
                "completed": sum(1 for r in self._stage_results if r.status.value == "completed"),
                "failed": sum(1 for r in self._stage_results if r.status.value == "failed"),
                "overall_confidence": self._calculate_overall_confidence()
            }
        }
    
    def _calculate_overall_confidence(self) -> float:
        if not self._stage_results:
            return 0.0
        return sum(r.confidence for r in self._stage_results) / len(self._stage_results)
    
    def get_stage_result(self, stage_name: str) -> Optional[StageResult]:
        for result in self._stage_results:
            if result.stage_name == stage_name:
                return result
        return None
    
    async def re_run_from(self, stage_name: str) -> Dict[str, Any]:
        start_idx = next((i for i, s in enumerate(self._stages) if s.name == stage_name), 0)
        
        for stage in self._stages[start_idx:]:
            result = await stage.execute(self.context)
            self._stage_results.append(result)
            self._persist_artifact(stage.name, result.output)
        
        return self._build_final_output()