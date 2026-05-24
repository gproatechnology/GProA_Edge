"""
Processing contracts for deterministic stage interfaces.
Each stage has well-defined input/output/validation schemas.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProcessingContract(BaseModel):
    """Contract defining stage input/output requirements."""
    stage_name: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    validation_rules: List[str] = Field(default_factory=list)
    confidence_thresholds: Dict[str, float] = Field(default_factory=dict)


class StageResult(BaseModel):
    """Standard result from any processing stage."""
    stage_name: str
    status: StageStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    execution_time_ms: Optional[float] = None