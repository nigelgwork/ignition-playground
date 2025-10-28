"""
Tests for AI router endpoints
"""

import pytest
from fastapi.testclient import TestClient

from ignition_toolkit.api.app import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_list_ai_credentials(client):
    """Test listing AI credentials"""
    response = client.get("/api/ai/credentials")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_get_ai_settings(client):
    """Test getting AI settings"""
    response = client.get("/api/ai/settings")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)


def test_create_ai_credential_missing_fields(client):
    """Test creating AI credential with missing fields"""
    payload = {
        "name": "test_ai"
        # Missing api_key
    }
    response = client.post("/api/ai/credentials", json=payload)
    assert response.status_code == 422  # Validation error


def test_update_ai_credential_not_found(client):
    """Test updating non-existent AI credential"""
    payload = {"api_key": "new-key"}
    response = client.put("/api/ai/credentials/nonexistent", json=payload)
    assert response.status_code == 404


def test_delete_ai_credential_not_found(client):
    """Test deleting non-existent AI credential"""
    response = client.delete("/api/ai/credentials/nonexistent")
    assert response.status_code == 404


def test_ai_assist_not_configured(client):
    """Test AI assist without configuration"""
    payload = {"execution_id": 1, "prompt": "Help me debug this"}
    response = client.post("/api/ai/assist", json=payload)
    # Should return error if AI not configured
    assert response.status_code in [400, 404, 500]
