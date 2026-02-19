# Data Management Handler Direct Invocation Event Formats

**Handler**: `lambda/data-management-handler/index.py`  
**Function**: `handle_direct_invocation(event, context)`  
**Purpose**: CRUD operations for Protection Groups, Recovery Plans, Target Accounts, and Configuration

## Event Structure

All data-management-handler direct invocations use this base structure:

```json
{
  "operation": "operation_name",
  "body": {
    "param1": "value1",
    "param2": "value2"
  },
  "queryParams": {
    "filter1": "value1"
  }
}
```

**Required Fields**:
- `operation` (string): Operation name from supported operations list

**Optional Fields**:
- `body` (object): Request body for create/update operations
- `queryParams` (object): Query parameters for list/filter operations

## Supported Operations (18 total)

### 1. Protection Group Operations (6 operations)

#### 1.1 create_protection_group

Create a new protection group with tag-based or explicit server selection.

**Event**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "groupName": "Production Web Servers",
    "description": "Web tier servers for production environment",
    "region": "us-east-1",
    "accountId": "123456789012",
    "sourceServerIds": [
      "s-1234567890abcdef0",
      "s-1234567890abcdef1"
    ],
    "launchConfig": {
      "instanceType": "t3.medium",
      "subnet": "subnet-0123456789abcdef0",
      "securityGroups": ["sg-0123456789abcdef0"]
    },
    "servers": [
      {
        "serverId": "s-1234567890abcdef0",
        "launchConfig": {
          "instanceType": "t3.large"
        }
      }
    ]
  }
}
```

**Parameters**:
- `groupName` (string, required): Unique protection group name
- `description` (string, optional): Group description
- `region` (string, required): AWS region
- `accountId` (string, required): Target account ID
- `sourceServerIds` (array, optional): Explicit list of DRS source server IDs
- `serverSelectionTags` (object, optional): Tag-based server selection criteria
- `launchConfig` (object, optional): Group-level default launch configuration
- `servers` (array, optional): Per-server launch configuration overrides

**Response**:
```json
{
  "statusCode": 201,
  "body": {
    "groupId": "pg-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "groupName": "Production Web Servers",
    "message": "Protection group created successfully"
  }
}
```

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name data-management-handler \
  --payload '{
    "operation": "create_protection_group",
    "body": {
      "groupName": "Production Web Servers",
      "region": "us-east-1",
      "accountId": "123456789012",
      "sourceServerIds": ["s-abc", "s-def"]
    }
  }' \
  response.json
```

**Python boto3**:
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
    })
)

result = json.loads(response['Payload'].read())
print(f"Created group: {result['body']['groupId']}")
```

---

#### 1.2 list_protection_groups

List all protection groups with optional filtering.

**Event**:
```json
{
  "operation": "list_protection_groups",
  "queryParams": {
    "limit": 50,
    "nextToken": "eyJsYXN0RXZhbHVhdGVkS2V5Ijp7Imd..."
  }
}
```

**Parameters**:
- `limit` (number, optional): Maximum number of results (default: 50)
- `nextToken` (string, optional): Pagination token

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "protectionGroups": [
      {
        "groupId": "pg-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "groupName": "Production Web Servers",
        "description": "Web tier servers",
        "region": "us-east-1",
        "accountId": "123456789012",
        "serverCount": 5,
        "createdAt": "2025-01-15T10:30:00Z",
        "updatedAt": "2025-01-20T14:45:00Z"
      }
    ],
    "count": 1,
    "nextToken": null
  }
}
```

---

#### 1.3 get_protection_group

Get detailed information about a specific protection group.

**Event**:
```json
{
  "operation": "get_protection_group",
  "body": {
    "groupId": "pg-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

**Parameters**:
- `groupId` (string, required): Protection group ID

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "groupId": "pg-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "groupName": "Production Web Servers",
    "description": "Web tier servers",
    "region": "us-east-1",
    "accountId": "123456789012",
    "sourceServerIds": ["s-abc", "s-def"],
    "launchConfig": {
      "instanceType": "t3.medium",
      "subnet": "subnet-123",
      "securityGroups": ["sg-123"]
    },
    "servers": [
      {
        "serverId": "s-abc",
        "hostname": "web-01",
        "launchConfig": {
          "instanceType": "t3.large"
        }
      }
    ],
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-01-20T14:45:00Z"
  }
}
```

---

#### 1.4 update_protection_group

Update an existing protection group.

**Event**:
```json
{
  "operation": "update_protection_group",
  "body": {
    "groupId": "pg-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "groupName": "Production Web Servers - Updated",
    "description": "Updated description",
    "sourceServerIds": ["s-abc", "s-def", "s-ghi"],
    "launchConfig": {
      "instanceType": "t3.large"
    }
  }
}
```

