# AWS DRS Orchestration REST API Reference

A comprehensive reference for the AWS DRS Orchestration Solution REST API endpoints.

> **Last Updated**: December 2024  
> **API Version**: 1.0  
> **Base URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/prod`

## Overview

The AWS DRS Orchestration Solution provides a comprehensive REST API for managing disaster recovery operations through Protection Groups, Recovery Plans, and Executions. This API enables programmatic access to all orchestration features including multi-wave recovery, pause/resume capabilities, and cross-account management.

## Authentication

All API requests require a valid Cognito JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://your-api-endpoint.execute-api.us-east-1.amazonaws.com/prod/protection-groups
```

### Getting a Token

```bash
# Using AWS CLI
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id {client-id} \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME={email},PASSWORD={password} \
  --query 'AuthenticationResult.IdToken' \
  --output text)
```

## Base URL Structure

```text
https://{api-gateway-id}.execute-api.{region}.amazonaws.com/prod
```

## API Categories

| Category | Description | Endpoints |
|----------|-------------|-----------|
| **Protection Groups** | Manage logical groupings of DRS source servers | 6 endpoints |
| **Recovery Plans** | Define multi-wave recovery sequences | 6 endpoints |
| **Executions** | Monitor and control recovery operations | 9 endpoints |
| **DRS Integration** | Direct AWS DRS service integration | 4 endpoints |
| **EC2 Resources** | Launch configuration management | 4 endpoints |
| **Multi-Account** | Cross-account orchestration | 5 endpoints |
| **Configuration** | Export/import and health checks | 3 endpoints |

---

## Protection Groups API

Protection Groups organize DRS source servers into logical units for coordinated recovery.

### List Protection Groups

**Endpoint**: `GET /protection-groups`

**Purpose**: Retrieve all protection groups with optional filtering.

**Query Parameters**:
- `accountId` (string) - Filter by target account ID
- `region` (string) - Filter by AWS region
- `name` (string) - Filter by group name (partial match)
- `hasConflict` (boolean) - Filter by conflict status

