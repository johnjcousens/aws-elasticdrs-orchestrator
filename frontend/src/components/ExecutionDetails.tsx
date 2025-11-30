/**
 * Execution Details Modal
 * 
 * Modal dialog for viewing detailed execution information with real-time updates.
 * Includes wave progress, server status, and cancel functionality.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Stack,
  Typography,
  Alert,
  LinearProgress,
  Chip,
  Divider,
  IconButton,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import RefreshIcon from '@mui/icons-material/Refresh';
import CancelIcon from '@mui/icons-material/Cancel';
import { LoadingState } from './LoadingState';
import { StatusBadge } from './StatusBadge';
import { DateTimeDisplay } from './DateTimeDisplay';
import { WaveProgress } from './WaveProgress';
import { ConfirmDialog } from './ConfirmDialog';
import apiClient from '../services/api';
import type { Execution } from '../types';

interface ExecutionDetailsProps {
  open: boolean;
  executionId: string | null;
  onClose: () => void;
  onRefresh?: () => void;
}

/**
 * ExecutionDetails Component
 * 
 * Displays comprehensive execution details with real-time monitoring.
 */
export const ExecutionDetails: React.FC<ExecutionDetailsProps> = ({
  open,
  executionId,
  onClose,
  onRefresh,
}) => {
  const [execution, setExecution] = useState<Execution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  // Fetch execution details
  useEffect(() => {
    if (open && executionId) {
      fetchExecution();
    }
  }, [open, executionId]);

  // Real-time polling for active executions
  useEffect(() => {
    if (!open || !execution) return;

    const isActive = 
      execution.status === 'in_progress' || 
      execution.status === 'pending' ||
      execution.status === 'paused';

    if (!isActive) return;

    const interval = setInterval(() => {
      fetchExecution(true); // Silent refresh
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [open, execution]);

  const fetchExecution = async (silent = false) => {
    if (!executionId) return;

    try {
      if (!silent) {
        setLoading(true);
        setError(null);
      }
      const data = await apiClient.getExecution(executionId);
      setExecution(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load execution details');
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  const handleCancelExecution = async () => {
    if (!executionId) return;

    setCancelling(true);
    setCancelError(null);

    try {
      await apiClient.cancelExecution(executionId);
      setCancelDialogOpen(false);
      
      // Refresh execution details
      await fetchExecution();
      
      // Notify parent component
      if (onRefresh) {
        onRefresh();
      }
    } catch (err: any) {
      setCancelError(err.message || 'Failed to cancel execution');
    } finally {
      setCancelling(false);
    }
  };

  const handleRefresh = () => {
    fetchExecution();
  };

  const handleClose = () => {
    setExecution(null);
    setLoading(true);
    setError(null);
    setCancelError(null);
    onClose();
  };

  // Calculate execution duration
  const calculateDuration = (): string => {
    if (!execution || !execution.startTime) return '-';
    
    // Convert Unix timestamp (seconds) to milliseconds
    // API returns timestamps in seconds, JavaScript Date expects milliseconds
    let startTimeMs: number | string = execution.startTime;
    if (typeof execution.startTime === 'number' && execution.startTime < 10000000000) {
      startTimeMs = execution.startTime * 1000;
    }
    
    let endTimeMs: number | string | undefined = execution.endTime;
    if (execution.endTime) {
      if (typeof execution.endTime === 'number' && execution.endTime < 10000000000) {
        endTimeMs = execution.endTime * 1000;
      }
    }
    
    const start = new Date(startTimeMs);
    const end = endTimeMs ? new Date(endTimeMs) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    // Validate duration (not negative, not > 1 year)
    if (durationMs < 0 || durationMs > 365 * 24 * 60 * 60 * 1000) {
      return 'Invalid';
    }
    
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  // Calculate progress percentage
  const calculateProgress = (): number => {
    if (!execution || !execution.currentWave) return 0;
    return (execution.currentWave / execution.totalWaves) * 100;
  };

  // Check if execution can be cancelled
  const canCancel = execution && (
    execution.status === 'in_progress' || 
    execution.status === 'pending' ||
    execution.status === 'paused'
  );

  return (
    <>
      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: {
            minHeight: '60vh',
            maxHeight: '90vh',
          },
        }}
      >
        {/* Dialog Title */}
        <DialogTitle>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Execution Details</Typography>
            <Stack direction="row" spacing={1}>
              <IconButton onClick={handleRefresh} disabled={loading} size="small">
                <RefreshIcon />
              </IconButton>
              <IconButton onClick={handleClose} size="small">
                <CloseIcon />
              </IconButton>
            </Stack>
          </Stack>
        </DialogTitle>

        <Divider />

        {/* Dialog Content */}
        <DialogContent>
          {loading && !execution ? (
            <LoadingState message="Loading execution details..." />
          ) : error ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          ) : execution ? (
            <Stack spacing={3}>
              {/* Cancel Error Alert */}
              {cancelError && (
                <Alert severity="error" onClose={() => setCancelError(null)}>
                  {cancelError}
                </Alert>
              )}

              {/* Execution Metadata */}
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Recovery Plan
                </Typography>
                <Typography variant="h6" gutterBottom>
                  {execution.recoveryPlanName}
                </Typography>

                <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                  <StatusBadge status={execution.status} />
                  
                  {execution.currentWave && (
                    <Chip 
                      label={`Wave ${execution.currentWave} of ${execution.totalWaves}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  )}

                  {execution.executedBy && (
                    <Chip 
                      label={`By: ${execution.executedBy}`}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Stack>

                <Stack direction="row" spacing={4} sx={{ mb: 2 }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Started
                    </Typography>
                    <Typography variant="body2">
                      <DateTimeDisplay value={execution.startTime} format="full" />
                    </Typography>
                  </Box>

                  {execution.endTime && (
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Ended
                      </Typography>
                      <Typography variant="body2">
                        <DateTimeDisplay value={execution.endTime} format="full" />
                      </Typography>
                    </Box>
                  )}

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Duration
                    </Typography>
                    <Typography variant="body2">
                      {calculateDuration()}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Execution ID
                    </Typography>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        fontFamily: 'monospace',
                        fontSize: '0.875rem',
                      }}
                    >
                      {execution.executionId}
                    </Typography>
                  </Box>
                </Stack>

                {/* Progress Bar for Active Executions */}
                {execution.status === 'in_progress' && execution.currentWave && (
                  <Box sx={{ mb: 2 }}>
                    <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Overall Progress
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {Math.round(calculateProgress())}%
                      </Typography>
                    </Stack>
                    <LinearProgress 
                      variant="determinate" 
                      value={calculateProgress()}
                      sx={{ height: 8, borderRadius: 1 }}
                    />
                  </Box>
                )}
              </Box>

              <Divider />

              {/* Error Information */}
              {execution.error && (
                <Alert severity="error">
                  <Typography variant="subtitle2" gutterBottom>
                    {execution.error.code}
                  </Typography>
                  <Typography variant="body2">
                    {execution.error.message}
                  </Typography>
                  {execution.error.details && (
                    <Typography 
                      variant="caption" 
                      component="pre"
                      sx={{ 
                        mt: 1,
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}
                    >
                      {JSON.stringify(execution.error.details, null, 2)}
                    </Typography>
                  )}
                </Alert>
              )}

              {/* Wave Progress Timeline */}
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Wave Progress
                </Typography>
                <WaveProgress waves={execution.waveExecutions || []} />
              </Box>
            </Stack>
          ) : null}
        </DialogContent>

        {/* Dialog Actions */}
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleClose}>
            Close
          </Button>
          {canCancel && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<CancelIcon />}
              onClick={() => setCancelDialogOpen(true)}
              disabled={cancelling}
            >
              Cancel Execution
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Cancel Confirmation Dialog */}
      <ConfirmDialog
        open={cancelDialogOpen}
        title="Cancel Execution"
        message="Are you sure you want to cancel this execution? This action cannot be undone. Servers that have already been recovered will remain in their current state."
        confirmLabel="Cancel Execution"
        confirmColor="error"
        onConfirm={handleCancelExecution}
        onCancel={() => setCancelDialogOpen(false)}
      />
    </>
  );
};
