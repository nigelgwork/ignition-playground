/**
 * Playbooks page - List and execute playbooks organized by category
 */

import { useState } from 'react';
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
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { PlaybookCard } from '../components/PlaybookCard';
import { PlaybookExecutionDialog } from '../components/PlaybookExecutionDialog';
import type { PlaybookInfo } from '../types/api';

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

  return { gateway, designer, perspective };
}

export function Playbooks() {
  const [selectedPlaybook, setSelectedPlaybook] = useState<PlaybookInfo | null>(null);
  const [executionStarted, setExecutionStarted] = useState(false);
  const [lastExecutionId, setLastExecutionId] = useState<string>('');

  // Fetch playbooks
  const { data: playbooks = [], isLoading, error } = useQuery<PlaybookInfo[]>({
    queryKey: ['playbooks'],
    queryFn: api.playbooks.list,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const handleConfigure = (playbook: PlaybookInfo) => {
    setSelectedPlaybook(playbook);
  };

  const handleExecute = (playbook: PlaybookInfo) => {
    // For now, execute opens the configure dialog
    // In the future, this could use saved configurations
    setSelectedPlaybook(playbook);
  };

  const handleExecutionStarted = (executionId: string) => {
    setLastExecutionId(executionId);
    setExecutionStarted(true);
  };

  // Categorize playbooks
  const categories = categorizePlaybooks(playbooks);

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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Playbooks
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Select a playbook to configure and execute
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
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
              <Typography variant="h6">🔧 Gateway ({categories.gateway.length})</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {categories.gateway.length > 0 ? (
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: {
                      xs: '1fr',
                      sm: 'repeat(2, 1fr)',
                      md: 'repeat(3, 1fr)',
                    },
                    gap: 3,
                  }}
                >
                  {categories.gateway.map((playbook) => (
                    <PlaybookCard
                      key={playbook.path}
                      playbook={playbook}
                      onConfigure={handleConfigure}
                      onExecute={handleExecute}
                      onExport={handleExport}
                    />
                  ))}
                </Box>
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
              <Typography variant="h6">🎨 Designer ({categories.designer.length})</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {categories.designer.length > 0 ? (
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: {
                      xs: '1fr',
                      sm: 'repeat(2, 1fr)',
                      md: 'repeat(3, 1fr)',
                    },
                    gap: 3,
                  }}
                >
                  {categories.designer.map((playbook) => (
                    <PlaybookCard
                      key={playbook.path}
                      playbook={playbook}
                      onConfigure={handleConfigure}
                      onExecute={handleExecute}
                      onExport={handleExport}
                    />
                  ))}
                </Box>
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
              <Typography variant="h6">📱 Perspective ({categories.perspective.length})</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {categories.perspective.length > 0 ? (
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: {
                      xs: '1fr',
                      sm: 'repeat(2, 1fr)',
                      md: 'repeat(3, 1fr)',
                    },
                    gap: 3,
                  }}
                >
                  {categories.perspective.map((playbook) => (
                    <PlaybookCard
                      key={playbook.path}
                      playbook={playbook}
                      onConfigure={handleConfigure}
                      onExecute={handleExecute}
                      onExport={handleExport}
                    />
                  ))}
                </Box>
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
