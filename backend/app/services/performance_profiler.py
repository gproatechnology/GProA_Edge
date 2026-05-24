"""
Performance profiling for pipeline stages.
"""
import time
import tracemalloc
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class StageProfile:
    stage_name: str
    duration_ms: float = 0.0
    memory_peak_kb: int = 0
    entity_count: int = 0
    relationship_count: int = 0
    start_time: float = 0.0


@dataclass
class PipelineProfile:
    project_id: str
    revision: str = "latest"
    stages: List[StageProfile] = field(default_factory=list)
    total_duration_ms: float = 0.0
    total_memory_kb: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "revision": self.revision,
            "total_duration_ms": self.total_duration_ms,
            "total_memory_kb": self.total_memory_kb,
            "stages": [
                {
                    "name": s.stage_name,
                    "duration_ms": s.duration_ms,
                    "memory_peak_kb": s.memory_peak_kb,
                    "entity_count": s.entity_count,
                    "relationship_count": s.relationship_count
                }
                for s in self.stages
            ]
        }


class PerformanceProfiler:
    """Profile pipeline performance."""
    
    def __init__(self, project_id: str):
        self.profile = PipelineProfile(project_id=project_id)
        self.current_stage: Optional[StageProfile] = None
    
    @contextmanager
    def stage(self, name: str):
        """Context manager for profiling a stage."""
        stage_profile = StageProfile(stage_name=name, start_time=time.time())
        self.current_stage = stage_profile
        
        tracemalloc.start()
        start = time.time()
        
        try:
            yield stage_profile
        finally:
            end = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            stage_profile.duration_ms = (end - start) * 1000
            stage_profile.memory_peak_kb = peak // 1024
            
            self.profile.stages.append(stage_profile)
            self.current_stage = None
    
    def set_entity_count(self, count: int):
        if self.current_stage:
            self.current_stage.entity_count = count
    
    def set_relationship_count(self, count: int):
        if self.current_stage:
            self.current_stage.relationship_count = count
    
    def finalize(self):
        self.profile.total_duration_ms = sum(s.duration_ms for s in self.profile.stages)
        self.profile.total_memory_kb = max(s.memory_peak_kb for s in self.profile.stages)
    
    @classmethod
    def profile_pipeline(cls, project_id: str, pipeline_func):
        """Decorator to profile a pipeline run."""
        async def wrapper(*args, **kwargs):
            profiler = cls(project_id)
            
            with profiler.stage("total"):
                result = await pipeline_func(*args, **kwargs)
            
            profiler.finalize()
            return result, profiler.profile
        
        return wrapper


profiler = PerformanceProfiler