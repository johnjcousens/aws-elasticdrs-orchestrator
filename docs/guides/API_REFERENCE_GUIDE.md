# API Reference Guide

Complete REST API documentation for AWS DRS Orchestration Solution.

**Current Implementation**: 42+ endpoints across 12 categories  
**Authentication**: Cognito JWT Bearer tokens  
**RBAC**: 5 roles with granular permissions  
**Last Updated**: January 1, 2026

## Authentication & Authorization

All API requests require a valid Cognito JWT token and appropriate RBAC permissions:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://your-api-endpoint.execute-api.us-east-1.amazonaws.com/prod/protection-groups
```

### RBAC Roles
- **DRSOrchestrationAdmin** - Full administrative access
- **DRSRecoveryManager** - Execute and manage recovery operations  
- **DRSPlanManager** - Create/modify recovery plans and protection groups
- **DRSOperator** - Execute recovery but not modify plans
- **DRSReadOnly** - View-only access for monitoring

## Core Endpoints

### Protection Groups

| Method | Endpoint                         | Description                           |
| ------ | -------------------------------- | ------------------------------------- |
| GET    | `/protection-groups`           | List all protection groups with optional filtering |
| POST   | `/protection-groups`           | Create protection group with tag-based or explicit server selection |
| GET    | `/protection-groups/{id}`      | Get protection group details          |
| PUT    | `/protection-groups/{id}`      | Update protection group with optimistic locking |
| DELETE | `/protection-groups/{id}`      | Delete protection group (blocked if used in plans) |
| POST   | `/protection-groups/resolve`   | Preview servers matching tags in real-time |

**Query Parameters for GET `/protection-groups`:**
- `accountId` - Filter by target account ID
- `region` - Filter by AWS region
- `name` - Filter by group name (partial match)
- `hasConflict` - Filter by conflict status (true/false)

### Recovery Plans

| Method | Endpoint                                      | Description                           |
| ------ | --------------------------------------------- | ------------------------------------- |
| GET    | `/recovery-plans`                           | List all recovery plans with execution history and conflict info |
| POST   | `/recovery-plans`                           | Create recovery plan with multi-wave configuration |
| GET    | `/recovery-plans/{id}`                      | Get recovery plan details with wave dependencies |
| PUT    | `/recovery-plans/{id}`                      | Update recovery plan with validation |
| DELETE | `/recovery-plans/{id}`                      | Delete recovery plan (blocked if has active executions) |
| POST   | `/recovery-plans/{id}/execute`              | Execute recovery plan (drill or recovery mode) |
| GET    | `/recovery-plans/{id}/check-existing-instances` | Check for existing recovery instances before execution |

**Query Parameters for GET `/recovery-plans`:**
- `accountId` - Filter by target account ID
- `name` - Filter by plan name (partial match)
- `nameExact` - Filter by exact plan name
- `tag` - Filter by protection group tags (format: key=value)
- `hasConflict` - Filter by server conflict status (true/false)
- `status` - Filter by last execution status

### Executions

| Method | Endpoint                                 | Description                           |
| ------ | ---------------------------------------- | ------------------------------------- |
| GET    | `/executions`                          | List execution history with advanced filtering |
| POST   | `/executions`                          | Start new execution (alternative to recovery-plans execute) |
| GET    | `/executions/{id}`                     | Get detailed execution status and wave progress |
| POST   | `/executions/{id}/pause`               | Pause execution between waves (uses Step Functions waitForTaskToken) |
| POST   | `/executions/{id}/resume`              | Resume paused execution |
| POST   | `/executions/{id}/cancel`              | Cancel running execution |
| POST   | `/executions/{id}/terminate-instances` | Terminate recovery instances after drill completion |
| GET    | `/executions/{id}/job-logs`            | Get DRS job logs for execution with real-time updates |
| GET    | `/executions/{id}/termination-status`  | Check status of instance termination job |
| DELETE | `/executions`                          | Bulk delete completed executions |
| POST   | `/executions/delete`                   | Delete specific executions by IDs |
**Query Parameters for GET `/executions`:**
- `planId` - Filter by recovery plan ID
- `status` - Filter by execution status
- `executionType` - Filter by DRILL or RECOVERY
- `initiatedBy` - Filter by who started the execution
- `startDate` - Filter by start date (MM-DD-YYYY format)
- `endDate` - Filter by end date (MM-DD-YYYY format)
- `dateRange` - Quick filters: today, yesterday, thisWeek, lastWeek, thisMonth, lastMonth
- `limit` - Limit number of results (default: 50)
- `sortBy` - Sort field: StartTime, EndTime, Status (default: StartTime)
- `sortOrder` - Sort direction: asc, desc (default: desc)

## DRS Integration

### DRS Source Servers

| Method | Endpoint                                | Description                              |
| ------ | --------------------------------------- | ---------------------------------------- |
| GET    | `/drs/source-servers`                 | Discover DRS source servers across regions with advanced filtering |
| GET    | `/drs/quotas`                         | Get DRS service quotas and current usage |
| GET    | `/drs/accounts`                       | Get DRS account information and initialization status |
| POST   | `/drs/tag-sync`                       | Sync EC2 tags to DRS source servers across all regions |

**Query Parameters for GET `/drs/source-servers`:**
- `region` - Target AWS region (required)
- `accountId` - Target account ID for cross-account access
- `tags` - Filter by server tags (JSON object)
- `replicationState` - Filter by replication state
- `lifecycleState` - Filter by lifecycle state
- `hostname` - Filter by hostname (partial match)
- `includeArchived` - Include archived servers (default: false)

**Query Parameters for GET `/drs/quotas`:**
- `region` - Target AWS region (required)
- `accountId` - Target account ID for cross-account access

**Query Parameters for GET `/drs/accounts`:**
- `region` - Target AWS region (required)
- `includeCapacity` - Include detailed capacity metrics (default: false)

### EC2 Resources (for Launch Configuration)

| Method | Endpoint                                   | Description                       |
| ------ | ------------------------------------------ | --------------------------------- |
| GET    | `/ec2/subnets`                           | List VPC subnets for launch configuration |
| GET    | `/ec2/security-groups`                   | List security groups for launch configuration |
| GET    | `/ec2/instance-profiles`                 | List IAM instance profiles for EC2 instances |
| GET    | `/ec2/instance-types`                    | List available EC2 instance types |

**Query Parameters for all EC2 endpoints:**
- `region` - Target AWS region (required)
- `accountId` - Target account ID for cross-account access
- `vpcId` - Filter by VPC ID (for subnets and security groups)

## Multi-Account Management

### Target Accounts

| Method | Endpoint                              | Description                    |
| ------ | ------------------------------------- | ------------------------------ |
| GET    | `/accounts/targets`                 | List registered target accounts for cross-account orchestration |
| POST   | `/accounts/targets`                 | Register new target account with cross-account role |
| PUT    | `/accounts/targets/{id}`            | Update target account configuration |
| DELETE | `/accounts/targets/{id}`            | Unregister target account |
| POST   | `/accounts/targets/{id}/validate`   | Validate cross-account role access |

### Current Account

| Method | Endpoint              | Description                    |
| ------ | --------------------- | ------------------------------ |
| GET    | `/accounts/current` | Get current account information |

## Configuration Management

### Config Export/Import

| Method | Endpoint           | Description                           |
| ------ | ------------------ | ------------------------------------- |
| GET    | `/config/export` | Export all Protection Groups and Recovery Plans as JSON |
| POST   | `/config/import` | Import Protection Groups and Recovery Plans from JSON |

**Query Parameters for GET `/config/export`:**
- `includeExecutions` - Include execution history (default: false)
- `accountId` - Export only resources for specific account
- `format` - Export format: json, yaml (default: json)

### Tag Sync Settings

| Method | Endpoint              | Description                           |
| ------ | --------------------- | ------------------------------------- |
| GET    | `/config/tag-sync`  | Get tag synchronization settings |
| PUT    | `/config/tag-sync`  | Update tag synchronization settings |

### User Management

| Method | Endpoint              | Description                           |
| ------ | --------------------- | ------------------------------------- |
| GET    | `/user/permissions` | Get current user's roles and permissions |

### Health Check

| Method | Endpoint    | Description                   |
| ------ | ----------- | ----------------------------- |
| GET    | `/health` | Service health check endpoint (no authentication required) |
## Request/Response Examples

### Create Protection Group with Tag-Based Selection

```bash
curl -X POST "${API_ENDPOINT}/protection-groups" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

