# Software Requirements Specification
# AWS DRS Orchestration System

**Version**: 4.0  
**Status**: Production Ready

---

## Document Purpose

This Software Requirements Specification (SRS) defines the functional and non-functional requirements for the AWS DRS Orchestration system. It serves as the authoritative source for system capabilities, API contracts, data models, and validation criteria.

---

## System Overview

### Architecture Components

**Compute Layer**:
- 6 Lambda functions (decomposed architecture)
- Step Functions state machine with waitForTaskToken (1-year timeout)
- EventBridge scheduled rules (1-minute intervals)

**Data Layer**:
- 4 DynamoDB tables with GSI indexes (camelCase schema)
- S3 buckets for artifacts and static hosting

**API Layer** (Optional):
- API Gateway REST API with 44 endpoints across 9 categories
- Cognito User Pool with 5 RBAC roles

**Frontend Layer** (Optional):
- React 19.1.1 + CloudScape Design System 3.0.1148
- 35+ components across 8 pages
- CloudFront CDN distribution
- S3 static website hosting

**Infrastructure**:
- 16 CloudFormation templates (1 master + 15 nested)
- 4 deployment modes (standalone, API-only, external integration)

---

## Functional Requirements

### FR-1: Lambda Functions

#### FR-1.1: data-management-handler

**Purpose**: CRUD operations for Protection Groups, Recovery Plans, and Configuration

**Responsibilities**:
- Create, update, delete Protection Groups
- Create, update, delete Recovery Plans
- Target account management
- Configuration management
- Tag sync configuration

**Endpoints (22 Total)**:
1. POST /protection-groups - Create protection group
2. PUT /protection-groups/{id} - Update protection group
3. DELETE /protection-groups/{id} - Delete protection group
4. GET /protection-groups - List protection groups
5. GET /protection-groups/{id} - Get protection group details
6. POST /protection-groups/resolve - Resolve tag-based servers
7. POST /recovery-plans - Create recovery plan
8. PUT /recovery-plans/{id} - Update recovery plan
9. DELETE /recovery-plans/{id} - Delete recovery plan
10. GET /recovery-plans - List recovery plans
11. GET /recovery-plans/{id} - Get recovery plan details
12. GET /recovery-plans/{id}/check-existing-instances - Check for existing recovery instances
13. POST /drs/tag-sync - Manual tag synchronization
14. POST /config/import - Import system configuration
15. GET /config/tag-sync - Get tag sync configuration
16. PUT /config/tag-sync - Update tag sync configuration
17. GET /accounts/targets - List target accounts
18. POST /accounts/targets - Create target account
19. GET /accounts/targets/{id} - Get target account details
20. PUT /accounts/targets/{id} - Update target account
21. DELETE /accounts/targets/{id} - Delete target account
22. POST /accounts/targets/{id}/validate - Validate cross-account access

**Performance Requirements**:
- Cold start: < 2 seconds
- Warm invocation: < 500ms
- Memory: 512 MB
- Timeout: 120 seconds

**Validation Requirements**:
- Protection Group names: 1-128 characters, alphanumeric + hyphens
- Server IDs: Valid DRS source server ID format (s-[0-9a-f]{17})
- Tag criteria: Valid AWS tag key/value pairs
- Wave numbers: Positive integers, sequential
- Launch configuration: Valid EC2 parameters

#### FR-1.2: execution-handler

**Purpose**: DR execution operations and monitoring

**Responsibilities**:
- Start recovery plan executions
- Pause, resume, cancel executions
- Terminate recovery instances
- Poll DRS job status
- Update execution state
- Finalize completed executions

**Endpoints (11 Total)**:
1. POST /executions - Start execution
2. GET /executions - List executions with filtering
3. GET /executions/{id} - Get execution details
4. POST /executions/{id}/cancel - Cancel execution
5. POST /executions/{id}/pause - Pause execution
6. POST /executions/{id}/resume - Resume execution
7. POST /executions/{id}/terminate-instances - Terminate recovery instances
8. GET /executions/{id}/job-logs - Get DRS job logs
9. GET /executions/{id}/termination-status - Check termination status
10. DELETE /executions - Bulk delete executions
11. POST /executions/delete - Delete specific executions

