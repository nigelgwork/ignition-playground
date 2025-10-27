"""
FastAPI application - Main API server

Provides REST endpoints for playbook management and execution control.
"""

import asyncio
import logging
import os
import pty
import subprocess
import select
import signal
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Request, Response
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
from ignition_toolkit.ai import AIAssistant
from ignition_toolkit import __version__
from ignition_toolkit.startup.lifecycle import lifespan
from ignition_toolkit.api.routers import health_router
from ignition_toolkit.api.routers.playbooks import router as playbooks_router
from ignition_toolkit.api.routers.executions import router as executions_router
from ignition_toolkit.api.routers.credentials import router as credentials_router
from ignition_toolkit.api.routers.ai import router as ai_router
from ignition_toolkit.core.paths import get_playbooks_dir, get_playbook_path

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

# Register playbooks router
app.include_router(playbooks_router)

# Register executions router
app.include_router(executions_router)

# Register credentials router
app.include_router(credentials_router)

# Register AI router
app.include_router(ai_router)

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
claude_code_processes: Dict[str, subprocess.Popen] = {}  # Track Claude Code PTY processes by execution_id

# AI Assistant (will use ANTHROPIC_API_KEY from environment)
ai_assistant = AIAssistant()

# Configuration
EXECUTION_TTL_MINUTES = 30  # Keep completed executions for 30 minutes

# Initialize playbook metadata store
metadata_store = PlaybookMetadataStore()


# Custom StaticFiles class with cache-busting headers
class NoCacheStaticFiles(StaticFiles):
    """StaticFiles subclass that adds no-cache headers to prevent browser caching"""

    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        # Add no-cache headers to all static files
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


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
    debug_mode: bool = False
    step_results: Optional[List[StepResultResponse]] = None


# Frontend static files will be mounted AFTER all API routes to avoid conflicts
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"



# Execution endpoints


# Credential routes moved to routers/credentials.py


# Playbook Metadata Endpoints











