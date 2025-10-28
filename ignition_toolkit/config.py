"""
Configuration and paths for Ignition Toolkit

Provides consistent, environment-independent paths for data storage.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_environment():
    """
    Set up environment variables for consistent paths

    This must be called before any other imports that depend on environment variables
    (e.g., Playwright, which uses HOME for browser cache).
    """
    # Set consistent Playwright browsers path
    if "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
        browsers_path = Path("/git/ignition-playground/data/.playwright-browsers")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
        logger.debug(f"Set PLAYWRIGHT_BROWSERS_PATH={browsers_path}")


# Call setup immediately on module import
setup_environment()


def get_toolkit_data_dir() -> Path:
    """
    Get the toolkit data directory (credentials, database, etc.)

    Priority order:
    1. IGNITION_TOOLKIT_DATA environment variable (if set)
    2. Project directory: /git/ignition-playground/data/.ignition-toolkit
    3. Fallback: /root/.ignition-toolkit (actual root home, not $HOME)

    This ensures credentials are stored in a consistent location regardless
    of how the HOME environment variable is set by different tools.

    Returns:
        Path to data directory
    """
    # Check environment variable override
    env_path = os.getenv("IGNITION_TOOLKIT_DATA")
    if env_path:
        path = Path(env_path)
        logger.info(f"Using data directory from IGNITION_TOOLKIT_DATA: {path}")
        return path

    # Try to detect if we're running from the project directory
    project_dir = Path("/git/ignition-playground")
    if project_dir.exists():
        # Use project-relative data directory
        data_dir = project_dir / "data" / ".ignition-toolkit"
        logger.debug(f"Using project data directory: {data_dir}")
        return data_dir

    # Fallback to actual root home (not $HOME which can be overridden)
    fallback = Path("/root/.ignition-toolkit")
    logger.debug(f"Using fallback data directory: {fallback}")
    return fallback


def migrate_credentials_if_needed() -> None:
    """
    Check for credentials in old locations and migrate to new location

    Old locations (from when Path.home() was used):
    - /root/.config/claude-work/.ignition-toolkit/
    - /root/.config/claude-personal/.ignition-toolkit/
    - ~/.ignition-toolkit/ (wherever HOME pointed)

    If credentials are found in old location but not in new location,
    copy them over automatically.
    """
    new_location = get_toolkit_data_dir()

    # Don't migrate if new location already has credentials
    if (new_location / "credentials.json").exists():
        logger.debug(f"Credentials already exist in {new_location}, skipping migration")
        return

    # Check old locations
    old_locations = [
        Path("/root/.config/claude-work/.ignition-toolkit"),
        Path("/root/.config/claude-personal/.ignition-toolkit"),
        Path.home() / ".ignition-toolkit",  # Wherever HOME currently points
    ]

    for old_location in old_locations:
        if old_location == new_location:
            continue  # Skip if it's the same as new location

        creds_file = old_location / "credentials.json"
        key_file = old_location / "encryption.key"
        db_file = old_location / "ignition_toolkit.db"

        if creds_file.exists() and key_file.exists():
            logger.info(f"Found credentials in old location: {old_location}")
            logger.info(f"Migrating to new location: {new_location}")

            # Create new location
            new_location.mkdir(parents=True, exist_ok=True)

            # Copy files
            import shutil

            shutil.copy2(creds_file, new_location / "credentials.json")
            shutil.copy2(key_file, new_location / "encryption.key")

            # Copy database if it exists and has data
            if db_file.exists() and db_file.stat().st_size > 0:
                dest_db = new_location / "ignition_toolkit.db"
                # Only copy if destination doesn't exist or is smaller
                if not dest_db.exists() or dest_db.stat().st_size < db_file.stat().st_size:
                    shutil.copy2(db_file, dest_db)
                    logger.info(f"  - Copied database: {db_file.stat().st_size} bytes")

            # Copy metadata if it exists
            metadata_file = old_location / "playbook_metadata.json"
            if metadata_file.exists():
                shutil.copy2(metadata_file, new_location / "playbook_metadata.json")

            logger.info(f"✓ Migration complete from {old_location}")
            return  # Only migrate from first found location

    logger.debug("No old credentials found to migrate")
