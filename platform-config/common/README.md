# Common Platform Configuration

This directory contains shared dependencies and configuration for all platforms (Linux, Windows).

## Files

### requirements.txt
Python packages required on all platforms:

**Web Framework:**
- `fastapi` - Modern async web framework
- `uvicorn` - ASGI server for FastAPI

**HTTP & Networking:**
- `httpx` - Async HTTP client for Gateway API
- `websockets` - WebSocket protocol support

**Data & Validation:**
- `pydantic` - Data validation and settings management
- `pydantic-settings` - Environment-based configuration
- `pyyaml` - YAML parsing for playbooks
- `python-dotenv` - .env file support

**Database:**
- `sqlalchemy` - ORM for execution history
- `aiosqlite` - Async SQLite driver

**Security:**
- `cryptography` - Credential encryption (Fernet)

**Browser Automation:**
- `playwright` - Headless browser for Perspective tests

**Utilities:**
- `click` - CLI framework
- `rich` - Rich console output
- `apscheduler` - Background task scheduling
- `psutil` - System and process utilities
- `python-multipart` - File upload support

**AI Integration:**
- `anthropic` - Anthropic API client for AI features

## Usage

These dependencies are installed first during the portable build process, followed by platform-specific dependencies from `platform-config/linux/` or `platform-config/windows/`.

## Version Pinning

All dependencies use minimum version constraints (`>=`) to allow updates while ensuring compatibility. The build process will install the latest compatible versions at build time.

## Installation Order

1. Common dependencies (this file)
2. Platform-specific Python dependencies
3. Platform-specific system dependencies (manual installation)

## Testing

To verify all common dependencies are installed:
```bash
pip freeze | grep -f platform-config/common/requirements.txt
```
