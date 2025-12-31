import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { fetchAuthSession } from 'aws-amplify/auth';

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
const ROLE_PERMISSIONS: Record<DRSRole, DRSPermission[]> = {
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

interface PermissionsContextType {
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

const PermissionsContext = createContext<PermissionsContextType | undefined>(undefined);

export const usePermissions = () => {
  const context = useContext(PermissionsContext);
  if (!context) {
    throw new Error('usePermissions must be used within a PermissionsProvider');
  }
  return context;
};

interface PermissionsProviderProps {
  children: React.ReactNode;
}

export const PermissionsProvider: React.FC<PermissionsProviderProps> = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [userRoles, setUserRoles] = useState<DRSRole[]>([]);
  const [userPermissions, setUserPermissions] = useState<DRSPermission[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !user) {
      setUserRoles([]);
      setUserPermissions([]);
      setIsLoading(false);
      return;
    }

    const fetchUserPermissions = async () => {
      try {
        // In Amplify v6, we need to use fetchAuthSession to get tokens
        let cognitoGroups: string[] = [];
        let jwtToken: string | null = null;
        
        try {
          const session = await fetchAuthSession();
          
          // Get the ID token (contains user claims including groups)
          if (session.tokens?.idToken) {
            const idToken = session.tokens.idToken;
            jwtToken = idToken.toString();
            
            // Extract groups from token payload
            const payload = idToken.payload;
            
            // Try different possible group claim names
            cognitoGroups = payload['cognito:groups'] as string[] || 
                           payload['groups'] as string[] || 
                           [];
          }
          
          // If no groups in ID token, try access token
          if (cognitoGroups.length === 0 && session.tokens?.accessToken) {
            const accessToken = session.tokens.accessToken;
            const payload = accessToken.payload;
            
            cognitoGroups = payload['cognito:groups'] as string[] || 
                           payload['groups'] as string[] || 
                           [];
            
            // Use access token if no ID token available
            if (!jwtToken) {
              jwtToken = accessToken.toString();
            }
          }
        } catch (sessionError) {
          console.error('Error fetching auth session:', sessionError);
        }

        // Ensure we always have an array
        const groups = Array.isArray(cognitoGroups) ? cognitoGroups : (cognitoGroups ? [cognitoGroups] : []);

        // If no groups found in JWT token, try to fetch from backend API
        if (groups.length === 0) {
          try {
            // Get API endpoint from aws-config.json (loaded by App.tsx)
            const apiEndpoint = window.location.origin.includes('localhost') 
              ? 'https://bu05wxn2ci.execute-api.us-east-1.amazonaws.com/dev'
              : 'https://bu05wxn2ci.execute-api.us-east-1.amazonaws.com/dev';
            
            if (!jwtToken) {
              throw new Error('No JWT token available');
            }
            
            const response = await fetch(`${apiEndpoint}/user/permissions`, {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${jwtToken}`,
                'Content-Type': 'application/json',
              },
            });

            if (response.ok) {
              const userData = await response.json();
              
              if (userData.roles && userData.permissions) {
                const backendRoles = userData.roles.map((role: string) => {
                  // Map backend role strings to enum values
                  const roleMapping: Record<string, DRSRole> = {
                    'DRSOrchestrationAdmin': DRSRole.DRS_ORCHESTRATION_ADMIN,
                    'DRSRecoveryManager': DRSRole.DRS_RECOVERY_MANAGER,
                    'DRSPlanManager': DRSRole.DRS_PLAN_MANAGER,
                    'DRSOperator': DRSRole.DRS_OPERATOR,
                    'DRSReadOnly': DRSRole.DRS_READ_ONLY,
                  };
                  return roleMapping[role];
                }).filter(Boolean);

                const backendPermissions = userData.permissions.map((perm: string) => {
                  // Map backend permission strings to enum values
                  return Object.values(DRSPermission).find(p => p === perm);
                }).filter(Boolean);

                setUserRoles(backendRoles);
                setUserPermissions(backendPermissions);
                setIsLoading(false);
                return;
              }
            }
          } catch (apiError) {
            // Fall back to JWT token processing
          }
        }

        // Map Cognito group names to DRS roles
        const groupToRoleMapping: Record<string, DRSRole> = {
          // New DRS Orchestration Roles
          'DRSOrchestrationAdmin': DRSRole.DRS_ORCHESTRATION_ADMIN,
          'DRSRecoveryManager': DRSRole.DRS_RECOVERY_MANAGER,
          'DRSPlanManager': DRSRole.DRS_PLAN_MANAGER,
          'DRSOperator': DRSRole.DRS_OPERATOR,
          'DRSReadOnly': DRSRole.DRS_READ_ONLY,
          
          // Legacy AWS-style role names
          'aws:admin': DRSRole.DRS_ORCHESTRATION_ADMIN,
          'aws:admin-limited': DRSRole.DRS_RECOVERY_MANAGER,
          'aws:power-user': DRSRole.DRS_PLAN_MANAGER,
          'aws:operator': DRSRole.DRS_OPERATOR,
          'aws:read-only': DRSRole.DRS_READ_ONLY,
          
          // Legacy DRS group names
          'DRS-Administrator': DRSRole.DRS_ORCHESTRATION_ADMIN,
          'DRS-Infrastructure-Admin': DRSRole.DRS_RECOVERY_MANAGER,
          'DRS-Recovery-Plan-Manager': DRSRole.DRS_PLAN_MANAGER,
          'DRS-Operator': DRSRole.DRS_OPERATOR,
          'DRS-Read-Only': DRSRole.DRS_READ_ONLY,
        };

        const roles: DRSRole[] = [];
        for (const group of groups) {
          if (group && typeof group === 'string' && group in groupToRoleMapping) {
            roles.push(groupToRoleMapping[group]);
          }
        }

        // Get all permissions for user's roles
        const permissions = new Set<DRSPermission>();
        for (const role of roles) {
          const rolePerms = ROLE_PERMISSIONS[role] || [];
          if (Array.isArray(rolePerms)) {
            rolePerms.forEach(perm => permissions.add(perm));
          }
        }

        const permissionsArray = Array.from(permissions);
        
        setUserRoles(roles);
        setUserPermissions(permissionsArray);
        setIsLoading(false);
      } catch (error) {
        console.error('Error in PermissionsProvider:', error);
        // Fallback to empty arrays
        setUserRoles([]);
        setUserPermissions([]);
        setIsLoading(false);
      }
    };

    fetchUserPermissions();
  }, [user, isAuthenticated]);

  const hasPermission = (permission: DRSPermission): boolean => {
    return Array.isArray(userPermissions) && userPermissions.includes(permission);
  };

  const hasAnyPermission = (permissions: DRSPermission[]): boolean => {
    return Array.isArray(userPermissions) && Array.isArray(permissions) && 
           permissions.some(perm => userPermissions.includes(perm));
  };

  const hasRole = (role: DRSRole): boolean => {
    return Array.isArray(userRoles) && userRoles.includes(role);
  };

  // Convenience computed properties
  const canManageAccounts = hasAnyPermission([
    DRSPermission.REGISTER_ACCOUNTS,
    DRSPermission.MODIFY_ACCOUNTS,
    DRSPermission.DELETE_ACCOUNTS
  ]);

  const canTerminateInstances = hasPermission(DRSPermission.TERMINATE_INSTANCES);

  const canCreateResources = hasAnyPermission([
    DRSPermission.CREATE_PROTECTION_GROUPS,
    DRSPermission.CREATE_RECOVERY_PLANS
  ]);

  const canDeleteResources = hasAnyPermission([
    DRSPermission.DELETE_PROTECTION_GROUPS,
    DRSPermission.DELETE_RECOVERY_PLANS,
    DRSPermission.DELETE_ACCOUNTS
  ]);

  const value: PermissionsContextType = {
    userRoles: Array.isArray(userRoles) ? userRoles : [],
    userPermissions: Array.isArray(userPermissions) ? userPermissions : [],
    hasPermission,
    hasAnyPermission,
    hasRole,
    isLoading,
    canManageAccounts,
    canTerminateInstances,
    canCreateResources,
    canDeleteResources,
  };

  return (
    <PermissionsContext.Provider value={value}>
      {children}
    </PermissionsContext.Provider>
  );
};

// Utility function to get role display name
export const getRoleDisplayName = (role: DRSRole): string => {
  const displayNames: Record<DRSRole, string> = {
    [DRSRole.DRS_ORCHESTRATION_ADMIN]: 'Orchestration Administrator',
    [DRSRole.DRS_RECOVERY_MANAGER]: 'Recovery Manager',
    [DRSRole.DRS_PLAN_MANAGER]: 'Plan Manager',
    [DRSRole.DRS_OPERATOR]: 'Operator',
    [DRSRole.DRS_READ_ONLY]: 'Read Only',
  };
  return displayNames[role] || role;
};

// Utility function to get role description
export const getRoleDescription = (role: DRSRole): string => {
  const descriptions: Record<DRSRole, string> = {
    [DRSRole.DRS_ORCHESTRATION_ADMIN]: 'Full administrative access to all DRS orchestration functions including account management',
    [DRSRole.DRS_RECOVERY_MANAGER]: 'Can execute and manage all recovery operations, register accounts, and manage infrastructure',
    [DRSRole.DRS_PLAN_MANAGER]: 'Can create, modify, and delete recovery plans and protection groups, execute recovery operations',
    [DRSRole.DRS_OPERATOR]: 'Can execute recovery operations and modify existing plans but cannot create/delete or terminate instances',
    [DRSRole.DRS_READ_ONLY]: 'View-only access to all DRS configuration, executions, and status for monitoring and compliance'
  };
  return descriptions[role] || 'Unknown role';
};