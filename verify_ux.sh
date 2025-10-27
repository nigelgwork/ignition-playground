#!/bin/bash
# UX Verification Script
# Run this before asking user to test

set -e

echo "=================================="
echo "🔍 UX Verification Checklist"
echo "=================================="
echo ""

# 1. Check working directory
echo "✓ Step 1: Checking working directory..."
if [ "$PWD" != "/git/ignition-playground" ]; then
    echo "  ❌ Wrong directory: $PWD"
    cd /git/ignition-playground
    echo "  ✓ Changed to /git/ignition-playground"
fi
echo ""

# 2. Kill all old servers
echo "✓ Step 2: Killing old servers..."
pkill -f "uvicorn ignition_toolkit" 2>/dev/null || true
pkill -f "vite.*dev" 2>/dev/null || true
sleep 2
echo "  ✓ Old servers killed"
echo ""

# 3. Check frontend dist exists and has latest build
echo "✓ Step 3: Checking frontend build..."
if [ ! -d "frontend/dist" ]; then
    echo "  ❌ frontend/dist not found - building..."
    cd frontend && npm run build && cd ..
fi

DIST_FILES=$(find frontend/dist -name "*.js" -newer frontend/package.json | wc -l)
if [ "$DIST_FILES" -eq "0" ]; then
    echo "  ⚠️  Dist files older than package.json - rebuilding..."
    cd frontend && npm run build && cd ..
else
    echo "  ✓ Frontend dist is up to date"
fi
echo ""

# 4. Get current version
echo "✓ Step 4: Checking version number..."
VERSION=$(grep '"version"' frontend/package.json | head -1 | awk -F'"' '{print $4}')
echo "  📦 Current version: $VERSION"
echo ""

# 5. Start backend on port 5000
echo "✓ Step 5: Starting backend on port 5000..."
export PLAYWRIGHT_BROWSERS_PATH=/git/ignition-playground/data/.playwright-browsers
./venv/bin/uvicorn ignition_toolkit.api.app:app --reload --port 5000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "  ✓ Backend started (PID: $BACKEND_PID)"
echo ""

# 6. Wait for backend to be ready
echo "✓ Step 6: Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "  ✓ Backend is responding"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "  ❌ Backend failed to start after 30 seconds"
        echo "  Last 20 lines of log:"
        tail -20 /tmp/backend.log
        exit 1
    fi
    sleep 1
done
echo ""

# 7. Test API health
echo "✓ Step 7: Testing API health..."
HEALTH=$(curl -s http://localhost:5000/health)
echo "  Response: $HEALTH"
if echo "$HEALTH" | grep -q "healthy"; then
    echo "  ✓ Health check passed"
else
    echo "  ❌ Health check failed"
    exit 1
fi
echo ""

# 8. Test that frontend is served
echo "✓ Step 8: Testing frontend is served..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/)
if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ Frontend is being served (HTTP $HTTP_CODE)"
else
    echo "  ❌ Frontend not served correctly (HTTP $HTTP_CODE)"
    exit 1
fi
echo ""

# 9. Check for version in served HTML
echo "✓ Step 9: Verifying version in served files..."
SERVED_HTML=$(curl -s http://localhost:5000/)
if echo "$SERVED_HTML" | grep -q "index.*\.js"; then
    echo "  ✓ JavaScript bundle found in HTML"
else
    echo "  ⚠️  No JavaScript bundle in HTML (might be loading issue)"
fi
echo ""

# 10. List active processes
echo "✓ Step 10: Active processes..."
echo "  Uvicorn processes:"
ps aux | grep uvicorn | grep -v grep | awk '{print "    PID " $2 ": " $11 " " $12 " " $13 " " $14}'
echo ""

# Summary
echo "=================================="
echo "✅ UX Verification Complete!"
echo "=================================="
echo ""
echo "📍 Access the UX at: http://localhost:5000"
echo "📦 Version: $VERSION"
echo "🔧 Backend PID: $BACKEND_PID"
echo "📝 Backend logs: tail -f /tmp/backend.log"
echo ""
echo "🎯 IMPORTANT REMINDERS:"
echo "   1. If browser shows old version, hard refresh (Ctrl+Shift+R or Cmd+Shift+R)"
echo "   2. Check browser console for errors (F12)"
echo "   3. Verify version number in UI footer matches: $VERSION"
echo ""
