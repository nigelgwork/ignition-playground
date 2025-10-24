/**
 * Executions page - View execution history and real-time status
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  Alert,
  CircularProgress,
  Stack,
  ToggleButtonGroup,
  ToggleButton,
  Snackbar,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { ExecutionCard } from '../components/ExecutionCard';
import { useStore } from '../store';
import type { ExecutionStatusResponse } from '../types/api';

type StatusFilter = 'all' | 'running' | 'paused' | 'completed' | 'failed';

export function Executions() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const executionUpdates = useStore((state) => state.executionUpdates);

  // Fetch executions from API
  const { data: executions = [], isLoading, error } = useQuery<ExecutionStatusResponse[]>({
    queryKey: ['executions'],
    queryFn: () => api.executions.list({ limit: 50 }),
    refetchInterval: 5000, // Refetch every 5 seconds as fallback
  });

  // Apply real-time updates from WebSocket to the execution list
  const updatedExecutions = executions.map((exec) => {
    const update = executionUpdates.get(exec.execution_id);
    if (update) {
      return {
        ...exec,
        status: update.status,
        current_step_index: update.current_step_index,
        error: update.error || exec.error,
        started_at: update.started_at || exec.started_at,
        completed_at: update.completed_at || exec.completed_at,
        step_results: update.step_results || exec.step_results || [],
      };
    }
    return exec;
  });

  // Filter executions by status
  const filteredExecutions = statusFilter === 'all'
    ? updatedExecutions
    : updatedExecutions.filter((exec) => exec.status === statusFilter);

  // Pause execution mutation
  const pauseMutation = useMutation({
    mutationFn: (executionId: string) => api.executions.pause(executionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      setSnackbarMessage('Execution paused');
      setSnackbarOpen(true);
    },
    onError: (error) => {
      setSnackbarMessage(`Failed to pause: ${(error as Error).message}`);
      setSnackbarOpen(true);
    },
  });

  // Resume execution mutation
  const resumeMutation = useMutation({
    mutationFn: (executionId: string) => api.executions.resume(executionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      setSnackbarMessage('Execution resumed');
      setSnackbarOpen(true);
    },
    onError: (error) => {
      setSnackbarMessage(`Failed to resume: ${(error as Error).message}`);
      setSnackbarOpen(true);
    },
  });

  // Skip step mutation
  const skipMutation = useMutation({
    mutationFn: (executionId: string) => api.executions.skip(executionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      setSnackbarMessage('Step skipped');
      setSnackbarOpen(true);
    },
    onError: (error) => {
      setSnackbarMessage(`Failed to skip: ${(error as Error).message}`);
      setSnackbarOpen(true);
    },
  });

  // Cancel execution mutation
  const cancelMutation = useMutation({
    mutationFn: (executionId: string) => api.executions.cancel(executionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      setSnackbarMessage('Execution cancelled');
      setSnackbarOpen(true);
    },
    onError: (error) => {
      setSnackbarMessage(`Failed to cancel: ${(error as Error).message}`);
      setSnackbarOpen(true);
    },
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Executions
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Monitor playbook execution status in real-time
      </Typography>

      {/* Status Filter */}
      <Box sx={{ mb: 3 }}>
        <ToggleButtonGroup
          value={statusFilter}
          exclusive
          onChange={(_, newFilter) => newFilter && setStatusFilter(newFilter)}
          aria-label="Filter executions by status"
          size="small"
        >
          <ToggleButton value="all" aria-label="Show all executions">
            All ({updatedExecutions.length})
          </ToggleButton>
          <ToggleButton value="running" aria-label="Show running executions">
            Running ({updatedExecutions.filter((e) => e.status === 'running').length})
          </ToggleButton>
          <ToggleButton value="paused" aria-label="Show paused executions">
            Paused ({updatedExecutions.filter((e) => e.status === 'paused').length})
          </ToggleButton>
          <ToggleButton value="completed" aria-label="Show completed executions">
            Completed ({updatedExecutions.filter((e) => e.status === 'completed').length})
          </ToggleButton>
          <ToggleButton value="failed" aria-label="Show failed executions">
            Failed ({updatedExecutions.filter((e) => e.status === 'failed').length})
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Loading state */}
      {isLoading && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CircularProgress size={20} aria-label="Loading executions" />
          <Typography variant="body2" color="text.secondary">
            Loading executions...
          </Typography>
        </Box>
      )}

      {/* Error state */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load executions: {(error as Error).message}
        </Alert>
      )}

      {/* Empty state */}
      {!isLoading && !error && filteredExecutions.length === 0 && (
        <Alert severity="info">
          {statusFilter === 'all'
            ? 'No executions yet. Start a playbook from the Playbooks page.'
            : `No ${statusFilter} executions found.`}
        </Alert>
      )}

      {/* Execution List */}
      {!isLoading && !error && filteredExecutions.length > 0 && (
        <Stack spacing={2}>
          {filteredExecutions.map((execution) => (
            <ExecutionCard
              key={execution.execution_id}
              execution={execution}
              onPause={(id) => pauseMutation.mutate(id)}
              onResume={(id) => resumeMutation.mutate(id)}
              onSkip={(id) => skipMutation.mutate(id)}
              onCancel={(id) => cancelMutation.mutate(id)}
            />
          ))}
        </Stack>
      )}

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      />
    </Box>
  );
}
