"""
Smoke tests for critical API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from starlette.requests import Request


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    """Root endpoint should return API status."""
    response = client.get("/api")
    assert response.status_code == 200
    assert "message" in response.json()


def test_projects_list_empty(client):
    """Projects list should return empty list when no projects."""
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_upload_missing_project(client):
    """Upload to non-existent project should return 404."""
    files = {"file": ("test.pdf", b"%PDF-1.4", "application/pdf")}
    response = client.post("/api/projects/nonexistent/files", files=files)
    assert response.status_code == 404


def test_chat_missing_project(client):
    """Chat with non-existent project should return error message."""
    response = client.post(
        "/api/projects/nonexistent/chat",
        json={"message": "hello", "history": []}
    )
    assert response.status_code == 200
    assert "response" in response.json()