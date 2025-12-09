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
} from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { CardSkeleton } from '../components/CardSkeleton';
import { PageTransition } from '../components/PageTransition';
import { StatusBadge } from '../components/StatusBadge';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';

export const ExecutionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeTabId, setActiveTabId] = useState('active');
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [refreshing, setRefreshing] = useState(false);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const [clearing, setClearing] = useState(false);

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
      const response = await apiClient.listExecutions();
      setExecutions(response.items);
      setLastRefresh(new Date());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load executions';
      setErrorMsg(msg);
      toast.error(msg);
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
      toast.success(`Cleared ${result.deletedCount} completed executions`);
      setClearDialogOpen(false);
      await fetchExecutions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to clear history';
      toast.error(msg);
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
    return ['COMPLETED', 'PARTIAL', 'FAILED', 'CANCELLED', 'ROLLED_BACK', 'TIMEOUT'].includes(status);
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
                        { id: 'plan', header: 'Plan Name', cell: (item) => item.recoveryPlanName, sortingField: 'recoveryPlanName' },
                        { id: 'status', header: 'Status', cell: (item) => <StatusBadge status={item.status} /> },
                        { id: 'waves', header: 'Waves', cell: (item) => (item.totalWaves > 0 ? `${item.totalWaves} waves` : '-') },
                        { id: 'started', header: 'Started', cell: (item) => <DateTimeDisplay value={item.startTime} format="full" /> },
                        { id: 'completed', header: 'Completed', cell: (item) => (item.endTime ? <DateTimeDisplay value={item.endTime} format="full" /> : '-') },
                        { id: 'duration', header: 'Duration', cell: (item) => calculateDuration(item) },
                        { id: 'actions', header: 'Actions', cell: (item) => <Button variant="inline-link" iconName="external" onClick={() => handleViewDetails(item)}>View</Button> },
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
                      filter={<TextFilter {...filterProps} filteringPlaceholder="Find executions" countText={`${filteredItemsCount} ${filteredItemsCount === 1 ? 'match' : 'matches'}`} />}
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
      </ContentLayout>
    </PageTransition>
  );
};
