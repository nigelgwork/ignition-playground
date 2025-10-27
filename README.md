# Ignition Automation Toolkit

> Lightweight, transferable automation platform for Ignition SCADA Gateway operations

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](VERSION)

## 🎯 Overview

A modern, Docker-free automation toolkit for Ignition SCADA with complete playbook-driven workflows:

- **Gateway Automation**: REST API client for modules, projects, system operations
- **Playbook System**: YAML-based reusable workflows with 15+ step types
- **Real-Time Control**: Pause, resume, skip steps during execution via WebSocket
- **Browser Automation**: Playwright integration for web-based operations
- **Secure Credentials**: Fernet-encrypted local storage, never committed to git
- **Import/Export**: Share playbooks as JSON with colleagues
- **AI-Ready**: Integration scaffolding for AI-assisted testing steps
- **Web UI**: Modern dark-theme interface with Warp terminal colors

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Linux or WSL2 Ubuntu
- pip

### Installation

#### Option 1: Using Makefile (Recommended)

```bash
# Clone repository
git clone git@github.com:nigelgwork/ignition-playground.git
cd ignition-playground

# Install and initialize
make install          # Install in development mode
make install-dev      # Install with dev dependencies
make install-playwright  # Install Playwright browsers
make init             # Initialize credential vault and .env

# Start development server
make dev              # Start backend + frontend with hot reload

# Or use Docker
make docker-build     # Build Docker image
make docker-up        # Start services with docker-compose
```

#### Option 2: Manual Setup

```bash
# Clone repository
git clone git@github.com:nigelgwork/ignition-playground.git
cd ignition-playground

# Install in development mode
pip install -e .

# Install Playwright browsers
playwright install chromium

# Initialize credential vault
ignition-toolkit init

# Start server
ignition-toolkit serve --port 8080
```

Access the web UI at http://localhost:8080

#### Option 3: Docker Deployment

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

- [Getting Started Guide](docs/getting_started.md) - Installation and first steps
- [Running Playbooks](docs/RUNNING_PLAYBOOKS.md) - Complete guide with examples
- [Playbook Syntax](docs/playbook_syntax.md) - YAML reference and step types
- [Testing Guide](docs/TESTING_GUIDE.md) - Test suite and coverage
- [Versioning Guide](docs/VERSIONING_GUIDE.md) - Release management

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
│   ├── api/                   # FastAPI server + WebSocket
│   ├── storage/               # SQLite database models
│   ├── ai/                    # AI integration scaffolding
│   └── cli.py                 # Command-line interface
├── playbooks/                 # YAML playbook library
│   ├── gateway/               # Gateway automation workflows
│   ├── browser/               # Browser automation workflows
│   ├── ai/                    # AI-assisted workflows
│   └── examples/              # Example playbooks
├── frontend/                  # Web UI (HTML/CSS/JS)
├── tests/                     # Test suite (46 tests)
├── docs/                      # Documentation
├── .claude/                   # Claude Code instructions
├── CHANGELOG.md               # Version history
├── VERSION                    # Current version (1.0.27)
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

**Current Version:** 1.0.30 (October 2025)
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
