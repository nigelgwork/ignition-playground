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
from ignition_toolkit.gateway import GatewayClient
from ignition_toolkit.credentials import CredentialVault
from ignition_toolkit.storage import get_database
from ignition_toolkit import __version__

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Ignition Automation Toolkit API",
    description="REST API for Ignition Gateway automation",
    version=__version__,
)

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


# Pydantic models for API
class ParameterInfo(BaseModel):
    """Parameter definition for frontend"""

    name: str
    type: str
    required: bool
    default: Optional[str] = None
    description: str = ""


class PlaybookInfo(BaseModel):
    """Playbook metadata"""

    name: str
    path: str
    version: str
    description: str
    parameter_count: int
    step_count: int
    parameters: List[ParameterInfo] = []


class ExecutionRequest(BaseModel):
    """Request to execute a playbook"""

    playbook_path: str
    parameters: Dict[str, str]
    gateway_url: Optional[str] = None

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


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.3",
        "timestamp": datetime.now().isoformat(),
    }


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

            playbooks.append(
                PlaybookInfo(
                    name=playbook.name,
                    path=str(yaml_file),
                    version=playbook.version,
                    description=playbook.description,
                    parameter_count=len(playbook.parameters),
                    step_count=len(playbook.steps),
                    parameters=parameters,
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

        return PlaybookInfo(
            name=playbook.name,
            path=str(validated_path),
            version=playbook.version,
            description=playbook.description,
            parameter_count=len(playbook.parameters),
            step_count=len(playbook.steps),
            parameters=parameters,
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
        gateway_client = None
        if request.gateway_url:
            gateway_client = GatewayClient(request.gateway_url)

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

        # Start execution in background
        async def run_execution():
            try:
                if gateway_client:
                    await gateway_client.__aenter__()

                execution_state = await engine.execute_playbook(
                    playbook,
                    request.parameters,
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

            executions.append(ExecutionStatusResponse(
                execution_id=state.execution_id,
                playbook_name=state.playbook_name,
                status=state.status.value,
                started_at=state.started_at,
                completed_at=state.completed_at,
                current_step_index=state.current_step_index,
                total_steps=len(state.step_results) + 1,
                error=state.error,
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
                    ))
    except Exception as e:
        logger.warning(f"Failed to fetch executions from database: {e}")

    # Sort by started_at (most recent first) and limit
    executions.sort(key=lambda x: x.started_at, reverse=True)
    return executions[:limit]


@app.get("/api/executions/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(execution_id: str):
    """Get execution status"""
    # Check active engines
    if execution_id in active_engines:
        engine = active_engines[execution_id]
        state = engine.get_current_execution()
        if state:
            return ExecutionStatusResponse(
                execution_id=state.execution_id,
                playbook_name=state.playbook_name,
                status=state.status.value,
                started_at=state.started_at,
                completed_at=state.completed_at,
                current_step_index=state.current_step_index,
                total_steps=len(state.step_results) + 1,  # Approximate
                error=state.error,
            )

    raise HTTPException(status_code=404, detail="Execution not found")


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


# Credential management endpoints
class CredentialInfo(BaseModel):
    """Credential information (without password)"""
    name: str
    username: str
    description: Optional[str] = ""


class CredentialCreate(BaseModel):
    """Credential creation request"""
    name: str
    username: str
    password: str
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
                description=credential.description
            )
        )

        return {"message": "Credential added successfully", "name": credential.name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding credential: {e}")
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
            "execution_id": execution_id,
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


# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Ignition Automation Toolkit API started")

    # Security warning for default WebSocket API key
    ws_api_key = os.getenv("WEBSOCKET_API_KEY", "dev-key-change-in-production")
    if ws_api_key == "dev-key-change-in-production":
        logger.warning("=" * 80)
        logger.warning("SECURITY WARNING: Using default WebSocket API key!")
        logger.warning("Set WEBSOCKET_API_KEY environment variable for production")
        logger.warning("See SECURITY.md for production deployment guidelines")
        logger.warning("=" * 80)

    # Start periodic cleanup task
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes
            try:
                await cleanup_old_executions()
            except Exception as e:
                logger.exception(f"Error in periodic cleanup: {e}")

    asyncio.create_task(periodic_cleanup())


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


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Ignition Automation Toolkit API shutting down")

    # Cancel all active executions
    for engine in active_engines.values():
        try:
            await engine.cancel()
        except Exception as e:
            logger.exception(f"Error cancelling execution: {e}")

    # Close WebSocket connections
    for ws in websocket_connections:
        try:
            await ws.close()
        except Exception:
            pass
