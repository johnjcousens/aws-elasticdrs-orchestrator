/**
 * Staging Accounts Management Type Definitions
 *
 * These types support the Staging Accounts Management feature, which extends
 * DRS replication capacity beyond the 300-server limit by enabling multiple
 * staging accounts alongside the target account.
 *
 * FEATURE OVERVIEW:
 * - Each account provides 300 servers of replication capacity
 * - Staging accounts are stored in Target Accounts DynamoDB table
 * - Capacity queries execute concurrently across all accounts
 * - Status indicators and warnings based on capacity thresholds
 *
 * REQUIREMENTS VALIDATED:
 * - 4.3: CombinedCapacityData interface
 * - 5.2: AccountCapacity interface with regional breakdown
 * - 1.4: ValidationResult interface
 * - 8.2: StagingAccount interface with all required fields
 */

// ============================================================================
// Staging Account Types
// ============================================================================

/**
 * Staging account configuration.
 *
 * Represents an additional AWS account configured to provide extended
 * DRS replication capacity for a target account.
 */
export interface StagingAccount {
  /** AWS account ID (12-digit string) */
  accountId: string;

  /** Human-readable name for the staging account */
  accountName: string;

  /** IAM role ARN for cross-account access */
  roleArn: string;

  /** External ID for role assumption security */
  externalId: string;

  /** ISO 8601 timestamp when staging account was added */
  addedAt?: string;

  /** User/system that added the staging account */
  addedBy?: string;

  /** Connection status (populated by UI after validation) */
  status?: "connected" | "error" | "validating";

  /** Total server count (populated by capacity queries) */
  serverCount?: number;

  /** Replicating server count (populated by capacity queries) */
  replicatingCount?: number;
}

/**
 * Target account with staging accounts configuration.
 *
 * Extends the base target account with staging accounts list.
 */
export interface TargetAccount {
  /** AWS account ID (12-digit string) */
  accountId: string;

  /** Human-readable name for the target account */
  accountName: string;

  /** IAM role ARN for cross-account access (optional for same-account) */
  roleArn?: string;

  /** External ID for role assumption (optional) */
  externalId?: string;

  /** List of staging account configurations */
  stagingAccounts: StagingAccount[];

  /** Account status */
  status?: "active" | "inactive" | "error";

  /** ISO 8601 timestamp when account was created */
  createdAt?: string;

  /** ISO 8601 timestamp when account was last updated */
  updatedAt?: string;

  /** User/system that created the account */
  createdBy?: string;
}

// ============================================================================
// Capacity Types
// ============================================================================

/**
 * Capacity status levels based on utilization thresholds.
 *
 * Status thresholds:
 * - OK: 0-200 servers (0-67%)
 * - INFO: 200-225 servers (67-75%)
 * - WARNING: 225-250 servers (75-83%)
 * - CRITICAL: 250-280 servers (83-93%)
 * - HYPER-CRITICAL: 280-300 servers (93-100%)
 */
export type CapacityStatus =
  | "OK"
  | "INFO"
  | "WARNING"
  | "CRITICAL"
  | "HYPER-CRITICAL";

/**
 * Account type identifier.
 */
export type AccountType = "target" | "staging";

/**
 * Regional capacity breakdown for a single region.
 *
 * Shows server counts per AWS region within an account.
 */
export interface RegionalCapacity {
  /** AWS region code (e.g., 'us-east-1') */
  region: string;

  /** Total servers in this region */
  totalServers: number;

  /** Replicating servers in this region */
  replicatingServers: number;
}

/**
 * Per-account capacity metrics with regional breakdown.
 *
 * Provides detailed capacity information for a single account
 * (target or staging) including status and warnings.
 *
 * Validates: Requirement 5.2
 */
export interface AccountCapacity {
  /** AWS account ID */
  accountId: string;

  /** Human-readable account name */
  accountName: string;

  /** Account type (target or staging) */
  accountType: AccountType;

  /** Number of servers actively replicating */
  replicatingServers: number;

  /** Total servers (replicating + other states) */
  totalServers: number;

  /** Maximum replication capacity (always 300) */
  maxReplicating: number;

  /** Percentage of capacity used (0-100) */
  percentUsed: number;

  /** Available replication slots remaining */
  availableSlots: number;

  /** Capacity status based on thresholds */
  status: CapacityStatus;

  /** Regional breakdown of server counts */
  regionalBreakdown: RegionalCapacity[];

  /** Account-specific warnings */
  warnings: string[];

  /** Whether account is accessible (false if role assumption failed) */
  accessible?: boolean;

  /** Error message if account query failed */
  error?: string;
}

