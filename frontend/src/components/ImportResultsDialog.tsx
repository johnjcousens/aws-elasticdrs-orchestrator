// Copyright Amazon.com and Affiliates. All rights reserved.
// This deliverable is considered Developed Content as defined in the AWS Service Terms.

/**
 * Import Results Dialog
 * 
 * Displays detailed results of a configuration import operation.
 */

import React from 'react';
import {
  Modal,
  SpaceBetween,
  Box,
  ExpandableSection,
  StatusIndicator,
  Table,
  ColumnLayout,
  Badge,
} from '@cloudscape-design/components';
import type { ImportResults, ImportResourceResult } from '../types';

interface ImportResultsDialogProps {
  visible: boolean;
  onDismiss: () => void;
  results: ImportResults;
}

export const ImportResultsDialog: React.FC<ImportResultsDialogProps> = ({
  visible,
  onDismiss,
  results,
}) => {
  const { summary, created, skipped, failed, dryRun, correlationId } = results;

  const totalCreated = summary.protectionGroups.created + summary.recoveryPlans.created;
  const totalSkipped = summary.protectionGroups.skipped + summary.recoveryPlans.skipped;
  const totalFailed = summary.protectionGroups.failed + summary.recoveryPlans.failed;

  const getReasonLabel = (reason: string): string => {
    const labels: Record<string, string> = {
      ALREADY_EXISTS: 'Already exists',
      SERVER_NOT_FOUND: 'Server not found in DRS',
      SERVER_CONFLICT: 'Server assigned to another group',
      ACTIVE_EXECUTION_CONFLICT: 'Server in active execution',
      NO_TAG_MATCHES: 'No servers match tags',
      TAG_RESOLUTION_ERROR: 'Tag resolution failed',
      DRS_NOT_INITIALIZED: 'DRS not initialized in region',
      MISSING_PROTECTION_GROUP: 'Referenced Protection Group missing',
      CASCADE_FAILURE: 'Dependent Protection Group failed',
      CREATE_ERROR: 'Database error',
    };
    return labels[reason] || reason;
  };

  const columnDefinitions = [
    {
      id: 'type',
      header: 'Type',
      cell: (item: ImportResourceResult) => (
        <Badge color={item.type === 'ProtectionGroup' ? 'blue' : 'green'}>
          {item.type === 'ProtectionGroup' ? 'PG' : 'RP'}
        </Badge>
      ),
      width: 60,
    },
    {
      id: 'name',
      header: 'Name',
      cell: (item: ImportResourceResult) => item.name,
    },
    {
      id: 'reason',
      header: 'Reason',
      cell: (item: ImportResourceResult) => item.reason ? getReasonLabel(item.reason) : '-',
    },
  ];

  return (
    <Modal
      visible={visible}
      onDismiss={onDismiss}
      header={dryRun ? 'Dry Run Results' : 'Import Results'}
      size="large"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <span style={{ color: '#5f6b7a', fontSize: '12px' }}>
              Correlation ID: {correlationId}
            </span>
          </SpaceBetween>
        </Box>
      }
    >
      <SpaceBetween size="l">
        <Box>
          <StatusIndicator type={results.success ? 'success' : 'warning'}>
            {dryRun
              ? 'Validation complete - no changes made'
              : results.success
              ? 'Import completed successfully'
              : 'Import completed with errors'}
          </StatusIndicator>
        </Box>

        <ColumnLayout columns={3} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">
              {dryRun ? 'Would Create' : 'Created'}
            </Box>
            <Box variant="awsui-value-large" color="text-status-success">
              {totalCreated}
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Skipped</Box>
            <Box variant="awsui-value-large" color="text-body-secondary">
              {totalSkipped}
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Failed</Box>
            <Box variant="awsui-value-large" color="text-status-error">
              {totalFailed}
            </Box>
          </div>
        </ColumnLayout>

        {created.length > 0 && (
          <ExpandableSection
            headerText={`${dryRun ? 'Would Create' : 'Created'} (${created.length})`}
            defaultExpanded={!dryRun}
          >
            <Table
              items={created}
              columnDefinitions={columnDefinitions.slice(0, 2)}
              variant="embedded"
            />
          </ExpandableSection>
        )}

        {skipped.length > 0 && (
          <ExpandableSection headerText={`Skipped (${skipped.length})`}>
            <Table
              items={skipped}
              columnDefinitions={columnDefinitions}
              variant="embedded"
            />
          </ExpandableSection>
        )}

        {failed.length > 0 && (
          <ExpandableSection headerText={`Failed (${failed.length})`} defaultExpanded>
            <Table
              items={failed}
              columnDefinitions={columnDefinitions}
              variant="embedded"
            />
          </ExpandableSection>
        )}
      </SpaceBetween>
    </Modal>
  );
};
