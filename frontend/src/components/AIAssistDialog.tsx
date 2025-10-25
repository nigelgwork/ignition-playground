/**
 * AIAssistDialog - Floating AI chat interface for debugging paused executions
 *
 * Displays as a collapsible chat box with toggle button.
 * Shows current error context, allows chat with AI, and can apply fixes.
 */

import { useState, useEffect } from 'react';
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
  Fab,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Send as SendIcon,
  BugReport as BugIcon,
  AutoFixHigh as FixIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Close as CloseIcon,
  Chat as ChatIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';

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

interface AICredentialInfo {
  id: number;
  name: string;
  provider: string;
  api_base_url: string | null;
  model_name: string | null;
  enabled: string;
  has_api_key: boolean;
}

export function AIAssistDialog({
  open,
  onClose: _onClose,
  executionId: _executionId,
  currentError,
  currentStep: _currentStep,
}: AIAssistDialogProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);
  const [isVisible, setIsVisible] = useState(true); // Auto-show when open=true
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const [selectedCredential, setSelectedCredential] = useState<string>('');

  // Fetch AI credentials
  const { data: credentials = [] } = useQuery<AICredentialInfo[]>({
    queryKey: ['ai-credentials'],
    queryFn: () => fetch('/api/ai-credentials').then((r) => r.json()),
    enabled: open, // Only fetch when dialog is open
  });

  // Auto-select first enabled credential
  useEffect(() => {
    if (credentials.length > 0 && !selectedCredential) {
      const enabledCred = credentials.find((c) => c.enabled === 'true');
      if (enabledCred) {
        setSelectedCredential(enabledCred.name);
      } else if (credentials.length > 0) {
        setSelectedCredential(credentials[0].name);
      }
    }
  }, [credentials, selectedCredential]);

  // Load initial context from backend when dialog opens
  useEffect(() => {
    if (open && !initialLoadDone) {
      setIsLoading(true);
      fetch('/api/ai/assist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          execution_id: _executionId,
          user_message: 'What is the current status?',
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          setMessages([
            {
              role: 'assistant',
              content: data.message || `I can help you debug this issue.${currentError ? ` Error: "${currentError}"` : ''} What would you like me to help you with?`,
              timestamp: new Date(),
            },
          ]);
          setInitialLoadDone(true);
        })
        .catch(() => {
          setMessages([
            {
              role: 'assistant',
              content: `I can help you debug this issue.${currentError ? ` Error: "${currentError}"` : ''} What would you like me to help you with?`,
              timestamp: new Date(),
            },
          ]);
          setInitialLoadDone(true);
        })
        .finally(() => setIsLoading(false));
    }
  }, [open, _executionId, currentError, initialLoadDone]);

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
          error_context: currentError,
          credential_name: selectedCredential,
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

  const handleToggleVisibility = () => {
    setIsVisible(!isVisible);
    if (!isVisible) {
      setIsExpanded(true); // Auto-expand when showing
    }
  };

  if (!open) {
    return null;
  }

  return (
    <>
      {/* Toggle Button - Fixed Bottom Left */}
      <Tooltip title={isVisible ? 'Hide AI Assistant' : 'Show AI Assistant'} placement="right">
        <Fab
          color="primary"
          size="medium"
          onClick={handleToggleVisibility}
          sx={{
            position: 'fixed',
            bottom: 24,
            left: 260,
            zIndex: 2000,
            display: isVisible ? 'none' : 'flex',
          }}
        >
          <ChatIcon />
        </Fab>
      </Tooltip>

      {/* Floating Chat Box */}
      {isVisible && (
        <Paper
          elevation={8}
          sx={{
            position: 'fixed',
            bottom: 24,
            left: 260,
            width: isExpanded ? 420 : 56,
            maxHeight: isExpanded ? '65vh' : 56,
            display: 'flex',
            flexDirection: 'column',
            transition: 'all 0.3s ease-in-out',
            zIndex: 2000,
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
              cursor: isExpanded ? 'default' : 'pointer',
            }}
            onClick={() => !isExpanded && setIsExpanded(true)}
          >
            <BugIcon fontSize="small" />
            {isExpanded && (
              <>
                <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                  AI Debug Assistant
                </Typography>
                <Chip label="Paused" color="warning" size="small" />
                <Tooltip title="Minimize">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsExpanded(false);
                    }}
                    sx={{ color: 'inherit' }}
                  >
                    <ExpandMoreIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Close">
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsVisible(false);
                    }}
                    sx={{ color: 'inherit' }}
                  >
                    <CloseIcon />
                  </IconButton>
                </Tooltip>
              </>
            )}
            {!isExpanded && (
              <Tooltip title="Expand">
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsExpanded(true);
                  }}
                  sx={{ color: 'inherit', ml: 'auto' }}
                >
                  <ExpandLessIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>

          {/* Chat Content */}
          <Collapse in={isExpanded} timeout="auto">
            {/* AI Credential Selector */}
            <Box sx={{ px: 2, py: 1.5, bgcolor: 'background.default' }}>
              <FormControl fullWidth size="small">
                <InputLabel>AI Provider</InputLabel>
                <Select
                  value={selectedCredential}
                  label="AI Provider"
                  onChange={(e) => setSelectedCredential(e.target.value)}
                  disabled={credentials.length === 0}
                >
                  {credentials.length === 0 && (
                    <MenuItem value="" disabled>
                      No AI credentials configured
                    </MenuItem>
                  )}
                  {credentials.map((cred) => (
                    <MenuItem key={cred.name} value={cred.name}>
                      {cred.name} ({cred.provider} - {cred.model_name || 'default'})
                      {cred.enabled === 'false' && ' [Disabled]'}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

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
                maxHeight: 'calc(65vh - 220px)',
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
      )}
    </>
  );
}
