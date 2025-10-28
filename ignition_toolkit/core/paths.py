"""
Dynamic path resolution for Ignition Toolkit.

Solves ISSUE-001: Server fails to start from different directories due to hardcoded paths.

This module provides reliable path resolution that works regardless of:
- Current working directory
- Where the server is started from
- Installation method (pip install -e . vs direct run)

All paths are calculated dynamically from the installed package location.
"""

import os
from pathlib import Path

# === Core Project Structure ===


def get_package_root() -> Path:
    """
    Get the root directory of the ignition_toolkit package.

    This is the directory containing the ignition_toolkit/ folder,
    calculated dynamically from this file's location.

    Returns:
        Path: Absolute path to package root (e.g., /git/ignition-playground)

    Example:
        >>> root = get_package_root()
        >>> print(root)
        /git/ignition-playground
    """
    # This file is at: ignition_toolkit/core/paths.py
    # Package root is 2 levels up
    return Path(__file__).parent.parent.parent.resolve()


def get_package_dir() -> Path:
    """
    Get the ignition_toolkit package directory.

    Returns:
        Path: Absolute path to ignition_toolkit/ directory

    Example:
        >>> pkg = get_package_dir()
        >>> print(pkg)
        /git/ignition-playground/ignition_toolkit
    """
    # This file is at: ignition_toolkit/core/paths.py
    # Package dir is 2 levels up
    return Path(__file__).parent.parent.resolve()


# === Playbook Paths ===


def get_playbooks_dir() -> Path:
    """
    Get the playbooks directory.

    Returns:
        Path: Absolute path to playbooks/ directory

    Example:
        >>> playbooks = get_playbooks_dir()
        >>> print(playbooks)
        /git/ignition-playground/playbooks
    """
    return get_package_root() / "playbooks"


def get_playbook_path(playbook_name: str) -> Path:
    """
    Get the full path to a playbook file.

    Args:
        playbook_name: Name of the playbook (with or without .yaml extension)

    Returns:
        Path: Absolute path to playbook file

    Example:
        >>> path = get_playbook_path("gateway_login.yaml")
        >>> print(path)
        /git/ignition-playground/playbooks/gateway_login.yaml
    """
    if not playbook_name.endswith((".yaml", ".yml")):
        playbook_name = f"{playbook_name}.yaml"

    return get_playbooks_dir() / playbook_name


# === Data Paths ===


def get_data_dir() -> Path:
    """
    Get the data directory for browser artifacts, screenshots, etc.

    Returns:
        Path: Absolute path to data/ directory

    Example:
        >>> data = get_data_dir()
        >>> print(data)
        /git/ignition-playground/data
    """
    data_dir = get_package_root() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_screenshots_dir() -> Path:
    """
    Get the directory for screenshot storage.

    Returns:
        Path: Absolute path to data/screenshots/ directory

    Example:
        >>> screenshots = get_screenshots_dir()
        >>> print(screenshots)
        /git/ignition-playground/data/screenshots
    """
    screenshots_dir = get_data_dir() / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    return screenshots_dir


def get_playwright_browsers_dir() -> Path:
    """
    Get the directory for Playwright browser binaries.

    Returns:
        Path: Absolute path to data/.playwright-browsers/ directory

    Example:
        >>> browsers = get_playwright_browsers_dir()
        >>> print(browsers)
        /git/ignition-playground/data/.playwright-browsers
    """
    browsers_dir = get_data_dir() / ".playwright-browsers"
    browsers_dir.mkdir(exist_ok=True)
    return browsers_dir


# === Frontend Paths ===


def get_frontend_dir() -> Path:
    """
    Get the frontend directory.

    Returns:
        Path: Absolute path to frontend/ directory

    Example:
        >>> frontend = get_frontend_dir()
        >>> print(frontend)
        /git/ignition-playground/frontend
    """
    return get_package_root() / "frontend"


def get_frontend_dist_dir() -> Path:
    """
    Get the built frontend distribution directory.

    Returns:
        Path: Absolute path to frontend/dist/ directory

    Example:
        >>> dist = get_frontend_dist_dir()
        >>> print(dist)
        /git/ignition-playground/frontend/dist
    """
    return get_frontend_dir() / "dist"


# === User Data Paths ===


