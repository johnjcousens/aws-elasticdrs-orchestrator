/**
 * Wave Progress Component
 * 
 * Displays wave execution timeline using CloudScape components.
 * Pure display component - receives data as props, no internal polling.
 * 
 * Based on archive reference pattern for stability.
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  SpaceBetween,
  Box,
  ExpandableSection,
  Alert,
  Badge,
  ProgressBar,
  Table,
  Link,
} from '@cloudscape-design/components';
import { StatusBadge } from './StatusBadge';
import apiClient from '../services/api';
import type { WaveExecution, ServerExecution, JobLogsResponse, JobLogEvent } from '../types';

interface WaveProgressProps {
  waves: WaveExecution[];
  currentWave?: number;
  totalWaves?: number;
  jobLogs?: JobLogsResponse | null;
}

interface StagingJobDetails {
  jobId: string;
  stagingAccountId: string;
  type: string;
  status: string;
  statusMessage?: string;
  creationDateTime: string;
  endDateTime?: string;
  participatingServers: number;
  serverIds: string[];
}

interface StagingJobLogs {
  [jobId: string]: JobLogEvent[];
}

/**
 * Determine effective wave status based on wave status and server statuses
 * If wave says "started" but all servers are "LAUNCHED", it's actually completed
 * Also checks job logs for LAUNCH_END events as authoritative completion signal
 */
const getEffectiveWaveStatus = (wave: WaveExecution, jobLogs?: JobLogsResponse | null): string => {
  const waveStatus = (wave.status || 'pending').toLowerCase();
  
  // If wave already shows completed/failed, use that
  if (['completed', 'failed', 'cancelled'].includes(waveStatus)) {
    return waveStatus;
  }
  
  // Check server statuses to determine if wave is actually complete
  const servers = wave.serverExecutions || [];
  if (servers.length > 0) {
    const allLaunched = servers.every(s => {
      const status = (s.launchStatus || s.status || '').toUpperCase();
      return status === 'LAUNCHED';
    });
    
    const anyFailed = servers.some(s => {
      const status = (s.launchStatus || s.status || '').toUpperCase();
      return status === 'FAILED';
    });
    
    const anyInProgress = servers.some(s => {
      const status = (s.launchStatus || s.status || '').toUpperCase();
      return ['IN_PROGRESS', 'LAUNCHING', 'PENDING_LAUNCH'].includes(status);
    });
    
    if (allLaunched) return 'completed';
    if (anyFailed) return 'failed';
    
    // Check job logs for authoritative completion signal
    if (jobLogs && wave.jobId) {
      const waveLog = jobLogs.jobLogs?.find(log => log.jobId === wave.jobId);
      if (waveLog) {
        const hasJobEnd = waveLog.events.some(e => e.event === 'JOB_END');
        const launchEndEvents = waveLog.events.filter(e => e.event === 'LAUNCH_END');
        
        // If job ended and we have LAUNCH_END for all servers, wave is complete
        if (hasJobEnd && launchEndEvents.length === servers.length) {
          return 'completed';
        }
      }
    }
    
    if (anyInProgress) return 'in_progress';
  }
  
  // Map DRS job statuses to appropriate display statuses
  switch (waveStatus) {
    case 'started':
      return 'in_progress'; // DRS job is active, show as in progress
    case 'launching':
    case 'initiated':
      return 'in_progress';
    case 'polling':
      return 'in_progress';
    default:
      return waveStatus;
  }
};

/**
 * Get status indicator icon for wave (AWS Design System compatible)
 */
const getWaveStatusIndicator = (status: string): string => {
  switch (status?.toLowerCase()) {
    case 'completed':
    case 'launched':
      return '✅'; // Green checkmark for completed
    case 'failed':
      return '❌'; // Red X for failed
    case 'in_progress':
    case 'started':
    case 'polling':
    case 'launching':
      return '🔄'; // Blue spinning for in progress
    case 'pending':
      return '⏳'; // Hourglass for pending
    case 'skipped':
      return '⏭️'; // Skip icon
    case 'cancelled':
      return '🚫'; // Cancelled icon
    default:
      return '⚪'; // Default circle
  }
};

