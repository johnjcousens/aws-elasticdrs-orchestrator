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
  Select,
  type SelectProps,
} from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { DRSQuotaStatusPanel } from '../components/DRSQuotaStatus';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';
import type { DRSQuotaStatus } from '../services/drsQuotaService';

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

// Default region for DRS quota display
const DEFAULT_REGION = 'us-east-1';

// All 28 AWS DRS-supported commercial regions (verified December 2025)
// Reference: https://docs.aws.amazon.com/general/latest/gr/drs.html
const DRS_REGIONS: SelectProps.Option[] = [
  // Americas (6)
  { value: 'us-east-1', label: 'us-east-1 (N. Virginia)' },
  { value: 'us-east-2', label: 'us-east-2 (Ohio)' },
  { value: 'us-west-1', label: 'us-west-1 (N. California)' },
  { value: 'us-west-2', label: 'us-west-2 (Oregon)' },
  { value: 'ca-central-1', label: 'ca-central-1 (Canada)' },
  { value: 'sa-east-1', label: 'sa-east-1 (São Paulo)' },
  // Europe (8)
  { value: 'eu-west-1', label: 'eu-west-1 (Ireland)' },
  { value: 'eu-west-2', label: 'eu-west-2 (London)' },
  { value: 'eu-west-3', label: 'eu-west-3 (Paris)' },
  { value: 'eu-central-1', label: 'eu-central-1 (Frankfurt)' },
  { value: 'eu-central-2', label: 'eu-central-2 (Zurich)' },
  { value: 'eu-north-1', label: 'eu-north-1 (Stockholm)' },
  { value: 'eu-south-1', label: 'eu-south-1 (Milan)' },
  { value: 'eu-south-2', label: 'eu-south-2 (Spain)' },
  // Asia Pacific (10)
  { value: 'ap-northeast-1', label: 'ap-northeast-1 (Tokyo)' },
  { value: 'ap-northeast-2', label: 'ap-northeast-2 (Seoul)' },
  { value: 'ap-northeast-3', label: 'ap-northeast-3 (Osaka)' },
  { value: 'ap-southeast-1', label: 'ap-southeast-1 (Singapore)' },
  { value: 'ap-southeast-2', label: 'ap-southeast-2 (Sydney)' },
  { value: 'ap-southeast-3', label: 'ap-southeast-3 (Jakarta)' },
  { value: 'ap-southeast-4', label: 'ap-southeast-4 (Melbourne)' },
  { value: 'ap-south-1', label: 'ap-south-1 (Mumbai)' },
  { value: 'ap-south-2', label: 'ap-south-2 (Hyderabad)' },
  { value: 'ap-east-1', label: 'ap-east-1 (Hong Kong)' },
  // Middle East & Africa (4)
  { value: 'me-south-1', label: 'me-south-1 (Bahrain)' },
  { value: 'me-central-1', label: 'me-central-1 (UAE)' },
  { value: 'af-south-1', label: 'af-south-1 (Cape Town)' },
  { value: 'il-central-1', label: 'il-central-1 (Tel Aviv)' },
];

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // DRS Quota state
  const [selectedRegion, setSelectedRegion] = useState<SelectProps.Option>(DRS_REGIONS[0]);
  const [drsQuotas, setDrsQuotas] = useState<DRSQuotaStatus | null>(null);
  const [quotasLoading, setQuotasLoading] = useState(false);
  const [quotasError, setQuotasError] = useState<string | null>(null);

  const fetchExecutions = useCallback(async () => {
    try {
      const response = await apiClient.listExecutions({ limit: 100 });
      setExecutions(response.items || []);
      setError(null);
    } catch (err) {
      setError('Failed to load executions');
      console.error('Error fetching executions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDRSQuotas = useCallback(async (region: string) => {
    setQuotasLoading(true);
    setQuotasError(null);
    try {
      const quotas = await apiClient.getDRSQuotas(region);
      setDrsQuotas(quotas);
    } catch (err) {
      console.error('Error fetching DRS quotas:', err);
      setQuotasError('Unable to fetch DRS capacity');
      setDrsQuotas(null);
    } finally {
      setQuotasLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExecutions();
    const interval = setInterval(fetchExecutions, 30000);
    return () => clearInterval(interval);
  }, [fetchExecutions]);

  // Fetch DRS quotas on region change and auto-refresh every 30 seconds
  useEffect(() => {
    const region = selectedRegion?.value;
    if (region) {
      fetchDRSQuotas(region);
      const interval = setInterval(() => {
        fetchDRSQuotas(region);
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [selectedRegion, fetchDRSQuotas]);

  // Calculate status counts
  const statusCounts = executions.reduce(
    (acc, exec) => {
      const status = exec.status || 'pending';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  // Active executions (non-terminal)
  const activeStatuses = ['pending', 'in_progress', 'paused'];
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
                <Header
                  variant="h2"
                  actions={
                    <Select
                      selectedOption={selectedRegion}
                      onChange={({ detail }) => setSelectedRegion(detail.selectedOption)}
                      options={DRS_REGIONS}
                      placeholder="Select region"
                    />
                  }
                >
                  DRS Capacity
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
                  {executions.slice(0, 5).map((exec) => (
                    <Box key={exec.executionId} padding="xs">
                      <SpaceBetween direction="horizontal" size="m">
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
                        <Box color="text-body-secondary" fontSize="body-s">
                          {exec.startTime
                            ? new Date(Number(exec.startTime) * 1000).toLocaleString()
                            : 'Not started'}
                        </Box>
                      </SpaceBetween>
                    </Box>
                  ))}
                </SpaceBetween>
              ) : (
                <Box textAlign="center" padding="l" color="text-body-secondary">
                  No execution history yet
                </Box>
              )}
            </Container>
          </SpaceBetween>
        )}
      </ContentLayout>
    </PageTransition>
  );
};
