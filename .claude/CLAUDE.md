# CLAUDE.md - Development Guide for Claude Code

This file provides guidance to Claude Code when working with the Ignition Automation Toolkit.

## 📚 Project Overview

**Ignition Automation Toolkit** is a lightweight, Docker-free automation platform for Ignition SCADA Gateway operations. Built from a fresh start after migrating away from a complex Docker-based architecture.

**Current Version:** 1.0.0 (Fresh start - October 2025)
**Phase:** 2 of 8 Complete (Gateway Client ✅)
**Target Platform:** Ignition SCADA 8.3+
**Primary Language:** Python 3.10+
**Key Technologies:** FastAPI, Playwright, SQLite, Anthropic SDK

## 🎯 Project Goals

1. **Gateway Automation FIRST** - Focus on Gateway REST API operations
2. **Playbook System** - YAML-based reusable workflows with step-by-step execution
3. **Real-Time Control** - Pause, resume, skip steps during execution
4. **Secure Credentials** - Fernet encryption, local storage, never in git
5. **Import/Export** - Share playbooks as JSON with colleagues
6. **Browser Automation** - Live Playwright viewing for web operations (future)
7. **AI-Ready** - Integration points for AI-assisted testing steps (future)
8. **No Docker** - Native Python installation on Linux/WSL2 for simplicity

## 🏗️ Architecture

### Technology Stack
```yaml
Backend:
  - FastAPI (API server + WebSocket)
  - Playwright (browser automation - future)
  - SQLAlchemy + SQLite (state management)
  - httpx (async HTTP for Gateway API)
  - Anthropic SDK (AI steps - future)

Frontend:
  - React + TypeScript (to be migrated)
  - Material-UI
  - WebSocket (real-time updates)

Storage:
  - SQLite (execution history, configs)
  - JSON/YAML (playbook definitions)
  - Local filesystem (encrypted credentials)
```

### Project Structure
```
ignition-playground/
├── ignition_toolkit/           # Main Python package
│   ├── credentials/            # ✅ Fernet encrypted credential vault
│   ├── gateway/                # ✅ Async Gateway REST API client
│   ├── storage/                # ✅ SQLite database + models
│   ├── playbook/               # 🚧 Execution engine (next)
│   ├── browser/                # ⏳ Playwright automation
│   ├── api/                    # ⏳ FastAPI server
│   └── ai/                     # ⏳ AI integration
├── playbooks/                  # YAML playbook library
├── frontend/                   # React UI (to migrate)
├── tests/                      # Test suite
└── docs/                       # Documentation
```

## ✅ What's Complete (Phases 1-2)

### Phase 1: Foundation
- ✅ Modern Python packaging (pyproject.toml)
- ✅ Credential vault with Fernet encryption
- ✅ SQLite database schema (executions, steps, configs)
- ✅ CLI framework with Rich console
- ✅ Project structure and documentation

### Phase 2: Gateway Client
- ✅ Async Gateway REST API client (httpx)
- ✅ Authentication and session management
- ✅ Module operations (list, upload, installation tracking)
- ✅ Project operations (list, get)
- ✅ System operations (restart, health check, wait_for_ready)
- ✅ Type-safe models (Module, Project, Tag, GatewayInfo, HealthStatus)
- ✅ Custom exceptions
- ✅ Automatic re-authentication on 401

## 🚧 What's Next (Phase 3)

### Playbook Engine
Build the core execution engine with:
1. **YAML Parser** - Load playbooks from YAML files
2. **Step Executor** - Execute steps using Gateway client
3. **State Manager** - Pause/resume/skip functionality
4. **Parameter Resolution** - Substitute `{{ credential.xxx }}` with actual values
5. **Execution Tracking** - Save to SQLite database

### Example Playbook (YAML):
```yaml
name: "Module Upgrade"
version: "1.0"

parameters:
  - name: gateway_url
    type: string
    required: true
  - name: gateway_password
    type: credential
    required: true
  - name: module_file
    type: file
    required: true

steps:
  - id: authenticate
    name: "Login to Gateway"
    type: gateway.login
    parameters:
      url: "{{ gateway_url }}"
      password: "{{ credential.gateway_password }}"

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

### Must Read:
1. **README.md** - Project overview and quick start
2. **PLAN.md** - Detailed implementation roadmap
3. **PROGRESS.md** - Current status and next steps
4. **pyproject.toml** - Package configuration and dependencies

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

### Phase 3: Playbook Engine (Next)
**Priority**: High
**Timeline**: 2-3 days
**Files to Create**:
- `ignition_toolkit/playbook/models.py` - Playbook, Step, Execution dataclasses
- `ignition_toolkit/playbook/loader.py` - YAML parser
- `ignition_toolkit/playbook/engine.py` - Main execution engine
- `ignition_toolkit/playbook/state_manager.py` - Pause/resume/skip logic
- `ignition_toolkit/playbook/step_executor.py` - Execute individual steps
- `ignition_toolkit/playbook/parameters.py` - Parameter resolution

**Key Features**:
1. Load playbooks from YAML
2. Parse parameters and steps
3. Resolve credential references (`{{ credential.xxx }}`)
4. Execute steps sequentially
5. Save state to database
6. Support pause/resume/skip

## 📊 Progress Tracking

Use the todo list to track progress:
- Mark tasks as in_progress when starting
- Mark as completed immediately when done
- Don't batch completions

Current phase: **Phase 3 - Playbook Engine**

## 🐛 Known Issues

None yet! Fresh start = clean slate.

## 💡 Design Decisions

1. **No Docker** - Simplified deployment, native Python on Linux/WSL2
2. **SQLite** - Single-file database, easy to transfer between machines
3. **YAML Playbooks** - Human-readable, version control friendly
4. **Local Credentials** - Fernet encryption, never in git
5. **Async Gateway Client** - httpx for async, Playwright compatibility
6. **Modular Steps** - Each step can be AI-assisted in future

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

- **Documentation**: See `/docs` directory
- **Issues**: Check `PROGRESS.md` for current status
- **Security**: See `.claude/SECURITY_CHECKLIST.md`
- **Architecture**: See `PLAN.md`

---

**Last Updated**: 2025-10-22
**Maintainer**: Nigel G
**Status**: Phase 2 Complete, Phase 3 Next
**Confidence Level**: High ✨