**Request Example**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "${API_ENDPOINT}/protection-groups?region=us-east-1&hasConflict=false"
```

**Response**:
```json
{
  "protectionGroups": [
    {
      "groupId": "pg-12345678-1234-1234-1234-123456789012",
      "groupName": "Database-Servers",
      "description": "Production database servers for HRP application",
      "region": "us-east-1",
      "accountId": "123456789012",
      "serverSelectionTags": {
        "DR-Application": "HRP",
        "DR-Tier": "Database",
        "Environment": "Production"
      },
      "resolvedServers": [
        {
          "sourceServerID": "s-1234567890abcdef0",
          "hostname": "db-primary-01.example.com",
          "replicationState": "CONTINUOUS",
          "lifecycleState": "READY_FOR_LAUNCH"
        }
      ],
      "serverCount": 2,
      "hasConflict": false,
      "createdDate": 1703875200,
      "lastModifiedDate": 1703875200,
      "version": 1
    }
  ],
  "totalCount": 1
}
```

### Create Protection Group

**Endpoint**: `POST /protection-groups`

**Purpose**: Create a new protection group with tag-based or explicit server selection.

**Request Body**:
```json
{
  "GroupName": "Database-Servers",
  "Description": "Production database servers for HRP application",
  "Region": "us-east-1",
  "AccountId": "123456789012",
  "AssumeRoleName": "DRSOrchestrationCrossAccountRole",
  "ServerSelectionTags": {
    "DR-Application": "HRP",
    "DR-Tier": "Database",
    "Environment": "Production"
  },
  "LaunchConfig": {
    "SubnetId": "subnet-12345678",
    "SecurityGroupIds": ["sg-12345678", "sg-87654321"],
    "InstanceType": "r5.xlarge",
    "IamInstanceProfileName": "EC2-DRS-Instance-Profile",
    "CopyPrivateIp": true,
    "CopyTags": true,
    "Licensing": {"osByol": false},
    "TargetInstanceTypeRightSizingMethod": "BASIC",
    "LaunchDisposition": "STARTED"
  }
}
```

**Response**: Returns the created protection group with generated `groupId` and timestamps.

### Get Protection Group

**Endpoint**: `GET /protection-groups/{id}`

**Purpose**: Retrieve detailed information about a specific protection group.

**Path Parameters**:
- `id` (string, required) - Protection group ID

**Response**: Returns complete protection group details including resolved servers and launch configuration.

### Update Protection Group

**Endpoint**: `PUT /protection-groups/{id}`

**Purpose**: Update protection group with optimistic locking.

**Request Body**: Same as create, plus:
```json
{
  "Version": 2
}
```

**Response**: Returns updated protection group with incremented version.

### Delete Protection Group

**Endpoint**: `DELETE /protection-groups/{id}`

**Purpose**: Delete protection group (blocked if used in recovery plans).

**Response**:
```json
{
  "message": "Protection group deleted successfully",
  "groupId": "pg-12345678-1234-1234-1234-123456789012"
}
```

### Preview Server Resolution

**Endpoint**: `POST /protection-groups/resolve`

**Purpose**: Preview servers matching tags in real-time without creating a group.

**Request Body**:
```json
{
  "region": "us-east-1",
  "AccountId": "123456789012",
  "AssumeRoleName": "DRSOrchestrationCrossAccountRole",
  "ServerSelectionTags": {
    "DR-Application": "HRP",
    "DR-Tier": "Database"
  }
}
```

**Response**:
```json
{
  "region": "us-east-1",
  "ServerSelectionTags": {
    "DR-Application": "HRP",
    "DR-Tier": "Database"
  },
  "resolvedServers": [
    {
      "sourceServerID": "s-1234567890abcdef0",
      "hostname": "db-primary-01.example.com",
      "replicationState": "CONTINUOUS",
      "lifecycleState": "READY_FOR_LAUNCH",
      "tags": {
        "DR-Application": "HRP",
        "DR-Tier": "Database",
        "Environment": "Production"
      }
    }
  ],
  "serverCount": 1,
  "resolvedAt": 1703875200
}
```

---

## Recovery Plans API

Recovery Plans define multi-wave recovery sequences with dependency management.

### List Recovery Plans

**Endpoint**: `GET /recovery-plans`

**Purpose**: Retrieve all recovery plans with execution history and conflict information.

**Query Parameters**:
- `accountId` (string) - Filter by target account ID
- `name` (string) - Filter by plan name (partial match)
- `nameExact` (string) - Filter by exact plan name
- `tag` (string) - Filter by protection group tags (format: key=value)
- `hasConflict` (boolean) - Filter by server conflict status
- `status` (string) - Filter by last execution status

**Response**:
```json
{
  "recoveryPlans": [
    {
      "PlanId": "rp-12345678-1234-1234-1234-123456789012",
      "PlanName": "HRP-Multi-Tier-DR",
      "Description": "Complete HRP application disaster recovery",
      "Waves": [
        {
          "WaveName": "Database Tier",
          "WaveNumber": 1,
          "ProtectionGroupId": "pg-database-uuid",
          "PauseBeforeWave": false,
          "DependsOn": []
        }
      ],
      "LastExecutionStatus": "COMPLETED",
      "LastExecutionDate": 1703875200,
      "ExecutionCount": 5,
      "HasConflict": false,
      "CreatedDate": 1703875200,
      "Version": 1
    }
  ],
  "totalCount": 1
}
```

### Create Recovery Plan

**Endpoint**: `POST /recovery-plans`

**Purpose**: Create recovery plan with multi-wave configuration and dependency validation.

**Request Body**:
```json
{
  "PlanName": "HRP-Multi-Tier-DR",
  "Description": "Complete HRP application disaster recovery with dependency management",
  "Waves": [
    {
      "WaveName": "Database Tier",
      "WaveNumber": 1,
      "ProtectionGroupId": "pg-database-uuid",
      "PauseBeforeWave": false,
      "DependsOn": []
    },
    {
      "WaveName": "Application Tier",
      "WaveNumber": 2,
      "ProtectionGroupId": "pg-application-uuid",
      "PauseBeforeWave": true,
      "DependsOn": [1]
    },
    {
      "WaveName": "Web Tier",
      "WaveNumber": 3,
      "ProtectionGroupId": "pg-web-uuid",
      "PauseBeforeWave": false,
      "DependsOn": [2]
    }
  ]
}
```

**Validation Rules**:
- Wave numbers must be sequential starting from 1
- Dependencies must reference existing wave numbers
- Circular dependencies are detected and rejected
- Protection group IDs must exist and be valid

### Get Recovery Plan

**Endpoint**: `GET /recovery-plans/{id}`

**Purpose**: Retrieve detailed recovery plan with wave dependencies and execution history.

### Update Recovery Plan

**Endpoint**: `PUT /recovery-plans/{id}`

**Purpose**: Update recovery plan with validation and optimistic locking.

### Delete Recovery Plan

**Endpoint**: `DELETE /recovery-plans/{id}`

**Purpose**: Delete recovery plan (blocked if has active executions).

### Execute Recovery Plan

**Endpoint**: `POST /recovery-plans/{id}/execute`

**Purpose**: Start recovery plan execution in drill or recovery mode.

**Request Body**:
```json
{
  "ExecutionType": "DRILL",
  "InitiatedBy": "user@example.com",
  "Description": "Monthly DR drill for HRP application"
}
```

**Response**:
```json
{
  "executionId": "exec-12345678-1234-1234-1234-123456789012",
  "stepFunctionExecutionArn": "arn:aws:states:us-east-1:123456789012:execution:drs-orchestration:exec-12345678",
  "status": "PENDING",
  "message": "Execution started successfully"
}
```

### Check Existing Recovery Instances

**Endpoint**: `GET /recovery-plans/{id}/check-existing-instances`

**Purpose**: Check for existing recovery instances before execution to prevent conflicts.

**Response**:
```json
{
  "hasExistingInstances": true,
  "existingInstances": [
    {
      "sourceServerID": "s-1234567890abcdef0",
      "recoveryInstanceID": "i-0987654321fedcba0",
      "ec2InstanceState": "running",
      "jobID": "drsjob-previous-execution"
    }
  ],
  "recommendation": "Terminate existing instances before starting new execution"
}
```

---

## Executions API

Executions provide monitoring and control of recovery operations with real-time status updates.

### List Executions

**Endpoint**: `GET /executions`

**Purpose**: Retrieve execution history with advanced filtering and pagination.

**Query Parameters**:
- `planId` (string) - Filter by recovery plan ID
- `status` (string) - Filter by execution status
- `executionType` (string) - Filter by DRILL or RECOVERY
- `initiatedBy` (string) - Filter by who started the execution
- `startDate` (string) - Filter by start date (MM-DD-YYYY format)
- `endDate` (string) - Filter by end date (MM-DD-YYYY format)
- `dateRange` (string) - Quick filters: today, yesterday, thisWeek, lastWeek, thisMonth, lastMonth
- `limit` (number) - Limit number of results (default: 50)
- `sortBy` (string) - Sort field: StartTime, EndTime, Status (default: StartTime)
- `sortOrder` (string) - Sort direction: asc, desc (default: desc)

**Response**:
```json
{
  "executions": [
    {
      "ExecutionId": "exec-12345678-1234-1234-1234-123456789012",
      "PlanId": "rp-12345678-1234-1234-1234-123456789012",
      "PlanName": "HRP-Multi-Tier-DR",
      "ExecutionType": "DRILL",
      "Status": "COMPLETED",
      "InitiatedBy": "user@example.com",
      "StartTime": 1703875200,
      "EndTime": 1703878800,
      "Duration": 3600,
      "CurrentWave": 3,
      "TotalWaves": 3,
      "WaveStatuses": [
        {"WaveNumber": 1, "Status": "COMPLETED", "StartTime": 1703875200, "EndTime": 1703876400},
        {"WaveNumber": 2, "Status": "COMPLETED", "StartTime": 1703876400, "EndTime": 1703877600},
        {"WaveNumber": 3, "Status": "COMPLETED", "StartTime": 1703877600, "EndTime": 1703878800}
      ],
      "RecoveryInstancesLaunched": 6,
      "StepFunctionExecutionArn": "arn:aws:states:us-east-1:123456789012:execution:drs-orchestration:exec-12345678"
    }
  ],
  "totalCount": 1,
  "hasMore": false
}
```

### Create Execution

**Endpoint**: `POST /executions`

**Purpose**: Start new execution (alternative to recovery-plans execute endpoint).

### Get Execution Details

**Endpoint**: `GET /executions/{id}`

**Purpose**: Retrieve detailed execution status with real-time wave progress.

**Response**:
```json
{
  "ExecutionId": "exec-12345678-1234-1234-1234-123456789012",
  "PlanId": "rp-12345678-1234-1234-1234-123456789012",
  "PlanName": "HRP-Multi-Tier-DR",
  "ExecutionType": "DRILL",
  "Status": "IN_PROGRESS",
  "InitiatedBy": "user@example.com",
  "StartTime": 1703875200,
  "CurrentWave": 2,
  "TotalWaves": 3,
  "WaveDetails": [
    {
      "WaveNumber": 1,
      "WaveName": "Database Tier",
      "Status": "COMPLETED",
      "StartTime": 1703875200,
      "EndTime": 1703876400,
      "ServersLaunched": 2,
      "DRSJobId": "drsjob-wave1-12345678"
    },
    {
      "WaveNumber": 2,
      "WaveName": "Application Tier",
      "Status": "PAUSED",
      "PauseReason": "Manual approval required before application tier launch",
      "TaskToken": "AAAAKgAAAAIAAA..."
    }
  ],
  "StepFunctionExecutionArn": "arn:aws:states:us-east-1:123456789012:execution:drs-orchestration:exec-12345678",
  "CanPause": false,
  "CanResume": true,
  "CanCancel": true
}
```

### Pause Execution

**Endpoint**: `POST /executions/{id}/pause`

**Purpose**: Pause execution between waves using Step Functions waitForTaskToken.

**Response**:
```json
{
  "message": "Execution paused successfully",
  "status": "PAUSED",
  "pausedAt": 1703876400
}
```

### Resume Execution

**Endpoint**: `POST /executions/{id}/resume`

**Purpose**: Resume paused execution by sending task success to Step Functions.

**Response**:
```json
{
  "message": "Execution resumed successfully",
  "status": "IN_PROGRESS",
  "resumedAt": 1703876500
}
```

### Cancel Execution

**Endpoint**: `POST /executions/{id}/cancel`

**Purpose**: Cancel running execution and stop Step Functions state machine.

### Terminate Recovery Instances

**Endpoint**: `POST /executions/{id}/terminate-instances`

**Purpose**: Terminate recovery instances after drill completion for cost management.

**Response**:
```json
{
  "message": "Termination initiated for 6 recovery instances",
  "terminationJobId": "drsjob-terminate-12345678",
  "instancesTerminated": [
    "i-0987654321fedcba0",
    "i-0987654321fedcba1"
  ]
}
```

### Get Job Logs

**Endpoint**: `GET /executions/{id}/job-logs`

**Purpose**: Retrieve DRS job logs for execution with real-time updates.

**Query Parameters**:
- `waveNumber` (number) - Filter logs by specific wave
- `limit` (number) - Limit number of log entries (default: 100)

**Response**:
```json
{
  "executionId": "exec-12345678-1234-1234-1234-123456789012",
  "jobLogs": [
    {
      "waveNumber": 1,
      "jobId": "drsjob-wave1-12345678",
      "logEntries": [
        {
          "logDateTime": "2024-01-15T14:30:00Z",
          "event": "JOB_START",
          "eventData": {
            "sourceServerID": "s-1234567890abcdef0",
            "targetInstanceID": "i-0987654321fedcba0"
          }
        }
      ]
    }
  ],
  "totalEntries": 25
}
```

### Bulk Delete Executions

**Endpoint**: `DELETE /executions`

**Purpose**: Delete multiple selected executions.

**Request Body**:
```json
{
  "executionIds": [
    "exec-12345678-1234-1234-1234-123456789012",
    "exec-87654321-4321-4321-4321-210987654321"
  ]
}
```

---

## DRS Integration API

Direct integration with AWS DRS service for server discovery and quota management.

### Discover DRS Source Servers

**Endpoint**: `GET /drs/source-servers`

**Purpose**: Discover DRS source servers across all 28 commercial regions with advanced filtering.

**Query Parameters**:
- `region` (string, required) - Target AWS region
- `accountId` (string) - Target account ID for cross-account access
- `tags` (string) - Filter by server tags (JSON object)
- `replicationState` (string) - Filter by replication state
- `lifecycleState` (string) - Filter by lifecycle state
- `hostname` (string) - Filter by hostname (partial match)
- `includeArchived` (boolean) - Include archived servers (default: false)

**Request Example**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "${API_ENDPOINT}/drs/source-servers?region=us-east-1&replicationState=CONTINUOUS"
```

