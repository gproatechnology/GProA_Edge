"""
Tests for pipeline orchestration.
"""
import pytest
import asyncio
from app.services.pipeline import ProcessingPipeline
from app.services.pipeline.events import event_bus, PipelineEventType


@pytest.mark.asyncio
async def test_pipeline_basic():
    """Test basic pipeline execution."""
    pipeline = ProcessingPipeline(project_id="test_001", revision="v1")
    result = await pipeline.run([{"path": "dummy.dxf", "type": "dxf"}])
    
    assert result["project_id"] == "test_001"
    assert result["summary"]["total_stages"] >= 9
    assert "stage_results" in result


@pytest.mark.asyncio
async def test_pipeline_events():
    """Test event emission during pipeline execution."""
    events = []
    
    def capture(event):
        events.append(event)
    
    event_bus.subscribe(PipelineEventType.STAGE_COMPLETED, capture)
    
    pipeline = ProcessingPipeline(project_id="test_002")
    await pipeline.run([{"path": "dummy.dxf", "type": "dxf"}])
    
    assert len(events) >= 9
    assert events[0].type == PipelineEventType.STAGE_COMPLETED


def test_artifact_persistence():
    """Test artifact saving and loading."""
    from app.services.pipeline.artifacts import artifact_store
    
    test_data = {"entities": [{"id": "test1", "type": "area"}]}
    artifact_store.save("proj1", "test.json", test_data)
    
    loaded = artifact_store.load("proj1", "test.json")
    assert loaded == test_data


if __name__ == "__main__":
    asyncio.run(test_pipeline_basic())
    asyncio.run(test_pipeline_events())
    test_artifact_persistence()