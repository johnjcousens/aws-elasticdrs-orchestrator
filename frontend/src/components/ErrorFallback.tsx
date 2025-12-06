import React from 'react';
import type { ErrorInfo } from 'react';
import {
  Box,
  Button,
  Alert,
  SpaceBetween,
  Container,
  ExpandableSection,
} from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';

interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  onReset?: () => void;
}

/**
 * Error Fallback UI Component
 * 
 * Displays a user-friendly error message when an error boundary catches an error.
 * Provides options to:
 * - Retry the failed operation
 * - Return to home page
 * - View technical error details (for debugging)
 */
export const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  errorInfo,
  onReset,
}) => {
  const navigate = useNavigate();

  const handleRetry = () => {
    if (onReset) {
      onReset();
    } else {
      // Fallback: reload the page
      window.location.reload();
    }
  };

  const handleGoHome = () => {
    if (onReset) {
      onReset();
    }
    navigate('/');
  };

  return (
    <Container>
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
        }}
      >
        <div
          style={{
            maxWidth: '800px',
            width: '100%',
            textAlign: 'center',
          }}
        >
          <SpaceBetween size="l">
            {/* Error Icon */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
              }}
            >
              <div
                style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '50%',
                  backgroundColor: '#fef2f2',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '48px',
                }}
              >
                ⚠️
              </div>
            </div>

            {/* Error Message */}
            <Box textAlign="center">
              <h1 style={{ color: '#d13212', marginBottom: '8px' }}>
                Something went wrong
              </h1>
              <p style={{ color: '#5f6b7a', fontSize: '16px' }}>
                We're sorry for the inconvenience. The application encountered an unexpected error.
              </p>
            </Box>

            {/* Action Buttons */}
            <Box textAlign="center">
              <SpaceBetween direction="horizontal" size="s">
                <Button
                  variant="primary"
                  iconName="refresh"
                  onClick={handleRetry}
                >
                  Try Again
                </Button>
                <Button
                  onClick={handleGoHome}
                >
                  Go to Home
                </Button>
              </SpaceBetween>
            </Box>

            {/* Technical Details (Expandable) */}
            {(error || errorInfo) && (
              <Box>
                <ExpandableSection headerText="Technical Details" variant="footer">
                  <Alert type="error">
                    <SpaceBetween size="m">
                      {error && (
                        <div>
                          <strong>Error Message:</strong>
                          <pre
                            style={{
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                              fontFamily: 'monospace',
                              fontSize: '14px',
                              marginTop: '8px',
                            }}
                          >
                            {error.toString()}
                          </pre>
                        </div>
                      )}

                      {error?.stack && (
                        <div>
                          <strong>Stack Trace:</strong>
                          <pre
                            style={{
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                              fontFamily: 'monospace',
                              fontSize: '12px',
                              maxHeight: '200px',
                              overflow: 'auto',
                              backgroundColor: '#f5f5f5',
                              padding: '8px',
                              borderRadius: '4px',
                              marginTop: '8px',
                            }}
                          >
                            {error.stack}
                          </pre>
                        </div>
                      )}

                      {errorInfo?.componentStack && (
                        <div>
                          <strong>Component Stack:</strong>
                          <pre
                            style={{
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                              fontFamily: 'monospace',
                              fontSize: '12px',
                              maxHeight: '200px',
                              overflow: 'auto',
                              backgroundColor: '#f5f5f5',
                              padding: '8px',
                              borderRadius: '4px',
                              marginTop: '8px',
                            }}
                          >
                            {errorInfo.componentStack}
                          </pre>
                        </div>
                      )}
                    </SpaceBetween>
                  </Alert>
                </ExpandableSection>
              </Box>
            )}

            {/* Help Text */}
            <Box textAlign="center">
              <p style={{ color: '#5f6b7a', fontSize: '12px', marginTop: '16px' }}>
                If this problem persists, please contact support with the technical details above.
              </p>
            </Box>
          </SpaceBetween>
        </div>
      </div>
    </Container>
  );
};
