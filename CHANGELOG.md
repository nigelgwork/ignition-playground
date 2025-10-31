# Changelog

All notable changes to the Ignition Automation Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.2] - 2025-10-31

### Fixed
- **Critical:** Resolved cancel button race condition causing task cleanup before cancellation logic completes
- Replaced 43 debug `print()` statements with `logger.debug()` for proper logging
  - `ignition_toolkit/playbook/engine.py`: 33 statements
  - `ignition_toolkit/api/routers/executions.py`: 4 statements
  - `ignition_toolkit/browser/manager.py`: 6 statements

### Removed
- Deleted unused legacy file `step_executor_old.py` (781 lines, 32KB)
- Removed 115 lines of dead credential autofill code from `executions.py` (duplicate of `CredentialManager`)
- Cleaned up 8 screenshot files from root directory → moved to `docs/screenshots/`
- Archived 63MB tarball `designerlauncher.tar.gz` → moved to `archive/`
- Archived 8 temporary V4 development documents → moved to `archive/v4-development/`

### Changed
- Updated all version references from 3.0.0 → 4.0.2 across 10 documentation files
- Moved 7 test files from root directory to `tests/` for better organization
- Standardized "Last Updated" dates to 2025-10-31 across documentation

### Security
- Verified `.env` never committed to git history
- Confirmed `.env` properly listed in `.gitignore`

## [3.1.0] - 2025-10-30

### Added - Designer Automation

**NEW: Desktop Application Automation for Ignition Designer**

This release adds comprehensive Designer automation capabilities, enabling automated testing and setup of Ignition Designer desktop applications across Windows, Linux, and WSL2 environments.

#### Core Features
- **DesignerManager Class**: Lifecycle management for Designer desktop applications
  - Async context manager pattern (mirrors BrowserManager)
  - Platform-specific automation via hybrid approach
  - Auto-detection of Designer installation paths
  - Screenshot capture from Designer window

- **New Step Types** (6 new designer.* steps):
  - `designer.launch` - Launch Designer from downloaded launcher file
  - `designer.login` - Automatic credential entry and login
  - `designer.open_project` - Open specific project or wait for manual selection
  - `designer.close` - Close Designer application
  - `designer.screenshot` - Capture Designer window screenshot
  - `designer.wait` - Wait for Designer window to appear

- **Platform-Specific Automation**:
  - **Windows**: pywinauto-based window detection and interaction
  - **Linux**: python-xlib + pyatspi for X11 automation
  - **WSL2**: Automatic detection with Windows path support

- **Installation Detection**:
  - Auto-detects Designer installation on Windows, Linux, and WSL2
  - Manual override via `designer_install_path` parameter
  - Supports JNLP and native launcher files

#### Example Playbooks
- `playbooks/designer/launch_designer_simple.yaml` - Basic Designer launch and login
- `playbooks/designer/launch_designer.yaml` - Full browser-triggered workflow (advanced)

#### Integration
- Conditional DesignerManager creation in PlaybookEngine (only when designer.* steps present)
- Seamless integration with existing credential vault (global credentials work automatically)
- Browser-triggered download workflow (download launcher → launch Designer)
- Optional project selection (specify project_name or leave empty for manual selection)

#### Dependencies
- New optional dependency group: `pip install ignition-toolkit[designer]`
  - `pywinauto>=0.6.8` (Windows only)
  - `python-xlib>=0.33` (Linux only)
  - `pyatspi>=2.38.2` (Linux only)

#### Testing
- Comprehensive unit tests in `tests/test_designer.py`
- Platform-specific tests (Windows, Linux)
- Integration test framework (requires Designer installation)

#### Technical Details
- Files added:
  - `ignition_toolkit/designer/__init__.py`
  - `ignition_toolkit/designer/manager.py`
  - `ignition_toolkit/designer/detector.py`
  - `ignition_toolkit/designer/platform_windows.py`
  - `ignition_toolkit/designer/platform_linux.py`
- Files modified:
  - `ignition_toolkit/playbook/models.py` (added Designer StepType enums)
  - `ignition_toolkit/playbook/step_executor.py` (added designer routing)
  - `ignition_toolkit/playbook/engine.py` (conditional DesignerManager creation)
  - `pyproject.toml` (version bump + optional dependencies)

### Impact Assessment
- **Zero Breaking Changes**: Fully backward compatible
- **Minimal Impact**: New module in isolated directory, optional dependency
- **Clean Extension**: Follows established BrowserManager pattern

### Use Cases
- Automated Designer project creation and configuration
- Designer login testing across different environments
- Automated project migration/deployment verification
- Designer UI automation for acceptance testing
- Cross-platform Designer setup scripts

---

## [3.0.0] - 2025-10-27

### Major Release - Claude Code Phase 2 Complete

**Breaking Change:** Version numbering reset to v3.0.0+ for major architecture improvements.

