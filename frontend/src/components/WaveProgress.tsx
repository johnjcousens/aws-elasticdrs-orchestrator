/**
 * Wave Progress Component
 * 
 * Displays wave execution timeline using Material-UI Stepper.
 * Shows wave statuses, timing, and server details.
 */

import React, { useState } from 'react';
import {
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Box,
  Typography,
  Stack,
  Chip,
  Alert,
  Collapse,
  IconButton,
  Paper,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import PendingIcon from '@mui/icons-material/Pending';
import PlayCircleIcon from '@mui/icons-material/PlayCircle';
import { StatusBadge } from './StatusBadge';
import { DateTimeDisplay } from './DateTimeDisplay';
import type { WaveExecution, ServerExecution } from '../types';

interface WaveProgressProps {
  waves: WaveExecution[];
  currentWave?: number;
}

/**
 * Get icon for wave status
 */
const getWaveIcon = (status: string, isCurrent: boolean) => {
  if (isCurrent && status === 'in_progress') {
    return <PlayCircleIcon color="warning" />;
  }
  
  switch (status) {
    case 'completed':
      return <CheckCircleIcon color="success" />;
    case 'failed':
      return <ErrorIcon color="error" />;
    case 'pending':
    case 'skipped':
      return <PendingIcon color="disabled" />;
    default:
      return <PendingIcon color="disabled" />;
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
  const [showDetails, setShowDetails] = useState(false);
  
  return (
    <Paper variant="outlined" sx={{ p: 1.5, mb: 1 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Box sx={{ flex: 1 }}>
          <Typography variant="body2" sx={{ fontWeight: 500 }}>
            {server.serverName || server.serverId}
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
            <StatusBadge status={server.status} size="small" />
            {server.recoveredInstanceId && (
              <Chip label={`Instance: ${server.recoveredInstanceId}`} size="small" variant="outlined" />
            )}
            {server.healthCheckStatus && (
              <Chip 
                label={`Health: ${server.healthCheckStatus}`} 
                size="small" 
                variant="outlined"
                color={server.healthCheckStatus === 'passed' ? 'success' : 'default'}
              />
            )}
          </Stack>
        </Box>
        
        {(server.healthCheckResults || server.error) && (
          <IconButton
            size="small"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        )}
      </Stack>
      
      {/* Details Section */}
      <Collapse in={showDetails}>
        <Box sx={{ mt: 2 }}>
          {server.healthCheckResults && server.healthCheckResults.length > 0 && (
            <Box sx={{ mb: 1 }}>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Health Checks
              </Typography>
              <Stack spacing={0.5}>
                {server.healthCheckResults.map((check, idx) => (
                  <Stack key={idx} direction="row" spacing={1} alignItems="center">
                    {check.status === 'passed' ? (
                      <CheckCircleIcon fontSize="small" color="success" />
                    ) : check.status === 'failed' ? (
                      <ErrorIcon fontSize="small" color="error" />
                    ) : (
                      <ErrorIcon fontSize="small" color="warning" />
                    )}
                    <Typography variant="body2">
                      {check.checkName}
                      {check.message && `: ${check.message}`}
                    </Typography>
                  </Stack>
                ))}
              </Stack>
            </Box>
          )}
          
          {server.error && (
            <Alert severity="error" sx={{ mt: 1 }}>
              <Typography variant="body2">
                {server.error.message}
              </Typography>
            </Alert>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
};

/**
 * Wave Progress Component
 * 
 * Visualizes execution progress through waves with expandable server details.
 */
export const WaveProgress: React.FC<WaveProgressProps> = ({ waves, currentWave }) => {
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

  return (
    <Stepper orientation="vertical" activeStep={currentWave ? currentWave - 1 : -1}>
      {(waves || []).map((wave) => {
        const isCurrent = currentWave === wave.waveNumber;
        const isExpanded = expandedWaves.has(wave.waveNumber);
        const hasServers = wave.serverExecutions && wave.serverExecutions.length > 0;
        
        return (
          <Step key={wave.waveNumber} active={isCurrent} completed={wave.status === 'completed'}>
            <StepLabel
              icon={getWaveIcon(wave.status, isCurrent)}
              onClick={() => hasServers && toggleWave(wave.waveNumber)}
              sx={{ cursor: hasServers ? 'pointer' : 'default' }}
            >
              <Stack direction="row" spacing={2} alignItems="center">
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  Wave {wave.waveNumber}: {wave.waveName}
                </Typography>
                <StatusBadge status={wave.status} size="small" />
                {wave.startTime && (
                  <Typography variant="caption" color="text.secondary">
                    {calculateWaveDuration(wave)}
                  </Typography>
                )}
              </Stack>
              
              {wave.startTime && (
                <Typography variant="caption" color="text.secondary" display="block">
                  Started <DateTimeDisplay value={wave.startTime} format="relative" />
                </Typography>
              )}
            </StepLabel>
            
            {hasServers && (
              <StepContent>
                <Collapse in={isExpanded}>
                  <Box sx={{ mt: 2 }}>
                    {wave.error && (
                      <Alert severity="error" sx={{ mb: 2 }}>
                        {wave.error.message}
                      </Alert>
                    )}
                    
                    <Typography variant="caption" color="text.secondary" gutterBottom>
                      Servers ({wave.serverExecutions.length})
                    </Typography>
                    
                    <Box sx={{ mt: 1 }}>
                      {wave.serverExecutions.map((server) => (
                        <ServerStatusRow key={server.serverId} server={server} />
                      ))}
                    </Box>
                  </Box>
                </Collapse>
              </StepContent>
            )}
          </Step>
        );
      })}
    </Stepper>
  );
};
