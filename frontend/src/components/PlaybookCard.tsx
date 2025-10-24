/**
 * PlaybookCard - Display playbook information with action button
 */

import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
} from '@mui/material';
import { PlayArrow as PlayIcon } from '@mui/icons-material';
import type { PlaybookInfo } from '../types/api';

interface PlaybookCardProps {
  playbook: PlaybookInfo;
  onExecute: (playbook: PlaybookInfo) => void;
}

export function PlaybookCard({ playbook, onExecute }: PlaybookCardProps) {
  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6" gutterBottom>
          {playbook.name}
        </Typography>

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
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {playbook.path.split('/').slice(-2).join('/')}
        </Typography>
      </CardContent>

      <CardActions>
        <Button
          size="small"
          variant="contained"
          startIcon={<PlayIcon />}
          onClick={() => onExecute(playbook)}
          fullWidth
        >
          Execute
        </Button>
      </CardActions>
    </Card>
  );
}