### Added
- **Claude Code Phase 2 - npm-based Embedded Terminal**: Production-ready terminal integration
  - Migrated from CDN to npm package imports (xterm@5.3.0, xterm-addon-fit@0.8.0, xterm-addon-web-links@0.9.0)
  - Fixed TypeScript compatibility issues with xterm 5.3.0 API
  - Updated EmbeddedTerminal component with proper npm imports
  - Null-safety fixes throughout terminal component
  - Backend WebSocket endpoint `/ws/claude-code/{execution_id}` fully functional
  - ClaudeCodeDialog with embedded/manual mode toggle already integrated

### Fixed
- **npm Dependency Version Issues**: Resolved future/non-existent version conflicts
  - Fixed package.json versions (eslint, react-router-dom, xterm, react, vite)
  - Documented fix procedure in `.claude/NPM_DEPENDENCY_FIX.md`
  - Restored working versions from commit d676a2a (v1.0.34 baseline)
  - Successfully installed 262 packages with 0 vulnerabilities

### Technical Details
- TypeScript API updates: `selection` → `selectionBackground` for xterm 5.3.0
- Removed CDN globals (`window.Terminal`, `window.FitAddon`, `window.WebLinksAddon`)
- Added proper TypeScript typing for Terminal and addons
- Frontend version: 3.0.0
- Backend version: 3.0.0
- Files modified: `frontend/src/components/EmbeddedTerminal.tsx`, `frontend/package.json`
- Documentation: `.claude/NPM_DEPENDENCY_FIX.md`

## [2.4.0] - 2025-10-27

### Added
- **Playbook Code Viewer/Editor in Debug Mode**: View and edit playbook YAML source during execution
  - "View Code" button appears when execution is paused or debug mode is enabled
  - Live code editor with syntax validation
  - Automatic backup creation before any changes (timestamped `.backup.YYYYMMDD_HHMMSS.yaml`)
  - Read-only mode when not in debug/paused state
  - Three-column layout: Step progress | Live browser view | Code editor
  - Unsaved changes warning before closing
  - Backend endpoints: `GET /api/executions/{execution_id}/playbook/code`, `PUT /api/executions/{execution_id}/playbook/code`
  - Frontend component: `PlaybookCodeViewer.tsx`
  - Integration in `ExecutionDetail.tsx` with dynamic grid layout
  - Files: `ignition_toolkit/api/app.py`, `frontend/src/components/PlaybookCodeViewer.tsx`, `frontend/src/pages/ExecutionDetail.tsx`, `frontend/src/api/client.ts`

### Technical Details
- Backup format: `{playbook_name}.backup.{timestamp}.yaml`
- Grid layout adjusts: 2 columns (default) → 3 columns (when code viewer open)
- Visibility logic: Only shows button when `debugMode || status === 'paused'`
- Edit protection: Textarea disabled unless `isDebugMode || isPaused`
- Frontend version: 2.4.0
- Backend version: 2.4.0

## [2.3.0] - 2025-10-27

### Added
- **Claude Code Integration (Phase 2 - Embedded Terminal)**: Real-time Claude Code interaction in the browser
  - Embedded xterm.js terminal with WebSocket PTY proxy
  - Mode toggle: Switch between "Embedded" and "Manual" modes
  - WebSocket endpoint: `/ws/claude-code/{execution_id}`
  - Full bidirectional I/O: Type commands directly in browser terminal
  - Process lifecycle management: Automatic cleanup on disconnect
  - Custom Warp Terminal-inspired theme
  - xterm.js loaded via CDN (no npm dependency issues)
  - Backend: PTY process spawning, stdin/stdout proxying, signal handling
  - Frontend: `EmbeddedTerminal.tsx` component, updated `ClaudeCodeDialog.tsx`
  - Files: `ignition_toolkit/api/app.py`, `frontend/src/components/EmbeddedTerminal.tsx`, `frontend/src/components/ClaudeCodeDialog.tsx`, `frontend/index.html`

### Technical Details
- WebSocket binary frames for terminal I/O
- PTY (pseudoterminal) using built-in Python `pty` module
- Process group management with `os.setsid()` for clean termination
- Graceful shutdown: SIGTERM followed by SIGKILL if needed
- Terminal auto-resize with FitAddon
- Support for clickable links with WebLinksAddon
- Connection status messages and error handling

## [2.2.0] - 2025-10-27

### Added
- **Claude Code Integration (Phase 1 - Manual Launch)**: Debug paused executions with Claude Code CLI
  - "Claude Code" button appears when execution is paused or in debug mode
  - Generates pre-configured `claude-code` command with full execution context
  - Opens playbook YAML file with execution details (step results, errors, parameters)
  - Copy-to-clipboard functionality for easy command execution
  - Context includes current step, error messages, and masked sensitive parameters
  - Backend endpoint: `POST /api/ai/claude-code-session`
  - Frontend components: `ClaudeCodeDialog.tsx`, updates to `ExecutionControls.tsx`
  - Documentation: `docs/CLAUDE_CODE_INTEGRATION.md`
  - **Phase 2 Planned**: Embedded terminal with WebSocket proxy (see `docs/CLAUDE_CODE_PHASE2_PLAN.md`)
  - Files: `ignition_toolkit/api/app.py`, `frontend/src/components/ClaudeCodeDialog.tsx`, `frontend/src/components/ExecutionControls.tsx`, `frontend/src/pages/ExecutionDetail.tsx`, `frontend/src/api/client.ts`

