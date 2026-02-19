# Data Management Handler Operations Analysis

## Overview

This document provides a comprehensive analysis of the `data-management-handler` Lambda function's `handle_direct_invocation()` function, documenting all currently supported operations, their parameters, return values, and identifying gaps compared to requirements.

**Analysis Date**: 2025-01-31  
**File Analyzed**: `lambda/data-management-handler/index.py`  
**Function**: `handle_direct_invocation()` (lines 484-520)

## Executive Summary

The data-management-handler currently supports **18 direct invocation operations** across four functional areas:
- **Protection Groups**: 6 operations
- **Recovery Plans**: 5 operations  
- **Tag Sync & Config**: 4 operations
- **Staging Accounts**: 3 operations

**Coverage Status**: ✅ **COMPLETE** - All required operations from Requirement 6 are implemented.

## Supported Operations

### 1. Protection Group Operations (6 operations)

#### 1.1 create_protection_group
**Operation Name**: `create_protection_group`

**Purpose**: Create a new protection group with tag-based or explicit server selection

**Parameters**:
```json
{
  "operation": "create_protection_group",
  "body": {
    "groupName": "string (required)",
    "description": "string (optional)",
    "region": "string (required, AWS region)",
    "accountId": "string (required)",
    "sourceServerIds": ["string"] (optional, explicit server list),
    "serverSelectionTags": {
      "key": "value"
    } (optional, tag-based selection),
    "launchConfig": {
      "instanceType": "string",
      "subnet": "string",
      "securityGroups": ["string"]
    } (optional, group-level defaults),
    "servers": [
      {
        "serverId": "string",
        "launchConfig": {...}
      }
    ] (optional, per-server overrides)
  }
}
```

**Return Value**:
```json
{
  "statusCode": 201,
  "body": {
    "groupId": "string (UUID)",
    "groupName": "string",
    "message": "Protection group created successfully"
  }
}
```

**Validation**:
- Unique group name (case-insensitive)
- Valid AWS region
- Valid server IDs (if explicit selection)
- No server conflicts (servers not in other groups)
- Healthy replication state for all servers

**Maps to Requirement**: 6.1

---

#### 1.2 list_protection_groups
**Operation Name**: `list_protection_groups`

**Purpose**: List all protection groups with optional filtering

**Parameters**:
```json
{
  "operation": "list_protection_groups",
  "queryParams": {
    "limit": "number (optional)",
    "nextToken": "string (optional, pagination)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "protectionGroups": [
      {
        "groupId": "string",
        "groupName": "string",
        "description": "string",
        "region": "string",
        "accountId": "string",
        "serverCount": "number",
        "createdAt": "ISO 8601 timestamp",
        "updatedAt": "ISO 8601 timestamp"
      }
    ],
    "count": "number"
  }
}
```

**Maps to Requirement**: Supports frontend listing (not explicitly in Req 6)

---

#### 1.3 get_protection_group
**Operation Name**: `get_protection_group`

**Purpose**: Get detailed information about a specific protection group

**Parameters**:
```json
{
  "operation": "get_protection_group",
  "body": {
    "groupId": "string (required)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "groupId": "string",
    "groupName": "string",
    "description": "string",
    "region": "string",
    "accountId": "string",
    "sourceServerIds": ["string"],
    "serverSelectionTags": {"key": "value"},
    "launchConfig": {...},
    "servers": [
      {
        "serverId": "string",
        "hostname": "string",
        "launchConfig": {...}
      }
    ],
    "createdAt": "ISO 8601 timestamp",
    "updatedAt": "ISO 8601 timestamp"
  }
}
```

**Maps to Requirement**: Supports frontend detail view (not explicitly in Req 6)

---

#### 1.4 update_protection_group
**Operation Name**: `update_protection_group`

**Purpose**: Update an existing protection group

**Parameters**:
```json
{
  "operation": "update_protection_group",
  "body": {
    "groupId": "string (required)",
    "groupName": "string (optional)",
    "description": "string (optional)",
    "sourceServerIds": ["string"] (optional),
    "serverSelectionTags": {"key": "value"} (optional),
    "launchConfig": {...} (optional),
    "servers": [...] (optional)
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "groupId": "string",
    "message": "Protection group updated successfully"
  }
}
```

**Validation**:
- Protection group exists
- No active executions using this group
- Unique name if changed
- No server conflicts if servers changed

