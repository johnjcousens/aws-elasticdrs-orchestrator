/**
 * InvocationSourceBadge Component
 * Displays the source of an execution (UI, CLI, Scheduled, SSM, etc.)
 * with appropriate icon and color coding.
 */

import React from 'react';
import { Badge, Icon, SpaceBetween, Popover, Box } from '@cloudscape-design/components';

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
  description: string;
}

const SOURCE_CONFIG: Record<string, SourceConfig> = {
  UI: {
    color: 'blue',
    icon: 'user-profile',
    label: 'UI',
    description: 'Started manually from the web interface',
  },
  CLI: {
    color: 'grey',
    icon: 'script',
    label: 'CLI',
    description: 'Started via AWS CLI or SDK',
  },
  EVENTBRIDGE: {
    color: 'green',
    icon: 'calendar',
    label: 'Scheduled',
    description: 'Started by EventBridge scheduled rule',
  },
  SSM: {
    color: 'blue',
    icon: 'settings',
    label: 'SSM',
    description: 'Started by SSM Automation runbook',
  },
  STEPFUNCTIONS: {
    color: 'blue',
    icon: 'share',
    label: 'Step Functions',
    description: 'Started by parent Step Functions workflow',
  },
  API: {
    color: 'grey',
    icon: 'external',
    label: 'API',
    description: 'Started via API Gateway',
  },
};

const getDetailContent = (source: string, details?: InvocationDetails): React.ReactNode => {
  if (!details) return null;

  switch (source) {
    case 'UI':
      return details.userEmail ? (
        <>
          <Box variant="awsui-key-label">User</Box>
          <Box>{details.userEmail}</Box>
        </>
      ) : null;

    case 'CLI':
      return (
        <>
          {details.iamUser && (
            <>
              <Box variant="awsui-key-label">IAM User</Box>
              <Box>{details.iamUser}</Box>
            </>
          )}
          {details.correlationId && (
            <>
              <Box variant="awsui-key-label">Correlation ID</Box>
              <Box>{details.correlationId}</Box>
            </>
          )}
        </>
      );

    case 'EVENTBRIDGE':
      return (
        <>
          {details.scheduleRuleName && (
            <>
              <Box variant="awsui-key-label">Rule Name</Box>
              <Box>{details.scheduleRuleName}</Box>
            </>
          )}
          {details.scheduleExpression && (
            <>
              <Box variant="awsui-key-label">Schedule</Box>
              <Box>{details.scheduleExpression}</Box>
            </>
          )}
        </>
      );

    case 'SSM':
      return (
        <>
          {details.ssmDocumentName && (
            <>
              <Box variant="awsui-key-label">Document</Box>
              <Box>{details.ssmDocumentName}</Box>
            </>
          )}
          {details.ssmExecutionId && (
            <>
              <Box variant="awsui-key-label">Execution ID</Box>
              <Box>{details.ssmExecutionId}</Box>
            </>
          )}
        </>
      );

    case 'STEPFUNCTIONS':
      return (
        <>
          {details.parentExecutionId && (
            <>
              <Box variant="awsui-key-label">Parent Execution</Box>
              <Box>{details.parentExecutionId}</Box>
            </>
          )}
          {details.parentStepFunctionArn && (
            <>
              <Box variant="awsui-key-label">State Machine</Box>
              <Box fontSize="body-s">{details.parentStepFunctionArn.split(':').pop()}</Box>
            </>
          )}
        </>
      );

    case 'API':
      return (
        <>
          {details.apiKeyId && (
            <>
              <Box variant="awsui-key-label">API Key</Box>
              <Box>{details.apiKeyId}</Box>
            </>
          )}
          {details.correlationId && (
            <>
              <Box variant="awsui-key-label">Correlation ID</Box>
              <Box>{details.correlationId}</Box>
            </>
          )}
        </>
      );

    default:
      return details.correlationId ? (
        <>
          <Box variant="awsui-key-label">Correlation ID</Box>
          <Box>{details.correlationId}</Box>
        </>
      ) : null;
  }
};

export const InvocationSourceBadge: React.FC<InvocationSourceBadgeProps> = ({
  source,
  details,
  showDetails = true,
}) => {
  const config = SOURCE_CONFIG[source] || SOURCE_CONFIG.API;
  const detailContent = getDetailContent(source, details);
  const hasDetails = showDetails && detailContent;

  const badgeContent = (
    <SpaceBetween direction="horizontal" size="xxs">
      <Icon name={config.icon as any} size="small" />
      <Badge color={config.color}>{config.label}</Badge>
    </SpaceBetween>
  );

  if (!hasDetails) {
    return badgeContent;
  }

  return (
    <Popover
      dismissButton={false}
      position="top"
      size="medium"
      triggerType="custom"
      content={
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Source</Box>
          <Box>{config.label}</Box>
          <Box color="text-body-secondary" fontSize="body-s">
            {config.description}
          </Box>
          {detailContent && (
            <Box margin={{ top: 's' }}>{detailContent}</Box>
          )}
        </SpaceBetween>
      }
    >
      <span style={{ cursor: 'pointer' }}>{badgeContent}</span>
    </Popover>
  );
};

export default InvocationSourceBadge;