/**
 * Get status color for wave indicator (AWS Design System colors)
 */
const getStatusColor = (status: string): string => {
  switch (status?.toLowerCase()) {
    case 'completed':
    case 'launched':
      return '#037f0c'; // AWS Success Green
    case 'failed':
      return '#d91515'; // AWS Error Red
    case 'in_progress':
    case 'started':
    case 'polling':
    case 'launching':
      return '#0972d3'; // AWS Info Blue
    case 'pending':
      return '#ff9900'; // AWS Warning Orange
    case 'cancelled':
      return '#879596'; // AWS Disabled Gray
    default:
      return '#5f6b7a'; // AWS Text Secondary
  }
};

/**
 * Get job logs for a specific wave
 */
const getWaveJobLogs = (jobLogs: JobLogsResponse | null, waveNumber: number): JobLogEvent[] => {
  if (!jobLogs || !jobLogs.jobLogs) return [];
  
  const waveLog = jobLogs.jobLogs.find(log => log.waveNumber === waveNumber);
  return waveLog?.events || [];
};

/**
 * Format job log event for display with AWS-style icons
 */
const formatJobLogEvent = (event: JobLogEvent): string => {
  switch (event.event) {
    case 'SNAPSHOT_START':
      return '📸 Starting snapshot creation';
    case 'SNAPSHOT_END':
      return '✅ Snapshot creation completed';
    case 'CONVERSION_START':
      return '🔄 Starting server conversion';
    case 'CONVERSION_END':
      return '✅ Server conversion completed';
    case 'LAUNCH_START':
      return '🚀 Starting instance launch';
    case 'LAUNCH_END':
      return '✅ Instance launch completed';
    case 'JOB_START':
      return '▶️ DRS job started';
    case 'JOB_END':
      return '🎉 DRS job completed';
    case 'CLEANUP_START':
      return '🧹 Starting cleanup';
    case 'CLEANUP_END':
      return '✅ Cleanup completed';
    default:
      return `📋 ${event.event.replace(/_/g, ' ').toLowerCase()}`;
  }
};

/**
 * Parse timestamp - handles both Unix timestamps and ISO strings
 */
const parseTimestamp = (timestamp: string | number | undefined): Date | null => {
  if (!timestamp) return null;
  
  if (typeof timestamp === 'number' || /^\d+$/.test(String(timestamp))) {
    const ts = typeof timestamp === 'number' ? timestamp : parseInt(String(timestamp), 10);
    return new Date(ts < 10000000000 ? ts * 1000 : ts);
  }
  
  return new Date(timestamp);
};

/**
 * Format timestamp for display
 */
const formatTimestamp = (timestamp: string | number | undefined): string => {
  const date = parseTimestamp(timestamp);
  if (!date) return '-';
  return date.toLocaleString();
};

/**
 * Calculate wave duration
 */
const calculateWaveDuration = (wave: WaveExecution): string => {
  if (!wave.startTime) return '-';
  
  const start = parseTimestamp(wave.startTime);
  if (!start) return '-';
  
  const end = wave.endTime ? parseTimestamp(wave.endTime) : new Date();
  if (!end) return '-';
  
  const durationMs = end.getTime() - start.getTime();
  if (durationMs < 0) return '-';
  
  const hours = Math.floor(durationMs / (1000 * 60 * 60));
  const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
  
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
};

/**
 * Format relative time from timestamp
 */
const formatRelativeTime = (timestamp: string | number | undefined): string => {
  const date = parseTimestamp(timestamp);
  if (!date) return '-';
  
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  return date.toLocaleString();
};

/**
 * Generate AWS console link for EC2 instance
 */
const getConsoleLink = (instanceId: string, region: string): string => {
  return `https://console.aws.amazon.com/ec2/v2/home?region=${region}#Instances:instanceId=${instanceId}`;
};