**Response**:
```json
{
  "region": "us-east-1",
  "sourceServers": [
    {
      "sourceServerID": "s-1234567890abcdef0",
      "hostname": "web-server-01.example.com",
      "replicationState": "CONTINUOUS",
      "lifecycleState": "READY_FOR_LAUNCH",
      "lastSeenByServiceDateTime": "2024-01-15T14:30:00Z",
      "tags": {
        "Environment": "Production",
        "Application": "WebApp",
        "DR-Tier": "Web"
      },
      "sourceProperties": {
        "recommendedInstanceType": "m5.large",
        "os": {
          "fullString": "Ubuntu 20.04.3 LTS"
        },
        "cpus": [
          {
            "cores": 2,
            "modelName": "Intel(R) Xeon(R) CPU E5-2676 v3 @ 2.40GHz"
          }
        ],
        "ramBytes": 8589934592,
        "disks": [
          {
            "deviceName": "/dev/sda1",
            "bytes": 107374182400
          }
        ]
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
      }
    }
  ],
  "serverCount": 1,
  "queriedAt": 1703875200
}
```

### Get DRS Service Quotas

**Endpoint**: `GET /drs/quotas`

**Purpose**: Retrieve DRS service quotas and current usage for capacity planning.

**Query Parameters**:
- `region` (string, required) - Target AWS region
- `accountId` (string) - Target account ID for cross-account access

