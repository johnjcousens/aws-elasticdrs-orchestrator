/**
 * Wave Progress Component
 * 
 * Displays wave execution timeline using CloudScape components.
 * Shows wave statuses, timing, and server details.
 */

import React, { useEffect, useState, useMemo, useCallback } from 'react';
import {
  Container,
  SpaceBetween,
  Box,
  ExpandableSection,
  Alert,
  Badge,
  ProgressBar,
  Spinner,
} from '@cloudscape-design/components';
import { StatusBadge } from './StatusBadge';
import apiClient from '../services/api';
import type { WaveExecution, ServerExecution } from '../types';

// Job log event type
interface JobLogEvent {
  event: string;
  eventData: Record<string, unknown>;
  logDateTime: string;
  sourceServerId?: string;
  error?: string;
  conversionServerId?: string;
}

interface WaveJobLogs {
  waveNumber: number;
  jobId: string;
  events: JobLogEvent[];
  error?: string;
}

interface WaveProgressProps {
  waves: WaveExecution[];
  currentWave?: number;
  totalWaves?: number;  // Total waves from recovery plan (not just executed waves)
  executionId?: string; // For fetching job logs
  executionStatus?: string; // Execution status (for capping wave duration on cancelled executions)
  executionEndTime?: string | number; // Execution end time (for capping wave duration)
}

/**
 * Format DRS event type to human-readable text
 */
const formatEventType = (event: string): { label: string; icon: string; color: string } => {
  const eventMap: Record<string, { label: string; icon: string; color: string }> = {
    'JOB_START': { label: 'Job Started', icon: '▶', color: '#0972d3' },
    'JOB_END': { label: 'Job Completed', icon: '✓', color: '#037f0c' },
    'JOB_CANCEL': { label: 'Job Cancelled', icon: '⊘', color: '#5f6b7a' },
    'SNAPSHOT_START': { label: 'Taking Snapshot', icon: '◉', color: '#0972d3' },
    'SNAPSHOT_END': { label: 'Snapshot Complete', icon: '✓', color: '#037f0c' },
    'CONVERSION_START': { label: 'Conversion Started', icon: '↻', color: '#0972d3' },
    'CONVERSION_END': { label: 'Conversion Succeeded', icon: '✓', color: '#037f0c' },
    'LAUNCH_START': { label: 'Launching Instance', icon: '↑', color: '#0972d3' },
    'LAUNCH_END': { label: 'Instance Launched', icon: '✓', color: '#037f0c' },
    'CLEANUP_START': { label: 'Cleanup Started', icon: '○', color: '#5f6b7a' },
    'CLEANUP_END': { label: 'Cleanup Complete', icon: '✓', color: '#037f0c' },
    'CLEANUP_FAIL': { label: 'Cleanup Failed', icon: '⚠', color: '#d91515' },
    'USING_PREVIOUS_SNAPSHOT': { label: 'Using Previous Snapshot', icon: 'ℹ', color: '#5f6b7a' },
    'USING_PREVIOUS_SNAPSHOT_CLEANUP_FAILED': { label: 'Previous Snapshot (Cleanup Failed)', icon: '⚠', color: '#d91515' },
  };
  return eventMap[event] || { label: event, icon: '•', color: '#5f6b7a' };
};

/**
 * Job Events Timeline Component
 */