def get_user_data_dir() -> Path:
    """
    Get the user's data directory for credentials, database, etc.

    Uses XDG_DATA_HOME if set, otherwise ~/.ignition-toolkit/

    Returns:
        Path: Absolute path to user data directory

    Example:
        >>> user_data = get_user_data_dir()
        >>> print(user_data)
        /root/.ignition-toolkit
    """
    xdg_data_home = os.environ.get("XDG_DATA_HOME")

    if xdg_data_home:
        user_dir = Path(xdg_data_home) / "ignition-toolkit"
    else:
        user_dir = Path.home() / ".ignition-toolkit"

    user_dir.mkdir(exist_ok=True)
    return user_dir


def get_credentials_file() -> Path:
    """
    Get the path to the encrypted credentials vault file.

    Returns:
        Path: Absolute path to credentials.enc file

    Example:
        >>> creds = get_credentials_file()
        >>> print(creds)
        /root/.ignition-toolkit/credentials.enc
    """
    return get_user_data_dir() / "credentials.enc"


def get_database_file() -> Path:
    """
    Get the path to the SQLite database file.

    Returns:
        Path: Absolute path to executions.db file

    Example:
        >>> db = get_database_file()
        >>> print(db)
        /root/.ignition-toolkit/executions.db
    """
    return get_user_data_dir() / "executions.db"


# === Environment-Aware Paths ===


def get_env_file() -> Path:
    """
    Get the path to the .env file.

    Returns:
        Path: Absolute path to .env file

    Example:
        >>> env = get_env_file()
        >>> print(env)
        /git/ignition-playground/.env
    """
    return get_package_root() / ".env"


# === Validation ===


def validate_paths() -> dict:
    """
    Validate that all critical paths exist and are accessible.

    Returns:
        dict: Status of each path with 'exists' and 'writable' flags

    Example:
        >>> status = validate_paths()
        >>> print(status['playbooks_dir']['exists'])
        True
    """
    paths_to_check = {
        "package_root": get_package_root(),
        "package_dir": get_package_dir(),
        "playbooks_dir": get_playbooks_dir(),
        "data_dir": get_data_dir(),
        "frontend_dir": get_frontend_dir(),
        "frontend_dist_dir": get_frontend_dist_dir(),
        "user_data_dir": get_user_data_dir(),
        "credentials_file": get_credentials_file(),
        "database_file": get_database_file(),
        "env_file": get_env_file(),
    }

    status = {}
    for name, path in paths_to_check.items():
        status[name] = {
            "path": str(path),
            "exists": path.exists(),
            "is_dir": path.is_dir() if path.exists() else None,
            "is_file": path.is_file() if path.exists() else None,
            "writable": os.access(path.parent if path.is_file() else path, os.W_OK),
        }

    return status


# === Convenience Functions ===


def ensure_directories() -> None:
    """
    Ensure all required directories exist.

    Creates directories if they don't exist:
    - data/
    - data/screenshots/
    - data/.playwright-browsers/
    - ~/.ignition-toolkit/
    """
    get_data_dir()
    get_screenshots_dir()
    get_playwright_browsers_dir()
    get_user_data_dir()


def get_relative_path(absolute_path: Path) -> Path | None:
    """
    Get a path relative to the package root.

    Args:
        absolute_path: Absolute path to convert

    Returns:
        Path: Relative path from package root, or None if not under package root

    Example:
        >>> abs_path = Path("/git/ignition-playground/playbooks/test.yaml")
        >>> rel = get_relative_path(abs_path)
        >>> print(rel)
        playbooks/test.yaml
    """
    try:
        return absolute_path.relative_to(get_package_root())
    except ValueError:
        return None


# === Module Initialization ===

# Ensure directories exist on import
ensure_directories()


# === Public API ===

__all__ = [
    "get_package_root",
    "get_package_dir",
    "get_playbooks_dir",
    "get_playbook_path",
    "get_data_dir",
    "get_screenshots_dir",
    "get_playwright_browsers_dir",
    "get_frontend_dir",
    "get_frontend_dist_dir",
    "get_user_data_dir",
    "get_credentials_file",
    "get_database_file",
    "get_env_file",
    "validate_paths",
    "ensure_directories",
    "get_relative_path",
]
