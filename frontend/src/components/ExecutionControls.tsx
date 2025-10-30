/**
 * ExecutionControls - Control buttons for playbook execution
 *
 * Provides pause, resume, skip, and stop controls
 */

import { useState, useRef } from 'react';
import {
  Box,
  Button,
  ButtonGroup,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Pause as PauseIcon,
  PlayArrow as ResumeIcon,
  SkipNext as SkipIcon,
  Cancel as CancelIcon,
  Psychology as AIIcon,
} from '@mui/icons-material';
import { api } from '../api/client';

interface ExecutionControlsProps {
  executionId: string;
  status: string;
  disabled?: boolean;
  debugMode?: boolean;
  onAIAssist?: () => void;
}

export function ExecutionControls({
  executionId,
  status,
  disabled = false,
  debugMode = false,
  onAIAssist,
}: ExecutionControlsProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const cancelInProgressRef = useRef(false);

  const handlePause = async () => {
    try {
      setLoading('pause');
      await api.executions.pause(executionId);
    } catch (error) {
      console.error('Failed to pause execution:', error);
    } finally {
      setLoading(null);
    }
  };

  const handleResume = async () => {
    try {
      setLoading('resume');
      await api.executions.resume(executionId);
    } catch (error) {
      console.error('Failed to resume execution:', error);
    } finally {
      setLoading(null);
    }
  };

  const handleSkip = async () => {
    try {
      setLoading('skip');
      await api.executions.skip(executionId);
    } catch (error) {
      console.error('Failed to skip step:', error);
    } finally {
      setLoading(null);
    }
  };


  const handleCancel = async () => {
    console.log('[ExecutionControls] Cancel button clicked, executionId:', executionId);

    // Prevent duplicate cancel requests
    if (cancelInProgressRef.current) {
      console.log('[ExecutionControls] Cancel already in progress, ignoring duplicate click');
      return;
    }

    // Mark cancel as in progress using ref (persists across re-renders)
    cancelInProgressRef.current = true;
    setLoading('cancel');

    try {
      console.log('[ExecutionControls] Sending cancel request...');
      const response = await api.executions.cancel(executionId);
      console.log('[ExecutionControls] Cancel request succeeded:', response);
    } catch (error) {
      console.error('[ExecutionControls] Failed to cancel execution:', error);
      alert(`Failed to cancel execution: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      console.log('[ExecutionControls] Cancel request complete, clearing loading state');
      cancelInProgressRef.current = false;
      setLoading(null);
    }
  };

  const isRunning = status === 'running';
  const isPaused = status === 'paused';
  const isActive = isRunning || isPaused;  // Execution is active if running or paused
  const isDisabled = disabled || !isActive;  // Only disable if not active at all

  // Debug logging
  console.log('[ExecutionControls] Render:', {
    executionId,
    status,
    isRunning,
    isPaused,
    isActive,
    isDisabled,
    disabled,
    loading
  });

  return (
    <Box sx={{ display: 'flex', gap: 1 }}>
      {/* AI Assist Button (show when paused OR in debug mode) */}
      {(isPaused || debugMode) && onAIAssist && (
        <Tooltip title={debugMode ? "AI assistant available in debug mode" : "Get AI help to debug this issue"}>
          <Button
            onClick={onAIAssist}
            variant="contained"
            color="secondary"
            size="small"
            startIcon={<AIIcon />}
          >
            AI
          </Button>
        </Tooltip>
      )}

      <ButtonGroup variant="outlined" size="small">
        {/* Pause Button */}
        <Tooltip title="Pause execution after current step">
          <span>
            <Button
              onClick={handlePause}
              disabled={disabled || !isRunning || isPaused || loading !== null}
              startIcon={
                loading === 'pause' ? (
                  <CircularProgress size={16} />
                ) : (
                  <PauseIcon />
                )
              }
            >
              Pause
            </Button>
          </span>
        </Tooltip>

        {/* Resume Button */}
        <Tooltip title="Resume paused execution">
          <span>
            <Button
              onClick={handleResume}
              disabled={disabled || !isPaused || loading !== null}
              startIcon={
                loading === 'resume' ? (
                  <CircularProgress size={16} />
                ) : (
                  <ResumeIcon />
                )
              }
            >
              Resume
            </Button>
          </span>
        </Tooltip>

        {/* Skip Button */}
        <Tooltip title="Skip current step">
          <span>
            <Button
              onClick={handleSkip}
              disabled={isDisabled || loading !== null}
              startIcon={
                loading === 'skip' ? (
                  <CircularProgress size={16} />
                ) : (
                  <SkipIcon />
                )
              }
            >
              Skip
            </Button>
          </span>
        </Tooltip>

        {/* Cancel Button */}
        <Tooltip title="Cancel execution">
          <span>
            <Button
              onClick={() => {
                console.log('[ExecutionControls] Cancel button onClick fired', {
                  executionId,
                  status,
                  isDisabled,
                  loading,
                  cancelInProgress: cancelInProgressRef.current,
                  buttonDisabled: isDisabled || loading !== null
                });
                handleCancel();
              }}
              disabled={isDisabled || loading !== null || cancelInProgressRef.current}
              color="error"
              startIcon={
                loading === 'cancel' ? (
                  <CircularProgress size={16} />
                ) : (
                  <CancelIcon />
                )
              }
            >
              Cancel
            </Button>
          </span>
        </Tooltip>
      </ButtonGroup>
    </Box>
  );
}
