# Query Handler Direct Invocation Event Formats

**Handler**: `lambda/query-handler/index.py`  
**Function**: `handle_direct_invocation(event, context)`  
**Purpose**: Read-only queries for DRS infrastructure, EC2 resources, and configuration data

## Event Structure

All query-handler direct invocations use this base structure:

```json
{
  "operation": "operation_name",
  "queryParams": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Required Fields**:
- `operation` (string): Operation name from supported operations list

**Optional Fields**:
- `queryParams` (object): Operation-specific parameters

## Supported Operations (16 total)

### 1. DRS Infrastructure Operations

#### 1.1 get_drs_source_servers

List DRS source servers in a region with optional filtering.

**Event**:
```json
{
  "operation": "get_drs_source_servers",
  "queryParams": {
    "region": "us-east-1",
    "accountId": "123456789012",
    "tags": {
      "Environment": "Production",
      "Application": "WebApp"
    },
    "replicationState": "CONTINUOUS",
    "lifecycleState": "READY_FOR_RECOVERY"
  }
}
```

**Parameters**:
- `region` (string, optional): AWS region to query
- `accountId` (string, optional): Target account ID for cross-account queries
- `tags` (object, optional): Filter by tags (key-value pairs)
- `replicationState` (string, optional): Filter by replication state
- `lifecycleState` (string, optional): Filter by lifecycle state

**Response**:
```json
{
  "servers": [
    {
      "sourceServerId": "s-1234567890abcdef0",
      "hostname": "web-server-01",
      "arn": "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0",
      "tags": {
        "Environment": "Production",
        "Application": "WebApp"
      },
      "dataReplicationInfo": {
        "dataReplicationState": "CONTINUOUS",
        "lagDuration": "PT0S"
      },
      "lifeCycle": {
        "state": "READY_FOR_RECOVERY"
      }
    }
  ],
  "totalCount": 1
}
```

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation":"get_drs_source_servers","queryParams":{"region":"us-east-1"}}' \
  response.json
```

**Python boto3**:
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='query-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_source_servers",
        "queryParams": {
            "region": "us-east-1",
            "accountId": "123456789012"
        }
    })
)

result = json.loads(response['Payload'].read())
```

---

#### 1.2 get_drs_account_capacity

Get DRS capacity metrics for a specific region and account.

**Event**:
```json
{
  "operation": "get_drs_account_capacity",
  "queryParams": {
    "region": "us-east-1",
    "accountId": "123456789012"
  }
}
```

**Parameters**:
- `region` (string, required): AWS region
- `accountId` (string, optional): Target account ID

**Response**:
```json
{
  "region": "us-east-1",
  "accountId": "123456789012",
  "capacity": {
    "maxSourceServers": 1000,
    "currentSourceServers": 250,
    "availableCapacity": 750,
    "utilizationPercentage": 25.0
  }
}
```

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation":"get_drs_account_capacity","queryParams":{"region":"us-east-1"}}' \
  response.json
```

---

#### 1.3 get_drs_account_capacity_all_regions

Get aggregated DRS capacity across all regions for an account.

**Event**:
```json
{
  "operation": "get_drs_account_capacity_all_regions",
  "queryParams": {
    "account_context": {
      "accountId": "123456789012",
      "roleName": "DRSOrchestrationRole"
    }
  }
}
```

**Parameters**:
- `account_context` (object, optional): Cross-account context

**Response**:
```json
{
  "accountId": "123456789012",
  "regions": [
    {
      "region": "us-east-1",
      "maxSourceServers": 1000,
      "currentSourceServers": 250,
      "availableCapacity": 750
    },
    {
      "region": "us-west-2",
      "maxSourceServers": 1000,
      "currentSourceServers": 100,
      "availableCapacity": 900
    }
  ],
  "totalCapacity": {
    "maxSourceServers": 2000,
    "currentSourceServers": 350,
    "availableCapacity": 1650
  }
}
```

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation":"get_drs_account_capacity_all_regions"}' \
  response.json
