# Check Ignition Automation Toolkit Server Status (PowerShell)
# Cross-platform wrapper around Python CLI

Write-Host "=== Ignition Toolkit Server Health Check ===" -ForegroundColor Cyan

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    exit 1
}

# Check server status using Python CLI
python -m ignition_toolkit.cli server status
