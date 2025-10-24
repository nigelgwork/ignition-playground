/**
 * ExecutionDetail - Detailed view of a running/completed playbook execution
 *
 * Features:
 * - Split-pane layout: Step progress (left) + Live browser view (right)
 * - Execution controls (pause/resume/skip/stop)
 * - Real-time updates via WebSocket
 */

import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Button,
  Divider,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  CheckCircle as CompletedIcon,
  Error as ErrorIcon,
  PlayArrow as RunningIcon,
  ArrowBack as BackIcon,
  Pending as PendingIcon,
  Cancel as SkippedIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { LiveBrowserView } from '../components/LiveBrowserView';
import { ExecutionControls } from '../components/ExecutionControls';
import { useStore } from '../store';
import type { ExecutionStatusResponse } from '../types/api';

export function ExecutionDetail() {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  const executionUpdates = useStore((state) => state.executionUpdates);

  // Fetch execution from API
  const { data: executionFromAPI, isLoading, error } = useQuery<ExecutionStatusResponse>({
    queryKey: ['execution', executionId],
    queryFn: () => api.executions.get(executionId!),
    enabled: !!executionId,
    refetchInterval: 2000, // Refetch every 2 seconds as fallback
  });

  if (!executionId) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">Invalid execution ID</Typography>
      </Box>
    );
  }

  // Use WebSocket update if available, otherwise use API data
  const wsUpdate = executionUpdates.get(executionId);
  const execution = wsUpdate || executionFromAPI;

  if (isLoading) {
    return (
      <Box sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <CircularProgress size={20} />
        <Typography>Loading execution details...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load execution: {(error as Error).message}
        </Alert>
      </Box>
    );
  }

  if (!execution) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          Execution not found
        </Alert>
      </Box>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CompletedIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'running':
        return <RunningIcon color="primary" />;
      case 'skipped':
        return <SkippedIcon color="warning" />;
      default:
        return <PendingIcon color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'primary';
      case 'skipped':
        return 'warning';
      default:
        return 'default';
    }
  };

  const progress = execution.step_results
    ? (execution.step_results.filter((s) => s.status === 'completed').length /
        execution.step_results.length) *
      100
    : 0;

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper
        elevation={1}
        sx={{
          p: 2,
          borderRadius: 0,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
        }}
      >
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/executions')}
          variant="outlined"
          size="small"
        >
          Back
        </Button>

        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6">{execution.playbook_name}</Typography>
          <Typography variant="caption" color="text.secondary">
            Execution ID: {executionId}
          </Typography>
        </Box>

        <Chip
          label={execution.status}
          color={getStatusColor(execution.status) as any}
          size="small"
        />

        <ExecutionControls
          executionId={executionId}
          status={execution.status}
        />
      </Paper>

      {/* Progress Bar */}
      {execution.status === 'running' && (
        <Box sx={{ px: 2 }}>
          <LinearProgress variant="determinate" value={progress} />
          <Typography variant="caption" color="text.secondary">
            Progress: {Math.round(progress)}%
          </Typography>
        </Box>
      )}

      {/* Split Pane */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 2,
          p: 2,
          overflow: 'hidden',
        }}
      >
        {/* Left: Step Progress */}
        <Paper elevation={2} sx={{ overflow: 'auto' }}>
          <Box
            sx={{
              p: 2,
              borderBottom: 1,
              borderColor: 'divider',
              position: 'sticky',
              top: 0,
              bgcolor: 'background.paper',
              zIndex: 1,
            }}
          >
            <Typography variant="h6">Step Progress</Typography>
            <Typography variant="caption" color="text.secondary">
              {execution.current_step_index !== undefined
                ? `Current step: ${execution.current_step_index + 1}`
                : 'Initializing...'}
            </Typography>
          </Box>

          <List>
            {execution.step_results && execution.step_results.length > 0 ? (
              execution.step_results.map((step, index) => (
                <Box key={step.step_id || index}>
                  <ListItem
                    sx={{
                      bgcolor:
                        index === execution.current_step_index
                          ? 'action.selected'
                          : 'transparent',
                    }}
                  >
                    <Box sx={{ mr: 2 }}>{getStatusIcon(step.status)}</Box>
                    <ListItemText
                      primary={step.step_name || `Step ${index + 1}`}
                      secondary={
                        step.error ? (
                          <Typography variant="caption" color="error">
                            Error: {step.error}
                          </Typography>
                        ) : step.completed_at ? (
                          `Completed at ${new Date(
                            step.completed_at
                          ).toLocaleTimeString()}`
                        ) : (
                          step.status
                        )
                      }
                    />
                    <Chip
                      label={step.status}
                      size="small"
                      color={getStatusColor(step.status) as any}
                    />
                  </ListItem>
                  {execution.step_results && index < execution.step_results.length - 1 && <Divider />}
                </Box>
              ))
            ) : (
              <ListItem>
                <ListItemText primary="No steps executed yet" />
              </ListItem>
            )}
          </List>
        </Paper>

        {/* Right: Live Browser View */}
        <LiveBrowserView executionId={executionId} />
      </Box>
    </Box>
  );
}
