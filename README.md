# Ignition Automation Toolkit

> Lightweight, transferable automation platform for Ignition SCADA Gateway operations with plugin-based playbook library

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.0.0-blue.svg)](VERSION)

## 🎯 Overview

A modern automation toolkit for Ignition SCADA with **plugin architecture** and playbook marketplace (native Python installation, Docker optional):

- **🔌 Plugin Architecture**: Browse, install, and update playbooks from central repository (NEW in v5.0)
- **📦 Playbook Library**: 24+ verified playbooks for Gateway, Perspective, and Designer automation
- **🔄 Automatic Updates**: Check for playbook updates with one-click installation
- **Gateway Automation**: REST API client for modules, projects, system operations
- **Playbook System**: YAML-based reusable workflows with 35+ step types
- **Real-Time Control**: Pause, resume, skip steps during execution via WebSocket
- **Browser Automation**: Playwright integration for Perspective and web-based operations
- **Designer Integration**: Linux Designer automation with keyboard/mouse control
- **Secure Credentials**: Fernet-encrypted local storage, never committed to git
- **Import/Export**: Share playbooks as JSON with colleagues
- **Web UI**: Modern dark-theme interface with Warp terminal colors

## ⚡ What's New in v5.0

**Major Changes:**
- **🔌 Plugin Architecture**: Playbooks are now installable plugins from a central repository
- **📦 Playbook Library UI**: Browse and install 24+ verified playbooks with search and filtering
- **🔄 Update System**: Automatic checking for playbook updates with visual notifications
- **🔐 Enhanced Security**: SHA256 checksum verification for all playbook downloads
- **🏗️ Restructured Directories**: 6 base playbooks built-in, others installable on-demand
- **❌ AI Features Removed**: Temporarily removed (will return as optional plugin in future release)

**Migration Required:** See [MIGRATION_V5.md](docs/MIGRATION_V5.md) for upgrade guide

## 📚 Documentation Quick Links

- **[Playbook Library Guide](docs/PLAYBOOK_LIBRARY.md)** - Browse, install, and update playbooks
- **[Migration Guide (v5.0)](docs/MIGRATION_V5.md)** - Upgrade from v4.x to v5.0
- **[Getting Started](docs/getting_started.md)** - First-time setup and tutorials
- **[Playbook Syntax Reference](docs/playbook_syntax.md)** - Writing custom playbooks
- **[Architecture Documentation](ARCHITECTURE.md)** - Design decisions and ADRs

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip
- Node.js 18+ (for frontend development)
- **Windows**: PowerShell 5.1+
- **Linux/macOS**: bash or zsh

### Installation

#### Option 1: Using Python Task Runner (Cross-Platform, Recommended)

Works on Windows, Linux, and macOS:

```bash
# Clone repository
git clone git@github.com:nigelgwork/ignition-playground.git
cd ignition-playground

# Install and initialize
python tasks.py install        # Install in development mode
python tasks.py install-dev    # Install with dev dependencies
python tasks.py init           # Initialize credential vault

# Start development server
python tasks.py dev

# Other useful commands
python tasks.py test           # Run tests
python tasks.py lint           # Run linters
python tasks.py build          # Build frontend
python tasks.py help           # Show all commands
```

#### Option 2: Using Makefile (Linux/macOS only)

```bash
# Clone repository
git clone git@github.com:nigelgwork/ignition-playground.git
cd ignition-playground

# Install and initialize
make install          # Install in development mode
make install-dev      # Install with dev dependencies
make init             # Initialize credential vault

# Start development server
make dev
```

#### Option 3: Manual Setup (All Platforms)

```bash
# Clone repository
git clone git@github.com:nigelgwork/ignition-playground.git
cd ignition-playground

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install package
pip install -e .

# Install Playwright browsers
playwright install chromium

# Initialize credential vault
ignition-toolkit init

# Start server
ignition-toolkit server start
```

#### Option 4: PowerShell Scripts (Windows Convenience)

```powershell
# Clone repository
git clone git@github.com:nigelgwork/ignition-playground.git
cd ignition-playground

# Set up using Python tasks
python tasks.py install
python tasks.py install-dev
python tasks.py init

# Use PowerShell convenience scripts
.\scripts\start-server.ps1    # Start server
.\scripts\check-server.ps1    # Check status
.\scripts\stop-server.ps1     # Stop server
```

Access the web UI at **http://localhost:5000**

