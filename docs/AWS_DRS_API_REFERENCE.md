# AWS Elastic Disaster Recovery (DRS) REST API Reference

A comprehensive reference for AWS DRS REST API endpoints used in disaster recovery orchestration.

## Overview

AWS Elastic Disaster Recovery (DRS) provides REST APIs for managing source servers, replication, and recovery operations. This document covers the key endpoints used in the DRS Orchestration Solution.

## Authentication

All DRS API calls require AWS Signature Version 4 authentication:

```python
import boto3
drs_client = boto3.client('drs', region_name='us-east-1')
```

## Base URL Structure

```
https://drs.{region}.amazonaws.com/
```

## Source Server Management

### List Source Servers

**Endpoint**: `POST /DescribeSourceServers`

**Purpose**: Retrieve all DRS source servers in the current region

**Request**:
```json
{
    "filters": {
        "sourceServerIDs": ["s-1234567890abcdef0"],
        "isArchived": false
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
            "hostname": "web-server-01",
            "arn": "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0",
            "tags": {
                "Environment": "Production",
                "Application": "WebApp"
            },
            "dataReplicationInfo": {
                "dataReplicationState": "CONTINUOUS",
                "dataReplicationInitiation": {
                    "startDateTime": "2024-01-15T10:30:00Z",
                    "nextAttemptDateTime": "2024-01-15T11:00:00Z"
                },
                "dataReplicationError": {
                    "error": "NONE",
                    "rawError": ""
                },
                "lagDuration": "PT5M",
                "replicatedDisks": [
                    {
                        "deviceName": "/dev/sda1",
                        "totalStorageBytes": 107374182400,
                        "replicatedStorageBytes": 107374182400,
                        "rescannedStorageBytes": 0,
                        "backloggedStorageBytes": 0
                    }
                ]
            },
            "lifeCycle": {
                "addedToServiceDateTime": "2024-01-15T10:00:00Z",
                "firstByteDateTime": "2024-01-15T10:05:00Z",
                "elapsedReplicationDuration": "PT25M"
            },
            "sourceProperties": {
                "lastUpdatedDateTime": "2024-01-15T10:30:00Z",
                "recommendedInstanceType": "m5.large",
                "identificationHints": {
                    "fqdn": "web-server-01.example.com",
                    "hostname": "web-server-01",
                    "vmWareUuid": "502f1234-5678-90ab-cdef-123456789012"
                },
                "networkInterfaces": [
                    {
                        "macAddress": "02:12:34:56:78:90",
                        "ips": ["10.0.1.100", "192.168.1.100"]
                    }
                ],
                "disks": [
                    {
                        "deviceName": "/dev/sda1",
                        "bytes": 107374182400
                    }
                ],
                "cpus": [
                    {
                        "cores": 2,
                        "modelName": "Intel(R) Xeon(R) CPU E5-2686 v4 @ 2.30GHz"
                    }
                ],
                "ramBytes": 8589934592,
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

### Get Source Server Details

**Endpoint**: `POST /DescribeSourceServers`

**Purpose**: Get detailed information about a specific source server

**Request**:
```json
{
    "filters": {
        "sourceServerIDs": ["s-1234567890abcdef0"]
    }
}
```

### Update Source Server Tags

**Endpoint**: `POST /TagResource`

**Purpose**: Add or update tags on a source server

**Request**:
```json
{
    "resourceArn": "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0",
    "tags": {
        "ProtectionGroup": "WebServers",
        "Environment": "Production"
    }
}
```

## Recovery Job Management

### Start Recovery Job

**Endpoint**: `POST /StartRecovery`

**Purpose**: Initiate recovery for source servers

**Request**:
```json
{
    "sourceServers": [
        {
            "sourceServerID": "s-1234567890abcdef0",
            "recoveryInstanceProperties": {
                "instanceType": "m5.large",
                "targetInstanceTypeRightSizingMethod": "BASIC"
            }
        }
    ],
    "isDrill": false,
    "tags": {
        "RecoveryPlan": "WebApp-Recovery",
        "Wave": "1"
    }
}
```

**Response**:
```json
{
    "job": {
        "jobID": "job-1234567890abcdef0",
        "arn": "arn:aws:drs:us-east-1:123456789012:job/job-1234567890abcdef0",
        "type": "LAUNCH",
        "initiatedBy": "START_RECOVERY",
        "creationDateTime": "2024-01-15T14:30:00Z",
        "endDateTime": "2024-01-15T14:45:00Z",
        "status": "STARTED",
        "participatingServers": [
            {
                "sourceServerID": "s-1234567890abcdef0",
                "recoveryInstanceID": "i-0987654321fedcba0",
                "launchStatus": "LAUNCHED"
            }
        ],
        "tags": {
            "RecoveryPlan": "WebApp-Recovery",
            "Wave": "1"
        }
    }
}
```

### Describe Recovery Jobs

**Endpoint**: `POST /DescribeJobs`

**Purpose**: List and monitor recovery jobs

**Request**:
```json
{
    "filters": {
        "jobIDs": ["job-1234567890abcdef0"],
        "fromDate": "2024-01-15T00:00:00Z",
        "toDate": "2024-01-15T23:59:59Z"
    },
    "maxResults": 50,
    "nextToken": "string"
}
```

**Response**:
```json
{
    "items": [
        {
            "jobID": "job-1234567890abcdef0",
            "arn": "arn:aws:drs:us-east-1:123456789012:job/job-1234567890abcdef0",
            "type": "LAUNCH",
            "initiatedBy": "START_RECOVERY",
            "creationDateTime": "2024-01-15T14:30:00Z",
            "endDateTime": "2024-01-15T14:45:00Z",
            "status": "COMPLETED",
            "participatingServers": [
                {
                    "sourceServerID": "s-1234567890abcdef0",
                    "recoveryInstanceID": "i-0987654321fedcba0",
                    "launchStatus": "LAUNCHED"
                }
            ]
        }
    ],
    "nextToken": "string"
}
```

### Terminate Recovery Instances

**Endpoint**: `POST /TerminateRecoveryInstances`

**Purpose**: Terminate recovery instances (for drills or failback)

**Request**:
```json
{
    "recoveryInstanceIDs": ["i-0987654321fedcba0"]
}
```

## Recovery Instance Management

### Describe Recovery Instances

**Endpoint**: `POST /DescribeRecoveryInstances`

**Purpose**: Get information about launched recovery instances

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
            "ec2InstanceState": "running",
            "jobID": "job-1234567890abcdef0",
            "recoveryInstanceProperties": {
                "lastUpdatedDateTime": "2024-01-15T14:45:00Z",
                "identificationHints": {
                    "fqdn": "web-server-01.example.com",
                    "hostname": "web-server-01"
                },
                "networkInterfaces": [
                    {
                        "macAddress": "02:12:34:56:78:90",
                        "ips": ["10.0.1.100"]
                    }
                ],
                "disks": [
                    {
                        "deviceName": "/dev/sda1",
                        "bytes": 107374182400
                    }
                ],
                "cpus": [
                    {
                        "cores": 2,
                        "modelName": "Intel(R) Xeon(R) CPU E5-2686 v4 @ 2.30GHz"
                    }
                ],
                "ramBytes": 8589934592,
                "os": {
                    "fullString": "Ubuntu 20.04.3 LTS"
                }
            },
            "isDrill": false,
            "tags": {
                "ProtectionGroup": "WebServers"
            }
        }
    ],
    "nextToken": "string"
}
```

