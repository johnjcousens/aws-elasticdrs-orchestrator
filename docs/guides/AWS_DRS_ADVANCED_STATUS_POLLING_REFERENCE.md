# AWS DRS Advanced Status Polling Reference

## Overview

This document provides comprehensive status polling patterns for the AWS DRS Orchestration solution, covering per-server launch status, SSM integration monitoring, and production-ready polling strategies.

## Status Field Definitions

### Execution Status Hierarchy

```typescript
interface ExecutionStatus {
  // Top-level execution status
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  
  // Wave-level status
  waves: WaveStatus[];
  
  // Overall progress metrics
  progress: {
    totalServers: number;
    launchedServers: number;
    completedServers: number;
    failedServers: number;
    percentComplete: number;
  };
  
  // Timing information
  startTime: string;
  endTime?: string;
  estimatedCompletion?: string;
}

interface WaveStatus {
  waveNumber: number;
  status: 'PENDING' | 'LAUNCHING' | 'POST_ACTIONS' | 'COMPLETED' | 'FAILED';
  servers: ServerStatus[];
  preActions?: ActionStatus[];
  postActions?: ActionStatus[];
  startTime?: string;
  endTime?: string;
}

interface ServerStatus {
  sourceServerId: string;
  hostname: string;
  
  // Launch status progression
  launchStatus: 'PENDING' | 'LAUNCHING' | 'LAUNCHED' | 'FAILED';
  
  // DRS-specific fields
  recoveryJobId?: string;
  recoveryInstanceId?: string;
  launchedInstanceId?: string;
  
  // Instance details (populated after launch)
  instanceType?: string;
  privateIpAddress?: string;
  publicIpAddress?: string;
  availabilityZone?: string;
  
  // Health check status
  healthStatus?: 'PENDING' | 'CHECKING' | 'HEALTHY' | 'UNHEALTHY' | 'TIMEOUT';
  
  // Timing
  launchStartTime?: string;
  launchEndTime?: string;
  
  // Error details
  errorMessage?: string;
  errorCode?: string;
}

interface ActionStatus {
  actionId: string;
  actionType: 'SSM_DOCUMENT' | 'LAMBDA_FUNCTION' | 'CUSTOM_SCRIPT';
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'TIMEOUT';
  
  // SSM-specific fields
  commandId?: string;
  documentName?: string;
  
  // Results
  output?: string;
  errorMessage?: string;
  
  // Timing
  startTime?: string;
  endTime?: string;
}
```

## DRS Status Polling Implementation

### Core DRS Status Checker

