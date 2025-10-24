"""
Parameter resolution system

Handles resolving parameter references like:
- {{ credential.gateway_admin }} -> actual password from vault
- {{ variable.module_name }} -> value from runtime variables
- {{ parameter.gateway_url }} -> value from playbook parameters
"""

import re
from typing import Any, Dict, Optional
from pathlib import Path

from ignition_toolkit.credentials import CredentialVault
from ignition_toolkit.playbook.exceptions import ParameterResolutionError


class ParameterResolver:
    """
    Resolve parameter references in playbook values

    Supports three types of references:
    1. {{ credential.name }} - Load from credential vault
    2. {{ variable.name }} - Load from runtime variables
    3. {{ parameter.name }} - Load from playbook parameters

    Example:
        resolver = ParameterResolver(
            credential_vault=vault,
            parameters={"gateway_url": "http://localhost:8088"},
            variables={"module_name": "Perspective"}
        )
        resolved = resolver.resolve("{{ credential.gateway_admin }}")
    """

    # Pattern to match {{ type.name }} or {{ name }}
    PATTERN = re.compile(r"\{\{\s*(\w+)(?:\.(\w+))?\s*\}\}")

    def __init__(
        self,
        credential_vault: Optional[CredentialVault] = None,
        parameters: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize parameter resolver

        Args:
            credential_vault: Credential vault for loading credentials
            parameters: Playbook parameters
            variables: Runtime variables
        """
        self.credential_vault = credential_vault
        self.parameters = parameters or {}
        self.variables = variables or {}

    def resolve(self, value: Any) -> Any:
        """
        Resolve parameter references in value

        Args:
            value: Value to resolve (string, dict, list, or primitive)

        Returns:
            Resolved value with references replaced

        Raises:
            ParameterResolutionError: If reference cannot be resolved
        """
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve(item) for item in value]
        else:
            # Primitive value (int, float, bool, None)
            return value

    def _resolve_string(self, value: str) -> Any:
        """
        Resolve references in string value

        Args:
            value: String value (may contain {{ ... }} references)

        Returns:
            Resolved value (string or other type if fully replaced)

        Raises:
            ParameterResolutionError: If reference cannot be resolved
        """
        # Find all matches
        matches = list(self.PATTERN.finditer(value))

        if not matches:
            # No references, return as-is
            return value

        # If the entire string is a single reference, return the actual value
        # (allows non-string values like credentials to be returned)
        # However, for parameters and variables, convert to string to maintain template semantics
        if len(matches) == 1 and matches[0].group(0) == value:
            ref_type = matches[0].group(1)
            ref_name = matches[0].group(2)

            # If ref_name is None, it means bare parameter name like {{ gateway_url }}
            if ref_name is None:
                ref_name = ref_type
                ref_type = "parameter"

            resolved = self._resolve_reference(ref_type, ref_name)

            # For credentials, return as-is (may be Credential object)
            # For parameters/variables in template context, convert to string
            if ref_type == "credential":
                return resolved
            else:
                return str(resolved)

        # Multiple references or mixed content - build string
        result = value
        for match in reversed(matches):  # Reverse to preserve positions
            ref_type = match.group(1)
            ref_name = match.group(2)

            # If ref_name is None, it means bare parameter name like {{ gateway_url }}
            if ref_name is None:
                ref_name = ref_type
                ref_type = "parameter"

            replacement = str(self._resolve_reference(ref_type, ref_name))
            result = result[: match.start()] + replacement + result[match.end() :]

        return result

    def _resolve_reference(self, ref_type: str, ref_name: str) -> Any:
        """
        Resolve individual reference

        Args:
            ref_type: Reference type (credential, variable, parameter)
            ref_name: Reference name

        Returns:
            Resolved value

        Raises:
            ParameterResolutionError: If reference cannot be resolved
        """
        if ref_type == "credential":
            return self._resolve_credential(ref_name)
        elif ref_type == "variable":
            return self._resolve_variable(ref_name)
        elif ref_type == "parameter":
            return self._resolve_parameter(ref_name)
        else:
            raise ParameterResolutionError(
                f"Unknown reference type '{ref_type}' (valid: credential, variable, parameter)"
            )

    def _resolve_credential(self, name: str) -> Any:
        """
        Resolve credential reference

        Args:
            name: Credential name

        Returns:
            Credential object

        Raises:
            ParameterResolutionError: If credential not found
        """
        if self.credential_vault is None:
            raise ParameterResolutionError(
                f"Cannot resolve credential '{name}': no credential vault configured"
            )

        try:
            credential = self.credential_vault.get_credential(name)
            if credential is None:
                raise ParameterResolutionError(f"Credential '{name}' not found in vault")
            return credential
        except Exception as e:
            raise ParameterResolutionError(f"Error loading credential '{name}': {e}")

    def _resolve_variable(self, name: str) -> Any:
        """
        Resolve variable reference

        Args:
            name: Variable name

        Returns:
            Variable value

        Raises:
            ParameterResolutionError: If variable not found
        """
        if name not in self.variables:
            raise ParameterResolutionError(f"Variable '{name}' not found in runtime variables")
        return self.variables[name]

    def _resolve_parameter(self, name: str) -> Any:
        """
        Resolve parameter reference

        Args:
            name: Parameter name

        Returns:
            Parameter value

        Raises:
            ParameterResolutionError: If parameter not found
        """
        if name not in self.parameters:
            raise ParameterResolutionError(f"Parameter '{name}' not found in playbook parameters")
        return self.parameters[name]

    def resolve_file_path(self, path: str, base_path: Optional[Path] = None) -> Path:
        """
        Resolve file path (handle relative paths)

        Args:
            path: File path (may be relative)
            base_path: Base path for resolving relative paths

        Returns:
            Absolute Path object

        Raises:
            ParameterResolutionError: If file not found
        """
        # Resolve any parameter references first
        resolved_path = self.resolve(path)

        if not isinstance(resolved_path, (str, Path)):
            raise ParameterResolutionError(
                f"File path must be string or Path, got {type(resolved_path)}"
            )

        path_obj = Path(resolved_path)

        # Make absolute
        if not path_obj.is_absolute():
            if base_path:
                path_obj = base_path / path_obj
            else:
                path_obj = path_obj.resolve()

        # Validate exists
        if not path_obj.exists():
            raise ParameterResolutionError(f"File not found: {path_obj}")

        return path_obj
