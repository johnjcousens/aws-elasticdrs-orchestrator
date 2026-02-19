# Direct Lambda Invocation API Reference

## Overview

This document provides complete API reference for all operations supported by the AWS DRS Orchestration Platform in Direct Lambda Invocation Mode. Each operation includes:

- Operation name
- Lambda function handler
- Required parameters
- Optional parameters
- Request format (JSON)
- Response format (JSON)
- Error codes
- AWS CLI example
- Python boto3 example

## Table of Contents

1. [Protection Groups](#protection-groups)
2. [Recovery Plans](#recovery-plans)
3. [Executions](#executions)
4. [DRS Infrastructure](#drs-infrastructure)
5. [Target Accounts](#target-accounts)
6. [EC2 Resources](#ec2-resources)
7. [Configuration Management](#configuration-management)
8. [User Management](#user-management)

---

## Protection Groups

### List Protection Groups

**Operation**: `list_protection_groups`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "list_protection_groups",
  "queryParams": {
    "accountId": "123456789012",
    "limit": 50,
    "nextToken": "optional-pagination-token"
  }
}
```

**Response Format**:
```json
{
  "protectionGroups": [
    {
      "groupId": "pg-abc123",
      "name": "Production Servers",
      "description": "Critical production workloads",
      "tags": {
        "Environment": "Production",
        "Application": "WebApp"
      },
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-20T14:45:00Z",
      "serverCount": 15
    }
  ],
  "count": 1,
  "nextToken": "optional-next-page-token"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --payload '{"operation":"list_protection_groups","queryParams":{"limit":50}}' \
  response.json

cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='hrp-drs-tech-adapter-query-handler-dev',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'operation': 'list_protection_groups',
        'queryParams': {
            'limit': 50
        }
    })
)

result = json.loads(response['Payload'].read())
print(json.dumps(result, indent=2))
```

### Get Protection Group

**Operation**: `get_protection_group`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_protection_group",
  "groupId": "pg-abc123"
}
```

**Response Format**:
```json
{
  "groupId": "pg-abc123",
  "name": "Production Servers",
  "description": "Critical production workloads",
  "tags": {
    "Environment": "Production",
    "Application": "WebApp"
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-20T14:45:00Z",
  "serverCount": 15,
  "servers": [
    {
      "serverId": "s-1234567890abcdef0",
      "hostname": "web-server-01",
      "sourceAccountId": "123456789012",
      "region": "us-east-1"
    }
  ]
}
```

**Error Codes**:
- `MISSING_PARAMETER`: groupId is required
- `NOT_FOUND`: Protection group not found

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --payload '{"operation":"get_protection_group","groupId":"pg-abc123"}' \
  response.json
```


### Create Protection Group

**Operation**: `create_protection_group`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "name": "Production Servers",
    "description": "Critical production workloads",
    "tags": {
      "Environment": "Production",
      "Application": "WebApp",
      "Owner": "Platform Team"
    }
  }
}
```

**Response Format**:
```json
{
  "groupId": "pg-abc123",
  "name": "Production Servers",
  "description": "Critical production workloads",
  "tags": {
    "Environment": "Production",
    "Application": "WebApp",
    "Owner": "Platform Team"
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z",
  "serverCount": 0
}
```

**Error Codes**:
- `MISSING_PARAMETER`: name is required
- `INVALID_PARAMETER`: name must be 3-50 characters
- `ALREADY_EXISTS`: Protection group with this name already exists

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-data-management-handler-dev \
  --payload '{
    "operation": "create_protection_group",
    "body": {
      "name": "Production Servers",
      "description": "Critical production workloads",
      "tags": {
        "Environment": "Production"
      }
    }
  }' \
  response.json
```

### Update Protection Group

**Operation**: `update_protection_group`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "update_protection_group",
  "groupId": "pg-abc123",
  "body": {
    "description": "Updated description",
    "tags": {
      "Environment": "Production",
      "Application": "WebApp",
      "Owner": "Platform Team",
      "CostCenter": "Engineering"
    }
  }
}
```

**Response Format**:
```json
{
  "groupId": "pg-abc123",
  "name": "Production Servers",
  "description": "Updated description",
  "tags": {
    "Environment": "Production",
    "Application": "WebApp",
    "Owner": "Platform Team",
    "CostCenter": "Engineering"
  },
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-20T14:45:00Z",
  "serverCount": 15
}
```

### Delete Protection Group

**Operation**: `delete_protection_group`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "delete_protection_group",
  "groupId": "pg-abc123"
}
```

**Response Format**:
```json
{
  "message": "Protection group pg-abc123 deleted successfully"
}
```

**Error Codes**:
- `NOT_FOUND`: Protection group not found
- `INVALID_STATE`: Cannot delete protection group with active recovery plans

### Resolve Protection Group Tags

**Operation**: `resolve_protection_group_tags`  
**Handler**: `data-management-handler`  
**Method**: Query

**Request Format**:
```json
{
  "operation": "resolve_protection_group_tags",
  "body": {
    "tags": {
      "Environment": "Production",
      "Application": "WebApp"
    },
    "region": "us-east-1",
    "accountId": "123456789012"
  }
}
```

**Response Format**:
```json
{
  "servers": [
    {
      "serverId": "s-1234567890abcdef0",
      "hostname": "web-server-01",
      "sourceAccountId": "123456789012",
      "region": "us-east-1",
      "tags": {
        "Environment": "Production",
        "Application": "WebApp",
        "Name": "web-server-01"
      }
    }
  ],
  "count": 1
}
```

---

## Recovery Plans

### List Recovery Plans

**Operation**: `list_recovery_plans`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "list_recovery_plans",
  "queryParams": {
    "status": "ACTIVE",
    "limit": 50
  }
}
```

**Response Format**:
```json
{
  "recoveryPlans": [
    {
      "planId": "plan-xyz789",
      "name": "Production DR Plan",
      "description": "Disaster recovery for production",
      "protectionGroupId": "pg-abc123",
      "status": "ACTIVE",
      "waveCount": 2,
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-20T14:45:00Z"
    }
  ],
  "count": 1
}
```


### Get Recovery Plan

**Operation**: `get_recovery_plan`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_recovery_plan",
  "planId": "plan-xyz789"
}
```

**Response Format**:
```json
{
  "planId": "plan-xyz789",
  "name": "Production DR Plan",
  "description": "Disaster recovery for production",
  "protectionGroupId": "pg-abc123",
  "status": "ACTIVE",
  "waves": [
    {
      "waveNumber": 1,
      "name": "Database Tier",
      "launchOrder": 1,
      "servers": [
        {
          "serverId": "s-1234567890abcdef0",
          "hostname": "db-server-01"
        }
      ]
    },
    {
      "waveNumber": 2,
      "name": "Application Tier",
      "launchOrder": 2,
      "servers": [
        {
          "serverId": "s-abcdef1234567890",
          "hostname": "app-server-01"
        }
      ]
    }
  ],
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-20T14:45:00Z"
}
```

### Create Recovery Plan

**Operation**: `create_recovery_plan`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "create_recovery_plan",
  "body": {
    "name": "Production DR Plan",
    "description": "Disaster recovery for production",
    "protectionGroupId": "pg-abc123",
    "targetAccountId": "987654321098",
    "targetRegion": "us-west-2",
    "waves": [
      {
        "waveNumber": 1,
        "name": "Database Tier",
        "launchOrder": 1,
        "servers": ["s-1234567890abcdef0"]
      },
      {
        "waveNumber": 2,
        "name": "Application Tier",
        "launchOrder": 2,
        "servers": ["s-abcdef1234567890"]
      }
    ]
  }
}
```

**Response Format**:
```json
{
  "planId": "plan-xyz789",
  "name": "Production DR Plan",
  "description": "Disaster recovery for production",
  "protectionGroupId": "pg-abc123",
  "targetAccountId": "987654321098",
  "targetRegion": "us-west-2",
  "status": "ACTIVE",
  "waveCount": 2,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

### Update Recovery Plan

**Operation**: `update_recovery_plan`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "update_recovery_plan",
  "planId": "plan-xyz789",
  "body": {
    "description": "Updated recovery plan",
    "waves": [
      {
        "waveNumber": 1,
        "name": "Database Tier",
        "launchOrder": 1,
        "servers": ["s-1234567890abcdef0", "s-newserver123456"]
      }
    ]
  }
}
```

### Delete Recovery Plan

**Operation**: `delete_recovery_plan`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "delete_recovery_plan",
  "planId": "plan-xyz789"
}
```

**Response Format**:
```json
{
  "message": "Recovery plan plan-xyz789 deleted successfully"
}
```

---

## Executions

### List Executions

**Operation**: `list_executions`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "list_executions",
  "queryParams": {
    "status": "IN_PROGRESS",
    "planId": "plan-xyz789",
    "limit": 20,
    "nextToken": "optional-pagination-token"
  }
}
```

**Response Format**:
```json
{
  "executions": [
    {
      "executionId": "exec-123456",
      "planId": "plan-xyz789",
      "planName": "Production DR Plan",
      "status": "IN_PROGRESS",
      "executionType": "DRILL",
      "startTime": "2024-01-20T10:00:00Z",
      "currentWave": 1,
      "totalWaves": 2,
      "progress": 45
    }
  ],
  "count": 1,
  "nextToken": "optional-next-page-token"
}
```

### Get Execution

**Operation**: `get_execution`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_execution",
  "executionId": "exec-123456"
}
```

**Response Format**:
```json
{
  "executionId": "exec-123456",
  "planId": "plan-xyz789",
  "planName": "Production DR Plan",
  "status": "IN_PROGRESS",
  "executionType": "DRILL",
  "startTime": "2024-01-20T10:00:00Z",
  "currentWave": 1,
  "totalWaves": 2,
  "progress": 45,
  "waves": [
    {
      "waveNumber": 1,
      "name": "Database Tier",
      "status": "COMPLETED",
      "startTime": "2024-01-20T10:00:00Z",
      "endTime": "2024-01-20T10:15:00Z",
      "servers": [
        {
          "serverId": "s-1234567890abcdef0",
          "hostname": "db-server-01",
          "status": "LAUNCHED",
          "recoveryInstanceId": "i-0abcdef1234567890"
        }
      ]
    },
    {
      "waveNumber": 2,
      "name": "Application Tier",
      "status": "IN_PROGRESS",
      "startTime": "2024-01-20T10:15:00Z",
      "servers": [
        {
          "serverId": "s-abcdef1234567890",
          "hostname": "app-server-01",
          "status": "LAUNCHING"
        }
      ]
    }
  ]
}
```


### Start Execution

**Operation**: `start_execution`  
**Handler**: `execution-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "start_execution",
  "planId": "plan-xyz789",
  "executionType": "DRILL",
  "dryRun": false,
  "targetAccountId": "987654321098",
  "targetRegion": "us-west-2"
}
```

**Response Format**:
```json
{
  "executionId": "exec-123456",
  "planId": "plan-xyz789",
  "status": "PENDING",
  "executionType": "DRILL",
  "startTime": "2024-01-20T10:00:00Z",
  "stateMachineArn": "arn:aws:states:us-east-1:123456789012:execution:drs-orchestration:exec-123456",
  "message": "Recovery execution started successfully"
}
```

**Parameters**:
- `planId` (required): Recovery plan ID
- `executionType` (required): "DRILL" or "RECOVERY"
- `dryRun` (optional): If true, validates without executing (default: false)
- `targetAccountId` (optional): Override target account from plan
- `targetRegion` (optional): Override target region from plan

**Error Codes**:
- `MISSING_PARAMETER`: planId or executionType is required
- `INVALID_PARAMETER`: executionType must be DRILL or RECOVERY
- `NOT_FOUND`: Recovery plan not found
- `INVALID_STATE`: Recovery plan has no waves configured

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-execution-handler-dev \
  --payload '{
    "operation": "start_execution",
    "planId": "plan-xyz789",
    "executionType": "DRILL",
    "dryRun": false
  }' \
  response.json
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='hrp-drs-tech-adapter-execution-handler-dev',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'operation': 'start_execution',
        'planId': 'plan-xyz789',
        'executionType': 'DRILL',
        'dryRun': False
    })
)

result = json.loads(response['Payload'].read())
print(f"Execution ID: {result['executionId']}")
print(f"Status: {result['status']}")
```

