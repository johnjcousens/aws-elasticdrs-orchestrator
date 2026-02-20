# Handler Responsibilities

## Overview

This document defines the clear separation of responsibilities across the three Lambda handlers in the DR Orchestration Platform. This architecture ensures maintainability, testability, and adherence to the single responsibility principle.

## Handler Responsibility Pattern

```
data-management-handler: CRUD Operations + Data Sync
  ├── Protection Groups, Recovery Plans
  ├── Tag sync, Launch configs
  ├── Recovery instance sync
  ├── Source server inventory sync
  └── Staging account sync

execution-handler: Recovery Actions + Wave Completion Sync
  ├── Start recovery, Cancel execution
  ├── Terminate instances, Apply configs
  └── Wave completion sync

query-handler: Read Operations ONLY
  ├── List executions, Poll DRS jobs
  ├── Server status, Dashboard data
  ├── NO WRITES, NO SYNC OPERATIONS
  └── Audit logging for all read operations
```

## Data Management Handler

**Purpose**: Manage all CRUD operations and data synchronization tasks.

### Responsibilities

**Protection Group Management**:
- Create, update, delete protection groups
- Validate protection group configurations
- Resolve servers from tags
- Check protection group quotas

**Recovery Plan Management**:
- Create, update, delete recovery plans
- Validate recovery plan configurations
- Manage wave configurations
- Handle plan versioning

**Launch Configuration Management**:
- Create, update launch configurations
- Validate launch settings
- Merge configurations (global, group, server-level)

**Data Synchronization**:
- Source server inventory sync (EventBridge scheduled)
- Staging account sync (EventBridge scheduled)
- Recovery instance sync (EventBridge scheduled)
- Tag sync operations

**Target Account Management**:
- Register, update, delete target accounts
- Validate cross-account IAM roles
- Test cross-account connectivity

### Key Operations

| Operation | HTTP Method | Path | Description |
|-----------|-------------|------|-------------|
| `create_protection_group` | POST | `/protection-groups` | Create new protection group |
| `update_protection_group` | PUT | `/protection-groups/{id}` | Update existing group |
| `delete_protection_group` | DELETE | `/protection-groups/{id}` | Delete protection group |
| `create_recovery_plan` | POST | `/recovery-plans` | Create new recovery plan |
| `update_recovery_plan` | PUT | `/recovery-plans/{id}` | Update existing plan |
| `delete_recovery_plan` | DELETE | `/recovery-plans/{id}` | Delete recovery plan |
| `handle_sync_source_server_inventory` | N/A | EventBridge | Sync DRS source servers |
| `handle_sync_staging_accounts` | N/A | EventBridge | Sync staging accounts |
| `handle_sync_recovery_instances` | N/A | EventBridge | Sync recovery instances |

### DynamoDB Tables (Write Access)

- `ProtectionGroups` - Protection group configurations
- `RecoveryPlans` - Recovery plan definitions
- `LaunchConfigurations` - Launch configuration settings
- `TargetAccounts` - Target account registrations
- `SourceServerInventory` - DRS source server inventory
- `RecoveryInstanceInventory` - Recovery instance inventory
- `StagingAccounts` - Staging account configurations
- `RegionStatus` - Region availability status

### AWS API Calls (Write Operations)

- **DRS API**: `extend_source_server()` - Extend staging servers
- **DynamoDB**: Batch writes, updates, deletes for all managed tables

## Execution Handler

**Purpose**: Execute recovery actions and manage execution state.

### Responsibilities

**Recovery Execution**:
- Start recovery operations
- Cancel in-progress executions
- Terminate recovery instances
- Apply launch configurations

**Wave Management**:
- Execute wave-based recovery
- Update wave completion status
- Handle wave pause/resume
- Manage wave transitions

**Instance Management**:
- Terminate recovery instances
- Apply post-launch configurations
- Manage instance lifecycle

**Execution State Management**:
- Update execution history
- Track execution progress
- Persist wave completion status
- Handle execution failures

### Key Operations

| Operation | HTTP Method | Path | Description |
|-----------|-------------|------|-------------|
| `start_recovery` | POST | `/executions` | Start recovery execution |
| `cancel_execution` | POST | `/executions/{id}/cancel` | Cancel execution |
| `terminate_recovery_instances` | POST | `/executions/{id}/terminate` | Terminate instances |
| `apply_launch_config` | POST | `/executions/{id}/apply-config` | Apply configurations |
| `update_wave_completion_status` | N/A | Step Functions | Update wave status |

