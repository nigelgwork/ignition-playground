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
    from ignition_toolkit.credentials import CredentialVault
    from ignition_toolkit.gateway import GatewayClient
    from ignition_toolkit.core.paths import get_playbooks_dir
    from pathlib import Path
    import uuid

    active_engines = get_active_engines()

    try:
        # Validate and load playbook (prevents path traversal)
        playbook_relative_path = Path(request.playbook_path)

        # Security check - prevent directory traversal
        if ".." in str(playbook_relative_path) or playbook_relative_path.is_absolute():
            raise HTTPException(
                status_code=400,
                detail="Invalid playbook path - relative paths only, no directory traversal"
            )

        # Resolve full path relative to playbooks directory
        playbooks_dir = get_playbooks_dir()
        playbook_path = playbooks_dir / playbook_relative_path

        if not playbook_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Playbook file not found: {request.playbook_path}"
            )

        loader = PlaybookLoader()
        playbook = loader.load_from_file(playbook_path)

        # Create components
        vault = CredentialVault()
        database = get_database()

        # If credential_name provided, load credential and auto-fill parameters
        parameters = request.parameters.copy()
        gateway_url = request.gateway_url

        if request.credential_name:
            credential = vault.get_credential(request.credential_name)
            if not credential:
                raise HTTPException(
                    status_code=404,
                    detail=f"Credential '{request.credential_name}' not found"
                )

            # Auto-fill gateway_url if not provided
            if not gateway_url and credential.gateway_url:
                gateway_url = credential.gateway_url

            # Auto-fill credential-type parameters with credential name
            for param in playbook.parameters:
                if param.type == "credential" and param.name not in parameters:
                    parameters[param.name] = request.credential_name

            # Auto-fill gateway_url parameter if it exists in playbook
            for param in playbook.parameters:
                if param.name.lower() in ['gateway_url', 'url'] and param.name not in parameters:
                    if credential.gateway_url:
                        parameters[param.name] = credential.gateway_url

            # Auto-fill username/password parameters if they exist
            for param in playbook.parameters:
                if param.name.lower() in ['username', 'user', 'gateway_username'] and param.name not in parameters:
                    parameters[param.name] = credential.username
                elif param.name.lower() in ['password', 'pass', 'gateway_password'] and param.name not in parameters:
                    parameters[param.name] = credential.password

        logger.info(f"Execution parameters after credential auto-fill: gateway_url={gateway_url}, params={parameters}")

        gateway_client = None
        if gateway_url:
            gateway_client = GatewayClient(gateway_url)

        # Create screenshot callback for browser streaming
        from ignition_toolkit.api.routers.websockets import broadcast_screenshot_frame, broadcast_execution_state

        async def screenshot_callback(execution_id: str, screenshot_b64: str):
            await broadcast_screenshot_frame(execution_id, screenshot_b64)

        # Create engine with proper dependencies
        engine = PlaybookEngine(
            gateway_client=gateway_client,
            credential_vault=vault,
            database=database,
            screenshot_callback=screenshot_callback,
        )

        # Set up WebSocket broadcast callback
        async def broadcast_update(state: ExecutionState):
            await broadcast_execution_state(state)

        engine.set_update_callback(broadcast_update)

        # Generate execution ID upfront
        execution_id = str(uuid.uuid4())
        logger.info(f"Starting execution {execution_id} for playbook: {playbook.name}")

        # Store engine with real execution ID immediately
        active_engines[execution_id] = engine

        # Enable debug mode if requested
        if request.debug_mode:
            engine.enable_debug(execution_id)
            logger.info(f"Debug mode enabled for execution {execution_id}")

        # Start execution in background
        async def run_execution():
            try:
                if gateway_client:
                    await gateway_client.__aenter__()

                execution_state = await engine.execute_playbook(
                    playbook,
                    parameters,
                    base_path=playbook_path.parent,
                    execution_id=execution_id,
                    playbook_path=playbook_path,
                )

                logger.info(
                    f"Execution {execution_state.execution_id} completed with status: {execution_state.status}"
                )

                # Mark completion time for TTL cleanup
                engine_completion_times = get_engine_completion_times()
                engine_completion_times[execution_id] = datetime.now()

            except Exception as e:
                logger.exception(f"Error in execution {execution_id}: {e}")
            finally:
                if gateway_client:
                    await gateway_client.__aexit__(None, None, None)

        background_tasks.add_task(run_execution)

        # Schedule cleanup task
        background_tasks.add_task(cleanup_old_executions)

        return ExecutionResponse(
            execution_id=execution_id,
            playbook_name=playbook.name,
            status="started",
            message=f"Execution started with ID: {execution_id}"
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
        state = engine.get_current_execution()
        if not state:
            continue

        step_results = [
            StepResultResponse(
                step_id=result.step_id,
                step_name=result.step_name,
                status=result.status.value,
                error=result.error,
                started_at=result.started_at,
                completed_at=result.completed_at
            )
            for result in state.step_results
        ]

        executions.append(
            ExecutionStatusResponse(
                execution_id=exec_id,
                playbook_name=state.playbook_name,
                status=state.status.value,
                started_at=state.started_at,
                completed_at=state.completed_at,
                current_step_index=state.current_step_index,
                total_steps=len(engine._current_playbook.steps) if engine._current_playbook else 0,
                error=state.error,
                debug_mode=engine.state_manager.is_debug_mode_enabled(),
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
                        started_at=db_exec.started_at,
                        completed_at=db_exec.completed_at,
                        current_step_index=0,
                        total_steps=0,
                        error=db_exec.error_message,
                        debug_mode=False,
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
        state = engine.get_current_execution()

        if not state:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} has no state")

        step_results = [
            StepResultResponse(
                step_id=result.step_id,
                step_name=result.step_name,
                status=result.status.value,
                error=result.error,
                started_at=result.started_at,
                completed_at=result.completed_at
            )
            for result in state.step_results
        ]

        return ExecutionStatusResponse(
            execution_id=execution_id,
            playbook_name=state.playbook_name,
            status=state.status.value,
            started_at=state.started_at,
            completed_at=state.completed_at,
            current_step_index=state.current_step_index,
            total_steps=len(engine._current_playbook.steps) if engine._current_playbook else 0,
            error=state.error,
            debug_mode=engine.state_manager.is_debug_mode_enabled(),
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
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    current_step_index=0,
                    total_steps=0,
                    error=execution.error_message,
                    debug_mode=False,
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
    playbook_path = engine._playbook_path
    if not playbook_path or not playbook_path.exists():
        raise HTTPException(status_code=404, detail="Playbook file not found")

    yaml_content = playbook_path.read_text()

    state = engine.get_current_execution()
    playbook_name = state.playbook_name if state else "Unknown"

    return {
        "execution_id": execution_id,
        "playbook_path": str(playbook_path),
        "playbook_name": playbook_name,
        "code": yaml_content  # Frontend expects 'code' field
    }


@router.put("/{execution_id}/playbook/code")
async def update_playbook_code(execution_id: str, request: PlaybookCodeUpdateRequest):
    """Update the playbook YAML during execution (for AI fixes)"""
    active_engines = get_active_engines()

    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    engine = active_engines[execution_id]

    # Get playbook path
    playbook_path = engine._playbook_path
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