- **Nested Playbook Execution (`playbook.run` step type)**: Use verified playbooks as building blocks
  - Composable playbook architecture - build complex workflows from tested components
  - Verification enforcement: Only verified playbooks can be used as steps
  - Circular dependency detection prevents infinite loops
  - Maximum nesting depth limit (3 levels)
  - Parameter mapping from parent to child playbooks
  - Single-step visibility in execution view (child steps hidden)
  - Files: `ignition_toolkit/playbook/models.py`, `ignition_toolkit/playbook/step_executor.py`
  - Documentation: `docs/FEATURE_REQUEST_NESTED_PLAYBOOKS.md`, `docs/playbook_syntax.md`

- **Delete Playbook Functionality**: Remove unwanted playbooks via UI
  - Delete menu item in playbook card 3-dot menu (red text, confirmation dialog)
  - Backend endpoint: `DELETE /api/playbooks/{path}`
  - Deletes both YAML file and metadata
  - Safety check: Only allows deleting from `playbooks/` directory
  - Files: `ignition_toolkit/api/app.py`, `frontend/src/api/client.ts`, `frontend/src/components/PlaybookCard.tsx`

### Fixed
- **Documentation Version Sync**: Updated CLAUDE.md to show correct v2.2.0 instead of v2.1.0
- **Frontend Build**: Rebuilt frontend to display v2.2.0 in UI (was incorrectly showing v1.0.28)

### Technical Details
- Frontend version: 2.2.0
- Backend version: 2.2.0
- Feature request captured in `docs/FEATURE_REQUEST_NESTED_PLAYBOOKS.md`
- Full implementation with safety checks and error handling
- Claude Code integration is Phase 1 (manual launch) - Phase 2 (embedded terminal) is future enhancement

## [2.1.0] - 2025-10-27

### Added
- **browser.verify Step Type**: New verification step for asserting element presence/absence
  - Verifies if elements exist or don't exist on page
  - Supports `exists: true` (default) or `exists: false` parameter
  - Shorter default timeout (5s) suitable for verification checks
  - Clear error messages on verification failure
  - Added to StepType enum in `ignition_toolkit/playbook/models.py`
  - Implementation in `ignition_toolkit/playbook/step_executor.py`
  - Used in gateway_login.yaml playbook for trial warning detection

### Fixed
- **WebSocket Stability - Reconnection Loop Fixed**: Comprehensive fix for rapid connect/disconnect cycles
  - **Root Cause**: Callback dependency hell causing infinite reconnection loops
  - **Solution 1 - Callback Refs Pattern**: Store callbacks in refs to break dependency cycle
    - `useWebSocket` hook now uses `callbacksRef` instead of callback dependencies
    - Connection remains stable across component re-renders
    - File: `frontend/src/hooks/useWebSocket.ts`
  - **Solution 2 - Heartbeat Mechanism**: Keep connections alive through proxies/firewalls
    - Frontend sends ping every 30 seconds
    - Backend responds with pong
    - Prevents idle connection termination
    - Files: `frontend/src/hooks/useWebSocket.ts`, `ignition_toolkit/api/app.py`
  - **Solution 3 - Removed Duplicate Endpoints**: Fixed AI credentials routing
    - Removed duplicate `/api/ai-credentials` endpoint definition
    - Only one definition now (line 1362-1440)
    - File: `ignition_toolkit/api/app.py`
  - **Result**: WebSocket connection now rock-solid, no more status indicator flickering

- **Gateway Login Playbook - License Steps Optional**: Made license checking steps non-critical
  - Steps 10-13 now have `on_failure: continue`
  - Playbook completes successfully even if license navigation UI changes
  - Core login test (Steps 1-9) remains strict
  - File: `playbooks/examples/gateway_login.yaml`

### Changed
- **Version Numbering**: Jumped from v1.0.34 to v2.1.0
  - Major version bump (2.x) reflects WebSocket architecture improvements
  - Minor version bump (x.1.x) reflects browser.verify feature addition
  - Skipped v2.0.x to align with significant stability improvements

### Technical Details
- WebSocket fixes documented in `WEBSOCKET_STABILITY_FIX.md`
- Frontend version: 2.1.0
- Backend version: 2.1.0
- All 8 phases complete (100% project completion)

## [2.0.1] - 2025-10-26

### Fixed
- **WebSocket Auto-Reconnect**: Enhanced reliability and connection management
  - Exponential backoff: 1s → 1.5s → 2.25s → ... → max 30s
  - Connection status tracking: connected | connecting | reconnecting | disconnected
  - Intentional close detection to prevent reconnect loops
  - State persistence across component remounts

### Added
- **Server Management Scripts**: Reliable lifecycle management
  - `stop_server.sh`: Clean shutdown, kills uvicorn and curl processes
  - `start_server.sh`: Pre-flight checks, prevents multiple instances
  - `update_version.sh`: All-in-one update procedure with health checks

