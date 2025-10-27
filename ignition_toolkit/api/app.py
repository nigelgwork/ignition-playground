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
from ignition_toolkit.api.routers.websockets import router as websockets_router
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

# Register WebSocket router
app.include_router(websockets_router)

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











# WebSocket endpoints moved to routers/websockets.py

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
