/**
 * Playbooks page - List and execute playbooks
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  Alert,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { PlaybookCard } from '../components/PlaybookCard';
import { PlaybookExecutionDialog } from '../components/PlaybookExecutionDialog';
import type { PlaybookInfo } from '../types/api';

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

  const handleExecute = (playbook: PlaybookInfo) => {
    setSelectedPlaybook(playbook);
  };

  const handleExecutionStarted = (executionId: string) => {
    setLastExecutionId(executionId);
    setExecutionStarted(true);
  };

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

      {/* Playbook grid */}
      {!isLoading && !error && playbooks.length > 0 && (
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
          {playbooks.map((playbook) => (
            <PlaybookCard key={playbook.path} playbook={playbook} onExecute={handleExecute} />
          ))}
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
