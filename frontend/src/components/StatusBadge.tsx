/**
 * Status Badge Component
 * 
 * Displays colored status badges for executions, waves, and servers.
 * Provides consistent status visualization across the application.
 */

import React from 'react';
import { Badge } from '@cloudscape-design/components';
import type { ExecutionStatus } from '../types';

export interface StatusBadgeProps {
  status: ExecutionStatus | string;
  size?: 'small' | 'medium';
}

/**
 * Status Badge Component
 * 
 * @param status - Status string
 * @param size - Badge size (small or medium) - Note: CloudScape badges don't have size variants
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'small', // Kept for API compatibility but not used in CloudScape
}) => {
  const getStatusConfig = (status: string) => {
    const normalizedStatus = status.toLowerCase().replace(/_/g, ' ');
    
    switch (normalizedStatus) {
      case 'completed':
      case 'success':
        return {
          label: 'Completed',
          color: 'green' as const,
        };
      
      case 'failed':
      case 'error':
        return {
          label: 'Failed',
          color: 'red' as const,
        };
      
      case 'in progress':
      case 'in_progress':
      case 'running':
        return {
          label: 'In Progress',
          color: 'blue' as const,
        };
      
      case 'pending':
      case 'queued':
        return {
          label: 'Pending',
          color: 'grey' as const,
        };
      
      case 'paused':
        return {
          label: 'Paused',
          color: 'grey' as const,
        };
      
      case 'cancelled':
      case 'canceled':
        return {
          label: 'Cancelled',
          color: 'grey' as const,
        };
      
      case 'rolled back':
      case 'rolled_back':
      case 'rollback':
        return {
          label: 'Rolled Back',
          color: 'grey' as const,
        };
      
      case 'draft':
        return {
          label: 'Draft',
          color: 'grey' as const,
        };
      
      case 'active':
        return {
          label: 'Active',
          color: 'green' as const,
        };
      
      // DRS-specific states
      case 'initiated':
      case 'launching':
      case 'started':
        return {
          label: normalizedStatus.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
          color: 'blue' as const,
        };
      
      case 'polling':
        return {
          label: 'Polling',
          color: 'blue' as const,
        };
      
      case 'partial':
      case 'partial failure':
        return {
          label: 'Partial',
          color: 'red' as const,
        };
      
      default:
        return {
          label: status.charAt(0).toUpperCase() + status.slice(1),
          color: 'grey' as const,
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <Badge color={config.color}>
      {config.label}
    </Badge>
  );
};
