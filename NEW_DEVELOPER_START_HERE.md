# 👋 New Developer - Start Here!

Welcome to the **Ignition Automation Toolkit** project! This guide will get you up and running quickly.

**Current Version:** 4.0.2 (Production Ready)
**Last Updated:** 2025-10-31

---

## 📚 What is This Project?

The Ignition Automation Toolkit is a **visual acceptance testing platform** for Ignition SCADA systems. It allows you to:

- Automate Ignition Gateway operations (module upgrades, project management)
- Test Perspective web applications with browser automation
- Create reusable test workflows in YAML
- Monitor executions in real-time via a modern web UI
- Debug failed tests with AI assistance

**Think of it as:** Selenium + Postman + Ansible, specifically for Ignition SCADA.

---

## 🚀 Quick Start (10 Minutes)

### 1. Prerequisites

```bash
# Check you have these installed
python3 --version  # Need 3.10+
node --version     # Need 18+
git --version
```

**Required Environment:**
- Linux or WSL2 Ubuntu (not Windows native or Mac)
- pip and npm installed

### 2. Clone and Install

```bash
cd /git/ignition-playground  # Or wherever you cloned the repo

# Install Python package in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install Playwright browsers
./venv/bin/playwright install chromium

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 3. Initialize

```bash
# Create credential vault and database
ignition-toolkit init

# This creates:
#   ~/.ignition-toolkit/credentials.enc  (Fernet-encrypted)
#   ~/.ignition-toolkit/toolkit.db       (SQLite database)
```

### 4. Start the Server

```bash
# Start both backend (FastAPI) and frontend (React) in one command
./start_server.sh

# Server will be at: http://localhost:5000
# Backend API: http://localhost:5000/api/*
# Frontend: http://localhost:5000/ (served by FastAPI)
```

### 5. Verify It's Working

Open your browser to http://localhost:5000 and you should see:
- Playbooks page (list of example playbooks)
- Executions page (empty initially)
- Credentials page (empty until you add some)

---

## 📖 Essential Reading (In Order)

**Before coding anything, read these in order:**

1. **README.md** (5 min)
   - Project overview and features
   - Quick installation instructions

2. **PROJECT_GOALS.md** (15 min)
   - MOST IMPORTANT - defines project goals and decision-making framework
   - Explains domain separation (Gateway vs Perspective vs Designer)
   - Key principles and use cases

3. **.claude/CLAUDE.md** (20 min)
   - Technical development guide
   - Code quality standards
   - Architecture patterns
   - Security best practices

4. **ARCHITECTURE.md** (20 min)
   - System architecture overview with diagrams
   - Architecture Decision Records (ADRs)
   - Technology stack rationale
   - Data flow and security architecture

5. **PACKAGES.md** (10 min)
   - Complete dependency tracking
   - Version compatibility matrix
   - How to update dependencies

6. **docs/PLAYBOOK_BEST_PRACTICES.md** (15 min)
   - How to write good playbooks
   - Common pitfalls and solutions
   - Example patterns and templates

7. **docs/ROADMAP.md** (10 min)
   - Future plans and priorities
   - Feature backlog
   - What's next for the project

---

## 🏗️ Project Structure

```
ignition-playground/
├── ignition_toolkit/          # Main Python package
│   ├── credentials/           # Fernet-encrypted credential vault
│   ├── gateway/               # Async Gateway REST API client (httpx)
│   ├── storage/               # SQLite database + SQLAlchemy models
│   ├── playbook/              # YAML playbook execution engine
│   │   ├── engine.py          # Main execution engine
│   │   ├── loader.py          # YAML parser
│   │   ├── resolver.py        # Parameter resolution
│   │   └── steps/             # 15+ step type implementations
│   ├── browser/               # Playwright browser automation
│   ├── ai/                    # AI assistant (Anthropic SDK)
│   └── api/                   # FastAPI server
│       ├── app.py             # Main app entry point
│       └── routers/           # API endpoints by feature
├── frontend/                  # React 19 + TypeScript UI
│   ├── src/
│   │   ├── pages/             # Main pages (Playbooks, Executions, Credentials)
│   │   ├── components/        # Reusable components
│   │   ├── hooks/             # WebSocket, API hooks
│   │   └── store/             # Zustand state management
│   └── dist/                  # Built frontend (served by FastAPI)
├── playbooks/                 # Example YAML playbooks
│   ├── gateway/               # Gateway-only playbooks
│   ├── perspective/           # Perspective-only playbooks
│   └── examples/              # Learning examples
├── tests/                     # Pytest test suite (46+ tests)
├── docs/                      # Documentation
│   ├── getting_started.md     # Installation guide
│   ├── playbook_syntax.md     # YAML syntax reference
│   ├── ROADMAP.md             # Future plans
│   └── archive/               # Historical implementation docs
├── .claude/                   # Claude Code instructions
│   └── CLAUDE.md              # Development guide (IMPORTANT!)
├── Makefile                   # Common development commands
├── pyproject.toml             # Python package configuration
├── VERSION                    # Current version (3.0.0)
└── CHANGELOG.md               # Version history
```

---

## 🔑 Key Concepts

### 1. Domain Separation

**Critical Rule:** Playbooks are Gateway-only OR Perspective-only OR Designer-only (NEVER mixed)

- **Gateway playbooks** = REST API operations (modules, projects, system)
- **Perspective playbooks** = Browser automation (Playwright)
- **Designer playbooks** = Future feature (not yet implemented)

### 2. Playbook System

Tests are defined in YAML:

```yaml
name: "Module Upgrade Test"
version: "1.0"

