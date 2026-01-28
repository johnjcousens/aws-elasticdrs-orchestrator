/**
 * TypeScript Type Definitions
 * 
 * These types mirror the backend DynamoDB schema and API responses.
 */

// ============================================================================
// Protection Group Types
// ============================================================================

export interface ProtectionGroup {
  groupId: string;        // Database primary key
  protectionGroupId: string;  // Alias for backward compatibility
  groupName: string;      // Protection group name
  description?: string;
  region: string;
  
  // Tag-based server selection - servers matching ALL tags are included at execution time
  serverSelectionTags?: Record<string, string>;
  
  // Legacy: Explicit server IDs (for backward compatibility with existing PGs)
  sourceServerIds?: string[];
  
  // EC2 Launch Configuration - applied to all servers in this group
  launchConfig?: LaunchConfig;
  
  // Per-server launch configurations (overrides group defaults)
  servers?: ServerLaunchConfig[];
  
  createdDate: number;    // Creation timestamp
  lastModifiedDate: number; // Last update timestamp
  accountId?: string;
  assumeRoleName?: string;
  owner?: string;
  
  // Resolved servers (populated by /resolve endpoint or at execution time)
  resolvedServers?: ResolvedServer[];
  resolvedServerCount?: number;
  
  // Optimistic locking version - incremented on each update
  version?: number;
}

// ============================================================================
// EC2 Launch Configuration Types
// ============================================================================

export interface LaunchConfig {
  // EC2 Launch Template settings
  subnetId?: string;
  securityGroupIds?: string[];
  instanceProfileName?: string;
  instanceType?: string;
  staticPrivateIp?: string;  // Static private IP for recovery instance
  
  // DRS Launch Configuration settings
  targetInstanceTypeRightSizingMethod?: 'NONE' | 'BASIC' | 'IN_AWS';
  launchIntoInstanceProperties?: {
    launchIntoEC2InstanceID?: string;
  };
  bootMode?: 'LEGACY_BIOS' | 'UEFI' | 'USE_SOURCE';
  copyPrivateIp?: boolean;
  copyTags?: boolean;
  launchDisposition?: 'STOPPED' | 'STARTED';
  licensing?: {
    osByol?: boolean;
  };
  postLaunchEnabled?: boolean;
}

// Per-server launch configuration (overrides group defaults)
export interface ServerLaunchConfig {
  sourceServerId: string;
  instanceId?: string;
  instanceName?: string;
  tags?: Record<string, string>;
  useGroupDefaults: boolean;
  launchTemplate: Partial<LaunchConfig>;
  effectiveConfig?: LaunchConfig;
}

// Result from IP validation endpoint
export interface IPValidationResult {
  valid: boolean;
  ip: string;
  subnetId: string;
  error?: string;
  message?: string;
  details?: {
    inCidrRange?: boolean;
    notReserved?: boolean;
    available?: boolean;
    subnetCidr?: string;
  };
  conflictingResource?: {
    type: string;
    id: string;
    name?: string;
    isDrsResource?: boolean;
  };
}

// EC2 Dropdown option types
export interface SubnetOption {
  value: string;
  label: string;
  vpcId: string;
  az: string;
  cidr: string;
}

export interface SecurityGroupOption {
  value: string;
  label: string;
  name: string;
  vpcId: string;
  description: string;
}

export interface InstanceProfileOption {
  value: string;
  label: string;
  arn: string;
}

export interface InstanceTypeOption {
  value: string;
  label: string;
  vcpus: number;
  memoryGb: number;
}

// Server resolved from tag-based Protection Group
export interface ResolvedServer {
  sourceServerID: string;  // Fixed: uppercase 'ID' to match DRSServer
  hostname: string;
  fqdn?: string;
  nameTag?: string;
  sourceInstanceId?: string;
  sourceIp?: string;
  sourceMac?: string;
  sourceRegion?: string;
  sourceAccount?: string;
  os?: string;
  state?: string;
  replicationState: string;
  lagDuration?: string;
  lastSeen?: string;
  lastLaunchType?: string;
  lastLaunchStatus?: string;
  lastLaunchTime?: string;
  replicatedStorageBytes?: number;
  sourceAvailabilityZone?: string;
  targetAvailabilityZone?: string;
  hardware?: {
    cpus?: Array<{
      modelName: string;
      cores: number;
    }>;
    totalCores?: number;
    ramBytes?: number;
    ramGiB?: number;
    disks?: Array<{
      deviceName: string;
      bytes: number;
      sizeGiB: number;
    }>;
    totalDiskGiB?: number;
  };
  networkInterfaces?: Array<{
    ips: string[];
    macAddress: string;
    isPrimary: boolean;
  }>;
  drsTags?: Record<string, string>;
  tags: Record<string, string>;
  assignedToProtectionGroup?: {
    protectionGroupId: string;
    protectionGroupName: string;
  } | null;
  selectable?: boolean;
}