**EventBridge Integration**:
- Trigger: Every 1 minute
- Action: Query StatusIndex GSI for POLLING executions
- Invoke: Poll DRS job status for active executions

**DRS Job Polling**:
- Poll interval: 30 seconds
- Status tracking: PENDING → STARTED → COMPLETED/FAILED
- Update DynamoDB with real-time progress
- Transition to COMPLETED/FAILED when all jobs finish

**Performance Requirements**:
- Cold start: < 2 seconds
- Warm invocation: < 500ms
- Memory: 512 MB
- Timeout: 300 seconds

**EventBridge Integration**:
- Trigger: Every 1 minute
- Action: Query StatusIndex GSI for POLLING executions
- Invoke: Poll DRS job status for active executions

**DRS Job Polling**:
- Poll interval: 30 seconds
- Status tracking: PENDING → STARTED → COMPLETED/FAILED
- Update DynamoDB with real-time progress
- Transition to COMPLETED/FAILED when all jobs finish

#### FR-1.3: query-handler

**Purpose**: Read-only query operations

**Responsibilities**:
- List and describe operations
- DRS source server discovery
- Service quota monitoring
- Configuration export
- User permissions and profile

**Endpoints (12 Total)**:
1. GET /drs/source-servers - Discover DRS source servers
2. GET /drs/quotas - Get DRS service quotas
3. GET /drs/accounts - List DRS accounts
4. GET /ec2/subnets - List EC2 subnets
5. GET /ec2/security-groups - List security groups
6. GET /ec2/instance-profiles - List IAM instance profiles
7. GET /ec2/instance-types - List EC2 instance types
8. GET /config/export - Export system configuration
9. GET /user/profile - Get user profile
10. GET /user/roles - Get user roles
11. GET /user/permissions - Get user permissions
12. GET /health - API health check (no auth)

**Performance Requirements**:
- Cold start: < 2 seconds
- Warm invocation: < 500ms
- Memory: 256 MB
- Timeout: 60 seconds

**Caching Strategy**:
- DRS source servers: 5-minute TTL
- Service quotas: 1-hour TTL
- EC2 resources: 15-minute TTL

#### FR-1.4: orchestration-stepfunctions

**Purpose**: Wave-based orchestration logic for Step Functions

**Responsibilities**:
- Wave-based orchestration with pause/resume capability
- Tag-based server discovery at execution time
- Launch configuration synchronization (Protection Group → DRS)
- 15-second delays between server launches (DRS safety)
- Archive Pattern: Lambda owns state via OutputPath

**Input Parameters**:
```python
{
    "executionId": str,  # Execution UUID
    "planId": str,  # Recovery plan UUID
    "waveNumber": int,  # Current wave number
    "protectionGroupIds": List[str],  # Protection groups in wave
    "pauseBeforeWave": bool,  # Pause flag
    "taskToken": str  # Step Functions task token
}
```

**Output Format**:
```python
{
    "waveNumber": int,
    "status": str,  # COMPLETED/FAILED
    "serversRecovered": int,
    "jobIds": List[str],
    "errors": List[dict]
}
```

**Key Operations**:
- Get protection group servers
- Sync launch configuration to DRS
- Launch servers in parallel with 15-second delays
- Poll DRS job status
- Update execution state

**Performance Requirements**:
- Cold start: < 2 seconds
- Warm invocation: < 500ms
- Memory: 512 MB
- Timeout: 120 seconds

#### FR-1.5: frontend-deployer

**Purpose**: React frontend build and deployment (CloudFormation Custom Resource)

