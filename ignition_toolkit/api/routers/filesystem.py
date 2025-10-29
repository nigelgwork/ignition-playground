"""
Filesystem router - Browse server filesystem for path selection

Provides secure filesystem browsing for selecting download locations.
"""

import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/filesystem", tags=["filesystem"])


class DirectoryEntry(BaseModel):
    """Represents a file or directory entry"""

    name: str
    path: str
    is_directory: bool
    is_accessible: bool


class DirectoryContents(BaseModel):
    """Directory listing response"""

    current_path: str
    parent_path: str | None
    entries: List[DirectoryEntry]


# Security: Define allowed base paths to prevent directory traversal attacks
ALLOWED_BASE_PATHS = [
    Path("./data"),
    Path.home(),
    Path("/tmp"),
    Path("/mnt"),  # Windows drives mounted in WSL (e.g., /mnt/c, /mnt/d)
]


def is_path_allowed(path: Path) -> bool:
    """
    Check if path is within allowed base paths

    Args:
        path: Path to validate

    Returns:
        True if path is allowed, False otherwise
    """
    try:
        resolved_path = path.resolve()
        for base_path in ALLOWED_BASE_PATHS:
            resolved_base = base_path.resolve()
            if resolved_path == resolved_base or resolved_path.is_relative_to(
                resolved_base
            ):
                return True
        return False
    except (ValueError, RuntimeError, OSError):
        return False


@router.get("/browse", response_model=DirectoryContents)
async def browse_directory(path: str = "./data/downloads") -> DirectoryContents:
    """
    Browse server filesystem directory

    Args:
        path: Directory path to browse (default: ./data/downloads)

    Returns:
        Directory contents with subdirectories and parent path

    Raises:
        HTTPException: If path is invalid or not accessible
    """
    try:
        target_path = Path(path).resolve()

        # Security check: Verify path is within allowed base paths
        if not is_path_allowed(target_path):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: Path must be within allowed directories (./data, home directory, /tmp, or /mnt for Windows drives)",
            )

        # Verify path exists and is a directory
        if not target_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Directory not found: {path}",
            )

        if not target_path.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Path is not a directory: {path}",
            )

        # Get parent directory path (if not at root of allowed paths)
        parent_path = None
        if target_path.parent != target_path:
            if is_path_allowed(target_path.parent):
                parent_path = str(target_path.parent)

        # List directory contents (directories only, sorted)
        entries: List[DirectoryEntry] = []

        try:
            for entry in sorted(target_path.iterdir(), key=lambda x: x.name.lower()):
                if entry.is_dir():
                    is_accessible = is_path_allowed(entry)
                    entries.append(
                        DirectoryEntry(
                            name=entry.name,
                            path=str(entry),
                            is_directory=True,
                            is_accessible=is_accessible,
                        )
                    )
        except PermissionError:
            # If we can't list the directory, return empty list
            logger.warning(f"Permission denied listing directory: {target_path}")

        return DirectoryContents(
            current_path=str(target_path),
            parent_path=parent_path,
            entries=entries,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error browsing directory {path}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to browse directory: {str(e)}",
        )
