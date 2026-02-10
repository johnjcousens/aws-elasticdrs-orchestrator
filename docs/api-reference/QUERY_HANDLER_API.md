# Query Handler API Reference

## Overview

The Query Handler provides read-only query operations for the AWS DRS Orchestration Platform. It supports both API Gateway invocations (for frontend/CLI) and direct Lambda invocations (for automation/IaC workflows).

### Key Features

- **Dual Invocation Support**: API Gateway REST endpoints and direct Lambda invocation
- **Cross-Account Queries**: Hub-and-spoke model with IAM role assumption
- **DRS Infrastructure**: Source servers, capacity, quotas, accounts
- **EC2 Resources**: Subnets, security groups, instance types, instance profiles
- **Configuration Export**: Protection Groups and Recovery Plans
- **Performance Optimized**: Concurrent regional queries, response caching

### Invocation Modes

#### 1. API Gateway Mode (Frontend/CLI)
```bash
curl -X GET "https://api.example.com/drs/source-servers?region=us-east-1" \
  -H "Authorization: Bearer $TOKEN"
```

#### 2. Direct Lambda Invocation (Automation)
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation": "get_drs_source_servers", "queryParams": {"region": "us-east-1"}}' \
  response.json
```

#### 3. Python boto3 (Programmatic)
```python
import boto3
import json

lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName='query-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_source_servers",
        "queryParams": {"region": "us-east-1"}
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
- **Required IAM Permission**: `lambda:InvokeFunction` on query-handler function

### Required IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:*:*:function:aws-drs-orchestration-query-handler-*"
    }
  ]
}
```


## Operations

### DRS Infrastructure Queries

#### get_drs_source_servers

Query DRS source servers in a specific region with optional filtering.

**Operation**: `get_drs_source_servers`

**Parameters**:
- `region` (required): AWS region to query (e.g., "us-east-1")
- `accountId` (optional): Target account ID for cross-account queries
- `currentProtectionGroupId` (optional): Exclude servers from this Protection Group

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
      "sourceServerID": "s-abc123def456",
      "hostname": "web-server-01",
      "fqdn": "web-server-01.example.com",
      "nameTag": "Production Web Server",
      "sourceInstanceId": "i-0123456789abcdef0",
      "sourceIp": "10.0.1.50",
      "os": "Ubuntu 20.04 LTS",
      "state": "Ready for Launch",
      "replicationState": "CONTINUOUS",
      "lagDuration": "PT0S",
      "lastSeen": "2026-01-31T12:00:00Z",
      "hardware": {
        "cpus": [
          {
            "modelName": "Intel Xeon",
            "cores": 4
          }
        ],
        "totalCores": 4,
        "ramBytes": 17179869184,
        "ramGiB": 16.0,
        "disks": [
          {
            "deviceName": "/dev/sda1",
            "bytes": 107374182400,
            "sizeGiB": 100.0
          }
        ],
        "totalDiskGiB": 100.0
      },
      "networkInterfaces": [
        {
          "ips": ["10.0.1.50"],
          "macAddress": "02:42:ac:11:00:02",
          "isPrimary": true
        }
      ],
      "drsTags": {
        "Environment": "production",
        "Application": "web"
      },
      "assignedToProtectionGroup": {
        "protectionGroupId": "pg-xyz789",
        "protectionGroupName": "Production Servers"
      },
      "selectable": false
    }
  ],
  "region": "us-east-1",
  "serverCount": 1
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_drs_source_servers","queryParams":{"region":"us-east-1"}}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_source_servers",
        "queryParams": {
            "region": "us-east-1"
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Found {result['serverCount']} servers in {result['region']}")
for server in result['servers']:
    print(f"  - {server['hostname']} ({server['sourceServerID']}): {server['state']}")
```

**Error Responses**:
- `MISSING_PARAMETER`: region parameter is required
- `DRS_NOT_INITIALIZED`: DRS not initialized in the specified region
- `REGION_NOT_ENABLED`: Opt-in region not enabled in AWS account
- `DRS_ERROR`: Failed to retrieve DRS source servers
- `AUTHORIZATION_FAILED`: Insufficient IAM permissions

---

#### get_drs_account_capacity_all_regions

Get DRS account capacity aggregated across all 15 DRS-enabled regions.

**Operation**: `get_drs_account_capacity_all_regions`

