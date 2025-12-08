# AWS Elastic Disaster Recovery (DRS) REST API Reference

A comprehensive reference for AWS DRS REST API endpoints used in disaster recovery orchestration.

> **Last Updated**: December 2024  
> **API Version**: 2020-02-26  
> **Official Documentation**: [AWS DRS API Reference](https://docs.aws.amazon.com/drs/latest/APIReference/Welcome.html)

## Overview

AWS Elastic Disaster Recovery (DRS) provides REST APIs for managing source servers, replication, recovery operations, failback, and source network protection. This document covers all key endpoints used in the DRS Orchestration Solution.

## Authentication

All DRS API calls require AWS Signature Version 4 authentication:

```python
import boto3
drs_client = boto3.client('drs', region_name='us-east-1')
```

## Base URL Structure

```text
https://drs.{region}.amazonaws.com/
```

## Complete API Reference

### API Categories

| Category | APIs |
|----------|------|
| Service Initialization | InitializeService |
| Source Server Management | DescribeSourceServers, DeleteSourceServer, DisconnectSourceServer, RetryDataReplication, StartReplication, StopReplication |
| Recovery Operations | StartRecovery, DescribeJobs, DescribeJobLogItems, DeleteJob |
| Recovery Instances | DescribeRecoveryInstances, DeleteRecoveryInstance, DisconnectRecoveryInstance, TerminateRecoveryInstances |
| Failback Operations | StartFailbackLaunch, StopFailback, ReverseReplication, GetFailbackReplicationConfiguration, UpdateFailbackReplicationConfiguration |
| Launch Configuration | GetLaunchConfiguration, UpdateLaunchConfiguration, CreateLaunchConfigurationTemplate, DescribeLaunchConfigurationTemplates, UpdateLaunchConfigurationTemplate, DeleteLaunchConfigurationTemplate |
| Launch Actions | PutLaunchAction, ListLaunchActions, DeleteLaunchAction |
| Replication Configuration | GetReplicationConfiguration, UpdateReplicationConfiguration, CreateReplicationConfigurationTemplate, DescribeReplicationConfigurationTemplates, UpdateReplicationConfigurationTemplate, DeleteReplicationConfigurationTemplate |
| Recovery Snapshots | DescribeRecoverySnapshots |
| Source Networks | CreateSourceNetwork, DescribeSourceNetworks, DeleteSourceNetwork, StartSourceNetworkRecovery, StartSourceNetworkReplication, StopSourceNetworkReplication, AssociateSourceNetworkStack, ExportSourceNetworkCfnTemplate |
| Cross-Account | CreateExtendedSourceServer, ListExtensibleSourceServers, ListStagingAccounts |
| Tagging | TagResource, UntagResource, ListTagsForResource |

---

## Service Initialization

### InitializeService

**Endpoint**: `POST /InitializeService`

**Purpose**: Initialize Elastic Disaster Recovery service in the account. Must be called before using any other DRS APIs.

**Request**: No request body required.

**Response**: HTTP 204 (No Content) on success.

**Python Example**:

```python
drs_client.initialize_service()
```

---

## Source Server Management

### DescribeSourceServers

**Endpoint**: `POST /DescribeSourceServers`

**Purpose**: Retrieve all DRS source servers in the current region.

**Request**:

```json
{
    "filters": {
        "sourceServerIDs": ["s-1234567890abcdef0"],
        "isArchived": false,
        "replicationTypes": ["AGENT_BASED"],
        "stagingAccountIDs": ["123456789012"]
    },
    "maxResults": 200,
    "nextToken": "string"
}
```

**Response**:

```json
{
    "items": [
        {
            "sourceServerID": "s-1234567890abcdef0",
            "arn": "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0",
            "tags": {
                "Environment": "Production"
            },
            "dataReplicationInfo": {
                "dataReplicationState": "CONTINUOUS",
                "lagDuration": "PT5M",
                "replicatedDisks": [
                    {
                        "deviceName": "/dev/sda1",
                        "totalStorageBytes": 107374182400,
                        "replicatedStorageBytes": 107374182400,
                        "backloggedStorageBytes": 0
                    }
                ]
            },
            "lifeCycle": {
                "addedToServiceDateTime": "2024-01-15T10:00:00Z",
                "firstByteDateTime": "2024-01-15T10:05:00Z"
            },
            "sourceProperties": {
                "hostname": "web-server-01",
                "recommendedInstanceType": "m5.large",
                "os": {
                    "fullString": "Ubuntu 20.04.3 LTS"
                }
            },
            "replicationTypes": ["AGENT_BASED"],
            "isArchived": false
        }
    ],
    "nextToken": "string"
}
```

### DeleteSourceServer

**Endpoint**: `POST /DeleteSourceServer`

**Purpose**: Deletes a single source server by ID. The source server must be disconnected first.

**Request**:

```json
{
    "sourceServerID": "s-1234567890abcdef0"
}
```

### DisconnectSourceServer

**Endpoint**: `POST /DisconnectSourceServer`

**Purpose**: Disconnects a specific source server from DRS. Data replication is stopped.

**Request**:

```json
{
    "sourceServerID": "s-1234567890abcdef0"
}
```

### StartReplication

**Endpoint**: `POST /StartReplication`

**Purpose**: Starts replication for a source server. Used after stopping replication or for initial start.

**Request**:

```json
{
    "sourceServerID": "s-1234567890abcdef0"
}
```

### StopReplication

**Endpoint**: `POST /StopReplication`

**Purpose**: Stops the replication for a source server.

**Request**:

```json
{
    "sourceServerID": "s-1234567890abcdef0"
}
```

### RetryDataReplication

**Endpoint**: `POST /RetryDataReplication`

**Purpose**: Retries data replication for a source server that has failed replication.

**Request**:

```json
{
    "sourceServerID": "s-1234567890abcdef0"
}
```

---

## Recovery Job Management

### StartRecovery

**Endpoint**: `POST /StartRecovery`

**Purpose**: Launches Recovery Instances for specified Source Servers. Supports point-in-time or on-demand snapshots.

**Request**:

```json
{
    "sourceServers": [
        {
            "sourceServerID": "s-1234567890abcdef0",
            "recoverySnapshotID": "snap-1234567890abcdef0"
        }
    ],
    "isDrill": false,
    "tags": {
        "RecoveryPlan": "WebApp-Recovery",
        "Wave": "1"
    }
}
```

**Response** (HTTP 202):

```json
{
    "job": {
        "jobID": "drsjob-1234567890abcdef0",
        "arn": "arn:aws:drs:us-east-1:123456789012:job/drsjob-1234567890abcdef0",
        "type": "LAUNCH",
        "initiatedBy": "START_RECOVERY",
        "creationDateTime": "2024-01-15T14:30:00Z",
        "status": "PENDING",
        "participatingServers": [
            {
                "sourceServerID": "s-1234567890abcdef0",
                "recoveryInstanceID": "i-0987654321fedcba0",
                "launchStatus": "PENDING"
            }
        ],
        "tags": {
            "RecoveryPlan": "WebApp-Recovery"
        }
    }
}
```

**Launch Status Values**: `PENDING`, `IN_PROGRESS`, `LAUNCHED`, `FAILED`, `TERMINATED`

### DescribeJobs

**Endpoint**: `POST /DescribeJobs`

**Purpose**: List and monitor recovery jobs with filtering options.

**Request**:

```json
{
    "filters": {
        "jobIDs": ["drsjob-1234567890abcdef0"],
        "fromDate": "2024-01-15T00:00:00Z",
        "toDate": "2024-01-15T23:59:59Z"
    },
    "maxResults": 50,
    "nextToken": "string"
}
```

**Job Status Values**: `PENDING`, `STARTED`, `COMPLETED`, `PARTIALLY_SUCCEEDED`, `FAILED`

**Job Types**: `LAUNCH`, `TERMINATE`, `CREATE_CONVERTED_SNAPSHOT`

### DescribeJobLogItems

**Endpoint**: `POST /DescribeJobLogItems`

**Purpose**: Retrieves detailed job log with pagination. Essential for debugging recovery failures.

**Request**:

```json
{
    "jobID": "drsjob-1234567890abcdef0",
    "maxResults": 100,
    "nextToken": "string"
}
```

**Response**:

```json
{
    "items": [
        {
            "logDateTime": "2024-01-15T14:30:00Z",
            "event": "JOB_START",
            "eventData": {
                "sourceServerID": "s-1234567890abcdef0",
                "targetInstanceID": "i-0987654321fedcba0",
                "conversionServerID": "i-conv123456789",
                "rawError": ""
            }
        }
    ],
    "nextToken": "string"
}
```

**Event Types**: `JOB_START`, `SERVER_SKIPPED`, `CLEANUP_START`, `CLEANUP_END`, `CLEANUP_FAIL`, `SNAPSHOT_START`, `SNAPSHOT_END`, `SNAPSHOT_FAIL`, `USING_PREVIOUS_SNAPSHOT`, `USING_PREVIOUS_SNAPSHOT_FAILED`, `CONVERSION_START`, `CONVERSION_END`, `CONVERSION_FAIL`, `LAUNCH_START`, `LAUNCH_FAILED`, `JOB_CANCEL`, `JOB_END`

### DeleteJob

**Endpoint**: `POST /DeleteJob`

**Purpose**: Deletes a single job by ID.

**Request**:

```json
{
    "jobID": "drsjob-1234567890abcdef0"
}
```

---

## Recovery Instance Management

### DescribeRecoveryInstances

**Endpoint**: `POST /DescribeRecoveryInstances`

**Purpose**: Get information about launched recovery instances.

**Request**:

```json
{
    "filters": {
        "recoveryInstanceIDs": ["i-0987654321fedcba0"],
        "sourceServerIDs": ["s-1234567890abcdef0"]
    },
    "maxResults": 200,
    "nextToken": "string"
}
```

**Response**:

```json
{
    "items": [
        {
            "recoveryInstanceID": "i-0987654321fedcba0",
            "arn": "arn:aws:drs:us-east-1:123456789012:recovery-instance/i-0987654321fedcba0",
            "sourceServerID": "s-1234567890abcdef0",
            "ec2InstanceID": "i-0987654321fedcba0",
            "ec2InstanceState": {
                "name": "running"
            },
            "jobID": "drsjob-1234567890abcdef0",
            "isDrill": false,
            "failback": {
                "state": "FAILBACK_NOT_STARTED",
                "agentLastSeenByServiceDateTime": "2024-01-15T14:45:00Z"
            },
            "dataReplicationInfo": {
                "dataReplicationState": "NOT_STARTED"
            }
        }
    ],
    "nextToken": "string"
}
```

**Failback States**: `FAILBACK_NOT_STARTED`, `FAILBACK_IN_PROGRESS`, `FAILBACK_READY_FOR_LAUNCH`, `FAILBACK_COMPLETED`, `FAILBACK_ERROR`, `FAILBACK_NOT_READY_FOR_REPLICATION`, `FAILBACK_LAUNCH_STATE_NOT_AVAILABLE`

### TerminateRecoveryInstances

**Endpoint**: `POST /TerminateRecoveryInstances`

**Purpose**: Terminate recovery instances (for drills or failback completion).

**Request**:

```json
{
    "recoveryInstanceIDs": ["i-0987654321fedcba0", "i-0987654321fedcba1"]
}
```

**Response**: Returns a job object tracking the termination.

### DeleteRecoveryInstance

**Endpoint**: `POST /DeleteRecoveryInstance`

**Purpose**: Deletes a single recovery instance by ID.

**Request**:

```json
{
    "recoveryInstanceID": "i-0987654321fedcba0"
}
```

### DisconnectRecoveryInstance

**Endpoint**: `POST /DisconnectRecoveryInstance`

**Purpose**: Disconnect a recovery instance from DRS.

**Request**:

```json
{
    "recoveryInstanceID": "i-0987654321fedcba0"
}
```

---

## Failback Operations

### StartFailbackLaunch

**Endpoint**: `POST /StartFailbackLaunch`

**Purpose**: Initiates failback for recovery instances. Runs conversion and reboots the machine to complete failback.

**Request**:

```json
{
    "recoveryInstanceIDs": ["i-0987654321fedcba0"],
    "tags": {
        "FailbackType": "Planned"
    }
}
```

**Response**: Returns a job object tracking the failback launch.

### StopFailback

**Endpoint**: `POST /StopFailback`

**Purpose**: Stops the failback process for a recovery instance. Changes state back to `FAILBACK_NOT_STARTED`.

**Request**:

```json
{
    "recoveryInstanceID": "i-0987654321fedcba0"
}
```

### ReverseReplication

**Endpoint**: `POST /ReverseReplication`

**Purpose**: Start replication to origin/target region. For recovery instances on target region, starts replication back to origin. For failback instances on origin region, starts replication to target region to re-protect them.

**Request**:

```json
{
    "recoveryInstanceID": "i-0987654321fedcba0"
}
```

**Response**:

```json
{
    "reversedDirectionSourceServerArn": "arn:aws:drs:us-east-1:123456789012:source-server/s-newserver12345678"
}
```

### GetFailbackReplicationConfiguration

**Endpoint**: `POST /GetFailbackReplicationConfiguration`

**Purpose**: Get failback replication configuration for a recovery instance.

**Request**:

```json
{
    "recoveryInstanceID": "i-0987654321fedcba0"
}
```

### UpdateFailbackReplicationConfiguration

**Endpoint**: `POST /UpdateFailbackReplicationConfiguration`

**Purpose**: Update failback replication configuration settings.

**Request**:

```json
{
    "recoveryInstanceID": "i-0987654321fedcba0",
    "bandwidthThrottling": 0,
    "name": "failback-config",
    "usePrivateIP": true
}
```

---

## Launch Configuration

### GetLaunchConfiguration

**Endpoint**: `POST /GetLaunchConfiguration`

**Purpose**: Retrieve launch configuration for a source server.

**Request**:

```json
{
    "sourceServerID": "s-1234567890abcdef0"
}
```

**Response**:

```json
{
    "sourceServerID": "s-1234567890abcdef0",
    "name": "web-server-01-launch-config",
    "ec2LaunchTemplateID": "lt-1234567890abcdef0",
    "launchDisposition": "STARTED",
    "targetInstanceTypeRightSizingMethod": "BASIC",
    "copyPrivateIp": false,
    "copyTags": true,
    "licensing": {
        "osByol": false
    },
    "bootMode": "LEGACY_BIOS",
    "postLaunchEnabled": true
}
```

**Launch Disposition Values**: `STOPPED`, `STARTED`

**Right Sizing Methods**: `NONE`, `BASIC`, `IN_AWS`

**Boot Modes**: `LEGACY_BIOS`, `UEFI`, `USE_SOURCE`

### UpdateLaunchConfiguration

**Endpoint**: `POST /UpdateLaunchConfiguration`

**Purpose**: Modify launch configuration for a source server.

**Request**:

```json
{
    "sourceServerID": "s-1234567890abcdef0",
    "launchDisposition": "STARTED",
    "targetInstanceTypeRightSizingMethod": "BASIC",
    "copyPrivateIp": false,
    "copyTags": true,
    "postLaunchEnabled": true
}
```

### CreateLaunchConfigurationTemplate

**Endpoint**: `POST /CreateLaunchConfigurationTemplate`

**Purpose**: Create a launch configuration template for consistent settings across source servers.

**Request**:

```json
{
    "launchDisposition": "STARTED",
    "targetInstanceTypeRightSizingMethod": "BASIC",
    "copyPrivateIp": false,
    "copyTags": true,
    "postLaunchEnabled": true,
    "tags": {
        "Environment": "Production"
    }
}
```

### DescribeLaunchConfigurationTemplates

**Endpoint**: `POST /DescribeLaunchConfigurationTemplates`

**Purpose**: List launch configuration templates.

**Request**:

```json
{
    "launchConfigurationTemplateIDs": ["lct-1234567890abcdef0"],
    "maxResults": 50,
    "nextToken": "string"
}
```

---

## Launch Actions

### PutLaunchAction

**Endpoint**: `POST /PutLaunchAction`

**Purpose**: Create or update a launch action (SSM document execution after recovery).

**Request**:

```json
{
    "resourceId": "s-1234567890abcdef0",
    "actionId": "12345678-1234-1234-1234-123456789012",
    "actionCode": "AWS-RunShellScript",
    "actionVersion": "$DEFAULT",
    "name": "health-check",
    "description": "Post-launch health check",
    "category": "VALIDATION",
    "order": 1,
    "active": true,
    "optional": false,
    "parameters": {
        "commands": {
            "type": "STATIC",
            "value": "systemctl status apache2"
        }
    }
}
```

**Category Values**: `MONITORING`, `VALIDATION`, `CONFIGURATION`, `SECURITY`, `OTHER`

### ListLaunchActions

**Endpoint**: `POST /ListLaunchActions`

**Purpose**: List launch actions for a source server or template.

**Request**:

```json
{
    "resourceId": "s-1234567890abcdef0",
    "filters": {
        "actionIds": ["12345678-1234-1234-1234-123456789012"]
    },
    "maxResults": 50,
    "nextToken": "string"
}
```

### DeleteLaunchAction

**Endpoint**: `POST /DeleteLaunchAction`

**Purpose**: Delete a launch action.

**Request**:

```json
{
    "resourceId": "s-1234567890abcdef0",
    "actionId": "12345678-1234-1234-1234-123456789012"
}
```

---

## Replication Configuration

### GetReplicationConfiguration

**Endpoint**: `POST /GetReplicationConfiguration`

**Purpose**: Retrieve replication settings for a source server.

**Request**:

```json
{
    "sourceServerID": "s-1234567890abcdef0"
}
```

**Response**:

```json
{
    "sourceServerID": "s-1234567890abcdef0",
    "name": "web-server-01-replication",
    "stagingAreaSubnetId": "subnet-1234567890abcdef0",
    "associateDefaultSecurityGroup": true,
    "securityGroupIDs": ["sg-1234567890abcdef0"],
    "replicationServerInstanceType": "t3.small",
    "useDedicatedReplicationServer": false,
    "defaultLargeStagingDiskType": "GP3",
    "ebsEncryption": "DEFAULT",
    "bandwidthThrottling": 0,
    "dataPlaneRouting": "PRIVATE_IP",
    "createPublicIP": false,
    "pitPolicy": [
        {
            "ruleID": 1,
            "interval": 10,
            "retentionDuration": 60,
            "units": "MINUTE",
            "enabled": true
        }
    ]
}
```

**Data Plane Routing**: `PRIVATE_IP`, `PUBLIC_IP`

**EBS Encryption**: `DEFAULT`, `CUSTOM`

**Staging Disk Types**: `GP2`, `GP3`, `ST1`, `AUTO`

### UpdateReplicationConfiguration

**Endpoint**: `POST /UpdateReplicationConfiguration`

**Purpose**: Modify replication settings for a source server.

**Request**:

```json
{
    "sourceServerID": "s-1234567890abcdef0",
    "stagingAreaSubnetId": "subnet-1234567890abcdef0",
    "replicationServerInstanceType": "t3.small",
    "bandwidthThrottling": 100,
    "dataPlaneRouting": "PRIVATE_IP"
}
```

---

## Recovery Snapshots

### DescribeRecoverySnapshots

**Endpoint**: `POST /DescribeRecoverySnapshots`

**Purpose**: List available recovery snapshots for point-in-time recovery.

**Request**:

```json
{
    "filters": {
        "sourceServerID": "s-1234567890abcdef0",
        "fromDateTime": "2024-01-15T00:00:00Z",
        "toDateTime": "2024-01-15T23:59:59Z"
    },
    "order": "DESC",
    "maxResults": 50,
    "nextToken": "string"
}
```

**Response**:

```json
{
    "items": [
        {
            "sourceServerID": "s-1234567890abcdef0",
            "snapshotID": "pit-1234567890abcdef0",
            "expectedTimestamp": "2024-01-15T14:00:00Z",
            "timestamp": "2024-01-15T14:00:15Z",
            "ebsSnapshots": ["snap-0987654321fedcba0"]
        }
    ],
    "nextToken": "string"
}
```

---

## Source Network Management

### CreateSourceNetwork

**Endpoint**: `POST /CreateSourceNetwork`

**Purpose**: Create a Source Network resource for VPC-level disaster recovery.

**Request**:

```json
{
    "vpcID": "vpc-1234567890abcdef0",
    "originAccountID": "123456789012",
    "originRegion": "us-east-1",
    "tags": {
        "Environment": "Production"
    }
}
```

**Response**:

```json
{
    "sourceNetworkID": "sn-1234567890abcdef0"
}
```

### DescribeSourceNetworks

**Endpoint**: `POST /DescribeSourceNetworks`

**Purpose**: List source networks.

**Request**:

```json
{
    "filters": {
        "sourceNetworkIDs": ["sn-1234567890abcdef0"],
        "originAccountID": "123456789012",
        "originRegion": "us-east-1"
    },
    "maxResults": 50,
    "nextToken": "string"
}
```

### StartSourceNetworkRecovery

**Endpoint**: `POST /StartSourceNetworkRecovery`

**Purpose**: Start recovery for source networks (VPC-level recovery).

**Request**:

```json
{
    "sourceNetworks": [
        {
            "sourceNetworkID": "sn-1234567890abcdef0",
            "cfnStackName": "recovered-vpc-stack"
        }
    ],
    "deployAsNew": false,
    "tags": {
        "RecoveryType": "VPC"
    }
}
```

### StartSourceNetworkReplication

**Endpoint**: `POST /StartSourceNetworkReplication`

**Purpose**: Start replication for a source network.

**Request**:

```json
{
    "sourceNetworkID": "sn-1234567890abcdef0"
}
```

### StopSourceNetworkReplication

**Endpoint**: `POST /StopSourceNetworkReplication`

**Purpose**: Stop replication for a source network.

**Request**:

```json
{
    "sourceNetworkID": "sn-1234567890abcdef0"
}
```

### ExportSourceNetworkCfnTemplate

**Endpoint**: `POST /ExportSourceNetworkCfnTemplate`

**Purpose**: Export CloudFormation template for a source network.

**Request**:

```json
{
    "sourceNetworkID": "sn-1234567890abcdef0"
}
```

---

## Cross-Account Operations

### CreateExtendedSourceServer

**Endpoint**: `POST /CreateExtendedSourceServer`

**Purpose**: Create an extended source server for cross-account replication.

**Request**:

```json
{
    "sourceServerArn": "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0",
    "tags": {
        "CrossAccount": "true"
    }
}
```

### ListExtensibleSourceServers

**Endpoint**: `POST /ListExtensibleSourceServers`

**Purpose**: List source servers available for extension from staging accounts.

**Request**:

```json
{
    "stagingAccountID": "123456789012",
    "maxResults": 50,
    "nextToken": "string"
}
```

### ListStagingAccounts

**Endpoint**: `POST /ListStagingAccounts`

**Purpose**: List staging accounts for cross-account replication.

**Request**:

```json
{
    "maxResults": 50,
    "nextToken": "string"
}
```

---

## Tagging

### TagResource

**Endpoint**: `POST /TagResource`

**Purpose**: Add or update tags on a DRS resource.

**Request**:

```json
{
    "resourceArn": "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0",
    "tags": {
        "Environment": "Production",
        "Application": "WebApp"
    }
}
```

### UntagResource

**Endpoint**: `DELETE /UntagResource`

**Purpose**: Remove tags from a DRS resource.

**Request Parameters**:

- `resourceArn` (query): ARN of the resource
- `tagKeys` (query): List of tag keys to remove

### ListTagsForResource

**Endpoint**: `GET /ListTagsForResource`

**Purpose**: List all tags for a DRS resource.

**Request Parameters**:

- `resourceArn` (query): ARN of the resource

---

## Error Handling

### Common Error Responses

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| ValidationException | 400 | Input validation failed |
| UninitializedAccountException | 400 | DRS not initialized in account |
| AccessDeniedException | 403 | Insufficient permissions |
| ResourceNotFoundException | 404 | Resource not found |
| ConflictException | 409 | Conflict with current state |
| ServiceQuotaExceededException | 402 | Service quota exceeded |
| ThrottlingException | 429 | Rate limit exceeded |
| InternalServerException | 500 | Internal server error |

**Example Error Response**:

```json
{
    "__type": "ValidationException",
    "message": "1 validation error detected: Value null at 'sourceServerID' failed to satisfy constraint: Member must not be null.",
    "fieldList": [
        {
            "name": "sourceServerID",
            "message": "Member must not be null"
        }
    ],
    "reason": "FIELD_VALIDATION_FAILED"
}
```

---

## Python SDK Examples

### Basic Client Setup

```python
import boto3
from botocore.exceptions import ClientError
import time

# Initialize DRS client
drs_client = boto3.client('drs', region_name='us-east-1')

def handle_drs_error(func):
    """Decorator for DRS API error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"DRS API Error [{error_code}]: {error_message}")
            raise
    return wrapper
```

### List All Source Servers with Pagination

```python
@handle_drs_error
def list_all_source_servers(filters=None):
    """Get all DRS source servers with pagination"""
    servers = []
    next_token = None
    
    while True:
        params = {'maxResults': 200}
        if next_token:
            params['nextToken'] = next_token
        if filters:
            params['filters'] = filters
            
        response = drs_client.describe_source_servers(**params)
        servers.extend(response.get('items', []))
        
        next_token = response.get('nextToken')
        if not next_token:
            break
    
    return servers
```

### Start Recovery with Monitoring

```python
@handle_drs_error
def start_recovery_with_monitoring(source_server_ids, is_drill=False, snapshot_ids=None):
    """Start recovery and monitor progress until completion"""
    
    # Prepare source servers for recovery
    source_servers = []
    for i, server_id in enumerate(source_server_ids):
        server_config = {'sourceServerID': server_id}
        if snapshot_ids and i < len(snapshot_ids):
            server_config['recoverySnapshotID'] = snapshot_ids[i]
        source_servers.append(server_config)
    
    # Start recovery
    response = drs_client.start_recovery(
        sourceServers=source_servers,
        isDrill=is_drill,
        tags={'RecoveryType': 'Drill' if is_drill else 'Recovery'}
    )
    
    job_id = response['job']['jobID']
    print(f"Recovery job started: {job_id}")
    
    # Monitor job progress
    while True:
        job_response = drs_client.describe_jobs(
            filters={'jobIDs': [job_id]}
        )
        
        if not job_response['items']:
            break
            
        job = job_response['items'][0]
        status = job['status']
        
        # Check participating servers status
        for server in job.get('participatingServers', []):
            print(f"  Server {server['sourceServerID']}: {server['launchStatus']}")
        
        print(f"Job {job_id} status: {status}")
        
        if status in ['COMPLETED', 'PARTIALLY_SUCCEEDED', 'FAILED']:
            break
            
        time.sleep(30)
    
    return job
```

### Get Job Log Items for Debugging

```python
@handle_drs_error
def get_job_logs(job_id):
    """Get all log items for a job"""
    logs = []
    next_token = None
    
    while True:
        params = {'jobID': job_id, 'maxResults': 100}
        if next_token:
            params['nextToken'] = next_token
            
        response = drs_client.describe_job_log_items(**params)
        logs.extend(response.get('items', []))
        
        next_token = response.get('nextToken')
        if not next_token:
            break
    
    # Print formatted logs
    for log in logs:
        print(f"[{log['logDateTime']}] {log['event']}")
        if log.get('eventData', {}).get('rawError'):
            print(f"  Error: {log['eventData']['rawError']}")
    
    return logs
```

### Retry with Exponential Backoff

```python
import random

def retry_with_backoff(func, max_retries=3):
    """Retry function with exponential backoff for throttling"""
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Throttled, waiting {wait_time:.2f}s before retry...")
                    time.sleep(wait_time)
                    continue
            raise
    raise Exception(f"Max retries ({max_retries}) exceeded")
```

### Complete Recovery Workflow Example

```python
def execute_drill_workflow(protection_group_servers):
    """Execute a complete drill workflow"""
    
    # 1. Start drill recovery
    print("Starting drill recovery...")
    job = start_recovery_with_monitoring(
        source_server_ids=protection_group_servers,
        is_drill=True
    )
    
    if job['status'] != 'COMPLETED':
        print(f"Drill failed with status: {job['status']}")
        get_job_logs(job['jobID'])
        return False
    
    # 2. Get recovery instances
    print("Getting recovery instances...")
    recovery_instances = []
    for server in job.get('participatingServers', []):
        if server.get('recoveryInstanceID'):
            recovery_instances.append(server['recoveryInstanceID'])
    
    print(f"Recovery instances launched: {recovery_instances}")
    
    # 3. Verify instances are running (add your validation logic)
    response = drs_client.describe_recovery_instances(
        filters={'recoveryInstanceIDs': recovery_instances}
    )
    
    for instance in response.get('items', []):
        print(f"Instance {instance['recoveryInstanceID']}: {instance['ec2InstanceState']['name']}")
    
    # 4. Terminate drill instances
    print("Terminating drill instances...")
    terminate_response = drs_client.terminate_recovery_instances(
        recoveryInstanceIDs=recovery_instances
    )
    
    print(f"Termination job: {terminate_response['job']['jobID']}")
    return True
```

---

## Rate Limits and Best Practices

### API Rate Limits

| API | Rate Limit |
|-----|------------|
| DescribeSourceServers | 10 requests/second |
| DescribeJobs | 10 requests/second |
| DescribeRecoveryInstances | 10 requests/second |
| StartRecovery | 2 requests/second |
| TerminateRecoveryInstances | 2 requests/second |
| Other APIs | 5 requests/second |

### Best Practices

1. **Initialize Service First**: Always call `InitializeService` before using other DRS APIs in a new account/region.

2. **Use Pagination**: Always handle `nextToken` for large result sets to avoid missing data.

3. **Implement Retry Logic**: Use exponential backoff for `ThrottlingException` errors.

4. **Batch Operations**: Group multiple servers in single recovery jobs when possible (max 200 servers per job).

5. **Monitor Job Status**: Poll job status rather than assuming immediate completion. Recovery can take 15-45 minutes.

6. **Tag Resources**: Use consistent tagging for tracking, automation, and cost allocation.

7. **Handle Errors Gracefully**: Implement proper error handling for all API calls, especially for long-running operations.

8. **Use Job Logs for Debugging**: When recovery fails, always check `DescribeJobLogItems` for detailed error information.

9. **Validate Before Recovery**: Check source server replication state is `CONTINUOUS` before starting recovery.

10. **Clean Up Drill Instances**: Always terminate drill recovery instances after testing to avoid unnecessary costs.

---

## Data Replication States

| State | Description |
|-------|-------------|
| `STOPPED` | Replication is stopped |
| `INITIATING` | Replication is being initiated |
| `INITIAL_SYNC` | Initial data sync in progress |
| `BACKLOG` | Replication has backlog |
| `CREATING_SNAPSHOT` | Creating recovery snapshot |
| `CONTINUOUS` | Continuous replication active (ready for recovery) |
| `PAUSED` | Replication paused |
| `RESCAN` | Rescanning disks |
| `STALLED` | Replication stalled |
| `DISCONNECTED` | Agent disconnected |

---

## Job Event Types Reference

| Event | Description |
|-------|-------------|
| `JOB_START` | Job has started |
| `JOB_END` | Job completed |
| `JOB_CANCEL` | Job was cancelled |
| `SERVER_SKIPPED` | Server was skipped |
| `SNAPSHOT_START` | Snapshot creation started |
| `SNAPSHOT_END` | Snapshot creation completed |
| `SNAPSHOT_FAIL` | Snapshot creation failed |
| `USING_PREVIOUS_SNAPSHOT` | Using existing snapshot |
| `CONVERSION_START` | Conversion started |
| `CONVERSION_END` | Conversion completed |
| `CONVERSION_FAIL` | Conversion failed |
| `LAUNCH_START` | Instance launch started |
| `LAUNCH_FAILED` | Instance launch failed |
| `CLEANUP_START` | Cleanup started |
| `CLEANUP_END` | Cleanup completed |
| `CLEANUP_FAIL` | Cleanup failed |

---

## Related Resources

- [AWS DRS User Guide](https://docs.aws.amazon.com/drs/latest/userguide/what-is-drs.html)
- [AWS DRS API Reference](https://docs.aws.amazon.com/drs/latest/APIReference/Welcome.html)
- [AWS DRS Pricing](https://aws.amazon.com/disaster-recovery/pricing/)
- [boto3 DRS Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/drs.html)
