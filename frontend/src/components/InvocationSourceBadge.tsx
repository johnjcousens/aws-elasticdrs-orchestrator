// Copyright Amazon.com and Affiliates. All rights reserved.
// This deliverable is considered Developed Content as defined in the AWS Service Terms.

/**
 * InvocationSourceBadge Component
 * Displays the source of an execution (UI, CLI, Scheduled, SSM, etc.)
 */

import React from 'react';
import { Badge, Icon } from '@cloudscape-design/components';
import type { InvocationSource, InvocationDetails } from '../types';

interface InvocationSourceBadgeProps {
  source: InvocationSource | string;
  details?: InvocationDetails;
  showDetails?: boolean;
}

interface SourceConfig {
  color: 'blue' | 'grey' | 'green' | 'red';
  icon: string;
  label: string;
}

const SOURCE_CONFIG: Record<string, SourceConfig> = {
  UI: { color: 'blue', icon: 'user-profile', label: 'UI' },
  CLI: { color: 'grey', icon: 'script', label: 'CLI' },
  EVENTBRIDGE: { color: 'green', icon: 'calendar', label: 'Scheduled' },
  SSM: { color: 'blue', icon: 'settings', label: 'SSM' },
  STEPFUNCTIONS: { color: 'blue', icon: 'share', label: 'Step Functions' },
  API: { color: 'grey', icon: 'external', label: 'API' },
};

export const InvocationSourceBadge: React.FC<InvocationSourceBadgeProps> = ({
  source,
}) => {
  const cfg = SOURCE_CONFIG[source] || SOURCE_CONFIG.API;

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', whiteSpace: 'nowrap' }}>
      <Icon name={cfg.icon as 'user-profile' | 'script' | 'calendar' | 'settings' | 'share' | 'external'} size="small" />
      <Badge color={cfg.color}>{cfg.label}</Badge>
    </span>
  );
};

export default InvocationSourceBadge;
