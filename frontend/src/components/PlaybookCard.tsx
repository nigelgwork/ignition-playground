/**
 * PlaybookCard - Display playbook information with action button
 */

import { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  Divider,
  List,
  ListItem,
  ListItemText,
  Tooltip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import {
  Settings as ConfigureIcon,
  PlayArrow as PlayIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Download as DownloadIcon,
  MoreVert as MoreVertIcon,
  List as ViewStepsIcon,
  Verified as VerifiedIcon,
  ToggleOn as EnableIcon,
  ToggleOff as DisableIcon,
  Info as InfoIcon,
  Close as ClearIcon,
  BugReport as DebugIcon,
} from '@mui/icons-material';
import type { PlaybookInfo } from '../types/api';
import { useStore } from '../store';
import { api } from '../api/client';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface PlaybookCardProps {
  playbook: PlaybookInfo;
  onConfigure: (playbook: PlaybookInfo) => void;
  onExecute?: (playbook: PlaybookInfo) => void;
  onExport?: (playbook: PlaybookInfo) => void;
  onViewSteps?: (playbook: PlaybookInfo) => void;
}

// Get saved config for preview
interface SavedConfig {
  gatewayUrl: string;
  parameters: Record<string, string>;
  savedAt: string;
}

function getSavedConfigPreview(playbookPath: string): SavedConfig | null {
  const stored = localStorage.getItem(`playbook_config_${playbookPath}`);
  return stored ? JSON.parse(stored) : null;
}

// Determine test status based on playbook path
function getTestStatus(path: string): 'tested' | 'untested' | 'example' {
  if (path.includes('/examples/')) return 'example';
  // Only Reset Gateway Trial is tested
  if (path.includes('/gateway/reset_gateway_trial')) return 'tested';
  return 'untested'; // Default to untested for safety
}

export function PlaybookCard({ playbook, onConfigure, onExecute, onExport, onViewSteps }: PlaybookCardProps) {
  const queryClient = useQueryClient();
  const [savedConfig, setSavedConfig] = useState<SavedConfig | null>(getSavedConfigPreview(playbook.path));
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [debugMode, setDebugMode] = useState(() => {
    const stored = localStorage.getItem(`playbook_debug_${playbook.path}`);
    return stored === 'true';
  });
  const selectedCredential = useStore((state) => state.selectedCredential);

  const testStatus = getTestStatus(playbook.path);
  const isDisabled = !playbook.enabled;

  // Check for saved config updates periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setSavedConfig(getSavedConfigPreview(playbook.path));
    }, 1000);
    return () => clearInterval(interval);
  }, [playbook.path]);

  // Mutation for verifying playbook
  const verifyMutation = useMutation({
    mutationFn: () => api.playbooks.verify(playbook.path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] });
      setSnackbarMessage('Playbook marked as verified');
      setSnackbarOpen(true);
      setMenuAnchor(null);
    },
    onError: (error) => {
      setSnackbarMessage(`Failed to verify: ${(error as Error).message}`);
      setSnackbarOpen(true);
    },
  });

  // Mutation for unverifying playbook
  const unverifyMutation = useMutation({
    mutationFn: () => api.playbooks.unverify(playbook.path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] });
      setSnackbarMessage('Playbook verification removed');
      setSnackbarOpen(true);
      setMenuAnchor(null);
    },
    onError: (error) => {
      setSnackbarMessage(`Failed to unverify: ${(error as Error).message}`);
      setSnackbarOpen(true);
    },
  });

  // Mutation for enabling playbook
  const enableMutation = useMutation({
    mutationFn: () => api.playbooks.enable(playbook.path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] });
      setSnackbarMessage('Playbook enabled');
      setSnackbarOpen(true);
      setMenuAnchor(null);
    },
    onError: (error) => {
      setSnackbarMessage(`Failed to enable: ${(error as Error).message}`);
      setSnackbarOpen(true);
    },
  });

  // Mutation for disabling playbook
  const disableMutation = useMutation({
    mutationFn: () => api.playbooks.disable(playbook.path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] });
      setSnackbarMessage('Playbook disabled');
      setSnackbarOpen(true);
      setMenuAnchor(null);
    },
    onError: (error) => {
      setSnackbarMessage(`Failed to disable: ${(error as Error).message}`);
      setSnackbarOpen(true);
    },
  });

  const handleDebugModeToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newDebugMode = event.target.checked;
    setDebugMode(newDebugMode);
    localStorage.setItem(`playbook_debug_${playbook.path}`, newDebugMode.toString());
  };

  const handleExecuteClick = () => {
    if (onExecute) {
      onExecute(playbook);
    } else {
      // Fallback to configure if no execute handler
      onConfigure(playbook);
    }
  };

  return (
    <Card
      elevation={3}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        opacity: isDisabled ? 0.6 : 1,
        border: '2px solid',
        borderColor: isDisabled ? 'warning.main' : 'divider',
        borderRadius: 2,
        backgroundColor: 'background.paper',
        transition: 'all 0.3s ease-in-out',
        '&:hover': {
          transform: 'translateY(-6px)',
          boxShadow: (theme) => theme.shadows[12],
          borderColor: 'primary.main',
          borderWidth: '3px',
          backgroundColor: 'action.hover',
        },
        cursor: 'grab',
      }}
    >
      <CardContent sx={{ flexGrow: 1, pb: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Typography variant="h6" gutterBottom sx={{ flexGrow: 1 }}>
            {playbook.name}
          </Typography>

          {/* Menu Button */}
          {onExport && (
            <IconButton
              size="small"
              onClick={(e) => setMenuAnchor(e.currentTarget)}
              sx={{ ml: 1 }}
            >
              <MoreVertIcon fontSize="small" />
            </IconButton>
          )}

          {/* Test Status Icon */}
          {(testStatus === 'tested' || testStatus === 'untested') && (
            <Tooltip
              title={
                testStatus === 'tested'
                  ? 'Tested and verified'
                  : 'Not yet tested - use with caution'
              }
            >
              {testStatus === 'tested' ? (
                <CheckIcon color="success" fontSize="small" />
              ) : (
                <WarningIcon color="warning" fontSize="small" />
              )}
            </Tooltip>
          )}
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {playbook.description}
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
          <Chip
            label={`v${playbook.version}.r${playbook.revision}`}
            size="small"
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`${playbook.step_count} steps`}
            size="small"
            variant="outlined"
          />
          {playbook.parameter_count > 0 && (
            <Chip
              label={`${playbook.parameter_count} params`}
              size="small"
              variant="outlined"
            />
          )}
          {playbook.verified && (
            <Chip
              icon={<VerifiedIcon />}
              label="Verified"
              size="small"
              color="success"
              variant="outlined"
            />
          )}
          {!playbook.enabled && (
            <Chip
              label="Disabled"
              size="small"
              color="error"
              variant="outlined"
            />
          )}
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {playbook.path.split('/').slice(-2).join('/')}
        </Typography>

        {/* Saved Configuration Preview */}
        {savedConfig && (
          <Box sx={{ mt: 1, mb: 2, p: 1, bgcolor: 'success.dark', borderRadius: 1, border: '1px solid', borderColor: 'success.main' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="caption" color="success.light" fontWeight="bold">
                  ✓ Configured
                </Typography>
                <Typography variant="caption" color="success.light" sx={{ display: 'block' }}>
                  Gateway: {savedConfig.gatewayUrl}
                </Typography>
                {Object.keys(savedConfig.parameters).length > 0 && (
                  <Typography variant="caption" color="success.light" sx={{ display: 'block' }}>
                    {Object.keys(savedConfig.parameters).length} parameter(s) set
                  </Typography>
                )}
              </Box>
              <Tooltip title="Clear manual config (use global credential instead)">
                <IconButton
                  size="small"
                  onClick={() => {
                    localStorage.removeItem(`playbook_config_${playbook.path}`);
                    setSavedConfig(null);
                  }}
                  sx={{ color: 'success.light', ml: 1, mt: -0.5 }}
                >
                  <ClearIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        )}

        {/* Debug Mode Toggle */}
        <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={debugMode}
                onChange={handleDebugModeToggle}
                size="small"
                disabled={isDisabled}
                icon={<DebugIcon />}
                checkedIcon={<DebugIcon />}
              />
            }
            label={
              <Typography variant="caption" color={debugMode ? 'primary' : 'text.secondary'}>
                Debug Mode {debugMode ? 'ON' : 'OFF'}
              </Typography>
            }
          />
        </Box>

      </CardContent>

      <CardActions sx={{ pt: 0, gap: 1 }}>
        {/* Configure Button */}
        <Tooltip title="Configure parameters for this playbook">
          <span style={{ flex: 1 }}>
            <Button
              size="small"
              variant="outlined"
              startIcon={<ConfigureIcon />}
              onClick={() => onConfigure(playbook)}
              fullWidth
              disabled={isDisabled}
              aria-label={`Configure ${playbook.name} playbook`}
            >
              Configure
            </Button>
          </span>
        </Tooltip>

        {/* Execute Button */}
        <Tooltip title={
          isDisabled ? 'Enable this playbook first' :
          selectedCredential ? `Execute with global credential: ${selectedCredential.name}` :
          savedConfig ? 'Execute with saved configuration' :
          'Select a global credential or configure this playbook first'
        }>
          <span style={{ flex: 1 }}>
            <Button
              size="small"
              variant="contained"
              startIcon={<PlayIcon />}
              onClick={handleExecuteClick}
              fullWidth
              disabled={isDisabled || (!savedConfig && !selectedCredential)}
              aria-label={`Execute ${playbook.name} playbook`}
            >
              Execute
            </Button>
          </span>
        </Tooltip>
      </CardActions>

      {/* Menu for all options */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        {/* Show Details */}
        <MenuItem
          onClick={() => {
            setMenuAnchor(null);
            setDetailsDialogOpen(true);
          }}
        >
          <InfoIcon fontSize="small" sx={{ mr: 1 }} />
          Show Details
        </MenuItem>

        <Divider />

        {/* Verify/Unverify */}
        {playbook.verified ? (
          <MenuItem
            onClick={() => unverifyMutation.mutate()}
            disabled={unverifyMutation.isPending}
          >
            <VerifiedIcon fontSize="small" sx={{ mr: 1 }} />
            Remove Verification
          </MenuItem>
        ) : (
          <MenuItem
            onClick={() => verifyMutation.mutate()}
            disabled={verifyMutation.isPending}
          >
            <VerifiedIcon fontSize="small" sx={{ mr: 1 }} />
            Mark as Verified
          </MenuItem>
        )}

        {/* Enable/Disable */}
        {playbook.enabled ? (
          <MenuItem
            onClick={() => disableMutation.mutate()}
            disabled={disableMutation.isPending}
          >
            <DisableIcon fontSize="small" sx={{ mr: 1 }} />
            Disable Playbook
          </MenuItem>
        ) : (
          <MenuItem
            onClick={() => enableMutation.mutate()}
            disabled={enableMutation.isPending}
          >
            <EnableIcon fontSize="small" sx={{ mr: 1 }} />
            Enable Playbook
          </MenuItem>
        )}

        <Divider />

        {/* View All Steps */}
        {onViewSteps && (
          <MenuItem
            onClick={() => {
              setMenuAnchor(null);
              onViewSteps(playbook);
            }}
          >
            <ViewStepsIcon fontSize="small" sx={{ mr: 1 }} />
            View All Steps
          </MenuItem>
        )}

        {/* Export */}
        <MenuItem
          onClick={() => {
            setMenuAnchor(null);
            onExport?.(playbook);
          }}
        >
          <DownloadIcon fontSize="small" sx={{ mr: 1 }} />
          Export Playbook
        </MenuItem>
      </Menu>

      {/* Details Dialog */}
      <Dialog
        open={detailsDialogOpen}
        onClose={() => setDetailsDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{playbook.name} - Details</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary" fontWeight="bold">
              Steps ({playbook.step_count}):
            </Typography>
            <List dense sx={{ py: 0 }}>
              {playbook.steps && playbook.steps.length > 0 ? (
                playbook.steps.map((step, index) => (
                  <ListItem key={step.id} sx={{ py: 0.5 }}>
                    <ListItemText
                      primary={
                        <Typography variant="caption" color="text.secondary">
                          {index + 1}. {step.name}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary">
                          Type: {step.type} | Timeout: {step.timeout}s
                        </Typography>
                      }
                    />
                  </ListItem>
                ))
              ) : (
                <ListItem sx={{ py: 0.5 }}>
                  <ListItemText
                    primary={
                      <Typography variant="caption" color="text.secondary">
                        • {playbook.step_count} step(s)
                      </Typography>
                    }
                  />
                </ListItem>
              )}
            </List>

            {playbook.parameter_count > 0 && (
              <>
                <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ mt: 2 }}>
                  Required Parameters:
                </Typography>
                <List dense sx={{ py: 0 }}>
                  <ListItem sx={{ py: 0.5 }}>
                    <ListItemText
                      primary={
                        <Typography variant="caption" color="text.secondary">
                          • Gateway URL
                        </Typography>
                      }
                    />
                  </ListItem>
                  <ListItem sx={{ py: 0.5 }}>
                    <ListItemText
                      primary={
                        <Typography variant="caption" color="text.secondary">
                          • Gateway Credentials
                        </Typography>
                      }
                    />
                  </ListItem>
                </List>
              </>
            )}

            {playbook.verified && playbook.verified_at && (
              <Box sx={{ mt: 2, p: 1, bgcolor: 'success.dark', borderRadius: 1 }}>
                <Typography variant="caption" color="success.light" fontWeight="bold">
                  Verified
                </Typography>
                <Typography variant="caption" color="success.light" sx={{ display: 'block' }}>
                  At: {new Date(playbook.verified_at).toLocaleString()}
                </Typography>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      />
    </Card>
  );
}
