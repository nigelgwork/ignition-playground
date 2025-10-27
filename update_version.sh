#!/bin/bash
# Update Version and Rebuild - Ignition Automation Toolkit
# Controlled version update procedure with full rebuild

# Check if version argument provided
if [ -z "$1" ]; then
    echo "❌ ERROR: Version number required"
    echo "Usage: ./update_version.sh X.Y.Z"
    echo "Example: ./update_version.sh 2.0.2"
    exit 1
fi

NEW_VERSION="$1"
echo "=== Updating to Version $NEW_VERSION ==="

# Step 1: Stop server
echo ""
echo "Step 1/6: Stopping server..."
./stop_server.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to stop server"
    exit 1
fi

# Step 2: Update VERSION file
echo ""
echo "Step 2/6: Updating VERSION file..."
echo "$NEW_VERSION" > VERSION
echo "✅ VERSION file updated"

# Step 3: Update __init__.py
echo ""
echo "Step 3/6: Updating ignition_toolkit/__init__.py..."
TODAY=$(date +%Y-%m-%d)
sed -i "s/^__version__ = .*/__version__ = \"$NEW_VERSION\"  # Updated: $TODAY/" ignition_toolkit/__init__.py
sed -i "s/^__build_date__ = .*/__build_date__ = \"$TODAY\"/" ignition_toolkit/__init__.py
echo "✅ __init__.py updated"

# Step 4: Update frontend/package.json
echo ""
echo "Step 4/6: Updating frontend/package.json..."
cd frontend
sed -i "s/\"version\": \".*\"/\"version\": \"$NEW_VERSION\"/" package.json
echo "✅ package.json updated"

# Step 5: Rebuild frontend
echo ""
echo "Step 5/6: Rebuilding frontend (npm run build)..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed"
    cd ..
    exit 1
fi
cd ..
echo "✅ Frontend rebuilt successfully"

# Step 6: Start server and verify
echo ""
echo "Step 6/6: Starting server..."
./start_server.sh &
SERVER_PID=$!
sleep 5

# Wait for server to be ready (max 30 seconds)
echo "Waiting for server to be ready..."
for i in {1..30}; do
    HEALTH=$(curl -s http://localhost:5000/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ Server is responding"

        # Verify version
        VERSION_CHECK=$(echo "$HEALTH" | grep -o "\"version\":\"[^\"]*\"" | cut -d'"' -f4)
        if [ "$VERSION_CHECK" = "$NEW_VERSION" ]; then
            echo "✅ Version verified: $NEW_VERSION"
            echo ""
            echo "=========================================="
            echo "✅ UPDATE COMPLETE - Version $NEW_VERSION"
            echo "=========================================="
            echo "Server running at: http://localhost:5000"
            echo "Frontend: http://localhost:5000/"
            echo ""
            echo "To stop server: ./stop_server.sh"
            exit 0
        else
            echo "⚠️  Version mismatch: Expected $NEW_VERSION, got $VERSION_CHECK"
        fi
        break
    fi
    sleep 1
done

echo "❌ Server failed to start or respond within 30 seconds"
kill $SERVER_PID 2>/dev/null
exit 1
