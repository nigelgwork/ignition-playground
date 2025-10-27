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
  SkipPrevious as SkipBackIcon,
  Stop as StopIcon,
  Psychology as AIIcon,
  Terminal as TerminalIcon,
} from '@mui/icons-material';
import { api } from '../api/client';

interface ExecutionControlsProps {
  executionId: string;
  status: string;
  disabled?: boolean;
  debugMode?: boolean;
  onAIAssist?: () => void;
  onClaudeCode?: () => void;
}

export function ExecutionControls({
  executionId,
  status,
  disabled = false,
  debugMode = false,
  onAIAssist,
  onClaudeCode,
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

  const handleSkipBack = async () => {
    try {
      setLoading('skip_back');
      await api.executions.skipBack(executionId);
    } catch (error) {
      console.error('Failed to skip back:', error);
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
  const isActive = isRunning || isPaused;  // Execution is active if running or paused
  const isDisabled = disabled || !isActive;  // Only disable if not active at all

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
            Ask AI
          </Button>
        </Tooltip>
      )}

      {/* Claude Code Button (show when paused OR in debug mode) */}
      {(isPaused || debugMode) && onClaudeCode && (
        <Tooltip title="Open playbook in Claude Code with execution context">
          <Button
            onClick={onClaudeCode}
            variant="outlined"
            color="primary"
            size="small"
            startIcon={<TerminalIcon />}
          >
            Claude Code
          </Button>
        </Tooltip>
      )}

      <ButtonGroup variant="outlined" size="small">
        {/* Skip Back Button */}
        <Tooltip title="Skip back to previous step">
          <span>
            <Button
              onClick={handleSkipBack}
              disabled={isDisabled || loading !== null}
              startIcon={
                loading === 'skip_back' ? (
                  <CircularProgress size={16} />
                ) : (
                  <SkipBackIcon />
                )
              }
            >
              Back
            </Button>
          </span>
        </Tooltip>

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
