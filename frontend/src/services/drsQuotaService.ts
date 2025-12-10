/**
 * DRS Quota Service
 * 
 * Service for fetching DRS account quotas and current usage.
 * Used to display capacity warnings and validate operations.
 */

import apiClient from './api';

export interface DRSLimits {
  MAX_SERVERS_PER_JOB: number;
  MAX_CONCURRENT_JOBS: number;
  MAX_SERVERS_IN_ALL_JOBS: number;
  MAX_REPLICATING_SERVERS: number;
  MAX_SOURCE_SERVERS: number;
  WARNING_REPLICATING_THRESHOLD: number;
  CRITICAL_REPLICATING_THRESHOLD: number;
}

export interface DRSCapacity {
  totalSourceServers: number;
  replicatingServers: number;
  maxReplicatingServers: number;
  maxSourceServers: number;
  availableReplicatingSlots: number;
  status: 'OK' | 'INFO' | 'WARNING' | 'CRITICAL' | 'UNKNOWN';
  message: string;
  error?: string;
}

export interface DRSQuotaStatus {
  region: string;
  limits: DRSLimits;
  capacity: DRSCapacity;
  concurrentJobs: {
    current: number | null;
    max: number;
    available: number | null;
  };
  serversInJobs: {
    current: number | null;
    max: number;
  };
}

// DRS hard limits (matching backend constants)
export const DRS_LIMITS: DRSLimits = {
  MAX_SERVERS_PER_JOB: 100,
  MAX_CONCURRENT_JOBS: 20,
  MAX_SERVERS_IN_ALL_JOBS: 500,
  MAX_REPLICATING_SERVERS: 300,
  MAX_SOURCE_SERVERS: 4000,
  WARNING_REPLICATING_THRESHOLD: 250,
  CRITICAL_REPLICATING_THRESHOLD: 280,
};

/**
 * Fetch DRS quotas and current usage for a region
 */
export const getDRSQuotas = async (region: string): Promise<DRSQuotaStatus> => {
  return apiClient.getDRSQuotas(region);
};

/**
 * Validate wave size against DRS limit
 * @returns Error message if invalid, null if valid
 */
export const validateWaveSize = (serverCount: number): string | null => {
  if (serverCount > DRS_LIMITS.MAX_SERVERS_PER_JOB) {
    return `Wave cannot exceed ${DRS_LIMITS.MAX_SERVERS_PER_JOB} servers (DRS limit). Current: ${serverCount}`;
  }
  return null;
};

/**
 * Get capacity status color for UI
 */
export const getCapacityStatusType = (status: string): 'success' | 'info' | 'warning' | 'error' => {
  switch (status) {
    case 'CRITICAL':
      return 'error';
    case 'WARNING':
      return 'warning';
    case 'INFO':
      return 'info';
    default:
      return 'success';
  }
};
