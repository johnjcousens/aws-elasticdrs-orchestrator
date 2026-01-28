import { DRSRole } from '../types/permissions';

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