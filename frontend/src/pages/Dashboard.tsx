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

  // Fetch capacity data for ALL accounts (universal dashboard)
  const fetchCapacityData = useCallback(async (bustCache = false) => {
    // Dashboard shows ALL accounts - single API call for better performance
    if (availableAccounts.length === 0) {
      setCapacityData(null);
      return;
    }

    // Only show loading spinner on initial load (when no data exists) or when busting cache
    if (!capacityData || bustCache) {
      setCapacityLoading(true);
    }
    setCapacityError(null);
    
    try {
      // Fetch capacity for ALL target accounts in a single API call
      const data = await getAllAccountsCapacity();
      setCapacityData(data);
    } catch (err) {
      console.error('Error fetching capacity data:', err);
      setCapacityError('Unable to fetch capacity data');
      setCapacityData(null);
    } finally {
      setCapacityLoading(false);
    }
  }, [availableAccounts.length, capacityData]);

  // Refresh capacity data callback for staging account changes
  const refreshCapacityData = useCallback(() => {
    if (availableAccounts.length > 0) {
      fetchCapacityData(true); // Force cache bust
    }
  }, [availableAccounts.length, fetchCapacityData]);

  // Setup staging account refresh coordination
  useStagingAccountRefresh({
    onRefreshCapacity: refreshCapacityData,
  });
  // Open settings modal if no accounts configured
  // Only open settings modal if accounts have finished loading AND there are no accounts
  useEffect(() => {
    if (!accountsLoading && availableAccounts.length === 0) {
      // Add a small delay to avoid race conditions with account loading
      const timer = setTimeout(() => {
        if (availableAccounts.length === 0) {
          openSettingsModal('accounts');
        }
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [accountsLoading, availableAccounts.length, openSettingsModal]);

  const fetchExecutions = useCallback(async () => {
    const accountId = getCurrentAccountId();
    if (!accountId) {
      setLoading(false);
      return;
    }

    try {
      // Only show loading spinner on initial load (when no data exists)
      if (executions.length === 0) {
        setLoading(true);
      }
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
  }, [getCurrentAccountId, executions.length]);

  // Fetch executions when account changes
  useEffect(() => {
    fetchExecutions();
    const interval = setInterval(fetchExecutions, 30000);
    return () => clearInterval(interval);
  }, [fetchExecutions]);

  // Fetch DRS capacity for ALL accounts (dashboard is universal)
  useEffect(() => {
    if (availableAccounts.length > 0) {
      fetchCapacityData();
      const interval = setInterval(() => {
        fetchCapacityData();
      }, 30000);
      return () => clearInterval(interval);
    } else {
      setCapacityData(null);
    }
  }, [availableAccounts.length, fetchCapacityData]);

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

  const handleRefresh = async () => {
    const accountId = getCurrentAccountId();
    
    // Refresh executions (still per-account)
    fetchExecutions();
    
    // Refresh capacity data (all accounts)
    if (availableAccounts.length > 0) {
      fetchCapacityData(true); // Force cache bust
    }
    
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
          fetchCapacityData(true);
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

            {/* Regional Replication Capacity Section */}
            {capacityData && capacityData.regionalCapacity && (
              <RegionalCapacitySection 
                regionalCapacity={capacityData.regionalCapacity}
                combinedTotal={capacityData.combined.totalReplicating}
                combinedMax={capacityData.combined.maxReplicating}
                combinedPercent={capacityData.combined.percentUsed}
                combinedStatus={capacityData.combined.status}
              />
            )}

            <Container
              header={
                <Header variant="h2">
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
                  {/* Warnings */}
                  {capacityData.warnings.length > 0 && (
                    <SpaceBetween size="s">
                      {capacityData.warnings.map((warning, index) => (
                        <Alert
                          key={index}
                          type={
                            capacityData.combined.status === 'OK'
                              ? 'info'
                              : capacityData.combined.status === 'INFO'
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

                  {/* 1x3 Grid Layout for Job-Related Capacity Gauges */}
                  <ColumnLayout columns={3} variant="text-grid">
                    {/* Concurrent Recovery Jobs */}
                    <Container>
                      <SpaceBetween size="s">
                        <div>
                          <Box variant="h3" padding={{ bottom: 'xxs' }}>Concurrent Recovery Jobs</Box>
                          <Box variant="small" color="text-body-secondary">
                            Number of recovery jobs that can run at the same time. AWS DRS limit: 20 concurrent jobs per account.
                          </Box>
                        </div>
                        <CapacityGauge
                          used={capacityData.concurrentJobs?.current ?? 0}
                          total={capacityData.concurrentJobs?.max ?? 20}
                          size="medium"
                          label={`${(capacityData.concurrentJobs?.current ?? 0).toLocaleString()} / ${(capacityData.concurrentJobs?.max ?? 20).toLocaleString()} jobs`}
                        />
                        <Box textAlign="center">
                          <Box variant="small" color="text-body-secondary">
                            {((capacityData.concurrentJobs?.max ?? 20) - (capacityData.concurrentJobs?.current ?? 0)).toLocaleString()} jobs available
                          </Box>
                        </Box>
                      </SpaceBetween>
                    </Container>

                    {/* Servers in Active Jobs */}
                    <Container>
                      <SpaceBetween size="s">
                        <div>
                          <Box variant="h3" padding={{ bottom: 'xxs' }}>Servers in Active Jobs</Box>
                          <Box variant="small" color="text-body-secondary">
                            Total servers across all active recovery jobs. AWS DRS limit: 500 servers in all jobs combined per account.
                          </Box>
                        </div>
                        <CapacityGauge
                          used={capacityData.serversInJobs?.current ?? 0}
                          total={capacityData.serversInJobs?.max ?? 500}
                          size="medium"
                          label={`${(capacityData.serversInJobs?.current ?? 0).toLocaleString()} / ${(capacityData.serversInJobs?.max ?? 500).toLocaleString()} servers`}
                        />
                        <Box textAlign="center">
                          <Box variant="small" color="text-body-secondary">
                            {((capacityData.serversInJobs?.max ?? 500) - (capacityData.serversInJobs?.current ?? 0)).toLocaleString()} slots available
                          </Box>
                        </Box>
                      </SpaceBetween>
                    </Container>

                    {/* Max Servers Per Job */}
                    <Container>
                      <SpaceBetween size="s">
                        <div>
                          <Box variant="h3" padding={{ bottom: 'xxs' }}>Max Servers Per Job</Box>
                          <Box variant="small" color="text-body-secondary">
                            Maximum servers allowed in a single recovery job. AWS DRS limit: 100 servers per job.
                          </Box>
                        </div>
                        {capacityData.maxServersPerJob ? (
                          <>
                            <CapacityGauge
                              used={capacityData.maxServersPerJob.current ?? 0}
                              total={capacityData.maxServersPerJob.max ?? 100}
                              size="medium"
                              label={`${(capacityData.maxServersPerJob.current ?? 0).toLocaleString()} / ${(capacityData.maxServersPerJob.max ?? 100).toLocaleString()} servers`}
                            />
                            <Box textAlign="center">
                              <Box variant="small" color="text-body-secondary">
                                {capacityData.maxServersPerJob.current > 0
                                  ? `Largest job: ${capacityData.maxServersPerJob.current.toLocaleString()} servers`
                                  : 'No active jobs'}
                              </Box>
                            </Box>
                          </>
                        ) : (
                          <Box textAlign="center" padding={{ top: 'l', bottom: 'l' }}>
                            <Box variant="small" color="text-status-error">
                              Data not available
                            </Box>
                          </Box>
                        )}
                      </SpaceBetween>
                    </Container>
                  </ColumnLayout>
                </SpaceBetween>
              ) : (
                <Box textAlign="center" padding="l" color="text-body-secondary">
                  Select a target account to view capacity
                </Box>
              )}
            </Container>

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
          </SpaceBetween>
        )}
        </AccountRequiredWrapper>
      </ContentLayout>
    </PageTransition>
  );
};