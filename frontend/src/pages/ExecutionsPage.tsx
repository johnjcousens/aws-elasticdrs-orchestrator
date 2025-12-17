import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  SpaceBetween,
  Button,
  Header,
  Table,
  Tabs,
  Container,
  ProgressBar,
  Badge,
  Pagination,
  TextFilter,
  Alert,
  Modal,
  Select,
} from '@cloudscape-design/components';
import type { SelectProps } from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { formatDistanceToNow } from 'date-fns';
import { useNotifications } from '../contexts/NotificationContext';
import { useAccount } from '../contexts/AccountContext';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { CardSkeleton } from '../components/CardSkeleton';
import { PageTransition } from '../components/PageTransition';
import { StatusBadge } from '../components/StatusBadge';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import { InvocationSourceBadge } from '../components/InvocationSourceBadge';
import type { InvocationSource, InvocationDetails } from '../components/InvocationSourceBadge';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';

// Invocation source filter options
const INVOCATION_SOURCE_OPTIONS: SelectProps.Option[] = [
  { value: '', label: 'All Sources' },
  { value: 'UI', label: 'UI (Manual)' },
  { value: 'CLI', label: 'CLI' },
  { value: 'EVENTBRIDGE', label: 'Scheduled' },
  { value: 'SSM', label: 'SSM Runbook' },
  { value: 'STEPFUNCTIONS', label: 'Step Functions' },
  { value: 'API', label: 'API' },
];

// Selection mode filter options
const SELECTION_MODE_OPTIONS: SelectProps.Option[] = [
  { value: '', label: 'All Modes' },
  { value: 'PLAN', label: 'Plan-Based' },
  { value: 'TAGS', label: 'Tag-Based' },
];

