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
  
  // 1. Check explicit wave status first
  if (['completed', 'failed', 'cancelled'].includes(waveStatus)) {
    return waveStatus;
  }
  
  // 2. Check if wave has endTime (authoritative completion signal)
  if (wave.endTime) {
    // Verify all servers are in terminal state
    const servers = wave.serverExecutions || [];
    const allServersTerminal = servers.every(s => {
      const status = (s.launchStatus || s.status || '').toUpperCase();
      return ['LAUNCHED', 'FAILED', 'TERMINATED'].includes(status);
    });
    
    if (allServersTerminal) {
      // Check if any failed
      const anyFailed = servers.some(s => {
        const status = (s.launchStatus || s.status || '').toUpperCase();
        return status === 'FAILED';
      });
      
      return anyFailed ? 'failed' : 'completed';
    }
  }
  
  // 3. Check if all servers launched successfully
  const servers = wave.serverExecutions || [];
  if (servers.length > 0) {
    const allLaunched = servers.every(s => {
      const status = (s.launchStatus || s.status || '').toUpperCase();
      return status === 'LAUNCHED';
    });
    
    if (allLaunched) {
      return 'completed';
    }
    
    // 4. Check for failures
    // Only check for failures if servers have actually started launching
    // During early phases (cleanup, snapshot, conversion), servers won't have launch status yet
    const serversWithStatus = servers.filter(s => s.launchStatus || s.status);
    const anyFailed = serversWithStatus.length > 0 && serversWithStatus.some(s => {
      const status = (s.launchStatus || s.status || '').toUpperCase();
      return status === 'FAILED';
    });
    
    if (anyFailed) {
      return 'failed';
    }
    
    // 5. Check job logs for completion (if available)
    if (jobLogs && wave.jobId) {
      const waveLog = jobLogs.jobLogs?.find(log => log.jobId === wave.jobId);
      if (waveLog) {
        const jobEndEvents = waveLog.events.filter(e => e.event === 'JOB_END');
        const launchEndEvents = waveLog.events.filter(e => e.event === 'LAUNCH_END');
        
        // JOB_END is authoritative completion signal
        if (jobEndEvents.length > 0) {
          return 'completed';
        }
        
        // LAUNCH_END for all servers also indicates completion
        if (launchEndEvents.length === servers.length && servers.length > 0) {
          return 'completed';
        }
      }
    }
    
    // 6. Check for in-progress
    const anyInProgress = servers.some(s => {
      const status = (s.launchStatus || s.status || '').toUpperCase();
      return ['IN_PROGRESS', 'LAUNCHING', 'PENDING_LAUNCH', 'PENDING'].includes(status);
    });
    
    if (anyInProgress) {
      return 'in_progress';
    }
  }
  
  // 7. Map wave status as fallback
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
 * For completed waves, uses endTime. For in-progress waves, uses current time.
 * 
 * CRITICAL: This function is called on every render due to parent timer.
 * We MUST return a stable value for completed waves to prevent continuous updates.
 */
