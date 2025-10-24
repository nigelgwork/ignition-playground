/**
 * PlaybookCard - Display playbook information with action button
 */

import { useState } from 'react';
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
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import type { PlaybookInfo } from '../types/api';

interface PlaybookCardProps {
  playbook: PlaybookInfo;
  onExecute: (playbook: PlaybookInfo) => void;
}

// Determine test status based on playbook path
function getTestStatus(path: string): 'tested' | 'untested' | 'example' {
  if (path.includes('/examples/')) return 'example';
  if (path.includes('/gateway/simple_health_check')) return 'tested';
  if (path.includes('/gateway/module_upgrade')) return 'tested';
  if (path.includes('/gateway/backup_and_restart')) return 'tested';
  return 'untested'; // Default to untested for safety
}

export function PlaybookCard({ playbook, onExecute }: PlaybookCardProps) {
  const [expanded, setExpanded] = useState(false);
  const testStatus = getTestStatus(playbook.path);
  const isDisabled = testStatus === 'untested';

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        opacity: isDisabled ? 0.6 : 1,
        border: isDisabled ? '1px solid' : 'none',
        borderColor: 'warning.main',
      }}
    >
      <CardContent sx={{ flexGrow: 1, pb: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Typography variant="h6" gutterBottom sx={{ flexGrow: 1 }}>
            {playbook.name}
          </Typography>

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
              <ListItem sx={{ py: 0.5 }}>
                <ListItemText
                  primary={
                    <Typography variant="caption" color="text.secondary">
                      • Authentication & validation
                    </Typography>
                  }
                />
              </ListItem>
              <ListItem sx={{ py: 0.5 }}>
                <ListItemText
                  primary={
                    <Typography variant="caption" color="text.secondary">
                      • Main operations
                    </Typography>
                  }
                />
              </ListItem>
              <ListItem sx={{ py: 0.5 }}>
                <ListItemText
                  primary={
                    <Typography variant="caption" color="text.secondary">
                      • Verification & cleanup
                    </Typography>
                  }
                />
              </ListItem>
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

      <CardActions sx={{ pt: 0 }}>
        <Tooltip
          title={
            isDisabled
              ? 'This playbook has not been tested yet. Enable with caution.'
              : 'Execute this playbook'
          }
        >
          <span style={{ width: '100%' }}>
            <Button
              size="small"
              variant="contained"
              startIcon={<PlayIcon />}
              onClick={() => onExecute(playbook)}
              fullWidth
              disabled={isDisabled}
              aria-label={`Execute ${playbook.name} playbook`}
            >
              {isDisabled ? 'Not Tested' : 'Execute'}
            </Button>
          </span>
        </Tooltip>
      </CardActions>
    </Card>
  );
}