### Cancel Execution

**Operation**: `cancel_execution`  
**Handler**: `execution-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "cancel_execution",
  "executionId": "exec-123456",
  "reason": "User requested cancellation"
}
```

**Response Format**:
```json
{
  "executionId": "exec-123456",
  "status": "CANCELLING",
  "message": "Execution cancellation initiated"
}
```

### Pause Execution

**Operation**: `pause_execution`  
**Handler**: `execution-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "pause_execution",
  "executionId": "exec-123456"
}
```

**Response Format**:
```json
{
  "executionId": "exec-123456",
  "status": "PAUSED",
  "message": "Execution paused successfully"
}
```

### Resume Execution

**Operation**: `resume_execution`  
**Handler**: `execution-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "resume_execution",
  "executionId": "exec-123456"
}
```

**Response Format**:
```json
{
  "executionId": "exec-123456",
  "status": "IN_PROGRESS",
  "message": "Execution resumed successfully"
}
```

### Terminate Recovery Instances

**Operation**: `terminate_instances`  
**Handler**: `execution-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "terminate_instances",
  "executionId": "exec-123456"
}
```

**Response Format**:
```json
{
  "executionId": "exec-123456",
  "jobIds": ["drsjob-abc123", "drsjob-def456"],
  "message": "Termination initiated for 2 recovery instances",
  "instanceCount": 2
}
```

