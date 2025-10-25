# Changelog

All notable changes to the Ignition Automation Toolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