**Response**:
```json
{
  "region": "us-east-1",
  "quotas": {
    "replicatingServers": {
      "limit": 300,
      "current": 45,
      "available": 255,
      "utilizationPercent": 15,
      "status": "OK"
    },
    "sourceServers": {
      "limit": 4000,
      "current": 120,
      "available": 3880,
      "utilizationPercent": 3,
      "status": "OK"
    },
    "concurrentJobs": {
      "limit": 20,
      "current": 0,
      "available": 20,
      "utilizationPercent": 0,
      "status": "OK"
    },
    "serversPerJob": {
      "limit": 100,
      "description": "Maximum servers per recovery job"
    },
    "serversInAllJobs": {
      "limit": 500,
      "current": 0,
      "available": 500,
      "utilizationPercent": 0,
      "status": "OK"
    }
  },
  "warnings": [],
  "recommendations": [
    "Current usage is well within limits",
    "Consider enabling replication for additional servers"
  ],
  "queriedAt": 1703875200
}
```

### Get DRS Account Information

**Endpoint**: `GET /drs/accounts`

**Purpose**: Retrieve DRS account initialization status and configuration.

**Query Parameters**:
- `region` (string, required) - Target AWS region
- `includeCapacity` (boolean) - Include detailed capacity metrics (default: false)

