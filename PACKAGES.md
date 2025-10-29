# Package Dependencies

**Project:** Ignition Automation Toolkit
**Current Version:** 3.0.0
**Last Updated:** 2025-10-27
**Python:** 3.10+
**Node.js:** 18+ or 20+

This document tracks all project dependencies, their versions, and provides guidance for keeping them up-to-date.

---

## Python Dependencies (Backend)

### Production Dependencies

From `pyproject.toml` (version 3.0.0):

| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| **fastapi** | >=0.115.0 | Web framework & API server | Modern async web framework |
| **uvicorn[standard]** | >=0.32.0 | ASGI server | Production server for FastAPI |
| **httpx** | >=0.27.0 | Async HTTP client | Gateway REST API communication |
| **pydantic** | >=2.10.0 | Data validation | Type-safe models |
| **pydantic-settings** | >=2.7.0 | Configuration management | Environment variables |
| **sqlalchemy** | >=2.0.35 | Database ORM | Execution history storage |
| **aiosqlite** | >=0.20.0 | Async SQLite driver | Database async support |
| **pyyaml** | >=6.0.2 | YAML parser | Playbook definitions |
| **cryptography** | >=44.0.0 | Encryption library | Fernet credential encryption |
| **playwright** | >=1.49.0 | Browser automation | Perspective testing |
| **python-multipart** | >=0.0.18 | Multipart form data | File uploads |
| **python-dotenv** | >=1.0.1 | Environment loader | .env file support |
| **websockets** | >=14.0 | WebSocket protocol | Real-time updates |
| **click** | >=8.1.7 | CLI framework | Command-line interface |
| **rich** | >=13.9.0 | Terminal formatting | Beautiful console output |

### Development Dependencies

From `pyproject.toml` [dev]:

| Package | Version | Purpose |
|---------|---------|---------|
| **pytest** | >=8.3.0 | Testing framework |
| **pytest-asyncio** | >=0.24.0 | Async test support |
| **pytest-cov** | >=6.0.0 | Coverage reporting |
| **black** | >=24.10.0 | Code formatter |
| **ruff** | >=0.8.0 | Fast linter |
| **mypy** | >=1.13.0 | Type checker |

### Optional Dependencies

From `pyproject.toml` [ai]:

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| **anthropic** | >=0.42.0 | Claude AI integration | Integrated in v1.0.26 |

**Install optional dependencies:**
```bash
pip install -e ".[ai]"     # AI features
pip install -e ".[dev]"    # Development tools
pip install -e ".[ai,dev]" # Both
```

---

## Frontend Dependencies (React)

### Production Dependencies

From `frontend/package.json` (version 3.29.0):

| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| **react** | ^19.1.1 | UI framework | Upgraded from 18 in v3.0 |
| **react-dom** | ^19.1.1 | React DOM bindings | Matches react version |
| **react-router-dom** | ^7.9.4 | Client-side routing | Navigation |
| **@mui/material** | ^7.3.4 | Material-UI components | Upgraded from v6 in v3.0 |
| **@mui/icons-material** | ^7.3.4 | Material-UI icons | Matches MUI version |
| **@emotion/react** | ^11.14.0 | CSS-in-JS | MUI dependency |
| **@emotion/styled** | ^11.14.1 | Styled components | MUI dependency |
| **@tanstack/react-query** | ^5.90.5 | Data fetching & caching | Server state management |
| **zustand** | ^5.0.8 | State management | Global client state |
| **xterm** | ^5.3.0 | Terminal emulator | Claude Code terminal |
| **xterm-addon-fit** | ^0.8.0 | Terminal resize addon | Auto-fit terminal |
| **xterm-addon-web-links** | ^0.9.0 | Terminal hyperlinks | Clickable links |
| **@monaco-editor/react** | ^4.7.0 | Code editor | Playbook YAML editing |
| **@dnd-kit/core** | ^6.3.1 | Drag & drop core | Reordering UI |
| **@dnd-kit/sortable** | ^10.0.0 | Sortable lists | Drag & drop lists |

