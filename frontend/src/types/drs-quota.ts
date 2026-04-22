// Copyright Amazon.com and Affiliates. All rights reserved.
// This deliverable is considered Developed Content as defined in the AWS Service Terms.

/**
 * DRS quota and capacity types used by the quota endpoint and by
 * recovery-plan validation. Kept in the types layer (no runtime
 * imports) so services and components can reference them without
 * introducing import cycles.
 */

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
  regionalBreakdown?: Array<{
    region: string;
    replicatingServers: number;
  }>;
}

export interface DRSQuotaStatus {
  accountId: string;
  accountName?: string;
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

/**
 * DRS hard limits. Keep in sync with backend constants in
 * lambda/shared/drs_limits.py.
 */
export const DRS_LIMITS: DRSLimits = {
  MAX_SERVERS_PER_JOB: 100,
  MAX_CONCURRENT_JOBS: 20,
  MAX_SERVERS_IN_ALL_JOBS: 500,
  MAX_REPLICATING_SERVERS: 300,
  MAX_SOURCE_SERVERS: 4000,
  WARNING_REPLICATING_THRESHOLD: 250,
  CRITICAL_REPLICATING_THRESHOLD: 280,
};