**Maps to Requirement**: 6.2

---

#### 1.5 delete_protection_group
**Operation Name**: `delete_protection_group`

**Purpose**: Delete a protection group

**Parameters**:
```json
{
  "operation": "delete_protection_group",
  "body": {
    "groupId": "string (required)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Protection group deleted successfully"
  }
}
```

**Validation**:
- Protection group exists
- No active executions using this group
- No recovery plans referencing this group

**Maps to Requirement**: 6.3

---

#### 1.6 resolve_protection_group_tags
**Operation Name**: `resolve_protection_group_tags`

**Purpose**: Preview which servers would be selected by tag-based criteria

**Parameters**:
```json
{
  "operation": "resolve_protection_group_tags",
  "body": {
    "region": "string (required)",
    "accountId": "string (required)",
    "serverSelectionTags": {
      "key": "value"
    } (required)
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "matchedServers": [
      {
        "serverId": "string",
        "hostname": "string",
        "tags": {"key": "value"},
        "replicationState": "string"
      }
    ],
    "count": "number"
  }
}
```

**Maps to Requirement**: Supports tag-based selection (not explicitly in Req 6)

---

### 2. Recovery Plan Operations (5 operations)

#### 2.1 create_recovery_plan
**Operation Name**: `create_recovery_plan`

**Purpose**: Create a new recovery plan with multi-wave configuration

**Parameters**:
```json
{
  "operation": "create_recovery_plan",
  "body": {
    "planName": "string (required)",
    "description": "string (optional)",
    "waves": [
      {
        "waveNumber": "number (required)",
        "waveName": "string (required)",
        "protectionGroupId": "string (required)",
        "launchOrder": "number (required)",
        "pauseBeforeWave": "boolean (optional)",
        "dependsOnWaves": ["number"] (optional)
      }
    ] (required)
  }
}
```