### Get Recovery Instances

**Operation**: `get_recovery_instances`  
**Handler**: `execution-handler`  
**Method**: Query

**Request Format**:
```json
{
  "operation": "get_recovery_instances",
  "executionId": "exec-123456"
}
```

**Response Format**:
```json
{
  "executionId": "exec-123456",
  "instances": [
    {
      "recoveryInstanceId": "i-0abcdef1234567890",
      "sourceServerId": "s-1234567890abcdef0",
      "hostname": "db-server-01",
      "instanceType": "m5.large",
      "privateIpAddress": "10.0.1.100",
      "publicIpAddress": "54.123.45.67",
      "state": "running",
      "launchTime": "2024-01-20T10:05:00Z"
    }
  ],
  "count": 1
}
```

---

## DRS Infrastructure

### Get DRS Source Servers

**Operation**: `get_drs_source_servers`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_drs_source_servers",
  "queryParams": {
    "region": "us-east-1",
    "accountId": "123456789012"
  }
}
```

**Response Format**:
```json
{
  "servers": [
    {
      "serverId": "s-1234567890abcdef0",
      "hostname": "web-server-01",
      "sourceAccountId": "123456789012",
      "region": "us-east-1",
      "replicationStatus": "HEALTHY",
      "lastSeenByService": "2024-01-20T14:30:00Z",
      "tags": {
        "Environment": "Production",
        "Application": "WebApp"
      }
    }
  ],
  "count": 1
}
```


### Get DRS Quotas

**Operation**: `get_drs_quotas`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_drs_quotas",
  "queryParams": {
    "accountId": "123456789012",
    "region": "us-east-1"
  }
}
```

**Response Format**:
```json
{
  "accountId": "123456789012",
  "region": "us-east-1",
  "quotas": {
    "sourceServers": {
      "limit": 1000,
      "used": 15,
      "available": 985
    },
    "replicationServers": {
      "limit": 100,
      "used": 5,
      "available": 95
    }
  }
}
```

---

## Target Accounts

### Get Target Accounts

**Operation**: `get_target_accounts`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_target_accounts"
}
```

**Response Format**:
```json
{
  "accounts": [
    {
      "accountId": "987654321098",
      "accountName": "DR Target Account",
      "region": "us-west-2",
      "status": "ACTIVE",
      "roleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationRole",
      "createdAt": "2024-01-10T09:00:00Z"
    }
  ],
  "count": 1
}
```

### Get Target Account

**Operation**: `get_target_account`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_target_account",
  "accountId": "987654321098"
}
```

**Response Format**:
```json
{
  "accountId": "987654321098",
  "accountName": "DR Target Account",
  "region": "us-west-2",
  "status": "ACTIVE",
  "roleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationRole",
  "vpcId": "vpc-abc123",
  "subnetIds": ["subnet-123", "subnet-456"],
  "securityGroupIds": ["sg-789"],
  "createdAt": "2024-01-10T09:00:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

### Create Target Account

**Operation**: `create_target_account`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "create_target_account",
  "body": {
    "accountId": "987654321098",
    "accountName": "DR Target Account",
    "region": "us-west-2",
    "roleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationRole",
    "vpcId": "vpc-abc123",
    "subnetIds": ["subnet-123", "subnet-456"],
    "securityGroupIds": ["sg-789"]
  }
}
```

**Response Format**:
```json
{
  "accountId": "987654321098",
  "accountName": "DR Target Account",
  "region": "us-west-2",
  "status": "ACTIVE",
  "roleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationRole",
  "createdAt": "2024-01-10T09:00:00Z",
  "message": "Target account registered successfully"
}
```

### Update Target Account

**Operation**: `update_target_account`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "update_target_account",
  "accountId": "987654321098",
  "body": {
    "accountName": "Updated DR Target Account",
    "subnetIds": ["subnet-123", "subnet-456", "subnet-789"]
  }
}
```

### Delete Target Account

**Operation**: `delete_target_account`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "delete_target_account",
  "accountId": "987654321098"
}
```

**Response Format**:
```json
{
  "message": "Target account 987654321098 deleted successfully"
}
```

### Validate Target Account

**Operation**: `validate_target_account`  
**Handler**: `query-handler`  
**Method**: Query

**Request Format**:
```json
{
  "operation": "validate_target_account",
  "accountId": "987654321098"
}
```

**Response Format**:
```json
{
  "accountId": "987654321098",
  "valid": true,
  "checks": {
    "roleExists": true,
    "roleAssumable": true,
    "drsServiceEnabled": true,
    "vpcExists": true,
    "subnetsExist": true,
    "securityGroupsExist": true
  },
  "message": "Target account validation successful"
}
```

---

## EC2 Resources

### Get EC2 Subnets

**Operation**: `get_ec2_subnets`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_ec2_subnets",
  "queryParams": {
    "region": "us-west-2",
    "accountId": "987654321098"
  }
}
```

**Response Format**:
```json
{
  "subnets": [
    {
      "subnetId": "subnet-123",
      "subnetName": "Private Subnet 1A",
      "vpcId": "vpc-abc123",
      "availabilityZone": "us-west-2a",
      "cidrBlock": "10.0.1.0/24",
      "availableIpAddressCount": 250
    }
  ],
  "count": 1
}
```

### Get EC2 Security Groups

**Operation**: `get_ec2_security_groups`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_ec2_security_groups",
  "queryParams": {
    "region": "us-west-2",
    "accountId": "987654321098",
    "vpcId": "vpc-abc123"
  }
}
```

**Response Format**:
```json
{
  "securityGroups": [
    {
      "groupId": "sg-789",
      "groupName": "web-servers-sg",
      "description": "Security group for web servers",
      "vpcId": "vpc-abc123"
    }
  ],
  "count": 1
}
```

### Get EC2 Instance Profiles