### Development Dependencies

From `frontend/package.json`:

| Package | Version | Purpose |
|---------|---------|---------|
| **vite** | ^7.1.7 | Build tool & dev server |
| **typescript** | ~5.9.3 | Type system |
| **@vitejs/plugin-react** | ^5.0.4 | React support for Vite |
| **eslint** | ^9.36.0 | JavaScript linter |
| **@eslint/js** | ^9.36.0 | ESLint core rules |
| **eslint-plugin-react-hooks** | ^5.2.0 | React hooks linting |
| **eslint-plugin-react-refresh** | ^0.4.22 | Fast refresh linting |
| **typescript-eslint** | ^8.45.0 | TypeScript ESLint |
| **@types/react** | ^19.1.16 | React type definitions |
| **@types/react-dom** | ^19.1.9 | React DOM types |
| **@types/node** | ^24.6.0 | Node.js types |
| **globals** | ^16.4.0 | Global variables types |

---

## System Dependencies

### Required System Packages

| Package | Version | Purpose | Installation |
|---------|---------|---------|--------------|
| **Python** | 3.10+ | Backend runtime | `apt install python3.10` (Ubuntu) |
| **Node.js** | 18+ or 20+ | Frontend build | `nvm install 20` or `apt install nodejs` |
| **npm** | 9+ | Package manager | Included with Node.js |
| **Chromium** | Latest | Browser automation | Auto-installed by Playwright |

### Playwright Browsers

Playwright automatically downloads browser binaries:

```bash
# Install Playwright browsers
playwright install chromium

# Or via npm after frontend install
cd frontend
npm install
npx playwright install chromium
```

**Browser storage location:**
- Default: `~/.cache/ms-playwright/`
- Custom (project): `data/.playwright-browsers/` (if configured)

---

## Version Update History

### v3.0.0 (2025-10-27) - Major Frontend Upgrade
- **React**: 18.x → 19.1.1
- **Material-UI**: 6.x → 7.3.4
- **xterm**: CDN → npm 5.3.0 (migrated from CDN link)
- **React Router**: 6.x → 7.9.4
- **Anthropic SDK**: 0.7.x → 0.42.0 (previous upgrade in v2.0.0)

### v2.0.0 (2025-10-xx) - API Modernization
- **Anthropic SDK**: 0.7.x → 0.71.0 (then later → 0.42.0)
- **FastAPI**: 0.110.x → 0.115.0+
- **Pydantic**: 2.8.x → 2.10.0+

### v1.0.0 (2025-10-xx) - Initial Release
- Initial dependency set established

---

## Keeping Dependencies Up-to-Date

### Check for Outdated Packages

**Python (Backend):**
```bash
# Check outdated packages
pip list --outdated

# Or use pip-outdated (if installed)
pip install pip-outdated
pip-outdated

# Check specific package
pip show <package-name>
```

**Node.js (Frontend):**
```bash
cd frontend

# Check outdated packages
npm outdated

# Check specific package
npm list <package-name>
```

### Update Packages Safely

**Python (Backend):**
```bash
# Update specific package
pip install --upgrade <package-name>

# Update all packages (use with caution)
pip install --upgrade -r <(pip freeze)

# Update and test
pip install --upgrade <package-name>
pytest tests/ -v  # Run tests to verify
```

**Node.js (Frontend):**
```bash
cd frontend

# Update specific package (respects semver)
npm update <package-name>

# Update to latest (may break semver)
npm install <package-name>@latest

# Update all packages (respects package.json constraints)
npm update

# Update and test
npm run build  # Verify build succeeds
npm run lint   # Check for linting issues
```

### Upgrade Strategy

1. **Check compatibility** - Read changelogs and migration guides
2. **Update dev environment first** - Test locally before production
3. **Run full test suite** - `pytest tests/ -v` and `npm run build`
4. **Update one major dependency at a time** - Easier to debug issues
5. **Update pyproject.toml and package.json** - Commit version changes
6. **Document breaking changes** - Update CHANGELOG.md
7. **Update this file** - Add entry to Version Update History