**Response**:
```json
{
  "region": "us-east-1",
  "accountId": "123456789012",
  "drsInitialized": true,
  "initializationDate": "2024-01-01T00:00:00Z",
  "defaultReplicationConfiguration": {
    "stagingAreaSubnetId": "subnet-12345678",
    "replicationServerInstanceType": "t3.small",
    "defaultLargeStagingDiskType": "GP3",
    "ebsEncryption": "DEFAULT"
  },
  "capacity": {
    "totalSourceServers": 120,
    "replicatingServers": 45,
    "readyForLaunch": 40,
    "initialSync": 3,
    "disconnected": 2
  },
  "queriedAt": 1703875200
}
```

### Sync EC2 Tags to DRS

**Endpoint**: `POST /drs/tag-sync`

**Purpose**: Synchronize EC2 instance tags to DRS source servers across all regions.

**Request Body**:
```json
{
  "regions": ["us-east-1", "us-west-2"],
  "accountId": "123456789012",
  "sourceServerIds": ["s-1234567890abcdef0"],
  "dryRun": false
}
```

**Response**:
```json
{
  "syncResults": [
    {
      "region": "us-east-1",
      "sourceServerID": "s-1234567890abcdef0",
      "status": "SUCCESS",
      "tagsAdded": 3,
      "tagsUpdated": 1,
      "tagsRemoved": 0,
      "syncedTags": {
        "Environment": "Production",
        "Application": "WebApp",
        "DR-Tier": "Web"
      }
    }
  ],
  "totalServersProcessed": 1,
  "successCount": 1,
  "failureCount": 0,
  "syncedAt": 1703875200
}
```

---

## EC2 Resources API

Provides EC2 resource information for launch configuration management.

### List VPC Subnets

**Endpoint**: `GET /ec2/subnets`

**Purpose**: Retrieve VPC subnets for launch configuration.

**Query Parameters**:
- `region` (string, required) - Target AWS region
- `accountId` (string) - Target account ID for cross-account access
- `vpcId` (string) - Filter by VPC ID