**Operation**: `get_ec2_instance_profiles`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_ec2_instance_profiles",
  "queryParams": {
    "region": "us-west-2",
    "accountId": "987654321098"
  }
}
```

**Response Format**:
```json
{
  "instanceProfiles": [
    {
      "instanceProfileArn": "arn:aws:iam::987654321098:instance-profile/WebServerProfile",
      "instanceProfileName": "WebServerProfile",
      "roles": ["WebServerRole"]
    }
  ],
  "count": 1
}
```

### Get EC2 Instance Types

**Operation**: `get_ec2_instance_types`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_ec2_instance_types",
  "queryParams": {
    "region": "us-west-2"
  }
}
```

**Response Format**:
```json
{
  "instanceTypes": [
    {
      "instanceType": "t3.micro",
      "vcpus": 2,
      "memory": 1024,
      "storage": "EBS-Only",
      "networkPerformance": "Up to 5 Gigabit"
    },
    {
      "instanceType": "m5.large",
      "vcpus": 2,
      "memory": 8192,
      "storage": "EBS-Only",
      "networkPerformance": "Up to 10 Gigabit"
    }
  ],
  "count": 2
}
```

---

## Configuration Management

### Export Configuration

**Operation**: `export_configuration`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "export_configuration"
}
```

**Response Format**:
```json
{
  "exportedAt": "2024-01-20T15:00:00Z",
  "version": "1.0",
  "configuration": {
    "protectionGroups": [
      {
        "groupId": "pg-abc123",
        "name": "Production Servers",
        "tags": {
          "Environment": "Production"
        }
      }
    ],
    "recoveryPlans": [
      {
        "planId": "plan-xyz789",
        "name": "Production DR Plan",
        "protectionGroupId": "pg-abc123",
        "waves": []
      }
    ],
    "targetAccounts": [
      {
        "accountId": "987654321098",
        "accountName": "DR Target Account",
        "region": "us-west-2"
      }
    ]
  }
}
```


### Import Configuration

**Operation**: `import_configuration`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "import_configuration",
  "body": {
    "configuration": {
      "protectionGroups": [
        {
          "name": "Production Servers",
          "tags": {
            "Environment": "Production"
          }
        }
      ],
      "recoveryPlans": [
        {
          "name": "Production DR Plan",
          "protectionGroupId": "pg-abc123",
          "waves": []
        }
      ]
    },
    "overwrite": false
  }
}
```

**Response Format**:
```json
{
  "importedAt": "2024-01-20T15:05:00Z",
  "results": {
    "protectionGroups": {
      "created": 1,
      "updated": 0,
      "skipped": 0
    },
    "recoveryPlans": {
      "created": 1,
      "updated": 0,
      "skipped": 0
    }
  },
  "message": "Configuration imported successfully"
}
```

---

## Complete Operation Reference Table

| Operation | Handler | Method | Description |
|-----------|---------|--------|-------------|
| `list_protection_groups` | query-handler | GET | List all protection groups |
| `get_protection_group` | query-handler | GET | Get specific protection group |
| `create_protection_group` | data-management-handler | POST | Create new protection group |
| `update_protection_group` | data-management-handler | PUT | Update protection group |
| `delete_protection_group` | data-management-handler | DELETE | Delete protection group |
| `resolve_protection_group_tags` | data-management-handler | POST | Resolve DRS servers by tags |
| `list_recovery_plans` | query-handler | GET | List all recovery plans |
| `get_recovery_plan` | query-handler | GET | Get specific recovery plan |
| `create_recovery_plan` | data-management-handler | POST | Create new recovery plan |
| `update_recovery_plan` | data-management-handler | PUT | Update recovery plan |
| `delete_recovery_plan` | data-management-handler | DELETE | Delete recovery plan |
| `list_executions` | query-handler | GET | List all executions |
| `get_execution` | query-handler | GET | Get specific execution |
| `start_execution` | execution-handler | POST | Start recovery execution |
| `cancel_execution` | execution-handler | POST | Cancel execution |
| `pause_execution` | execution-handler | POST | Pause execution |
| `resume_execution` | execution-handler | POST | Resume execution |
| `terminate_instances` | execution-handler | POST | Terminate recovery instances |
| `get_recovery_instances` | execution-handler | GET | Get recovery instance details |
| `get_drs_source_servers` | query-handler | GET | List DRS source servers |
| `get_drs_quotas` | query-handler | GET | Get DRS service quotas |
| `get_target_accounts` | query-handler | GET | List target accounts |
| `get_target_account` | query-handler | GET | Get specific target account |
| `create_target_account` | data-management-handler | POST | Register target account |
| `update_target_account` | data-management-handler | PUT | Update target account |
| `delete_target_account` | data-management-handler | DELETE | Delete target account |
| `validate_target_account` | query-handler | POST | Validate target account |
| `get_ec2_subnets` | query-handler | GET | List EC2 subnets |
| `get_ec2_security_groups` | query-handler | GET | List EC2 security groups |
| `get_ec2_instance_profiles` | query-handler | GET | List IAM instance profiles |
| `get_ec2_instance_types` | query-handler | GET | List EC2 instance types |
| `export_configuration` | query-handler | GET | Export platform configuration |
| `import_configuration` | data-management-handler | POST | Import platform configuration |

---

## Error Response Format

All errors follow this consistent structure:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "specific field that caused error",
    "value": "invalid value",
    "constraint": "validation constraint violated"
  },
  "retryable": false,
  "retryAfter": 0
}
```

### Common Error Codes

| Error Code | HTTP Equivalent | Description | Retryable |
|------------|----------------|-------------|-----------|
| `INVALID_INVOCATION` | 400 | Event format is invalid | No |
| `INVALID_OPERATION` | 400 | Operation name not supported | No |
| `MISSING_PARAMETER` | 400 | Required parameter missing | No |
| `INVALID_PARAMETER` | 400 | Parameter value invalid | No |
| `AUTHORIZATION_FAILED` | 403 | IAM principal not authorized | No |
| `NOT_FOUND` | 404 | Resource not found | No |
| `ALREADY_EXISTS` | 409 | Resource already exists | No |
| `INVALID_STATE` | 409 | Resource in invalid state | No |
| `DYNAMODB_ERROR` | 500 | DynamoDB operation failed | Yes |
| `DRS_ERROR` | 500 | DRS API operation failed | Yes |
| `STEP_FUNCTIONS_ERROR` | 500 | Step Functions failed | Yes |
| `STS_ERROR` | 500 | STS assume role failed | Yes |
| `INTERNAL_ERROR` | 500 | Unexpected internal error | Yes |

---

## IAM Policy Requirements

### OrchestrationRole Policy

To invoke Lambda functions directly, the OrchestrationRole (or any IAM principal) needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:us-east-1:123456789012:function:hrp-drs-tech-adapter-query-handler-dev",
        "arn:aws:lambda:us-east-1:123456789012:function:hrp-drs-tech-adapter-execution-handler-dev",
        "arn:aws:lambda:us-east-1:123456789012:function:hrp-drs-tech-adapter-data-management-handler-dev"
      ]
    }
  ]
}
```