export interface CreateProtectionGroupRequest {
  groupName: string;  // API now expects camelCase
  description?: string;
  region: string;
  serverSelectionTags?: Record<string, string>;  // Tag filters for server discovery
  sourceServerIds?: string[];  // Explicit server IDs (legacy)
  launchConfig?: LaunchConfig;  // EC2 launch settings
  servers?: ServerLaunchConfig[];  // Per-server launch configurations
  accountId?: string;
  owner?: string;
}

export interface UpdateProtectionGroupRequest {
  groupName?: string;  // API now expects camelCase
  description?: string;
  serverSelectionTags?: Record<string, string>;  // Update tag filters
  sourceServerIds?: string[];  // Explicit server IDs (legacy)
  launchConfig?: LaunchConfig;  // EC2 launch settings
  servers?: ServerLaunchConfig[];  // Per-server launch configurations
  version?: number;  // Optimistic locking - must match current version
}

// ============================================================================
// Recovery Plan Types
// ============================================================================

export interface RecoveryPlan {
  planId: string;  // Database primary key
  planName: string;  // Recovery plan name
  description?: string;
  protectionGroupId: string;
  protectionGroupName?: string;
  waves: Wave[];
  createdDate: string | number;  // Creation timestamp
  lastModifiedDate: string;  // Last update timestamp
  createdBy?: string;
  status?: 'draft' | 'active' | 'archived';
  lastExecutionId?: string;
  lastExecutionStatus?: ExecutionStatus;
  lastExecutedAt?: string;
  lastStartTime?: number; // Unix timestamp
  lastEndTime?: number; // Unix timestamp
  // Server conflict detection - prevents starting execution when servers are in use by another plan
  hasServerConflict?: boolean;
  conflictInfo?: {
    hasConflict: boolean;
    conflictingServers: string[];
    conflictingExecutionId?: string;
    conflictingPlanId?: string;
    conflictingStatus?: string;
    reason?: string;
  };
  // Optimistic locking version - incremented on each update
  version?: number;
}

export interface Wave {
  waveNumber: number;
  waveName: string;
  waveDescription?: string;
  serverIds: string[];
  serverCount?: number;
  // executionType removed - backend ignores this field, all within-wave execution
  // is parallel with DRS-safe delays (15s between servers). Use dependsOnWaves for sequential operations.
  dependsOnWaves?: number[];
  pauseBeforeWave?: boolean;  // If true, execution pauses before starting this wave (requires manual resume)
  protectionGroupIds: string[];  // Required - wave can have multiple Protection Groups
  protectionGroupId?: string;  // Backward compatibility - single PG (deprecated, use protectionGroupIds)
  preWaveActions?: WaveAction[];
  postWaveActions?: WaveAction[];
  healthCheckConfig?: HealthCheckConfig;
  rollbackConfig?: RollbackConfig;
}

export interface WaveAction {
  actionType: 'ssm-automation' | 'lambda' | 'wait' | 'approval';
  actionName: string;
  parameters?: Record<string, unknown>;
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
  version?: number;  // Optimistic locking - must match current version
}

// ============================================================================
// Execution Types
// ============================================================================

export type ExecutionStatus =
  | 'pending'
  | 'in_progress'
  | 'running'
  | 'started'
  | 'polling'
  | 'launching'
  | 'initiated'
  | 'completed'
  | 'failed'
  | 'rolled_back'
  | 'cancelled'
  | 'cancelling'
  | 'paused';

export interface Execution {
  executionId: string;
  planId: string;  // Database field
  recoveryPlanId: string;  // API alias for frontend compatibility
  planName?: string;  // Database field
  recoveryPlanName?: string;  // API alias for frontend compatibility
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
  metadata?: Record<string, unknown>;
  pausedBeforeWave?: number;  // Wave number that execution is paused before (0-indexed)
  terminationMetadata?: {
    canTerminate: boolean;
    reason?: string;
    hasRecoveryInstances: boolean;
  };
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
  sourceIp?: string;          // Source server IP address
  sourceRegion?: string;      // Source region (where server is replicating from)
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
  launchTime?: string | number; // FIXED: Add missing launchTime field (Unix timestamp or ISO string)
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
  output?: unknown;
  error?: ExecutionError;
}

