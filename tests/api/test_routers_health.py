"""
Tests for health router endpoints
"""

import pytest
from fastapi.testclient import TestClient

from ignition_toolkit.api.app import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_health_check(client):
    """Test basic health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "version" in data
    assert data["version"] == "3.0.0"


def test_liveness_probe(client):
    """Test liveness probe endpoint"""
    response = client.get("/health/live")
    assert response.status_code == 200

    data = response.json()
    assert data.get("alive") is True


def test_readiness_probe(client):
    """Test readiness probe endpoint"""
    response = client.get("/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert "ready" in data
    assert "components" in data


def test_detailed_health(client):
    """Test detailed health status endpoint"""
    response = client.get("/health/detailed")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "components" in data

    # Verify component structure
    components = data["components"]
    expected_components = ["database", "vault", "playbooks", "frontend"]
    for component in expected_components:
        assert component in components
        assert "status" in components[component]