**Parameters**:
- `account_context` (optional): Cross-account context with accountId

**Request Format**:
```json
{
  "operation": "get_drs_account_capacity_all_regions",
  "queryParams": {
    "account_context": {
      "accountId": "123456789012"
    }
  }
}
```

**Response Format**:
```json
{
  "totalSourceServers": 325,
  "replicatingServers": 280,
  "maxReplicatingServers": 300,
  "maxSourceServers": 4000,
  "availableReplicatingSlots": 320,
  "status": "OK",
  "message": "Capacity OK: 280 replicating servers across 2 regions (each region has 300-server limit)",
  "regionalBreakdown": [
    {
      "region": "us-east-1",
      "totalServers": 200,
      "replicatingServers": 180,
      "maxReplicating": 300,
      "availableSlots": 120,
      "percentUsed": 60.0,
      "status": "OK"
    },
    {
      "region": "us-west-2",
      "totalServers": 125,
      "replicatingServers": 100,
      "maxReplicating": 300,
      "availableSlots": 200,
      "percentUsed": 33.3,
      "status": "OK"
    }
  ],
  "failedRegions": [],
  "activeRegions": 2,
  "totalRegionalCapacity": 600
}
```

**Status Values**:
- `OK`: All regions < 240 replicating servers (< 80% of limit)
- `INFO`: Any region >= 240 replicating servers (>= 80% of limit)
- `WARNING`: Any region >= 270 replicating servers (>= 90% of limit)
- `CRITICAL`: Any region >= 300 replicating servers (at hard limit)

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_drs_account_capacity_all_regions"}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_account_capacity_all_regions"
    })
)

result = json.loads(response['Payload'].read())
print(f"Account Capacity Status: {result['status']}")
print(f"Total Servers: {result['totalSourceServers']}")
print(f"Replicating: {result['replicatingServers']}")
print(f"Available Slots: {result['availableReplicatingSlots']}")
print(f"\nRegional Breakdown:")
for region in result['regionalBreakdown']:
    print(f"  {region['region']}: {region['replicatingServers']}/{region['maxReplicating']} ({region['percentUsed']}%)")
```

**Error Responses**:
- `DRS_ERROR`: Failed to query DRS capacity
- `INTERNAL_ERROR`: Unexpected error during capacity aggregation

---

#### get_target_accounts

List all configured target accounts for cross-account DR operations.

**Operation**: `get_target_accounts`

**Parameters**: None

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
      "accountId": "123456789012",
      "accountName": "Production Account",
      "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole",
      "assumeRoleName": "DRSOrchestrationCrossAccountRole",
      "externalId": "unique-external-id-123",
      "status": "ACTIVE",
      "createdAt": "2026-01-15T10:00:00Z",
      "updatedAt": "2026-01-30T15:30:00Z"
    }
  ],
  "count": 1
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_target_accounts"}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_target_accounts"
    })
)

result = json.loads(response['Payload'].read())
print(f"Found {result['count']} target accounts:")
for account in result['accounts']:
    print(f"  - {account['accountName']} ({account['accountId']}): {account['status']}")
```

**Error Responses**:
- `DYNAMODB_ERROR`: Failed to query target accounts table
- `INTERNAL_ERROR`: Unexpected error

---

### EC2 Resource Queries

#### get_ec2_subnets

List EC2 subnets in a specific VPC and region.

**Operation**: `get_ec2_subnets`

**Parameters**:
- `region` (required): AWS region
- `vpcId` (required): VPC ID to query subnets
- `availabilityZone` (optional): Filter by availability zone

**Request Format**:
```json
{
  "operation": "get_ec2_subnets",
  "queryParams": {
    "region": "us-east-1",
    "vpcId": "vpc-0123456789abcdef0"
  }
}
```

**Response Format**:
```json
{
  "subnets": [
    {
      "subnetId": "subnet-abc123",
      "subnetName": "Private Subnet 1A",
      "availabilityZone": "us-east-1a",
      "cidrBlock": "10.0.1.0/24",
      "vpcId": "vpc-0123456789abcdef0",
      "availableIpAddressCount": 251
    }
  ],
  "count": 1
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_ec2_subnets","queryParams":{"region":"us-east-1","vpcId":"vpc-0123456789abcdef0"}}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_ec2_subnets",
        "queryParams": {
            "region": "us-east-1",
            "vpcId": "vpc-0123456789abcdef0"
        }
    })
)

result = json.loads(response['Payload'].read())
for subnet in result['subnets']:
    print(f"{subnet['subnetName']} ({subnet['subnetId']}): {subnet['cidrBlock']} in {subnet['availabilityZone']}")
```

