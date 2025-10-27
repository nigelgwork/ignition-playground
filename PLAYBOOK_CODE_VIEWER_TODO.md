# Playbook Code Viewer - Remaining Integration Steps

## Status
- ✅ Backend endpoints created (GET/PUT `/api/executions/{execution_id}/playbook/code`)
- ✅ Frontend component created (`PlaybookCodeViewer.tsx`)
- ✅ API client methods added
- ✅ Component imported into ExecutionDetail
- ⏳ **Need to add UI button and render component in ExecutionDetail**

## What's Left to Do

### In `frontend/src/pages/ExecutionDetail.tsx`:

1. **Add "View Code" button** after the Debug toggle (around line 283):
```tsx
<Tooltip title="View and edit playbook code">
  <Button
    variant="outlined"
    size="small"
    startIcon={<CodeIcon />}
    onClick={() => setShowCodeViewer(!showCodeViewer)}
    sx={{ ml: 1 }}
  >
    {showCodeViewer ? 'Hide Code' : 'View Code'}
  </Button>
</Tooltip>
```

2. **Add PlaybookCodeViewer component** in the main content area (find the split pane/grid layout and add a third column when showCodeViewer is true, or show it below the step list):

```tsx
{showCodeViewer && execution && (
  <Box sx={{ height: '100%', overflow: 'hidden' }}>
    <PlaybookCodeViewer
      executionId={executionId}
      playbookName={execution.playbook_name}
      isDebugMode={debugMode}
      isPaused={execution.status === 'paused'}
      onClose={() => setShowCodeViewer(false)}
    />
  </Box>
)}
```

## Testing Instructions

1. Start a playbook execution
2. Enable debug mode or pause the execution
3. Click "View Code" button
4. Should see playbook YAML source
5. Edit the code
6. Click "Save Changes"
7. Should create a backup and update the playbook file

## Backup Behavior
- Automatic backup created before any changes
- Backup filename format: `playbook_name.backup.YYYYMMDD_HHMMSS.yaml`
- Original file is updated with new content