### DynamoDB Tables (Write Access)

- `ExecutionHistory` - Execution state and progress
- `WaveStatus` - Wave completion tracking

### AWS API Calls (Write Operations)

- **DRS API**: `start_recovery()`, `terminate_recovery_instances()`
- **EC2 API**: `terminate_instances()`, `modify_instance_attribute()`
- **DynamoDB**: Updates to execution history and wave status

### Step Functions Integration

The execution-handler is invoked by Step Functions for wave completion updates:

```json
{
  "UpdateWaveStatus": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:execution-handler",
    "Parameters": {
      "action": "update_wave_completion_status",
      "executionId.$": "$.execution_id",
      "planId.$": "$.plan_id",
      "waveNumber.$": "$.current_wave_number",
      "status.$": "$.status",
      "waveData.$": "$"
    },
    "Next": "CheckWaveComplete"
  }
}
```

## Query Handler

**Purpose**: Provide read-only access to all system data with comprehensive audit logging.

### Responsibilities

**Read-Only Queries**:
- List executions and execution history
- Poll DRS job status (NO writes)
- Query server status and inventory
- Retrieve dashboard data
- Export configurations

**DRS Infrastructure Queries**:
- Get DRS source servers
- Get DRS service limits
- Get DRS accounts
- Get DRS capacity information

**EC2 Resource Queries**:
- Get EC2 subnets
- Get EC2 security groups
- Get EC2 instance types
- Get EC2 instance profiles

**Audit Logging**:
- Log all read operations
- Capture IAM principal information
- Mask sensitive parameters
- Support dual invocation modes (API Gateway + Direct Lambda)

### Key Operations

| Operation | HTTP Method | Path | Description |
|-----------|-------------|------|-------------|
| `list_executions` | GET | `/executions` | List all executions |
| `get_execution` | GET | `/executions/{id}` | Get execution details |
| `poll_wave_status` | N/A | Step Functions | Poll DRS job status (READ-ONLY) |
| `get_drs_source_servers` | GET | `/drs/servers` | List DRS servers |
| `get_server_status` | GET | `/servers/{id}/status` | Get server status |
| `get_dashboard_data` | GET | `/dashboard` | Get dashboard metrics |
| `export_configuration` | GET | `/export` | Export configurations |

### DynamoDB Tables (Read-Only Access)

- `ProtectionGroups` - Read protection groups
- `RecoveryPlans` - Read recovery plans
- `LaunchConfigurations` - Read launch configs
- `TargetAccounts` - Read target accounts
- `SourceServerInventory` - Read server inventory
- `RecoveryInstanceInventory` - Read recovery instances
- `ExecutionHistory` - Read execution history
- `AuditLogs` - **WRITE** audit log entries (exception to read-only rule)

### AWS API Calls (Read-Only Operations)

- **DRS API**: `describe_source_servers()`, `describe_jobs()`, `describe_job_log_items()`
- **EC2 API**: `describe_instances()`, `describe_subnets()`, `describe_security_groups()`
- **DynamoDB**: Query and scan operations (read-only)
- **DynamoDB**: **WRITE** to AuditLogs table (audit logging exception)

### Critical Constraints

**NO WRITE OPERATIONS**:
- ❌ NO DynamoDB writes (except AuditLogs table)
- ❌ NO DRS API writes
- ❌ NO EC2 API writes
- ❌ NO cross-service write operations

**Exception**: Audit logging to `AuditLogs` table is the ONLY write operation permitted in query-handler.

### Dual Invocation Mode Support

Query-handler supports two invocation modes:

**1. API Gateway Invocations** (Frontend):
- Authentication: Cognito JWT token
- Principal: Cognito user email
- RBAC: Role-based permissions from Cognito groups
- Audit: User email, operation, timestamp, parameters

**2. Direct Lambda Invocations** (Step Functions, EventBridge):
- Authentication: IAM role/user from Lambda context
- Principal: IAM ARN extracted from context
- RBAC: Not applicable (service-to-service)
- Audit: IAM ARN, principal type, session name, operation