/**
 * Recovery capacity metrics for target account.
 *
 * Shows recovery instance capacity (4,000 instance limit).
 * Only applies to target account, not staging accounts.
 */
export interface RecoveryCapacity {
  /** Current number of servers (potential recovery instances) */
  currentServers: number;

  /** Maximum recovery instances allowed (4,000) */
  maxRecoveryInstances: number;

  /** Percentage of recovery capacity used (0-100) */
  percentUsed: number;

  /** Available recovery instance slots remaining */
  availableSlots: number;

  /** Recovery capacity status (OK, WARNING, CRITICAL) */
  status: "OK" | "WARNING" | "CRITICAL";
}

/**
 * Combined capacity data across all accounts.
 *
 * Aggregates capacity metrics from target account and all staging accounts,
 * providing a unified view of total replication capacity.
 *
 * Validates: Requirement 4.3
 */
export interface CombinedCapacityData {
  /** Combined metrics across all accounts */
  combined: {
    /** Total replicating servers across all accounts */
    totalReplicating: number;

    /** Maximum replication capacity (num_accounts × 300) */
    maxReplicating: number;

    /** Percentage of combined capacity used (0-100) */
    percentUsed: number;

    /** Combined capacity status */
    status: CapacityStatus;

    /** Status message describing capacity state */
    message: string;

    /** Available slots across all accounts */
    availableSlots: number;
  };

  /** Per-account capacity breakdown */
  accounts: AccountCapacity[];

  /** Recovery capacity metrics (target account only) */
  recoveryCapacity: RecoveryCapacity;

  /** Concurrent jobs metrics */
  concurrentJobs: {
    current: number;
    max: number;
    available: number;
  };

  /** Servers in active jobs metrics */
  serversInJobs: {
    current: number;
    max: number;
    available: number;
  };

  /** System-wide warnings and recommendations */
  warnings: string[];

  /** Timestamp when capacity data was retrieved */
  timestamp?: string;
}

// ============================================================================
// Validation Types
// ============================================================================

/**
 * Staging account validation result.
 *
 * Returned by the validate_staging_account API endpoint after checking
 * role accessibility and DRS initialization status.
 *
 * Validates: Requirement 1.4
 */
export interface ValidationResult {
  /** Whether validation passed all checks */
  valid: boolean;

  /** Whether IAM role is accessible via AssumeRole */
  roleAccessible: boolean;

  /** Whether DRS is initialized in the staging account */
  drsInitialized: boolean;

  /** Current total servers in staging account */
  currentServers: number;

  /** Current replicating servers in staging account */
  replicatingServers: number;

  /** Projected total replicating servers after adding this staging account */
  totalAfter: number;

  /** Error message if validation failed */
  error?: string;

  /** Additional validation details */
  details?: {
    /** Regions where DRS is initialized */
    initializedRegions?: string[];

    /** Regions where DRS is not initialized */
    uninitializedRegions?: string[];

    /** Role assumption error code */
    roleErrorCode?: string;

    /** DRS initialization error */
    drsError?: string;
  };
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Request to validate staging account access.
 */
export interface ValidateStagingAccountRequest {
  /** AWS account ID to validate */
  accountId: string;

  /** IAM role ARN for cross-account access */
  roleArn: string;

  /** External ID for role assumption */
  externalId: string;

  /** AWS region to check DRS initialization */
  region: string;
}

/**
 * Request to add staging account to target account.
 */
export interface AddStagingAccountRequest {
  /** Target account ID to add staging account to */
  targetAccountId: string;

  /** Staging account configuration */
  stagingAccount: {
    accountId: string;
    accountName: string;
    roleArn: string;
    externalId: string;
  };

  /** User adding the staging account */
  addedBy?: string;
}

/**
 * Response from add/remove staging account operations.
 */
export interface StagingAccountOperationResponse {
  /** Whether operation succeeded */
  success: boolean;

  /** Operation result message */
  message: string;

  /** Updated list of staging accounts */
  stagingAccounts: StagingAccount[];

  /** Error details if operation failed */
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

/**
 * Request to remove staging account from target account.
 */
export interface RemoveStagingAccountRequest {
  /** Target account ID */
  targetAccountId: string;

  /** Staging account ID to remove */
  stagingAccountId: string;
}

/**
 * Request to get combined capacity across all accounts.
 */
export interface GetCombinedCapacityRequest {
  /** Target account ID */
  targetAccountId: string;

  /** Whether to include detailed regional breakdown */
  includeRegionalBreakdown?: boolean;
}

// ============================================================================
// UI Component Props Types
// ============================================================================

/**
 * Props for CapacityDashboard component.
 */
export interface CapacityDashboardProps {
  /** Target account ID to display capacity for */
  targetAccountId: string;