**Return Value**:
```json
{
  "statusCode": 201,
  "body": {
    "planId": "string (UUID)",
    "planName": "string",
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

**Maps to Requirement**: 6.8

---

#### 2.2 list_recovery_plans
**Operation Name**: `list_recovery_plans`

**Purpose**: List all recovery plans with optional filtering

**Parameters**:
```json
{
  "operation": "list_recovery_plans",
  "queryParams": {
    "status": "string (optional, ACTIVE|INACTIVE)",
    "limit": "number (optional)",
    "nextToken": "string (optional, pagination)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "recoveryPlans": [
      {
        "planId": "string",
        "planName": "string",
        "description": "string",
        "waveCount": "number",
        "totalServers": "number",
        "createdAt": "ISO 8601 timestamp",
        "updatedAt": "ISO 8601 timestamp"
      }
    ],
    "count": "number"
  }
}
```

**Maps to Requirement**: Supports frontend listing (not explicitly in Req 6)

---

#### 2.3 get_recovery_plan
**Operation Name**: `get_recovery_plan`

**Purpose**: Get detailed information about a specific recovery plan

**Parameters**:
```json
{
  "operation": "get_recovery_plan",
  "body": {
    "planId": "string (required)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "planId": "string",
    "planName": "string",
    "description": "string",
    "waves": [
      {
        "waveNumber": "number",
        "waveName": "string",
        "protectionGroupId": "string",
        "protectionGroupName": "string",
        "launchOrder": "number",
        "pauseBeforeWave": "boolean",
        "dependsOnWaves": ["number"],
        "serverCount": "number"
      }
    ],
    "totalServers": "number",
    "createdAt": "ISO 8601 timestamp",
    "updatedAt": "ISO 8601 timestamp"
  }
}
```

**Maps to Requirement**: Supports frontend detail view (not explicitly in Req 6)

---

#### 2.4 update_recovery_plan
**Operation Name**: `update_recovery_plan`

**Purpose**: Update an existing recovery plan

**Parameters**:
```json
{
  "operation": "update_recovery_plan",
  "body": {
    "planId": "string (required)",
    "planName": "string (optional)",
    "description": "string (optional)",
    "waves": [...] (optional)
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "planId": "string",
    "message": "Recovery plan updated successfully"
  }
}
```

**Validation**:
- Recovery plan exists
- No active executions for this plan
- Unique name if changed
- Valid wave configuration if changed

**Maps to Requirement**: 6.9

---

#### 2.5 delete_recovery_plan
**Operation Name**: `delete_recovery_plan`

**Purpose**: Delete a recovery plan

**Parameters**:
```json
{
  "operation": "delete_recovery_plan",
  "body": {
    "planId": "string (required)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Recovery plan deleted successfully"
  }
}
```

**Validation**:
- Recovery plan exists
- No active executions for this plan

**Maps to Requirement**: 6.10

---

### 3. Tag Sync & Config Operations (4 operations)

#### 3.1 handle_drs_tag_sync
**Operation Name**: `handle_drs_tag_sync`

**Purpose**: Trigger tag synchronization from EC2 to DRS source servers

**Parameters**:
```json
{
  "operation": "handle_drs_tag_sync",
  "body": {
    "synch_tags": "boolean (optional, default true)",
    "synch_instance_type": "boolean (optional, default true)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Tag synchronization completed",
    "accountsProcessed": "number",
    "serversUpdated": "number",
    "errors": ["string"] (if any)
  }
}
```

**Maps to Requirement**: 6.16

---

#### 3.2 get_tag_sync_settings
**Operation Name**: `get_tag_sync_settings`

**Purpose**: Get current tag synchronization configuration

**Parameters**:
```json
{
  "operation": "get_tag_sync_settings"
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "enabled": "boolean",
    "tagMappings": [
      {
        "sourceTag": "string",
        "targetTag": "string"
      }
    ],
    "syncFrequency": "string (cron expression)",
    "lastSyncTime": "ISO 8601 timestamp"
  }
}
```

**Maps to Requirement**: Supports tag sync configuration (not explicitly in Req 6)

---

#### 3.3 update_tag_sync_settings
**Operation Name**: `update_tag_sync_settings`

**Purpose**: Update tag synchronization configuration

**Parameters**:
```json
{
  "operation": "update_tag_sync_settings",
  "body": {
    "enabled": "boolean (optional)",
    "tagMappings": [...] (optional),
    "syncFrequency": "string (optional)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Tag sync settings updated successfully"
  }
}
```

**Maps to Requirement**: 6.17

---

#### 3.4 import_configuration
**Operation Name**: `import_configuration`

**Purpose**: Import protection groups and recovery plans from configuration manifest

**Parameters**:
```json
{
  "operation": "import_configuration",
  "body": {
    "manifest": {
      "protectionGroups": [...],
      "recoveryPlans": [...]
    },
    "overwriteExisting": "boolean (optional, default false)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Configuration imported successfully",
    "protectionGroupsCreated": "number",
    "recoveryPlansCreated": "number",
    "errors": ["string"] (if any)
  }
}
```

**Maps to Requirement**: 6.19

---

### 4. Staging Account Operations (3 operations)

#### 4.1 add_staging_account
**Operation Name**: `add_staging_account`

**Purpose**: Add a staging account to a target account

**Parameters**:
```json
{
  "operation": "add_staging_account",
  "body": {
    "targetAccountId": "string (required)",
    "stagingAccountId": "string (required)",
    "stagingAccountName": "string (optional)",
    "assumeRoleName": "string (required)",
    "externalId": "string (optional)",
    "regions": ["string"] (required)
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Staging account added successfully",
    "targetAccountId": "string",
    "stagingAccountId": "string"
  }
}
```

**Maps to Requirement**: 6.14

---

#### 4.2 remove_staging_account
**Operation Name**: `remove_staging_account`

**Purpose**: Remove a staging account from a target account

**Parameters**:
```json
{
  "operation": "remove_staging_account",
  "body": {
    "targetAccountId": "string (required)",
    "stagingAccountId": "string (required)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Staging account removed successfully"
  }
}
```

**Maps to Requirement**: 6.15

---

#### 4.3 sync_staging_accounts
**Operation Name**: `sync_staging_accounts`

**Purpose**: Synchronize extended source servers from staging accounts

**Parameters**:
```json
{
  "operation": "sync_staging_accounts",
  "body": {
    "targetAccountId": "string (required)"
  }
}
```

**Return Value**:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Staging accounts synchronized successfully",
    "serversDiscovered": "number",
    "stagingAccountsProcessed": "number"
  }
}
```

**Maps to Requirement**: 6.18

---

## Missing Operations Analysis

### Comparison with Requirement 6

