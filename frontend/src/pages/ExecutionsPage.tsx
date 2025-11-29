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
  Chip,
} from '@mui/material';
import type { GridColDef } from '@mui/x-data-grid';
import { GridActionsCellItem } from '@mui/x-data-grid';
import RefreshIcon from '@mui/icons-material/Refresh';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import VisibilityIcon from '@mui/icons-material/Visibility';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';
import { DataGridWrapper } from '../components/DataGridWrapper';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { CardSkeleton } from '../components/CardSkeleton';
import { PageTransition } from '../components/PageTransition';
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
  const [lastRefresh, setLastRefresh] = useState(new Date());
  const [refreshing, setRefreshing] = useState(false);

  // Fetch executions on mount
  useEffect(() => {
    fetchExecutions();
  }, []);

  // Real-time polling for active executions (faster 3s polling)
  useEffect(() => {
    const hasActiveExecutions = executions.some(
      e => e.status === 'in_progress' || e.status === 'pending'
    );

    if (!hasActiveExecutions) return;

    const interval = setInterval(() => {
      fetchExecutions();
    }, 3000); // Poll every 3 seconds (faster updates)

    return () => clearInterval(interval);
  }, [executions]);

  const fetchExecutions = async () => {
    try {
      if (loading) {
        setError(null);
      }
      const response = await apiClient.listExecutions();
      setExecutions(response.items);
      setLastRefresh(new Date());
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load executions';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
      setRefreshing(false);
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
    setRefreshing(true);
    fetchExecutions();
  };

  // Filter executions by active/history
  // Active: All in-progress states (orchestration + DRS job states)
  const activeExecutions = executions.filter(
    e => {
      const status = e.status.toUpperCase();
      // Orchestration states
      return status === 'PENDING' || status === 'POLLING' || 
             status === 'INITIATED' ||  // FIXED: Added DRS state
             status === 'LAUNCHING' ||   // FIXED: Added DRS state
             // DRS job states
             status === 'STARTED' ||     // FIXED: Added DRS job state
             status === 'IN_PROGRESS' || 
             status === 'RUNNING' ||     // Added for completeness
             status === 'PAUSED';
    }
  );
  
  // History: Terminal states (completed, failed, etc.)
  const historyExecutions = executions.filter(
    e => {
      const status = e.status.toUpperCase();
      return status === 'COMPLETED' || 
             status === 'PARTIAL' ||     // FIXED: Added partial failure state
             status === 'FAILED' || 
             status === 'CANCELLED' || 
             status === 'ROLLED_BACK';
    }
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
    // Handle missing or invalid start time
    if (!execution.startTime) {
      return '-';
    }
    
    const start = new Date(execution.startTime);
    
    // Validate start time
    if (isNaN(start.getTime())) {
      return '-';
    }
    
    const end = execution.endTime ? new Date(execution.endTime) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    // Handle negative duration (invalid data)
    if (durationMs < 0) {
      return '-';
    }
    
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
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
      renderCell: (params) => {
        const waves = params.value || 0;
        return waves > 0 ? `${waves} waves` : '-';
      },
    },
    {
      field: 'startTime',
      headerName: 'Started',
      width: 180,
      sortable: true,
      renderCell: (params) => <DateTimeDisplay value={params.value} format="full" />,
    },
    {
      field: 'endTime',
      headerName: 'Completed',
      width: 180,
      sortable: true,
      renderCell: (params) => params.value ? <DateTimeDisplay value={params.value} format="full" /> : '-',
    },
    {
      field: 'duration',
      headerName: 'Duration',
      width: 120,
      sortable: false,
      valueGetter: (value, row: ExecutionListItem) => calculateDuration(row),
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
    <PageTransition in={!loading && !error}>
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
        <Stack direction="row" spacing={2} alignItems="center">
          {activeExecutions.length > 0 && (
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip
                icon={
                  <AutorenewIcon 
                    sx={{ 
                      animation: 'spin 2s linear infinite',
                      '@keyframes spin': {
                        '0%': { transform: 'rotate(0deg)' },
                        '100%': { transform: 'rotate(360deg)' },
                      },
                    }} 
                  />
                }
                label="Live Updates"
                size="small"
                color="success"
                variant="outlined"
              />
              <Typography variant="caption" color="text.secondary">
                Updated {formatDistanceToNow(lastRefresh, { addSuffix: true })}
              </Typography>
            </Stack>
          )}
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              <RefreshIcon className={refreshing ? 'rotating' : ''} />
            </IconButton>
          </Tooltip>
        </Stack>
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
        {loading ? (
          <CardSkeleton count={5} showProgress={true} />
        ) : error ? (
          <ErrorState error={error} onRetry={handleRefresh} />
        ) : activeExecutions.length === 0 ? (
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
                        
                        <DateTimeDisplay value={execution.startTime} format="full" />
                        
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
    </PageTransition>
  );
};
