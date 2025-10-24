/**
 * AddCredentialDialog - Dialog for adding new credentials
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
  Alert,
  IconButton,
  InputAdornment,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import type { CredentialCreate } from '../types/api';

interface AddCredentialDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (credential: CredentialCreate) => void;
  isLoading?: boolean;
  error?: string | null;
}

export function AddCredentialDialog({
  open,
  onClose,
  onSubmit,
  isLoading = false,
  error = null,
}: AddCredentialDialogProps) {
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [description, setDescription] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !username.trim() || !password.trim()) {
      return;
    }

    onSubmit({
      name: name.trim(),
      username: username.trim(),
      password: password.trim(),
      description: description.trim() || undefined,
    });
  };

  const handleClose = () => {
    // Reset form
    setName('');
    setUsername('');
    setPassword('');
    setDescription('');
    setShowPassword(false);
    onClose();
  };

  const isValid = name.trim() && username.trim() && password.trim();

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add New Credential</DialogTitle>

      <form onSubmit={handleSubmit}>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="gateway_admin"
              required
              fullWidth
              autoFocus
              helperText="Unique identifier for this credential"
              disabled={isLoading}
            />

            <TextField
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              required
              fullWidth
              disabled={isLoading}
            />

            <TextField
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              fullWidth
              disabled={isLoading}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              label="Description (Optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Gateway administrator credentials"
              fullWidth
              multiline
              rows={2}
              disabled={isLoading}
            />

            {error && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {error}
              </Alert>
            )}
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={!isValid || isLoading}
          >
            {isLoading ? 'Adding...' : 'Add Credential'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
