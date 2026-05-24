"""
Event-driven architecture for pipeline orchestration.
Enables loose coupling between processing stages.
"""
import logging
from typing import Callable, Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class PipelineEventType(str, Enum):
    PARSE_COMPLETED = "parse_completed"
    ENTITIES_RESOLVED = "entities_resolved"
    GRAPH_BUILT = "graph_built"
    VALIDATION_FINISHED = "validation_finished"
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    ARTIFACT_SAVED = "artifact_saved"


@dataclass
class PipelineEvent:
    """Event emitted during pipeline processing."""
    type: PipelineEventType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    project_id: Optional[str] = None
    stage: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None


class EventBus:
    """Simple event bus for intra-system communication."""
    
    def __init__(self):
        self._handlers: Dict[PipelineEventType, List[Callable]] = {}
        self._history: List[PipelineEvent] = []
    
    def subscribe(self, event_type: PipelineEventType, handler: Callable[[PipelineEvent], None]):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def emit(self, event: PipelineEvent):
        self._history.append(event)
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    def get_history(self, event_type: Optional[PipelineEventType] = None) -> List[PipelineEvent]:
        if event_type:
            return [e for e in self._history if e.type == event_type]
        return self._history.copy()
    
    def clear_history(self):
        self._history.clear()


event_bus = EventBus()