**Parameters**:
- `groupId` (string, required): Protection group ID
- `groupName` (string, optional): New group name
- `description` (string, optional): New description
- `sourceServerIds` (array, optional): Updated server list
- `serverSelectionTags` (object, optional): Updated tag criteria
- `launchConfig` (object, optional): Updated launch configuration
- `servers` (array, optional): Updated per-server configurations

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "groupId": "pg-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message": "Protection group updated successfully"
  }
}
```

**Validation**:
- Protection group must exist
- No active executions using this group
- Unique name if changed
- No server conflicts if servers changed

---

#### 1.5 delete_protection_group

Delete a protection group.

**Event**:
```json
{
  "operation": "delete_protection_group",
  "body": {
    "groupId": "pg-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

**Parameters**:
- `groupId` (string, required): Protection group ID

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Protection group deleted successfully"
  }
}
```

**Validation**:
- Protection group must exist
- No active executions using this group
- No recovery plans referencing this group

---

#### 1.6 resolve_protection_group_tags

Preview which servers would be selected by tag-based criteria.

**Event**:
```json
{
  "operation": "resolve_protection_group_tags",
  "body": {
    "region": "us-east-1",
    "accountId": "123456789012",
    "serverSelectionTags": {
      "Environment": "Production",
      "Application": "WebApp"
    }
  }
}
```

**Parameters**:
- `region` (string, required): AWS region
- `accountId` (string, required): Target account ID
- `serverSelectionTags` (object, required): Tag criteria

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "matchedServers": [
      {
        "serverId": "s-abc",
        "hostname": "web-01",
        "tags": {
          "Environment": "Production",
          "Application": "WebApp"
        },
        "replicationState": "CONTINUOUS"
      }
    ],
    "count": 1
  }
}
```

---

### 2. Recovery Plan Operations (5 operations)

#### 2.1 create_recovery_plan

Create a new recovery plan with multi-wave configuration.

**Event**:
```json
{
  "operation": "create_recovery_plan",
  "body": {
    "planName": "Production DR Plan",
    "description": "Full production environment recovery",
    "waves": [
      {
        "waveNumber": 1,
        "waveName": "Database Tier",
        "protectionGroupId": "pg-database-tier",
        "launchOrder": 1,
        "pauseBeforeWave": false,
        "dependsOnWaves": []
      },
      {
        "waveNumber": 2,
        "waveName": "Application Tier",
        "protectionGroupId": "pg-app-tier",
        "launchOrder": 2,
        "pauseBeforeWave": true,
        "dependsOnWaves": [1]
      }
    ]
  }
}
```

**Parameters**:
- `planName` (string, required): Unique recovery plan name
- `description` (string, optional): Plan description
- `waves` (array, required): Wave configuration array
  - `waveNumber` (number, required): Wave sequence number
  - `waveName` (string, required): Wave display name
  - `protectionGroupId` (string, required): Protection group to recover
  - `launchOrder` (number, required): Launch order within wave
  - `pauseBeforeWave` (boolean, optional): Pause for manual approval
  - `dependsOnWaves` (array, optional): Wave dependencies

**Response**:
```json
{
  "statusCode": 201,
  "body": {
    "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "planName": "Production DR Plan",
    "message": "Recovery plan created successfully"
  }
}
```

**Validation**:
- Unique plan name (case-insensitive)
- Valid protection group IDs
- No circular wave dependencies
- Max 100 servers per wave (DRS limit)
- Valid wave numbers and launch orders

**AWS CLI**:
```bash
aws lambda invoke \
  --function-name data-management-handler \
  --payload '{
    "operation": "create_recovery_plan",
    "body": {
      "planName": "Production DR Plan",
      "waves": [
        {
          "waveNumber": 1,
          "waveName": "Database Tier",
          "protectionGroupId": "pg-database",
          "launchOrder": 1
        }
      ]
    }
  }' \
  response.json
```

---

#### 2.2 list_recovery_plans

List all recovery plans with optional filtering.

**Event**:
```json
{
  "operation": "list_recovery_plans",
  "queryParams": {
    "status": "ACTIVE",
    "limit": 50,
    "nextToken": null
  }
}
```

**Parameters**:
- `status` (string, optional): Filter by status (ACTIVE|INACTIVE)
- `limit` (number, optional): Maximum results
- `nextToken` (string, optional): Pagination token

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "recoveryPlans": [
      {
        "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "planName": "Production DR Plan",
        "description": "Full production recovery",
        "waveCount": 3,
        "totalServers": 25,
        "createdAt": "2025-01-15T10:30:00Z",
        "updatedAt": "2025-01-20T14:45:00Z"
      }
    ],
    "count": 1
  }
}
```

---

#### 2.3 get_recovery_plan

Get detailed information about a specific recovery plan.

**Event**:
```json
{
  "operation": "get_recovery_plan",
  "body": {
    "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901"
  }
}
```

**Parameters**:
- `planId` (string, required): Recovery plan ID

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "planName": "Production DR Plan",
    "description": "Full production recovery",
    "waves": [
      {
        "waveNumber": 1,
        "waveName": "Database Tier",
        "protectionGroupId": "pg-database",
        "protectionGroupName": "Production Databases",
        "launchOrder": 1,
        "pauseBeforeWave": false,
        "dependsOnWaves": [],
        "serverCount": 5
      }
    ],
    "totalServers": 25,
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-01-20T14:45:00Z"
  }
}
```

