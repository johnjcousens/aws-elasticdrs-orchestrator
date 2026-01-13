/**
 * Dashboard Page Component
 *
 * Operational dashboard showing execution status, metrics, and system health.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  SpaceBetween,
  Container,
  Header,
  ColumnLayout,
  StatusIndicator,
  Link,
  Spinner,
  PieChart,
  Button,
} from '@cloudscape-design/components';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { DRSQuotaStatusPanel } from '../components/DRSQuotaStatus';
import { RegionSelector } from '../components/RegionSelector';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { useAccount } from '../contexts/AccountContext';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';
import type { DRSQuotaStatus } from '../services/drsQuotaService';
import type { SelectProps } from '@cloudscape-design/components';

// Status colors for the pie chart
const STATUS_COLORS: Record<string, string> = {
  completed: '#037f0c',
  in_progress: '#0972d3',
  pending: '#5f6b7a',
  failed: '#d91515',
  rolled_back: '#ff9900',
  cancelled: '#5f6b7a',
  paused: '#5f6b7a',
};

const STATUS_LABELS: Record<string, string> = {
  completed: 'Completed',
  in_progress: 'In Progress',
  pending: 'Pending',
  failed: 'Failed',
  rolled_back: 'Rolled Back',
  cancelled: 'Cancelled',
  paused: 'Paused',
};

// Common regions to check for finding the busiest region
const COMMON_REGIONS = [
  { value: 'us-east-1', label: 'us-east-1 (N. Virginia)' },
  { value: 'us-east-2', label: 'us-east-2 (Ohio)' },
  { value: 'us-west-2', label: 'us-west-2 (Oregon)' },
  { value: 'eu-west-1', label: 'eu-west-1 (Ireland)' },
  { value: 'eu-central-1', label: 'eu-central-1 (Frankfurt)' },
  { value: 'ap-northeast-1', label: 'ap-northeast-1 (Tokyo)' },
  { value: 'ap-southeast-1', label: 'ap-southeast-1 (Singapore)' },
  { value: 'ap-southeast-2', label: 'ap-southeast-2 (Sydney)' },
];

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { selectedAccount, getCurrentAccountId, getCurrentAccountName } = useAccount();
  
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // DRS Quota state
  const [drsQuotas, setDrsQuotas] = useState<DRSQuotaStatus | null>(null);
  const [quotasLoading, setQuotasLoading] = useState(false);
  const [quotasError, setQuotasError] = useState<string | null>(null);
  const [tagSyncLoading, setTagSyncLoading] = useState(false);
  const [selectedRegion, setSelectedRegion] = useState<SelectProps.Option | null>(null);
  const [initialRegionDetected, setInitialRegionDetected] = useState(false);

  const fetchExecutions = useCallback(async () => {
    const accountId = getCurrentAccountId();
    if (!accountId) {
      setLoading(false);
      return;
    }

    try {
      // Pass accountId to API call for multi-account support
      const response = await apiClient.listExecutions({ 
        limit: 100,
        accountId 
      });
      // Defensive check: ensure items is an array
      setExecutions(Array.isArray(response?.items) ? response.items : []);
      setError(null);
    } catch (err) {
      setError('Failed to load executions');
      console.error('Error fetching executions:', err);
    } finally {
      setLoading(false);
    }
  }, [getCurrentAccountId]);

  const fetchDRSQuotas = useCallback(async (accountId: string, region: string) => {
    setQuotasLoading(true);
    setQuotasError(null);
    try {
      const quotas = await apiClient.getDRSQuotas(accountId, region);
      setDrsQuotas(quotas);
    } catch (err) {
      console.error('Error fetching DRS quotas:', err);
      setQuotasError('Unable to fetch DRS capacity');
      setDrsQuotas(null);
    } finally {
      setQuotasLoading(false);
    }
  }, []);

  // Find the region with the most replicating servers
  const detectBusiestRegion = useCallback(async (accountId: string) => {
    setQuotasLoading(true);
    try {
      // Fetch quotas for common regions in parallel
      const results = await Promise.allSettled(
        COMMON_REGIONS.map(async (region) => {
          const quotas = await apiClient.getDRSQuotas(accountId, region.value);
          return { region, quotas };
        })
      );

      // Find region with most replicating servers
      let busiestRegion = COMMON_REGIONS[0];
      let maxServers = 0;
      let busiestQuotas: DRSQuotaStatus | null = null;

      for (const result of results) {
        if (result.status === 'fulfilled') {
          const { region, quotas } = result.value;
          const serverCount = quotas.capacity?.replicatingServers || 0;
          if (serverCount > maxServers) {
            maxServers = serverCount;
            busiestRegion = region;
            busiestQuotas = quotas;
          }
        }
      }

      // Set the busiest region as default
      setSelectedRegion(busiestRegion);
      if (busiestQuotas) {
        setDrsQuotas(busiestQuotas);
      }
      setInitialRegionDetected(true);
    } catch (err) {
      console.error('Error detecting busiest region:', err);
      // Fall back to us-east-1
      setSelectedRegion(COMMON_REGIONS[0]);
      setInitialRegionDetected(true);
    } finally {
      setQuotasLoading(false);
    }
  }, []);

  // Fetch executions when account changes
  useEffect(() => {
    fetchExecutions();
    const interval = setInterval(fetchExecutions, 30000);
    return () => clearInterval(interval);
  }, [fetchExecutions]);

  // Detect busiest region on account change (only once per account)
  useEffect(() => {
    const accountId = getCurrentAccountId();
    if (accountId && !initialRegionDetected) {
      detectBusiestRegion(accountId);
    }
  }, [selectedAccount, getCurrentAccountId, initialRegionDetected, detectBusiestRegion]);

  // Reset region detection when account changes
  useEffect(() => {
    setInitialRegionDetected(false);
    setSelectedRegion(null);
    setDrsQuotas(null);
  }, [selectedAccount]);

  // Fetch DRS quotas on region change (after initial detection) and auto-refresh every 30 seconds
  useEffect(() => {
    const accountId = getCurrentAccountId();
    const region = selectedRegion?.value;
    if (accountId && region && initialRegionDetected) {
      fetchDRSQuotas(accountId, region);
      const interval = setInterval(() => {
        fetchDRSQuotas(accountId, region);
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [selectedRegion, fetchDRSQuotas, getCurrentAccountId, initialRegionDetected]);

  const handleTagSync = async () => {
    const accountId = getCurrentAccountId();
    if (!accountId) {
      toast.error('Please select a target account first');
      return;
    }

    setTagSyncLoading(true);
    try {
      await apiClient.triggerTagSync(accountId);
      const accountName = getCurrentAccountName();
      const accountDisplay = accountName ? `${accountName} (${accountId})` : accountId;
      toast.success(`Tag sync initiated for account ${accountDisplay} - EC2 tags will be synced to DRS servers`);
    } catch (err) {
      console.error('Error triggering tag sync:', err);
      toast.error('Failed to trigger tag sync');
    } finally {
      setTagSyncLoading(false);
    }
  };



  // Calculate status counts
  const statusCounts = executions.reduce(
    (acc, exec) => {
      const status = exec.status || 'pending';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  // Active executions (non-terminal) - check both lowercase and uppercase
  const activeStatuses = [
    'pending', 'PENDING',
    'in_progress', 'IN_PROGRESS',
    'paused', 'PAUSED',
    'running', 'RUNNING',
    'polling', 'POLLING',
    'initiated', 'INITIATED',
    'launching', 'LAUNCHING',
    'started', 'STARTED',
  ];
  const activeExecutions = executions.filter((e) =>
    activeStatuses.includes(e.status)
  );
  const completedCount = statusCounts['completed'] || 0;
  const failedCount = statusCounts['failed'] || 0;
  const rolledBackCount = statusCounts['rolled_back'] || 0;

  // Pie chart data
  const pieData = Object.entries(statusCounts)
    .filter(([, count]) => count > 0)
    .map(([status, count]) => ({
      title: STATUS_LABELS[status] || status,
      value: count,
      color: STATUS_COLORS[status] || '#5f6b7a',
    }));

  // Success rate calculation
  const totalCompleted = completedCount + failedCount + rolledBackCount;
  const successRate =
    totalCompleted > 0
      ? Math.round((completedCount / totalCompleted) * 100)
      : 0;

  const getStatusType = (
    status: string
  ): 'success' | 'error' | 'warning' | 'in-progress' | 'stopped' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'rolled_back':
        return 'warning';
      case 'cancelled':
      case 'paused':
        return 'stopped';
      default:
        return 'in-progress';
    }
  };

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            description="Real-time execution status and system metrics"
          >
            Dashboard
          </Header>
        }
      >
        <AccountRequiredWrapper pageName="the dashboard">
          {loading ? (
          <Box textAlign="center" padding="xxl">
            <Spinner size="large" />
          </Box>
        ) : error ? (
          <Container>
            <StatusIndicator type="error">{error}</StatusIndicator>
          </Container>
        ) : (
          <SpaceBetween size="l">
            <ColumnLayout columns={4} variant="text-grid">
              <Container>
                <Box variant="awsui-key-label">Active Executions</Box>
                <Box variant="awsui-value-large">
                  <span
                    style={{
                      color:
                        activeExecutions.length > 0 ? '#0972d3' : '#5f6b7a',
                    }}
                  >
                    {activeExecutions.length}
                  </span>
                </Box>
              </Container>
              <Container>
                <Box variant="awsui-key-label">Completed</Box>
                <Box variant="awsui-value-large">
                  <span style={{ color: '#037f0c' }}>{completedCount}</span>
                </Box>
              </Container>
              <Container>
                <Box variant="awsui-key-label">Failed</Box>
                <Box variant="awsui-value-large">
                  <span
                    style={{ color: failedCount > 0 ? '#d91515' : '#5f6b7a' }}
                  >
                    {failedCount}
                  </span>
                </Box>
              </Container>
              <Container>
                <Box variant="awsui-key-label">Success Rate</Box>
                <Box variant="awsui-value-large">
                  <span
                    style={{
                      color:
                        successRate >= 80
                          ? '#037f0c'
                          : successRate >= 50
                            ? '#ff9900'
                            : '#d91515',
                    }}
                  >
                    {successRate}%
                  </span>
                </Box>
              </Container>
            </ColumnLayout>

            <ColumnLayout columns={2}>
              <Container header={<Header variant="h2">Execution Status</Header>}>
                {pieData.length > 0 ? (
                  <PieChart
                    data={pieData}
                    detailPopoverContent={(datum) => [
                      { key: 'Count', value: datum.value },
                      {
                        key: 'Percentage',
                        value: `${Math.round((datum.value / executions.length) * 100)}%`,
                      },
                    ]}
                    segmentDescription={(datum) => `${datum.value} executions`}
                    size="medium"
                    variant="donut"
                    innerMetricDescription="total"
                    innerMetricValue={executions.length.toString()}
                    hideFilter
                    hideLegend={false}
                    empty={
                      <Box textAlign="center" color="inherit">
                        No execution data
                      </Box>
                    }
                  />
                ) : (
                  <Box textAlign="center" padding="l" color="text-body-secondary">
                    No executions yet.{' '}
                    <Link onFollow={() => navigate('/recovery-plans')}>
                      Create a Recovery Plan
                    </Link>{' '}
                    to get started.
                  </Box>
                )}
              </Container>

              <Container
                header={
                  <Header
                    variant="h2"
                    counter={`(${activeExecutions.length})`}
                    actions={
                      <Link onFollow={() => navigate('/executions')}>
                        View all
                      </Link>
                    }
                  >
                    Active Executions
                  </Header>
                }
              >
                {activeExecutions.length > 0 ? (
                  <SpaceBetween size="s">
                    {activeExecutions.slice(0, 5).map((exec) => (
                      <Box key={exec.executionId} padding="s">
                        <SpaceBetween direction="horizontal" size="xs">
                          <StatusIndicator type={getStatusType(exec.status)}>
                            {STATUS_LABELS[exec.status] || exec.status}
                          </StatusIndicator>
                          <Link
                            onFollow={() =>
                              navigate(`/executions/${exec.executionId}`)
                            }
                          >
                            {exec.planName || exec.planId}
                          </Link>
                        </SpaceBetween>
                      </Box>
                    ))}
                  </SpaceBetween>
                ) : (
                  <Box textAlign="center" padding="l" color="text-body-secondary">
                    No active executions
                  </Box>
                )}
              </Container>
            </ColumnLayout>

            <Container
              header={
                <Header
                  variant="h2"
                  actions={
                    <SpaceBetween direction="horizontal" size="xs">
                      <Button
                        onClick={handleTagSync}
                        loading={tagSyncLoading}
                        disabled={!selectedAccount}
                        iconName="refresh"
                      >
                        Sync Tags
                      </Button>
                      <RegionSelector
                        selectedRegion={selectedRegion}
                        onRegionChange={setSelectedRegion}
                        placeholder="Select region"
                      />
                    </SpaceBetween>
                  }
                >
                  DRS Capacity by Region
                </Header>
              }
            >
              {quotasLoading ? (
                <Box textAlign="center" padding="l">
                  <Spinner /> Loading DRS capacity...
                </Box>
              ) : quotasError ? (
                <StatusIndicator type="warning">{quotasError}</StatusIndicator>
              ) : drsQuotas ? (
                <DRSQuotaStatusPanel quotas={drsQuotas} />
              ) : (
                <Box textAlign="center" padding="l" color="text-body-secondary">
                  Select a region to view DRS capacity
                </Box>
              )}
            </Container>

            <Container
              header={
                <Header
                  variant="h2"
                  actions={
                    <Link onFollow={() => navigate('/executions')}>
                      View history
                    </Link>
                  }
                >
                  Recent Activity
                </Header>
              }
            >
              {executions.length > 0 ? (
                <SpaceBetween size="xs">
                  {executions.slice(0, 5).map((exec) => {
                    // Sanitize user-controlled data to prevent command injection
                    const sanitizedExecutionId = String(exec.executionId || '').replace(/[^a-zA-Z0-9-]/g, '');
                    const sanitizedStatus = String(exec.status || '').replace(/[^a-zA-Z0-9_]/g, '');
                    const sanitizedPlanName = String(exec.planName || exec.planId || '').replace(/[<>"'&]/g, '');
                    
                    return (
                    <Box key={sanitizedExecutionId} padding="xs">
                      <SpaceBetween direction="horizontal" size="m">
                        <StatusIndicator type={getStatusType(sanitizedStatus)}>
                          {STATUS_LABELS[sanitizedStatus] || sanitizedStatus}
                        </StatusIndicator>
                        <Link
                          onFollow={() =>
                            navigate(`/executions/${sanitizedExecutionId}`)
                          }
                        >
                          {sanitizedPlanName}
                        </Link>
                        <Box color="text-body-secondary" fontSize="body-s">
                          {exec.startTime
                            ? new Date(Number(exec.startTime) * 1000).toLocaleString()
                            : 'Not started'}
                        </Box>
                      </SpaceBetween>
                    </Box>
                    );
                  })}
                </SpaceBetween>
              ) : (
                <Box textAlign="center" padding="l" color="text-body-secondary">
                  No execution history yet
                </Box>
              )}
            </Container>
          </SpaceBetween>
        )}
        </AccountRequiredWrapper>
      </ContentLayout>
    </PageTransition>
  );
};