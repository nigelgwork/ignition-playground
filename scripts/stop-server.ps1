# Stop Ignition Automation Toolkit Server (PowerShell)
# Cross-platform wrapper around Python CLI

Write-Host "=== Stopping Ignition Automation Toolkit Server ===" -ForegroundColor Cyan

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    exit 1
}

# Stop server using Python CLI
python -m ignition_toolkit.cli server stop