const JobEventsTimeline: React.FC<{ events: JobLogEvent[] }> = ({ events }) => {
  if (!events || events.length === 0) {
    return <Box color="text-status-inactive">No events available</Box>;
  }

  return (
    <div style={{ fontSize: '13px' }}>
      {events.map((event, idx) => {
        const { label, icon, color } = formatEventType(event.event);
        const eventData = event.eventData || {};
        const sourceServer = (eventData.sourceServerID as string) || event.sourceServerId;
        const hostname = eventData.hostname as string;
        const conversionServer = (eventData.conversionServerID as string) || event.conversionServerId;
        const timestamp = event.logDateTime ? new Date(event.logDateTime).toLocaleString() : '';
        
        return (
          <div 
            key={idx} 
            style={{ 
              display: 'flex', 
              gap: '12px', 
              padding: '8px 0',
              borderBottom: idx < events.length - 1 ? '1px solid #e9ebed' : 'none'
            }}
          >
            <span style={{ color, fontSize: '16px', width: '24px', textAlign: 'center' }}>{icon}</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 500, color }}>{label}</div>
              {(sourceServer || hostname) && (
                <div style={{ color: '#5f6b7a', fontSize: '12px' }}>
                  Source server: {hostname || sourceServer}
                  {sourceServer && hostname && ` (${sourceServer})`}
                </div>
              )}
              {conversionServer && (
                <div style={{ color: '#5f6b7a', fontSize: '12px' }}>
                  Conversion server: <code style={{ fontSize: '11px' }}>{conversionServer}</code>
                </div>
              )}
              {event.error && (
                <div style={{ color: '#d91515', fontSize: '12px' }}>
                  Error: {event.error}
                </div>
              )}
            </div>
            <div style={{ color: '#5f6b7a', fontSize: '11px', whiteSpace: 'nowrap' }}>
              {timestamp}
            </div>
          </div>
        );
      })}
    </div>
  );
};

/**
 * Get status indicator for wave
 */
const getWaveStatusIndicator = (status: string): string => {
  switch (status) {
    case 'completed':
      return '✓';
    case 'failed':
      return '✗';
    case 'in_progress':
      return '▶';
    case 'pending':
    case 'skipped':
      return '○';
    default:
      return '○';
  }
};

/**
 * Parse timestamp - handles both Unix timestamps and ISO strings
 */
const parseTimestamp = (timestamp: string | number | undefined): Date | null => {
  if (!timestamp) return null;
  
  // If it's a number or numeric string (Unix timestamp in seconds)
  if (typeof timestamp === 'number' || /^\d+$/.test(String(timestamp))) {
    const ts = typeof timestamp === 'number' ? timestamp : parseInt(String(timestamp), 10);
    // Unix timestamps are in seconds, JS Date expects milliseconds
    return new Date(ts * 1000);
  }
  
  // Otherwise treat as ISO string
  return new Date(timestamp);
};

/**
 * Calculate wave duration
 * For cancelled/cancelling executions, caps the wave duration at the execution end time
 * to avoid showing misleading durations when waves continue after cancellation
 */
const calculateWaveDuration = (
  wave: WaveExecution, 
  executionStatus?: string, 
  executionEndTime?: string | number
): string => {
  if (!wave.startTime) return '-';
  
  const start = parseTimestamp(wave.startTime);
  if (!start) return '-';
  
  let end = wave.endTime ? parseTimestamp(wave.endTime) : new Date();
  if (!end) return '-';
  
  // For cancelled/cancelling executions, cap wave duration at execution end time
  // This applies to ALL waves (in-progress or completed) to show accurate duration
  // at the time of cancellation, not the time waves actually finished
  const isCancelledOrCancelling = executionStatus && 
    ['cancelled', 'cancelling'].includes(executionStatus.toLowerCase());
  
  if (isCancelledOrCancelling && executionEndTime) {
    const execEnd = parseTimestamp(executionEndTime);
    if (execEnd) {
      // Cap at execution end time for all waves
      if (end.getTime() > execEnd.getTime()) {
        end = execEnd;
      }
    }
  }
  
  const durationMs = end.getTime() - start.getTime();
  
  // Handle negative or invalid durations
  if (durationMs < 0) return '-';
  
  const hours = Math.floor(durationMs / (1000 * 60 * 60));
  const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }
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
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  
  return date.toLocaleString();
};

/**
 * Get detailed status description based on wave status and job events
 */