```python
import boto3
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class DRSStatusPoller:
    def __init__(self, region: str):
        self.drs_client = boto3.client('drs', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.ssm_client = boto3.client('ssm', region_name=region)
    
    def get_recovery_job_status(self, job_id: str) -> Dict:
        """Get detailed status of DRS recovery job"""
        try:
            response = self.drs_client.describe_jobs(
                filters={'jobIDs': [job_id]}
            )
            
            if not response['items']:
                return {'status': 'NOT_FOUND'}
            
            job = response['items'][0]
            return {
                'jobId': job['jobID'],
                'status': job['status'],  # PENDING, STARTED, SUCCESSFUL, FAILED
                'type': job['type'],
                'creationDateTime': job['creationDateTime'],
                'endDateTime': job.get('endDateTime'),
                'participatingServers': job.get('participatingServers', []),
                'participatingResources': job.get('participatingResources', [])
            }
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
    
    def get_recovery_instances_status(self, source_server_ids: List[str]) -> Dict[str, Dict]:
        """Get recovery instance status for multiple source servers"""
        try:
            response = self.drs_client.describe_recovery_instances(
                filters={'sourceServerIDs': source_server_ids}
            )
            
            status_map = {}
            for instance in response['items']:
                server_id = instance['sourceServerID']
                status_map[server_id] = {
                    'recoveryInstanceID': instance['recoveryInstanceID'],
                    'pointInTimeSnapshotDateTime': instance.get('pointInTimeSnapshotDateTime'),
                    'dataReplicationInfo': instance.get('dataReplicationInfo', {}),
                    'ec2InstanceID': instance.get('ec2InstanceID'),
                    'ec2InstanceState': instance.get('ec2InstanceState'),
                    'failback': instance.get('failback', {}),
                    'isDrill': instance.get('isDrill', False),
                    'jobID': instance.get('jobID'),
                    'originEnvironment': instance.get('originEnvironment'),
                    'recoveryInstanceProperties': instance.get('recoveryInstanceProperties', {})
                }
            
            return status_map
        except Exception as e:
            print(f"Error getting recovery instances: {str(e)}")
            return {}
    
    def get_launched_instance_details(self, instance_ids: List[str]) -> Dict[str, Dict]:
        """Get EC2 instance details for launched instances"""
        if not instance_ids:
            return {}
        
        try:
            response = self.ec2_client.describe_instances(InstanceIds=instance_ids)
            
            instance_map = {}
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_map[instance_id] = {
                        'instanceId': instance_id,
                        'instanceType': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'privateIpAddress': instance.get('PrivateIpAddress'),
                        'publicIpAddress': instance.get('PublicIpAddress'),
                        'availabilityZone': instance['Placement']['AvailabilityZone'],
                        'launchTime': instance['LaunchTime'].isoformat(),
                        'securityGroups': [sg['GroupId'] for sg in instance['SecurityGroups']],
                        'subnetId': instance.get('SubnetId'),
                        'vpcId': instance.get('VpcId')
                    }
            
            return instance_map
        except Exception as e:
            print(f"Error getting instance details: {str(e)}")
            return {}
```

### Comprehensive Status Aggregator

