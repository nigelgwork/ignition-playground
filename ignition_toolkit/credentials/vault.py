"""
Credential vault for secure local storage
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, UTC

from ignition_toolkit.credentials.models import Credential
from ignition_toolkit.credentials.encryption import CredentialEncryption

logger = logging.getLogger(__name__)


class CredentialVault:
    """
    Secure credential storage with Fernet encryption

    Credentials are stored in ~/.ignition-toolkit/credentials.json (encrypted)
    Encryption key is stored in ~/.ignition-toolkit/encryption.key

    Both files are excluded from git via .gitignore
    """

    def __init__(self, vault_path: Optional[Path] = None):
        """
        Initialize credential vault

        Args:
            vault_path: Path to vault directory. If None, uses ~/.ignition-toolkit/
        """
        if vault_path is None:
            vault_path = Path.home() / ".ignition-toolkit"

        self.vault_path = vault_path
        self.credentials_file = vault_path / "credentials.json"
        self.encryption_key_path = vault_path / "encryption.key"
        self.encryption = CredentialEncryption(self.encryption_key_path)

        # Ensure vault directory exists
        self.vault_path.mkdir(parents=True, exist_ok=True)

        # Ensure credentials file exists
        if not self.credentials_file.exists():
            self._save_credentials_file({})

    def _save_credentials_file(self, data: dict) -> None:
        """Save credentials to encrypted file"""
        # Encrypt the entire JSON structure
        json_str = json.dumps(data, indent=2)
        encrypted = self.encryption.encrypt(json_str)

        self.credentials_file.write_text(encrypted)
        self.credentials_file.chmod(0o600)  # Owner read/write only

        logger.debug(f"Credentials saved to {self.credentials_file}")

    def _load_credentials_file(self) -> dict:
        """Load credentials from encrypted file"""
        if not self.credentials_file.exists():
            return {}

        encrypted = self.credentials_file.read_text()

        try:
            json_str = self.encryption.decrypt(encrypted)
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise ValueError("Failed to decrypt credentials. Key may be corrupted.") from e

    def save_credential(self, credential: Credential) -> None:
        """
        Save or update a credential

        Args:
            credential: Credential to save
        """
        credentials_data = self._load_credentials_file()

        # Encrypt the password before storing
        encrypted_password = self.encryption.encrypt(credential.password)

        # Store credential data
        credentials_data[credential.name] = {
            "name": credential.name,
            "username": credential.username,
            "password": encrypted_password,  # Already encrypted
            "description": credential.description,
            "created_at": credential.created_at.isoformat() if credential.created_at else datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        self._save_credentials_file(credentials_data)
        logger.info(f"Credential '{credential.name}' saved successfully")

    def get_credential(self, name: str) -> Optional[Credential]:
        """
        Retrieve a credential by name

        Args:
            name: Credential name

        Returns:
            Credential object with decrypted password, or None if not found
        """
        credentials_data = self._load_credentials_file()

        if name not in credentials_data:
            logger.warning(f"Credential '{name}' not found")
            return None

        cred_data = credentials_data[name]

        # Decrypt password
        decrypted_password = self.encryption.decrypt(cred_data["password"])

        # Create credential object
        return Credential(
            name=cred_data["name"],
            username=cred_data["username"],
            password=decrypted_password,
            description=cred_data.get("description"),
            created_at=datetime.fromisoformat(cred_data["created_at"]) if cred_data.get("created_at") else None,
            updated_at=datetime.fromisoformat(cred_data["updated_at"]) if cred_data.get("updated_at") else None,
        )

    def list_credentials(self) -> List[Credential]:
        """
        List all stored credentials (without passwords)

        Returns:
            List of Credential objects with empty passwords
        """
        credentials_data = self._load_credentials_file()

        credentials = []
        for name, cred_data in credentials_data.items():
            credentials.append(Credential(
                name=cred_data["name"],
                username=cred_data["username"],
                password="<encrypted>",  # Don't return actual password
                description=cred_data.get("description"),
                created_at=datetime.fromisoformat(cred_data["created_at"]) if cred_data.get("created_at") else None,
                updated_at=datetime.fromisoformat(cred_data["updated_at"]) if cred_data.get("updated_at") else None,
            ))

        return sorted(credentials, key=lambda c: c.name)

    def delete_credential(self, name: str) -> bool:
        """
        Delete a credential

        Args:
            name: Credential name

        Returns:
            True if deleted, False if not found
        """
        credentials_data = self._load_credentials_file()

        if name not in credentials_data:
            logger.warning(f"Credential '{name}' not found for deletion")
            return False

        del credentials_data[name]
        self._save_credentials_file(credentials_data)

        logger.info(f"Credential '{name}' deleted")
        return True

    def credential_exists(self, name: str) -> bool:
        """
        Check if a credential exists

        Args:
            name: Credential name

        Returns:
            True if exists, False otherwise
        """
        credentials_data = self._load_credentials_file()
        return name in credentials_data
