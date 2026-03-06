// Copyright Amazon.com and Affiliates. All rights reserved.
// This deliverable is considered Developed Content as defined in the AWS Service Terms.

import { DRSPermission } from '../types/permissions';
import { usePermissions } from '../contexts/PermissionsContext';

// Hook for permission-based conditional rendering
export const usePermissionCheck = (
  requiredPermission?: DRSPermission,
  requiredPermissions?: DRSPermission[]
) => {
  const { hasPermission, hasAnyPermission } = usePermissions();

  if (requiredPermission) {
    return hasPermission(requiredPermission);
  } else if (requiredPermissions && requiredPermissions.length > 0) {
    return hasAnyPermission(requiredPermissions);
  }

  return true;
};