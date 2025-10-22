"""
Tests for parameter resolver
"""

import pytest
import tempfile
from pathlib import Path
from ignition_toolkit.playbook.parameters import ParameterResolver
from ignition_toolkit.playbook.exceptions import ParameterResolutionError
from ignition_toolkit.credentials import CredentialVault, Credential


@pytest.fixture
def temp_vault_dir():
    """Create temporary directory for vault"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def vault_with_credentials(temp_vault_dir):
    """Create vault with test credentials"""
    vault = CredentialVault(vault_path=temp_vault_dir)
    vault.save_credential(Credential(
        name="test_cred",
        username="testuser",
        password="testpass"
    ))
    return vault


def test_resolve_parameter():
    """Test resolving parameter reference"""
    resolver = ParameterResolver(
        parameters={"url": "http://localhost:8088"}
    )

    result = resolver.resolve("{{ parameter.url }}")
    assert result == "http://localhost:8088"


def test_resolve_variable():
    """Test resolving variable reference"""
    resolver = ParameterResolver(
        variables={"step_name": "Login"}
    )

    result = resolver.resolve("{{ variable.step_name }}")
    assert result == "Login"


def test_resolve_credential(vault_with_credentials):
    """Test resolving credential reference"""
    resolver = ParameterResolver(
        credential_vault=vault_with_credentials
    )

    result = resolver.resolve("{{ credential.test_cred }}")
    assert result.username == "testuser"
    assert result.password == "testpass"


def test_resolve_multiple_references():
    """Test resolving multiple references in one string"""
    resolver = ParameterResolver(
        parameters={"host": "localhost", "port": "8088"}
    )

    result = resolver.resolve("http://{{ parameter.host }}:{{ parameter.port }}")
    assert result == "http://localhost:8088"


def test_resolve_dict():
    """Test resolving references in dictionary"""
    resolver = ParameterResolver(
        parameters={"username": "admin", "timeout": 30}
    )

    data = {
        "user": "{{ parameter.username }}",
        "timeout": "{{ parameter.timeout }}",
        "nested": {
            "value": "{{ parameter.username }}"
        }
    }

    result = resolver.resolve(data)
    assert result["user"] == "admin"
    assert result["timeout"] == "30"  # String because of template
    assert result["nested"]["value"] == "admin"


def test_resolve_list():
    """Test resolving references in list"""
    resolver = ParameterResolver(
        parameters={"item1": "first", "item2": "second"}
    )

    data = ["{{ parameter.item1 }}", "{{ parameter.item2 }}"]
    result = resolver.resolve(data)

    assert result == ["first", "second"]


def test_resolve_no_references():
    """Test resolving value with no references"""
    resolver = ParameterResolver()

    result = resolver.resolve("plain text")
    assert result == "plain text"


def test_resolve_primitive_values():
    """Test resolving primitive values"""
    resolver = ParameterResolver()

    assert resolver.resolve(42) == 42
    assert resolver.resolve(3.14) == 3.14
    assert resolver.resolve(True) is True
    assert resolver.resolve(None) is None


def test_missing_parameter():
    """Test error when parameter not found"""
    resolver = ParameterResolver(parameters={})

    with pytest.raises(ParameterResolutionError, match="Parameter 'missing' not found"):
        resolver.resolve("{{ parameter.missing }}")


def test_missing_variable():
    """Test error when variable not found"""
    resolver = ParameterResolver(variables={})

    with pytest.raises(ParameterResolutionError, match="Variable 'missing' not found"):
        resolver.resolve("{{ variable.missing }}")


def test_missing_credential(vault_with_credentials):
    """Test error when credential not found"""
    resolver = ParameterResolver(credential_vault=vault_with_credentials)

    with pytest.raises(ParameterResolutionError, match="Credential 'missing' not found"):
        resolver.resolve("{{ credential.missing }}")


def test_no_vault_configured():
    """Test error when trying to resolve credential without vault"""
    resolver = ParameterResolver()

    with pytest.raises(ParameterResolutionError, match="no credential vault"):
        resolver.resolve("{{ credential.test }}")


def test_unknown_reference_type():
    """Test error with unknown reference type"""
    resolver = ParameterResolver()

    with pytest.raises(ParameterResolutionError, match="Unknown reference type"):
        resolver.resolve("{{ unknown.value }}")


def test_resolve_file_path(temp_vault_dir):
    """Test resolving file path"""
    test_file = temp_vault_dir / "test.txt"
    test_file.write_text("test content")

    resolver = ParameterResolver(
        parameters={"filename": "test.txt"}
    )

    result = resolver.resolve_file_path(
        "{{ parameter.filename }}",
        base_path=temp_vault_dir
    )

    assert result.exists()
    assert result.name == "test.txt"


def test_resolve_nonexistent_file_path(temp_vault_dir):
    """Test error resolving nonexistent file"""
    resolver = ParameterResolver(
        parameters={"filename": "nonexistent.txt"}
    )

    with pytest.raises(ParameterResolutionError, match="File not found"):
        resolver.resolve_file_path(
            "{{ parameter.filename }}",
            base_path=temp_vault_dir
        )


def test_whitespace_in_references():
    """Test that whitespace is handled correctly"""
    resolver = ParameterResolver(
        parameters={"value": "test"}
    )

    # With spaces
    result1 = resolver.resolve("{{  parameter.value  }}")
    assert result1 == "test"

    # With tabs
    result2 = resolver.resolve("{{\tparameter.value\t}}")
    assert result2 == "test"