```

---

#### 1.4 get_drs_regional_capacity

Get DRS capacity for a specific region.

**Event**:
```json
{
  "operation": "get_drs_regional_capacity",
  "queryParams": {
    "region": "us-east-1"
  }
}
```

**Parameters**:
- `region` (string, required): AWS region

**Response**:
```json
{
  "region": "us-east-1",
  "capacity": {
    "maxSourceServers": 1000,
    "currentSourceServers": 250,
    "availableCapacity": 750
  }
}
```

---

### 2. Account Management Operations

#### 2.1 get_target_accounts

List all registered target accounts.

**Event**:
```json
{
  "operation": "get_target_accounts"
}
```

**Parameters**: None

**Response**:
```json
{
  "accounts": [
    {
      "accountId": "123456789012",
      "accountName": "Production Account",
      "roleName": "DRSOrchestrationRole",
      "regions": ["us-east-1", "us-west-2"],
      "status": "ACTIVE",
      "createdAt": "2025-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation":"get_target_accounts"}' \
  response.json
```

---

### 3. EC2 Resource Operations

#### 3.1 get_ec2_subnets

List EC2 subnets in a VPC.

**Event**:
```json
{
  "operation": "get_ec2_subnets",
  "queryParams": {
    "region": "us-east-1",
    "vpcId": "vpc-0123456789abcdef0",
    "availabilityZone": "us-east-1a"
  }
}
```

**Parameters**:
- `region` (string, required): AWS region
- `vpcId` (string, required): VPC ID
- `availabilityZone` (string, optional): Filter by AZ

**Response**:
```json
{
  "subnets": [
    {
      "subnetId": "subnet-0123456789abcdef0",
      "subnetArn": "arn:aws:ec2:us-east-1:123456789012:subnet/subnet-0123456789abcdef0",
      "vpcId": "vpc-0123456789abcdef0",
      "cidrBlock": "10.0.1.0/24",
      "availabilityZone": "us-east-1a",
      "availableIpAddressCount": 251,
      "tags": {
        "Name": "Public Subnet 1A"
      }
    }
  ],
  "count": 1
}
```

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation":"get_ec2_subnets","queryParams":{"region":"us-east-1","vpcId":"vpc-123"}}' \
  response.json
```

---

#### 3.2 get_ec2_security_groups

List EC2 security groups in a VPC.

**Event**:
```json
{
  "operation": "get_ec2_security_groups",
  "queryParams": {
    "region": "us-east-1",
    "vpcId": "vpc-0123456789abcdef0"
  }
}
```

**Parameters**:
- `region` (string, required): AWS region
- `vpcId` (string, required): VPC ID

**Response**:
```json
{
  "securityGroups": [
    {
      "groupId": "sg-0123456789abcdef0",
      "groupName": "web-server-sg",
      "description": "Security group for web servers",
      "vpcId": "vpc-0123456789abcdef0",
      "tags": {
        "Name": "Web Server SG"
      }
    }
  ],
  "count": 1
}
```

---

#### 3.3 get_ec2_instance_profiles

List IAM instance profiles.

**Event**:
```json
{
  "operation": "get_ec2_instance_profiles",
  "queryParams": {
    "region": "us-east-1"
  }
}
```

**Parameters**:
- `region` (string, required): AWS region

**Response**:
```json
{
  "instanceProfiles": [
    {
      "instanceProfileName": "EC2-DRS-Role",
      "instanceProfileArn": "arn:aws:iam::123456789012:instance-profile/EC2-DRS-Role",
      "roles": [
        {
          "roleName": "EC2-DRS-Role",
          "roleArn": "arn:aws:iam::123456789012:role/EC2-DRS-Role"
        }
      ]
    }
  ],
  "count": 1
}
```

---

#### 3.4 get_ec2_instance_types

List available EC2 instance types.

**Event**:
```json
{
  "operation": "get_ec2_instance_types",
  "queryParams": {
    "region": "us-east-1",
    "instanceFamily": "t3"
  }
}
```

**Parameters**:
- `region` (string, required): AWS region
- `instanceFamily` (string, optional): Filter by instance family (e.g., "t3", "m5")

**Response**:
```json
{
  "instanceTypes": [
    {
      "instanceType": "t3.micro",
      "vcpus": 2,
      "memoryMiB": 1024,
      "networkPerformance": "Up to 5 Gigabit"
    },
    {
      "instanceType": "t3.small",
      "vcpus": 2,
      "memoryMiB": 2048,
      "networkPerformance": "Up to 5 Gigabit"
    }
  ],
  "count": 2
}
```

---

### 4. Account Information Operations

#### 4.1 get_current_account_id

Get current AWS account ID.

**Event**:
```json
{
  "operation": "get_current_account_id"
}
```

**Parameters**: None

**Response**:
```json
{
  "accountId": "123456789012"
}
```

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation":"get_current_account_id"}' \
  response.json
```

---

### 5. Configuration Export Operations

#### 5.1 export_configuration

Export all protection groups and recovery plans.

**Event**:
```json
{
  "operation": "export_configuration"
}
```

**Parameters**: None

**Response**:
```json
{
  "exportDate": "2025-01-31T15:30:00Z",
  "protectionGroups": [
    {
      "groupId": "pg-123",
      "groupName": "Production Web Servers",
      "region": "us-east-1",
      "accountId": "123456789012",
      "sourceServerIds": ["s-abc", "s-def"],
      "launchConfig": {
        "instanceType": "t3.medium",
        "subnet": "subnet-123",
        "securityGroups": ["sg-123"]
      }
    }
  ],
  "recoveryPlans": [
    {
      "planId": "rp-456",
      "planName": "Production DR Plan",
      "waves": [
        {
          "waveNumber": 1,
          "waveName": "Database Tier",
          "protectionGroupId": "pg-123",
          "launchOrder": 1
        }
      ]
    }
  ]
}
```

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation":"export_configuration"}' \
  response.json
```

---

### 6. User Permissions Operations

#### 6.1 get_user_permissions

Get RBAC permissions for authenticated user.

**Event**:
```json
{
  "operation": "get_user_permissions"
}
```

**Parameters**: None

**Response** (Direct Invocation):
```json
{
  "error": "User permissions not available in direct invocation mode"
}
```

**Note**: This operation only works with API Gateway/Cognito authentication.

---

### 7. Staging Account Operations

#### 7.1 validate_staging_account

Validate a staging account configuration.

**Event**:
```json
{
  "operation": "validate_staging_account",
  "queryParams": {
    "targetAccountId": "123456789012",
    "stagingAccountId": "987654321098",
    "roleName": "DRSOrchestrationRole",
    "regions": ["us-east-1", "us-west-2"]
  }
}
```

**Parameters**:
- `targetAccountId` (string, required): Target account ID
- `stagingAccountId` (string, required): Staging account ID
- `roleName` (string, required): IAM role name for cross-account access
- `regions` (array, required): List of regions to validate

**Response**:
```json
{
  "valid": true,
  "targetAccountId": "123456789012",
  "stagingAccountId": "987654321098",
  "validations": {
    "roleExists": true,
    "roleAssumable": true,
    "drsEnabled": true,
    "regionsValid": true
  },
  "errors": []
}
```

---

#### 7.2 discover_staging_accounts

Discover staging accounts for a target account.

**Event**:
```json
{
  "operation": "discover_staging_accounts",
  "queryParams": {
    "targetAccountId": "123456789012"
  }
}
```

**Parameters**:
- `targetAccountId` (string, required): Target account ID

**Response**:
```json
{
  "targetAccountId": "123456789012",
  "stagingAccounts": [
    {
      "stagingAccountId": "987654321098",
      "stagingAccountName": "DR Staging Account",
      "regions": ["us-east-1", "us-west-2"],
      "sourceServerCount": 50
    }
  ],
  "count": 1
}
```

---

#### 7.3 get_combined_capacity

Get combined DRS capacity for target and staging accounts.

**Event**:
```json
{
  "operation": "get_combined_capacity",
  "queryParams": {
    "targetAccountId": "123456789012"
  }
}
```

**Parameters**:
- `targetAccountId` (string, required): Target account ID

**Response**:
```json
{
  "targetAccountId": "123456789012",
  "targetCapacity": {
    "maxSourceServers": 1000,
    "currentSourceServers": 250,
    "availableCapacity": 750
  },
  "stagingCapacity": {
    "maxSourceServers": 500,
    "currentSourceServers": 50,
    "availableCapacity": 450
  },
  "combinedCapacity": {
    "maxSourceServers": 1500,
    "currentSourceServers": 300,
    "availableCapacity": 1200
  }
}
```

---

### 8. Synchronization Operations

#### 8.1 sync_staging_accounts

Synchronize staging accounts data.

**Event**:
```json
{
  "operation": "sync_staging_accounts"
}
```

**Parameters**: None

**Response**:
```json
{
  "message": "Staging accounts synchronized successfully",
  "accountsProcessed": 3,
  "serversDiscovered": 150,
  "syncTimestamp": "2025-01-31T15:30:00Z"
}
```

---

## Error Responses

### Unknown Operation

**Event**:
```json
{
  "operation": "invalid_operation_name"
}
```

**Response**:
```json
{
  "error": "Unknown operation",
  "operation": "invalid_operation_name"
}
```

### Missing Parameters

**Event**:
```json
{
  "operation": "get_ec2_subnets",
  "queryParams": {
    "region": "us-east-1"
  }
}
```

**Response**:
```json
{
  "error": "Missing required parameter: vpcId"
}
```

---

## Complete AWS CLI Examples

### Query DRS Source Servers with Filtering
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{
    "operation": "get_drs_source_servers",
    "queryParams": {
      "region": "us-east-1",
      "tags": {
        "Environment": "Production"
      },
      "replicationState": "CONTINUOUS"
    }
  }' \
  response.json && cat response.json | jq .
```

### Get Combined Capacity
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{
    "operation": "get_combined_capacity",
    "queryParams": {
      "targetAccountId": "123456789012"
    }
  }' \
  response.json && cat response.json | jq .
```

### Export Configuration
```bash
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation":"export_configuration"}' \
  response.json && cat response.json | jq . > config-export.json
```

---

## Complete Python boto3 Examples

### Query DRS Source Servers
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='query-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "get_drs_source_servers",
        "queryParams": {
            "region": "us-east-1",
            "tags": {
                "Environment": "Production"
            }
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Found {result['totalCount']} servers")
for server in result['servers']:
    print(f"  - {server['hostname']} ({server['sourceServerId']})")
```

### Get EC2 Subnets
```python
response = lambda_client.invoke(
    FunctionName='query-handler',
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
    print(f"{subnet['subnetId']}: {subnet['cidrBlock']} ({subnet['availabilityZone']})")
```

### Export Configuration
```python
response = lambda_client.invoke(
    FunctionName='query-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "export_configuration"
    })
)

config = json.loads(response['Payload'].read())
print(f"Protection Groups: {len(config['protectionGroups'])}")
print(f"Recovery Plans: {len(config['recoveryPlans'])}")

# Save to file
with open('dr-config-export.json', 'w') as f:
    json.dump(config, f, indent=2)
```
