# Start Ignition Automation Toolkit Server (PowerShell)
# Cross-platform wrapper around Python CLI

Write-Host "=== Starting Ignition Automation Toolkit Server ===" -ForegroundColor Cyan

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ and add to PATH" -ForegroundColor Yellow
    exit 1
}

# Check if package is installed
$checkInstall = python -c "import ignition_toolkit" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: ignition_toolkit not installed" -ForegroundColor Red
    Write-Host "Run: pip install -e ." -ForegroundColor Yellow
    exit 1
}

# Start server using Python CLI
Write-Host "Starting server..." -ForegroundColor Green
python -m ignition_toolkit.cli server start
