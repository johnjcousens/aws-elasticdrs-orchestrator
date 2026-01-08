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
} from '@cloudscape-design/components';
import { StatusBadge } from './StatusBadge';
import type { WaveExecution, ServerExecution } from '../types';

interface WaveProgressProps {
  waves: WaveExecution[];
  currentWave?: number;
  totalWaves?: number;
}

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
    // Unix timestamps in seconds need conversion to milliseconds
    return new Date(ts < 10000000000 ? ts * 1000 : ts);
  }
  
  return new Date(timestamp);
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
 * Server Status Row Component
 */
const ServerStatusRow: React.FC<{ server: ServerExecution }> = ({ server }) => {
  const launchStatus = server.launchStatus || server.status || 'pending';
  
  return (
    <Container>
      <Box padding={{ vertical: 'xs', horizontal: 's' }}>
        {/* Server Name/ID */}
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
        
        {/* Status Badges */}
        <SpaceBetween direction="horizontal" size="xs">
          <Badge color={getLaunchStatusColor(launchStatus)}>
            {launchStatus}
          </Badge>
          {server.region && (
            <Badge color="grey">{server.region}</Badge>
          )}
        </SpaceBetween>
        
        {/* Recovery Instance Details */}
        {server.recoveredInstanceId && (
          <div style={{ 
            marginTop: '8px', 
            padding: '8px', 
            backgroundColor: '#f2f8fd', 
            borderRadius: '4px',
            fontSize: '13px'
          }}>
            <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
              Recovery Instance
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
              <span>
                <strong>Instance:</strong>{' '}
                <code style={{ fontSize: '12px' }}>{server.recoveredInstanceId}</code>
              </span>
              {server.instanceType && (
                <span><strong>Type:</strong> {server.instanceType}</span>
              )}
              {server.privateIp && (
                <span><strong>IP:</strong> {server.privateIp}</span>
              )}
            </div>
          </div>
        )}
        
        {/* Error */}
        {server.error && (
          <Alert type="error" statusIconAriaLabel="Error">
            {typeof server.error === 'string' ? server.error : server.error.message}
          </Alert>
        )}
      </Box>
    </Container>
  );
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
    const status = (w.status || '').toLowerCase();
    return status === 'completed' || status === 'launched';
  }).length;
  
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
  
  return { percentage, completed, total };
};

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
    new Set(currentWave !== undefined ? [currentWave] : [])
  );

  const toggleWave = (waveNumber: number) => {
    setExpandedWaves(prev => {
      const next = new Set(prev);
      if (next.has(waveNumber)) {
        next.delete(waveNumber);
      } else {
        next.add(waveNumber);
      }
      return next;
    });
  };

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
        const statusIndicator = getWaveStatusIndicator(wave.status);
        const statusColor = getStatusColor(wave.status);
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
                onClick={() => hasServers && toggleWave(waveNum)}
              >
                <span style={{ fontSize: '24px', color: statusColor }}>
                  {statusIndicator}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: '16px' }}>
                    Wave {displayNum}: {wave.waveName || `Wave ${displayNum}`}
                  </div>
                  {wave.startTime && (
                    <div style={{ fontSize: '12px', color: '#5f6b7a', marginTop: '2px' }}>
                      Started {formatRelativeTime(wave.startTime)}
                      {' • '}Duration: {duration}
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
                  {typeof wave.error === 'string' ? wave.error : wave.error.message}
                </Alert>
              )}

              {/* Servers - Expandable */}
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
                  <SpaceBetween size="s">
                    {wave.serverExecutions.map((server) => (
                      <ServerStatusRow key={server.serverId} server={server} />
                    ))}
                  </SpaceBetween>
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
