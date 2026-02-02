/**
 * Compact Capacity Summary Component
 * 
 * Dashboard view showing visual gauges for all DRS service limits.
 * Provides at-a-glance capacity monitoring with progress bars.
 */

import React from 'react';
import {
  Box,
  SpaceBetween,
  ColumnLayout,
  ProgressBar,
  Link,
  Spinner,
  StatusIndicator,
} from '@cloudscape-design/components';
import type { CombinedCapacityData } from '../types/staging-accounts';

interface CompactCapacitySummaryProps {
  data: CombinedCapacityData | null;
  loading: boolean;
  error: string | null;
  onViewDetails?: () => void;
}

function getProgressStatus(
  current: number,
  max: number
): 'success' | 'in-progress' | 'error' {
  if (max <= 0) return 'in-progress';
  const percentage = (current / max) * 100;
  if (percentage >= 90) return 'error';
  if (percentage >= 80) return 'in-progress';
  return 'success';
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

  const { combined, recoveryCapacity, concurrentJobs, serversInJobs, maxServersPerJob } = data;

  // Replicating servers capacity (300 per account)
  const replicatingPct = (combined.totalReplicating / combined.maxReplicating) * 100;
  const replicatingStatus = getProgressStatus(combined.totalReplicating, combined.maxReplicating);

  // Recovery capacity (4,000 total source servers)
  const recoveryPct = (recoveryCapacity.currentServers / recoveryCapacity.maxRecoveryInstances) * 100;
  const recoveryStatus = getProgressStatus(recoveryCapacity.currentServers, recoveryCapacity.maxRecoveryInstances);

  // Concurrent jobs (from backend data)
  const jobsCurrent = concurrentJobs?.current ?? 0;
  const jobsMax = concurrentJobs?.max ?? 20;
  const jobsPct = (jobsCurrent / jobsMax) * 100;
  const jobsStatus = getProgressStatus(jobsCurrent, jobsMax);

  // Servers in active jobs (from backend data)
  const serversCurrent = serversInJobs?.current ?? 0;
  const serversMax = serversInJobs?.max ?? 500;
  const serversInJobsPct = (serversCurrent / serversMax) * 100;
  const serversInJobsStatus = getProgressStatus(serversCurrent, serversMax);

  // Max servers per job (from backend data)
  const maxPerJobCurrent = maxServersPerJob?.current ?? 0;
  const maxPerJobMax = maxServersPerJob?.max ?? 100;
  const maxPerJobPct = (maxPerJobCurrent / maxPerJobMax) * 100;
  const maxPerJobStatus = getProgressStatus(maxPerJobCurrent, maxPerJobMax);

  return (
    <SpaceBetween size="l">
      <ColumnLayout columns={2} variant="text-grid">
        <Box>
          <Box variant="awsui-key-label" margin={{ bottom: 'xs' }}>
            Replicating Servers (Active Replication)
          </Box>
          <ProgressBar
            value={replicatingPct}
            additionalInfo={`${combined.availableSlots} slots available`}
            description={`${combined.totalReplicating} / ${combined.maxReplicating}`}
            status={replicatingStatus}
          />
        </Box>

        <Box>
          <Box variant="awsui-key-label" margin={{ bottom: 'xs' }}>
            Recovery Capacity (Total Source Servers)
          </Box>
          <ProgressBar
            value={recoveryPct}
            additionalInfo={`${recoveryCapacity.availableSlots} slots available`}
            description={`${recoveryCapacity.currentServers} / ${recoveryCapacity.maxRecoveryInstances}`}
            status={recoveryStatus}
          />
        </Box>

        <Box>
          <Box variant="awsui-key-label" margin={{ bottom: 'xs' }}>
            Concurrent Recovery Jobs
          </Box>
          <ProgressBar
            value={jobsPct}
            additionalInfo={`${jobsMax - jobsCurrent} jobs available`}
            description={`${jobsCurrent} / ${jobsMax}`}
            status={jobsStatus}
          />
        </Box>

        <Box>
          <Box variant="awsui-key-label" margin={{ bottom: 'xs' }}>
            Servers in Active Jobs
          </Box>
          <ProgressBar
            value={serversInJobsPct}
            additionalInfo={`${serversMax - serversCurrent} slots available`}
            description={`${serversCurrent} / ${serversMax}`}
            status={serversInJobsStatus}
          />
        </Box>

        <Box>
          <Box variant="awsui-key-label" margin={{ bottom: 'xs' }}>
            Max Servers Per Job
          </Box>
          <ProgressBar
            value={maxPerJobPct}
            additionalInfo={
              maxPerJobCurrent > 0
                ? `Largest job: ${maxPerJobCurrent} servers`
                : 'No active jobs'
            }
            description={`${maxPerJobCurrent} / ${maxPerJobMax}`}
            status={maxPerJobStatus}
          />
        </Box>
      </ColumnLayout>

      {onViewDetails && (
        <Box textAlign="center">
          <Link onFollow={onViewDetails}>
            View detailed capacity breakdown by account
          </Link>
        </Box>
      )}
    </SpaceBetween>
  );
};

