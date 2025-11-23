/**
 * Protection Groups Page
 * 
 * Main page for managing DRS protection groups.
 * Displays list of groups with CRUD operations.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Button,
  Typography,
  Stack,
} from '@mui/material';
import type { GridColDef } from '@mui/x-data-grid';
import { GridActionsCellItem } from '@mui/x-data-grid';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import toast from 'react-hot-toast';
import { DataGridWrapper } from '../components/DataGridWrapper';
import { PageTransition } from '../components/PageTransition';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import { ProtectionGroupDialog } from '../components/ProtectionGroupDialog';
import apiClient from '../services/api';
import type { ProtectionGroup } from '../types';

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
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<ProtectionGroup | null>(null);

  // Fetch protection groups on mount
  useEffect(() => {
    fetchGroups();
  }, []);

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
    if (!groupToDelete) return;

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

  // DataGrid columns configuration
  const columns: GridColDef[] = useMemo(() => [
    {
      field: 'name',
      headerName: 'Name',
      width: 200,
      sortable: true,
    },
    {
      field: 'description',
      headerName: 'Description',
      flex: 1,
      sortable: true,
      renderCell: (params) => params.value || '-',
    },
    {
      field: 'region',
      headerName: 'Region',
      width: 150,
      sortable: true,
    },
    {
      field: 'sourceServerIds',
      headerName: 'Servers',
      width: 100,
      sortable: true,
      renderCell: (params) => {
        const serverIds = params.value as string[] || [];
        return <Typography variant="body2">{serverIds.length}</Typography>;
      },
    },
    {
      field: 'createdAt',
      headerName: 'Created',
      width: 180,
      sortable: true,
      renderCell: (params) => <DateTimeDisplay value={params.value} format="relative" />,
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 120,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => handleEdit(params.row as ProtectionGroup)}
          showInMenu={false}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon color="error" />}
          label="Delete"
          onClick={() => handleDelete(params.row as ProtectionGroup)}
          showInMenu={false}
        />,
      ],
    },
  ], []);

  // Transform data for DataGrid - use protectionGroupId as id
  const rows = useMemo(() => groups.map((group) => ({
    ...group,
    id: group.protectionGroupId,
  })), [groups]);

  return (
    <PageTransition in={!loading && !error}>
      <Box>
        {/* Header */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Protection Groups
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Define groups of servers to protect together based on tags
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          Create Group
        </Button>
      </Stack>

      {/* Protection Groups DataGrid */}
      <DataGridWrapper
        rows={rows}
        columns={columns}
        loading={loading}
        error={error}
        onRetry={fetchGroups}
        emptyMessage="No protection groups found. Click 'Create Group' above to get started."
        height={600}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Protection Group"
        message={
          groupToDelete
            ? `Are you sure you want to delete "${groupToDelete.name}"? This action cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        confirmColor="error"
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
      />

      {/* Create/Edit Dialog */}
      <ProtectionGroupDialog
        open={dialogOpen}
        group={editingGroup}
        onClose={handleDialogClose}
        onSave={handleDialogSave}
      />
      </Box>
    </PageTransition>
  );
};
