"""
Tests for credential vault
"""

import pytest
import tempfile
from pathlib import Path
from ignition_toolkit.credentials import CredentialVault, Credential


@pytest.fixture
def temp_vault_dir():
    """Create temporary directory for vault"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def vault(temp_vault_dir):
    """Create credential vault in temp directory"""
    return CredentialVault(vault_path=temp_vault_dir)


def test_credential_creation():
    """Test creating a credential"""
    cred = Credential(
        name="test_cred",
        username="testuser",
        password="testpass",
        description="Test credential"
    )

    assert cred.name == "test_cred"
    assert cred.username == "testuser"
    assert cred.password == "testpass"
    assert cred.description == "Test credential"


def test_vault_initialization(vault):
    """Test vault initialization"""
    assert vault.vault_path.exists()
    assert vault.encryption_key_path.exists()


def test_save_and_get_credential(vault):
    """Test saving and retrieving credential"""
    cred = Credential(
        name="gateway_admin",
        username="admin",
        password="secret123"
    )

    vault.save_credential(cred)
    retrieved = vault.get_credential("gateway_admin")

    assert retrieved is not None
    assert retrieved.name == "gateway_admin"
    assert retrieved.username == "admin"
    assert retrieved.password == "secret123"


def test_list_credentials(vault):
    """Test listing credentials"""
    cred1 = Credential(name="cred1", username="user1", password="pass1")
    cred2 = Credential(name="cred2", username="user2", password="pass2")

    vault.save_credential(cred1)
    vault.save_credential(cred2)

    credentials = vault.list_credentials()

    assert len(credentials) == 2
    names = [c.name for c in credentials]
    assert "cred1" in names
    assert "cred2" in names


def test_delete_credential(vault):
    """Test deleting credential"""
    cred = Credential(name="temp_cred", username="temp", password="temp")

    vault.save_credential(cred)
    assert vault.get_credential("temp_cred") is not None

    vault.delete_credential("temp_cred")
    assert vault.get_credential("temp_cred") is None


def test_update_credential(vault):
    """Test updating existing credential"""
    cred = Credential(name="update_test", username="user1", password="pass1")
    vault.save_credential(cred)

    # Update with new password
    updated = Credential(name="update_test", username="user1", password="newpass")
    vault.save_credential(updated)

    retrieved = vault.get_credential("update_test")
    assert retrieved.password == "newpass"


def test_credential_encryption(vault):
    """Test that credentials are encrypted on disk"""
    cred = Credential(name="secret", username="admin", password="supersecret")
    vault.save_credential(cred)

    # Read raw file
    creds_file = vault.vault_path / "credentials.json"
    content = creds_file.read_text()

    # Password should not appear in plaintext
    assert "supersecret" not in content


def test_get_nonexistent_credential(vault):
    """Test getting credential that doesn't exist"""
    result = vault.get_credential("nonexistent")
    assert result is None


def test_delete_nonexistent_credential(vault):
    """Test deleting credential that doesn't exist"""
    # Should not raise error
    vault.delete_credential("nonexistent")
