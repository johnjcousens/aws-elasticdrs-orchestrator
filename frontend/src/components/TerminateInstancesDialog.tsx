/**
 * Terminate Instances Dialog
 * 
 * Shows a list of recovery instances that will be terminated before confirmation.
 * Fetches actual EC2 instance details from the DRS API via the backend.
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Box,
  Button,
  SpaceBetween,
  Table,
  Header,
  Alert,
  StatusIndicator,
  Pagination,
  Spinner,
} from '@cloudscape-design/components';
import { apiClient } from '../services/api';
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

  // Fetch recovery instances when dialog opens
  useEffect(() => {
    if (open && execution?.executionId) {
      fetchRecoveryInstances();
    }
  }, [open, execution?.executionId]);

  const fetchRecoveryInstances = async () => {
    if (!execution?.executionId) return;

    setFetchLoading(true);
    setFetchError(null);
    
    try {
      const response = await apiClient.get(`/executions/${execution.executionId}/recovery-instances`);
      
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
  };

  const columnDefinitions = [
    {
      id: 'instanceId',
      header: 'Instance ID',
      cell: (item: RecoveryInstance) => (
        <div style={{ fontFamily: 'monospace', fontSize: '14px' }}>
          {item.instanceId}
        </div>
      ),
      sortingField: 'instanceId',
      isRowHeader: true,
    },
    {
      id: 'serverName',
      header: 'Server',
      cell: (item: RecoveryInstance) => (
        <div>
          <div>{item.serverName || item.hostname || 'Unknown'}</div>
          <div style={{ fontSize: '12px', color: '#5f6b7a', fontFamily: 'monospace' }}>
            {item.sourceServerId}
          </div>
        </div>
      ),
    },
    {
      id: 'wave',
      header: 'Wave',
      cell: (item: RecoveryInstance) => item.waveName,
      sortingField: 'waveName',
    },
    {
      id: 'region',
      header: 'Region',
      cell: (item: RecoveryInstance) => item.region,
      sortingField: 'region',
    },
    {
      id: 'status',
      header: 'Status',
      cell: (item: RecoveryInstance) => {
        const status = item.status.toUpperCase();
        let type: 'success' | 'error' | 'warning' | 'info' = 'info';
        
        if (status === 'RUNNING' || status === 'LAUNCHED') {
          type = 'success';
        } else if (status === 'TERMINATED' || status === 'FAILED') {
          type = 'error';
        } else if (status === 'PENDING' || status === 'STARTING') {
          type = 'warning';
        }
        
        return <StatusIndicator type={type}>{item.status}</StatusIndicator>;
      },
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
      size="large"
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

            {recoveryInstances.length <= 10 ? (
              // Show full table for small lists (≤10 instances)
              <Table
                columnDefinitions={columnDefinitions}
                items={recoveryInstances}
                loadingText="Loading instances..."
                empty={
                  <Box textAlign="center" color="inherit">
                    <b>No recovery instances</b>
                    <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                      No recovery instances to display.
                    </Box>
                  </Box>
                }
                header={
                  <Header
                    counter={`(${recoveryInstances.length})`}
                    description="EC2 instances that will be terminated"
                  >
                    Recovery Instances
                  </Header>
                }
                variant="embedded"
              />
            ) : (
              // Show summary with collapsible details for large lists (>10 instances)
              <SpaceBetween size="s">
                <Header
                  counter={`(${recoveryInstances.length})`}
                  description="EC2 instances that will be terminated"
                >
                  Recovery Instances
                </Header>
                
                <Box>
                  <strong>Instance Summary:</strong>
                </Box>
                <Box>
                  • Total instances: {recoveryInstances.length}
                </Box>
                <Box>
                  • Running: {recoveryInstances.filter(i => i.status.toUpperCase() === 'RUNNING' || i.status.toUpperCase() === 'LAUNCHED').length}
                </Box>
                <Box>
                  • Other states: {recoveryInstances.filter(i => i.status.toUpperCase() !== 'RUNNING' && i.status.toUpperCase() !== 'LAUNCHED').length}
                </Box>
                
                <details>
                  <summary style={{ cursor: 'pointer', padding: '8px 0' }}>
                    <strong>Show all instances</strong>
                  </summary>
                  <Box padding={{ top: 's' }}>
                    <Table
                      columnDefinitions={columnDefinitions}
                      items={recoveryInstances}
                      loadingText="Loading instances..."
                      empty={
                        <Box textAlign="center" color="inherit">
                          <b>No recovery instances</b>
                          <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                            No recovery instances to display.
                          </Box>
                        </Box>
                      }
                      variant="embedded"
                      pagination={
                        recoveryInstances.length > 25 ? (
                          <Pagination
                            currentPageIndex={1}
                            pagesCount={Math.ceil(recoveryInstances.length / 25)}
                          />
                        ) : undefined
                      }
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