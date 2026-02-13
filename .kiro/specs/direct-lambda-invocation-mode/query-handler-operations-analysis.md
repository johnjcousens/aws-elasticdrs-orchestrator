# Query Handler Direct Invocation Operations Analysis

**Task**: 1.1 - Analyze query-handler's handle_direct_invocation() function and document all supported operations

**Date**: January 31, 2026

**File Analyzed**: `lambda/query-handler/index.py`

**Function**: `handle_direct_invocation(event, context)` (lines 749-785)

## Summary

The query-handler Lambda function currently supports **16 direct invocation operations** through its `handle_direct_invocation()` function. All operations are read-only queries that retrieve DRS infrastructure data, EC2 resources, account information, and configuration exports.

## Supported Operations

### 1. DRS Infrastructure Operations (4 operations)

#### 1.1 `get_drs_source_servers`
- **Purpose**: List DRS source servers in a region
- **Parameters**: 
  - `region` (optional): AWS region to query
  - `accountId` (optional): Target account ID for cross-account queries
  - `tags` (optional): Filter by tags
  - `replicationState` (optional): Filter by replication state
  - `lifecycleState` (optional): Filter by lifecycle state
- **Returns**: List of DRS source servers with details
- **Function**: `get_drs_source_servers(query_params)`

#### 1.2 `get_drs_account_capacity`
- **Purpose**: Get DRS capacity for a specific region and account
- **Parameters**:
  - `region` (required): AWS region
  - `accountId` (optional): Target account ID
- **Returns**: DRS capacity metrics for the region
- **Function**: `get_drs_account_capacity(region, accountId)`

#### 1.3 `get_drs_account_capacity_all_regions`
- **Purpose**: Get DRS capacity across all regions for an account
- **Parameters**:
  - `account_context` (optional): Cross-account context
- **Returns**: Aggregated DRS capacity across all regions
- **Function**: `get_drs_account_capacity_all_regions(account_context)`

#### 1.4 `get_drs_regional_capacity`
- **Purpose**: Get DRS capacity for a specific region
- **Parameters**:
  - `region` (required): AWS region
- **Returns**: Regional DRS capacity metrics
- **Function**: `get_drs_regional_capacity(region)`

### 2. Account Management Operations (1 operation)

#### 2.1 `get_target_accounts`
- **Purpose**: List all registered target accounts
- **Parameters**: None
- **Returns**: List of target accounts with configuration
- **Function**: `get_target_accounts()`

### 3. EC2 Resource Operations (4 operations)

#### 3.1 `get_ec2_subnets`
- **Purpose**: List EC2 subnets in a VPC
- **Parameters**:
  - `region` (required): AWS region
  - `vpcId` (required): VPC ID
  - `availabilityZone` (optional): Filter by AZ
- **Returns**: List of subnets with details
- **Function**: `get_ec2_subnets(query_params)`

#### 3.2 `get_ec2_security_groups`
- **Purpose**: List EC2 security groups in a VPC
- **Parameters**:
  - `region` (required): AWS region
  - `vpcId` (required): VPC ID
- **Returns**: List of security groups
- **Function**: `get_ec2_security_groups(query_params)`

#### 3.3 `get_ec2_instance_profiles`
- **Purpose**: List IAM instance profiles
- **Parameters**:
  - `region` (required): AWS region
- **Returns**: List of instance profiles
- **Function**: `get_ec2_instance_profiles(query_params)`

#### 3.4 `get_ec2_instance_types`
- **Purpose**: List available EC2 instance types
- **Parameters**:
  - `region` (required): AWS region
  - `instanceFamily` (optional): Filter by instance family (e.g., "t3", "m5")
- **Returns**: List of instance types
- **Function**: `get_ec2_instance_types(query_params)`

### 4. Account Information Operations (1 operation)

#### 4.1 `get_current_account_id`
- **Purpose**: Get current AWS account ID
- **Parameters**: None
- **Returns**: `{"accountId": "123456789012"}`
- **Function**: Returns account ID directly

