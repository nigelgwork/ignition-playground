/**
 * LiveBrowserView - Display live browser screenshots from WebSocket stream
 *
 * Shows browser automation in real-time at 2 FPS
 */

import { Box, Paper, Typography, Chip } from '@mui/material';
import { Computer as BrowserIcon, Pause as PausedIcon } from '@mui/icons-material';
import { useStore } from '../store';

interface LiveBrowserViewProps {
  executionId: string;
}

export function LiveBrowserView({ executionId }: LiveBrowserViewProps) {
  const currentScreenshots = useStore((state) => state.currentScreenshots);
  const screenshot = currentScreenshots.get(executionId);

  return (
    <Paper
      elevation={2}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        bgcolor: 'background.default',
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
          gap: 1,
        }}
      >
        <BrowserIcon color="primary" />
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Live Browser View
        </Typography>
        <Chip
          label="2 FPS"
          size="small"
          color="success"
          variant="outlined"
        />
      </Box>

      {/* Screenshot Display */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2,
          bgcolor: 'grey.900',
          position: 'relative',
        }}
      >
        {screenshot ? (
          <img
            src={`data:image/jpeg;base64,${screenshot.screenshot}`}
            alt="Browser screenshot"
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain',
              borderRadius: '4px',
            }}
          />
        ) : (
          <Box
            sx={{
              textAlign: 'center',
              color: 'text.secondary',
            }}
          >
            <PausedIcon sx={{ fontSize: 64, mb: 2, opacity: 0.3 }} />
            <Typography variant="body1">
              Waiting for browser screenshots...
            </Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              Screenshots will appear here when browser automation starts
            </Typography>
          </Box>
        )}
      </Box>

      {/* Footer with timestamp */}
      {screenshot && (
        <Box
          sx={{
            p: 1,
            borderTop: 1,
            borderColor: 'divider',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Typography variant="caption" color="text.secondary">
            Last updated: {new Date(screenshot.timestamp).toLocaleTimeString()}
          </Typography>
          <Chip
            label="Live"
            size="small"
            color="success"
            sx={{
              animation: 'pulse 2s infinite',
              '@keyframes pulse': {
                '0%, 100%': { opacity: 1 },
                '50%': { opacity: 0.5 },
              },
            }}
          />
        </Box>
      )}
    </Paper>
  );
}
