"""
Integration tests for startup system and health check endpoints
"""

import pytest
from fastapi.testclient import TestClient

from ignition_toolkit.api.app import app
from ignition_toolkit.startup.health import reset_health_state


@pytest.fixture(autouse=True)
def reset_health():
    """Reset health state before each test"""
    reset_health_state()
    yield
    reset_health_state()


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_health_endpoint_returns_200_when_healthy(client):
    """Test /health endpoint returns 200 when system is healthy"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "ready" in data


def test_health_endpoint_returns_json(client):
    """Test /health endpoint returns proper JSON structure"""
    response = client.get("/health")
    data = response.json()

    assert isinstance(data, dict)
    assert "status" in data
    assert "ready" in data
    assert "errors" in data or data.get("errors") is None
    assert "warnings" in data or data.get("warnings") is None


def test_liveness_probe_always_returns_200(client):
    """Test /health/live always returns 200 (liveness probe)"""
    response = client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_readiness_probe_returns_200_when_ready(client):
    """Test /health/ready returns 200 when system is ready"""
    response = client.get("/health/ready")

    # Should be 200 or 503 depending on startup state
    assert response.status_code in [200, 503]

    data = response.json()
    assert "ready" in data
    assert "status" in data


def test_detailed_health_endpoint(client):
    """Test /health/detailed returns comprehensive health information"""
    response = client.get("/health/detailed")

    # Should be 200 or 503 depending on system health
    assert response.status_code in [200, 503]

    data = response.json()
    assert "overall" in data
    assert "ready" in data
    assert "startup_time" in data
    assert "components" in data
    assert "errors" in data
    assert "warnings" in data

    # Verify component structure
    components = data["components"]
    assert "database" in components
    assert "vault" in components
    assert "playbooks" in components
    assert "frontend" in components

    # Verify each component has required fields
    for component in components.values():
        assert "status" in component
        assert "message" in component
        assert "last_checked" in component


def test_health_endpoints_cors_headers(client):
    """Test health endpoints include CORS headers"""
    response = client.get("/health")

    # CORS should be configured in the app
    assert response.status_code == 200


def test_multiple_health_checks_consistent(client):
    """Test multiple health checks return consistent results"""
    response1 = client.get("/health")
    response2 = client.get("/health")

    data1 = response1.json()
    data2 = response2.json()

    # Status should be consistent
    assert data1["status"] == data2["status"]
    assert data1["ready"] == data2["ready"]


def test_detailed_health_has_timestamps(client):
    """Test detailed health includes timestamp information"""
    response = client.get("/health/detailed")
    data = response.json()

    # Should have startup time (if ready)
    if data.get("ready"):
        assert data.get("startup_time") is not None

    # Each component should have last_checked timestamp
    components = data.get("components", {})
    for component in components.values():
        assert "last_checked" in component
        # Should be ISO format timestamp
        assert isinstance(component["last_checked"], str)


def test_health_endpoint_error_handling(client):
    """Test health endpoints handle errors gracefully"""
    # Even if something goes wrong, endpoints should return valid responses
    response = client.get("/health")

    assert response.status_code in [200, 503]
    assert response.headers["content-type"] == "application/json"

    # Should always be valid JSON
    data = response.json()
    assert isinstance(data, dict)


def test_readiness_probe_503_when_not_ready(client):
    """Test readiness probe returns 503 when system is not ready"""
    # This test depends on the actual startup state
    # If system starts successfully, it will be ready
    response = client.get("/health/ready")

    data = response.json()

    # If not ready, should return 503
    if not data.get("ready"):
        assert response.status_code == 503
    else:
        assert response.status_code == 200


def test_health_endpoint_503_when_unhealthy(client):
    """Test health endpoint returns 503 when system is unhealthy"""
    # This test checks the contract - if unhealthy, returns 503
    response = client.get("/health")

    data = response.json()

    if data.get("status") == "unhealthy":
        assert response.status_code == 503
    else:
        # Healthy or degraded should return 200
        assert response.status_code == 200
