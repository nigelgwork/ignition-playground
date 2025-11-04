# Systemd Service Configuration

The Ignition Automation Toolkit is configured to run as a systemd service, ensuring it starts automatically on boot and restarts if it crashes.

## Service Status

Check if the service is running:
```bash
systemctl status ignition-toolkit.service
```

## Service Controls

**Start the service:**
```bash
sudo systemctl start ignition-toolkit.service
```

**Stop the service:**
```bash
sudo systemctl stop ignition-toolkit.service
```

**Restart the service:**
```bash
sudo systemctl restart ignition-toolkit.service
```

**Enable service to start on boot** (already enabled):
```bash
sudo systemctl enable ignition-toolkit.service
```

**Disable service from starting on boot:**
```bash
sudo systemctl disable ignition-toolkit.service
```

## View Logs

**Real-time logs:**
```bash
journalctl -u ignition-toolkit.service -f
```

**Last 100 lines:**
```bash
journalctl -u ignition-toolkit.service -n 100 --no-pager
```

**Logs since last boot:**
```bash
journalctl -u ignition-toolkit.service -b --no-pager
```

**Logs from specific time:**
```bash
journalctl -u ignition-toolkit.service --since "1 hour ago" --no-pager
```

## Service Configuration

**Location:** `/etc/systemd/system/ignition-toolkit.service`

**Key Features:**
- **Auto-start on boot** - Service starts when the system boots
- **Auto-restart on crash** - If the service crashes, it automatically restarts after 10 seconds
- **Graceful shutdown** - Properly handles SIGTERM signals
- **Journal logging** - All logs go to systemd journal (viewable with `journalctl`)
- **Network dependency** - Waits for network to be online before starting

## Troubleshooting

**Service won't start:**
```bash
# Check for errors in the service configuration
sudo systemctl status ignition-toolkit.service

# View detailed logs
journalctl -u ignition-toolkit.service -n 50 --no-pager
```

**Port 5000 already in use:**
```bash
# Find what's using port 5000
sudo lsof -i :5000

# Kill any manual instances
pkill -f "ignition-toolkit serve"

# Restart the service
sudo systemctl restart ignition-toolkit.service
```

**After updating code:**
```bash
# Restart the service to load new changes
sudo systemctl restart ignition-toolkit.service
```

**After modifying service file:**
```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Restart the service
sudo systemctl restart ignition-toolkit.service
```

## Verifying Auto-Start on Boot

**Check if enabled:**
```bash
systemctl is-enabled ignition-toolkit.service
# Should output: enabled
```

**Test reboot behavior** (optional):
```bash
# Reboot the system
sudo reboot

# After reboot, verify service is running
systemctl status ignition-toolkit.service
```

## Server Access

Once the service is running, the server is accessible at:
- **URL:** http://localhost:5000
- **Health Check:** http://localhost:5000/health
- **API Docs:** http://localhost:5000/docs

## Important Notes

1. **Manual instances conflict** - If you run `ignition-toolkit serve` manually, it will conflict with the systemd service (port 5000 already in use). Always use the systemd service instead.

2. **Viewing logs** - Don't use `tail -f` on log files. Use `journalctl -u ignition-toolkit.service -f` to view real-time logs.

3. **Code updates** - After pulling new code from git, restart the service: `sudo systemctl restart ignition-toolkit.service`

4. **Environment variables** - If you need to set environment variables, edit the service file and add them under `[Service]` section:
   ```ini
   Environment="VARIABLE_NAME=value"
   ```

## Current Configuration

```ini
[Unit]
Description=Ignition Automation Toolkit Server
Documentation=https://github.com/nigelgwork/ignition-playground
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/git/ignition-playground
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/ignition-toolkit serve
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
NoNewPrivileges=true
PrivateTmp=true
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

---

**Last Updated:** 2025-11-04
**Version:** 4.1.1
