"""
FastAPI application - Main API server

Provides REST endpoints for playbook management and execution control.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, validator

from ignition_toolkit.playbook.loader import PlaybookLoader
from ignition_toolkit.playbook.engine import PlaybookEngine
from ignition_toolkit.playbook.models import ExecutionState, ExecutionStatus
from ignition_toolkit.playbook.metadata import PlaybookMetadataStore
from ignition_toolkit.gateway import GatewayClient
from ignition_toolkit.credentials import CredentialVault
from ignition_toolkit.storage import get_database
from ignition_toolkit import __version__
from ignition_toolkit.startup.lifecycle import lifespan
from ignition_toolkit.api.routers import health_router

logger = logging.getLogger(__name__)

# Create FastAPI app with lifespan manager
app = FastAPI(
    title="Ignition Automation Toolkit API",
    description="REST API for Ignition Gateway automation",
    version=__version__,
    lifespan=lifespan,
)

# Register health check router FIRST (before other routes)
app.include_router(health_router)

# CORS middleware - Restrict to localhost only (secure default)
import os
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5000,http://127.0.0.1:5000,http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Restricted to configured origins only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_engines: Dict[str, PlaybookEngine] = {}
engine_completion_times: Dict[str, datetime] = {}  # Track when engines completed for TTL cleanup
websocket_connections: List[WebSocket] = []

# Configuration
EXECUTION_TTL_MINUTES = 30  # Keep completed executions for 30 minutes

# Initialize playbook metadata store
metadata_store = PlaybookMetadataStore()


# Pydantic models for API
class ParameterInfo(BaseModel):
    """Parameter definition for frontend"""

    name: str
    type: str
    required: bool
    default: Optional[str] = None
    description: str = ""


class StepInfo(BaseModel):
    """Step definition for frontend"""

    id: str
    name: str
    type: str
    timeout: int
    retry_count: int


class PlaybookInfo(BaseModel):
    """Playbook metadata"""

    name: str
    path: str
    version: str
    description: str
    parameter_count: int
    step_count: int
    parameters: List[ParameterInfo] = []
    steps: List[StepInfo] = []
    # Metadata fields
    revision: int = 0
    verified: bool = False
    enabled: bool = True
    last_modified: Optional[str] = None
    verified_at: Optional[str] = None


class ExecutionRequest(BaseModel):
    """Request to execute a playbook"""

    playbook_path: str
    parameters: Dict[str, str]
    gateway_url: Optional[str] = None
    credential_name: Optional[str] = None  # Name of saved credential to use
    debug_mode: Optional[bool] = False  # Enable debug mode for this execution

    @validator('parameters')
    def validate_parameters(cls, v):
        """Validate parameters to prevent injection attacks and DoS"""
        # Limit number of parameters
        if len(v) > 50:
            raise ValueError('Too many parameters (max 50)')

        # Limit value length to prevent DoS
        for key, value in v.items():
            if len(key) > 255:
                raise ValueError(f'Parameter name too long (max 255 chars)')
            if len(value) > 10000:
                raise ValueError(f'Parameter "{key}" value too long (max 10000 chars)')

            # Check for potentially dangerous characters
            dangerous_chars = [';', '--', '/*', '*/', '<?', '?>']
            for char in dangerous_chars:
                if char in value:
                    logger.warning(f'Potentially dangerous characters in parameter "{key}": {char}')

        return v

    @validator('gateway_url')
    def validate_gateway_url(cls, v):
        """Validate gateway URL format"""
        if v is not None:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('Gateway URL must start with http:// or https://')
            if len(v) > 500:
                raise ValueError('Gateway URL too long (max 500 chars)')
        return v


class ExecutionResponse(BaseModel):
    """Response with execution ID"""

    execution_id: str
    status: str
    message: str


class StepResultResponse(BaseModel):
    """Step execution result"""
    step_id: str
    step_name: str
    status: str
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionStatusResponse(BaseModel):
    """Current execution status"""

    execution_id: str
    playbook_name: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    current_step_index: int
    total_steps: int
    error: Optional[str]
    step_results: Optional[List[StepResultResponse]] = None


# Frontend static files will be mounted AFTER all API routes to avoid conflicts
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"


# TTL-based execution cleanup
async def cleanup_old_executions():
    """Remove completed executions older than TTL from memory"""
    from datetime import timedelta

    current_time = datetime.now()
    ttl_delta = timedelta(minutes=EXECUTION_TTL_MINUTES)
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


# Playbook endpoints
@app.get("/api/playbooks", response_model=List[PlaybookInfo])
async def list_playbooks():
    """List all available playbooks"""
    playbooks_dir = Path("./playbooks")
    if not playbooks_dir.exists():
        return []

    playbooks = []
    for yaml_file in playbooks_dir.rglob("*.yaml"):
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
                    path=str(yaml_file),
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


@app.get("/api/playbooks/{playbook_path:path}", response_model=PlaybookInfo)
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


# Execution endpoints
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
    playbooks_dir = Path("./playbooks").resolve()

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


@app.post("/api/executions", response_model=ExecutionResponse)
async def start_execution(request: ExecutionRequest, background_tasks: BackgroundTasks):
    """Start playbook execution"""
    try:
        # Validate and load playbook (prevents path traversal)
        playbook_path = validate_playbook_path(request.playbook_path)
        loader = PlaybookLoader()
        playbook = loader.load_from_file(playbook_path)

        # Create components
        vault = CredentialVault()
        database = get_database()

        # If credential_name provided, load credential and auto-fill parameters
        parameters = request.parameters.copy()
        gateway_url = request.gateway_url

        print(f"DEBUG: Request credential_name: {request.credential_name}")
        print(f"DEBUG: Request gateway_url: {request.gateway_url}")
        print(f"DEBUG: Request parameters: {request.parameters}")

        if request.credential_name:
            credential = vault.get_credential(request.credential_name)
            if not credential:
                raise HTTPException(status_code=404, detail=f"Credential '{request.credential_name}' not found")

            print(f"DEBUG: Loaded credential: name={credential.name}, gateway_url={credential.gateway_url}, username={credential.username}")

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

            print(f"DEBUG: Parameters after auto-fill: {parameters}")

        gateway_client = None
        if gateway_url:
            gateway_client = GatewayClient(gateway_url)

        # Create screenshot callback for browser streaming
        async def screenshot_callback(execution_id: str, screenshot_b64: str):
            await broadcast_screenshot_frame(execution_id, screenshot_b64)

        # Create engine
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
        import uuid
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
                    parameters,  # Use auto-filled parameters instead of request.parameters
                    base_path=Path(request.playbook_path).parent,
                    execution_id=execution_id,  # Pass the pre-generated ID
                )

                logger.info(
                    f"Execution {execution_state.execution_id} completed with status: {execution_state.status}"
                )

            except Exception as e:
                logger.exception(f"Execution error: {e}")
            finally:
                if gateway_client:
                    await gateway_client.__aexit__(None, None, None)
                # Mark completion time for TTL-based cleanup (don't delete immediately)
                engine_completion_times[execution_id] = datetime.now()
                logger.info(f"Execution {execution_id} marked for TTL cleanup")

        # Start execution in background
        background_tasks.add_task(run_execution)

        return ExecutionResponse(
            execution_id=execution_id,
            status="starting",
            message="Playbook execution started",
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to start execution: {e}")


@app.get("/api/executions", response_model=List[ExecutionStatusResponse])
async def list_executions(limit: int = 50, status: Optional[str] = None):
    """
    List recent executions from database and active engines

    Args:
        limit: Maximum number of executions to return (default 50)
        status: Optional filter by status (running, completed, failed, etc.)
    """
    # Cleanup old executions before listing
    await cleanup_old_executions()

    executions = []

    # First, add all active executions
    for exec_id, engine in active_engines.items():
        state = engine.get_current_execution()
        if state:
            # Apply status filter if provided
            if status and state.status.value != status:
                continue

            # Convert step results to response format
            step_results = [
                StepResultResponse(
                    step_id=step.step_id,
                    step_name=step.step_name,
                    status=step.status.value,
                    error=step.error,
                    started_at=step.started_at,
                    completed_at=step.completed_at,
                )
                for step in state.step_results
            ]

            executions.append(ExecutionStatusResponse(
                execution_id=state.execution_id,
                playbook_name=state.playbook_name,
                status=state.status.value,
                started_at=state.started_at,
                completed_at=state.completed_at,
                current_step_index=state.current_step_index,
                total_steps=len(state.step_results) + 1,
                error=state.error,
                step_results=step_results,
            ))

    # Then, fetch recent executions from database
    try:
        database = get_database()
        with database.session_scope() as session:
            from ignition_toolkit.storage.models import ExecutionModel
            query = session.query(ExecutionModel).order_by(
                ExecutionModel.started_at.desc()
            )

            # Apply status filter if provided
            if status:
                query = query.filter(ExecutionModel.status == status)

            db_executions = query.limit(limit).all()

            # Add executions from DB that aren't already in active list
            active_ids = {e.execution_id for e in executions}
            for db_exec in db_executions:
                if db_exec.execution_id not in active_ids:
                    executions.append(ExecutionStatusResponse(
                        execution_id=db_exec.execution_id,
                        playbook_name=db_exec.playbook_name,
                        status=db_exec.status,
                        started_at=db_exec.started_at,
                        completed_at=db_exec.completed_at,
                        current_step_index=0,  # Not tracked in DB model
                        total_steps=0,  # Not tracked in DB model
                        error=db_exec.error_message,
                        step_results=[],  # Return empty array instead of null for consistency
                    ))
    except Exception as e:
        logger.warning(f"Failed to fetch executions from database: {e}")

    # Sort by started_at (most recent first) and limit
    executions.sort(key=lambda x: x.started_at, reverse=True)
    return executions[:limit]


@app.get("/api/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """Get execution status"""
    # Check active engines first (for running executions)
    if execution_id in active_engines:
        engine = active_engines[execution_id]
        state = engine.get_current_execution()
        if state:
            # Convert step results to response format
            step_results = [
                StepResultResponse(
                    step_id=step.step_id,
                    step_name=step.step_name,
                    status=step.status.value,
                    error=step.error,
                    started_at=step.started_at,
                    completed_at=step.completed_at,
                )
                for step in state.step_results
            ]

            return ExecutionStatusResponse(
                execution_id=state.execution_id,
                playbook_name=state.playbook_name,
                status=state.status.value,
                started_at=state.started_at,
                completed_at=state.completed_at,
                current_step_index=state.current_step_index,
                total_steps=len(state.step_results) + 1,  # Approximate
                error=state.error,
                step_results=step_results,
            )

    # If not in active engines, check database (for completed executions)
    try:
        database = get_database()
        with database.session_scope() as session:
            from ignition_toolkit.storage.models import ExecutionModel, StepResultModel

            db_exec = session.query(ExecutionModel).filter(
                ExecutionModel.execution_id == execution_id
            ).first()

            if db_exec:
                # Get step results from database
                # NOTE: execution_id column is INTEGER FK to executions.id, not UUID
                db_steps = session.query(StepResultModel).filter(
                    StepResultModel.execution_id == db_exec.id
                ).order_by(StepResultModel.id).all()

                step_results = [
                    StepResultResponse(
                        step_id=step.step_id,
                        step_name=step.step_name,
                        status=step.status,
                        error=step.error_message,
                        started_at=step.started_at,
                        completed_at=step.completed_at,
                    )
                    for step in db_steps
                ]

                return ExecutionStatusResponse(
                    execution_id=db_exec.execution_id,
                    playbook_name=db_exec.playbook_name,
                    status=db_exec.status,
                    started_at=db_exec.started_at,
                    completed_at=db_exec.completed_at,
                    current_step_index=len(db_steps) - 1 if db_steps else 0,
                    total_steps=len(db_steps),
                    error=db_exec.error_message,
                    step_results=step_results,
                )
    except Exception as e:
        logger.warning(f"Failed to fetch execution from database: {e}")

    raise HTTPException(status_code=404, detail="Execution not found")


@app.get("/api/executions/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_execution_status_with_path(execution_id: str):
    """Get execution status (alternative route for frontend compatibility)"""
    return await get_execution_status(execution_id)


@app.post("/api/executions/{execution_id}/pause")
async def pause_execution(execution_id: str):
    """Pause execution"""
    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail="Execution not found")

    engine = active_engines[execution_id]
    await engine.pause()

    return {"status": "paused", "execution_id": execution_id}


@app.post("/api/executions/{execution_id}/resume")
async def resume_execution(execution_id: str):
    """Resume execution"""
    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail="Execution not found")

    engine = active_engines[execution_id]
    await engine.resume()

    return {"status": "resumed", "execution_id": execution_id}


@app.post("/api/executions/{execution_id}/skip")
async def skip_step(execution_id: str):
    """Skip current step"""
    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail="Execution not found")

    engine = active_engines[execution_id]
    await engine.skip_current_step()

    return {"status": "skipped", "execution_id": execution_id}


@app.post("/api/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str):
    """Cancel execution"""
    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail="Execution not found")

    engine = active_engines[execution_id]
    await engine.cancel()

    return {"status": "cancelled", "execution_id": execution_id}


# Debug Mode Endpoints

@app.post("/api/executions/{execution_id}/debug/enable")
async def enable_debug_mode(execution_id: str):
    """Enable debug mode - auto-pause on failures"""
    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail="Execution not found")

    engine = active_engines[execution_id]
    engine.state_manager.enable_debug_mode()

    return {"status": "enabled", "execution_id": execution_id}


@app.post("/api/executions/{execution_id}/debug/disable")
async def disable_debug_mode(execution_id: str):
    """Disable debug mode"""
    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail="Execution not found")

    engine = active_engines[execution_id]
    engine.state_manager.disable_debug_mode()

    return {"status": "disabled", "execution_id": execution_id}


@app.get("/api/executions/{execution_id}/debug/context")
async def get_debug_context(execution_id: str):
    """Get debug context (screenshot, HTML, step info, error)"""
    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail="Execution not found")

    engine = active_engines[execution_id]
    context = engine.state_manager.get_debug_context()

    if not context:
        raise HTTPException(status_code=404, detail="No debug context available")

    return context


@app.get("/api/executions/{execution_id}/debug/dom")
async def get_debug_dom(execution_id: str):
    """Get current page DOM/HTML"""
    if execution_id not in active_engines:
        raise HTTPException(status_code=404, detail="Execution not found")

    engine = active_engines[execution_id]

    # Get HTML from browser if available
    if engine._browser_manager:
        try:
            html = await engine._browser_manager.get_page_html()
            return {"html": html}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get DOM: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="No browser available for this execution")


# Playbook Update Endpoint

class PlaybookUpdateRequest(BaseModel):
    """Request to update a playbook YAML file"""
    playbook_path: str  # Relative path from playbooks directory
    yaml_content: str  # New YAML content


@app.put("/api/playbooks/update")
async def update_playbook(request: PlaybookUpdateRequest):
    """
    Update a playbook YAML file with new content

    This is used when applying fixes from debug mode.
    Creates a backup before updating.
    """
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
        from datetime import datetime
        backup_path = playbook_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
        backup_path.write_text(playbook_path.read_text())
        logger.info(f"Created backup: {backup_path}")

        # Validate YAML syntax before writing
        import yaml
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


# Credential management endpoints
class CredentialInfo(BaseModel):
    """Credential information (without password)"""
    name: str
    username: str
    gateway_url: Optional[str] = None
    description: Optional[str] = ""


class CredentialCreate(BaseModel):
    """Credential creation request"""
    name: str
    username: str
    password: str
    gateway_url: Optional[str] = None
    description: Optional[str] = ""


@app.get("/api/credentials", response_model=List[CredentialInfo])
async def list_credentials():
    """List all credentials (without passwords)"""
    try:
        vault = CredentialVault()
        credentials = vault.list_credentials()
        return [
            CredentialInfo(
                name=cred.name,
                username=cred.username,
                gateway_url=cred.gateway_url,
                description=cred.description or ""
            )
            for cred in credentials
        ]
    except Exception as e:
        logger.error(f"Error listing credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/credentials")
async def add_credential(credential: CredentialCreate):
    """Add new credential"""
    try:
        vault = CredentialVault()
        from ignition_toolkit.credentials.vault import Credential

        # Check if credential already exists
        try:
            existing = vault.get_credential(credential.name)
            if existing:
                raise HTTPException(status_code=400, detail=f"Credential '{credential.name}' already exists")
        except ValueError:
            # Credential doesn't exist, which is what we want
            pass

        # Save new credential
        vault.save_credential(
            Credential(
                name=credential.name,
                username=credential.username,
                password=credential.password,
                gateway_url=credential.gateway_url,
                description=credential.description
            )
        )

        return {"message": "Credential added successfully", "name": credential.name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding credential: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/credentials/{name}")
async def update_credential(name: str, credential: CredentialCreate):
    """Update existing credential"""
    try:
        vault = CredentialVault()
        from ignition_toolkit.credentials.vault import Credential

        # Check if credential exists
        try:
            existing = vault.get_credential(name)
            if not existing:
                raise HTTPException(status_code=404, detail=f"Credential '{name}' not found")
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Credential '{name}' not found")

        # Update credential (delete and re-add with same name)
        vault.delete_credential(name)
        vault.save_credential(
            Credential(
                name=name,  # Use name from URL path, not from body
                username=credential.username,
                password=credential.password,
                gateway_url=credential.gateway_url,
                description=credential.description
            )
        )

        return {"message": "Credential updated successfully", "name": name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating credential: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/credentials/{name}")
async def delete_credential(name: str):
    """Delete credential"""
    try:
        vault = CredentialVault()
        success = vault.delete_credential(name)

        if not success:
            raise HTTPException(status_code=404, detail=f"Credential '{name}' not found")

        return {"message": "Credential deleted successfully", "name": name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting credential: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Playbook Metadata Endpoints

@app.post("/api/playbooks/{playbook_path:path}/verify")
async def mark_playbook_verified(playbook_path: str):
    """Mark a playbook as verified"""
    try:
        metadata_store.mark_verified(playbook_path, verified_by="user")
        meta = metadata_store.get_metadata(playbook_path)
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


@app.post("/api/playbooks/{playbook_path:path}/unverify")
async def unmark_playbook_verified(playbook_path: str):
    """Unmark a playbook as verified"""
    try:
        metadata_store.unmark_verified(playbook_path)
        return {
            "status": "success",
            "playbook_path": playbook_path,
            "verified": False,
            "message": "Playbook verification removed"
        }
    except Exception as e:
        logger.error(f"Error unmarking playbook as verified: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/playbooks/{playbook_path:path}/enable")
async def enable_playbook(playbook_path: str):
    """Enable a playbook"""
    try:
        metadata_store.set_enabled(playbook_path, True)
        return {
            "status": "success",
            "playbook_path": playbook_path,
            "enabled": True,
            "message": "Playbook enabled"
        }
    except Exception as e:
        logger.error(f"Error enabling playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/playbooks/{playbook_path:path}/disable")
async def disable_playbook(playbook_path: str):
    """Disable a playbook"""
    try:
        metadata_store.set_enabled(playbook_path, False)
        return {
            "status": "success",
            "playbook_path": playbook_path,
            "enabled": False,
            "message": "Playbook disabled"
        }
    except Exception as e:
        logger.error(f"Error disabling playbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates
@app.websocket("/ws/executions")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time execution updates"""
    # Simple authentication: check for API key in query params
    # In production, use proper token-based auth
    api_key = websocket.query_params.get("api_key")
    expected_key = os.getenv("WEBSOCKET_API_KEY", "dev-key-change-in-production")

    if api_key != expected_key:
        logger.warning(f"Unauthorized WebSocket connection attempt from {websocket.client}")
        await websocket.close(code=1008, reason="Unauthorized")
        return

    await websocket.accept()
    logger.info(f"WebSocket connection accepted from {websocket.client}")
    websocket_connections.append(websocket)

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_json({"type": "pong", "data": data})

    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("WebSocket client disconnected")