See [DUAL_INVOCATION_MODE.md](DUAL_INVOCATION_MODE.md) for detailed architecture.

## Shared Utilities

All handlers leverage 19 shared utility modules in `lambda/shared/`:

**Core Utilities**:
- `drs_utils.py` - DRS API normalization and operations
- `cross_account.py` - Cross-account IAM role assumption
- `account_utils.py` - Account validation and management
- `execution_utils.py` - Execution state management
- `response_utils.py` - API Gateway response formatting
- `security_utils.py` - Input validation and sanitization
- `iam_utils.py` - IAM principal extraction and authorization
- `rbac_middleware.py` - Role-based access control

**Supporting Utilities**:
- `drs_regions.py` - DRS-available regions
- `drs_limits.py` - DRS service limits
- `launch_config_service.py` - Launch configuration management
- `launch_config_validation.py` - Launch config validation
- `conflict_detection.py` - Resource conflict detection
- `config_merge.py` - Configuration merging
- `staging_account_models.py` - Staging account data models
- `notifications.py` - SNS notifications
- `active_region_filter.py` - Active region filtering
- `inventory_query.py` - Inventory table query patterns

## EventBridge Integration

### Scheduled Sync Operations

**Source Server Inventory Sync**:
```yaml
SourceServerInventorySyncRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: rate(5 minutes)
    Targets:
      - Arn: !GetAtt DataManagementHandler.Arn
        Input: '{"operation": "handle_sync_source_server_inventory"}'
```

**Staging Account Sync**:
```yaml
StagingAccountSyncRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: rate(15 minutes)
    Targets:
      - Arn: !GetAtt DataManagementHandler.Arn
        Input: '{"operation": "handle_sync_staging_accounts"}'
```

**Recovery Instance Sync**:
```yaml
RecoveryInstanceSyncRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: rate(10 minutes)
    Targets:
      - Arn: !GetAtt DataManagementHandler.Arn
        Input: '{"operation": "handle_sync_recovery_instances"}'
```

## Handler Size Management

### Current Sizes (Post-Refactoring)

```
query-handler:        ~6,564 lines (read-only operations)
data-management:     ~10,551 lines (CRUD + sync operations)
execution-handler:    ~7,831 lines (recovery actions + wave updates)
```

### Size Constraints

**Lambda Deployment Package Limits**:
- Uncompressed: 250 MB
- Compressed (zipped): 50 MB

**Measured Sizes (February 2026)**:
- query-handler: 16.04 MB (8.02% of 200 MB limit) ✓ PASS
- data-management-handler: 0.17 MB (0.09% of 200 MB limit) ✓ PASS
- execution-handler: 16.06 MB (8.03% of 200 MB limit) ✓ PASS

All handlers are well under size limits with significant headroom.

## Design Principles

### Single Responsibility Principle

Each handler has a clear, focused responsibility:
- **data-management-handler**: Data persistence and synchronization
- **execution-handler**: Recovery actions and execution state
- **query-handler**: Read-only queries and audit logging

### No Cross-Handler Lambda Invocations

- EventBridge routes directly to appropriate handler
- Step Functions orchestrates handler invocations
- No handler invokes another handler directly

### Shared Utilities Pattern

- Common code extracted to `lambda/shared/`
- Utilities reused across all handlers
- Consistent patterns and conventions

### Zero Downtime Deployments

- Deploy new operations before removing old ones
- Update EventBridge rules atomically
- Test all operations after migration
- Rollback plan documented

## Migration History

### Query Handler Read-Only Audit (2026)

**Completed Migrations**:
1. ✅ Source server inventory sync → data-management-handler
2. ✅ Staging account sync → data-management-handler
3. ✅ Wave status polling split → query-handler (read) + execution-handler (write)

**Result**: Query-handler is now strictly read-only (except audit logging).

## Related Documentation

- [Dual Invocation Mode Architecture](DUAL_INVOCATION_MODE.md)
- [IAM Principal Extraction](../security/IAM_PRINCIPAL_EXTRACTION.md)
- [RBAC Permissions](../security/RBAC_PERMISSIONS.md)
- [Audit Log Schema](../security/AUDIT_LOG_SCHEMA.md)
- [Deployment Guide](../guides/DEPLOYMENT_GUIDE.md)
