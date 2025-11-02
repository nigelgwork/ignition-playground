#!/bin/bash
# Rebuild frontend with verification
# This ensures the build is clean and all file references are correct

set -e  # Exit on error

echo "🔨 Rebuilding frontend..."
cd frontend

# Clean and rebuild
npm run rebuild

echo ""
echo "✅ Frontend rebuild complete!"
echo ""
echo "📝 Next steps:"
echo "   The server will automatically serve the updated files."
echo "   If the server is running, the changes are live immediately."
echo ""