### Minimal IAM Policy for Read-Only Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:hrp-drs-tech-adapter-query-handler-dev"
    }
  ]
}
```

---

## Complete Integration Examples

### Python Script: List and Execute Recovery Plan

```python
#!/usr/bin/env python3
"""
Complete example: List recovery plans and execute one.
"""
import boto3
import json
import time

lambda_client = boto3.client('lambda', region_name='us-east-1')

def invoke_lambda(function_name, payload):
    """Invoke Lambda function and return parsed response."""
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    return json.loads(response['Payload'].read())

# 1. List all recovery plans
print("Listing recovery plans...")
plans_response = invoke_lambda(
    'hrp-drs-tech-adapter-query-handler-dev',
    {
        'operation': 'list_recovery_plans',
        'queryParams': {'status': 'ACTIVE'}
    }
)

if 'error' in plans_response:
    print(f"Error: {plans_response['error']} - {plans_response['message']}")
    exit(1)

plans = plans_response.get('recoveryPlans', [])
print(f"Found {len(plans)} active recovery plans")

if not plans:
    print("No recovery plans found")
    exit(0)

# 2. Select first plan
plan = plans[0]
print(f"\nSelected plan: {plan['name']} (ID: {plan['planId']})")

# 3. Start execution
print("\nStarting recovery execution...")
exec_response = invoke_lambda(
    'hrp-drs-tech-adapter-execution-handler-dev',
    {
        'operation': 'start_execution',
        'planId': plan['planId'],
        'executionType': 'DRILL',
        'dryRun': False
    }
)

if 'error' in exec_response:
    print(f"Error: {exec_response['error']} - {exec_response['message']}")
    exit(1)

execution_id = exec_response['executionId']
print(f"Execution started: {execution_id}")

# 4. Poll execution status
print("\nPolling execution status...")
while True:
    status_response = invoke_lambda(
        'hrp-drs-tech-adapter-query-handler-dev',
        {
            'operation': 'get_execution',
            'executionId': execution_id
        }
    )
    
    if 'error' in status_response:
        print(f"Error: {status_response['error']}")
        break
    
    status = status_response['status']
    progress = status_response.get('progress', 0)
    current_wave = status_response.get('currentWave', 0)
    total_waves = status_response.get('totalWaves', 0)
    
    print(f"Status: {status} | Progress: {progress}% | Wave: {current_wave}/{total_waves}")
    
    if status in ['COMPLETED', 'FAILED', 'CANCELLED']:
        break
    
    time.sleep(30)

print(f"\nExecution finished with status: {status}")
```

### Bash Script: Export Configuration

```bash
#!/bin/bash
# Export platform configuration to JSON file

FUNCTION_NAME="hrp-drs-tech-adapter-query-handler-dev"
OUTPUT_FILE="drs-config-export-$(date +%Y%m%d-%H%M%S).json"

echo "Exporting configuration from $FUNCTION_NAME..."

aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload '{"operation":"export_configuration"}' \
  --cli-binary-format raw-in-base64-out \
  "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
  echo "Configuration exported to $OUTPUT_FILE"
  
  # Pretty print the configuration
  cat "$OUTPUT_FILE" | jq '.'
  
  # Show summary
  echo ""
  echo "Summary:"
  echo "  Protection Groups: $(cat "$OUTPUT_FILE" | jq '.configuration.protectionGroups | length')"
  echo "  Recovery Plans: $(cat "$OUTPUT_FILE" | jq '.configuration.recoveryPlans | length')"
  echo "  Target Accounts: $(cat "$OUTPUT_FILE" | jq '.configuration.targetAccounts | length')"
else
  echo "Error exporting configuration"
  exit 1
fi
```

### Terraform Integration Example

```hcl
# Invoke Lambda to create protection group
resource "null_resource" "create_protection_group" {
  provisioner "local-exec" {
    command = <<EOF
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-data-management-handler-dev \
  --payload '{
    "operation": "create_protection_group",
    "body": {
      "name": "${var.protection_group_name}",
      "description": "Created by Terraform",
      "tags": ${jsonencode(var.tags)}
    }
  }' \
  response.json
EOF
  }
}

# Read the response
data "local_file" "protection_group_response" {
  depends_on = [null_resource.create_protection_group]
  filename   = "${path.module}/response.json"
}

output "protection_group_id" {
  value = jsondecode(data.local_file.protection_group_response.content).groupId
}
```

---

## Migration Guide

### From API Gateway Mode to Direct Invocation Mode

**Step 1: Test Direct Invocation Alongside API Gateway**

Deploy with `DeployApiGateway=true` (default) and test direct invocations:

```bash
# Test query operation
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

# Verify response
cat response.json | jq .
```

**Step 2: Update Automation Scripts**

Replace API Gateway calls with Lambda invocations:

```python
# Before (API Gateway)
import requests
response = requests.get(
    'https://api-id.execute-api.us-east-1.amazonaws.com/test/protection-groups',
    headers={'Authorization': f'Bearer {cognito_token}'}
)

# After (Direct Invocation)
import boto3
import json
lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName='hrp-drs-tech-adapter-query-handler-dev',
    Payload=json.dumps({'operation': 'list_protection_groups'})
)
result = json.loads(response['Payload'].read())
```

**Step 3: Validate All Operations**

Test all critical operations in direct invocation mode before removing API Gateway.

**Step 4: Redeploy Without API Gateway**

```bash
# Update CloudFormation stack
aws cloudformation update-stack \
  --stack-name hrp-drs-tech-adapter-dev \
  --use-previous-template \
  --parameters ParameterKey=DeployApiGateway,ParameterValue=false \
  --capabilities CAPABILITY_NAMED_IAM
```

**Step 5: Verify Removal**

Confirm API Gateway, Cognito, and Frontend resources are removed:

```bash
# Check stack resources
aws cloudformation list-stack-resources \
  --stack-name hrp-drs-tech-adapter-dev \
  --query 'StackResourceSummaries[?ResourceType==`AWS::ApiGateway::RestApi`]'
```

---

## Troubleshooting

### Common Issues

**Issue**: `AccessDeniedException` when invoking Lambda

**Solution**: Verify IAM principal has `lambda:InvokeFunction` permission:
```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/OrchestrationRole \
  --action-names lambda:InvokeFunction \
  --resource-arns arn:aws:lambda:us-east-1:123456789012:function:hrp-drs-tech-adapter-query-handler-dev
