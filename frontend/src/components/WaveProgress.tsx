/**
 * Wave Progress Component
 * 
 * Displays wave execution timeline using CloudScape components.
 * Shows wave statuses, timing, and server details.
 */

import React, { useState } from 'react';
import {
  Container,
  SpaceBetween,
  Box,
  ExpandableSection,
  Alert,
  Badge,
} from '@cloudscape-design/components';
import { StatusBadge } from './StatusBadge';
import { DateTimeDisplay } from './DateTimeDisplay';
import type { WaveExecution, ServerExecution } from '../types';

interface WaveProgressProps {
  waves: WaveExecution[];
  currentWave?: number;
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
 * Calculate wave duration
 */
const calculateWaveDuration = (wave: WaveExecution): string => {
  if (!wave.startTime) return '-';
  
  const start = new Date(wave.startTime);
  const end = wave.endTime ? new Date(wave.endTime) : new Date();
  const durationMs = end.getTime() - start.getTime();
  
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
 * Server Status Row Component
 */
const ServerStatusRow: React.FC<{ server: ServerExecution }> = ({ server }) => {
  const hasDetails = (server.healthCheckResults && server.healthCheckResults.length > 0) || server.error;
  
  const serverContent = (
    <Box padding={{ vertical: 'xs', horizontal: 's' }}>
      <div style={{ marginBottom: '8px', fontWeight: 500 }}>
        {server.serverName || server.serverId}
      </div>
      <SpaceBetween direction="horizontal" size="xs">
        <StatusBadge status={server.status} size="small" />
        {server.recoveredInstanceId && (
          <Badge color="blue">Instance: {server.recoveredInstanceId}</Badge>
        )}
        {server.healthCheckStatus && (
          <Badge color={server.healthCheckStatus === 'passed' ? 'green' : 'grey'}>
            Health: {server.healthCheckStatus}
          </Badge>
        )}
      </SpaceBetween>
    </Box>
  );

  if (!hasDetails) {
    return <Container>{serverContent}</Container>;
  }

  return (
    <ExpandableSection
      headerText={server.serverName || server.serverId}
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
 * Wave Progress Component
 * 
 * Visualizes execution progress through waves with expandable server details.
 */
export const WaveProgress: React.FC<WaveProgressProps> = ({ waves, currentWave }) => {
  return (
    <SpaceBetween size="m">
      {(waves || []).map((wave) => {
        const isCurrent = currentWave === wave.waveNumber;
        const hasServers = wave.serverExecutions && wave.serverExecutions.length > 0;
        const statusIndicator = getWaveStatusIndicator(wave.status);
        
        return (
          <Container key={wave.waveNumber}>
            <SpaceBetween size="s">
              {/* Wave Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '24px' }}>{statusIndicator}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: '16px' }}>
                    Wave {wave.waveNumber}: {wave.waveName}
                  </div>
                  {wave.startTime && (
                    <div style={{ fontSize: '12px', color: '#5f6b7a', marginTop: '4px' }}>
                      Started <DateTimeDisplay value={wave.startTime} format="relative" />
                      {' • '}
                      Duration: {calculateWaveDuration(wave)}
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
