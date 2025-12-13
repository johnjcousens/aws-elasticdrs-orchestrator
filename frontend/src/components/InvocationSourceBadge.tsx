/**
 * InvocationSourceBadge Component
 * Displays the source of an execution (UI, CLI, Scheduled, SSM, etc.)
 */

import React from 'react';
import { Badge, Icon, SpaceBetween } from '@cloudscape-design/components';

export type InvocationSource = 'UI' | 'CLI' | 'EVENTBRIDGE' | 'SSM' | 'STEPFUNCTIONS' | 'API';

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
      <Icon name={cfg.icon as any} size="small" />
      <Badge color={cfg.color}>{cfg.label}</Badge>
    </span>
  );
};

export default InvocationSourceBadge;