## Launch Configuration Management

### Get Launch Configuration

**Endpoint**: `POST /GetLaunchConfiguration`

**Purpose**: Retrieve launch configuration for a source server

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
    "postLaunchActions": {
        "deployment": "TEST_AND_CUTOVER",
        "s3LogBucket": "drs-logs-bucket",
        "s3OutputKeyPrefix": "post-launch-logs/",
        "cloudWatchLogGroupName": "/aws/drs/post-launch",
        "ssmDocuments": [
            {
                "actionName": "health-check",
                "ssmDocumentName": "DRS-PostLaunchHealthCheck",
                "timeoutSeconds": 300,
                "mustSucceedForCutover": true,
                "parameters": {
                    "InstanceId": "{{ InstanceId }}",
                    "CheckType": "basic"
                }
            }
        ]
    }
}
```

### Update Launch Configuration

**Endpoint**: `POST /UpdateLaunchConfiguration`

**Purpose**: Modify launch configuration for a source server

**Request**:
```json
{
    "sourceServerID": "s-1234567890abcdef0",
    "launchDisposition": "STARTED",
    "targetInstanceTypeRightSizingMethod": "BASIC",
    "copyPrivateIp": false,
    "copyTags": true,
    "postLaunchActions": {
        "deployment": "TEST_AND_CUTOVER",
        "s3LogBucket": "drs-logs-bucket",
        "ssmDocuments": [
            {
                "actionName": "application-startup",
                "ssmDocumentName": "DRS-ApplicationStartup",
                "timeoutSeconds": 600,
                "mustSucceedForCutover": true,
                "parameters": {
                    "ServiceName": "apache2"
                }
            }
        ]
    }
}
```

## Replication Configuration

### Get Replication Configuration

**Endpoint**: `POST /GetReplicationConfiguration`

**Purpose**: Retrieve replication settings for a source server

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
    "stagingAreaTags": {
        "Environment": "Production",
        "Purpose": "DRS-Staging"
    },
    "replicationServerInstanceType": "t3.small",
    "useDedicatedReplicationServer": false,
    "defaultLargeStagingDiskType": "GP3",
    "replicatedDisks": [
        {
            "deviceName": "/dev/sda1",
            "iops": 3000,
            "isBootDisk": true,
            "stagingDiskType": "GP3",
            "throughput": 125
        }
    ],
    "replicationServersSecurityGroupsIDs": ["sg-0987654321fedcba0"],
    "createPublicIP": false,
    "dataPlaneRouting": "PRIVATE_IP",
    "defaultSmallStagingDiskType": "GP3",
    "ebsEncryption": "DEFAULT",
    "ebsEncryptionKeyArn": "***REMOVED***",
    "bandwidthThrottling": 0,
    "pitPolicy": [
        {
            "interval": 10,
            "retentionDuration": 60,
            "units": "MINUTE",
            "enabled": true,
            "ruleID": 1
        }
    ]
}
```