```

**Issue**: `INVALID_OPERATION` error

**Solution**: Check operation name spelling and refer to operation reference table above.

**Issue**: `MISSING_PARAMETER` error

**Solution**: Review request format for the operation and ensure all required parameters are included.

**Issue**: Cross-account operations fail

**Solution**: Verify DRSOrchestrationRole exists in target account and trust policy allows assumption from orchestration account.

---

## Additional Resources

- [AWS Lambda Invoke API Documentation](https://docs.aws.amazon.com/lambda/latest/dg/API_Invoke.html)
- [AWS CLI Lambda Invoke Command](https://docs.aws.amazon.com/cli/latest/reference/lambda/invoke.html)
- [Boto3 Lambda Client Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda.html#Lambda.Client.invoke)
- [AWS DRS API Reference](https://docs.aws.amazon.com/drs/latest/APIReference/Welcome.html)


---

## Server Launch Configuration

### Get Server Launch Configuration

**Operation**: `get_server_launch_config`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_server_launch_config",
  "serverId": "s-1234567890abcdef0",
  "accountId": "123456789012",
  "region": "us-east-1"
}
```

**Response Format**:
```json
{
  "serverId": "s-1234567890abcdef0",
  "hostname": "web-server-01",
  "accountId": "123456789012",
  "region": "us-east-1",
  "launchConfiguration": {
    "copyPrivateIp": false,
    "copyTags": true,
    "launchDisposition": "STARTED",
    "licensing": {
      "osByol": false
    },
    "name": "web-server-01-recovery",
    "targetInstanceTypeRightSizingMethod": "BASIC",
    "ec2LaunchTemplateID": "lt-abc123",
    "launchIntoInstanceProperties": {
      "launchIntoEC2InstanceID": ""
    },
    "postLaunchActions": [],
    "staticIpConfiguration": {
      "enabled": true,
      "privateIpAddress": "10.0.1.100"
    }
  },
  "updatedAt": "2024-01-20T14:30:00Z"
}
```

**Parameters**:
- `serverId` (required): DRS source server ID
- `accountId` (required): AWS account ID where server is located
- `region` (required): AWS region where server is located

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --payload '{
    "operation": "get_server_launch_config",
    "serverId": "s-1234567890abcdef0",
    "accountId": "123456789012",
    "region": "us-east-1"
  }' \
  response.json
```

### Update Server Launch Configuration

**Operation**: `update_server_launch_config`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "update_server_launch_config",
  "serverId": "s-1234567890abcdef0",
  "accountId": "123456789012",
  "region": "us-east-1",
  "body": {
    "copyPrivateIp": false,
    "copyTags": true,
    "launchDisposition": "STARTED",
    "name": "web-server-01-recovery",
    "targetInstanceTypeRightSizingMethod": "BASIC",
    "staticIpConfiguration": {
      "enabled": true,
      "privateIpAddress": "10.0.1.100"
    }
  }
}
```

**Response Format**:
```json
{
  "serverId": "s-1234567890abcdef0",
  "hostname": "web-server-01",
  "accountId": "123456789012",
  "region": "us-east-1",
  "launchConfiguration": {
    "copyPrivateIp": false,
    "copyTags": true,
    "launchDisposition": "STARTED",
    "name": "web-server-01-recovery",
    "targetInstanceTypeRightSizingMethod": "BASIC",
    "staticIpConfiguration": {
      "enabled": true,
      "privateIpAddress": "10.0.1.100"
    }
  },
  "updatedAt": "2024-01-20T15:00:00Z",
  "message": "Launch configuration updated successfully"
}
```

