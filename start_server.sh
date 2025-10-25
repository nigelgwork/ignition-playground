#!/bin/bash
# Startup script for Ignition Automation Toolkit
#
# Sets consistent environment variables to avoid HOME-dependent paths

# Set consistent Playwright browser cache location
export PLAYWRIGHT_BROWSERS_PATH=/git/ignition-playground/data/.playwright-browsers

# Optional: Set toolkit data directory override
# export IGNITION_TOOLKIT_DATA=/custom/path/.ignition-toolkit

# Start the server
exec ./venv/bin/uvicorn ignition_toolkit.api.app:app --host 0.0.0.0 --port 5000 --reload
