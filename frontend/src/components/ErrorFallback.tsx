import React from 'react';
import type { ErrorInfo } from 'react';
import {
  Box,
  Button,
  Container,
  Paper,
  Typography,
  Stack,
  Alert,
  Collapse,
  IconButton,
} from '@mui/material';
import {
  ErrorOutline as ErrorIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
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
  const [showDetails, setShowDetails] = React.useState(false);

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
    <Container maxWidth="md">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 4,
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: '100%',
            textAlign: 'center',
          }}
        >
          <Stack spacing={3} alignItems="center">
            {/* Error Icon */}
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: '50%',
                bgcolor: 'error.light',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ErrorIcon sx={{ fontSize: 48, color: 'error.dark' }} />
            </Box>

            {/* Error Message */}
            <Box>
              <Typography variant="h4" gutterBottom color="error">
                Something went wrong
              </Typography>
              <Typography variant="body1" color="text.secondary">
                We're sorry for the inconvenience. The application encountered an unexpected error.
              </Typography>
            </Box>

            {/* Action Buttons */}
            <Stack direction="row" spacing={2}>
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={handleRetry}
                size="large"
              >
                Try Again
              </Button>
              <Button
                variant="outlined"
                startIcon={<HomeIcon />}
                onClick={handleGoHome}
                size="large"
              >
                Go to Home
              </Button>
            </Stack>

            {/* Technical Details (Collapsible) */}
            {(error || errorInfo) && (
              <Box sx={{ width: '100%', mt: 2 }}>
                <Button
                  onClick={() => setShowDetails(!showDetails)}
                  endIcon={
                    <ExpandMoreIcon
                      sx={{
                        transform: showDetails ? 'rotate(180deg)' : 'rotate(0deg)',
                        transition: 'transform 0.3s',
                      }}
                    />
                  }
                  size="small"
                  color="inherit"
                >
                  {showDetails ? 'Hide' : 'Show'} Technical Details
                </Button>

                <Collapse in={showDetails}>
                  <Alert
                    severity="error"
                    sx={{
                      mt: 2,
                      textAlign: 'left',
                      '& .MuiAlert-message': {
                        width: '100%',
                      },
                    }}
                  >
                    {error && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Error Message:
                        </Typography>
                        <Typography
                          variant="body2"
                          component="pre"
                          sx={{
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            fontFamily: 'monospace',
                            fontSize: '0.875rem',
                          }}
                        >
                          {error.toString()}
                        </Typography>
                      </Box>
                    )}

                    {error?.stack && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Stack Trace:
                        </Typography>
                        <Typography
                          variant="body2"
                          component="pre"
                          sx={{
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            maxHeight: '200px',
                            overflow: 'auto',
                            bgcolor: 'action.hover',
                            p: 1,
                            borderRadius: 1,
                          }}
                        >
                          {error.stack}
                        </Typography>
                      </Box>
                    )}

                    {errorInfo?.componentStack && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Component Stack:
                        </Typography>
                        <Typography
                          variant="body2"
                          component="pre"
                          sx={{
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            maxHeight: '200px',
                            overflow: 'auto',
                            bgcolor: 'action.hover',
                            p: 1,
                            borderRadius: 1,
                          }}
                        >
                          {errorInfo.componentStack}
                        </Typography>
                      </Box>
                    )}
                  </Alert>
                </Collapse>
              </Box>
            )}

            {/* Help Text */}
            <Typography variant="caption" color="text.secondary" sx={{ mt: 2 }}>
              If this problem persists, please contact support with the technical details above.
            </Typography>
          </Stack>
        </Paper>
      </Box>
    </Container>
  );
};
