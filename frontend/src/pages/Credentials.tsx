/**
 * Credentials page - Manage Gateway credentials
 */

import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { CredentialCard } from '../components/CredentialCard';
import { AddCredentialDialog } from '../components/AddCredentialDialog';
import type { CredentialInfo, CredentialCreate } from '../types/api';

export function Credentials() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  // Fetch credentials
  const { data: credentials = [], isLoading, error } = useQuery<CredentialInfo[]>({
    queryKey: ['credentials'],
    queryFn: api.credentials.list,
  });

  // Add credential mutation
  const addMutation = useMutation({
    mutationFn: (credential: CredentialCreate) => api.credentials.create(credential),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      setDialogOpen(false);
      setSnackbarMessage(`Credential "${data.name}" added successfully`);
      setSnackbarOpen(true);
    },
  });

  // Delete credential mutation
  const deleteMutation = useMutation({
    mutationFn: (name: string) => api.credentials.delete(name),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      setSnackbarMessage(`Credential "${data.name}" deleted successfully`);
      setSnackbarOpen(true);
    },
    onError: (error) => {
      setSnackbarMessage(`Failed to delete: ${(error as Error).message}`);
      setSnackbarOpen(true);
    },
  });

  const handleAddCredential = (credential: CredentialCreate) => {
    addMutation.mutate(credential);
  };

  const handleDeleteCredential = (name: string) => {
    deleteMutation.mutate(name);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Credentials
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage Gateway login credentials (stored encrypted locally)
          </Typography>
        </Box>

        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
          aria-label="Add new credential"
        >
          Add Credential
        </Button>
      </Box>

      {/* Loading state */}
      {isLoading && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CircularProgress size={20} aria-label="Loading credentials" />
          <Typography variant="body2" color="text.secondary">
            Loading credentials...
          </Typography>
        </Box>
      )}

      {/* Error state */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load credentials: {(error as Error).message}
        </Alert>
      )}

      {/* Empty state */}
      {!isLoading && !error && credentials.length === 0 && (
        <Alert severity="info">
          No credentials yet. Add your first Gateway credential to get started.
        </Alert>
      )}

      {/* Credentials Grid */}
      {!isLoading && !error && credentials.length > 0 && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(3, 1fr)',
            },
            gap: 3,
          }}
        >
          {credentials.map((credential) => (
            <CredentialCard
              key={credential.name}
              credential={credential}
              onDelete={handleDeleteCredential}
            />
          ))}
        </Box>
      )}

      {/* Add Credential Dialog */}
      <AddCredentialDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleAddCredential}
        isLoading={addMutation.isPending}
        error={addMutation.error ? (addMutation.error as Error).message : null}
      />

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      />
    </Box>
  );
}
