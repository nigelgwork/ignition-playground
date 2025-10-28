"""
Playbook management routes

Handles playbook listing, retrieval, updates, metadata operations, and deletion.
"""

import logging
import os
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ignition_toolkit.playbook.loader import PlaybookLoader
from ignition_toolkit.playbook.metadata import PlaybookMetadataStore
from ignition_toolkit.core.paths import get_playbooks_dir, get_playbook_path
from ignition_toolkit.api.routers.models import ParameterInfo, StepInfo, PlaybookInfo

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
    """Request to update playbook name and description"""
    playbook_path: str
    name: Optional[str] = None
    description: Optional[str] = None


class StepEditRequest(BaseModel):
    """Request to edit a step in a playbook"""
    playbook_path: str
    step_id: str
    new_parameters: Dict[str, Any]


# ============================================================================
# Helper Functions
# ============================================================================

def validate_playbook_path(path_str: str) -> Path:
    """
    Validate playbook path to prevent directory traversal attacks

    Args:
        path_str: User-provided playbook path

    Returns:
        Validated absolute Path

    Raises:
        HTTPException: If path is invalid or outside playbooks directory
    """
    playbooks_dir = get_playbooks_dir().resolve()

    # Resolve the provided path
    try:
        playbook_path = Path(path_str).resolve()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid path format: {e}")

    # Check if path is within playbooks directory
    if not playbook_path.is_relative_to(playbooks_dir):
        raise HTTPException(
            status_code=400,
            detail="Playbook path must be within ./playbooks directory"
        )

    # Check file extension
    if playbook_path.suffix not in ['.yaml', '.yml']:
        raise HTTPException(status_code=400, detail="Playbook must be a YAML file")

    # Check file exists
    if not playbook_path.exists():
        raise HTTPException(status_code=404, detail="Playbook file not found")

    return playbook_path


def get_relative_playbook_path(path_str: str) -> str:
    """
    Convert a playbook path (full or relative) to a relative path from playbooks directory

    Args:
        path_str: User-provided playbook path (can be full or relative)

    Returns:
        Relative path string from playbooks directory (e.g., "gateway/reset_gateway_trial.yaml")
    """
    playbooks_dir = get_playbooks_dir().resolve()
    playbook_path = Path(path_str).resolve()

    # Convert to relative path from playbooks directory
    try:
        relative_path = playbook_path.relative_to(playbooks_dir)
        return str(relative_path)
    except ValueError:
        # If path is not relative to playbooks_dir, try using it as-is
        # (might already be relative)
        return path_str


# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=List[PlaybookInfo])
async def list_playbooks():
    """List all available playbooks"""
    metadata_store = get_metadata_store()
    playbooks_dir = get_playbooks_dir()
    if not playbooks_dir.exists():
        return []

    playbooks = []
    for yaml_file in playbooks_dir.rglob("*.yaml"):
        # Skip backup files
        if '.backup.' in yaml_file.name:
            continue
        try:
            loader = PlaybookLoader()
            playbook = loader.load_from_file(yaml_file)

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
            relative_path = str(yaml_file.relative_to(playbooks_dir))
            meta = metadata_store.get_metadata(relative_path)

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
                    revision=meta.revision,
                    verified=meta.verified,
                    enabled=meta.enabled,
                    last_modified=meta.last_modified,
                    verified_at=meta.verified_at,
                )
            )
        except Exception as e:
            logger.warning(f"Failed to load playbook {yaml_file}: {e}")
            continue

    return playbooks


@router.get("/{playbook_path:path}", response_model=PlaybookInfo)
async def get_playbook(playbook_path: str):
    """Get detailed playbook information including full parameter schema"""
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

        return PlaybookInfo(
            name=playbook.name,
            path=str(validated_path),
            version=playbook.version,
            description=playbook.description,
            parameter_count=len(playbook.parameters),
            step_count=len(playbook.steps),
            parameters=parameters,
            steps=steps,
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
        backup_path = playbook_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
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
            "message": f"Playbook updated successfully (revision {meta.revision})"
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
        with open(playbook_path, 'r') as f:
            playbook_data = yaml.safe_load(f)

        # Update name and/or description
        if request.name is not None:
            playbook_data['name'] = request.name
        if request.description is not None:
            playbook_data['description'] = request.description

        # Create backup
        backup_path = playbook_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
        backup_path.write_text(playbook_path.read_text())

        # Write updated YAML
        with open(playbook_path, 'w') as f:
            yaml.safe_dump(playbook_data, f, default_flow_style=False, sort_keys=False)

        # Increment revision
        metadata_store.increment_revision(request.playbook_path)
        meta = metadata_store.get_metadata(request.playbook_path)

        logger.info(f"Updated playbook metadata: {playbook_path}")

        return {
            "status": "success",
            "playbook_path": str(request.playbook_path),
            "name": playbook_data.get('name'),
            "description": playbook_data.get('description'),
            "revision": meta.revision,
            "message": "Playbook metadata updated successfully"
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
            "message": "Playbook marked as verified"
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
            "message": "Playbook verification removed"
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
            "message": "Playbook enabled"
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
            "message": "Playbook disabled"
        }
    except Exception as e:
        logger.error(f"Error disabling playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{playbook_path:path}")
async def delete_playbook(playbook_path: str):
    """Delete a playbook file and its metadata"""
    metadata_store = get_metadata_store()
    try:
        # Get absolute path to playbook
        full_path = Path(playbook_path)
        if not full_path.is_absolute():
            # Assume relative to project root
            full_path = Path.cwd() / playbook_path

        # Safety check - only allow deleting files in playbooks/ directory
        if "playbooks/" not in str(full_path):
            raise HTTPException(
                status_code=400,
                detail="Can only delete playbooks from the playbooks/ directory"
            )

        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"Playbook not found: {playbook_path}")

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

        return {
            "status": "success",
            "message": f"Playbook deleted: {playbook_path}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edit-step")
async def edit_step(request: StepEditRequest):
    """Edit a step's parameters in a playbook during execution"""
    try:
        playbook_path = validate_playbook_path(request.playbook_path)

        with open(playbook_path, 'r') as f:
            playbook_data = yaml.safe_load(f)

        step_found = False
        for step in playbook_data.get('steps', []):
            if step.get('id') == request.step_id:
                if 'parameters' not in step:
                    step['parameters'] = {}
                step['parameters'].update(request.new_parameters)
                step_found = True
                break

        if not step_found:
            raise HTTPException(status_code=404, detail=f"Step not found: {request.step_id}")

        with open(playbook_path, 'w') as f:
            yaml.safe_dump(playbook_data, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Updated step '{request.step_id}' in {playbook_path}")
        return {"message": "Step updated", "step_id": request.step_id}

    except Exception as e:
        logger.exception(f"Step edit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
