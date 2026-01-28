/**
 * ServerConfigBadge Component
 * 
 * Displays a badge indicating whether a server uses custom configuration
 * or protection group defaults. Shows a tooltip with customized fields.
 */

import React from 'react';
import { Badge, Popover, Box } from '@cloudscape-design/components';

export interface ServerConfigBadgeProps {
  /** Whether the server has custom configuration */
  hasCustomConfig: boolean;
  /** List of customized field names (for tooltip) */
  customFields?: string[];
}

/**
 * Maps internal field names to user-friendly display names
 */
const FIELD_DISPLAY_NAMES: Record<string, string> = {
  staticPrivateIp: 'Static Private IP',
  subnetId: 'Subnet',
  securityGroupIds: 'Security Groups',
  instanceType: 'Instance Type',
  instanceProfileName: 'IAM Instance Profile',
  associatePublicIp: 'Public IP Assignment',
  monitoring: 'Detailed Monitoring',
  ebsOptimized: 'EBS Optimized',
  disableApiTermination: 'Termination Protection',
  tags: 'Resource Tags',
};

/**
 * ServerConfigBadge Component
 * 
 * Displays a visual indicator for server configuration status with tooltip.
 * 
 * @param hasCustomConfig - Whether the server has custom configuration
 * @param customFields - Array of customized field names
 */
export const ServerConfigBadge: React.FC<ServerConfigBadgeProps> = ({
  hasCustomConfig,
  customFields = [],
}) => {
  // Prepare tooltip content
  const tooltipContent = hasCustomConfig ? (
    <Box variant="div">
      <Box variant="strong" fontSize="body-s">
        Customized fields:
      </Box>
      <Box margin={{ top: 'xs' }}>
        <ul>
        {customFields.length > 0 ? (
          customFields.map((field) => (
            <li key={field}>
              {FIELD_DISPLAY_NAMES[field] || field}
            </li>
          ))
        ) : (
          <li>Custom configuration applied</li>
        )}
        </ul>
      </Box>
    </Box>
  ) : (
    <Box variant="div">
      Using protection group defaults
    </Box>
  );

  // Badge configuration
  const badgeColor = hasCustomConfig ? 'blue' : 'grey';
  const badgeText = hasCustomConfig ? 'Custom' : 'Default';

  return (
    <Popover
      dismissButton={false}
      position="top"
      size="small"
      triggerType="custom"
      content={tooltipContent}
    >
      <Badge color={badgeColor}>{badgeText}</Badge>
    </Popover>
  );
};

export default ServerConfigBadge;
