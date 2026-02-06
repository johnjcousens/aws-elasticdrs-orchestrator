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
  status?: ExecutionStatus | string;
}

/**
 * Status Badge Component
 * 
 * @param status - Status string
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
}) => {
  const getStatusConfig = (status: string) => {
    if (!status) {
      return {
        label: 'Unknown',
        color: 'grey' as const,
      };
    }
    
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
      
      case 'cancelling':
        return {
          label: 'Cancelling',
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
      case 'polling':
        return {
          label: 'In Progress',
          color: 'blue' as const,
        };
      
      case 'partial':
      case 'partial failure':
        return {
          label: 'Partial',
          color: 'blue' as const,  // Blue to indicate mixed results (not pure failure)
        };
      
      default:
        return {
          label: status.charAt(0).toUpperCase() + status.slice(1),
          color: 'grey' as const,
        };
    }
  };

  const config = getStatusConfig(status || '');

  return (
    <Badge color={config.color}>
      {config.label}
    </Badge>
  );
};