---

#### 2.4 update_recovery_plan

Update an existing recovery plan.

**Event**:
```json
{
  "operation": "update_recovery_plan",
  "body": {
    "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "planName": "Production DR Plan - Updated",
    "description": "Updated description",
    "waves": [
      {
        "waveNumber": 1,
        "waveName": "Database Tier",
        "protectionGroupId": "pg-database",
        "launchOrder": 1
      }
    ]
  }
}
```

**Parameters**:
- `planId` (string, required): Recovery plan ID
- `planName` (string, optional): New plan name
- `description` (string, optional): New description
- `waves` (array, optional): Updated wave configuration

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "message": "Recovery plan updated successfully"
  }
}
```

---

#### 2.5 delete_recovery_plan

Delete a recovery plan.

**Event**:
```json
{
  "operation": "delete_recovery_plan",
  "body": {
    "planId": "rp-b2c3d4e5-f6a7-8901-bcde-f12345678901"
  }
}
```

**Parameters**:
- `planId` (string, required): Recovery plan ID

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Recovery plan deleted successfully"
  }
}
```

---

### 3. Tag Sync & Config Operations (4 operations)

#### 3.1 handle_drs_tag_sync

Trigger tag synchronization from EC2 to DRS source servers.

**Event**:
```json
{
  "operation": "handle_drs_tag_sync",
  "body": {
    "synch_tags": true,
    "synch_instance_type": true
  }
}
```

**Parameters**:
- `synch_tags` (boolean, optional): Sync tags (default: true)
- `synch_instance_type` (boolean, optional): Sync instance type (default: true)

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Tag synchronization completed",
    "accountsProcessed": 3,
    "serversUpdated": 150,
    "errors": []
  }
}
```

---

#### 3.2 get_tag_sync_settings

Get current tag synchronization configuration.

**Event**:
```json
{
  "operation": "get_tag_sync_settings"
}
```

**Parameters**: None

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "enabled": true,
    "tagMappings": [
      {
        "sourceTag": "Environment",
        "targetTag": "Environment"
      }
    ],
    "syncFrequency": "0 */6 * * *",
    "lastSyncTime": "2025-01-31T12:00:00Z"
  }
}
```

---

#### 3.3 update_tag_sync_settings

Update tag synchronization configuration.

**Event**:
```json
{
  "operation": "update_tag_sync_settings",
  "body": {
    "enabled": true,
    "tagMappings": [
      {
        "sourceTag": "Environment",
        "targetTag": "Environment"
      }
    ],
    "syncFrequency": "0 */12 * * *"
  }
}
```

**Parameters**:
- `enabled` (boolean, optional): Enable/disable tag sync
- `tagMappings` (array, optional): Tag mapping configuration
- `syncFrequency` (string, optional): Cron expression

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Tag sync settings updated successfully"
  }
}
```

---

#### 3.4 import_configuration

Import protection groups and recovery plans from configuration manifest.

**Event**:
```json
{
  "operation": "import_configuration",
  "body": {
    "manifest": {
      "protectionGroups": [
        {
          "groupName": "Production Web Servers",
          "region": "us-east-1",
          "accountId": "123456789012",
          "sourceServerIds": ["s-abc", "s-def"]
        }
      ],
      "recoveryPlans": [
        {
          "planName": "Production DR Plan",
          "waves": [
            {
              "waveNumber": 1,
              "waveName": "Web Tier",
              "protectionGroupId": "pg-web",
              "launchOrder": 1
            }
          ]
        }
      ]
    },
    "overwriteExisting": false
  }
}
```

**Parameters**:
- `manifest` (object, required): Configuration manifest
  - `protectionGroups` (array): Protection groups to import
  - `recoveryPlans` (array): Recovery plans to import
- `overwriteExisting` (boolean, optional): Overwrite existing resources (default: false)

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Configuration imported successfully",
    "protectionGroupsCreated": 5,
    "recoveryPlansCreated": 2,
    "errors": []
  }
}
```

---

### 4. Staging Account Operations (3 operations)

#### 4.1 add_staging_account

Add a staging account to a target account.

