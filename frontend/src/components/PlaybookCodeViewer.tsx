/**
 * PlaybookCodeViewer - View and edit playbook YAML code
 *
 * Shows the playbook source code in a syntax-highlighted editor
 * Allows editing when in debug/paused mode
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Code as CodeIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

interface PlaybookCodeViewerProps {
  executionId: string;
  playbookName: string;
  isDebugMode: boolean;
  isPaused: boolean;
  onClose?: () => void;
}

interface PlaybookCodeResponse {
  code: string;
  playbook_path: string;
  playbook_name: string;
}

export function PlaybookCodeViewer({
  executionId,
  playbookName,
  isDebugMode,
  isPaused,
  onClose,
}: PlaybookCodeViewerProps) {
  const [code, setCode] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const queryClient = useQueryClient();

  // Fetch playbook code
  const { data: playbookData, isLoading, error, refetch } = useQuery<PlaybookCodeResponse>({
    queryKey: ['playbook-code', executionId],
    queryFn: async () => {
      const response = await api.executions.getPlaybookCode(executionId);
      return response;
    },
  });

  // Set initial code when data loads
  useEffect(() => {
    if (playbookData?.code) {
      setCode(playbookData.code);
      setHasChanges(false);
    }
  }, [playbookData]);

  // Save playbook code mutation
  const saveMutation = useMutation({
    mutationFn: async (updatedCode: string) => {
      return await api.executions.updatePlaybookCode(executionId, updatedCode);
    },
    onSuccess: () => {
      setHasChanges(false);
      queryClient.invalidateQueries({ queryKey: ['playbook-code', executionId] });
    },
  });

  const handleCodeChange = (newCode: string) => {
    setCode(newCode);
    setHasChanges(newCode !== (playbookData?.code || ''));
  };

  const handleSave = () => {
    saveMutation.mutate(code);
  };

  const handleRefresh = () => {
    refetch();
  };

  const canEdit = isDebugMode || isPaused;

  return (
    <Paper
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.paper',
        borderRadius: 1,
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CodeIcon color="primary" />
          <Typography variant="h6">Playbook Code</Typography>
          <Typography variant="body2" color="text.secondary">
            {playbookName}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {canEdit && (
            <>
              <Tooltip title="Refresh code">
                <IconButton size="small" onClick={handleRefresh} disabled={isLoading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              <Button
                variant="contained"
                size="small"
                startIcon={<SaveIcon />}
                onClick={handleSave}
                disabled={!hasChanges || saveMutation.isPending}
              >
                {saveMutation.isPending ? 'Saving...' : 'Save Changes'}
              </Button>
            </>
          )}
          {onClose && (
            <IconButton size="small" onClick={onClose}>
              <CloseIcon />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Content */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load playbook code: {error instanceof Error ? error.message : 'Unknown error'}
          </Alert>
        )}

        {saveMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to save changes: {saveMutation.error instanceof Error ? saveMutation.error.message : 'Unknown error'}
          </Alert>
        )}

        {saveMutation.isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Changes saved successfully!
          </Alert>
        )}

        {!canEdit && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Enable debug mode or pause execution to edit the playbook code.
          </Alert>
        )}

        {!isLoading && !error && (
          <Box
            component="textarea"
            value={code}
            onChange={(e) => handleCodeChange(e.target.value)}
            readOnly={!canEdit}
            sx={{
              width: '100%',
              minHeight: 500,
              fontFamily: '"Fira Code", "Monaco", "Courier New", monospace',
              fontSize: '0.875rem',
              lineHeight: 1.6,
              p: 2,
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              bgcolor: canEdit ? 'background.default' : 'action.disabledBackground',
              color: 'text.primary',
              resize: 'vertical',
              '&:focus': {
                outline: 'none',
                borderColor: 'primary.main',
              },
            }}
          />
        )}
      </Box>

      {/* Footer with status */}
      {hasChanges && (
        <Box
          sx={{
            p: 1,
            borderTop: 1,
            borderColor: 'divider',
            bgcolor: 'warning.dark',
          }}
        >
          <Typography variant="caption" color="warning.contrastText">
            ⚠️ You have unsaved changes
          </Typography>
        </Box>
      )}
    </Paper>
  );
}