export const ExecutionsPage: React.FC = () => {
  const navigate = useNavigate();
  const { addNotification } = useNotifications();
  const { getCurrentAccountId } = useAccount();
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeTabId, setActiveTabId] = useState('active');
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [refreshing, setRefreshing] = useState(false);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<SelectProps.Option | null>(null);
  const [modeFilter, setModeFilter] = useState<SelectProps.Option | null>(null);

  useEffect(() => {
    fetchExecutions();
  }, []);

  useEffect(() => {
    const hasActiveExecutions = executions.some((e) => {
      const status = e.status.toLowerCase();
      return ['in_progress', 'pending', 'running', 'started', 'polling', 'launching', 'initiated'].includes(status);
    });
    if (!hasActiveExecutions) return;
    const interval = setInterval(() => fetchExecutions(), 3000);
    return () => clearInterval(interval);
  }, [executions]);

  const fetchExecutions = async () => {
    try {
      if (loading) setErrorMsg(null);
      const accountId = getCurrentAccountId();
      const response = await apiClient.listExecutions(accountId ? { accountId } : undefined);
      setExecutions(response.items);
      setLastRefresh(new Date());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load executions';
      setErrorMsg(msg);
      addNotification('error', msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleViewDetails = (execution: ExecutionListItem) => {
    navigate(`/executions/${execution.executionId}`);
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchExecutions();
  };

  const handleClearHistory = () => setClearDialogOpen(true);

  const handleConfirmClear = async () => {
    setClearing(true);
    try {
      const result = await apiClient.deleteCompletedExecutions();
      addNotification('success', `Cleared ${result.deletedCount} completed executions`);
      setClearDialogOpen(false);
      await fetchExecutions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to clear history';
      addNotification('error', msg);
    } finally {
      setClearing(false);
    }
  };

  const activeExecutions = executions.filter((e) => {
    const status = e.status.toUpperCase();
    return ['PENDING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 'IN_PROGRESS', 'PAUSED', 'RUNNING'].includes(status);
  });

  const historyExecutions = executions.filter((e) => {
    const status = e.status.toUpperCase();
    const isTerminal = ['COMPLETED', 'PARTIAL', 'FAILED', 'CANCELLED', 'ROLLED_BACK', 'TIMEOUT'].includes(status);
    if (!isTerminal) return false;
    
    // Apply source filter
    if (sourceFilter?.value && (e as any).invocationSource !== sourceFilter.value) {
      return false;
    }
    
    // Apply selection mode filter
    if (modeFilter?.value && (e as any).selectionMode !== modeFilter.value) {
      return false;
    }
    
    return true;
  });

  const calculateProgress = (execution: ExecutionListItem): number => {
    if (execution.status !== 'in_progress' || !execution.currentWave) return 0;
    return (execution.currentWave / execution.totalWaves) * 100;
  };

  const calculateDuration = (execution: ExecutionListItem): string => {
    if (!execution.startTime) return '-';
    
    // Handle Unix timestamps (seconds) vs JavaScript timestamps (milliseconds)
    let startTimeMs: number | string = execution.startTime;
    if (typeof startTimeMs === 'number' && startTimeMs < 10000000000) {
      startTimeMs = startTimeMs * 1000; // Convert seconds to milliseconds
    }
    
    let endTimeMs: number | string | undefined = execution.endTime;
    if (endTimeMs && typeof endTimeMs === 'number' && endTimeMs < 10000000000) {
      endTimeMs = endTimeMs * 1000; // Convert seconds to milliseconds
    }
    
    const start = new Date(startTimeMs);
    if (isNaN(start.getTime())) return '-';
    
    // For failed/completed executions without endTime, show '-' instead of calculating from now
    const isTerminal = ['completed', 'failed', 'cancelled', 'partial', 'COMPLETED', 'FAILED', 'CANCELLED', 'PARTIAL'].includes(execution.status as string);
    if (isTerminal && !endTimeMs) return '-';
    
    const end = endTimeMs ? new Date(endTimeMs) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    // Sanity check - duration shouldn't be negative or more than a year
    if (durationMs < 0 || durationMs > 365 * 24 * 60 * 60 * 1000) return '-';
    
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };


  const { items, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    historyExecutions,
    {
      filtering: { empty: 'No execution history', noMatch: 'No executions match the filter' },
      pagination: { pageSize: 10 },
      sorting: {},
    }
  );

  if (loading && executions.length === 0) {
    return <LoadingState message="Loading executions..." />;
  }

  if (errorMsg && executions.length === 0) {
    return <ErrorState message={errorMsg} onRetry={fetchExecutions} />;
  }

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            description="Real-time monitoring and historical records of DRS recoveries"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                {activeExecutions.length > 0 && (
                  <Box>
                    <Badge color="green">Live Updates</Badge>
                    <Box variant="small" color="text-body-secondary" display="inline" margin={{ left: 'xs' }}>
                      Updated {formatDistanceToNow(lastRefresh, { addSuffix: true })}
                    </Box>
                  </Box>
                )}
                <Button onClick={handleRefresh} disabled={refreshing} iconName="refresh">
                  Refresh
                </Button>
              </SpaceBetween>
            }
          >
            History
          </Header>
        }
      >
        <AccountRequiredWrapper pageName="Executions">
          <SpaceBetween size="l">
          {errorMsg && executions.length > 0 && (
            <Alert type="error" dismissible onDismiss={() => setErrorMsg(null)}>
              {errorMsg}
            </Alert>
          )}

          <Tabs
            activeTabId={activeTabId}
            onChange={({ detail }) => setActiveTabId(detail.activeTabId)}
            tabs={[
              {
                id: 'active',
                label: `Active (${activeExecutions.length})`,
                content: (
                  <SpaceBetween size="m">
                    {loading ? (
                      <CardSkeleton count={3} />
                    ) : activeExecutions.length === 0 ? (
                      <Container>
                        <Box textAlign="center" padding="xxl">
                          <b>No Active Executions</b>
                          <Box padding={{ top: 's' }} color="text-body-secondary">
                            Start a recovery plan execution to monitor progress here
                          </Box>
                        </Box>
                      </Container>
                    ) : (
                      activeExecutions.map((execution) => (
                        <Container key={execution.executionId} header={<Header variant="h2">{execution.recoveryPlanName}</Header>}>
                          <SpaceBetween size="m">
                            <SpaceBetween direction="horizontal" size="m">
                              <StatusBadge status={execution.status} />
                              {execution.currentWave && (
                                <Box color="text-body-secondary">
                                  Wave {execution.currentWave} of {execution.totalWaves}
                                </Box>
                              )}
                              <DateTimeDisplay value={execution.startTime} format="full" />
                              <Box color="text-body-secondary">Duration: {calculateDuration(execution)}</Box>
                            </SpaceBetween>
                            {execution.status === 'in_progress' && execution.currentWave && (
                              <Box>
                                <SpaceBetween direction="horizontal" size="xs">
                                  <Box variant="small" color="text-body-secondary">Progress</Box>
                                  <Box variant="small" color="text-body-secondary">{Math.round(calculateProgress(execution))}%</Box>
                                </SpaceBetween>
                                <ProgressBar value={calculateProgress(execution)} variant="standalone" />
                              </Box>
                            )}
                            <Button onClick={() => handleViewDetails(execution)}>View Details</Button>
                          </SpaceBetween>
                        </Container>
                      ))
                    )}
                  </SpaceBetween>
                ),
              },
              {
                id: 'history',
                label: `History (${historyExecutions.length})`,
                content: (
                  <SpaceBetween size="m">
                    {historyExecutions.length > 0 && (
                      <Box float="right">
                        <Button variant="normal" onClick={handleClearHistory} disabled={clearing}>
                          Clear Completed History
                        </Button>
                      </Box>
                    )}
                    <Table
                      {...collectionProps}
                      columnDefinitions={[
                        { id: 'plan', header: 'Plan Name', cell: (item) => item.recoveryPlanName || '-', sortingField: 'recoveryPlanName', width: 180 },
                        { id: 'status', header: 'Status', cell: (item) => <StatusBadge status={item.status} />, width: 110 },
                        { 
                          id: 'source', 
                          header: 'Source', 
                          cell: (item) => (
                            <span style={{ whiteSpace: 'nowrap' }}>
                              <InvocationSourceBadge 
                                source={((item as any).invocationSource || 'UI') as InvocationSource} 
                                details={(item as any).invocationDetails as InvocationDetails}
                              />
                            </span>
                          ),
                          width: 100,
                        },
                        { 
                          id: 'recoveryType', 
                          header: 'Recovery Type', 
                          cell: (item) => (
                            <span style={{ whiteSpace: 'nowrap' }}>
                              <Badge color="blue">
                                {item.selectionMode === 'TAGS' ? 'Tag-Based' : 'Plan-Based'}
                              </Badge>
                            </span>
                          ),
                          width: 110,
                        },
                        { 
                          id: 'type', 
                          header: 'Type', 
                          cell: (item) => (
                            <Badge color={item.executionType === 'DRILL' ? 'blue' : 'red'}>
                              {item.executionType || 'DRILL'}
                            </Badge>
                          ),
                          width: 70,
                        },
                        { id: 'waves', header: 'Waves', cell: (item) => (item.totalWaves > 0 ? `${item.totalWaves} waves` : '-'), width: 70 },
                        { id: 'started', header: 'Started', cell: (item) => <DateTimeDisplay value={item.startTime} format="full" />, width: 150 },
                        { id: 'completed', header: 'Completed', cell: (item) => (item.endTime ? <DateTimeDisplay value={item.endTime} format="full" /> : '-'), width: 150 },
                        { id: 'duration', header: 'Duration', cell: (item) => calculateDuration(item), width: 80 },
                        { id: 'actions', header: 'Actions', cell: (item) => <Button variant="inline-link" iconName="external" onClick={() => handleViewDetails(item)}>View</Button>, width: 70 },
                      ]}
                      items={items}
                      loading={loading}
                      loadingText="Loading execution history"
                      empty={
                        <Box textAlign="center" color="inherit">
                          <b>No execution history</b>
                          <Box padding={{ bottom: 's' }} variant="p" color="inherit">Completed executions will appear here</Box>
                        </Box>
                      }
                      filter={
                        <SpaceBetween direction="horizontal" size="xs">
                          <TextFilter {...filterProps} filteringPlaceholder="Find executions" countText={`${filteredItemsCount} ${filteredItemsCount === 1 ? 'match' : 'matches'}`} />
                          <Select
                            selectedOption={sourceFilter}
                            onChange={({ detail }) => setSourceFilter(detail.selectedOption)}
                            options={INVOCATION_SOURCE_OPTIONS}
                            placeholder="Filter by source"
                          />
                          <Select
                            selectedOption={modeFilter}
                            onChange={({ detail }) => setModeFilter(detail.selectedOption)}
                            options={SELECTION_MODE_OPTIONS}
                            placeholder="Filter by mode"
                          />
                        </SpaceBetween>
                      }
                      pagination={<Pagination {...paginationProps} />}
                      variant="full-page"
                    />
                  </SpaceBetween>
                ),
              },
            ]}
          />

          <Modal
            visible={clearDialogOpen}
            onDismiss={() => setClearDialogOpen(false)}
            header="Clear Completed History?"
            footer={
              <Box float="right">
                <SpaceBetween direction="horizontal" size="xs">
                  <Button onClick={() => setClearDialogOpen(false)} disabled={clearing}>Cancel</Button>
                  <Button variant="primary" onClick={handleConfirmClear} disabled={clearing} loading={clearing}>Clear History</Button>
                </SpaceBetween>
              </Box>
            }
          >
            <SpaceBetween size="m">
              <Box>This will permanently delete all completed execution records ({historyExecutions.length} items). Active executions will not be affected.</Box>
              <Alert type="warning">This action cannot be undone.</Alert>
            </SpaceBetween>
          </Modal>
        </SpaceBetween>
        </AccountRequiredWrapper>
      </ContentLayout>
    </PageTransition>
  );
};
