"""
Execution management routes

Handles playbook execution control, status tracking, and lifecycle management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ignition_toolkit.playbook.engine import PlaybookEngine
from ignition_toolkit.playbook.models import ExecutionState, ExecutionStatus
from ignition_toolkit.storage import get_database
from ignition_toolkit.api.routers.models import (
    ExecutionRequest,
    ExecutionResponse,
    StepResultResponse,
    ExecutionStatusResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/executions", tags=["executions"])

# Dependency injection for global state
def get_active_engines():
    """Get shared active engines dict from app"""
    from ignition_toolkit.api.app import active_engines
    return active_engines


def get_engine_completion_times():
    """Get shared engine completion times dict from app"""
    from ignition_toolkit.api.app import engine_completion_times
    return engine_completion_times


def get_execution_ttl_minutes():
    """Get execution TTL configuration from app"""
    from ignition_toolkit.api.app import EXECUTION_TTL_MINUTES
    return EXECUTION_TTL_MINUTES


# ============================================================================
# Pydantic Models (shared models imported from models.py)
# ============================================================================


class PlaybookCodeUpdateRequest(BaseModel):
    """Request to update playbook code during execution"""
    code: str


# ============================================================================
# Background Tasks
# ============================================================================

async def cleanup_old_executions():
    """Remove completed executions older than TTL from memory"""
    active_engines = get_active_engines()
    engine_completion_times = get_engine_completion_times()
    ttl_minutes = get_execution_ttl_minutes()

    current_time = datetime.now()
    ttl_delta = timedelta(minutes=ttl_minutes)
    to_remove = []

    for exec_id, completion_time in engine_completion_times.items():
        if current_time - completion_time > ttl_delta:
            to_remove.append(exec_id)

    for exec_id in to_remove:
        if exec_id in active_engines:
            logger.info(f"Removing execution {exec_id} (TTL expired)")
            del active_engines[exec_id]
        del engine_completion_times[exec_id]

    if to_remove:
        logger.info(f"Cleaned up {len(to_remove)} old execution(s)")


# ============================================================================
# Routes
# ============================================================================

@router.post("", response_model=ExecutionResponse)
async def start_execution(request: ExecutionRequest, background_tasks: BackgroundTasks):
    """Start playbook execution"""
    from ignition_toolkit.playbook.loader import PlaybookLoader
    from pathlib import Path

    active_engines = get_active_engines()

    try:
        # Validate and load playbook (prevents path traversal)
        playbook_path = Path(request.playbook_path)

        # Security check - prevent directory traversal
        if ".." in str(playbook_path) or playbook_path.is_absolute():
            raise HTTPException(
                status_code=400,
                detail="Invalid playbook path - relative paths only, no directory traversal"
            )

        loader = PlaybookLoader()
        playbook = loader.load_from_file(playbook_path)

        # Get credential if specified
        credential = None
        if request.credential_name:
            from ignition_toolkit.credentials import CredentialVault
            vault = CredentialVault()
            credential = vault.get_credential(request.credential_name)
            if not credential:
                raise HTTPException(
                    status_code=404,
                    detail=f"Credential '{request.credential_name}' not found"
                )

        # Create and start engine
        engine = PlaybookEngine(playbook, parameters=request.parameters, credential=credential)

        # Enable debug mode if requested
        if request.debug_mode:
            engine.state.debug_mode = True

        active_engines[engine.execution_id] = engine

        # Start execution in background
        background_tasks.add_task(engine.execute)

        # Schedule cleanup task
        background_tasks.add_task(cleanup_old_executions)

        return ExecutionResponse(
            execution_id=engine.execution_id,
            playbook_name=playbook.name,
            status="started",
            message=f"Execution started with ID: {engine.execution_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error starting execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ExecutionStatusResponse])
async def list_executions(limit: int = 50, status: Optional[str] = None):
    """List all executions (active + recent completed from database)"""
    active_engines = get_active_engines()
    db = get_database()

    executions = []

    # Add active executions
    for exec_id, engine in active_engines.items():
        step_results = [
            StepResultResponse(
                step_id=result.step_id,
                status=result.status.value,
                output=result.output,
                error=result.error
            )
            for result in engine.state.step_results
        ]

        executions.append(
            ExecutionStatusResponse(
                execution_id=exec_id,
                playbook_name=engine.playbook.name,
                status=engine.state.status.value,
                current_step=engine.state.current_step_index,
                total_steps=len(engine.playbook.steps),
                step_results=step_results
            )
        )

    # Add recent completed executions from database
    try:
        with db.session_scope() as session:
            from ignition_toolkit.storage.models import ExecutionModel
            query = session.query(ExecutionModel).order_by(ExecutionModel.started_at.desc())

            if status:
                query = query.filter(ExecutionModel.status == status)

            db_executions = query.limit(limit).all()

            for db_exec in db_executions:
                # Skip if already in active list
                if db_exec.execution_id in active_engines:
                    continue

                executions.append(
                    ExecutionStatusResponse(
                        execution_id=db_exec.execution_id,
                        playbook_name=db_exec.playbook_name,
                        status=db_exec.status,
                        current_step=None,
                        total_steps=0,
                        step_results=[]
                    )
                )
    except Exception as e:
        logger.warning(f"Error loading executions from database: {e}")

    return executions[:limit]


@router.get("/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """Get execution status and step results"""
    active_engines = get_active_engines()

    if execution_id in active_engines:
        engine = active_engines[execution_id]

        step_results = [
            StepResultResponse(
                step_id=result.step_id,
                status=result.status.value,
                output=result.output,
                error=result.error
            )
            for result in engine.state.step_results
        ]

        return ExecutionStatusResponse(
            execution_id=execution_id,
            playbook_name=engine.playbook.name,
            status=engine.state.status.value,
            current_step=engine.state.current_step_index,
            total_steps=len(engine.playbook.steps),
            step_results=step_results
        )

    # Try to load from database
    db = get_database()
    try:
        with db.session_scope() as session:
            from ignition_toolkit.storage.models import ExecutionModel
            execution = session.query(ExecutionModel).filter(
                ExecutionModel.execution_id == execution_id
            ).first()

            if execution:
                return ExecutionStatusResponse(
                    execution_id=execution.execution_id,
                    playbook_name=execution.playbook_name,
                    status=execution.status,
                    current_step=None,
                    total_steps=0,
                    step_results=[]
                )
    except Exception as e:
        logger.error(f"Error loading execution from database: {e}")

    raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")


@router.get("/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_execution_status_with_path(execution_id: str):
    """Get execution status (alternate endpoint for compatibility)"""
    return await get_execution_status(execution_id)


@router.post("/{execution_id}/pause")
async def pause_execution(execution_id: str):
    """Pause execution"""
    active_engines = get_active_engines()

    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    engine = active_engines[execution_id]
    engine.pause()
    return {"message": "Execution paused", "execution_id": execution_id}


@router.post("/{execution_id}/resume")
async def resume_execution(execution_id: str):
    """Resume paused execution"""
    active_engines = get_active_engines()

    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    engine = active_engines[execution_id]
    engine.resume()
    return {"message": "Execution resumed", "execution_id": execution_id}


@router.post("/{execution_id}/skip")
async def skip_step(execution_id: str):
    """Skip current step and move to next"""
    active_engines = get_active_engines()

    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    engine = active_engines[execution_id]
    engine.skip_step()
    return {"message": "Step skipped", "execution_id": execution_id}


@router.post("/{execution_id}/skip_back")
async def skip_back_step(execution_id: str):
    """Skip back to previous step"""
    active_engines = get_active_engines()

    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    engine = active_engines[execution_id]
    engine.skip_back()
    return {"message": "Skipped back to previous step", "execution_id": execution_id}


@router.post("/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """Cancel execution"""
    active_engines = get_active_engines()
    engine_completion_times = get_engine_completion_times()

    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    engine = active_engines[execution_id]
    engine.cancel()

    # Mark completion time for TTL cleanup
    engine_completion_times[execution_id] = datetime.now()

    return {"message": "Execution cancelled", "execution_id": execution_id}


@router.get("/{execution_id}/playbook/code")
async def get_playbook_code(execution_id: str):
    """Get the YAML code for the playbook being executed"""
    active_engines = get_active_engines()

    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    engine = active_engines[execution_id]

    # Read the original playbook file
    playbook_path = engine.playbook_path
    if not playbook_path or not playbook_path.exists():
        raise HTTPException(status_code=404, detail="Playbook file not found")

    yaml_content = playbook_path.read_text()

    return {
        "execution_id": execution_id,
        "playbook_path": str(playbook_path),
        "playbook_name": engine.playbook.name,
        "yaml_content": yaml_content
    }


@router.put("/{execution_id}/playbook/code")
async def update_playbook_code(execution_id: str, request: PlaybookCodeUpdateRequest):
    """Update the playbook YAML during execution (for AI fixes)"""
    active_engines = get_active_engines()

    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    engine = active_engines[execution_id]

    # Get playbook path
    playbook_path = engine.playbook_path
    if not playbook_path or not playbook_path.exists():
        raise HTTPException(status_code=404, detail="Playbook file not found")

    # Validate YAML
    import yaml
    try:
        yaml.safe_load(request.code)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

    # Create backup
    backup_path = playbook_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
    backup_path.write_text(playbook_path.read_text())
    logger.info(f"Created backup: {backup_path}")

    # Write new content
    playbook_path.write_text(request.code)
    logger.info(f"Updated playbook code: {playbook_path}")

    return {
        "message": "Playbook code updated",
        "execution_id": execution_id,
        "playbook_path": str(playbook_path),
        "backup_path": str(backup_path.name)
    }