**Static IP Configuration Fields**:
- `enabled` (boolean): Enable static IP assignment
- `privateIpAddress` (string): Static private IP address to assign

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Update server launch config with static IP
response = lambda_client.invoke(
    FunctionName='hrp-drs-tech-adapter-data-management-handler-dev',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'operation': 'update_server_launch_config',
        'serverId': 's-1234567890abcdef0',
        'accountId': '123456789012',
        'region': 'us-east-1',
        'body': {
            'copyPrivateIp': False,
            'copyTags': True,
            'launchDisposition': 'STARTED',
            'staticIpConfiguration': {
                'enabled': True,
                'privateIpAddress': '10.0.1.100'
            }
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Updated server: {result['hostname']}")
print(f"Static IP: {result['launchConfiguration']['staticIpConfiguration']['privateIpAddress']}")
```

### Bulk Update Server Configurations

**Operation**: `bulk_update_server_configs`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "bulk_update_server_configs",
  "accountId": "123456789012",
  "region": "us-east-1",
  "body": {
    "servers": [
      {
        "serverId": "s-1234567890abcdef0",
        "launchConfiguration": {
          "copyPrivateIp": false,
          "staticIpConfiguration": {
            "enabled": true,
            "privateIpAddress": "10.0.1.100"
          }
        }
      },
      {
        "serverId": "s-abcdef1234567890",
        "launchConfiguration": {
          "copyPrivateIp": false,
          "staticIpConfiguration": {
            "enabled": true,
            "privateIpAddress": "10.0.1.101"
          }
        }
      }
    ]
  }
}
```

**Response Format**:
```json
{
  "accountId": "123456789012",
  "region": "us-east-1",
  "results": {
    "successful": 2,
    "failed": 0,
    "total": 2
  },
  "servers": [
    {
      "serverId": "s-1234567890abcdef0",
      "status": "SUCCESS",
      "message": "Configuration updated"
    },
    {
      "serverId": "s-abcdef1234567890",
      "status": "SUCCESS",
      "message": "Configuration updated"
    }
  ]
}
```

### Validate Static IP

**Operation**: `validate_static_ip`  
**Handler**: `query-handler`  
**Method**: Query

**Request Format**:
```json
{
  "operation": "validate_static_ip",
  "accountId": "987654321098",
  "region": "us-west-2",
  "body": {
    "subnetId": "subnet-123",
    "ipAddress": "10.0.1.100"
  }
}
```

**Response Format**:
```json
{
  "valid": true,
  "ipAddress": "10.0.1.100",
  "subnetId": "subnet-123",
  "subnetCidr": "10.0.1.0/24",
  "available": true,
  "checks": {
    "inSubnetRange": true,
    "notReserved": true,
    "notInUse": true
  },
  "message": "IP address is valid and available"
}
```

**Error Response Example**:
```json
{
  "valid": false,
  "ipAddress": "10.0.1.100",
  "subnetId": "subnet-123",
  "available": false,
  "checks": {
    "inSubnetRange": true,
    "notReserved": true,
    "notInUse": false
  },
  "error": "INVALID_PARAMETER",
  "message": "IP address 10.0.1.100 is already in use"
}
```

### Get Server Configuration History

**Operation**: `get_server_config_history`  
**Handler**: `query-handler`  
**Method**: Query (read-only)

**Request Format**:
```json
{
  "operation": "get_server_config_history",
  "serverId": "s-1234567890abcdef0",
  "accountId": "123456789012",
  "region": "us-east-1",
  "queryParams": {
    "limit": 10
  }
}
```

**Response Format**:
```json
{
  "serverId": "s-1234567890abcdef0",
  "accountId": "123456789012",
  "region": "us-east-1",
  "history": [
    {
      "timestamp": "2024-01-20T15:00:00Z",
      "changedBy": "arn:aws:iam::123456789012:role/OrchestrationRole",
      "changes": {
        "staticIpConfiguration.enabled": {
          "old": false,
          "new": true
        },
        "staticIpConfiguration.privateIpAddress": {
          "old": null,
          "new": "10.0.1.100"
        }
      }
    },
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "changedBy": "user@example.com",
      "changes": {
        "copyTags": {
          "old": false,
          "new": true
        }
      }
    }
  ],
  "count": 2
}
```

---

## Cross-Account Operations

All operations support cross-account context through the `accountId` parameter. The system automatically assumes the DRSOrchestrationRole in the target account.

### Cross-Account Protection Group with Servers

**Request Format**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "name": "Multi-Account Production Servers",
    "description": "Servers across multiple accounts",
    "tags": {
      "Environment": "Production"
    },
    "accountContext": {
      "sourceAccountId": "123456789012",
      "targetAccountId": "987654321098",
      "region": "us-east-1"
    }
  }
}
```

### Cross-Account Server Query

**Request Format**:
```json
{
  "operation": "get_drs_source_servers",
  "queryParams": {
    "accountId": "123456789012",
    "region": "us-east-1"
  }
}
```

**Response includes account context**:
```json
{
  "servers": [
    {
      "serverId": "s-1234567890abcdef0",
      "hostname": "web-server-01",
      "sourceAccountId": "123456789012",
      "region": "us-east-1",
      "accountContext": {
        "accountId": "123456789012",
        "accountName": "Production Account",
        "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
      }
    }
  ]
}
```

### Cross-Account Recovery Execution

**Request Format**:
```json
{
  "operation": "start_execution",
  "planId": "plan-xyz789",
  "executionType": "DRILL",
  "accountContext": {
    "sourceAccountId": "123456789012",
    "targetAccountId": "987654321098",
    "sourceRegion": "us-east-1",
    "targetRegion": "us-west-2"
  }
}
```

**Response includes cross-account details**:
```json
{
  "executionId": "exec-123456",
  "planId": "plan-xyz789",
  "status": "PENDING",
  "accountContext": {
    "sourceAccountId": "123456789012",
    "targetAccountId": "987654321098",
    "sourceRegion": "us-east-1",
    "targetRegion": "us-west-2",
    "assumedRoleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationRole"
  },
  "message": "Cross-account recovery execution started"
}
```

---

## Staging Accounts Management

### Discover Staging Accounts

**Operation**: `discover_staging_accounts`  
**Handler**: `query-handler`  
**Method**: Query

**Request Format**:
```json
{
  "operation": "discover_staging_accounts",
  "targetAccountId": "987654321098",
  "region": "us-west-2"
}
```

**Response Format**:
```json
{
  "targetAccountId": "987654321098",
  "region": "us-west-2",
  "stagingAccounts": [
    {
      "accountId": "111222333444",
      "accountAlias": "drs-staging-account-1",
      "status": "ACTIVE",
      "capacity": {
        "maxServers": 100,
        "usedServers": 15,
        "availableServers": 85
      }
    }
  ],
  "count": 1
}
```

### Sync Staging Accounts

**Operation**: `sync_staging_accounts`  
**Handler**: `data-management-handler`  
**Method**: Write

**Request Format**:
```json
{
  "operation": "sync_staging_accounts",
  "targetAccountId": "987654321098",
  "region": "us-west-2"
}
```

**Response Format**:
```json
{
  "targetAccountId": "987654321098",
  "region": "us-west-2",
  "syncedAt": "2024-01-20T16:00:00Z",
  "results": {
    "discovered": 1,
    "updated": 1,
    "removed": 0
  },
  "message": "Staging accounts synchronized successfully"
}
```

### Validate Staging Account

**Operation**: `validate_staging_account`  
**Handler**: `query-handler`  
**Method**: Query

**Request Format**:
```json
{
  "operation": "validate_staging_account",
  "accountId": "111222333444",
  "region": "us-west-2"
}
```

**Response Format**:
```json
{
  "accountId": "111222333444",
  "region": "us-west-2",
  "valid": true,
  "checks": {
    "accountAccessible": true,
    "drsServiceEnabled": true,
    "sufficientCapacity": true,
    "networkConnectivity": true
  },
  "capacity": {
    "maxServers": 100,
    "usedServers": 15,
    "availableServers": 85
  },
  "message": "Staging account validation successful"
}
```

---

## Complete Multi-Account Workflow Example

### Python Script: Multi-Account DR Setup

```python
#!/usr/bin/env python3
"""
Complete multi-account DR setup workflow.
"""
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

def invoke_lambda(function_name, payload):
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    return json.loads(response['Payload'].read())

# Account configuration
SOURCE_ACCOUNT = "123456789012"
TARGET_ACCOUNT = "987654321098"
SOURCE_REGION = "us-east-1"
TARGET_REGION = "us-west-2"

print("=== Multi-Account DR Setup ===\n")

# 1. Register target account
print("1. Registering target account...")
target_response = invoke_lambda(
    'hrp-drs-tech-adapter-data-management-handler-dev',
    {
        'operation': 'create_target_account',
        'body': {
            'accountId': TARGET_ACCOUNT,
            'accountName': 'DR Target Account',
            'region': TARGET_REGION,
            'roleArn': f'arn:aws:iam::{TARGET_ACCOUNT}:role/DRSOrchestrationRole'
        }
    }
)
print(f"   Target account registered: {target_response.get('message')}\n")

# 2. Discover DRS source servers in source account
print("2. Discovering DRS source servers...")
servers_response = invoke_lambda(
    'hrp-drs-tech-adapter-query-handler-dev',
    {
        'operation': 'get_drs_source_servers',
        'queryParams': {
            'accountId': SOURCE_ACCOUNT,
            'region': SOURCE_REGION
        }
    }
)
servers = servers_response.get('servers', [])
print(f"   Found {len(servers)} servers\n")

