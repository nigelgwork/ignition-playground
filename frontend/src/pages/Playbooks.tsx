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
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
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

  const handleExecutionStarted = (executionId: string) => {
    setLastExecutionId(executionId);
    setExecutionStarted(true);
  };

  // Categorize playbooks
  const categories = categorizePlaybooks(playbooks);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Playbooks
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Select a playbook to configure and execute
      </Typography>

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
      {!isLoading && !error && playbooks.length > 0 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Gateway Section */}
          {categories.gateway.length > 0 && (
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">🔧 Gateway ({categories.gateway.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
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
                    <PlaybookCard key={playbook.path} playbook={playbook} onConfigure={handleConfigure} />
                  ))}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Designer Section */}
          {categories.designer.length > 0 && (
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">🎨 Designer ({categories.designer.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
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
                    <PlaybookCard key={playbook.path} playbook={playbook} onConfigure={handleConfigure} />
                  ))}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Perspective Section */}
          {categories.perspective.length > 0 && (
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">📱 Perspective ({categories.perspective.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
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
                    <PlaybookCard key={playbook.path} playbook={playbook} onConfigure={handleConfigure} />
                  ))}
                </Box>
              </AccordionDetails>
            </Accordion>
          )}
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