#### Option 3: Docker Deployment (Optional)

> **Note**: Native Python installation (Option 1 or 2) is the recommended approach for simpler setup and better performance. Docker is provided as an optional deployment method for containerized environments.

```bash
# Clone and build
git clone git@github.com:nigelgwork/ignition-playground.git
cd ignition-playground

# Production mode (SQLite)
docker-compose up -d

# Development mode (hot reload)
docker-compose --profile dev up -d

# Production with PostgreSQL
docker-compose --profile postgres up -d
```

Access the web UI at http://localhost:5000

### Your First Playbook

```bash
# Add Gateway credentials
ignition-toolkit credential add gateway_admin
# Enter username and password when prompted

# Run example health check playbook
ignition-toolkit playbook run playbooks/examples/simple_health_check.yaml \
  --param gateway_url=http://localhost:8088 \
  --param gateway_credential=gateway_admin
```

### Health Monitoring

The toolkit includes Kubernetes-style health check endpoints for monitoring:

```bash
# Overall health status
curl http://localhost:5000/health

# Liveness probe (always returns 200 if running)
curl http://localhost:5000/health/live

# Readiness probe (200 if ready, 503 if not)
curl http://localhost:5000/health/ready

# Detailed component-level health
curl http://localhost:5000/health/detailed
```

**Example detailed health response:**
```json
{
  "overall": "healthy",
  "ready": true,
  "startup_time": "2025-10-24T08:38:10.751958",
  "components": {
    "database": {"status": "healthy", "message": "Database operational"},
    "vault": {"status": "healthy", "message": "Vault operational"},
    "playbooks": {"status": "healthy", "message": "Found 4 playbooks"},
    "frontend": {"status": "healthy", "message": "Dev mode - frontend served separately"}
  },
  "errors": [],
  "warnings": []
}
```

## 📚 Documentation

### Getting Started
- [Getting Started Guide](docs/getting_started.md) - Installation and first steps
- [Running Playbooks](docs/RUNNING_PLAYBOOKS.md) - Complete guide with examples
- [Playbook Syntax](docs/playbook_syntax.md) - YAML reference and step types
- [Playbook Best Practices](docs/PLAYBOOK_BEST_PRACTICES.md) - How to write good playbooks

### Reference
- [PACKAGES.md](PACKAGES.md) - Complete dependency tracking and versions
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture, design decisions (ADRs)
- [PROJECT_GOALS.md](PROJECT_GOALS.md) - Project vision, use cases, goals

### Development
- [Testing Guide](docs/TESTING_GUIDE.md) - Test suite and coverage
- [Versioning Guide](docs/VERSIONING_GUIDE.md) - Release management
- [CI/CD Setup](docs/CI_CD_SETUP.md) - Continuous integration configuration
- [ROADMAP.md](docs/ROADMAP.md) - Future features and priorities

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   Web UI (HTML/CSS/JS + Material)   │
│        http://localhost:8080         │
│      Warp Terminal Dark Theme        │
└──────────────┬──────────────────────┘
               │ WebSocket + REST API
               ▼
