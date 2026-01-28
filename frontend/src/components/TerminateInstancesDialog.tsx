/**
 * Terminate Instances Dialog
 * 
 * Shows a list of recovery instances that will be terminated before confirmation.
 * Fetches actual EC2 instance details from the DRS API via the backend.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Modal,
  Box,
  Button,
  SpaceBetween,
  Table,
  Header,
  Alert,
  Spinner,
} from '@cloudscape-design/components';
import apiClient from '../services/api';
import type { Execution } from '../types';

interface RecoveryInstance {
  instanceId: string;
  recoveryInstanceId: string;
  sourceServerId: string;
  region: string;
  waveName: string;
  waveNumber: number;
  jobId: string;
  status: string;
  hostname?: string;
  serverName?: string;
}

interface TerminateInstancesDialogProps {
  open: boolean;
  execution: Execution | null;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export const TerminateInstancesDialog: React.FC<TerminateInstancesDialogProps> = ({
  open,
  execution,
  onConfirm,
  onCancel,
  loading = false,
}) => {
  const [recoveryInstances, setRecoveryInstances] = useState<RecoveryInstance[]>([]);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchRecoveryInstances = useCallback(async () => {
    if (!execution?.executionId) return;

    setFetchLoading(true);
    setFetchError(null);
    
    try {
      const response = await apiClient.getRecoveryInstances(execution.executionId);
      
      if (response.instances) {
        setRecoveryInstances(response.instances);
      } else {
        setRecoveryInstances([]);
      }
    } catch (error) {
      console.error('Error fetching recovery instances:', error);
      setFetchError(error instanceof Error ? error.message : 'Failed to fetch recovery instances');
      setRecoveryInstances([]);
    } finally {
      setFetchLoading(false);
    }
  }, [execution?.executionId]); // apiClient is stable, no need to include

  useEffect(() => {
    if (open && execution?.executionId) {
      fetchRecoveryInstances();
    }
    // fetchRecoveryInstances is stable (wrapped in useCallback)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, execution?.executionId]);

  const columnDefinitions = [
    {
      id: 'instanceId',
      header: 'Instance ID',
      cell: (item: RecoveryInstance) => (
        <span style={{ fontFamily: 'monospace', fontSize: '13px' }}>
          {item.instanceId}
        </span>
      ),
      sortingField: 'instanceId',
      isRowHeader: true,
      width: 180,
    },
    {
      id: 'serverName',
      header: 'Server',
      cell: (item: RecoveryInstance) => (
        <span>{item.serverName || item.hostname || 'Unknown'}</span>
      ),
      width: 140,
    },
    {
      id: 'region',
      header: 'Region',
      cell: (item: RecoveryInstance) => item.region,
      sortingField: 'region',
      width: 120,
    },
  ];

  if (!open) return null;

  return (
    <Modal
      visible={open}
      onDismiss={onCancel}
      header="Terminate Recovery Instances"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={onCancel} disabled={loading || fetchLoading}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={onConfirm} 
              loading={loading}
              disabled={recoveryInstances.length === 0 || fetchLoading || fetchError !== null}
            >
              Terminate {recoveryInstances.length} Instance{recoveryInstances.length !== 1 ? 's' : ''}
            </Button>
          </SpaceBetween>
        </Box>
      }
      size="medium"
    >
      <SpaceBetween size="m">
        {fetchLoading ? (
          <Box textAlign="center" padding="l">
            <SpaceBetween size="m" alignItems="center">
              <Spinner size="large" />
              <div>Loading recovery instances...</div>
            </SpaceBetween>
          </Box>
        ) : fetchError ? (
          <Alert type="error" header="Error Loading Recovery Instances">
            {fetchError}
            <Box padding={{ top: 's' }}>
              <Button onClick={fetchRecoveryInstances} iconName="refresh">
                Retry
              </Button>
            </Box>
          </Alert>
        ) : recoveryInstances.length === 0 ? (
          <Alert type="warning" header="No Recovery Instances Found">
            No recovery instances were found for this execution. This may be because:
            <ul>
              <li>The execution was cancelled before instances were launched</li>
              <li>The instances have already been terminated</li>
              <li>The execution failed before launching instances</li>
            </ul>
          </Alert>
        ) : (
          <>
            <Alert type="warning" header="Permanent Action">
              <strong>This action cannot be undone.</strong> The following {recoveryInstances.length} EC2 recovery instance{recoveryInstances.length !== 1 ? 's' : ''} will be permanently terminated:
            </Alert>

            {recoveryInstances.length <= 8 ? (
              // Show full table for small lists (≤8 instances)
              <Table
                columnDefinitions={columnDefinitions}
                items={recoveryInstances}
                loadingText="Loading instances..."
                empty={
                  <Box textAlign="center" color="inherit">
                    <b>No recovery instances</b>
                  </Box>
                }
                header={
                  <Header counter={`(${recoveryInstances.length})`}>
                    Recovery Instances
                  </Header>
                }
                variant="embedded"
              />
            ) : (
              // Show summary with expandable details for large lists (>8 instances)
              <SpaceBetween size="xs">
                <Box>
                  <strong>{recoveryInstances.length} instances</strong> across {
                    [...new Set(recoveryInstances.map(i => i.region))].length
                  } region(s): {
                    [...new Set(recoveryInstances.map(i => i.region))].join(', ')
                  }
                </Box>
                
                <details>
                  <summary style={{ cursor: 'pointer', padding: '4px 0', color: '#0972d3' }}>
                    Show all instances
                  </summary>
                  <Box padding={{ top: 'xs' }}>
                    <Table
                      columnDefinitions={columnDefinitions}
                      items={recoveryInstances}
                      variant="embedded"
                      stickyHeader
                    />
                  </Box>
                </details>
              </SpaceBetween>
            )}

            <Alert type="info">
              <strong>What happens next:</strong>
              <ol>
                <li>DRS will create termination jobs for each region</li>
                <li>EC2 instances will be stopped and terminated</li>
                <li>EBS volumes will be deleted (unless configured otherwise)</li>
                <li>You can monitor progress in the DRS console</li>
              </ol>
            </Alert>
          </>
        )}
      </SpaceBetween>
    </Modal>
  );
};