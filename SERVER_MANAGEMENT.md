# Server Management Guide

## Quick Commands

```bash
# Check if server is running and healthy
./check_server.sh

# Start the server
./start_server.sh

# Stop the server
./stop_server.sh
```

## Common Issues

### "Server already running" error
The `start_server.sh` script prevents starting multiple instances. If you see this error:
```bash
./stop_server.sh
./start_server.sh
```

### Server appears stuck or not responding
1. Check server health:
   ```bash
   ./check_server.sh
   ```

2. If unhealthy, restart:
   ```bash
   ./stop_server.sh
   ./start_server.sh
   ```

3. If still having issues, force kill everything:
   ```bash
   pkill -9 -f "uvicorn.*ignition"
   lsof -ti:5000 | xargs kill -9
   ./start_server.sh
   ```

### Multiple background processes
If you accidentally started multiple servers in background:
```bash
# Kill all ignition uvicorn processes
pkill -9 -f "uvicorn.*ignition"

# Verify they're gone
pgrep -af uvicorn | grep ignition

# Start fresh
./start_server.sh
```

## Server URLs

- **Web UI**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs
- **Health Check**: http://localhost:5000/api/health

## Auto-Reload Behavior

The server runs with `--reload` flag, which means:
- ✅ Code changes automatically reload the server
- ⚠️ Server briefly unavailable during reload (1-2 seconds)
- ⚠️ Multiple rapid file changes can cause reload loops

**Tip**: If making many changes, consider:
1. Stop the server
2. Make all your changes
3. Start the server once when done

## Troubleshooting

### Port 5000 already in use
```bash
# Find what's using port 5000
lsof -i :5000

# Kill the process
lsof -ti:5000 | xargs kill -9
```

### Cannot find uvicorn
Make sure you're in the project directory and the virtualenv is set up:
```bash
cd /git/ignition-playground
ls -la venv/bin/uvicorn  # Should exist
```

### Permission denied
Make scripts executable:
```bash
chmod +x start_server.sh stop_server.sh check_server.sh
```

## Server Logs

To view server logs in real-time:
```bash
# If running in background via start_server.sh
tail -f /path/to/logs  # Update with actual log path

# Or restart in foreground to see logs directly
./stop_server.sh
./venv/bin/uvicorn ignition_toolkit.api.app:app --host 0.0.0.0 --port 5000 --reload
```