**Responsibilities**:
- Build React frontend (npm build)
- Deploy to S3 bucket
- Invalidate CloudFront cache
- Cleanup old deployment artifacts
- CloudFormation custom resource lifecycle

**Custom Resource Actions**:
- Create: Build and deploy frontend
- Update: Rebuild and redeploy frontend
- Delete: Cleanup deployment artifacts

**Performance Requirements**:
- Cold start: < 3 seconds
- Build time: 2-5 minutes
- Memory: 2048 MB
- Timeout: 900 seconds (15 minutes)

**Build Process**:
1. Download source from S3
2. Install npm dependencies
3. Run npm build
4. Upload build artifacts to S3
5. Invalidate CloudFront cache
6. Return success/failure to CloudFormation

#### FR-1.6: notification-formatter

**Purpose**: Format and send notifications (EventBridge target)

**Responsibilities**:
- Format SNS messages for execution events
- Send email notifications
- Format pipeline notifications
- Format security scan notifications

**Notification Types**:
- Execution started
- Execution completed
- Execution failed
- Wave completed
- System health alerts

**Performance Requirements**:
- Cold start: < 1 second
- Warm invocation: < 200ms
- Memory: 256 MB
- Timeout: 60 seconds

---

### FR-2: DynamoDB Tables

#### FR-2.1: protection-groups Table

**Table Name**: `{ProjectName}-protection-groups-{Environment}`

**Schema**: camelCase (migrated from PascalCase)

**Primary Key**:
- Partition Key: `groupId` (String) - UUID v4

**Attributes**:
```python
{
    "groupId": str,  # UUID v4 (camelCase)
    "groupName": str,  # 1-128 characters
    "description": str,  # Optional description
    "region": str,  # AWS region code
    "accountId": str,  # 12-digit AWS account ID
    "sourceServerIds": List[str],  # DRS source server IDs (camelCase)
    "serverCount": int,  # Number of servers
    "serverSelectionTags": dict,  # Tag-based selection criteria (camelCase)
    "launchConfiguration": dict,  # Launch configuration settings (camelCase)
    "createdAt": str,  # ISO 8601 timestamp (camelCase)
    "updatedAt": str,  # ISO 8601 timestamp (camelCase)
    "createdBy": str,  # User email
    "updatedBy": str  # User email (camelCase)
}
```

**Capacity**:
- Billing Mode: On-Demand
- Encryption: SSE-S3 (AWS-managed keys)
- Point-in-Time Recovery: Enabled
- Backup Retention: 35 days

**Access Patterns**:
- Get by groupId: O(1) lookup
- List all groups: Scan with pagination
- Filter by region: Scan with FilterExpression
- Filter by account: Scan with FilterExpression

#### FR-2.2: recovery-plans Table

**Table Name**: `{ProjectName}-recovery-plans-{Environment}`

**Schema**: camelCase (migrated from PascalCase)

**Primary Key**:
- Partition Key: `planId` (String) - UUID v4

**Attributes**:
```python
{
    "planId": str,  # UUID v4 (camelCase)
    "planName": str,  # 1-128 characters
    "description": str,  # Optional description
    "waves": List[dict],  # Wave configurations
    "totalWaves": int,  # Total number of waves
    "totalServers": int,  # Total servers across all waves
    "estimatedTotalDuration": int,  # Estimated duration in seconds
    "createdAt": str,  # ISO 8601 timestamp (camelCase)
    "updatedAt": str,  # ISO 8601 timestamp (camelCase)
    "createdBy": str,  # User email
    "updatedBy": str,  # User email (camelCase)
    "lastExecutionId": str,  # Most recent execution ID
    "lastExecutionStatus": str,  # Most recent execution status
    "lastExecutionDate": str  # Most recent execution timestamp (camelCase)
}
```

**Wave Structure**:
```python
{
    "waveNumber": int,  # Sequential wave number (1-N)
    "waveName": str,  # Wave display name
    "protectionGroupIds": List[str],  # Protection Group UUIDs
    "pauseBeforeWave": bool,  # Pause for manual validation
    "estimatedDuration": int  # Estimated duration in seconds
}
```

