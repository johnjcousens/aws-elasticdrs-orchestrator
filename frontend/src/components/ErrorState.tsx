/**
 * Error State Component
 * 
 * Displays error messages with optional retry functionality.
 * Provides consistent error handling across the application.
 */

import React from 'react';
import { Box, Typography, Button, Alert, AlertTitle } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import RefreshIcon from '@mui/icons-material/Refresh';

export interface ErrorStateProps {
  error: string | Error;
  title?: string;
  onRetry?: () => void;
  variant?: 'full' | 'inline' | 'alert';
}

/**
 * ErrorState Component
 * 
 * @param error - Error message or Error object
 * @param title - Optional error title
 * @param onRetry - Optional retry callback
 * @param variant - Display variant (full, inline, or alert)
 */
export const ErrorState: React.FC<ErrorStateProps> = ({
  error,
  title = 'Error',
  onRetry,
  variant = 'full',
}) => {
  const errorMessage = error instanceof Error ? error.message : error;

  if (variant === 'alert') {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        <AlertTitle>{title}</AlertTitle>
        {errorMessage}
        {onRetry && (
          <Button
            size="small"
            startIcon={<RefreshIcon />}
            onClick={onRetry}
            sx={{ mt: 1 }}
          >
            Retry
          </Button>
        )}
      </Alert>
    );
  }

  if (variant === 'inline') {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
        <ErrorOutlineIcon color="error" />
        <Box sx={{ flex: 1 }}>
          <Typography variant="body2" color="error">
            {errorMessage}
          </Typography>
        </Box>
        {onRetry && (
          <Button size="small" startIcon={<RefreshIcon />} onClick={onRetry}>
            Retry
          </Button>
        )}
      </Box>
    );
  }

  // Default: full page error
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 400,
        gap: 2,
        textAlign: 'center',
        p: 3,
      }}
    >
      <ErrorOutlineIcon sx={{ fontSize: 64, color: 'error.main' }} />
      <Typography variant="h5" color="error">
        {title}
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600 }}>
        {errorMessage}
      </Typography>
      {onRetry && (
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={onRetry}
          sx={{ mt: 2 }}
        >
          Try Again
        </Button>
      )}
    </Box>
  );
};