- **WebSocket Connection Indicator**: Visual status in UI
  - Green (solid): Connected
  - Yellow (pulsing): Connecting/Reconnecting
  - Red (solid): Disconnected
  - Located in Layout component header

### Technical Details
- Documentation in `WEBSOCKET_RELIABILITY_UPDATE.md`
- Frontend version: 2.0.1
- Backend version: 2.0.1

## [2.0.0] - 2025-10-26

### Changed
- **React Upgrade**: Updated from React 18 to React 19
  - All React dependencies updated to v19
  - TypeScript types updated for React 19
  - No breaking changes in component APIs
  - Improved concurrent rendering performance

- **Material-UI v7**: Upgraded from MUI v6 to v7
  - Latest stable Material-UI components
  - Enhanced theme customization
  - Warp Terminal inspired color palette

- **Anthropic SDK**: Upgraded from 0.7.0 to 0.71.0
  - Latest Claude API features
  - Improved streaming support
  - Better error handling
  - Migration documented in `ANTHROPIC_SDK_MIGRATION.md`

### Technical Details
- Frontend version: 2.0.0
- Backend version: 2.0.0
- Node.js recommended: 20.19+ or 22.12+

## [1.0.34] - 2025-10-25

### Fixed
- **Disabled Playbook Badge Not Working**: Fixed path mismatch issue
  - Problem: Frontend sent full paths, backend stored metadata with relative paths
  - Created `get_relative_playbook_path()` helper function (app.py:388)
  - Updated enable/disable/verify/unverify endpoints to use relative paths
  - Disabled badge now appears correctly when playbook is disabled
  - Execute button properly disabled when playbook is disabled
  - Verified/Unverified status now works correctly

- **Debug Mode Not Persisting to Execution Page**: Fixed metadata storage
  - Problem: Debug mode not saved to database, lost when navigating to execution detail
  - Added debug_mode to execution_metadata when creating executions (engine.py:373)
  - Extract debug_mode from execution_metadata when retrieving from database (app.py:687-701)
  - Debug mode toggle on playbook card now persists through execution

- **Gateway Login Playbook Failing at Step 5**: Fixed for modern Ignition 8.x
  - Problem: Playbook tried to click non-existent "Continue" button
  - Modern Ignition uses single-step login (both username and password on same page)
  - Removed Continue button click step
  - Updated playbook from 8 steps to simpler 8-step flow
  - Added "Wait for Dashboard" step for better verification
  - Updated version to 1.1 and description
  - File: `playbooks/examples/gateway_login.yaml`

### Technical Details
- Backend: `ignition_toolkit/api/app.py` lines 388-408 - Path conversion helper
- Backend: `ignition_toolkit/api/app.py` lines 1119, 1139, 1157, 1175 - Metadata endpoints fixed
- Backend: `ignition_toolkit/playbook/engine.py` line 373 - Debug mode storage
- Backend: `ignition_toolkit/api/app.py` lines 687-703 - Debug mode retrieval
- Playbook: `playbooks/examples/gateway_login.yaml` - Updated for single-step login
- Frontend version: 1.0.34
- Backend version: 1.0.34

## [1.0.32] - 2025-10-25

### Fixed
- **Browser Caching Issues**: Permanent solution implemented with no-cache headers
  - Custom NoCacheStaticFiles class extends FastAPI StaticFiles
  - Adds Cache-Control, Pragma, and Expires headers to all static assets
  - index.html served with explicit no-cache headers
  - Frontend changes now immediately visible without hard refresh (Ctrl+F5)
  - Eliminates "frontend not loading" issues caused by aggressive browser caching

