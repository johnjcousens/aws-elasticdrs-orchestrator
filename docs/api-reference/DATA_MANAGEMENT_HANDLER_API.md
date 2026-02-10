# Data Management Handler API Reference

## Overview

The Data Management Handler provides CRUD operations for Protection Groups, Recovery Plans, Target Accounts, and configuration management for the AWS DRS Orchestration Platform. It supports both API Gateway invocations (for frontend/CLI) and direct Lambda invocations (for automation/IaC workflows).

### Key Features

- **Dual Invocation Support**: API Gateway REST endpoints and direct Lambda invocation
- **Protection Group Management**: Tag-based or explicit server selection with per-server launch configs
- **Recovery Plan Management**: Multi-wave orchestration with dependencies and pause gates
- **Target Account Management**: Cross-account DR with staging account support
- **Tag Synchronization**: Automated EC2-to-DRS tag sync across regions
- **Configuration Import/Export**: Backup and migration of DR configurations
- **Validation & Conflict Detection**: Prevents server conflicts and validates replication states

### Invocation Modes

#### 1. API Gateway Mode (Frontend/CLI)
```bash
curl -X POST "https://api.example.com/protection-groups" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Production Servers", "region": "us-east-1", ...}'
```

#### 2. Direct Lambda Invocation (Automation)
```bash
aws lambda invoke \
  --function-name data-management-handler \
  --payload '{"operation": "create_protection_group", "body": {...}}' \
  response.json
```

#### 3. Python boto3 (Programmatic)
```python
import boto3
import json

lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName='data-management-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "create_protection_group",
        "body": {
            "name": "Production Servers",
            "region": "us-east-1",
            ...
        }
    })
)
result = json.loads(response['Payload'].read())
```

## Authentication & Authorization

### API Gateway Mode
- **Authentication**: Cognito User Pool JWT tokens
- **Authorization**: RBAC permissions from user attributes
- **Header**: `Authorization: Bearer <jwt-token>`

### Direct Lambda Invocation Mode
- **Authentication**: IAM principal validation
- **Authorization**: Lambda resource-based policy
- **Required IAM Permission**: `lambda:InvokeFunction` on data-management-handler function

### Required IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:*:*:function:aws-drs-orchestration-data-management-handler-*"
    }
  ]
}
```


## Operations

### Protection Group Management

#### create_protection_group

Create a new Protection Group with tag-based or explicit server selection.

**Operation**: `create_protection_group`

**Parameters**:
- `name` (required): Unique Protection Group name
- `description` (optional): Description of the Protection Group
- `region` (required): AWS region (e.g., "us-east-1")
- `accountId` (optional): Target account ID for cross-account DR
- `serverSelectionMode` (required): "tags" or "explicit"
- `serverSelectionTags` (required if mode=tags): Tag filters for dynamic server selection
- `sourceServerIds` (required if mode=explicit): Array of DRS source server IDs
- `launchConfiguration` (optional): Default launch config for all servers
- `servers` (optional): Per-server launch configuration overrides

**Request Format (Tag-Based Selection)**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "name": "Production Web Servers",
    "description": "All production web tier servers",
    "region": "us-east-1",
    "accountId": "123456789012",
    "serverSelectionMode": "tags",
    "serverSelectionTags": {
      "Environment": "production",
      "Tier": "web"
    },
    "launchConfiguration": {
      "targetInstanceTypeRightSizingMethod": "BASIC",
      "copyPrivateIp": false,
      "copyTags": true,
      "launchDisposition": "STARTED",
      "licensing": {
        "osByol": false
      }
    }
  }
}
```

