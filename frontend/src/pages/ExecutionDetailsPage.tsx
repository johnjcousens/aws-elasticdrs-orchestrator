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
      (execution.status as string) === 'RUNNING' ||
      (execution.status as string) === 'STARTED' ||
      (execution.status as string) === 'POLLING' ||
      (execution.status as string) === 'LAUNCHING' ||
      (execution.status as string) === 'INITIATED';

    if (!isActive) return;

    const interval = setInterval(() => {
      fetchExecution(true); // Silent refresh
    }, 3000); // Poll every 3 seconds for faster updates

    return () => clearInterval(interval);
  }, [execution]);

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

  // Calculate progress percentage
  const calculateProgress = (): number => {
    if (!execution || !execution.currentWave) return 0;
    return (execution.currentWave / execution.totalWaves) * 100;
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
    (execution.status as string) === 'STARTED'
  );

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
          {/* Cancel Error Alert */}
          {cancelError && (
            <Alert type="error" dismissible onDismiss={() => setCancelError(null)}>
              {cancelError}
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
            <WaveProgress waves={mapWavesToWaveExecutions(execution)} />
          </Container>
        </SpaceBetween>
      </ContentLayout>

      {/* Cancel Confirmation Dialog */}
      <ConfirmDialog
        open={cancelDialogOpen}
        title="Cancel Execution"
        message="Are you sure you want to cancel this execution? This action cannot be undone. Servers that have already been recovered will remain in their current state."
        confirmLabel="Cancel Execution"
        confirmColor="error"
        onConfirm={handleCancelExecution}
        onCancel={() => setCancelDialogOpen(false)}
      />
    </PageTransition>
  );
};