**Capacity**: Same as protection-groups table

**Access Patterns**:
- Get by planId: O(1) lookup
- List all plans: Scan with pagination
- Find plans using protection group: Scan with FilterExpression

#### FR-2.3: execution-history Table

**Table Name**: `{ProjectName}-execution-history-{Environment}`

**Schema**: camelCase (migrated from PascalCase)

**Primary Key**:
- Partition Key: `executionId` (String) - UUID v4
- Sort Key: `planId` (String)

**Global Secondary Indexes**:
- Index Name: `StatusIndex`
  - Partition Key: `status` (String)
- Index Name: `planIdIndex`
  - Partition Key: `planId` (String)

**Attributes**:
```python
{
    "executionId": str,  # UUID v4 (camelCase)
    "planId": str,  # Recovery plan UUID (camelCase)
    "planName": str,  # Recovery plan name
    "executionType": str,  # DRILL or RECOVERY
    "status": str,  # PENDING/POLLING/PAUSED/COMPLETED/FAILED/CANCELLED
    "currentWave": int,  # Current wave number
    "totalWaves": int,  # Total waves in plan
    "startTime": str,  # ISO 8601 timestamp (camelCase)
    "endTime": str,  # ISO 8601 timestamp (null if active, camelCase)
    "duration": int,  # Duration in seconds
    "initiatedBy": str,  # User email
    "accountContext": dict,  # Account context (camelCase)
    "stepFunctionArn": str,  # Step Functions execution ARN
    "taskToken": str,  # Task token for pause/resume
    "waves": List[dict],  # Per-wave status tracking (camelCase)
    "errors": List[dict],  # Error details
    "instancesTerminated": bool  # Termination status
}
```

**Wave Status Structure**:
```python
{
    "waveNumber": int,
    "waveName": str,
    "status": str,  # PENDING/RUNNING/COMPLETED/FAILED
    "startTime": int,
    "endTime": int,
    "duration": int,
    "serversRecovered": int,
    "jobIds": List[str],  # DRS job IDs
    "servers": List[dict]  # Per-server status
}
```

**Capacity**: Same as protection-groups table

**Access Patterns**:
- Get by executionId: O(1) lookup
- Query by status: GSI query on StatusIndex
- List all executions: Scan with pagination
- Find by planId: Scan with FilterExpression

#### FR-2.4: target-accounts Table

**Table Name**: `{ProjectName}-target-accounts-{Environment}`

**Schema**: camelCase (migrated from PascalCase)

**Primary Key**:
- Partition Key: `accountId` (String) - 12-digit AWS account ID

