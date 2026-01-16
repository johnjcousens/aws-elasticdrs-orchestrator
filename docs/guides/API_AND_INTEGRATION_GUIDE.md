# API and Integration Guide

**Version**: 3.0  
**Date**: January 15, 2026  
**Status**: Production Ready - Complete RBAC Coverage  
**Current Implementation**: 47+ endpoints across 12 categories  
**Authentication**: Cognito JWT Bearer tokens or IAM-based direct Lambda invocation

This comprehensive guide covers the complete REST API, integration patterns, and automation workflows for AWS DRS Orchestration. Use this guide for API development, CLI integration, SSM automation, Step Functions orchestration, and EventBridge scheduling.

## Table of Contents

1. [Authentication Methods](#authentication-methods)
2. [API Endpoints Reference](#api-endpoints-reference)
3. [RBAC System](#rbac-system)
4. [Request/Response Examples](#requestresponse-examples)
5. [CLI Integration](#cli-integration)
6. [SSM Automation Integration](#ssm-automation-integration)
7. [Step Functions Integration](#step-functions-integration)
8. [EventBridge Scheduled Execution](#eventbridge-scheduled-execution)
9. [Python SDK Examples](#python-sdk-examples)
10. [Bash Script Examples](#bash-script-examples)
11. [API Gateway Architecture](#api-gateway-architecture)
12. [Adding New Endpoints](#adding-new-endpoints)
13. [Error Handling](#error-handling)
14. [Best Practices](#best-practices)

---

## Authentication Methods

All API calls require authentication. Choose the method that best fits your use case:

### Method 1: Cognito User Credentials (Interactive)

For manual operations and interactive workflows:

```bash
# Get JWT token using username/password
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id ${COGNITO_CLIENT_ID} \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=${USERNAME},PASSWORD=${PASSWORD} \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Use token in API requests
curl -H "Authorization: Bearer $TOKEN" \
  "https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/protection-groups"
```

### Method 2: Cognito Service Account (Automation)

For external integrations and third-party tools:

```bash
# Create service account (one-time setup)
aws cognito-idp admin-create-user \
  --user-pool-id ${USER_POOL_ID} \
  --username dr-automation@example.com \
  --user-attributes Name=email,Value=dr-automation@example.com \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id ${USER_POOL_ID} \
  --username dr-automation@example.com \
  --password "${SERVICE_ACCOUNT_PASSWORD}" \
  --permanent
```

### Method 3: IAM Role-Based (AWS-Native) - RECOMMENDED

For AWS-native automation (Lambda, Step Functions, SSM, EventBridge):

```bash
# Direct Lambda invocation (no Cognito token needed)
AWS_PAGER="" aws lambda invoke \
  --function-name aws-elasticdrs-orchestrator-api-handler-{environment} \
  --payload '{"httpMethod":"GET","path":"/recovery-plans"}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/response.json \
  --region {region}

cat /tmp/response.json | jq -r '.body' | jq .
```

**IAM Policy Required:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:{region}:*:function:aws-elasticdrs-orchestrator-*"
    }
  ]
}
```

**When to Use Each Method:**

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Cognito User** | Interactive/manual operations | User identity tracking | Password management |
| **Cognito Service** | External integrations, third-party tools | Works with any HTTP client | Token refresh needed |
| **IAM Direct Lambda** | AWS-native automation (Step Functions, SSM, EventBridge) | No token management, uses IAM roles | Only works within AWS |

---

## API Endpoints Reference

**Base URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}`  
**Authentication**: Cognito JWT Bearer token or direct Lambda invocation  
**Total Endpoints**: 47+ across 12 categories

### 1. Protection Groups (6 endpoints)

Manage logical groupings of DRS source servers for coordinated recovery.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/protection-groups` | List all protection groups with filtering |
| POST | `/protection-groups` | Create protection group (explicit or tag-based) |
| GET | `/protection-groups/{id}` | Get protection group details |
| PUT | `/protection-groups/{id}` | Update protection group |
| DELETE | `/protection-groups/{id}` | Delete protection group |
| POST | `/protection-groups/resolve` | Preview servers from tag-based selection |

**Query Parameters for GET `/protection-groups`:**
- `accountId` - Filter by target account ID
- `region` - Filter by AWS region
- `name` - Filter by group name (partial match)
- `hasConflict` - Filter by conflict status (true/false)

### 2. Recovery Plans (7 endpoints)

Manage multi-wave disaster recovery execution plans.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/recovery-plans` | List all recovery plans with filtering |
| POST | `/recovery-plans` | Create recovery plan |
| GET | `/recovery-plans/{id}` | Get recovery plan details |
| PUT | `/recovery-plans/{id}` | Update recovery plan |
| DELETE | `/recovery-plans/{id}` | Delete recovery plan |
| POST | `/recovery-plans/{id}/execute` | Execute recovery plan (start DR) |
| GET | `/recovery-plans/{id}/check-existing-instances` | Check for conflicting recovery instances |

**Query Parameters for GET `/recovery-plans`:**
- `accountId` - Filter by target account ID
- `name` - Filter by plan name (partial match)
- `nameExact` - Filter by exact plan name
- `tag` - Filter by protection group tags (format: key=value)
- `hasConflict` - Filter by server conflict status (true/false)
- `status` - Filter by last execution status

### 3. Executions (12 endpoints)

Monitor and control disaster recovery executions with wave-based orchestration.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/executions` | List executions with pagination |
| POST | `/executions` | Start new execution |
| GET | `/executions/{executionId}` | Get detailed execution status |
| POST | `/executions/{executionId}/cancel` | Cancel running execution |
| POST | `/executions/{executionId}/pause` | Pause execution before next wave |
| POST | `/executions/{executionId}/resume` | Resume paused execution |
| POST | `/executions/{executionId}/terminate-instances` | Terminate recovery instances |
| GET | `/executions/{executionId}/job-logs` | Get DRS job logs for troubleshooting |
| GET | `/executions/{executionId}/termination-status` | Check instance termination status |
| GET | `/executions/{executionId}/recovery-instances` | Get recovery instances launched |
| DELETE | `/executions` | Bulk delete completed executions |
| POST | `/executions/delete` | Delete specific executions by IDs |

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

### 4. DRS Integration (4 endpoints)

Direct integration with AWS Elastic Disaster Recovery service.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/drs/source-servers` | Discover DRS source servers across regions |
| GET | `/drs/quotas` | Get DRS service quotas and current usage |
| POST | `/drs/tag-sync` | Sync EC2 instance tags to DRS source servers |
| GET | `/drs/accounts` | Get available DRS-enabled accounts |

### 5. Account Management (6 endpoints)

Manage cross-account DRS operations and target accounts.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/accounts/targets` | List configured target accounts |
| POST | `/accounts/targets` | Register new target account |
| PUT | `/accounts/targets/{id}` | Update target account configuration |
| DELETE | `/accounts/targets/{id}` | Remove target account configuration |
| POST | `/accounts/targets/{id}/validate` | Validate cross-account role permissions |
| GET | `/accounts/current` | Get current account information |

### 6. EC2 Resources (4 endpoints)

Retrieve EC2 resources for launch configuration dropdowns.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ec2/subnets` | List available subnets by region |
| GET | `/ec2/security-groups` | List security groups by region |
| GET | `/ec2/instance-types` | List EC2 instance types |
| GET | `/ec2/instance-profiles` | List IAM instance profiles |

### 7. Configuration (4 endpoints)

Export and import system configuration for backup and migration.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/config/export` | Export all Protection Groups and Recovery Plans |
| POST | `/config/import` | Import configuration (supports dry-run mode) |
| POST | `/config/import?dryRun=true` | Validate import without making changes |
| GET | `/config/validate` | Validate current configuration integrity |

### 8. User Management (1 endpoint)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/current` | Get current user profile/roles |

### 9. Health Check (1 endpoint)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check endpoint (returns service status) |

---

## RBAC System

The API implements comprehensive Role-Based Access Control with 5 roles and granular permissions. All 47+ API endpoints have verified RBAC permission mappings with 100% coverage.

### Roles (5 Total)

1. **DRSOrchestrationAdmin** - Full administrative access to all operations
2. **DRSRecoveryManager** - Execute and manage recovery operations with plan modification (no account deletion)
3. **DRSPlanManager** - Create/modify recovery plans and protection groups (no instance termination)
4. **DRSOperator** - Execute recovery operations but cannot modify plans (no create/delete)
5. **DRSReadOnly** - View-only access for monitoring and reporting

### Cognito Group Names

**Primary Groups (Recommended):**
- `DRSOrchestrationAdmin`, `DRSRecoveryManager`, `DRSPlanManager`, `DRSOperator`, `DRSReadOnly`

**Legacy Groups (Backward Compatible):**
- `DRS-Administrator` → DRSOrchestrationAdmin
- `DRS-Infrastructure-Admin` → DRSRecoveryManager
- `DRS-Recovery-Plan-Manager` → DRSPlanManager
- `DRS-Operator` → DRSOperator
- `DRS-Read-Only` → DRSReadOnly

### Permissions (11 Total)

**Account Management:**
- `register_accounts` - Register new target accounts
- `delete_accounts` - Remove target accounts
- `modify_accounts` - Update account configurations
- `view_accounts` - View account information

**Recovery Operations:**
- `start_recovery` - Start disaster recovery executions
- `terminate_instances` - Terminate recovery instances
- `view_executions` - View execution status and history

**Infrastructure Management:**
- `create_protection_groups` - Create protection groups
- `delete_protection_groups` - Delete protection groups
- `modify_protection_groups` - Update protection groups
- `view_protection_groups` - View protection groups
- `create_recovery_plans` - Create recovery plans
- `delete_recovery_plans` - Delete recovery plans
- `modify_recovery_plans` - Update recovery plans
- `view_recovery_plans` - View recovery plans

**Configuration:**
- `export_configuration` - Export system configuration
- `import_configuration` - Import system configuration

### Role-Permission Matrix

| Role | Account Mgmt | Recovery Ops | Infrastructure | Config |
|------|-------------|-------------|----------------|--------|
| **Admin** | Full | Full | Full | Full |
| **Recovery Manager** | Register/Modify | Full | Full | Full |
| **Plan Manager** | View | Start/Stop | Full | None |
| **Operator** | View | Start/Stop | Modify Only | None |
| **Read Only** | View | View | View | None |

---

## Request/Response Examples

### Create Protection Group (Tag-Based Selection)

**Request:**
```bash
POST /protection-groups
Content-Type: application/json

{
  "GroupName": "Database-Servers",
  "Description": "Production database servers for HRP application",
  "Region": "us-east-1",
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
}
```

**Response (201 Created):**
```json
{
  "groupId": "pg-12345678-1234-1234-1234-123456789012",
  "groupName": "Database-Servers",
  "description": "Production database servers for HRP application",
  "region": "us-east-1",
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

### Create Recovery Plan with Multi-Wave Configuration

**Request:**
```bash
POST /recovery-plans
Content-Type: application/json

{
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
}
```

### Start Drill Execution

**Request:**
```bash
POST /recovery-plans/rp-12345678-1234-1234-1234-123456789012/execute
Content-Type: application/json

{
  "ExecutionType": "DRILL",
  "InitiatedBy": "cli-automation",
  "ExecutionName": "Monthly-DR-Test-December-2024",
  "Description": "Scheduled monthly disaster recovery test for HRP application"
}
```

### Pause and Resume Execution

**Pause Request:**
```bash
POST /executions/exec-12345678-1234-1234-1234-123456789012/pause
Content-Type: application/json

{
  "reason": "Manual validation required before proceeding to application tier",
  "pausedBy": "operations-team"
}
```

**Resume Request:**
```bash
POST /executions/exec-12345678-1234-1234-1234-123456789012/resume
Content-Type: application/json

{
  "resumedBy": "operations-team",
  "notes": "Database validation completed successfully, proceeding with application tier"
}
```

### Configuration Export/Import

**Export Request:**
```bash
GET /config/export
```

**Import Request (Dry Run):**
```bash
POST /config/import?dryRun=true
Content-Type: application/json

{
  "metadata": {
    "schemaVersion": "1.0"
  },
  "protectionGroups": [...],
  "recoveryPlans": [...]
}
```

---

## CLI Integration

### Environment Setup

```bash
# Set environment variables
export API_ENDPOINT="https://{api-id}.execute-api.{region}.amazonaws.com/{stage}"
export COGNITO_CLIENT_ID="{client-id}"
export COGNITO_USER_POOL_ID="{pool-id}"
export DR_USERNAME="dr-automation@example.com"
export DR_PASSWORD="{password}"

# Function to get auth token
get_token() {
  aws cognito-idp initiate-auth \
    --client-id ${COGNITO_CLIENT_ID} \
    --auth-flow USER_PASSWORD_AUTH \
    --auth-parameters USERNAME=${DR_USERNAME},PASSWORD=${DR_PASSWORD} \
    --query 'AuthenticationResult.IdToken' \
    --output text
}

# Function to make authenticated API calls
api_call() {
  local method=$1
  local endpoint=$2
  local data=$3
  local token=$(get_token)
  
  if [ -n "$data" ]; then
    curl -s -X ${method} \
      -H "Authorization: Bearer ${token}" \
      -H "Content-Type: application/json" \
      -d "${data}" \
      "${API_ENDPOINT}${endpoint}"
  else
    curl -s -X ${method} \
      -H "Authorization: Bearer ${token}" \
      "${API_ENDPOINT}${endpoint}"
  fi
}
```

### Common CLI Operations

**List Recovery Plans:**
```bash
# List all plans
api_call GET "/recovery-plans" | jq '.plans[] | {id, name, waveCount}'

# Find plan by name
api_call GET "/recovery-plans?nameExact=2-Tier%20Recovery" | jq '.plans[0]'

# Find plans ready to execute (no conflicts)
api_call GET "/recovery-plans?hasConflict=false" | jq '.plans[] | {id, name}'
```

**Start Execution:**
```bash
# Start a drill execution
PLAN_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
api_call POST "/executions" '{
  "recoveryPlanId": "'${PLAN_ID}'",
  "executionType": "DRILL",
  "initiatedBy": "cli-automation"
}'
```

**Monitor Execution:**
```bash
# Poll until complete
EXECUTION_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
while true; do
  STATUS=$(api_call GET "/executions/${EXECUTION_ID}" | jq -r '.status')
  echo "Status: ${STATUS}"
  
  case ${STATUS} in
    completed|failed|cancelled)
      echo "Execution finished with status: ${STATUS}"
      break
      ;;
    paused)
      echo "Execution paused - manual intervention required"
      break
      ;;
  esac
  
  sleep 30
done
```

---

## API Gateway Architecture

### Stack Organization

The API Gateway uses a nested stack architecture to organize resources logically and avoid CloudFormation template size limits.

**Stack Hierarchy:**
```
master-template.yaml
├── api-gateway-core-stack.yaml (REST API, Authorizer)
├── api-gateway-resources-stack.yaml (URL paths)
├── api-gateway-core-methods-stack.yaml (CRUD methods)
├── api-gateway-operations-methods-stack.yaml (Execution/DRS operations)
├── api-gateway-infrastructure-methods-stack.yaml (Infrastructure discovery)
├── api-gateway-deployment-stack.yaml (Deployment, Stage, CORS)
└── api-auth-stack.yaml (Cognito User Pool, Client)
```

### Stack Responsibilities

| Stack | Purpose | Resource Count |
|-------|---------|----------------|
| `api-gateway-core-stack.yaml` | REST API, Authorizer, Lambda Permissions | ~10 |
| `api-gateway-resources-stack.yaml` | API Resources (URL paths) | ~50 |
| `api-gateway-core-methods-stack.yaml` | Core CRUD methods | ~30 |
| `api-gateway-operations-methods-stack.yaml` | Execution & DRS operation methods | ~40 |
| `api-gateway-infrastructure-methods-stack.yaml` | Infrastructure & configuration methods | ~35 |
| `api-gateway-deployment-stack.yaml` | Deployment, Stage, CORS responses | ~15 |
| `api-auth-stack.yaml` | Cognito User Pool, Client, Identity Pool | ~10 |

**Total Resources**: ~190 across 7 stacks (well under individual stack limits)

---

## Adding New Endpoints

### Decision Tree

```
New API Endpoint?
├── Is it CRUD for Protection Groups/Recovery Plans/Config?
│   └── YES → api-gateway-core-methods-stack.yaml
├── Is it execution/workflow/DRS operation?
│   └── YES → api-gateway-operations-methods-stack.yaml
├── Is it infrastructure discovery/cross-account config?
│   └── YES → api-gateway-infrastructure-methods-stack.yaml
└── Is it new major feature (15+ endpoints)?
    └── YES → Create new api-gateway-[category]-methods-stack.yaml
```

### Step-by-Step Process

**1. Add Resource (if new path needed):**
```yaml
# In cfn/api-gateway-resources-stack.yaml
NewFeatureResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref RestApiId
    ParentId: !Ref RootResourceId
    PathPart: 'new-feature'
```

**2. Add Methods to Appropriate Stack:**
```yaml
# In appropriate cfn/api-gateway-*-methods-stack.yaml
NewFeatureGetMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    RestApiId: !Ref RestApiId
    ResourceId: !Ref NewFeatureResourceId
    HttpMethod: GET
    AuthorizationType: COGNITO_USER_POOLS
    AuthorizerId: !Ref AuthorizerId
    Integration:
      Type: AWS_PROXY
      IntegrationHttpMethod: POST
      Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${LambdaFunctionArn}/invocations'
```

**3. Add OPTIONS Method for CORS:**
```yaml
NewFeatureOptionsMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    RestApiId: !Ref RestApiId
    ResourceId: !Ref NewFeatureResourceId
    HttpMethod: OPTIONS
    AuthorizationType: NONE
    Integration:
      Type: MOCK
      IntegrationResponses:
        - StatusCode: 200
          ResponseParameters:
            method.response.header.Access-Control-Allow-Headers: "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
            method.response.header.Access-Control-Allow-Methods: "'GET,OPTIONS'"
            method.response.header.Access-Control-Allow-Origin: "'*'"
```

### Naming Conventions

| Pattern | Example | Usage |
|---------|---------|-------|
| `[Feature]sGetMethod` | `ProtectionGroupsGetMethod` | GET /protection-groups |
| `[Feature]GetMethod` | `ProtectionGroupGetMethod` | GET /protection-groups/{id} |
| `[Feature]sPostMethod` | `ProtectionGroupsPostMethod` | POST /protection-groups |
| `[Feature]PutMethod` | `ProtectionGroupPutMethod` | PUT /protection-groups/{id} |
| `[Feature]DeleteMethod` | `ProtectionGroupDeleteMethod` | DELETE /protection-groups/{id} |
| `[Feature][Action]Method` | `ExecutionPauseMethod` | POST /executions/{id}/pause |

### Validation Commands

```bash
# Run architecture validation
./scripts/validate-api-architecture.sh

# Check CloudFormation syntax
make validate

# Check resource counts
grep -E "^  [A-Za-z][A-Za-z0-9]*:$" cfn/api-gateway-*-methods-stack.yaml | wc -l

# Check template sizes
ls -la cfn/api-gateway-*.yaml | awk '{print $5/1024 "KB", $9}'
```

---

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

---

## Best Practices

### API Development
- Follow naming conventions: `[Feature][Action]Method`
- Always include OPTIONS method for CORS
- Use AWS_PROXY integration pattern
- Use parameters instead of hardcoded values
- Run validation script before committing
- Test in development environment

### Authentication
- Use IAM-based authentication for AWS-native workflows
- Use Cognito service accounts for external integrations
- Implement proper token refresh for long-running processes
- Use least-privilege IAM policies

### Integration
- Implement exponential backoff for retries
- Monitor DRS service quotas before operations
- Use configuration export for backup and disaster recovery
- Validate imports with dry-run before execution

### Performance
- Use pagination for large result sets
- Implement caching for frequently accessed data
- Monitor API Gateway throttling limits
- Use batch operations where available

### Security
- Never hardcode credentials in scripts
- Use AWS Secrets Manager for sensitive data
- Implement proper RBAC role assignments
- Enable CloudTrail for audit logging
- Use VPC endpoints for private API access

---

## Additional Resources

- **API Reference**: Complete endpoint documentation with examples
- **Architecture Guide**: Detailed CloudFormation stack organization
- **Development Guide**: Step-by-step endpoint addition process
- **Integration Examples**: SSM, Step Functions, EventBridge patterns
- **Troubleshooting**: Common issues and solutions

For complete integration examples including SSM Automation, Step Functions orchestration, EventBridge scheduling, and Python SDK usage, refer to the individual sections in this guide or the original source documentation.
