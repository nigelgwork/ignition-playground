# Changelog

All notable changes to the Ignition Automation Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.4] - 2025-10-24

### Added
- **Live Browser Streaming**: Real-time browser screenshot streaming at 2 FPS during playbook execution
  - BrowserManager screenshot streaming with configurable FPS and quality
  - WebSocket broadcast of JPEG screenshots (base64 encoded)
  - LiveBrowserView React component for displaying live browser feed
  - ExecutionDetail page with split-pane layout (steps + live browser)
  - ExecutionControls component (Pause/Resume/Skip/Stop buttons)
  - Pause/resume controls affect both execution AND screenshot streaming
  - Environment variables: SCREENSHOT_FPS, SCREENSHOT_QUALITY, SCREENSHOT_STREAMING

### Changed
- **Auto-navigation to Execution Detail**: When executing a playbook, automatically navigate to /executions/{id}
  - Previously: Dialog closed, user stayed on Playbooks page
  - Now: Immediately redirected to ExecutionDetail page with live browser streaming
  - Seamless UX from configuration to execution monitoring

### Fixed
- Execute button now properly navigates to execution detail page instead of reopening configuration dialog

### Technical Details
- Backend: Screenshot callback pattern for decoupling BrowserManager from WebSocket
- Frontend: TypeScript types for ScreenshotFrame messages
- Performance: 2 FPS @ JPEG 80% quality = ~102 KB/s bandwidth (very feasible)
- Playwright can handle 13+ FPS, throttled to 2 FPS for optimal bandwidth usage

## [1.0.1] - 2025-10-22

### Changed
- Redesigned web UI with Warp terminal dark theme colors
- Updated color scheme to match Warp terminal aesthetic (#01050d background, #58a6ff primary, #3fb950 success)
- Changed app bar from bright blue to dark surface theme
- Moved stat cards from main content to compact sidebar display
- Updated branding from "Ignition Auto" to "Ignition Playground"
- Reduced sidebar header font size for better fit
- Made UI default to dark mode on first load

### Fixed
- SQLAlchemy reserved name conflict (renamed `metadata` to `execution_metadata` in storage models)
- Import errors in `__init__.py` (changed `Step` to `PlaybookStep`, `Execution` to `ExecutionState`)

## [1.0.0] - 2025-10-22

### Added - Initial Release

#### Phase 1: Foundation
- Modern Python packaging with pyproject.toml
- Fernet encrypted credential vault
- SQLite database schema for execution tracking
- CLI framework with Rich console
- Project structure and configuration

#### Phase 2: Gateway Client
- Async Gateway REST API client using httpx
- Authentication and session management
- Module operations (list, upload, wait for installation)
- Project operations (list, get details)
- System operations (restart, health check, wait_for_ready)
- Type-safe models with dataclasses
- Custom exceptions and error handling
- Automatic re-authentication on 401

#### Phase 3: Playbook Engine
- YAML playbook loader and validator
- Parameter resolution system (credential, variable, parameter references)
- Step execution framework with retry logic
- Main execution engine with orchestration
- State manager for pause/resume/skip control
- Database tracking for execution history
- Real-time callbacks for progress updates
- 15+ step types across Gateway, Browser, and Utility categories

#### Phase 4: Import/Export
- JSON export with credential stripping
- JSON import with validation
- CLI commands for sharing playbooks
- Metadata preservation

#### Phase 5: API & Frontend
- FastAPI REST API with 9 endpoints
- WebSocket for real-time execution updates
- Background task execution
- CORS support
- Simple HTML/CSS/JS web dashboard (no build step)
- Static file serving

#### Phase 6: Browser Automation
- Playwright integration (Chromium)
- Browser manager for lifecycle management
- Screenshot recorder
- 5 browser step types (navigate, click, fill, screenshot, wait)
- Headless and headed modes
- Integration with playbook engine

#### Phase 7: AI Scaffolding
- AI module structure with placeholders
- AI assistant class (placeholder for future integration)
- Prompt template system
- 3 AI step types (generate, validate, analyze)
- Integration with step executor

#### Phase 8: Testing & Documentation
- Unit tests for credential vault (10 tests)
- Unit tests for playbook loader (15 tests)
- Unit tests for parameter resolver (15 tests)
- Integration tests for playbook execution (6 tests)
- Getting started documentation
- Playbook syntax reference
- 7 example playbooks (Gateway, Browser, AI)

### Features

**Core Capabilities:**
- YAML-based playbook system
- Secure credential management with encryption
- Gateway REST API automation
- Browser automation with Playwright
- Pause/Resume/Skip during execution
- Import/Export for playbook sharing
- Web UI for monitoring and control
- Real-time execution updates via WebSocket
- Comprehensive testing suite

**Security:**
- Fernet encryption for credentials
- Local key storage
- Credentials never committed to git
- Export strips credentials automatically
- File permissions (0600) on sensitive files

**Extensibility:**
- Modular step types
- AI integration hooks
- Custom exceptions
- Plugin-ready architecture

### Technical Details

**Dependencies:**
- FastAPI 0.104+ for API server
- httpx 0.25+ for async HTTP
- Playwright 1.40+ for browser automation
- SQLAlchemy 2.0+ for database
- Pydantic 2.4+ for validation
- Click 8.1+ for CLI
- Rich 13.6+ for console output
- cryptography 41.0+ for encryption

**Supported Platforms:**
- Linux
- WSL2
- Python 3.10+

**Database:**
- SQLite (single-file, portable)
- 3 tables: executions, step_results, playbook_configs

---

## Version Scheme

**Major.Minor.Patch**

- **Major**: Breaking changes, major features
- **Minor**: New features, backwards compatible
- **Patch**: Bug fixes, minor improvements

---

## Future Releases

### Planned for 1.1.0
- Full AI integration with Anthropic API
- Additional Gateway operations (backup, restore, tags)
- Video recording for browser sessions
- Advanced playbook debugging
- Performance optimizations

### Planned for 1.2.0
- Plugin system for custom steps
- Advanced scheduling and triggers
- Email/Slack notifications
- Dashboard improvements
- Multi-user support

### Planned for 2.0.0
- Breaking changes if needed
- Major architecture updates
- New automation capabilities
- Enterprise features

---

## How to Upgrade

### From Development to 1.0.0

If you were using a development version:

```bash
cd /git/ignition-playground
git pull
pip install -e . --force-reinstall
```

### Future Upgrades

Check this CHANGELOG for breaking changes and migration guides before upgrading.

---

**Note**: This is the initial release. All features are new in 1.0.0.
