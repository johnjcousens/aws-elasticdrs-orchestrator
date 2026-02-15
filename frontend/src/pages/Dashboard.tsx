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
  Alert,
  ProgressBar,
} from '@cloudscape-design/components';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { RegionalCapacitySection } from '../components/RegionalCapacitySection';
import { CapacityGauge } from '../components/CapacityGauge';
import { getAllAccountsCapacity } from '../services/staging-accounts-api';
import type { CombinedCapacityData } from '../types/staging-accounts';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { useAccount } from '../contexts/AccountContext';
import { useSettings } from '../contexts/SettingsContext';
import { useStagingAccountRefresh } from '../hooks/useStagingAccountRefresh';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';

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
  const { openSettingsModal } = useSettings();
  
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [tagSyncLoading, setTagSyncLoading] = useState(false);
  const [stagingSyncLoading, setStagingSyncLoading] = useState(false);
  
  const [capacityData, setCapacityData] = useState<CombinedCapacityData | null>(null);
  const [capacityLoading, setCapacityLoading] = useState(false);
  const [capacityError, setCapacityError] = useState<string | null>(null);

  // Fetch executions - useCallback so it can be called from handleRefresh and useEffect
  const fetchExecutions = useCallback(async () => {
    const accountId = getCurrentAccountId();
    if (!accountId) {
      setLoading(false);
      return;
    }

    try {
      const response = await apiClient.listExecutions({ 
        limit: 100,
        accountId 
      });
      
      const items = Array.isArray(response?.items) ? response.items : [];
      setExecutions(items);
      setError(null);
    } catch (err) {
      setError('Failed to load executions');
      console.error('Error fetching executions:', err);
    } finally {
      setLoading(false);
    }
  }, [getCurrentAccountId]);

  // Fetch capacity data - simple callback, check is done in useEffect
  const fetchCapacityData = useCallback(async () => {
    const accountId = getCurrentAccountId();
    if (!accountId) return;
    
    setCapacityLoading(true);
    setCapacityError(null);
    
    try {
      const data = await getAllAccountsCapacity(accountId);
      setCapacityData(data);
    } catch (err) {
      console.error('Error fetching capacity data:', err);
      setCapacityError('Unable to fetch capacity data');
      setCapacityData(null);
    } finally {
      setCapacityLoading(false);
    }
  }, [getCurrentAccountId]);

  // Setup staging account refresh coordination
  useStagingAccountRefresh({
    onRefreshCapacity: fetchCapacityData,
  });

  // Open settings modal if no accounts configured
  useEffect(() => {
    if (!accountsLoading && availableAccounts.length === 0) {
      const timer = setTimeout(() => {
        if (availableAccounts.length === 0) {
          openSettingsModal('accounts');
        }
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [accountsLoading, availableAccounts.length, openSettingsModal]);

  // Fetch executions when account changes - setup interval
  useEffect(() => {
    const accountId = getCurrentAccountId();
    if (!accountId) {
      setLoading(false);
      return;
    }

    fetchExecutions();
    const interval = setInterval(fetchExecutions, 30000);
    return () => clearInterval(interval);
  }, [selectedAccount, fetchExecutions]);

  // Fetch DRS capacity for ALL accounts - setup interval
  useEffect(() => {
    if (availableAccounts.length === 0) {
      setCapacityData(null);
      return;
    }

    fetchCapacityData();
    const interval = setInterval(fetchCapacityData, 30000);
    return () => clearInterval(interval);
  }, [selectedAccount, availableAccounts.length, fetchCapacityData]);

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
      toast.success(`Tag sync started for account ${accountDisplay} - running in background`);
    } catch (err) {
      console.error('Error triggering tag sync:', err);
      toast.error('Failed to trigger tag sync');
    } finally {
      setTagSyncLoading(false);
    }
  };

  const handleRefresh = async () => {
    const accountId = getCurrentAccountId();
    
    // Refresh executions (still per-account)
    fetchExecutions();
    
    // Refresh capacity data (all accounts)
    fetchCapacityData();
    
    // Sync staging accounts in background for current account
    if (accountId) {
      setStagingSyncLoading(true);
      try {
        const result = await apiClient.syncStagingAccountsForAccount(accountId);
        
        // Show toast if changes were detected
        if (result.changes && (result.changes.added.length > 0 || result.changes.removed.length > 0)) {
          const addedMsg = result.changes.added.length > 0 
            ? `Added: ${result.changes.added.join(', ')}` 
            : '';
          const removedMsg = result.changes.removed.length > 0 
            ? `Removed: ${result.changes.removed.join(', ')}` 
            : '';
          const changeMsg = [addedMsg, removedMsg].filter(Boolean).join('. ');
          toast.success(`Staging accounts updated. ${changeMsg}`);
          
          // Refresh capacity data again to show updated staging accounts
          fetchCapacityData();
        }
      } catch (err) {
        console.error('Error syncing staging accounts:', err);
        // Don't show error toast - this is a background operation
      } finally {
        setStagingSyncLoading(false);
      }
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
      case 'PARTIAL':
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
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  iconName="refresh"
                  onClick={handleRefresh}
                  loading={loading || capacityLoading || stagingSyncLoading}
                >
                  Refresh
                </Button>
                <Button
                  onClick={handleTagSync}
                  loading={tagSyncLoading}
                  disabled={!selectedAccount}
                  iconName="upload"
                >
                  Sync Tags
                </Button>
              </SpaceBetween>
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

            {/* Execution Status */}
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

            {/* Regional Replication Capacity Section */}
            {capacityData && capacityData.regionalCapacity && (
              <RegionalCapacitySection 
                regionalCapacity={capacityData.regionalCapacity}
                accounts={capacityData.accounts}
              />
            )}

            <Container
              header={
                <Header
                  variant="h2"
                  description="AWS DRS service quotas for recovery operations"
                >
                  DRS Service Capacity
                </Header>
              }
            >
              {capacityLoading && !capacityData ? (
                <Box textAlign="center" padding="l">
                  <Spinner size="large" />
                </Box>
              ) : capacityError ? (
                <StatusIndicator type="error">{capacityError}</StatusIndicator>
              ) : capacityData ? (
                <SpaceBetween size="l">
                  {capacityData.warnings.length > 0 && (
                    <SpaceBetween size="s">
                      {capacityData.warnings.map((warning, index) => (
                        <Alert
                          key={index}
                          type={
                            capacityData.combined.status === 'OK' || capacityData.combined.status === 'INFO'
                              ? 'info'
                              : capacityData.combined.status === 'WARNING'
                                ? 'warning'
                                : 'error'
                          }
                        >
                          {warning}
                        </Alert>
                      ))}
                    </SpaceBetween>
                  )}

                  <ColumnLayout columns={3} variant="text-grid">
                    <SpaceBetween size="xxs">
                      <Box variant="awsui-key-label">Concurrent Recovery Jobs</Box>
                      <Box variant="small" color="text-body-secondary">
                        Max 20 concurrent jobs per account
                      </Box>
                      <ProgressBar
                        value={capacityData.concurrentJobs?.max ? Math.ceil(((capacityData.concurrentJobs?.current ?? 0) / capacityData.concurrentJobs.max) * 100) : 0}
                        status={(capacityData.concurrentJobs?.current ?? 0) >= 18 ? 'error' : 'in-progress'}
                        additionalInfo={`${(capacityData.concurrentJobs?.current ?? 0).toLocaleString()} / ${(capacityData.concurrentJobs?.max ?? 20).toLocaleString()} jobs`}
                        description={`${((capacityData.concurrentJobs?.max ?? 20) - (capacityData.concurrentJobs?.current ?? 0)).toLocaleString()} available`}
                      />
                    </SpaceBetween>

                    <SpaceBetween size="xxs">
                      <Box variant="awsui-key-label">Servers in Active Jobs</Box>
                      <Box variant="small" color="text-body-secondary">
                        Max 500 servers across all jobs
                      </Box>
                      <ProgressBar
                        value={capacityData.serversInJobs?.max ? Math.ceil(((capacityData.serversInJobs?.current ?? 0) / capacityData.serversInJobs.max) * 100) : 0}
                        status={(capacityData.serversInJobs?.current ?? 0) >= 450 ? 'error' : 'in-progress'}
                        resultText={`${((capacityData.serversInJobs?.current ?? 0) / (capacityData.serversInJobs?.max ?? 500) * 100).toFixed(1)}%`}
                        additionalInfo={`${(capacityData.serversInJobs?.current ?? 0).toLocaleString()} / ${(capacityData.serversInJobs?.max ?? 500).toLocaleString()} servers`}
                        description={`${((capacityData.serversInJobs?.max ?? 500) - (capacityData.serversInJobs?.current ?? 0)).toLocaleString()} available`}
                      />
                    </SpaceBetween>

                    <SpaceBetween size="xxs">
                      <Box variant="awsui-key-label">Max Servers Per Job</Box>
                      <Box variant="small" color="text-body-secondary">
                        Max 100 servers in a single job
                      </Box>
                      <ProgressBar
                        value={capacityData.maxServersPerJob?.max ? Math.ceil(((capacityData.maxServersPerJob?.current ?? 0) / capacityData.maxServersPerJob.max) * 100) : 0}
                        status={(capacityData.maxServersPerJob?.current ?? 0) >= 90 ? 'error' : 'in-progress'}
                        additionalInfo={`${(capacityData.maxServersPerJob?.current ?? 0).toLocaleString()} / ${(capacityData.maxServersPerJob?.max ?? 100).toLocaleString()} servers`}
                        description={capacityData.maxServersPerJob?.current && capacityData.maxServersPerJob.current > 0
                          ? `Largest job: ${capacityData.maxServersPerJob.current.toLocaleString()} servers`
                          : 'No active jobs'}
                      />
                    </SpaceBetween>
                  </ColumnLayout>
                </SpaceBetween>
              ) : (
                <Box textAlign="center" padding="l" color="text-body-secondary">
                  Select a target account to view capacity
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