const calculateWaveDuration = (wave: WaveExecution, effectiveStatus?: string): string => {
  if (!wave.startTime) return '-';
  
  const start = parseTimestamp(wave.startTime);
  if (!start) return '-';
  
  // For completed waves, MUST use endTime to freeze the duration
  // For in-progress waves, use current time for live updates
  const isCompleted = effectiveStatus === 'completed' || effectiveStatus === 'launched';
  
  // CRITICAL: Always use endTime if available for completed waves
  let end: Date;
  if (isCompleted && wave.endTime) {
    end = parseTimestamp(wave.endTime)!;
  } else {
    end = new Date();
  }
  
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
 * Get server progress from DRS job log events
 * Maps DRS recovery phases to progress percentages:
 * - SNAPSHOT phase: 0-25%
 * - CONVERSION phase: 25-50%
 * - LAUNCH phase: 50-100%
 */
const getServerProgressFromJobLogs = (
  serverId: string,
  waveNumber: number,
  jobLogs?: JobLogsResponse | null
): number => {
  if (!jobLogs || !jobLogs.jobLogs) return 0;
  
  const waveLog = jobLogs.jobLogs.find(log => log.waveNumber === waveNumber);
  if (!waveLog) return 0;
  
  // Find all events for this server, sorted by time (most recent first)
  const serverEvents = waveLog.events
    .filter(e => {
      const eventData = e.eventData as { sourceServerID?: string } | undefined;
      return eventData?.sourceServerID === serverId;
    })
    .sort((a, b) => {
      const timeA = new Date(a.logDateTime).getTime();
      const timeB = new Date(b.logDateTime).getTime();
      return timeB - timeA; // Most recent first
    });
  
  if (serverEvents.length === 0) return 0;
  
  // Map most recent event to progress percentage
  const latestEvent = serverEvents[0].event;
  switch (latestEvent) {
    case 'LAUNCH_END':
      return 1.0; // 100% - server fully launched
    case 'LAUNCH_START':
      return 0.75; // 75% - launching
    case 'CONVERSION_END':
      return 0.5; // 50% - conversion complete
    case 'CONVERSION_START':
      return 0.375; // 37.5% - converting
    case 'SNAPSHOT_END':
      return 0.25; // 25% - snapshot complete
    case 'SNAPSHOT_START':
    case 'USING_PREVIOUS_SNAPSHOT':
      return 0.125; // 12.5% - snapshotting
    case 'CLEANUP_START':
    case 'CLEANUP_END':
      return 0.05; // 5% - cleanup phase
    default:
      return 0;
  }
};

/**
 * Calculate overall progress with granular server-level tracking using DRS job events
 * 
 * Progress calculation:
 * - Completed waves: 1.0 each
 * - In-progress waves: average of all server progress (from job log events)
 * - Pending waves: 0
 * 
 * Server progress from DRS events:
 * - SNAPSHOT phase: 0-25%
 * - CONVERSION phase: 25-50%
 * - LAUNCH phase: 50-100%
 * 
 * Example with 3 waves, wave 1 has 4 servers:
 * - Wave started, cleanup: 1-2%
 * - Server 1 SNAPSHOT_START: 4%
 * - Server 1 SNAPSHOT_END: 8%
 * - Server 1 CONVERSION_START: 12%
 * - Server 1 CONVERSION_END: 17%
 * - Server 1 LAUNCH_START: 25%
 * - Server 1 LAUNCH_END: 33%
 * - All 4 servers LAUNCH_END: 100% (wave complete)
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
      // In-progress wave: calculate based on server progress from job logs
      const servers = w.serverExecutions || [];
      const waveNum = w.waveNumber ?? 0;
      
      if (servers.length > 0) {
        let waveProgress = 0;
        
        servers.forEach(server => {
          // Try to get progress from job logs first
          const jobLogProgress = getServerProgressFromJobLogs(server.serverId, waveNum, jobLogs);
          
          if (jobLogProgress > 0) {
            // Use job log event progress (0.0 to 1.0)
            waveProgress += jobLogProgress;
          } else {
            // Fallback to launchStatus if no job log events
            const status = (server.launchStatus || server.status || '').toUpperCase();
            if (status === 'LAUNCHED') {
              waveProgress += 1.0;
            } else if (['IN_PROGRESS', 'LAUNCHING', 'PENDING_LAUNCH'].includes(status)) {
              // Server is actively launching but not complete yet - count as 50% progress
              waveProgress += 0.5;
            }
            // PENDING servers contribute 0
          }
        });
        
        // Average server progress for this wave
        totalProgress += waveProgress / servers.length;
      } else {
        // No servers yet, but wave started - count as minimal progress
        totalProgress += 0.1;
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
 * Get server's current status from job log events
 * Returns the most recent event type for the server to show actual progress
 */
const getServerStatusFromJobLogs = (
  serverId: string,
  waveNumber: number,
  jobLogs?: JobLogsResponse | null
): string | null => {
  if (!jobLogs || !jobLogs.jobLogs) return null;
  
  const waveLog = jobLogs.jobLogs.find(log => log.waveNumber === waveNumber);
  if (!waveLog) return null;
  
  // Find all events for this server, sorted by time (most recent first)
  const serverEvents = waveLog.events
    .filter(e => {
      const eventData = e.eventData as { sourceServerID?: string } | undefined;
      return eventData?.sourceServerID === serverId;
    })
    .sort((a, b) => {
      const timeA = new Date(a.logDateTime).getTime();
      const timeB = new Date(b.logDateTime).getTime();
      return timeB - timeA; // Most recent first
    });
  
  if (serverEvents.length === 0) return null;
  
  // Return the most recent event type
  const latestEvent = serverEvents[0];
  return latestEvent.event;
};

/**
 * Map DRS job event to display status
 */
const mapEventToStatus = (event: string): { status: string; icon: string; color: 'blue' | 'green' | 'red' | 'grey' } => {
  switch (event) {
    case 'LAUNCH_END':
      return { status: 'Launched', icon: '✓', color: 'green' };
    case 'LAUNCH_START':
      return { status: 'Launching', icon: '🚀', color: 'blue' };
    case 'CONVERSION_END':
      return { status: 'Converted', icon: '✓', color: 'green' };
    case 'CONVERSION_START':
      return { status: 'Converting', icon: '🔄', color: 'blue' };
    case 'SNAPSHOT_END':
      return { status: 'Snapshot Done', icon: '✓', color: 'green' };
    case 'SNAPSHOT_START':
      return { status: 'Snapshotting', icon: '📸', color: 'blue' };
    case 'CLEANUP_END':
      return { status: 'Cleanup Done', icon: '✓', color: 'green' };
    case 'CLEANUP_START':
      return { status: 'Cleaning', icon: '🧹', color: 'blue' };
    case 'USING_PREVIOUS_SNAPSHOT':
      return { status: 'Using Snapshot', icon: '📋', color: 'blue' };
    case 'JOB_START':
      return { status: 'Started', icon: '▶️', color: 'blue' };
    default:
      return { status: 'Pending', icon: '⏳', color: 'grey' };
  }
};

/**
 * Create server table column definitions with wave context for consistent status display
 */
const createServerColumnDefinitions = (wave: WaveExecution, jobLogs?: JobLogsResponse | null) => [
  {
    id: 'serverId',
    header: 'Server Name',
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
      const waveNum = wave.waveNumber ?? 0;
      
      // CRITICAL FIX: Check job log events FIRST for actual current status
      const latestEvent = getServerStatusFromJobLogs(server.serverId, waveNum, jobLogs);
      
      let displayStatus = '';
      let badgeColor: 'blue' | 'green' | 'red' | 'grey' = 'grey';
      
      if (waveEffectiveStatus === 'completed') {
        // Wave is completed - force all servers to show completed status for consistency
        displayStatus = '✓';
        badgeColor = 'green';
      } else {
        // Use launchStatus from DRS API (standard DRS status values)
        const serverStatus = server.status || server.launchStatus || 'pending';
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
            // Show full status for unknown cases
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
      
      // Check server status to provide appropriate feedback
      const status = (server.launchStatus || server.status || '').toUpperCase();
      
      // Check if server is still launching
      if (status === 'PENDING' || status === 'IN_PROGRESS' || status === 'LAUNCHING') {
        return (
          <span style={{ color: '#5f6b7a', fontSize: '13px' }}>
            Launching...
          </span>
        );
      }
      
      // Check if server failed
      if (status === 'FAILED' || status === 'ERROR') {
        return (
          <span style={{ color: '#d13212', fontSize: '13px' }}>
            Launch failed
          </span>
        );
      }
      
      return (
        <span style={{ color: '#5f6b7a', fontSize: '13px' }} title="Instance ID not available">
          —
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
 * Log EC2 data availability for debugging (only when data is missing)
 * REMOVED: This was causing console spam due to parent component re-rendering every second
 */
const logEC2DataAvailability = (wave: WaveExecution) => {
  // Logging removed to prevent console spam
  // EC2 data availability can be checked by inspecting the table directly
};

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
  
  // Cache completed wave durations to prevent recalculation on every render
  // Key: waveNumber, Value: frozen duration string
  const [completedWaveDurations, setCompletedWaveDurations] = useState<Map<number, string>>(new Map());

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
  
  // Update completed wave durations cache when waves complete
  React.useEffect(() => {
    const newCompletedDurations = new Map(completedWaveDurations);
    let hasChanges = false;
    
    for (const wave of waves) {
      const waveNum = wave.waveNumber ?? 0;
      const effectiveStatus = getEffectiveWaveStatus(wave, jobLogs);
      const isCompleted = effectiveStatus === 'completed' || effectiveStatus === 'launched';
      
      // If wave is completed and we don't have a cached duration, calculate and cache it
      if (isCompleted && wave.endTime && !newCompletedDurations.has(waveNum)) {
        const duration = calculateWaveDuration(wave, effectiveStatus);
        newCompletedDurations.set(waveNum, duration);
        hasChanges = true;
      }
    }
    
    if (hasChanges) {
      setCompletedWaveDurations(newCompletedDurations);
    }
  }, [waves, jobLogs, completedWaveDurations]);
  
  // Filter waves to only show up to current wave (don't show future waves)
  const visibleWaves = React.useMemo(() => {
    if (!waves || waves.length === 0) return [];
    
    // If currentWave is defined, only show waves up to and including current wave
    if (currentWave !== undefined) {
      return waves.filter(wave => {
        const waveNum = wave.waveNumber ?? 0;
        return waveNum <= currentWave;
      });
    }
    
    // If no currentWave specified, show all waves (backward compatibility)
    return waves;
  }, [waves, currentWave]);
  
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
      {visibleWaves.map((wave, index) => {
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
        
        // Use cached duration for completed waves, calculate live for in-progress
        const isCompleted = effectiveStatus === 'completed' || effectiveStatus === 'launched';
        const duration = isCompleted && completedWaveDurations.has(waveNum)
          ? completedWaveDurations.get(waveNum)!
          : calculateWaveDuration(wave, effectiveStatus);
        
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
                        Started {effectiveStatus === 'completed' || effectiveStatus === 'launched' 
                          ? formatTimestamp(wave.startTime)
                          : formatRelativeTime(wave.startTime)}
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
                  {/* Log EC2 data availability for debugging */}
                  {(() => {
                    logEC2DataAvailability(wave);
                    return null;
                  })()}
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

              {/* DRS Job Events Timeline - Unified View */}
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
                    
                    // Combine all events from all jobs (staging + target) into unified timeline
                    const allEvents: Array<JobLogEvent & { jobId: string; accountId: string; accountName?: string; jobType: string }> = [];
                    
                    // Add target account job events
                    const targetAccountId = (wave as any).DRSJobDetails?.targetAccountId;
                    const targetAccountName = (wave as any).DRSJobDetails?.targetAccountName;
                    waveJobLogs.forEach(event => {
                      allEvents.push({
                        ...event,
                        jobId: wave.jobId!,
                        accountId: targetAccountId || 'unknown',
                        accountName: targetAccountName,  // undefined if not provided - display logic will handle
                        jobType: 'LAUNCH'
                      });
                    });
                    
                    // Add staging account job events
                    if (hasStagingJobs) {
                      for (const stagingJob of stagingJobs) {
                        const events = stagingJobLogs[stagingJob.jobId] || [];
                        events.forEach(event => {
                          allEvents.push({
                            ...event,
                            jobId: stagingJob.jobId,
                            accountId: stagingJob.stagingAccountId,
                            jobType: stagingJob.type
                          });
                        });
                      }
                    }
                    
                    // Sort all events by timestamp (newest first)
                    allEvents.sort((a, b) => {
                      const timeA = new Date(a.logDateTime).getTime();
                      const timeB = new Date(b.logDateTime).getTime();
                      return timeB - timeA;
                    });
                    
                    // Group events that occur at the same time with the same event type
                    // This matches DRS Console behavior where events for multiple servers are combined
                    interface GroupedEvent {
                      event: string;
                      logDateTime: string;
                      jobId: string;
                      accountId: string;
                      accountName?: string;
                      jobType: string;
                      servers: Array<{
                        sourceServerId?: string;
                        conversionServerId?: string;
                        eventData?: any;
                        error?: string;
                      }>;
                      count: number;
                    }
                    
                    const groupedEvents: GroupedEvent[] = [];
                    const TIME_THRESHOLD_MS = 5000; // Group events within 5 seconds
                    
                    for (const event of allEvents) {
                      // Try to find an existing group for this event
                      const existingGroup = groupedEvents.find(g => {
                        const timeDiff = Math.abs(
                          new Date(g.logDateTime).getTime() - new Date(event.logDateTime).getTime()
                        );
                        return (
                          g.event === event.event &&
                          g.jobId === event.jobId &&
                          g.accountId === event.accountId &&
                          timeDiff <= TIME_THRESHOLD_MS
                        );
                      });
                      
                      if (existingGroup) {
                        // Add to existing group
                        existingGroup.servers.push({
                          sourceServerId: event.sourceServerId,
                          conversionServerId: event.conversionServerId,
                          eventData: event.eventData,
                          error: event.error,
                        });
                        existingGroup.count++;
                      } else {
                        // Create new group
                        groupedEvents.push({
                          event: event.event,
                          logDateTime: event.logDateTime,
                          jobId: event.jobId,
                          accountId: event.accountId,
                          accountName: event.accountName,
                          jobType: event.jobType,
                          servers: [{
                            sourceServerId: event.sourceServerId,
                            conversionServerId: event.conversionServerId,
                            eventData: event.eventData,
                            error: event.error,
                          }],
                          count: 1,
                        });
                      }
                    }
                    
                    const anyLoading = hasStagingJobs && stagingJobs.some(sj => loadingStagingJobs.has(sj.jobId));
                    const totalJobs = 1 + (stagingJobs?.length || 0);
                    
                    if (groupedEvents.length === 0 && !anyLoading) {
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
                      <Container
                        header={
                          <Box>
                            <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                              DRS Job Timeline
                            </div>
                            <div style={{ fontSize: '12px', color: '#5f6b7a' }}>
                              {totalJobs} job{totalJobs !== 1 ? 's' : ''} • {groupedEvents.length} events
                              {hasStagingJobs && (
                                <span>
                                  {' • '}
                                  Staging: {stagingJobs.map(sj => sj.jobId).join(', ')}
                                  {' • '}
                                  Target: {wave.jobId}
                                </span>
                              )}
                            </div>
                          </Box>
                        }
                      >
                        {anyLoading ? (
                          <Box textAlign="center" padding="m">
                            <div style={{ color: '#5f6b7a' }}>Loading job events...</div>
                          </Box>
                        ) : (
                          <SpaceBetween size="s">
                            {groupedEvents.map((group, groupIdx) => (
                              <Box key={groupIdx} padding="s">
                                <div style={{ fontWeight: 500 }}>
                                  {formatJobLogEvent({ 
                                    event: group.event,
                                    logDateTime: group.logDateTime,
                                    eventData: group.servers[0].eventData || {},
                                  } as JobLogEvent)}
                                </div>
                                <div style={{ fontSize: '12px', color: '#5f6b7a', marginTop: '2px' }}>
                                  {formatTimestamp(group.logDateTime)}
                                  <span> • Account: {group.accountName ? `${group.accountName} (${group.accountId})` : <code style={{ fontSize: '11px' }}>{group.accountId}</code>}</span>
                                  <span> • Job: <code style={{ fontSize: '11px' }}>{group.jobId}</code></span>
                                  {group.count > 1 && (
                                    <span> • <strong>Servers: {group.count}</strong></span>
                                  )}
                                  {group.count === 1 && group.servers[0].sourceServerId && (
                                    <span> • Server: <code style={{ fontSize: '11px' }}>{group.servers[0].sourceServerId}</code></span>
                                  )}
                                  {group.count === 1 && group.servers[0].conversionServerId && (
                                    <span> • Conversion: <code style={{ fontSize: '11px' }}>{group.servers[0].conversionServerId}</code></span>
                                  )}
                                </div>
                                {group.servers.some(s => s.error) && (
                                  <Alert type="error" header="Event Error" dismissible={false}>
                                    {group.servers.find(s => s.error)?.error}
                                  </Alert>
                                )}
                                {group.count > 1 && (
                                  <details style={{ marginTop: '8px' }}>
                                    <summary style={{ fontSize: '12px', color: '#5f6b7a', cursor: 'pointer' }}>
                                      Server Details
                                    </summary>
                                    <div style={{ marginTop: '4px', paddingLeft: '12px' }}>
                                      {group.servers.map((server, serverIdx) => {
                                        // Find matching server execution to get name, hostname, region
                                        const serverExecution = wave.serverExecutions?.find(
                                          s => s.serverId === server.sourceServerId
                                        );
                                        
                                        return (
                                          <div key={serverIdx} style={{ fontSize: '11px', color: '#232f3e', marginTop: '4px', paddingBottom: '4px', borderBottom: serverIdx < group.servers.length - 1 ? '1px solid #e9ebed' : 'none' }}>
                                            {serverExecution ? (
                                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
                                                {serverExecution.serverName && (
                                                  <span><strong>Name:</strong> {serverExecution.serverName}</span>
                                                )}
                                                <span><strong>Server ID:</strong> <code style={{ fontSize: '10px' }}>{server.sourceServerId}</code></span>
                                                {serverExecution.region && (
                                                  <span><strong>Region:</strong> {serverExecution.region}</span>
                                                )}
                                                {serverExecution.hostname && serverExecution.serverName && serverExecution.hostname !== serverExecution.serverName && (
                                                  <span><strong>Hostname:</strong> {serverExecution.hostname}</span>
                                                )}
                                                {server.conversionServerId && (
                                                  <span><strong>Conversion:</strong> <code style={{ fontSize: '10px' }}>{server.conversionServerId}</code></span>
                                                )}
                                              </div>
                                            ) : (
                                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
                                                {server.sourceServerId && (
                                                  <span><strong>Server:</strong> <code>{server.sourceServerId}</code></span>
                                                )}
                                                {server.conversionServerId && (
                                                  <span><strong>Conversion:</strong> <code>{server.conversionServerId}</code></span>
                                                )}
                                              </div>
                                            )}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </details>
                                )}
                                {group.count === 1 && group.servers[0].eventData && Object.keys(group.servers[0].eventData).length > 0 && (
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
                                      {JSON.stringify(group.servers[0].eventData, null, 2)}
                                    </pre>
                                  </details>
                                )}
                              </Box>
                            ))}
                          </SpaceBetween>
                        )}
                      </Container>
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
