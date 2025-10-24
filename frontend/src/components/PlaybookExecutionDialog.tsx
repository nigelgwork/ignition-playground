/**
 * PlaybookExecutionDialog - Dialog for configuring and executing playbooks
 */

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  FormLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../api/client';
import type { PlaybookInfo, CredentialInfo } from '../types/api';

interface PlaybookExecutionDialogProps {
  open: boolean;
  playbook: PlaybookInfo | null;
  onClose: () => void;
  onExecutionStarted?: (executionId: string) => void;
}

export function PlaybookExecutionDialog({
  open,
  playbook,
  onClose,
  onExecutionStarted,
}: PlaybookExecutionDialogProps) {
  const [parameters, setParameters] = useState<Record<string, string>>({});
  const [gatewayUrl, setGatewayUrl] = useState('http://localhost:8088');

  // Fetch available credentials
  const { data: credentials = [] } = useQuery<CredentialInfo[]>({
    queryKey: ['credentials'],
    queryFn: api.credentials.list,
    enabled: open,
  });

  // Execute playbook mutation
  const executeMutation = useMutation({
    mutationFn: (params: { playbook_path: string; parameters: Record<string, string>; gateway_url?: string }) =>
      api.executions.start(params),
    onSuccess: (data) => {
      onExecutionStarted?.(data.execution_id);
      onClose();
      // Reset form
      setParameters({});
    },
  });

  // Reset form when playbook changes
  useEffect(() => {
    if (playbook) {
      const defaultParams: Record<string, string> = {};
      playbook.parameters.forEach((param) => {
        if (param.default) {
          defaultParams[param.name] = param.default;
        }
      });
      setParameters(defaultParams);
    }
  }, [playbook]);

  if (!playbook) return null;

  const handleParameterChange = (name: string, value: string) => {
    setParameters((prev) => ({ ...prev, [name]: value }));
  };

  const handleExecute = () => {
    executeMutation.mutate({
      playbook_path: playbook.path,
      parameters,
      gateway_url: gatewayUrl,
    });
  };

  const isValid = playbook.parameters.every((param) => {
    if (!param.required) return true;
    return parameters[param.name] && parameters[param.name].trim() !== '';
  });

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Execute Playbook: {playbook.name}</DialogTitle>

      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {playbook.description}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Version {playbook.version} • {playbook.step_count} steps
          </Typography>
        </Box>

        {/* Gateway URL */}
        <TextField
          label="Gateway URL"
          fullWidth
          value={gatewayUrl}
          onChange={(e) => setGatewayUrl(e.target.value)}
          placeholder="http://localhost:8088"
          sx={{ mb: 2 }}
          helperText="Ignition Gateway base URL"
        />

        {/* Parameter inputs */}
        {playbook.parameters.length > 0 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Parameters
            </Typography>

            {playbook.parameters.map((param) => (
              <FormControl key={param.name} fullWidth>
                <FormLabel sx={{ mb: 0.5, fontSize: '0.875rem' }}>
                  {param.name}
                  {param.required && ' *'}
                </FormLabel>

                {param.type === 'credential' ? (
                  <Select
                    value={parameters[param.name] || ''}
                    onChange={(e) => handleParameterChange(param.name, e.target.value)}
                    displayEmpty
                    size="small"
                  >
                    <MenuItem value="" disabled>
                      Select credential...
                    </MenuItem>
                    {credentials.map((cred) => (
                      <MenuItem key={cred.name} value={cred.name}>
                        {cred.name} ({cred.username})
                      </MenuItem>
                    ))}
                  </Select>
                ) : param.type === 'file' ? (
                  <TextField
                    value={parameters[param.name] || ''}
                    onChange={(e) => handleParameterChange(param.name, e.target.value)}
                    placeholder="Enter file path..."
                    size="small"
                    fullWidth
                  />
                ) : (
                  <TextField
                    value={parameters[param.name] || ''}
                    onChange={(e) => handleParameterChange(param.name, e.target.value)}
                    placeholder={param.default || `Enter ${param.name}...`}
                    size="small"
                    fullWidth
                  />
                )}

                {param.description && (
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                    {param.description}
                  </Typography>
                )}
              </FormControl>
            ))}
          </Box>
        )}

        {/* Error display */}
        {executeMutation.isError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            Failed to start execution: {(executeMutation.error as Error).message}
          </Alert>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={executeMutation.isPending}>
          Cancel
        </Button>
        <Button
          onClick={handleExecute}
          variant="contained"
          disabled={!isValid || executeMutation.isPending}
          startIcon={executeMutation.isPending ? <CircularProgress size={16} /> : undefined}
        >
          {executeMutation.isPending ? 'Starting...' : 'Execute'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