**Response**:
```json
{
  "region": "us-east-1",
  "subnets": [
    {
      "SubnetId": "subnet-12345678",
      "VpcId": "vpc-12345678",
      "AvailabilityZone": "us-east-1a",
      "CidrBlock": "10.0.1.0/24",
      "State": "available",
      "MapPublicIpOnLaunch": false,
      "Tags": [
        {"Key": "Name", "Value": "Private Subnet 1A"}
      ]
    }
  ],
  "subnetCount": 1
}
```

### List Security Groups

**Endpoint**: `GET /ec2/security-groups`

**Purpose**: Retrieve security groups for launch configuration.

### List IAM Instance Profiles

**Endpoint**: `GET /ec2/instance-profiles`

**Purpose**: Retrieve IAM instance profiles for EC2 instances.

### List EC2 Instance Types

**Endpoint**: `GET /ec2/instance-types`

**Purpose**: Retrieve available EC2 instance types for right-sizing.

---

## Multi-Account Management API

Manages cross-account orchestration capabilities.

### List Target Accounts

**Endpoint**: `GET /accounts/targets`

**Purpose**: Retrieve registered target accounts for cross-account orchestration.

**Response**:
```json
{
  "targetAccounts": [
    {
      "accountId": "123456789012",
      "accountName": "Production Account",
      "crossAccountRoleName": "DRSOrchestrationCrossAccountRole",
      "regions": ["us-east-1", "us-west-2"],
      "status": "ACTIVE",
      "lastValidated": 1703875200,
      "createdDate": 1703875200
    }
  ],
  "totalCount": 1
}
```

### Register Target Account

**Endpoint**: `POST /accounts/targets`

**Purpose**: Register new target account with cross-account role.

**Request Body**:
```json
{
  "accountId": "123456789012",
  "accountName": "Production Account",
  "crossAccountRoleName": "DRSOrchestrationCrossAccountRole",
  "regions": ["us-east-1", "us-west-2"],
  "description": "Production workloads account"
}
```

### Update Target Account

**Endpoint**: `PUT /accounts/targets/{id}`

**Purpose**: Update target account configuration.

### Delete Target Account

**Endpoint**: `DELETE /accounts/targets/{id}`

**Purpose**: Unregister target account.

### Validate Cross-Account Access

**Endpoint**: `GET /accounts/targets/{id}/validate`

**Purpose**: Validate cross-account role access and permissions.

**Response**:
```json
{
  "accountId": "123456789012",
  "validationStatus": "SUCCESS",
  "permissions": {
    "drs:DescribeSourceServers": true,
    "drs:StartRecovery": true,
    "ec2:DescribeInstances": true,
    "ec2:RunInstances": true
  },
  "validatedAt": 1703875200,
  "message": "All required permissions are available"
}
```

---

## Configuration Management API

Handles configuration export/import and health monitoring.

### Export Configuration

**Endpoint**: `GET /config/export`

**Purpose**: Export all Protection Groups and Recovery Plans as JSON/YAML.

**Query Parameters**:
- `includeExecutions` (boolean) - Include execution history (default: false)
- `accountId` (string) - Export only resources for specific account
- `format` (string) - Export format: json, yaml (default: json)

**Response**:
```json
{
  "exportMetadata": {
    "exportedAt": 1703875200,
    "version": "1.0",
    "totalProtectionGroups": 5,
    "totalRecoveryPlans": 3,
    "totalExecutions": 25
  },
  "protectionGroups": [...],
  "recoveryPlans": [...],
  "executions": [...]
}
```

### Import Configuration

**Endpoint**: `POST /config/import`

**Purpose**: Import Protection Groups and Recovery Plans from JSON/YAML.

**Request Body**:
```json
{
  "importData": {
    "protectionGroups": [...],
    "recoveryPlans": [...]
  },
  "options": {
    "overwriteExisting": false,
    "validateOnly": false,
    "skipConflicts": true
  }
}
```

### Health Check

**Endpoint**: `GET /health`

**Purpose**: Service health check endpoint (no authentication required).

**Response**:
```json
{
  "status": "healthy",
  "service": "drs-orchestration-api",
  "version": "1.0",
  "timestamp": 1703875200,
  "dependencies": {
    "dynamodb": "healthy",
    "stepfunctions": "healthy",
    "drs": "healthy"
  }
}
```

---

## Status Values Reference

### Execution Status Values