**Error Responses**:
- `MISSING_PARAMETER`: region or vpcId parameter is required
- `NOT_FOUND`: VPC not found
- `INTERNAL_ERROR`: Failed to retrieve subnets

---

#### get_ec2_security_groups

List EC2 security groups in a specific VPC and region.

**Operation**: `get_ec2_security_groups`

**Parameters**:
- `region` (required): AWS region
- `vpcId` (required): VPC ID to query security groups

**Request Format**:
```json
{
  "operation": "get_ec2_security_groups",
  "queryParams": {
    "region": "us-east-1",
    "vpcId": "vpc-0123456789abcdef0"
  }
}
```

**Response Format**:
```json
{
  "securityGroups": [
    {
      "groupId": "sg-abc123",
      "groupName": "web-server-sg",
      "description": "Security group for web servers",
      "vpcId": "vpc-0123456789abcdef0"
    }
  ],
  "count": 1
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_ec2_security_groups","queryParams":{"region":"us-east-1","vpcId":"vpc-0123456789abcdef0"}}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_ec2_security_groups",
        "queryParams": {
            "region": "us-east-1",
            "vpcId": "vpc-0123456789abcdef0"
        }
    })
)

result = json.loads(response['Payload'].read())
for sg in result['securityGroups']:
    print(f"{sg['groupName']} ({sg['groupId']}): {sg['description']}")
```

**Error Responses**:
- `MISSING_PARAMETER`: region or vpcId parameter is required
- `NOT_FOUND`: VPC not found
- `INTERNAL_ERROR`: Failed to retrieve security groups

---

#### get_ec2_instance_types

List available EC2 instance types in a region.

**Operation**: `get_ec2_instance_types`

**Parameters**:
- `region` (required): AWS region
- `instanceFamily` (optional): Filter by instance family (e.g., "t3", "m5")

**Request Format**:
```json
{
  "operation": "get_ec2_instance_types",
  "queryParams": {
    "region": "us-east-1",
    "instanceFamily": "t3"
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
      "memoryMiB": 1024,
      "instanceFamily": "t3"
    },
    {
      "instanceType": "t3.small",
      "vcpus": 2,
      "memoryMiB": 2048,
      "instanceFamily": "t3"
    }
  ],
  "count": 2
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_ec2_instance_types","queryParams":{"region":"us-east-1"}}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_ec2_instance_types",
        "queryParams": {
            "region": "us-east-1",
            "instanceFamily": "t3"
        }
    })
)

result = json.loads(response['Payload'].read())
for instance_type in result['instanceTypes']:
    print(f"{instance_type['instanceType']}: {instance_type['vcpus']} vCPUs, {instance_type['memoryMiB']} MiB RAM")
```

**Error Responses**:
- `MISSING_PARAMETER`: region parameter is required
- `INTERNAL_ERROR`: Failed to retrieve instance types

---

#### get_ec2_instance_profiles

List IAM instance profiles available in a region.

**Operation**: `get_ec2_instance_profiles`

**Parameters**:
- `region` (required): AWS region

**Request Format**:
```json
{
  "operation": "get_ec2_instance_profiles",
  "queryParams": {
    "region": "us-east-1"
  }
}
```

**Response Format**:
```json
{
  "instanceProfiles": [
    {
      "instanceProfileName": "EC2-SSM-Role",
      "instanceProfileArn": "arn:aws:iam::123456789012:instance-profile/EC2-SSM-Role",
      "roles": ["EC2-SSM-Role"]
    }
  ],
  "count": 1
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_ec2_instance_profiles","queryParams":{"region":"us-east-1"}}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_ec2_instance_profiles",
        "queryParams": {
            "region": "us-east-1"
        }
    })
)

result = json.loads(response['Payload'].read())
for profile in result['instanceProfiles']:
    print(f"{profile['instanceProfileName']}: {', '.join(profile['roles'])}")
```

**Error Responses**:
- `MISSING_PARAMETER`: region parameter is required
- `INTERNAL_ERROR`: Failed to retrieve instance profiles