  /** Refresh interval in milliseconds (default: 30000) */
  refreshInterval?: number;

  /** Whether to auto-refresh capacity data */
  autoRefresh?: boolean;

  /** Callback when capacity data is loaded */
  onCapacityLoaded?: (data: CombinedCapacityData) => void;

  /** Callback when error occurs */
  onError?: (error: Error) => void;
}

/**
 * Props for TargetAccountSettingsModal component.
 */
export interface TargetAccountSettingsModalProps {
  /** Target account to edit */
  targetAccount: TargetAccount;

  /** Whether modal is visible */
  visible: boolean;

  /** Callback when modal is dismissed */
  onDismiss: () => void;

  /** Callback when account is saved */
  onSave: (updatedAccount: TargetAccount) => Promise<void>;
}

/**
 * Props for AddStagingAccountModal component.
 */
export interface AddStagingAccountModalProps {
  /** Whether modal is visible */
  visible: boolean;

  /** Callback when modal is dismissed */
  onDismiss: () => void;

  /** Callback when staging account is added */
  onAdd: (stagingAccount: StagingAccount) => void;

  /** Target account ID */
  targetAccountId: string;
}

/**
 * Props for CapacityDetailsModal component.
 */
export interface CapacityDetailsModalProps {
  /** Capacity data to display */
  capacityData: CombinedCapacityData;

  /** Whether modal is visible */
  visible: boolean;

  /** Callback when modal is dismissed */
  onDismiss: () => void;
}

// ============================================================================
// Form State Types
// ============================================================================

/**
 * Form data for adding a staging account.
 */
export interface AddStagingAccountFormData {
  /** AWS account ID (12 digits) */
  accountId: string;

  /** Human-readable account name */
  accountName: string;

  /** IAM role ARN */
  roleArn: string;

  /** External ID for role assumption */
  externalId: string;

  /** AWS region to validate DRS initialization */
  region: string;
}

/**
 * Form validation errors.
 */
export interface StagingAccountFormErrors {
  accountId?: string;
  accountName?: string;
  roleArn?: string;
  externalId?: string;
  region?: string;
}

/**
 * State for AddStagingAccountModal component.
 */
export interface AddStagingAccountModalState {
  /** Form input data */
  formData: AddStagingAccountFormData;

  /** Whether validation is in progress */
  validating: boolean;

  /** Validation result (null if not validated yet) */
  validationResult: ValidationResult | null;

  /** Form validation errors */
  errors: StagingAccountFormErrors;

  /** Whether add operation is in progress */
  adding: boolean;
}

/**
 * State for TargetAccountSettingsModal component.
 */
export interface TargetAccountSettingsModalState {
  /** Form data (editable copy of target account) */
  formData: TargetAccount;

  /** Whether add staging account modal is visible */
  showAddStaging: boolean;

  /** Whether save operation is in progress */
  saving: boolean;

  /** Error message if operation failed */
  error: string | null;

  /** Staging account being removed (for confirmation dialog) */
  removingAccount: StagingAccount | null;
}

/**
 * State for CapacityDashboard component.
 */
export interface CapacityDashboardState {
  /** Whether capacity data is loading */
  loading: boolean;

  /** Error message if load failed */
  error: string | null;

  /** Capacity data (null if not loaded yet) */
  capacityData: CombinedCapacityData | null;

  /** Timestamp of last successful refresh */
  lastRefresh: Date | null;

  /** Whether auto-refresh is enabled */
  autoRefreshEnabled: boolean;
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Capacity threshold configuration.
 */
export interface CapacityThresholds {
  /** OK threshold (0-67%) */
  ok: number;

  /** INFO threshold (67-75%) */
  info: number;

  /** WARNING threshold (75-83%) */
  warning: number;

  /** CRITICAL threshold (83-93%) */
  critical: number;

  /** HYPER-CRITICAL threshold (93-100%) */
  hyperCritical: number;
}

/**
 * Default capacity thresholds.
 */
export const DEFAULT_CAPACITY_THRESHOLDS: CapacityThresholds = {
  ok: 200, // 67% of 300
  info: 225, // 75% of 300
  warning: 250, // 83% of 300
  critical: 280, // 93% of 300
  hyperCritical: 300, // 100% of 300
};

/**
 * Operational and hard limits for DRS capacity.
 */
export const CAPACITY_LIMITS = {
  /** Operational limit per account (leaves 50-server safety buffer) */
  OPERATIONAL_LIMIT: 250,

  /** AWS-enforced hard limit per account */
  HARD_LIMIT: 300,

  /** Maximum recovery instances in target account */
  RECOVERY_LIMIT: 4000,
} as const;
