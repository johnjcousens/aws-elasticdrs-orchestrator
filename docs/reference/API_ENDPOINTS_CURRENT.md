<!-- Copyright Amazon.com and Affiliates. All rights reserved.
     This deliverable is considered Developed Content as defined in the AWS Service Terms. -->

# AWS DRS Orchestration - Current API Endpoints

## Overview

The AWS DRS Orchestration platform provides a comprehensive REST API with **66 endpoints** (functional methods, excluding CORS `OPTIONS`) across **9 categories**. All endpoints require Cognito JWT authentication except for health checks and EventBridge-triggered operations.

**Base URL**: `https://api-gateway-url/stage`  
**Authentication**: Cognito JWT Bearer token  
**RBAC**: 5 roles with granular permissions (see [RBAC System](#rbac-system))

**Version**: 4.0

## Lambda Handler Architecture

The API is served by **3 specialized Lambda handlers** for separation of concerns. The decomposition is transitional: most routes target a specialized handler, while a subset still route to a shared API handler ARN pending full migration.

### 1. Data Management Handler
**Function**: `data-management-handler`  
**Purpose**: Create, update, delete operations for configuration data  
**Endpoints**: Protection Groups, Recovery Plans, Target/Staging Accounts, Tag Sync & Configuration

### 2. Execution Handler
**Function**: `execution-handler`  
**Purpose**: Recovery execution control and monitoring  
**Endpoints**: Executions (control, monitoring, DRS job logs) plus internal `find`/`poll`/`finalize` operations

### 3. Query Handler
**Function**: `query-handler`  
**Purpose**: Read-only queries and resource discovery  
**Endpoints**: DRS Integration, EC2 Resources, Configuration Export, User Management

### Supporting Handlers
- **dr-orchestration-stepfunction**: Step Functions orchestration logic (internal)
- **frontend-deployer**: Frontend build and deployment (internal)
- **drs-agent-deployer**: DRS replication agent installation via SSM (in development; not yet deployed by the main stack)

> **Notifications**: SNS execution/wave notifications are published inline by the handlers via the shared `lambda/shared/notifications.py` module. There is no dedicated notification Lambda.

## API Categories

1. [Protection Groups](#1-protection-groups) - 8 endpoints
2. [Recovery Plans](#2-recovery-plans) - 8 endpoints
3. [Executions](#3-executions) - 13 endpoints
4. [DRS Integration](#4-drs-integration) - 11 endpoints
5. [Account & Staging Management](#5-account--staging-management) - 14 endpoints
6. [EC2 Resources](#6-ec2-resources) - 4 endpoints
7. [Configuration](#7-configuration) - 4 endpoints
8. [User Management](#8-user-management) - 3 endpoints
9. [Health Check](#9-health-check) - 1 endpoint

**Total: 66 functional endpoints** (CORS `OPTIONS` preflight methods excluded).

---

## 1. Protection Groups

**Handler**: `data-management-handler`

Manage logical groupings of DRS source servers for coordinated recovery.

### `GET /protection-groups`
List all protection groups with optional filtering.

**Query Parameters:**
- `region` (optional): Filter by AWS region
- `status` (optional): Filter by status (`active`, `inactive`)

**Response:** Array of protection group objects

### `POST /protection-groups`
Create a new protection group.

**Request Body:**
```json
{
  "name": "Web Tier Servers",
  "description": "Frontend web servers",
  "region": "us-east-1",
  "accountId": "123456789012",
  "sourceServerIds": ["s-1234567890abcdef0"],
  "serverSelectionTags": {
    "Environment": "Production",
    "Tier": "Web"
  }
}
```

**Response:** Created protection group object (201)

### `GET /protection-groups/{id}`
Get details of a specific protection group.

**Path Parameters:**
- `id`: Protection group UUID

**Response:** Protection group object with resolved server details

### `PUT /protection-groups/{id}`
Update an existing protection group.

**Path Parameters:**
- `id`: Protection group UUID

**Request Body:** Partial protection group object with fields to update

**Response:** Updated protection group object

### `DELETE /protection-groups/{id}`
Delete a protection group.

**Path Parameters:**
- `id`: Protection group UUID

**Response:** Success confirmation (204)

### `POST /protection-groups/resolve`
Preview servers that would be selected by tag-based criteria.

**Request Body:**
```json
{
  "region": "us-east-1",
  "serverSelectionTags": {
    "Environment": "Production",
    "Tier": "Web"
  }
}
```

**Response:** Array of matching DRS source servers

### `POST /protection-groups/{id}/apply-launch-configs`
Apply per-server DRS launch configurations to all servers in the group.

**Path Parameters:**
- `id`: Protection group UUID

**Response:** Job details for the launch-config apply operation

### `GET /protection-groups/{id}/launch-config-status`
Get the status of a launch-config apply operation for the group.

**Path Parameters:**
- `id`: Protection group UUID

**Response:** Per-server launch-config apply status

---

## 2. Recovery Plans

**Handler**: `data-management-handler`

Manage multi-wave disaster recovery execution plans.

### `GET /recovery-plans`
List all recovery plans with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status
- `region` (optional): Filter by region

**Response:** Array of recovery plan objects

### `POST /recovery-plans`
Create a new recovery plan.

**Request Body:**
```json
{
  "planName": "Production DR Plan",
  "description": "Multi-tier production recovery",
  "waves": [
    {
      "waveName": "Database Tier",
      "protectionGroupId": "pg-uuid-1",
      "waitTimeMinutes": 5
    },
    {
      "waveName": "Application Tier", 
      "protectionGroupId": "pg-uuid-2",
      "waitTimeMinutes": 3
    }
  ]
}
```

**Response:** Created recovery plan object (201)

### `GET /recovery-plans/{id}`
Get details of a specific recovery plan.

**Path Parameters:**
- `id`: Recovery plan UUID

**Response:** Recovery plan object with wave details

### `PUT /recovery-plans/{id}`
Update an existing recovery plan.

**Path Parameters:**
- `id`: Recovery plan UUID

**Request Body:** Partial recovery plan object with fields to update

**Response:** Updated recovery plan object

### `DELETE /recovery-plans/{id}`
Delete a recovery plan.

**Path Parameters:**
- `id`: Recovery plan UUID

**Response:** Success confirmation (204)

### `POST /recovery-plans/{id}/execute`
Execute a recovery plan (start disaster recovery).

**Path Parameters:**
- `id`: Recovery plan UUID

**Request Body:**
```json
{
  "executionType": "DRILL",
  "initiatedBy": "user@company.com"
}
```

**Response:** Execution details with execution ID

### `GET /recovery-plans/{id}/check-existing-instances`
Check for existing recovery instances before execution.

**Path Parameters:**
- `id`: Recovery plan UUID

**Response:** Array of existing recovery instances that would conflict

### `POST /recovery-plans/{id}/check-existing-instances`
Trigger an on-demand scan for existing recovery instances that would conflict with execution.

**Path Parameters:**
- `id`: Recovery plan UUID

**Response:** Scan results with conflicting recovery instances

---

## 3. Executions

**Handler**: `execution-handler`

Monitor and control disaster recovery executions.

### `GET /executions`
List all executions with pagination and filtering.

**Query Parameters:**
- `status` (optional): Filter by execution status
- `planId` (optional): Filter by recovery plan
- `limit` (optional): Number of results (default: 50)
- `nextToken` (optional): Pagination token

**Response:** Paginated array of execution objects

### `POST /executions`
Start a new recovery execution.

**Request Body:**
```json
{
  "planId": "plan-uuid",
  "executionType": "RECOVERY",
  "initiatedBy": "user@company.com"
}
```

**Response:** Execution details with execution ID

### `GET /executions/{executionId}`
Get detailed execution status and progress.

**Path Parameters:**
- `executionId`: Execution UUID

**Response:** Detailed execution object with wave progress

### `POST /executions/{executionId}/cancel`
Cancel a running execution.

**Path Parameters:**
- `executionId`: Execution UUID

**Response:** Cancellation confirmation

### `POST /executions/{executionId}/pause`
Pause execution before next wave.

**Path Parameters:**
- `executionId`: Execution UUID

**Response:** Pause confirmation

### `POST /executions/{executionId}/resume`
Resume a paused execution.

**Path Parameters:**
- `executionId`: Execution UUID

**Response:** Resume confirmation

### `POST /executions/{executionId}/terminate-instances`
Terminate recovery instances from completed execution.

**Path Parameters:**
- `executionId`: Execution UUID

**Response:** Termination job details

### `GET /executions/{executionId}/job-logs`
Get DRS job logs for troubleshooting.

**Path Parameters:**
- `executionId`: Execution UUID

**Query Parameters:**
- `jobId` (optional): Specific DRS job ID

**Response:** Array of log entries

### `GET /executions/{executionId}/termination-status`
Check status of instance termination job.

**Path Parameters:**
- `executionId`: Execution UUID

**Response:** Termination job status and progress

### `DELETE /executions`
Bulk delete completed executions.

**Response:** Deletion summary

### `POST /executions/delete`
Delete specific executions by IDs.

**Request Body:**
```json
{
  "executionIds": ["exec-uuid-1", "exec-uuid-2"]
}
```

**Response:** Deletion results per execution

### `GET /executions/{executionId}/recovery-instances`
List recovery instances launched by an execution, enriched with EC2 details.

**Path Parameters:**
- `executionId`: Execution UUID

**Response:** Array of recovery instance objects (instance ID, private IP, status)

### `GET /execution-callback`
Step Functions task callback endpoint for execution lifecycle transitions.

**Authentication**: IAM role-based (invoked by Step Functions, not end users)

**Response:** Callback acknowledgment

---

## 4. DRS Integration

**Handler**: `query-handler`

Direct integration with AWS Elastic Disaster Recovery service.

### `GET /drs/source-servers`
Discover DRS source servers across regions.

**Query Parameters:**
- `region` (optional): Specific AWS region
- `accountId` (optional): Target account ID

**Response:** Array of DRS source servers with replication status

### `GET /drs/quotas`
Get DRS service quotas and current usage.

**Query Parameters:**
- `region` (required): AWS region
- `accountId` (optional): Target account ID

**Response:** DRS capacity metrics and limits

### `POST /drs/tag-sync`
Sync EC2 instance tags to DRS source servers.

**Request Body:**
```json
{
  "regions": ["us-east-1", "us-west-2"],
  "dryRun": false
}
```

**Response:** Tag sync results per region

### `GET /drs/accounts`
Get available DRS-enabled accounts.

**Response:** Array of accounts with DRS initialization status

### `GET /drs/source-server-inventory`
Get the cached source-server inventory (from the `source-server-inventory` table).

**Query Parameters:**
- `region` (optional): Filter by AWS region
- `accountId` (optional): Target account ID

**Response:** Array of inventoried source servers with last-sync metadata

### `GET /drs/tag-sync`
Get the status and configuration of the EC2-to-DRS tag sync.

**Response:** Tag sync status and last-run results

### `GET /drs/replication`
Get DRS replication status across source servers.

**Query Parameters:**
- `region` (optional): AWS region
- `accountId` (optional): Target account ID

**Response:** Replication state per source server

### `GET /drs/service`
Get DRS service initialization and configuration status for a region/account.

**Query Parameters:**
- `region` (required): AWS region
- `accountId` (optional): Target account ID

**Response:** DRS service status details

### `GET /drs/failover`
Get failover status and available failover options.

**Response:** Failover status details

### `POST /drs/start-recovery`
Start a direct DRS recovery for selected source servers (resource path `/drs/failover/start-recovery`).

**Request Body:**
```json
{
  "sourceServerIds": ["s-1234567890abcdef0"],
  "isDrill": true
}
```

**Response:** DRS recovery job details

### `GET /drs/jobs`
List DRS recovery/termination jobs.

**Query Parameters:**
- `region` (optional): AWS region
- `accountId` (optional): Target account ID

**Response:** Array of DRS job objects

---

## 5. Account & Staging Management

**Handler**: `data-management-handler`

Manage cross-account DRS operations, target accounts, staging accounts, and capacity.

### `GET /accounts/targets`
List all configured target accounts.

**Response:** Array of target account configurations

### `GET /accounts/targets/{id}`
Get a single target account configuration.

**Path Parameters:**
- `id`: Account ID

**Response:** Target account configuration object

### `POST /accounts/targets`
Register a new target account.

**Request Body:**
```json
{
  "accountId": "123456789012",
  "accountName": "Production Account",
  "crossAccountRoleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
}
```

**Response:** Created target account configuration (201)

### `PUT /accounts/targets/{id}`
Update target account configuration.

**Path Parameters:**
- `id`: Account ID

**Request Body:** Partial account configuration

**Response:** Updated account configuration

### `DELETE /accounts/targets/{id}`
Remove target account configuration.

**Path Parameters:**
- `id`: Account ID

**Response:** Success confirmation (204)

### `POST /accounts/targets/{id}/validate`
Validate cross-account role and permissions.

**Path Parameters:**
- `id`: Account ID

**Response:** Validation results with permission details

### `GET /accounts/current`
Get current account information.

**Response:** Current account details

### `POST /staging-accounts/validate`
Validate a staging account's cross-account role and DRS configuration.

**Request Body:**
```json
{
  "stagingAccountId": "123456789012",
  "crossAccountRoleArn": "arn:aws:iam::123456789012:role/DRSStagingRole"
}
```

**Response:** Validation results

### `POST /accounts/targets/{id}/staging-accounts`
Associate a staging account with a target account.

**Path Parameters:**
- `id`: Target account ID

**Response:** Created staging account association (201)

### `DELETE /accounts/targets/{id}/staging-accounts/{stagingAccountId}`
Remove a staging account association from a target account.

**Path Parameters:**
- `id`: Target account ID
- `stagingAccountId`: Staging account ID

**Response:** Success confirmation (204)

### `GET /accounts/targets/{id}/staging-accounts/discover`
Discover staging accounts available for a target account.

**Path Parameters:**
- `id`: Target account ID

**Response:** Array of discovered staging accounts

### `POST /accounts/targets/{id}/staging-accounts/sync`
Sync staging account associations for a target account.

**Path Parameters:**
- `id`: Target account ID

**Response:** Sync results

### `GET /accounts/targets/{id}/capacity`
Get DRS capacity metrics for a single target account.

**Path Parameters:**
- `id`: Target account ID

**Response:** Capacity metrics (used/available source servers)

### `GET /accounts/capacity/all`
Get aggregated DRS capacity metrics across all target accounts.

**Response:** Per-account capacity summary

---

## 6. EC2 Resources

**Handler**: `query-handler`

Retrieve EC2 resources for launch configuration dropdowns.

### `GET /ec2/subnets`
Get available subnets for recovery instance placement.

**Query Parameters:**
- `region` (required): AWS region
- `accountId` (optional): Target account ID

**Response:** Array of subnet objects

### `GET /ec2/security-groups`
Get available security groups.

**Query Parameters:**
- `region` (required): AWS region
- `accountId` (optional): Target account ID

**Response:** Array of security group objects

### `GET /ec2/instance-profiles`
Get available IAM instance profiles.

**Query Parameters:**
- `region` (required): AWS region
- `accountId` (optional): Target account ID

**Response:** Array of instance profile objects

### `GET /ec2/instance-types`
Get available EC2 instance types.

**Query Parameters:**
- `region` (required): AWS region

**Response:** Array of instance type objects with specifications

---

## 7. Configuration

**Handlers**: `query-handler` (export), `data-management-handler` (import, tag-sync)

Export/import configuration and manage settings.

### `GET /config/export`
Export complete configuration (protection groups, recovery plans).

**Query Parameters:**
- `format` (optional): Export format (`json`, `yaml`)
- `includeExecutions` (optional): Include execution history

**Response:** Configuration export file

### `POST /config/import`
Import configuration from backup.

**Request Body:** Configuration data (JSON/YAML)

**Response:** Import results with validation errors

### `GET /config/tag-sync`
Get tag synchronization settings.

**Response:** Tag sync configuration

### `PUT /config/tag-sync`
Update tag synchronization settings.

**Request Body:**
```json
{
  "enabled": true,
  "scheduleExpression": "rate(1 hour)",
  "regions": ["us-east-1", "us-west-2"]
}
```

**Response:** Updated tag sync configuration

---

## 8. User Management

**Handler**: `query-handler`

User profile, role, and permission information.

### `GET /user/profile`
Get the current user's profile (email, username, Cognito groups).

**Response:** User profile object

### `GET /user/roles`
Get the current user's assigned RBAC roles.

**Response:** Array of role identifiers

### `GET /user/permissions`
Get current user's roles and permissions.

**Response:**
```json
{
  "user": {
    "email": "user@company.com",
    "username": "user",
    "groups": ["DRSRecoveryManager"]
  },
  "roles": ["DRS_RECOVERY_MANAGER"],
  "permissions": ["start_recovery", "view_executions", ...]
}
```

---

## 9. Health Check

**Handler**: All handlers support health checks

Service health monitoring.

### `GET /health`
Service health check (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "service": "drs-orchestration-api"
}
```

---

## Internal Operations (EventBridge/Step Functions)

The `execution-handler` Lambda function supports operation-based routing for internal system operations. These operations are invoked by EventBridge schedules and Step Functions for execution lifecycle management.

**Authentication**: IAM role-based (no Cognito JWT required)  
**Invocation**: Direct Lambda invoke via AWS SDK or EventBridge

### Operation: `find`

**Purpose**: Discover active executions that need polling  
**Trigger**: EventBridge (1-minute schedule)  
**Behavior**: Queries DynamoDB StatusIndex GSI for POLLING/CANCELLING executions, invokes poll for each

**Parameters**:
```json
{
  "operation": "find"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionsFound": 3,
  "executionsPolled": 3,
  "results": [
    {"executionId": "uuid", "success": true, "status": "POLLING"}
  ]
}
```

**CLI Usage**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{"operation":"find"}' \
  response.json
```

---

### Operation: `poll`

**Purpose**: Update wave status and enrich server data  
**Trigger**: Self-invoked by find operation  
**Behavior**: Queries DRS job status, enriches with EC2 data, updates DynamoDB

**Critical**: Never changes execution status or calls finalize - only updates wave data

**Parameters**:
```json
{
  "operation": "poll",
  "executionId": "uuid",
  "planId": "uuid"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionId": "uuid",
  "status": "POLLING",
  "allWavesComplete": false,
  "waves": [
    {
      "waveNumber": 0,
      "status": "COMPLETED",
      "serverStatuses": [
        {
          "sourceServerId": "s-123",
          "launchStatus": "LAUNCHED",
          "instanceId": "i-abc",
          "privateIp": "10.0.1.50",
          "instanceType": "t3.medium"
        }
      ]
    }
  ]
}
```

**Data Enrichment**:
- **DRS API**: sourceServerId, launchStatus, recoveryInstanceId
- **EC2 API**: instanceId, privateIp, hostname, instanceType
- **Schema**: All fields normalized to camelCase

**CLI Usage**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{"operation":"poll","executionId":"uuid","planId":"uuid"}' \
  response.json
```

---

### Operation: `finalize`

**Purpose**: Mark execution complete after all waves finish  
**Trigger**: Step Functions only  
**Behavior**: Validates all waves complete, updates status to COMPLETED

**Critical**: Idempotent operation using conditional DynamoDB writes

**Parameters**:
```json
{
  "operation": "finalize",
  "executionId": "uuid",
  "planId": "uuid"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionId": "uuid",
  "status": "COMPLETED",
  "totalWaves": 3,
  "alreadyFinalized": false
}
```

**Validation**: Returns 400 if any wave status is not COMPLETED

**CLI Usage**:
```bash
aws lambda invoke \
  --function-name execution-handler \
  --payload '{"operation":"finalize","executionId":"uuid","planId":"uuid"}' \
  response.json
```

---

### Operation: `pause`

**Purpose**: Pause execution between waves  
**Trigger**: API Gateway or Step Functions  
**Behavior**: Changes execution status to PAUSED

**Parameters**:
```json
{
  "operation": "pause",
  "executionId": "uuid",
  "planId": "uuid"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionId": "uuid",
  "status": "PAUSED"
}
```

---

### Operation: `resume`

**Purpose**: Resume paused execution  
**Trigger**: API Gateway  
**Behavior**: Changes status to POLLING, sends task success to Step Functions

**Parameters**:
```json
{
  "operation": "resume",
  "executionId": "uuid",
  "planId": "uuid"
}
```

**Returns**:
```json
{
  "statusCode": 200,
  "executionId": "uuid",
  "status": "POLLING"
}
```

---

### Internal Operations Architecture

```
EventBridge (1-minute schedule)
  ↓
execution-handler (operation: "find")
  ↓
Query DynamoDB StatusIndex GSI (status: POLLING/CANCELLING)
  ↓
For each active execution:
  ↓
  execution-handler (operation: "poll")
    ↓
  Query DRS API (job status)
    ↓
  Query EC2 API (instance details)
    ↓
  Update DynamoDB (waves, serverStatuses)
    ↓
  Return allWavesComplete flag
    ↓
Step Functions checks flag
  ↓
If all waves complete:
  ↓
  execution-handler (operation: "finalize")
    ↓
  Update execution status to COMPLETED
```

---

## RBAC System

### Roles (5 Total)

1. **DRSOrchestrationAdmin** - Full administrative access
2. **DRSRecoveryManager** - Execute and manage recovery operations  
3. **DRSPlanManager** - Create/modify recovery plans and protection groups
4. **DRSOperator** - Execute recovery but not modify plans
5. **DRSReadOnly** - View-only access for monitoring

### Permissions (11 Total)

- **Account Management**: `register_accounts`, `delete_accounts`, `modify_accounts`, `view_accounts`
- **Recovery Operations**: `start_recovery`, `stop_recovery`, `terminate_instances`, `view_executions`
- **Infrastructure**: `create_protection_groups`, `delete_protection_groups`, `modify_protection_groups`, `view_protection_groups`, `create_recovery_plans`, `delete_recovery_plans`, `modify_recovery_plans`, `view_recovery_plans`
- **Configuration**: `export_configuration`, `import_configuration`

### Role-Permission Matrix

| Role | Account Mgmt | Recovery Ops | Infrastructure | Config |
|------|-------------|-------------|----------------|--------|
| **Admin** | Full | Full | Full | Full |
| **Recovery Manager** | Register/Modify | Full | Full | Full |
| **Plan Manager** | View | Start/Stop | Full | None |
| **Operator** | View | Start/Stop | Modify Only | None |
| **Read Only** | View | View | View | None |

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "ERROR_CODE",
  "message": "Human readable error message",
  "details": {
    "field": "Additional context"
  }
}
```

### Common HTTP Status Codes

- **200** - Success
- **201** - Created
- **204** - No Content (successful deletion)
- **400** - Bad Request (validation error)
- **401** - Unauthorized (authentication required)
- **403** - Forbidden (insufficient permissions)
- **404** - Not Found
- **409** - Conflict (resource already exists or in use)
- **500** - Internal Server Error

### Common Error Codes

- `VALIDATION_ERROR` - Input validation failed
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `RESOURCE_CONFLICT` - Resource already exists or is in use
- `INSUFFICIENT_PERMISSIONS` - User lacks required permissions
- `DRS_SERVICE_ERROR` - AWS DRS service error
- `CROSS_ACCOUNT_ERROR` - Cross-account role assumption failed

---

## Rate Limits

- **General API**: 100 requests per minute per user
- **Execution Operations**: 10 concurrent executions per account
- **DRS Integration**: Subject to AWS DRS service limits

---

## Pagination

List endpoints support cursor-based pagination:

**Request:**
```
GET /executions?limit=25&nextToken=abc123
```

**Response:**
```json
{
  "items": [...],
  "nextToken": "def456",
  "hasMore": true
}
```

---

## WebSocket Events (Future)

Real-time execution updates will be available via WebSocket connection:

- `execution.started`
- `execution.wave.completed` 
- `execution.paused`
- `execution.completed`
- `execution.failed`

---

## SDK Support

Official SDKs planned for:
- Python (boto3-style)
- JavaScript/TypeScript
- Java
- .NET

---

**Version**: 4.0  
**Status**: Production Ready