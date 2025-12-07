/**
 * TypeScript Type Definitions
 * 
 * These types mirror the backend DynamoDB schema and API responses.
 */

// ============================================================================
// Protection Group Types
// ============================================================================

export interface ProtectionGroup {
  id: string;  // Lambda returns 'id' from transform_pg_to_camelcase
  protectionGroupId: string;  // Alias for backward compatibility
  name: string;
  description?: string;
  region: string;
  sourceServerIds: string[];
  createdAt: number;
  updatedAt: number;
  accountId?: string;
  owner?: string;
  serverDetails?: any[];
}

export interface CreateProtectionGroupRequest {
  GroupName: string;  // API expects PascalCase
  Description?: string;
  Region: string;
  sourceServerIds: string[];
  AccountId?: string;
  Owner?: string;
}

export interface UpdateProtectionGroupRequest {
  GroupName?: string;  // API expects PascalCase
  Description?: string;
  sourceServerIds?: string[];
}

// ============================================================================
// Recovery Plan Types
// ============================================================================

export interface RecoveryPlan {
  id: string;
  name: string;
  description?: string;
  protectionGroupId: string;
  protectionGroupName?: string;
  waves: Wave[];
  createdAt: string | number;
  updatedAt: string;
  createdBy?: string;
  status?: 'draft' | 'active' | 'archived';
  lastExecutionId?: string;
  lastExecutionStatus?: ExecutionStatus;
  lastExecutedAt?: string;
  lastStartTime?: number; // Unix timestamp
  lastEndTime?: number; // Unix timestamp
}

export interface Wave {
  waveNumber: number;
  name: string;
  description?: string;
  serverIds: string[];
  serverCount?: number;
  // executionType removed - backend ignores this field, all within-wave execution
  // is parallel with DRS-safe delays (15s between servers). Use dependsOnWaves for sequential operations.
  dependsOnWaves?: number[];
  protectionGroupIds: string[];  // Required - wave can have multiple Protection Groups
  protectionGroupId?: string;  // Backward compatibility - single PG (deprecated, use protectionGroupIds)
  ProtectionGroupIds?: string[];  // Backend PascalCase version for compatibility
  ProtectionGroupId?: string;  // Backend PascalCase version for compatibility (deprecated)
  preWaveActions?: WaveAction[];
  postWaveActions?: WaveAction[];
  healthCheckConfig?: HealthCheckConfig;
  rollbackConfig?: RollbackConfig;
}

export interface WaveAction {
  actionType: 'ssm-automation' | 'lambda' | 'wait' | 'approval';
  actionName: string;
  parameters?: Record<string, any>;
  timeoutSeconds?: number;
  retryConfig?: RetryConfig;
}

export interface HealthCheckConfig {
  enabled: boolean;
  ssmDocumentName?: string;
  timeoutSeconds?: number;
  maxRetries?: number;
}

export interface RollbackConfig {
  enabled: boolean;
  automaticRollback?: boolean;
  rollbackOnHealthCheckFailure?: boolean;
}

export interface RetryConfig {
  maxAttempts: number;
  backoffMultiplier?: number;
  initialDelaySeconds?: number;
}

export interface CreateRecoveryPlanRequest {
  name: string;
  description?: string;
  protectionGroupId: string;
  waves: Wave[];
}

export interface UpdateRecoveryPlanRequest {
  name?: string;
  description?: string;
  waves?: Wave[];
  status?: 'draft' | 'active' | 'archived';
}

// ============================================================================
// Execution Types
// ============================================================================

export type ExecutionStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'rolled_back'
  | 'cancelled'
  | 'paused';

export interface Execution {
  executionId: string;
  recoveryPlanId: string;
  recoveryPlanName?: string;
  protectionGroupId: string;
  protectionGroupName?: string;
  status: ExecutionStatus;
  startTime: string;
  endTime?: string;
  duration?: number;
  currentWave?: number;
  totalWaves: number;
  waveExecutions: WaveExecution[];
  executedBy?: string;
  error?: ExecutionError;
  metadata?: Record<string, any>;
}

export interface WaveExecution {
  waveNumber: number;
  waveName: string;
  status: ExecutionStatus;
  startTime?: string | number;
  endTime?: string | number;
  duration?: number;
  jobId?: string;
  serverExecutions: ServerExecution[];
  preWaveActionsStatus?: ActionStatus[];
  postWaveActionsStatus?: ActionStatus[];
  error?: ExecutionError;
}