const getStatusDescription = (status: string, jobEvents?: JobLogEvent[]): string => {
  const statusUpper = status.toUpperCase();
  
  // For STARTED status, check job events to determine current DRS phase
  if (statusUpper === 'STARTED' && jobEvents && jobEvents.length > 0) {
    // Get the most recent event to show current phase
    const sortedEvents = [...jobEvents].sort((a, b) => 
      new Date(b.logDateTime).getTime() - new Date(a.logDateTime).getTime()
    );
    
    const latestEvent = sortedEvents[0]?.event.toUpperCase();
    
    // Map DRS events to current phase descriptions
    if (latestEvent?.includes('CLEANUP')) {
      return 'DRS job initiated, cleanup in progress';
    } else if (latestEvent?.includes('LAUNCH')) {
      return 'DRS job initiated, launching instances';
    } else if (latestEvent?.includes('CONVERSION')) {
      return 'DRS job initiated, converting instances';
    } else if (latestEvent?.includes('SNAPSHOT')) {
      return 'DRS job initiated, taking snapshots';
    } else if (latestEvent?.includes('JOB_START')) {
      return 'DRS job initiated, starting recovery';
    }
    
    // Default for STARTED without clear phase
    return 'DRS job initiated';
  }
  
  const statusMap: Record<string, string> = {
    'PENDING': 'Waiting to start',
    'STARTED': 'DRS job initiated',
    'IN_PROGRESS': 'Recovery in progress',
    'LAUNCHING': 'EC2 instances launching',
    'COMPLETED': 'Successfully completed',
    'FAILED': 'Failed - check error details',
    'CANCELLED': 'Cancelled by user',
  };
  
  return statusMap[statusUpper] || status;
};

/**
 * Get launch status color and description
 */
const getLaunchStatusInfo = (status: string | undefined): { color: 'blue' | 'green' | 'red' | 'grey'; description: string } => {
  const statusMap: Record<string, { color: 'blue' | 'green' | 'red' | 'grey'; description: string }> = {
    'PENDING': { color: 'grey', description: 'Waiting to launch' },
    'IN_PROGRESS': { color: 'blue', description: 'Launching...' },
    'LAUNCHED': { color: 'green', description: 'Successfully launched' },
    'FAILED': { color: 'red', description: 'Launch failed' },
    'TERMINATED': { color: 'grey', description: 'Terminated' },
  };
  return statusMap[status?.toUpperCase() || ''] || { color: 'grey', description: status || 'Unknown' };
};

/**
 * Server Status Row Component
 */