```python
class ExecutionStatusAggregator:
    def __init__(self, region: str):
        self.poller = DRSStatusPoller(region)
        self.dynamodb = boto3.resource('dynamodb')
        self.executions_table = self.dynamodb.Table('drs-orchestration-executions')
    
    def get_comprehensive_status(self, execution_id: str) -> Dict:
        """Get complete execution status with all details"""
        
        # Get base execution record
        execution = self._get_execution_record(execution_id)
        if not execution:
            return {'error': 'Execution not found'}
        
        # Process each wave
        updated_waves = []
        total_servers = 0
        launched_servers = 0
        completed_servers = 0
        failed_servers = 0
        
        for wave in execution.get('waves', []):
            wave_status = self._process_wave_status(wave)
            updated_waves.append(wave_status)
            
            # Aggregate server counts
            for server in wave_status['servers']:
                total_servers += 1
                if server['launchStatus'] in ['LAUNCHED', 'COMPLETED']:
                    launched_servers += 1
                if server['launchStatus'] == 'COMPLETED':
                    completed_servers += 1
                if server['launchStatus'] == 'FAILED':
                    failed_servers += 1
        
        # Calculate overall progress
        percent_complete = (completed_servers / total_servers * 100) if total_servers > 0 else 0
        
        # Determine overall status
        overall_status = self._calculate_overall_status(updated_waves, execution)
        
        return {
            'executionId': execution_id,
            'planId': execution['planId'],
            'status': overall_status,
            'waves': updated_waves,
            'progress': {
                'totalServers': total_servers,
                'launchedServers': launched_servers,
                'completedServers': completed_servers,
                'failedServers': failed_servers,
                'percentComplete': round(percent_complete, 1)
            },
            'startTime': execution['startTime'],
            'endTime': execution.get('endTime'),
            'estimatedCompletion': self._calculate_eta(execution, percent_complete),
            'lastUpdated': datetime.utcnow().isoformat()
        }
    
    def _process_wave_status(self, wave: Dict) -> Dict:
        """Process status for a single wave"""
        
        # Get server IDs for this wave
        server_ids = [server['sourceServerId'] for server in wave['servers']]
        
        # Get DRS recovery instance status
        recovery_status = self.poller.get_recovery_instances_status(server_ids)
        
        # Get launched instance details
        launched_instance_ids = []
        for server_id, status in recovery_status.items():
            if status.get('ec2InstanceID'):
                launched_instance_ids.append(status['ec2InstanceID'])
        
        instance_details = self.poller.get_launched_instance_details(launched_instance_ids)
        
        # Update server status
        updated_servers = []
        for server in wave['servers']:
            server_id = server['sourceServerId']
            updated_server = self._update_server_status(
                server, 
                recovery_status.get(server_id, {}),
                instance_details
            )
            updated_servers.append(updated_server)
        
        # Update wave-level status
        wave_status = self._calculate_wave_status(updated_servers)
        
        return {
            **wave,
            'servers': updated_servers,
            'status': wave_status,
            'lastUpdated': datetime.utcnow().isoformat()
        }
    
    def _update_server_status(self, server: Dict, recovery_info: Dict, instance_details: Dict) -> Dict:
        """Update individual server status with latest information"""
        
        updated_server = server.copy()
        
        # Update DRS-specific information
        if recovery_info:
            updated_server.update({
                'recoveryInstanceId': recovery_info.get('recoveryInstanceID'),
                'launchedInstanceId': recovery_info.get('ec2InstanceID'),
                'jobId': recovery_info.get('jobID')
            })
            
            # Determine launch status based on DRS state
            if recovery_info.get('ec2InstanceID'):
                updated_server['launchStatus'] = 'LAUNCHED'
            elif recovery_info.get('jobID'):
                updated_server['launchStatus'] = 'LAUNCHING'
        
        # Update EC2 instance details
        instance_id = updated_server.get('launchedInstanceId')
        if instance_id and instance_id in instance_details:
            instance_info = instance_details[instance_id]
            updated_server.update({
                'instanceType': instance_info['instanceType'],
                'privateIpAddress': instance_info['privateIpAddress'],
                'publicIpAddress': instance_info['publicIpAddress'],
                'availabilityZone': instance_info['availabilityZone'],
                'instanceState': instance_info['state']
            })
            
            # Update launch timing
            if instance_info.get('launchTime') and not updated_server.get('launchEndTime'):
                updated_server['launchEndTime'] = instance_info['launchTime']
        
        return updated_server
    
    def _calculate_wave_status(self, servers: List[Dict]) -> str:
        """Calculate overall wave status based on server states"""
        
        if not servers:
            return 'PENDING'
        
        server_statuses = [server['launchStatus'] for server in servers]
        
        if all(status == 'COMPLETED' for status in server_statuses):
            return 'COMPLETED'
        elif any(status == 'FAILED' for status in server_statuses):
            return 'FAILED'
        elif any(status in ['LAUNCHING', 'LAUNCHED'] for status in server_statuses):
            return 'LAUNCHING'
        else:
            return 'PENDING'
    
    def _calculate_overall_status(self, waves: List[Dict], execution: Dict) -> str:
        """Calculate overall execution status"""
        
        if execution.get('status') in ['CANCELLED', 'FAILED']:
            return execution['status']
        
        wave_statuses = [wave['status'] for wave in waves]
        
        if all(status == 'COMPLETED' for status in wave_statuses):
            return 'COMPLETED'
        elif any(status == 'FAILED' for status in wave_statuses):
            return 'FAILED'
        elif any(status in ['LAUNCHING', 'POST_ACTIONS'] for status in wave_statuses):
            return 'IN_PROGRESS'
        else:
            return 'PENDING'
    
    def _calculate_eta(self, execution: Dict, percent_complete: float) -> Optional[str]:
        """Calculate estimated completion time"""
        
        if percent_complete <= 0:
            return None
        
        start_time = datetime.fromisoformat(execution['startTime'].replace('Z', '+00:00'))
        elapsed = datetime.utcnow().replace(tzinfo=start_time.tzinfo) - start_time
        
        if percent_complete >= 100:
            return None
        
        total_estimated = elapsed / (percent_complete / 100)
        eta = start_time + total_estimated
        
        return eta.isoformat()
```

