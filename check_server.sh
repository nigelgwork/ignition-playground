#!/bin/bash
# Quick server health check script
# Returns 0 if healthy, 1 if not

echo "=== Ignition Toolkit Server Health Check ==="

# Check if process is running
SERVER_PID=$(pgrep -f "uvicorn.*ignition_toolkit" | head -1)

if [ -z "$SERVER_PID" ]; then
    echo "❌ Server is NOT running"
    echo ""
    echo "To start the server:"
    echo "  ./start_server.sh"
    exit 1
fi

echo "✅ Server process found (PID: $SERVER_PID)"

# Check if port 5000 is listening
PORT_LISTEN=$(lsof -i :5000 -t 2>/dev/null | head -1)
if [ -z "$PORT_LISTEN" ]; then
    echo "❌ Port 5000 is not listening"
    echo "Server may be starting up or crashed"
    exit 1
fi

echo "✅ Port 5000 is listening"

# Check if server responds to HTTP
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/ 2>/dev/null)

if [ "$HTTP_RESPONSE" = "200" ]; then
    echo "✅ Server is responding to HTTP requests (HTTP $HTTP_RESPONSE)"
    echo ""
    echo "🎉 Server is HEALTHY"
    echo "   URL: http://localhost:5000"
    echo "   PID: $SERVER_PID"
    exit 0
else
    echo "❌ Server returned HTTP $HTTP_RESPONSE"
    echo "Server may be unhealthy"
    exit 1
fi
