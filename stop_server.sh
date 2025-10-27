#!/bin/bash
# Stop Ignition Automation Toolkit Server
# Comprehensive shutdown of all server-related processes

echo "=== Stopping Ignition Automation Toolkit Server ==="

# Count processes before cleanup
UVICORN_COUNT=$(pgrep -f "uvicorn.*ignition_toolkit" | wc -l)
CURL_COUNT=$(pgrep -f "curl.*localhost:5000" | wc -l)

echo "Found $UVICORN_COUNT uvicorn process(es)"
echo "Found $CURL_COUNT hanging curl process(es)"

# Kill all uvicorn processes for this project
if [ "$UVICORN_COUNT" -gt 0 ]; then
    echo "Stopping uvicorn server(s)..."
    pkill -f "uvicorn.*ignition_toolkit"
    sleep 1
fi

# Kill any hanging curl processes to localhost:5000
if [ "$CURL_COUNT" -gt 0 ]; then
    echo "Killing hanging curl processes..."
    pkill -f "curl.*localhost:5000"
fi

# Force kill anything on port 5000
echo "Clearing port 5000..."
fuser -k 5000/tcp 2>/dev/null
sleep 1

# Verify clean shutdown
REMAINING=$(lsof -i :5000 2>/dev/null | grep -v COMMAND | wc -l)
if [ "$REMAINING" -eq 0 ]; then
    echo "✅ Server stopped successfully - port 5000 is free"
    exit 0
else
    echo "⚠️  Warning: Some processes still bound to port 5000"
    lsof -i :5000 2>/dev/null
    exit 1
fi
