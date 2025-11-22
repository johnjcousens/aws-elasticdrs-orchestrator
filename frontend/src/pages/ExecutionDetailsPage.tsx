import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Typography,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Link,
  LinearProgress,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import apiClient from '../services/api';
import { PageTransition } from '../components/PageTransition';

// Backend response types (PascalCase from Lambda)
interface BackendServerExecution {
  SourceServerId: string;
  RecoveryJobId?: string;
  InstanceId?: string | null;
  Status: 'LAUNCHING' | 'LAUNCHED' | 'FAILED';
  LaunchTime: number;
  Error?: string;
}

interface BackendWaveExecution {
  WaveName: string;
  ProtectionGroupId: string;
  Region: string;
  Status: string;
  Servers: BackendServerExecution[];
  StartTime: number;
  EndTime?: number;
}

interface BackendExecutionDetails {
  ExecutionId: string;
  PlanId: string;
  ExecutionType: 'DRILL' | 'RECOVERY' | 'FAILBACK';
  Status: 'IN_PROGRESS' | 'COMPLETED' | 'PARTIAL' | 'FAILED';
  StartTime: number;
  EndTime?: number;
  InitiatedBy: string;
  Waves: BackendWaveExecution[];
  RecoveryPlanName?: string;
}

export const ExecutionDetailsPage: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  
  const [execution, setExecution] = useState<BackendExecutionDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pollingEnabled, setPollingEnabled] = useState(true);

  // Fetch execution details
  const fetchExecution = async () => {
    if (!executionId) return;
    
    try {
      const data = await apiClient.getExecution(executionId);
      // Cast to our backend type (backend returns PascalCase)
      setExecution(data as unknown as BackendExecutionDetails);
      setError(null);
      
      // Disable polling if execution is complete
      const typedData = data as unknown as BackendExecutionDetails;
      if (typedData.Status !== 'IN_PROGRESS') {
        setPollingEnabled(false);
      }
    } catch (err: any) {
      console.error('Failed to fetch execution:', err);
      setError(err.message || 'Failed to load execution details');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchExecution();
  }, [executionId]);

  // Polling effect - refresh every 15 seconds while IN_PROGRESS
  useEffect(() => {
    if (!pollingEnabled || execution?.Status !== 'IN_PROGRESS') {
      return;
    }

    const interval = setInterval(() => {
      fetchExecution();
    }, 15000); // 15 seconds

    return () => clearInterval(interval);
  }, [pollingEnabled, execution?.Status]);

  // Helper: Get status color
  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'info' => {
    switch (status) {
      case 'COMPLETED':
      case 'LAUNCHED':
        return 'success';
      case 'FAILED':
        return 'error';
      case 'IN_PROGRESS':
      case 'LAUNCHING':
        return 'warning';
      case 'PARTIAL':
        return 'info';
      default:
        return 'info';
    }
  };

  // Helper: Get status icon
  const getStatusIcon = (status: string): React.ReactElement | undefined => {
    switch (status) {
      case 'COMPLETED':
      case 'LAUNCHED':
        return <CheckCircleIcon fontSize="small" />;
      case 'FAILED':
        return <ErrorIcon fontSize="small" />;
      case 'IN_PROGRESS':
      case 'LAUNCHING':
        return <ScheduleIcon fontSize="small" />;
      default:
        return undefined;
    }
  };

  // Helper: Format timestamp
  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  // Helper: Calculate duration
  const calculateDuration = (startTime: number, endTime?: number): string => {
    const end = endTime || Math.floor(Date.now() / 1000);
    const durationSec = end - startTime;
    const minutes = Math.floor(durationSec / 60);
    const seconds = durationSec % 60;
    return `${minutes}m ${seconds}s`;
  };

  // Helper: Calculate wave progress
  const calculateProgress = (waves: BackendWaveExecution[]): number => {
    if (!waves || waves.length === 0) return 0;
    const completedWaves = waves.filter(w => w.Status === 'COMPLETED').length;
    return (completedWaves / waves.length) * 100;
  };

  // Helper: Generate AWS console link
  const getConsoleLink = (instanceId: string, region: string): string => {
    return `https://console.aws.amazon.com/ec2/v2/home?region=${region}#Instances:instanceId=${instanceId}`;
  };

  if (loading) {
    return (
      <PageTransition>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </PageTransition>
    );
  }

  if (error) {
    return (
      <PageTransition>
        <Box>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/recovery-plans')}
            sx={{ mb: 2 }}
          >
            Back to Recovery Plans
          </Button>
          <Alert severity="error" action={
            <Button color="inherit" size="small" onClick={fetchExecution}>
              Retry
            </Button>
          }>
            {error}
          </Alert>
        </Box>
      </PageTransition>
    );
  }

  if (!execution) {
    return (
      <PageTransition>
        <Alert severity="warning">Execution not found</Alert>
      </PageTransition>
    );
  }

  const progress = calculateProgress(execution.Waves);
  const completedWaves = execution.Waves.filter(w => w.Status === 'COMPLETED').length;

  return (
    <PageTransition>
      <Box>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/recovery-plans')}
          >
            Back to Recovery Plans
          </Button>
          <Button
            startIcon={<RefreshIcon />}
            onClick={fetchExecution}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        {/* Execution Overview */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              {execution.RecoveryPlanName || 'Recovery Plan'} - {execution.ExecutionType} Execution
            </Typography>
            
            <Box display="flex" gap={2} alignItems="center" mb={2}>
              <Chip
                icon={getStatusIcon(execution.Status)}
                label={execution.Status}
                color={getStatusColor(execution.Status)}
                size="medium"
              />
              {execution.Status === 'IN_PROGRESS' && (
                <Typography variant="body2" color="text.secondary">
                  Auto-refreshing every 15 seconds...
                </Typography>
              )}
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>Execution ID:</strong> {execution.ExecutionId}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>Started:</strong> {formatTimestamp(execution.StartTime)} by {execution.InitiatedBy}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>Duration:</strong> {calculateDuration(execution.StartTime, execution.EndTime)}
            </Typography>
          </CardContent>
        </Card>

        {/* Wave Progress */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Wave Progress: {completedWaves} of {execution.Waves.length} complete
            </Typography>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ height: 10, borderRadius: 5 }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {Math.round(progress)}%
            </Typography>
          </CardContent>
        </Card>

        {/* Waves */}
        {execution.Waves.map((wave, index) => (
          <Accordion key={index} defaultExpanded={wave.Status === 'IN_PROGRESS'}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center" gap={2} width="100%">
                <Chip
                  icon={getStatusIcon(wave.Status)}
                  label={wave.Status}
                  color={getStatusColor(wave.Status)}
                  size="small"
                />
                <Typography variant="h6">
                  Wave {index + 1}: {wave.WaveName}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                  Region: {wave.Region}
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Server ID</strong></TableCell>
                      <TableCell><strong>Status</strong></TableCell>
                      <TableCell><strong>Instance ID</strong></TableCell>
                      <TableCell><strong>Recovery Job ID</strong></TableCell>
                      <TableCell><strong>Launch Time</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {wave.Servers.map((server, serverIndex) => (
                      <TableRow key={serverIndex}>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {server.SourceServerId}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getStatusIcon(server.Status)}
                            label={server.Status}
                            color={getStatusColor(server.Status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {server.InstanceId ? (
                            <Link
                              href={getConsoleLink(server.InstanceId, wave.Region)}
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                            >
                              <Typography variant="body2" fontFamily="monospace">
                                {server.InstanceId}
                              </Typography>
                              🔗
                            </Link>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              {server.Status === 'LAUNCHING' ? 'Launching...' : '-'}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {server.RecoveryJobId || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatTimestamp(server.LaunchTime)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                    {wave.Servers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          <Typography variant="body2" color="text.secondary">
                            No servers in this wave
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Show errors if any */}
              {wave.Servers.some(s => s.Error) && (
                <Box mt={2}>
                  {wave.Servers.filter(s => s.Error).map((server, idx) => (
                    <Alert severity="error" key={idx} sx={{ mb: 1 }}>
                      <strong>{server.SourceServerId}:</strong> {server.Error}
                    </Alert>
                  ))}
                </Box>
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    </PageTransition>
  );
};
