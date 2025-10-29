#!/bin/bash
# Start Ignition Automation Toolkit Server
# Ensures clean startup with verification

echo "=== Starting Ignition Automation Toolkit Server ==="

# Check if server is already running
EXISTING=$(pgrep -f "uvicorn.*ignition_toolkit" | wc -l)
if [ "$EXISTING" -gt 0 ]; then
    echo "❌ ERROR: Server already running ($EXISTING process(es))"
    echo "Run './stop_server.sh' first to stop existing server"
    exit 1
fi

# Verify port 5000 is free
PORT_CHECK=$(lsof -i :5000 2>/dev/null | grep -v COMMAND | wc -l)
if [ "$PORT_CHECK" -gt 0 ]; then
    echo "❌ ERROR: Port 5000 is already in use"
    lsof -i :5000 2>/dev/null
    echo "Run './stop_server.sh' to clean up"
    exit 1
fi

# Set consistent Playwright browser cache location
export PLAYWRIGHT_BROWSERS_PATH=/git/ignition-playground/data/.playwright-browsers

# Optional: Set toolkit data directory override
# export IGNITION_TOOLKIT_DATA=/custom/path/.ignition-toolkit

echo "✅ Pre-flight checks passed"
echo "🚀 Starting server on http://0.0.0.0:5000"
echo "📝 Auto-reload DISABLED for stable operation"
echo ""
echo "Press CTRL+C to stop the server"
echo "=========================================="
echo ""

# Start the server WITHOUT auto-reload for stable operation during testing
# Use ./restart_server.sh to apply code changes
exec ./venv/bin/uvicorn ignition_toolkit.api.app:app --host 0.0.0.0 --port 5000