# WebSocket endpoint for real-time updates
@app.websocket("/ws/executions")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time execution updates with heartbeat support"""
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
            # Keep connection alive and handle heartbeat
            data = await websocket.receive_text()

            # Parse message to check for ping
            try:
                import json
                message = json.loads(data)
                if message.get('type') == 'ping':
                    # Respond to heartbeat ping
                    await websocket.send_json({"type": "pong", "timestamp": message.get('timestamp')})
                    logger.debug("Heartbeat ping received and acknowledged")
                else:
                    # Echo back other messages for compatibility
                    await websocket.send_json({"type": "pong", "data": data})
            except json.JSONDecodeError:
                # Not JSON, echo back as before
                await websocket.send_json({"type": "pong", "data": data})

    except WebSocketDisconnect:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)


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


@app.websocket("/ws/claude-code/{execution_id}")
async def claude_code_terminal(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for embedded Claude Code terminal.
    Spawns a Claude Code process with PTY and proxies stdin/stdout.
    """
    await websocket.accept()
    logger.info(f"Claude Code WebSocket connected for execution: {execution_id}")

    master_fd = None
    process = None

    try:
        # Get execution context
        engine = active_engines.get(execution_id)
        if not engine:
            await websocket.send_json({
                "type": "error",
                "message": "Execution not found or not active"
            })
            await websocket.close(code=1008, reason="Execution not found")
            return

        execution_state = engine.get_current_execution()
        if not execution_state:
            await websocket.send_json({
                "type": "error",
                "message": "Execution state not available"
            })
            await websocket.close(code=1008, reason="No execution state")
            return

        # Find playbook path
        playbook_name = execution_state.playbook_name
        playbooks_dir = get_playbooks_dir().resolve()
        playbook_path = None

        import yaml
        # Search for playbook by name
        for yaml_file in playbooks_dir.rglob("*.yaml"):
            # Skip backup files
            if '.backup.' in yaml_file.name:
                continue
            try:
                with open(yaml_file, 'r') as f:
                    playbook_data = yaml.safe_load(f)
                    if playbook_data and playbook_data.get('name') == playbook_name:
                        playbook_path = str(yaml_file.absolute())
                        logger.info(f"Found playbook: {playbook_path}")
                        break
            except Exception as e:
                logger.warning(f"Error reading {yaml_file}: {e}")
                continue

        if not playbook_path:
            error_msg = f"Playbook file not found for '{playbook_name}' in {playbooks_dir}"
            logger.error(error_msg)
            await websocket.send_json({
                "type": "error",
                "message": error_msg
            })
            await websocket.close(code=1008, reason="Playbook not found")
            return

        # Build context message
        context_parts = [
            f"# Playbook Execution Debug Session",
            f"",
            f"**Execution ID:** {execution_id}",
            f"**Playbook:** {playbook_name}",
            f"**Status:** {execution_state.status.value}",
            f"**Current Step:** {execution_state.current_step_index + 1 if execution_state.current_step_index is not None else 'N/A'}",
            f"",
        ]

        # Add step results
        if execution_state.step_results:
            context_parts.append("## Step Results:")
            for idx, result in enumerate(execution_state.step_results, 1):
                status_str = result.status.value if hasattr(result, 'status') else str(result.get('status', 'unknown'))
                status_emoji = "✅" if status_str == "success" else "❌"
                step_name = result.step_name if hasattr(result, 'step_name') else result.get('step_name', 'Unknown')
                context_parts.append(f"{status_emoji} **Step {idx}:** {step_name}")
                error = result.error if hasattr(result, 'error') else result.get('error')
                if error:
                    context_parts.append(f"   Error: {error}")
            context_parts.append("")

        context_message = "\n".join(context_parts)

        # Spawn Claude Code with PTY
        master_fd, slave_fd = pty.openpty()

        # Build command - check environment variable first, then try common names
        claude_cmd = os.getenv("CLAUDE_CLI_COMMAND")  # User can override with env var

        if claude_cmd:
            # User-specified command - verify it exists
            if not shutil.which(claude_cmd):
                error_msg = f"Configured Claude CLI command '{claude_cmd}' not found. Set CLAUDE_CLI_COMMAND environment variable to the correct command."
                logger.error(error_msg)
                await websocket.send_json({
                    "type": "error",
                    "message": error_msg
                })
                await websocket.close(code=1008, reason="Claude CLI not found")
                return
        else:
            # Auto-detect: try common Claude CLI names
            for cmd_name in ["claude-code", "claude-work", "claude", "claude-personal"]:
                found_cmd = shutil.which(cmd_name)
                if found_cmd:
                    claude_cmd = found_cmd
                    break

            if not claude_cmd:
                error_msg = (
                    "Claude CLI not found. Please install one of: claude-code, claude-work, claude, claude-personal\n"
                    "Or set CLAUDE_CLI_COMMAND environment variable to your Claude CLI command name."
                )
                logger.error(error_msg)
                await websocket.send_json({
                    "type": "error",
                    "message": error_msg
                })
                await websocket.close(code=1008, reason="Claude CLI not found")
                return

        logger.info(f"Using Claude CLI: {claude_cmd}")

        # Build arguments - check if it's a script that needs bash
        cmd_file_info = os.path.isfile(claude_cmd)
        context_msg = f"{context_message}\n\nYou are debugging a paused Ignition Automation Toolkit playbook execution. The playbook YAML file is open for editing."

        # Check if the command is a shell script (not a binary)
        is_shell_script = False
        if cmd_file_info:
            try:
                with open(claude_cmd, 'rb') as f:
                    first_bytes = f.read(20)
                    if first_bytes.startswith(b'#!/'):
                        is_shell_script = True
            except Exception:
                pass

        if is_shell_script:
            # It's a shell script - need to invoke through bash
            cmd_args = [
                "/bin/bash",
                claude_cmd,
                "-p", playbook_path,
                "-m", context_msg
            ]
            logger.info(f"Detected shell script, using: /bin/bash {claude_cmd}")
        else:
            # It's a binary - call directly
            cmd_args = [
                claude_cmd,
                "-p", playbook_path,
                "-m", context_msg
            ]

        process = subprocess.Popen(
            cmd_args,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid,  # Create new process group
            close_fds=True
        )

        os.close(slave_fd)  # Parent doesn't need slave_fd
        claude_code_processes[execution_id] = process

        logger.info(f"Claude Code process started: PID={process.pid}, playbook={playbook_path}")

        # Send initial welcome message
        await websocket.send_json({
            "type": "connected",
            "message": f"Claude Code session started for {playbook_name}",
            "pid": process.pid
        })

        # Create tasks for bidirectional I/O
        async def read_from_pty():
            """Read output from PTY and send to WebSocket"""
            while True:
                try:
                    # Check if process is still alive
                    if process.poll() is not None:
                        logger.info(f"Claude Code process exited: {process.pid}")
                        await websocket.send_json({
                            "type": "exit",
                            "code": process.returncode
                        })
                        break

                    # Use select to check if data is available (non-blocking)
                    readable, _, _ = select.select([master_fd], [], [], 0.1)
                    if readable:
                        data = os.read(master_fd, 1024)
                        if not data:
                            break
                        # Send binary data as bytes WebSocket frame
                        await websocket.send_bytes(data)
                    else:
                        # Small sleep to prevent busy loop
                        await asyncio.sleep(0.01)

                except OSError:
                    break
                except Exception as e:
                    logger.error(f"Error reading from PTY: {e}")
                    break

        async def write_to_pty():
            """Receive data from WebSocket and write to PTY"""
            while True:
                try:
                    message = await websocket.receive()

                    if "bytes" in message:
                        # Binary data from terminal
                        data = message["bytes"]
                        os.write(master_fd, data)
                    elif "text" in message:
                        # Text message (e.g., resize events)
                        import json
                        try:
                            msg = json.loads(message["text"])
                            if msg.get("type") == "resize":
                                # Handle terminal resize (optional)
                                pass
                        except json.JSONDecodeError:
                            pass

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error writing to PTY: {e}")
                    break

        # Run both tasks concurrently
        await asyncio.gather(
            read_from_pty(),
            write_to_pty(),
            return_exceptions=True
        )

    except Exception as e:
        logger.exception(f"Claude Code WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass

    finally:
        # Cleanup
        logger.info(f"Cleaning up Claude Code session: {execution_id}")

        if process:
            try:
                # Try graceful termination first
                if process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if still running
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        process.wait()
            except Exception as e:
                logger.error(f"Error terminating Claude Code process: {e}")

        if master_fd is not None:
            try:
                os.close(master_fd)
            except Exception:
                pass

        if execution_id in claude_code_processes:
            del claude_code_processes[execution_id]

        try:
            await websocket.close()
        except Exception:
            pass


# AI routes moved to routers/ai.py





# ============================================================================
# NOTE: AI Credentials endpoints are defined earlier in this file (line ~1362-1440)
# This section intentionally left empty to avoid duplicate endpoint definitions
# ============================================================================


# ============================================================================
# Frontend Serving
# ============================================================================

# Serve frontend (React build) - MUST be at the END to avoid catching API routes
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    # Mount static assets directory with no-cache headers
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", NoCacheStaticFiles(directory=str(assets_dir)), name="assets")

    # Serve index.html for all routes (SPA routing) with cache-busting headers
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve React SPA - returns index.html for all non-API routes with no-cache headers"""
        # Serve index.html for all other routes (React Router handles routing)
        index_path = frontend_dist / "index.html"
        response = FileResponse(str(index_path))
        # Add cache-busting headers to prevent browser caching of index.html
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
else:
    logger.warning("Frontend build not found at frontend/dist - run 'npm run build' in frontend/ directory")


# Note: Shutdown logic moved to startup/lifecycle.py lifespan manager