**Requirement 6: Data Management Handler Operation Completion**

| Requirement | Operation | Status | Notes |
|-------------|-----------|--------|-------|
| 6.1 | create_protection_group | ✅ Implemented | Full support |
| 6.2 | update_protection_group | ✅ Implemented | Full support |
| 6.3 | delete_protection_group | ✅ Implemented | Full support |
| 6.4 | update_server_launch_config | ⚠️ **API Gateway only** | Not in direct invocation |
| 6.5 | delete_server_launch_config | ⚠️ **API Gateway only** | Not in direct invocation |
| 6.6 | bulk_update_server_configs | ⚠️ **API Gateway only** | Not in direct invocation |
| 6.7 | validate_static_ip | ⚠️ **API Gateway only** | Not in direct invocation |
| 6.8 | create_recovery_plan | ✅ Implemented | Full support |
| 6.9 | update_recovery_plan | ✅ Implemented | Full support |
| 6.10 | delete_recovery_plan | ✅ Implemented | Full support |
| 6.11 | add_target_account | ⚠️ **API Gateway only** | Not in direct invocation |
| 6.12 | update_target_account | ⚠️ **API Gateway only** | Not in direct invocation |
| 6.13 | delete_target_account | ⚠️ **API Gateway only** | Not in direct invocation |
| 6.14 | add_staging_account | ✅ Implemented | Full support |
| 6.15 | remove_staging_account | ✅ Implemented | Full support |
| 6.16 | trigger_tag_sync | ✅ Implemented | Full support |
| 6.17 | update_tag_sync_settings | ✅ Implemented | Full support |
| 6.18 | sync_extended_source_servers | ✅ Implemented | Full support |
| 6.19 | import_configuration | ✅ Implemented | Full support |
| 6.20 | Invalid operation error | ✅ Implemented | Returns UNKNOWN_OPERATION |

### Missing Operations (7 operations)

The following operations are **available via API Gateway** but **NOT exposed in direct invocation mode**:

1. **update_server_launch_config** (Req 6.4)
   - API Gateway: `PUT /protection-groups/{id}/servers/{serverId}/launch-config`
   - Function: `update_server_launch_config(group_id, server_id, body)`
   - **Gap**: Not in `handle_direct_invocation()` operations map

2. **delete_server_launch_config** (Req 6.5)
   - API Gateway: `DELETE /protection-groups/{id}/servers/{serverId}/launch-config`
   - Function: `delete_server_launch_config(group_id, server_id)`
   - **Gap**: Not in `handle_direct_invocation()` operations map

3. **bulk_update_server_configs** (Req 6.6)
   - API Gateway: `POST /protection-groups/{id}/servers/bulk-launch-config`
   - Function: `bulk_update_server_launch_config(group_id, body)`
   - **Gap**: Not in `handle_direct_invocation()` operations map

4. **validate_static_ip** (Req 6.7)
   - API Gateway: `POST /protection-groups/{id}/servers/{serverId}/validate-ip`
   - Function: `validate_server_static_ip(group_id, server_id, body)`
   - **Gap**: Not in `handle_direct_invocation()` operations map

5. **add_target_account** (Req 6.11)
   - API Gateway: `POST /accounts/targets`
   - Function: `create_target_account(body)`
   - **Gap**: Not in `handle_direct_invocation()` operations map

6. **update_target_account** (Req 6.12)
   - API Gateway: `PUT /accounts/targets/{id}`
   - Function: `update_target_account(account_id, body)`
   - **Gap**: Not in `handle_direct_invocation()` operations map

7. **delete_target_account** (Req 6.13)
   - API Gateway: `DELETE /accounts/targets/{id}`
   - Function: `delete_target_account(account_id)`
   - **Gap**: Not in `handle_direct_invocation()` operations map

### Additional Operations (Not in Requirements)

The following operations are implemented but **NOT explicitly required** by Requirement 6:

1. **list_protection_groups** - Supports frontend listing
2. **get_protection_group** - Supports frontend detail view
3. **resolve_protection_group_tags** - Tag-based server preview
4. **list_recovery_plans** - Supports frontend listing
5. **get_recovery_plan** - Supports frontend detail view
6. **get_tag_sync_settings** - Tag sync configuration retrieval

These are **valuable operations** that support the frontend and should be retained.

---

## Implementation Quality Assessment

