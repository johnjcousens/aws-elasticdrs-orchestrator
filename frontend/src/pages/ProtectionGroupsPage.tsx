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
  SpaceBetween,
  Button,
  Header,
  Table,
  ButtonDropdown,
  Pagination,
  TextFilter,
} from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';
import toast from 'react-hot-toast';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import { ProtectionGroupDialog } from '../components/ProtectionGroupDialog';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import apiClient from '../services/api';

/**
 * Protection Groups Page Component
 * 
 * Manages the display and CRUD operations for protection groups.
 */
export const ProtectionGroupsPage: React.FC = () => {
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

  // Fetch protection groups and check which are in recovery plans/active executions
  useEffect(() => {
    fetchGroups();
    fetchRecoveryPlansForGroupCheck();
  }, []);

  const fetchRecoveryPlansForGroupCheck = async () => {
    try {
      const plans = await apiClient.listRecoveryPlans();
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
        if (plan.id) {
          planToGroups[plan.id] = groupIds;
        }
      });
      setGroupsInRecoveryPlans(usedGroupIds);
      
      // Check for active executions
      try {
        const executionsResponse = await apiClient.listExecutions();
        const executions = executionsResponse.items || [];
        const activeStatuses = ['PENDING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 'IN_PROGRESS', 'RUNNING', 'PAUSED', 'CANCELLING'];
        executions.forEach((exec: { status?: string; recoveryPlanId?: string }) => {
          const status = (exec.status || '').toUpperCase();
          if (activeStatuses.includes(status) && exec.recoveryPlanId) {
            // Add all protection groups from this plan to active set
            const groupIds = planToGroups[exec.recoveryPlanId] || [];
            groupIds.forEach(gid => activeGroupIds.add(gid));
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
      const data = await apiClient.listProtectionGroups();
      setGroups(data);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load protection groups';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

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
      toast.success(`Protection group "${groupToDelete.name}" deleted successfully`);
      setDeleteDialogOpen(false);
      setGroupToDelete(null);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to delete protection group';
      setError(errorMessage);
      toast.error(errorMessage);
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
    // Show success toast
    const action = editingGroup ? 'updated' : 'created';
    toast.success(`Protection group "${savedGroup.name}" ${action} successfully`);
    
    // Refresh the groups list after save
    fetchGroups();
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setEditingGroup(null);
  };

  // CloudScape collection hooks for table state management
  const { items, actions, filteredItemsCount, collectionProps, filterProps, paginationProps } = useCollection(
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
              <Button variant="primary" onClick={handleCreate}>
                Create Group
              </Button>
            }
          >
            Protection Groups
          </Header>
        }
      >
        <Table
          {...collectionProps}
          columnDefinitions={[
            {
              id: 'name',
              header: 'Name',
              cell: (item) => item.name,
              sortingField: 'name',
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
              id: 'servers',
              header: 'Servers',
              cell: (item) => (item.sourceServerIds || []).length,
              sortingField: 'sourceServerIds',
            },
            {
              id: 'createdAt',
              header: 'Created',
              cell: (item) => <DateTimeDisplay value={item.createdAt} format="relative" />,
              sortingField: 'createdAt',
            },
            {
              id: 'actions',
              header: 'Actions',
              width: 120,
              cell: (item) => {
                const isInRecoveryPlan = groupsInRecoveryPlans.has(item.protectionGroupId);
                const isInActiveExecution = groupsInActiveExecutions.has(item.protectionGroupId);
                return (
                  <ButtonDropdown
                    items={[
                      { id: 'edit', text: 'Edit', iconName: 'edit', disabled: isInActiveExecution, disabledReason: 'Cannot edit while execution is running' },
                      { id: 'delete', text: 'Delete', iconName: 'remove', disabled: isInRecoveryPlan, disabledReason: 'Remove from recovery plans first' },
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
              ? `Are you sure you want to delete "${groupToDelete.name}"? This action cannot be undone.`
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
      </ContentLayout>
    </PageTransition>
  );
};