---

### Account & Configuration Operations

#### get_current_account_id

Get the current AWS account ID.

**Operation**: `get_current_account_id`

**Parameters**: None

**Request Format**:
```json
{
  "operation": "get_current_account_id"
}
```

**Response Format**:
```json
{
  "accountId": "123456789012"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_current_account_id"}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_current_account_id"
    })
)

result = json.loads(response['Payload'].read())
print(f"Current Account ID: {result['accountId']}")
```

**Error Responses**:
- `INTERNAL_ERROR`: Failed to retrieve account ID

---

#### export_configuration

Export all Protection Groups and Recovery Plans for backup or migration.

**Operation**: `export_configuration`

**Parameters**: None

**Request Format**:
```json
{
  "operation": "export_configuration"
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
      "region": "us-east-1",
      "accountId": "123456789012",
      "sourceServerIds": ["s-server1", "s-server2"],
      "tags": {
        "Environment": "Production"
      }
    }
  ],
  "recoveryPlans": [
    {
      "planId": "plan-xyz789",
      "name": "Production DR Plan",
      "description": "Disaster recovery for production",
      "protectionGroupId": "pg-abc123",
      "waves": [
        {
          "waveNumber": 1,
          "name": "Database Tier",
          "launchOrder": 1
        }
      ]
    }
  ],
  "exportedAt": "2026-01-31T12:00:00Z",
  "version": "1.0"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"export_configuration"}' \
  response.json && cat response.json | jq . > config-backup.json
```

**Python boto3 Example**:
```python
import boto3
import json
from datetime import datetime

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "export_configuration"
    })
)

result = json.loads(response['Payload'].read())

# Save to file with timestamp
timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
filename = f'drs-config-backup-{timestamp}.json'
with open(filename, 'w') as f:
    json.dump(result, f, indent=2)

print(f"Configuration exported to {filename}")
print(f"Protection Groups: {len(result['protectionGroups'])}")
print(f"Recovery Plans: {len(result['recoveryPlans'])}")
```

**Error Responses**:
- `DYNAMODB_ERROR`: Failed to query configuration tables
- `INTERNAL_ERROR`: Failed to export configuration

---

### Phase 4 Operations (NEW)

#### get_server_launch_config

Get individual server launch configuration within a Protection Group.

**Operation**: `get_server_launch_config`

**Parameters**:
- `groupId` (required): Protection Group ID
- `serverId` (required): DRS source server ID

**Request Format**:
```json
{
  "operation": "get_server_launch_config",
  "groupId": "pg-abc123",
  "serverId": "s-1234567890abcdef0"
}
```

**Response Format**:
```json
{
  "serverId": "s-1234567890abcdef0",
  "useGroupDefaults": false,
  "launchConfiguration": {
    "instanceType": "c6a.xlarge",
    "subnetId": "subnet-456",
    "securityGroupIds": ["sg-789"],
    "iamInstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/EC2-SSM-Role"
  },
  "instanceId": "i-recovered123",
  "instanceName": "web-server-01-dr",
  "tags": {
    "Environment": "DR",
    "Application": "WebApp"
  }
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_server_launch_config","groupId":"pg-abc123","serverId":"s-1234567890abcdef0"}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_server_launch_config",
        "groupId": "pg-abc123",
        "serverId": "s-1234567890abcdef0"
    })
)

result = json.loads(response['Payload'].read())
if result.get('useGroupDefaults'):
    print(f"Server {result['serverId']} uses group default configuration")
else:
    print(f"Server {result['serverId']} has custom configuration:")
    print(f"  Instance Type: {result['launchConfiguration']['instanceType']}")
    print(f"  Subnet: {result['launchConfiguration']['subnetId']}")
```

**Error Responses**:
- `MISSING_PARAMETER`: groupId and serverId are required
- `NOT_FOUND`: Protection group or server not found
- `INTERNAL_ERROR`: Failed to retrieve server configuration

---

#### get_server_config_history

Get configuration change audit history for a specific server.

**Operation**: `get_server_config_history`

**Parameters**:
- `groupId` (required): Protection Group ID
- `serverId` (required): DRS source server ID

**Request Format**:
```json
{
  "operation": "get_server_config_history",
  "groupId": "pg-abc123",
  "serverId": "s-1234567890abcdef0"
}
```

