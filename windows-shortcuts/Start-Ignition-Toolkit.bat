@echo off
REM Ignition Automation Toolkit - Windows Launcher
REM This batch file starts the Ignition Toolkit server in WSL2

echo ====================================
echo Ignition Automation Toolkit
echo ====================================
echo.
echo Starting server in WSL2...
echo.

REM Start the server in WSL2
wsl -d Ubuntu -e bash -c "cd /git/ignition-playground && ignition-toolkit server start"

REM If the above fails, try without distribution name
if errorlevel 1 (
    echo.
    echo Trying default WSL distribution...
    wsl bash -c "cd /git/ignition-playground && ignition-toolkit server start"
)

pause
