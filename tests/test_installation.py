"""
Test basic installation and imports
"""

import pytest


def test_package_imports():
    """Test that main package can be imported"""
    import ignition_toolkit
    assert ignition_toolkit.__version__ == "1.0.1"


def test_gateway_client_import():
    """Test Gateway client can be imported"""
    from ignition_toolkit.gateway import GatewayClient
    assert GatewayClient is not None


def test_credential_vault_import():
    """Test Credential vault can be imported"""
    from ignition_toolkit.credentials import CredentialVault
    assert CredentialVault is not None


def test_database_import():
    """Test Database can be imported"""
    from ignition_toolkit.storage import Database
    assert Database is not None


def test_models_import():
    """Test all models can be imported"""
    from ignition_toolkit.gateway import Module, Project, Tag
    from ignition_toolkit.credentials import Credential
    from ignition_toolkit.storage import ExecutionModel

    assert Module is not None
    assert Project is not None
    assert Tag is not None
    assert Credential is not None
    assert ExecutionModel is not None