## SSM Integration Monitoring

### SSM Command Status Tracking

```python
class SSMActionMonitor:
    def __init__(self, region: str):
        self.ssm_client = boto3.client('ssm', region_name=region)
    
    def execute_document(self, instance_ids: List[str], document_name: str, parameters: Dict = None) -> str:
        """Execute SSM document and return command ID"""
        
        try:
            response = self.ssm_client.send_command(
                InstanceIds=instance_ids,
                DocumentName=document_name,
                Parameters=parameters or {},
                TimeoutSeconds=3600,  # 1 hour timeout
                MaxConcurrency='50%',
                MaxErrors='0'
            )
            
            return response['Command']['CommandId']
        except Exception as e:
            print(f"Error executing SSM document: {str(e)}")
            raise
    
    def get_command_status(self, command_id: str) -> Dict:
        """Get comprehensive command execution status"""
        
        try:
            # Get overall command status
            command_response = self.ssm_client.describe_commands(
                CommandId=command_id
            )
            
            if not command_response['Commands']:
                return {'status': 'NOT_FOUND'}
            
            command = command_response['Commands'][0]
            
            # Get per-instance status
            invocations_response = self.ssm_client.list_command_invocations(
                CommandId=command_id,
                Details=True
            )
            
            instance_results = {}
            for invocation in invocations_response['CommandInvocations']:
                instance_id = invocation['InstanceId']
                instance_results[instance_id] = {
                    'status': invocation['Status'],
                    'statusDetails': invocation.get('StatusDetails', ''),
                    'standardOutputContent': invocation.get('StandardOutputContent', ''),
                    'standardErrorContent': invocation.get('StandardErrorContent', ''),
                    'requestedDateTime': invocation.get('RequestedDateTime', '').isoformat() if invocation.get('RequestedDateTime') else None,
                    'statusUpdateDateTime': invocation.get('StatusUpdateDateTime', '').isoformat() if invocation.get('StatusUpdateDateTime') else None
                }
            
            return {
                'commandId': command_id,
                'status': command['Status'],
                'statusDetails': command.get('StatusDetails', ''),
                'requestedDateTime': command['RequestedDateTime'].isoformat(),
                'completedCount': command.get('CompletedCount', 0),
                'errorCount': command.get('ErrorCount', 0),
                'deliveryTimedOutCount': command.get('DeliveryTimedOutCount', 0),
                'targetCount': command.get('TargetCount', 0),
                'instanceResults': instance_results
            }
            
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
    
    def monitor_health_checks(self, instance_ids: List[str]) -> Dict[str, Dict]:
        """Execute and monitor health check commands"""
        
        health_results = {}
        
        # Execute basic connectivity check
        try:
            connectivity_command = self.execute_document(
                instance_ids=instance_ids,
                document_name='AWS-RunShellScript',
                parameters={
                    'commands': [
                        'echo "Health check started: $(date)"',
                        'curl -f http://169.254.169.254/latest/meta-data/instance-id || echo "Metadata service check failed"',
                        'df -h | head -5',
                        'free -m',
                        'uptime',
                        'echo "Health check completed: $(date)"'
                    ]
                }
            )
            
            # Wait briefly for execution to start
            time.sleep(2)
            
            # Get initial status
            status = self.get_command_status(connectivity_command)
            
            for instance_id in instance_ids:
                instance_result = status['instanceResults'].get(instance_id, {})
                health_results[instance_id] = {
                    'commandId': connectivity_command,
                    'status': instance_result.get('status', 'PENDING'),
                    'output': instance_result.get('standardOutputContent', ''),
                    'error': instance_result.get('standardErrorContent', ''),
                    'lastChecked': datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            for instance_id in instance_ids:
                health_results[instance_id] = {
                    'status': 'FAILED',
                    'error': f"Health check execution failed: {str(e)}",
                    'lastChecked': datetime.utcnow().isoformat()
                }
        
        return health_results
```

