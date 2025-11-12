/**
 * Recovery Plans Page
 * 
 * Main page for managing DRS recovery plans.
 * Displays list of plans with CRUD operations and wave configuration.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Chip,
  Stack,
} from '@mui/material';
import type { GridColDef } from '@mui/x-data-grid';
import { GridActionsCellItem } from '@mui/x-data-grid';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import toast from 'react-hot-toast';
import { DataGridWrapper } from '../components/DataGridWrapper';
import { PageTransition } from '../components/PageTransition';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import { StatusBadge } from '../components/StatusBadge';
import { RecoveryPlanDialog } from '../components/RecoveryPlanDialog';
import apiClient from '../services/api';
import type { RecoveryPlan } from '../types';

/**
 * Recovery Plans Page Component
 * 
 * Manages the display and CRUD operations for recovery plans.
 */
export const RecoveryPlansPage: React.FC = () => {
  const [plans, setPlans] = useState<RecoveryPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [planToDelete, setPlanToDelete] = useState<RecoveryPlan | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<RecoveryPlan | null>(null);

  // Fetch recovery plans on mount
  useEffect(() => {
    fetchPlans();
  }, []);

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
    // Show success toast
    const action = editingPlan ? 'updated' : 'created';
    toast.success(`Recovery plan "${savedPlan.name}" ${action} successfully`);
    
    // Refresh the plans list after save
    fetchPlans();
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
    setEditingPlan(null);
  };

  const handleExecute = async (plan: RecoveryPlan) => {
    try {
      // Execute recovery plan in DRILL mode
      const execution = await apiClient.executeRecoveryPlan({
        recoveryPlanId: plan.id,
        dryRun: false,
        executedBy: 'demo-user' // TODO: Get from auth context
      });
      
      toast.success(`Execution started: ${execution.executionId}`);
      
      // Navigate to execution details page
      // TODO: Add navigation to /executions/{executionId}
      console.log('Execution started:', execution.executionId);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to execute recovery plan';
      toast.error(errorMessage);
      console.error('Execution error:', err);
    }
  };

  // DataGrid columns configuration
  const columns: GridColDef<RecoveryPlan>[] = useMemo(() => [
    {
      field: 'name',
      headerName: 'Plan Name',
      width: 200,
      sortable: true,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {params.value}
          </Typography>
          {params.row.description && (
            <Typography variant="caption" color="text.secondary" display="block">
              {params.row.description}
            </Typography>
          )}
        </Box>
      ),
    },
    {
      field: 'waves',
      headerName: 'Waves',
      width: 100,
      sortable: true,
      renderCell: (params) => (
        <Chip
          label={`${params.value.length} wave${params.value.length !== 1 ? 's' : ''}`}
          size="small"
          color="primary"
          variant="outlined"
        />
      ),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      sortable: true,
      renderCell: (params) => <StatusBadge status={params.value || 'draft'} />,
    },
    {
      field: 'lastExecutedAt',
      headerName: 'Last Execution',
      width: 180,
      sortable: true,
      renderCell: (params) => {
        if (!params.value) {
          return (
            <Typography variant="body2" color="text.secondary">
              Never executed
            </Typography>
          );
        }
        return (
          <Box>
            <StatusBadge status={params.row.lastExecutionStatus || 'pending'} size="small" />
            <Typography variant="caption" color="text.secondary" display="block">
              <DateTimeDisplay value={params.value} format="relative" />
            </Typography>
          </Box>
        );
      },
    },
    {
      field: 'createdAt',
      headerName: 'Created',
      width: 150,
      sortable: true,
      renderCell: (params) => <DateTimeDisplay value={params.value} format="relative" />,
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 140,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<PlayArrowIcon />}
          label="Execute"
          onClick={() => handleExecute(params.row as RecoveryPlan)}
          disabled={params.row.status === 'archived'}
          showInMenu={false}
          sx={{ color: 'success.main' }}
        />,
        <GridActionsCellItem
          icon={<EditIcon />}
          label="Edit"
          onClick={() => handleEdit(params.row as RecoveryPlan)}
          showInMenu={false}
        />,
        <GridActionsCellItem
          icon={<DeleteIcon />}
          label="Delete"
          onClick={() => handleDelete(params.row as RecoveryPlan)}
          showInMenu={false}
          sx={{ color: 'error.main' }}
        />,
      ],
    },
  ], []);

  // Transform data for DataGrid (requires 'id' field)
  const rows = useMemo(() => plans.map((plan) => ({
    id: plan.id,
    ...plan,
  })), [plans]);

  return (
    <PageTransition in={!loading && !error}>
      <Box>
        {/* Header */}
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Recovery Plans
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Define recovery strategies with wave-based orchestration
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreate}
        >
          Create Plan
        </Button>
      </Stack>

      {/* Recovery Plans DataGrid */}
      <DataGridWrapper
        rows={rows}
        columns={columns}
        loading={loading}
        error={error}
        onRetry={fetchPlans}
        emptyMessage="No recovery plans found. Click 'Create Plan' above to get started."
        height={600}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Recovery Plan"
        message={
          planToDelete
            ? `Are you sure you want to delete "${planToDelete.name}"? This action cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        confirmColor="error"
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
      />

      {/* Create/Edit Dialog */}
      <RecoveryPlanDialog
        open={dialogOpen}
        plan={editingPlan}
        onClose={handleDialogClose}
        onSave={handleDialogSave}
      />
      </Box>
    </PageTransition>
  );
};
