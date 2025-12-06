/**
 * Execution Details Modal
 * 
 * Modal dialog for viewing detailed execution information with real-time updates.
 * Includes wave progress, server status, and cancel functionality.
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Box,
  Button,
  Alert,
  ProgressBar,
  SpaceBetween,
  Header,
  ColumnLayout,
  Container,
  Badge,
} from '@cloudscape-design/components';
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
      <Modal
        visible={open}
        onDismiss={handleClose}
        size="large"
        header={
          <Header
            variant="h2"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  iconName="refresh"
                  onClick={handleRefresh}
                  disabled={loading}
                  variant="icon"
                />
              </SpaceBetween>
            }
          >
            Execution Details
          </Header>
        }
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={handleClose} variant="link">
                Close
              </Button>
              {canCancel && (
                <Button
                  onClick={() => setCancelDialogOpen(true)}
                  disabled={cancelling}
                  iconName="close"
                >
                  Cancel Execution
                </Button>
              )}
            </SpaceBetween>
          </Box>
        }
      >
        {loading && !execution ? (
          <LoadingState message="Loading execution details..." />
        ) : error ? (
          <Alert type="error" dismissible onDismiss={() => setError(null)}>
            {error}
          </Alert>
        ) : execution ? (
          <SpaceBetween size="l">
            {/* Cancel Error Alert */}
            {cancelError && (
              <Alert type="error" dismissible onDismiss={() => setCancelError(null)}>
                {cancelError}
              </Alert>
            )}

            {/* Execution Metadata */}
            <Container header={<Header variant="h3">Recovery Plan</Header>}>
              <SpaceBetween size="m">
                <div>
                  <div style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>
                    {execution.recoveryPlanName}
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <StatusBadge status={execution.status} />
                    {execution.currentWave && (
                      <Badge color="blue">
                        Wave {execution.currentWave} of {execution.totalWaves}
                      </Badge>
                    )}
                    {execution.executedBy && (
                      <Badge>
                        By: {execution.executedBy}
                      </Badge>
                    )}
                  </div>
                </div>

                <ColumnLayout columns={4} variant="text-grid">
                  <div>
                    <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                      Started
                    </div>
                    <DateTimeDisplay value={execution.startTime} format="full" />
                  </div>

                  {execution.endTime && (
                    <div>
                      <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                        Ended
                      </div>
                      <DateTimeDisplay value={execution.endTime} format="full" />
                    </div>
                  )}

                  <div>
                    <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                      Duration
                    </div>
                    <div>{calculateDuration()}</div>
                  </div>

                  <div>
                    <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                      Execution ID
                    </div>
                    <div style={{ fontFamily: 'monospace', fontSize: '14px' }}>
                      {execution.executionId}
                    </div>
                  </div>
                </ColumnLayout>

                {/* Progress Bar for Active Executions */}
                {execution.status === 'in_progress' && execution.currentWave && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <div style={{ fontSize: '12px', color: '#5f6b7a' }}>
                        Overall Progress
                      </div>
                      <div style={{ fontSize: '12px', color: '#5f6b7a' }}>
                        {Math.round(calculateProgress())}%
                      </div>
                    </div>
                    <ProgressBar
                      value={calculateProgress()}
                      variant="standalone"
                    />
                  </div>
                )}
              </SpaceBetween>
            </Container>

            {/* Error Information */}
            {execution.error && (
              <Alert type="error" header={execution.error.code}>
                <div>{execution.error.message}</div>
                {execution.error.details && (
                  <pre style={{ 
                    marginTop: '8px',
                    fontFamily: 'monospace',
                    fontSize: '12px',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}>
                    {JSON.stringify(execution.error.details, null, 2)}
                  </pre>
                )}
              </Alert>
            )}

            {/* Wave Progress Timeline */}
            <Container header={<Header variant="h3">Wave Progress</Header>}>
              <WaveProgress waves={execution.waveExecutions || []} />
            </Container>
          </SpaceBetween>
        ) : null}
      </Modal>

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
