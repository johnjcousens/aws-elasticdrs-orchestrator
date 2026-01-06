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
  DateInput,
  FormField,
  ButtonDropdown,
} from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { formatDistanceToNow, format, isWithinInterval, subDays, subHours, subMinutes, startOfDay, endOfDay, parse } from 'date-fns';
import { useNotifications } from '../contexts/NotificationContext';
import { useAccount } from '../contexts/AccountContext';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { CardSkeleton } from '../components/CardSkeleton';
import { PageTransition } from '../components/PageTransition';
import { PermissionAwareButton } from '../components/PermissionAware';
import { DRSPermission } from '../types/permissions';
import { StatusBadge } from '../components/StatusBadge';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import { InvocationSourceBadge } from '../components/InvocationSourceBadge';
import type { InvocationSource, InvocationDetails } from '../components/InvocationSourceBadge';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';

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
  const [selectedItems, setSelectedItems] = useState<ExecutionListItem[]>([]);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Helper function to set quick date ranges
  const setQuickDateRange = (minutes?: number, hours?: number, days?: number) => {
    const now = new Date();
    const end = format(now, 'MM-dd-yyyy');
    
    let start: Date;
    if (minutes) {
      start = subMinutes(now, minutes);
    } else if (hours) {
      start = subHours(now, hours);
    } else if (days) {
      start = subDays(now, days);
    } else {
      // Clear filter
      setStartDate('');
      setEndDate('');
      return;
    }
    
    setStartDate(format(start, 'MM-dd-yyyy'));
    setEndDate(end);
  };

  const clearDateFilter = () => {
    setStartDate('');
    setEndDate('');
  };

  useEffect(() => {
    fetchExecutions();
  }, []);

  useEffect(() => {
    const hasActiveExecutions = executions.some((e) => {
      const status = e.status?.toLowerCase() || '';
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
      // Defensive check: ensure items is an array
      setExecutions(Array.isArray(response?.items) ? response.items : []);
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
      if (selectedItems.length === 0) {
        addNotification('error', 'No executions selected for deletion');
        return;
      }

      // Debug: Log selected items and their statuses
      console.log('Selected items for deletion:', selectedItems.map(item => ({
        executionId: item.executionId,
        status: item.status,
        recoveryPlanName: item.recoveryPlanName
      })));

      // Delete selected executions by ID
      const executionIds = selectedItems.map(item => item.executionId);
      console.log('Calling deleteExecutions with IDs:', executionIds);
      
      const result = await apiClient.deleteExecutions(executionIds);
      console.log('Delete result:', result);
      
      // Show detailed results to user
      if (result.deletedCount > 0) {
        addNotification('success', `Deleted ${result.deletedCount} selected executions`);
      }
      
      if (result.activeSkipped > 0) {
        addNotification('warning', `Skipped ${result.activeSkipped} active executions (cannot delete while running)`);
      }
      
      if (result.notFound > 0) {
        addNotification('warning', `${result.notFound} executions not found`);
      }
      
      if (result.failed > 0) {
        addNotification('error', `Failed to delete ${result.failed} executions`);
      }
      
      // Show overall summary
      const totalProcessed = result.deletedCount + result.activeSkipped + result.notFound + result.failed;
      if (totalProcessed === 0) {
        addNotification('warning', 'No executions were processed');
      }
      
      setClearDialogOpen(false);
      setSelectedItems([]);
      await fetchExecutions();
    } catch (err: unknown) {
      console.error('Delete executions error:', err);
      const msg = err instanceof Error ? err.message : 'Failed to delete selected executions';
      addNotification('error', msg);
    } finally {
      setClearing(false);
    }
  };

  const activeExecutions = executions.filter((e) => {
    const status = e.status?.toUpperCase() || '';
    // Include standard active statuses
    if (['PENDING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 'IN_PROGRESS', 'PAUSED', 'RUNNING'].includes(status)) {
      return true;
    }
    // Also include CANCELLED/CANCELLING executions that still have active DRS jobs
    if (['CANCELLED', 'CANCELLING'].includes(status) && e.hasActiveDrsJobs) {
      return true;
    }
    return false;
  });

  const historyExecutions = executions.filter((e) => {
    const status = e.status?.toUpperCase() || '';
    const isTerminal = ['COMPLETED', 'PARTIAL', 'FAILED', 'CANCELLED', 'ROLLED_BACK', 'TIMEOUT'].includes(status);
    if (!isTerminal) return false;
    
    // Exclude CANCELLED executions that still have active DRS jobs (they show in Active)
    if (['CANCELLED', 'CANCELLING'].includes(status) && e.hasActiveDrsJobs) {
      return false;
    }
    
    // Apply date range filter
    if (startDate || endDate) {
      if (!e.startTime) return false;
      
      // Handle Unix timestamps (seconds) vs JavaScript timestamps (milliseconds)
      let startTimeMs: number = typeof e.startTime === 'number' ? e.startTime : parseInt(e.startTime as string);
      if (startTimeMs < 10000000000) {
        startTimeMs = startTimeMs * 1000; // Convert seconds to milliseconds
      }
      
      const executionDate = new Date(startTimeMs);
      if (isNaN(executionDate.getTime())) return false;
      
      // Check if execution date is within the selected range
      if (startDate && endDate) {
        const filterStartDate = startOfDay(parse(startDate, 'MM-dd-yyyy', new Date()));
        const filterEndDate = endOfDay(parse(endDate, 'MM-dd-yyyy', new Date()));
        
        if (!isWithinInterval(executionDate, { start: filterStartDate, end: filterEndDate })) {
          return false;
        }
      } else if (startDate) {
        const filterStartDate = startOfDay(parse(startDate, 'MM-dd-yyyy', new Date()));
        if (executionDate < filterStartDate) {
          return false;
        }
      } else if (endDate) {
        const filterEndDate = endOfDay(parse(endDate, 'MM-dd-yyyy', new Date()));
        if (executionDate > filterEndDate) {
          return false;
        }
      }
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
      selection: {},
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
                        <Container key={execution.executionId} header={<Header variant="h2">{execution.recoveryPlanName || ''}</Header>}>
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
                      <SpaceBetween direction="horizontal" size="xs">
                        <Button 
                          variant="normal" 
                          onClick={handleClearHistory} 
                          disabled={clearing || selectedItems.length === 0}
                        >
                          Clear History ({selectedItems.length})
                        </Button>
                      </SpaceBetween>
                    )}
                    
                    {/* Date Range Filter */}
                    <Container>
                      <SpaceBetween size="m">
                        <Header variant="h3">Filter by Date Range</Header>
                        
                        {/* Quick Filter Buttons */}
                        <SpaceBetween direction="horizontal" size="xs">
                          <ButtonDropdown
                            items={[
                              { id: 'last-hour', text: 'Last Hour' },
                              { id: 'last-6-hours', text: 'Last 6 Hours' },
                              { id: 'today', text: 'Today' },
                              { id: 'last-3-days', text: 'Last 3 Days' },
                              { id: 'last-week', text: 'Last Week' },
                              { id: 'last-month', text: 'Last Month' },
                            ]}
                            onItemClick={({ detail }) => {
                              switch (detail.id) {
                                case 'last-hour':
                                  setQuickDateRange(undefined, 1);
                                  break;
                                case 'last-6-hours':
                                  setQuickDateRange(undefined, 6);
                                  break;
                                case 'today':
                                  setQuickDateRange(undefined, undefined, 1);
                                  break;
                                case 'last-3-days':
                                  setQuickDateRange(undefined, undefined, 3);
                                  break;
                                case 'last-week':
                                  setQuickDateRange(undefined, undefined, 7);
                                  break;
                                case 'last-month':
                                  setQuickDateRange(undefined, undefined, 30);
                                  break;
                              }
                            }}
                          >
                            Quick Filters
                          </ButtonDropdown>
                          
                          {(startDate || endDate) && (
                            <Button 
                              variant="normal" 
                              onClick={clearDateFilter}
                              iconName="close"
                            >
                              Clear Filter
                            </Button>
                          )}
                        </SpaceBetween>
                        
                        {/* Custom Date Range */}
                        <SpaceBetween direction="horizontal" size="m">
                          <FormField label="From Date">
                            <DateInput
                              value={startDate}
                              onChange={({ detail }) => setStartDate(detail.value)}
                              placeholder="MM-DD-YYYY"
                            />
                          </FormField>
                          <FormField label="To Date">
                            <DateInput
                              value={endDate}
                              onChange={({ detail }) => setEndDate(detail.value)}
                              placeholder="MM-DD-YYYY"
                            />
                          </FormField>
                        </SpaceBetween>
                        
                        {(startDate || endDate) && (
                          <Box color="text-body-secondary" fontSize="body-s">
                            {startDate && endDate 
                              ? `Showing executions from ${startDate} to ${endDate}`
                              : startDate 
                                ? `Showing executions from ${startDate} onwards`
                                : `Showing executions up to ${endDate}`
                            }
                          </Box>
                        )}
                      </SpaceBetween>
                    </Container>
                    
                    <Table
                      {...collectionProps}
                      columnDefinitions={[
                        { id: 'actions', header: 'Actions', cell: (item) => <Button variant="inline-link" iconName="external" onClick={() => handleViewDetails(item)}>View</Button>, width: 70 },
                        { id: 'plan', header: 'Plan Name', cell: (item) => item.recoveryPlanName || '-', sortingField: 'recoveryPlanName', width: 180 },
                        { id: 'status', header: 'Status', cell: (item) => <StatusBadge status={item.status} />, width: 110 },
                        { 
                          id: 'source', 
                          header: 'Source', 
                          cell: (item) => (
                            <span style={{ whiteSpace: 'nowrap' }}>
                              <InvocationSourceBadge 
                                source={(item.invocationSource || 'UI') as InvocationSource} 
                                details={item.invocationDetails as InvocationDetails}
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
                      ]}
                      items={items}
                      loading={loading}
                      loadingText="Loading execution history"
                      selectedItems={selectedItems}
                      onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}
                      selectionType="multi"
                      empty={
                        <Box textAlign="center" color="inherit">
                          <b>No execution history</b>
                          <Box padding={{ bottom: 's' }} variant="p" color="inherit">Completed executions will appear here</Box>
                        </Box>
                      }
                      header={
                        <Header
                          counter={
                            selectedItems.length > 0 
                              ? `(${selectedItems.length}/${items.length} selected)` 
                              : (startDate || endDate)
                                ? `(${items.length} of ${historyExecutions.length} filtered)`
                                : `(${items.length})`
                          }
                          actions={
                            <SpaceBetween direction="horizontal" size="xs">
                              <Button 
                                variant="normal" 
                                onClick={handleClearHistory} 
                                disabled={clearing || selectedItems.length === 0}
                              >
                                Clear History ({selectedItems.length})
                              </Button>
                            </SpaceBetween>
                          }
                        >
                          Execution History
                        </Header>
                      }
                      filter={
                        <TextFilter {...filterProps} filteringPlaceholder="Search by plan name or status" countText={`${filteredItemsCount} ${filteredItemsCount === 1 ? 'match' : 'matches'}`} />
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
            header="Delete Selected Executions?"
            footer={
              <Box float="right">
                <SpaceBetween direction="horizontal" size="xs">
                  <Button onClick={() => setClearDialogOpen(false)} disabled={clearing}>Cancel</Button>
                  <PermissionAwareButton 
                    variant="primary" 
                    onClick={handleConfirmClear} 
                    disabled={clearing} 
                    loading={clearing}
                    requiredPermission={DRSPermission.STOP_RECOVERY}
                    fallbackTooltip="Requires recovery stop permission"
                  >
                    Delete Selected
                  </PermissionAwareButton>
                </SpaceBetween>
              </Box>
            }
          >
            <SpaceBetween size="m">
              <Box>This will permanently delete {selectedItems.length} selected execution record{selectedItems.length !== 1 ? 's' : ''}. Active executions will not be affected.</Box>
              <Alert type="warning">This action cannot be undone.</Alert>
            </SpaceBetween>
          </Modal>
        </SpaceBetween>
        </AccountRequiredWrapper>
      </ContentLayout>
    </PageTransition>
  );
};
