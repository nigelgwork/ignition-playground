# CLAUDE.md - Development Guide for Claude Code

This file provides guidance to Claude Code when working with the Ignition Automation Toolkit.

> **⚠️ IMPORTANT:** This file contains development patterns and technical guidance. For project goals, use cases, and decision-making framework, see [PROJECT_GOALS.md](/PROJECT_GOALS.md) - the definitive reference.

## 📚 Project Overview

**Ignition Automation Toolkit** is a visual acceptance testing platform for Ignition SCADA (Gateway, Perspective, Designer) with domain-separated playbook libraries, real-time visual feedback, and optional AI-assisted test creation.

**Current Version:** 2.3.0 (Production Ready)
**Phase:** 8/8 Complete - All Core Features Implemented ✅
**Target Platform:** Ignition SCADA 8.3+
**Primary Language:** Python 3.10+
**Key Technologies:** FastAPI, Playwright, SQLite, Anthropic SDK, React 19, Material-UI v7

## 🎯 Core Principles

> **See [PROJECT_GOALS.md](/PROJECT_GOALS.md) for complete project goals and decision-making framework.**

**Key Principles for Development:**

1. **Domain Separation** - Playbooks are Gateway-only OR Perspective-only OR Designer-only (NEVER mixed)
2. **Visual Feedback Required** - Users must SEE what's happening, especially for Perspective tests
3. **Playbook Library Over Programming** - Users duplicate and modify existing playbooks, not write from scratch
4. **AI Injectable and Optional** - AI assists where helpful but is never required for execution
5. **Secure by Default** - Credentials never in playbooks, always encrypted at rest

## 🏗️ Architecture

### Technology Stack
```yaml
Backend (Python 3.10+):
  - FastAPI (API server + WebSocket) ✅
  - Playwright (browser automation for Perspective tests) ✅
  - SQLAlchemy + SQLite (execution history, state management) ✅
  - httpx (async HTTP for Gateway REST API) ✅
  - Anthropic SDK (AI-injectable steps) ✅ (integrated in v1.0.26)

Frontend (Production React App):
  - React 19 + TypeScript ✅
  - Material-UI v7 with custom Warp Terminal theme ✅
  - React Router v6 (navigation) ✅
  - Zustand (global state management) ✅
  - React Query / TanStack Query (API calls) ✅
  - WebSocket hooks (real-time execution updates) ✅
  - Vite (build system) ✅

Storage:
  - SQLite (execution history, step results, configurations) ✅
  - YAML (playbook definitions in /playbooks/) ✅
  - JSON (import/export format) ✅
  - Local filesystem (~/.ignition-toolkit/) ✅
  - Fernet-encrypted credential vault ✅
  - localStorage (UI state, saved configurations) ✅
```

### Project Structure
```
ignition-playground/
├── ignition_toolkit/           # Main Python package
│   ├── credentials/            # ✅ Fernet encrypted credential vault
│   ├── gateway/                # ✅ Async Gateway REST API client
│   ├── storage/                # ✅ SQLite database + models
│   ├── playbook/               # ✅ Execution engine (COMPLETE)
│   ├── browser/                # ✅ Playwright automation
│   ├── api/                    # ✅ FastAPI server with WebSocket
│   └── ai/                     # ⚠️ AI module (exists, not integrated in UI)
├── playbooks/                  # Domain-separated YAML playbook library
│   ├── gateway/                # Gateway-only playbooks
│   ├── perspective/            # Perspective-only playbooks
│   ├── designer/               # Designer playbooks (future)
│   └── examples/               # Example playbooks
├── frontend/                   # Production React 19 + TypeScript app
│   ├── src/
│   │   ├── pages/              # Playbooks, Executions, Credentials pages
│   │   ├── components/         # Reusable UI components
│   │   ├── hooks/              # WebSocket, API hooks
│   │   ├── store/              # Zustand global state
│   │   └── api/                # API client
│   └── dist/                   # Built frontend (served by FastAPI)
├── tests/                      # Pytest test suite
├── docs/                       # Documentation
└── PROJECT_GOALS.md            # ⭐ DEFINITIVE project goals reference
```

## ✅ What's Complete (All 8 Phases - Production Ready)

### Phase 1: Foundation ✅
- Modern Python packaging (pyproject.toml)
- Credential vault with Fernet encryption
- SQLite database schema (executions, steps, configs)
- CLI framework with Rich console
- Project structure and documentation

### Phase 2: Gateway Client ✅
- Async Gateway REST API client (httpx)
- Authentication and session management
- Module operations (list, upload, installation tracking)
- Project operations (list, get)
- System operations (restart, health check, wait_for_ready)
- Type-safe models (Module, Project, Tag, GatewayInfo, HealthStatus)

