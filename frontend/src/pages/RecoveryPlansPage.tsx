/**
 * Recovery Plans Page
 * 
 * Main page for managing DRS recovery plans.
 * Displays list of plans with CRUD operations and wave configuration.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Typography,
  Chip,
  Stack,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
} from '@mui/material';
import type { GridColDef } from '@mui/x-data-grid';
import { GridActionsCellItem } from '@mui/x-data-grid';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import WarningIcon from '@mui/icons-material/Warning';
import ScienceIcon from '@mui/icons-material/Science';
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
  const navigate = useNavigate();
  const [plans, setPlans] = useState<RecoveryPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [planToDelete, setPlanToDelete] = useState<RecoveryPlan | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<RecoveryPlan | null>(null);
  const [executing, setExecuting] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedPlanForExecution, setSelectedPlanForExecution] = useState<RecoveryPlan | null>(null);
  const [plansWithInProgressExecution, setPlansWithInProgressExecution] = useState<Set<string>>(() => {
    // Initialize from sessionStorage to persist across navigation
    const stored = sessionStorage.getItem('plansWithInProgressExecution');
    return stored ? new Set(JSON.parse(stored)) : new Set();
  });

  // Fetch recovery plans on mount
  useEffect(() => {
    fetchPlans();
    checkInProgressExecutions();
    
    // Poll for in-progress executions every 5 seconds (faster polling)
    const interval = setInterval(() => {
      checkInProgressExecutions();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  // Re-check when page becomes visible (user navigates back)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        checkInProgressExecutions();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);
  
  // Persist to sessionStorage when state changes
  useEffect(() => {
    sessionStorage.setItem('plansWithInProgressExecution', JSON.stringify([...plansWithInProgressExecution]));
  }, [plansWithInProgressExecution]);
  
  // Check for in-progress executions
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

  // Handle execution menu
  const handleExecuteMenuClick = (event: React.MouseEvent<HTMLElement>, plan: RecoveryPlan) => {
    setAnchorEl(event.currentTarget);
    setSelectedPlanForExecution(plan);
  };

  const handleExecuteMenuClose = () => {
    setAnchorEl(null);
    setSelectedPlanForExecution(null);
  };

  // Direct execution handlers
  const handleExecuteDrill = async () => {
    console.log('🔵 handleExecuteDrill called', {
      selectedPlan: selectedPlanForExecution?.id,
      executing,
      hasSelection: !!selectedPlanForExecution
    });
    
    if (!selectedPlanForExecution) {
      console.error('❌ No plan selected for execution');
      toast.error('No plan selected');
      return;
    }
    
    if (executing) {
      console.warn('⚠️ Already executing, skipping');
      return;
    }

    handleExecuteMenuClose();
    setExecuting(true);

    try {
      console.log('🚀 Starting DRILL execution for plan:', selectedPlanForExecution.id);
      
      const execution = await apiClient.executeRecoveryPlan({
        recoveryPlanId: selectedPlanForExecution.id,
        executionType: 'DRILL',
        dryRun: false,
        executedBy: 'demo-user' // TODO: Get from auth context
      });
      
      console.log('✅ Execution created:', execution);
      toast.success('🔵 DRILL execution started');
      
      // Mark this plan as having an in-progress execution immediately
      const updatedSet = new Set(plansWithInProgressExecution);
      updatedSet.add(selectedPlanForExecution.id);
      setPlansWithInProgressExecution(updatedSet);
      
      // Refresh in-progress executions after a short delay
      setTimeout(() => checkInProgressExecutions(), 1000);
      
      navigate(`/executions/${execution.executionId}`);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to execute recovery plan';
      console.error('❌ Execution error:', err);
      toast.error(errorMessage);
    } finally {
      setExecuting(false);
    }
  };

  const handleExecuteRecovery = async () => {
    console.log('⚠️ handleExecuteRecovery called', {
      selectedPlan: selectedPlanForExecution?.id,
      executing,
      hasSelection: !!selectedPlanForExecution
    });
    
    if (!selectedPlanForExecution) {
      console.error('❌ No plan selected for execution');
      toast.error('No plan selected');
      return;
    }
    
    if (executing) {
      console.warn('⚠️ Already executing, skipping');
      return;
    }

    handleExecuteMenuClose();
    setExecuting(true);

    try {
      console.log('🚀 Starting RECOVERY execution for plan:', selectedPlanForExecution.id);
      
      const execution = await apiClient.executeRecoveryPlan({
        recoveryPlanId: selectedPlanForExecution.id,
        executionType: 'RECOVERY',
        dryRun: false,
        executedBy: 'demo-user' // TODO: Get from auth context
      });
      
      console.log('✅ Execution created:', execution);
      toast.success('⚠️ RECOVERY execution started');
      
      // Mark this plan as having an in-progress execution immediately
      const updatedSet = new Set(plansWithInProgressExecution);
      updatedSet.add(selectedPlanForExecution.id);
      setPlansWithInProgressExecution(updatedSet);
      
      // Refresh in-progress executions after a short delay
      setTimeout(() => checkInProgressExecutions(), 1000);
      
      navigate(`/executions/${execution.executionId}`);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to execute recovery plan';
      console.error('❌ Execution error:', err);
      toast.error(errorMessage);
    } finally {
      setExecuting(false);
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
      field: 'lastExecutionStatus',
      headerName: 'Status',
      width: 130,
      sortable: true,
      renderCell: (params) => {
        if (!params.value) {
          return (
            <Chip label="Not Run" size="small" variant="outlined" />
          );
        }
        return <StatusBadge status={params.value} />;
      },
    },
    {
      field: 'lastStartTime',
      headerName: 'Last Start',
      width: 180,
      sortable: true,
      renderCell: (params) => {
        if (!params.value) {
          return (
            <Typography variant="body2" color="text.secondary">
              Never
            </Typography>
          );
        }
        // lastStartTime comes as Unix timestamp in seconds, convert to milliseconds
        return <DateTimeDisplay value={params.value * 1000} format="full" />;
      },
    },
    {
      field: 'lastEndTime',
      headerName: 'Last End',
      width: 180,
      sortable: true,
      renderCell: (params) => {
        if (!params.value) {
          return (
            <Typography variant="body2" color="text.secondary">
              Never
            </Typography>
          );
        }
        // lastEndTime comes as Unix timestamp in seconds, convert to milliseconds
        return <DateTimeDisplay value={params.value * 1000} format="full" />;
      },
    },
    {
      field: 'createdAt',
      headerName: 'Created',
      width: 150,
      sortable: true,
      renderCell: (params) => {
        // Defensive: Check for null, undefined, 0, or invalid timestamps
        if (!params.value || params.value === 0) {
          return (
            <Typography variant="body2" color="text.secondary">
              Unknown
            </Typography>
          );
        }
        return <DateTimeDisplay value={params.value} format="full" />;
      },
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 140,
      getActions: (params) => {
        const plan = params.row as RecoveryPlan;
        const hasInProgressExecution = plansWithInProgressExecution.has(plan.id);
        const isDisabled = plan.status === 'archived' || executing || hasInProgressExecution;
        
        const executeButton = (
          <GridActionsCellItem
            icon={<PlayArrowIcon />}
            label="Execute"
            onClick={(event) => handleExecuteMenuClick(event, plan)}
            disabled={isDisabled}
            showInMenu={false}
          />
        );
        
        // Wrap with tooltip if disabled due to in-progress execution
        const executeAction = hasInProgressExecution ? (
          <Tooltip title="Execution already in progress for this plan" arrow>
            <span>{executeButton}</span>
          </Tooltip>
        ) : executeButton;
        
        return [
          executeAction,
          <GridActionsCellItem
            icon={<EditIcon />}
            label="Edit"
            onClick={() => handleEdit(plan)}
            showInMenu={false}
          />,
          <GridActionsCellItem
            icon={<DeleteIcon />}
            label="Delete"
            onClick={() => handleDelete(plan)}
            showInMenu={false}
          />,
        ];
      },
    },
  ], [executing, plansWithInProgressExecution]);

  // Transform data for DataGrid (requires 'id' field) - plans already have id
  const rows = useMemo(() => plans, [plans]);

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

        {/* Execution Type Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleExecuteMenuClose}
        >
          <MenuItem 
            onClick={handleExecuteDrill} 
            disabled={executing || (selectedPlanForExecution ? plansWithInProgressExecution.has(selectedPlanForExecution.id) : false)}
          >
            <ListItemIcon>
              <ScienceIcon fontSize="small" color="primary" />
            </ListItemIcon>
            <ListItemText
              primary="Run Drill"
              secondary="Test recovery without failover"
            />
          </MenuItem>
          <MenuItem 
            onClick={handleExecuteRecovery} 
            disabled={executing || (selectedPlanForExecution ? plansWithInProgressExecution.has(selectedPlanForExecution.id) : false)}
          >
            <ListItemIcon>
              <WarningIcon fontSize="small" color="warning" />
            </ListItemIcon>
            <ListItemText
              primary="Run Recovery"
              secondary="Actual failover operation"
            />
          </MenuItem>
        </Menu>

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