### 5. Configuration Export Operations (1 operation)

#### 5.1 `export_configuration`
- **Purpose**: Export all protection groups and recovery plans
- **Parameters**: None (query_params passed but not used)
- **Returns**: Complete configuration export with protection groups and recovery plans
- **Function**: `export_configuration(query_params)`

### 6. User Permissions Operations (1 operation)

#### 6.1 `get_user_permissions`
- **Purpose**: Get RBAC permissions for authenticated user
- **Parameters**: None
- **Returns**: `{"error": "User permissions not available in direct invocation mode"}`
- **Note**: This operation is NOT supported in direct invocation mode (only works with API Gateway/Cognito)

### 7. Staging Account Operations (3 operations)

#### 7.1 `validate_staging_account`
- **Purpose**: Validate a staging account configuration
- **Parameters**:
  - Account validation parameters (from query_params)
- **Returns**: Validation result
- **Function**: `handle_validate_staging_account(query_params)`

#### 7.2 `discover_staging_accounts`
- **Purpose**: Discover staging accounts for a target account
- **Parameters**:
  - `targetAccountId` (required): Target account ID
- **Returns**: List of discovered staging accounts
- **Function**: `handle_discover_staging_accounts(query_params)`

#### 7.3 `get_combined_capacity`
- **Purpose**: Get combined DRS capacity for target and staging accounts
- **Parameters**:
  - `targetAccountId` (required): Target account ID
- **Returns**: Combined capacity metrics
- **Function**: `handle_get_combined_capacity(query_params)`

### 8. Synchronization Operations (1 operation)

#### 8.1 `sync_staging_accounts`
- **Purpose**: Synchronize staging accounts data
- **Parameters**: None
- **Returns**: Synchronization result
- **Function**: `handle_sync_staging_accounts()`

## Event Format

### Direct Invocation Event Structure