const ServerStatusRow: React.FC<{ server: ServerExecution }> = ({ server }) => {
  const hasDetails = (server.healthCheckResults && server.healthCheckResults.length > 0) || server.error;
  const launchInfo = getLaunchStatusInfo(server.launchStatus || server.status as string);
  
  const serverContent = (
    <Box padding={{ vertical: 'xs', horizontal: 's' }}>
      {/* Server Name/ID Header */}
      <div style={{ marginBottom: '8px' }}>
        <div style={{ fontWeight: 500, fontSize: '14px' }}>
          {server.serverName || server.hostname || server.serverId}
        </div>
        {server.serverName && server.serverId && (
          <div style={{ fontSize: '12px', color: '#5f6b7a', fontFamily: 'monospace' }}>
            {server.serverId}
          </div>
        )}
      </div>
      
      {/* Status Badges Row */}
      <SpaceBetween direction="horizontal" size="xs">
        <Badge color={launchInfo.color}>{launchInfo.description}</Badge>
        {server.region && (
          <Badge color="grey">{server.region}</Badge>
        )}
        {server.replicationState && (
          <Badge color={server.replicationState === 'CONTINUOUS' ? 'green' : 'grey'}>
            {server.replicationState}
          </Badge>
        )}
      </SpaceBetween>
      
      {/* Source Server Details */}
      {(server.sourceInstanceId || server.sourceAccountId || server.sourceIp || server.sourceRegion) && (
        <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#fafafa', borderRadius: '4px', fontSize: '12px' }}>
          <div style={{ color: '#5f6b7a', marginBottom: '4px' }}>Source Server</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
            {server.serverName && (
              <span><strong>Name:</strong> {server.serverName}</span>
            )}
            {server.sourceIp && (
              <span><strong>IP:</strong> <code style={{ fontSize: '11px' }}>{server.sourceIp}</code></span>
            )}
            {server.sourceRegion && (
              <span><strong>Region:</strong> <code style={{ fontSize: '11px' }}>{server.sourceRegion}</code></span>
            )}
            {server.sourceInstanceId && (
              <span><strong>Instance:</strong> <code style={{ fontSize: '11px' }}>{server.sourceInstanceId}</code></span>
            )}
            {server.sourceAccountId && (
              <span><strong>Account:</strong> <code style={{ fontSize: '11px' }}>{server.sourceAccountId}</code></span>
            )}
          </div>
        </div>
      )}
      
      {/* Instance Details (if launched) */}
      {server.recoveredInstanceId && (
        <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#f2f8fd', borderRadius: '4px' }}>
          <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>Recovery Instance</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', fontSize: '13px' }}>
            <span><strong>Instance:</strong> <code style={{ fontSize: '12px' }}>{server.recoveredInstanceId}</code></span>
            {server.instanceType && <span><strong>Type:</strong> {server.instanceType}</span>}
            {server.privateIp && <span><strong>IP:</strong> {server.privateIp}</span>}
          </div>
        </div>
      )}
      
      {/* Health Check Status */}
      {server.healthCheckStatus && (
        <div style={{ marginTop: '8px' }}>
          <Badge color={server.healthCheckStatus === 'passed' ? 'green' : server.healthCheckStatus === 'failed' ? 'red' : 'grey'}>
            Health: {server.healthCheckStatus}
          </Badge>
        </div>
      )}
    </Box>
  );

  if (!hasDetails) {
    return <Container>{serverContent}</Container>;
  }

  return (
    <ExpandableSection
      headerText={server.serverName || server.hostname || server.serverId}
      variant="container"
    >
      {serverContent}
      
      {server.healthCheckResults && server.healthCheckResults.length > 0 && (
        <Box padding={{ top: 's' }}>
          <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '8px' }}>
            Health Checks
          </div>
          <SpaceBetween size="xs">
            {server.healthCheckResults.map((check, idx) => (
              <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>{check.status === 'passed' ? '✓' : '✗'}</span>
                <span style={{ fontSize: '14px' }}>
                  {check.checkName}
                  {check.message && `: ${check.message}`}
                </span>
              </div>
            ))}
          </SpaceBetween>
        </Box>
      )}
      
      {server.error && (
        <Box padding={{ top: 's' }}>
          <Alert type="error">
            {server.error.message}
          </Alert>
        </Box>
      )}
    </ExpandableSection>
  );
};

/**
 * Calculate overall progress percentage
 * 
 * For cancelled executions, only count waves that actually ran (not cancelled waves).
 * This gives a more accurate representation of what was accomplished before cancellation.
 */
/**
 * Calculate progress using job logs for accurate DRS phase detection
 */
