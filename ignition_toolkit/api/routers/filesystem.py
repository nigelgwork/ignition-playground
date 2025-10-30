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
    Path("/Ubuntu"),  # Ubuntu modules folder
    Path("/modules"),  # WSL Ubuntu modules directory
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
                detail=f"Access denied: Path must be within allowed directories (./data, /modules, home directory, /tmp, or /mnt for Windows drives)",
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


class ModuleFileInfo(BaseModel):
    """Information about a module file"""

    filename: str
    filepath: str
    is_unsigned: bool
    module_name: str | None = None
    module_version: str | None = None
    module_id: str | None = None


class ModuleFilesResponse(BaseModel):
    """Response containing detected module files"""

    path: str
    files: List[ModuleFileInfo]


@router.get("/list-modules")
async def list_module_files(path: str = "/Ubuntu/modules") -> ModuleFilesResponse:
    """
    List .modl and .unsigned.modl files in a directory and extract metadata

    Args:
        path: Directory path to search for module files

    Returns:
        ModuleFilesResponse with detected module files and their metadata
    """
    try:
        from ignition_toolkit.modules import parse_module_metadata

        target_path = Path(path).resolve()

        # Security check
        if not is_path_allowed(target_path):
            raise HTTPException(status_code=403, detail="Access denied to this path")

        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {path}")

        if not target_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

        # Find all .modl and .unsigned.modl files
        module_files = []

        for file_path in target_path.iterdir():
            if file_path.is_file() and (
                file_path.suffix == ".modl" or str(file_path).endswith(".unsigned.modl")
            ):
                is_unsigned = str(file_path).endswith(".unsigned.modl")

                # Try to extract metadata
                metadata = parse_module_metadata(str(file_path))

                module_files.append(
                    ModuleFileInfo(
                        filename=file_path.name,
                        filepath=str(file_path.absolute()),
                        is_unsigned=is_unsigned,
                        module_name=metadata.name if metadata else None,
                        module_version=metadata.version if metadata else None,
                        module_id=metadata.id if metadata else None,
                    )
                )

        logger.info(f"Found {len(module_files)} module files in {path}")

        return ModuleFilesResponse(path=str(target_path), files=module_files)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing module files in {path}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list module files: {str(e)}",
        )
