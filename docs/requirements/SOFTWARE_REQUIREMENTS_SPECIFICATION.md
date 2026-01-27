# Software Requirements Specification
# AWS DRS Orchestration System

**Version**: 3.5  
**Status**: Production Ready

---

## Document Purpose

This Software Requirements Specification (SRS) defines the functional and non-functional requirements for the AWS DRS Orchestration system. It serves as the authoritative source for system capabilities, API contracts, data models, and validation criteria.

---

## System Overview

### Architecture Components

**Compute Layer**:
- 5 Lambda functions (decomposed architecture)
- Step Functions state machine with waitForTaskToken
- EventBridge scheduled rules

**Data Layer**:
- 4 DynamoDB tables with GSI indexes
- S3 buckets for artifacts and static hosting

**API Layer** (Optional):
- API Gateway REST API with 48 endpoints
- Cognito User Pool with RBAC

**Frontend Layer** (Optional):
- React 19.1.1 + CloudScape Design System
- CloudFront CDN distribution
- S3 static website hosting

**Infrastructure**:
- 18 CloudFormation templates (1 master + 17 nested)
- 4 deployment modes (standalone, API-only, external integration)

---

## Functional Requirements

### FR-1: Lambda Functions

#### FR-1.1: orchestration-stepfunctions

**Purpose**: Entry point and Step Functions orchestration engine

**Responsibilities**:
- Route requests to specialized handlers (query, data-mgmt, execution)
- Start Step Functions workflows for recovery plan execution
- Track execution history in DynamoDB
- Wave-based orchestration with pause/resume capability

**Input Parameters**:
```python
{
    "action": str,  # Route action (query/crud/execute)
    "resource": str,  # Resource type
    "method": str,  # HTTP method
    "body": dict,  # Request payload
    "pathParameters": dict,  # URL path parameters
    "queryStringParameters": dict,  # Query parameters
    "requestContext": dict  # Cognito user context
}
```

**Output Format**:
```python
{
    "statusCode": int,  # HTTP status code
    "body": str,  # JSON-encoded response
    "headers": dict  # Response headers with CORS
}
```

**Key Operations**:
- Route to query-handler for read operations
- Route to data-mgmt-handler for CRUD operations
- Route to execution-handler for DR operations
- Start Step Functions execution for recovery plans
- Store task tokens for pause/resume functionality

**Performance Requirements**:
- Cold start: < 2 seconds
- Warm invocation: < 500ms
- Memory: 1024 MB
- Timeout: 5 minutes

#### FR-1.2: query-handler

**Purpose**: Read-only query operations

**Responsibilities**:
- List and describe operations
- DRS source server discovery
- Service quota monitoring
- Configuration export

**Endpoints (13 Total)**:
1. GET /protection-groups - List protection groups with filtering
2. GET /protection-groups/{id} - Get protection group details
3. GET /recovery-plans - List recovery plans with execution history
4. GET /recovery-plans/{id} - Get recovery plan details
5. GET /drs/source-servers - Discover DRS source servers
6. GET /drs/quotas - Get DRS service quotas
7. GET /accounts/current - Get current account information
8. GET /accounts/targets - List target accounts
9. GET /ec2/subnets - List EC2 subnets
10. GET /ec2/security-groups - List security groups
11. GET /ec2/instance-profiles - List IAM instance profiles
12. GET /ec2/instance-types - List EC2 instance types
13. GET /config/export - Export system configuration
14. GET /config/tag-sync - Get tag sync settings
15. GET /user/permissions - Get user permissions and roles

**Performance Requirements**:
- Cold start: < 2 seconds
- Warm invocation: < 500ms
- Memory: 512 MB
- Timeout: 30 seconds

**Caching Strategy**:
- DRS source servers: 5-minute TTL
- Service quotas: 1-hour TTL
- EC2 resources: 15-minute TTL

#### FR-1.3: data-mgmt-handler

**Purpose**: CRUD operations for Protection Groups and Recovery Plans

**Responsibilities**:
- Create, update, delete Protection Groups
- Create, update, delete Recovery Plans
- Configuration management
- Tag sync configuration

**Endpoints (21 Total)**:
1. POST /protection-groups - Create protection group
2. PUT /protection-groups/{id} - Update protection group
3. DELETE /protection-groups/{id} - Delete protection group
4. POST /protection-groups/resolve - Resolve tag-based servers
5. POST /recovery-plans - Create recovery plan
6. PUT /recovery-plans/{id} - Update recovery plan
7. DELETE /recovery-plans/{id} - Delete recovery plan
8. GET /recovery-plans/{id}/check-existing-instances - Check for existing recovery instances
9. POST /drs/tag-sync - Manual tag synchronization
10. GET /config/tag-sync - Get tag sync configuration
11. PUT /config/tag-sync - Update tag sync configuration
12. POST /config/import - Import system configuration
13. GET /accounts/targets - List target accounts
14. POST /accounts/targets - Create target account
15. GET /accounts/targets/{id} - Get target account details
16. PUT /accounts/targets/{id} - Update target account
17. DELETE /accounts/targets/{id} - Delete target account
18. POST /accounts/targets/{id}/validate - Validate cross-account access

**Validation Requirements**:
- Protection Group names: 1-128 characters, alphanumeric + hyphens
- Server IDs: Valid DRS source server ID format (s-[0-9a-f]{17})
- Tag criteria: Valid AWS tag key/value pairs
- Wave numbers: Positive integers, sequential
- Launch configuration: Valid EC2 parameters

