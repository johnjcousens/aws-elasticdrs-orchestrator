/**
 * Loading State Component
 * 
 * Displays loading skeleton or spinner while data is being fetched.
 * Provides consistent loading experience across the application.
 */

import React from 'react';
import { Box, CircularProgress, Skeleton, Stack, Typography } from '@mui/material';

export interface LoadingStateProps {
  variant?: 'spinner' | 'skeleton' | 'inline';
  message?: string;
  rows?: number;
  height?: number | string;
}

/**
 * LoadingState Component
 * 
 * @param variant - Loading display type (spinner, skeleton, or inline)
 * @param message - Optional loading message
 * @param rows - Number of skeleton rows to display (default: 5)
 * @param height - Height of each skeleton row (default: 60)
 */
export const LoadingState: React.FC<LoadingStateProps> = ({
  variant = 'spinner',
  message = 'Loading...',
  rows = 5,
  height = 60,
}) => {
  if (variant === 'inline') {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
        <CircularProgress size={20} />
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      </Box>
    );
  }

  if (variant === 'skeleton') {
    return (
      <Stack spacing={2} sx={{ p: 3 }}>
        {Array.from({ length: rows }).map((_, index) => (
          <Skeleton
            key={index}
            variant="rectangular"
            height={height}
            animation="wave"
            sx={{ borderRadius: 1 }}
          />
        ))}
      </Stack>
    );
  }

  // Default: centered spinner
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 400,
        gap: 2,
      }}
    >
      <CircularProgress size={48} />
      <Typography variant="body1" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
};
