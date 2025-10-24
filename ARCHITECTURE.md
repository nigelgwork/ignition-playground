# Architecture Decision Records (ADRs)

**Last Updated:** 2025-10-24
**Version:** 1.0.3

This document captures key architectural decisions for the Ignition Automation Toolkit. Each decision is documented with context, rationale, and consequences.

---

## ADR-001: Domain-Separated Playbooks

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

When designing the playbook system, we had to decide whether to allow mixing step types from different domains (Gateway, Perspective, Designer) within a single playbook, or enforce domain separation.

**Option 1: Mixed Playbooks**
```yaml
# Mixed approach - Gateway + Perspective in one playbook
steps:
  - type: gateway.upload_project
  - type: gateway.restart
  - type: perspective.navigate  # Different domain!
  - type: perspective.verify_element
```

**Option 2: Domain-Separated Playbooks**
```yaml
# Domain-separated - Gateway playbook only
steps:
  - type: gateway.upload_project
  - type: gateway.restart

# Separate Perspective playbook
steps:
  - type: perspective.navigate
  - type: perspective.verify_element
```

### Decision

**We chose domain-separated playbooks**: Each playbook must stay within one domain (Gateway OR Perspective OR Designer, never mixed).

### Rationale

1. **Simpler Execution Model**: Each domain has different requirements:
   - Gateway steps: HTTP client, API authentication
   - Perspective steps: Playwright browser, DOM interaction
   - Designer steps (future): Different automation approach (non-web)

   Mixing these in one execution context complicates state management.

2. **Clearer Organization**: Users can easily find relevant playbooks:
   - Looking for Gateway module upgrade? Check `/playbooks/gateway/`
   - Looking for Perspective login test? Check `/playbooks/perspective/`

3. **Easier Troubleshooting**: When a playbook fails, domain separation makes it clear which system (Gateway vs Perspective vs Designer) has the issue.

4. **Better Reusability**: Domain-specific playbooks are more reusable:
   - Gateway playbook "upload_module.yml" works regardless of what Perspective apps exist
   - Perspective playbook "test_login.yml" works regardless of Gateway state

5. **Modular Development**: Frontend UI can be organized by domain, backend step executors are domain-specific, and new domains can be added without affecting existing ones.

### Consequences

**Positive:**
- Clear responsibility boundaries
- Easier to test (domain-specific test suites)
- Better documentation (domain-specific guides)
- Encourages modular, reusable playbooks

**Negative:**
- Users must run multiple playbooks sequentially for end-to-end workflows
- Example: Run "gateway_deploy.yml" → wait → run "perspective_verify.yml"

**Accepted Trade-off:** Sequential execution is acceptable because:
- Each step should be testable independently
- Clear boundaries make debugging easier
- Users can still orchestrate complex workflows by running playbooks in sequence

---

## ADR-002: YAML for Playbook Definitions

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

We needed a format for playbook definitions that would be:
- Human-readable
- Version control friendly
- Easy to duplicate and modify
- Accessible to non-programmers

**Options Considered:**
1. **JSON**: Machine-readable, widely supported
2. **YAML**: Human-readable, comments supported
3. **Python DSL**: Programmable, flexible
4. **Custom format**: Tailored to needs

### Decision

**We chose YAML** for playbook definitions.

### Rationale

1. **Human-Readable**: Test engineers (not just programmers) can read and understand:
   ```yaml
   name: "Test Login Flow"
   steps:
     - name: "Navigate to login page"
       type: perspective.navigate
       parameters:
         url: "{{ gateway_url }}/perspective/client/MyApp"
   ```

2. **Comments Supported**: Users can document their playbooks:
   ```yaml
   # This step verifies the dashboard chart loads within 10 seconds
   - name: "Verify chart loads"
     type: perspective.verify_element
     parameters:
       selector: ".dashboard-chart"
       timeout: 10
   ```

3. **Version Control Friendly**: YAML diffs are readable, making code review easy

4. **Easy to Duplicate**: Copy YAML file, change a few values, done

5. **Industry Standard**: Widely used in automation (Ansible, GitHub Actions, Kubernetes)

### Consequences

**Positive:**
- Non-programmers can create and modify playbooks
- Copy-paste-modify workflow is fast
- Version control shows meaningful diffs
- Comments allow in-line documentation

