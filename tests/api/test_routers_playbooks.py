"""
Tests for playbooks router endpoints
"""
import pytest
from fastapi.testclient import TestClient
from ignition_toolkit.api.app import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_list_playbooks(client):
    """Test listing playbooks"""
    response = client.get("/api/playbooks")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Verify playbook structure if any exist
    if len(data) > 0:
        playbook = data[0]
        assert "path" in playbook
        assert "name" in playbook


def test_list_playbooks_with_domain_filter(client):
    """Test listing playbooks with domain filter"""
    response = client.get("/api/playbooks?domain=gateway")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_get_playbook_not_found(client):
    """Test getting non-existent playbook"""
    response = client.get("/api/playbooks/nonexistent.yaml")
    assert response.status_code == 404


def test_delete_playbook_not_found(client):
    """Test deleting non-existent playbook"""
    response = client.delete("/api/playbooks/nonexistent.yaml")
    assert response.status_code == 404