const calculateOverallProgressWithLogs = (
  waves: WaveExecution[], 
  planTotalWaves?: number,
  jobLogs?: Record<number, WaveJobLogs>
): { percentage: number; completedWaves: number; totalWaves: number; activeWaves: number } => {
  if (!waves || waves.length === 0) return { percentage: 0, completedWaves: 0, totalWaves: planTotalWaves || 0, activeWaves: 0 };
  
  const totalWaves = planTotalWaves || waves.length;
  const completedWaves = waves.filter(w => ['completed', 'COMPLETED'].includes(w.status)).length;
  
  // Count waves that are actually running (not cancelled/pending)
  const activeWaves = waves.filter(w => {
    const status = (w.status || '').toUpperCase();
    return ['STARTED', 'IN_PROGRESS', 'POLLING', 'LAUNCHING', 'INITIATED'].includes(status);
  }).length;
  
  // Count cancelled waves (these shouldn't contribute to progress)
  const cancelledWaves = waves.filter(w => ['cancelled', 'CANCELLED'].includes(w.status)).length;
  
  // If all non-completed waves are cancelled, show progress based on completed waves only
  const effectiveWaves = totalWaves - cancelledWaves;
  const waveWeight = effectiveWaves > 0 ? 100 / effectiveWaves : 0;
  
  // DRS phase weights (must sum to 1.0)
  const phaseProgress: Record<string, number> = {
    'JOB_START': 0.05,
    'SNAPSHOT_START': 0.08,
    'SNAPSHOT_END': 0.15,
    'CONVERSION_START': 0.20,
    'CONVERSION_END': 0.75,
    'LAUNCH_START': 0.85,
    'LAUNCH_END': 1.0,
    'LAUNCHED': 1.0,
  };
  
  let totalProgress = 0;
  
  for (const wave of waves) {
    const status = (wave.status || 'pending').toUpperCase();
    const waveNum = wave.waveNumber ?? 0;
    const waveJobLogs = jobLogs?.[waveNum];
    
    // Skip cancelled waves - they don't contribute to progress
    if (status === 'CANCELLED') {
      continue;
    }
    
    let wavePhaseProgress = 0;
    
    if (status === 'COMPLETED' || status === 'LAUNCHED') {
      wavePhaseProgress = 1.0;
    } else if (status === 'FAILED') {
      wavePhaseProgress = 0.5;
    } else if (status === 'PAUSED' || status === 'PENDING') {
      wavePhaseProgress = 0;
    } else if (waveJobLogs && waveJobLogs.events && waveJobLogs.events.length > 0) {
      // Use job logs to determine actual phase
      const events = waveJobLogs.events.map(e => e.event.toUpperCase());
      
      // Find the most advanced phase
      if (events.includes('LAUNCH_END')) {
        wavePhaseProgress = phaseProgress['LAUNCH_END'];
      } else if (events.includes('LAUNCH_START')) {
        wavePhaseProgress = phaseProgress['LAUNCH_START'];
      } else if (events.includes('CONVERSION_END')) {
        wavePhaseProgress = phaseProgress['CONVERSION_END'];
      } else if (events.includes('CONVERSION_START')) {
        // Conversion is the longest phase - estimate progress within it
        wavePhaseProgress = phaseProgress['CONVERSION_START'] + 0.25; // ~45% through wave
      } else if (events.includes('SNAPSHOT_END')) {
        wavePhaseProgress = phaseProgress['SNAPSHOT_END'];
      } else if (events.includes('SNAPSHOT_START')) {
        wavePhaseProgress = phaseProgress['SNAPSHOT_START'];
      } else if (events.includes('JOB_START')) {
        wavePhaseProgress = phaseProgress['JOB_START'];
      }
    } else {
      // Fallback to wave status
      if (status === 'LAUNCHING') {
        wavePhaseProgress = 0.85;
      } else if (status === 'POLLING' || status === 'IN_PROGRESS') {
        wavePhaseProgress = 0.40;
      } else if (status === 'STARTED') {
        wavePhaseProgress = 0.10;
      }
    }
    
    totalProgress += wavePhaseProgress * waveWeight;
  }
  
  return { 
    percentage: Math.min(Math.round(totalProgress), 100), 
    completedWaves, 
    totalWaves,
    activeWaves
  };
};

/**
 * Wave Progress Component
 * 
 * Visualizes execution progress through waves with expandable server details.
 */
