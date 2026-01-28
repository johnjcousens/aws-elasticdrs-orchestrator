// DRS Permission definitions (matching backend)
export enum DRSPermission {
  // Account Management
  REGISTER_ACCOUNTS = 'register_accounts',
  DELETE_ACCOUNTS = 'delete_accounts',
  MODIFY_ACCOUNTS = 'modify_accounts',
  VIEW_ACCOUNTS = 'view_accounts',
  
  // Recovery Operations
  START_RECOVERY = 'start_recovery',
  STOP_RECOVERY = 'stop_recovery',
  TERMINATE_INSTANCES = 'terminate_instances',
  VIEW_EXECUTIONS = 'view_executions',
  
  // Protection Groups
  CREATE_PROTECTION_GROUPS = 'create_protection_groups',
  DELETE_PROTECTION_GROUPS = 'delete_protection_groups',
  MODIFY_PROTECTION_GROUPS = 'modify_protection_groups',
  VIEW_PROTECTION_GROUPS = 'view_protection_groups',
  
  // Recovery Plans
  CREATE_RECOVERY_PLANS = 'create_recovery_plans',
  DELETE_RECOVERY_PLANS = 'delete_recovery_plans',
  MODIFY_RECOVERY_PLANS = 'modify_recovery_plans',
  VIEW_RECOVERY_PLANS = 'view_recovery_plans',
  
  // Configuration Management
  EXPORT_CONFIGURATION = 'export_configuration',
  IMPORT_CONFIGURATION = 'import_configuration',
}

// DRS Role definitions (matching backend)
export enum DRSRole {
  DRS_ORCHESTRATION_ADMIN = 'DRSOrchestrationAdmin',
  DRS_RECOVERY_MANAGER = 'DRSRecoveryManager',
  DRS_PLAN_MANAGER = 'DRSPlanManager',
  DRS_OPERATOR = 'DRSOperator',
  DRS_READ_ONLY = 'DRSReadOnly',
}

// Role-Permission Matrix (matching backend exactly)
export const ROLE_PERMISSIONS: Record<DRSRole, DRSPermission[]> = {
  [DRSRole.DRS_ORCHESTRATION_ADMIN]: [
    // Account Management - Full access
    DRSPermission.REGISTER_ACCOUNTS,
    DRSPermission.DELETE_ACCOUNTS,
    DRSPermission.MODIFY_ACCOUNTS,
    DRSPermission.VIEW_ACCOUNTS,
    // Recovery Operations - Full access
    DRSPermission.START_RECOVERY,
    DRSPermission.STOP_RECOVERY,
    DRSPermission.TERMINATE_INSTANCES,
    DRSPermission.VIEW_EXECUTIONS,
    // Protection Groups - Full access
    DRSPermission.CREATE_PROTECTION_GROUPS,
    DRSPermission.DELETE_PROTECTION_GROUPS,
    DRSPermission.MODIFY_PROTECTION_GROUPS,
    DRSPermission.VIEW_PROTECTION_GROUPS,
    // Recovery Plans - Full access
    DRSPermission.CREATE_RECOVERY_PLANS,
    DRSPermission.DELETE_RECOVERY_PLANS,
    DRSPermission.MODIFY_RECOVERY_PLANS,
    DRSPermission.VIEW_RECOVERY_PLANS,
    // Configuration Management - Full access
    DRSPermission.EXPORT_CONFIGURATION,
    DRSPermission.IMPORT_CONFIGURATION,
  ],
  
  [DRSRole.DRS_RECOVERY_MANAGER]: [
    // Account Management - Can register and modify, but not delete accounts
    DRSPermission.REGISTER_ACCOUNTS,
    DRSPermission.MODIFY_ACCOUNTS,
    DRSPermission.VIEW_ACCOUNTS,
    // Recovery Operations - Full recovery access
    DRSPermission.START_RECOVERY,
    DRSPermission.STOP_RECOVERY,
    DRSPermission.TERMINATE_INSTANCES,
    DRSPermission.VIEW_EXECUTIONS,
    // Protection Groups - Full access
    DRSPermission.CREATE_PROTECTION_GROUPS,
    DRSPermission.DELETE_PROTECTION_GROUPS,
    DRSPermission.MODIFY_PROTECTION_GROUPS,
    DRSPermission.VIEW_PROTECTION_GROUPS,
    // Recovery Plans - Full access
    DRSPermission.CREATE_RECOVERY_PLANS,
    DRSPermission.DELETE_RECOVERY_PLANS,
    DRSPermission.MODIFY_RECOVERY_PLANS,
    DRSPermission.VIEW_RECOVERY_PLANS,
    // Configuration Management - Full access
    DRSPermission.EXPORT_CONFIGURATION,
    DRSPermission.IMPORT_CONFIGURATION,
  ],
  
  [DRSRole.DRS_PLAN_MANAGER]: [
    // Account Management - View only
    DRSPermission.VIEW_ACCOUNTS,
    // Recovery Operations - Can start/stop but not terminate instances
    DRSPermission.START_RECOVERY,
    DRSPermission.STOP_RECOVERY,
    DRSPermission.VIEW_EXECUTIONS,
    // Protection Groups - Full access
    DRSPermission.CREATE_PROTECTION_GROUPS,
    DRSPermission.DELETE_PROTECTION_GROUPS,
    DRSPermission.MODIFY_PROTECTION_GROUPS,
    DRSPermission.VIEW_PROTECTION_GROUPS,
    // Recovery Plans - Full access
    DRSPermission.CREATE_RECOVERY_PLANS,
    DRSPermission.DELETE_RECOVERY_PLANS,
    DRSPermission.MODIFY_RECOVERY_PLANS,
    DRSPermission.VIEW_RECOVERY_PLANS,
  ],
  
  [DRSRole.DRS_OPERATOR]: [
    // Account Management - View only
    DRSPermission.VIEW_ACCOUNTS,
    // Recovery Operations - Can execute but not terminate instances
    DRSPermission.START_RECOVERY,
    DRSPermission.STOP_RECOVERY,
    DRSPermission.VIEW_EXECUTIONS,
    // Protection Groups - View and modify existing, but not create/delete
    DRSPermission.MODIFY_PROTECTION_GROUPS,
    DRSPermission.VIEW_PROTECTION_GROUPS,
    // Recovery Plans - View and modify existing, but not create/delete
    DRSPermission.MODIFY_RECOVERY_PLANS,
    DRSPermission.VIEW_RECOVERY_PLANS,
  ],
  
  [DRSRole.DRS_READ_ONLY]: [
    // Account Management - View only
    DRSPermission.VIEW_ACCOUNTS,
    // Recovery Operations - View only
    DRSPermission.VIEW_EXECUTIONS,
    // Protection Groups - View only
    DRSPermission.VIEW_PROTECTION_GROUPS,
    // Recovery Plans - View only
    DRSPermission.VIEW_RECOVERY_PLANS,
  ],
};

export interface PermissionsContextType {
  userRoles: DRSRole[];
  userPermissions: DRSPermission[];
  hasPermission: (permission: DRSPermission) => boolean;
  hasAnyPermission: (permissions: DRSPermission[]) => boolean;
  hasRole: (role: DRSRole) => boolean;
  isLoading: boolean;
  canManageAccounts: boolean;
  canTerminateInstances: boolean;
  canCreateResources: boolean;
  canDeleteResources: boolean;
}