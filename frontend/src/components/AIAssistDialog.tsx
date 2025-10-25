/**
 * AIAssistDialog - AI chat interface for debugging paused executions
 *
 * Displays when execution is paused and user needs AI help to debug issues.
 * Shows current error context, allows chat with AI, and can apply fixes.
 */

import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Paper,
  Chip,
  CircularProgress,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  Close as CloseIcon,
  BugReport as BugIcon,
  AutoFixHigh as FixIcon,
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
  onClose,
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

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          height: '80vh',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, pb: 1 }}>
        <BugIcon color="primary" />
        <Typography variant="h6" component="span" sx={{ flexGrow: 1 }}>
          AI Debug Assistant
        </Typography>
        <Chip label="Paused" color="warning" size="small" />
        <IconButton size="small" onClick={onClose} edge="end">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <Divider />

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
      <DialogContent
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          p: 2,
        }}
      >
        {messages.map((msg, index) => (
          <Box
            key={index}
            sx={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '75%',
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
            <CircularProgress size={20} />
            <Typography variant="body2" color="text.secondary">
              AI is thinking...
            </Typography>
          </Box>
        )}
      </DialogContent>

      <Divider />

      {/* Input Area */}
      <DialogActions sx={{ p: 2, gap: 1 }}>
        <TextField
          fullWidth
          placeholder="Describe the issue or ask for help..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          multiline
          maxRows={3}
          size="small"
        />
        <Button
          variant="contained"
          onClick={handleSendMessage}
          disabled={!inputMessage.trim() || isLoading}
          endIcon={<SendIcon />}
          sx={{ minWidth: 100 }}
        >
          Send
        </Button>
      </DialogActions>

      {/* Action Buttons */}
      <Box sx={{ px: 2, pb: 2, display: 'flex', gap: 1 }}>
        <Button
          variant="outlined"
          startIcon={<FixIcon />}
          size="small"
          disabled
          fullWidth
        >
          Apply Suggested Fix
        </Button>
        <Button variant="outlined" onClick={onClose} size="small" fullWidth>
          Close & Resume
        </Button>
      </Box>
    </Dialog>
  );
}
