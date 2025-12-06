/**
 * Error State Component
 * 
 * Displays error messages with optional retry functionality.
 * Provides consistent error handling across the application.
 */

import React from 'react';
import { Box, Button, Alert } from '@cloudscape-design/components';

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
      <Alert
        type="error"
        header={title}
        action={
          onRetry ? (
            <Button onClick={onRetry} iconName="refresh">
              Retry
            </Button>
          ) : undefined
        }
      >
        {errorMessage}
      </Alert>
    );
  }

  if (variant === 'inline') {
    return (
      <Box padding={{ vertical: 's', horizontal: 'm' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ flex: 1, color: '#d13212' }}>
            {errorMessage}
          </div>
          {onRetry && (
            <Button onClick={onRetry} iconName="refresh">
              Retry
            </Button>
          )}
        </div>
      </Box>
    );
  }

  // Default: full page error
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px',
        gap: '16px',
        textAlign: 'center',
        padding: '24px',
      }}
    >
      <div style={{ fontSize: '48px', color: '#d13212' }}>⚠️</div>
      <h2 style={{ color: '#d13212', margin: 0 }}>{title}</h2>
      <p style={{ color: '#5f6b7a', maxWidth: '600px', margin: 0 }}>
        {errorMessage}
      </p>
      {onRetry && (
        <Button variant="primary" onClick={onRetry} iconName="refresh">
          Try Again
        </Button>
      )}
    </div>
  );
};
