"""
Tests for rate limiting middleware.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_rate_limiter_exists():
    """Rate limiter should be configured on app state."""
    from slowapi import Limiter
    assert hasattr(app.state, "limiter")
    assert isinstance(app.state.limiter, Limiter)


def test_assistant_rate_limit():
    """Assistant endpoint should have rate limit configured."""
    from app.api.endpoints.assistant import limiter as assistant_limiter
    assert assistant_limiter is not None