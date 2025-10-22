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
    version="1.0.0",
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
        "version": "1.0.0",
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

        # Start execution in background
        async def run_execution():
            try:
                if gateway_client:
                    await gateway_client.__aenter__()

                execution_state = await engine.execute_playbook(
                    playbook,
                    request.parameters,
                    base_path=Path(request.playbook_path).parent,
                )

                logger.info(
                    f"Execution {execution_state.execution_id} completed with status: {execution_state.status}"
                )

            except Exception as e:
                logger.exception(f"Execution error: {e}")
            finally:
                if gateway_client:
                    await gateway_client.__aexit__(None, None, None)
                # Remove from active engines
                if engine.get_current_execution():
                    exec_id = engine.get_current_execution().execution_id
                    if exec_id in active_engines:
                        del active_engines[exec_id]

        # Generate execution ID (will be set by engine)
        # For now, start execution and return pending response
        background_tasks.add_task(run_execution)

        # Store engine temporarily (will be updated with actual ID)
        temp_id = f"pending_{datetime.now().timestamp()}"
        active_engines[temp_id] = engine

        return ExecutionResponse(
            execution_id=temp_id,
            status="starting",
            message="Playbook execution started",
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to start execution: {e}")


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