**Response Format**:
```json
{
  "serverId": "s-1234567890abcdef0",
  "groupId": "pg-abc123",
  "history": [],
  "note": "Configuration history tracking is not yet implemented. This feature is planned for a future release."
}
```

**Future Response Format** (when implemented):
```json
{
  "serverId": "s-1234567890abcdef0",
  "groupId": "pg-abc123",
  "history": [
    {
      "timestamp": "2026-01-25T10:30:00Z",
      "user": "admin@example.com",
      "action": "UPDATE_LAUNCH_CONFIG",
      "changes": {
        "instanceType": {
          "old": "t3.medium",
          "new": "c6a.xlarge"
        },
        "subnetId": {
          "old": "subnet-123",
          "new": "subnet-456"
        }
      }
    }
  ]
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_server_config_history","groupId":"pg-abc123","serverId":"s-1234567890abcdef0"}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_server_config_history",
        "groupId": "pg-abc123",
        "serverId": "s-1234567890abcdef0"
    })
)

result = json.loads(response['Payload'].read())
if result.get('note'):
    print(f"Note: {result['note']}")
else:
    print(f"Configuration history for {result['serverId']}:")
    for entry in result['history']:
        print(f"  {entry['timestamp']}: {entry['action']} by {entry['user']}")
```

**Error Responses**:
- `MISSING_PARAMETER`: groupId and serverId are required
- `NOT_FOUND`: Protection group or server not found
- `INTERNAL_ERROR`: Failed to retrieve configuration history

---

#### get_staging_accounts

Get staging accounts configured for a target account.

**Operation**: `get_staging_accounts`

**Parameters**:
- `targetAccountId` (required): Target account ID (12-digit string)

**Request Format**:
```json
{
  "operation": "get_staging_accounts",
  "targetAccountId": "123456789012"
}
```

**Response Format**:
```json
{
  "targetAccountId": "123456789012",
  "stagingAccounts": [
    {
      "accountId": "987654321098",
      "accountName": "Staging Account 1",
      "roleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationRole",
      "externalId": "unique-external-id",
      "replicatingServers": 25,
      "totalServers": 30,
      "status": "active"
    }
  ]
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_staging_accounts","targetAccountId":"123456789012"}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_staging_accounts",
        "targetAccountId": "123456789012"
    })
)

result = json.loads(response['Payload'].read())
print(f"Staging accounts for {result['targetAccountId']}:")
for account in result['stagingAccounts']:
    print(f"  - {account['accountName']} ({account['accountId']}): {account['replicatingServers']} servers")
```

**Error Responses**:
- `MISSING_PARAMETER`: targetAccountId is required
- `INVALID_PARAMETER`: Invalid account ID format (must be 12-digit string)
- `NOT_FOUND`: Target account not found
- `INTERNAL_ERROR`: Failed to retrieve staging accounts

---

#### get_tag_sync_status

Get current tag synchronization status.

**Operation**: `get_tag_sync_status`

**Parameters**: None

**Request Format**:
```json
{
  "operation": "get_tag_sync_status"
}
```

**Response Format**:
```json
{
  "enabled": false,
  "lastSyncTime": null,
  "serversProcessed": 0,
  "tagsSynchronized": 0,
  "status": "not_implemented",
  "note": "Tag synchronization is not yet implemented. This feature is planned for a future release."
}
```

**Future Response Format** (when implemented):
```json
{
  "enabled": true,
  "lastSyncTime": "2026-01-31T12:00:00Z",
  "serversProcessed": 150,
  "tagsSynchronized": 450,
  "errors": [],
  "nextScheduledSync": "2026-01-31T12:05:00Z",
  "status": "idle"
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_tag_sync_status"}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_tag_sync_status"
    })
)

result = json.loads(response['Payload'].read())
if result.get('enabled'):
    print(f"Tag Sync Status: {result['status']}")
    print(f"Last Sync: {result['lastSyncTime']}")
    print(f"Servers Processed: {result['serversProcessed']}")
else:
    print(f"Note: {result.get('note', 'Tag sync is disabled')}")
```

**Error Responses**:
- `INTERNAL_ERROR`: Failed to retrieve tag sync status

---

#### get_tag_sync_settings

Get tag synchronization configuration settings.

**Operation**: `get_tag_sync_settings`

**Parameters**: None

**Request Format**:
```json
{
  "operation": "get_tag_sync_settings"
}
```