```json
{
  "operation": "operation_name",
  "queryParams": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

### Example Events

#### Get DRS Source Servers
```json
{
  "operation": "get_drs_source_servers",
  "queryParams": {
    "region": "us-east-1",
    "accountId": "123456789012"
  }
}
```

#### Get Target Accounts
```json
{
  "operation": "get_target_accounts"
}
```

#### Get Combined Capacity
```json
{
  "operation": "get_combined_capacity",
  "queryParams": {
    "targetAccountId": "123456789012"
  }
}
```

## Response Format

### Success Response
Direct invocation returns raw data without API Gateway wrapping:

```json
{
  "servers": [...],
  "totalCount": 25
}
```

### Error Response
```json
{
  "error": "Unknown operation",
  "operation": "invalid_operation_name"
}
```

## Comparison with Requirements

### Requirements Coverage

From **Requirement 4: Query Handler Operation Completion**, the following operations are required:

| Requirement | Operation | Status |
|-------------|-----------|--------|
| 4.1 | list_protection_groups | ❌ **MISSING** |
| 4.2 | get_protection_group | ❌ **MISSING** |
| 4.3 | get_server_launch_config | ❌ **MISSING** |
| 4.4 | get_server_config_history | ❌ **MISSING** |
| 4.5 | list_recovery_plans | ❌ **MISSING** |
| 4.6 | get_recovery_plan | ❌ **MISSING** |
| 4.7 | list_executions | ❌ **MISSING** |
| 4.8 | get_execution | ❌ **MISSING** |
| 4.9 | get_drs_source_servers | ✅ **IMPLEMENTED** |
| 4.10 | get_target_accounts | ✅ **IMPLEMENTED** |
| 4.11 | get_staging_accounts | ✅ **IMPLEMENTED** (as `discover_staging_accounts`) |
| 4.12 | get_combined_capacity | ✅ **IMPLEMENTED** |
| 4.13 | get_all_accounts_capacity | ✅ **IMPLEMENTED** (as `get_drs_account_capacity_all_regions`) |
| 4.14 | get_tag_sync_status | ❌ **MISSING** |
| 4.15 | get_tag_sync_settings | ❌ **MISSING** |
| 4.16 | get_drs_capacity_conflicts | ❌ **MISSING** |

### Additional Operations (Not in Requirements)

The following operations are implemented but not explicitly mentioned in requirements:

1. `get_drs_account_capacity` - Regional capacity query
2. `get_drs_regional_capacity` - Regional capacity query (alternative)
3. `get_ec2_subnets` - EC2 subnet queries
4. `get_ec2_security_groups` - EC2 security group queries
5. `get_ec2_instance_profiles` - IAM instance profile queries
6. `get_ec2_instance_types` - EC2 instance type queries
7. `get_current_account_id` - Current account information
8. `export_configuration` - Configuration export
9. `get_user_permissions` - User RBAC permissions (not functional in direct mode)
10. `validate_staging_account` - Staging account validation
11. `sync_staging_accounts` - Staging account synchronization

## Missing Operations

Based on Requirement 4, the following operations need to be implemented:

### Protection Group Operations (2 operations)
1. **list_protection_groups** - List all protection groups
2. **get_protection_group** - Get specific protection group with launch configurations

### Server Launch Configuration Operations (2 operations)
3. **get_server_launch_config** - Get individual server launch configuration
4. **get_server_config_history** - Get configuration change audit history

### Recovery Plan Operations (2 operations)
5. **list_recovery_plans** - List all recovery plans
6. **get_recovery_plan** - Get specific recovery plan

### Execution Operations (2 operations)
7. **list_executions** - List all executions with optional filtering
8. **get_execution** - Get specific execution details

### Tag Synchronization Operations (2 operations)
9. **get_tag_sync_status** - Get current tag synchronization status
10. **get_tag_sync_settings** - Get tag synchronization configuration

### DRS Capacity Operations (1 operation)
11. **get_drs_capacity_conflicts** - Get detected capacity conflicts across accounts

## Implementation Notes

### Current Implementation Characteristics

1. **Dual Mode Support**: The function correctly detects and handles both API Gateway and direct invocation patterns
2. **Response Format Handling**: Automatically unwraps API Gateway response format for direct invocations
3. **Error Handling**: Returns simple error objects for unknown operations
4. **Parameter Passing**: Uses `queryParams` dictionary for all operation parameters
5. **Cross-Account Support**: Several operations support cross-account queries via `accountId` or `account_context` parameters

### Code Location

- **File**: `lambda/query-handler/index.py`
- **Function**: `handle_direct_invocation(event, context)`
- **Lines**: 749-785
- **Operations Dictionary**: Lines 755-772

### Related Functions

The `handle_direct_invocation()` function delegates to these handler functions:
- `get_drs_source_servers()`
- `get_drs_account_capacity()`
- `get_drs_account_capacity_all_regions()`
- `get_drs_regional_capacity()`
- `get_target_accounts()`
- `get_ec2_subnets()`
- `get_ec2_security_groups()`
- `get_ec2_instance_profiles()`
- `get_ec2_instance_types()`
- `get_current_account_id()`
- `export_configuration()`
- `handle_validate_staging_account()`
- `handle_discover_staging_accounts()`
- `handle_get_combined_capacity()`
- `handle_sync_staging_accounts()`

## Recommendations for Phase 3

To complete Requirement 4, the following operations should be added to `handle_direct_invocation()`:

1. Add operations dictionary entries for all 11 missing operations
2. Implement handler functions for each operation
3. Ensure consistent parameter naming (use `groupId`, `serverId`, `planId`, `executionId`)
4. Maintain consistent response format (raw data for direct invocation)
5. Add proper error handling for missing parameters
6. Update operation routing to include new operations

## Next Steps

1. ✅ **Task 1.1 Complete**: Query handler operations documented
2. **Task 1.2**: Analyze data-management-handler operations
3. **Task 1.3**: Analyze execution-handler operations
4. **Task 1.4**: Create comprehensive operation inventory spreadsheet
5. **Task 1.5**: Identify gaps between frontend features and Lambda implementations
