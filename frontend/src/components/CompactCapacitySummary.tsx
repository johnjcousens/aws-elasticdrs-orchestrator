/**
 * Compact Capacity Summary Component
 * 
 * Shows a concise view of DRS capacity across target and staging accounts.
 * For detailed breakdown, users can navigate to the System Status page.
 */

import React from 'react';
import {
  Box,
  SpaceBetween,
  ColumnLayout,
  StatusIndicator,
  Link,
  Spinner,
} from '@cloudscape-design/components';
import type { CombinedCapacityData } from '../types/staging-accounts';

interface CompactCapacitySummaryProps {
  data: CombinedCapacityData | null;
  loading: boolean;
  error: string | null;
  onViewDetails?: () => void;
}

export const CompactCapacitySummary: React.FC<CompactCapacitySummaryProps> = ({
  data,
  loading,
  error,
  onViewDetails,
}) => {
  if (loading) {
    return (
      <Box textAlign="center" padding="l">
        <Spinner /> Loading capacity...
      </Box>
    );
  }

  if (error) {
    return <StatusIndicator type="error">{error}</StatusIndicator>;
  }

  if (!data) {
    return (
      <Box textAlign="center" padding="l" color="text-body-secondary">
        No capacity data available
      </Box>
    );
  }

  const { combined, accounts } = data;
  const statusColor = {
    OK: '#037f0c',
    INFO: '#0972d3',
    WARNING: '#ff9900',
    CRITICAL: '#d91515',
    'HYPER-CRITICAL': '#d91515',
  }[combined.status] || '#5f6b7a';

  return (
    <SpaceBetween size="m">
      <ColumnLayout columns={4} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">Total Accounts</Box>
          <Box variant="awsui-value-large">{accounts.length}</Box>
        </div>
        <div>
          <Box variant="awsui-key-label">Replicating Servers</Box>
          <Box variant="awsui-value-large">
            <span style={{ color: statusColor }}>
              {combined.totalReplicating}
            </span>
            <Box variant="small" color="text-body-secondary">
              {' '}/ {combined.maxReplicating}
            </Box>
          </Box>
        </div>
        <div>
          <Box variant="awsui-key-label">Capacity Used</Box>
          <Box variant="awsui-value-large">
            <span style={{ color: statusColor }}>
              {combined.percentUsed.toFixed(1)}%
            </span>
          </Box>
        </div>
        <div>
          <Box variant="awsui-key-label">Status</Box>
          <Box variant="awsui-value-large">
            <StatusIndicator
              type={
                combined.status === 'OK'
                  ? 'success'
                  : combined.status === 'INFO'
                    ? 'info'
                    : combined.status === 'WARNING'
                      ? 'warning'
                      : 'error'
              }
            >
              {combined.status}
            </StatusIndicator>
          </Box>
        </div>
      </ColumnLayout>

      {onViewDetails && (
        <Box textAlign="center">
          <Link onFollow={onViewDetails}>View detailed capacity breakdown</Link>
        </Box>
      )}
    </SpaceBetween>
  );
};