**Response Format**:
```json
{
  "enabled": false,
  "schedule": null,
  "tagFilters": {
    "include": [],
    "exclude": []
  },
  "sourceAccounts": [],
  "targetAccounts": [],
  "note": "Tag synchronization is not yet implemented. This feature is planned for a future release."
}
```

**Future Response Format** (when implemented):
```json
{
  "enabled": true,
  "schedule": "rate(5 minutes)",
  "tagFilters": {
    "include": ["Environment", "Application", "Owner"],
    "exclude": ["aws:*", "Name"]
  },
  "sourceAccounts": ["123456789012"],
  "targetAccounts": ["987654321098"],
  "tagMappings": {
    "Environment": "DR-Environment",
    "Application": "DR-Application"
  }
}
```

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_tag_sync_settings"}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_tag_sync_settings"
    })
)

result = json.loads(response['Payload'].read())
if result.get('enabled'):
    print(f"Tag Sync Schedule: {result['schedule']}")
    print(f"Include Tags: {', '.join(result['tagFilters']['include'])}")
    print(f"Exclude Tags: {', '.join(result['tagFilters']['exclude'])}")
else:
    print(f"Note: {result.get('note', 'Tag sync is disabled')}")
```

**Error Responses**:
- `INTERNAL_ERROR`: Failed to retrieve tag sync settings

---

#### get_drs_capacity_conflicts

Get detected DRS capacity conflicts across accounts.

**Operation**: `get_drs_capacity_conflicts`

**Parameters**: None

**Request Format**:
```json
{
  "operation": "get_drs_capacity_conflicts"
}
```

**Response Format**:
```json
{
  "conflicts": [
    {
      "accountId": "123456789012",
      "accountName": "Production Account",
      "conflictType": "approaching_replication_limit",
      "severity": "warning",
      "currentUsage": 280,
      "limit": 300,
      "message": "Account is approaching replication limit (280/300 servers, 93.3%)"
    }
  ],
  "totalConflicts": 1
}
```

**Conflict Types**:
- `approaching_replication_limit`: Account >= 270 replicating servers (90% of 300 limit)
- `at_replication_limit`: Account >= 300 replicating servers (at hard limit)
- `approaching_recovery_limit`: Account >= 3600 total servers (90% of 4000 limit)
- `at_recovery_limit`: Account >= 4000 total servers (at hard limit)

**Severity Levels**:
- `info`: 80-89% of limit
- `warning`: 90-99% of limit
- `critical`: At or above limit

**AWS CLI Example**:
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_drs_capacity_conflicts"}' \
  response.json && cat response.json | jq .
```

**Python boto3 Example**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='aws-drs-orchestration-query-handler-test',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_capacity_conflicts"
    })
)

result = json.loads(response['Payload'].read())
print(f"Total Capacity Conflicts: {result['totalConflicts']}")
for conflict in result['conflicts']:
    print(f"\n{conflict['severity'].upper()}: {conflict['accountName']}")
    print(f"  Type: {conflict['conflictType']}")
    print(f"  Usage: {conflict['currentUsage']}/{conflict['limit']}")
    print(f"  Message: {conflict['message']}")
