/**
 * Protection Groups Page
 * 
 * Main page for managing DRS protection groups.
 * Displays list of groups with CRUD operations.
 */

import React, { useState, useEffect } from 'react';
import type { ProtectionGroup } from '../types';
import {
  Box,
  Header,
  Table,
  Pagination,
  TextFilter,
} from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { useNotifications } from '../contexts/NotificationContext';
import { useAccount } from '../contexts/AccountContext';
import { PageTransition } from '../components/PageTransition';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import { ProtectionGroupDialog } from '../components/ProtectionGroupDialog';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { AccountRequiredWrapper } from '../components/AccountRequiredWrapper';
import { PermissionAwareButton, PermissionAwareButtonDropdown } from '../components/PermissionAware';
import { DRSPermission } from '../types/permissions';
import apiClient from '../services/api';

/**
 * Protection Groups Page Component
 * 
 * Manages the display and CRUD operations for protection groups.
 */
export const ProtectionGroupsPage: React.FC = () => {
  const { addNotification } = useNotifications();
  const { getCurrentAccountId, selectedAccount } = useAccount();
  const [groups, setGroups] = useState<ProtectionGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [groupToDelete, setGroupToDelete] = useState<ProtectionGroup | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<ProtectionGroup | null>(null);
  const [groupsInRecoveryPlans, setGroupsInRecoveryPlans] = useState<Set<string>>(new Set());
  const [groupsInActiveExecutions, setGroupsInActiveExecutions] = useState<Set<string>>(new Set());

  // Track dialog state with ref for interval callbacks
  const isAnyDialogOpenRef = React.useRef(false);
  isAnyDialogOpenRef.current = dialogOpen || deleteDialogOpen;

  const fetchRecoveryPlansForGroupCheck = async () => {
    try {
      const accountId = getCurrentAccountId();
      const plansResponse = await apiClient.listRecoveryPlans(accountId ? { accountId } : undefined);
      // Defensive check: ensure plans is an array
      const plans = Array.isArray(plansResponse) ? plansResponse : [];
      const usedGroupIds = new Set<string>();
      const activeGroupIds = new Set<string>();
      
      // Build map of plan ID to protection group IDs
      const planToGroups: Record<string, string[]> = {};
      plans.forEach((plan) => {
        const groupIds: string[] = [];
        plan.waves?.forEach((wave) => {
          if (wave.protectionGroupId) {
            usedGroupIds.add(wave.protectionGroupId);
            groupIds.push(wave.protectionGroupId);
          }
        });
        if (plan.planId) {
          planToGroups[plan.planId] = groupIds;
        }
      });
      setGroupsInRecoveryPlans(usedGroupIds);
      
      // Check for active executions
      try {
        const accountId = getCurrentAccountId();
        const executionsResponse = await apiClient.listExecutions(accountId ? { accountId } : undefined);
        // Defensive check: ensure items is an array
        const executions = Array.isArray(executionsResponse?.items) ? executionsResponse.items : [];
        const activeStatuses = ['PENDING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 'IN_PROGRESS', 'RUNNING', 'PAUSED', 'PAUSE_PENDING', 'CANCELLING'];
        executions.forEach((exec: { status?: string; planId?: string }) => {
          const status = String(exec.status || '').replace(/[^a-zA-Z0-9_]/g, '').toUpperCase();
          if (activeStatuses.includes(status) && exec.planId) {
            // Add all protection groups from this plan to active set
            const sanitizedPlanId = String(exec.planId).replace(/[^a-zA-Z0-9\-_]/g, '');
            const groupIds = planToGroups[sanitizedPlanId] || [];
            groupIds.forEach(gid => activeGroupIds.add(String(gid).replace(/[^a-zA-Z0-9\-_]/g, '')));
          }
        });
        
        // Also check for plans with server conflicts (DRS jobs)
        plans.forEach((plan: { hasServerConflict?: boolean; planId?: string }) => {
          if (plan.hasServerConflict && plan.planId) {
            const sanitizedPlanId = String(plan.planId).replace(/[^a-zA-Z0-9\-_]/g, '');
            const groupIds = planToGroups[sanitizedPlanId] || [];
            groupIds.forEach(gid => activeGroupIds.add(String(gid).replace(/[^a-zA-Z0-9\-_]/g, '')));
          }
        });
        
        setGroupsInActiveExecutions(activeGroupIds);
      } catch (err) {
        console.error('Failed to check active executions:', err);
      }
    } catch (err) {
      console.error('Failed to check recovery plans:', err);
    }
  };

  const fetchGroups = async () => {
    try {
      setLoading(true);
      setError(null);
      const accountId = getCurrentAccountId();
      const data = await apiClient.listProtectionGroups(accountId ? { accountId } : undefined);
      // Defensive check: ensure data is an array
      setGroups(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load protection groups';
      setError(errorMessage);
      addNotification('error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Fetch data when account changes or on mount
  useEffect(() => {
    const accountId = getCurrentAccountId();
    console.log('[ProtectionGroupsPage] Account changed to:', accountId);
    if (accountId) {
      console.log('[ProtectionGroupsPage] Fetching groups for account:', accountId);
      fetchGroups();
      fetchRecoveryPlansForGroupCheck();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAccount]);

  const handleDelete = (group: ProtectionGroup) => {
    setGroupToDelete(group);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!groupToDelete || deleting) return;

    setDeleting(true);
    try {
      await apiClient.deleteProtectionGroup(groupToDelete.protectionGroupId);
      setGroups(groups.filter(g => g.protectionGroupId !== groupToDelete.protectionGroupId));
      addNotification('success', `Protection group "${groupToDelete.groupName}" deleted successfully`);
      setDeleteDialogOpen(false);
      setGroupToDelete(null);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete protection group';
      setError(errorMessage);
      addNotification('error', errorMessage);
      setDeleteDialogOpen(false);
    } finally {
      setDeleting(false);
    }
  };

  const cancelDelete = () => {
    setDeleteDialogOpen(false);
    setGroupToDelete(null);
  };

  const handleCreate = () => {
    setEditingGroup(null);
    setDialogOpen(true);
  };

  const handleEdit = (group: ProtectionGroup) => {
    setEditingGroup(group);
    setDialogOpen(true);
  };

  const handleDialogSave = (savedGroup: ProtectionGroup) => {
    const action = editingGroup ? 'updated' : 'created';
    addNotification('success', `Protection group "${savedGroup.groupName}" ${action} successfully`);
    fetchGroups();
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setEditingGroup(null);
  };

  // CloudScape collection hooks for table state management
  const { items, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
    groups,
    {
      filtering: {
        empty: 'No protection groups found',
        noMatch: 'No protection groups match the filter',
      },
      pagination: { pageSize: 10 },
      sorting: {},
    }
  );

  if (loading) {
    return <LoadingState message="Loading protection groups..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchGroups} />;
  }

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            description="Define groups of servers to protect together"
            actions={
              <PermissionAwareButton 
                variant="primary" 
                onClick={handleCreate}
                requiredPermission={DRSPermission.CREATE_PROTECTION_GROUPS}
                fallbackTooltip="Requires protection group creation permission"
              >
                Create Group
              </PermissionAwareButton>
            }
          >
            Protection Groups
          </Header>
        }
      >
        <AccountRequiredWrapper pageName="Protection Groups">
          <Table
          {...collectionProps}
          columnDefinitions={[
            {
              id: 'actions',
              header: 'Actions',
              width: 70,
              cell: (item) => {
                const isInRecoveryPlan = groupsInRecoveryPlans.has(item.protectionGroupId);
                const isInActiveExecution = groupsInActiveExecutions.has(item.protectionGroupId);
                return (
                  <PermissionAwareButtonDropdown
                    items={[
                      { 
                        id: 'edit', 
                        text: 'Edit', 
                        iconName: 'edit', 
                        disabled: isInActiveExecution, 
                        disabledReason: 'Cannot edit while execution is running',
                        requiredPermission: DRSPermission.MODIFY_PROTECTION_GROUPS
                      },
                      { 
                        id: 'delete', 
                        text: 'Delete', 
                        iconName: 'remove', 
                        disabled: isInRecoveryPlan, 
                        disabledReason: 'Remove from recovery plans first',
                        requiredPermission: DRSPermission.DELETE_PROTECTION_GROUPS
                      },
                    ]}
                    onItemClick={({ detail }) => {
                      if (detail.id === 'edit') {
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
              id: 'groupName',
              header: 'Name',
              cell: (item) => item.groupName,
              sortingField: 'groupName',
            },
            {
              id: 'description',
              header: 'Description',
              cell: (item) => item.description || '-',
              sortingField: 'description',
            },
            {
              id: 'region',
              header: 'Region',
              cell: (item) => item.region,
              sortingField: 'region',
            },
            {
              id: 'tags',
              header: 'Selection Tags',
              cell: (item) => {
                const tags = item.serverSelectionTags || {};
                const tagCount = Object.keys(tags).length;
                return tagCount > 0 ? `${tagCount} tag${tagCount !== 1 ? 's' : ''}` : '-';
              },
            },
            {
              id: 'createdDate',
              header: 'Created',
              cell: (item) => <DateTimeDisplay value={item.createdDate} format="full" />,
              sortingField: 'createdDate',
            },
          ]}
          items={items}
          loading={loading}
          loadingText="Loading protection groups"
          empty={
            <Box textAlign="center" color="inherit">
              <b>No protection groups</b>
              <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                No protection groups found. Click 'Create Group' above to get started.
              </Box>
            </Box>
          }
          filter={
            <TextFilter
              {...filterProps}
              filteringPlaceholder="Find protection groups"
              countText={`${filteredItemsCount} ${filteredItemsCount === 1 ? 'match' : 'matches'}`}
            />
          }
          pagination={<Pagination {...paginationProps} />}
          variant="full-page"
          stickyHeader
        />

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          visible={deleteDialogOpen}
          title="Delete Protection Group"
          message={
            groupToDelete
              ? `Are you sure you want to delete "${groupToDelete.groupName}"? This action cannot be undone.`
              : ''
          }
          confirmLabel="Delete"
          onConfirm={confirmDelete}
          onDismiss={cancelDelete}
          loading={deleting}
        />

        {/* Create/Edit Dialog */}
        <ProtectionGroupDialog
          open={dialogOpen}
          group={editingGroup}
          onClose={handleDialogClose}
          onSave={handleDialogSave}
        />
        </AccountRequiredWrapper>
      </ContentLayout>
    </PageTransition>
  );
};