**Request Format (Explicit Selection with Per-Server Configs)**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "name": "Critical Database Servers",
    "description": "Production database tier",
    "region": "us-east-1",
    "serverSelectionMode": "explicit",
    "sourceServerIds": [
      "s-1234567890abcdef0",
      "s-abcdef1234567890"
    ],
    "launchConfiguration": {
      "targetInstanceTypeRightSizingMethod": "BASIC",
      "copyPrivateIp": false
    },
    "servers": [
      {
        "serverId": "s-1234567890abcdef0",
        "useGroupDefaults": false,
        "launchConfiguration": {
          "ec2LaunchTemplateID": "lt-0123456789abcdef0",
          "targetInstanceTypeRightSizingMethod": "CUSTOM",
          "instanceType": "r6i.2xlarge",
          "subnetId": "subnet-abc123",
          "securityGroupIds": ["sg-xyz789"],
          "iamInstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/DB-Role"
        }
      }
    ]
  }
}
```

**Response Format**:
```json
{
  "groupId": "pg-abc123def456",
  "name": "Production Web Servers",
  "description": "All production web tier servers",
  "region": "us-east-1",
  "accountId": "123456789012",
  "accountName": "Production Account",
  "serverSelectionMode": "tags",
  "serverSelectionTags": {
    "Environment": "production",
    "Tier": "web"
  },
  "sourceServerIds": [
    "s-1234567890abcdef0",
    "s-abcdef1234567890",
    "s-fedcba0987654321"
  ],
  "serverCount": 3,
  "launchConfiguration": {
    "targetInstanceTypeRightSizingMethod": "BASIC",
    "copyPrivateIp": false,
    "copyTags": true,
    "launchDisposition": "STARTED"
  },
  "createdAt": "2026-01-31T12:00:00Z",
  "updatedAt": "2026-01-31T12:00:00Z",
  "version": 1
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "create_protection_group",
    "body": {
      "name": "Production Web Servers",
      "region": "us-east-1",
      "serverSelectionMode": "tags",
      "serverSelectionTags": {
        "Environment": "production",
        "Tier": "web"
      }
    }
  }' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-data-management-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "create_protection_group",
        "body": {
            "name": "Production Web Servers",
            "region": "us-east-1",
            "serverSelectionMode": "tags",
            "serverSelectionTags": {
                "Environment": "production",
                "Tier": "web"
            }
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Created Protection Group: {result['groupId']}")
print(f"Server Count: {result['serverCount']}")
```

**Error Responses**:
- `MISSING_PARAMETER`: Required field missing (name, region, serverSelectionMode)
- `INVALID_PARAMETER`: Invalid region, invalid server selection mode
- `ALREADY_EXISTS`: Protection Group name already exists (case-insensitive)
- `SERVER_CONFLICT`: Servers already assigned to another Protection Group
- `INVALID_REPLICATION_STATE`: Servers not ready for recovery (disconnected, stopped, stalled)
- `DRS_ERROR`: Failed to query DRS source servers
- `DYNAMODB_ERROR`: Failed to create Protection Group record

---

#### update_protection_group

Update an existing Protection Group with optimistic locking.

**Operation**: `update_protection_group`

**Parameters**:
- `groupId` (required): Protection Group ID
- `name` (optional): New name
- `description` (optional): New description
- `serverSelectionTags` (optional): Updated tag filters (for tag-based groups)
- `sourceServerIds` (optional): Updated server list (for explicit groups)
- `launchConfiguration` (optional): Updated default launch config
- `servers` (optional): Updated per-server configurations
- `version` (required): Current version for optimistic locking

**Request Format**:
```json
{
  "operation": "update_protection_group",
  "body": {
    "groupId": "pg-abc123def456",
    "description": "Updated description",
    "launchConfiguration": {
      "targetInstanceTypeRightSizingMethod": "CUSTOM",
      "copyPrivateIp": true
    },
    "version": 1
  }
}
```

**Response Format**:
```json
{
  "groupId": "pg-abc123def456",
  "name": "Production Web Servers",
  "description": "Updated description",
  "region": "us-east-1",
  "serverCount": 3,
  "updatedAt": "2026-01-31T13:00:00Z",
  "version": 2
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "update_protection_group",
    "body": {
      "groupId": "pg-abc123def456",
      "description": "Updated description",
      "version": 1
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Protection Group not found
- `VERSION_MISMATCH`: Optimistic locking conflict (version mismatch)
- `ACTIVE_EXECUTION`: Cannot update while execution in progress
- `SERVER_CONFLICT`: New servers already assigned to another group

---

#### delete_protection_group

Delete a Protection Group. Blocked if used in any Recovery Plan.

**Operation**: `delete_protection_group`

**Parameters**:
- `groupId` (required): Protection Group ID to delete

**Request Format**:
```json
{
  "operation": "delete_protection_group",
  "body": {
    "groupId": "pg-abc123def456"
  }
}
```

**Response Format**:
```json
{
  "message": "Protection Group deleted successfully",
  "groupId": "pg-abc123def456"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "delete_protection_group",
    "body": {
      "groupId": "pg-abc123def456"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Protection Group not found
- `IN_USE`: Protection Group is referenced by one or more Recovery Plans
- `DYNAMODB_ERROR`: Failed to delete Protection Group

---

### Server Launch Configuration Management

#### update_server_launch_config

Update per-server launch configuration within a Protection Group.

**Operation**: `update_server_launch_config`

**Parameters**:
- `groupId` (required): Protection Group ID
- `serverId` (required): DRS source server ID
- `useGroupDefaults` (optional): If true, remove custom config and use group defaults
- `launchConfiguration` (required if useGroupDefaults=false): Custom launch config

**Request Format**:
```json
{
  "operation": "update_server_launch_config",
  "body": {
    "groupId": "pg-abc123def456",
    "serverId": "s-1234567890abcdef0",
    "useGroupDefaults": false,
    "launchConfiguration": {
      "targetInstanceTypeRightSizingMethod": "CUSTOM",
      "instanceType": "c6a.xlarge",
      "subnetId": "subnet-abc123",
      "securityGroupIds": ["sg-xyz789"],
      "iamInstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/WebServer-Role",
      "copyPrivateIp": false,
      "copyTags": true
    }
  }
}
```

**Response Format**:
```json
{
  "message": "Server launch configuration updated successfully",
  "groupId": "pg-abc123def456",
  "serverId": "s-1234567890abcdef0",
  "useGroupDefaults": false,
  "launchConfiguration": {
    "targetInstanceTypeRightSizingMethod": "CUSTOM",
    "instanceType": "c6a.xlarge",
    "subnetId": "subnet-abc123",
    "securityGroupIds": ["sg-xyz789"],
    "iamInstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/WebServer-Role"
  },
  "effectiveConfiguration": {
    "targetInstanceTypeRightSizingMethod": "CUSTOM",
    "instanceType": "c6a.xlarge",
    "subnetId": "subnet-abc123",
    "securityGroupIds": ["sg-xyz789"],
    "iamInstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/WebServer-Role",
    "copyPrivateIp": false,
    "copyTags": true,
    "launchDisposition": "STARTED"
  }
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "update_server_launch_config",
    "body": {
      "groupId": "pg-abc123def456",
      "serverId": "s-1234567890abcdef0",
      "launchConfiguration": {
        "instanceType": "c6a.xlarge",
        "subnetId": "subnet-abc123"
      }
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Protection Group or server not found
- `INVALID_PARAMETER`: Invalid instance type, subnet, or security group
- `ACTIVE_EXECUTION`: Cannot update while execution in progress

---

#### delete_server_launch_config

Delete per-server launch configuration and revert to group defaults.

**Operation**: `delete_server_launch_config`

**Parameters**:
- `groupId` (required): Protection Group ID
- `serverId` (required): DRS source server ID

**Request Format**:
```json
{
  "operation": "delete_server_launch_config",
  "body": {
    "groupId": "pg-abc123def456",
    "serverId": "s-1234567890abcdef0"
  }
}
```

**Response Format**:
```json
{
  "message": "Server launch configuration deleted successfully. Server will now use group defaults.",
  "groupId": "pg-abc123def456",
  "serverId": "s-1234567890abcdef0",
  "useGroupDefaults": true
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "delete_server_launch_config",
    "body": {
      "groupId": "pg-abc123def456",
      "serverId": "s-1234567890abcdef0"
    }
  }' \
  response.json && cat response.json | jq .
```

---

#### bulk_update_server_configs

Bulk update launch configurations for multiple servers.

**Operation**: `bulk_update_server_configs`

**Parameters**:
- `groupId` (required): Protection Group ID
- `servers` (required): Array of server configurations

**Request Format**:
```json
{
  "operation": "bulk_update_server_configs",
  "body": {
    "groupId": "pg-abc123def456",
    "servers": [
      {
        "serverId": "s-1234567890abcdef0",
        "useGroupDefaults": false,
        "launchConfiguration": {
          "instanceType": "c6a.xlarge",
          "subnetId": "subnet-abc123"
        }
      },
      {
        "serverId": "s-abcdef1234567890",
        "useGroupDefaults": true
      }
    ]
  }
}
```

**Response Format**:
```json
{
  "message": "Bulk update completed",
  "groupId": "pg-abc123def456",
  "totalServers": 2,
  "successCount": 2,
  "failureCount": 0,
  "results": [
    {
      "serverId": "s-1234567890abcdef0",
      "status": "success"
    },
    {
      "serverId": "s-abcdef1234567890",
      "status": "success"
    }
  ]
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "bulk_update_server_configs",
    "body": {
      "groupId": "pg-abc123def456",
      "servers": [
        {
          "serverId": "s-1234567890abcdef0",
          "launchConfiguration": {"instanceType": "c6a.xlarge"}
        }
      ]
    }
  }' \
  response.json && cat response.json | jq .
```

---

#### validate_static_ip

Validate static private IP address for a server.

**Operation**: `validate_static_ip`

**Parameters**:
- `groupId` (required): Protection Group ID
- `serverId` (required): DRS source server ID
- `staticIp` (required): Static IP address to validate
- `subnetId` (required): Target subnet ID

**Request Format**:
```json
{
  "operation": "validate_static_ip",
  "body": {
    "groupId": "pg-abc123def456",
    "serverId": "s-1234567890abcdef0",
    "staticIp": "10.0.1.100",
    "subnetId": "subnet-abc123"
  }
}
```

**Response Format**:
```json
{
  "valid": true,
  "staticIp": "10.0.1.100",
  "subnetId": "subnet-abc123",
  "subnetCidr": "10.0.1.0/24",
  "message": "IP address is valid and available in subnet"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "validate_static_ip",
    "body": {
      "groupId": "pg-abc123def456",
      "serverId": "s-1234567890abcdef0",
      "staticIp": "10.0.1.100",
      "subnetId": "subnet-abc123"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `INVALID_PARAMETER`: IP not in subnet CIDR range
- `IP_IN_USE`: IP address already in use
- `SUBNET_NOT_FOUND`: Subnet does not exist

---

### Recovery Plan Management

#### create_recovery_plan

Create a new Recovery Plan with multi-wave configuration.

**Operation**: `create_recovery_plan`

**Parameters**:
- `name` (required): Unique Recovery Plan name
- `description` (optional): Description of the Recovery Plan
- `waves` (required): Array of wave configurations

**Request Format**:
```json
{
  "operation": "create_recovery_plan",
  "body": {
    "name": "Production DR Plan",
    "description": "Multi-tier production disaster recovery",
    "waves": [
      {
        "waveNumber": 1,
        "name": "Database Tier",
        "protectionGroupId": "pg-database123",
        "launchOrder": 1,
        "pauseBeforeWave": false
      },
      {
        "waveNumber": 2,
        "name": "Application Tier",
        "protectionGroupId": "pg-app456",
        "launchOrder": 2,
        "pauseBeforeWave": true,
        "dependsOnWaves": [1]
      },
      {
        "waveNumber": 3,
        "name": "Web Tier",
        "protectionGroupId": "pg-web789",
        "launchOrder": 3,
        "pauseBeforeWave": false,
        "dependsOnWaves": [2]
      }
    ]
  }
}
```

**Response Format**:
```json
{
  "planId": "plan-xyz789abc",
  "name": "Production DR Plan",
  "description": "Multi-tier production disaster recovery",
  "waves": [
    {
      "waveNumber": 1,
      "name": "Database Tier",
      "protectionGroupId": "pg-database123",
      "protectionGroupName": "Production Databases",
      "serverCount": 5,
      "launchOrder": 1,
      "pauseBeforeWave": false
    },
    {
      "waveNumber": 2,
      "name": "Application Tier",
      "protectionGroupId": "pg-app456",
      "protectionGroupName": "Application Servers",
      "serverCount": 10,
      "launchOrder": 2,
      "pauseBeforeWave": true,
      "dependsOnWaves": [1]
    },
    {
      "waveNumber": 3,
      "name": "Web Tier",
      "protectionGroupId": "pg-web789",
      "protectionGroupName": "Web Servers",
      "serverCount": 8,
      "launchOrder": 3,
      "pauseBeforeWave": false,
      "dependsOnWaves": [2]
    }
  ],
  "totalWaves": 3,
  "totalServers": 23,
  "createdAt": "2026-01-31T12:00:00Z",
  "updatedAt": "2026-01-31T12:00:00Z",
  "version": 1
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "create_recovery_plan",
    "body": {
      "name": "Production DR Plan",
      "waves": [
        {
          "waveNumber": 1,
          "name": "Database Tier",
          "protectionGroupId": "pg-database123",
          "launchOrder": 1
        }
      ]
    }
  }' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-data-management-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "create_recovery_plan",
        "body": {
            "name": "Production DR Plan",
            "description": "Multi-tier production disaster recovery",
            "waves": [
                {
                    "waveNumber": 1,
                    "name": "Database Tier",
                    "protectionGroupId": "pg-database123",
                    "launchOrder": 1,
                    "pauseBeforeWave": False
                },
                {
                    "waveNumber": 2,
                    "name": "Application Tier",
                    "protectionGroupId": "pg-app456",
                    "launchOrder": 2,
                    "pauseBeforeWave": True,
                    "dependsOnWaves": [1]
                }
            ]
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Created Recovery Plan: {result['planId']}")
print(f"Total Waves: {result['totalWaves']}")
print(f"Total Servers: {result['totalServers']}")
```

**Error Responses**:
- `MISSING_PARAMETER`: Required field missing (name, waves)
- `INVALID_PARAMETER`: Invalid wave configuration, circular dependencies
- `ALREADY_EXISTS`: Recovery Plan name already exists (case-insensitive)
- `WAVE_SIZE_EXCEEDED`: Wave exceeds 100 servers (DRS limit)
- `PROTECTION_GROUP_NOT_FOUND`: Referenced Protection Group does not exist
- `DYNAMODB_ERROR`: Failed to create Recovery Plan record

---

#### update_recovery_plan

Update an existing Recovery Plan with optimistic locking.

**Operation**: `update_recovery_plan`

**Parameters**:
- `planId` (required): Recovery Plan ID
- `name` (optional): New name
- `description` (optional): New description
- `waves` (optional): Updated wave configuration
- `version` (required): Current version for optimistic locking

**Request Format**:
```json
{
  "operation": "update_recovery_plan",
  "body": {
    "planId": "plan-xyz789abc",
    "description": "Updated description",
    "waves": [
      {
        "waveNumber": 1,
        "name": "Database Tier - Updated",
        "protectionGroupId": "pg-database123",
        "launchOrder": 1,
        "pauseBeforeWave": true
      }
    ],
    "version": 1
  }
}
```

**Response Format**:
```json
{
  "planId": "plan-xyz789abc",
  "name": "Production DR Plan",
  "description": "Updated description",
  "waves": [
    {
      "waveNumber": 1,
      "name": "Database Tier - Updated",
      "protectionGroupId": "pg-database123",
      "serverCount": 5,
      "launchOrder": 1,
      "pauseBeforeWave": true
    }
  ],
  "totalWaves": 1,
  "totalServers": 5,
  "updatedAt": "2026-01-31T13:00:00Z",
  "version": 2
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "update_recovery_plan",
    "body": {
      "planId": "plan-xyz789abc",
      "description": "Updated description",
      "version": 1
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Recovery Plan not found
- `VERSION_MISMATCH`: Optimistic locking conflict (version mismatch)
- `ACTIVE_EXECUTION`: Cannot update while execution in progress
- `INVALID_PARAMETER`: Invalid wave configuration

---

#### delete_recovery_plan

Delete a Recovery Plan. Blocked if any active execution exists.

**Operation**: `delete_recovery_plan`

**Parameters**:
- `planId` (required): Recovery Plan ID to delete

**Request Format**:
```json
{
  "operation": "delete_recovery_plan",
  "body": {
    "planId": "plan-xyz789abc"
  }
}
```

**Response Format**:
```json
{
  "message": "Recovery Plan deleted successfully",
  "planId": "plan-xyz789abc"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "delete_recovery_plan",
    "body": {
      "planId": "plan-xyz789abc"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Recovery Plan not found
- `ACTIVE_EXECUTION`: Cannot delete while execution in progress
- `DYNAMODB_ERROR`: Failed to delete Recovery Plan

---

### Target Account Management

#### add_target_account

Register a new target account for cross-account DR operations.

**Operation**: `add_target_account`

**Parameters**:
- `accountId` (required): 12-digit AWS account ID
- `accountName` (required): Friendly name for the account
- `assumeRoleName` (required): IAM role name to assume
- `externalId` (optional): External ID for role assumption
- `regions` (optional): Array of enabled regions

**Request Format**:
```json
{
  "operation": "add_target_account",
  "body": {
    "accountId": "123456789012",
    "accountName": "Production Account",
    "assumeRoleName": "DRSOrchestrationCrossAccountRole",
    "externalId": "unique-external-id-123",
    "regions": ["us-east-1", "us-west-2"]
  }
}
```

**Response Format**:
```json
{
  "accountId": "123456789012",
  "accountName": "Production Account",
  "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole",
  "assumeRoleName": "DRSOrchestrationCrossAccountRole",
  "externalId": "unique-external-id-123",
  "regions": ["us-east-1", "us-west-2"],
  "status": "ACTIVE",
  "createdAt": "2026-01-31T12:00:00Z",
  "updatedAt": "2026-01-31T12:00:00Z"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "add_target_account",
    "body": {
      "accountId": "123456789012",
      "accountName": "Production Account",
      "assumeRoleName": "DRSOrchestrationCrossAccountRole",
      "externalId": "unique-external-id-123"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `MISSING_PARAMETER`: Required field missing (accountId, accountName, assumeRoleName)
- `INVALID_PARAMETER`: Invalid account ID format (must be 12 digits)
- `ALREADY_EXISTS`: Target account already registered
- `ROLE_ASSUMPTION_FAILED`: Cannot assume role in target account
- `DYNAMODB_ERROR`: Failed to create target account record

---

#### update_target_account

Update target account configuration.

**Operation**: `update_target_account`

**Parameters**:
- `accountId` (required): Target account ID
- `accountName` (optional): New account name
- `assumeRoleName` (optional): New role name
- `externalId` (optional): New external ID
- `regions` (optional): Updated regions list

**Request Format**:
```json
{
  "operation": "update_target_account",
  "body": {
    "accountId": "123456789012",
    "accountName": "Production Account - Updated",
    "regions": ["us-east-1", "us-west-2", "eu-west-1"]
  }
}
```

**Response Format**:
```json
{
  "accountId": "123456789012",
  "accountName": "Production Account - Updated",
  "regions": ["us-east-1", "us-west-2", "eu-west-1"],
  "updatedAt": "2026-01-31T13:00:00Z"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "update_target_account",
    "body": {
      "accountId": "123456789012",
      "accountName": "Production Account - Updated"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Target account not found
- `INVALID_PARAMETER`: Invalid parameter value
- `DYNAMODB_ERROR`: Failed to update target account

---

#### delete_target_account

Delete target account configuration.

**Operation**: `delete_target_account`

**Parameters**:
- `accountId` (required): Target account ID to delete

**Request Format**:
```json
{
  "operation": "delete_target_account",
  "body": {
    "accountId": "123456789012"
  }
}
```

**Response Format**:
```json
{
  "message": "Target account deleted successfully",
  "accountId": "123456789012"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "delete_target_account",
    "body": {
      "accountId": "123456789012"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Target account not found
- `IN_USE`: Target account is referenced by Protection Groups
- `DYNAMODB_ERROR`: Failed to delete target account

---

### Staging Account Management

#### add_staging_account

Add staging account to target account configuration.

**Operation**: `add_staging_account`

**Parameters**:
- `targetAccountId` (required): Target account ID
- `stagingAccountId` (required): Staging account ID to add
- `stagingAccountName` (required): Friendly name for staging account
- `assumeRoleName` (required): IAM role name in staging account
- `externalId` (optional): External ID for role assumption

**Request Format**:
```json
{
  "operation": "add_staging_account",
  "body": {
    "targetAccountId": "123456789012",
    "stagingAccountId": "987654321098",
    "stagingAccountName": "Staging Account 1",
    "assumeRoleName": "DRSOrchestrationRole",
    "externalId": "staging-external-id"
  }
}
```

**Response Format**:
```json
{
  "message": "Staging account added successfully",
  "targetAccountId": "123456789012",
  "stagingAccount": {
    "accountId": "987654321098",
    "accountName": "Staging Account 1",
    "roleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationRole",
    "externalId": "staging-external-id",
    "status": "active"
  }
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "add_staging_account",
    "body": {
      "targetAccountId": "123456789012",
      "stagingAccountId": "987654321098",
      "stagingAccountName": "Staging Account 1",
      "assumeRoleName": "DRSOrchestrationRole"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Target account not found
- `ALREADY_EXISTS`: Staging account already added
- `ROLE_ASSUMPTION_FAILED`: Cannot assume role in staging account
- `DYNAMODB_ERROR`: Failed to add staging account

---

#### remove_staging_account

Remove staging account from target account configuration.

**Operation**: `remove_staging_account`

**Parameters**:
- `targetAccountId` (required): Target account ID
- `stagingAccountId` (required): Staging account ID to remove

**Request Format**:
```json
{
  "operation": "remove_staging_account",
  "body": {
    "targetAccountId": "123456789012",
    "stagingAccountId": "987654321098"
  }
}
```

**Response Format**:
```json
{
  "message": "Staging account removed successfully",
  "targetAccountId": "123456789012",
  "stagingAccountId": "987654321098"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "remove_staging_account",
    "body": {
      "targetAccountId": "123456789012",
      "stagingAccountId": "987654321098"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Target account or staging account not found
- `DYNAMODB_ERROR`: Failed to remove staging account

---

#### sync_extended_source_servers

Synchronize extended source servers from staging accounts.

**Operation**: `sync_extended_source_servers`

**Parameters**:
- `targetAccountId` (required): Target account ID to sync

**Request Format**:
```json
{
  "operation": "sync_extended_source_servers",
  "body": {
    "targetAccountId": "123456789012"
  }
}
```

**Response Format**:
```json
{
  "message": "Extended source servers synchronized successfully",
  "targetAccountId": "123456789012",
  "stagingAccountsProcessed": 2,
  "serversFound": 45,
  "syncedAt": "2026-01-31T12:00:00Z"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "sync_extended_source_servers",
    "body": {
      "targetAccountId": "123456789012"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `NOT_FOUND`: Target account not found
- `NO_STAGING_ACCOUNTS`: No staging accounts configured
- `SYNC_FAILED`: Failed to sync from one or more staging accounts

---

### Tag Synchronization

#### trigger_tag_sync

Trigger EC2-to-DRS tag synchronization across all regions.

**Operation**: `trigger_tag_sync`

**Parameters**:
- `synch_tags` (optional): Sync EC2 tags to DRS (default: true)
- `synch_instance_type` (optional): Sync instance type recommendations (default: false)

**Request Format**:
```json
{
  "operation": "trigger_tag_sync",
  "body": {
    "synch_tags": true,
    "synch_instance_type": false
  }
}
```

**Response Format**:
```json
{
  "message": "Tag synchronization completed successfully",
  "regionsProcessed": 15,
  "serversProcessed": 150,
  "tagsSynchronized": 450,
  "errors": [],
  "syncedAt": "2026-01-31T12:00:00Z",
  "duration": "45.2 seconds"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "trigger_tag_sync",
    "body": {
      "synch_tags": true
    }
  }' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-data-management-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "trigger_tag_sync",
        "body": {
            "synch_tags": True,
            "synch_instance_type": False
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Regions Processed: {result['regionsProcessed']}")
print(f"Servers Processed: {result['serversProcessed']}")
print(f"Tags Synchronized: {result['tagsSynchronized']}")
print(f"Duration: {result['duration']}")
```

**Error Responses**:
- `DRS_ERROR`: Failed to sync tags in one or more regions
- `INTERNAL_ERROR`: Unexpected error during synchronization

---

#### update_tag_sync_settings

Update tag synchronization configuration settings.

**Operation**: `update_tag_sync_settings`

**Parameters**:
- `enabled` (required): Enable/disable tag sync
- `schedule` (optional): EventBridge schedule expression
- `tagFilters` (optional): Tag inclusion/exclusion filters

**Request Format**:
```json
{
  "operation": "update_tag_sync_settings",
  "body": {
    "enabled": true,
    "schedule": "rate(5 minutes)",
    "tagFilters": {
      "include": ["Environment", "Application", "Owner"],
      "exclude": ["aws:*", "Name"]
    }
  }
}
```

**Response Format**:
```json
{
  "message": "Tag sync settings updated successfully",
  "enabled": true,
  "schedule": "rate(5 minutes)",
  "tagFilters": {
    "include": ["Environment", "Application", "Owner"],
    "exclude": ["aws:*", "Name"]
  },
  "updatedAt": "2026-01-31T12:00:00Z"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "update_tag_sync_settings",
    "body": {
      "enabled": true,
      "schedule": "rate(5 minutes)"
    }
  }' \
  response.json && cat response.json | jq .
```

**Error Responses**:
- `INVALID_PARAMETER`: Invalid schedule expression
- `INTERNAL_ERROR`: Failed to update EventBridge rule

---

### Configuration Management

#### import_configuration

Import Protection Groups and Recovery Plans from JSON configuration.

**Operation**: `import_configuration`

**Parameters**:
- `manifest` (required): Configuration manifest with Protection Groups and Recovery Plans
- `dryRun` (optional): Validate without importing (default: false)
- `overwriteExisting` (optional): Overwrite existing configurations (default: false)

**Request Format**:
```json
{
  "operation": "import_configuration",
  "body": {
    "manifest": {
      "protectionGroups": [
        {
          "name": "Production Web Servers",
          "region": "us-east-1",
          "serverSelectionMode": "tags",
          "serverSelectionTags": {
            "Environment": "production",
            "Tier": "web"
          }
        }
      ],
      "recoveryPlans": [
        {
          "name": "Production DR Plan",
          "waves": [
            {
              "waveNumber": 1,
              "name": "Web Tier",
              "protectionGroupName": "Production Web Servers",
              "launchOrder": 1
            }
          ]
        }
      ]
    },
    "dryRun": false,
    "overwriteExisting": false
  }
}
```

**Response Format**:
```json
{
  "message": "Configuration imported successfully",
  "protectionGroupsCreated": 1,
  "recoveryPlansCreated": 1,
  "errors": [],
  "warnings": [],
  "importedAt": "2026-01-31T12:00:00Z"
}
```

**AWS CLI Example**:
```bash
# First, validate the manifest
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "import_configuration",
    "body": {
      "manifest": {...},
      "dryRun": true
    }
  }' \
  validation.json && cat validation.json | jq .

# Then import if validation passes
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{
    "operation": "import_configuration",
    "body": {
      "manifest": {...},
      "dryRun": false
    }
  }' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Load configuration from file
with open('drs-config-backup.json', 'r') as f:
    manifest = json.load(f)

# Validate first
response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-data-management-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "import_configuration",
        "body": {
            "manifest": manifest,
            "dryRun": True
        }
    })
)

validation_result = json.loads(response['Payload'].read())
if validation_result.get('errors'):
    print("Validation failed:")
    for error in validation_result['errors']:
        print(f"  - {error}")
else:
    print("Validation passed. Importing configuration...")
    
    # Import configuration
    response = lambda_client.invoke(
        FunctionName='aws-drs-orchestration-data-management-handler-test',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "operation": "import_configuration",
            "body": {
                "manifest": manifest,
                "dryRun": False
            }
        })
    )
    
    result = json.loads(response['Payload'].read())
    print(f"Protection Groups Created: {result['protectionGroupsCreated']}")
    print(f"Recovery Plans Created: {result['recoveryPlansCreated']}")
```

**Error Responses**:
- `INVALID_PARAMETER`: Invalid manifest format
- `VALIDATION_FAILED`: Manifest validation failed
- `ALREADY_EXISTS`: Configuration already exists (when overwriteExisting=false)
- `DYNAMODB_ERROR`: Failed to import configuration

---

## Error Codes

### Standard Error Response Format

All errors follow a consistent format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "additionalContext": "value"
  }
}
```

### Error Code Reference

| Error Code | HTTP Status | Description | Resolution |
|------------|-------------|-------------|------------|
| `INVALID_INVOCATION` | 400 | Event format is invalid | Check event structure contains required fields |
| `INVALID_OPERATION` | 400 | Operation not supported | Verify operation name is correct |
| `MISSING_PARAMETER` | 400 | Required parameter missing | Add required parameter to body |
| `INVALID_PARAMETER` | 400 | Parameter value is invalid | Check parameter format and constraints |
| `ALREADY_EXISTS` | 409 | Resource name already exists | Use unique name (case-insensitive) |
| `NOT_FOUND` | 404 | Resource not found | Verify resource ID exists |
| `IN_USE` | 409 | Resource is referenced by other resources | Remove references before deleting |
| `SERVER_CONFLICT` | 409 | Servers already assigned to another group | Remove from other group first |
| `ACTIVE_EXECUTION` | 409 | Cannot modify during active execution | Wait for execution to complete |
| `VERSION_MISMATCH` | 409 | Optimistic locking conflict | Fetch latest version and retry |
| `INVALID_REPLICATION_STATE` | 400 | Servers not ready for recovery | Check DRS replication status |
| `WAVE_SIZE_EXCEEDED` | 400 | Wave exceeds 100 servers | Split into multiple waves |
| `AUTHORIZATION_FAILED` | 403 | IAM principal not authorized | Verify IAM permissions for lambda:InvokeFunction |
| `ROLE_ASSUMPTION_FAILED` | 403 | Cannot assume cross-account role | Check IAM role trust relationship |
| `DYNAMODB_ERROR` | 500 | DynamoDB operation failed | Check DynamoDB table status and permissions |
| `DRS_ERROR` | 500 | DRS API operation failed | Check DRS service status and permissions |
| `INTERNAL_ERROR` | 500 | Unexpected error occurred | Check CloudWatch Logs for details |

### Common Error Scenarios

#### Server Already Assigned

**Error**:
```json
{
  "error": "SERVER_CONFLICT",
  "message": "1 server(s) are already assigned to other Protection Groups",
  "conflicts": [
    {
      "serverId": "s-1234567890abcdef0",
      "hostname": "web-server-01",
      "currentGroupId": "pg-existing123",
      "currentGroupName": "Existing Group"
    }
  ]
}
```

**Resolution**:
1. Remove server from existing Protection Group
2. Or use different servers
3. Retry the operation

#### Active Execution in Progress

**Error**:
```json
{
  "error": "ACTIVE_EXECUTION",
  "message": "Cannot modify Protection Group while execution is in progress",
  "executionId": "exec-abc123",
  "executionStatus": "RUNNING"
}
```

**Resolution**:
1. Wait for execution to complete
2. Or cancel the execution
3. Retry the operation

#### Version Mismatch (Optimistic Locking)

**Error**:
```json
{
  "error": "VERSION_MISMATCH",
  "message": "Version mismatch. Resource was modified by another process.",
  "currentVersion": 2,
  "providedVersion": 1
}
```

**Resolution**:
1. Fetch the latest version of the resource
2. Reapply your changes with the new version
3. Retry the operation

#### Invalid Replication State

**Error**:
```json
{
  "error": "INVALID_REPLICATION_STATE",
  "message": "2 server(s) have invalid replication states",
  "invalidServers": [
    {
      "serverId": "s-1234567890abcdef0",
      "hostname": "web-server-01",
      "replicationState": "DISCONNECTED"
    },
    {
      "serverId": "s-abcdef1234567890",
      "hostname": "web-server-02",
      "replicationState": "STALLED"
    }
  ]
}
```

**Resolution**:
1. Check DRS replication status in AWS Console
2. Resolve replication issues (network, agent, etc.)
3. Wait for servers to reach healthy state
4. Retry the operation

---

## Troubleshooting

### Enable Debug Logging

Set environment variable `DEBUG=true` on the Lambda function to enable detailed logging:

```bash
aws lambda update-function-configuration \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --environment Variables={DEBUG=true}
```

### Check CloudWatch Logs

View Lambda execution logs:

```bash
aws logs tail /aws/lambda/aws-drs-orchestration-data-management-handler-test --follow
```

### Test IAM Permissions

Verify your IAM principal can invoke the function:

```bash
aws lambda get-policy \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --query 'Policy' \
  --output text | jq .
```

### Validate Event Format

Test with a simple operation first:

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"get_tag_sync_settings"}' \
  response.json && cat response.json
```

### Cross-Account Issues

If cross-account operations fail:

1. Verify target account is registered in Target Accounts table
2. Check IAM role trust relationship allows hub account to assume role
3. Verify External ID matches (if configured)
4. Test role assumption manually:

```bash
aws sts assume-role \
  --role-arn arn:aws:iam::TARGET_ACCOUNT:role/DRSOrchestrationCrossAccountRole \
  --role-session-name test-session \
  --external-id YOUR_EXTERNAL_ID
```

### DynamoDB Optimistic Locking

If you encounter frequent version mismatches:

1. Implement retry logic with exponential backoff
2. Fetch latest version before each update
3. Consider using conditional writes for critical operations

### Tag Sync Issues

If tag synchronization fails:

1. Check DRS initialization in all regions
2. Verify IAM permissions for DRS and EC2 APIs
3. Check CloudWatch Logs for specific region failures
4. Verify EC2 instances have corresponding DRS source servers

---

## Integration Examples

### Python Script - Create Protection Group with Validation

```python
#!/usr/bin/env python3
"""
Create Protection Group with comprehensive validation.
"""
import boto3
import json
import sys

def create_protection_group(lambda_client, config):
    """Create Protection Group with validation."""
    
    # Step 1: Resolve tags to preview servers
    if config.get('serverSelectionMode') == 'tags':
        print("Resolving tag-based server selection...")
        response = lambda_client.invoke(
            FunctionName='aws-drs-orchestration-data-management-handler-test',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                "operation": "resolve_protection_group_tags",
                "body": {
                    "region": config['region'],
                    "serverSelectionTags": config['serverSelectionTags']
                }
            })
        )
        
        result = json.loads(response['Payload'].read())
        if result.get('error'):
            print(f"Error resolving tags: {result['message']}")
            return None
        
        print(f"Found {result['serverCount']} servers matching tags:")
        for server in result['servers'][:5]:  # Show first 5
            print(f"  - {server['hostname']} ({server['sourceServerID']})")
        
        if result['serverCount'] > 5:
            print(f"  ... and {result['serverCount'] - 5} more")
        
        # Confirm with user
        confirm = input("\nProceed with creating Protection Group? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return None
    
    # Step 2: Create Protection Group
    print("\nCreating Protection Group...")
    response = lambda_client.invoke(
        FunctionName='aws-drs-orchestration-data-management-handler-test',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "operation": "create_protection_group",
            "body": config
        })
    )
    
    result = json.loads(response['Payload'].read())
    if result.get('error'):
        print(f"Error creating Protection Group: {result['message']}")
        if result.get('conflicts'):
            print("\nServer conflicts:")
            for conflict in result['conflicts']:
                print(f"  - {conflict['hostname']}: already in {conflict['currentGroupName']}")
        return None
    
    print(f"\n✓ Protection Group created successfully!")
    print(f"  Group ID: {result['groupId']}")
    print(f"  Name: {result['name']}")
    print(f"  Server Count: {result['serverCount']}")
    
    return result

def main():
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Configuration
    config = {
        "name": "Production Web Servers",
        "description": "All production web tier servers",
        "region": "us-east-1",
        "serverSelectionMode": "tags",
        "serverSelectionTags": {
            "Environment": "production",
            "Tier": "web"
        },
        "launchConfiguration": {
            "targetInstanceTypeRightSizingMethod": "BASIC",
            "copyPrivateIp": False,
            "copyTags": True
        }
    }
    
    result = create_protection_group(lambda_client, config)
    if result:
        # Save group ID for later use
        with open('protection-group-id.txt', 'w') as f:
            f.write(result['groupId'])
        print(f"\nGroup ID saved to protection-group-id.txt")

if __name__ == '__main__':
    main()
```

### Bash Script - Bulk Server Configuration

```bash
#!/bin/bash
# Bulk update server launch configurations

set -euo pipefail

FUNCTION_NAME="aws-drs-orchestration-data-management-handler-test"
GROUP_ID="pg-abc123def456"

# Server configurations
cat > servers-config.json << 'EOF'
{
  "operation": "bulk_update_server_configs",
  "body": {
    "groupId": "pg-abc123def456",
    "servers": [
      {
        "serverId": "s-1234567890abcdef0",
        "useGroupDefaults": false,
        "launchConfiguration": {
          "instanceType": "c6a.xlarge",
          "subnetId": "subnet-abc123",
          "securityGroupIds": ["sg-xyz789"]
        }
      },
      {
        "serverId": "s-abcdef1234567890",
        "useGroupDefaults": false,
        "launchConfiguration": {
          "instanceType": "r6i.2xlarge",
          "subnetId": "subnet-def456",
          "securityGroupIds": ["sg-uvw012"]
        }
      }
    ]
  }
}
EOF

echo "Updating server configurations..."

aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload file://servers-config.json \
  response.json > /dev/null

# Parse results
SUCCESS_COUNT=$(jq -r '.successCount' response.json)
FAILURE_COUNT=$(jq -r '.failureCount' response.json)
TOTAL=$(jq -r '.totalServers' response.json)

echo "================================"
echo "Bulk Update Results"
echo "================================"
echo "Total Servers: $TOTAL"
echo "Successful: $SUCCESS_COUNT"
echo "Failed: $FAILURE_COUNT"
echo ""

if [ "$FAILURE_COUNT" -gt 0 ]; then
    echo "Failed servers:"
    jq -r '.results[] | select(.status == "failed") | "  - \(.serverId): \(.error)"' response.json
    exit 1
else
    echo "✓ All servers updated successfully"
    exit 0
fi
```

### Terraform Module - Protection Group Management

```hcl
# Create Protection Group using Lambda invocation
data "aws_lambda_invocation" "create_protection_group" {
  function_name = "aws-drs-orchestration-data-management-handler-test"

  input = jsonencode({
    operation = "create_protection_group"
    body = {
      name                 = "Production Web Servers"
      description          = "All production web tier servers"
      region               = "us-east-1"
      serverSelectionMode  = "tags"
      serverSelectionTags = {
        Environment = "production"
        Tier        = "web"
      }
      launchConfiguration = {
        targetInstanceTypeRightSizingMethod = "BASIC"
        copyPrivateIp                       = false
        copyTags                            = true
      }
    }
  })
}

# Parse response
locals {
  protection_group = jsondecode(data.aws_lambda_invocation.create_protection_group.result)
  group_id         = local.protection_group.groupId
  server_count     = local.protection_group.serverCount
}

# Create Recovery Plan
data "aws_lambda_invocation" "create_recovery_plan" {
  function_name = "aws-drs-orchestration-data-management-handler-test"

  input = jsonencode({
    operation = "create_recovery_plan"
    body = {
      name        = "Production DR Plan"
      description = "Disaster recovery for production workloads"
      waves = [
        {
          waveNumber        = 1
          name              = "Web Tier"
          protectionGroupId = local.group_id
          launchOrder       = 1
          pauseBeforeWave   = false
        }
      ]
    }
  })

  depends_on = [data.aws_lambda_invocation.create_protection_group]
}

# Outputs
output "protection_group_id" {
  value = local.group_id
}

output "server_count" {
  value = local.server_count
}

output "recovery_plan_id" {
  value = jsondecode(data.aws_lambda_invocation.create_recovery_plan.result).planId
}
```

### CloudWatch Events - Scheduled Tag Sync

EventBridge Rule for automated tag synchronization:

```json
{
  "source": ["aws.events"],
  "detail-type": ["Scheduled Event"],
  "detail": {
    "synch_tags": true,
    "synch_instance_type": false
  }
}
```

Create EventBridge Rule:
```bash
# Create rule
aws events put-rule \
  --name drs-tag-sync \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED

# Add Lambda target
aws events put-targets \
  --rule drs-tag-sync \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:aws-drs-orchestration-data-management-handler-test","Input"='{"synch_tags":true}'

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:123456789012:rule/drs-tag-sync
```

---

## Performance Characteristics

### Execution Time

| Operation | Typical Duration | Notes |
|-----------|------------------|-------|
| `create_protection_group` (tags) | 3-8 seconds | Queries DRS servers across regions |
| `create_protection_group` (explicit) | 1-3 seconds | Direct server validation |
| `update_protection_group` | 2-5 seconds | Includes conflict detection |
| `delete_protection_group` | 1-2 seconds | Checks Recovery Plan references |
| `create_recovery_plan` | 2-4 seconds | Validates waves and Protection Groups |
| `update_server_launch_config` | 1-2 seconds | Single server update |
| `bulk_update_server_configs` | 3-10 seconds | Depends on server count |
| `trigger_tag_sync` | 30-120 seconds | Processes all DRS-enabled regions |
| `import_configuration` | 10-60 seconds | Depends on manifest size |

### Concurrency

- **Max Concurrent Executions**: 1000 (default Lambda account limit)
- **DynamoDB Operations**: Optimistic locking prevents conflicts
- **Recommended Rate**: < 50 requests/second for sustained load

### Memory & Timeout

- **Memory**: 512 MB (moderate complexity with DRS API calls)
- **Timeout**: 120 seconds (tag sync can take time)
- **Cold Start**: < 3 seconds

### Optimistic Locking

- **Version Field**: All Protection Groups and Recovery Plans have version field
- **Update Pattern**: Fetch → Modify → Update with version
- **Conflict Resolution**: Retry with latest version on mismatch

---

## Related Documentation

- [Direct Lambda Invocation Mode Design](../../.kiro/specs/direct-lambda-invocation-mode/design.md)
- [Query Handler API](./QUERY_HANDLER_API.md)
- [Execution Handler API](./EXECUTION_HANDLER_API.md) (coming soon)
- [Developer Guide](../guides/DEVELOPER_GUIDE.md)

---

## Changelog

### Version 1.0 (2026-01-31)
- Initial API reference documentation
- Documented 18 data management operations
- Protection Group management (6 operations)
- Server launch configuration management (4 operations)
- Recovery Plan management (3 operations)
- Target Account management (3 operations)
- Staging Account management (3 operations)
- Tag synchronization (2 operations)
- Configuration import/export (1 operation)
- Included AWS CLI and Python boto3 examples
- Added error codes and troubleshooting guide
- Provided integration examples and Terraform modules

