"""
Tests for executions router endpoints
"""
import pytest
from fastapi.testclient import TestClient
from ignition_toolkit.api.app import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_list_executions_empty(client):
    """Test listing executions when none exist"""
    response = client.get("/api/executions")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_start_execution_missing_playbook(client):
    """Test starting execution with missing playbook"""
    payload = {
        "playbook_path": "nonexistent.yaml",
        "parameters": {}
    }
    response = client.post("/api/executions/start", json=payload)
    assert response.status_code in [400, 404]


def test_get_execution_status_not_found(client):
    """Test getting status of non-existent execution"""
    response = client.get("/api/executions/999999/status")
    assert response.status_code == 404


def test_pause_execution_not_found(client):
    """Test pausing non-existent execution"""
    response = client.post("/api/executions/999999/pause")
    assert response.status_code == 404


def test_resume_execution_not_found(client):
    """Test resuming non-existent execution"""
    response = client.post("/api/executions/999999/resume")
    assert response.status_code == 404


def test_cancel_execution_not_found(client):
    """Test cancelling non-existent execution"""
    response = client.post("/api/executions/999999/cancel")
    assert response.status_code == 404