┌─────────────────────────────────────┐
│    FastAPI Backend                   │
│  • Playbook Engine (15+ step types) │
│  • Gateway Client (async httpx)     │
│  • Browser Automation (Playwright)  │
│  • Credential Vault (Fernet)        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  SQLite + Local File Storage         │
│  • Execution History                 │
│  • Encrypted Credentials             │
│    (~/.ignition-toolkit/)            │
│  • Playbook Library (YAML)           │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  External Ignition Gateway(s)        │
│        Your SCADA Systems            │
└─────────────────────────────────────┘
```

## 📁 Project Structure

```
ignition-playground/
├── ignition_toolkit/          # Main Python package
│   ├── gateway/               # Gateway REST API client (httpx)
│   ├── playbook/              # Playbook engine & step executor
│   ├── browser/               # Playwright browser automation
│   ├── credentials/           # Fernet encrypted credential vault
│   ├── api/                   # FastAPI server (modular architecture)
│   │   ├── app.py             # Main FastAPI app (190 lines, 92% reduced!)
│   │   └── routers/           # Modular API routers
│   │       ├── health.py      # Health check endpoints
│   │       ├── playbooks.py   # Playbook management (6 routes)
│   │       ├── executions.py  # Execution control (11 routes)
│   │       ├── credentials.py # Credential CRUD (4 routes)
│   │       ├── ai.py          # AI integration (8 routes)
│   │       ├── websockets.py  # WebSocket endpoints (2 WS + broadcast)
│   │       └── models.py      # Shared Pydantic models (7 models)
│   ├── storage/               # SQLite database models
│   ├── ai/                    # AI integration scaffolding
│   └── cli.py                 # Command-line interface
├── playbooks/                 # YAML playbook library
│   ├── gateway/               # Gateway automation workflows
│   ├── browser/               # Browser automation workflows
│   ├── ai/                    # AI-assisted workflows
│   └── examples/              # Example playbooks
├── frontend/                  # React 19 + TypeScript Web UI
│   ├── src/                   # React source code
│   │   ├── pages/             # Page components
│   │   ├── components/        # Reusable components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── store/             # Zustand state management
│   │   └── api/               # API client
│   └── dist/                  # Built frontend (served by FastAPI)
├── tests/                     # Test suite (46 tests)
├── docs/                      # Documentation
│   ├── design/                # Future feature designs
│   └── archive/               # Historical documentation
├── .claude/                   # Claude Code instructions
├── CHANGELOG.md               # Version history
├── VERSION                    # Current version (5.0.0)
└── pyproject.toml             # Package configuration
```

## 🔑 Key Features

### Playbook System

Define reusable automation workflows in YAML:

```yaml
name: "Ignition Module Upgrade"
version: "1.0"

parameters:
  - name: gateway_url
    type: string
  - name: gateway_password
    type: credential
  - name: module_file
    type: file

steps:
  - id: authenticate
    name: "Login to Gateway"
    type: gateway.login

  - id: upload
    name: "Upload Module"
    type: gateway.upload_module
    parameters:
      file: "{{ module_file }}"

  - id: restart
    name: "Restart Gateway"
    type: gateway.restart
    wait_for_ready: true
```

### Secure Credential Storage

Credentials encrypted with Fernet and stored locally:

```bash
# Add credential via CLI
ignition-toolkit credential add gateway_admin \
  --username admin \
  --password <your-password>

# Reference in playbooks
parameters:
  gateway_password: "{{ credential.gateway_admin }}"
```

### Import/Export Playbooks

Share workflows with your team:

```bash
# Export playbook to JSON
ignition-toolkit export playbooks/gateway/module_upgrade.yaml \
  --output module_upgrade.json

# Import on colleague's machine
ignition-toolkit import module_upgrade.json
```

### Real-Time Execution Control

- ⏸️ **Pause**: Stop after current step completes
- ⏭️ **Skip**: Skip current step and continue
- ▶️ **Resume**: Continue paused execution
- 🎥 **Live Browser**: Watch automation in real-time
- 📊 **WebSocket Logs**: Streaming execution updates

## 📦 Portability (New in v4.0)

The Ignition Automation Toolkit is designed to be **fully portable** - run it from any directory on any machine without hardcoded paths or environment assumptions.

### Key Portability Features

✅ **Dynamic Path Resolution**
- All paths calculated from package installation location
- No hardcoded absolute paths in code
- Works from any directory (`/git/project`, `/home/user/toolkit`, `C:\Projects\automation`)

✅ **Portable Archives**
- Package entire toolkit with playbooks and frontend
- Transfer between machines or teams
- Credentials remain local (never included in archives)

✅ **Environment Verification**
- Built-in verification command checks all dependencies
- Validates paths, permissions, and configurations
- Helpful error messages with fix suggestions

✅ **Configurable Security**
- Filesystem access restricted by default (data/ only)
- Optional additional paths via environment variables
- Rate limiting to prevent abuse

### Creating Portable Archives

Package the toolkit for transfer to another machine:

```bash
# Create portable archive (excludes venv, node_modules, credentials)
python scripts/create_portable.py

# Output: ignition-toolkit-portable-v5.0.0.tar.gz (~50MB)
# Includes: source code, playbooks, built frontend, documentation
```

**What's Included:**
- Complete source code
- All playbooks (gateway/, perspective/, designer/, examples/)
- Built React frontend (frontend/dist/)
- Documentation
- Configuration files

**What's Excluded (for security):**
- Virtual environments (venv/)
- Node modules (node_modules/)
- User credentials (~/.ignition-toolkit/)
- Execution history database
- Git repository (.git/)

### Using a Portable Archive

Extract and run on a new machine:

```bash
# Extract archive
tar -xzf ignition-toolkit-portable-v5.0.0.tar.gz
cd ignition-toolkit-v5.0.0

# Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
playwright install chromium

# Initialize (creates new credential vault)
ignition-toolkit init

# Verify installation
ignition-toolkit verify

# Start server
ignition-toolkit server start
```

### Environment Verification

Check that your environment is correctly configured:

```bash
# Verify all dependencies and paths
ignition-toolkit verify

# Example output:
# ✓ Python version: 3.10.12
# ✓ Package installation: /opt/ignition-toolkit
# ✓ Playbooks directory: /opt/ignition-toolkit/playbooks (42 playbooks)
# ✓ Frontend build: /opt/ignition-toolkit/frontend/dist
# ✓ Data directory: /opt/ignition-toolkit/data (writable)
# ✓ Playwright: Chromium installed
# ✓ Credential vault: /home/user/.ignition-toolkit/credentials.enc
# ✓ Database: /home/user/.ignition-toolkit/executions.db
#
# All checks passed! ✅
```

### Advanced Configuration

#### Custom Filesystem Access

By default, filesystem browsing is restricted to the `data/` directory for security. To allow access to additional directories (e.g., for module storage):

```bash
# Allow access to custom module directory
export FILESYSTEM_ALLOWED_PATHS="/opt/ignition-modules:/mnt/shared/modules"

# Paths are colon-separated (:)
# Both /opt/ignition-modules and /mnt/shared/modules will be accessible
```

#### Custom Ports

Run multiple instances on different ports:

```bash
# Set custom port via environment variable
export API_PORT=5001
ignition-toolkit server start

# Or specify in command (if supported)
ignition-toolkit server start --port 5001
```

#### CORS Configuration

Allow connections from additional origins:

```bash
# Add custom origins (comma-separated)
export ALLOWED_ORIGINS="http://localhost:5000,http://localhost:5001,http://192.168.1.100:5000"
```

### Security in Portable Deployments

**Rate Limiting (New in v4.0):**
- Critical endpoints: 10 requests/minute (credentials, execution start)
- Normal endpoints: 60 requests/minute (list, get operations)
- High-frequency endpoints: 120 requests/minute (status, health checks)

**Filesystem Protection:**
- Browsing restricted to `data/` directory by default
- Prevents access to credentials, SSH keys, system files
- Path traversal attacks blocked by PathValidator

**Input Validation:**
- All user inputs validated and sanitized
- XSS protection on metadata fields
- YAML injection prevention

**Credentials:**
- Always stored in user home directory (`~/.ignition-toolkit/`)
- Never included in portable archives
- Fernet encryption at rest
- Each machine maintains its own credential vault

### Playbook Portability

**Origin Tracking (New in v4.0):**
Playbooks are automatically tagged with their origin:

- **Built-in** 🏭 - Shipped with toolkit (gateway/, perspective/, designer/, examples/)
- **Custom** 👤 - User-created playbooks
- **Duplicated** 📋 - Copied from existing playbooks

**Duplication:**
```bash
# Duplicate a playbook via UI (one-click)
# Or via CLI:
curl -X POST http://localhost:5000/api/playbooks/gateway/module_upgrade.yaml/duplicate
```

Duplicated playbooks are marked with their source for easy tracking.

### Path Resolution Details

The toolkit uses dynamic path resolution to work from any directory:

```python
# Package root automatically detected from installation
/opt/ignition-toolkit/               # Wherever you install
├── playbooks/                       # Always found relative to package
├── frontend/dist/                   # Built frontend location
├── data/                            # Runtime data
└── ignition_toolkit/                # Python package
```

**User data is always stored in home directory:**
```bash
~/.ignition-toolkit/                 # Platform-independent
├── credentials.enc                  # Fernet-encrypted credentials
└── executions.db                    # SQLite execution history
```

This design ensures:
- No hardcoded paths in code
- Works on Windows, Linux, macOS
- Multiple installations can coexist
- Each user has separate credentials

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Test Gateway client
pytest tests/test_gateway_client.py -v

# Test playbook execution
pytest tests/test_playbook_engine.py -v

# Or use Makefile
make test             # Run all tests
make test-cov         # Run with coverage report
make test-fast        # Skip slow integration tests
```

## 🛠️ Makefile Commands

The project includes a comprehensive Makefile with 52 commands. Run `make help` to see all available commands.

