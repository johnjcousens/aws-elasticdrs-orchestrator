import React from 'react';
import {
  Box,
  ProgressBar,
  StatusIndicator,
  SpaceBetween,
  ColumnLayout,
} from '@cloudscape-design/components';
import type { DRSQuotaStatus } from '../services/drsQuotaService';
import { getCapacityStatusType } from '../services/drsQuotaService';

interface Props {
  quotas: DRSQuotaStatus;
  compact?: boolean;
}

function getProgressStatus(current: number, max: number): 'in-progress' | 'error' {
  if (max <= 0) return 'in-progress';
  const percentage = (current / max) * 100;
  return percentage >= 90 ? 'error' : 'in-progress';
}

export function DRSQuotaStatusPanel({ quotas, compact = false }: Props): React.ReactElement {
  if (compact) {
    return (
      <SpaceBetween size="xs">
        <StatusIndicator type={getCapacityStatusType(quotas.capacity.status)}>
          {quotas.capacity.message}
        </StatusIndicator>
      </SpaceBetween>
    );
  }

  const accountDisplay = quotas.accountName 
    ? `${quotas.accountName} (${quotas.accountId})`
    : quotas.accountId;

  const replicatingPct = (quotas.capacity.replicatingServers / quotas.capacity.maxReplicatingServers) * 100;
  const replicatingDesc = quotas.capacity.replicatingServers + ' / ' + quotas.capacity.maxReplicatingServers;
  const replicatingStatus = getProgressStatus(quotas.capacity.replicatingServers, quotas.capacity.maxReplicatingServers);

  const jobsCurrent = quotas.concurrentJobs.current;
  const jobsMax = quotas.concurrentJobs.max;
  const jobsPct = jobsCurrent !== null ? (jobsCurrent / jobsMax) * 100 : 0;
  const jobsDesc = jobsCurrent !== null ? jobsCurrent + ' / ' + jobsMax : 'Unknown';
  const jobsStatus = jobsCurrent !== null ? getProgressStatus(jobsCurrent, jobsMax) : 'in-progress';

  const serversCurrent = quotas.serversInJobs.current;
  const serversMax = quotas.serversInJobs.max;
  const serversPct = serversCurrent !== null ? (serversCurrent / serversMax) * 100 : 0;
  const serversDesc = serversCurrent !== null ? serversCurrent + ' / ' + serversMax : 'Unknown';
  const serversStatus = serversCurrent !== null ? getProgressStatus(serversCurrent, serversMax) : 'in-progress';

  return (
    <SpaceBetween size="m">
      <SpaceBetween direction="horizontal" size="m">
        <Box>
          <Box variant="awsui-key-label">Account</Box>
          <Box variant="awsui-value-large">{accountDisplay}</Box>
        </Box>
        <Box>
          <Box variant="awsui-key-label">Region</Box>
          <Box variant="awsui-value-large">{quotas.region}</Box>
        </Box>
      </SpaceBetween>
      <Box>
        <StatusIndicator type={getCapacityStatusType(quotas.capacity.status)}>
          {quotas.capacity.message}
        </StatusIndicator>
      </Box>
      <ColumnLayout columns={3} variant="text-grid">
        <Box>
          <Box variant="awsui-key-label">Replicating Servers</Box>
          <ProgressBar value={replicatingPct} description={replicatingDesc} status={replicatingStatus} />
        </Box>
        <Box>
          <Box variant="awsui-key-label">Concurrent Jobs</Box>
          <ProgressBar value={jobsPct} description={jobsDesc} status={jobsStatus} />
        </Box>
        <Box>
          <Box variant="awsui-key-label">Servers in Active Jobs</Box>
          <ProgressBar value={serversPct} description={serversDesc} status={serversStatus} />
        </Box>
      </ColumnLayout>
    </SpaceBetween>
  );
}

export default DRSQuotaStatusPanel;