**Performance Requirements**:
- Cold start: < 2 seconds
- Warm invocation: < 500ms
- Memory: 512 MB
- Timeout: 30 seconds

#### FR-1.4: execution-handler

**Purpose**: DR execution operations and monitoring

**Responsibilities**:
- Find active executions (EventBridge-triggered)
- Poll DRS job status
- Update execution state
- Finalize completed executions

**Endpoints (12 Total)**:
1. POST /executions - Start execution
2. DELETE /executions - Bulk delete executions
3. GET /executions - List executions with filtering
4. GET /executions/{id} - Get execution details
5. POST /executions/{id}/cancel - Cancel execution
6. POST /executions/{id}/pause - Pause execution
7. POST /executions/{id}/resume - Resume execution
8. POST /executions/{id}/terminate-instances - Terminate recovery instances
9. GET /executions/{id}/recovery-instances - Get recovery instances
10. GET /executions/{id}/job-logs - Get DRS job logs
11. GET /executions/{id}/termination-status - Check termination status
12. POST /recovery-plans/{id}/execute - Execute recovery plan

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
- Memory: 256 MB
- Timeout: 2 minutes

#### FR-1.5: notification-formatter

**Purpose**: Format and send notifications

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
- Timeout: 1 minute

---

### FR-2: DynamoDB Tables

#### FR-2.1: protection-groups Table

**Table Name**: `{ProjectName}-protection-groups-{Environment}`

**Primary Key**:
- Partition Key: `groupId` (String) - UUID v4

**Attributes**:
```python
{
    "groupId": str,  # UUID v4
    "groupName": str,  # 1-128 characters
    "description": str,  # Optional description
    "region": str,  # AWS region code
    "accountId": str,  # 12-digit AWS account ID
    "serverIds": List[str],  # DRS source server IDs
    "serverCount": int,  # Number of servers
    "tagCriteria": dict,  # Tag-based selection criteria
    "launchConfig": dict,  # Launch configuration settings
    "createdDate": int,  # Unix timestamp
    "lastModifiedDate": int,  # Unix timestamp
    "createdBy": str,  # User email
    "lastModifiedBy": str  # User email
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

**Primary Key**:
- Partition Key: `planId` (String) - UUID v4

**Attributes**:
```python
{
    "planId": str,  # UUID v4
    "planName": str,  # 1-128 characters
    "description": str,  # Optional description
    "waves": List[dict],  # Wave configurations
    "totalWaves": int,  # Total number of waves
    "totalServers": int,  # Total servers across all waves
    "estimatedTotalDuration": int,  # Estimated duration in seconds
    "createdDate": int,  # Unix timestamp
    "lastModifiedDate": int,  # Unix timestamp
    "createdBy": str,  # User email
    "lastModifiedBy": str,  # User email
    "lastExecutionId": str,  # Most recent execution ID
    "lastExecutionStatus": str,  # Most recent execution status
    "lastExecutionDate": int  # Most recent execution timestamp
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

**Primary Key**:
- Partition Key: `executionId` (String) - UUID v4

**Global Secondary Index**:
- Index Name: `StatusIndex`
- Partition Key: `status` (String)
- Sort Key: `startTime` (Number)

**Attributes**:
```python
{
    "executionId": str,  # UUID v4
    "planId": str,  # Recovery plan UUID
    "planName": str,  # Recovery plan name
    "executionType": str,  # DRILL or RECOVERY
    "status": str,  # PENDING/POLLING/PAUSED/COMPLETED/FAILED/CANCELLED
    "currentWave": int,  # Current wave number
    "totalWaves": int,  # Total waves in plan
    "startTime": int,  # Unix timestamp
    "endTime": int,  # Unix timestamp (null if active)
    "duration": int,  # Duration in seconds
    "initiatedBy": str,  # User email
    "stepFunctionArn": str,  # Step Functions execution ARN
    "taskToken": str,  # Task token for pause/resume
    "waveStatus": List[dict],  # Per-wave status tracking
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

**Primary Key**:
- Partition Key: `accountId` (String) - 12-digit AWS account ID

**Attributes**:
```python
{
    "accountId": str,  # 12-digit AWS account ID
    "accountName": str,  # Display name
    "roleArn": str,  # Cross-account IAM role ARN
    "externalId": str,  # External ID for role assumption
    "regions": List[str],  # Supported AWS regions
    "validated": bool,  # Validation status
    "lastValidated": int,  # Last validation timestamp
    "createdDate": int,  # Unix timestamp
    "lastModifiedDate": int,  # Unix timestamp
    "createdBy": str  # User email
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

#### FR-6.1: Pages (7 Total)

1. **Dashboard**: Metrics, active executions, DRS quotas
2. **LoginPage**: Cognito authentication with password reset
3. **GettingStartedPage**: 3-step onboarding guide
4. **ProtectionGroupsPage**: CRUD with tag/server selection
5. **RecoveryPlansPage**: Wave-based plan management
6. **ExecutionsPage**: Active and historical monitoring
7. **ExecutionDetailsPage**: Detailed wave progress

#### FR-6.2: Key Components (32+ Total)

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
- ✅ All 5 Lambda functions
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
- ✅ All 5 Lambda functions
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
- ✅ All 5 Lambda functions
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
- ✅ All 5 Lambda functions
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
- v3.5: Comprehensive update reflecting decomposed Lambda architecture and current implementation
- v3.0: Production-ready release
- v2.0: Beta release
- v1.0: Initial specification
