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
  ExpandableSection,
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
          <ExpandableSection 
            headerText="Replicating Servers (Active Replication)" 
            variant="footer"
            defaultExpanded={false}
          >
            <SpaceBetween size="s">
              <ProgressBar
                value={replicatingPct}
                additionalInfo={`${combined.availableSlots} slots available`}
                description={`${combined.totalReplicating} / ${combined.maxReplicating}`}
                status={replicatingStatus}
              />
              <Box variant="p" color="text-body-secondary" fontSize="body-s">
                Tracks how many source servers are actively replicating data to AWS. 
                Each AWS account has a limit of 300 replicating servers **per region** (not total across all regions). 
                For example: 200 servers in us-east-1 + 200 servers in us-west-2 = 400 total, but that's OK because each region is under its 300 limit.
                This is the foundation of your DR protection - servers must be replicating before they can be recovered.
              </Box>
            </SpaceBetween>
          </ExpandableSection>
        </Box>

        <Box>
          <ExpandableSection 
            headerText="Recovery Capacity (Total Source Servers)" 
            variant="footer"
            defaultExpanded={false}
          >
            <SpaceBetween size="s">
              <ProgressBar
                value={recoveryPct}
                additionalInfo={`${recoveryCapacity.availableSlots} slots available`}
                description={`${recoveryCapacity.currentServers} / ${recoveryCapacity.maxRecoveryInstances}`}
                status={recoveryStatus}
              />
              <Box variant="p" color="text-body-secondary" fontSize="body-s">
                The total number of source servers you can protect with DRS, including both 
                actively replicating servers and extended source servers (servers that have been disconnected but still consume capacity). 
                AWS allows up to 4,000 total source servers per account (adjustable via AWS Support). This is your maximum DR footprint - you cannot add more servers 
                once this limit is reached without removing existing ones or requesting a quota increase.
              </Box>
            </SpaceBetween>
          </ExpandableSection>
        </Box>

        <Box>
          <ExpandableSection 
            headerText="Concurrent Recovery Jobs" 
            variant="footer"
            defaultExpanded={false}
          >
            <SpaceBetween size="s">
              <ProgressBar
                value={jobsPct}
                additionalInfo={`${jobsMax - jobsCurrent} jobs available`}
                description={`${jobsCurrent} / ${jobsMax}`}
                status={jobsStatus}
              />
              <Box variant="p" color="text-body-secondary" fontSize="body-s">
                Limits how many recovery operations can run simultaneously per account. AWS DRS allows 
                20 concurrent recovery jobs per account. Each Recovery Plan execution creates one job. If you try to start a 21st job 
                while 20 are running, AWS will reject it. The orchestrator checks this limit before starting executions to prevent failures.
              </Box>
            </SpaceBetween>
          </ExpandableSection>
        </Box>

        <Box>
          <ExpandableSection 
            headerText="Servers in Active Jobs" 
            variant="footer"
            defaultExpanded={false}
          >
            <SpaceBetween size="s">
              <ProgressBar
                value={serversInJobsPct}
                additionalInfo={`${serversMax - serversCurrent} slots available`}
                description={`${serversCurrent} / ${serversMax}`}
                status={serversInJobsStatus}
              />
              <Box variant="p" color="text-body-secondary" fontSize="body-s">
                Tracks the total number of source servers being recovered across ALL concurrent jobs per account. 
                AWS limits this to 500 servers maximum. Even if you're under the 20 job limit, you cannot exceed 500 total servers 
                across all jobs. Example: 10 jobs with 50 servers each = 500 servers (limit reached). This is the aggregate capacity constraint 
                for recovery operations.
              </Box>
            </SpaceBetween>
          </ExpandableSection>
        </Box>

        <Box>
          <ExpandableSection 
            headerText="Max Servers Per Job" 
            variant="footer"
            defaultExpanded={false}
          >
            <SpaceBetween size="s">
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
              <Box variant="p" color="text-body-secondary" fontSize="body-s">
                Shows the largest single recovery job currently running. AWS limits each individual 
                recovery job to 100 servers maximum. If your Recovery Plan has more than 100 servers, the orchestrator automatically splits 
                it into waves (e.g., 150 servers = Wave 1: 100 servers, Wave 2: 50 servers). This gauge helps you monitor the size of your 
                largest active recovery operation.
              </Box>
            </SpaceBetween>
          </ExpandableSection>
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

