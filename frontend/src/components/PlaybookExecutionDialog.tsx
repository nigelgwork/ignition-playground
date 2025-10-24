/**
 * PlaybookExecutionDialog - Dialog for configuring and executing playbooks
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import { Save as SaveIcon, PlayArrow as PlayIcon } from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../api/client';
import { ParameterInput } from './ParameterInput';
import type { PlaybookInfo, CredentialInfo } from '../types/api';
import { useStore, type SessionCredential } from '../store';

interface PlaybookExecutionDialogProps {
  open: boolean;
  playbook: PlaybookInfo | null;
  onClose: () => void;
  onExecutionStarted?: (executionId: string) => void;
}

interface SavedConfig {
  gatewayUrl: string;
  parameters: Record<string, string>;
  savedAt: string;
}

// Get saved config for a playbook
function getSavedConfig(playbookPath: string): SavedConfig | null {
  const stored = localStorage.getItem(`playbook_config_${playbookPath}`);
  return stored ? JSON.parse(stored) : null;
}

// Save config for a playbook
function saveConfig(playbookPath: string, config: SavedConfig) {
  localStorage.setItem(`playbook_config_${playbookPath}`, JSON.stringify(config));
}

export function PlaybookExecutionDialog({
  open,
  playbook,
  onClose,
  onExecutionStarted,
}: PlaybookExecutionDialogProps) {
  const navigate = useNavigate();
  const [parameters, setParameters] = useState<Record<string, string>>({});
  const [gatewayUrl, setGatewayUrl] = useState('http://localhost:8088');
  const [configSaved, setConfigSaved] = useState(false);

  // Get global selected credential
  const selectedCredential = useStore((state) => state.selectedCredential);
  const sessionCredentials = useStore((state) => state.sessionCredentials);

  // Fetch available credentials
  const { data: credentials = [] } = useQuery<CredentialInfo[]>({
    queryKey: ['credentials'],
    queryFn: api.credentials.list,
    enabled: open,
  });

  // Combine saved and session credentials for display
  const allCredentials = [
    ...credentials,
    ...sessionCredentials,
  ];

  // Execute playbook mutation
  const executeMutation = useMutation({
    mutationFn: (params: { playbook_path: string; parameters: Record<string, string>; gateway_url?: string }) =>
      api.executions.start(params),
    onSuccess: (data) => {
      onExecutionStarted?.(data.execution_id);
      onClose();
      // Reset form
      setParameters({});
      // Navigate to execution detail page to see live browser streaming
      navigate(`/executions/${data.execution_id}`);
    },
  });

  // Load saved config or defaults when playbook changes
  useEffect(() => {
    if (playbook) {
      const savedConfig = getSavedConfig(playbook.path);

      if (savedConfig) {
        // Load saved configuration
        setGatewayUrl(savedConfig.gatewayUrl);
        setParameters(savedConfig.parameters);
        setConfigSaved(true);
      } else {
        // Load defaults
        const defaultParams: Record<string, string> = {};
        playbook.parameters.forEach((param) => {
          if (param.default) {
            defaultParams[param.name] = param.default;
          }
        });

        // Auto-fill from global credential if available
        if (selectedCredential) {
          // Auto-fill credential parameter if playbook has one
          const credentialParam = playbook.parameters.find(p => p.type === 'credential');
          if (credentialParam) {
            defaultParams[credentialParam.name] = selectedCredential.name;
          }

          // Auto-fill any username/password parameters if they exist
          const usernameParam = playbook.parameters.find(p => p.name.toLowerCase().includes('username') || p.name.toLowerCase().includes('user'));
          const passwordParam = playbook.parameters.find(p => p.name.toLowerCase().includes('password') || p.name.toLowerCase().includes('pass'));

          if (usernameParam) {
            defaultParams[usernameParam.name] = selectedCredential.username;
          }

          // For session credentials, we have the password available
          const isSessionCredential = 'isSessionOnly' in selectedCredential && selectedCredential.isSessionOnly;
          if (passwordParam && isSessionCredential) {
            defaultParams[passwordParam.name] = (selectedCredential as SessionCredential).password;
          }
        }

        setParameters(defaultParams);

        // Auto-fill gateway URL from selected credential
        if (selectedCredential?.gateway_url) {
          setGatewayUrl(selectedCredential.gateway_url);
        } else {
          setGatewayUrl('http://localhost:8088');
        }

        setConfigSaved(false);
      }
    }
  }, [playbook, selectedCredential]);

  if (!playbook) return null;

  const handleParameterChange = (name: string, value: string) => {
    setParameters((prev) => ({ ...prev, [name]: value }));
    setConfigSaved(false); // Mark as unsaved when changes are made
  };

  const handleSaveConfig = () => {
    if (!playbook) return;

    saveConfig(playbook.path, {
      gatewayUrl,
      parameters,
      savedAt: new Date().toISOString(),
    });
    setConfigSaved(true);
  };

  const handleExecute = () => {
    executeMutation.mutate({
      playbook_path: playbook.path,
      parameters,
      gateway_url: gatewayUrl,
    });
  };

  const handleSaveAndExecute = () => {
    if (!playbook) return;

    // Save config first
    saveConfig(playbook.path, {
      gatewayUrl,
      parameters,
      savedAt: new Date().toISOString(),
    });
    setConfigSaved(true);

    // Then execute
    handleExecute();
  };

  const isValid = playbook.parameters.every((param) => {
    if (!param.required) return true;
    return parameters[param.name] && parameters[param.name].trim() !== '';
  });

  const savedConfig = playbook ? getSavedConfig(playbook.path) : null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Configure Playbook: {playbook.name}</span>
          {savedConfig && (
            <Chip
              label={configSaved ? 'Configuration Saved' : 'Unsaved Changes'}
              size="small"
              color={configSaved ? 'success' : 'warning'}
              variant="outlined"
            />
          )}
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {playbook.description}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Version {playbook.version} • {playbook.step_count} steps
          </Typography>
          {savedConfig && (
            <Typography variant="caption" color="success.main" sx={{ display: 'block', mt: 0.5 }}>
              Last saved: {new Date(savedConfig.savedAt).toLocaleString()}
            </Typography>
          )}
        </Box>

        {/* Show selected credential info if available */}
        {selectedCredential && !savedConfig && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Auto-filled from global credential: <strong>{selectedCredential.name}</strong>
            {selectedCredential.gateway_url && ` (${selectedCredential.gateway_url})`}
          </Alert>
        )}

        {/* Gateway URL */}
        <TextField
          label="Gateway URL"
          fullWidth
          value={gatewayUrl}
          onChange={(e) => {
            setGatewayUrl(e.target.value);
            setConfigSaved(false);
          }}
          placeholder="http://localhost:8088"
          sx={{ mb: 2 }}
          helperText={selectedCredential?.gateway_url ? "Auto-filled from global credential" : "Ignition Gateway base URL"}
        />

        {/* Parameter inputs - filter out gateway_url since it's shown above */}
        {playbook.parameters.filter(p => p.name !== 'gateway_url').length > 0 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Parameters
            </Typography>

            {playbook.parameters
              .filter(param => param.name !== 'gateway_url')
              .map((param) => (
                <ParameterInput
                  key={param.name}
                  parameter={param}
                  value={parameters[param.name] || ''}
                  credentials={allCredentials}
                  onChange={handleParameterChange}
                />
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

      <DialogActions sx={{ gap: 1, flexWrap: 'wrap' }}>
        <Button onClick={onClose} disabled={executeMutation.isPending}>
          {configSaved ? 'Close' : 'Cancel'}
        </Button>

        <Box sx={{ flexGrow: 1 }} />

        <Button
          onClick={handleSaveConfig}
          variant="outlined"
          disabled={configSaved}
          startIcon={<SaveIcon />}
        >
          Save Config
        </Button>

        <Button
          onClick={handleExecute}
          variant="outlined"
          disabled={!isValid || executeMutation.isPending}
          startIcon={executeMutation.isPending ? <CircularProgress size={16} /> : <PlayIcon />}
        >
          {executeMutation.isPending ? 'Starting...' : 'Execute'}
        </Button>

        <Button
          onClick={handleSaveAndExecute}
          variant="contained"
          disabled={!isValid || executeMutation.isPending}
          startIcon={executeMutation.isPending ? <CircularProgress size={16} /> : <PlayIcon />}
        >
          {executeMutation.isPending ? 'Starting...' : 'Save & Execute'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
