"""
WebSocket Manager - Centralized WebSocket connection management

Manages WebSocket connections and broadcasts execution updates.
"""

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts

    Responsibilities:
    - Track active WebSocket connections
    - Broadcast execution state updates
    - Broadcast screenshot frames
    - Handle connection cleanup
    """

    def __init__(self):
        """Initialize WebSocket manager"""
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """
        Add new WebSocket connection

        Args:
            websocket: WebSocket connection to add
        """
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)
            logger.info(f"WebSocket connected. Total connections: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove WebSocket connection

        Args:
            websocket: WebSocket connection to remove
        """
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)
                logger.info(
                    f"WebSocket disconnected. Total connections: {len(self._connections)}"
                )

    async def broadcast_execution_state(self, state: "ExecutionState") -> None:
        """
        Broadcast execution state to all connected clients

        Args:
            state: ExecutionState object to broadcast
        """
        from ignition_toolkit.api.routers.models import StepResultResponse

        # Convert step results to response format
        step_results = [
            StepResultResponse(
                step_id=result.step_id,
                step_name=result.step_name,
                status=result.status.value
                if hasattr(result.status, "value")
                else result.status,
                error=result.error,
                started_at=result.started_at,
                completed_at=result.completed_at,
                output=result.output,
            )
            for result in state.step_results
        ]

        message = {
            "type": "execution_update",
            "execution_id": state.execution_id,
            "playbook_name": state.playbook_name,
            "status": state.status.value if hasattr(state.status, "value") else state.status,
            "current_step_index": state.current_step_index,
            "started_at": state.started_at.isoformat() if state.started_at else None,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "error": state.error,
            "step_results": [
                {
                    "step_id": sr.step_id,
                    "step_name": sr.step_name,
                    "status": sr.status,
                    "error": sr.error,
                    "started_at": sr.started_at.isoformat() if sr.started_at else None,
                    "completed_at": sr.completed_at.isoformat() if sr.completed_at else None,
                    "output": sr.output,
                }
                for sr in step_results
            ],
        }

        await self._broadcast(message)

    async def broadcast_screenshot(self, execution_id: str, screenshot_b64: str) -> None:
        """
        Broadcast screenshot frame to all connected clients

        Args:
            execution_id: Execution UUID
            screenshot_b64: Base64-encoded screenshot
        """
        message = {
            "type": "screenshot_frame",
            "execution_id": execution_id,
            "screenshot": screenshot_b64,
        }
        await self._broadcast(message)

    async def broadcast_debug_context(
        self, execution_id: str, debug_context: dict[str, Any]
    ) -> None:
        """
        Broadcast debug context on failure

        Args:
            execution_id: Execution UUID
            debug_context: Debug context dictionary
        """
        message = {
            "type": "debug_context",
            "execution_id": execution_id,
            "context": debug_context,
        }
        await self._broadcast(message)

    async def _broadcast(self, message: dict) -> None:
        """
        Send message to all connected clients

        Args:
            message: Message dictionary to broadcast
        """
        disconnected = []

        async with self._lock:
            for ws in self._connections:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to WebSocket: {e}")
                    disconnected.append(ws)

            # Clean up disconnected clients
            for ws in disconnected:
                self._connections.remove(ws)

        if disconnected:
            logger.info(f"Removed {len(disconnected)} disconnected WebSocket(s)")

    async def close_all(self) -> None:
        """
        Close all WebSocket connections (called on shutdown)
        """
        logger.info("Closing all WebSocket connections...")

        async with self._lock:
            for ws in self._connections:
                try:
                    await ws.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")

            self._connections.clear()

        logger.info("All WebSocket connections closed")

    def get_connection_count(self) -> int:
        """
        Get number of active connections

        Returns:
            Number of active WebSocket connections
        """
        return len(self._connections)
