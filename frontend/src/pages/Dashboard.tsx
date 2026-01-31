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
import { CompactCapacitySummary } from '../components/CompactCapacitySummary';
import { getCombinedCapacity } from '../services/staging-accounts-api';
import type { CombinedCapacityData } from '../types/staging-accounts';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { useAccount } from '../contexts/AccountContext';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';
import type { DRSQuotaStatus } from '../services/drsQuotaService';

// Status colors for the pie chart (CloudScape AWS marketing approved colors)
// Green: Success/Completed, Blue: In Progress, Red: Failed/Error
// Yellow/Amber: Warning/Paused/Suspended, Grey: Neutral/Cancelled
const STATUS_COLORS: Record<string, string> = {
  COMPLETED: '#037f0c',      // Green - success
  IN_PROGRESS: '#0972d3',    // Blue - in progress
  PENDING: '#5f6b7a',        // Grey - neutral
  FAILED: '#d91515',         // Red - error
  ROLLED_BACK: '#ff9900',    // Orange - warning
  CANCELLED: '#5f6b7a',      // Grey - neutral/closed
  CANCELLING: '#ff9900',     // Orange - warning/in progress
  PAUSED: '#ff9900',         // Yellow/Amber - suspended/awaiting input
  RUNNING: '#0972d3',        // Blue - in progress
  POLLING: '#0972d3',        // Blue - in progress
  INITIATED: '#0972d3',      // Blue - in progress
  LAUNCHING: '#0972d3',      // Blue - in progress
  STARTED: '#0972d3',        // Blue - in progress
};

const STATUS_LABELS: Record<string, string> = {
  COMPLETED: 'Completed',
  IN_PROGRESS: 'In Progress',
  PENDING: 'Pending',
  FAILED: 'Failed',
  ROLLED_BACK: 'Rolled Back',
  CANCELLED: 'Cancelled',
  CANCELLING: 'Cancelling',
  PAUSED: 'Paused',
  RUNNING: 'Running',
  POLLING: 'In Progress',
  INITIATED: 'Initiated',
  LAUNCHING: 'Launching',
  STARTED: 'Started',
};

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { selectedAccount, getCurrentAccountId, getCurrentAccountName, availableAccounts, accountsLoading } = useAccount();
  
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [drsQuotas, setDrsQuotas] = useState<DRSQuotaStatus | null>(null);
  const [quotasLoading, setQuotasLoading] = useState(false);
  const [quotasError, setQuotasError] = useState<string | null>(null);
  const [tagSyncLoading, setTagSyncLoading] = useState(false);
  
  const [capacityData, setCapacityData] = useState<CombinedCapacityData | null>(null);
  const [capacityLoading, setCapacityLoading] = useState(false);
  const [capacityError, setCapacityError] = useState<string | null>(null);

  useEffect(() => {
    if (!accountsLoading && availableAccounts.length === 0) {
      navigate('/getting-started');
    }
  }, [accountsLoading, availableAccounts, navigate]);

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

  const fetchDRSQuotas = useCallback(async (accountId: string) => {
    setQuotasLoading(true);
    setQuotasError(null);
    try {
      // Fetch account-wide capacity (backend aggregates all regions)
      const quotas = await apiClient.getDRSQuotas(accountId);
      setDrsQuotas(quotas);
    } catch (err) {
      console.error('Error fetching DRS quotas:', err);
      setQuotasError('Unable to fetch DRS capacity');
      setDrsQuotas(null);
    } finally {
      setQuotasLoading(false);
    }
  }, []);

  const fetchCapacityData = useCallback(async (accountId: string) => {
    setCapacityLoading(true);
    setCapacityError(null);
    try {
      const data = await getCombinedCapacity(accountId, false); // Don't need regional breakdown for summary
      setCapacityData(data);
    } catch (err) {
      console.error('Error fetching capacity data:', err);
      setCapacityError('Unable to fetch capacity data');
      setCapacityData(null);
    } finally {
      setCapacityLoading(false);
    }
  }, []);

  // Fetch executions when account changes
  useEffect(() => {
    fetchExecutions();
    const interval = setInterval(fetchExecutions, 30000);
    return () => clearInterval(interval);
  }, [fetchExecutions]);

  // Fetch DRS quotas and capacity when account changes
  useEffect(() => {
    const accountId = getCurrentAccountId();
    if (accountId) {
      fetchDRSQuotas(accountId);
      fetchCapacityData(accountId);
      const interval = setInterval(() => {
        fetchDRSQuotas(accountId);
        fetchCapacityData(accountId);
      }, 30000);
      return () => clearInterval(interval);
    } else {
      setDrsQuotas(null);
      setCapacityData(null);
    }
  }, [selectedAccount, getCurrentAccountId, fetchDRSQuotas, fetchCapacityData]);

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
    'cancelling', 'CANCELLING',
  ];
  const activeExecutions = executions.filter((e) =>
    activeStatuses.includes(e.status)
  );
  const completedCount = statusCounts['COMPLETED'] || 0;
  const failedCount = statusCounts['FAILED'] || 0;
  const rolledBackCount = statusCounts['ROLLED_BACK'] || 0;

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
    const upperStatus = status.toUpperCase();
    switch (upperStatus) {
      case 'COMPLETED':
        return 'success';
      case 'FAILED':
        return 'error';
      case 'ROLLED_BACK':
      case 'CANCELLING':
        return 'warning';
      case 'CANCELLED':
      case 'PAUSED':
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
            actions={
              <Button
                onClick={handleTagSync}
                loading={tagSyncLoading}
                disabled={!selectedAccount}
                iconName="refresh"
              >
                Sync Tags
              </Button>
            }
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

            <Container
              header={
                <Header variant="h2">
                  Combined Capacity Summary
                </Header>
              }
            >
              <CompactCapacitySummary
                data={capacityData}
                loading={capacityLoading}
                error={capacityError}
                onViewDetails={() => navigate('/system-status')}
              />
            </Container>

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
                            {exec.recoveryPlanName || exec.recoveryPlanId}
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
                <Header variant="h2">
                  DRS Capacity per Account
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
                  No DRS capacity data available
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
                    const sanitizedPlanName = String(exec.recoveryPlanName || exec.recoveryPlanId || '').replace(/[<>"'&]/g, '');
                    
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