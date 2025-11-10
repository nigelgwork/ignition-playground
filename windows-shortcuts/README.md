# Windows Desktop Shortcuts for Ignition Toolkit

This folder contains Windows launcher scripts for the Ignition Automation Toolkit running in WSL2.

## Available Scripts

### Option 1: Direct Server Start (Foreground)
- **`Start-Ignition-Toolkit.bat`** - Starts the server directly (keeps window open)
- **`Start-Ignition-Toolkit.ps1`** - PowerShell version (same functionality)

**Use this when:** You want to see real-time server logs and manually stop the server with Ctrl+C.

### Option 2: Systemd Service (Background)
- **`Start-Ignition-Toolkit-Systemd.bat`** - Starts the systemd service (runs in background)
- **`Stop-Ignition-Toolkit-Systemd.bat`** - Stops the systemd service

**Use this when:** You want the server to run in the background and keep running even after closing the terminal.

### Option 3: Open Web UI
- **`Open-Ignition-Toolkit-Browser.bat`** - Opens http://localhost:5000 in your default browser

## How to Create Desktop Shortcuts

### Method 1: Right-click drag (easiest)
1. Open Windows File Explorer
2. Navigate to the WSL path: `\\wsl$\Ubuntu\git\ignition-playground\windows-shortcuts`
3. Right-click and drag the desired `.bat` file to your Desktop
4. Select "Create shortcuts here"

### Method 2: Manual shortcut creation
1. Right-click on your Desktop
2. Select **New > Shortcut**
3. For the location, enter one of these paths:
   - For direct start: `\\wsl$\Ubuntu\git\ignition-playground\windows-shortcuts\Start-Ignition-Toolkit.bat`
   - For systemd service: `\\wsl$\Ubuntu\git\ignition-playground\windows-shortcuts\Start-Ignition-Toolkit-Systemd.bat`
   - For browser: `\\wsl$\Ubuntu\git\ignition-playground\windows-shortcuts\Open-Ignition-Toolkit-Browser.bat`
4. Click **Next**
5. Give it a name like "Ignition Toolkit" or "Start Ignition Toolkit"
6. Click **Finish**

### Method 3: Copy batch file directly (simplest)
1. Copy any `.bat` file from this folder to your Desktop
2. Double-click to run

## Customizing the Shortcut Icon (Optional)

1. Right-click the shortcut on your Desktop
2. Select **Properties**
3. Click **Change Icon**
4. Browse to an icon file (.ico) or select from Windows system icons
5. Click **OK**

## Troubleshooting

### "WSL distribution 'Ubuntu' not found"
If you get this error, your WSL distribution might have a different name. Edit the `.bat` file and change:
```batch
wsl -d Ubuntu -e bash -c "..."
```
to just:
```batch
wsl bash -c "..."
```

To find your WSL distribution name:
```cmd
wsl --list
```

### "sudo: no tty present and no askpass program specified"
The systemd scripts require sudo access. You may need to configure passwordless sudo for the systemd service:

```bash
# In WSL terminal
sudo visudo
# Add this line (replace 'root' with your username if different):
root ALL=(ALL) NOPASSWD: /bin/systemctl start ignition-toolkit.service
root ALL=(ALL) NOPASSWD: /bin/systemctl stop ignition-toolkit.service
root ALL=(ALL) NOPASSWD: /bin/systemctl restart ignition-toolkit.service
```

### Port 5000 already in use
If the server won't start because port 5000 is in use:
```bash
# In WSL terminal
sudo systemctl stop ignition-toolkit.service
# Or manually kill processes
pkill -f "ignition-toolkit"
```

## Recommended Setup

For the best experience:

1. **Create 3 desktop shortcuts:**
   - `Start Ignition Toolkit` → `Start-Ignition-Toolkit-Systemd.bat`
   - `Stop Ignition Toolkit` → `Stop-Ignition-Toolkit-Systemd.bat`
   - `Open Ignition Toolkit` → `Open-Ignition-Toolkit-Browser.bat`

2. **Startup workflow:**
   1. Double-click "Start Ignition Toolkit"
   2. Wait a few seconds for the service to start
   3. Double-click "Open Ignition Toolkit" to access the web UI

3. **Shutdown workflow:**
   1. Double-click "Stop Ignition Toolkit"

## Alternative: Auto-start on WSL boot

If you want the server to start automatically when WSL starts, the systemd service is already configured to do this. Just ensure WSL starts on Windows boot:

1. Open Windows Task Scheduler
2. Create a new task that runs at login:
   - Program: `wsl`
   - Arguments: `-d Ubuntu -e sudo systemctl start ignition-toolkit.service`

## Server Access

Once started, access the server at:
- **Web UI:** http://localhost:5000
- **API Docs:** http://localhost:5000/docs
- **Health Check:** http://localhost:5000/api/health

---

**Last Updated:** 2025-11-10
**Version:** 4.1.1
