/**
 * Terminate Instances Dialog
 * 
 * Shows a list of recovery instances that will be terminated before confirmation.
 * Displays actual EC2 instance details from the execution data.
 */

import React from 'react';
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
} from '@cloudscape-design/components';
import type { Execution } from '../types';

interface RecoveryInstance {
  instanceId: string;
  sourceServerId: string;
  region: string;
  waveName: string;
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

  // Extract recovery instances from execution data
  const getRecoveryInstances = (): RecoveryInstance[] => {
    if (!execution) return [];

    const instances: RecoveryInstance[] = [];
    const waves = (execution as any).waves || execution.waveExecutions || [];

    for (const wave of waves) {
      const waveName = wave.waveName || wave.WaveName || `Wave ${wave.waveNumber + 1}`;
      const region = wave.region || wave.Region || 'us-east-1';
      
      // Check servers in wave
      const servers = wave.servers || wave.serverExecutions || [];
      for (const server of servers) {
        const instanceId = server.instanceId || server.recoveredInstanceId || server.ec2InstanceId;
        const sourceServerId = server.sourceServerId || server.serverId || server.SourceServerId;
        
        // Only include servers with actual EC2 instances
        if (instanceId && instanceId.startsWith('i-')) {
          instances.push({
            instanceId,
            sourceServerId: sourceServerId || 'unknown',
            region: server.region || region,
            waveName,
            status: server.status || server.launchStatus || 'UNKNOWN',
            hostname: server.hostname,
            serverName: server.serverName,
          });
        }
      }

      // Also check ServerStatuses (newer format)
      const serverStatuses = wave.ServerStatuses || wave.serverStatuses || [];
      for (const server of serverStatuses) {
        const instanceId = server.RecoveryInstanceID || server.recoveryInstanceId || server.EC2InstanceId || server.ec2InstanceId;
        const sourceServerId = server.SourceServerId || server.sourceServerId;
        
        if (instanceId && instanceId.startsWith('i-')) {
          // Avoid duplicates
          const exists = instances.some(inst => inst.instanceId === instanceId);
          if (!exists) {
            instances.push({
              instanceId,
              sourceServerId: sourceServerId || 'unknown',
              region: server.Region || region,
              waveName,
              status: server.LaunchStatus || server.status || 'UNKNOWN',
              hostname: server.Hostname || server.hostname,
              serverName: server.ServerName || server.serverName,
            });
          }
        }
      }
    }

    return instances;
  };

  const recoveryInstances = getRecoveryInstances();

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
        
        if (status === 'LAUNCHED') {
          type = 'success';
        } else if (status === 'FAILED') {
          type = 'error';
        } else if (status === 'STARTED' || status === 'IN_PROGRESS') {
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
            <Button onClick={onCancel} disabled={loading}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={onConfirm} 
              loading={loading}
              disabled={recoveryInstances.length === 0}
            >
              Terminate {recoveryInstances.length} Instance{recoveryInstances.length !== 1 ? 's' : ''}
            </Button>
          </SpaceBetween>
        </Box>
      }
      size="large"
    >
      <SpaceBetween size="m">
        {recoveryInstances.length === 0 ? (
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
                  • Running: {recoveryInstances.filter(i => i.status.toUpperCase() === 'LAUNCHED').length}
                </Box>
                <Box>
                  • Other states: {recoveryInstances.filter(i => i.status.toUpperCase() !== 'LAUNCHED').length}
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