**Attributes**:
```python
{
    "accountId": str,  # 12-digit AWS account ID (camelCase)
    "accountName": str,  # Display name
    "status": str,  # Account status
    "IsCurrentAccount": bool,  # Is current account flag (PascalCase for compatibility)
    "IsDefault": bool,  # Is default account flag (PascalCase for compatibility)
    "crossAccountRoleArn": str,  # Cross-account IAM role ARN (camelCase)
    "regions": List[str],  # Supported AWS regions
    "validated": bool,  # Validation status
    "lastValidated": str,  # Last validation timestamp (camelCase)
    "createdAt": str,  # ISO 8601 timestamp (camelCase)
    "updatedAt": str,  # ISO 8601 timestamp (camelCase)
    "createdBy": str  # User email
}
```
}
```

**Capacity**: Same as protection-groups table

**Access Patterns**:
- Get by accountId: O(1) lookup
- List all accounts: Scan
- Filter by region: Scan with FilterExpression

---

### FR-3: Step Functions State Machine

**State Machine Name**: `{ProjectName}-DROrchestrator-{Environment}`

**Purpose**: Wave-based recovery plan execution with pause/resume

**Key States**:

1. **ValidateRecoveryPlan**: Validate plan exists and is executable
2. **InitializeExecution**: Create execution record in DynamoDB
3. **ProcessWaves**: Sequential wave execution (Map state)
4. **CheckPauseConfiguration**: Determine if pause required
5. **WaitForResumeSignal**: Pause with waitForTaskToken (if configured)
6. **ExecuteWave**: Start DRS recovery jobs for wave servers
7. **MonitorWaveCompletion**: Poll DRS job status until completion
8. **CheckWaveStatus**: Evaluate wave completion status
9. **WaitAndPoll**: 30-second wait between polling attempts
10. **WaveCompleted**: Finalize successful wave
11. **WaveFailed**: Handle wave failure
12. **WaveCancelled**: Handle user cancellation
13. **FinalizeExecution**: Update execution record with final status
14. **ExecutionCompleted**: Success state
15. **ExecutionFailed**: Failure state with error context

**Pause/Resume Pattern**:
```json
{
  "WaitForResumeSignal": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
    "Parameters": {
      "FunctionName": "orchestration-stepfunctions",
      "Payload": {
        "action": "pause_before_wave",
        "TaskToken.$": "$.Task.Token",
        "execution_id.$": "$.execution_id",
        "wave_number.$": "$.wave_number"
      }
    },
    "TimeoutSeconds": 31536000,
    "Next": "ExecuteWave"
  }
}
```

**Input Format**:
```python
{
    "planId": str,  # Recovery plan UUID
    "executionType": str,  # DRILL or RECOVERY
    "initiatedBy": str  # User email
}
```

**Output Format**:
```python
{
    "executionId": str,  # Execution UUID
    "status": str,  # Final status
    "wavesCompleted": int,  # Number of completed waves
    "totalWaves": int,  # Total waves
    "duration": int  # Duration in seconds
}
```

---

### FR-4: API Gateway (Optional)

**Deployment**: Conditional based on `DeployFrontend` parameter

**Architecture**: 6 nested CloudFormation stacks

#### FR-4.1: Core Stack

**Resources**:
- REST API
- Cognito authorizer
- Request validator
- CORS configuration

**Throttling**:
- Burst: 500 requests
- Sustained: 1,000 requests/second

#### FR-4.2: Resources Stack

**Path Structure**:
```
/
├── /protection-groups
│   ├── /{id}
│   └── /resolve
├── /recovery-plans
│   ├── /{id}
│   └── /{id}/execute
│   └── /{id}/check-existing-instances
├── /executions
│   ├── /{id}
│   ├── /{id}/pause
│   ├── /{id}/resume
│   ├── /{id}/cancel
│   ├── /{id}/terminate-instances
│   ├── /{id}/job-logs
│   ├── /{id}/termination-status
│   ├── /{id}/status
│   ├── /{id}/recovery-instances
│   └── /history
├── /drs
│   ├── /source-servers
│   ├── /quotas
│   ├── /capacity
│   └── /capacity/regional
├── /accounts
│   └── /{accountId}
│   └── /{accountId}/validate
├── /ec2
│   ├── /subnets
│   ├── /security-groups
│   ├── /instance-profiles
│   └── /instance-types
├── /config
│   ├── /export
│   ├── /tag-sync
│   └── /health
├── /users
│   └── /profile
└── /health
```

#### FR-4.3: Methods Stacks

**Core Methods Stack**:
- Health endpoints
- User profile
- Protection Groups CRUD
- Recovery Plans CRUD
- Configuration endpoints

**Operations Methods Stack**:
- Execution lifecycle
- Pause/resume/cancel
- Termination operations
- Job logs and status

**Infrastructure Methods Stack**:
- DRS discovery
- Account management
- EC2 resource discovery
- Health checks

#### FR-4.4: Deployment Stack

**Stage Configuration**:
- Stage name: `{Environment}`
- Deployment description: Auto-generated
- Cache settings: Disabled
- Logging: CloudWatch Logs enabled

---

### FR-5: RBAC Security

**Authentication**: Cognito JWT tokens (45-minute sessions)

**Authorization**: 5 roles with 11 granular permissions

#### FR-5.1: Roles and Permissions

**DRSOrchestrationAdmin**:
- All 11 permissions
- Full administrative access

**DRSRecoveryManager**:
- drs:ExecuteRecovery
- drs:ManageExecution
- drs:TerminateInstances
- drs:ViewResources

**DRSPlanManager**:
- drs:CreateProtectionGroup
- drs:UpdateProtectionGroup
- drs:CreateRecoveryPlan
- drs:UpdateRecoveryPlan
- drs:ViewResources

**DRSOperator**:
- drs:ExecuteRecovery
- drs:ViewResources

**DRSReadOnly**:
- drs:ViewResources

#### FR-5.2: Permission Enforcement

**Middleware**: `rbac_middleware.py`

**Enforcement Points**:
- API Gateway authorizer
- Lambda function entry point
- Frontend route guards
- Component-level rendering

**Permission Check Logic**:
```python
def check_permission(user_roles: List[str], required_permission: str) -> bool:
    role_permissions = {
        'DRSOrchestrationAdmin': ['*'],
        'DRSRecoveryManager': [
            'drs:ExecuteRecovery', 'drs:ManageExecution',
            'drs:TerminateInstances', 'drs:ViewResources'
        ],
        'DRSPlanManager': [
            'drs:CreateProtectionGroup', 'drs:UpdateProtectionGroup',
            'drs:CreateRecoveryPlan', 'drs:UpdateRecoveryPlan',
            'drs:ViewResources'
        ],
        'DRSOperator': ['drs:ExecuteRecovery', 'drs:ViewResources'],
        'DRSReadOnly': ['drs:ViewResources']
    }
    
    for role in user_roles:
        permissions = role_permissions.get(role, [])
        if '*' in permissions or required_permission in permissions:
            return True
    return False