```

**Error Responses**:
- `INTERNAL_ERROR`: Failed to analyze capacity conflicts

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
| `MISSING_PARAMETER` | 400 | Required parameter missing | Add required parameter to queryParams |
| `INVALID_PARAMETER` | 400 | Parameter value is invalid | Check parameter format and constraints |
| `AUTHORIZATION_FAILED` | 403 | IAM principal not authorized | Verify IAM permissions for lambda:InvokeFunction |
| `NOT_FOUND` | 404 | Resource not found | Verify resource ID exists |
| `DRS_NOT_INITIALIZED` | 400 | DRS not initialized in region | Initialize DRS in AWS Console |
| `REGION_NOT_ENABLED` | 400 | Opt-in region not enabled | Enable region in AWS Account Settings |
| `DYNAMODB_ERROR` | 500 | DynamoDB operation failed | Check DynamoDB table status and permissions |
| `DRS_ERROR` | 500 | DRS API operation failed | Check DRS service status and permissions |
| `INTERNAL_ERROR` | 500 | Unexpected error occurred | Check CloudWatch Logs for details |

### Common Error Scenarios

#### DRS Not Initialized

**Error**:
```json
{
  "error": "DRS_NOT_INITIALIZED",
  "message": "AWS Elastic Disaster Recovery (DRS) is not initialized in us-east-1...",
  "region": "us-east-1",
  "initialized": false
}
```

**Resolution**:
1. Open AWS DRS Console in the specified region
2. Complete the initialization wizard
3. Retry the operation

#### Region Not Enabled

**Error**:
```json
{
  "error": "REGION_NOT_ENABLED",
  "message": "Region ap-south-1 is not enabled in your AWS account...",
  "region": "ap-south-1",
  "initialized": false
}
```

**Resolution**:
1. Go to AWS Account Settings
2. Enable the opt-in region
3. Wait for region activation (may take a few minutes)
4. Initialize DRS in the region
5. Retry the operation

#### Authorization Failed

**Error**:
```json
{
  "error": "AUTHORIZATION_FAILED",
  "message": "IAM principal is not authorized to invoke this function",
  "principal": "arn:aws:iam::123456789012:role/MyRole"
}
```

**Resolution**:
1. Add `lambda:InvokeFunction` permission to IAM role/user
2. Verify Lambda resource-based policy allows invocation
3. Check IAM policy is attached to the principal

---

## Troubleshooting

### Enable Debug Logging

Set environment variable `DEBUG=true` on the Lambda function to enable detailed logging:

```bash
aws lambda update-function-configuration \
  --function-name aws-drs-orchestration-query-handler-test \
  --environment Variables={DEBUG=true}
```

### Check CloudWatch Logs

View Lambda execution logs:

```bash
aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-test --follow
```

### Test IAM Permissions

Verify your IAM principal can invoke the function:

```bash
aws lambda get-policy \
  --function-name aws-drs-orchestration-query-handler-test \
  --query 'Policy' \
  --output text | jq .
```

### Validate Event Format

Test with a simple operation first:

```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"get_current_account_id"}' \
  response.json && cat response.json
```

### Cross-Account Issues

If cross-account queries fail:

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

---

## Integration Examples

### Python Script - Query All Servers

```python
#!/usr/bin/env python3
"""
Query all DRS source servers across multiple regions.
"""
import boto3
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# DRS-enabled regions
DRS_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'eu-west-1', 'eu-west-2', 'eu-central-1',
    'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
    'ca-central-1', 'sa-east-1', 'ap-south-1', 'eu-north-1', 'eu-south-1'
]

def query_region(lambda_client, region):
    """Query DRS servers in a single region."""
    try:
        response = lambda_client.invoke(
            FunctionName='aws-drs-orchestration-query-handler-test',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                "operation": "get_drs_source_servers",
                "queryParams": {"region": region}
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if 'error' in result:
            return {'region': region, 'error': result['error'], 'servers': []}
        
        return {
            'region': region,
            'servers': result.get('servers', []),
            'count': result.get('serverCount', 0)
        }
    except Exception as e:
        return {'region': region, 'error': str(e), 'servers': []}

def main():
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    all_servers = []
    
    # Query all regions concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(query_region, lambda_client, region): region
            for region in DRS_REGIONS
        }
        
        for future in as_completed(futures):
            result = future.result()
            
            if result.get('error'):
                print(f"⚠️  {result['region']}: {result['error']}")
            elif result['count'] > 0:
                print(f"✓ {result['region']}: {result['count']} servers")
                all_servers.extend(result['servers'])
            else:
                print(f"  {result['region']}: No servers")
    
    print(f"\nTotal servers across all regions: {len(all_servers)}")
    
    # Export to JSON
    with open('drs-servers-inventory.json', 'w') as f:
        json.dump(all_servers, f, indent=2)
    
    print(f"Inventory exported to drs-servers-inventory.json")

if __name__ == '__main__':
    main()
```

### Bash Script - Capacity Monitoring

```bash
#!/bin/bash
# Monitor DRS capacity across all accounts

set -euo pipefail

FUNCTION_NAME="aws-drs-orchestration-query-handler-test"
OUTPUT_FILE="capacity-report-$(date +%Y%m%d-%H%M%S).json"

echo "Querying DRS capacity..."

# Get account-wide capacity
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload '{"operation":"get_drs_account_capacity_all_regions"}' \
  "$OUTPUT_FILE" > /dev/null

