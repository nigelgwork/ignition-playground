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
from pydantic import BaseModel

from ignition_toolkit.playbook.loader import PlaybookLoader
from ignition_toolkit.playbook.engine import PlaybookEngine
from ignition_toolkit.playbook.models import ExecutionState, ExecutionStatus
from ignition_toolkit.gateway import GatewayClient
from ignition_toolkit.credentials import CredentialVault
from ignition_toolkit.storage import get_database

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Ignition Automation Toolkit API",
    description="REST API for Ignition Gateway automation",
    version="1.0.1",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
active_engines: Dict[str, PlaybookEngine] = {}
websocket_connections: List[WebSocket] = []


# Pydantic models for API
class PlaybookInfo(BaseModel):
    """Playbook metadata"""

    name: str
    path: str
    version: str
    description: str
    parameter_count: int
    step_count: int


class ExecutionRequest(BaseModel):
    """Request to execute a playbook"""

    playbook_path: str
    parameters: Dict[str, str]
    gateway_url: Optional[str] = None


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


# Serve frontend
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/")
    async def serve_frontend():
        """Serve frontend index.html"""
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"message": "Frontend not available"}


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.1",
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
            playbooks.append(
                PlaybookInfo(
                    name=playbook.name,
                    path=str(yaml_file),
                    version=playbook.version,
                    description=playbook.description,
                    parameter_count=len(playbook.parameters),
                    step_count=len(playbook.steps),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to load playbook {yaml_file}: {e}")
            continue

    return playbooks


@app.get("/api/playbooks/{playbook_path:path}")
async def get_playbook(playbook_path: str):
    """Get playbook details"""
    try:
        loader = PlaybookLoader()
        playbook = loader.load_from_file(Path(playbook_path))

        return {
            "name": playbook.name,
            "version": playbook.version,
            "description": playbook.description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type.value,
                    "required": p.required,
                    "description": p.description,
                }
                for p in playbook.parameters
            ],
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type.value,
                    "timeout": s.timeout,
                }
                for s in playbook.steps
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Playbook not found: {e}")


# Execution endpoints
@app.post("/api/executions", response_model=ExecutionResponse)
async def start_execution(request: ExecutionRequest, background_tasks: BackgroundTasks):
    """Start playbook execution"""
    try:
        # Load playbook
        loader = PlaybookLoader()
        playbook = loader.load_from_file(Path(request.playbook_path))

        # Create components
        vault = CredentialVault()
        database = get_database()
        gateway_client = None
        if request.gateway_url:
            gateway_client = GatewayClient(request.gateway_url)

        # Create engine
        engine = PlaybookEngine(
            gateway_client=gateway_client,
            credential_vault=vault,
            database=database,
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
                # Remove from active engines after execution completes
                if execution_id in active_engines:
                    del active_engines[execution_id]

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
    await websocket.accept()
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
            "step_results": [
                {
                    "step_id": r.step_id,
                    "status": r.status.value,
                    "error": r.error,
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


# Startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Ignition Automation Toolkit API started")


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