parameters:
  - name: gateway_url
    required: true
  - name: module_file
    required: true

credentials:
  - gateway_admin  # Reference to encrypted credential

steps:
  - type: gateway.login
    url: "{{ gateway_url }}"
    credential: gateway_admin

  - type: gateway.upload_module
    file: "{{ module_file }}"

  - type: gateway.wait_for_ready
    timeout: 300
```

### 3. Credential Vault

**Credentials are NEVER in playbooks or git!**

- Stored in `~/.ignition-toolkit/credentials.enc` (Fernet encrypted)
- Playbooks reference credentials by name: `credential: gateway_admin`
- Resolved at execution time

### 4. Real-Time Execution

- Backend pushes updates via WebSocket
- Frontend shows live progress
- Can pause/resume/skip steps during execution
- AI assistant available for debugging

---

## 🛠️ Common Development Tasks

### Run Tests

```bash
# All tests
make test

# With coverage report
make test-cov

# Fast tests only (skip slow integration tests)
make test-fast
```

### Code Quality

```bash
# Auto-format code (Black + Ruff)
make format

# Check code formatting
make format-check

# Run linters
make lint

# Check complexity
make complexity
```

### CI/CD Pipeline

```bash
# Run full CI/CD pipeline (all 13 stages)
make ci

# Run specific stages
make ci-lint      # Lint only
make ci-test      # Tests only
make ci-build     # Build only

# Pre-release workflow (format + full pipeline)
make pre-release
```

### Frontend Development

```bash
# Start backend only (for frontend dev)
make dev-backend

# Start frontend dev server (hot reload)
make dev-frontend

# Build production frontend
make build
```

### Database Operations

```bash
# Reset database
make db-reset

# Backup database
make db-backup

# Open SQLite shell
make db-shell
```

### Credentials

```bash
# List credentials
make cred-list

# Add credential (interactive)
make cred-add

# Backup credentials
make cred-backup
```

---

## 📝 Development Workflow

### Before Making Changes

1. Read the relevant documentation
2. Check [docs/ROADMAP.md](docs/ROADMAP.md) to see if it's planned
3. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design decisions
4. Run `make ci-lint` to ensure starting point is clean

### While Coding

1. Follow patterns in [.claude/CLAUDE.md](.claude/CLAUDE.md)
2. Write tests as you go
3. Run `make format` before committing
4. Keep functions <50 lines, cyclomatic complexity <10

### Before Committing

```bash
# 1. Format code
make format

# 2. Run linters
make ci-lint

