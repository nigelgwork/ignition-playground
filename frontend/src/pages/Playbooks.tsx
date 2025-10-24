/**
 * Playbooks page - List and execute playbooks organized by category
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Alert,
  CircularProgress,
  Snackbar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  DragIndicator as DragIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { api } from '../api/client';
import { PlaybookCard } from '../components/PlaybookCard';
import { PlaybookExecutionDialog } from '../components/PlaybookExecutionDialog';
import { PlaybookStepsDialog } from '../components/PlaybookStepsDialog';
import { useStore } from '../store';
import type { PlaybookInfo } from '../types/api';

// Sortable playbook card wrapper
function SortablePlaybookCard({ playbook, onConfigure, onExecute, onExport, onViewSteps, dragEnabled }: {
  playbook: PlaybookInfo;
  onConfigure: (playbook: PlaybookInfo) => void;
  onExecute?: (playbook: PlaybookInfo) => void;
  onExport?: (playbook: PlaybookInfo) => void;
  onViewSteps?: (playbook: PlaybookInfo) => void;
  dragEnabled: boolean;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: playbook.path, disabled: !dragEnabled });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    cursor: dragEnabled ? 'grab' : 'default',
  };

  return (
    <div ref={setNodeRef} style={style} {...(dragEnabled ? attributes : {})} {...(dragEnabled ? listeners : {})}>
      <PlaybookCard
        playbook={playbook}
        onConfigure={onConfigure}
        onExecute={onExecute}
        onExport={onExport}
        onViewSteps={onViewSteps}
      />
    </div>
  );
}

// Load custom order from localStorage
function getPlaybookOrder(category: string): string[] {
  const stored = localStorage.getItem(`playbook_order_${category}`);
  return stored ? JSON.parse(stored) : [];
}

// Save custom order to localStorage
function savePlaybookOrder(category: string, order: string[]) {
  localStorage.setItem(`playbook_order_${category}`, JSON.stringify(order));
}

// Apply saved order to playbooks
function applyOrder(playbooks: PlaybookInfo[], category: string): PlaybookInfo[] {
  const savedOrder = getPlaybookOrder(category);
  if (savedOrder.length === 0) return playbooks;

  // Create a map for quick lookup
  const playbookMap = new Map(playbooks.map(p => [p.path, p]));

  // First, add playbooks in saved order
  const ordered: PlaybookInfo[] = [];
  savedOrder.forEach(path => {
    const playbook = playbookMap.get(path);
    if (playbook) {
      ordered.push(playbook);
      playbookMap.delete(path);
    }
  });

  // Then add any new playbooks that weren't in the saved order
  playbookMap.forEach(playbook => ordered.push(playbook));

  return ordered;
}

// Categorize playbooks by path
function categorizePlaybooks(playbooks: PlaybookInfo[]) {
  const gateway: PlaybookInfo[] = [];
  const designer: PlaybookInfo[] = [];
  const perspective: PlaybookInfo[] = [];

  playbooks.forEach((playbook) => {
    if (playbook.path.includes('/gateway/')) {
      gateway.push(playbook);
    } else if (playbook.path.includes('/designer/')) {
      designer.push(playbook);
    } else if (playbook.path.includes('/perspective/') || playbook.path.includes('/browser/')) {
      perspective.push(playbook);
    } else {
      // Default to gateway if unclear
      gateway.push(playbook);
    }
  });

  // Apply saved order to each category
  return {
    gateway: applyOrder(gateway, 'gateway'),
    designer: applyOrder(designer, 'designer'),
    perspective: applyOrder(perspective, 'perspective'),
  };
}

export function Playbooks() {
  const [selectedPlaybook, setSelectedPlaybook] = useState<PlaybookInfo | null>(null);
  const [executionStarted, setExecutionStarted] = useState(false);
  const [lastExecutionId, setLastExecutionId] = useState<string>('');
  const [dragEnabled, setDragEnabled] = useState(false);
  const [stepsDialogPlaybook, setStepsDialogPlaybook] = useState<PlaybookInfo | null>(null);

  // Fetch playbooks
  const { data: playbooks = [], isLoading, error } = useQuery<PlaybookInfo[]>({
    queryKey: ['playbooks'],
    queryFn: api.playbooks.list,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Categorize playbooks
  const categories = categorizePlaybooks(playbooks);

  // State for each category to enable re-rendering on drag
  const [gatewayPlaybooks, setGatewayPlaybooks] = useState(categories.gateway);
  const [designerPlaybooks, setDesignerPlaybooks] = useState(categories.designer);
  const [perspectivePlaybooks, setPerspectivePlaybooks] = useState(categories.perspective);

  // Update state when playbooks change
  useEffect(() => {
    setGatewayPlaybooks(categories.gateway);
    setDesignerPlaybooks(categories.designer);
    setPerspectivePlaybooks(categories.perspective);
  }, [playbooks]);

  // Configure drag sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleConfigure = (playbook: PlaybookInfo) => {
    setSelectedPlaybook(playbook);
  };

  const handleExecute = async (playbook: PlaybookInfo) => {
    // Get global selected credential
    const selectedCredential = useStore.getState().selectedCredential;

    // Get saved configuration from localStorage
    const savedConfigKey = `playbook_config_${playbook.path}`;
    const savedConfigStr = localStorage.getItem(savedConfigKey);

    // Get debug mode preference
    const debugModeStr = localStorage.getItem(`playbook_debug_${playbook.path}`);
    const debug_mode = debugModeStr === 'true';

    // If global credential is selected, execute directly with it
    if (selectedCredential && !savedConfigStr) {
      try {
        const response = await api.executions.start({
          playbook_path: playbook.path,
          parameters: {}, // Backend will auto-fill from credential
          gateway_url: selectedCredential.gateway_url,
          credential_name: selectedCredential.name,
          debug_mode,
        });

        // Navigate to execution detail page
        window.location.href = `/executions/${response.execution_id}`;
        return;
      } catch (error) {
        console.error('Failed to execute playbook:', error);
        alert('Failed to start execution. Please check the console for details.');
        return;
      }
    }

    if (!savedConfigStr) {
      // No saved config and no global credential - open configure dialog
      setSelectedPlaybook(playbook);
      return;
    }

    try {
      const savedConfig = JSON.parse(savedConfigStr);

      // Execute directly with saved config
      const response = await api.executions.start({
        playbook_path: playbook.path,
        parameters: savedConfig.parameters,
        gateway_url: savedConfig.gatewayUrl,
        debug_mode,
      });

      // Navigate to execution detail page
      window.location.href = `/executions/${response.execution_id}`;
    } catch (error) {
      console.error('Failed to execute playbook:', error);
      alert('Failed to start execution. Please check the console for details.');
    }
  };

  const handleExecutionStarted = (executionId: string) => {
    setLastExecutionId(executionId);
    setExecutionStarted(true);
  };

  // Drag end handlers for each category
  const handleGatewayDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = gatewayPlaybooks.findIndex(p => p.path === active.id);
      const newIndex = gatewayPlaybooks.findIndex(p => p.path === over.id);
      const newOrder = arrayMove(gatewayPlaybooks, oldIndex, newIndex);
      setGatewayPlaybooks(newOrder);
      savePlaybookOrder('gateway', newOrder.map(p => p.path));
    }
  };

  const handleDesignerDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = designerPlaybooks.findIndex(p => p.path === active.id);
      const newIndex = designerPlaybooks.findIndex(p => p.path === over.id);
      const newOrder = arrayMove(designerPlaybooks, oldIndex, newIndex);
      setDesignerPlaybooks(newOrder);
      savePlaybookOrder('designer', newOrder.map(p => p.path));
    }
  };

  const handlePerspectiveDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = perspectivePlaybooks.findIndex(p => p.path === active.id);
      const newIndex = perspectivePlaybooks.findIndex(p => p.path === over.id);
      const newOrder = arrayMove(perspectivePlaybooks, oldIndex, newIndex);
      setPerspectivePlaybooks(newOrder);
      savePlaybookOrder('perspective', newOrder.map(p => p.path));
    }
  };

  const handleViewSteps = (playbook: PlaybookInfo) => {
    setStepsDialogPlaybook(playbook);
  };

  const handleExport = (playbook: PlaybookInfo) => {
    // Create download link for playbook export
    const exportData = {
      name: playbook.name,
      path: playbook.path,
      version: playbook.version,
      description: playbook.description,
      message: 'To import this playbook, use the Import button and select this JSON file.',
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${playbook.name.replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e: Event) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const data = JSON.parse(event.target?.result as string);
            alert(`Import playbook: ${data.name}\n\nNote: This is a reference. The actual playbook YAML file must be copied to:\n${data.path}\n\nSee documentation for import instructions.`);
          } catch (error) {
            alert('Invalid JSON file');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2 }}>
          <Typography variant="h5">
            Playbooks
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Select a playbook to configure and execute
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={dragEnabled ? "Disable drag mode" : "Enable drag mode to reorder playbooks"}>
            <Button
              variant={dragEnabled ? "contained" : "outlined"}
              startIcon={<DragIcon />}
              onClick={() => setDragEnabled(!dragEnabled)}
              size="small"
              color={dragEnabled ? "success" : "primary"}
            >
              {dragEnabled ? "Drag Mode ON" : "Drag Mode"}
            </Button>
          </Tooltip>

          <Tooltip title="Import playbook reference">
            <Button
              variant="outlined"
              startIcon={<UploadIcon />}
              onClick={handleImport}
              size="small"
            >
              Import
            </Button>
          </Tooltip>

          <Tooltip title="Refresh playbook list">
            <IconButton
              onClick={() => window.location.reload()}
              size="small"
              color="primary"
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Loading state */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress aria-label="Loading playbooks" />
        </Box>
      )}

      {/* Error state */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load playbooks: {(error as Error).message}
        </Alert>
      )}

      {/* Empty state */}
      {!isLoading && !error && playbooks.length === 0 && (
        <Alert severity="info">
          No playbooks found. Add YAML playbooks to the ./playbooks directory.
        </Alert>
      )}

      {/* Organized Playbook Sections */}
      {!isLoading && !error && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Gateway Section */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">🔧 Gateway ({gatewayPlaybooks.length})</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {gatewayPlaybooks.length > 0 ? (
                <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleGatewayDragEnd}>
                  <SortableContext items={gatewayPlaybooks.map(p => p.path)} strategy={verticalListSortingStrategy}>
                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: {
                          xs: '1fr',
                          sm: 'repeat(2, 1fr)',
                          md: 'repeat(3, 1fr)',
                        },
                        gap: 4,
                      }}
                    >
                      {gatewayPlaybooks.map((playbook) => (
                        <SortablePlaybookCard
                          key={playbook.path}
                          playbook={playbook}
                          onConfigure={handleConfigure}
                          onExecute={handleExecute}
                          onExport={handleExport}
                          onViewSteps={handleViewSteps}
                          dragEnabled={dragEnabled}
                        />
                      ))}
                    </Box>
                  </SortableContext>
                </DndContext>
              ) : (
                <Alert severity="info">
                  No Gateway playbooks found. Add YAML playbooks to ./playbooks/gateway/
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Designer Section - Always shown */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">🎨 Designer ({designerPlaybooks.length})</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {designerPlaybooks.length > 0 ? (
                <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDesignerDragEnd}>
                  <SortableContext items={designerPlaybooks.map(p => p.path)} strategy={verticalListSortingStrategy}>
                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: {
                          xs: '1fr',
                          sm: 'repeat(2, 1fr)',
                          md: 'repeat(3, 1fr)',
                        },
                        gap: 4,
                      }}
                    >
                      {designerPlaybooks.map((playbook) => (
                        <SortablePlaybookCard
                          key={playbook.path}
                          playbook={playbook}
                          onConfigure={handleConfigure}
                          onExecute={handleExecute}
                          onExport={handleExport}
                          onViewSteps={handleViewSteps}
                          dragEnabled={dragEnabled}
                        />
                      ))}
                    </Box>
                  </SortableContext>
                </DndContext>
              ) : (
                <Alert severity="info">
                  No Designer playbooks found. Add YAML playbooks to ./playbooks/designer/
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>

          {/* Perspective Section */}
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">📱 Perspective ({perspectivePlaybooks.length})</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {perspectivePlaybooks.length > 0 ? (
                <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handlePerspectiveDragEnd}>
                  <SortableContext items={perspectivePlaybooks.map(p => p.path)} strategy={verticalListSortingStrategy}>
                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: {
                          xs: '1fr',
                          sm: 'repeat(2, 1fr)',
                          md: 'repeat(3, 1fr)',
                        },
                        gap: 4,
                      }}
                    >
                      {perspectivePlaybooks.map((playbook) => (
                        <SortablePlaybookCard
                          key={playbook.path}
                          playbook={playbook}
                          onConfigure={handleConfigure}
                          onExecute={handleExecute}
                          onExport={handleExport}
                          onViewSteps={handleViewSteps}
                          dragEnabled={dragEnabled}
                        />
                      ))}
                    </Box>
                  </SortableContext>
                </DndContext>
              ) : (
                <Alert severity="info">
                  No Perspective playbooks found. Add YAML playbooks to ./playbooks/perspective/ or ./playbooks/browser/
                </Alert>
              )}
            </AccordionDetails>
          </Accordion>
        </Box>
      )}

      {/* Execution dialog */}
      <PlaybookExecutionDialog
        open={selectedPlaybook !== null}
        playbook={selectedPlaybook}
        onClose={() => setSelectedPlaybook(null)}
        onExecutionStarted={handleExecutionStarted}
      />

      {/* Steps dialog */}
      <PlaybookStepsDialog
        open={stepsDialogPlaybook !== null}
        playbook={stepsDialogPlaybook}
        onClose={() => setStepsDialogPlaybook(null)}
      />

      {/* Success notification */}
      <Snackbar
        open={executionStarted}
        autoHideDuration={6000}
        onClose={() => setExecutionStarted(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setExecutionStarted(false)}
          severity="success"
          sx={{ width: '100%' }}
        >
          Execution started! ID: {lastExecutionId.substring(0, 8)}...
          <br />
          Check the Executions page for real-time updates.
        </Alert>
      </Snackbar>
    </Box>
  );
}