## Frontend Polling Implementation

### React Status Polling Hook

```typescript
import { useState, useEffect, useCallback } from 'react';
import { ApiClient } from '../services/api-client';

interface UseExecutionPollingOptions {
  executionId: string;
  interval?: number; // milliseconds
  enabled?: boolean;
  onStatusChange?: (status: ExecutionStatus) => void;
}

export const useExecutionPolling = ({
  executionId,
  interval = 10000, // 10 seconds default
  enabled = true,
  onStatusChange
}: UseExecutionPollingOptions) => {
  const [status, setStatus] = useState<ExecutionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const apiClient = new ApiClient();

  const fetchStatus = useCallback(async () => {
    if (!enabled || !executionId) return;

    try {
      setError(null);
      const newStatus = await apiClient.getExecutionStatus(executionId);
      
      setStatus(newStatus);
      setLastUpdated(new Date());
      setLoading(false);
      
      // Notify parent component of status changes
      if (onStatusChange) {
        onStatusChange(newStatus);
      }
      
      // Stop polling if execution is complete
      if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(newStatus.status)) {
        return false; // Signal to stop polling
      }
      
      return true; // Continue polling
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
      setLoading(false);
      return true; // Continue polling even on error
    }
  }, [executionId, enabled, onStatusChange, apiClient]);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchStatus();

    // Set up polling interval
    const intervalId = setInterval(async () => {
      const shouldContinue = await fetchStatus();
      if (!shouldContinue) {
        clearInterval(intervalId);
      }
    }, interval);

    return () => clearInterval(intervalId);
  }, [fetchStatus, interval, enabled]);

  return {
    status,
    loading,
    error,
    lastUpdated,
    refetch: fetchStatus
  };
};
```

### Execution Dashboard Component

