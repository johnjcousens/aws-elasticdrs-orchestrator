/**
 * Wave Progress Component
 * 
 * Displays wave execution timeline using CloudScape components.
 * Pure display component - receives data as props, no internal polling.
 * 
 * Based on archive reference pattern for stability.
 */

import React, { useState } from 'react';
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
import type { WaveExecution, ServerExecution } from '../types';

interface WaveProgressProps {
  waves: WaveExecution[];
  currentWave?: number;
  totalWaves?: number;
}

/**
 * Determine effective wave status based on wave status and server statuses
 * If wave says "started" but all servers are "LAUNCHED", it's actually completed
 */
const getEffectiveWaveStatus = (wave: WaveExecution): string => {
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
    
    if (allLaunched) return 'completed';
    if (anyFailed) return 'failed';
  }
  
  return waveStatus;
};

/**
 * Get status indicator icon for wave
 */
const getWaveStatusIndicator = (status: string): string => {
  switch (status?.toLowerCase()) {
    case 'completed':
    case 'launched':
      return '✓';
    case 'failed':
      return '✗';
    case 'in_progress':
    case 'started':
    case 'polling':
    case 'launching':
      return '▶';
    case 'pending':
    case 'skipped':
      return '○';
    default:
      return '○';
  }
};

/**
 * Get status color for wave indicator
 */
const getStatusColor = (status: string): string => {
  switch (status?.toLowerCase()) {
    case 'completed':
    case 'launched':
      return '#037f0c';
    case 'failed':
      return '#d91515';
    case 'in_progress':
    case 'started':
    case 'polling':
    case 'launching':
      return '#0972d3';
    default:
      return '#5f6b7a';
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
 * Get launch status badge color
 */
const getLaunchStatusColor = (status: string | undefined): 'blue' | 'green' | 'red' | 'grey' => {
  switch (status?.toUpperCase()) {
    case 'LAUNCHED':
      return 'green';
    case 'IN_PROGRESS':
    case 'LAUNCHING':
      return 'blue';
    case 'FAILED':
      return 'red';
    default:
      return 'grey';
  }
};

/**
 * Generate AWS console link for EC2 instance
 */
const getConsoleLink = (instanceId: string, region: string): string => {
  return `https://console.aws.amazon.com/ec2/v2/home?region=${region}#Instances:instanceId=${instanceId}`;
};

/**
 * Calculate overall progress
 */
const calculateProgress = (
  waves: WaveExecution[], 
  totalWaves?: number
): { percentage: number; completed: number; total: number } => {
  if (!waves || waves.length === 0) {
    return { percentage: 0, completed: 0, total: totalWaves || 0 };
  }
  
  const total = totalWaves || waves.length;
  const completed = waves.filter(w => {
    const effectiveStatus = getEffectiveWaveStatus(w);
    return effectiveStatus === 'completed' || effectiveStatus === 'launched';
  }).length;
  
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  
  return { percentage, completed, total };
};

/**
 * Server table column definitions
 */
const serverColumnDefinitions = [
  {
    id: 'serverId',
    header: 'Server ID',
    cell: (server: ServerExecution) => (
      <span style={{ fontFamily: 'monospace', fontSize: '13px' }}>
        {server.serverName || server.hostname || server.serverId}
      </span>
    ),
    width: 200,
  },
  {
    id: 'status',
    header: 'Status',
    cell: (server: ServerExecution) => {
      const status = server.launchStatus || server.status || 'pending';
      return <Badge color={getLaunchStatusColor(status)}>{status}</Badge>;
    },
    width: 120,
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
            <span style={{ fontFamily: 'monospace' }}>{instanceId}</span>
          </Link>
        );
      }
      
      const status = (server.launchStatus || server.status || '').toUpperCase();
      return status === 'LAUNCHING' ? 'Launching...' : '-';
    },
    width: 180,
  },
  {
    id: 'instanceType',
    header: 'Type',
    cell: (server: ServerExecution) => server.instanceType || '-',
    width: 100,
  },
  {
    id: 'privateIp',
    header: 'Private IP',
    cell: (server: ServerExecution) => server.privateIp || '-',
    width: 120,
  },
  {
    id: 'launchTime',
    header: 'Launch Time',
    cell: (server: ServerExecution) => {
      // Check for various timestamp field names
      const timestamp = (server as any).launchTime || (server as any).startTime;
      return formatTimestamp(timestamp);
    },
    width: 160,
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
  totalWaves 
}) => {
  const [expandedWaves, setExpandedWaves] = useState<Set<number>>(
    new Set(currentWave !== undefined ? [currentWave] : [0])
  );

  const progress = calculateProgress(waves, totalWaves);
  
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
        const isExpanded = expandedWaves.has(waveNum);
        const hasServers = wave.serverExecutions && wave.serverExecutions.length > 0;
        
        // Use effective status that considers server statuses
        const effectiveStatus = getEffectiveWaveStatus(wave);
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
                  gap: '12px',
                  cursor: hasServers ? 'pointer' : 'default'
                }}
                onClick={() => {
                  if (hasServers) {
                    setExpandedWaves(prev => {
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
                <span style={{ fontSize: '24px', color: statusColor }}>
                  {statusIndicator}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: '16px' }}>
                    Wave {displayNum}: {wave.waveName || `Wave ${displayNum}`}
                  </div>
                  <div style={{ fontSize: '12px', color: '#5f6b7a', marginTop: '2px' }}>
                    {wave.startTime ? (
                      <>
                        Started {formatRelativeTime(wave.startTime)}
                        {' • '}Duration: {duration}
                        {wave.jobId && (
                          <span> • Job: <code style={{ fontSize: '11px' }}>{wave.jobId}</code></span>
                        )}
                      </>
                    ) : (
                      'Not started'
                    )}
                  </div>
                </div>
                <StatusBadge status={effectiveStatus} />
              </div>

              {/* Wave Error */}
              {wave.error && (
                <Alert type="error">
                  {typeof wave.error === 'string' ? wave.error : wave.error.message}
                </Alert>
              )}

              {/* Servers Table - Expandable */}
              {hasServers && (
                <ExpandableSection
                  headerText={`Servers (${wave.serverExecutions.length})`}
                  variant="footer"
                  expanded={isExpanded || isCurrent}
                  onChange={({ detail }) => {
                    if (detail.expanded) {
                      setExpandedWaves(prev => new Set([...prev, waveNum]));
                    } else {
                      setExpandedWaves(prev => {
                        const next = new Set(prev);
                        next.delete(waveNum);
                        return next;
                      });
                    }
                  }}
                >
                  <Table
                    columnDefinitions={serverColumnDefinitions}
                    items={wave.serverExecutions}
                    variant="embedded"
                    wrapLines
                    empty={
                      <Box textAlign="center" color="inherit">
                        No servers in this wave
                      </Box>
                    }
                  />
                  
                  {/* Server Errors */}
                  {wave.serverExecutions.some(s => s.error) && (
                    <SpaceBetween size="xs">
                      {wave.serverExecutions
                        .filter(s => s.error)
                        .map((server, idx) => (
                          <Alert type="error" key={idx}>
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