# 3. Run tests
make test

# 4. (Optional) Run full pipeline
make ci
```

### Committing

```bash
git add <files>
git commit -m "Brief summary

Detailed explanation:
- What changed
- Why it changed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 🐛 Troubleshooting

### Server won't start

```bash
# Check if port 5000 is in use
lsof -i :5000

# Stop any running servers
./stop_server.sh

# Check server status
./check_server.sh

# Restart
./start_server.sh
```

### Frontend not updating

```bash
# Frontend is served from backend after build
cd frontend && npm run build && cd ..

# Restart server
./stop_server.sh && ./start_server.sh
```

### Playwright browser not found

```bash
# Set custom browser path
export PLAYWRIGHT_BROWSERS_PATH=/git/ignition-playground/data/.playwright-browsers

# Reinstall browsers
./venv/bin/playwright install chromium
```

### Credential vault issues

```bash
# Vault is encrypted, can't edit directly
# Use CLI to manage credentials
ignition-toolkit credential list
ignition-toolkit credential add <name>
```

---

## 🔐 Security Reminders

**NEVER commit:**
- `.env` files
- Credentials
- `~/.ignition-toolkit/` contents
- Database files (`data/*.db`)
- Screenshots with sensitive data

**Always:**
- Use credential vault for passwords
- Validate user inputs
- Never log passwords or API keys
- Check `.gitignore` before staging files

---

## 📞 Getting Help

**Documentation:**
- Technical: [.claude/CLAUDE.md](.claude/CLAUDE.md)
- Goals: [PROJECT_GOALS.md](PROJECT_GOALS.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Future: [docs/ROADMAP.md](docs/ROADMAP.md)

**Code Examples:**
- Check `playbooks/examples/` for playbook syntax
- Check `tests/` for testing patterns
- Check `frontend/src/` for React patterns

**Common Commands:**
```bash
make help          # List all available commands
make info          # Show environment info
make version       # Show current version
```

---

## ✅ Your First Contribution

**Good first tasks:**

1. **Fix a Ruff linting warning** (easy)
   - Run `make ci-lint`
   - Pick an E501 (line too long) warning
   - Shorten the line, run `make format`
   - Test: `make ci-lint`

2. **Add a test** (medium)
   - Pick a function without tests
   - Add test to `tests/test_*.py`
   - Run: `make test`

3. **Improve documentation** (easy)
   - Fix a typo
   - Add missing docstring
   - Clarify a confusing section

4. **Add a playbook example** (medium)
   - Create a new YAML in `playbooks/examples/`
   - Follow existing patterns
   - Test it via the UI

---

## 🎓 Learning Path

**Week 1: Understand the project**
- [ ] Read all essential docs (listed above)
- [ ] Install and run the server
- [ ] Run an example playbook via the UI
- [ ] Explore the codebase structure

**Week 2: Make small changes**
- [ ] Fix a linting warning
- [ ] Add a docstring
- [ ] Write a simple test
- [ ] Create a custom playbook

**Week 3: Understand the engine**
- [ ] Read `ignition_toolkit/playbook/engine.py`
- [ ] Understand step execution flow
- [ ] Try adding a new step type
- [ ] Debug a failed execution

**Week 4: Frontend or backend feature**
- [ ] Pick a feature from [docs/ROADMAP.md](docs/ROADMAP.md)
- [ ] Design the implementation
- [ ] Write tests first (TDD)
- [ ] Implement and submit for review

---

## 🚀 You're Ready!

You now have everything you need to contribute to the Ignition Automation Toolkit.

**Next steps:**
1. Star reading [PROJECT_GOALS.md](PROJECT_GOALS.md)
2. Run `make info` to verify your environment
3. Run `make help` to see all available commands
4. Start the server with `./start_server.sh`
5. Explore the UI at http://localhost:5000

**Happy coding! 🎉**

---

**Questions?** Check the documentation links above or review existing code for patterns.

**Maintainer:** Nigel G
**Project Status:** Production Ready (v3.0.0)
**Last Updated:** 2025-10-28
