/**
 * Status Badge Component
 * 
 * Displays colored status badges for executions, waves, and servers.
 * Provides consistent status visualization across the application.
 */

import React from 'react';
import { Chip } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import CancelIcon from '@mui/icons-material/Cancel';
import UndoIcon from '@mui/icons-material/Undo';
import type { ExecutionStatus } from '../types';

export interface StatusBadgeProps {
  status: ExecutionStatus | string;
  size?: 'small' | 'medium';
}

/**
 * Status Badge Component
 * 
 * @param status - Status string
 * @param size - Badge size (small or medium)
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'small',
}) => {
  const getStatusConfig = (status: string) => {
    const normalizedStatus = status.toLowerCase().replace(/_/g, ' ');
    
    switch (normalizedStatus) {
      case 'completed':
      case 'success':
        return {
          label: 'Completed',
          color: 'success' as const,
          icon: <CheckCircleIcon />,
        };
      
      case 'failed':
      case 'error':
        return {
          label: 'Failed',
          color: 'error' as const,
          icon: <ErrorIcon />,
        };
      
      case 'in progress':
      case 'in_progress':
      case 'running':
        return {
          label: 'In Progress',
          color: 'primary' as const,
          icon: <PlayArrowIcon />,
        };
      
      case 'pending':
      case 'queued':
        return {
          label: 'Pending',
          color: 'default' as const,
          icon: <HourglassEmptyIcon />,
        };
      
      case 'paused':
        return {
          label: 'Paused',
          color: 'warning' as const,
          icon: <PauseIcon />,
        };
      
      case 'cancelled':
      case 'canceled':
        return {
          label: 'Cancelled',
          color: 'default' as const,
          icon: <CancelIcon />,
        };
      
      case 'rolled back':
      case 'rolled_back':
      case 'rollback':
        return {
          label: 'Rolled Back',
          color: 'warning' as const,
          icon: <UndoIcon />,
        };
      
      default:
        return {
          label: status.charAt(0).toUpperCase() + status.slice(1),
          color: 'default' as const,
          icon: undefined,
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <Chip
      label={config.label}
      color={config.color}
      size={size}
      icon={config.icon}
      sx={{
        fontWeight: 500,
        '& .MuiChip-icon': {
          fontSize: size === 'small' ? 16 : 20,
        },
      }}
    />
  );
};
