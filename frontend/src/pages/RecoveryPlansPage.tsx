/**
 * Recovery Plans Page
 * 
 * Main page for managing DRS recovery plans.
 * Displays list of plans with CRUD operations and wave configuration.
 */

import React, { useState, useEffect } from 'react';
import type { RecoveryPlan } from '../types';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  SpaceBetween,
  Button,
  Header,
  Table,
  ButtonDropdown,
  Badge,
  Pagination,
  TextFilter,
  CopyToClipboard,
} from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';
import toast from 'react-hot-toast';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import { StatusBadge } from '../components/StatusBadge';
import { RecoveryPlanDialog } from '../components/RecoveryPlanDialog';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../services/api';

/**
 * Recovery Plans Page Component
 * 
 * Manages the display and CRUD operations for recovery plans.
 */
export const RecoveryPlansPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [plans, setPlans] = useState<RecoveryPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [planToDelete, setPlanToDelete] = useState<RecoveryPlan | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<RecoveryPlan | null>(null);
  const [executing, setExecuting] = useState(false);
  const [plansWithInProgressExecution, setPlansWithInProgressExecution] = useState<Set<string>>(() => {
    const stored = sessionStorage.getItem('plansWithInProgressExecution');
    return stored ? new Set(JSON.parse(stored)) : new Set();
  });
  const [executionProgress, setExecutionProgress] = useState<Map<string, { currentWave: number; totalWaves: number }>>(new Map());

  // CloudScape collection hooks
  const { items, actions, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    plans,
    {
      filtering: {
        empty: 'No recovery plans found',
        noMatch: 'No recovery plans match the filter',
      },
      pagination: { pageSize: 10 },
      sorting: {},
    }
  );

  useEffect(() => {
    fetchPlans();
    checkInProgressExecutions();
    
    // Auto-refresh plans every 30 seconds, execution status every 5 seconds
    const plansInterval = setInterval(() => {
      fetchPlans();
    }, 30000);
    
    const executionInterval = setInterval(() => {
      checkInProgressExecutions();
    }, 5000);
    
    return () => {
      clearInterval(plansInterval);
      clearInterval(executionInterval);
    };
  }, []);
  
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        checkInProgressExecutions();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);
  
  useEffect(() => {
    sessionStorage.setItem('plansWithInProgressExecution', JSON.stringify([...plansWithInProgressExecution]));
  }, [plansWithInProgressExecution]);
  
  const checkInProgressExecutions = async () => {
    try {
      const response = await apiClient.listExecutions();
      // Include all active statuses
      const activeStatuses = ['IN_PROGRESS', 'PENDING', 'RUNNING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 'PAUSED'];
      const activeExecutions = response.items.filter((exec) => activeStatuses.includes(exec.status.toUpperCase()));
      const plansWithActiveExecution = new Set<string>(activeExecutions.map((exec) => exec.recoveryPlanId));
      setPlansWithInProgressExecution(plansWithActiveExecution);
      
      // Track wave progress for each plan
      const progressMap = new Map<string, { currentWave: number; totalWaves: number }>();
      activeExecutions.forEach((exec) => {
        progressMap.set(exec.recoveryPlanId, {
          currentWave: exec.currentWave || 1,
          totalWaves: exec.totalWaves || 1,
        });
      });
      setExecutionProgress(progressMap);
    } catch (err) {
      console.error('Failed to check in-progress executions:', err);
    }
  };

  const fetchPlans = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.listRecoveryPlans();
      setPlans(data);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load recovery plans';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (plan: RecoveryPlan) => {
    setPlanToDelete(plan);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!planToDelete || deleting) return;

    setDeleting(true);
    try {
      await apiClient.deleteRecoveryPlan(planToDelete.id);
      setPlans(plans.filter(p => p.id !== planToDelete.id));
      toast.success(`Recovery plan "${planToDelete.name}" deleted successfully`);
      setDeleteDialogOpen(false);
      setPlanToDelete(null);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete recovery plan';
      setError(errorMessage);
      toast.error(errorMessage);
      setDeleteDialogOpen(false);
    } finally {
      setDeleting(false);
    }
  };

  const cancelDelete = () => {
    setDeleteDialogOpen(false);
    setPlanToDelete(null);
  };

  const handleCreate = () => {
    setEditingPlan(null);
    setDialogOpen(true);
  };

  const handleEdit = (plan: RecoveryPlan) => {
    setEditingPlan(plan);
    setDialogOpen(true);
  };

  const handleDialogSave = (savedPlan: RecoveryPlan) => {
    const action = editingPlan ? 'updated' : 'created';
    toast.success(`Recovery plan "${savedPlan.name}" ${action} successfully`);
    fetchPlans();
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setEditingPlan(null);
  };

  const handleExecute = async (plan: RecoveryPlan, executionType: 'DRILL' | 'RECOVERY') => {
    if (executing) return;

    setExecuting(true);

    try {
      const execution = await apiClient.executeRecoveryPlan({
        recoveryPlanId: plan.id,
        executionType,
        dryRun: false,
        executedBy: user?.username || 'unknown'
      });
      
      toast.success(`${executionType === 'DRILL' ? 'Drill' : 'Recovery'} execution started`);
      
      const updatedSet = new Set(plansWithInProgressExecution);
      updatedSet.add(plan.id);
      setPlansWithInProgressExecution(updatedSet);
      
      setTimeout(() => checkInProgressExecutions(), 1000);
      
      navigate(`/executions/${execution.executionId}`);
    } catch (err: any) {
      // Handle DRS service limit errors with specific messages
      const errorCode = err.response?.data?.error || err.error;
      const errorData = err.response?.data || err;
      
      switch (errorCode) {
        case 'WAVE_SIZE_LIMIT_EXCEEDED':
          toast.error(`Wave size limit exceeded. Maximum ${errorData.limit || 100} servers per wave.`);
          break;
        case 'CONCURRENT_JOBS_LIMIT_EXCEEDED':
          toast.error(`DRS concurrent jobs limit reached (${errorData.currentJobs}/${errorData.maxJobs}). Wait for active jobs to complete.`);
          break;
        case 'SERVERS_IN_JOBS_LIMIT_EXCEEDED':
          toast.error(`Would exceed max servers in active jobs (${errorData.totalAfterNew}/${errorData.maxServers}).`);
          break;
        case 'UNHEALTHY_SERVER_REPLICATION': {
          const unhealthyCount = errorData.unhealthyCount || errorData.unhealthyServers?.length || 0;
          toast.error(`${unhealthyCount} server(s) have unhealthy replication state and cannot be recovered.`);
          break;
        }
        default:
          toast.error(err.message || errorData.message || 'Failed to execute recovery plan');
      }
    } finally {
      setExecuting(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading recovery plans..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchPlans} />;
  }

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            description="Define recovery strategies with wave-based orchestration"
            actions={
              <Button variant="primary" onClick={handleCreate}>
                Create Plan
              </Button>
            }
          >
            Recovery Plans
          </Header>
        }
      >
        <Table
          {...collectionProps}
          columnDefinitions={[
            {
              id: 'name',
              header: 'Plan Name',
              cell: (item) => (
                <span title={item.description || ''} style={{ fontWeight: 500 }}>
                  {item.name}
                </span>
              ),
              sortingField: 'name',
            },
            {
              id: 'planId',
              header: 'Plan ID',
              width: 340,
              cell: (item) => (
                <div style={{ display: 'flex', alignItems: 'center', whiteSpace: 'nowrap' }}>
                  <Box fontSize="body-s" color="text-body-secondary">
                    {item.id}
                  </Box>
                  <CopyToClipboard
                    copyButtonAriaLabel="Copy Plan ID"
                    copySuccessText="Plan ID copied"
                    copyErrorText="Failed to copy"
                    textToCopy={item.id}
                    variant="icon"
                  />
                </div>
              ),
            },
            {
              id: 'waves',
              header: 'Waves',
              width: 90,
              cell: (item) => {
                const progress = executionProgress.get(item.id);
                if (progress) {
                  return `${progress.currentWave} of ${progress.totalWaves}`;
                }
                return `${item.waves.length}`;
              },
            },
            {
              id: 'status',
              header: 'Status',
              minWidth: 120,
              cell: (item) => {
                if (!item.lastExecutionStatus) {
                  return <Badge>Not Run</Badge>;
                }
                return <StatusBadge status={item.lastExecutionStatus} />;
              },
            },
            {
              id: 'lastStart',
              header: 'Last Start',
              minWidth: 180,
              cell: (item) => {
                if (!item.lastStartTime) {
                  return <span style={{ color: '#5f6b7a' }}>Never</span>;
                }
                return <DateTimeDisplay value={item.lastStartTime * 1000} format="full" />;
              },
            },
            {
              id: 'lastEnd',
              header: 'Last End',
              minWidth: 180,
              cell: (item) => {
                if (!item.lastEndTime) {
                  return <span style={{ color: '#5f6b7a' }}>Never</span>;
                }
                return <DateTimeDisplay value={item.lastEndTime * 1000} format="full" />;
              },
            },
            {
              id: 'created',
              header: 'Created',
              minWidth: 180,
              cell: (item) => {
                if (!item.createdAt || (typeof item.createdAt === 'number' && item.createdAt === 0)) {
                  return <span style={{ color: '#5f6b7a' }}>Unknown</span>;
                }
                return <DateTimeDisplay value={item.createdAt} format="full" />;
              },
            },
            {
              id: 'actions',
              header: 'Actions',
              width: 150,
              cell: (item) => {
                const hasInProgressExecution = plansWithInProgressExecution.has(item.id);
                const hasServerConflict = item.hasServerConflict === true;
                const isExecutionDisabled = item.status === 'archived' || executing || hasInProgressExecution || hasServerConflict;
                
                // Build description for disabled state
                let drillDescription = 'Test recovery without failover';
                const recoveryDescription = 'Coming soon - actual failover operation';
                if (hasServerConflict && item.conflictInfo?.reason) {
                  drillDescription = `Blocked: ${item.conflictInfo.reason}`;
                }
                
                return (
                  <ButtonDropdown
                    items={[
                      { id: 'drill', text: 'Run Drill', iconName: 'check', description: drillDescription, disabled: isExecutionDisabled },
                      { id: 'recovery', text: 'Run Recovery', iconName: 'status-warning', description: recoveryDescription, disabled: true },
                      { id: 'divider', text: '-', disabled: true },
                      { id: 'edit', text: 'Edit', iconName: 'edit', disabled: hasInProgressExecution },
                      { id: 'delete', text: 'Delete', iconName: 'remove', disabled: hasInProgressExecution },
                    ]}
                    onItemClick={({ detail }) => {
                      if (detail.id === 'drill') {
                        handleExecute(item, 'DRILL');
                      } else if (detail.id === 'recovery') {
                        handleExecute(item, 'RECOVERY');
                      } else if (detail.id === 'edit') {
                        handleEdit(item);
                      } else if (detail.id === 'delete') {
                        handleDelete(item);
                      }
                    }}
                    expandToViewport
                    variant="icon"
                    ariaLabel="Actions"
                  />
                );
              },
            },
          ]}
          items={items}
          loading={loading}
          loadingText="Loading recovery plans"
          empty={
            <Box textAlign="center" color="inherit">
              <b>No recovery plans</b>
              <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                No recovery plans found. Click 'Create Plan' above to get started.
              </Box>
            </Box>
          }
          filter={
            <TextFilter
              {...filterProps}
              filteringPlaceholder="Find recovery plans"
              countText={`${filteredItemsCount} ${filteredItemsCount === 1 ? 'match' : 'matches'}`}
            />
          }
          pagination={<Pagination {...paginationProps} />}
          variant="full-page"
          stickyHeader
        />

        <ConfirmDialog
          visible={deleteDialogOpen}
          title="Delete Recovery Plan"
          message={
            planToDelete
              ? `Are you sure you want to delete "${planToDelete.name}"? This action cannot be undone.`
              : ''
          }
          confirmLabel="Delete"
          onConfirm={confirmDelete}
          onDismiss={cancelDelete}
          loading={deleting}
        />

        <RecoveryPlanDialog
          open={dialogOpen}
          plan={editingPlan}
          onClose={handleDialogClose}
          onSave={handleDialogSave}
        />
      </ContentLayout>
    </PageTransition>
  );
};
