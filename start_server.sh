#!/bin/bash
# Start Ignition Automation Toolkit Server
# Ensures clean startup with verification

echo "=== Starting Ignition Automation Toolkit Server ==="

# PORTABILITY: Dynamically determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Verify we're in the right place
if [ ! -f "${SCRIPT_DIR}/tasks.py" ]; then
    echo "❌ ERROR: Not in project directory (tasks.py not found)"
    echo "Current directory: ${SCRIPT_DIR}"
    exit 1
fi

# Check if server is already running
EXISTING=$(pgrep -f "uvicorn.*ignition_toolkit" | wc -l)
if [ "$EXISTING" -gt 0 ]; then
    echo "❌ ERROR: Server already running ($EXISTING process(es))"
    echo "Run './stop_server.sh' first to stop existing server"
    exit 1
fi

# Read port from .env or default to 5000
if [ -f "${SCRIPT_DIR}/.env" ]; then
    PORT=$(grep "^API_PORT=" "${SCRIPT_DIR}/.env" | cut -d'=' -f2)
    PORT=${PORT:-5000}
else
    PORT=5000
fi

# Verify port is free
PORT_CHECK=$(lsof -i :${PORT} 2>/dev/null | grep -v COMMAND | wc -l)
if [ "$PORT_CHECK" -gt 0 ]; then
    echo "❌ ERROR: Port ${PORT} is already in use"
    lsof -i :${PORT} 2>/dev/null
    echo "Run './stop_server.sh' to clean up"
    exit 1
fi

# PORTABILITY: Set Playwright browser cache relative to project
export PLAYWRIGHT_BROWSERS_PATH="${SCRIPT_DIR}/data/.playwright-browsers"

# Optional: Set toolkit data directory override
# export IGNITION_TOOLKIT_DATA=/custom/path/.ignition-toolkit

echo "✅ Pre-flight checks passed"
echo "📍 Project directory: ${SCRIPT_DIR}"
echo "🚀 Starting server on http://0.0.0.0:${PORT}"
echo "📝 Auto-reload DISABLED for stable operation"
echo ""
echo "Press CTRL+C to stop the server"
echo "=========================================="
echo ""

# Change to project directory
cd "${SCRIPT_DIR}" || exit 1

# Start the server WITHOUT auto-reload for stable operation during testing
# Use ./restart_server.sh to apply code changes
exec ./venv/bin/uvicorn ignition_toolkit.api.app:app --host 0.0.0.0 --port ${PORT}
