/**
 * Execution Details Page
 * 
 * Full page view for execution details with real-time updates.
 * Matches the design of the ExecutionDetails modal component.
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
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
import apiClient from '../services/api';
import type { Execution, WaveExecution } from '../types';

export const ExecutionDetailsPage: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  
  const [execution, setExecution] = useState<Execution | null>(null);
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

  // Fetch execution details
  const fetchExecution = async (silent = false) => {
    if (!executionId) return;

    try {
      if (!silent) {
        setLoading(true);
        setError(null);
      }
      const data = await apiClient.getExecution(executionId);
      setExecution(data);
      
      // Reset resumeInProgress when execution is no longer paused
      if (data.status !== 'paused' && resumeInProgress) {
        setResumeInProgress(false);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load execution details');
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchExecution();
  }, [executionId]);

  // Real-time polling for active executions
  useEffect(() => {
    if (!execution) return;

    const isActive = 
      execution.status === 'in_progress' || 
      execution.status === 'pending' ||
      execution.status === 'paused' ||
      execution.status === 'running' ||
      execution.status === 'started' ||
      execution.status === 'polling' ||
      execution.status === 'launching' ||
      execution.status === 'initiated' ||
      execution.status === 'cancelling' ||
      (execution.status as string) === 'RUNNING' ||
      (execution.status as string) === 'STARTED' ||
      (execution.status as string) === 'POLLING' ||
      (execution.status as string) === 'LAUNCHING' ||
      (execution.status as string) === 'INITIATED' ||
      (execution.status as string) === 'CANCELLING';

    if (!isActive) return;

    const interval = setInterval(() => {
      fetchExecution(true); // Silent refresh
    }, 3000); // Poll every 3 seconds for faster updates

    return () => clearInterval(interval);
  }, [execution]);

  // Polling while termination is in progress
  useEffect(() => {
    if (!terminationInProgress || !execution) return;

    // Check if instances are now terminated
    const isTerminated = 
      (execution as any).instancesTerminated === true ||
      (execution as any).InstancesTerminated === true;

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
      console.log('[Termination Poll] terminationJobInfo:', terminationJobInfo);
      console.log('[Termination Poll] jobIds:', terminationJobInfo?.jobIds);
      if (terminationJobInfo?.jobIds?.length && executionId) {
        try {
          const region = terminationJobInfo.region || 'us-west-2';
          console.log('[Termination Poll] Calling getTerminationStatus with jobIds:', terminationJobInfo.jobIds, 'region:', region);
          const statusResult = await apiClient.getTerminationStatus(executionId, terminationJobInfo.jobIds, region);
          console.log('[Termination Poll] Status result:', statusResult);
          
          if (statusResult.progressPercent !== undefined) {
            console.log('[Termination Poll] Setting progress to:', statusResult.progressPercent);
            setTerminationProgress(statusResult.progressPercent);
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
  }, [terminationInProgress, execution, terminationJobInfo, executionId]);

  const handleCancelExecution = async () => {
    if (!executionId) return;

    setCancelling(true);
    setCancelError(null);

    try {
      await apiClient.cancelExecution(executionId);
      setCancelDialogOpen(false);
      await fetchExecution();
    } catch (err: any) {
      setCancelError(err.message || 'Failed to cancel execution');
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
      // Keep resumeInProgress true - status polling will update when execution resumes
    } catch (err: any) {
      setResumeError(err.message || 'Failed to resume execution');
      setResumeInProgress(false); // Only reset on error so button can be retried
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
        const resultAny = result as any;
        const jobIds = (resultAny.jobs || []).map((j: any) => j.jobId).filter(Boolean);
        console.log('[Terminate] API result:', result);
        console.log('[Terminate] Extracted jobIds:', jobIds);
        // Get region from first job or execution
        const region = (resultAny.jobs?.[0]?.region) || (execution as any)?.drsRegion || 'us-west-2';
        console.log('[Terminate] Setting terminationJobInfo with region:', region);
        setTerminationJobInfo({
          totalInstances: result.totalTerminated,
          jobIds: jobIds,
          region: region
        });
        setTerminationProgress(0); // Reset progress
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
    } catch (err: any) {
      // Check if error indicates already terminated
      const errorMsg = err.message || '';
      if (errorMsg.includes('No recovery instances') || errorMsg.includes('already')) {
        setTerminateSuccess('Recovery instances have already been terminated or do not exist.');
        await fetchExecution();
      } else {
        setTerminateError(err.message || 'Failed to terminate recovery instances');
      }
      setTerminationInProgress(false);
    } finally {
      setTerminating(false);
    }
  };

  // Check if execution is paused
  const isPaused = execution && (
    execution.status === 'paused' ||
    (execution.status as string) === 'PAUSED'
  );

  // Get paused before wave number (from execution data)
  const pausedBeforeWave = execution ? (execution as any).pausedBeforeWave : undefined;

  // Calculate execution duration
  const calculateDuration = (): string => {
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
    
    const waves = (execution as any).waves || execution.waveExecutions || [];
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
      const status = (wave.status || wave.Status || 'pending').toUpperCase();
      const serverStatuses = wave.serverStatuses || wave.ServerStatuses || [];
      
      // Check for specific DRS phases from server statuses
      let wavePhaseProgress = 0;
      
      if (status === 'COMPLETED' || status === 'LAUNCHED') {
        wavePhaseProgress = 1.0;
      } else if (status === 'FAILED') {
        // Failed waves count as their last known progress
        wavePhaseProgress = 0.5;
      } else if (serverStatuses.length > 0) {
        // Check individual server launch statuses
        const launchStatuses = serverStatuses.map((s: any) => 
          (s.LaunchStatus || s.launchStatus || 'PENDING').toUpperCase()
        );
        
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
  const canCancel = execution && (
    execution.status === 'in_progress' || 
    execution.status === 'pending' ||
    execution.status === 'paused' ||
    execution.status === 'running' ||
    execution.status === 'started' ||
    execution.status === 'polling' ||
    execution.status === 'launching' ||
    execution.status === 'initiated' ||
    (execution.status as string) === 'RUNNING' ||
    (execution.status as string) === 'STARTED' ||
    (execution.status as string) === 'PAUSED' ||
    (execution.status as string) === 'PENDING' ||
    (execution.status as string) === 'IN_PROGRESS' ||
    (execution.status as string) === 'POLLING' ||
    (execution.status as string) === 'LAUNCHING' ||
    (execution.status as string) === 'INITIATED'
  ) && !(
    // Don't allow cancel if already cancelling
    execution.status === 'cancelling' ||
    (execution.status as string) === 'CANCELLING'
  );

  // Check if instances have already been terminated
  const instancesAlreadyTerminated = execution && (
    (execution as any).instancesTerminated === true ||
    (execution as any).InstancesTerminated === true
  );

  // Check if recovery instances can be terminated
  // Only enabled when execution is in terminal state AND has at least one wave with a jobId AND not already terminated
  const canTerminate = execution && (() => {
    const terminalStatuses = [
      'completed', 'cancelled', 'failed', 'partial',
      'COMPLETED', 'CANCELLED', 'FAILED', 'PARTIAL'
    ];
    const isTerminal = terminalStatuses.includes(execution.status as string);
    
    // Check if any wave has a jobId (meaning recovery instances were launched)
    const waves = (execution as any).waves || execution.waveExecutions || [];
    const hasJobId = waves.some((wave: any) => wave.jobId || wave.JobId);
    
    // Don't show button if already terminated
    if (instancesAlreadyTerminated) return false;
    
    return isTerminal && hasJobId;
  })();
  
  // Show terminated status badge instead of button when already terminated
  const showTerminatedBadge = execution && instancesAlreadyTerminated;

  // Map API response (waves/servers) to frontend types (waveExecutions/serverExecutions)
  const mapWavesToWaveExecutions = (exec: Execution): WaveExecution[] => {
    // API returns 'waves' but type expects 'waveExecutions'
    const waves = (exec as any).waves || exec.waveExecutions || [];
    return waves.map((wave: any, index: number) => {
      const waveRegion = wave.region || wave.Region || 'us-east-1';
      // ServerIds might be an array of strings or objects
      const serverIds = wave.serverIds || wave.ServerIds || wave.servers || wave.serverExecutions || [];
      
      return {
        waveNumber: wave.waveNumber ?? wave.WaveNumber ?? index,
        waveName: wave.waveName || wave.WaveName || `Wave ${index + 1}`,
        status: wave.status || wave.Status || 'pending',
        startTime: wave.startTime || wave.StartTime,
        jobId: wave.jobId || wave.JobId,
        endTime: wave.endTime || wave.EndTime,
        serverExecutions: serverIds.map((server: any) => {
          // Handle both string IDs and object formats
          const serverId = typeof server === 'string' ? server : (server.sourceServerId || server.serverId || server.SourceServerId);
          return {
            serverId: serverId,
            serverName: typeof server === 'object' ? (server.serverName || server.hostname) : undefined,
            hostname: typeof server === 'object' ? server.hostname : undefined,
            status: typeof server === 'object' ? (server.status || server.launchStatus || 'pending') : 'pending',
            launchStatus: typeof server === 'object' ? (server.launchStatus || server.status) : undefined,
            recoveredInstanceId: typeof server === 'object' ? (server.instanceId || server.recoveredInstanceId || server.ec2InstanceId) : undefined,
            instanceType: typeof server === 'object' ? server.instanceType : undefined,
            privateIp: typeof server === 'object' ? server.privateIp : undefined,
            region: typeof server === 'object' ? (server.region || waveRegion) : waveRegion,
            sourceInstanceId: typeof server === 'object' ? server.sourceInstanceId : undefined,
            sourceAccountId: typeof server === 'object' ? server.sourceAccountId : undefined,
            sourceIp: typeof server === 'object' ? server.sourceIp : undefined,
            sourceRegion: typeof server === 'object' ? server.sourceRegion : undefined,
            replicationState: typeof server === 'object' ? server.replicationState : undefined,
            error: typeof server === 'object' ? server.error : undefined,
          };
        }),
        error: wave.error,
      };
    });
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
                {canTerminate && !terminationInProgress && (
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
                <ProgressBar
                  value={terminationProgress}
                  status={terminationProgress >= 100 ? "success" : "in-progress"}
                  label="Termination Progress"
                  description={terminationJobInfo?.jobIds?.length 
                    ? `DRS Job${terminationJobInfo.jobIds.length > 1 ? 's' : ''}: ${terminationJobInfo.jobIds.join(', ')} - ${terminationProgress}%`
                    : 'Waiting for DRS to terminate instances...'}
                />
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
                      Wave {execution.currentWave ?? 1} of {execution.totalWaves}
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
              {execution.status === 'in_progress' && execution.currentWave && (
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
              totalWaves={execution.totalWaves} 
              executionId={execution.executionId}
              executionStatus={execution.status}
              executionEndTime={execution.endTime}
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
      <ConfirmDialog
        open={terminateDialogOpen}
        title="Terminate Recovery Instances"
        message="Are you sure you want to terminate all recovery instances from this execution? This will permanently terminate all EC2 instances that were launched as part of this recovery. This action cannot be undone."
        confirmLabel="Terminate Instances"
        confirmColor="error"
        onConfirm={handleTerminateInstances}
        onCancel={() => setTerminateDialogOpen(false)}
        loading={terminating}
      />
    </PageTransition>
  );
};
