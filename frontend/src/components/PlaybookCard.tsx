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
  Collapse,
  Divider,
  List,
  ListItem,
  ListItemText,
  Tooltip,
  Switch,
  FormControlLabel,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Settings as ConfigureIcon,
  PlayArrow as PlayIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Download as DownloadIcon,
  MoreVert as MoreVertIcon,
  List as ViewStepsIcon,
} from '@mui/icons-material';
import type { PlaybookInfo } from '../types/api';

interface PlaybookCardProps {
  playbook: PlaybookInfo;
  onConfigure: (playbook: PlaybookInfo) => void;
  onExecute?: (playbook: PlaybookInfo) => void;
  onExport?: (playbook: PlaybookInfo) => void;
  onViewSteps?: (playbook: PlaybookInfo) => void;
}

// Get enabled playbooks from localStorage
function getEnabledPlaybooks(): Set<string> {
  const stored = localStorage.getItem('enabledPlaybooks');
  return stored ? new Set(JSON.parse(stored)) : new Set();
}

// Save enabled playbooks to localStorage
function saveEnabledPlaybooks(enabled: Set<string>) {
  localStorage.setItem('enabledPlaybooks', JSON.stringify(Array.from(enabled)));
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
  const [expanded, setExpanded] = useState(false);
  const [enabledPlaybooks, setEnabledPlaybooks] = useState<Set<string>>(getEnabledPlaybooks());
  const [savedConfig, setSavedConfig] = useState<SavedConfig | null>(getSavedConfigPreview(playbook.path));
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  const testStatus = getTestStatus(playbook.path);
  const isManuallyEnabled = enabledPlaybooks.has(playbook.path);
  const isDisabled = testStatus === 'untested' && !isManuallyEnabled;

  // Check for saved config updates periodically
  useEffect(() => {
    const interval = setInterval(() => {
      setSavedConfig(getSavedConfigPreview(playbook.path));
    }, 1000);
    return () => clearInterval(interval);
  }, [playbook.path]);

  const handleToggleEnabled = () => {
    const newEnabled = new Set(enabledPlaybooks);
    if (isManuallyEnabled) {
      newEnabled.delete(playbook.path);
    } else {
      newEnabled.add(playbook.path);
    }
    setEnabledPlaybooks(newEnabled);
    saveEnabledPlaybooks(newEnabled);
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
            label={`v${playbook.version}`}
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
          {testStatus === 'untested' && (
            <Chip
              label="Untested"
              size="small"
              color="warning"
              variant="outlined"
            />
          )}
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {playbook.path.split('/').slice(-2).join('/')}
        </Typography>

        {/* Saved Configuration Preview */}
        {savedConfig && (
          <Box sx={{ mt: 1, p: 1, bgcolor: 'success.dark', borderRadius: 1, border: '1px solid', borderColor: 'success.main' }}>
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
        )}

        {/* Expandable Details Section */}
        <Box sx={{ mt: 1 }}>
          <Button
            size="small"
            onClick={() => setExpanded(!expanded)}
            endIcon={
              <ExpandMoreIcon
                sx={{
                  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s',
                }}
              />
            }
            sx={{ textTransform: 'none', p: 0, minWidth: 0 }}
          >
            <Typography variant="caption">
              {expanded ? 'Hide' : 'Show'} Details
            </Typography>
          </Button>
        </Box>

        <Collapse in={expanded} timeout="auto">
          <Divider sx={{ my: 1 }} />
          <Box sx={{ mt: 1 }}>
            <Typography variant="caption" color="text.secondary" fontWeight="bold">
              Steps ({playbook.step_count}):
            </Typography>
            <List dense sx={{ py: 0 }}>
              {playbook.steps && playbook.steps.length > 0 ? (
                playbook.steps.slice(0, 5).map((step, index) => (
                  <ListItem key={step.id} sx={{ py: 0.5 }}>
                    <ListItemText
                      primary={
                        <Typography variant="caption" color="text.secondary">
                          {index + 1}. {step.name}
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
              {playbook.steps && playbook.steps.length > 5 && (
                <ListItem sx={{ py: 0.5 }}>
                  <ListItemText
                    primary={
                      <Typography variant="caption" color="primary" fontStyle="italic">
                        + {playbook.steps.length - 5} more steps...
                      </Typography>
                    }
                  />
                </ListItem>
              )}
            </List>

            {playbook.parameter_count > 0 && (
              <>
                <Typography variant="caption" color="text.secondary" fontWeight="bold" sx={{ mt: 1 }}>
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
          </Box>
        </Collapse>
      </CardContent>

      <CardActions sx={{ pt: 0, gap: 1, flexDirection: 'column', alignItems: 'stretch' }}>
        {/* Enable/Disable Switch - Always available at top */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', px: 1 }}>
          <Typography variant="caption" color="text.secondary">
            {testStatus === 'tested' ? 'Tested' : 'Enable for testing'}
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={isManuallyEnabled || testStatus === 'tested'}
                onChange={handleToggleEnabled}
                disabled={testStatus === 'tested'}
                size="small"
              />
            }
            label=""
            sx={{ m: 0 }}
          />
        </Box>

        {/* Button Row */}
        <Box sx={{ display: 'flex', gap: 1 }}>
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
            !savedConfig ? 'Configure this playbook first' :
            'Execute with saved configuration'
          }>
            <span style={{ flex: 1 }}>
              <Button
                size="small"
                variant="contained"
                startIcon={<PlayIcon />}
                onClick={handleExecuteClick}
                fullWidth
                disabled={isDisabled || !savedConfig}
                aria-label={`Execute ${playbook.name} playbook`}
              >
                Execute
              </Button>
            </span>
          </Tooltip>
        </Box>
      </CardActions>

      {/* Menu for Export and other options */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
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
    </Card>
  );
}
