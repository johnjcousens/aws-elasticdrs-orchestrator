/**
 * Recovery Plans Page
 * 
 * Main page for managing DRS recovery plans.
 * Displays list of plans with CRUD operations and wave configuration.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  IconButton,
  Chip,
  Stack,
  Tooltip,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import toast from 'react-hot-toast';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
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
    // TODO: Navigate to execution confirmation or trigger execution
    console.log('Execute plan:', plan.id);
    // Could navigate to /executions or show execution dialog
  };

  if (loading) {
    return <LoadingState message="Loading recovery plans..." />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={fetchPlans} />;
  }

  return (
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

      {/* Recovery Plans Table */}
      {plans.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Recovery Plans
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Create your first recovery plan to orchestrate disaster recovery
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Create Recovery Plan
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Plan Name</TableCell>
                <TableCell>Protection Group</TableCell>
                <TableCell>Waves</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Execution</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {plans.map((plan) => (
                <TableRow key={plan.id} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {plan.name}
                    </Typography>
                    {plan.description && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {plan.description}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {plan.protectionGroupName || plan.protectionGroupId}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={`${plan.waves.length} wave${plan.waves.length !== 1 ? 's' : ''}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={plan.status || 'draft'} />
                  </TableCell>
                  <TableCell>
                    {plan.lastExecutedAt ? (
                      <Box>
                        <StatusBadge status={plan.lastExecutionStatus || 'pending'} size="small" />
                        <Typography variant="caption" color="text.secondary" display="block">
                          <DateTimeDisplay value={plan.lastExecutedAt} format="relative" />
                        </Typography>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Never executed
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <DateTimeDisplay value={plan.createdAt} format="relative" />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Execute Plan">
                      <IconButton
                        size="small"
                        onClick={() => handleExecute(plan)}
                        color="success"
                        disabled={plan.status === 'archived'}
                      >
                        <PlayArrowIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit Plan">
                      <IconButton
                        size="small"
                        onClick={() => handleEdit(plan)}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Plan">
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(plan)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

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
  );
};
