/**
 * Execution Details Page
 * 
 * Full page view for execution details with real-time updates.
 * Matches the design of the ExecutionDetails modal component.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Button,
  Container,
  Header,
  SpaceBetween,
  Badge,
  Alert,
  ProgressBar,
  ColumnLayout,
} from '@cloudscape-design/components';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
import { PageTransition } from '../components/PageTransition';
import { LoadingState } from '../components/LoadingState';
import { StatusBadge } from '../components/StatusBadge';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import { WaveProgress } from '../components/WaveProgress';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { TerminateInstancesDialog } from '../components/TerminateInstancesDialog';
import { useApiErrorHandler } from '../hooks/useApiErrorHandler';
import apiClient from '../services/api';
import type { Execution, WaveExecution, ServerExecution, JobLogsResponse } from '../types';

export const ExecutionDetailsPage: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  const { handleError } = useApiErrorHandler();
  
  const [execution, setExecution] = useState<Execution | null>(null);
  const [jobLogs, setJobLogs] = useState<JobLogsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);
  const [resuming, setResuming] = useState(false);
  const [resumeInProgress, setResumeInProgress] = useState(false);
  const [resumeError, setResumeError] = useState<string | null>(null);
  const [terminateDialogOpen, setTerminateDialogOpen] = useState(false);
  const [terminating, setTerminating] = useState(false);
  const [terminationInProgress, setTerminationInProgress] = useState(false);
  const [terminateError, setTerminateError] = useState<string | null>(null);
  const [terminateSuccess, setTerminateSuccess] = useState<string | null>(null);
  const [terminationJobInfo, setTerminationJobInfo] = useState<{
    totalInstances: number;
    jobIds: string[];
    region?: string;
  } | null>(null);
  const [terminationProgress, setTerminationProgress] = useState<number>(0);

  // Fetch execution details and job logs
  const fetchExecution = useCallback(async (silent = false) => {
    if (!executionId) return;

    try {
      if (!silent) {
        setLoading(true);
        setError(null);
      }
      
      // Bust cache on explicit refresh (non-silent calls) to ensure fresh data
      const bustCache = !silent;
      const data = await apiClient.getExecution(executionId, bustCache);
      setExecution(data);
      
      // Fetch job logs for enhanced DRS status display
      try {
        const jobLogsData = await apiClient.getJobLogs(executionId);
        setJobLogs(jobLogsData);
      } catch (jobLogsError) {
        // Job logs are optional - don't fail if they're not available
        console.warn('Failed to fetch job logs:', jobLogsError);
        setJobLogs(null);
      }
      
      // Reset resumeInProgress when execution is no longer paused
      if (data.status?.toUpperCase() !== 'PAUSED' && resumeInProgress) {
        setResumeInProgress(false);
      }
    } catch (err: unknown) {
      const error = err instanceof Error ? err : new Error('Failed to load execution details');
      
      // Use the error handler for authentication errors
      try {
        await handleError(error);
      } catch (handledError) {
        // If error handler doesn't handle it, set local error
        const errorMessage = handledError instanceof Error ? handledError.message : 'Failed to load execution details';
        setError(errorMessage);
      }
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, [executionId, resumeInProgress, handleError]);

  // Initial fetch - only depend on executionId to prevent unnecessary refetches
  useEffect(() => {
    fetchExecution();
    // fetchExecution is stable (wrapped in useCallback)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [executionId]);

  // Cleanup all intervals on unmount to prevent navigation blocking
  useEffect(() => {
    return () => {
      // Clear any remaining intervals when component unmounts
      // This ensures navigation isn't blocked by running intervals
    };
  }, []);

  // Real-time polling for active executions
  // This effect starts polling when execution data is loaded and status is active
  useEffect(() => {
    if (!executionId) return;

    // Determine if we should poll based on current execution status
    const status = (execution?.status || '').toUpperCase();
    const isTerminal = 
      status === 'COMPLETED' || 
      status === 'FAILED' ||
      status === 'CANCELLED' ||
      status === 'TIMEOUT';

    // Don't poll if execution is loaded and status is terminal (unless resuming)
    if (execution && isTerminal && !resumeInProgress) {
      return;
    }

    // Poll function - fetches latest execution data
    const poll = async () => {
      try {
        // Always bust cache during polling to get fresh data
        const data = await apiClient.getExecution(executionId, true);
        // Force new object reference to ensure React re-renders
        setExecution({ ...data });
        
        // Clear resumeInProgress when execution is no longer paused
        if (data.status?.toUpperCase() !== 'PAUSED' && resumeInProgress) {
          setResumeInProgress(false);
        }
        
        // Also fetch job logs
        try {
          const jobLogsData = await apiClient.getJobLogs(executionId);
          setJobLogs({ ...jobLogsData });
        } catch {
          // Job logs are optional
        }
      } catch {
        // Polling error - silently continue
      }
    };

    // Immediate poll on mount or when resumeInProgress changes
    poll();

    // Start polling every 3 seconds
    const interval = setInterval(poll, 3000);

    return () => {
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [execution?.status, executionId, resumeInProgress, fetchExecution]);

  // Timer to update duration display every second for active executions
  const [durationTick, setDurationTick] = useState(0);
  useEffect(() => {
    if (!execution) return;

    const status = execution.status?.toUpperCase() || '';
    const isActive = ['IN_PROGRESS', 'PENDING', 'PAUSED', 'RUNNING', 'STARTED', 'POLLING', 'LAUNCHING', 'INITIATED', 'CANCELLING'].includes(status);

    if (!isActive) return;

    const timer = setInterval(() => {
      setDurationTick(tick => tick + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [execution]);

  // Polling while termination is in progress
  useEffect(() => {
    if (!terminationInProgress || !execution) return;

    // Check if instances are now terminated
    const executionWithTermination = execution as Execution & {
      instancesTerminated?: boolean;
      InstancesTerminated?: boolean;
    };
    const isTerminated = 
      executionWithTermination.instancesTerminated === true ||
      executionWithTermination.InstancesTerminated === true;

    if (isTerminated) {
      setTerminationInProgress(false);
      setTerminationProgress(100);
      // NOW show the success message - termination is actually complete
      const instanceCount = terminationJobInfo?.totalInstances || 0;
      if (instanceCount > 0) {
        setTerminateSuccess(`Successfully terminated ${instanceCount} recovery instance(s)`);
      } else {
        setTerminateSuccess('All recovery instances have been terminated.');
      }
      setTerminationJobInfo(null);
      return;
    }

    // Poll for termination job status if we have job IDs
    const pollTerminationStatus = async () => {
      if (terminationJobInfo?.jobIds?.length && executionId) {
        try {
          const region = terminationJobInfo.region || 'us-west-2';
          const statusResult = await apiClient.getTerminationStatus(executionId, terminationJobInfo.jobIds, region);
          
          // Update progress - handle case where DRS clears participatingServers on completion
          if (statusResult.progressPercent !== undefined) {
            setTerminationProgress(statusResult.progressPercent);
          } else if (statusResult.allCompleted) {
            // If all jobs completed but no progress percent, set to 100%
            setTerminationProgress(100);
          } else {
            // Calculate progress based on job completion status
            const completedJobs = statusResult.jobs?.filter(j => j.status === 'COMPLETED').length || 0;
            const totalJobs = statusResult.jobs?.length || 1;
            const jobProgress = Math.round((completedJobs / totalJobs) * 100);
            setTerminationProgress(jobProgress);
          }
          
          // Check if all jobs completed
          if (statusResult.allCompleted) {
            setTerminationInProgress(false);
            setTerminationProgress(100);
            const instanceCount = terminationJobInfo?.totalInstances || statusResult.totalServers || 0;
            if (statusResult.anyFailed) {
              setTerminateSuccess(`Terminated ${statusResult.completedServers} of ${instanceCount} recovery instance(s). Some failed.`);
            } else {
              setTerminateSuccess(`Successfully terminated ${instanceCount} recovery instance(s)`);
            }
            setTerminationJobInfo(null);
            // Refresh execution to update UI
            fetchExecution(true);
          }
        } catch (err) {
          console.error('Error polling termination status:', err);
        }
      }
      // Also refresh execution status
      fetchExecution(true);
    };

    const interval = setInterval(pollTerminationStatus, 3000); // Poll every 3 seconds
    // Initial poll
    pollTerminationStatus();

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [terminationInProgress, terminationJobInfo?.totalInstances, terminationJobInfo?.jobIds, terminationJobInfo?.region, executionId, fetchExecution]);

  const handleCancelExecution = async () => {
    if (!executionId) return;

    setCancelling(true);
    setCancelError(null);

    try {
      await apiClient.cancelExecution(executionId);
      setCancelDialogOpen(false);
      await fetchExecution();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cancel execution';
      setCancelError(errorMessage);
    } finally {
      setCancelling(false);
    }
  };

  const handleResumeExecution = async () => {
    if (!executionId || resuming || resumeInProgress) return;

    setResuming(true);
    setResumeInProgress(true);
    setResumeError(null);

    try {
      await apiClient.resumeExecution(executionId);
      await fetchExecution();
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to resume execution';
      setResumeError(errorMessage);
      setResumeInProgress(false);
    } finally {
      setResuming(false);
    }
  };

  const handleTerminateInstances = async () => {
    if (!executionId) return;

    setTerminating(true);
    setTerminationInProgress(true);
    setTerminateError(null);
    setTerminateSuccess(null);
    setTerminateDialogOpen(false);
    setTerminationJobInfo(null);

    try {
      const result = await apiClient.terminateRecoveryInstances(executionId);
      
      // Handle "already terminated" response
      if (result.alreadyTerminated) {
        setTerminateSuccess('Recovery instances have already been terminated.');
        setTerminationInProgress(false);
      } else if (result.totalTerminated > 0) {
        // Termination INITIATED (not completed) - DRS job created
        // Store job info for progress tracking
        const resultAny = result as { jobs?: Array<{ jobId: string; region?: string }> };
        const jobIds = (resultAny.jobs || []).map((j) => j.jobId).filter(Boolean);
        // Get region from first job or execution
        const region = (resultAny.jobs?.[0]?.region) || (execution as Execution & { drsRegion?: string })?.drsRegion || 'us-west-2';
        setTerminationJobInfo({
          totalInstances: result.totalTerminated,
          jobIds: jobIds,
          region: region
        });
        setTerminationProgress(10); // Start with 10% to show progress has begun
        
        // Keep terminationInProgress true - polling will detect when complete
        // Do NOT show success message yet - wait for actual completion
      } else if (result.totalFailed > 0) {
        setTerminateError(`Failed to terminate ${result.totalFailed} instance(s). They may have already been terminated.`);
        setTerminationInProgress(false);
      } else {
        setTerminateSuccess('No recovery instances to terminate.');
        setTerminationInProgress(false);
      }
      await fetchExecution();
    } catch (err) {
      // Check if error indicates already terminated
      const errorMsg = err instanceof Error ? err.message : '';
      if (errorMsg.includes('No recovery instances') || errorMsg.includes('already')) {
        setTerminateSuccess('Recovery instances have already been terminated or do not exist.');
        await fetchExecution();
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Failed to terminate recovery instances';
        setTerminateError(errorMessage);
      }
      setTerminationInProgress(false);
    } finally {
      setTerminating(false);
    }
  };

  // Check if execution is paused
  const isPaused = execution && execution.status?.toUpperCase() === 'PAUSED';

  // Get paused before wave number (from execution data)
  const pausedBeforeWave = execution ? (execution as Execution & { pausedBeforeWave?: number }).pausedBeforeWave : undefined;

  // Calculate execution duration
  const calculateDuration = (): string => {
    // Force re-render every second via durationTick state
    void durationTick;
    
    if (!execution || !execution.startTime) return '-';
    
    let startTimeMs: number | string = execution.startTime;
    if (typeof execution.startTime === 'number' && execution.startTime < 10000000000) {
      startTimeMs = execution.startTime * 1000;
    }
    
    let endTimeMs: number | string | undefined = execution.endTime;
    if (execution.endTime) {
      if (typeof execution.endTime === 'number' && execution.endTime < 10000000000) {
        endTimeMs = execution.endTime * 1000;
      }
    }
    
    const start = new Date(startTimeMs);
    const end = endTimeMs ? new Date(endTimeMs) : new Date();
    const durationMs = end.getTime() - start.getTime();
    
    if (durationMs < 0 || durationMs > 365 * 24 * 60 * 60 * 1000) {
      return 'Invalid';
    }
    
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  };

  // Calculate progress percentage based on DRS job phases
  // Phases: JOB_START(5%) → SNAPSHOT(10%) → CONVERSION(60%) → LAUNCH(25%)
  const calculateProgress = (): number => {
    if (!execution) return 0;
    
    const waves = (execution as Execution & { waves?: WaveExecution[] }).waves || execution.waveExecutions || [];
    const totalWaves = execution.totalWaves || waves.length || 1;
    
    if (totalWaves === 0) return 0;
    
    // Weight per wave (each wave contributes equally to 100%)
    const waveWeight = 100 / totalWaves;
    
    // Phase weights within a wave (must sum to 1.0)
    const phaseWeights = {
      pending: 0,
      started: 0.05,      // Job started
      snapshot: 0.15,     // Snapshot complete
      conversion: 0.75,   // Conversion complete (longest phase)
      launched: 1.0       // Fully launched
    };
    
    let totalProgress = 0;
    
    for (const wave of waves) {
      const waveAny = wave as WaveExecution & { Status?: string; serverStatuses?: unknown[]; ServerStatuses?: unknown[] };
      const status = (wave.status || waveAny.Status || 'pending').toUpperCase();
      const serverStatuses = waveAny.serverStatuses || waveAny.ServerStatuses || [];
      
      // Check for specific DRS phases from server statuses
      let wavePhaseProgress = 0;
      
      if (status === 'COMPLETED' || status === 'LAUNCHED') {
        wavePhaseProgress = 1.0;
      } else if (status === 'FAILED') {
        // Failed waves count as their last known progress
        wavePhaseProgress = 0.5;
      } else if (serverStatuses.length > 0) {
        // Check individual server launch statuses
        const launchStatuses = serverStatuses.map((s: unknown) => {
          const server = s as { LaunchStatus?: string; launchStatus?: string };
          return (server.LaunchStatus || server.launchStatus || 'PENDING').toUpperCase();
        });
        
        if (launchStatuses.some((s: string) => s === 'LAUNCHED')) {
          wavePhaseProgress = phaseWeights.launched;
        } else if (launchStatuses.some((s: string) => s === 'IN_PROGRESS' || s === 'LAUNCHING')) {
          wavePhaseProgress = phaseWeights.conversion + 0.1; // Past conversion, launching
        } else if (launchStatuses.some((s: string) => s === 'PENDING')) {
          // Still pending - check wave status for more detail
          if (status === 'POLLING' || status === 'STARTED' || status === 'IN_PROGRESS') {
            wavePhaseProgress = phaseWeights.started;
          }
        }
      } else {
        // No server statuses yet, use wave status
        if (status === 'POLLING' || status === 'STARTED' || status === 'IN_PROGRESS' || status === 'LAUNCHING') {
          wavePhaseProgress = phaseWeights.started;
        } else if (status === 'PENDING') {
          wavePhaseProgress = 0;
        }
      }
      
      totalProgress += wavePhaseProgress * waveWeight;
    }
    
    // Ensure we don't exceed 100%
    return Math.min(Math.round(totalProgress), 100);
  };

  // Check if execution can be cancelled
  // Cannot cancel if on the final wave
  
  const currentWave = execution?.currentWave ?? 1;
  const totalWaves = execution?.totalWaves ?? 1;
  
  // Check if we're on the final wave
  const isOnFinalWave = currentWave >= totalWaves;
  

  
  const canCancel = execution && !isOnFinalWave && (() => {
    const status = execution.status?.toUpperCase() || '';
    const activeStatuses = ['IN_PROGRESS', 'PENDING', 'PAUSED', 'RUNNING', 'STARTED', 'POLLING', 'LAUNCHING', 'INITIATED'];
    return activeStatuses.includes(status) && status !== 'CANCELLING';
  })();



  // Check if instances have already been terminated
  const instancesAlreadyTerminated = execution && (() => {
    const executionWithTermination = execution as Execution & {
      instancesTerminated?: boolean;
      InstancesTerminated?: boolean;
    };
    const result = (executionWithTermination.instancesTerminated === true ||
      executionWithTermination.InstancesTerminated === true);
    return result;
  })();

  // Check if recovery instances can be terminated
  // Backend provides centralized termination logic via terminationMetadata
  const canTerminate = execution?.terminationMetadata?.canTerminate ?? false;
  
  // Show terminated status badge instead of button when already terminated
  const showTerminatedBadge = execution && instancesAlreadyTerminated;

  // Map API response (waves/servers) to frontend types (waveExecutions/serverExecutions)
  const mapWavesToWaveExecutions = (exec: Execution): WaveExecution[] => {
    // API returns 'waves' but type expects 'waveExecutions'
    const execAny = exec as Execution & { waves?: WaveExecution[] };
    const waves = execAny.waves || exec.waveExecutions || [];
    
    return waves.map((wave: WaveExecution, index: number) => {
      const waveRegion = (wave as WaveExecution & { region?: string; Region?: string }).region || 
                         (wave as WaveExecution & { region?: string; Region?: string }).Region || 
                         'us-east-1';
      
      // API returns 'serverStatuses' but type expects 'serverExecutions'
      const waveAny = wave as WaveExecution & { serverStatuses?: ServerExecution[] };
      const servers = wave.serverExecutions || waveAny.serverStatuses || [];
      
      return {
        waveNumber: wave.waveNumber ?? index,
        waveName: wave.waveName || `Wave ${index + 1}`,
        status: wave.status || 'pending',
        startTime: wave.startTime,
        jobId: wave.jobId,
        endTime: wave.endTime,
        serverExecutions: servers.map((server: ServerExecution & { serverId?: string; instanceId?: string; ec2InstanceId?: string }) => {
          return {
            serverId: server.serverId || (server as ServerExecution & { sourceServerId?: string }).sourceServerId || '',
            serverName: server.serverName || server.hostname,
            hostname: server.hostname,
            status: server.status || server.launchStatus || 'pending',
            launchStatus: server.launchStatus || server.status,
            recoveredInstanceId: server.instanceId || server.recoveredInstanceId || server.ec2InstanceId,
            instanceType: server.instanceType,
            privateIp: server.privateIp,
            launchTime: server.launchTime,
            region: server.region || waveRegion,
            sourceInstanceId: server.sourceInstanceId,
            sourceAccountId: server.sourceAccountId,
            sourceIp: server.sourceIp,
            sourceRegion: server.sourceRegion,
            replicationState: server.replicationState,
            error: server.error,
          };
        }),
        error: wave.error,
      };
    });
  };

  // Calculate current wave number from waves array (more accurate than API currentWave)
  const calculateCurrentWaveDisplay = (exec: Execution): number => {
    const execAny = exec as Execution & { waves?: WaveExecution[] };
    const waves = execAny.waves || exec.waveExecutions || [];
    const total = exec.totalWaves || waves.length || 1;
    
    // If execution is completed, show total waves
    const status = exec.status?.toUpperCase() || '';
    if (status === 'COMPLETED') {
      return total;
    }
    
    // Active statuses that indicate a wave is currently running
    const activeStatuses = ['IN_PROGRESS', 'POLLING', 'LAUNCHING', 'STARTED', 'INITIATED', 'PENDING'];
    // Completed statuses
    const completedStatuses = ['COMPLETED', 'LAUNCHED'];
    
    // Find the first active wave (1-indexed for display)
    for (let i = 0; i < waves.length; i++) {
      const waveStatus = (waves[i].status || '').toUpperCase();
      if (activeStatuses.includes(waveStatus)) {
        return i + 1; // 1-indexed
      }
    }
    
    // If no active wave, count completed waves
    let completedCount = 0;
    for (const wave of waves) {
      const waveStatus = (wave.status || '').toUpperCase();
      if (completedStatuses.includes(waveStatus)) {
        completedCount++;
      }
    }
    
    // Return completed count (or 1 if none completed yet)
    return completedCount > 0 ? completedCount : 1;
  };

  if (loading && !execution) {
    return (
      <PageTransition>
        <ContentLayout header={<Header variant="h1">Execution Details</Header>}>
          <LoadingState message="Loading execution details..." />
        </ContentLayout>
      </PageTransition>
    );
  }

  if (error && !execution) {
    return (
      <PageTransition>
        <ContentLayout header={<Header variant="h1">Execution Details</Header>}>
          <SpaceBetween size="m">
            <Button onClick={() => navigate('/executions')} iconName="arrow-left">
              Back to Executions
            </Button>
            <Alert type="error" action={<Button onClick={() => fetchExecution()}>Retry</Button>}>
              {error}
            </Alert>
          </SpaceBetween>
        </ContentLayout>
      </PageTransition>
    );
  }

  if (!execution) {
    return (
      <PageTransition>
        <ContentLayout header={<Header variant="h1">Execution Details</Header>}>
          <SpaceBetween size="m">
            <Button onClick={() => navigate('/executions')} iconName="arrow-left">
              Back to Executions
            </Button>
            <Alert type="warning">Execution not found</Alert>
          </SpaceBetween>
        </ContentLayout>
      </PageTransition>
    );
  }



  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button onClick={() => navigate('/executions')} iconName="arrow-left">
                  Back to Executions
                </Button>
                <Button
                  iconName="refresh"
                  onClick={() => fetchExecution()}
                  disabled={loading}
                >
                  Refresh
                </Button>
                {isPaused && !resumeInProgress && (
                  <Button
                    onClick={handleResumeExecution}
                    disabled={resuming || resumeInProgress}
                    loading={resuming}
                    variant="primary"
                    iconName="caret-right-filled"
                  >
                    Resume Execution
                  </Button>
                )}
                {resumeInProgress && (
                  <Badge color="blue">Resuming...</Badge>
                )}
                {canCancel && (
                  <Button
                    onClick={() => setCancelDialogOpen(true)}
                    disabled={cancelling}
                    iconName="close"
                  >
                    Cancel Execution
                  </Button>
                )}
                {canTerminate && !instancesAlreadyTerminated && !terminationInProgress && (
                  <Button
                    onClick={() => setTerminateDialogOpen(true)}
                    disabled={terminating}
                    iconName="remove"
                  >
                    Terminate Instances
                  </Button>
                )}
                {terminationInProgress && (
                  <Badge color="blue">Terminating...</Badge>
                )}
                {showTerminatedBadge && !terminationInProgress && (
                  <Badge color="grey">Instances Terminated</Badge>
                )}
              </SpaceBetween>
            }
          >
            Execution Details
          </Header>
        }
      >
        <SpaceBetween size="l">
          {/* Cancel Error Alert */}
          {cancelError && (
            <Alert type="error" dismissible onDismiss={() => setCancelError(null)}>
              {cancelError}
            </Alert>
          )}

          {/* Resume Error Alert */}
          {resumeError && (
            <Alert type="error" dismissible onDismiss={() => setResumeError(null)}>
              {resumeError}
            </Alert>
          )}

          {/* Terminate Error Alert */}
          {terminateError && (
            <Alert type="error" dismissible onDismiss={() => setTerminateError(null)}>
              {terminateError}
            </Alert>
          )}

          {/* Terminate Success Alert */}
          {terminateSuccess && (
            <Alert type="success" dismissible onDismiss={() => setTerminateSuccess(null)}>
              {terminateSuccess}
            </Alert>
          )}

          {/* Termination In Progress */}
          {terminationInProgress && (
            <Alert type="info" header="Terminating Recovery Instances">
              <SpaceBetween size="s">
                <div>
                  {terminationJobInfo 
                    ? `Terminating ${terminationJobInfo.totalInstances} recovery instance(s) via DRS. This may take a few minutes...`
                    : 'Terminating recovery instances from DRS. This may take a few minutes...'}
                </div>
                
                {/* Termination Progress Bar */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <div style={{ fontSize: '12px', color: '#5f6b7a' }}>
                      Termination Progress
                    </div>
                    <div style={{ fontSize: '12px', color: '#5f6b7a' }}>
                      {terminationProgress}%
                    </div>
                  </div>
                  <ProgressBar
                    value={terminationProgress}
                    variant="standalone"
                    status={terminationProgress === 100 ? "success" : "in-progress"}
                  />
                </div>

                {terminationJobInfo?.jobIds?.length && (
                  <div style={{ fontSize: '14px', color: '#5f6b7a' }}>
                    DRS Job{terminationJobInfo.jobIds.length > 1 ? 's' : ''}: {terminationJobInfo.jobIds.join(', ')}
                  </div>
                )}
              </SpaceBetween>
            </Alert>
          )}

          {/* Paused Before Wave Alert */}
          {isPaused && !resumeInProgress && (
            <Alert
              type="info"
              header="Execution Paused"
              action={
                <Button
                  onClick={handleResumeExecution}
                  loading={resuming}
                  disabled={resuming || resumeInProgress}
                >
                  Resume Execution
                </Button>
              }
            >
              {pausedBeforeWave !== undefined
                ? `Execution is paused before starting Wave ${pausedBeforeWave + 1}. Click Resume to continue.`
                : 'Execution is paused. Click Resume to continue with the next wave.'}
            </Alert>
          )}

          {/* Resume In Progress Alert */}
          {resumeInProgress && (
            <Alert type="info" header="Resuming Execution">
              Execution is resuming. The next wave will start shortly...
            </Alert>
          )}

          {/* Execution Metadata */}
          <Container header={<Header variant="h3">Recovery Plan</Header>}>
            <SpaceBetween size="m">
              <div>
                <div style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>
                  {execution.recoveryPlanName}
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <StatusBadge status={execution.status} />
                  {execution.totalWaves && (
                    <Badge color="blue">
                      Wave {calculateCurrentWaveDisplay(execution)} of {execution.totalWaves}
                    </Badge>
                  )}
                  {execution.executedBy && (
                    <Badge>
                      By: {execution.executedBy}
                    </Badge>
                  )}
                </div>
              </div>

              <ColumnLayout columns={4} variant="text-grid">
                <div>
                  <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                    Started
                  </div>
                  <DateTimeDisplay value={execution.startTime} format="full" />
                </div>

                {execution.endTime && (
                  <div>
                    <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                      Ended
                    </div>
                    <DateTimeDisplay value={execution.endTime} format="full" />
                  </div>
                )}

                <div>
                  <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                    Duration
                  </div>
                  <div>{calculateDuration()}</div>
                </div>

                <div>
                  <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                    Execution ID
                  </div>
                  <div style={{ fontFamily: 'monospace', fontSize: '14px' }}>
                    {execution.executionId}
                  </div>
                </div>
              </ColumnLayout>

              {/* Progress Bar for Active Executions */}
              {['IN_PROGRESS', 'PAUSED'].includes(execution.status?.toUpperCase() || '') && execution.currentWave && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ fontSize: '12px', color: '#5f6b7a' }}>
                      Overall Progress
                    </div>
                    <div style={{ fontSize: '12px', color: '#5f6b7a' }}>
                      {Math.round(calculateProgress())}%
                    </div>
                  </div>
                  <ProgressBar
                    value={calculateProgress()}
                    variant="standalone"
                  />
                </div>
              )}
            </SpaceBetween>
          </Container>

          {/* Error Information */}
          {execution.error && (
            <Alert type="error" header={execution.error.code}>
              <div>{execution.error.message}</div>
              {execution.error.details && (
                <pre style={{ 
                  marginTop: '8px',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}>
                  {JSON.stringify(execution.error.details, null, 2)}
                </pre>
              )}
            </Alert>
          )}

          {/* Wave Progress Timeline */}
          <Container header={<Header variant="h3">Wave Progress</Header>}>
            <WaveProgress 
              waves={mapWavesToWaveExecutions(execution)} 
              currentWave={execution.currentWave}
              totalWaves={execution.totalWaves}
              jobLogs={jobLogs}
            />
          </Container>
        </SpaceBetween>
      </ContentLayout>

      {/* Cancel Confirmation Dialog */}
      <ConfirmDialog
        open={cancelDialogOpen}
        title="Cancel Execution"
        message="Are you sure you want to cancel this execution? Completed waves will remain unchanged. The current in-progress wave will continue to completion. Only pending (not yet started) waves will be cancelled."
        confirmLabel="Cancel Execution"
        confirmColor="error"
        onConfirm={handleCancelExecution}
        onCancel={() => setCancelDialogOpen(false)}
        loading={cancelling}
      />

      {/* Terminate Instances Confirmation Dialog */}
      <TerminateInstancesDialog
        open={terminateDialogOpen}
        execution={execution}
        onConfirm={handleTerminateInstances}
        onCancel={() => setTerminateDialogOpen(false)}
        loading={terminating}
      />
    </PageTransition>
  );
};
