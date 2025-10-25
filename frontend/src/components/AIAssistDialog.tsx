/**
 * AIAssistDialog - Floating AI chat interface for debugging paused executions
 *
 * Displays as a collapsible chat box in the bottom-left corner.
 * Shows current error context, allows chat with AI, and can apply fixes.
 */

import { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Chip,
  CircularProgress,
  IconButton,
  Divider,
  Collapse,
} from '@mui/material';
import {
  Send as SendIcon,
  BugReport as BugIcon,
  AutoFixHigh as FixIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';

interface AIAssistDialogProps {
  open: boolean;
  onClose: () => void;
  executionId: string;
  currentError?: string;
  currentStep?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function AIAssistDialog({
  open,
  onClose: _onClose,
  executionId: _executionId,
  currentError,
  currentStep,
}: AIAssistDialogProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: `I can help you debug this issue. The execution is paused at step "${currentStep || 'unknown'}"${
        currentError ? ` with error: "${currentError}"` : ''
      }. What would you like me to help you with?`,
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Call AI assist endpoint
      const response = await fetch('/api/ai/assist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          execution_id: _executionId,
          user_message: inputMessage,
          current_step_id: currentStep,
          error_context: currentError,
        }),
      });

      if (!response.ok) {
        throw new Error('AI assist failed');
      }

      const data = await response.json();
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.message || 'I can help you debug this issue. Please describe what you need help with in the Claude Code chat.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Error connecting to AI assistant. Please use Claude Code chat directly to get help.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!open) {
    return null;
  }

  return (
    <>
      {/* Floating Chat Box - Bottom Left */}
      <Paper
        elevation={8}
        sx={{
          position: 'fixed',
          bottom: 16,
          left: 16,
          width: isExpanded ? 400 : 56,
          maxHeight: isExpanded ? '70vh' : 56,
          display: 'flex',
          flexDirection: 'column',
          transition: 'all 0.3s ease-in-out',
          zIndex: 1300,
          borderRadius: 2,
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            p: 1.5,
            bgcolor: 'primary.dark',
            color: 'primary.contrastText',
            cursor: 'pointer',
          }}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <BugIcon fontSize="small" />
          {isExpanded && (
            <>
              <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                AI Debug Assistant
              </Typography>
              <Chip label="Paused" color="warning" size="small" />
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
                sx={{ color: 'inherit' }}
              >
                {isExpanded ? <ExpandMoreIcon /> : <ExpandLessIcon />}
              </IconButton>
            </>
          )}
        </Box>

        {/* Chat Content */}
        <Collapse in={isExpanded} timeout="auto">
          {/* Error Context */}
          {currentError && (
            <Box sx={{ px: 2, py: 1.5, bgcolor: 'error.dark', color: 'error.contrastText' }}>
              <Typography variant="caption" fontWeight="bold" display="block">
                Current Error:
              </Typography>
              <Typography variant="body2">{currentError}</Typography>
            </Box>
          )}

          {/* Chat Messages */}
          <Box
            sx={{
              flexGrow: 1,
              overflow: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 1.5,
              p: 2,
              maxHeight: 'calc(70vh - 200px)',
              minHeight: 200,
            }}
          >
            {messages.map((msg, index) => (
              <Box
                key={index}
                sx={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                }}
              >
                <Paper
                  elevation={1}
                  sx={{
                    p: 1.5,
                    bgcolor: msg.role === 'user' ? 'primary.dark' : 'background.paper',
                    color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                  }}
                >
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                    {msg.content}
                  </Typography>
                  <Typography
                    variant="caption"
                    color={msg.role === 'user' ? 'primary.light' : 'text.secondary'}
                    sx={{ mt: 0.5, display: 'block' }}
                  >
                    {msg.timestamp.toLocaleTimeString()}
                  </Typography>
                </Paper>
              </Box>
            ))}

            {isLoading && (
              <Box sx={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={16} />
                <Typography variant="body2" color="text.secondary">
                  AI is thinking...
                </Typography>
              </Box>
            )}
          </Box>

          <Divider />

          {/* Input Area */}
          <Box sx={{ p: 1.5, display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              placeholder="Describe the issue..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              multiline
              maxRows={2}
              size="small"
              sx={{
                '& .MuiOutlinedInput-root': {
                  fontSize: '0.875rem',
                },
              }}
            />
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              size="small"
            >
              <SendIcon fontSize="small" />
            </IconButton>
          </Box>

          {/* Action Buttons */}
          <Box sx={{ px: 1.5, pb: 1.5, display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<FixIcon />}
              size="small"
              disabled
              fullWidth
            >
              Apply Fix
            </Button>
          </Box>
        </Collapse>
      </Paper>
    </>
  );
}
