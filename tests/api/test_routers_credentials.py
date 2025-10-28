"""
Tests for credentials router endpoints
"""

import pytest
from fastapi.testclient import TestClient

from ignition_toolkit.api.app import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_list_credentials(client):
    """Test listing credentials"""
    response = client.get("/api/credentials")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_add_credential_missing_fields(client):
    """Test adding credential with missing fields"""
    payload = {
        "name": "test_credential"
        # Missing username and password
    }
    response = client.post("/api/credentials", json=payload)
    assert response.status_code == 422  # Validation error


def test_add_credential_invalid_name(client):
    """Test adding credential with invalid name"""
    payload = {"name": "", "username": "testuser", "password": "testpass"}  # Empty name
    response = client.post("/api/credentials", json=payload)
    assert response.status_code == 422  # Validation error


def test_update_credential_not_found(client):
    """Test updating non-existent credential"""
    payload = {"username": "newuser", "password": "newpass"}
    response = client.put("/api/credentials/nonexistent", json=payload)
    assert response.status_code == 404


def test_delete_credential_not_found(client):
    """Test deleting non-existent credential"""
    response = client.delete("/api/credentials/nonexistent")
    assert response.status_code == 404