## Recovery Snapshot Management

### Describe Recovery Snapshots

**Endpoint**: `POST /DescribeRecoverySnapshots`

**Purpose**: List available recovery snapshots for source servers

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
            "snapshotID": "snap-1234567890abcdef0",
            "expectedTimestamp": "2024-01-15T14:00:00Z",
            "timestamp": "2024-01-15T14:00:15Z",
            "ebsSnapshots": [
                {
                    "snapshotID": "snap-0987654321fedcba0",
                    "volumeSize": 100
                }
            ]
        }
    ],
    "nextToken": "string"
}
```

## Error Handling

### Common Error Responses

**Validation Error**:
```json
{
    "__type": "ValidationException",
    "message": "1 validation error detected: Value null at 'sourceServerID' failed to satisfy constraint: Member must not be null."
}
```

**Resource Not Found**:
```json
{
    "__type": "ResourceNotFoundException",
    "message": "Source server s-1234567890abcdef0 not found."
}
```

**Access Denied**:
```json
{
    "__type": "AccessDeniedException",
    "message": "User: arn:aws:iam::123456789012:user/test-user is not authorized to perform: drs:DescribeSourceServers"
}
```

**Throttling**:
```json
{
    "__type": "ThrottlingException",
    "message": "Rate exceeded"
}
```

## Python SDK Examples

### Basic Client Setup

```python
import boto3
from botocore.exceptions import ClientError

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

### List All Source Servers

