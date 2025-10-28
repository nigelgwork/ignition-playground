"""
Tests for startup health state management
"""

from datetime import datetime

import pytest

from ignition_toolkit.startup.health import (
    ComponentHealth,
    HealthStatus,
    SystemHealth,
    get_health_state,
    reset_health_state,
    set_component_degraded,
    set_component_healthy,
    set_component_unhealthy,
)


@pytest.fixture(autouse=True)
def reset_health():
    """Reset health state before each test"""
    reset_health_state()
    yield
    reset_health_state()


def test_health_status_enum():
    """Test HealthStatus enum values"""
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"
    assert HealthStatus.UNHEALTHY.value == "unhealthy"
    assert HealthStatus.UNKNOWN.value == "unknown"


def test_component_health_creation():
    """Test ComponentHealth dataclass creation"""
    comp = ComponentHealth(status=HealthStatus.HEALTHY, message="Test message", error=None)

    assert comp.status == HealthStatus.HEALTHY
    assert comp.message == "Test message"
    assert comp.error is None
    assert isinstance(comp.last_checked, datetime)


def test_component_health_to_dict():
    """Test ComponentHealth serialization"""
    comp = ComponentHealth(
        status=HealthStatus.UNHEALTHY, message="Failed", error="Connection timeout"
    )

    data = comp.to_dict()

    assert data["status"] == "unhealthy"
    assert data["message"] == "Failed"
    assert data["error"] == "Connection timeout"
    assert "last_checked" in data


def test_system_health_creation():
    """Test SystemHealth dataclass creation"""
    health = SystemHealth()

    assert health.overall == HealthStatus.UNKNOWN
    assert health.ready is False
    assert health.startup_time is None
    assert health.database.status == HealthStatus.UNKNOWN
    assert health.vault.status == HealthStatus.UNKNOWN
    assert health.playbooks.status == HealthStatus.UNKNOWN
    assert health.frontend.status == HealthStatus.UNKNOWN
    assert health.errors == []
    assert health.warnings == []


def test_system_health_to_dict():
    """Test SystemHealth serialization"""
    health = SystemHealth()
    health.overall = HealthStatus.HEALTHY
    health.ready = True
    health.startup_time = datetime.utcnow()

    data = health.to_dict()

    assert data["overall"] == "healthy"
    assert data["ready"] is True
    assert data["startup_time"] is not None
    assert "components" in data
    assert "database" in data["components"]
    assert "errors" in data
    assert "warnings" in data


def test_get_health_state_singleton():
    """Test that get_health_state returns singleton"""
    health1 = get_health_state()
    health2 = get_health_state()

    assert health1 is health2


def test_set_component_healthy():
    """Test marking component as healthy"""
    set_component_healthy("database", "Database operational")

    health = get_health_state()
    assert health.database.status == HealthStatus.HEALTHY
    assert health.database.message == "Database operational"
    assert health.database.error is None


def test_set_component_unhealthy():
    """Test marking component as unhealthy"""
    set_component_unhealthy("vault", "Encryption failed")

    health = get_health_state()
    assert health.vault.status == HealthStatus.UNHEALTHY
    assert health.vault.error == "Encryption failed"
    assert "vault: Encryption failed" in health.errors


def test_set_component_degraded():
    """Test marking component as degraded"""
    set_component_degraded("playbooks", "No playbooks found")

    health = get_health_state()
    assert health.playbooks.status == HealthStatus.DEGRADED
    assert health.playbooks.error == "No playbooks found"
    assert "playbooks: No playbooks found" in health.warnings


def test_multiple_errors():
    """Test multiple component errors"""
    set_component_unhealthy("database", "Connection failed")
    set_component_unhealthy("vault", "Key missing")

    health = get_health_state()
    assert len(health.errors) == 2
    assert "database: Connection failed" in health.errors
    assert "vault: Key missing" in health.errors


def test_multiple_warnings():
    """Test multiple component warnings"""
    set_component_degraded("playbooks", "Warning 1")
    set_component_degraded("frontend", "Warning 2")

    health = get_health_state()
    assert len(health.warnings) == 2


def test_reset_health_state():
    """Test resetting health state"""
    set_component_healthy("database", "OK")
    set_component_unhealthy("vault", "Failed")

    health = get_health_state()
    assert health.database.status == HealthStatus.HEALTHY
    assert len(health.errors) > 0

    reset_health_state()

    new_health = get_health_state()
    assert new_health.database.status == HealthStatus.UNKNOWN
    assert len(new_health.errors) == 0
    assert len(new_health.warnings) == 0


def test_health_state_persistence():
    """Test that health state persists across get_health_state calls"""
    set_component_healthy("database", "Test")

    health1 = get_health_state()
    health2 = get_health_state()

    assert health1.database.status == health2.database.status
    assert health1.database.message == health2.database.message
