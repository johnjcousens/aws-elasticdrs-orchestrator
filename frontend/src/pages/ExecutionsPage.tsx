/**
 * Executions Page
 * 
 * Main page for monitoring DRS recovery executions.
 * Provides real-time visibility into active and historical executions.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Tabs,
  Tab,
  Stack,
  Card,
  CardContent,
  CardActions,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip,
} from '@mui/material';
import type { GridColDef } from '@mui/x-data-grid';
import { GridActionsCellItem } from '@mui/x-data-grid';
import RefreshIcon from '@mui/icons-material/Refresh';
import VisibilityIcon from '@mui/icons-material/Visibility';
import toast from 'react-hot-toast';
import { DataGridWrapper } from '../components/DataGridWrapper';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { StatusBadge } from '../components/StatusBadge';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import { ExecutionDetails } from '../components/ExecutionDetails';
import apiClient from '../services/api';
import type { ExecutionListItem } from '../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
};

/**
 * Executions Page Component
 * 
 * Displays active and historical executions with real-time updates.
 */
export const ExecutionsPage: React.FC = () => {
  const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0); // 0 = Active, 1 = History
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Fetch executions on mount
  useEffect(() => {
    fetchExecutions();
  }, []);

  // Real-time polling for active executions
  useEffect(() => {
    const hasActiveExecutions = executions.some(
      e => e.status === 'in_progress' || e.status === 'pending'
    );

    if (!hasActiveExecutions) return;

    const interval = setInterval(() => {
      fetchExecutions();
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [executions]);

  const fetchExecutions = async () => {
    try {
      if (loading) {
        setError(null);
      }
      const response = await apiClient.listExecutions();
      setExecutions(response.items);
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load executions';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleViewDetails = (execution: ExecutionListItem) => {
    setSelectedExecutionId(execution.executionId);
    setDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsOpen(false);
    setSelectedExecutionId(null);
  };

  const handleRefresh = () => {
    setLoading(true);
    fetchExecutions();
  };

  // Filter executions by active/history
  const activeExecutions = executions.filter(
    e => e.status === 'in_progress' || e.status === 'pending' || e.status === 'paused'
  );
  
  const historyExecutions = executions.filter(
    e => e.status === 'completed' || e.status === 'failed' || 
         e.status === 'cancelled' || e.status === 'rolled_back'
  );

  // Calculate progress percentage for in-progress executions
  const calculateProgress = (execution: ExecutionListItem): number => {
    if (execution.status !== 'in_progress' || !execution.currentWave) {
      return 0;
    }
    return (execution.currentWave / execution.totalWaves) * 100;
  };

  // Calculate duration
  const calculateDuration = (execution: ExecutionListItem): string => {
    const start = new Date(execution.startTime);
    const end = execution.endTime ? new Date(execution.endTime) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  // DataGrid columns configuration for History tab
  const historyColumns: GridColDef[] = useMemo(() => [
    {
      field: 'recoveryPlanName',
      headerName: 'Plan Name',
      width: 200,
      sortable: true,
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 140,
      sortable: true,
      renderCell: (params) => <StatusBadge status={params.value} />,
    },
    {
      field: 'totalWaves',
      headerName: 'Waves',
      width: 100,
      sortable: true,
      renderCell: (params) => `${params.value} waves`,
    },
    {
      field: 'startTime',
      headerName: 'Started',
      width: 180,
      sortable: true,
      renderCell: (params) => <DateTimeDisplay value={params.value} format="relative" />,
    },
    {
      field: 'endTime',
      headerName: 'Completed',
      width: 180,
      sortable: true,
      renderCell: (params) => params.value ? <DateTimeDisplay value={params.value} format="relative" /> : '-',
    },
    {
      field: 'duration',
      headerName: 'Duration',
      width: 120,
      sortable: false,
      valueGetter: (params) => calculateDuration(params.row as ExecutionListItem),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 120,
      getActions: (params) => [
        <GridActionsCellItem
          icon={<VisibilityIcon />}
          label="View Details"
          onClick={() => handleViewDetails(params.row as ExecutionListItem)}
          showInMenu={false}
        />,
      ],
    },
  ], []);

  // Transform history data for DataGrid
  const historyRows = useMemo(() => historyExecutions.map((execution) => ({
    id: execution.executionId,
    ...execution,
  })), [historyExecutions]);

  // Get border color based on status
  const getBorderColor = (status: string): string => {
    switch (status) {
      case 'completed':
        return '#4caf50'; // green
      case 'in_progress':
      case 'pending':
      case 'paused':
        return '#ff9800'; // orange
      case 'failed':
        return '#f44336'; // red
      default:
        return '#9e9e9e'; // grey
    }
  };

  if (loading && executions.length === 0) {
    return <LoadingState message="Loading executions..." />;
  }

  if (error && executions.length === 0) {
    return <ErrorState error={error} onRetry={fetchExecutions} />;
  }

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Execution Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time monitoring of DRS recovery executions
          </Typography>
        </Box>
        <Tooltip title="Refresh">
          <IconButton onClick={handleRefresh} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Stack>

      {/* Error Alert */}
      {error && executions.length > 0 && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab 
            label={`Active (${activeExecutions.length})`} 
            sx={{ textTransform: 'none' }}
          />
          <Tab 
            label={`History (${historyExecutions.length})`}
            sx={{ textTransform: 'none' }}
          />
        </Tabs>
      </Paper>

      {/* Active Executions Tab */}
      <TabPanel value={tabValue} index={0}>
        {activeExecutions.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Active Executions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Start a recovery plan execution to monitor progress here
            </Typography>
          </Paper>
        ) : (
          <Stack spacing={2}>
            {activeExecutions.map((execution) => (
              <Card 
                key={execution.executionId}
                sx={{ 
                  borderLeft: 4,
                  borderColor: getBorderColor(execution.status),
                }}
              >
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" gutterBottom>
                        {execution.recoveryPlanName}
                      </Typography>
                      
                      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                        <StatusBadge status={execution.status} />
                        
                        {execution.currentWave && (
                          <Typography variant="body2" color="text.secondary">
                            Wave {execution.currentWave} of {execution.totalWaves}
                          </Typography>
                        )}
                        
                        <DateTimeDisplay value={execution.startTime} format="relative" />
                        
                        <Typography variant="body2" color="text.secondary">
                          Duration: {calculateDuration(execution)}
                        </Typography>
                      </Stack>

                      {execution.status === 'in_progress' && execution.currentWave && (
                        <Box sx={{ mb: 1 }}>
                          <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              Progress
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {Math.round(calculateProgress(execution))}%
                            </Typography>
                          </Stack>
                          <LinearProgress 
                            variant="determinate" 
                            value={calculateProgress(execution)}
                            sx={{ height: 8, borderRadius: 1 }}
                          />
                        </Box>
                      )}

                    </Box>
                  </Stack>
                </CardContent>
                
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<VisibilityIcon />}
                    onClick={() => handleViewDetails(execution)}
                  >
                    View Details
                  </Button>
                </CardActions>
              </Card>
            ))}
          </Stack>
        )}
      </TabPanel>

      {/* History Tab */}
      <TabPanel value={tabValue} index={1}>
        <DataGridWrapper
          rows={historyRows}
          columns={historyColumns}
          loading={loading && historyExecutions.length === 0}
          error={error && historyExecutions.length === 0 ? error : null}
          onRetry={fetchExecutions}
          emptyMessage="No execution history available. Completed executions will appear here."
          height={600}
        />
      </TabPanel>

      {/* Execution Details Modal */}
      <ExecutionDetails
        open={detailsOpen}
        executionId={selectedExecutionId}
        onClose={handleCloseDetails}
        onRefresh={fetchExecutions}
      />
    </Box>
  );
};