```python
@handle_drs_error
def list_all_source_servers():
    """Get all DRS source servers with pagination"""
    servers = []
    next_token = None
    
    while True:
        params = {'maxResults': 200}
        if next_token:
            params['nextToken'] = next_token
            
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
def start_recovery_with_monitoring(source_server_ids, is_drill=False):
    """Start recovery and monitor progress"""
    
    # Prepare source servers for recovery
    source_servers = [
        {
            'sourceServerID': server_id,
            'recoveryInstanceProperties': {
                'targetInstanceTypeRightSizingMethod': 'BASIC'
            }
        }
        for server_id in source_server_ids
    ]
    
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
        
        print(f"Job {job_id} status: {status}")
        
        if status in ['COMPLETED', 'PARTIALLY_SUCCEEDED', 'FAILED']:
            break
            
        time.sleep(30)  # Wait 30 seconds before checking again
    
    return job
```

### Get Server Recovery Status

```python
@handle_drs_error
def get_server_recovery_status(source_server_id):
    """Get current recovery status for a source server"""
    
    # Check if server has active recovery instances
    recovery_response = drs_client.describe_recovery_instances(
        filters={'sourceServerIDs': [source_server_id]}
    )
    
    recovery_instances = recovery_response.get('items', [])
    
    # Get recent jobs for this server
    jobs_response = drs_client.describe_jobs(
        filters={
            'fromDate': (datetime.now() - timedelta(days=7)).isoformat()
        }
    )
    
    server_jobs = [
        job for job in jobs_response.get('items', [])
        if any(server['sourceServerID'] == source_server_id 
               for server in job.get('participatingServers', []))
    ]
    
    return {
        'sourceServerID': source_server_id,
        'recoveryInstances': recovery_instances,
        'recentJobs': server_jobs
    }
```

## Rate Limits and Best Practices

### API Rate Limits

- **DescribeSourceServers**: 10 requests per second
- **StartRecovery**: 2 requests per second
- **DescribeJobs**: 10 requests per second
- **DescribeRecoveryInstances**: 10 requests per second

### Best Practices

1. **Use Pagination**: Always handle `nextToken` for large result sets
2. **Implement Retry Logic**: Use exponential backoff for throttling errors
3. **Batch Operations**: Group multiple servers in single recovery jobs when possible
4. **Monitor Job Status**: Poll job status rather than assuming immediate completion
5. **Tag Resources**: Use consistent tagging for tracking and automation
6. **Handle Errors Gracefully**: Implement proper error handling for all API calls

### Example Retry Logic

```python
import time
import random
from botocore.exceptions import ClientError

def retry_with_backoff(func, max_retries=3):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait_time)
                    continue
            raise
    raise Exception(f"Max retries ({max_retries}) exceeded")
```

## Integration with DRS Orchestration Solution

### Server Discovery Integration

```python
def discover_drs_servers_for_protection_group(region, current_pg_id=None):
    """Discover DRS servers with assignment tracking"""
    
    # Get all source servers
    servers = list_all_source_servers()
    
    # Get existing Protection Group assignments
    pg_assignments = get_protection_group_assignments()
    
    # Format for UI
    formatted_servers = []
    for server in servers:
        server_id = server['sourceServerID']
        hostname = server.get('sourceProperties', {}).get('identificationHints', {}).get('hostname', 'Unknown')
        
        # Check assignment status
        assigned_pg = pg_assignments.get(server_id)
        is_available = not assigned_pg or assigned_pg == current_pg_id
        
        formatted_servers.append({
            'serverId': server_id,
            'hostname': hostname,
            'isAvailable': is_available,
            'assignedProtectionGroup': assigned_pg,
            'replicationStatus': server.get('dataReplicationInfo', {}).get('dataReplicationState', 'UNKNOWN'),
            'tags': server.get('tags', {})
        })
    
    return formatted_servers
```

This comprehensive API reference provides all the essential DRS REST API endpoints needed for building disaster recovery orchestration solutions.