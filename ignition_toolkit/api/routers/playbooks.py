"""
Playbook management routes

Handles playbook listing, retrieval, updates, metadata operations, and deletion.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator

from ignition_toolkit.api.routers.models import ParameterInfo, PlaybookInfo, StepInfo
from ignition_toolkit.core.paths import (
    get_playbooks_dir,
    get_all_playbook_dirs,
    get_builtin_playbooks_dir,
    get_user_playbooks_dir,
)
from ignition_toolkit.playbook.loader import PlaybookLoader

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/playbooks", tags=["playbooks"])


# Dependency injection for metadata store
def get_metadata_store():
    """Get shared metadata store from app"""
    from ignition_toolkit.api.app import metadata_store

    return metadata_store


# ============================================================================
# Pydantic Models (shared models imported from models.py)
# ============================================================================


class PlaybookUpdateRequest(BaseModel):
    """Request to update a playbook YAML file"""

    playbook_path: str  # Relative path from playbooks directory
    yaml_content: str  # New YAML content


class PlaybookMetadataUpdateRequest(BaseModel):
    """Request to update playbook name and description

    SECURITY: Includes input validation to prevent XSS, injection attacks, and DoS
    """

    playbook_path: str
    name: str | None = None
    description: str | None = None

    @validator('playbook_path')
    def validate_playbook_path_field(cls, v):
        """Validate playbook path field"""
        if not v or not v.strip():
            raise ValueError("Playbook path cannot be empty")
        if len(v) > 500:
            raise ValueError("Playbook path too long (max 500 characters)")
        # Path traversal is checked by validate_playbook_path() function later
        return v.strip()

    @validator('name')
    def validate_name(cls, v):
        """Validate playbook name for security and sanity"""
        if v is None:
            return v

        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or whitespace")

        # Length check
        if len(v) > 200:
            raise ValueError("Name too long (max 200 characters)")

        # Check for dangerous characters that could break YAML or enable XSS
        dangerous_chars = ['<', '>', '"', "'", '`', '{', '}', '$', '|', '&', ';']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f"Name contains invalid character: {char}")

        # Check for control characters
        if any(ord(c) < 32 for c in v):
            raise ValueError("Name contains control characters")

        return v

    @validator('description')
    def validate_description(cls, v):
        """Validate playbook description for security"""
        if v is None:
            return v

        v = v.strip()

        # Length check - descriptions can be longer but still need limits
        if len(v) > 2000:
            raise ValueError("Description too long (max 2000 characters)")

        # Check for dangerous patterns (less strict than name but still important)
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onload=', '<?php']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Description contains potentially dangerous pattern: {pattern}")

        # Check for control characters (except newlines and tabs)
        for c in v:
            if ord(c) < 32 and c not in ['\n', '\r', '\t']:
                raise ValueError("Description contains invalid control characters")

        return v


class StepEditRequest(BaseModel):
    """Request to edit a step in a playbook"""

    playbook_path: str
    step_id: str
    new_parameters: dict[str, Any]


# ============================================================================
# Helper Functions
# ============================================================================


def validate_playbook_path(path_str: str) -> Path:
    """
    Validate playbook path to prevent directory traversal attacks

    SECURITY: This is a wrapper around PathValidator for backwards compatibility.
    Use PathValidator directly for new code.

    Args:
        path_str: User-provided playbook path

    Returns:
        Validated absolute Path

    Raises:
        HTTPException: If path is invalid or outside playbooks directory
    """
    # SECURITY: Use centralized PathValidator to prevent path traversal
    # This checks for ".." and absolute paths BEFORE resolution
    from ignition_toolkit.core.validation import PathValidator

    return PathValidator.validate_playbook_path(
        path_str,
        base_dir=get_playbooks_dir(),
        must_exist=True
    )


def get_relative_playbook_path(path_str: str) -> str:
    """
    Convert a playbook path (full or relative) to a relative path from playbooks directory

    SECURITY: Validates path before conversion to prevent traversal attacks.

    Args:
        path_str: User-provided playbook path (can be full or relative)

    Returns:
        Relative path string from playbooks directory (e.g., "gateway/reset_gateway_trial.yaml")
    """
    # SECURITY: First validate the path to prevent traversal
    from ignition_toolkit.core.validation import PathValidator

    playbooks_dir = get_playbooks_dir().resolve()

    # Validate path (prevents ".." and absolute paths)
    # Use must_exist=False because metadata operations might reference non-existent files
    try:
        validated_path = PathValidator.validate_playbook_path(
            path_str,
            base_dir=playbooks_dir,
            must_exist=False  # Metadata operations might reference deleted playbooks
        )
        # Convert to relative path
        relative_path = validated_path.relative_to(playbooks_dir)
        return str(relative_path)
    except HTTPException:
        # If validation fails, path might already be relative
        # Return as-is if it looks safe
        if ".." not in path_str and not Path(path_str).is_absolute():
            return path_str
        # Otherwise reject it
        raise HTTPException(
            status_code=400,
            detail="Invalid playbook path - must be relative path within playbooks directory"
        )


# ============================================================================
# Routes
# ============================================================================


@router.get("", response_model=list[PlaybookInfo])
async def list_playbooks():
    """
    List all available playbooks from all sources.

    Scans both built-in and user-installed playbook directories.
    User playbooks take priority over built-in playbooks with the same path.
    """
    metadata_store = get_metadata_store()

    # Get all playbook directories (user has priority)
    playbook_dirs = get_all_playbook_dirs()
    builtin_dir = get_builtin_playbooks_dir()
    user_dir = get_user_playbooks_dir()

    # Track seen playbook paths to handle priority (first seen wins)
    seen_paths = set()
    playbooks = []

    for playbooks_dir in playbook_dirs:
        if not playbooks_dir.exists():
            continue

        # Determine source type
        if playbooks_dir == builtin_dir:
            source = "built-in"
        elif playbooks_dir == user_dir:
            source = "user-installed"
        else:
            source = "unknown"

        for yaml_file in playbooks_dir.rglob("*.yaml"):
            # Skip backup files
            if ".backup." in yaml_file.name:
                continue

            try:
                loader = PlaybookLoader()
                playbook = loader.load_from_file(yaml_file)

                # Calculate relative path for deduplication
                # Use path relative to the playbooks_dir (e.g., "gateway/module_upgrade.yaml")
                relative_path = str(yaml_file.relative_to(playbooks_dir))

                # Skip if we've already seen this playbook path (user overrides built-in)
                if relative_path in seen_paths:
                    logger.debug(f"Skipping {relative_path} from {source} (already loaded from higher priority source)")
                    continue

                seen_paths.add(relative_path)

                # Convert parameters to ParameterInfo models
                parameters = [
                    ParameterInfo(
                        name=p.name,
                        type=p.type.value,
                        required=p.required,
                        default=str(p.default) if p.default is not None else None,
                        description=p.description,
                    )
                    for p in playbook.parameters
                ]

                # Convert steps to StepInfo models
                steps = [
                    StepInfo(
                        id=s.id,
                        name=s.name,
                        type=s.type.value,
                        timeout=s.timeout,
                        retry_count=s.retry_count,
                    )
                    for s in playbook.steps
                ]

                # Get metadata for this playbook
                meta = metadata_store.get_metadata(relative_path)

                # Prefer YAML verified status over database for portability
                yaml_verified = playbook.metadata.get("verified")
                verified_status = yaml_verified if yaml_verified is not None else meta.verified

                # Determine origin if not already set
                if meta.origin == "unknown":
                    meta.origin = source
                    metadata_store.update_metadata(relative_path, meta)

                playbooks.append(
                    PlaybookInfo(
                        name=playbook.name,
                        path=relative_path,  # Use relative path instead of absolute
                        version=playbook.version,
                        description=playbook.description,
                        parameter_count=len(playbook.parameters),
                        step_count=len(playbook.steps),
                        parameters=parameters,
                        steps=steps,
                        domain=playbook.metadata.get("domain"),  # Extract domain from metadata
                        group=playbook.metadata.get("group"),  # Extract group for UI organization
                        revision=meta.revision,
                        verified=verified_status,  # Prefer YAML over database
                        enabled=meta.enabled,
                        last_modified=meta.last_modified,
                        verified_at=meta.verified_at,
                        # PORTABILITY v4: Include origin tracking
                        origin=meta.origin,
                        duplicated_from=meta.duplicated_from,
                        created_at=meta.created_at,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to load playbook {yaml_file}: {e}")
                continue

    return playbooks

# ============================================================================
# Playbook Library Routes (v5.0 - Plugin Architecture)
# ============================================================================


@router.get("/browse")
async def browse_available_playbooks(force_refresh: bool = False):
    """
    Browse playbooks available in the central repository

    Args:
        force_refresh: Force refresh from GitHub (ignore cache)

    Returns:
        List of available playbooks with metadata
    """
    try:
        from ignition_toolkit.playbook.registry import PlaybookRegistry

        registry = PlaybookRegistry()
        registry.load()

        # Fetch available playbooks from GitHub
        await registry.fetch_available_playbooks(force_refresh=force_refresh)

        # Get playbooks that are not installed
        available = registry.get_available_playbooks(include_installed=False)

        # Convert to response format
        playbooks = [
            {
                "playbook_path": pb.playbook_path,
                "version": pb.version,
                "domain": pb.domain,
                "verified": pb.verified,
                "verified_by": pb.verified_by,
                "description": pb.description,
                "author": pb.author,
                "tags": pb.tags,
                "group": pb.group,
                "size_bytes": pb.size_bytes,
                "dependencies": pb.dependencies,
                "release_notes": pb.release_notes,
            }
            for pb in available
        ]

        return {
            "status": "success",
            "count": len(playbooks),
            "playbooks": playbooks,
            "last_fetched": registry.last_fetched,
        }

    except Exception as e:
        logger.exception(f"Error browsing available playbooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PlaybookInstallRequest(BaseModel):
    """Request to install a playbook"""
    playbook_path: str  # e.g., "gateway/module_upgrade"
    version: str = "latest"
    verify_checksum: bool = True


@router.post("/install")
async def install_playbook(request: PlaybookInstallRequest):
    """
    Install a playbook from the repository

    Downloads the playbook, verifies checksum, and installs to user directory.
    """
    try:
        from ignition_toolkit.playbook.installer import PlaybookInstaller, PlaybookInstallError

        installer = PlaybookInstaller()

        # Install playbook
        installed_path = await installer.install_playbook(
            playbook_path=request.playbook_path,
            version=request.version,
            verify_checksum=request.verify_checksum
        )

        return {
            "status": "success",
            "message": f"Playbook {request.playbook_path} installed successfully",
            "playbook_path": request.playbook_path,
            "installed_at": str(installed_path),
        }

    except PlaybookInstallError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error installing playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{playbook_path:path}/uninstall")
async def uninstall_playbook(playbook_path: str, force: bool = False):
    """
    Uninstall a playbook

    Args:
        playbook_path: Playbook path (e.g., "gateway/module_upgrade")
        force: Force uninstall even if built-in (dangerous!)
    """
    try:
        from ignition_toolkit.playbook.installer import PlaybookInstaller, PlaybookInstallError

        installer = PlaybookInstaller()

        # Uninstall playbook
        success = await installer.uninstall_playbook(
            playbook_path=playbook_path,
            force=force
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Playbook {playbook_path} not found")

        return {
            "status": "success",
            "message": f"Playbook {playbook_path} uninstalled successfully",
            "playbook_path": playbook_path,
        }

    except PlaybookInstallError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error uninstalling playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{playbook_path:path}/update")
async def update_playbook_to_latest(playbook_path: str):
    """
    Update a playbook to the latest version

    Args:
        playbook_path: Playbook path (e.g., "gateway/module_upgrade")
    """
    try:
        from ignition_toolkit.playbook.installer import PlaybookInstaller, PlaybookInstallError

        installer = PlaybookInstaller()

        # Update playbook
        updated_path = await installer.update_playbook(playbook_path=playbook_path)

        return {
            "status": "success",
            "message": f"Playbook {playbook_path} updated successfully",
            "playbook_path": playbook_path,
            "installed_at": str(updated_path),
        }

    except PlaybookInstallError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error updating playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/updates")
async def check_for_updates(force_refresh: bool = False):
    """
    Check for available playbook updates

    Compares installed playbooks against available versions in the repository.

    Args:
        force_refresh: Force refresh from GitHub (ignore cache)

    Returns:
        Update check results with detailed information for each update
    """
    try:
        from ignition_toolkit.playbook.update_checker import PlaybookUpdateChecker

        checker = PlaybookUpdateChecker()

        # Refresh available playbooks if requested
        if force_refresh:
            await checker.refresh(force=True)

        # Check for updates
        result = checker.check_for_updates()

        # Convert updates to response format
        updates = [
            {
                "playbook_path": update.playbook_path,
                "current_version": update.current_version,
                "latest_version": update.latest_version,
                "description": update.description,
                "release_notes": update.release_notes,
                "domain": update.domain,
                "verified": update.verified,
                "verified_by": update.verified_by,
                "size_bytes": update.size_bytes,
                "author": update.author,
                "tags": update.tags,
                "is_major_update": update.is_major_update,
                "version_diff": update.version_diff,
                "download_url": update.download_url,
                "checksum": update.checksum,
            }
            for update in result.updates
        ]

        return {
            "status": "success",
            "checked_at": result.checked_at,
            "total_playbooks": result.total_playbooks,
            "updates_available": result.updates_available,
            "has_updates": result.has_updates,
            "last_fetched": result.last_fetched,
            "updates": updates,
            "major_updates": len(result.major_updates),
            "minor_updates": len(result.minor_updates),
        }

    except Exception as e:
        logger.exception(f"Error checking for updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/updates/stats")
async def get_update_stats():
    """
    Get update statistics

    Returns summary statistics about available updates.
    """
    try:
        from ignition_toolkit.playbook.update_checker import PlaybookUpdateChecker

        checker = PlaybookUpdateChecker()
        result = checker.check_for_updates()

        # Group updates by domain
        updates_by_domain = {}
        for update in result.updates:
            domain = update.domain
            if domain not in updates_by_domain:
                updates_by_domain[domain] = []
            updates_by_domain[domain].append(update)

        # Get verified updates
        verified_updates = checker.get_verified_updates()

        return {
            "status": "success",
            "checked_at": result.checked_at,
            "total_installed": result.total_playbooks,
            "total_updates_available": result.updates_available,
            "has_updates": result.has_updates,
            "major_updates": len(result.major_updates),
            "minor_updates": len(result.minor_updates),
            "verified_updates": len(verified_updates),
            "updates_by_domain": {
                domain: len(updates)
                for domain, updates in updates_by_domain.items()
            },
            "last_fetched": result.last_fetched,
        }

    except Exception as e:
        logger.exception(f"Error getting update stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/updates/{playbook_path:path}")
async def check_playbook_update(playbook_path: str):
    """
    Check for update for a specific playbook

    Args:
        playbook_path: Playbook path (e.g., "gateway/module_upgrade")

    Returns:
        Update information if available, or null if no update
    """
    try:
        from ignition_toolkit.playbook.update_checker import PlaybookUpdateChecker

        checker = PlaybookUpdateChecker()
        update = checker.get_update(playbook_path)

        if not update:
            return {
                "status": "success",
                "has_update": False,
                "playbook_path": playbook_path,
                "message": "No update available",
            }

        return {
            "status": "success",
            "has_update": True,
            "playbook_path": update.playbook_path,
            "current_version": update.current_version,
            "latest_version": update.latest_version,
            "description": update.description,
            "release_notes": update.release_notes,
            "domain": update.domain,
            "verified": update.verified,
            "verified_by": update.verified_by,
            "size_bytes": update.size_bytes,
            "author": update.author,
            "tags": update.tags,
            "is_major_update": update.is_major_update,
            "version_diff": update.version_diff,
        }

    except Exception as e:
        logger.exception(f"Error checking update for {playbook_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{playbook_path:path}", response_model=PlaybookInfo)
async def get_playbook(playbook_path: str):
    """Get detailed playbook information including full parameter schema"""
    metadata_store = get_metadata_store()
    try:
        # Validate path for security
        validated_path = validate_playbook_path(playbook_path)

        loader = PlaybookLoader()
        playbook = loader.load_from_file(validated_path)

        # Convert parameters to ParameterInfo models
        parameters = [
            ParameterInfo(
                name=p.name,
                type=p.type.value,
                required=p.required,
                default=str(p.default) if p.default is not None else None,
                description=p.description,
            )
            for p in playbook.parameters
        ]

        # Convert steps to StepInfo models
        steps = [
            StepInfo(
                id=s.id,
                name=s.name,
                type=s.type.value,
                timeout=s.timeout,
                retry_count=s.retry_count,
            )
            for s in playbook.steps
        ]

        # Get metadata for this playbook
        playbooks_dir = get_playbooks_dir()
        relative_path = str(validated_path.relative_to(playbooks_dir))
        meta = metadata_store.get_metadata(relative_path)

        return PlaybookInfo(
            name=playbook.name,
            path=relative_path,  # Use relative path
            version=playbook.version,
            description=playbook.description,
            parameter_count=len(playbook.parameters),
            step_count=len(playbook.steps),
            parameters=parameters,
            steps=steps,
            domain=playbook.metadata.get("domain"),  # Extract domain from metadata
            group=playbook.metadata.get("group"),  # Extract group for UI organization
            revision=meta.revision,
            verified=meta.verified,
            enabled=meta.enabled,
            last_modified=meta.last_modified,
            verified_at=meta.verified_at,
            # PORTABILITY v4: Include origin tracking
            origin=meta.origin,
            duplicated_from=meta.duplicated_from,
            created_at=meta.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Playbook not found: {e}")


@router.put("/update")
async def update_playbook(request: PlaybookUpdateRequest):
    """
    Update a playbook YAML file with new content

    This is used when applying fixes from debug mode.
    Creates a backup before updating.
    """
    metadata_store = get_metadata_store()
    try:
        # Resolve playbook path
        playbooks_dir = Path("playbooks")
        playbook_path = playbooks_dir / request.playbook_path

        # Security check: ensure path is within playbooks directory
        try:
            playbook_path = playbook_path.resolve()
            playbooks_dir = playbooks_dir.resolve()
            if not str(playbook_path).startswith(str(playbooks_dir)):
                raise HTTPException(status_code=400, detail="Invalid playbook path")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid playbook path")

        # Check if file exists
        if not playbook_path.exists():
            raise HTTPException(status_code=404, detail="Playbook not found")

        # Create backup with timestamp
        backup_path = playbook_path.with_suffix(
            f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        )
        backup_path.write_text(playbook_path.read_text())
        logger.info(f"Created backup: {backup_path}")

        # Validate YAML syntax before writing
        try:
            yaml.safe_load(request.yaml_content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

        # Write new content
        playbook_path.write_text(request.yaml_content)
        logger.info(f"Updated playbook: {playbook_path}")

        # Increment revision in metadata
        metadata_store.increment_revision(request.playbook_path)
        meta = metadata_store.get_metadata(request.playbook_path)

        return {
            "status": "success",
            "playbook_path": str(request.playbook_path),
            "backup_path": str(backup_path.name),
            "revision": meta.revision,
            "message": f"Playbook updated successfully (revision {meta.revision})",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/metadata")
async def update_playbook_metadata(request: PlaybookMetadataUpdateRequest):
    """
    Update playbook name and/or description in YAML file
    """
    metadata_store = get_metadata_store()
    try:
        # Validate and resolve playbook path
        playbook_path = validate_playbook_path(request.playbook_path)

        if not playbook_path.exists():
            raise HTTPException(status_code=404, detail="Playbook not found")

        # Read current YAML
        with open(playbook_path) as f:
            playbook_data = yaml.safe_load(f)

        # Update name and/or description
        if request.name is not None:
            playbook_data["name"] = request.name
        if request.description is not None:
            playbook_data["description"] = request.description

        # Create backup
        backup_path = playbook_path.with_suffix(
            f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        )
        backup_path.write_text(playbook_path.read_text())

        # Write updated YAML
        with open(playbook_path, "w") as f:
            yaml.safe_dump(playbook_data, f, default_flow_style=False, sort_keys=False)

        # Increment revision
        metadata_store.increment_revision(request.playbook_path)
        meta = metadata_store.get_metadata(request.playbook_path)

        logger.info(f"Updated playbook metadata: {playbook_path}")

        return {
            "status": "success",
            "playbook_path": str(request.playbook_path),
            "name": playbook_data.get("name"),
            "description": playbook_data.get("description"),
            "revision": meta.revision,
            "message": "Playbook metadata updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating playbook metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{playbook_path:path}/verify")
async def mark_playbook_verified(playbook_path: str):
    """Mark a playbook as verified"""
    metadata_store = get_metadata_store()
    try:
        # Convert to relative path for metadata store
        relative_path = get_relative_playbook_path(playbook_path)
        metadata_store.mark_verified(relative_path, verified_by="user")
        meta = metadata_store.get_metadata(relative_path)
        return {
            "status": "success",
            "playbook_path": playbook_path,
            "verified": meta.verified,
            "verified_at": meta.verified_at,
            "message": "Playbook marked as verified",
        }
    except Exception as e:
        logger.error(f"Error marking playbook as verified: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{playbook_path:path}/unverify")
async def unmark_playbook_verified(playbook_path: str):
    """Unmark a playbook as verified"""
    metadata_store = get_metadata_store()
    try:
        # Convert to relative path for metadata store
        relative_path = get_relative_playbook_path(playbook_path)
        metadata_store.unmark_verified(relative_path)
        return {
            "status": "success",
            "playbook_path": playbook_path,
            "verified": False,
            "message": "Playbook verification removed",
        }
    except Exception as e:
        logger.error(f"Error unmarking playbook as verified: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{playbook_path:path}/enable")
async def enable_playbook(playbook_path: str):
    """Enable a playbook"""
    metadata_store = get_metadata_store()
    try:
        # Convert to relative path for metadata store
        relative_path = get_relative_playbook_path(playbook_path)
        metadata_store.set_enabled(relative_path, True)
        return {
            "status": "success",
            "playbook_path": playbook_path,
            "enabled": True,
            "message": "Playbook enabled",
        }
    except Exception as e:
        logger.error(f"Error enabling playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{playbook_path:path}/disable")
async def disable_playbook(playbook_path: str):
    """Disable a playbook"""
    metadata_store = get_metadata_store()
    try:
        # Convert to relative path for metadata store
        relative_path = get_relative_playbook_path(playbook_path)
        metadata_store.set_enabled(relative_path, False)
        return {
            "status": "success",
            "playbook_path": playbook_path,
            "enabled": False,
            "message": "Playbook disabled",
        }
    except Exception as e:
        logger.error(f"Error disabling playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{playbook_path:path}")
async def delete_playbook(playbook_path: str):
    """Delete a playbook file and its metadata"""
    metadata_store = get_metadata_store()
    try:
        # SECURITY: Use centralized validator to prevent path traversal
        from ignition_toolkit.core.validation import PathValidator

        # This validates and ensures:
        # 1. No ".." or absolute paths (prevents traversal)
        # 2. Path is within playbooks directory
        # 3. File exists
        # 4. Valid YAML extension
        full_path = PathValidator.validate_playbook_path(
            playbook_path,
            base_dir=get_playbooks_dir(),
            must_exist=True
        )

        if not full_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {playbook_path}")

        # Delete the file
        os.remove(full_path)
        logger.info(f"Deleted playbook file: {full_path}")

        # Delete metadata if exists
        relative_path = get_relative_playbook_path(playbook_path)
        try:
            metadata = metadata_store.get_metadata(relative_path)
            if metadata:
                # Remove from metadata store
                if relative_path in metadata_store._metadata:
                    del metadata_store._metadata[relative_path]
                    metadata_store._save()
                    logger.info(f"Deleted metadata for: {relative_path}")
        except Exception as meta_error:
            logger.warning(f"Could not delete metadata: {meta_error}")

        return {"status": "success", "message": f"Playbook deleted: {playbook_path}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{playbook_path:path}/duplicate")
async def duplicate_playbook(playbook_path: str, new_name: str | None = None):
    """
    Duplicate a playbook with a new name

    Creates a copy of the playbook in the same directory with a new name.
    Marks the new playbook as duplicated from the source.

    Args:
        playbook_path: Source playbook path (relative to playbooks dir)
        new_name: Optional new playbook name (defaults to source_name_copy)

    Returns:
        dict: New playbook info with path and metadata
    """
    metadata_store = get_metadata_store()

    try:
        # Validate source playbook exists
        from ignition_toolkit.core.validation import PathValidator

        source_path = PathValidator.validate_playbook_path(
            playbook_path,
            base_dir=get_playbooks_dir(),
            must_exist=True
        )

        if not source_path.is_file():
            raise HTTPException(status_code=400, detail=f"Source is not a file: {playbook_path}")

        # Generate new filename
        source_parent = source_path.parent
        source_stem = source_path.stem  # filename without extension
        source_suffix = source_path.suffix  # .yaml or .yml

        if new_name:
            # User provided new name
            new_stem = new_name.replace(source_suffix, "")  # Remove extension if included
        else:
            # Auto-generate name with _copy suffix
            new_stem = f"{source_stem}_copy"

        # Check if file exists, add number if needed
        new_path = source_parent / f"{new_stem}{source_suffix}"
        counter = 1
        while new_path.exists():
            new_path = source_parent / f"{new_stem}_{counter}{source_suffix}"
            counter += 1

        # Copy the file
        import shutil
        shutil.copy2(source_path, new_path)
        logger.info(f"Duplicated playbook: {source_path} -> {new_path}")

        # Mark as duplicated in metadata
        playbooks_dir = get_playbooks_dir()
        source_relative = str(source_path.relative_to(playbooks_dir))
        new_relative = str(new_path.relative_to(playbooks_dir))

        metadata_store.mark_as_duplicated(new_relative, source_relative)
        logger.info(f"Marked {new_relative} as duplicated from {source_relative}")

        # Load and return new playbook info
        loader = PlaybookLoader()
        new_playbook = loader.load_from_file(new_path)

        # Get domain from metadata (may be None for older playbooks)
        domain = new_playbook.metadata.get("domain")

        return {
            "status": "success",
            "message": f"Playbook duplicated successfully",
            "source_path": source_relative,
            "new_path": new_relative,
            "playbook": {
                "path": new_relative,
                "name": new_playbook.name,
                "description": new_playbook.description,
                "version": new_playbook.version,
                "domain": domain,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error duplicating playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edit-step")
async def edit_step(request: StepEditRequest):
    """Edit a step's parameters in a playbook during execution"""
    try:
        playbook_path = validate_playbook_path(request.playbook_path)

        with open(playbook_path) as f:
            playbook_data = yaml.safe_load(f)

        step_found = False
        for step in playbook_data.get("steps", []):
            if step.get("id") == request.step_id:
                if "parameters" not in step:
                    step["parameters"] = {}
                step["parameters"].update(request.new_parameters)
                step_found = True
                break

        if not step_found:
            raise HTTPException(status_code=404, detail=f"Step not found: {request.step_id}")

        with open(playbook_path, "w") as f:
            yaml.safe_dump(playbook_data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Updated step '{request.step_id}' in {playbook_path}")
        return {"message": "Step updated", "step_id": request.step_id}

    except Exception as e:
        logger.exception(f"Step edit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PlaybookExportResponse(BaseModel):
    """Response for playbook export containing YAML content"""
    name: str
    path: str
    version: str
    description: str
    domain: str
    yaml_content: str
    metadata: dict[str, Any]


class PlaybookImportRequest(BaseModel):
    """Request to import a playbook from JSON"""
    name: str
    domain: str  # gateway, perspective, or designer
    yaml_content: str
    overwrite: bool = False
    metadata: dict[str, Any] | None = None  # Optional metadata from export (includes verified status)


@router.get("/{playbook_path:path}/export", response_model=PlaybookExportResponse)
async def export_playbook(playbook_path: str):
    """
    Export a playbook with full YAML content

    Returns JSON with playbook metadata and YAML content for portability
    """
    try:
        # Validate path
        validated_path = validate_playbook_path(playbook_path)

        # Load playbook
        loader = PlaybookLoader()
        playbook = loader.load_from_file(validated_path)

        # Read YAML content
        with open(validated_path) as f:
            yaml_content = f.read()

        # Get metadata
        playbooks_dir = get_playbooks_dir()
        relative_path = str(validated_path.relative_to(playbooks_dir))
        metadata_store = get_metadata_store()
        meta = metadata_store.get_metadata(relative_path)

        # Get domain from metadata (defaults to 'gateway' for older playbooks)
        domain = playbook.metadata.get('domain', 'gateway')

        return PlaybookExportResponse(
            name=playbook.name,
            path=relative_path,
            version=playbook.version,
            description=playbook.description,
            domain=domain,
            yaml_content=yaml_content,
            metadata={
                'revision': meta.revision,
                'verified': meta.verified,
                'verified_at': meta.verified_at,
                'verified_by': meta.verified_by,
                'origin': meta.origin,
                'created_at': meta.created_at,
                'exported_at': datetime.now().isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error exporting playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_playbook(request: PlaybookImportRequest):
    """
    Import a playbook from JSON export

    Creates a new playbook file in the appropriate domain directory.
    If a playbook with the same name exists, either overwrites or creates a copy.
    """
    metadata_store = get_metadata_store()
    try:
        # Validate domain
        if request.domain not in ['gateway', 'perspective', 'designer']:
            raise HTTPException(status_code=400, detail=f"Invalid domain: {request.domain}")

        # Validate YAML syntax
        try:
            yaml.safe_load(request.yaml_content)
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

        # Determine target directory
        playbooks_dir = get_playbooks_dir()
        target_dir = playbooks_dir / request.domain
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from name
        safe_name = request.name.lower().replace(' ', '_').replace('-', '_')
        # Remove any characters that aren't alphanumeric or underscore
        import re
        safe_name = re.sub(r'[^a-z0-9_]', '', safe_name)

        target_file = target_dir / f"{safe_name}.yaml"

        # Check if file exists
        if target_file.exists() and not request.overwrite:
            # Create a copy with a number suffix
            counter = 1
            while target_file.exists():
                target_file = target_dir / f"{safe_name}_{counter}.yaml"
                counter += 1

        # Write playbook file
        with open(target_file, 'w') as f:
            f.write(request.yaml_content)

        logger.info(f"Imported playbook to: {target_file}")

        # Create metadata and restore verified status if provided
        relative_path = str(target_file.relative_to(playbooks_dir))
        metadata_store.mark_as_imported(relative_path)

        # Restore verified status from export metadata if available
        if request.metadata and request.metadata.get('verified'):
            metadata_store.mark_verified(
                relative_path,
                verified_by=request.metadata.get('verified_by', 'imported')
            )
            logger.info(f"Restored verified status for imported playbook: {relative_path}")

        # Load and return playbook info
        loader = PlaybookLoader()
        new_playbook = loader.load_from_file(target_file)

        return {
            "status": "success",
            "message": "Playbook imported successfully",
            "path": relative_path,
            "playbook": {
                "name": new_playbook.name,
                "path": relative_path,
                "version": new_playbook.version,
                "description": new_playbook.description,
                "domain": request.domain,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error importing playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_playbook(request: PlaybookImportRequest):
    """
    Create a new blank playbook or from template

    Same as import but intended for creating new playbooks from scratch
    """
    return await import_playbook(request)


