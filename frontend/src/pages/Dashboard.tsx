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
  Table,
  ProgressBar,
} from '@cloudscape-design/components';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { CapacityGauge } from '../components/CapacityGauge';
import { getCombinedCapacity } from '../services/staging-accounts-api';
import type { CombinedCapacityData } from '../types/staging-accounts';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { useAccount } from '../contexts/AccountContext';
import { useSettings } from '../contexts/SettingsContext';
import { useStagingAccountRefresh } from '../hooks/useStagingAccountRefresh';
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
  const { openSettingsModal } = useSettings();
  
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [tagSyncLoading, setTagSyncLoading] = useState(false);
  
  const [capacityData, setCapacityData] = useState<CombinedCapacityData | null>(null);
  const [capacityLoading, setCapacityLoading] = useState(false);
  const [capacityError, setCapacityError] = useState<string | null>(null);
  const [expandedItems, setExpandedItems] = useState<any[]>([]);
  const [expandedStagingItems, setExpandedStagingItems] = useState<any[]>([]);

  // Refresh capacity data callback for staging account changes
  const refreshCapacityData = useCallback(() => {
    const accountId = getCurrentAccountId();
    if (accountId) {
      fetchCapacityData(accountId, true); // Force cache bust
    }
  }, [getCurrentAccountId]);

  // Setup staging account refresh coordination
  useStagingAccountRefresh({
    onRefreshCapacity: refreshCapacityData,
  });
  // Open settings modal if no accounts configured
  useEffect(() => {
    if (!accountsLoading && availableAccounts.length === 0) {
      openSettingsModal('accounts');
    }
  }, [accountsLoading, availableAccounts, openSettingsModal]);

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

  const fetchCapacityData = useCallback(async (accountId: string, bustCache = false) => {
    // Only show loading spinner on initial load (when no data exists) or when busting cache
    if (!capacityData || bustCache) {
      setCapacityLoading(true);
    }
    setCapacityError(null);
    try {
      // Add timestamp to bust browser cache when explicitly requested
      const timestamp = bustCache ? `?_t=${Date.now()}` : '';
      const data = await getCombinedCapacity(accountId, false); // Don't need regional breakdown for summary
      setCapacityData(data);
    } catch (err) {
      console.error('Error fetching capacity data:', err);
      setCapacityError('Unable to fetch capacity data');
      setCapacityData(null);
    } finally {
      setCapacityLoading(false);
    }
  }, [capacityData]);

  // Fetch executions when account changes
  useEffect(() => {
    fetchExecutions();
    const interval = setInterval(fetchExecutions, 30000);
    return () => clearInterval(interval);
  }, [fetchExecutions]);

  // Fetch DRS capacity when account changes
  useEffect(() => {
    const accountId = getCurrentAccountId();
    if (accountId) {
      fetchCapacityData(accountId);
      const interval = setInterval(() => {
        fetchCapacityData(accountId);
      }, 30000);
      return () => clearInterval(interval);
    } else {
      setCapacityData(null);
    }
  }, [selectedAccount, getCurrentAccountId, fetchCapacityData]);

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
              <SpaceBetween direction="horizontal" size="xs">
                <Button
                  iconName="refresh"
                  onClick={() => {
                    fetchExecutions();
                    const accountId = getCurrentAccountId();
                    if (accountId) {
                      fetchCapacityData(accountId);
                    }
                  }}
                  loading={loading || capacityLoading}
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

                  {/* Visual Capacity Gauges */}
                  <SpaceBetween size="l">
                    <ColumnLayout columns={3} variant="text-grid">
                      <div>
                        <Box variant="h3" padding={{ bottom: 's' }}>
                          Replication Capacity
                        </Box>
                        <CapacityGauge
                          used={capacityData.combined.totalReplicating}
                          total={capacityData.combined.maxReplicating}
                          size="medium"
                          label={`${capacityData.combined.totalReplicating.toLocaleString()} / ${capacityData.combined.maxReplicating.toLocaleString()} servers`}
                        />
                        <Box textAlign="center" padding={{ top: 's' }}>
                          <StatusIndicator
                            type={
                              capacityData.combined.status === 'OK'
                                ? 'success'
                                : capacityData.combined.status === 'INFO'
                                  ? 'info'
                                  : capacityData.combined.status === 'WARNING'
                                    ? 'warning'
                                    : 'error'
                            }
                          >
                            {capacityData.combined.status}
                          </StatusIndicator>
                        </Box>
                      </div>

                      <div>
                        <Box variant="h3" padding={{ bottom: 's' }}>
                          Recovery Capacity
                        </Box>
                        <CapacityGauge
                          used={capacityData.recoveryCapacity.currentServers}
                          total={capacityData.recoveryCapacity.maxRecoveryInstances}
                          size="medium"
                          label={`${capacityData.recoveryCapacity.currentServers.toLocaleString()} / ${capacityData.recoveryCapacity.maxRecoveryInstances.toLocaleString()} instances`}
                        />
                        <Box textAlign="center" padding={{ top: 's' }}>
                          <StatusIndicator
                            type={
                              capacityData.recoveryCapacity.status === 'OK'
                                ? 'success'
                                : capacityData.recoveryCapacity.status === 'WARNING'
                                  ? 'warning'
                                  : 'error'
                            }
                          >
                            {capacityData.recoveryCapacity.status}
                          </StatusIndicator>
                        </Box>
                      </div>

                      <div>
                        <Box variant="h3" padding={{ bottom: 's' }}>
                          Available Slots
                        </Box>
                        <Box textAlign="center" padding={{ top: 'xl', bottom: 'xl' }}>
                          <Box variant="awsui-value-large" color="text-status-success">
                            {capacityData.combined.availableSlots.toLocaleString()}
                          </Box>
                          <Box variant="small" color="text-body-secondary" padding={{ top: 'xs' }}>
                            slots available
                          </Box>
                        </Box>
                        <Box textAlign="center" padding={{ top: 's' }}>
                          <Box variant="small" color="text-body-secondary">
                            {capacityData.accounts.length} account{capacityData.accounts.length !== 1 ? 's' : ''} monitored
                          </Box>
                        </Box>
                      </div>
                    </ColumnLayout>

                    {/* DRS Service Limits */}
                    <ColumnLayout columns={3} variant="text-grid">
                      <div>
                        <Box variant="h3" padding={{ bottom: 's' }}>
                          Concurrent Recovery Jobs
                        </Box>
                        <CapacityGauge
                          used={capacityData.concurrentJobs?.current ?? 0}
                          total={capacityData.concurrentJobs?.max ?? 20}
                          size="medium"
                          label={`${(capacityData.concurrentJobs?.current ?? 0).toLocaleString()} / ${(capacityData.concurrentJobs?.max ?? 20).toLocaleString()} jobs`}
                        />
                        <Box textAlign="center" padding={{ top: 's' }}>
                          <Box variant="small" color="text-body-secondary">
                            {((capacityData.concurrentJobs?.max ?? 20) - (capacityData.concurrentJobs?.current ?? 0)).toLocaleString()} jobs available
                          </Box>
                        </Box>
                      </div>

                      <div>
                        <Box variant="h3" padding={{ bottom: 's' }}>
                          Servers in Active Jobs
                        </Box>
                        <CapacityGauge
                          used={capacityData.serversInJobs?.current ?? 0}
                          total={capacityData.serversInJobs?.max ?? 500}
                          size="medium"
                          label={`${(capacityData.serversInJobs?.current ?? 0).toLocaleString()} / ${(capacityData.serversInJobs?.max ?? 500).toLocaleString()} servers`}
                        />
                        <Box textAlign="center" padding={{ top: 's' }}>
                          <Box variant="small" color="text-body-secondary">
                            {((capacityData.serversInJobs?.max ?? 500) - (capacityData.serversInJobs?.current ?? 0)).toLocaleString()} slots available
                          </Box>
                        </Box>
                      </div>

                      <div>
                        <Box variant="h3" padding={{ bottom: 's' }}>
                          Max Servers Per Job
                        </Box>
                        {capacityData.maxServersPerJob ? (
                          <>
                            <CapacityGauge
                              used={capacityData.maxServersPerJob.current ?? 0}
                              total={capacityData.maxServersPerJob.max ?? 100}
                              size="medium"
                              label={`${(capacityData.maxServersPerJob.current ?? 0).toLocaleString()} / ${(capacityData.maxServersPerJob.max ?? 100).toLocaleString()} servers`}
                            />
                            <Box textAlign="center" padding={{ top: 's' }}>
                              <Box variant="small" color="text-body-secondary">
                                {capacityData.maxServersPerJob.current > 0
                                  ? `Largest job: ${capacityData.maxServersPerJob.current.toLocaleString()} servers`
                                  : 'No active jobs'}
                              </Box>
                            </Box>
                          </>
                        ) : (
                          <Box textAlign="center" padding={{ top: 'xl', bottom: 'xl' }}>
                            <Box variant="small" color="text-status-error">
                              Data not available
                            </Box>
                          </Box>
                        )}
                      </div>
                    </ColumnLayout>
                  </SpaceBetween>

                  {/* Per-Account Capacity Breakdown */}
                  {capacityData.accounts && capacityData.accounts.length > 0 && (
                    <Container
                      header={<Header variant="h3">Target Account Capacity</Header>}
                    >
                      <Table
                        columnDefinitions={[
                          {
                            id: 'accountName',
                            header: 'Account',
                            cell: (item) => (
                              <div>
                                <div>
                                  <strong>{item.accountName}</strong>
                                </div>
                                <div style={{ fontSize: '0.875rem', color: '#5f6b7a' }}>
                                  {item.accountId}
                                </div>
                              </div>
                            ),
                            sortingField: 'accountName',
                          },
                          {
                            id: 'replicatingServers',
                            header: 'Replicating Servers',
                            cell: (item) =>
                              `${item.replicatingServers.toLocaleString()} / ${item.maxReplicating.toLocaleString()}`,
                            sortingField: 'replicatingServers',
                          },
                          {
                            id: 'percentUsed',
                            header: 'Percentage Used',
                            cell: (item) => (
                              <div>
                                <div>{item.percentUsed.toFixed(1)}%</div>
                                <ProgressBar
                                  value={item.percentUsed}
                                  status={
                                    item.percentUsed < 67
                                      ? 'success'
                                      : item.percentUsed < 83
                                        ? 'in-progress'
                                        : 'error'
                                  }
                                  variant="standalone"
                                />
                              </div>
                            ),
                            sortingField: 'percentUsed',
                          },
                          {
                            id: 'availableSlots',
                            header: 'Available Slots',
                            cell: (item) => item.availableSlots.toLocaleString(),
                            sortingField: 'availableSlots',
                          },
                          {
                            id: 'status',
                            header: 'Status',
                            cell: (item) => (
                              <StatusIndicator
                                type={
                                  item.status === 'OK'
                                    ? 'success'
                                    : item.status === 'INFO'
                                      ? 'info'
                                      : item.status === 'WARNING'
                                        ? 'warning'
                                        : 'error'
                                }
                              >
                                {item.status}
                              </StatusIndicator>
                            ),
                            sortingField: 'status',
                          },
                          {
                            id: 'regions',
                            header: 'Regions',
                            cell: (item) => {
                              const activeRegions = item.regionalBreakdown?.filter(
                                (r: any) => r.replicatingServers > 0
                              ) || [];
                              return (
                                <Box variant="span" color="text-body-secondary">
                                  {activeRegions.length > 0
                                    ? `${activeRegions.length} active region${activeRegions.length !== 1 ? 's' : ''}`
                                    : 'No active regions'}
                                </Box>
                              );
                            },
                          },
                        ]}
                        items={capacityData.accounts.filter((acc) => acc.accountType === 'target')}
                        sortingDisabled={false}
                        variant="embedded"
                        expandableRows={{
                          getItemChildren: (item) => {
                            // Return empty array - we'll show custom content instead
                            return [];
                          },
                          isItemExpandable: (item) => {
                            // Always expandable to show regional breakdown
                            return true;
                          },
                          expandedItems: expandedItems,
                          onExpandableItemToggle: (event) => {
                            const item = event.detail.item;
                            const isCurrentlyExpanded = expandedItems.some(
                              (expandedItem) => expandedItem.accountId === item.accountId
                            );
                            setExpandedItems(isCurrentlyExpanded ? [] : [item]);
                          },
                        }}
                        empty={
                          <Box textAlign="center" color="inherit">
                            <b>No accounts</b>
                            <Box variant="p" color="inherit">
                              No capacity data available
                            </Box>
                          </Box>
                        }
                      />

                      {/* Expanded Content: Regional Breakdown & Staging Accounts */}
                      {expandedItems.length > 0 && expandedItems.map((expandedItem) => (
                        <Container key={expandedItem.accountId}>
                          <SpaceBetween size="m">
                            {/* Regional Breakdown */}
                            {expandedItem.regionalBreakdown && expandedItem.regionalBreakdown.length > 0 && (
                              <div>
                                <Box variant="h4" padding={{ bottom: 's' }}>
                                  Regional Breakdown
                                </Box>
                                <ColumnLayout columns={4} variant="text-grid">
                                  {expandedItem.regionalBreakdown
                                    .filter((region: any) => region.replicatingServers > 0)
                                    .map((region: any) => (
                                      <div key={region.region}>
                                        <SpaceBetween size="xxs">
                                          <Box>
                                            <strong>{region.region}</strong>
                                            <Box variant="small" color="text-body-secondary" display="inline" margin={{ left: 'xs' }}>
                                              {(region.percentUsed || 0) < 67
                                                ? '✓'
                                                : (region.percentUsed || 0) < 83
                                                  ? '⚠'
                                                  : '✗'}
                                            </Box>
                                          </Box>
                                          <Box variant="small">
                                            {region.replicatingServers.toLocaleString()} / {region.maxReplicating?.toLocaleString() || '300'} servers
                                          </Box>
                                          <ProgressBar
                                            value={region.percentUsed || 0}
                                            status={
                                              (region.percentUsed || 0) < 67
                                                ? 'success'
                                                : (region.percentUsed || 0) < 83
                                                  ? 'in-progress'
                                                  : 'error'
                                            }
                                            variant="standalone"
                                          />
                                        </SpaceBetween>
                                      </div>
                                    ))}
                                </ColumnLayout>
                              </div>
                            )}

                            {/* Staging Accounts */}
                            {capacityData.accounts.filter((acc) => acc.accountType === 'staging').length > 0 && (
                              <div>
                                <Box variant="h4" padding={{ bottom: 's' }}>
                                  Staging Accounts
                                </Box>
                                <Table
                                  columnDefinitions={[
                                    {
                                      id: 'accountName',
                                      header: 'Account',
                                      cell: (item) => (
                                        <div>
                                          <div><strong>{item.accountName}</strong></div>
                                          <div style={{ fontSize: '0.875rem', color: '#5f6b7a' }}>
                                            {item.accountId}
                                          </div>
                                        </div>
                                      ),
                                    },
                                    {
                                      id: 'replicatingServers',
                                      header: 'Servers',
                                      cell: (item) =>
                                        `${item.replicatingServers.toLocaleString()} / ${item.maxReplicating.toLocaleString()}`,
                                    },
                                    {
                                      id: 'percentUsed',
                                      header: '% Used',
                                      cell: (item) => `${item.percentUsed.toFixed(1)}%`,
                                    },
                                    {
                                      id: 'status',
                                      header: 'Status',
                                      cell: (item) => (
                                        <StatusIndicator
                                          type={
                                            item.status === 'OK'
                                              ? 'success'
                                              : item.status === 'INFO'
                                                ? 'info'
                                                : item.status === 'WARNING'
                                                  ? 'warning'
                                                  : 'error'
                                          }
                                        >
                                          {item.status}
                                        </StatusIndicator>
                                      ),
                                    },
                                    {
                                      id: 'regions',
                                      header: 'Regions',
                                      cell: (item) => {
                                        const activeRegions = item.regionalBreakdown?.filter(
                                          (r: any) => r.replicatingServers > 0
                                        ) || [];
                                        return (
                                          <Box variant="span" color="text-body-secondary">
                                            {activeRegions.length > 0
                                              ? `${activeRegions.length} active region${activeRegions.length !== 1 ? 's' : ''}`
                                              : 'No active regions'}
                                          </Box>
                                        );
                                      },
                                    },
                                  ]}
                                  items={capacityData.accounts.filter((acc) => acc.accountType === 'staging')}
                                  variant="embedded"
                                  expandableRows={{
                                    getItemChildren: (item) => [],
                                    isItemExpandable: (item) => {
                                      const activeRegions = item.regionalBreakdown?.filter(
                                        (r: any) => r.replicatingServers > 0
                                      ) || [];
                                      return activeRegions.length > 0;
                                    },
                                    expandedItems: expandedStagingItems,
                                    onExpandableItemToggle: (event) => {
                                      const item = event.detail.item;
                                      const isCurrentlyExpanded = expandedStagingItems.some(
                                        (expandedItem) => expandedItem.accountId === item.accountId
                                      );
                                      setExpandedStagingItems(isCurrentlyExpanded ? [] : [item]);
                                    },
                                  }}
                                  empty={
                                    <Box textAlign="center" color="inherit">
                                      No staging accounts
                                    </Box>
                                  }
                                />
                                
                                {/* Staging Account Regional Breakdown */}
                                {expandedStagingItems.length > 0 && expandedStagingItems.map((stagingItem) => (
                                  <Container key={`staging-${stagingItem.accountId}`}>
                                    <Box variant="h5" padding={{ bottom: 's' }}>
                                      Regional Breakdown - {stagingItem.accountName}
                                    </Box>
                                    <ColumnLayout columns={4} variant="text-grid">
                                      {stagingItem.regionalBreakdown
                                        ?.filter((region: any) => region.replicatingServers > 0)
                                        .map((region: any) => (
                                          <div key={region.region}>
                                            <SpaceBetween size="xxs">
                                              <Box>
                                                <strong>{region.region}</strong>
                                                <Box variant="small" color="text-body-secondary" display="inline" margin={{ left: 'xs' }}>
                                                  {(region.percentUsed || 0) < 67
                                                    ? '✓'
                                                    : (region.percentUsed || 0) < 83
                                                      ? '⚠'
                                                      : '✗'}
                                                </Box>
                                              </Box>
                                              <Box variant="small">
                                                {region.replicatingServers.toLocaleString()} / {region.maxReplicating?.toLocaleString() || '300'} servers
                                              </Box>
                                              <ProgressBar
                                                value={region.percentUsed || 0}
                                                status={
                                                  (region.percentUsed || 0) < 67
                                                    ? 'success'
                                                    : (region.percentUsed || 0) < 83
                                                      ? 'in-progress'
                                                      : 'error'
                                                }
                                                variant="standalone"
                                              />
                                            </SpaceBetween>
                                          </div>
                                        ))}
                                    </ColumnLayout>
                                  </Container>
                                ))}
                              </div>
                            )}
                          </SpaceBetween>
                        </Container>
                      ))}

                      {/* Account-specific warnings */}
                      {capacityData.accounts.some((acc) => acc.warnings && acc.warnings.length > 0) && (
                        <Box margin={{ top: 'm' }}>
                          <SpaceBetween size="s">
                            {capacityData.accounts
                              .filter((acc) => acc.warnings && acc.warnings.length > 0)
                              .map((acc) =>
                                acc.warnings.map((warning, idx) => (
                                  <Alert
                                    key={`${acc.accountId}-${idx}`}
                                    type={
                                      acc.status === 'OK'
                                        ? 'info'
                                        : acc.status === 'INFO'
                                          ? 'info'
                                          : acc.status === 'WARNING'
                                            ? 'warning'
                                            : 'error'
                                    }
                                    header={`${acc.accountName} Warning`}
                                  >
                                    {warning}
                                  </Alert>
                                ))
                              )}
                          </SpaceBetween>
                        </Box>
                      )}
                    </Container>
                  )}
                </SpaceBetween>
              ) : (
                <Box textAlign="center" padding="l" color="text-body-secondary">
                  Select a target account to view capacity
                </Box>
              )}
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