export interface HealthCheckResult {
  checkName: string;
  status: 'passed' | 'failed' | 'warning';
  timestamp: string;
  message?: string;
  details?: Record<string, unknown>;
}

export interface ExecutionError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface ExecuteRecoveryPlanRequest {
  planId: string;  // Database field
  recoveryPlanId?: string;  // API alias for backward compatibility
  executionType: 'DRILL' | 'RECOVERY';  // Required - DRILL or RECOVERY only
  dryRun?: boolean;
  skipHealthChecks?: boolean;
  startFromWave?: number;
  parameters?: Record<string, unknown>;
  executedBy?: string;  // Added for backend compatibility
  topicArn?: string;    // Added for backend SNS notifications
}

// Invocation source types for unified orchestration
export type InvocationSource = 'UI' | 'CLI' | 'SSM' | 'STEPFUNCTIONS' | 'API';

export interface InvocationDetails {
  userEmail?: string;
  userId?: string;
  scheduleRuleName?: string;
  scheduleExpression?: string;
  ssmDocumentName?: string;
  ssmExecutionId?: string;
  parentStepFunctionArn?: string;
  parentExecutionId?: string;
  apiKeyId?: string;
  correlationId?: string;
  iamUser?: string;
}

export interface ExecutionListItem {
  executionId: string;
  planId: string;  // Database field
  recoveryPlanId: string;  // API alias for frontend compatibility
  planName?: string;  // Database field
  recoveryPlanName: string;  // API alias for frontend compatibility
  status: ExecutionStatus;
  startTime: string;
  endTime?: string;
  duration?: number;
  currentWave?: number;
  totalWaves: number;
  executedBy?: string;
  executionType?: 'DRILL' | 'RECOVERY';  // Execution type (DRILL or RECOVERY)
  selectionMode?: 'TAGS' | 'PLAN';  // Server selection mode (tag-based or plan-based)
  hasActiveDrsJobs?: boolean;  // True if cancelled execution still has active DRS jobs
  waves?: Array<{ status?: string }>;  // Wave status array for progress calculation
  // Unified orchestration fields
  invocationSource?: InvocationSource;
  invocationDetails?: InvocationDetails;
  initiatedBy?: string;
}

// ============================================================================
// Job Logs Types (Enhanced DRS Status Display)
// ============================================================================

export interface JobLogsResponse {
  executionId: string;
  jobLogs: Array<{
    waveNumber: number;
    jobId: string;
    events: Array<{
      event: string;
      eventData: Record<string, unknown>;
      logDateTime: string;
      sourceServerId?: string;
      error?: string;
      conversionServerId?: string;
    }>;
    error?: string;
  }>;
}

export interface JobLogEvent {
  event: string;
  eventData: Record<string, unknown>;
  logDateTime: string;
  sourceServerId?: string;
  error?: string;
  conversionServerId?: string;
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
  details?: Record<string, unknown>;
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
  fqdn?: string;
  nameTag?: string;
  sourceInstanceId?: string;
  sourceIp?: string;
  sourceMac?: string;
  sourceRegion?: string;
  sourceAccount?: string;
  sourceAvailabilityZone?: string;
  targetAvailabilityZone?: string;
  os?: string;
  state: string;
  replicationState: string;
  lagDuration: string;
  lastSeen: string;
  lastLaunchResult?: string;
  lastLaunchType?: string;
  lastLaunchStatus?: string;
  lastLaunchTime?: string;
  replicatedStorageBytes?: number;
  hardware?: {
    cpus?: Array<{
      modelName: string;
      cores: number;
    }>;
    totalCores?: number;
    ramBytes?: number;
    ramGiB?: number;
    disks?: Array<{
      deviceName: string;
      bytes: number;
      sizeGiB: number;
    }>;
    totalDiskGiB?: number;
  };
  networkInterfaces?: Array<{
    ips: string[];
    macAddress: string;
    isPrimary: boolean;
  }>;
  drsTags?: Record<string, string>;
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
  attributes?: Record<string, unknown>;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error?: string;
}
