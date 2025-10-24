# Visual Feedback Implementation Plan

**Goal**: Live browser streaming for Perspective playbooks + visual feedback for Gateway playbooks

**Benchmark Results**:
- JPEG 80% quality: 38 KB/frame
- 2 FPS streaming: 102 KB/s bandwidth
- Playwright can handle 13+ FPS easily

---

## Files to Modify

### Backend (Python)

1. **`ignition_toolkit/browser/manager.py`**
   - Add `start_screenshot_streaming()` method
   - Add `stop_screenshot_streaming()` method
   - Add screenshot streaming task that captures at 2 FPS
   - Send screenshots via WebSocket

2. **`ignition_toolkit/playbook/engine.py`**
   - Add execution state management (pause/resume/skip)
   - Connect browser streaming to execution lifecycle
   - Add pause/resume/skip control methods

3. **`ignition_toolkit/api/app.py`**
   - Add POST `/api/executions/{id}/pause` endpoint
   - Add POST `/api/executions/{id}/resume` endpoint
   - Add POST `/api/executions/{id}/skip` endpoint
   - Add POST `/api/executions/{id}/stop` endpoint
   - Enhance WebSocket to broadcast screenshot frames

4. **`ignition_toolkit/api/websocket.py`** (if exists, or add to app.py)
   - Add `screenshot_frame` message type
   - Add `execution_paused` message type
   - Add `execution_resumed` message type

### Frontend (React + TypeScript)

5. **`frontend/src/components/LiveBrowserView.tsx`** (NEW)
   - Component to display live browser screenshots
   - WebSocket listener for screenshot frames
   - FPS counter (debug mode)

6. **`frontend/src/components/ExecutionControls.tsx`** (NEW)
   - Pause/Resume/Skip/Stop buttons
   - API calls to control endpoints

7. **`frontend/src/pages/ExecutionDetail.tsx`** (NEW or modify existing)
   - Split-pane layout
   - Left: Step list
   - Right: Live browser view OR Gateway operation display

8. **`frontend/src/api/client.ts`**
   - Add `executions.pause(id)` method
   - Add `executions.resume(id)` method
   - Add `executions.skip(id)` method
   - Add `executions.stop(id)` method

---

## Implementation Phases

### Phase 1: Backend Screenshot Streaming (3-4 hours)
✅ Research complete - benchmark shows feasibility
- Modify `BrowserManager` to support streaming
- Add streaming control to playbook engine
- Test standalone (without frontend)

### Phase 2: Backend Execution Controls (2 hours)
- Add pause/resume/skip endpoints
- Add state management to execution engine
- Test with CLI/Postman

### Phase 3: Frontend Components (3-4 hours)
- Create LiveBrowserView component
- Create ExecutionControls component
- Test WebSocket screenshot reception

### Phase 4: Frontend Integration (2-3 hours)
- Redesign Executions page
- Wire up controls
- End-to-end testing

### Phase 5: Testing & Polish (2-3 hours)
- Test with Gateway playbook (visual indicators)
- Test with Perspective playbook (browser streaming)
- Performance optimization
- Documentation

**Total Estimated Time**: 12-16 hours

---

## Next Step

Proceed with Phase 1: Backend Screenshot Streaming

This will modify:
1. `browser/manager.py` - Add streaming capability
2. `playbook/engine.py` - Connect streaming to execution
3. `api/app.py` - Enhance WebSocket messages

Ready to proceed?
