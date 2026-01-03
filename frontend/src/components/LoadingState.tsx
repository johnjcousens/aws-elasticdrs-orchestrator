/**
 * Loading State Component
 * 
 * Displays loading skeleton or spinner while data is being fetched.
 * Provides consistent loading experience across the application.
 */

import React from 'react';
import { Spinner, Box } from '@cloudscape-design/components';

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
 * @param rows - Number of skeleton rows to display (default: 5) - Note: skeleton not implemented in CloudScape
 * @param height - Height of each skeleton row (default: 60) - Note: skeleton not implemented in CloudScape
 */
export const LoadingState: React.FC<LoadingStateProps> = ({
  variant = 'spinner',
  message = 'Loading...',
}) => {
  if (variant === 'inline') {
    return (
      <Box padding={{ vertical: 's', horizontal: 'm' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Spinner size="normal" />
          <span style={{ fontSize: '14px', color: '#5f6b7a' }}>
            {message}
          </span>
        </div>
      </Box>
    );
  }

  if (variant === 'skeleton') {
    // CloudScape doesn't have skeleton components, fall back to spinner
    return (
      <Box padding="l">
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <Spinner size="large" />
          <span style={{ fontSize: '14px', color: '#5f6b7a' }}>
            {message}
          </span>
        </div>
      </Box>
    );
  }

  // Default: centered spinner
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px',
        gap: '16px',
      }}
    >
      <Spinner size="large" />
      <span style={{ fontSize: '14px', color: '#5f6b7a' }}>
        {message}
      </span>
    </div>
  );
};
