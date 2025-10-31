#!/usr/bin/env python3
"""Test script to trace credential parameter flow"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from ignition_toolkit.credentials import CredentialVault, Credential
from ignition_toolkit.playbook.loader import PlaybookLoader
from ignition_toolkit.playbook.parameters import ParameterResolver
from ignition_toolkit.playbook.models import ParameterType


async def main():
    # Initialize credential vault
    vault = CredentialVault()

    # Create test credential if it doesn't exist
    try:
        test_cred = vault.get_credential("localgateway")
        if not test_cred:
            test_cred = Credential(
                name="localgateway",
                username="admin",
                password="password",
                gateway_url="http://localhost:9088",
                description="Test credential"
            )
            vault.save_credential(test_cred)
    except Exception as e:
        print(f"Error setting up credential: {e}")
        return

    # Load the playbook
    playbook = PlaybookLoader.load_from_file(Path("playbooks/designer/launch_designer_shortcut.yaml"))

    print(f"\n=== PLAYBOOK INFO ===")
    print(f"Name: {playbook.name}")
    print(f"Version: {playbook.version}")
    print(f"Parameters: {[p.name for p in playbook.parameters]}")

    # Simulate user input parameters
    user_parameters = {
        "designer_shortcut": "C:\\test.exe",
        "project_name": "TestProject",
        "gateway_credential": "localgateway"  # This is the credential NAME
    }

    print(f"\n=== USER PARAMETERS ===")
    for k, v in user_parameters.items():
        print(f"  {k}: type={type(v).__name__}, value={v}")

    # Simulate what engine.py does - preprocess credential parameters
    print(f"\n=== PREPROCESSING CREDENTIALS ===")
    result = user_parameters.copy()

    for param_def in playbook.parameters:
        if param_def.type == ParameterType.CREDENTIAL:
            param_name = param_def.name
            credential_name = user_parameters.get(param_name)

            print(f"Found credential parameter: {param_name}")
            print(f"  Credential name: {credential_name}")

            # Fetch credential from vault
            credential = vault.get_credential(credential_name)
            print(f"  Fetched credential: type={type(credential).__name__}, username={credential.username if credential else None}")

            # Replace string with Credential object
            result[param_name] = credential

    print(f"\n=== PREPROCESSED PARAMETERS ===")
    for k, v in result.items():
        print(f"  {k}: type={type(v).__name__}, value={v if not hasattr(v, 'password') else f'Credential(username={v.username})'}")

    # Create parameter resolver
    resolver = ParameterResolver(
        credential_vault=vault,
        parameters=result,  # Use preprocessed parameters
        variables={},
        step_results={}
    )

    # Simulate resolving step parameters (what happens in step_executor.py)
    print(f"\n=== RESOLVING STEP PARAMETERS ===")
    step_params = {
        "designer_shortcut": "{{ designer_shortcut }}",
        "project_name": "{{ project_name }}",
        "gateway_credential": "{{ gateway_credential }}",
        "timeout": 60
    }

    print(f"Step parameters before resolution:")
    for k, v in step_params.items():
        print(f"  {k}: {v}")

    resolved_params = resolver.resolve(step_params)

    print(f"\nResolved step parameters:")
    for k, v in resolved_params.items():
        value_str = f"Credential(username={v.username})" if hasattr(v, 'password') else v
        print(f"  {k}: type={type(v).__name__}, value={value_str}")

    # Test if credential object is preserved
    print(f"\n=== VALIDATION ===")
    gw_cred = resolved_params.get("gateway_credential")
    if isinstance(gw_cred, Credential):
        print(f"✓ SUCCESS: gateway_credential is a Credential object")
        print(f"  Username: {gw_cred.username}")
        print(f"  Has password: {bool(gw_cred.password)}")
    else:
        print(f"✗ FAILED: gateway_credential is type {type(gw_cred).__name__}, not Credential")


if __name__ == "__main__":
    asyncio.run(main())