### Phase 3: Playbook Engine ✅
- YAML parser with parameter resolution
- Step executor for all step types
- State manager (pause/resume/skip)
- Credential reference substitution (`{{ credential.xxx }}`)
- Execution tracking in SQLite

### Phase 4: Import/Export ✅
- JSON export (credentials stripped)
- JSON import with validation
- CLI commands for sharing

### Phase 5: API & Frontend ✅
- FastAPI REST API (9+ endpoints)
- WebSocket real-time updates
- React 19 + TypeScript frontend
- Playbooks, Executions, Credentials pages
- Real-time execution monitoring

### Phase 6: Browser Automation ✅
- Playwright integration (Chromium)
- Browser manager and recorder
- Perspective step types (navigate, click, fill, verify)
- Screenshot capture

### Phase 7: AI Scaffolding ✅
- AI assistant class (exists, not integrated in UI yet)
- Prompt template system
- AI step types defined
- Ready for Anthropic API integration

### Phase 8: Testing & Documentation ✅
- 46+ automated tests (credential, loader, resolver, integration)
- Getting started guide
- Playbook syntax reference
- Version tracking and changelog

**Status:** Production Ready (v1.0.27) - All core features implemented

## 🔑 Key Design Patterns

### 1. Async/Await for I/O Operations
```python
async with GatewayClient("http://localhost:8088") as client:
    await client.login("admin", "password")
    modules = await client.list_modules()
```

### 2. Type-Safe with Dataclasses and Enums
```python
from dataclasses import dataclass
from enum import Enum

class ModuleState(str, Enum):
    RUNNING = "running"
    LOADED = "loaded"

@dataclass
class Module:
    name: str
    version: str
    state: ModuleState
```

### 3. Context Managers for Resources
```python
with db.session_scope() as session:
    execution = session.query(ExecutionModel).first()
```

### 4. Credential Vault Pattern
```python
vault = CredentialVault()
vault.save_credential(Credential(name="gateway_admin", username="admin", password="secret"))
credential = vault.get_credential("gateway_admin")  # Returns decrypted
```

### 5. SQLite with SQLAlchemy
```python
from ignition_toolkit.storage import get_database, ExecutionModel

db = get_database()
with db.session_scope() as session:
    execution = ExecutionModel(playbook_name="Module Upgrade", status="pending")
    session.add(execution)
```

## 🔒 Security Best Practices

### Critical Rules:
1. **Never commit credentials** - All secrets in `~/.ignition-toolkit/` or `.env`
2. **Fernet encryption** - All passwords encrypted at rest
3. **Playbook export** - Strip credentials, export only references
4. **Validation** - Validate all user inputs (tag paths, file paths, etc.)
5. **Logging** - Never log passwords or sensitive data

### Before Every Commit:
```bash
# Check for credentials in code
grep -r "password.*=.*['\"]" --exclude-dir=.git --exclude=".env" .

# Verify .env not staged
git status --porcelain | grep "\.env$"

# Check for dangerous patterns
grep -r "eval(\|exec(" ignition_toolkit/
```

### Security Checklist:
See `.claude/SECURITY_CHECKLIST.md` for comprehensive security requirements.

## 📝 Code Quality Standards

### Complexity Target:
- **Cyclomatic Complexity**: <10 (check with `radon cc ignition_toolkit/ -a`)
- **Function Length**: <50 lines (excluding docstring)
- **File Length**: <500 lines

### Documentation Requirements:
- **Google-style docstrings** for all public methods
- **Type hints** on all function parameters and returns
- **Comments** for complex logic

### Example:
```python
async def upload_module(self, module_file_path: Path) -> str:
    """
    Upload a module file (.modl) to Gateway

    Args:
        module_file_path: Path to .modl file

    Returns:
        Module ID or name

    Raises:
        ModuleInstallationError: If upload fails
        FileNotFoundError: If module file doesn't exist
    """
    pass
```

## 🧪 Testing Strategy

### Test Structure:
```
tests/
├── test_installation.py       # ✅ Package imports
├── test_credentials.py         # ⏳ Credential vault
├── test_gateway_client.py      # ⏳ Gateway operations
├── test_playbook_engine.py     # ⏳ Playbook execution
└── conftest.py                 # Pytest fixtures
```

### Run Tests:
```bash
pytest tests/ -v
pytest tests/ --cov=ignition_toolkit --cov-report=html
```

## 📁 Important Files

### Must Read (in order):
1. **PROJECT_GOALS.md** - ⭐ DEFINITIVE reference for project goals, use cases, and decision-making framework
2. **README.md** - Project overview and quick start
3. **ARCHITECTURE.md** - Design decisions (ADRs)
4. **pyproject.toml** - Package configuration and dependencies
5. **CHANGELOG.md** - Version history