/**
 * Calculate overall progress with granular server-level tracking
 * 
 * Progress calculation:
 * - Completed waves: 1.0 each
 * - In-progress waves: base 0.1 + (launched servers / total servers * 0.9)
 *   This ensures in-progress waves show some progress even before servers launch
 * - Pending waves: 0
 * 
 * Example with 3 waves, wave 1 has 4 servers:
 * - Wave started, 0 servers launched: 0.1/3 = 3%
 * - 1 server launched: (0.1 + 0.225)/3 = 11%
 * - 2 servers launched: (0.1 + 0.45)/3 = 18%
 * - 3 servers launched: (0.1 + 0.675)/3 = 26%
 * - 4 servers launched (wave complete): 1/3 = 33%
 */
const calculateProgress = (
  waves: WaveExecution[], 
  totalWaves?: number,
  jobLogs?: JobLogsResponse | null
): { percentage: number; completed: number; total: number } => {
  // Use waves.length as fallback if totalWaves not provided
  const total = totalWaves || waves?.length || 0;
  
  if (!waves || waves.length === 0) {
    return { percentage: 0, completed: 0, total };
  }
  
  if (total === 0) {
    return { percentage: 0, completed: 0, total: 0 };
  }
  
  let totalProgress = 0;
  
  waves.forEach(w => {
    const effectiveStatus = getEffectiveWaveStatus(w, jobLogs);
    
    if (effectiveStatus === 'completed' || effectiveStatus === 'launched') {
      // Fully completed wave = 1.0
      totalProgress += 1.0;
    } else if (effectiveStatus === 'in_progress' || effectiveStatus === 'started' || 
               effectiveStatus === 'launching' || effectiveStatus === 'polling') {
      // In-progress wave: base progress (0.1) + server launch progress (0.9)
      const servers = w.serverExecutions || [];
      const baseProgress = 0.1; // Wave started = 10% of wave progress
      
      if (servers.length > 0) {
        const launchedServers = servers.filter(s => {
          const status = (s.launchStatus || s.status || '').toUpperCase();
          return status === 'LAUNCHED';
        }).length;
        // Server progress contributes remaining 90% of wave progress
        const serverProgress = (launchedServers / servers.length) * 0.9;
        totalProgress += baseProgress + serverProgress;
      } else {
        // No servers yet, count as base progress
        totalProgress += baseProgress;
      }
    }
    // Pending waves contribute 0
  });
  
  // Count fully completed waves for display
  const completed = waves.filter(w => {
    const effectiveStatus = getEffectiveWaveStatus(w, jobLogs);
    return effectiveStatus === 'completed' || effectiveStatus === 'launched';
  }).length;
  
  const percentage = Math.round((totalProgress / total) * 100);
  
  return { percentage, completed, total };
};

/**
 * Create server table column definitions with wave context for consistent status display
 */
