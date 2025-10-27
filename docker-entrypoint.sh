#!/bin/bash
# ========================================
# Docker Entrypoint Script
# ========================================
# Runs initialization tasks before starting the application

set -e  # Exit on error

echo "========================================="
echo "Ignition Toolkit - Starting..."
echo "========================================="

# Display environment info
echo "Environment: ${ENVIRONMENT:-production}"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"

# Ensure required directories exist
echo "Creating required directories..."
mkdir -p /app/data
mkdir -p /app/data/screenshots
mkdir -p /home/appuser/.ignition-toolkit

# Set proper permissions
echo "Setting permissions..."
chown -R appuser:appuser /app/data /home/appuser/.ignition-toolkit 2>/dev/null || true

# Initialize database if it doesn't exist
if [ ! -f "/app/data/toolkit.db" ]; then
    echo "Initializing database..."
    python -c "from ignition_toolkit.storage import get_database; get_database()"
fi

# Run database migrations (if any)
# Uncomment when Alembic is added in Phase 5
# echo "Running database migrations..."
# alembic upgrade head

# Initialize credential vault if it doesn't exist
if [ ! -f "/home/appuser/.ignition-toolkit/credentials.enc" ]; then
    echo "Initializing credential vault..."
    python -c "from ignition_toolkit.credentials import get_credential_vault; get_credential_vault()"
fi

# Validate environment
echo "Validating environment..."
python -c "
from ignition_toolkit.core.paths import validate_paths
import json
status = validate_paths()
print(json.dumps(status, indent=2))
"

echo "========================================="
echo "Initialization complete!"
echo "Starting application..."
echo "========================================="

# Execute the command passed to docker run
exec "$@"
