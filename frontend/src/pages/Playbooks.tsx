/**
 * Playbooks page - List and execute playbooks organized by category
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  DragIndicator as DragIcon,
  Add as AddIcon,
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

// Categorize playbooks by domain field (preferred) or path (fallback)
function categorizePlaybooks(playbooks: PlaybookInfo[]) {
  const gateway: PlaybookInfo[] = [];
  const designer: PlaybookInfo[] = [];
  const perspective: PlaybookInfo[] = [];

  playbooks.forEach((playbook) => {
    // Prefer domain field from YAML metadata
    if (playbook.domain) {
      if (playbook.domain === 'gateway') {
        gateway.push(playbook);
      } else if (playbook.domain === 'designer') {
        designer.push(playbook);
      } else if (playbook.domain === 'perspective') {
        perspective.push(playbook);
      } else {
        // Unknown domain, fall back to path
        categorizeByPath(playbook);
      }
    } else {
      // No domain field, fall back to path
      categorizeByPath(playbook);
    }

    function categorizeByPath(pb: PlaybookInfo) {
      if (pb.path.includes('gateway/')) {
        gateway.push(pb);
      } else if (pb.path.includes('designer/')) {
        designer.push(pb);
      } else if (pb.path.includes('perspective/') || pb.path.includes('browser/')) {
        perspective.push(pb);
      } else {
        // Default to gateway if unclear
        gateway.push(pb);
      }
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
  const [dragEnabled, setDragEnabled] = useState(false);
  const [stepsDialogPlaybook, setStepsDialogPlaybook] = useState<PlaybookInfo | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newPlaybookName, setNewPlaybookName] = useState('');
  const [newPlaybookDescription, setNewPlaybookDescription] = useState('');
  const [newPlaybookDomain, setNewPlaybookDomain] = useState<'gateway' | 'perspective' | 'designer'>('gateway');

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

    // Clean up saved configurations for deleted playbooks
    if (playbooks.length > 0) {
      const validPaths = new Set(playbooks.map(p => p.path));
      const keysToRemove: string[] = [];

      // Find all localStorage keys for playbook configurations
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith('playbook_config_') || key?.startsWith('playbook_debug_') || key?.startsWith('playbook_order_')) {
          // Extract playbook path from key
          if (key.startsWith('playbook_config_')) {
            const playbookPath = key.replace('playbook_config_', '');
            if (!validPaths.has(playbookPath)) {
              keysToRemove.push(key);
              // Also remove associated debug mode setting
              keysToRemove.push(`playbook_debug_${playbookPath}`);
            }
          }
        }
      }

      // Remove invalid configurations
      keysToRemove.forEach(key => {
        localStorage.removeItem(key);
        console.log(`Removed stale configuration: ${key}`);
      });

      if (keysToRemove.length > 0) {
        console.log(`Cleaned up ${keysToRemove.length} stale playbook configurations`);
      }
    }
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
    // v3.45.2 - Non-blocking execution with immediate navigation
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
      console.log('Executing playbook with credential:', {
        playbook_path: playbook.path,
        credential_name: selectedCredential.name,
        gateway_url: selectedCredential.gateway_url,
        debug_mode,
      });

      // Start execution (don't await - let it run in background)
      api.executions.start({
        playbook_path: playbook.path,
        parameters: {}, // Backend will auto-fill from credential
        gateway_url: selectedCredential.gateway_url,
        credential_name: selectedCredential.name,
        debug_mode,
      }).then(response => {
        console.log('Execution started successfully:', response);
        // Navigate to execution detail page AFTER getting execution ID
        window.location.href = `/executions/${response.execution_id}`;
      }).catch(error => {
        console.error('Failed to execute playbook:', error);
        console.error('Error details:', error instanceof Error ? error.message : String(error));
        if (error && typeof error === 'object' && 'data' in error) {
          console.error('Error data:', (error as any).data);
        }
        alert(`Failed to start execution: ${error instanceof Error ? error.message : String(error)}\n\nCheck console for details.`);
      });

      // Return immediately without waiting - navigation will happen when API responds
      return;
    }

    if (!savedConfigStr) {
      // No saved config and no global credential - open configure dialog
      setSelectedPlaybook(playbook);
      return;
    }

    // If we have saved config but no credential, open configure dialog
    if (!selectedCredential) {
      setSelectedPlaybook(playbook);
      return;
    }

    try {
      const savedConfig = JSON.parse(savedConfigStr);

      // Convert boolean string values to actual booleans
      const convertedParams: Record<string, any> = {};
      for (const [key, value] of Object.entries(savedConfig.parameters || {})) {
        // Find the parameter definition
        const paramDef = playbook.parameters.find(p => p.name === key);
        if (paramDef?.type === 'boolean') {
          // Convert string 'true'/'false' to boolean
          convertedParams[key] = value === 'true' || value === true;
        } else {
          convertedParams[key] = value;
        }
      }

      // Execute with saved config parameters + global credential (don't await - navigate when ready)
      api.executions.start({
        playbook_path: playbook.path,
        parameters: convertedParams, // Use converted params (boolean types fixed)
        gateway_url: selectedCredential.gateway_url, // Always use global credential's gateway_url
        credential_name: selectedCredential.name, // Always use global credential
        debug_mode,
      }).then(response => {
        // Navigate to execution detail page AFTER getting execution ID
        window.location.href = `/executions/${response.execution_id}`;
      }).catch(error => {
        console.error('Failed to execute playbook:', error);
        alert('Failed to start execution. Please check the console for details.');
      });
    } catch (error) {
      console.error('Failed to parse saved config:', error);
      alert('Failed to load saved configuration. Please try again.');
    }
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

  const handleExport = async (playbook: PlaybookInfo) => {
    try {
      // Fetch full playbook export with YAML content
      const exportData = await api.playbooks.export(playbook.path);

      // Create download link
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${playbook.name.replace(/\s+/g, '_')}_export.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      alert(`Failed to export playbook: ${(error as Error).message}`);
    }
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e: Event) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = async (event) => {
          try {
            const data = JSON.parse(event.target?.result as string);

            // Validate export format
            if (!data.yaml_content || !data.name || !data.domain) {
              alert('Invalid export file: missing required fields (yaml_content, name, domain)');
              return;
            }

            // Confirm import
            const confirmImport = window.confirm(
              `Import playbook "${data.name}"?\n\n` +
              `Domain: ${data.domain}\n` +
              `Version: ${data.version}\n\n` +
              `This will create a new playbook in your playbooks/${data.domain}/ directory.`
            );

            if (!confirmImport) return;

            // Import playbook
            const result = await api.playbooks.import(
              data.name,
              data.domain,
              data.yaml_content,
              false // Don't overwrite by default
            );

            alert(`Success! Playbook imported to:\n${result.path}\n\nRefreshing playbook list...`);

            // Refresh playbook list
            window.location.reload();
          } catch (error) {
            alert(`Failed to import playbook: ${(error as Error).message}`);
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  const handleCreatePlaybook = async () => {
    if (!newPlaybookName.trim()) {
      alert('Please enter a playbook name');
      return;
    }

    // Create basic playbook template
    const yamlTemplate = `name: "${newPlaybookName}"
version: "1.0"
description: "${newPlaybookDescription || 'New playbook'}"
domain: ${newPlaybookDomain}

parameters:
  - name: gateway_url
    type: string
    required: true
    description: "Gateway URL (e.g., http://localhost:8088)"

  - name: username
    type: string
    required: true
    description: "Gateway admin username"

  - name: password
    type: string
    required: true
    description: "Gateway admin password"

steps:
  # Add your steps here
  - id: step1
    name: "Example Step"
    type: utility.sleep
    parameters:
      seconds: 1
    timeout: 10
    on_failure: abort

metadata:
  author: "User"
  category: "${newPlaybookDomain}"
  tags: ["custom"]
`;

    try {
      const result = await api.playbooks.create(
        newPlaybookName,
        newPlaybookDomain,
        yamlTemplate
      );

      alert(`Success! Playbook created at:\n${result.path}\n\nRefreshing playbook list...`);

      // Reset form
      setNewPlaybookName('');
      setNewPlaybookDescription('');
      setNewPlaybookDomain('gateway');
      setCreateDialogOpen(false);

      // Refresh playbook list
      window.location.reload();
    } catch (error) {
      alert(`Failed to create playbook: ${(error as Error).message}`);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5, py: 0.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2 }}>
          <Typography variant="h5" sx={{ fontSize: '1.3rem' }}>
            Playbooks
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
            Select a playbook to configure and execute
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Create a new playbook from template">
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
              size="small"
              color="primary"
            >
              Create New
            </Button>
          </Tooltip>

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

          <Tooltip title="Import playbook from JSON export">
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
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: '32px !important', '& .MuiAccordionSummary-content': { my: '6px !important' } }}>
              <Typography variant="h6" sx={{ fontSize: '1.1rem' }}>🔧 Gateway ({gatewayPlaybooks.length})</Typography>
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
                          lg: 'repeat(3, 1fr)',
                          xl: 'repeat(4, 1fr)',
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
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: '32px !important', '& .MuiAccordionSummary-content': { my: '6px !important' } }}>
              <Typography variant="h6" sx={{ fontSize: '1.1rem' }}>🎨 Designer ({designerPlaybooks.length})</Typography>
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
                          lg: 'repeat(3, 1fr)',
                          xl: 'repeat(4, 1fr)',
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
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: '32px !important', '& .MuiAccordionSummary-content': { my: '6px !important' } }}>
              <Typography variant="h6" sx={{ fontSize: '1.1rem' }}>📱 Perspective ({perspectivePlaybooks.length})</Typography>
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
                          lg: 'repeat(3, 1fr)',
                          xl: 'repeat(4, 1fr)',
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
      />

      {/* Steps dialog */}
      <PlaybookStepsDialog
        open={stepsDialogPlaybook !== null}
        playbook={stepsDialogPlaybook}
        onClose={() => setStepsDialogPlaybook(null)}
      />

      {/* Create New Playbook Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Playbook</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Playbook Name"
              value={newPlaybookName}
              onChange={(e) => setNewPlaybookName(e.target.value)}
              fullWidth
              required
              variant="outlined"
              helperText="Give your playbook a descriptive name"
            />
            <TextField
              label="Description"
              value={newPlaybookDescription}
              onChange={(e) => setNewPlaybookDescription(e.target.value)}
              fullWidth
              multiline
              rows={2}
              variant="outlined"
              helperText="Describe what this playbook does"
            />
            <FormControl fullWidth>
              <InputLabel>Domain</InputLabel>
              <Select
                value={newPlaybookDomain}
                onChange={(e) => setNewPlaybookDomain(e.target.value as 'gateway' | 'perspective' | 'designer')}
                label="Domain"
              >
                <MenuItem value="gateway">Gateway</MenuItem>
                <MenuItem value="perspective">Perspective</MenuItem>
                <MenuItem value="designer">Designer</MenuItem>
              </Select>
            </FormControl>
            <Alert severity="info">
              A basic playbook template will be created with standard parameters and a sample step.
              You can edit the YAML file after creation to add your own steps.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleCreatePlaybook}
            variant="contained"
            disabled={!newPlaybookName.trim()}
          >
            Create Playbook
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
}
