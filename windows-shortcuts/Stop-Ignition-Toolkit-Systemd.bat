@echo off
REM Ignition Automation Toolkit - Windows Launcher (Stop Systemd Service)
REM This batch file stops the Ignition Toolkit systemd service in WSL2

echo ====================================
echo Ignition Automation Toolkit
echo Stopping systemd service...
echo ====================================
echo.

REM Stop the systemd service in WSL2
wsl -d Ubuntu -e bash -c "sudo systemctl stop ignition-toolkit.service && echo 'Service stopped successfully!'"

REM If the above fails, try without distribution name
if errorlevel 1 (
    echo.
    echo Trying default WSL distribution...
    wsl bash -c "sudo systemctl stop ignition-toolkit.service && echo 'Service stopped successfully!'"
)

pause
