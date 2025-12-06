/**
 * Executions Page
 * 
 * Main page for monitoring DRS recovery executions.
 * Provides real-time visibility into active and historical executions.
 */

import React, { useState, useEffect } from 'react';
import type { ExecutionListItem } from '../types';
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
import { ExecutionDetails } from '../components/ExecutionDetails';
import apiClient from '../services/api';

/**
 * Executions Page Component
 * 
 * Displays active and historical executions with real-time updates.
 */
export const ExecutionsPage: React.FC = () => {
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTabId, setActiveTabId] = useState('active');
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [refreshing, setRefreshing] = useState(false);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    fetchExecutions();
  }, []);

  // Real-time polling for active executions
  useEffect(() => {
    const hasActiveExecutions = executions.some(
      e => e.status === 'in_progress' || e.status === 'pending'
    );

    if (!hasActiveExecutions) return;

    const interval = setInterval(() => {
      fetchExecutions();
    }, 3000);

    return () => clearInterval(interval);
  }, [executions]);

  const fetchExecutions = async () => {
    try {
      if (loading) {
        setError(null);
      }
      const response = await apiClient.listExecutions();
      setExecutions(response.items);
      setLastRefresh(new Date());
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load executions';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleViewDetails = (execution: ExecutionListItem) => {
    setSelectedExecutionId(execution.executionId);
    setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
    setSelectedExecutionId(null);
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchExecutions();
  };

  const handleClearHistory = () => {
    setClearDialogOpen(true);
  };

  const handleConfirmClear = async () => {
    setClearing(true);
    try {
      const result = await apiClient.deleteCompletedExecutions();
      toast.success(`Cleared ${result.deletedCount} completed executions`);
      setClearDialogOpen(false);
      await fetchExecutions();
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to clear history';
      toast.error(errorMessage);
    } finally {
      setClearing(false);
    }
  };

  // Filter executions
  const activeExecutions = executions.filter(
    e => {
      const status = e.status.toUpperCase();
      return status === 'PENDING' || status === 'POLLING' || 
             status === 'INITIATED' || status === 'LAUNCHING' ||
             status === 'STARTED' || status === 'IN_PROGRESS' || 
             status === 'RUNNING' || status === 'PAUSED';
    }
  );
  
  const historyExecutions = executions.filter(
    e => {
      const status = e.status.toUpperCase();
      return status === 'COMPLETED' || status === 'PARTIAL' ||
             status === 'FAILED' || status === 'CANCELLED' || 
             status === 'ROLLED_BACK';
    }
  );

  const calculateProgress = (execution: ExecutionListItem): number => {
    if (execution.status !== 'in_progress' || !execution.currentWave) {
      return 0;
    }
    return (execution.currentWave / execution.totalWaves) * 100;
  };

  const calculateDuration = (execution: ExecutionListItem): string => {
    if (!execution.startTime) return '-';
    
    const start = new Date(execution.startTime);
    if (isNaN(start.getTime())) return '-';
    
    const end = execution.endTime ? new Date(execution.endTime) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    if (durationMs < 0) return '-';
    
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  };

  // Collection hooks for history table
  const { items, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    historyExecutions,
    {
      filtering: {
        empty: 'No execution history',
        noMatch: 'No executions match the filter',
      },
      pagination: { pageSize: 10 },
      sorting: {},
    }
  );

  if (loading && executions.length === 0) {
    return <LoadingState message="Loading executions..." />;
  }

  if (error && executions.length === 0) {
    return <ErrorState message={error} onRetry={fetchExecutions} />;
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
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Badge color="green">🔄 Live Updates</Badge>
                    <span style={{ fontSize: '12px', color: '#5f6b7a' }}>
                      Updated {formatDistanceToNow(lastRefresh, { addSuffix: true })}
                    </span>
                  </div>
                )}
                <Button
                  onClick={handleRefresh}
                  disabled={refreshing}
                  iconName="refresh"
                >
                  Refresh
                </Button>
              </SpaceBetween>
            }
          >
            Execution History
          </Header>
        }
      >
        <SpaceBetween size="l">
          {error && executions.length > 0 && (
            <Alert
              type="error"
              dismissible
              onDismiss={() => setError(null)}
            >
              {error}
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
                        <Container
                          key={execution.executionId}
                          header={
                            <Header variant="h2">
                              {execution.recoveryPlanName}
                            </Header>
                          }
                        >
                          <SpaceBetween size="m">
                            <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                              <StatusBadge status={execution.status} />
                              
                              {execution.currentWave && (
                                <span style={{ color: '#5f6b7a' }}>
                                  Wave {execution.currentWave} of {execution.totalWaves}
                                </span>
                              )}
                              
                              <DateTimeDisplay value={execution.startTime} format="full" />
                              
                              <span style={{ color: '#5f6b7a' }}>
                                Duration: {calculateDuration(execution)}
                              </span>
                            </div>

                            {execution.status === 'in_progress' && execution.currentWave && (
                              <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                  <span style={{ fontSize: '12px', color: '#5f6b7a' }}>Progress</span>
                                  <span style={{ fontSize: '12px', color: '#5f6b7a' }}>
                                    {Math.round(calculateProgress(execution))}%
                                  </span>
                                </div>
                                <ProgressBar
                                  value={calculateProgress(execution)}
                                  variant="standalone"
                                />
                              </div>
                            )}

                            <Button onClick={() => handleViewDetails(execution)}>
                              View Details
                            </Button>
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
                      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <Button
                          variant="normal"
                          onClick={handleClearHistory}
                          disabled={clearing}
                        >
                          🗑️ Clear Completed History
                        </Button>
                      </div>
                    )}
                    
                    <Table
                      {...collectionProps}
                      columnDefinitions={[
                        {
                          id: 'plan',
                          header: 'Plan Name',
                          cell: (item) => item.recoveryPlanName,
                          sortingField: 'recoveryPlanName',
                        },
                        {
                          id: 'status',
                          header: 'Status',
                          cell: (item) => <StatusBadge status={item.status} />,
                        },
                        {
                          id: 'waves',
                          header: 'Waves',
                          cell: (item) => {
                            const waves = item.totalWaves || 0;
                            return waves > 0 ? `${waves} waves` : '-';
                          },
                        },
                        {
                          id: 'started',
                          header: 'Started',
                          cell: (item) => <DateTimeDisplay value={item.startTime} format="full" />,
                        },
                        {
                          id: 'completed',
                          header: 'Completed',
                          cell: (item) => item.endTime ? <DateTimeDisplay value={item.endTime} format="full" /> : '-',
                        },
                        {
                          id: 'duration',
                          header: 'Duration',
                          cell: (item) => calculateDuration(item),
                        },
                        {
                          id: 'actions',
                          header: 'Actions',
                          cell: (item) => (
                            <Button
                              variant="inline-link"
                              iconName="external"
                              onClick={() => handleViewDetails(item)}
                            >
                              View
                            </Button>
                          ),
                        },
                      ]}
                      items={items}
                      loading={loading}
                      loadingText="Loading execution history"
                      empty={
                        <Box textAlign="center" color="inherit">
                          <b>No execution history</b>
                          <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                            Completed executions will appear here
                          </Box>
                        </Box>
                      }
                      filter={
                        <TextFilter
                          {...filterProps}
                          filteringPlaceholder="Find executions"
                          countText={`${filteredItemsCount} ${filteredItemsCount === 1 ? 'match' : 'matches'}`}
                        />
                      }
                      pagination={<Pagination {...paginationProps} />}
                      variant="full-page"
                    />
                  </SpaceBetween>
                ),
              },
            ]}
          />

          {/* Execution Details Modal */}
          <ExecutionDetails
            open={detailsOpen}
            executionId={selectedExecutionId}
            onClose={handleCloseDetails}
            onRefresh={fetchExecutions}
          />

          {/* Clear History Confirmation */}
          <Modal
            visible={clearDialogOpen}
            onDismiss={() => setClearDialogOpen(false)}
            header="Clear Completed History?"
            footer={
              <Box float="right">
                <SpaceBetween direction="horizontal" size="xs">
                  <Button onClick={() => setClearDialogOpen(false)} disabled={clearing}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    onClick={handleConfirmClear}
                    disabled={clearing}
                    loading={clearing}
                  >
                    Clear History
                  </Button>
                </SpaceBetween>
              </Box>
            }
          >
            <SpaceBetween size="m">
              <div>
                This will permanently delete all completed execution records ({historyExecutions.length} items).
                Active executions will not be affected.
              </div>
              <Alert type="warning">
                <strong>This action cannot be undone.</strong>
              </Alert>
            </SpaceBetween>
          </Modal>
        </SpaceBetween>
      </ContentLayout>
    </PageTransition>
  );
};