# Parse and display results
STATUS=$(jq -r '.status' "$OUTPUT_FILE")
TOTAL=$(jq -r '.totalSourceServers' "$OUTPUT_FILE")
REPLICATING=$(jq -r '.replicatingServers' "$OUTPUT_FILE")
AVAILABLE=$(jq -r '.availableReplicatingSlots' "$OUTPUT_FILE")

echo "================================"
echo "DRS Capacity Report"
echo "================================"
echo "Status: $STATUS"
echo "Total Servers: $TOTAL"
echo "Replicating: $REPLICATING"
echo "Available Slots: $AVAILABLE"
echo ""
echo "Regional Breakdown:"
echo "--------------------------------"

jq -r '.regionalBreakdown[] | "\(.region): \(.replicatingServers)/\(.maxReplicating) (\(.percentUsed)%) - \(.status)"' "$OUTPUT_FILE"

echo ""
echo "Full report saved to: $OUTPUT_FILE"

# Alert if critical
if [ "$STATUS" = "CRITICAL" ]; then
    echo "⚠️  ALERT: DRS capacity is CRITICAL!"
    exit 1
elif [ "$STATUS" = "WARNING" ]; then
    echo "⚠️  WARNING: DRS capacity approaching limit"
    exit 0
else
    echo "✓ Capacity OK"
    exit 0
fi
```

### Terraform Data Source

```hcl
# Query DRS source servers using Lambda invocation
data "aws_lambda_invocation" "drs_servers" {
  function_name = "aws-drs-orchestration-query-handler-test"

  input = jsonencode({
    operation = "get_drs_source_servers"
    queryParams = {
      region = "us-east-1"
    }
  })
}

# Parse response
locals {
  drs_servers = jsondecode(data.aws_lambda_invocation.drs_servers.result)
  server_ids  = [for server in local.drs_servers.servers : server.sourceServerID]
}

# Use server IDs in other resources
output "drs_server_count" {
  value = local.drs_servers.serverCount
}

output "drs_server_ids" {
  value = local.server_ids
}
```

### CloudWatch Events - Scheduled Capacity Check

```json
{
  "source": ["aws.events"],
  "detail-type": ["Scheduled Event"],
  "detail": {
    "operation": "get_drs_account_capacity_all_regions"
  }
}
```

EventBridge Rule:
```bash
aws events put-rule \
  --name drs-capacity-check \
  --schedule-expression "rate(1 hour)" \
  --state ENABLED

aws events put-targets \
  --rule drs-capacity-check \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123456789012:function:aws-drs-orchestration-query-handler-test"
```

---

## Performance Characteristics

### Execution Time

| Operation | Typical Duration | Notes |
|-----------|------------------|-------|
| `get_drs_source_servers` | 1-3 seconds | Single region query |
| `get_drs_account_capacity_all_regions` | 5-15 seconds | Concurrent multi-region query |
| `get_target_accounts` | < 1 second | DynamoDB scan |
| `get_ec2_subnets` | 1-2 seconds | EC2 API call |
| `export_configuration` | 2-5 seconds | Multiple DynamoDB scans |

### Concurrency

- **Max Concurrent Executions**: 1000 (default Lambda account limit)
- **Regional Queries**: Up to 10 regions queried concurrently
- **Recommended Rate**: < 100 requests/second for sustained load

### Caching

- **Capacity Data**: Cached for 30 seconds
- **DRS Server Lists**: No caching (always fresh)
- **Configuration Data**: No caching (always fresh)

### Memory & Timeout

- **Memory**: 256 MB (sufficient for read-only operations)
- **Timeout**: 60 seconds (sufficient for multi-region queries)
- **Cold Start**: < 2 seconds

---

## Related Documentation

- [Direct Lambda Invocation Mode Design](../../.kiro/specs/direct-lambda-invocation-mode/design.md)
- [Execution Handler API](./EXECUTION_HANDLER_API.md) (coming soon)
- [Data Management Handler API](./DATA_MANAGEMENT_HANDLER_API.md) (coming soon)
- [Developer Guide](../guides/DEVELOPER_GUIDE.md)

---

## Changelog

### Version 1.0 (2026-01-31)
- Initial API reference documentation
- Documented 16 query operations
- Added Phase 4 operations (6 new operations)
- Included AWS CLI and Python boto3 examples
- Added error codes and troubleshooting guide
- Provided integration examples