async def broadcast_execution_state(state: ExecutionState):
    """Broadcast execution state to all connected WebSocket clients"""
    if not websocket_connections:
        return

    message = {
        "type": "execution_update",
        "data": {
            "execution_id": state.execution_id,
            "playbook_name": state.playbook_name,
            "status": state.status.value,
            "current_step_index": state.current_step_index,
            "error": state.error,  # Overall execution error
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "step_results": [
                {
                    "step_id": r.step_id,
                    "step_name": r.step_name,
                    "status": r.status.value,
                    "error": r.error,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                }
                for r in state.step_results
            ],
        },
    }

    # Send to all connected clients
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket client: {e}")
            disconnected.append(websocket)

    # Remove disconnected clients
    for ws in disconnected:
        if ws in websocket_connections:
            websocket_connections.remove(ws)


async def broadcast_screenshot_frame(execution_id: str, screenshot_b64: str):
    """
    Broadcast screenshot frame to all connected WebSocket clients

    Args:
        execution_id: Execution ID this screenshot belongs to
        screenshot_b64: Base64-encoded JPEG screenshot data
    """
    if not websocket_connections:
        return

    message = {
        "type": "screenshot_frame",
        "data": {
            "executionId": execution_id,  # camelCase to match frontend
            "screenshot": screenshot_b64,
            "timestamp": datetime.now().isoformat()
        }
    }

    # Send to all connected clients
    disconnected = []
    for websocket in websocket_connections:
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning(f"Failed to send screenshot to WebSocket client: {e}")
            disconnected.append(websocket)

    # Remove disconnected clients
    for ws in disconnected:
        if ws in websocket_connections:
            websocket_connections.remove(ws)


# Note: Startup logic moved to startup/lifecycle.py lifespan manager
# Security warning for WebSocket API key is now in environment validation


# Serve frontend (React build) - MUST be at the END to avoid catching API routes
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    # Mount static assets directory
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Serve index.html for all routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React SPA - returns index.html for all non-API routes"""
        # Serve index.html for all other routes (React Router handles routing)
        index_path = frontend_dist / "index.html"
        return FileResponse(str(index_path))
else:
    logger.warning("Frontend build not found at frontend/dist - run 'npm run build' in frontend/ directory")


# Note: Shutdown logic moved to startup/lifecycle.py lifespan manager