```

---

### FR-6: Frontend Application (Optional)

**Deployment**: Conditional based on `DeployFrontend` parameter

**Technology Stack**:
- React 19.1.1
- TypeScript 5.9.3
- CloudScape Design System 3.0.1148
- AWS Amplify 6.15.8
- Vite 7.1.7

#### FR-6.1: Pages (8 Total)

1. **Dashboard**: Metrics, active executions, DRS quotas
2. **LoginPage**: Cognito authentication with password reset
3. **GettingStartedPage**: 3-step onboarding guide
4. **ProtectionGroupsPage**: CRUD with tag/server selection
5. **RecoveryPlansPage**: Wave-based plan management
6. **ExecutionsPage**: Active and historical monitoring
7. **ExecutionDetailsPage**: Detailed wave progress
8. **ExecutionDetailsPageMinimal**: Minimal execution view

#### FR-6.2: Key Components (35+ Total)

**Layout Components**:
- AppLayout
- Navigation
- Header
- Footer

**Data Display**:
- ProtectionGroupsTable
- RecoveryPlansTable
- ExecutionsTable
- WaveStatusTable
- ServerStatusTable

**Forms**:
- ProtectionGroupForm
- RecoveryPlanForm
- WaveConfigEditor
- ServerSelectionPanel
- TagCriteriaEditor

**Monitoring**:
- DRSQuotaStatus
- ExecutionProgress
- WaveProgress
- ServerStatus

**Security**:
- PermissionAware
- ProtectedRoute
- PasswordChangeForm

**Utilities**:
- AccountSelector
- RegionSelector
- LoadingIndicator
- ErrorBoundary

---

## Non-Functional Requirements

### NFR-1: Performance

| Metric | Requirement | Target |
|--------|-------------|--------|
| API Response Time | < 1 second | < 500ms p95 |
| Lambda Cold Start | < 2 seconds | 850-920ms |
| Frontend Load Time | < 3 seconds | < 2 seconds |
| DRS Job Polling | 30-second intervals | 30 seconds |
| Tag Sync Latency | < 5 minutes | Configurable (1-24 hours) |

### NFR-2: Scalability

| Dimension | Requirement |
|-----------|-------------|
| Source Servers | 1,000+ per account |
| Concurrent Executions | 10+ simultaneous |
| Protection Groups | 100+ per account |
| Recovery Plans | 50+ per account |
| API Requests | 1,000 req/sec |
| Multi-Region | All 30 DRS regions |

### NFR-3: Availability

| Component | Target | Implementation |
|-----------|--------|----------------|
| System Availability | 99.9% | Multi-AZ DynamoDB, Lambda |
| API Availability | 99.9% | API Gateway SLA |
| Frontend Availability | 99.9% | CloudFront + S3 |

### NFR-4: Security

**Encryption**:
- At Rest: DynamoDB SSE-S3, S3 SSE-S3/KMS
- In Transit: TLS 1.2+ for all connections

**Authentication**:
- Cognito JWT tokens
- 45-minute session timeout
- MFA support (optional)

**Authorization**:
- RBAC with 5 roles, 11 permissions
- API-level enforcement
- Audit trails in CloudWatch Logs

**Input Validation**:
- Comprehensive sanitization
- SQL injection prevention
- XSS attack prevention
- CSRF protection

### NFR-5: Monitoring

**CloudWatch Metrics**:
- Lambda invocations, errors, duration
- API Gateway requests, latency, errors
- Step Functions execution status
- DynamoDB read/write capacity

**CloudWatch Alarms**:
- Lambda error rate > 1%
- API Gateway 5xx errors
- Step Functions failed executions
- DynamoDB throttling

**SNS Notifications**:
- Execution completion
- Execution failures
- System health alerts

### NFR-6: Cost Optimization

**Monthly Operational Cost**:
- Full Stack: $12-40/month
- Backend-Only: $8-30/month (33% savings)

**Cost Controls**:
- On-Demand DynamoDB billing
- Lambda reserved concurrency (critical functions only)
- CloudFront caching (85-95% hit ratio)
- API Gateway throttling

---

## Data Validation Rules

### Protection Groups

**groupName**:
- Length: 1-128 characters
- Pattern: `^[a-zA-Z0-9-_]+$`
- Unique: Within account and region

**serverIds**:
- Format: `s-[0-9a-f]{17}`
- Validation: Must exist in DRS
- Conflict: Cannot be in active execution

**tagCriteria**:
- Keys: Valid AWS tag keys
- Values: Valid AWS tag values
- Limit: 50 tags maximum

**launchConfig**:
- subnet: Valid subnet ID
- securityGroups: Valid security group IDs
- instanceType: Valid EC2 instance type
- iamInstanceProfile: Valid IAM instance profile ARN

### Recovery Plans

**planName**:
- Length: 1-128 characters
- Pattern: `^[a-zA-Z0-9-_]+$`
- Unique: Within account

**waves**:
- waveNumber: Sequential integers starting from 1
- protectionGroupIds: Valid Protection Group UUIDs
- pauseBeforeWave: Boolean
- estimatedDuration: Positive integer (seconds)

### Executions

**executionType**:
- Values: DRILL, RECOVERY
- Required: Yes

**status**:
- Values: PENDING, POLLING, PAUSED, COMPLETED, FAILED, CANCELLED
- Transitions: PENDING → POLLING → PAUSED/COMPLETED/FAILED/CANCELLED

---

## API Response Formats

### Success Response

```json
{
  "success": true,
  "data": {
    "groupId": "uuid",
    "groupName": "string"
  },
  "timestamp": 1700000000
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "message": "Error description",
    "code": "ERROR_CODE"
  },
  "timestamp": 1700000000
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PUT |
| 201 | Created | Successful POST |
| 202 | Accepted | Async operation started |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid JWT |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate name, server conflict |
| 500 | Internal Server Error | Unexpected error |

