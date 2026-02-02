/**
 * System Status Page
 * 
 * Comprehensive system health view with visual capacity gauges:
 * - Visual capacity gauges with color coding
 * - Collapsible per-account breakdown
 * - Paused/waiting executions alerts
 * - Compact, space-efficient layout
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  SpaceBetween,
  Container,
  Header,
  StatusIndicator,
  Spinner,
  Alert,
  Link,
  ColumnLayout,
  ExpandableSection,
  Button,
  Toggle,
} from '@cloudscape-design/components';
import { useNavigate } from 'react-router-dom';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { CapacityGauge } from '../components/CapacityGauge';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { useAccount } from '../contexts/AccountContext';
import { getCombinedCapacity } from '../services/staging-accounts-api';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';
import type { CombinedCapacityData, CapacityStatus } from '../types/staging-accounts';

const getStatusType = (
  status: CapacityStatus
): "success" | "warning" | "error" | "info" => {
  switch (status) {
    case "OK":
      return "success";
    case "INFO":
      return "info";
    case "WARNING":
      return "warning";
    case "CRITICAL":
    case "HYPER-CRITICAL":
      return "error";
    default:
      return "info";
  }
};

const formatNumber = (num: number): string => num.toLocaleString();

export const SystemStatusPage: React.FC = () => {
  const navigate = useNavigate();
  const { getCurrentAccountId } = useAccount();
  
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [capacityData, setCapacityData] = useState<CombinedCapacityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [capacityLoading, setCapacityLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

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
      setExecutions(Array.isArray(response?.items) ? response.items : []);
      setError(null);
    } catch (err) {
      setError('Failed to load executions');
      console.error('Error fetching executions:', err);
    } finally {
      setLoading(false);
    }
  }, [getCurrentAccountId]);

  const fetchCapacity = useCallback(async () => {
    const accountId = getCurrentAccountId();
    if (!accountId) {
      setCapacityLoading(false);
      return;
    }

    try {
      setCapacityLoading(true);
      const data = await getCombinedCapacity(accountId, true);
      console.log('Capacity data received:', data);
      console.log('maxServersPerJob field:', data.maxServersPerJob);
      setCapacityData(data);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Error fetching capacity:', err);
    } finally {
      setCapacityLoading(false);
    }
  }, [getCurrentAccountId]);

  useEffect(() => {
    fetchExecutions();
    fetchCapacity();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchExecutions();
        fetchCapacity();
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [fetchExecutions, fetchCapacity, autoRefresh]);

  const pausedExecutions = executions.filter((e) => e.status === 'paused');
  const waitingExecutions = executions.filter((e) => e.status === 'pending');

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            description="Monitor disaster recovery capacity and active operations"
          >
            System Status
          </Header>
        }
      >
        <AccountRequiredWrapper pageName="system status">
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
              {/* Alerts Section */}
              {(pausedExecutions.length > 0 || waitingExecutions.length > 0) && (
                <Container header={<Header variant="h2">Alerts</Header>}>
                  <SpaceBetween size="m">
                    {pausedExecutions.length > 0 && (
                      <Alert
                        type="warning"
                        header={`${pausedExecutions.length} execution${pausedExecutions.length > 1 ? 's' : ''} paused`}
                        action={
                          <Link onFollow={() => navigate('/executions')}>
                            View executions
                          </Link>
                        }
                      >
                        The following executions are paused and waiting for resume:
                        <Box padding={{ top: 's' }}>
                          <SpaceBetween size="xs">
                            {pausedExecutions.map((exec) => (
                              <Link
                                key={exec.executionId}
                                onFollow={() =>
                                  navigate(`/executions/${exec.executionId}`)
                                }
                              >
                                {exec.recoveryPlanName || exec.recoveryPlanId}
                              </Link>
                            ))}
                          </SpaceBetween>
                        </Box>
                      </Alert>
                    )}

                    {waitingExecutions.length > 0 && (
                      <Alert
                        type="info"
                        header={`${waitingExecutions.length} execution${waitingExecutions.length > 1 ? 's' : ''} pending`}
                      >
                        {waitingExecutions.length} execution
                        {waitingExecutions.length > 1 ? 's are' : ' is'} waiting
                        to start
                      </Alert>
                    )}
                  </SpaceBetween>
                </Container>
              )}

              {/* Capacity Overview with Visual Gauges */}
              <Container
                header={
                  <Header
                    variant="h2"
                    actions={
                      <SpaceBetween direction="horizontal" size="xs">
                        <Toggle
                          checked={autoRefresh}
                          onChange={({ detail }) => setAutoRefresh(detail.checked)}
                        >
                          Auto-refresh
                        </Toggle>
                        <Button
                          iconName="refresh"
                          onClick={() => {
                            fetchExecutions();
                            fetchCapacity();
                          }}
                          loading={capacityLoading}
                        >
                          Refresh
                        </Button>
                      </SpaceBetween>
                    }
                    description={
                      lastRefresh
                        ? `Last updated: ${lastRefresh.toLocaleTimeString()}`
                        : undefined
                    }
                  >
                    Capacity Overview
                  </Header>
                }
              >
                {capacityLoading && !capacityData ? (
                  <Box textAlign="center" padding="l">
                    <Spinner size="large" />
                  </Box>
                ) : capacityData ? (
                  <SpaceBetween size="l">
                    {/* Warnings */}
                    {capacityData.warnings.length > 0 && (
                      <SpaceBetween size="s">
                        {capacityData.warnings.map((warning, index) => (
                          <Alert
                            key={index}
                            type={getStatusType(capacityData.combined.status) === 'success' ? 'warning' : getStatusType(capacityData.combined.status)}
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
                            label={`${formatNumber(capacityData.combined.totalReplicating)} / ${formatNumber(capacityData.combined.maxReplicating)} servers`}
                          />
                          <Box textAlign="center" padding={{ top: 's' }}>
                            <StatusIndicator type={getStatusType(capacityData.combined.status)}>
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
                            label={`${formatNumber(capacityData.recoveryCapacity.currentServers)} / ${formatNumber(capacityData.recoveryCapacity.maxRecoveryInstances)} instances`}
                          />
                          <Box textAlign="center" padding={{ top: 's' }}>
                            <StatusIndicator type={getStatusType(capacityData.recoveryCapacity.status as CapacityStatus)}>
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
                              {formatNumber(capacityData.combined.availableSlots)}
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
                            label={`${formatNumber(capacityData.concurrentJobs?.current ?? 0)} / ${formatNumber(capacityData.concurrentJobs?.max ?? 20)} jobs`}
                          />
                          <Box textAlign="center" padding={{ top: 's' }}>
                            <Box variant="small" color="text-body-secondary">
                              {formatNumber((capacityData.concurrentJobs?.max ?? 20) - (capacityData.concurrentJobs?.current ?? 0))} jobs available
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
                            label={`${formatNumber(capacityData.serversInJobs?.current ?? 0)} / ${formatNumber(capacityData.serversInJobs?.max ?? 500)} servers`}
                          />
                          <Box textAlign="center" padding={{ top: 's' }}>
                            <Box variant="small" color="text-body-secondary">
                              {formatNumber((capacityData.serversInJobs?.max ?? 500) - (capacityData.serversInJobs?.current ?? 0))} slots available
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
                                label={`${formatNumber(capacityData.maxServersPerJob.current ?? 0)} / ${formatNumber(capacityData.maxServersPerJob.max ?? 100)} servers`}
                              />
                              <Box textAlign="center" padding={{ top: 's' }}>
                                <Box variant="small" color="text-body-secondary">
                                  {capacityData.maxServersPerJob.current > 0
                                    ? `Largest job: ${formatNumber(capacityData.maxServersPerJob.current)} servers`
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

                    {/* Collapsible Per-Account Breakdown */}
                    <ExpandableSection
                      headerText="Per-Account Capacity Breakdown"
                      variant="container"
                      defaultExpanded={false}
                    >
                      <SpaceBetween size="m">
                        {/* Group accounts: target accounts first, then their staging accounts nested */}
                        {(() => {
                          const targetAccounts = capacityData.accounts.filter(
                            (acc) => acc.accountType === "target"
                          );
                          const stagingAccounts = capacityData.accounts.filter(
                            (acc) => acc.accountType === "staging"
                          );

                          return targetAccounts.map((targetAccount) => (
                            <Container key={targetAccount.accountId}>
                              <SpaceBetween size="m">
                                {/* Target Account Row */}
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <div style={{ flex: 1 }}>
                                    <div>
                                      <strong>{targetAccount.accountName}</strong>
                                      <Box variant="span" color="text-status-info" margin={{ left: 'xs' }}>
                                        (target)
                                      </Box>
                                    </div>
                                    <div style={{ fontSize: "0.875rem", color: "#5f6b7a" }}>
                                      {targetAccount.accountId}
                                    </div>
                                  </div>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                      <CapacityGauge
                                        used={targetAccount.replicatingServers}
                                        total={targetAccount.maxReplicating}
                                        size="small"
                                        showLabel={false}
                                      />
                                      <div>
                                        <div>{targetAccount.percentUsed.toFixed(1)}%</div>
                                        <div style={{ fontSize: "0.875rem", color: "#5f6b7a" }}>
                                          {formatNumber(targetAccount.replicatingServers)} / {formatNumber(targetAccount.maxReplicating)}
                                        </div>
                                      </div>
                                    </div>
                                    <div>
                                      <div><strong>{formatNumber(targetAccount.availableSlots)}</strong></div>
                                      <div style={{ fontSize: "0.875rem", color: "#5f6b7a" }}>slots</div>
                                    </div>
                                    <StatusIndicator type={getStatusType(targetAccount.status)}>
                                      {targetAccount.status}
                                    </StatusIndicator>
                                    <div style={{ minWidth: '120px' }}>
                                      {targetAccount.regionalBreakdown.map((region, idx) => (
                                        <div
                                          key={region.region}
                                          style={{
                                            fontSize: "0.875rem",
                                            marginBottom:
                                              idx < targetAccount.regionalBreakdown.length - 1
                                                ? "4px"
                                                : "0",
                                          }}
                                        >
                                          <strong>{region.region}:</strong>{" "}
                                          {formatNumber(region.replicatingServers)}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                </div>

                                {/* Staging Accounts (nested under target) */}
                                {stagingAccounts.length > 0 && (
                                  <ExpandableSection
                                    headerText={`Connected Staging Accounts (${stagingAccounts.length})`}
                                    variant="footer"
                                    defaultExpanded={false}
                                  >
                                    <SpaceBetween size="s">
                                      {stagingAccounts.map((stagingAccount) => (
                                        <div
                                          key={stagingAccount.accountId}
                                          style={{
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                            paddingLeft: '24px',
                                            borderLeft: '2px solid #e9ebed',
                                          }}
                                        >
                                          <div style={{ flex: 1 }}>
                                            <div>
                                              {stagingAccount.accountName}
                                              <Box variant="span" color="text-body-secondary" margin={{ left: 'xs' }}>
                                                (staging)
                                              </Box>
                                            </div>
                                            <div style={{ fontSize: "0.875rem", color: "#5f6b7a" }}>
                                              {stagingAccount.accountId}
                                            </div>
                                          </div>
                                          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                              <CapacityGauge
                                                used={stagingAccount.replicatingServers}
                                                total={stagingAccount.maxReplicating}
                                                size="small"
                                                showLabel={false}
                                              />
                                              <div>
                                                <div>{stagingAccount.percentUsed.toFixed(1)}%</div>
                                                <div style={{ fontSize: "0.875rem", color: "#5f6b7a" }}>
                                                  {formatNumber(stagingAccount.replicatingServers)} / {formatNumber(stagingAccount.maxReplicating)}
                                                </div>
                                              </div>
                                            </div>
                                            <div>
                                              <div><strong>{formatNumber(stagingAccount.availableSlots)}</strong></div>
                                              <div style={{ fontSize: "0.875rem", color: "#5f6b7a" }}>slots</div>
                                            </div>
                                            <StatusIndicator type={getStatusType(stagingAccount.status)}>
                                              {stagingAccount.status}
                                            </StatusIndicator>
                                            <div style={{ minWidth: '120px' }}>
                                              {stagingAccount.regionalBreakdown.map((region, idx) => (
                                                <div
                                                  key={region.region}
                                                  style={{
                                                    fontSize: "0.875rem",
                                                    marginBottom:
                                                      idx < stagingAccount.regionalBreakdown.length - 1
                                                        ? "4px"
                                                        : "0",
                                                  }}
                                                >
                                                  <strong>{region.region}:</strong>{" "}
                                                  {formatNumber(region.replicatingServers)}
                                                </div>
                                              ))}
                                            </div>
                                          </div>
                                        </div>
                                      ))}
                                    </SpaceBetween>
                                  </ExpandableSection>
                                )}
                              </SpaceBetween>
                            </Container>
                          ));
                        })()}
                      </SpaceBetween>
                    </ExpandableSection>
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
