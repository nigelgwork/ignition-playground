# Issues to Fix - ExecutionDetail & Playbook UI

## Issue #1: Show All Steps Before Execution
**Status:** Not Started
**Location:** `frontend/src/pages/ExecutionDetail.tsx` (line 280-321)

**Problem:** Steps only show after they've executed. Need to show all planned steps upfront.

**Solution:**
1. Add `playbook_steps: List[StepInfo]` to `ExecutionStatusResponse` in `ignition_toolkit/api/app.py` line 169
2. Populate from playbook when creating execution
3. Update frontend types in `frontend/src/types/api.ts`
4. Modify ExecutionDetail.tsx to show all steps with "pending" status initially
5. Update steps as they execute

**Code Changes Needed:**
- Backend: Add playbook steps to execution response
- Frontend: Display all steps from start, update status as execution progresses

---

## Issue #2: Add Live Runtime Display
**Status:** Not Started
**Location:** `frontend/src/pages/ExecutionDetail.tsx` (line 271-276)

**Problem:** No runtime counter showing how long execution has been running.

**Solution:**
1. Add `useEffect` hook to calculate elapsed time from `started_at`
2. Update every second
3. Display in "Step Progress" heading like: "Step Progress (Running for 1m 23s)"

**Code Changes Needed:**
```typescript
const [elapsedTime, setElapsedTime] = useState('');

useEffect(() => {
  if (!execution?.started_at || execution.status !== 'running') return;

  const interval = setInterval(() => {
    const now = new Date();
    const start = new Date(execution.started_at);
    const diff = Math.floor((now.getTime() - start.getTime()) / 1000);
    const minutes = Math.floor(diff / 60);
    const seconds = diff % 60;
    setElapsedTime(`${minutes}m ${seconds}s`);
  }, 1000);

  return () => clearInterval(interval);
}, [execution?.started_at, execution?.status]);
```

---

## Issue #3: Live Browser View Not Showing ✅ **IDENTIFIED**
**Status:** Root Cause Found
**Location:** `ignition_toolkit/api/app.py` (line 1115-1120)

**Problem:** Backend sends `execution_id` (snake_case) but frontend expects `executionId` (camelCase).

**Solution:**
Change line 1117 in `ignition_toolkit/api/app.py`:
```python
"data": {
    "executionId": execution_id,  # Changed from execution_id
    "screenshot": screenshot_b64,
    "timestamp": datetime.now().isoformat()
}
```

---

## Issue #4: Can't Clear Manual Playbook Config Overrides
**Status:** Not Started
**Location:** `frontend/src/components/PlaybookCard.tsx` & `frontend/src/pages/Playbooks.tsx`

**Problem:** When you configure a playbook manually, the green "Configured" box persists and there's no way to clear it to use global credentials again.

**Solution:**
1. Add a "Clear Config" button/icon to the green configured box
2. Clear localStorage for that playbook: `localStorage.removeItem(`playbook_config_${playbook.path}`)`
3. Refresh the saved config preview

**Code Changes Needed:**
In PlaybookCard.tsx around line 268-281, add a clear button:
```typescript
<Box sx={{ mt: 1, mb: 2, p: 1, bgcolor: 'success.dark', borderRadius: 1, border: '1px solid', borderColor: 'success.main' }}>
  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <Typography variant="caption" color="success.light" fontWeight="bold">
      ✓ Configured
    </Typography>
    <IconButton
      size="small"
      onClick={() => {
        localStorage.removeItem(`playbook_config_${playbook.path}`);
        setSavedConfig(null);
      }}
      sx={{ color: 'success.light' }}
    >
      <ClearIcon fontSize="small" />
    </IconButton>
  </Box>
  {/* ... rest of config display ... */}
</Box>
```

---

## Issue #5: Disabled Playbooks Not Greyed Out
**Status:** New Issue
**Location:** `frontend/src/components/PlaybookCard.tsx` (line 118-138)

**Problem:** After moving enable/disable to menu, the visual styling for disabled playbooks was removed.

**Solution:**
The `isDisabled` variable on line 95 now uses `!playbook.enabled` instead of the old manual localStorage toggle. The styling at line 124 should still work:
```typescript
opacity: isDisabled ? 0.6 : 1,
```

**Verification Needed:** Check if `playbook.enabled` is being properly read from the API metadata. The greyed out styling should still be applied.

---

## Priority Order:
1. **Issue #3** (Quick fix - change one line) ✅
2. **Issue #5** (Verify existing code works)
3. **Issue #4** (Add clear button)
4. **Issue #2** (Add runtime counter)
5. **Issue #1** (Most complex - requires backend + frontend changes)

---

**Date Created:** 2025-10-24
**Created By:** Claude Code