# 3. Configure static IPs for servers
print("3. Configuring static IPs for servers...")
server_configs = []
for i, server in enumerate(servers[:5]):  # First 5 servers
    static_ip = f"10.0.1.{100 + i}"
    
    # Validate static IP
    validation = invoke_lambda(
        'hrp-drs-tech-adapter-query-handler-dev',
        {
            'operation': 'validate_static_ip',
            'accountId': TARGET_ACCOUNT,
            'region': TARGET_REGION,
            'body': {
                'subnetId': 'subnet-123',
                'ipAddress': static_ip
            }
        }
    )
    
    if validation.get('valid'):
        server_configs.append({
            'serverId': server['serverId'],
            'launchConfiguration': {
                'copyPrivateIp': False,
                'staticIpConfiguration': {
                    'enabled': True,
                    'privateIpAddress': static_ip
                }
            }
        })
        print(f"   {server['hostname']}: {static_ip} (validated)")

# Bulk update server configurations
if server_configs:
    bulk_response = invoke_lambda(
        'hrp-drs-tech-adapter-data-management-handler-dev',
        {
            'operation': 'bulk_update_server_configs',
            'accountId': SOURCE_ACCOUNT,
            'region': SOURCE_REGION,
            'body': {
                'servers': server_configs
            }
        }
    )
    print(f"\n   Updated {bulk_response['results']['successful']} server configurations\n")

# 4. Create protection group
print("4. Creating protection group...")
pg_response = invoke_lambda(
    'hrp-drs-tech-adapter-data-management-handler-dev',
    {
        'operation': 'create_protection_group',
        'body': {
            'name': 'Multi-Account Production Servers',
            'description': 'Cross-account DR protection',
            'tags': {
                'Environment': 'Production',
                'SourceAccount': SOURCE_ACCOUNT,
                'TargetAccount': TARGET_ACCOUNT
            },
            'accountContext': {
                'sourceAccountId': SOURCE_ACCOUNT,
                'targetAccountId': TARGET_ACCOUNT,
                'region': SOURCE_REGION
            }
        }
    }
)
group_id = pg_response['groupId']
print(f"   Protection group created: {group_id}\n")

# 5. Create recovery plan
print("5. Creating recovery plan...")
plan_response = invoke_lambda(
    'hrp-drs-tech-adapter-data-management-handler-dev',
    {
        'operation': 'create_recovery_plan',
        'body': {
            'name': 'Multi-Account DR Plan',
            'description': 'Cross-account disaster recovery',
            'protectionGroupId': group_id,
            'targetAccountId': TARGET_ACCOUNT,
            'targetRegion': TARGET_REGION,
            'waves': [
                {
                    'waveNumber': 1,
                    'name': 'Application Tier',
                    'launchOrder': 1,
                    'servers': [s['serverId'] for s in servers[:5]]
                }
            ]
        }
    }
)
plan_id = plan_response['planId']
print(f"   Recovery plan created: {plan_id}\n")

print("=== Setup Complete ===")
print(f"Protection Group: {group_id}")
print(f"Recovery Plan: {plan_id}")
print(f"Source: {SOURCE_ACCOUNT} ({SOURCE_REGION})")
print(f"Target: {TARGET_ACCOUNT} ({TARGET_REGION})")
```

---

## Updated Operation Reference Table

| Operation | Handler | Cross-Account | Description |
|-----------|---------|---------------|-------------|
| `list_protection_groups` | query-handler | ✓ | List all protection groups |
| `get_protection_group` | query-handler | ✓ | Get specific protection group |
| `create_protection_group` | data-management-handler | ✓ | Create new protection group |
| `update_protection_group` | data-management-handler | ✓ | Update protection group |
| `delete_protection_group` | data-management-handler | ✓ | Delete protection group |
| `resolve_protection_group_tags` | data-management-handler | ✓ | Resolve DRS servers by tags |
| `get_server_launch_config` | query-handler | ✓ | Get server launch configuration |
| `update_server_launch_config` | data-management-handler | ✓ | Update server launch configuration |
| `bulk_update_server_configs` | data-management-handler | ✓ | Bulk update server configurations |
| `validate_static_ip` | query-handler | ✓ | Validate static IP address |
| `get_server_config_history` | query-handler | ✓ | Get server configuration history |
| `list_recovery_plans` | query-handler | ✓ | List all recovery plans |
| `get_recovery_plan` | query-handler | ✓ | Get specific recovery plan |
| `create_recovery_plan` | data-management-handler | ✓ | Create new recovery plan |
| `update_recovery_plan` | data-management-handler | ✓ | Update recovery plan |
| `delete_recovery_plan` | data-management-handler | ✓ | Delete recovery plan |
| `list_executions` | query-handler | ✓ | List all executions |
| `get_execution` | query-handler | ✓ | Get specific execution |
| `start_execution` | execution-handler | ✓ | Start recovery execution |
| `cancel_execution` | execution-handler | ✓ | Cancel execution |
| `pause_execution` | execution-handler | ✓ | Pause execution |
| `resume_execution` | execution-handler | ✓ | Resume execution |
| `terminate_instances` | execution-handler | ✓ | Terminate recovery instances |
| `get_recovery_instances` | execution-handler | ✓ | Get recovery instance details |
| `get_drs_source_servers` | query-handler | ✓ | List DRS source servers |
| `get_drs_quotas` | query-handler | ✓ | Get DRS service quotas |
| `get_target_accounts` | query-handler | ✓ | List target accounts |
| `get_target_account` | query-handler | ✓ | Get specific target account |
| `create_target_account` | data-management-handler | ✓ | Register target account |
| `update_target_account` | data-management-handler | ✓ | Update target account |
| `delete_target_account` | data-management-handler | ✓ | Delete target account |
| `validate_target_account` | query-handler | ✓ | Validate target account |
| `discover_staging_accounts` | query-handler | ✓ | Discover staging accounts |
| `sync_staging_accounts` | data-management-handler | ✓ | Sync staging accounts |
| `validate_staging_account` | query-handler | ✓ | Validate staging account |
| `get_ec2_subnets` | query-handler | ✓ | List EC2 subnets |
| `get_ec2_security_groups` | query-handler | ✓ | List EC2 security groups |
| `get_ec2_instance_profiles` | query-handler | ✓ | List IAM instance profiles |
| `get_ec2_instance_types` | query-handler | ✓ | List EC2 instance types |
| `export_configuration` | query-handler | ✓ | Export platform configuration |
| `import_configuration` | data-management-handler | ✓ | Import platform configuration |

**Total Operations**: 41 (all support cross-account context)
