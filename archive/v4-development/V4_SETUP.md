# V4 Development Environment Setup

**Branch:** `v4-portability`
**Directory:** `/git/ignition-playground-v4`
**Port:** 5001 (v3 uses 5000)
**Status:** Development Branch - DO NOT USE IN PRODUCTION

---

## Quick Start

### 1. Install Dependencies

```bash
cd /git/ignition-playground-v4

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd frontend
npm install
npm run build
cd ..

# Set Playwright browsers path (v4-specific)
export PLAYWRIGHT_BROWSERS_PATH=/git/ignition-playground-v4/data/.playwright-browsers
python -m playwright install chromium
```

### 2. Start Development Server

```bash
cd /git/ignition-playground-v4
source venv/bin/activate

# Start on port 5001
python tasks.py dev
```

**Access:** http://localhost:5001

---

## What's Different from v3?

| Aspect | v3 (master) | v4 (v4-portability) |
|--------|-------------|---------------------|
| Directory | `/git/ignition-playground` | `/git/ignition-playground-v4` |
| Branch | `master` | `v4-portability` |
| Port | 5000 | 5001 |
| Virtual Env | `ignition-playground/venv/` | `ignition-playground-v4/venv/` |
| Browsers | `ignition-playground/data/.playwright-browsers/` | `ignition-playground-v4/data/.playwright-browsers/` |
| Credentials | `~/.ignition-toolkit/` | `~/.ignition-toolkit/` (SHARED) |

---

## Development Phases

### Phase 1: Critical Security Fixes (4-5 hours)
- [ ] Fix path traversal vulnerability in playbooks API
- [ ] Sandbox Python execution in utility.python
- [ ] Fix hardcoded paths in shell scripts

### Phase 2: Full Portability (6-8 hours)
- [ ] Fix hardcoded paths in frontend
- [ ] Add /api/config endpoint
- [ ] Create portable archive script
- [ ] Add verify command
- [ ] Create portability tests

### Phase 3: Simplified Playbook Management (4-6 hours)
- [ ] Add playbook origin tracking
- [ ] Add duplicate API
- [ ] Update frontend UI

### Phase 4: Security Hardening (2-3 hours)
- [ ] Input validation
- [ ] Restrict filesystem access
- [ ] Rate limiting

### Phase 5: Documentation (2-3 hours)
- [ ] Update README
- [ ] Add security tests
- [ ] User guide

---

## Running v3 and v4 Side-by-Side

**Terminal 1 - v3 (Stable):**
```bash
cd /git/ignition-playground
source venv/bin/activate
python tasks.py dev
# http://localhost:5000
```

**Terminal 2 - v4 (Development):**
```bash
cd /git/ignition-playground-v4
source venv/bin/activate
python tasks.py dev
# http://localhost:5001
```

---

## Git Workflow

### Daily Development

```bash
cd /git/ignition-playground-v4

# Make changes
# ... edit files ...

# Commit to v4 branch
git add .
git commit -m "v4: Description of change"

# Push v4 branch
git push origin v4-portability
```

### Switching Between v3 and v4

**No need to switch!** They're separate directories. Just `cd` to the one you want:

```bash
cd /git/ignition-playground      # Work on v3
cd /git/ignition-playground-v4   # Work on v4
```

### Cherry-Picking Urgent Fixes

If you need to apply a v4 fix to v3:

```bash
# In v4, note the commit hash
cd /git/ignition-playground-v4
git log -1
# commit abc123...

# Switch to v3 and cherry-pick
cd /git/ignition-playground
git cherry-pick abc123
```

---

## When Development is Complete

### Merge v4 → master

```bash
cd /git/ignition-playground

# Ensure v3 is clean
git status

# Merge v4 branch
git merge v4-portability

# Resolve conflicts if any
# ... resolve ...

# Test merged version
python tasks.py install
python tasks.py dev

# Tag as v4.0.0
git tag v4.0.0
git push origin master
git push origin v4.0.0
```

### Cleanup Worktree

```bash
cd /git/ignition-playground
git worktree remove ../ignition-playground-v4

# Optionally delete branch (or keep for reference)
# git branch -d v4-portability
```

---

## Troubleshooting

### Port Already in Use

If port 5001 is taken, edit `.env`:
```bash
API_PORT=5002  # Or any free port
```

### Credentials Conflicts

v3 and v4 share `~/.ignition-toolkit/` credentials. This is intentional for development convenience. If you need separate credentials:

```bash
export IGNITION_TOOLKIT_DATA=/tmp/v4-credentials
```

### Frontend Not Building

```bash
cd /git/ignition-playground-v4/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## Important Notes

1. **Never commit to master from v4 directory** - Always commit to v4-portability branch
2. **Keep v3 stable** - Don't make changes in `/git/ignition-playground` during v4 development
3. **Test both versions** - Run side-by-side to ensure compatibility
4. **Security first** - Complete Phase 1 (security fixes) before other phases

---

## Next Steps

1. ✅ Environment created
2. ⏳ Install dependencies (see Quick Start above)
3. ⏳ Begin Phase 1: Security Fixes
4. ⏳ Test changes
5. ⏳ Continue through phases
6. ⏳ Merge when ready

**Ready to start Phase 1!**
