@echo off
REM Ignition Automation Toolkit - Windows Launcher (Systemd Service)
REM This batch file starts the Ignition Toolkit systemd service in WSL2

echo ====================================
echo Ignition Automation Toolkit
echo Starting systemd service...
echo ====================================
echo.

REM Start the systemd service in WSL2
wsl -d Ubuntu -e bash -c "sudo systemctl start ignition-toolkit.service && echo 'Service started successfully!' && echo 'Access the web UI at: http://localhost:5000' && echo 'Press Ctrl+C to close this window (service will keep running)' && read -p ''"

REM If the above fails, try without distribution name
if errorlevel 1 (
    echo.
    echo Trying default WSL distribution...
    wsl bash -c "sudo systemctl start ignition-toolkit.service && echo 'Service started successfully!' && echo 'Access the web UI at: http://localhost:5000' && echo 'Press Ctrl+C to close this window (service will keep running)' && read -p ''"
)

pause
