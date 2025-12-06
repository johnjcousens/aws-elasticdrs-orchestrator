import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Header,
  SpaceBetween,
  Badge,
  Spinner,
  Alert,
  ExpandableSection,
  Table,
  Link,
  ProgressBar,
  ColumnLayout,
  StatusIndicator,
} from '@cloudscape-design/components';
import { ContentLayout } from '../components/cloudscape/ContentLayout';
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
      
      // Disable polling only when all waves AND servers reach terminal states
      const typedData = data as unknown as ExecutionDetails;
      const hasInProgressWaves = (typedData.waves || []).some(w => 
        w.status === 'in_progress' || w.status === 'launching'
      );
      const hasLaunchingServers = (typedData.waves || []).some(w =>
        (w.servers || []).some(s => s.status === 'LAUNCHING')
      );
      
      // Continue polling if:
      // 1. Execution is in progress, OR
      // 2. Any wave is in progress/launching, OR  
      // 3. Any server is still launching
      if (typedData.status === 'in_progress' || hasInProgressWaves || hasLaunchingServers) {
        setPollingEnabled(true);
      } else {
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

  // Helper: Get status type for StatusIndicator
  const getStatusType = (status: string): 'success' | 'error' | 'warning' | 'info' | 'stopped' | 'pending' | 'in-progress' | 'loading' => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'launched':
        return 'success';
      case 'failed':
        return 'error';
      case 'in_progress':
      case 'launching':
        return 'in-progress';
      case 'partial':
        return 'warning';
      default:
        return 'pending';
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
  const calculateProgress = (waves: WaveExecution[] | undefined): number => {
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
        <ContentLayout header={<Header variant="h1">Execution Details</Header>}>
          <Box textAlign="center" padding={{ vertical: 'xxl' }}>
            <Spinner size="large" />
          </Box>
        </ContentLayout>
      </PageTransition>
    );
  }

  if (error) {
    return (
      <PageTransition>
        <ContentLayout header={<Header variant="h1">Execution Details</Header>}>
          <SpaceBetween size="m">
            <Button onClick={() => navigate('/recovery-plans')} iconName="arrow-left">
              Back to Recovery Plans
            </Button>
            <Alert
              type="error"
              action={
                <Button onClick={fetchExecution}>
                  Retry
                </Button>
              }
            >
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
          <Alert type="warning">Execution not found</Alert>
        </ContentLayout>
      </PageTransition>
    );
  }

  const progress = calculateProgress(execution.waves);
  const completedWaves = (execution.waves || []).filter(w => w.status === 'completed').length;

  return (
    <PageTransition>
      <ContentLayout
        header={
          <Header
            variant="h1"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button onClick={() => navigate('/recovery-plans')} iconName="arrow-left">
                  Back to Recovery Plans
                </Button>
                <Button
                  iconName="refresh"
                  onClick={fetchExecution}
                  disabled={loading}
                >
                  Refresh
                </Button>
              </SpaceBetween>
            }
          >
            {execution.recoveryPlanName || 'Recovery Plan'} - {execution.executionType} Execution
          </Header>
        }
      >
        <SpaceBetween size="l">
          {/* Execution Overview */}
          <Container>
            <SpaceBetween size="m">
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <StatusIndicator type={getStatusType(execution.status)}>
                  {execution.status}
                </StatusIndicator>
                {execution.status === 'in_progress' && (
                  <span style={{ fontSize: '14px', color: '#5f6b7a' }}>
                    Refreshing in {countdown}s...
                  </span>
                )}
              </div>

              <ColumnLayout columns={3} variant="text-grid">
                <div>
                  <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                    Execution ID
                  </div>
                  <div style={{ fontFamily: 'monospace', fontSize: '14px' }}>
                    {execution.executionId}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                    Started
                  </div>
                  <div>{formatTimestamp(execution.startTime)} by {execution.initiatedBy}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
                    Duration
                  </div>
                  <div>{calculateDuration(execution.startTime, execution.endTime)}</div>
                </div>
              </ColumnLayout>
            </SpaceBetween>
          </Container>

          {/* Wave Progress */}
          <Container
            header={
              <Header variant="h2">
                Wave Progress: {completedWaves} of {(execution.waves || []).length} complete
              </Header>
            }
          >
            <SpaceBetween size="s">
              <ProgressBar
                value={progress}
                variant="standalone"
                label={`${Math.round(progress)}%`}
              />
            </SpaceBetween>
          </Container>

          {/* Waves */}
          {(execution.waves || []).map((wave, index) => (
            <ExpandableSection
              key={index}
              defaultExpanded={wave.status === 'in_progress'}
              headerText={
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%' }}>
                  <StatusIndicator type={getStatusType(wave.status)}>
                    {wave.status}
                  </StatusIndicator>
                  <span style={{ fontWeight: 600, fontSize: '16px' }}>
                    Wave {index + 1}: {wave.waveName}
                  </span>
                  <span style={{ marginLeft: 'auto', fontSize: '14px', color: '#5f6b7a' }}>
                    Region: {wave.region}
                  </span>
                </div>
              }
            >
              <SpaceBetween size="m">
                <Table
                  columnDefinitions={[
                    {
                      id: 'serverId',
                      header: 'Server ID',
                      cell: (server: ServerExecution) => (
                        <span style={{ fontFamily: 'monospace', fontSize: '14px' }}>
                          {server.sourceServerId}
                        </span>
                      ),
                    },
                    {
                      id: 'status',
                      header: 'Status',
                      cell: (server: ServerExecution) => (
                        <StatusIndicator type={getStatusType(server.status)}>
                          {server.status}
                        </StatusIndicator>
                      ),
                    },
                    {
                      id: 'instanceId',
                      header: 'Instance ID',
                      cell: (server: ServerExecution) =>
                        server.instanceId ? (
                          <Link
                            href={getConsoleLink(server.instanceId, wave.region)}
                            external
                          >
                            {server.instanceId}
                          </Link>
                        ) : (
                          <span style={{ color: '#5f6b7a' }}>
                            {server.status === 'LAUNCHING' ? 'Launching...' : '-'}
                          </span>
                        ),
                    },
                    {
                      id: 'recoveryJobId',
                      header: 'Recovery Job ID',
                      cell: (server: ServerExecution) => (
                        <span style={{ fontFamily: 'monospace', fontSize: '14px' }}>
                          {server.recoveryJobId || '-'}
                        </span>
                      ),
                    },
                    {
                      id: 'launchTime',
                      header: 'Launch Time',
                      cell: (server: ServerExecution) => formatTimestamp(server.launchTime),
                    },
                  ]}
                  items={wave.servers}
                  empty={
                    <Box textAlign="center" color="inherit">
                      <div style={{ color: '#5f6b7a' }}>No servers in this wave</div>
                    </Box>
                  }
                  variant="embedded"
                />

                {/* Show errors if any */}
                {wave.servers.some(s => s.error) && (
                  <SpaceBetween size="xs">
                    {wave.servers.filter(s => s.error).map((server, idx) => (
                      <Alert type="error" key={idx}>
                        <strong>{server.sourceServerId}:</strong> {server.error}
                      </Alert>
                    ))}
                  </SpaceBetween>
                )}
              </SpaceBetween>
            </ExpandableSection>
          ))}
        </SpaceBetween>
      </ContentLayout>
    </PageTransition>
  );
};
