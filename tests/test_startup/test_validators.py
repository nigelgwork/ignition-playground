"""
Tests for startup validators
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

from ignition_toolkit.startup.validators import (
    validate_environment,
    initialize_database,
    initialize_vault,
    validate_playbooks,
    validate_frontend,
)
from ignition_toolkit.startup.exceptions import (
    EnvironmentError,
    DatabaseInitError,
    VaultInitError,
)


@pytest.mark.asyncio
async def test_validate_environment_success():
    """Test successful environment validation"""
    # Should not raise exception with valid environment
    await validate_environment()


@pytest.mark.asyncio
async def test_validate_environment_python_version():
    """Test Python version check"""
    with patch.object(sys, 'version_info', (3, 9)):
        with pytest.raises(EnvironmentError) as exc_info:
            await validate_environment()

        assert "Python 3.10+ required" in str(exc_info.value)
        assert "recovery_hint" in dir(exc_info.value)


@pytest.mark.asyncio
async def test_validate_environment_data_directory(tmp_path):
    """Test data directory creation"""
    # Should create directory if it doesn't exist
    test_db_path = tmp_path / "test_data" / "test.db"

    with patch('ignition_toolkit.startup.validators.get_settings') as mock_settings:
        settings = MagicMock()
        settings.database_path = test_db_path
        settings.vault_path = tmp_path / ".ignition-toolkit" / "vault"
        mock_settings.return_value = settings

        await validate_environment()

        assert test_db_path.parent.exists()


@pytest.mark.asyncio
async def test_initialize_database_success():
    """Test successful database initialization"""
    with patch('ignition_toolkit.startup.validators.get_database') as mock_get_db:
        mock_db = MagicMock()
        mock_db.create_tables = MagicMock()
        mock_db.session_scope = MagicMock()

        # Mock session context manager
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_session.execute.return_value = mock_result

        mock_db.session_scope.return_value.__enter__.return_value = mock_session
        mock_db.session_scope.return_value.__exit__.return_value = None

        mock_get_db.return_value = mock_db

        await initialize_database()

        mock_db.create_tables.assert_called_once()
        mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_database_failure():
    """Test database initialization failure"""
    with patch('ignition_toolkit.startup.validators.get_database') as mock_get_db:
        mock_db = MagicMock()
        mock_db.create_tables.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        with pytest.raises(DatabaseInitError) as exc_info:
            await initialize_database()

        assert "Database initialization failed" in str(exc_info.value)
        assert "recovery_hint" in dir(exc_info.value)


@pytest.mark.asyncio
async def test_initialize_vault_success():
    """Test successful vault initialization"""
    with patch('ignition_toolkit.startup.validators.get_credential_vault') as mock_get_vault:
        mock_vault = MagicMock()
        mock_vault.initialize = MagicMock()
        mock_vault.test_encryption.return_value = True
        mock_get_vault.return_value = mock_vault

        await initialize_vault()

        mock_vault.initialize.assert_called_once()
        mock_vault.test_encryption.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_vault_encryption_failure():
    """Test vault encryption test failure"""
    with patch('ignition_toolkit.startup.validators.get_credential_vault') as mock_get_vault:
        mock_vault = MagicMock()
        mock_vault.initialize = MagicMock()
        mock_vault.test_encryption.return_value = False
        mock_get_vault.return_value = mock_vault

        with pytest.raises(VaultInitError) as exc_info:
            await initialize_vault()

        assert "encryption test failed" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_validate_playbooks_success(tmp_path):
    """Test successful playbook validation"""
    # Create test playbook structure
    playbooks_dir = tmp_path / "playbooks"
    gateway_dir = playbooks_dir / "gateway"
    perspective_dir = playbooks_dir / "perspective"
    examples_dir = playbooks_dir / "examples"

    gateway_dir.mkdir(parents=True)
    perspective_dir.mkdir(parents=True)
    examples_dir.mkdir(parents=True)

    # Create dummy playbooks
    (gateway_dir / "test1.yaml").write_text("test")
    (gateway_dir / "test2.yaml").write_text("test")
    (perspective_dir / "test3.yaml").write_text("test")
    (examples_dir / "test4.yaml").write_text("test")

    with patch('ignition_toolkit.startup.validators.Path') as mock_path:
        mock_path.return_value = playbooks_dir

        stats = await validate_playbooks()

        assert stats["total"] == 4
        assert stats["gateway"] == 2
        assert stats["perspective"] == 1
        assert stats["examples"] == 1


@pytest.mark.asyncio
async def test_validate_playbooks_missing_directory(tmp_path):
    """Test playbook validation with missing directory"""
    nonexistent = tmp_path / "nonexistent"

    with patch('ignition_toolkit.startup.validators.Path') as mock_path:
        mock_path.return_value = nonexistent

        with pytest.raises(Exception) as exc_info:
            await validate_playbooks()

        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_validate_frontend_success(tmp_path):
    """Test successful frontend validation"""
    frontend_dir = tmp_path / "frontend" / "dist"
    frontend_dir.mkdir(parents=True)
    (frontend_dir / "index.html").write_text("<html></html>")

    with patch('ignition_toolkit.startup.validators.get_settings') as mock_settings:
        settings = MagicMock()
        settings.frontend_dir = frontend_dir
        mock_settings.return_value = settings

        await validate_frontend()


@pytest.mark.asyncio
async def test_validate_frontend_missing_directory(tmp_path):
    """Test frontend validation with missing directory"""
    nonexistent = tmp_path / "nonexistent"

    with patch('ignition_toolkit.startup.validators.get_settings') as mock_settings:
        settings = MagicMock()
        settings.frontend_dir = nonexistent
        mock_settings.return_value = settings

        with pytest.raises(Exception) as exc_info:
            await validate_frontend()

        assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_validate_frontend_missing_index_html(tmp_path):
    """Test frontend validation with missing index.html"""
    frontend_dir = tmp_path / "frontend" / "dist"
    frontend_dir.mkdir(parents=True)

    with patch('ignition_toolkit.startup.validators.get_settings') as mock_settings:
        settings = MagicMock()
        settings.frontend_dir = frontend_dir
        mock_settings.return_value = settings

        with pytest.raises(Exception) as exc_info:
            await validate_frontend()

        assert "index.html not found" in str(exc_info.value).lower()
