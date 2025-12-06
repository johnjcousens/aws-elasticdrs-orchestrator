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
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<RecoveryPlan | null>(null);
  const [executing, setExecuting] = useState(false);
  const [plansWithInProgressExecution, setPlansWithInProgressExecution] = useState<Set<string>>(() => {
    const stored = sessionStorage.getItem('plansWithInProgressExecution');
    return stored ? new Set(JSON.parse(stored)) : new Set();
  });

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
    
    const interval = setInterval(() => {
      checkInProgressExecutions();
    }, 5000);
    
    return () => clearInterval(interval);
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
      const inProgressStatuses = ['IN_PROGRESS', 'PENDING'];
      const plansWithActiveExecution = new Set<string>(
        response.items
          .filter((exec) => inProgressStatuses.includes(exec.status))
          .map((exec) => exec.recoveryPlanId)
      );
      setPlansWithInProgressExecution(plansWithActiveExecution);
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
    if (!planToDelete) return;

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
      
      toast.success(`${executionType === 'DRILL' ? '🔵 DRILL' : '⚠️ RECOVERY'} execution started`);
      
      const updatedSet = new Set(plansWithInProgressExecution);
      updatedSet.add(plan.id);
      setPlansWithInProgressExecution(updatedSet);
      
      setTimeout(() => checkInProgressExecutions(), 1000);
      
      navigate(`/executions/${execution.executionId}`);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to execute recovery plan';
      toast.error(errorMessage);
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
                <div>
                  <div style={{ fontWeight: 500 }}>{item.name}</div>
                  {item.description && (
                    <div style={{ fontSize: '12px', color: '#5f6b7a' }}>{item.description}</div>
                  )}
                </div>
              ),
              sortingField: 'name',
            },
            {
              id: 'waves',
              header: 'Waves',
              cell: (item) => (
                <Badge color="blue">
                  {item.waves.length} wave{item.waves.length !== 1 ? 's' : ''}
                </Badge>
              ),
            },
            {
              id: 'status',
              header: 'Status',
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
              cell: (item) => {
                const hasInProgressExecution = plansWithInProgressExecution.has(item.id);
                const isDisabled = item.status === 'archived' || executing || hasInProgressExecution;
                
                return (
                  <SpaceBetween direction="horizontal" size="xs">
                    <ButtonDropdown
                      items={[
                        { id: 'drill', text: '🔵 Run Drill', description: 'Test recovery without failover' },
                        { id: 'recovery', text: '⚠️ Run Recovery', description: 'Actual failover operation' },
                      ]}
                      onItemClick={({ detail }) => {
                        if (detail.id === 'drill') {
                          handleExecute(item, 'DRILL');
                        } else if (detail.id === 'recovery') {
                          handleExecute(item, 'RECOVERY');
                        }
                      }}
                      disabled={isDisabled}
                    >
                      Execute
                    </ButtonDropdown>
                    <ButtonDropdown
                      items={[
                        { id: 'edit', text: 'Edit' },
                        { id: 'delete', text: 'Delete' },
                      ]}
                      onItemClick={({ detail }) => {
                        if (detail.id === 'edit') {
                          handleEdit(item);
                        } else if (detail.id === 'delete') {
                          handleDelete(item);
                        }
                      }}
                    >
                      Actions
                    </ButtonDropdown>
                  </SpaceBetween>
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
