/**
 * Execution Details Page
 * 
 * Full page view for execution details with real-time updates.
 * Matches the design of the ExecutionDetails modal component.
 */

import React, { useEffect, useState } from 'react';
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
  const [resuming, setResuming] = useState(false);

  // Fetch execution details - simple pattern like other pages
  const fetchExecution = async () => {
    if (!executionId) return;

    try {
      setError(null);
      const data = await apiClient.getExecution(executionId);
      setExecution(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load execution details');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchExecution();
  }, [executionId]);

  // Simple polling like ExecutionsPage - only for active executions
  useEffect(() => {
    if (!execution) return;

    const isActive = ['in_progress', 'pending', 'paused', 'running', 'started', 'polling', 'launching', 'initiated'].includes(execution.status);
    if (!isActive) return;

    const interval = setInterval(fetchExecution, 3000);
    return () => clearInterval(interval);
  }, [execution?.status]);

  const handleCancelExecution = async () => {
    if (!executionId) return;

    setCancelling(true);
    try {
      await apiClient.cancelExecution(executionId);
      setCancelDialogOpen(false);
      fetchExecution();
    } catch (err: unknown) {
      console.error('Cancel execution error:', err);
    } finally {
      setCancelling(false);
    }
  };

  const handleResumeExecution = async () => {
    if (!executionId || resuming) return;

    setResuming(true);
    try {
      await apiClient.resumeExecution(executionId);
      fetchExecution();
    } catch (err: unknown) {
      console.error('Resume execution error:', err);
    } finally {
      setResuming(false);
    }
  };

  // Check if execution is paused
  const isPaused = execution && execution.status === 'paused';

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

  // Check if execution can be cancelled - simple logic
  const canCancel = execution && ['in_progress', 'pending', 'paused', 'running', 'started', 'polling', 'launching', 'initiated'].includes(execution.status);

  // Map API response (waves/servers) to frontend types (waveExecutions/serverExecutions)
  const mapWavesToWaveExecutions = (exec: Execution): WaveExecution[] => {
    // API returns 'waves' but type expects 'waveExecutions'
    const waves = (exec as Execution & { waves?: WaveExecution[] }).waves || exec.waveExecutions || [];
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
                <Button 
                  onClick={() => navigate('/executions')} 
                  iconName="arrow-left"
                >
                  Back to Executions
                </Button>
                <Button
                  iconName="refresh"
                  onClick={fetchExecution}
                  disabled={loading}
                >
                  Refresh
                </Button>
                {isPaused && (
                  <Button
                    onClick={handleResumeExecution}
                    disabled={resuming}
                    loading={resuming}
                    variant="primary"
                    iconName="caret-right-filled"
                  >
                    Resume Execution
                  </Button>
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
              </SpaceBetween>
            }
          >
            Execution Details
          </Header>
        }
      >
        <SpaceBetween size="l">
          {/* Paused Execution Alert */}
          {isPaused && (
            <Alert
              type="info"
              header="Execution Paused"
              action={
                <Button
                  onClick={handleResumeExecution}
                  loading={resuming}
                  disabled={resuming}
                >
                  Resume Execution
                </Button>
              }
            >
              Execution is paused. Click Resume to continue with the next wave.
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
        message="Are you sure you want to cancel this execution? This will stop the current execution and prevent any remaining waves from starting."
        confirmLabel="Cancel Execution"
        confirmColor="error"
        onConfirm={handleCancelExecution}
        onCancel={() => setCancelDialogOpen(false)}
        loading={cancelling}
      />
    </PageTransition>
  );
};