**Response:**
```json
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
  "launchConfig": {
    "SubnetId": "subnet-12345678",
    "SecurityGroupIds": ["sg-12345678", "sg-87654321"],
    "InstanceType": "r5.xlarge",
    "IamInstanceProfileName": "EC2-DRS-Instance-Profile",
    "CopyPrivateIp": true,
    "CopyTags": true,
    "Licensing": {"osByol": false},
    "TargetInstanceTypeRightSizingMethod": "BASIC",
    "LaunchDisposition": "STARTED"
  },
  "createdDate": 1703875200,
  "lastModifiedDate": 1703875200,
  "version": 1
}
```

### Preview Servers Matching Tags

```bash
curl -X POST "${API_ENDPOINT}/protection-groups/resolve" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "region": "us-east-1",
    "AccountId": "123456789012",
    "AssumeRoleName": "DRSOrchestrationCrossAccountRole",
    "ServerSelectionTags": {
      "DR-Application": "HRP",
      "DR-Tier": "Database"
    }
  }'
```

**Response:**
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
  "serverCount": 2,
  "resolvedAt": 1703875200
}
```
### Create Recovery Plan with Multi-Wave Configuration

```bash
curl -X POST "${API_ENDPOINT}/recovery-plans" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### Start Drill Execution

```bash
curl -X POST "${API_ENDPOINT}/recovery-plans/rp-12345678-1234-1234-1234-123456789012/execute" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "ExecutionType": "DRILL",
    "InitiatedBy": "cli-automation",
    "ExecutionName": "Monthly-DR-Test-December-2024",
    "Description": "Scheduled monthly disaster recovery test for HRP application"
  }'
```

