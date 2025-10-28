"""
WebSocket endpoints router

Handles real-time updates for playbook executions and Claude Code PTY sessions.
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
from typing import Dict, List
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ignition_toolkit.playbook.models import ExecutionState
from ignition_toolkit.playbook.engine import PlaybookEngine
from ignition_toolkit.core.paths import get_playbooks_dir

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websockets"])


# Dependency injection functions to access global state
def get_websocket_connections() -> List[WebSocket]:
    """Get shared websocket connections list from app"""
    from ignition_toolkit.api.app import websocket_connections
    return websocket_connections


def get_active_engines() -> Dict[str, "PlaybookEngine"]:
    """Get shared active engines dict from app"""
    from ignition_toolkit.api.app import active_engines
    return active_engines


def get_claude_code_processes() -> Dict[str, subprocess.Popen]:
    """Get shared claude code processes dict from app"""
    from ignition_toolkit.api.app import claude_code_processes
    return claude_code_processes


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@router.websocket("/ws/executions")
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

    websocket_connections = get_websocket_connections()
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


@router.websocket("/ws/claude-code/{execution_id}")
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
        active_engines = get_active_engines()
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

        claude_code_processes = get_claude_code_processes()
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

        claude_code_processes = get_claude_code_processes()
        if execution_id in claude_code_processes:
            del claude_code_processes[execution_id]

        try:
            await websocket.close()
        except Exception:
            pass


# ============================================================================
# Broadcast Helper Functions
# ============================================================================

async def broadcast_execution_state(state: ExecutionState):
    """Broadcast execution state to all connected WebSocket clients"""
    websocket_connections = get_websocket_connections()

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


@router.websocket("/ws/shell")
async def shell_terminal(websocket: WebSocket):
    """
    WebSocket endpoint for embedded bash shell terminal.
    Spawns a bash shell with PTY in the specified directory (default: playbooks).
    """
    # Get working directory from query params
    working_dir = websocket.query_params.get("path", str(get_playbooks_dir().resolve()))

    await websocket.accept()
    logger.info(f"Shell WebSocket connected, working directory: {working_dir}")

    master_fd = None
    process = None

    try:
        # Validate working directory exists
        if not os.path.isdir(working_dir):
            await websocket.send_json({
                "type": "error",
                "message": f"Directory does not exist: {working_dir}"
            })
            await websocket.close(code=1008, reason="Invalid directory")
            return

        # Spawn bash with PTY
        master_fd, slave_fd = pty.openpty()

        # Start bash in the specified directory
        process = subprocess.Popen(
            ["/bin/bash"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=working_dir,
            preexec_fn=os.setsid,  # Create new process group
            close_fds=True,
            env={**os.environ, "PS1": "$ "}  # Simple prompt
        )

        os.close(slave_fd)  # Parent doesn't need slave_fd

        logger.info(f"Bash shell started: PID={process.pid}, cwd={working_dir}")

        # Create tasks for bidirectional I/O
        async def read_from_pty():
            """Read output from PTY and send to WebSocket"""
            while True:
                try:
                    # Check if process is still alive
                    if process.poll() is not None:
                        logger.info(f"Shell process exited: {process.pid}")
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
                        # Send as JSON with output field
                        try:
                            decoded = data.decode('utf-8', errors='replace')
                            await websocket.send_json({"output": decoded})
                        except Exception as e:
                            logger.error(f"Error decoding output: {e}")
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
                    message = await websocket.receive_json()

                    if "input" in message:
                        # Text input from terminal
                        data = message["input"]
                        os.write(master_fd, data.encode('utf-8'))

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
        logger.exception(f"Shell WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass

    finally:
        # Cleanup
        logger.info(f"Cleaning up shell session, PID: {process.pid if process else 'N/A'}")

        if process:
            try:
                # Try graceful termination first
                if process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # Force kill if still running
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        process.wait()
            except Exception as e:
                logger.error(f"Error terminating shell process: {e}")

        if master_fd is not None:
            try:
                os.close(master_fd)
            except Exception:
                pass

        try:
            await websocket.close()
        except Exception:
            pass


async def broadcast_screenshot_frame(execution_id: str, screenshot_b64: str):
    """
    Broadcast screenshot frame to all connected WebSocket clients

    Args:
        execution_id: Execution ID this screenshot belongs to
        screenshot_b64: Base64-encoded JPEG screenshot data
    """
    websocket_connections = get_websocket_connections()

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
