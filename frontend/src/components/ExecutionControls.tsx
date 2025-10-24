/**
 * ExecutionControls - Control buttons for playbook execution
 *
 * Provides pause, resume, skip, and stop controls
 */

import { useState } from 'react';
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
  Stop as StopIcon,
} from '@mui/icons-material';
import { api } from '../api/client';

interface ExecutionControlsProps {
  executionId: string;
  status: string;
  disabled?: boolean;
}

export function ExecutionControls({
  executionId,
  status,
  disabled = false,
}: ExecutionControlsProps) {
  const [loading, setLoading] = useState<string | null>(null);

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

  const handleStop = async () => {
    try {
      setLoading('stop');
      await api.executions.cancel(executionId);
    } catch (error) {
      console.error('Failed to stop execution:', error);
    } finally {
      setLoading(null);
    }
  };

  const isRunning = status === 'running';
  const isPaused = status === 'paused';
  const isDisabled = disabled || !isRunning;

  return (
    <Box sx={{ display: 'flex', gap: 1 }}>
      <ButtonGroup variant="outlined" size="small">
        {/* Pause Button */}
        <Tooltip title="Pause execution after current step">
          <span>
            <Button
              onClick={handlePause}
              disabled={isDisabled || isPaused || loading !== null}
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
              disabled={!isPaused || loading !== null}
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

        {/* Stop Button */}
        <Tooltip title="Stop execution">
          <span>
            <Button
              onClick={handleStop}
              disabled={isDisabled || loading !== null}
              color="error"
              startIcon={
                loading === 'stop' ? (
                  <CircularProgress size={16} />
                ) : (
                  <StopIcon />
                )
              }
            >
              Stop
            </Button>
          </span>
        </Tooltip>
      </ButtonGroup>
    </Box>
  );
}
