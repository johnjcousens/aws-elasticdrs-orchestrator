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

// CONSISTENCY FIX: Use camelCase types that match backend transformation
interface ServerExecution {
  sourceServerId: string;
  recoveryJobId?: string;
  instanceId?: string | null;
  status: 'LAUNCHING' | 'LAUNCHED' | 'FAILED';
  launchTime: number;
  error?: string;
}

interface WaveExecution {
  waveName: string;
  protectionGroupId: string;
  region: string;
  status: string;
  servers: ServerExecution[];
  startTime: number;
  endTime?: number;
}

interface ExecutionDetails {
  executionId: string;
  recoveryPlanId: string;
  executionType: string;
  status: string;  // Already lowercase from backend
  startTime: number;
  endTime?: number;
  initiatedBy: string;
  waves: WaveExecution[];
  recoveryPlanName?: string;
}

export const ExecutionDetailsPage: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  
  const [execution, setExecution] = useState<ExecutionDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pollingEnabled, setPollingEnabled] = useState(true);
  const [countdown, setCountdown] = useState(15);

  // Fetch execution details
  const fetchExecution = async () => {
    if (!executionId) return;
    
    try {
      const data = await apiClient.getExecution(executionId);
      // Backend now returns camelCase (consistent transformation)
      setExecution(data as unknown as ExecutionDetails);
      setError(null);
      
      // Disable polling if execution is complete
      const typedData = data as unknown as ExecutionDetails;
      if (typedData.status !== 'in_progress') {
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

  // Countdown timer effect - updates every second
  useEffect(() => {
    if (!pollingEnabled || execution?.status !== 'in_progress') {
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          fetchExecution();
          return 15; // Reset countdown
        }
        return prev - 1;
      });
    }, 1000); // Update every second

    return () => clearInterval(timer);
  }, [pollingEnabled, execution?.status]);

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
  const calculateProgress = (waves: WaveExecution[]): number => {
    if (!waves || waves.length === 0) return 0;
    const completedWaves = waves.filter(w => w.status === 'completed').length;
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

  const progress = calculateProgress(execution.waves);
  const completedWaves = execution.waves.filter(w => w.status === 'completed').length;

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
              {execution.recoveryPlanName || 'Recovery Plan'} - {execution.executionType} Execution
            </Typography>
            
            <Box display="flex" gap={2} alignItems="center" mb={2}>
              <Chip
                icon={getStatusIcon(execution.status)}
                label={execution.status}
                color={getStatusColor(execution.status)}
                size="medium"
              />
              {execution.status === 'in_progress' && (
                <Typography variant="body2" color="text.secondary">
                  Refreshing in {countdown}s...
                </Typography>
              )}
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>Execution ID:</strong> {execution.executionId}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>Started:</strong> {formatTimestamp(execution.startTime)} by {execution.initiatedBy}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              <strong>Duration:</strong> {calculateDuration(execution.startTime, execution.endTime)}
            </Typography>
          </CardContent>
        </Card>

        {/* Wave Progress */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Wave Progress: {completedWaves} of {execution.waves.length} complete
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
        {execution.waves.map((wave, index) => (
          <Accordion key={index} defaultExpanded={wave.status === 'in_progress'}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center" gap={2} width="100%">
                <Chip
                  icon={getStatusIcon(wave.status)}
                  label={wave.status}
                  color={getStatusColor(wave.status)}
                  size="small"
                />
                <Typography variant="h6">
                  Wave {index + 1}: {wave.waveName}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                  Region: {wave.region}
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
                    {wave.servers.map((server, serverIndex) => (
                      <TableRow key={serverIndex}>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {server.sourceServerId}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            icon={getStatusIcon(server.status)}
                            label={server.status}
                            color={getStatusColor(server.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {server.instanceId ? (
                            <Link
                              href={getConsoleLink(server.instanceId, wave.region)}
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                            >
                              <Typography variant="body2" fontFamily="monospace">
                                {server.instanceId}
                              </Typography>
                              🔗
                            </Link>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              {server.status === 'LAUNCHING' ? 'Launching...' : '-'}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {server.recoveryJobId || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatTimestamp(server.launchTime)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                    {wave.servers.length === 0 && (
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
              {wave.servers.some(s => s.error) && (
                <Box mt={2}>
                  {wave.servers.filter(s => s.error).map((server, idx) => (
                    <Alert severity="error" key={idx} sx={{ mb: 1 }}>
                      <strong>{server.sourceServerId}:</strong> {server.error}
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