| Status | Description |
|--------|-------------|
| `PENDING` | Execution queued, not yet started |
| `POLLING` | Checking for existing recovery instances |
| `INITIATED` | Step Functions execution started |
| `LAUNCHING` | DRS recovery jobs in progress |
| `STARTED` | First wave launched successfully |
| `IN_PROGRESS` | Multiple waves executing |
| `RUNNING` | All waves launched, monitoring completion |
| `PAUSED` | Execution paused between waves |
| `COMPLETED` | All waves completed successfully |
| `PARTIAL` | Some waves completed, others failed |
| `FAILED` | Execution failed |
| `CANCELLED` | Execution cancelled by user |

### DRS Replication States

| State | Description | Ready for Recovery |
|-------|-------------|-------------------|
| `CONTINUOUS` | Continuous replication active | ✅ Yes |
| `INITIAL_SYNC` | Initial data sync in progress | ✅ Yes |
| `RESCAN` | Rescanning disks | ✅ Yes |
| `BACKLOG` | Replication has backlog | ⚠️ Caution |
| `CREATING_SNAPSHOT` | Creating recovery snapshot | ⚠️ Caution |
| `PAUSED` | Replication paused | ❌ No |
| `STALLED` | Replication stalled | ❌ No |
| `DISCONNECTED` | Agent disconnected | ❌ No |
| `STOPPED` | Replication stopped | ❌ No |

### DRS Lifecycle States

| State | Description |
|-------|-------------|
| `READY_FOR_LAUNCH` | Server ready for recovery |
| `PENDING_INSTALLATION` | DRS agent installation pending |
| `INSTALLATION_IN_PROGRESS` | Installing DRS agent |
| `INSTALLATION_ERROR` | Agent installation failed |
| `AGENT_NOT_SEEN` | Agent not communicating |
| `FAILBACK_IN_PROGRESS` | Failback operation in progress |
| `FAILBACK_READY_FOR_LAUNCH` | Ready for failback launch |
| `FAILBACK_COMPLETED` | Failback completed |

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "ValidationException",
  "message": "Invalid protection group ID format",
  "details": {
    "field": "groupId",
    "provided": "invalid-id",
    "expected": "UUID format: pg-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  },
  "timestamp": 1703875200,
  "requestId": "12345678-1234-1234-1234-123456789012"
}
```

### Common HTTP Status Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid request parameters or body |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Insufficient permissions for operation |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., server already in use) |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | AWS service unavailable |
| 503 | Service Unavailable | Service temporarily unavailable |

### Error Categories

#### Validation Errors (400)
- Invalid UUID format
- Missing required fields
- Invalid enum values
- Circular dependencies in recovery plans

#### Authentication Errors (401)
- Missing Authorization header
- Invalid or expired JWT token
- Token signature verification failed

#### Permission Errors (403)
- Insufficient IAM permissions
- Cross-account role assumption failed
- DRS service not initialized

#### Resource Errors (404)
- Protection group not found
- Recovery plan not found
- Execution not found
- DRS source server not found

#### Conflict Errors (409)
- Server already assigned to another protection group
- Active execution prevents plan deletion
- Version mismatch (optimistic locking)

#### Service Errors (502/503)
- AWS DRS service unavailable
- DynamoDB throttling
- Step Functions execution limit reached

---

## Rate Limits and Best Practices

### API Rate Limits

| Endpoint Category | Rate Limit | Burst Limit |
|------------------|------------|-------------|
| Protection Groups | 10 req/sec | 20 req |
| Recovery Plans | 10 req/sec | 20 req |
| Executions | 5 req/sec | 10 req |
| DRS Integration | 5 req/sec | 10 req |
| Configuration | 2 req/sec | 5 req |

### Best Practices

#### 1. Authentication
- Cache JWT tokens and refresh before expiration
- Implement token refresh logic for long-running applications
- Use service accounts for automated systems

#### 2. Error Handling
- Implement exponential backoff for rate limit errors (429)
- Retry transient errors (502, 503) with jitter
- Log error details for debugging

#### 3. Pagination
- Use appropriate page sizes for list operations
- Implement cursor-based pagination for large datasets
- Cache results when appropriate

#### 4. Performance
- Use specific filters to reduce response sizes
- Batch operations when possible
- Monitor API response times

#### 5. Security
- Never log authentication tokens
- Use HTTPS for all API calls
- Validate all input parameters

#### 6. Monitoring
- Track API usage and error rates
- Set up alerts for high error rates
- Monitor execution success rates

---

## SDK Examples

### Python SDK Example

```python
import requests
import json
from typing import Dict, List, Optional

class DRSOrchestrationClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_protection_group(self, group_data: Dict) -> Dict:
        """Create a new protection group"""
        response = requests.post(
            f"{self.base_url}/protection-groups",
            headers=self.headers,
            json=group_data
        )
        response.raise_for_status()
        return response.json()
    
    def list_protection_groups(self, filters: Optional[Dict] = None) -> List[Dict]:
        """List protection groups with optional filters"""
        params = filters or {}
        response = requests.get(
            f"{self.base_url}/protection-groups",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()['protectionGroups']
    
    def execute_recovery_plan(self, plan_id: str, execution_type: str = 'DRILL') -> Dict:
        """Execute a recovery plan"""
        response = requests.post(
            f"{self.base_url}/recovery-plans/{plan_id}/execute",
            headers=self.headers,
            json={'ExecutionType': execution_type}
        )
        response.raise_for_status()
        return response.json()
    
    def monitor_execution(self, execution_id: str) -> Dict:
        """Get detailed execution status"""
        response = requests.get(
            f"{self.base_url}/executions/{execution_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def discover_drs_servers(self, region: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Discover DRS source servers in a region"""
        params = {'region': region}
        if filters:
            params.update(filters)
        
        response = requests.get(
            f"{self.base_url}/drs/source-servers",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()['sourceServers']

# Usage example
client = DRSOrchestrationClient(
    base_url='https://api-id.execute-api.us-east-1.amazonaws.com/prod',
    token='your-jwt-token'
)

# Create protection group
pg_data = {
    'GroupName': 'Web-Servers',
    'Region': 'us-east-1',
    'ServerSelectionTags': {'Tier': 'Web', 'Environment': 'Prod'}
}
protection_group = client.create_protection_group(pg_data)

# Execute recovery plan
execution = client.execute_recovery_plan(
    plan_id='rp-12345678-1234-1234-1234-123456789012',
    execution_type='DRILL'
)

# Monitor execution
status = client.monitor_execution(execution['executionId'])
print(f"Execution status: {status['Status']}")
```

### JavaScript/Node.js SDK Example

```javascript
class DRSOrchestrationClient {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    async createProtectionGroup(groupData) {
        const response = await fetch(`${this.baseUrl}/protection-groups`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify(groupData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        return response.json();
    }

    async executeRecoveryPlan(planId, executionType = 'DRILL') {
        const response = await fetch(`${this.baseUrl}/recovery-plans/${planId}/execute`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ ExecutionType: executionType })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        return response.json();
    }

    async monitorExecution(executionId) {
        const response = await fetch(`${this.baseUrl}/executions/${executionId}`, {
            headers: this.headers
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
        }
        
        return response.json();
    }
}

// Usage
const client = new DRSOrchestrationClient(
    'https://api-id.execute-api.us-east-1.amazonaws.com/prod',
    'your-jwt-token'
);

// Execute and monitor drill
async function runDrill() {
    try {
        const execution = await client.executeRecoveryPlan(
            'rp-12345678-1234-1234-1234-123456789012',
            'DRILL'
        );
        
        console.log(`Drill started: ${execution.executionId}`);
        
        // Poll for completion
        let status;
        do {
            await new Promise(resolve => setTimeout(resolve, 30000)); // Wait 30s
            status = await client.monitorExecution(execution.executionId);
            console.log(`Status: ${status.Status}, Wave: ${status.CurrentWave}/${status.TotalWaves}`);
        } while (['PENDING', 'IN_PROGRESS', 'PAUSED'].includes(status.Status));
        
        console.log(`Drill completed with status: ${status.Status}`);
    } catch (error) {
        console.error('Drill failed:', error.message);
    }
}
```

---

## Related Resources

- [AWS DRS Orchestration User Guide](../README.md)
- [Deployment and Operations Guide](DEPLOYMENT_AND_OPERATIONS_GUIDE.md)
- [AWS DRS Service Documentation](https://docs.aws.amazon.com/drs/latest/userguide/)
- [AWS DRS Service API Reference](https://docs.aws.amazon.com/drs/latest/APIReference/)
- [CloudScape Design System](https://cloudscape.design/)
- [AWS Step Functions Documentation](https://docs.aws.amazon.com/step-functions/)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 2024 | Initial comprehensive API reference |