- **AI Assistant Z-Index**: Fixed positioning to appear above sidebar
  - Increased z-index from 1400 → 2000 (well above sidebar's 1200)
  - Positioned at left: 260px (just right of 240px sidebar)
  - Visible on left side, in front of sidebar as requested

### Technical Details
- Backend: `app.py` lines 70-80 - Custom NoCacheStaticFiles class
- Backend: `app.py` lines 1371, 1379-1383 - No-cache headers on index.html
- Frontend: `AIAssistDialog.tsx` lines 147, 168 - z-index 2000, left: 260px
- Frontend version: 1.0.33
- Backend version: 1.0.32

## [1.0.30] - 2025-10-25

### Added
- **Floating AI Chat Box**: Redesigned AI assistant as collapsible bottom-left chat widget
  - Positioned in bottom-left corner, doesn't block execution view
  - Click header to expand/collapse (400px expanded, 56px collapsed)
  - Smooth transitions with 0.3s animation
  - User can monitor execution while chatting with AI
  - Shows error context banner when step fails
  - Chat history persists during session

### Changed
- **AI Assist Endpoint**: Graceful error handling instead of HTTP errors
  - Never throws 404 - always returns helpful response
  - Provides context even when execution not in active_engines
  - User-friendly formatted debug context with bullets
  - Friendly Claude Code introduction message
  - Catches all exceptions and returns helpful fallback

### Fixed
- **AI Connection Error**: "Error connecting to AI assistant" message eliminated
  - Previously: 404 when execution not found → frontend shows error
  - Now: Always returns 200 with context → frontend shows helpful message
  - Backend endpoint returns formatted debug context
  - Shows available context even in edge cases

- **StateManager.pause() Argument Error**: Fixed wrong number of arguments
  - Previously: `pause(execution_state.execution_id)` → TypeError
  - Now: `pause()` with no arguments (correct signature)
  - Fixed in engine.py line 264

- **Missing 'Any' Import**: Fixed NameError preventing backend startup
  - Added `Any` to typing imports in app.py
  - Backend now starts correctly

### Technical Details
- Frontend: `AIAssistDialog.tsx` - Floating chat box with Material-UI Collapse
- Backend: `app.py` lines 1248-1305 - Graceful AI assist endpoint
- Backend: `engine.py` line 264 - Fixed pause() call
- Frontend version: 1.0.31 (built with floating chat)
- Backend version: 1.0.30

## [1.0.29] - 2025-10-25

### Added
- **AI Assistance Integration**: Claude Code integration for debugging executions
  - New `/api/ai/assist` endpoint to collect execution context
  - New `/api/playbooks/edit-step` endpoint for live playbook fixes
  - AIAssistDialog component now calls backend API instead of showing placeholder
  - Users can describe issues and get help from Claude Code directly

- **PlaybookEngine Debug Method**: Added `enable_debug()` method
  - Required for debug mode to function correctly
  - Delegates to StateManager's `enable_debug_mode()`

### Changed
- **Debug Mode Pause on Failure**: Executions now PAUSE on step failure instead of aborting
  - In debug mode, failed steps pause execution for troubleshooting
  - User can use AI assist to diagnose and fix issues
  - Resume or skip controls work on failed steps
  - Error message indicates debug mode pause: "Use AI assist or skip to continue"

### Fixed
- **Missing enable_debug Method**: PlaybookEngine was missing `enable_debug()` method
  - API was calling non-existent method causing 400 errors
  - Added method to engine.py (lines 94-101)

- **Execution Lockout on Failure**: Debug mode executions no longer stop on first failure
  - Previously: Step failure → execution aborted → no way to fix
  - Now: Step failure → execution paused → fix with AI → resume

### Technical Details
- Backend: `ignition_toolkit/api/app.py` lines 1225-1326 - AI endpoints
- Backend: `ignition_toolkit/playbook/engine.py` lines 94-101 - enable_debug method
- Backend: `ignition_toolkit/playbook/engine.py` lines 259-267 - Pause on failure in debug mode
- Frontend: `frontend/src/components/AIAssistDialog.tsx` lines 77-111 - API integration
- Frontend: Built and deployed with v1.0.30

## [1.0.28] - 2025-10-25

### Fixed
- **Gateway Login Playbook**: Fixed invalid `browser.verify` step type
  - Changed step type from `browser.verify` (doesn't exist) to `browser.wait`
  - Removed invalid `text` parameter from browser.wait step
  - Playbook now loads and executes correctly

### Changed
- **Playbook Cleanup**: Renamed and consolidated Gateway Login playbooks
  - Renamed `simple_health_check.yaml` to `gateway_login.yaml` in examples directory
  - Deleted duplicate `simple_health_check.yaml` from gateway directory
  - Single "Gateway Login" playbook now in examples category
  - Updated playbook name and description for clarity

### Technical Details
- Playbook: `playbooks/examples/gateway_login.yaml` line 39 - Changed step type to `browser.wait`
- Removed duplicate playbook: `playbooks/gateway/simple_health_check.yaml`
- Valid browser step types: navigate, click, fill, screenshot, wait (verify is not valid)

## [1.0.27] - 2025-10-25

### Fixed
- **Debug Mode Step-by-Step Execution**: Debug mode now auto-pauses after each step
  - Modified `engine.py` to pause after each step completion when debug mode is enabled
  - User must manually click "Resume" to execute next step
  - Allows step-by-step debugging with full control
  - Sets execution status to PAUSED after each step

### Changed
- **AI Dialog Availability**: AI assistant now accessible throughout debug mode
  - "Ask AI" button visible when debug mode is enabled OR execution is paused
  - Previously only available when paused
  - Can interact with AI at any time during debug session
  - Updated ExecutionControls to accept debugMode prop

### Technical Details
- Backend: `engine.py` lines 239-244 - Auto-pause logic in debug mode
- Frontend: `ExecutionControls.tsx` - AI button conditional updated to `(isPaused || debugMode)`
- Frontend: `ExecutionDetail.tsx` - Pass debugMode prop to ExecutionControls
- Known limitation: Steps will still timeout if paused during execution (pause happens between steps, not during)

## [1.0.26] - 2025-10-25

### Fixed
- **Disabled Playbook Visibility**: Improved disabled playbook styling to be subtle and accessible
  - Changed from heavy overlay to subtle warning border (orange) with 0.7 opacity
  - Removed blocking overlay - all buttons now accessible (users can enable/configure)
  - Added small "Disabled" warning chip instead of large error overlay
  - Removed pulsing animation that was distracting

- **Debug Mode Spacing**: Fixed debug mode switch bleeding into button below
  - Added `mb: 2` margin-bottom to debug mode toggle Box
  - Proper spacing between debug toggle and action buttons

### Added
- **AI Prompt Dialog for Paused Executions**: Complete AI chat interface for debugging
  - Created `AIAssistDialog.tsx` component with chat interface
  - "Ask AI" button appears when execution is paused
  - Shows current error context and step information
  - Ready for Anthropic API integration (placeholder implemented)
  - Includes "Apply Suggested Fix" button for future functionality

- **Skip Backward Capability**: Navigate backward through execution steps
  - Backend: Added `skip_back_step()` to StateManager and PlaybookEngine
  - Backend: New `/api/executions/{id}/skip_back` POST endpoint
  - Frontend: Added `skipBack()` to API client
  - Frontend: Added "Back" button to ExecutionControls with SkipPrevious icon

- **Interactive Browser View**: Click detection and coordinate display
  - Image now has crosshair cursor and click handler
  - Calculates and displays actual browser coordinates
  - Shows coordinates in header chip with click icon
  - Animated ripple effect on click for visual feedback
  - "Interactive" badge in header
  - Logs coordinates to console for debugging/AI context

### Changed
- **Compact Step Cards**: Reduced step card size by ~50%
  - ListItem padding: `py: 0.5, px: 1, minHeight: 36px`
  - Primary text: `fontSize: 0.8rem`
  - Secondary text: `fontSize: 0.7rem`
  - Chip: `height: 20px, fontSize: 0.65rem`
  - Reduced icon margin spacing

- **Compact Execution Header**: Reduced header size by ~50%
  - Paper padding: `p: 1` (was `p: 2`)
  - Moved execution ID inline with playbook name
  - Typography: `0.95rem` for name, `0.7rem` for ID
  - Chip height: `24px`
  - Truncated ID to first 8 characters for brevity

### Technical Details
- Frontend: PlaybookCard.tsx - Subtle disabled styling with warning theme
- Frontend: ExecutionDetail.tsx - Compact header and step cards
- Frontend: ExecutionControls.tsx - AI assist button, skip back button
- Frontend: LiveBrowserView.tsx - Interactive click detection with ripple animation
- Frontend: AIAssistDialog.tsx - NEW chat interface component
- Frontend: API client - Added skipBack() method
- Backend: StateManager - Added skip_back_step(), is_skip_back_requested(), clear_skip_back()
- Backend: PlaybookEngine - Added skip_back_step() method
- Backend: app.py - New /api/executions/{id}/skip_back endpoint
- Verified: Pause timeout already implements indefinite wait (no changes needed)

## [1.0.13] - 2025-10-24

### Fixed
- **Credential Gateway URL Not Saving**: Fixed critical bug where gateway_url wasn't persisted
  - Root cause: `vault.py:91` was not including `gateway_url` in credentials_data dictionary
  - Added `"gateway_url": credential.gateway_url` to stored credential data
  - Credentials now properly save and display gateway URLs

### Changed
- **Executions Page Layout**: Converted from card-based to clean table layout
  - Replaced ExecutionCard components with Material-UI Table
  - Columns: Playbook, Status, Progress, Started, Completed, Actions
  - Status displayed as color-coded chips (running=blue, paused=orange, completed=green, failed=red)
  - Action buttons: View (eye icon), Pause/Resume, Skip, Cancel
  - Consistent with Credentials page table styling
  - Hover effects on table rows
  - Fixed table layout with column width percentages

### Technical Details
- Backend: `vault.py` save_credential() now includes gateway_url field
- Frontend: Executions.tsx converted to table with TableContainer, Table, TableHead, TableBody
- Frontend: Added helper functions for status colors and timestamp formatting
- Frontend: Uses useNavigate for navigation to execution details

## [1.0.12] - 2025-10-24

### Fixed
- **Credential Edit Not Saving**: Fixed bug where credential edits weren't persisting
  - Backend was using credential name from request body instead of URL path
  - Changed `app.py:737` to use `name` parameter from URL path
  - Credentials now properly update when edited

- **Simple Health Check Playbook Not Visible**: Fixed playbook validation error
  - Removed invalid step types: `browser.launch` and `browser.close`
  - Browser is automatically managed by playbook engine
  - Playbook now loads correctly with 7 valid steps
  - Card now visible in Examples category

### Technical Details
- Backend: `/api/credentials/{name}` PUT endpoint now uses path parameter for credential name
- Playbook: Removed non-existent step types from simple_health_check.yaml
- Browser automation launches automatically on first browser step
- Browser closes automatically when execution completes

## [1.0.11] - 2025-10-24

### Added
- **Credential Edit Function**: Full edit capability for existing credentials
  - New EditCredentialDialog component
  - Edit icon button added to credentials table
  - PUT endpoint `/api/credentials/{name}` for updating credentials
  - Update mutation in frontend with React Query
  - Password required when updating (security best practice)
  - Credential name cannot be changed (delete and recreate if needed)

### Fixed
- **Credentials Table Layout**: Improved horizontal spacing and table width
  - Added `width: '100%', maxWidth: '100%'` to parent Box
  - Set table layout to 'fixed' for consistent column widths
  - Proper column width percentages: 25%, 25%, 40%, 10%
  - Table now properly spreads across available space

### Changed
- **Credentials Table Actions**: Now includes both Edit and Delete buttons
  - Edit button (blue) appears first
  - Delete button (red) appears second
  - Both buttons have tooltips for better UX

### Technical Details
- Backend: Added `@app.put("/api/credentials/{name}")` endpoint
- Frontend: Created `EditCredentialDialog.tsx` component
- Frontend: Updated `Credentials.tsx` with edit state and mutation
- Frontend: Updated `client.ts` API with update method

## [1.0.10] - 2025-10-24

### Added
- **Playbook Step Inspection**: View all steps in a playbook before execution
  - Backend: Added `StepInfo` model with id, name, type, timeout, retry_count
  - Updated API endpoints to include step details in playbook responses
  - Created `PlaybookStepsDialog` component with full step table
  - Step type color-coded chips (gateway=primary, browser=secondary, ai=success)
  - "View All Steps" menu option in playbook cards
  - First 5 steps shown in expanded card details

- **Visual Health Check Playbook**: Simple browser-based health check
  - Opens Ignition Gateway in browser
  - Logs in with credentials
  - Takes screenshot for verification
  - Perfect first test to visually verify connectivity

### Changed
- **Enhanced Card Styling**: Made playbook cards more visually distinct
  - Increased border width from 1px to 2px (3px on hover)
  - Added elevation={3} for depth
  - Increased border radius for rounded corners
  - Changed gap between cards from 3 to 4
  - Stronger hover effects (translateY -6px, shadow 12)
  - Background color change on hover

- **Credentials Page**: Changed from card grid to clean table layout
  - Table format with Name, Username, Gateway URL, Actions columns
  - Hover effects on rows
  - Gateway URL displayed as chips
  - More compact and professional appearance

- **Drag Mode Toggle**: Added button to enable/disable drag mode
  - Button in Playbooks header changes to "Drag Mode ON" when enabled
  - Cards only draggable when mode is enabled
  - Fixes issue where buttons were unclickable during drag

### Technical Details
- Frontend: Added `StepInfo` interface to types
- Frontend: Updated `PlaybookInfo` to include `steps` array
- Frontend: Modified PlaybookCard to show real step data
- Card styling: Added borderRadius, backgroundColor, stronger transitions

## [1.0.9] - 2025-10-24

### Added
- **Drag-and-Drop Playbook Reordering**: Organize playbooks visually with persistent ordering
  - Drag playbook cards to reorder within each category (Gateway, Designer, Perspective)
  - Order persisted to localStorage per category
  - Smooth animations during drag operations
  - Visual feedback with opacity change while dragging
  - Uses @dnd-kit library for accessible, modern drag-and-drop

- **Auto-fill from Global Credentials**: Playbook execution dialog now auto-fills from selected credential
  - Auto-fills gateway URL from global credential
  - Auto-fills credential parameter if playbook has one
  - Auto-fills username/password parameters by name matching
  - Works with both saved credentials and session-only credentials
  - Visual indicator (Alert) shows which credential was used for auto-fill
  - No need to manually configure when using global credential

### Technical Details
- **Frontend**: Added @dnd-kit/core and @dnd-kit/sortable dependencies
- **State Management**: Added per-category state for playbooks to enable re-rendering on drag
- **Drag Sensors**: Configured pointer and keyboard sensors for accessibility
- **Order Persistence**: Uses localStorage keys: `playbook_order_gateway`, `playbook_order_designer`, `playbook_order_perspective`
- **Auto-fill Logic**: Reads from Zustand global state, auto-fills based on parameter name matching

## [1.0.8] - 2025-10-24

### Added
- **Global Credential Selector**: Select credentials once, apply to all playbook executions
  - Dropdown selector in main app bar
  - Shows username@gateway_url for quick reference
  - Applies globally across all playbook configurations

- **Enhanced Credential Management**:
  - Gateway URL field added to credentials (URL, username, password)
  - Session-only credentials (temporary, not saved to vault)
  - Credentials now support gateway URL for auto-configuration
  - Visual distinction between saved and session credentials

- **Improved Card UX**:
  - Playbook cards now have hover effects (elevation, border highlight, lift animation)
  - Smooth transitions on hover
  - Visual cursor feedback (grab cursor)

- **Playbook Organization**:
  - Created `/playbooks/perspective/` directory with README placeholder
  - Created `/playbooks/designer/` directory with README placeholder
  - Focus on Gateway automation first, Perspective/Designer coming later

### Changed
- **Version Display**: Fixed version showing as "v..." in UI - now displays correct version (1.0.8)
- **Credential Dialog**: Enhanced with Gateway URL field and "Session Only" toggle
- **Credential Cards**: Now display gateway URL when present

### Removed
- **Browser Playbooks**: Deleted `/playbooks/browser/` directory (incorrect Perspective implementations)
  - Removed: `ignition_web_test.yaml`, `screenshot_audit.yaml`, `web_login_test.yaml`
  - Will be replaced with proper Perspective playbooks in future release

### Technical Details
- **Backend**: Extended Credential model with `gateway_url` field (backward compatible)
- **Frontend**: Added Zustand state for global credential selection and session credentials
- **API**: Updated credential endpoints to handle gateway_url field
- **Database**: Credential vault automatically handles new field (no migration needed)

### Migration Notes
- Existing credentials work without URL - URL field is optional
- Session credentials are stored in browser memory only (cleared on refresh)
- No breaking changes - fully backward compatible

## [1.0.7] - 2025-10-24

### Added
- **Robust Startup System**: Comprehensive 5-phase startup validation system
  - Phase 1: Environment validation (Python version, directories, permissions)
  - Phase 2: Database initialization with schema verification
  - Phase 3: Credential vault initialization with encryption testing
  - Phase 4: Playbook library validation (non-fatal)
  - Phase 5: Frontend build validation (non-fatal, production only)
  - Fail-fast error handling with recovery hints
  - Graceful degradation for non-critical components

- **Health Check Endpoints**: Kubernetes-style health monitoring
  - `GET /health` - Overall health check (200 if healthy/degraded, 503 if unhealthy)
  - `GET /health/live` - Liveness probe (always 200 if running)
  - `GET /health/ready` - Readiness probe (200 if ready, 503 if not)
  - `GET /health/detailed` - Component-level health details with timestamps
  - Real-time health state tracking for all system components

- **Modular Startup Architecture**:
  - `ignition_toolkit/startup/health.py` - Health state management
  - `ignition_toolkit/startup/exceptions.py` - Startup-specific exceptions
  - `ignition_toolkit/startup/validators.py` - Component validators
  - `ignition_toolkit/startup/lifecycle.py` - FastAPI lifespan manager
  - `ignition_toolkit/api/routers/health.py` - Health check endpoints

### Enhanced
- **Database Module**: Added `verify_schema()` method for validation
- **Credential Vault**: Added `initialize()` and `test_encryption()` methods with singleton pattern
- **Configuration**: Added Playwright settings (headless, browser type, timeout)
- **FastAPI App**: Integrated lifespan context manager, replaced deprecated startup/shutdown events

### Testing
- **Comprehensive Test Coverage**: 44 automated tests for startup system
  - Unit tests for health state management (13 tests)
  - Unit tests for validators (13 tests)
  - Unit tests for lifecycle manager (8 tests)
  - Integration tests for health endpoints (11 tests)
  - All tests passing with 100% coverage of new components

### Technical Details
- Replaced deprecated `@app.on_event("startup")` with modern lifespan context manager
- Health router registered first to ensure availability during startup
- Singleton patterns for settings, database, and vault instances
- Clear separation between critical (database, vault) and non-critical (playbooks, frontend) validations
- Startup time tracking and detailed error/warning collection

### Migration Notes
- No breaking changes - all existing functionality preserved
- Health endpoints available immediately at startup
- Development mode automatically detected (skips frontend validation)
- Configuration errors now caught at startup instead of runtime

## [1.0.6] - 2025-10-24

### Fixed
- **Page Spacing**: Credentials and Executions pages no longer center content vertically
  - Loading states now appear at top of page with inline spinner and text
  - Removed `py: 8` padding and `justifyContent: 'center'` from loading boxes
  - Better UX with smaller spinner (size 20) and descriptive text

- **ExecutionDetail Loading**: Fixed "Loading execution details..." infinite loop
  - Now fetches execution from API using useQuery
  - Falls back to WebSocket updates when available
  - Shows proper loading state, error state, and not found state
  - Refetches every 2 seconds as fallback to WebSocket
  - ExecutionDetail.tsx: Added API fetch with React Query

### Technical Details
- Credentials.tsx: Changed loading box from centered to inline with text
- Executions.tsx: Changed loading box from centered to inline with text
- ExecutionDetail.tsx: Added useQuery to fetch execution, merged with WebSocket updates

## [1.0.5] - 2025-10-24

### Fixed
- **Execute Button UX**: Major improvement to playbook execution workflow
  - Execute button now disabled when no saved configuration exists (tooltip: "Configure this playbook first")
  - Execute button now directly executes with saved config instead of opening dialog
  - No need to fill form again for repeat executions
  - Automatically navigates to execution detail page with live browser streaming
  - Configure button opens dialog to edit/save configuration
  - Clear separation: Configure to setup, Execute to run

### Technical Details
- Playbooks.tsx: handleExecute() reads localStorage, calls API directly, navigates to /executions/{id}
- PlaybookCard.tsx: Execute button disabled when !savedConfig
- Defensive fallback: Opens config dialog if somehow no saved config exists

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