**Event**:
```json
{
  "operation": "add_staging_account",
  "body": {
    "targetAccountId": "123456789012",
    "stagingAccountId": "987654321098",
    "stagingAccountName": "DR Staging Account",
    "assumeRoleName": "DRSOrchestrationRole",
    "externalId": "unique-external-id",
    "regions": ["us-east-1", "us-west-2"]
  }
}
```

**Parameters**:
- `targetAccountId` (string, required): Target account ID
- `stagingAccountId` (string, required): Staging account ID
- `stagingAccountName` (string, optional): Display name
- `assumeRoleName` (string, required): IAM role name
- `externalId` (string, optional): External ID for role assumption
- `regions` (array, required): List of regions

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Staging account added successfully",
    "targetAccountId": "123456789012",
    "stagingAccountId": "987654321098"
  }
}
```

---

#### 4.2 remove_staging_account

Remove a staging account from a target account.

**Event**:
```json
{
  "operation": "remove_staging_account",
  "body": {
    "targetAccountId": "123456789012",
    "stagingAccountId": "987654321098"
  }
}
```

**Parameters**:
- `targetAccountId` (string, required): Target account ID
- `stagingAccountId` (string, required): Staging account ID

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Staging account removed successfully"
  }
}
```

---

#### 4.3 sync_staging_accounts

Synchronize extended source servers from staging accounts.

**Event**:
```json
{
  "operation": "sync_staging_accounts",
  "body": {
    "targetAccountId": "123456789012"
  }
}
```

**Parameters**:
- `targetAccountId` (string, required): Target account ID

**Response**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Staging accounts synchronized successfully",
    "serversDiscovered": 50,
    "stagingAccountsProcessed": 2
  }
}
```

---

## Error Responses

### Unknown Operation

**Event**:
```json
{
  "operation": "invalid_operation"
}
```

**Response**:
```json
{
  "statusCode": 400,
  "body": {
    "error": "UNKNOWN_OPERATION",
    "message": "Unknown operation: invalid_operation"
  }
}
```

### Missing Required Parameters

**Event**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "groupName": "Test Group"
  }
}
```

**Response**:
```json
{
  "statusCode": 400,
  "body": {
    "error": "MISSING_PARAMETERS",
    "message": "Missing required parameters: region, accountId"
  }
}
```

### Validation Error

**Event**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "groupName": "Existing Group Name",
    "region": "us-east-1",
    "accountId": "123456789012"
  }
}
```

**Response**:
```json
{
  "statusCode": 400,
  "body": {
    "error": "VALIDATION_ERROR",
    "message": "Protection group with name 'Existing Group Name' already exists"
  }
}
```

---

## Complete Python boto3 Examples

### Create Protection Group with Tag-Based Selection
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
            "groupName": "Production Web Servers",
            "description": "Tag-based selection for web tier",
            "region": "us-east-1",
            "accountId": "123456789012",
            "serverSelectionTags": {
                "Environment": "Production",
                "Tier": "Web"
            },
            "launchConfig": {
                "instanceType": "t3.medium",
                "subnet": "subnet-123",
                "securityGroups": ["sg-123"]
            }
        }
    })
)

result = json.loads(response['Payload'].read())
if result['statusCode'] == 201:
    print(f"Created group: {result['body']['groupId']}")
else:
    print(f"Error: {result['body']['message']}")
```

### Create Multi-Wave Recovery Plan
```python
response = lambda_client.invoke(
    FunctionName='data-management-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "create_recovery_plan",
        "body": {
            "planName": "Production DR Plan",
            "description": "Full production environment recovery",
            "waves": [
                {
                    "waveNumber": 1,
                    "waveName": "Database Tier",
                    "protectionGroupId": "pg-database",
                    "launchOrder": 1,
                    "pauseBeforeWave": False
                },
                {
                    "waveNumber": 2,
                    "waveName": "Application Tier",
                    "protectionGroupId": "pg-app",
                    "launchOrder": 2,
                    "pauseBeforeWave": True,
                    "dependsOnWaves": [1]
                },
                {
                    "waveNumber": 3,
                    "waveName": "Web Tier",
                    "protectionGroupId": "pg-web",
                    "launchOrder": 3,
                    "pauseBeforeWave": False,
                    "dependsOnWaves": [2]
                }
            ]
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Created plan: {result['body']['planId']}")
```

### Import Configuration from File
```python
# Load configuration from file
with open('dr-config-export.json', 'r') as f:
    config = json.load(f)

response = lambda_client.invoke(
    FunctionName='data-management-handler',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "operation": "import_configuration",
        "body": {
            "manifest": config,
            "overwriteExisting": False
        }
    })
)

result = json.loads(response['Payload'].read())
print(f"Imported {result['body']['protectionGroupsCreated']} protection groups")
print(f"Imported {result['body']['recoveryPlansCreated']} recovery plans")
```