export const WaveProgress: React.FC<WaveProgressProps> = ({ 
  waves, 
  currentWave, 
  totalWaves: planTotalWaves, 
  executionId,
  executionStatus,
  executionEndTime
}) => {
  const hasWaves = waves && waves.length > 0;
  
  // State for job logs
  const [jobLogs, setJobLogs] = useState<Record<number, WaveJobLogs>>({});
  const [loadingLogs, setLoadingLogs] = useState<Record<number, boolean>>({});
  const [expandedJobLogs, setExpandedJobLogs] = useState<Record<number, boolean>>({});

  // Fetch job logs for a wave
  const fetchJobLogs = useCallback(async (waveNumber: number, jobId: string, force = false) => {
    if (!executionId || (!force && jobLogs[waveNumber]) || loadingLogs[waveNumber]) return;
    
    setLoadingLogs(prev => ({ ...prev, [waveNumber]: true }));
    try {
      const result = await apiClient.getJobLogs(executionId, jobId);
      
      // Find logs by wave number first, then by jobId as fallback
      const waveLogs = result.jobLogs.find((l: WaveJobLogs) => l.waveNumber === waveNumber) 
        || result.jobLogs.find((l: WaveJobLogs) => l.jobId === jobId);
      
      if (waveLogs) {
        setJobLogs(prev => ({ ...prev, [waveNumber]: waveLogs }));
      }
    } catch (err) {
      console.error('Error fetching job logs:', err);
    } finally {
      setLoadingLogs(prev => ({ ...prev, [waveNumber]: false }));
    }
  }, [executionId, jobLogs, loadingLogs]);

  // Track wave statuses to detect changes
  const [prevWaveStatuses, setPrevWaveStatuses] = useState<Record<number, string>>({});
  
  // Ref to track polling interval (avoids recreating on every render)
  const pollingIntervalRef = React.useRef<NodeJS.Timeout | null>(null);

  // Auto-fetch job logs for all waves with job IDs
  useEffect(() => {
    if (!executionId || !waves) return;
    
    // Get all waves that have a jobId
    const wavesWithJobs = waves.filter(w => w.jobId);
    
    // Build current status map
    const currentStatuses: Record<number, string> = {};
    waves.forEach(w => {
      currentStatuses[w.waveNumber ?? 0] = w.status || '';
    });
    
    // Fetch for all waves with jobs - force refresh if status changed
    wavesWithJobs.forEach(wave => {
      const waveNum = wave.waveNumber ?? 0;
      const statusChanged = prevWaveStatuses[waveNum] !== currentStatuses[waveNum];
      const needsInitialFetch = !jobLogs[waveNum];
      
      if (wave.jobId && (needsInitialFetch || statusChanged)) {
        fetchJobLogs(waveNum, wave.jobId, statusChanged); // Force if status changed
      }
    });
    
    // Update previous statuses
    setPrevWaveStatuses(currentStatuses);
  }, [executionId, waves, fetchJobLogs, jobLogs, prevWaveStatuses]);

  // Separate effect for polling - uses ref to avoid dependency issues
  useEffect(() => {
    if (!executionId || !waves) return;
    
    // Check if any waves are still in progress
    const hasInProgressWaves = waves.some(w => {
      const status = (w.status || '').toUpperCase();
      return ['STARTED', 'IN_PROGRESS', 'POLLING', 'LAUNCHING'].includes(status) && w.jobId;
    });
    
    // Clear existing interval
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    
    // Set up polling if there are in-progress waves
    if (hasInProgressWaves) {
      const wavesWithJobs = waves.filter(w => w.jobId);
      
      pollingIntervalRef.current = setInterval(() => {
        wavesWithJobs.forEach(wave => {
          const waveNum = wave.waveNumber ?? 0;
          const status = (wave.status || '').toUpperCase();
          // Force refresh for in-progress waves
          if (wave.jobId && ['STARTED', 'IN_PROGRESS', 'POLLING', 'LAUNCHING'].includes(status)) {
            fetchJobLogs(waveNum, wave.jobId, true);
          }
        });
      }, 3000); // Poll every 3 seconds for faster updates
    }
    
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [executionId, waves, fetchJobLogs]);

  // Calculate progress using job logs for more accuracy
  const progress = useMemo(() => {
    return calculateOverallProgressWithLogs(waves, planTotalWaves, jobLogs);
  }, [waves, planTotalWaves, jobLogs]);

  // Pre-calculate wave durations to avoid useMemo inside map (React hooks rule violation)
  const waveDurations = useMemo(() => {
    if (!waves) return {};
    return waves.reduce((acc, wave, index) => {
      const waveNum = wave.waveNumber ?? index;
      acc[waveNum] = calculateWaveDuration(wave, executionStatus, executionEndTime);
      return acc;
    }, {} as Record<number, string>);
  }, [waves, executionStatus, executionEndTime]);

  
  return (
    <SpaceBetween size="m">
      {/* Overall Progress Bar */}
      {hasWaves && (
        <Box>
          <ProgressBar
            value={progress.percentage}
            label="Overall Progress"
            description={`${progress.completedWaves} of ${progress.totalWaves} waves completed`}
            status={progress.percentage === 100 ? 'success' : 'in-progress'}
          />
        </Box>
      )}
      
      {/* Wave List */}
      {(waves || []).map((wave, index) => {
        const displayWaveNumber = (wave.waveNumber ?? index) + 1; // 1-based display
        const waveNum = wave.waveNumber ?? index;
        const isCurrent = currentWave === wave.waveNumber || currentWave === index;
        const hasServers = wave.serverExecutions && wave.serverExecutions.length > 0;
        const statusIndicator = getWaveStatusIndicator(wave.status);
        const statusDescription = getStatusDescription(wave.status, waveJobLogs?.events);
        const hasJobId = !!wave.jobId;
        const waveJobLogs = jobLogs[waveNum];
        const isLoadingLogs = loadingLogs[waveNum];
        const waveDuration = waveDurations[waveNum] || '-';
        
        return (
          <Container key={wave.waveNumber ?? index}>
            <SpaceBetween size="s">
              {/* Wave Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ 
                  fontSize: '24px',
                  color: ['completed', 'COMPLETED'].includes(wave.status) ? '#037f0c' :
                         ['failed', 'FAILED'].includes(wave.status) ? '#d91515' :
                         ['started', 'STARTED', 'in_progress', 'IN_PROGRESS'].includes(wave.status) ? '#0972d3' : '#5f6b7a'
                }}>
                  {statusIndicator}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: '16px' }}>
                    Wave {displayWaveNumber}: {wave.waveName}
                  </div>
                  <div style={{ fontSize: '13px', color: '#5f6b7a', marginTop: '4px' }}>
                    {statusDescription}
                  </div>
                  {wave.startTime && !['cancelled', 'CANCELLED', 'skipped', 'SKIPPED', 'pending', 'PENDING'].includes(wave.status) && (
                    <div style={{ fontSize: '12px', color: '#5f6b7a', marginTop: '2px' }}>
                      Started {formatRelativeTime(wave.startTime)}
                      {' • '}
                      Duration: {waveDuration}
                      {wave.jobId && (
                        <span> • Job: <code style={{ fontSize: '11px' }}>{wave.jobId}</code></span>
                      )}
                    </div>
                  )}
                </div>
                <StatusBadge status={wave.status} />
              </div>

              {/* Wave Error */}
              {wave.error && (
                <Alert type="error">
                  {wave.error.message}
                </Alert>
              )}

              {/* Servers */}
              {hasServers && (
                <ExpandableSection
                  headerText={`Servers (${wave.serverExecutions.length})`}
                  variant="footer"
                  defaultExpanded={isCurrent}
                >
                  <SpaceBetween size="s">
                    {wave.serverExecutions.map((server) => (
                      <ServerStatusRow key={server.serverId} server={server} />
                    ))}
                  </SpaceBetween>
                </ExpandableSection>
              )}

              {/* DRS Job Events Timeline - Collapsible but auto-refreshes regardless */}
              {hasJobId && executionId && (
                <ExpandableSection
                  headerText={`DRS Job Events${waveJobLogs?.events?.length ? ` (${waveJobLogs.events.length})` : ''}`}
                  variant="footer"
                  expanded={expandedJobLogs[waveNum] ?? true}
                  onChange={({ detail }) => setExpandedJobLogs(prev => ({ ...prev, [waveNum]: detail.expanded }))}
                >
                  {isLoadingLogs && !waveJobLogs ? (
                    <Box textAlign="center" padding="s">
                      <Spinner /> Loading job events...
                    </Box>
                  ) : waveJobLogs?.events?.length ? (
                    <JobEventsTimeline events={waveJobLogs.events} />
                  ) : (
                    <Box color="text-status-inactive" padding="s">
                      Waiting for DRS job events...
                    </Box>
                  )}
                </ExpandableSection>
              )}
            </SpaceBetween>
          </Container>
        );
      })}
    </SpaceBetween>
  );
};