---

## Deployment Modes

### Mode 1: Default Standalone

**Configuration**:
- OrchestrationRoleArn: empty
- DeployFrontend: true

**Components**:
- ✅ Unified orchestration IAM role
- ✅ All 6 Lambda functions
- ✅ API Gateway
- ✅ Frontend (S3 + CloudFront)
- ✅ DynamoDB tables
- ✅ Step Functions
- ✅ Cognito authentication

### Mode 2: API-Only Standalone

**Configuration**:
- OrchestrationRoleArn: empty
- DeployFrontend: false

**Components**:
- ✅ Unified orchestration IAM role
- ✅ All 6 Lambda functions
- ✅ API Gateway
- ❌ Frontend (not deployed)
- ✅ DynamoDB tables
- ✅ Step Functions
- ✅ Cognito authentication

### Mode 3: External Integration + Frontend

**Configuration**:
- OrchestrationRoleArn: provided
- DeployFrontend: true

**Components**:
- ❌ Unified orchestration IAM role (uses external)
- ✅ All 6 Lambda functions
- ✅ API Gateway
- ✅ Frontend (S3 + CloudFront)
- ✅ DynamoDB tables
- ✅ Step Functions
- ✅ Cognito authentication

### Mode 4: Full External Integration

**Configuration**:
- OrchestrationRoleArn: provided
- DeployFrontend: false

