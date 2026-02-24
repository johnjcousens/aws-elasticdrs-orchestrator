/**
 * Launch Configuration Progress Modal
 * 
 * Displays real-time progress of async launch configuration application
 * with status indicators, progress bars, and error handling.
 */

import React, { useMemo } from 'react';
import {
  Modal,
  Box,
  SpaceBetween,
  StatusIndicator,
  ProgressBar,
  Alert,
  Button,
} from '@cloudscape-design/components';
import type { LaunchConfigStatus } from '../types';

interface LaunchConfigProgressModalProps {
  visible: boolean;
  status: LaunchConfigStatus | null;
  onDismiss: () => void;
  onRetry?: () => void;
}

export const LaunchConfigProgressModal: React.FC<LaunchConfigProgressModalProps> = ({
  visible,
  status,
  onDismiss,
  onRetry,
}) => {
  // Determine if modal can be dismissed
  const canDismiss = useMemo(() => {
    if (!status) return true;
    return !['pending', 'syncing'].includes(status.status);
  }, [status]);

  // Calculate progress percentage
  const progressPercent = useMemo(() => {
    if (!status || status.totalServers === 0) return 0;
    return Math.round((status.completedServers / status.totalServers) * 100);
  }, [status]);

  // Estimate time remaining
  const estimatedTimeRemaining = useMemo(() => {
    if (!status || status.status !== 'syncing' || !status.startTime) {
      return null;
    }

    const elapsed = Date.now() - status.startTime;
    const rate = status.completedServers / (elapsed / 1000); // servers per second
    
    if (rate === 0 || !isFinite(rate)) {
      return null;
    }

    const remaining = status.totalServers - status.completedServers;
    const secondsRemaining = Math.ceil(remaining / rate);

    if (secondsRemaining < 60) {
      return `~${secondsRemaining}s remaining`;
    }
    
    const minutesRemaining = Math.ceil(secondsRemaining / 60);
    return `~${minutesRemaining}m remaining`;
  }, [status]);

  // Get status indicator props
  const statusIndicatorProps = useMemo(() => {
    if (!status) {
      return { type: 'pending' as const, children: 'Loading...' };
    }

    switch (status.status) {
      case 'pending':
        return { type: 'pending' as const, children: 'Preparing to sync configurations...' };
      case 'syncing':
        return { type: 'in-progress' as const, children: 'Syncing configurations to DRS and EC2...' };
      case 'ready':
        return { type: 'success' as const, children: 'All configurations applied successfully' };
      case 'partial':
        return { type: 'warning' as const, children: 'Some configurations failed to apply' };
      case 'failed':
        return { type: 'error' as const, children: 'Configuration sync failed' };
      default:
        return { type: 'pending' as const, children: 'Unknown status' };
    }
  }, [status]);

  // Get failed servers for error display
  const failedServers = useMemo(() => {
    if (!status || !status.servers) return [];
    return status.servers.filter(s => s.status === 'failed');
  }, [status]);

  return (
    <Modal
      visible={visible}
      onDismiss={canDismiss ? onDismiss : undefined}
      header="Launch Configuration Sync"
      size="medium"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            {(status?.status === 'partial' || status?.status === 'failed') && onRetry && (
              <Button onClick={onRetry}>Retry Failed</Button>
            )}
            <Button
              variant="primary"
              onClick={onDismiss}
              disabled={!canDismiss}
            >
              {canDismiss ? 'Close' : 'Syncing...'}
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
      <SpaceBetween size="l">
        {/* Status Indicator */}
        <StatusIndicator {...statusIndicatorProps} />

        {/* Progress Bar (only during syncing) */}
        {status?.status === 'syncing' && (
          <SpaceBetween size="xs">
            <ProgressBar
              value={progressPercent}
              label="Configuration sync progress"
              description={`${status.completedServers} of ${status.totalServers} servers completed`}
              status="in-progress"
            />
            {estimatedTimeRemaining && (
              <Box color="text-body-secondary" fontSize="body-s">
                {estimatedTimeRemaining}
              </Box>
            )}
          </SpaceBetween>
        )}

        {/* Success Summary */}
        {status?.status === 'ready' && (
          <Alert type="success">
            Successfully applied launch configurations to all {status.totalServers} servers.
          </Alert>
        )}

        {/* Partial Failure Alert */}
        {status?.status === 'partial' && (
          <Alert type="warning" header={`${failedServers.length} of ${status.totalServers} servers failed`}>
            <SpaceBetween size="xs">
              <div>
                {status.completedServers} servers configured successfully, but {failedServers.length} failed.
              </div>
              {failedServers.length > 0 && (
                <Box>
                  <strong>Failed servers:</strong>
                  <ul>
                    {failedServers.slice(0, 5).map(server => (
                      <li key={server.sourceServerId}>
                        {server.sourceServerId}: {server.error || 'Unknown error'}
                      </li>
                    ))}
                    {failedServers.length > 5 && (
                      <li>...and {failedServers.length - 5} more</li>
                    )}
                  </ul>
                </Box>
              )}
            </SpaceBetween>
          </Alert>
        )}

        {/* Complete Failure Alert */}
        {status?.status === 'failed' && (
          <Alert type="error" header="Configuration sync failed">
            <SpaceBetween size="xs">
              <div>
                Failed to apply launch configurations. Please check the error details below and try again.
              </div>
              {failedServers.length > 0 && (
                <Box>
                  <strong>Failed servers:</strong>
                  <ul>
                    {failedServers.slice(0, 5).map(server => (
                      <li key={server.sourceServerId}>
                        {server.sourceServerId}: {server.error || 'Unknown error'}
                      </li>
                    ))}
                    {failedServers.length > 5 && (
                      <li>...and {failedServers.length - 5} more</li>
                    )}
                  </ul>
                </Box>
              )}
            </SpaceBetween>
          </Alert>
        )}
      </SpaceBetween>
    </Modal>
  );
};
