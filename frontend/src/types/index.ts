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
  
  // Tag-based server selection - servers matching ALL tags are included at execution time
  serverSelectionTags?: Record<string, string>;
  
  // Legacy: Explicit server IDs (for backward compatibility with existing PGs)
  sourceServerIds?: string[];
  
  // EC2 Launch Configuration - applied to all servers in this group
  launchConfig?: LaunchConfig;
  
  createdAt: number;
  updatedAt: number;
  accountId?: string;
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
  SubnetId?: string;
  SecurityGroupIds?: string[];
  InstanceProfileName?: string;
  InstanceType?: string;
  
  // DRS Launch Configuration settings
  TargetInstanceTypeRightSizingMethod?: 'NONE' | 'BASIC' | 'IN_AWS';
  LaunchIntoInstanceProperties?: {
    launchIntoEC2InstanceID?: string;
  };
  BootMode?: 'LEGACY_BIOS' | 'UEFI' | 'USE_SOURCE';
  CopyPrivateIp?: boolean;
  CopyTags?: boolean;
  LaunchDisposition?: 'STOPPED' | 'STARTED';
  Licensing?: {
    osByol?: boolean;
  };
  PostLaunchEnabled?: boolean;
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
  sourceServerId: string;
  hostname: string;
  nameTag?: string;
  sourceInstanceId?: string;
  sourceIp?: string;
  sourceRegion?: string;
  sourceAccount?: string;
  state?: string;
  replicationState: string;
  lagDuration?: string;
  tags: Record<string, string>;
}

export interface CreateProtectionGroupRequest {
  GroupName: string;  // API expects PascalCase
  Description?: string;
  Region: string;
  ServerSelectionTags?: Record<string, string>;  // Tag filters for server discovery
  SourceServerIds?: string[];  // Explicit server IDs (legacy)
  LaunchConfig?: LaunchConfig;  // EC2 launch settings
  AccountId?: string;
  Owner?: string;
}

export interface UpdateProtectionGroupRequest {
  GroupName?: string;  // API expects PascalCase
  Description?: string;
  ServerSelectionTags?: Record<string, string>;  // Update tag filters
  SourceServerIds?: string[];  // Explicit server IDs (legacy)
  LaunchConfig?: LaunchConfig;  // EC2 launch settings
  version?: number;  // Optimistic locking - must match current version
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
  name: string;
  description?: string;
  serverIds: string[];
  serverCount?: number;
  // executionType removed - backend ignores this field, all within-wave execution
  // is parallel with DRS-safe delays (15s between servers). Use dependsOnWaves for sequential operations.
  dependsOnWaves?: number[];
  pauseBeforeWave?: boolean;  // If true, execution pauses before starting this wave (requires manual resume)
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
  pausedBeforeWave?: number;  // Wave number that execution is paused before (0-indexed)
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
  recoveryPlanId: string;
  recoveryPlanName: string;
  status: ExecutionStatus;
  startTime: string;
  endTime?: string;
  duration?: number;
  currentWave?: number;
  totalWaves: number;
  executedBy?: string;
  executionType?: 'DRILL' | 'RECOVERY';  // Execution type (DRILL or RECOVERY)
  selectionMode?: 'TAGS' | 'PLAN';  // Server selection mode (tag-based or plan-based)
  
  // Unified orchestration fields
  invocationSource?: InvocationSource;
  invocationDetails?: InvocationDetails;
  initiatedBy?: string;
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
  fqdn?: string;
  nameTag?: string;
  sourceInstanceId?: string;
  sourceIp?: string;
  sourceMac?: string;
  sourceRegion?: string;
  sourceAccount?: string;
  os?: string;
  state: string;
  replicationState: string;
  lagDuration: string;
  lastSeen: string;
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
  attributes?: Record<string, any>;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error?: string;
}