export interface ServerExecution {
  serverId: string;
  serverName?: string;
  hostname?: string;
  region?: string;
  sourceInstanceId?: string;  // Original EC2 instance being replicated
  sourceAccountId?: string;   // Source AWS account ID
  status: ExecutionStatus | string;
  launchStatus?: string;
  replicationState?: string;  // DRS replication state (CONTINUOUS, etc.)
  healthCheckStatus?: 'not_started' | 'in_progress' | 'passed' | 'failed';
  startTime?: string;
  endTime?: string;
  duration?: number;
  recoveredInstanceId?: string;
  instanceType?: string;
  privateIp?: string;
  error?: ExecutionError;
  healthCheckResults?: HealthCheckResult[];
}

export interface ActionStatus {
  actionName: string;
  actionType: string;
  status: ExecutionStatus;
  startTime?: string;
  endTime?: string;
  duration?: number;
  output?: any;
  error?: ExecutionError;
}

export interface HealthCheckResult {
  checkName: string;
  status: 'passed' | 'failed' | 'warning';
  timestamp: string;
  message?: string;
  details?: Record<string, any>;
}

export interface ExecutionError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface ExecuteRecoveryPlanRequest {
  recoveryPlanId: string;
  executionType: 'DRILL' | 'RECOVERY';  // Required - DRILL or RECOVERY only
  dryRun?: boolean;
  skipHealthChecks?: boolean;
  startFromWave?: number;
  parameters?: Record<string, any>;
  executedBy?: string;  // Added for backend compatibility
  topicArn?: string;    // Added for backend SNS notifications
}

export interface ExecutionListItem {
  executionId: string;
  recoveryPlanId: string;
  recoveryPlanName: string;
  status: ExecutionStatus;
  startTime: string;
  endTime?: string;
  duration?: number;
  currentWave?: number;
  totalWaves: number;
  executedBy?: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  nextToken?: string;
  totalCount?: number;
}

// ============================================================================
// DRS-Specific Types
// ============================================================================

export interface DRSSourceServer {
  sourceServerID: string;
  hostname?: string;
  arn: string;
  tags?: Record<string, string>;
  dataReplicationInfo?: {
    dataReplicationState?: string;
    lagDuration?: string;
  };
  launchConfiguration?: {
    name?: string;
    launchDisposition?: string;
  };
  lifeCycle?: {
    state?: string;
    lastLaunch?: {
      initiated?: {
        apiCallDateTime?: string;
      };
    };
  };
}

export interface DRSRecoveryInstance {
  recoveryInstanceID: string;
  sourceServerID: string;
  ec2InstanceID?: string;
  ec2InstanceState?: string;
  jobID?: string;
  pointInTime?: string;
}

// ============================================================================
// DRS Server Discovery Types
// ============================================================================

export interface DRSServer {
  sourceServerID: string;
  hostname: string;
  state: string;
  replicationState: string;
  lagDuration: string;
  lastSeen: string;
  assignedToProtectionGroup: {
    protectionGroupId: string;
    protectionGroupName: string;
  } | null;
  selectable: boolean;
}

export interface DRSServerResponse {
  region: string;
  initialized: boolean;
  servers: DRSServer[];
  totalCount: number;
  availableCount: number;
  assignedCount: number;
}

// ============================================================================
// Legacy Types (for backward compatibility)
// ============================================================================

export interface TagFilter {
  KeyName: string;
  KeyValue: string;
  Values?: string[];
}

// ============================================================================
// UI State Types
// ============================================================================

export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface FormErrors {
  [fieldName: string]: string;
}

export interface FilterOptions {
  searchTerm?: string;
  status?: string[];
  dateRange?: {
    startDate: string;
    endDate: string;
  };
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface TablePagination {
  page: number;
  rowsPerPage: number;
  totalRows: number;
}

// ============================================================================
// Chart/Visualization Types
// ============================================================================

export interface WaveDependencyNode {
  id: number;
  name: string;
  serverCount: number;
  status?: ExecutionStatus;
  dependencies: number[];
}

export interface ExecutionTimeline {
  waveNumber: number;
  waveName: string;
  startTime: string;
  endTime?: string;
  duration?: number;
  status: ExecutionStatus;
  serverCount: number;
}

// ============================================================================
// Authentication Types
// ============================================================================

export interface User {
  username: string;
  email?: string;
  attributes?: Record<string, any>;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error?: string;
}
