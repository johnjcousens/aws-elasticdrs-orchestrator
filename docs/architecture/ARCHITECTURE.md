# AWS DRS Orchestration - Complete Architecture Guide

**Version**: 3.0.0  
**Last Updated**: January 15, 2026  
**Status**: Production Ready

---

## Document Overview

This comprehensive architecture guide consolidates all architectural documentation for the AWS DRS Orchestration Solution, providing complete technical specifications, service integration patterns, data models, security architecture, and operational procedures.

**Consolidated from**:
- ARCHITECTURAL_DESIGN_DOCUMENT.md (2,385 lines)
- AWS_SERVICES_ARCHITECTURE_DEEP_DIVE.md (1,219 lines)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [High-Level Architecture](#high-level-architecture)
4. [Data Architecture](#data-architecture)
5. [AWS Service Integration](#aws-service-integration)
6. [Security Architecture](#security-architecture)
7. [Execution Engine](#execution-engine)
8. [API Architecture](#api-architecture)
9. [Frontend Architecture](#frontend-architecture)
10. [Deployment Architecture](#deployment-architecture)
11. [Performance and Scalability](#performance-and-scalability)
12. [Cost Optimization](#cost-optimization)

---

## System Overview

### Purpose and Scope

AWS DRS Orchestration is a serverless disaster recovery orchestration platform that enables enterprise organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native services.

### Key Capabilities

- **Wave-Based Recovery**: Execute disaster recovery in coordinated waves with explicit dependencies
- **Protection Groups**: Organize DRS source servers into logical groups for coordinated recovery
- **Pause/Resume Execution**: Pause execution before specific waves for manual validation
- **API-First Design**: Complete REST API (47+ endpoints) for DevOps integration
- **Enterprise-Grade**: Built on AWS serverless architecture with CloudFormation IaC
- **Cross-Account Support**: Multi-account DRS operations via assumed roles
- **Real-Time Monitoring**: Continuous DRS job status polling with CloudWatch metrics

### Technology Stack

**Frontend**:
- React 19.1.1 with TypeScript 5.9.3
- CloudScape Design System 3.0.1148 (AWS-native UI)
- AWS Amplify 6.15.8 for authentication
- Vite 7.1.7 for build tooling

**Backend**:
- AWS Lambda (Python 3.12 runtime)
- API Gateway with Cognito JWT authentication
- Step Functions orchestration with waitForTaskToken
- DynamoDB (4 tables with GSI)
- EventBridge for scheduled polling

**Infrastructure**:
- CloudFormation (15+ nested stacks)
- S3 for static hosting and artifacts
- CloudFront for global CDN
- CloudWatch for monitoring and logging

---

## Architecture Principles

### 1. Serverless-First

**Rationale**: Eliminate operational overhead, enable automatic scaling, and optimize costs through pay-per-use pricing.

**Implementation**:
- Lambda functions for all compute workloads
- DynamoDB for data persistence
- API Gateway for REST API
- Step Functions for orchestration
- S3 + CloudFront for frontend delivery

**Benefits**:
- Zero server management
- Automatic high availability
- Built-in security and compliance
- Cost efficiency at scale

### 2. Event-Driven Architecture

**Rationale**: Enable loose coupling, asynchronous processing, and real-time responsiveness.

**Implementation**:
- EventBridge triggers for scheduled polling
- Step Functions for workflow orchestration
- Lambda functions for event processing
- DynamoDB Streams for change tracking (optional)

**Benefits**:
- Decoupled components
- Scalable processing
- Real-time updates
- Fault tolerance

### 3. API-First Design

**Rationale**: Enable programmatic access, DevOps integration, and automation workflows.

**Implementation**:
- Complete REST API with 47+ endpoints
- OpenAPI specification compliance
- Comprehensive RBAC authorization
- Real-time integration with AWS DRS

**Benefits**:
- DevOps automation
- Third-party integration
- Consistent interfaces
- Extensibility

### 4. Security by Design

**Rationale**: Implement defense-in-depth security controls at every layer.

**Implementation**:
- Encryption at rest and in transit
- Least-privilege IAM policies
- JWT-based authentication
- CORS and security headers
- RBAC with 5 roles and 11 permissions

**Benefits**:
- Enterprise compliance
- Data protection
- Access control
- Audit trails

### 5. Infrastructure as Code

**Rationale**: Enable reproducible deployments, version control, and disaster recovery.

**Implementation**:
- CloudFormation templates (15+ stacks)
- Nested stack architecture
- Parameter-driven configuration
- Automated deployment pipelines

**Benefits**:
- Reproducible deployments
- Version control
- Disaster recovery
- Multi-environment support

---

## High-Level Architecture

### System Architecture Diagram

```mermaid
graph TB
    subgraph "User Layer"
        USER[End Users]
        DEVOPS[DevOps/Automation]
    end
    
    subgraph "Frontend Layer"
        CF[CloudFront CDN]
        S3_FE[S3 Static Hosting]
    end
    
    subgraph "API Layer"
        APIGW[API Gateway]
        COGNITO[Cognito User Pool]
    end
    
    subgraph "Application Layer"
        API_LAMBDA[api-handler Lambda]
        ORCH_LAMBDA[orchestration-stepfunctions Lambda]
        POLLER_LAMBDA[execution-poller Lambda]
        FINDER_LAMBDA[execution-finder Lambda]
    end
    
    subgraph "Orchestration Layer"
        STEPFN[Step Functions State Machine]
        EB[EventBridge Rules]
    end
    
    subgraph "Data Layer"
        DDB_PG[(Protection Groups)]
        DDB_RP[(Recovery Plans)]
        DDB_EH[(Execution History)]
        DDB_TA[(Target Accounts)]
    end
    
    subgraph "AWS Services"
        DRS[AWS DRS]
        EC2[EC2 Instances]
        SNS[SNS Notifications]
    end
    
    USER --> CF
    DEVOPS --> APIGW
    CF --> S3_FE
    CF --> APIGW
    APIGW --> COGNITO
    APIGW --> API_LAMBDA
    
    API_LAMBDA --> DDB_PG
    API_LAMBDA --> DDB_RP
    API_LAMBDA --> DDB_EH
    API_LAMBDA --> DDB_TA
    API_LAMBDA --> STEPFN
    
    STEPFN --> ORCH_LAMBDA
    ORCH_LAMBDA --> DRS
    ORCH_LAMBDA --> DDB_EH
    
    EB --> FINDER_LAMBDA
    FINDER_LAMBDA --> DDB_EH
    FINDER_LAMBDA --> POLLER_LAMBDA
    POLLER_LAMBDA --> DRS
    POLLER_LAMBDA --> EC2
    POLLER_LAMBDA --> DDB_EH
    
    ORCH_LAMBDA --> SNS
    
    DRS --> EC2
    
    style USER fill:#FF9900
    style DEVOPS fill:#FF9900
    style CF fill:#0066CC
    style APIGW fill:#0066CC
    style STEPFN fill:#E7157B
```


### Component Responsibilities

#### Frontend Layer
- **CloudFront**: Global content delivery, caching, security headers
- **S3**: Static website hosting for React application

#### API Layer
- **API Gateway**: REST API endpoint, request validation, throttling
- **Cognito**: User authentication, JWT token issuance, RBAC groups

#### Application Layer
- **api-handler**: CRUD operations, execution control, RBAC enforcement
- **orchestration-stepfunctions**: Wave execution, DRS integration, job monitoring
- **execution-poller**: Real-time DRS job status polling
- **execution-finder**: Discover active executions for polling

#### Orchestration Layer
- **Step Functions**: Wave-based orchestration, pause/resume control
- **EventBridge**: Scheduled polling triggers (1-minute intervals)

#### Data Layer
- **Protection Groups**: Server organization and assignment tracking
- **Recovery Plans**: Multi-wave recovery configurations
- **Execution History**: Real-time execution status and progress
- **Target Accounts**: Cross-account access configuration

#### AWS Services
- **AWS DRS**: Disaster recovery service integration
- **EC2**: Recovery instance health checks
- **SNS**: Execution completion notifications

---

## Data Architecture

### DynamoDB Table Design

#### 1. Protection Groups Table

**Table Name**: `aws-elasticdrs-orchestrator-protection-groups-{env}`

**Primary Key**:
- Partition Key: `groupId` (String) - UUID v4

**Attributes**:
```json
{
  "groupId": "pg-uuid",
  "groupName": "Web Tier Servers",
  "description": "Production web servers",
  "region": "us-east-1",
  "accountId": "{account-id}",
  "serverIds": ["s-1234567890abcdef0", "s-0987654321fedcba0"],
  "serverCount": 2,
  "tagCriteria": {
    "Environment": "production",
    "Tier": "web"
  },
  "createdDate": 1700000000,
  "lastModifiedDate": 1700000100,
  "createdBy": "user@example.com",
  "lastModifiedBy": "user@example.com"
}
```

**Access Patterns**:
- Get protection group by ID: `get_item(Key={'groupId': id})`
- List all protection groups: `scan()` with pagination
- Find groups by region: `scan(FilterExpression=region=X)`
- Find groups by account: `scan(FilterExpression=accountId=X)`

**Capacity**: On-Demand billing, SSE encryption, Point-in-Time Recovery, Automated backups

#### 2. Recovery Plans Table

**Table Name**: `aws-elasticdrs-orchestrator-recovery-plans-{env}`

**Primary Key**:
- Partition Key: `planId` (String) - UUID v4

**Attributes**:
```json
{
  "planId": "plan-uuid",
  "planName": "Production 3-Tier Application",
  "description": "Complete production stack recovery",
  "waves": [
    {
      "waveNumber": 1,
      "waveName": "Database Tier",
      "protectionGroupIds": ["pg-uuid-1"],
      "pauseBeforeWave": false,
      "estimatedDuration": 600
    },
    {
      "waveNumber": 2,
      "waveName": "Application Tier",
      "protectionGroupIds": ["pg-uuid-2"],
      "pauseBeforeWave": true,
      "estimatedDuration": 300
    },
    {
      "waveNumber": 3,
      "waveName": "Web Tier",
      "protectionGroupIds": ["pg-uuid-3"],
      "pauseBeforeWave": false,
      "estimatedDuration": 300
    }
  ],
  "totalWaves": 3,
  "totalServers": 6,
  "estimatedTotalDuration": 1200,
  "createdDate": 1700000000,
  "lastModifiedDate": 1700000100,
  "createdBy": "user@example.com",
  "lastModifiedBy": "user@example.com",
  "lastExecutionId": "exec-uuid",
  "lastExecutionStatus": "COMPLETED",
  "lastExecutionDate": 1700000500
}
```

**Access Patterns**:
- Get recovery plan by ID: `get_item(Key={'planId': id})`
- List all recovery plans: `scan()` with pagination
- Find plans using protection group: `scan(FilterExpression=contains(waves, groupId))`

**Capacity**: Same as Protection Groups table

#### 3. Execution History Table

**Table Name**: `aws-elasticdrs-orchestrator-execution-history-{env}`

**Primary Key**:
- Partition Key: `executionId` (String) - UUID v4

**Global Secondary Index**:
- Index Name: `StatusIndex`
- Partition Key: `status` (String)
- Sort Key: `startTime` (Number)

**Attributes**:
```json
{
  "executionId": "exec-uuid",
  "planId": "plan-uuid",
  "planName": "Production 3-Tier Application",
  "executionType": "DRILL",
  "status": "COMPLETED",
  "currentWave": 3,
  "totalWaves": 3,
  "startTime": 1700000000,
  "endTime": 1700001200,
  "duration": 1200,
  "initiatedBy": "user@example.com",
  "stepFunctionArn": "arn:aws:states:...",
  "taskToken": "encrypted-token",
  "waveStatus": [
    {
      "waveNumber": 1,
      "waveName": "Database Tier",
      "status": "COMPLETED",
      "startTime": 1700000000,
      "endTime": 1700000600,
      "duration": 600,
      "serversRecovered": 2,
      "jobIds": ["drsjob-123"],
      "servers": [
        {
          "serverId": "s-1234567890abcdef0",
          "hostname": "db-primary",
          "privateIp": "10.0.1.10",
          "instanceType": "r5.xlarge",
          "status": "LAUNCHED"
        }
      ]
    }
  ],
  "errors": [],
  "instancesTerminated": false
}
```

**Access Patterns**:
- Get execution by ID: `get_item(Key={'executionId': id})`
- List all executions: `scan()` with pagination
- Find active executions: `query(IndexName='StatusIndex', KeyConditionExpression=status=POLLING)`
- Find executions by plan: `scan(FilterExpression=planId=X)`

**Capacity**: Same as other tables with GSI provisioned capacity

#### 4. Target Accounts Table

**Table Name**: `aws-elasticdrs-orchestrator-target-accounts-{env}`

**Primary Key**:
- Partition Key: `accountId` (String) - 12-digit AWS account ID

**Attributes**:
```json
{
  "accountId": "{account-id}",
  "accountName": "Production Account",
  "roleArn": "arn:aws:iam::{account-id}:role/DRS-Orchestration-CrossAccount-Role",
  "externalId": "drs-orchestration-external-id",
  "regions": ["us-east-1", "us-west-2"],
  "validated": true,
  "lastValidated": 1700000000,
  "createdDate": 1700000000,
  "lastModifiedDate": 1700000100,
  "createdBy": "admin@example.com"
}
```

**Access Patterns**:
- Get account by ID: `get_item(Key={'accountId': id})`
- List all accounts: `scan()`
- Find accounts by region: `scan(FilterExpression=contains(regions, region))`

---

## AWS Service Integration

### Amazon DynamoDB - Data Persistence

**Service Role**: Primary data store for all application entities

**Configuration**:
- **Billing Mode**: On-Demand (automatic scaling)
- **Encryption**: AWS-managed keys (SSE-S3)
- **Backup**: Point-in-Time Recovery enabled
- **Retention**: Automated backups for 35 days

**Performance Characteristics**:
- **Read Latency**: <10ms p99
- **Write Latency**: <10ms p99
- **Throughput**: 40,000 RCU/WCU per table
- **Item Size**: 400KB maximum

**Access Patterns**:
```python
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('aws-elasticdrs-orchestrator-protection-groups-test')

# Get item by primary key
response = table.get_item(Key={'groupId': 'pg-uuid'})
item = response.get('Item')

# Query with GSI
table = dynamodb.Table('aws-elasticdrs-orchestrator-execution-history-test')
response = table.query(
    IndexName='StatusIndex',
    KeyConditionExpression=Key('status').eq('POLLING')
)
active_executions = response.get('Items', [])

# Scan with filter
response = table.scan(
    FilterExpression=Attr('region').eq('us-east-1')
)
filtered_items = response.get('Items', [])

# Update item with condition
table.update_item(
    Key={'groupId': 'pg-uuid'},
    UpdateExpression='SET #status = :status, lastModifiedDate = :timestamp',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={
        ':status': 'ACTIVE',
        ':timestamp': int(time.time())
    },
    ConditionExpression='attribute_exists(groupId)'
)
```

### AWS Lambda - Serverless Compute

**Service Role**: Execute all application logic and AWS service integrations

**Lambda Functions**:

1. **api-handler** (Primary API Function)
   - **Runtime**: Python 3.12
   - **Memory**: 512 MB
   - **Timeout**: 30 seconds
   - **Concurrency**: 100 reserved
   - **Purpose**: Handle all API Gateway requests, CRUD operations, execution control

2. **orchestration-stepfunctions** (Orchestration Engine)
   - **Runtime**: Python 3.12
   - **Memory**: 1024 MB
   - **Timeout**: 5 minutes
   - **Concurrency**: 50 reserved
   - **Purpose**: Wave execution, DRS integration, job monitoring

3. **execution-poller** (Status Monitoring)
   - **Runtime**: Python 3.12
   - **Memory**: 256 MB
   - **Timeout**: 2 minutes
   - **Concurrency**: 20 reserved
   - **Purpose**: Poll DRS job status, update execution records

4. **execution-finder** (Discovery)
   - **Runtime**: Python 3.12
   - **Memory**: 256 MB
   - **Timeout**: 1 minute
   - **Concurrency**: 10 reserved
   - **Purpose**: Find active executions for polling

5. **frontend-builder** (Deployment)
   - **Runtime**: Python 3.12
   - **Memory**: 2048 MB
   - **Timeout**: 10 minutes
   - **Concurrency**: 1 reserved
   - **Purpose**: Build and deploy React frontend

**Lambda Best Practices Implemented**:
- Environment variables for configuration
- Secrets Manager integration for sensitive data
- CloudWatch Logs for monitoring
- X-Ray tracing for debugging
- VPC integration (optional for private resources)
- Reserved concurrency for critical functions
- Dead letter queues for failed invocations

### AWS Step Functions - Orchestration Engine

**Service Role**: Coordinate wave-based recovery execution with pause/resume capability

**State Machine Type**: Standard (long-running workflows, at-least-once execution)

**Key Features**:
- **Pause/Resume**: waitForTaskToken pattern for indefinite pause (up to 1 year)
- **Wave-Based Execution**: Sequential wave processing with dependency validation
- **Error Handling**: Retry logic, exponential backoff, graceful degradation
- **Task Token Management**: Secure token storage in DynamoDB

**State Machine Flow**:
1. **ValidateRecoveryPlan** - Validate plan exists and is executable
2. **InitializeExecution** - Create execution record in DynamoDB
3. **ProcessWaves** - Sequential wave execution (Map state with MaxConcurrency=1)
   - **CheckPauseConfiguration** - Determine if pause required
   - **WaitForResumeSignal** - Pause with waitForTaskToken (if configured)
   - **ExecuteWave** - Start DRS recovery jobs for wave servers
   - **MonitorWaveCompletion** - Poll DRS job status until completion
   - **CheckWaveStatus** - Evaluate wave completion status
   - **WaitAndPoll** - 30-second wait between polling attempts
   - **WaveCompleted** - Finalize successful wave
   - **WaveFailed** - Handle wave failure
   - **WaveCancelled** - Handle user cancellation
4. **FinalizeExecution** - Update execution record with final status
5. **ExecutionCompleted** - Success state
6. **ExecutionFailed** - Failure state with error context

**Pause/Resume Implementation**:
```json
{
  "WaitForResumeSignal": {
    "Type": "Task",
    "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
    "Parameters": {
      "FunctionName": "orchestration-stepfunctions",
      "Payload": {
        "action": "pause_before_wave",
        "TaskToken.$": "$$.Task.Token",
        "execution_id.$": "$.execution_id",
        "wave_number.$": "$.wave_number"
      }
    },
    "TimeoutSeconds": 31536000,
    "Next": "ExecuteWave"
  }
}
```

**Resume Trigger**:
```python
# API handler receives resume request
def resume_execution(execution_id: str):
    # Get execution record with task token
    execution = get_execution_from_dynamodb(execution_id)
    task_token = execution['taskToken']
    
    # Send success signal to Step Functions
    stepfunctions_client.send_task_success(
        taskToken=task_token,
        output=json.dumps({'resumed': True})
    )
    
    # Update execution status
    update_execution_status(execution_id, 'POLLING')
```


### Amazon API Gateway - REST API

**Service Role**: Unified entry point for all 47+ REST API endpoints

**Configuration**:
- **Endpoint Type**: Regional (CloudFront handles CDN)
- **Authorization**: Cognito User Pool JWT tokens
- **Throttling**: 500 burst, 1,000 sustained requests/second
- **CORS**: Enabled for all endpoints

**Complete API Endpoint Catalog (47+ Endpoints)**:

**Protection Groups (6 endpoints)**:
- `GET /protection-groups` - List with filtering
- `POST /protection-groups` - Create with tag-based selection
- `GET /protection-groups/{id}` - Get details
- `PUT /protection-groups/{id}` - Update
- `DELETE /protection-groups/{id}` - Delete
- `POST /protection-groups/resolve` - Preview tag matches

**Recovery Plans (7 endpoints)**:
- `GET /recovery-plans` - List with execution history
- `POST /recovery-plans` - Create multi-wave plan
- `GET /recovery-plans/{id}` - Get details
- `PUT /recovery-plans/{id}` - Update
- `DELETE /recovery-plans/{id}` - Delete
- `POST /recovery-plans/{id}/execute` - Execute plan
- `GET /recovery-plans/{id}/check-existing-instances` - Check instances

**Executions (11 endpoints)**:
- `GET /executions` - List with advanced filtering
- `POST /executions` - Start execution
- `GET /executions/{id}` - Get detailed status
- `POST /executions/{id}/pause` - Pause execution
- `POST /executions/{id}/resume` - Resume execution
- `POST /executions/{id}/cancel` - Cancel execution
- `POST /executions/{id}/terminate-instances` - Terminate instances
- `GET /executions/{id}/job-logs` - Get DRS job logs
- `GET /executions/{id}/termination-status` - Check termination status
- `DELETE /executions` - Bulk delete
- `POST /executions/delete` - Delete specific executions

**DRS Integration (4 endpoints)**:
- `GET /drs/source-servers` - Discover servers
- `GET /drs/quotas` - Get service quotas
- `GET /drs/accounts` - Get account status
- `GET /drs/job-logs/{jobId}` - Get job logs

**Account Management (6 endpoints)**:
- `GET /accounts` - List cross-account access
- `POST /accounts` - Add account
- `GET /accounts/{accountId}` - Get account details
- `PUT /accounts/{accountId}` - Update account
- `DELETE /accounts/{accountId}` - Remove account
- `POST /accounts/{accountId}/validate` - Validate access

**EC2 Resources (4 endpoints)**:
- `GET /ec2/instances` - List recovery instances
- `GET /ec2/instances/{instanceId}` - Get instance details
- `POST /ec2/instances/terminate` - Terminate instances
- `GET /ec2/launch-templates` - List launch templates

**Configuration (4 endpoints)**:
- `GET /config/settings` - Get system configuration
- `PUT /config/settings` - Update settings
- `GET /config/regions` - List supported regions
- `GET /config/health` - System health check

**User Management (1 endpoint)**:
- `GET /users/profile` - Get user profile

**Health Check (1 endpoint)**:
- `GET /health` - API health status (no auth)

**API Response Format**:
```json
{
  "success": true,
  "data": {
    "groupId": "pg-uuid",
    "groupName": "Web Tier Servers"
  },
  "timestamp": 1700000000
}
```

**Error Response Format**:
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

**HTTP Status Codes**:
- 200 OK: Successful GET/PUT
- 201 Created: Successful POST
- 202 Accepted: Async operation started
- 204 No Content: Successful DELETE
- 400 Bad Request: Invalid input
- 401 Unauthorized: Missing/invalid JWT
- 403 Forbidden: Insufficient permissions
- 404 Not Found: Resource doesn't exist
- 409 Conflict: Duplicate name, server conflict
- 500 Internal Server Error: Unexpected error

### Amazon Cognito - Authentication

**Service Role**: User authentication and JWT token issuance

**User Pool Configuration**:
- **Password Policy**: Min 8 chars, uppercase, lowercase, numbers
- **MFA**: Optional (TOTP and SMS)
- **Token Expiration**: Access/ID tokens 45 minutes, Refresh token 30 days
- **Auto-Verified Attributes**: Email

**JWT Token Structure**:
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "cognito:groups": ["DRSOrchestrationAdmin"],
  "cognito:username": "user@example.com",
  "exp": 1700000000,
  "iat": 1699996400
}
```

**RBAC Groups**:
- **DRSOrchestrationAdmin**: All permissions
- **DRSRecoveryManager**: Execute, manage, view operations
- **DRSPlanManager**: Create/modify plans and groups
- **DRSOperator**: Execute recovery, view plans
- **DRSReadOnly**: View-only access

### Amazon S3 - Storage

**Service Role**: Static website hosting and deployment artifacts

**Frontend Hosting Bucket**:
- **Name**: `aws-elasticdrs-orchestrator-fe-{account-id}-{env}`
- **Purpose**: React application hosting
- **Encryption**: SSE-S3
- **Versioning**: Enabled
- **Public Access**: Blocked (CloudFront OAC only)

**Deployment Artifacts Bucket**:
- **Name**: `aws-elasticdrs-orchestrator`
- **Purpose**: CloudFormation templates and Lambda packages
- **Encryption**: SSE-KMS
- **Versioning**: Enabled
- **Structure**:
  - `cfn/` - CloudFormation templates
  - `lambda/` - Lambda deployment packages
  - `frontend/` - Frontend source for builder

### Amazon CloudFront - CDN

**Service Role**: Global content delivery for React frontend

**Configuration**:
- **Edge Locations**: 450+ worldwide
- **Cache Hit Ratio**: 85-95%
- **Global Latency**: <50ms p95
- **Compression**: Gzip and Brotli enabled

**Caching Strategy**:
- **Static Assets** (`/assets/*`): 1 year cache
- **HTML Files**: No cache (SPA routing)
- **Configuration** (`aws-config.json`): No cache

**Security Headers**:
- Strict-Transport-Security: 1 year
- Content-Type-Options: nosniff
- Frame-Options: DENY
- Content-Security-Policy: Restrictive policy

### Amazon EventBridge - Scheduling

**Service Role**: Trigger scheduled polling for active executions

**Rules**:
- **execution-finder-schedule**: Every 1 minute
- **Target**: execution-finder Lambda function
- **Purpose**: Discover active executions and trigger polling

### AWS DRS - Disaster Recovery

**Service Role**: Core disaster recovery service integration

**Integration APIs**:
```python
import boto3

drs_client = boto3.client('drs', region_name='us-east-1')

# Discover source servers
response = drs_client.describe_source_servers(
    filters={'isArchived': False},
    maxResults=100
)

# Start recovery
response = drs_client.start_recovery(
    sourceServers=[
        {'sourceServerID': 's-123', 'recoverySnapshotID': 'LATEST'}
    ],
    isDrill=True,
    tags={'ExecutionId': 'exec-123'}
)

# Monitor job status
response = drs_client.describe_jobs(
    filters={'jobIDs': ['drsjob-123']}
)
```

**Cross-Account Access**:
```python
# Assume role in spoke account
sts_client = boto3.client('sts')
assumed_role = sts_client.assume_role(
    RoleArn='arn:aws:iam::{account-id}:role/DRS-Orchestration-Role',
    RoleSessionName='drs-orchestration'
)

# Create DRS client with assumed credentials
drs_client = boto3.client(
    'drs',
    region_name='us-west-2',
    aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
    aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
    aws_session_token=assumed_role['Credentials']['SessionToken']
)
```

---

## Security Architecture

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Cognito
    participant API Gateway
    participant Lambda
    
    User->>Frontend: Enter credentials
    Frontend->>Cognito: InitiateAuth
    Cognito-->>Frontend: JWT tokens
    Frontend->>API Gateway: Request + JWT
    API Gateway->>Cognito: Validate JWT
    Cognito-->>API Gateway: Token valid
    API Gateway->>Lambda: Invoke with claims
    Lambda-->>API Gateway: Response
    API Gateway-->>Frontend: Response
```

### RBAC Authorization System

**5 Roles with 11 Granular Permissions**:

| Role | Permissions | Use Case |
|------|-------------|----------|
| DRSOrchestrationAdmin | All 11 permissions | Full administrative access |
| DRSRecoveryManager | Execute, manage, view | Recovery team leads |
| DRSPlanManager | Create/modify plans | DR architects |
| DRSOperator | Execute, view | Operations staff |
| DRSReadOnly | View only | Monitoring, auditing |

**11 Granular Permissions**:
1. `drs:CreateProtectionGroup`
2. `drs:UpdateProtectionGroup`
3. `drs:DeleteProtectionGroup`
4. `drs:CreateRecoveryPlan`
5. `drs:UpdateRecoveryPlan`
6. `drs:DeleteRecoveryPlan`
7. `drs:ExecuteRecovery`
8. `drs:ManageExecution`
9. `drs:TerminateInstances`
10. `drs:ViewResources`
11. `drs:ManageAccounts`

**RBAC Middleware**:
```python
def check_permission(user_roles: List[str], required_permission: str) -> bool:
    """Check if user has required permission"""
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

### IAM Roles

**Lambda Execution Role**:
- DynamoDB: GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan
- DRS: DescribeSourceServers, StartRecovery, DescribeJobs, TerminateRecoveryInstances
- EC2: DescribeInstances, DescribeInstanceStatus, TerminateInstances
- Step Functions: StartExecution, DescribeExecution, SendTaskSuccess
- STS: AssumeRole (cross-account)

**Step Functions Execution Role**:
- Lambda: InvokeFunction

**Cross-Account Role** (in spoke accounts):
- DRS: DescribeSourceServers, StartRecovery, DescribeJobs
- EC2: DescribeInstances, DescribeInstanceStatus

### Encryption

**Data at Rest**:
- DynamoDB: AWS-managed keys (SSE-S3)
- S3: SSE-S3 (frontend), SSE-KMS (artifacts)
- CloudWatch Logs: AWS-managed keys

**Data in Transit**:
- Frontend ↔ CloudFront: HTTPS (TLS 1.2+)
- CloudFront ↔ API Gateway: HTTPS
- API Gateway ↔ Lambda: AWS internal encryption
- Lambda ↔ DynamoDB: AWS internal encryption
- Lambda ↔ DRS: HTTPS (boto3 TLS)

---

## Execution Engine

### Wave-Based Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant StepFn as Step Functions
    participant Lambda as orchestration-stepfunctions
    participant DRS
    participant DDB as DynamoDB
    
    User->>API: POST /recovery-plans/{id}/execute
    API->>StepFn: StartExecution
    StepFn->>Lambda: ValidateRecoveryPlan
    Lambda->>DDB: Get recovery plan
    Lambda-->>StepFn: Plan valid
    
    loop For each wave
        alt Pause configured
            StepFn->>Lambda: WaitForResumeSignal (waitForTaskToken)
            Lambda->>DDB: Store task token
            Lambda-->>User: Execution paused
            User->>API: POST /executions/{id}/resume
            API->>StepFn: SendTaskSuccess(taskToken)
        end
        
        StepFn->>Lambda: ExecuteWave
        Lambda->>DRS: StartRecovery (all servers)
        DRS-->>Lambda: Job IDs
        Lambda->>DDB: Update wave status
        
        loop Poll until complete
            StepFn->>Lambda: MonitorWaveCompletion
            Lambda->>DRS: DescribeJobs
            DRS-->>Lambda: Job status
            alt Jobs complete
                Lambda->>DDB: Update wave COMPLETED
            else Jobs running
                StepFn->>StepFn: Wait 30 seconds
            end
        end
    end
    
    StepFn->>Lambda: FinalizeExecution
    Lambda->>DDB: Update execution COMPLETED
```

### Real-Time Polling Architecture

```mermaid
graph TB
    EB[EventBridge<br/>1-minute schedule] -->|Trigger| Finder[execution-finder]
    Finder -->|Query StatusIndex| DDB[(DynamoDB)]
    DDB -->|Active executions| Finder
    Finder -->|Invoke for each| Poller[execution-poller]
    Poller -->|DescribeJobs| DRS[AWS DRS]
    DRS -->|Job status| Poller
    Poller -->|Update status| DDB
    Poller -->|Publish metrics| CW[CloudWatch]
```

**Polling Logic**:
1. EventBridge triggers execution-finder every 1 minute
2. execution-finder queries StatusIndex for `status=POLLING`
3. For each active execution, invoke execution-poller
4. execution-poller polls DRS job status
5. Update execution record with current status
6. Publish CloudWatch metrics

---

## Frontend Architecture

### Technology Stack

- **React**: 19.1.1 with TypeScript 5.9.3
- **UI Framework**: CloudScape Design System 3.0.1148
- **Authentication**: AWS Amplify 6.15.8
- **Build Tool**: Vite 7.1.7
- **Routing**: React Router 7.9.5

### Component Structure

**32 Total Components**:

**Page Components (7)**:
- LoginPage, Dashboard, GettingStartedPage
- ProtectionGroupsPage, RecoveryPlansPage
- ExecutionsPage, ExecutionDetailsPage

**Reusable Components (16)**:
- Layout: AppLayout, ContentLayout, ErrorBoundary
- Dialogs: ProtectionGroupDialog, RecoveryPlanDialog, ConfirmDialog
- Server Management: ServerSelector, ServerDiscoveryPanel
- Status Display: StatusBadge, WaveProgress, DateTimeDisplay
- Execution: ExecutionDetails

**DRS Management Components (9)**:
- LaunchSettingsDialog, EC2TemplateEditor, TagsEditor
- DiskSettingsEditor, ReplicationSettingsEditor
- PostLaunchSettingsEditor, ServerInfoPanel
- PitPolicyEditor, JobEventsTimeline

### State Management

**React Context**:
- AuthContext: User authentication state
- NotificationContext: Toast notifications

**Local State**:
- Component-level useState for UI state
- useEffect for data fetching and polling

**API Integration**:
```typescript
// API client with authentication
class APIClient {
  async getProtectionGroups(): Promise<ProtectionGroup[]> {
    const token = await Auth.currentSession().getIdToken().getJwtToken();
    const response = await fetch(`${API_URL}/protection-groups`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }
}
```

### Real-Time Updates

**Polling Strategy**:
- Active executions: Poll every 3 seconds
- Execution list: Poll every 10 seconds
- Protection groups/plans: No polling (user-triggered refresh)

---

## Deployment Architecture

### CloudFormation Stack Structure

**Master Template** (`master-template.yaml`):
- Orchestrates 14+ nested stacks
- Parameter-driven configuration
- Cross-stack references

**Nested Stacks**:
1. `database-stack.yaml` - 4 DynamoDB tables
2. `lambda-stack.yaml` - 7 Lambda functions
3. `api-gateway-core-stack.yaml` - API Gateway base
4. `api-gateway-resources-stack.yaml` - API resources
5. `api-gateway-core-methods-stack.yaml` - CRUD methods
6. `api-gateway-operations-methods-stack.yaml` - Execution methods
7. `api-gateway-infrastructure-methods-stack.yaml` - Discovery methods
8. `api-gateway-deployment-stack.yaml` - API deployment
9. `api-auth-stack.yaml` - Cognito User Pool
10. `step-functions-stack.yaml` - Orchestration state machine
11. `eventbridge-stack.yaml` - Scheduled rules
12. `security-stack.yaml` - WAF, CloudTrail
13. `frontend-stack.yaml` - S3, CloudFront
14. `notification-stack.yaml` - SNS topics

**Deployment Parameters**:
- Environment: test, dev, prod
- AdminEmail: Administrator email
- DeploymentBucket: S3 bucket for artifacts

**Deployment Command**:
```bash
aws cloudformation create-stack \
  --stack-name aws-elasticdrs-orchestrator-test \
  --template-body file://cfn/master-template.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=test \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
    ParameterKey=DeploymentBucket,ParameterValue=aws-elasticdrs-orchestrator \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### CI/CD Pipeline

**GitHub Actions Workflow**:
1. **Detect Changes** - Analyze changed files
2. **Validate** - CloudFormation validation, linting
3. **Security Scan** - Bandit, Safety checks
4. **Build** - Lambda packaging, frontend build
5. **Test** - Unit tests
6. **Deploy Infrastructure** - CloudFormation stack update
7. **Deploy Frontend** - S3 sync, CloudFront invalidation

**Concurrency Control**:
```yaml
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false
```

**Deployment Time**:
- Documentation-only: ~30 seconds
- Frontend-only: ~12 minutes
- Full deployment: ~22 minutes

---

## Performance and Scalability

### Performance Characteristics

**API Response Times**:
- Simple CRUD: <100ms p95
- DRS Discovery: 200-500ms p95
- Execution Start: <200ms p95
- Complex Queries: 100-300ms p95

**Throughput Capacity**:
- API Requests: 1,000 requests/second sustained
- Concurrent Executions: 100+ simultaneous
- DynamoDB: 40,000 RCU/WCU per table
- Frontend Delivery: Unlimited (CloudFront)

**Scalability Limits**:
- Step Functions: 25,000 executions/second/region
- Lambda: 1,000 concurrent executions
- DynamoDB: 40,000 RCU/WCU per table (auto-scaling)
- API Gateway: 10,000 requests/second/region

---

## Cost Optimization

### Estimated Monthly Costs

**Production Environment** (1,000 API calls, 50 executions):
- DynamoDB: $5-10 (on-demand)
- Lambda: $10-20 (compute time)
- API Gateway: $3-5 (requests)
- Step Functions: $2-5 (state transitions)
- S3: $1-2 (storage + requests)
- CloudFront: $5-10 (data transfer)
- Cognito: $0-5 (MAU based)
- Other services: $5-10

**Total**: $30-70/month for typical production usage

### Cost Optimization Strategies

1. **Serverless Pay-Per-Use**: No idle infrastructure costs
2. **Efficient Data Storage**: DynamoDB on-demand, S3 lifecycle policies
3. **Resource Right-Sizing**: Optimized Lambda memory allocation
4. **CloudFront Caching**: Reduces origin requests by 85-95%

---

## Summary

The AWS DRS Orchestration Solution implements a comprehensive serverless architecture that provides enterprise-grade disaster recovery orchestration capabilities while maintaining cost efficiency, operational simplicity, and security best practices through AWS-native service integration.

**Key Architectural Strengths**:
- Serverless-first design eliminates operational overhead
- Event-driven architecture enables real-time responsiveness
- API-first approach supports DevOps automation
- Security by design with defense-in-depth controls
- Infrastructure as Code ensures reproducible deployments
- Wave-based execution with pause/resume control
- Cross-account support for multi-account environments
- Real-time monitoring and comprehensive logging

**Production Readiness**:
- All systems operational and tested
- Complete API coverage (47+ endpoints)
- Comprehensive RBAC with 5 roles and 11 permissions
- Enterprise-grade security and compliance
- Automated CI/CD pipeline with intelligent optimization
- Performance targets met across all services
- Cost-optimized for production workloads

