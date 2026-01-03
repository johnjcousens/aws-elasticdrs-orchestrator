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
  Modal,
  Alert,
} from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { useNotifications } from '../contexts/NotificationContext';
import { useAccount } from '../contexts/AccountContext';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { PageTransition } from '../components/PageTransition';
import { PermissionAwareButton, PermissionAwareButtonDropdown } from '../components/PermissionAware';
import { DRSPermission } from '../contexts/PermissionsContext';
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
  const { addNotification } = useNotifications();
  const { getCurrentAccountId } = useAccount();
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
  
  // Existing instances confirmation dialog state
  const [existingInstancesDialogOpen, setExistingInstancesDialogOpen] = useState(false);
  const [existingInstancesInfo, setExistingInstancesInfo] = useState<{
    plan: RecoveryPlan;
    executionType: 'DRILL' | 'RECOVERY';
    instances: Array<{
      sourceServerId: string;
      recoveryInstanceId: string;
      ec2InstanceId: string;
      ec2InstanceState: string;
      sourceExecutionId?: string;
      sourcePlanName?: string;
      name?: string;
      privateIp?: string;
      publicIp?: string;
      instanceType?: string;
      launchTime?: string;
    }>;
  } | null>(null);
  const [checkingInstances, setCheckingInstances] = useState(false);

  // CloudScape collection hooks
  const { items, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
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

  // Track dialog state with ref for interval callbacks
  const isAnyDialogOpenRef = React.useRef(false);
  isAnyDialogOpenRef.current = dialogOpen || deleteDialogOpen || existingInstancesDialogOpen;

  // Initial fetch on mount only
  useEffect(() => {
    fetchPlans();
    checkInProgressExecutions();
  }, []);

  // Auto-refresh intervals - created once, check ref for dialog state
  useEffect(() => {
    const plansInterval = setInterval(() => {
      if (!isAnyDialogOpenRef.current) {
        fetchPlans();
      }
    }, 30000);
    
    const executionInterval = setInterval(() => {
      if (!isAnyDialogOpenRef.current) {
        checkInProgressExecutions();
      }
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
      const accountId = getCurrentAccountId();
      const response = await apiClient.listExecutions(accountId ? { accountId } : undefined);
      const activeStatuses = ['IN_PROGRESS', 'PENDING', 'RUNNING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 'PAUSED', 'PAUSE_PENDING', 'CANCELLING'];
      const activeExecutions = response.items.filter((exec) => activeStatuses.includes(exec.status.toUpperCase()));
      const plansWithActiveExecution = new Set<string>(activeExecutions.map((exec) => exec.recoveryPlanId));
      setPlansWithInProgressExecution(plansWithActiveExecution);
      
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
      const accountId = getCurrentAccountId();
      const data = await apiClient.listRecoveryPlans(accountId ? { accountId } : undefined);
      setPlans(data);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load recovery plans';
      setError(errorMessage);
      addNotification('error', errorMessage);
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
      addNotification('success', `Recovery plan "${planToDelete.name}" deleted successfully`);
      setDeleteDialogOpen(false);
      setPlanToDelete(null);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete recovery plan';
      setError(errorMessage);
      addNotification('error', errorMessage);
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
    addNotification('success', `Recovery plan "${savedPlan.name}" ${action} successfully`);
    fetchPlans();
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setEditingPlan(null);
  };

  const handleExecute = async (plan: RecoveryPlan, executionType: 'DRILL' | 'RECOVERY') => {
    if (executing || checkingInstances) return;

    // For drills, check for existing recovery instances first
    if (executionType === 'DRILL') {
      setCheckingInstances(true);
      try {
        const result = await apiClient.checkExistingRecoveryInstances(plan.id);
        if (result.hasExistingInstances && result.existingInstances.length > 0) {
          setExistingInstancesInfo({
            plan,
            executionType,
            instances: result.existingInstances
          });
          setExistingInstancesDialogOpen(true);
          setCheckingInstances(false);
          return;
        }
      } catch (err) {
        console.warn('Failed to check existing instances:', err);
      } finally {
        setCheckingInstances(false);
      }
    }

    await executeRecoveryPlanInternal(plan, executionType);
  };

  const executeRecoveryPlanInternal = async (plan: RecoveryPlan, executionType: 'DRILL' | 'RECOVERY') => {
    setExecuting(true);

    try {
      const execution = await apiClient.executeRecoveryPlan({
        recoveryPlanId: plan.id,
        executionType,
        dryRun: false,
        executedBy: user?.username || 'unknown'
      });
      
      addNotification('success', `${executionType === 'DRILL' ? 'Drill' : 'Recovery'} execution started`);
      
      const updatedSet = new Set(plansWithInProgressExecution);
      updatedSet.add(plan.id);
      setPlansWithInProgressExecution(updatedSet);
      
      setTimeout(() => checkInProgressExecutions(), 1000);
      
      navigate(`/executions/${execution.executionId}`);
    } catch (err: unknown) {
      interface ErrorData {
        error?: string;
        limit?: number;
        currentJobs?: number;
        maxJobs?: number;
        totalAfterNew?: number;
        maxServers?: number;
        unhealthyCount?: number;
        unhealthyServers?: unknown[];
        message?: string;
      }
      const error = err as { response?: { data?: ErrorData }; error?: string; message?: string };
      const errorCode = error.response?.data?.error || error.error;
      const errorData: ErrorData = error.response?.data || {};
      
      switch (errorCode) {
        case 'WAVE_SIZE_LIMIT_EXCEEDED':
          addNotification('error', `Wave size limit exceeded. Maximum ${Number(errorData.limit) || 100} servers per wave.`);
          break;
        case 'CONCURRENT_JOBS_LIMIT_EXCEEDED':
          addNotification('error', `DRS concurrent jobs limit reached (${Number(errorData.currentJobs) || 0}/${Number(errorData.maxJobs) || 20}). Wait for active jobs to complete.`);
          break;
        case 'SERVERS_IN_JOBS_LIMIT_EXCEEDED':
          addNotification('error', `Would exceed max servers in active jobs (${Number(errorData.totalAfterNew) || 0}/${Number(errorData.maxServers) || 500}).`);
          break;
        case 'UNHEALTHY_SERVER_REPLICATION': {
          const unhealthyCount = Number(errorData.unhealthyCount) || Number(errorData.unhealthyServers?.length) || 0;
          addNotification('error', `${unhealthyCount} server(s) have unhealthy replication state and cannot be recovered.`);
          break;
        }
        case 'SERVER_CONFLICT': {
          // Server is already in use by another execution or DRS job
          const conflictData = errorData as {
            conflicts?: Array<{ serverId: string; conflictSource?: string; executionId?: string; jobId?: string }>;
            conflictingExecutions?: Array<{ executionId: string; planId: string; servers: string[] }>;
            conflictingDrsJobs?: Array<{ jobId: string; servers: string[] }>;
            message?: string;
          };
          
          // Build a user-friendly message
          let conflictMessage = '';
          
          if (conflictData.conflictingDrsJobs?.length && !conflictData.conflictingExecutions?.length) {
            // Only DRS job conflicts
            const jobCount = conflictData.conflictingDrsJobs.length;
            const serverCount = conflictData.conflictingDrsJobs.reduce((sum, j) => sum + j.servers.length, 0);
            conflictMessage = `Cannot start: ${serverCount} server(s) are being processed by ${jobCount} active DRS job(s). Wait for jobs to complete or terminate recovery instances first.`;
          } else if (conflictData.conflictingExecutions?.length && !conflictData.conflictingDrsJobs?.length) {
            // Only execution conflicts
            const execCount = conflictData.conflictingExecutions.length;
            const serverCount = conflictData.conflictingExecutions.reduce((sum, e) => sum + e.servers.length, 0);
            conflictMessage = `Cannot start: ${serverCount} server(s) are in ${execCount} active execution(s). Complete or cancel those executions first.`;
          } else if (conflictData.conflictingExecutions?.length && conflictData.conflictingDrsJobs?.length) {
            // Both types of conflicts
            conflictMessage = `Cannot start: Servers are in use by active executions and DRS jobs. Wait for them to complete first.`;
          } else {
            // Fallback to API message
            conflictMessage = conflictData.message || 'Cannot start: One or more servers are already in use by another drill or recovery operation.';
          }
          
          addNotification('error', conflictMessage);
          break;
        }
        default:
          addNotification('error', error.message || errorData.message || 'Failed to execute recovery plan');
      }
    } finally {
      setExecuting(false);
    }
  };

  const handleExistingInstancesConfirm = async () => {
    if (!existingInstancesInfo) return;
    
    setExistingInstancesDialogOpen(false);
    const { plan, executionType } = existingInstancesInfo;
    setExistingInstancesInfo(null);
    
    await executeRecoveryPlanInternal(plan, executionType);
  };

  const handleExistingInstancesCancel = () => {
    setExistingInstancesDialogOpen(false);
    setExistingInstancesInfo(null);
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
              <PermissionAwareButton 
                variant="primary" 
                onClick={handleCreate}
                requiredPermission={DRSPermission.CREATE_RECOVERY_PLANS}
                fallbackTooltip="Requires recovery plan creation permission"
              >
                Create Plan
              </PermissionAwareButton>
            }
          >
            Recovery Plans
          </Header>
        }
      >
        <AccountRequiredWrapper pageName="Recovery Plans">
          <Table
          {...collectionProps}
          columnDefinitions={[
            {
              id: 'actions',
              header: 'Actions',
              width: 70,
              cell: (item) => {
                const hasInProgressExecution = plansWithInProgressExecution.has(item.id);
                const hasServerConflict = item.hasServerConflict === true;
                const isExecutionDisabled = item.status === 'archived' || executing || hasInProgressExecution || hasServerConflict;
                
                let drillDescription = 'Test recovery without failover';
                const recoveryDescription = 'Coming soon - actual failover operation';
                if (hasServerConflict && item.conflictInfo?.reason) {
                  drillDescription = `Blocked: ${item.conflictInfo.reason}`;
                }
                
                return (
                  <PermissionAwareButtonDropdown
                    items={[
                      { 
                        id: 'drill', 
                        text: 'Run Drill', 
                        iconName: 'check', 
                        disabled: isExecutionDisabled,
                        requiredPermission: DRSPermission.START_RECOVERY
                      },
                      { 
                        id: 'recovery', 
                        text: 'Run Recovery', 
                        iconName: 'status-warning', 
                        disabled: true,
                        requiredPermission: DRSPermission.START_RECOVERY
                      },
                      { id: 'divider', text: '-', disabled: true },
                      { 
                        id: 'edit', 
                        text: 'Edit', 
                        iconName: 'edit', 
                        disabled: hasInProgressExecution,
                        requiredPermission: DRSPermission.MODIFY_RECOVERY_PLANS
                      },
                      { 
                        id: 'delete', 
                        text: 'Delete', 
                        iconName: 'remove', 
                        disabled: hasInProgressExecution,
                        requiredPermission: DRSPermission.DELETE_RECOVERY_PLANS
                      },
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
              header: 'ID',
              width: 60,
              cell: (item) => (
                <CopyToClipboard
                  copyButtonAriaLabel="Copy Plan ID"
                  copySuccessText="Plan ID copied"
                  copyErrorText="Failed to copy"
                  textToCopy={item.id}
                  variant="icon"
                />
              ),
            },
            {
              id: 'waves',
              header: 'Waves',
              width: 90,
              cell: (item) => {
                const progress = executionProgress.get(item.id);
                if (progress) {
                  const sanitizedCurrentWave = Number(progress.currentWave) || 0;
                  const sanitizedTotalWaves = Number(progress.totalWaves) || 0;
                  return `${sanitizedCurrentWave} of ${sanitizedTotalWaves}`;
                }
                return `${Number(item.waves.length) || 0}`;
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
          ]}
          items={items}
          loading={loading}
          loadingText="Loading recovery plans"
          empty={
            <Box textAlign="center" color="inherit">
              <b>No recovery plans</b>
              <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                No recovery plans found. Click &apos;Create Plan&apos; above to get started.
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

        <Modal
          visible={existingInstancesDialogOpen}
          onDismiss={handleExistingInstancesCancel}
          header="Existing Recovery Instances Found"
          size="medium"
          footer={
            <Box float="right">
              <SpaceBetween direction="horizontal" size="xs">
                <Button variant="link" onClick={handleExistingInstancesCancel}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={handleExistingInstancesConfirm}>
                  Continue with Drill
                </Button>
              </SpaceBetween>
            </Box>
          }
        >
          <SpaceBetween size="m">
            <Alert type="warning">
              There are {existingInstancesInfo?.instances.length || 0} recovery instance(s) from a previous execution that have not been terminated.
            </Alert>
            <Box>
              {existingInstancesInfo?.instances[0]?.sourcePlanName && (
                <Box variant="p">
                  These instances were created by: <strong>{existingInstancesInfo.instances[0].sourcePlanName}</strong>
                </Box>
              )}
              <Box variant="p" color="text-body-secondary">
                Starting a new drill will <strong>terminate these existing instances</strong> before launching new ones. If you want to keep them, cancel and terminate them manually first.
              </Box>
            </Box>
            <Box>
              <Box variant="awsui-key-label">Existing instances ({existingInstancesInfo?.instances.length || 0}):</Box>
              <SpaceBetween size="xs">
                {existingInstancesInfo?.instances.slice(0, 6).map((inst, idx) => (
                  <Box key={idx} padding={{ left: 's' }}>
                    <Box fontSize="body-s">
                      <strong>{inst.name || inst.ec2InstanceId || ''}</strong>
                      <Box variant="span" color="text-status-success" fontSize="body-s"> ({inst.ec2InstanceState || ''})</Box>
                    </Box>
                    <Box fontSize="body-s" color="text-body-secondary">
                      {inst.privateIp && <span>IP: {inst.privateIp} • </span>}
                      {inst.instanceType && <span>{inst.instanceType} • </span>}
                      {inst.launchTime && <span>Launched: {new Date(inst.launchTime).toLocaleString()}</span>}
                    </Box>
                  </Box>
                ))}
              </SpaceBetween>
              {(existingInstancesInfo?.instances.length || 0) > 6 && (
                <Box color="text-body-secondary" fontSize="body-s" padding={{ top: 'xs' }}>
                  ... and {(existingInstancesInfo?.instances.length || 0) - 6} more
                </Box>
              )}
            </Box>
          </SpaceBetween>
        </Modal>
        </AccountRequiredWrapper>
      </ContentLayout>
    </PageTransition>
  );
};