### Security Updates

**Check for security vulnerabilities:**

```bash
# Python
pip install safety
safety check

# Node.js
cd frontend
npm audit

# Fix npm vulnerabilities automatically
npm audit fix
```

---

## Compatibility Matrix

### Python Version Compatibility

| Component | Python 3.10 | Python 3.11 | Python 3.12 | Notes |
|-----------|-------------|-------------|-------------|-------|
| Backend (all deps) | ✅ Tested | ✅ Tested | ✅ Compatible | Officially supported |
| FastAPI | ✅ | ✅ | ✅ | Full support |
| Playwright | ✅ | ✅ | ✅ | Full support |
| SQLAlchemy | ✅ | ✅ | ✅ | Full support |

### Node.js Version Compatibility

| Component | Node 18 | Node 20 | Node 22 | Notes |
|-----------|---------|---------|---------|-------|
| Frontend (all deps) | ✅ Tested | ✅ Tested | ✅ Compatible | All LTS versions |
| Vite 7 | ✅ | ✅ | ✅ | Full support |
| React 19 | ✅ | ✅ | ✅ | Full support |

### Operating System Compatibility

| OS | Python Backend | Node Frontend | Playwright | Notes |
|----|----------------|---------------|------------|-------|
| **Linux** | ✅ | ✅ | ✅ | Primary development OS |
| **WSL2 Ubuntu** | ✅ | ✅ | ✅ | Recommended for Windows |
| **macOS** | ✅ | ✅ | ✅ | Should work (not tested) |
| **Windows** | ⚠️ | ✅ | ⚠️ | Use WSL2 instead |

---

## Troubleshooting

### Common Issues

**Issue: `pip install` fails with "No matching distribution"**
- **Solution**: Upgrade pip: `pip install --upgrade pip`

**Issue: Playwright browsers not found**
- **Solution**: Install browsers: `playwright install chromium`

**Issue: `npm install` fails with EACCES error**
- **Solution**: Fix npm permissions or use nvm: [nvm installation guide](https://github.com/nvm-sh/nvm)

**Issue: Type errors after updating TypeScript**
- **Solution**: Clear build cache: `rm -rf frontend/node_modules/.vite && npm run build`

**Issue: FastAPI won't start after updating dependencies**
- **Solution**: Check compatibility, reinstall: `pip install -e .`

---

## Dependency Installation Commands

### Fresh Installation

**Backend:**
```bash
# Install production dependencies
pip install -e .

# Install with dev tools
pip install -e ".[dev]"

# Install with AI support
pip install -e ".[ai,dev]"

# Install Playwright browsers
playwright install chromium
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
```

### Verification

**Check installation:**
```bash
# Python packages
pip list | grep -E "fastapi|playwright|anthropic"

# Node packages
cd frontend
npm list --depth=0

# Playwright browsers
playwright --version
```

---

## Notes

- **Semantic Versioning**: This project uses `>=` for Python deps and `^` for npm deps
- **Python `>=` syntax**: Allows patch and minor updates (e.g., `>=0.115.0` allows 0.115.1, 0.116.0, etc.)
- **npm `^` syntax**: Allows patch and minor updates (e.g., `^19.1.1` allows 19.1.2, 19.2.0, but not 20.0.0)
- **Lockfiles**:
  - Python: No lockfile by default (consider `pip-tools` for `requirements.lock`)
  - Node.js: `package-lock.json` (committed to repo)

---

## Related Documentation

- **pyproject.toml** - Python package configuration
- **frontend/package.json** - Node.js package configuration
- **CHANGELOG.md** - Version history and breaking changes
- **ARCHITECTURE.md** - Technical architecture and design decisions

---

**Last Reviewed:** 2025-10-27
**Next Review Due:** 2026-01-27 (quarterly)
**Maintainer:** Nigel G