**Negative:**
- YAML syntax errors can be cryptic (indentation issues)
- Less flexible than programming (can't do complex logic)

**Mitigation:**
- Provide YAML syntax validation in UI
- Offer playbook templates
- AI-assisted playbook creation for complex cases

---

## ADR-003: No Docker / Native Python

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

Previous version (`ignition-auto-test`) used Docker with docker-compose for packaging. We had to decide whether to continue with Docker or use native Python installation.

**Option 1: Docker**
- Pros: Consistent environment, easy distribution
- Cons: Complex setup, resource overhead, slower development cycle

**Option 2: Native Python**
- Pros: Simple installation, faster development, direct system access
- Cons: Dependency management, environment variability

### Decision

**We chose native Python installation** on Linux/WSL2.

### Rationale

1. **Simpler Deployment**: `pip install ignition-toolkit` is simpler than Docker setup

2. **Faster Development**: No container rebuild cycles, direct code changes

3. **Better Playwright Integration**: Browser automation works more reliably without container layers

4. **Lightweight**: No container overhead, runs directly on host

5. **Easier Debugging**: Direct access to logs, processes, and system state

### Consequences

**Positive:**
- Faster installation for end users
- Easier development workflow
- Better performance (no container overhead)
- Simpler architecture

**Negative:**
- Users must manage Python environment
- Dependency conflicts possible (use virtual environments)
- Platform-specific (Linux/WSL2 primarily)

**Accepted Trade-off:** Target users (test automation engineers, DevOps) are comfortable with Python environments.

---

## ADR-004: SQLite for Execution History

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

We needed persistent storage for execution history, step results, and configurations.

**Options:**
1. **PostgreSQL**: Robust, scalable, client-server
2. **SQLite**: Lightweight, file-based, embedded
3. **JSON files**: Simple, human-readable
4. **NoSQL (MongoDB)**: Flexible schema

### Decision

**We chose SQLite** for execution history and configuration storage.

### Rationale

1. **Single File Database**: Easy to backup, transfer, and version control

2. **No Server Required**: Embedded database, no separate process

3. **Sufficient Performance**: Execution history doesn't require high concurrency

4. **Easy Migration**: Single file can be copied between environments

5. **Relational Model**: Good fit for execution → steps relationship

6. **Zero Configuration**: Works out of the box

### Consequences

**Positive:**
- Simple deployment (no database server)
- Easy backup (copy one file)
- Portable across environments
- Good performance for use case

**Negative:**
- Limited concurrency (single writer)
- Not suitable for multi-user simultaneously writing
- File size can grow (mitigate with cleanup tasks)

**Accepted Trade-off:** Primary use case is single-user execution history, not multi-user concurrent writes.

---

## ADR-005: React 18 with Material-UI for Frontend

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

Frontend needed to provide visual feedback, real-time updates, and modern UX.

**Options:**
1. **Legacy HTML/JS**: Simple, no build step
2. **React**: Component-based, rich ecosystem
3. **Vue**: Simpler learning curve
4. **Svelte**: Smaller bundle size

### Decision

**We chose React 18 + TypeScript** with Material-UI v5.

### Rationale

1. **Component Reusability**: Playbook cards, execution steps, dialogs all reusable

2. **Real-Time Updates**: React's state management works well with WebSocket updates

3. **Type Safety**: TypeScript catches errors at compile time

4. **Material-UI**: Professional-looking components out of the box

5. **Ecosystem**: Large community, many libraries, good documentation

6. **WebSocket Integration**: Easy to integrate with hooks

### Consequences

**Positive:**
- Professional, modern UI
- Type-safe development
- Rich component library (MUI)
- Good WebSocket integration

**Negative:**
- Larger bundle size (~600KB)
- Build step required (Vite)
- More complex than simple HTML

**Accepted Trade-off:** Professional UX is worth the complexity for a production tool.

---

## ADR-006: Zustand for State Management

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

React app needed global state management for theme and WebSocket connection.

**Options:**
1. **Redux**: Powerful, verbose
2. **Context API**: Built-in, simple
3. **Zustand**: Minimal, hooks-based
4. **MobX**: Reactive, less common

### Decision

**We chose Zustand** for global state management.

### Rationale

1. **Minimal Boilerplate**: Define store in a few lines:
   ```typescript
   const useStore = create((set) => ({
     theme: 'dark',
     setTheme: (theme) => set({ theme })
   }))
   ```

2. **Hooks-Based**: Natural fit with React hooks

3. **TypeScript Support**: Excellent type inference

4. **Small Bundle**: Lightweight (< 3KB)

5. **Simple Mental Model**: No actions, reducers, providers - just hooks

### Consequences

**Positive:**
- Easy to learn and use
- Minimal boilerplate
- Good TypeScript support
- Small performance overhead

**Negative:**
- Less common than Redux (smaller community)
- Fewer middleware options

**Accepted Trade-off:** Simplicity over ecosystem size for this use case.

---

## ADR-007: Fernet Encryption for Credentials

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

Credentials (Gateway passwords, Perspective user passwords) must be stored securely at rest.

**Options:**
1. **Plain text**: Simple, insecure
2. **Base64**: Encoding, not encryption
3. **AES**: Secure, complex implementation
4. **Fernet (symmetric)**: Simple, secure
5. **Asymmetric (RSA)**: Complex, overkill

### Decision

**We chose Fernet symmetric encryption** from Python's cryptography library.

### Rationale

1. **Secure**: AES-128 in CBC mode with HMAC authentication

2. **Simple API**: Easy to use:
   ```python
   key = Fernet.generate_key()
   f = Fernet(key)
   encrypted = f.encrypt(b"password")
   decrypted = f.decrypt(encrypted)
   ```

3. **Built-in Authentication**: HMAC prevents tampering

4. **Time-based Tokens**: Can add expiration if needed

5. **Widely Trusted**: Part of Python cryptography library

### Consequences

**Positive:**
- Secure at rest
- Simple implementation
- Authenticated encryption (prevents tampering)
- Well-tested library

**Negative:**
- Symmetric (same key encrypts and decrypts)
- Key must be protected (stored in ~/.ignition-toolkit/)

**Accepted Trade-off:** Symmetric is sufficient for local credential storage.

---

## ADR-008: Playwright for Browser Automation

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

Perspective testing requires browser automation to interact with web UI.

**Options:**
1. **Selenium**: Mature, widely used
2. **Playwright**: Modern, fast, Microsoft-backed
3. **Puppeteer**: Chrome-only, Google-backed
4. **Cypress**: E2E focused, different architecture

### Decision

**We chose Playwright** for browser automation.

### Rationale

1. **Multi-Browser**: Chromium, Firefox, WebKit support (even though we primarily use Chromium)

2. **Modern API**: Async/await, auto-wait for elements

3. **Fast**: Faster than Selenium for most operations

4. **Auto-Wait**: Automatically waits for elements to be ready

5. **Screenshots and Video**: Built-in capture for debugging

6. **Python Support**: First-class Python library (not just Node.js)

### Consequences

**Positive:**
- Fast, reliable browser automation
- Auto-wait reduces flaky tests
- Good Python integration
- Built-in screenshot/video capture

**Negative:**
- Larger installation (downloads browser binaries)
- Newer than Selenium (smaller community)

**Accepted Trade-off**: Modern API and performance worth the larger installation size.

---

## ADR-009: Domain-Specific Step Types (Not Mixed)

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

Step types needed to be organized. Should we have one flat namespace or domain-specific prefixes?

**Option 1: Flat Namespace**
```yaml
steps:
  - type: login          # Ambiguous - Gateway or Perspective?
  - type: navigate
  - type: verify_element
```

**Option 2: Domain Prefixes**
```yaml
steps:
  - type: gateway.login         # Clear: Gateway operation
  - type: perspective.navigate  # Clear: Perspective operation
  - type: perspective.verify_element
```

### Decision

**We chose domain-prefixed step types** (e.g., `gateway.login`, `perspective.navigate`).

### Rationale

1. **Clarity**: No ambiguity about which domain a step belongs to

2. **Namespace Organization**: Easy to see all Gateway steps (`gateway.*`) or Perspective steps (`perspective.*`)

3. **Extensibility**: New domains can be added without naming conflicts

4. **Consistency**: Aligns with domain-separated playbooks (ADR-001)

5. **Documentation**: Easy to document by domain

### Consequences

**Positive:**
- No naming conflicts
- Clear domain ownership
- Easy to filter/search steps by domain
- Self-documenting playbooks

**Negative:**
- Slightly more verbose (type: `gateway.login` vs `login`)

**Accepted Trade-off:** Clarity worth the extra characters.

---

## ADR-010: localStorage for UI Configuration

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

UI needed to persist user preferences (theme, saved playbook configurations, enabled playbooks).

**Options:**
1. **Server-side DB**: Persistent, multi-device
2. **localStorage**: Client-side, simple
3. **Cookies**: Limited size, sent with requests
4. **IndexedDB**: Large storage, complex

### Decision

**We chose localStorage** for UI configuration persistence.

### Rationale

1. **Simple API**: Easy to use:
   ```typescript
   localStorage.setItem('theme', 'dark')
   const theme = localStorage.getItem('theme')
   ```

2. **Sufficient Storage**: ~5-10MB limit, enough for configurations

3. **No Server Required**: Client-side only, works offline

4. **Synchronous**: Simple to integrate (no async complexity)

### Consequences

**Positive:**
- Simple implementation
- Fast access (synchronous)
- No server-side storage needed
- Works offline

**Negative:**
- Per-browser (not synced across devices)
- Cleared when browser data is cleared
- 5-10MB limit

**Accepted Trade-off:** Single-user, single-device use case doesn't need multi-device sync.

---

## ADR-011: FastAPI Lifespan for Robust Startup

**Date:** 2025-10-24
**Status:** Accepted ✅

### Context

The application needs a robust startup system that validates all components before accepting requests, with clear error messages when things go wrong.

**Options:**
1. **Deprecated @app.on_event**: Old pattern, works but deprecated
2. **FastAPI lifespan context manager**: Modern pattern, recommended
3. **Manual initialization in main()**: No framework integration
4. **Lazy initialization**: Initialize on first request

### Decision

**We chose FastAPI lifespan context manager** with 5-phase validation.

### Rationale

1. **Modern FastAPI Pattern**: Recommended approach since FastAPI 0.93+
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # Startup
       await validate_environment()
       await initialize_database()
       yield
       # Shutdown
       cleanup()
   ```

2. **Fail-Fast Validation**: Application won't start if critical components fail
   - Phase 1: Environment (Python version, directories, permissions)
   - Phase 2: Database (schema verification)
   - Phase 3: Credential vault (encryption test)
   - Phase 4: Playbook library (non-fatal warning)
   - Phase 5: Frontend build (non-fatal, production only)

3. **Health State Tracking**: Global singleton tracks component health:
   ```python
   health = get_health_state()
   # Overall: healthy/degraded/unhealthy
   # Components: database, vault, playbooks, frontend
   # Errors and warnings collected
   ```

4. **Kubernetes-Style Health Checks**:
   - `/health` - Overall health (200/503)
   - `/health/live` - Liveness probe (always 200)
   - `/health/ready` - Readiness probe (200/503)
   - `/health/detailed` - Component-level details

5. **Recovery Hints**: Exceptions include actionable recovery instructions
   ```python
   raise DatabaseInitError(
       "Database connection failed",
       recovery_hint="Delete data/toolkit.db and restart"
   )
   ```

### Consequences

**Positive:**
- Errors caught at startup, not runtime
- Clear component health visibility
- Standard health check endpoints for monitoring
- Non-critical failures don't block startup (degraded mode)
- Easy debugging with detailed error messages

**Negative:**
- Slightly slower startup (validates everything upfront)
- More complex than lazy initialization

**Accepted Trade-off:** Reliability over startup speed.

---

## Summary of Key Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | Domain-separated playbooks | Simpler execution model, clearer organization |
| ADR-002 | YAML for playbooks | Human-readable, easy to duplicate and modify |
| ADR-003 | Native Python (no Docker) | Simpler deployment, faster development |
| ADR-004 | SQLite for storage | Single-file, portable, zero configuration |
| ADR-005 | React 18 + Material-UI | Modern UX, component reusability, TypeScript |
| ADR-006 | Zustand state management | Minimal boilerplate, hooks-based, lightweight |
| ADR-007 | Fernet encryption | Secure, simple API, authenticated encryption |
| ADR-008 | Playwright automation | Modern API, fast, auto-wait, Python support |
| ADR-009 | Domain-prefixed step types | Clear namespace, no conflicts, self-documenting |
| ADR-010 | localStorage for UI config | Simple, fast, sufficient for single-user use |
| ADR-011 | FastAPI lifespan startup | Fail-fast validation, health monitoring, modern pattern |

---

**For questions about these decisions, see [PROJECT_GOALS.md](/PROJECT_GOALS.md) for context.**