const createServerColumnDefinitions = (wave: WaveExecution, jobLogs?: JobLogsResponse | null) => [
  {
    id: 'serverId',
    header: 'Server ID',
    cell: (server: ServerExecution) => (
      <Box>
        <div style={{ 
          fontFamily: 'monospace', 
          fontSize: '14px',
          fontWeight: 500,
          color: '#232f3e'
        }}>
          {server.serverName || server.hostname || server.serverId}
        </div>
        {server.hostname && server.serverName && server.hostname !== server.serverName && (
          <div style={{ 
            fontSize: '12px', 
            color: '#5f6b7a',
            fontFamily: 'monospace'
          }}>
            {server.hostname}
          </div>
        )}
      </Box>
    ),
    width: 180,
    minWidth: 180,
  },
  {
    id: 'status',
    header: 'Status',
    cell: (server: ServerExecution) => {
      const waveEffectiveStatus = getEffectiveWaveStatus(wave, jobLogs);
      const serverStatus = server.launchStatus || server.status || 'pending';
      
      // CRITICAL FIX: If wave is completed, ALL servers should show completed status
      // This ensures consistent UI when wave is done, regardless of individual server status data inconsistencies
      let displayStatus = '';
      let badgeColor: 'blue' | 'green' | 'red' | 'grey' = 'grey';
      
      if (waveEffectiveStatus === 'completed') {
        // Wave is completed - force all servers to show completed status for consistency
        displayStatus = '✓';
        badgeColor = 'green';
      } else {
        // Wave not completed - use individual server status
        switch (serverStatus.toUpperCase()) {
          case 'COMPLETED':
          case 'LAUNCHED':
            displayStatus = '✓';
            badgeColor = 'green';
            break;
          case 'FAILED':
          case 'ERROR':
            displayStatus = '✗';
            badgeColor = 'red';
            break;
          case 'IN_PROGRESS':
          case 'LAUNCHING':
          case 'POLLING':
            displayStatus = '⟳';
            badgeColor = 'blue';
            break;
          case 'PENDING':
            displayStatus = '⏳';
            badgeColor = 'grey';
            break;
          case 'STARTED':
            displayStatus = 'Started';
            badgeColor = 'blue';
            break;
          default:
            // Show full status for unknown cases instead of truncating
            displayStatus = serverStatus.charAt(0).toUpperCase() + serverStatus.slice(1).toLowerCase();
            badgeColor = 'grey';
        }
      }
      
      return (
        <Badge color={badgeColor}>
          {displayStatus}
        </Badge>
      );
    },
    width: 100,
    minWidth: 100,
  },
  {
    id: 'instanceId',
    header: 'Instance ID',
    cell: (server: ServerExecution) => {
      const instanceId = server.recoveredInstanceId;
      const region = server.region || 'us-east-1';
      
      if (instanceId) {
        return (
          <Link 
            href={getConsoleLink(instanceId, region)} 
            external
            fontSize="body-s"
          >
            <span style={{ 
              fontFamily: 'monospace',
              fontSize: '13px',
              color: '#0972d3'
            }}>
              {instanceId}
            </span>
          </Link>
        );
      }
      
      const status = (server.launchStatus || server.status || '').toUpperCase();
      return (
        <span style={{ color: '#5f6b7a', fontSize: '13px' }}>
          {status === 'LAUNCHING' ? 'Launching...' : '—'}
        </span>
      );
    },
    width: 200,
    minWidth: 200,
  },
  {
    id: 'instanceType',
    header: 'Type',
    cell: (server: ServerExecution) => (
      <span style={{ 
        fontFamily: 'monospace',
        fontSize: '13px',
        color: server.instanceType ? '#232f3e' : '#5f6b7a',
        fontWeight: server.instanceType ? 500 : 400
      }}>
        {server.instanceType || '—'}
      </span>
    ),
    width: 110,
    minWidth: 110,
  },
  {
    id: 'privateIp',
    header: 'Private IP',
    cell: (server: ServerExecution) => (
      <span style={{ 
        fontFamily: 'monospace',
        fontSize: '13px',
        color: server.privateIp ? '#232f3e' : '#5f6b7a',
        fontWeight: server.privateIp ? 500 : 400
      }}>
        {server.privateIp || '—'}
      </span>
    ),
    width: 130,
    minWidth: 130,
  },
  {
    id: 'launchTime',
    header: 'Launch Time',
    cell: (server: ServerExecution) => {
      const serverWithTimestamp = server as ServerExecution & { launchTime?: number; startTime?: number };
      const timestamp = serverWithTimestamp.launchTime || serverWithTimestamp.startTime;
      const formattedTime = formatTimestamp(timestamp);
      
      return (
        <span style={{ 
          fontSize: '13px',
          color: formattedTime !== '-' ? '#232f3e' : '#5f6b7a'
        }}>
          {formattedTime === '-' ? '—' : formattedTime}
        </span>
      );
    },
    width: 180,
    minWidth: 180,
  },
];

/**
 * Wave Progress Component
 * 
 * Pure display component - no internal polling or API calls.
 */