```typescript
import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Grid,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Schedule,
  PlayArrow,
  Refresh,
  OpenInNew
} from '@mui/icons-material';
import { useExecutionPolling } from '../hooks/useExecutionPolling';

interface ExecutionDashboardProps {
  executionId: string;
}

export const ExecutionDashboard: React.FC<ExecutionDashboardProps> = ({
  executionId
}) => {
  const { status, loading, error, lastUpdated, refetch } = useExecutionPolling({
    executionId,
    interval: 10000, // 10 seconds
    enabled: true
  });

  if (loading && !status) {
    return <LinearProgress />;
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Typography color="error">Error: {error}</Typography>
        </CardContent>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card>
        <CardContent>
          <Typography>Execution not found</Typography>
        </CardContent>
      </Card>
    );
  }

  const getStatusColor = (statusValue: string) => {
    switch (statusValue) {
      case 'COMPLETED': return 'success';
      case 'FAILED': return 'error';
      case 'IN_PROGRESS': case 'LAUNCHING': return 'primary';
      case 'PENDING': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (statusValue: string) => {
    switch (statusValue) {
      case 'COMPLETED': return <CheckCircle />;
      case 'FAILED': return <Error />;
      case 'IN_PROGRESS': case 'LAUNCHING': return <PlayArrow />;
      case 'PENDING': return <Schedule />;
      default: return <Schedule />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Execution Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Last updated: {lastUpdated?.toLocaleTimeString()}
          </Typography>
          <IconButton onClick={refetch} size="small">
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {/* Overall Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Chip
                  icon={getStatusIcon(status.status)}
                  label={status.status}
                  color={getStatusColor(status.status)}
                  variant="outlined"
                />
                <Typography variant="h6">
                  {status.progress.percentComplete}% Complete
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={status.progress.percentComplete}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Total Servers
                  </Typography>
                  <Typography variant="h6">
                    {status.progress.totalServers}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Launched
                  </Typography>
                  <Typography variant="h6" color="primary">
                    {status.progress.launchedServers}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Completed
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {status.progress.completedServers}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Failed
                  </Typography>
                  <Typography variant="h6" color="error.main">
                    {status.progress.failedServers}
                  </Typography>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Wave Progress */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Wave Progress
          </Typography>
          <Stepper orientation="vertical">
            {status.waves.map((wave, index) => (
              <Step key={wave.waveNumber} active={true} completed={wave.status === 'COMPLETED'}>
                <StepLabel
                  error={wave.status === 'FAILED'}
                  icon={getStatusIcon(wave.status)}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="subtitle1">
                      Wave {wave.waveNumber}
                    </Typography>
                    <Chip
                      label={wave.status}
                      size="small"
                      color={getStatusColor(wave.status)}
                      variant="outlined"
                    />
                  </Box>
                </StepLabel>
                <StepContent>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Server</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Instance ID</TableCell>
                          <TableCell>IP Address</TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {wave.servers.map((server) => (
                          <TableRow key={server.sourceServerId}>
                            <TableCell>
                              <Typography variant="body2" fontWeight="medium">
                                {server.hostname}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {server.sourceServerId}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={server.launchStatus}
                                size="small"
                                color={getStatusColor(server.launchStatus)}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              {server.launchedInstanceId ? (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="body2">
                                    {server.launchedInstanceId}
                                  </Typography>
                                  <Tooltip title="Open in EC2 Console">
                                    <IconButton
                                      size="small"
                                      onClick={() => {
                                        const url = `https://console.aws.amazon.com/ec2/v2/home#InstanceDetails:instanceId=${server.launchedInstanceId}`;
                                        window.open(url, '_blank');
                                      }}
                                    >
                                      <OpenInNew fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                </Box>
                              ) : (
                                <Typography variant="body2" color="text.secondary">
                                  -
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {server.privateIpAddress || '-'}
                              </Typography>
                              {server.publicIpAddress && (
                                <Typography variant="caption" color="text.secondary">
                                  Public: {server.publicIpAddress}
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              {server.errorMessage && (
                                <Tooltip title={server.errorMessage}>
                                  <Chip
                                    label="Error"
                                    size="small"
                                    color="error"
                                    variant="outlined"
                                  />
                                </Tooltip>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>
    </Box>
  );
};
```

## Production Polling Strategy

### Adaptive Polling Intervals

```typescript
class AdaptivePollingManager {
  private intervals = {
    PENDING: 30000,      // 30 seconds - slow polling for pending executions
    IN_PROGRESS: 5000,   // 5 seconds - fast polling during active execution
    LAUNCHING: 3000,     // 3 seconds - very fast during launch phase
    POST_ACTIONS: 10000, // 10 seconds - medium polling during post-actions
    COMPLETED: 0,        // Stop polling
    FAILED: 0,           // Stop polling
    CANCELLED: 0         // Stop polling
  };

  getPollingInterval(status: string): number {
    return this.intervals[status as keyof typeof this.intervals] || 10000;
  }

  shouldPoll(status: string): boolean {
    return this.getPollingInterval(status) > 0;
  }
}

// Usage in React hook
export const useAdaptiveExecutionPolling = (executionId: string) => {
  const [pollingManager] = useState(new AdaptivePollingManager());
  const [currentInterval, setCurrentInterval] = useState(10000);

  const { status, loading, error, lastUpdated, refetch } = useExecutionPolling({
    executionId,
    interval: currentInterval,
    enabled: true,
    onStatusChange: (newStatus) => {
      const newInterval = pollingManager.getPollingInterval(newStatus.status);
      if (newInterval !== currentInterval) {
        setCurrentInterval(newInterval);
      }
    }
  });

  return { status, loading, error, lastUpdated, refetch };
};
```

### Error Recovery and Retry Logic

```python
class RobustStatusPoller:
    def __init__(self, region: str, max_retries: int = 3):
        self.region = region
        self.max_retries = max_retries
        self.backoff_base = 2  # seconds
    
    async def get_status_with_retry(self, execution_id: str) -> Dict:
        """Get execution status with exponential backoff retry"""
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                aggregator = ExecutionStatusAggregator(self.region)
                return aggregator.get_comprehensive_status(execution_id)
                
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = self.backoff_base ** attempt
                    print(f"Status polling attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    print(f"Status polling failed after {self.max_retries + 1} attempts: {str(e)}")
        
        # Return error status if all retries failed
        return {
            'executionId': execution_id,
            'status': 'ERROR',
            'error': f"Failed to get status after {self.max_retries + 1} attempts: {str(last_error)}",
            'lastUpdated': datetime.utcnow().isoformat()
        }
```

## Performance Optimization

### Batch Status Queries

```python
class BatchStatusOptimizer:
    def __init__(self, region: str):
        self.poller = DRSStatusPoller(region)
    
    def get_multiple_execution_status(self, execution_ids: List[str]) -> Dict[str, Dict]:
        """Efficiently get status for multiple executions"""
        
        # Batch DynamoDB queries
        executions = self._batch_get_executions(execution_ids)
        
        # Collect all server IDs across all executions
        all_server_ids = set()
        for execution in executions.values():
            for wave in execution.get('waves', []):
                for server in wave['servers']:
                    all_server_ids.add(server['sourceServerId'])
        
        # Single batch call for all recovery instances
        recovery_status = self.poller.get_recovery_instances_status(list(all_server_ids))
        
        # Single batch call for all launched instances
        launched_instance_ids = [
            status.get('ec2InstanceID') 
            for status in recovery_status.values() 
            if status.get('ec2InstanceID')
        ]
        instance_details = self.poller.get_launched_instance_details(launched_instance_ids)
        
        # Process each execution with shared data
        results = {}
        for execution_id, execution in executions.items():
            aggregator = ExecutionStatusAggregator(self.region)
            # Use pre-fetched data instead of making individual calls
            results[execution_id] = aggregator._process_execution_with_data(
                execution, recovery_status, instance_details
            )
        
        return results
```

### Caching Strategy

```python
import redis
import json
from datetime import timedelta

class StatusCache:
    def __init__(self, redis_url: str = None):
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self.cache_ttl = {
            'PENDING': 60,       # 1 minute
            'IN_PROGRESS': 10,   # 10 seconds
            'LAUNCHING': 5,      # 5 seconds
            'COMPLETED': 3600,   # 1 hour
            'FAILED': 3600,      # 1 hour
        }
    
    def get_cached_status(self, execution_id: str) -> Optional[Dict]:
        """Get cached execution status"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(f"execution_status:{execution_id}")
            return json.loads(cached) if cached else None
        except Exception:
            return None
    
    def cache_status(self, execution_id: str, status: Dict) -> None:
        """Cache execution status with appropriate TTL"""
        if not self.redis_client:
            return
        
        try:
            ttl = self.cache_ttl.get(status.get('status'), 30)
            self.redis_client.setex(
                f"execution_status:{execution_id}",
                ttl,
                json.dumps(status)
            )
        except Exception as e:
            print(f"Failed to cache status: {str(e)}")
    
    def invalidate_status(self, execution_id: str) -> None:
        """Invalidate cached status"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.delete(f"execution_status:{execution_id}")
        except Exception:
            pass
```

## Monitoring and Alerting

### CloudWatch Metrics Integration

```python
import boto3
from datetime import datetime

class ExecutionMetrics:
    def __init__(self, region: str):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.namespace = 'DRS/Orchestration'
    
    def publish_execution_metrics(self, execution_status: Dict) -> None:
        """Publish execution metrics to CloudWatch"""
        
        try:
            metrics = []
            
            # Overall progress metrics
            progress = execution_status.get('progress', {})
            metrics.extend([
                {
                    'MetricName': 'TotalServers',
                    'Value': progress.get('totalServers', 0),
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'LaunchedServers',
                    'Value': progress.get('launchedServers', 0),
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'CompletedServers',
                    'Value': progress.get('completedServers', 0),
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'FailedServers',
                    'Value': progress.get('failedServers', 0),
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'PercentComplete',
                    'Value': progress.get('percentComplete', 0),
                    'Unit': 'Percent'
                }
            ])
            
            # Status-based metrics
            status_value = 1 if execution_status.get('status') == 'IN_PROGRESS' else 0
            metrics.append({
                'MetricName': 'ActiveExecutions',
                'Value': status_value,
                'Unit': 'Count'
            })
            
            # Publish metrics
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metrics
            )
            
        except Exception as e:
            print(f"Failed to publish metrics: {str(e)}")
    
    def create_execution_alarms(self, execution_id: str) -> None:
        """Create CloudWatch alarms for execution monitoring"""
        
        try:
            # Alarm for failed servers
            self.cloudwatch.put_metric_alarm(
                AlarmName=f'DRS-Execution-{execution_id}-FailedServers',
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=1,
                MetricName='FailedServers',
                Namespace=self.namespace,
                Period=300,
                Statistic='Maximum',
                Threshold=0.0,
                ActionsEnabled=True,
                AlarmActions=[
                    f'arn:aws:sns:{self.cloudwatch._client_config.region_name}:123456789012:drs-orchestration-alerts'
                ],
                AlarmDescription=f'Alert when servers fail during execution {execution_id}',
                Unit='Count'
            )
            
            # Alarm for stalled executions
            self.cloudwatch.put_metric_alarm(
                AlarmName=f'DRS-Execution-{execution_id}-Stalled',
                ComparisonOperator='LessThanThreshold',
                EvaluationPeriods=3,
                MetricName='PercentComplete',
                Namespace=self.namespace,
                Period=600,  # 10 minutes
                Statistic='Maximum',
                Threshold=100.0,
                TreatMissingData='breaching',
                ActionsEnabled=True,
                AlarmActions=[
                    f'arn:aws:sns:{self.cloudwatch._client_config.region_name}:123456789012:drs-orchestration-alerts'
                ],
                AlarmDescription=f'Alert when execution {execution_id} appears stalled',
                Unit='Percent'
            )
            
        except Exception as e:
            print(f"Failed to create alarms: {str(e)}")
```

## Best Practices Summary

### Polling Frequency Guidelines

1. **Adaptive Intervals**: Adjust polling frequency based on execution status
2. **Batch Operations**: Combine multiple API calls to reduce overhead
3. **Caching**: Cache status data with appropriate TTL based on volatility
4. **Error Handling**: Implement exponential backoff for failed requests
5. **Resource Limits**: Respect AWS API rate limits and implement throttling

### Performance Optimization

1. **Minimize API Calls**: Batch DRS and EC2 describe operations
2. **Efficient Queries**: Use DynamoDB batch operations where possible
3. **Smart Caching**: Cache stable data longer, volatile data shorter
4. **Connection Pooling**: Reuse AWS SDK clients across requests
5. **Async Operations**: Use async/await for concurrent status checks

### Monitoring and Alerting

1. **CloudWatch Integration**: Publish key metrics for monitoring
2. **Proactive Alerts**: Set up alarms for failures and stalled executions
3. **Audit Logging**: Log all status changes for troubleshooting
4. **Performance Metrics**: Track polling performance and API latency
5. **User Notifications**: Provide real-time updates via WebSocket or polling

This comprehensive status polling reference provides production-ready patterns for monitoring AWS DRS recovery executions with full visibility into server launch status, SSM integration, and real-time progress tracking.