### Development Commands
```bash
make install          # Install project in development mode
make install-dev      # Install with development dependencies
make dev              # Start development server (hot reload)
make dev-backend      # Start backend only
make dev-frontend     # Start frontend dev server only
make stop             # Stop all running servers
make restart          # Restart development server
make status           # Check server status
```

### Testing & Quality
```bash
make test             # Run all tests
make test-unit        # Run unit tests only
make test-integration # Run integration tests only
make test-cov         # Run tests with coverage report
make test-fast        # Run fast tests (skip slow ones)
make lint             # Run all linters (ruff, mypy)
make format           # Format code with ruff
make complexity       # Check code complexity
make security         # Run security checks with bandit
```

### Docker Commands
```bash
make docker-build     # Build Docker image
make docker-up        # Start services (production)
make docker-up-dev    # Start services (dev profile)
make docker-up-postgres # Start with PostgreSQL
make docker-down      # Stop Docker services
make docker-logs      # Show Docker logs
make docker-shell     # Open shell in backend container
make docker-rebuild   # Rebuild and restart
```

### Database & Credentials
```bash
make db-reset         # Reset database
make db-backup        # Backup database
make db-shell         # Open SQLite shell
make cred-list        # List all credentials
make cred-add         # Add new credential (interactive)
make cred-backup      # Backup credential vault
```

### Playbook Management
```bash
make playbook-list    # List all playbooks
make playbook-validate # Validate all YAML playbooks
```

### Build & Release
```bash
make build            # Build frontend for production
make build-all        # Build frontend and Docker image
make version          # Show current version
make bump-patch       # Bump patch version (x.x.X)
make bump-minor       # Bump minor version (x.X.0)
make bump-major       # Bump major version (X.0.0)
```

### Utilities
```bash
make clean            # Clean build artifacts
make clean-all        # Deep clean (including Docker volumes)
make info             # Show environment information
make deps-check       # Check for outdated dependencies
make deps-upgrade     # Upgrade all dependencies
make logs             # Show application logs
make verify-ux        # Verify UX functionality
```

### Common Workflows
```bash
# Fresh install
make install && make install-dev && make init

# Development cycle
make dev              # Start server
make test-fast        # Run tests while developing
make lint && make format  # Before committing

# Production deployment
make docker-build && make docker-up

# Upgrade dependencies
make deps-check && make deps-upgrade
```

## 🔒 Security

- **Credentials**: Encrypted with Fernet, stored in `~/.ignition-toolkit/credentials.db`
- **Encryption Key**: Generated on first run, stored locally
- **Never in Git**: Credential vault excluded via `.gitignore`
- **Playbook Export**: Credentials replaced with references, never exported

## 🤝 Contributing

Contributions welcome! This project uses:

- **Code Style**: Black formatter, type hints everywhere
- **Testing**: pytest with >70% coverage target
- **Documentation**: Google-style docstrings

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 📊 Project Status

**Current Version:** 5.0.0 (November 19, 2025)
**Status:** ✅ Production Ready
**Test Coverage:** 46+ automated tests across all components

### Completed Features (8/8 Phases)

✅ Phase 1: Foundation (packaging, credentials, database, CLI)
✅ Phase 2: Gateway Client (async REST API, authentication)
✅ Phase 3: Playbook Engine (YAML parser, execution, state management)
✅ Phase 4: Import/Export (JSON sharing with credential stripping)
✅ Phase 5: API & Frontend (FastAPI, WebSocket, dark-theme UI)
✅ Phase 6: Browser Automation (Playwright integration)
✅ Phase 7: AI Scaffolding (integration hooks, placeholder steps)
✅ Phase 8: Testing & Documentation (comprehensive test suite)

### Available Playbooks

- **Gateway Automation:** Module upgrade, backup & restart, trial reset, health checks
- **Browser Automation:** Web login tests, screenshot audits, Ignition web testing
- **AI-Assisted:** AI test generation (requires Anthropic API key)
- **Examples:** Simple health check workflow

See [CHANGELOG.md](CHANGELOG.md) for detailed release history.

## 🙏 Acknowledgments

- [Inductive Automation](https://inductiveautomation.com/) - Ignition SCADA Platform
- Built for automation engineers and test teams
- Developed with [Claude Code](https://claude.com/claude-code)

---

**Repository:** https://github.com/nigelgwork/ignition-playground
**Questions or Issues?** Open an issue on GitHub