export const WaveProgress: React.FC<WaveProgressProps> = ({ 
  waves, 
  currentWave, 
  totalWaves,
  jobLogs 
}) => {
  // Separate expansion states for servers and job events (working pattern from fe68d5a)
  const [expandedServers, setExpandedServers] = useState<Set<number>>(
    new Set(currentWave !== undefined ? [currentWave] : [0])
  );
  const [expandedJobEvents, setExpandedJobEvents] = useState<Set<number>>(
    new Set(currentWave !== undefined ? [currentWave] : [0])
  );
  
  // State for staging job logs
  const [stagingJobLogs, setStagingJobLogs] = useState<StagingJobLogs>({});
  const [loadingStagingJobs, setLoadingStagingJobs] = useState<Set<string>>(new Set());

  // Fetch staging job logs when waves with staging jobs are detected
  useEffect(() => {
    const fetchStagingJobLogs = async () => {
      if (!jobLogs) return;
      
      for (const wave of waves) {
        const stagingJobs = (wave as any).DRSJobDetails?.stagingJobs as StagingJobDetails[] | undefined;
        
        if (stagingJobs && stagingJobs.length > 0) {
          for (const stagingJob of stagingJobs) {
            const jobId = stagingJob.jobId;
            
            // Skip if already loaded or loading
            if (stagingJobLogs[jobId] || loadingStagingJobs.has(jobId)) {
              continue;
            }
            
            // Mark as loading
            setLoadingStagingJobs(prev => new Set([...prev, jobId]));
            
            try {
              // Fetch job logs for this staging job
              const executionId = jobLogs.executionId;
              const response = await apiClient.getJobLogs(executionId, jobId);
              
              // Extract events from the response
              const jobLog = response.jobLogs?.find(log => log.jobId === jobId);
              if (jobLog) {
                setStagingJobLogs(prev => ({
                  ...prev,
                  [jobId]: jobLog.events
                }));
              }
            } catch (error) {
              console.error(`Failed to fetch staging job logs for ${jobId}:`, error);
            } finally {
              // Remove from loading set
              setLoadingStagingJobs(prev => {
                const next = new Set(prev);
                next.delete(jobId);
                return next;
              });
            }
          }
        }
      }
    };
    
    fetchStagingJobLogs();
  }, [waves, jobLogs]); // Re-run when waves or jobLogs change

  const progress = calculateProgress(waves, totalWaves, jobLogs);
  
  return (
    <SpaceBetween size="m">
      {/* Overall Progress Bar */}
      {waves && waves.length > 0 && (
        <Box>
          <ProgressBar
            value={progress.percentage}
            label="Overall Progress"
            description={`${progress.completed} of ${progress.total} waves completed`}
            status={progress.percentage === 100 ? 'success' : 'in-progress'}
          />
        </Box>
      )}
      
      {/* Wave List */}
      {(waves || []).map((wave, index) => {
        const waveNum = wave.waveNumber ?? index;
        const displayNum = waveNum + 1;
        const isCurrent = currentWave === waveNum;
        const isServersExpanded = expandedServers.has(waveNum);
        const isJobEventsExpanded = expandedJobEvents.has(waveNum);
        const hasServers = wave.serverExecutions && wave.serverExecutions.length > 0;
        
        // Use effective status that considers server statuses and job logs
        const effectiveStatus = getEffectiveWaveStatus(wave, jobLogs);
        const statusIndicator = getWaveStatusIndicator(effectiveStatus);
        const statusColor = getStatusColor(effectiveStatus);
        const duration = calculateWaveDuration(wave);
        
        return (
          <Container key={waveNum}>
            <SpaceBetween size="s">
              {/* Wave Header */}
              <div 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '16px',
                  cursor: hasServers ? 'pointer' : 'default',
                  padding: '12px 0',
                  borderBottom: '1px solid #e9ebed'
                }}
                onClick={() => {
                  if (hasServers) {
                    setExpandedServers(prev => {
                      const next = new Set(prev);
                      if (next.has(waveNum)) {
                        next.delete(waveNum);
                      } else {
                        next.add(waveNum);
                      }
                      return next;
                    });
                  }
                }}
              >
                <span style={{ fontSize: '28px', color: statusColor, lineHeight: 1 }}>
                  {statusIndicator}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ 
                    fontWeight: 600, 
                    fontSize: '18px',
                    color: '#232f3e',
                    lineHeight: 1.3
                  }}>
                    Wave {displayNum}: {wave.waveName || `Wave ${displayNum}`}
                  </div>
                  <div style={{ 
                    fontSize: '13px', 
                    color: '#5f6b7a', 
                    marginTop: '4px',
                    lineHeight: 1.4
                  }}>
                    {wave.startTime ? (
                      <>
                        Started {formatRelativeTime(wave.startTime)}
                        <span style={{ margin: '0 8px', color: '#d5dbdb' }}>•</span>
                        Duration: {duration}
                        {wave.jobId && (
                          <>
                            <span style={{ margin: '0 8px', color: '#d5dbdb' }}>•</span>
                            Job: <code style={{ 
                              fontSize: '12px',
                              backgroundColor: '#f2f3f3',
                              padding: '2px 4px',
                              borderRadius: '3px',
                              color: '#232f3e'
                            }}>{wave.jobId}</code>
                          </>
                        )}
                      </>
                    ) : (
                      'Not started'
                    )}
                  </div>
                </div>
                <div style={{ marginLeft: '12px' }}>
                  <StatusBadge status={effectiveStatus} />
                </div>
              </div>

              {/* Wave Error */}
              {wave.error && (
                <Alert type="error">
                  {typeof wave.error === 'string' ? wave.error : wave.error.message}
                </Alert>
              )}

              {/* Wave Status Message (from backend reconciliation) */}
              {!wave.error && wave.statusMessage && effectiveStatus === 'failed' && (
                <Alert type="error" header="Wave Failure">
                  {wave.statusMessage}
                </Alert>
              )}

              {/* DRS Job Status Message (for failed/problematic jobs) */}
              {!wave.error && !wave.statusMessage && (wave as any).DRSJobDetails?.statusMessage && effectiveStatus === 'failed' && (
                <Alert type="error" header="DRS Job Failure">
                  {(wave as any).DRSJobDetails.statusMessage}
                </Alert>
              )}

              {/* Servers Table - Expandable */}
              {hasServers && (
                <ExpandableSection
                  headerText={`Servers (${wave.serverExecutions.length})`}
                  variant="footer"
                  expanded={isServersExpanded || isCurrent}
                  onChange={({ detail }) => {
                    if (detail.expanded) {
                      setExpandedServers(prev => new Set([...prev, waveNum]));
                    } else {
                      setExpandedServers(prev => {
                        const next = new Set(prev);
                        next.delete(waveNum);
                        return next;
                      });
                    }
                  }}
                >
                  <Table
                    columnDefinitions={createServerColumnDefinitions(wave, jobLogs)}
                    items={wave.serverExecutions}
                    variant="embedded"
                    stripedRows
                    contentDensity="comfortable"
                    empty={
                      <Box textAlign="center" color="inherit" padding="l">
                        <div style={{ color: '#5f6b7a' }}>No servers in this wave</div>
                      </Box>
                    }
                    header={
                      <div style={{ 
                        fontSize: '14px', 
                        fontWeight: 500, 
                        color: '#232f3e',
                        padding: '8px 0'
                      }}>
                        {wave.serverExecutions.length} server{wave.serverExecutions.length !== 1 ? 's' : ''}
                      </div>
                    }
                  />
                  
                  {/* Server Errors */}
                  {wave.serverExecutions.some(s => s.error) && (
                    <SpaceBetween size="xs">
                      {wave.serverExecutions
                        .filter(s => s.error)
                        .map((server) => (
                          <Alert type="error" key={server.serverId}>
                            <strong>{server.serverName || server.serverId}:</strong>{' '}
                            {typeof server.error === 'string' 
                              ? server.error 
                              : server.error?.message || 'Unknown error'}
                          </Alert>
                        ))}
                    </SpaceBetween>
                  )}
                </ExpandableSection>
              )}

              {/* Enhanced DRS Job Events Timeline - Multi-Phase Support for Extended Source Servers */}
              {wave.jobId && jobLogs && (
                <ExpandableSection
                  headerText="DRS Job Events"
                  variant="footer"
                  expanded={isJobEventsExpanded || isCurrent}
                  onChange={({ detail }) => {
                    if (detail.expanded) {
                      setExpandedJobEvents(prev => new Set([...prev, waveNum]));
                    } else {
                      setExpandedJobEvents(prev => {
                        const next = new Set(prev);
                        next.delete(waveNum);
                        return next;
                      });
                    }
                  }}
                >
                  {(() => {
                    const waveJobLogs = getWaveJobLogs(jobLogs, waveNum);
                    const stagingJobs = (wave as any).DRSJobDetails?.stagingJobs as StagingJobDetails[] | undefined;
                    const hasStagingJobs = stagingJobs && stagingJobs.length > 0;
                    
                    if (waveJobLogs.length === 0 && !hasStagingJobs) {
                      return (
                        <Box textAlign="center" color="inherit" padding="m">
                          <div style={{ color: '#5f6b7a' }}>
                            No DRS job events available yet
                          </div>
                          {wave.jobId && (
                            <div style={{ fontSize: '12px', color: '#5f6b7a', marginTop: '4px' }}>
                              Job ID: <code>{wave.jobId}</code>
                            </div>
                          )}
                        </Box>
                      );
                    }

                    return (
                      <SpaceBetween size="l">
                        {/* Phase 1: Staging Account Conversion (Extended Source Servers Only) */}
                        {hasStagingJobs && stagingJobs.map((stagingJob, idx) => {
                          const stagingEvents = stagingJobLogs[stagingJob.jobId] || [];
                          const isLoading = loadingStagingJobs.has(stagingJob.jobId);
                          
                          // Filter target account events to exclude extended server events
                          const extendedServerIds = new Set(stagingJob.serverIds);
                          
                          return (
                            <Container
                              key={stagingJob.jobId}
                              header={
                                <Box>
                                  <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                                    Phase 1: Staging Account Conversion
                                  </div>
                                  <div style={{ fontSize: '12px', color: '#5f6b7a' }}>
                                    Job ID: <code>{stagingJob.jobId}</code> • 
                                    Staging Account: <code>{stagingJob.stagingAccountId}</code> • 
                                    {stagingJob.participatingServers} server{stagingJob.participatingServers !== 1 ? 's' : ''}
                                    {stagingJob.status && (
                                      <span> • Status: <Badge color={stagingJob.status === 'COMPLETED' ? 'green' : 'blue'}>
                                        {stagingJob.status}
                                      </Badge></span>
                                    )}
                                  </div>
                                </Box>
                              }
                            >
                              {isLoading ? (
                                <Box textAlign="center" padding="m">
                                  <div style={{ color: '#5f6b7a' }}>Loading staging job events...</div>
                                </Box>
                              ) : stagingEvents.length === 0 ? (
                                <Box textAlign="center" padding="m">
                                  <div style={{ color: '#5f6b7a' }}>No staging job events available</div>
                                </Box>
                              ) : (
                                <SpaceBetween size="s">
                                  {stagingEvents.map((event, eventIdx) => (
                                    <Box key={eventIdx} padding="s">
                                      <div style={{ fontWeight: 500 }}>
                                        {formatJobLogEvent(event)}
                                      </div>
                                      <div style={{ fontSize: '12px', color: '#5f6b7a', marginTop: '2px' }}>
                                        {formatTimestamp(event.logDateTime)}
                                        {event.sourceServerId && (
                                          <span> • Server: <code style={{ fontSize: '11px' }}>{event.sourceServerId}</code></span>
                                        )}
                                        {event.conversionServerId && (
                                          <span> • Conversion: <code style={{ fontSize: '11px' }}>{event.conversionServerId}</code></span>
                                        )}
                                      </div>
                                      {event.error && (
                                        <Alert type="error" header="Event Error" dismissible={false}>
                                          {event.error}
                                        </Alert>
                                      )}
                                      {event.eventData && Object.keys(event.eventData).length > 0 && (
                                        <details style={{ marginTop: '8px' }}>
                                          <summary style={{ fontSize: '12px', color: '#5f6b7a', cursor: 'pointer' }}>
                                            Event Details
                                          </summary>
                                          <pre style={{ 
                                            fontSize: '11px', 
                                            color: '#5f6b7a', 
                                            marginTop: '4px',
                                            whiteSpace: 'pre-wrap',
                                            wordBreak: 'break-word'
                                          }}>
                                            {JSON.stringify(event.eventData, null, 2)}
                                          </pre>
                                        </details>
                                      )}
                                    </Box>
                                  ))}
                                </SpaceBetween>
                              )}
                            </Container>
                          );
                        })}

                        {/* Phase 2: Target Account Recovery (All Servers) */}
                        <Container
                          header={
                            <Box>
                              <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                                {hasStagingJobs ? 'Phase 2: Target Account Recovery' : 'DRS Job Events'}
                              </div>
                              <div style={{ fontSize: '12px', color: '#5f6b7a' }}>
                                Job ID: <code>{wave.jobId}</code> • {waveJobLogs.length} events
                              </div>
                            </Box>
                          }
                        >
                          {waveJobLogs.length === 0 ? (
                            <Box textAlign="center" padding="m">
                              <div style={{ color: '#5f6b7a' }}>No target account events available</div>
                            </Box>
                          ) : (
                            <SpaceBetween size="s">
                              {waveJobLogs.map((event, eventIdx) => {
                                // For extended servers, filter out conversion events (they're in staging phase)
                                const extendedServerIds = new Set(
                                  stagingJobs?.flatMap(sj => sj.serverIds) || []
                                );
                                const isExtendedServer = event.sourceServerId && extendedServerIds.has(event.sourceServerId);
                                const isConversionEvent = event.event?.includes('CONVERSION') || 
                                                         event.event?.includes('SNAPSHOT');
                                
                                // Skip conversion events for extended servers (shown in staging phase)
                                if (isExtendedServer && isConversionEvent) {
                                  return null;
                                }
                                
                                return (
                                  <Box key={eventIdx} padding="s">
                                    <div style={{ fontWeight: 500 }}>
                                      {formatJobLogEvent(event)}
                                    </div>
                                    <div style={{ fontSize: '12px', color: '#5f6b7a', marginTop: '2px' }}>
                                      {formatTimestamp(event.logDateTime)}
                                      {event.sourceServerId && (
                                        <span> • Server: <code style={{ fontSize: '11px' }}>{event.sourceServerId}</code></span>
                                      )}
                                      {event.conversionServerId && (
                                        <span> • Conversion: <code style={{ fontSize: '11px' }}>{event.conversionServerId}</code></span>
                                      )}
                                    </div>
                                    {event.error && (
                                      <Alert type="error" header="Event Error" dismissible={false}>
                                        {event.error}
                                      </Alert>
                                    )}
                                    {event.eventData && Object.keys(event.eventData).length > 0 && (
                                      <details style={{ marginTop: '8px' }}>
                                        <summary style={{ fontSize: '12px', color: '#5f6b7a', cursor: 'pointer' }}>
                                          Event Details
                                        </summary>
                                        <pre style={{ 
                                          fontSize: '11px', 
                                          color: '#5f6b7a', 
                                          marginTop: '4px',
                                          whiteSpace: 'pre-wrap',
                                          wordBreak: 'break-word'
                                        }}>
                                          {JSON.stringify(event.eventData, null, 2)}
                                        </pre>
                                      </details>
                                    )}
                                  </Box>
                                );
                              }).filter(Boolean)}
                            </SpaceBetween>
                          )}
                        </Container>
                      </SpaceBetween>
                    );
                  })()}
                </ExpandableSection>
              )}
            </SpaceBetween>
          </Container>
        );
      })}
      
      {/* Empty State */}
      {(!waves || waves.length === 0) && (
        <Box textAlign="center" color="text-body-secondary" padding="l">
          No wave data available
        </Box>
      )}
    </SpaceBetween>
  );
};
