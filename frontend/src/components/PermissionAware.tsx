import React from 'react';
import { Button, ButtonDropdown } from '@cloudscape-design/components';
import type { ButtonProps, ButtonDropdownProps } from '@cloudscape-design/components';
import { usePermissions, DRSPermission } from '../contexts/PermissionsContext';

// Permission-aware Button component
interface PermissionAwareButtonProps extends ButtonProps {
  requiredPermission?: DRSPermission;
  requiredPermissions?: DRSPermission[];
  fallbackTooltip?: string;
}

export const PermissionAwareButton: React.FC<PermissionAwareButtonProps> = ({
  requiredPermission,
  requiredPermissions,
  fallbackTooltip,
  disabled,
  children,
  ...buttonProps
}) => {
  const { hasPermission, hasAnyPermission } = usePermissions();

  let hasRequiredPermission = true;
  let tooltipText = fallbackTooltip;

  if (requiredPermission) {
    hasRequiredPermission = hasPermission(requiredPermission);
    if (!hasRequiredPermission && !tooltipText) {
      tooltipText = `Requires ${requiredPermission.replace(/_/g, ' ')} permission`;
    }
  } else if (requiredPermissions && requiredPermissions.length > 0) {
    hasRequiredPermission = hasAnyPermission(requiredPermissions);
    if (!hasRequiredPermission && !tooltipText) {
      const permNames = requiredPermissions.map(p => p.replace(/_/g, ' ')).join(' or ');
      tooltipText = `Requires ${permNames} permission`;
    }
  }

  const isDisabled = disabled || !hasRequiredPermission;

  return (
    <Button
      {...buttonProps}
      disabled={isDisabled}
      ariaLabel={!hasRequiredPermission ? tooltipText : undefined}
    >
      {children}
    </Button>
  );
};

// Permission-aware wrapper for any component
interface PermissionWrapperProps {
  requiredPermission?: DRSPermission;
  requiredPermissions?: DRSPermission[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
  showDisabled?: boolean; // If true, shows disabled version instead of hiding
}

export const PermissionWrapper: React.FC<PermissionWrapperProps> = ({
  requiredPermission,
  requiredPermissions,
  fallback = null,
  children,
  showDisabled = false,
}) => {
  const { hasPermission, hasAnyPermission } = usePermissions();

  let hasRequiredPermission = true;

  if (requiredPermission) {
    hasRequiredPermission = hasPermission(requiredPermission);
  } else if (requiredPermissions && requiredPermissions.length > 0) {
    hasRequiredPermission = hasAnyPermission(requiredPermissions);
  }

  if (!hasRequiredPermission) {
    if (showDisabled) {
      // Clone children and add disabled prop if it's a React element
      if (React.isValidElement(children)) {
        return React.cloneElement(children as React.ReactElement<any>, {
          disabled: true,
          title: `Permission required: ${requiredPermission || requiredPermissions?.join(', ')}`
        });
      }
    }
    return <>{fallback}</>;
  }

  return <>{children}</>;
};

// Permission-aware section that shows/hides entire sections
interface PermissionSectionProps {
  requiredPermission?: DRSPermission;
  requiredPermissions?: DRSPermission[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const PermissionSection: React.FC<PermissionSectionProps> = ({
  requiredPermission,
  requiredPermissions,
  children,
  fallback = null,
}) => {
  const { hasPermission, hasAnyPermission } = usePermissions();

  let hasRequiredPermission = true;

  if (requiredPermission) {
    hasRequiredPermission = hasPermission(requiredPermission);
  } else if (requiredPermissions && requiredPermissions.length > 0) {
    hasRequiredPermission = hasAnyPermission(requiredPermissions);
  }

  return hasRequiredPermission ? <>{children}</> : <>{fallback}</>;
};

// Permission-aware ButtonDropdown component
interface PermissionAwareButtonDropdownItem {
  id: string;
  text: string;
  iconName?: string;
  disabled?: boolean;
  disabledReason?: string;
  requiredPermission?: DRSPermission;
  requiredPermissions?: DRSPermission[];
}

interface PermissionAwareButtonDropdownProps extends Omit<ButtonDropdownProps, 'items'> {
  items: PermissionAwareButtonDropdownItem[];
}

export const PermissionAwareButtonDropdown: React.FC<PermissionAwareButtonDropdownProps> = ({
  items,
  ...buttonDropdownProps
}) => {
  const { hasPermission, hasAnyPermission } = usePermissions();

  // Filter and modify items based on permissions
  const processedItems = items.map(item => {
    let hasRequiredPermission = true;
    let permissionTooltip = '';

    if (item.requiredPermission) {
      hasRequiredPermission = hasPermission(item.requiredPermission);
      if (!hasRequiredPermission) {
        permissionTooltip = `Requires ${item.requiredPermission.replace(/_/g, ' ')} permission`;
      }
    } else if (item.requiredPermissions && item.requiredPermissions.length > 0) {
      hasRequiredPermission = hasAnyPermission(item.requiredPermissions);
      if (!hasRequiredPermission) {
        const permNames = item.requiredPermissions.map(p => p.replace(/_/g, ' ')).join(' or ');
        permissionTooltip = `Requires ${permNames} permission`;
      }
    }

    return {
      id: item.id,
      text: item.text,
      iconName: item.iconName,
      disabled: item.disabled || !hasRequiredPermission,
      disabledReason: !hasRequiredPermission ? permissionTooltip : item.disabledReason,
    };
  }) as ButtonDropdownProps['items'];

  return (
    <ButtonDropdown
      {...buttonDropdownProps}
      items={processedItems}
    />
  );
};

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