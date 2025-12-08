/**
 * Wave Progress Component
 * 
 * Displays wave execution timeline using CloudScape components.
 * Shows wave statuses, timing, and server details.
 */

import React from 'react';
import {
  Container,
  SpaceBetween,
  Box,
  ExpandableSection,
  Alert,
  Badge,
  ProgressBar,
  Header,
} from '@cloudscape-design/components';
import { StatusBadge } from './StatusBadge';
import type { WaveExecution, ServerExecution } from '../types';

interface WaveProgressProps {
  waves: WaveExecution[];
  currentWave?: number;
  totalWaves?: number;  // Total waves from recovery plan (not just executed waves)
}

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
 */
const calculateWaveDuration = (wave: WaveExecution): string => {
  if (!wave.startTime) return '-';
  
  const start = parseTimestamp(wave.startTime);
  if (!start) return '-';
  
  const end = wave.endTime ? parseTimestamp(wave.endTime) : new Date();
  if (!end) return '-';
  
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
 * Get detailed status description
 */
const getStatusDescription = (status: string): string => {
  const statusMap: Record<string, string> = {
    'pending': 'Waiting to start',
    'PENDING': 'Waiting to start',
    'started': 'DRS job initiated, launching instances',
    'STARTED': 'DRS job initiated, launching instances',
    'in_progress': 'Recovery in progress',
    'IN_PROGRESS': 'Recovery in progress',
    'launching': 'EC2 instances launching',
    'LAUNCHING': 'EC2 instances launching',
    'completed': 'Successfully completed',
    'COMPLETED': 'Successfully completed',
    'failed': 'Failed - check error details',
    'FAILED': 'Failed - check error details',
    'cancelled': 'Cancelled by user',
    'CANCELLED': 'Cancelled by user',
  };
  return statusMap[status] || status;
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
 */
const calculateOverallProgress = (waves: WaveExecution[], planTotalWaves?: number): { percentage: number; completedWaves: number; totalWaves: number } => {
  if (!waves || waves.length === 0) return { percentage: 0, completedWaves: 0, totalWaves: planTotalWaves || 0 };
  
  // Use planTotalWaves from recovery plan if provided, otherwise fall back to waves array length
  const totalWaves = planTotalWaves || waves.length;
  const completedWaves = waves.filter(w => 
    ['completed', 'COMPLETED'].includes(w.status)
  ).length;
  const inProgressWaves = waves.filter(w => 
    ['started', 'STARTED', 'in_progress', 'IN_PROGRESS', 'launching', 'LAUNCHING'].includes(w.status)
  ).length;
  
  // Each completed wave = 100/totalWaves, in-progress wave = 50% of its share
  const percentage = Math.round(
    ((completedWaves * 100) + (inProgressWaves * 50)) / totalWaves
  );
  
  return { percentage, completedWaves, totalWaves };
};

/**
 * Wave Progress Component
 * 
 * Visualizes execution progress through waves with expandable server details.
 */
export const WaveProgress: React.FC<WaveProgressProps> = ({ waves, currentWave, totalWaves: planTotalWaves }) => {
  const progress = calculateOverallProgress(waves, planTotalWaves);
  const hasWaves = waves && waves.length > 0;
  
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
        const isCurrent = currentWave === wave.waveNumber || currentWave === index;
        const hasServers = wave.serverExecutions && wave.serverExecutions.length > 0;
        const statusIndicator = getWaveStatusIndicator(wave.status);
        const statusDescription = getStatusDescription(wave.status);
        
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
                  {wave.startTime && (
                    <div style={{ fontSize: '12px', color: '#5f6b7a', marginTop: '2px' }}>
                      Started {formatRelativeTime(wave.startTime)}
                      {' • '}
                      Duration: {calculateWaveDuration(wave)}
                      {wave.jobId && (
                        <span> • Job: <code style={{ fontSize: '11px' }}>{wave.jobId}</code></span>
                      )}
                    </div>
                  )}
                </div>
                <StatusBadge status={wave.status} size="small" />
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
            </SpaceBetween>
          </Container>
        );
      })}
    </SpaceBetween>
  );
};
