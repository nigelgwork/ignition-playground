# Ignition Automation Toolkit - Windows PowerShell Launcher
# This PowerShell script starts the Ignition Toolkit server in WSL2

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Ignition Automation Toolkit" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting server in WSL2..." -ForegroundColor Yellow
Write-Host ""

# Start the server in WSL2
try {
    wsl -d Ubuntu -e bash -c "cd /git/ignition-playground && ignition-toolkit server start"
}
catch {
    Write-Host "Trying default WSL distribution..." -ForegroundColor Yellow
    wsl bash -c "cd /git/ignition-playground && ignition-toolkit server start"
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