### Documentation:
- **/docs/getting_started.md** - Installation and first playbook
- **/docs/PLAYBOOK_MANAGEMENT.md** - How to create/edit/duplicate playbooks
- **/docs/playbook_syntax.md** - YAML syntax reference
- **/docs/ROADMAP.md** - Planned features

### Configuration:
- **`.env.example`** - Configuration template (copy to `.env`)
- **`.gitignore`** - Excludes credentials, databases, artifacts

## 🚀 Development Workflow

### Starting Development:
```bash
cd /git/ignition-playground
pip install -e .  # Install in development mode
ignition-toolkit init  # Initialize credential vault
```

### CLI Commands:
```bash
# Initialize
ignition-toolkit init

# Credentials
ignition-toolkit credential add <name>
ignition-toolkit credential list
ignition-toolkit credential delete <name>

# Playbooks (future)
ignition-toolkit playbook list
ignition-toolkit playbook export <path>
ignition-toolkit playbook import <json>

# Server (future)
ignition-toolkit serve
```

### Git Workflow:
```bash
git add <files>
git status
git commit -m "Brief summary

Detailed explanation:
- What changed
- Why it changed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

## 🎯 Current Development Focus

> **See [ROADMAP.md](/docs/ROADMAP.md) for planned features and priorities.**

**Production Ready (v1.0.27)** - All 8 phases complete

**Recently Completed (v1.0.4 - v2.2.0):**
1. ✅ Live browser streaming at 2 FPS (v1.0.4)
2. ✅ Interactive browser view with click detection (v1.0.26)
3. ✅ AI chat interface for debugging paused executions (v1.0.26)
4. ✅ Skip backward capability (v1.0.26)
5. ✅ Debug mode with step-by-step execution (v1.0.27)
6. ✅ WebSocket stability fixes (v2.1.0)
7. ✅ browser.verify step type (v2.1.0)
8. ✅ Nested playbook execution (playbook.run) (v2.2.0)
9. ✅ Delete playbook functionality (v2.2.0)
10. ✅ Claude Code integration Phase 1 - Manual Launch (v2.2.0)

**Next Priorities (v2.3.0+):**
1. Claude Code integration Phase 2 - Embedded Terminal (see docs/CLAUDE_CODE_PHASE2_PLAN.md)
2. One-click playbook duplication UI
3. Dedicated YAML playbook editor with syntax highlighting
4. Visual regression testing with screenshot comparison

## 📊 Progress Tracking

Use the TodoWrite tool to track progress during development sessions:
- Create todos at start of work
- Mark tasks as in_progress when starting
- Mark as completed immediately when done (don't batch)
- Clean up stale todos at end of session

**DO NOT create session summary files** (PROGRESS_STATUS.md, etc.) - use git commits and CHANGELOG.md instead.

## 🐛 Known Issues

See GitHub Issues for current bugs and feature requests.

## 💡 Design Decisions

> **See [ARCHITECTURE.md](/ARCHITECTURE.md) for detailed Architecture Decision Records (ADRs).**

**Key Decisions:**

1. **Domain-Separated Playbooks** - Gateway OR Perspective OR Designer (never mixed) for simpler execution model
2. **No Docker** - Simplified deployment, native Python on Linux/WSL2
3. **SQLite** - Single-file database, easy to transfer between machines
4. **YAML Playbooks** - Human-readable, version control friendly, easy to duplicate and modify
5. **Local Credentials** - Fernet encryption, never in playbooks or git
6. **Async Gateway Client** - httpx for async, Playwright compatibility
7. **React Frontend** - Modern UI with real-time updates, not legacy HTML
8. **AI Injectable** - AI assists where helpful but never required

## 🔄 Migration Notes

This project is a **fresh start** from `ignition-auto-test`. Key differences:
- ❌ No Docker (was: docker-compose with multiple services)
- ❌ No PostgreSQL (was: PostgreSQL for Gateway data)
- ❌ No embedded Gateway (was: Ignition container)
- ✅ SQLite instead (lightweight, portable)
- ✅ Native Python (no containers)
- ✅ Connects to external Ignition gateways
- ✅ Modular architecture for future AI integration

## 📞 Getting Help

- **Project Goals**: See `PROJECT_GOALS.md` for what/why/who
- **Documentation**: See `/docs` directory for guides
- **Roadmap**: See `/docs/ROADMAP.md` for planned features
- **Security**: See `.claude/SECURITY_CHECKLIST.md`
- **Architecture**: See `ARCHITECTURE.md` for design decisions

---

**Last Updated**: 2025-10-25
**Maintainer**: Nigel G
**Status**: Production Ready (v1.0.27) - All 8 Phases Complete ✅
**Confidence Level**: High ✨