### List Executions with Filtering

```bash
# Get executions from last week
curl -X GET "${API_ENDPOINT}/executions?dateRange=lastWeek&status=COMPLETED&executionType=DRILL&limit=10" \
  -H "Authorization: Bearer ${TOKEN}"

# Get executions for specific date range
curl -X GET "${API_ENDPOINT}/executions?startDate=12-01-2024&endDate=12-31-2024" \
  -H "Authorization: Bearer ${TOKEN}"
```

### Pause and Resume Execution

```bash
# Pause execution
curl -X POST "${API_ENDPOINT}/executions/exec-12345678-1234-1234-1234-123456789012/pause" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Manual validation required before proceeding to application tier",
    "pausedBy": "operations-team"
  }'

# Resume execution
curl -X POST "${API_ENDPOINT}/executions/exec-12345678-1234-1234-1234-123456789012/resume" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "resumedBy": "operations-team",
    "notes": "Database validation completed successfully, proceeding with application tier"
  }'
```

### Terminate Recovery Instances

```bash
curl -X POST "${API_ENDPOINT}/executions/exec-12345678-1234-1234-1234-123456789012/terminate-instances" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "terminateAll": true,
    "reason": "Drill completed successfully, cleaning up resources"
  }'
```

### Get DRS Service Quotas

```bash
curl -X GET "${API_ENDPOINT}/drs/quotas?region=us-east-1&accountId=123456789012" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Response:**
```json
{
  "region": "us-east-1",
  "accountId": "123456789012",
  "quotas": {
    "totalSourceServers": 45,
    "maxSourceServers": 4000,
    "replicatingServers": 42,
    "maxReplicatingServers": 300,
    "availableReplicatingSlots": 258,
    "currentJobs": 2,
    "maxConcurrentJobs": 20,
    "serversInAllJobs": 15,
    "maxServersInAllJobs": 500
  },
  "status": "OK",
  "warnings": [],
  "lastUpdated": 1703875200
}
```

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "error": "INVALID_REQUEST",
  "message": "ServerSelectionTags must be a non-empty object with tag key-value pairs",
  "field": "ServerSelectionTags",
  "code": "INVALID_TAGS"
}
```

**401 Unauthorized:**
```json
{
  "error": "Unauthorized",
  "message": "Valid authentication required"
}
```

**409 Conflict:**
```json
{
  "error": "VERSION_CONFLICT", 
  "message": "Resource was modified by another user. Please refresh and try again.",
  "expectedVersion": 2,
  "currentVersion": 3,
  "resourceId": "pg-12345678-1234-1234-1234-123456789012"
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `MISSING_FIELD` | Required field missing | 400 |
| `INVALID_NAME` | Name validation failed | 400 |
| `PG_NAME_EXISTS` | Protection Group name exists | 409 |
| `RP_NAME_EXISTS` | Recovery Plan name exists | 409 |
| `VERSION_CONFLICT` | Optimistic locking conflict | 409 |
| `SERVER_CONFLICT` | Server already assigned | 409 |
| `TAG_CONFLICT` | Tags already in use | 409 |
| `PLAN_ALREADY_EXECUTING` | Plan has active execution | 409 |
| `EXECUTION_NOT_FOUND` | Execution not found | 404 |
| `WAVE_SIZE_LIMIT_EXCEEDED` | Wave exceeds 100 servers | 400 |
| `CONCURRENT_JOBS_LIMIT_EXCEEDED` | DRS job limit reached | 429 |

## Rate Limiting

The API implements rate limiting to ensure service stability:

- **Protection Groups**: 10 requests per minute per user
- **Recovery Plans**: 5 requests per minute per user  
- **Executions**: 3 executions per minute per user
- **DRS Operations**: 20 requests per minute per user
- **Bulk Operations**: 1 request per minute per user

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1703875260
```

## Data Formats

- **Timestamps**: Unix timestamps in seconds
- **UUIDs**: Standard UUID format for IDs
- **Field Names**: camelCase in responses, PascalCase in DynamoDB
- **Status Values**: UPPERCASE strings
- **Regions**: AWS region codes (e.g., "us-east-1")

For complete integration examples including CLI, SSM, Step Functions, EventBridge, and Python SDK, see the [Orchestration Integration Guide](ORCHESTRATION_INTEGRATION_GUIDE.md).