**Components**:
- ❌ Unified orchestration IAM role (uses external)
- ✅ All 6 Lambda functions
- ✅ API Gateway
- ❌ Frontend (not deployed)
- ✅ DynamoDB tables
- ✅ Step Functions
- ✅ Cognito authentication

---

## Testing Requirements

### Unit Testing

**Coverage Target**: > 80%

**Test Frameworks**:
- Python: pytest
- Frontend: vitest

**Test Categories**:
- Lambda function logic
- RBAC permission checks
- Input validation
- Error handling
- DynamoDB operations

### Integration Testing

**Test Scenarios**:
- End-to-end execution flow
- Cross-account operations
- Multi-wave execution
- Pause/resume functionality
- Error recovery

### Performance Testing

**Load Testing**:
- API Gateway: 1,000 req/sec
- Lambda concurrency: 100 concurrent
- DynamoDB throughput: On-demand scaling

**Stress Testing**:
- Large Protection Groups (100+ servers)
- Complex Recovery Plans (10+ waves)
- Concurrent executions (10+ simultaneous)

---

## Appendix

### Glossary

**Protection Group**: Logical grouping of DRS source servers

**Recovery Plan**: Multi-wave execution plan

**Wave**: Sequential execution phase

**Execution**: Instance of recovery plan execution

**DRS Source Server**: EC2 instance protected by AWS DRS

**Cross-Account Role**: IAM role for hub-and-spoke orchestration

**Unified Orchestration Role**: Consolidated IAM role for all Lambda functions

### References

- [Product Requirements Document](PRODUCT_REQUIREMENTS_DOCUMENT.md)
- [Architecture Guide](../architecture/ARCHITECTURE.md)
- [API and Integration Guide](../guides/API_AND_INTEGRATION_GUIDE.md)
- [Deployment Flexibility Guide](../guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md)

---

**Document Version History**:
- **v4.0**: Comprehensive update aligning with actual codebase implementation
  - Updated Lambda count: 5 → 6 functions (added frontend-deployer)
  - Updated API endpoints: 48 → 44 endpoints across 9 categories (not 12)
  - Updated CloudFormation templates: 18 → 16 templates
  - Updated frontend pages: 7 → 8 pages
  - Updated frontend components: 32+ → 35+ components
  - Corrected DynamoDB schema notation (camelCase)
  - Removed duplicate sections
  - Updated all deployment mode references
- **v3.5**: Comprehensive update reflecting decomposed Lambda architecture
- **v3.0**: Production-ready release
- **v2.0**: Beta release
- **v1.0**: Initial specification