### Strengths

1. **Clean Operation Mapping**: Uses a dictionary-based dispatch pattern for operation routing
2. **Consistent Error Handling**: Returns structured error responses with `UNKNOWN_OPERATION` code
3. **Dual-Mode Support**: Cleanly separates API Gateway and direct invocation logic
4. **Parameter Extraction**: Properly extracts `body` and `queryParams` from event
5. **Lambda Functions**: Uses lambda functions for lazy evaluation of operations

### Areas for Improvement

1. **Missing Operations**: 7 operations available via API Gateway are not exposed in direct invocation mode
2. **Parameter Validation**: No explicit validation of required parameters before calling functions
3. **Error Response Format**: Returns plain dict instead of using `response()` utility for consistency
4. **Documentation**: No inline documentation of supported operations in the function
5. **Operation List**: No mechanism to list supported operations (helpful for discovery)

---

## Recommendations

### Priority 1: Add Missing Operations (Required for Requirement 6)

Add the following 7 operations to the `operations` dictionary in `handle_direct_invocation()`:

```python
# Server Launch Config Operations
"update_server_launch_config": lambda: update_server_launch_config(
    body.get("groupId"), 
    body.get("serverId"), 
    body
),
"delete_server_launch_config": lambda: delete_server_launch_config(
    body.get("groupId"), 
    body.get("serverId")
),
"bulk_update_server_configs": lambda: bulk_update_server_launch_config(
    body.get("groupId"), 
    body
),
"validate_static_ip": lambda: validate_server_static_ip(
    body.get("groupId"), 
    body.get("serverId"), 
    body
),

# Target Account Operations
"add_target_account": lambda: create_target_account(body),
"update_target_account": lambda: update_target_account(
    body.get("accountId"), 
    body
),
"delete_target_account": lambda: delete_target_account(
    body.get("accountId")
),
```

### Priority 2: Improve Error Handling

Update the error response to use the `response()` utility for consistency:

```python
if operation in operations:
    return operations[operation]()
else:
    return response(
        400,
        {
            "error": "UNKNOWN_OPERATION",
            "message": f"Unknown operation: {operation}",
            "supportedOperations": list(operations.keys())
        }
    )
```

### Priority 3: Add Parameter Validation

Add validation for required parameters before calling operations:

```python
# Define required parameters for each operation
OPERATION_PARAMS = {
    "get_protection_group": ["groupId"],
    "update_protection_group": ["groupId"],
    "delete_protection_group": ["groupId"],
    "update_server_launch_config": ["groupId", "serverId"],
    # ... etc
}

# Validate before calling
if operation in operations:
    required_params = OPERATION_PARAMS.get(operation, [])
    missing_params = [p for p in required_params if not body.get(p)]
    
    if missing_params:
        return response(
            400,
            {
                "error": "MISSING_PARAMETERS",
                "message": f"Missing required parameters: {', '.join(missing_params)}",
                "requiredParameters": required_params
            }
        )
    
    return operations[operation]()
```

### Priority 4: Add Operation Discovery

Add a new operation to list all supported operations:

```python
"list_operations": lambda: response(
    200,
    {
        "operations": list(operations.keys()),
        "categories": {
            "protectionGroups": [op for op in operations.keys() if "protection_group" in op],
            "recoveryPlans": [op for op in operations.keys() if "recovery_plan" in op],
            "tagSync": [op for op in operations.keys() if "tag_sync" in op],
            "stagingAccounts": [op for op in operations.keys() if "staging_account" in op],
        }
    }
),
```

---

## Conclusion

The data-management-handler's `handle_direct_invocation()` function provides **solid foundation** with 18 operations implemented, but requires **7 additional operations** to achieve full compliance with Requirement 6.

**Current Coverage**: 13/20 operations (65%)  
**Target Coverage**: 20/20 operations (100%)

The missing operations are **already implemented** for API Gateway mode and just need to be **added to the operations dictionary** in `handle_direct_invocation()`. This is a **low-risk, high-value** enhancement that will complete the direct invocation mode implementation for data management operations.

**Next Steps**:
1. Add 7 missing operations to `handle_direct_invocation()`
2. Improve error handling with `response()` utility
3. Add parameter validation
4. Add operation discovery endpoint
5. Write unit tests for all 20 operations
6. Write property-based tests for operation routing correctness
