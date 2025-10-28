"""
Tests for startup lifecycle manager
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI

from ignition_toolkit.startup.exceptions import DatabaseInitError, VaultInitError
from ignition_toolkit.startup.health import HealthStatus, get_health_state, reset_health_state
from ignition_toolkit.startup.lifecycle import lifespan


@pytest.fixture(autouse=True)
def reset_health():
    """Reset health state before each test"""
    reset_health_state()
    yield
    reset_health_state()


@pytest.mark.asyncio
async def test_lifespan_successful_startup():
    """Test successful startup sequence"""
    app = FastAPI()

    with (
        patch(
            "ignition_toolkit.startup.lifecycle.validate_environment", new_callable=AsyncMock
        ) as mock_env,
        patch(
            "ignition_toolkit.startup.lifecycle.initialize_database", new_callable=AsyncMock
        ) as mock_db,
        patch(
            "ignition_toolkit.startup.lifecycle.initialize_vault", new_callable=AsyncMock
        ) as mock_vault,
        patch(
            "ignition_toolkit.startup.lifecycle.validate_playbooks", new_callable=AsyncMock
        ) as mock_playbooks,
        patch(
            "ignition_toolkit.startup.lifecycle.validate_frontend", new_callable=AsyncMock
        ) as mock_frontend,
    ):

        mock_playbooks.return_value = {"total": 5, "gateway": 2, "perspective": 2, "examples": 1}

        async with lifespan(app):
            health = get_health_state()

            # Verify all validators were called
            mock_env.assert_called_once()
            mock_db.assert_called_once()
            mock_vault.assert_called_once()
            mock_playbooks.assert_called_once()

            # Verify system is ready
            assert health.ready is True
            assert health.overall == HealthStatus.HEALTHY
            assert health.database.status == HealthStatus.HEALTHY
            assert health.vault.status == HealthStatus.HEALTHY
            assert health.playbooks.status == HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_lifespan_database_failure():
    """Test startup failure during database initialization"""
    app = FastAPI()

    with (
        patch("ignition_toolkit.startup.lifecycle.validate_environment", new_callable=AsyncMock),
        patch(
            "ignition_toolkit.startup.lifecycle.initialize_database", new_callable=AsyncMock
        ) as mock_db,
    ):

        mock_db.side_effect = DatabaseInitError("Database connection failed")

        with pytest.raises(DatabaseInitError):
            async with lifespan(app):
                pass

        health = get_health_state()
        assert health.ready is False
        assert health.overall == HealthStatus.UNHEALTHY
        assert health.database.status == HealthStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_lifespan_vault_failure():
    """Test startup failure during vault initialization"""
    app = FastAPI()

    with (
        patch("ignition_toolkit.startup.lifecycle.validate_environment", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_database", new_callable=AsyncMock),
        patch(
            "ignition_toolkit.startup.lifecycle.initialize_vault", new_callable=AsyncMock
        ) as mock_vault,
    ):

        mock_vault.side_effect = VaultInitError("Vault encryption failed")

        with pytest.raises(VaultInitError):
            async with lifespan(app):
                pass

        health = get_health_state()
        assert health.ready is False
        assert health.overall == HealthStatus.UNHEALTHY
        assert health.vault.status == HealthStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_lifespan_playbook_validation_non_fatal():
    """Test that playbook validation failures are non-fatal"""
    app = FastAPI()

    with (
        patch("ignition_toolkit.startup.lifecycle.validate_environment", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_database", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_vault", new_callable=AsyncMock),
        patch(
            "ignition_toolkit.startup.lifecycle.validate_playbooks", new_callable=AsyncMock
        ) as mock_playbooks,
        patch("ignition_toolkit.startup.lifecycle.validate_frontend", new_callable=AsyncMock),
    ):

        mock_playbooks.side_effect = Exception("Playbook directory not found")

        # Should not raise - playbook validation is non-fatal
        async with lifespan(app):
            health = get_health_state()

            # System should still be ready
            assert health.ready is True
            # But playbooks should be degraded
            assert health.playbooks.status == HealthStatus.DEGRADED
            assert len(health.warnings) > 0


@pytest.mark.asyncio
async def test_lifespan_frontend_validation_non_fatal():
    """Test that frontend validation failures are non-fatal"""
    app = FastAPI()

    with (
        patch("ignition_toolkit.startup.lifecycle.validate_environment", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_database", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_vault", new_callable=AsyncMock),
        patch(
            "ignition_toolkit.startup.lifecycle.validate_playbooks", new_callable=AsyncMock
        ) as mock_playbooks,
        patch(
            "ignition_toolkit.startup.lifecycle.validate_frontend", new_callable=AsyncMock
        ) as mock_frontend,
        patch("ignition_toolkit.startup.lifecycle.is_dev_mode") as mock_dev,
    ):

        mock_playbooks.return_value = {"total": 3, "gateway": 1, "perspective": 1, "examples": 1}
        mock_frontend.side_effect = Exception("Frontend build not found")
        mock_dev.return_value = False  # Production mode

        # Should not raise - frontend validation is non-fatal
        async with lifespan(app):
            health = get_health_state()

            # System should still be ready
            assert health.ready is True
            # But frontend should be degraded
            assert health.frontend.status == HealthStatus.DEGRADED
            assert len(health.warnings) > 0


@pytest.mark.asyncio
async def test_lifespan_dev_mode_skips_frontend():
    """Test that dev mode skips frontend validation"""
    app = FastAPI()

    with (
        patch("ignition_toolkit.startup.lifecycle.validate_environment", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_database", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_vault", new_callable=AsyncMock),
        patch(
            "ignition_toolkit.startup.lifecycle.validate_playbooks", new_callable=AsyncMock
        ) as mock_playbooks,
        patch(
            "ignition_toolkit.startup.lifecycle.validate_frontend", new_callable=AsyncMock
        ) as mock_frontend,
        patch("ignition_toolkit.startup.lifecycle.is_dev_mode") as mock_dev,
    ):

        mock_playbooks.return_value = {"total": 3, "gateway": 1, "perspective": 1, "examples": 1}
        mock_dev.return_value = True  # Dev mode

        async with lifespan(app):
            # Frontend validation should not have been called
            mock_frontend.assert_not_called()

            health = get_health_state()
            assert health.frontend.status == HealthStatus.HEALTHY
            assert "dev mode" in health.frontend.message.lower()


@pytest.mark.asyncio
async def test_lifespan_degraded_overall_status():
    """Test that warnings result in degraded overall status"""
    app = FastAPI()

    with (
        patch("ignition_toolkit.startup.lifecycle.validate_environment", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_database", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_vault", new_callable=AsyncMock),
        patch(
            "ignition_toolkit.startup.lifecycle.validate_playbooks", new_callable=AsyncMock
        ) as mock_playbooks,
        patch("ignition_toolkit.startup.lifecycle.validate_frontend", new_callable=AsyncMock),
    ):

        mock_playbooks.side_effect = Exception("Some playbooks invalid")

        async with lifespan(app):
            health = get_health_state()

            assert health.ready is True
            assert health.overall == HealthStatus.DEGRADED
            assert len(health.warnings) > 0


@pytest.mark.asyncio
async def test_lifespan_sets_startup_time():
    """Test that startup time is recorded"""
    app = FastAPI()

    with (
        patch("ignition_toolkit.startup.lifecycle.validate_environment", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_database", new_callable=AsyncMock),
        patch("ignition_toolkit.startup.lifecycle.initialize_vault", new_callable=AsyncMock),
        patch(
            "ignition_toolkit.startup.lifecycle.validate_playbooks", new_callable=AsyncMock
        ) as mock_playbooks,
        patch("ignition_toolkit.startup.lifecycle.validate_frontend", new_callable=AsyncMock),
    ):

        mock_playbooks.return_value = {"total": 1, "gateway": 1, "perspective": 0, "examples": 0}

        async with lifespan(app):
            health = get_health_state()

            assert health.startup_time is not None
