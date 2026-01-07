# Software Requirements Specification
# AWS DRS Orchestration System

**Version**: 3.0  
**Date**: January 7, 2026  
**Status**: Production Ready - Complete Implementation

---

## Document Purpose

This Software Requirements Specification (SRS) defines the functional and non-functional requirements for the AWS DRS Orchestration system based on the actual implemented codebase. It serves as the authoritative source for system capabilities, API contracts, and validation criteria.

---

## System Architecture

The system implements a 6-nested-stack API Gateway architecture with comprehensive DRS API coverage:

- **Master Template**: Orchestrates 15+ nested CloudFormation stacks
- **API Gateway**: 6 modular stacks with 80+ resources supporting 47+ DRS operations
- **Lambda Functions**: 7 production functions with specialized roles
- **DynamoDB**: 4 tables with optimistic locking and GSI indexes
- **Step Functions**: Orchestration with waitForTaskToken pattern
- **Frontend**: React 19 + CloudScape with 32+ components

---

## Functional Requirements

### FR-1: Lambda Functions (7 Production Functions)

#### FR-1.1: API Handler Lambda
**Function**: `api-handler`
**Purpose**: Main REST API handler with comprehensive DRS integration

**Capabilities**:
- 47+ DRS API operations across all categories
- RBAC middleware with 5 granular roles and 14 permissions
- Multi-account cross-account role assumption
- Input validation and security sanitization
- Comprehensive error handling with detailed responses

**Key Features**:
- EventBridge authentication bypass for tag synchronization
- Server conflict detection across active executions and DRS jobs
- Tag-based server selection with DRS source server tags
- Launch configuration management for Protection Groups
- Optimistic locking with version control

#### FR-1.2: Orchestration Step Functions Lambda
**Function**: `orchestration-stepfunctions`
**Purpose**: Step Functions orchestration engine

**Capabilities**:
- Wave-by-wave execution with pause/resume via waitForTaskToken
- DRS job monitoring with participatingServers tracking
- Cross-account DRS client creation with STS role assumption
- Recovery instance termination with job status tracking

#### FR-1.3: Execution Management Lambdas
**Functions**: `execution-finder`, `execution-poller`

**execution-finder**:
- Queries StatusIndex GSI for executions in POLLING status
- EventBridge-triggered every 1 minute
- Invokes execution-poller for active executions

**execution-poller**:
- Polls DRS job status and updates execution wave states
- Tracks participatingServers launchStatus progression
- Updates DynamoDB with real-time execution progress

#### FR-1.4: Infrastructure Support Lambdas
**Functions**: `frontend-builder`, `bucket-cleaner`, `notification-formatter`

**frontend-builder**:
- CloudFormation custom resource for frontend deployment
- S3 sync and CloudFront invalidation
- Dynamic AWS configuration injection

**bucket-cleaner**:
- S3 bucket cleanup for CloudFormation stack deletion
- Handles versioned objects and large buckets

**notification-formatter**:
- Formats pipeline and security scan notifications
- SNS integration for email notifications

### FR-2: API Gateway Architecture (6-Nested-Stack Design)

#### FR-2.1: Core Stack
**Template**: `api-gateway-core-stack.yaml`
**Resources**: REST API, Cognito authorizer, request validator

#### FR-2.2: Resources Stack
**Template**: `api-gateway-resources-stack.yaml`
**Resources**: 80+ API path definitions across all categories

**Resource Categories**:
- Health Check (no authentication)
- User Management (profile, roles, permissions)
- Protection Groups (CRUD, resolve, launch-config)
- Recovery Plans (CRUD, execute, check-existing-instances)
- Executions (CRUD, cancel, pause, resume, terminate-instances, job-logs)
- DRS Operations (47+ operations across 8 categories)
- EC2 Resources (subnets, security-groups, instance-profiles, instance-types)
- Configuration Management (export, import, tag-sync)
- Multi-Account Management (targets, validation)

#### FR-2.3: Methods Stacks
**Templates**: 
- `api-gateway-core-methods-stack.yaml`: Health, User, Protection Groups, Recovery Plans
- `api-gateway-operations-methods-stack.yaml`: All Execution endpoints
- `api-gateway-infrastructure-methods-stack.yaml`: DRS, EC2, Config, Target Accounts

#### FR-2.4: Deployment Stack
**Template**: `api-gateway-deployment-stack.yaml`
**Purpose**: Deployment orchestrator with timestamp-based redeployment

### FR-3: DRS API Integration (47+ Operations)

#### FR-3.1: Failover Operations
- `POST /drs/failover/start-recovery`: Start recovery with comprehensive validation
- `POST /drs/failover/terminate-instances`: Terminate recovery instances
- `POST /drs/failover/disconnect-instance`: Disconnect recovery instance

#### FR-3.2: Failback Operations
- `POST /drs/failback/reverse-replication`: Reverse replication direction
- `POST /drs/failback/start-failback`: Start failback process
- `POST /drs/failback/stop-failback`: Stop failback process
- `GET/PUT /drs/failback/configuration`: Failback configuration management

#### FR-3.3: Replication Management
- `POST /drs/replication/start`: Start replication
- `POST /drs/replication/stop`: Stop replication
- `POST /drs/replication/pause`: Pause replication
- `POST /drs/replication/resume`: Resume replication
- `POST /drs/replication/retry`: Retry data replication
- `GET/PUT /drs/replication/configuration`: Replication configuration
- `GET/PUT /drs/replication/template`: Replication configuration template

#### FR-3.4: Source Server Management
- `GET /drs/source-server/{id}`: Get source server details
- `POST /drs/source-server/{id}/disconnect`: Disconnect source server
- `POST /drs/source-server/{id}/archive`: Mark as archived
- `GET /drs/extended-source-servers`: List extended source servers
- `GET /drs/extensible-source-servers`: List extensible source servers

#### FR-3.5: Source Network Management
- `GET /drs/source-networks`: List source networks
- `GET /drs/source-networks/{id}`: Get source network details
- `POST /drs/source-networks/recovery`: Start source network recovery
- `POST /drs/source-networks/replication`: Start source network replication
- `GET /drs/source-networks/stack`: Get source network stack
- `GET /drs/source-networks/template`: Get source network template

#### FR-3.6: Launch Configuration Management
- `GET/PUT /drs/launch-configuration`: Launch configuration management
- `GET/PUT /drs/launch-configuration/template`: Launch configuration template
- `GET /drs/launch-actions`: List launch actions
- `GET/PUT /drs/launch-actions/{id}`: Launch action management

#### FR-3.7: Job Management
- `GET /drs/jobs`: List DRS jobs with filtering
- `GET /drs/jobs/{id}`: Get job details
- `GET /drs/jobs/{id}/logs`: Get job logs

#### FR-3.8: Service Management
- `POST /drs/service/initialize`: Initialize DRS service
- `GET /drs/recovery-instances`: List recovery instances
- `GET /drs/recovery-instances/{id}`: Get recovery instance details
- `GET /drs/recovery-snapshots`: List recovery snapshots

### FR-4: RBAC Security System

#### FR-4.1: Role-Based Access Control
**Implementation**: `rbac_middleware.py`

**Security Roles (5 Granular Roles)**:
1. **DRSOrchestrationAdmin**: Full administrative access
2. **DRSRecoveryManager**: Recovery operations and configuration
3. **DRSPlanManager**: Protection Groups and Recovery Plans management
4. **DRSOperator**: Execute drills only
5. **DRSReadOnly**: View-only access

**Granular Permissions (14 Business-Focused)**:
- Protection Groups: CREATE_PROTECTION_GROUP, UPDATE_PROTECTION_GROUP, DELETE_PROTECTION_GROUP
- Recovery Plans: CREATE_RECOVERY_PLAN, UPDATE_RECOVERY_PLAN, DELETE_RECOVERY_PLAN
- Executions: EXECUTE_RECOVERY, EXECUTE_DRILL, CONTROL_EXECUTION, TERMINATE_INSTANCES
- Configuration: EXPORT_CONFIG, IMPORT_CONFIG
- Server Management: MANAGE_SERVERS, VIEW_SERVERS

#### FR-4.2: Security Implementation
**Files**: `rbac_middleware.py`, `security_utils.py`

**Security Features**:
- JWT token validation with Cognito Groups integration
- Input validation and sanitization for all requests
- Comprehensive audit logging with role context
- Security headers for all responses
- Protection against SQL injection, XSS, command injection, log injection

#### FR-4.3: User Management
**Components**: `PasswordChangeForm`, `ProtectedRoute`

**Features**:
- Password reset capability for Cognito users
- Activity-based timeout (4 hours) with comprehensive tracking
- Automatic token refresh (50 minutes)
- Multi-factor authentication support

### FR-5: Frontend Application (7 Pages, 32+ Components)

#### FR-5.1: Pages
**Technology**: React 19.1.1 + TypeScript 5.9.3 + CloudScape 3.0.1148

**Page Components**:
- **Dashboard**: Metrics, pie charts, active executions, DRS quotas
- **LoginPage**: Cognito authentication with password reset
- **GettingStartedPage**: 3-step onboarding guide
- **ProtectionGroupsPage**: CRUD table with tag/server selection
- **RecoveryPlansPage**: Wave-based plan management
- **ExecutionsPage**: Active and historical execution monitoring
- **ExecutionDetailsPage**: Detailed execution view with controls

#### FR-5.2: Core Components (32+ Total)

**CloudScape Wrappers (2)**:
- **AppLayout**: Main application layout with navigation
- **ContentLayout**: Page content wrapper

**Multi-Account Management (4)**:
- **AccountSelector**: Account context switching dropdown
- **AccountRequiredWrapper**: Feature enforcement wrapper
- **AccountRequiredGuard**: Route-level account enforcement
- **AccountManagementPanel**: Account configuration panel

**RBAC & Security (3)**:
- **PermissionAware**: Permission-based conditional rendering
- **PasswordChangeForm**: Secure password change with Cognito
- **ProtectedRoute**: Route-level permission enforcement

**Server Management (4)**:
- **ServerSelector**: Server selection with conflict detection
- **ServerDiscoveryPanel**: Real-time DRS server discovery
- **ServerListItem**: Server display with hardware details
- **RegionSelector**: All 30 DRS regions selector

**Execution Management (3)**:
- **ExecutionDetails**: Real-time execution monitoring
- **WaveProgress**: Wave-by-wave progress tracking
- **WaveConfigEditor**: Multi-wave configuration editor

**Configuration Management (4)**:
- **ConfigExportPanel**: Configuration export functionality
- **ConfigImportPanel**: Configuration import with validation
- **TagSyncConfigPanel**: EventBridge tag sync configuration
- **LaunchConfigSection**: DRS launch settings configuration

**Status & Display (4)**:
- **StatusBadge**: Execution and server status indicators
- **InvocationSourceBadge**: Execution source tracking
- **DateTimeDisplay**: Consistent date/time formatting
- **DRSQuotaStatus**: Real-time service limits monitoring

**Dialogs & Modals (5)**:
- **ProtectionGroupDialog**: Protection Group CRUD with tabs
- **RecoveryPlanDialog**: Recovery Plan CRUD with wave editor
- **ConfirmDialog**: Confirmation dialogs with context
- **ImportResultsDialog**: Import results display
- **SettingsModal**: Application settings management

**Layout & Utility (6)**:
- **ErrorBoundary**: Error boundary with fallback UI
- **ErrorFallback**: Error display component
- **ErrorState**: Error state display
- **LoadingState**: Loading state indicators
- **CardSkeleton**: Loading skeleton for cards
- **DataTableSkeleton**: Loading skeleton for tables
- **PageTransition**: Smooth page transitions

**React Contexts (6)**:
- **AuthContext**: Authentication state management
- **PermissionsContext**: RBAC permissions caching
- **NotificationContext**: Toast notification management
- **ApiContext**: API client configuration
- **AccountContext**: Multi-account state management
- **SettingsContext**: Application settings persistence

### FR-6: Multi-Account Management

#### FR-6.1: Target Accounts Table
**Table**: `target-accounts-{env}`
**Schema**: `AccountId` (PK), `AssumeRoleName`, `CrossAccountRoleArn`, `IsDefault`
**GSI**: StatusIndex for health monitoring

#### FR-6.2: Cross-Account Operations
**Implementation**: STS role assumption with account context propagation

**Features**:
- Hub-and-spoke architecture with centralized orchestration
- Cross-account DRS client creation with credential management
- Account health monitoring and validation
- Scale beyond 300-server DRS limit per account

### FR-7: Tag Synchronization with EventBridge

#### FR-7.1: EventBridge Integration
**Function**: `api-handler` with EventBridge authentication bypass
**Security**: Multi-layer validation for EventBridge requests

**Validation Layers**:
1. Source IP validation (sourceIp === 'eventbridge')
2. Invocation source verification (X-Amz-Invocation-Source === 'EVENTBRIDGE')
3. API Gateway context validation (requestId, stage)
4. Authentication header validation (no unexpected Authorization headers)
5. EventBridge rule name validation (pattern matching)

#### FR-7.2: Tag Synchronization Process
**Endpoint**: `POST /drs/tag-sync`

**Features**:
- EC2 to DRS source server tag synchronization
- Cross-region support for all 30 DRS regions
- Batch processing with 10-server chunks
- Real-time progress monitoring
- Comprehensive error handling and audit trails

### FR-8: Performance Optimizations

#### FR-8.1: Backend Optimizations
- **Batch DynamoDB Operations**: Reduce API calls through batch operations
- **Optimized Query Patterns**: Efficient data access with GSI indexes
- **Connection Pooling**: Reuse AWS service connections
- **Smart Conflict Detection**: Fast server conflict validation
- **Reduced Scan Scope**: Limit data scanning to relevant records

#### FR-8.2: Frontend Optimizations
- **Memoization**: React.memo, useMemo, useCallback throughout
- **Optimized Polling**: Reduced frequencies (plans: 60s, executions: 10s)
- **Activity Tracking**: Efficient user activity detection
- **Local Assets**: Avoid external CORS requests
- **Smart State Management**: Efficient data structures (Map, Set)

---

## Non-Functional Requirements

### NFR-1: Performance
| Metric | Requirement | Implementation |
|--------|-------------|----------------|
| API Response Time | < 2 seconds | Batch operations, connection pooling |
| Page Load Time | < 3 seconds | Memoization, optimized polling |
| Execution Start | < 5 seconds | Async worker pattern |
| UI Status Refresh | 3-10 seconds | Smart polling intervals |

### NFR-2: Scalability
| Metric | Requirement | Implementation |
|--------|-------------|----------------|
| Concurrent Users | 50+ | Serverless auto-scaling |
| Protection Groups | 1000+ | DynamoDB auto-scaling |
| Recovery Plans | 500+ | Optimistic locking |
| Servers per Wave | 100+ | DRS API limits validation |

### NFR-3: Security
| Requirement | Implementation |
|-------------|----------------|
| Authentication | Cognito User Pool with JWT tokens |
| Authorization | RBAC with 5 roles and 14 permissions |
| Encryption at Rest | DynamoDB, S3 (AES-256) |
| Encryption in Transit | TLS 1.2+ for all communications |
| Input Validation | Comprehensive sanitization and validation |
| Security Scanning | 6 security tools in CI/CD pipeline |

### NFR-4: Availability
| Metric | Requirement | Implementation |
|--------|-------------|----------------|
| Target Availability | 99.9% | AWS serverless SLA |
| Recovery Time | < 15 minutes | Multi-AZ automatic failover |
| Data Durability | 99.999999999% | DynamoDB built-in durability |

---

## API Specifications

### Authentication
All API requests require JWT token in Authorization header:
```
Authorization: Bearer {id_token}
```

### Common Response Codes
| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 409 | Conflict (duplicate name, server conflict) |
| 429 | Too Many Requests (DRS limits exceeded) |
| 500 | Internal Server Error |

### Error Response Format
```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error description",
  "details": {},
  "requiredPermission": "PERMISSION_NAME",
  "userRoles": ["role1", "role2"]
}
```

---

## Data Requirements

### DynamoDB Tables

#### Protection Groups Table
**Table Name**: `{project}-protection-groups-{env}`
**Partition Key**: `GroupId` (String)

| Attribute | Type | Description |
|-----------|------|-------------|
| GroupId | String | UUID primary key |
| GroupName | String | Unique name (case-insensitive) |
| Region | String | AWS region code |
| SourceServerIds | List | Array of DRS source server IDs |
| ServerSelectionTags | Map | Tag-based server selection |
| LaunchConfig | Map | DRS launch configuration |
| AccountId | String | Target AWS account ID |
| AssumeRoleName | String | Cross-account role name |
| Version | Number | Optimistic locking version |
| CreatedDate | Number | Unix timestamp |
| LastModifiedDate | Number | Unix timestamp |

#### Recovery Plans Table
**Table Name**: `{project}-recovery-plans-{env}`
**Partition Key**: `PlanId` (String)

| Attribute | Type | Description |
|-----------|------|-------------|
| PlanId | String | UUID primary key |
| PlanName | String | Unique name (case-insensitive) |
| Waves | List | Array of wave configurations |
| Version | Number | Optimistic locking version |
| CreatedDate | Number | Unix timestamp |
| LastModifiedDate | Number | Unix timestamp |

#### Execution History Table
**Table Name**: `{project}-execution-history-{env}`
**Partition Key**: `ExecutionId` (String)
**Sort Key**: `PlanId` (String)
**GSI**: StatusIndex (Status, StartTime), PlanIdIndex (PlanId, StartTime)

| Attribute | Type | Description |
|-----------|------|-------------|
| ExecutionId | String | UUID primary key |
| PlanId | String | Reference to Recovery Plan |
| PlanName | String | Preserved plan name |
| ExecutionType | String | DRILL or RECOVERY |
| Status | String | Execution status |
| Waves | List | Array of wave execution states |
| StartTime | Number | Unix timestamp |
| EndTime | Number | Unix timestamp (when completed) |
| InitiatedBy | String | User who started execution |
| AccountContext | Map | Cross-account execution context |
| StateMachineArn | String | Step Functions execution ARN |
| TaskToken | String | Step Functions task token (pause/resume) |

#### Target Accounts Table
**Table Name**: `{project}-target-accounts-{env}`
**Partition Key**: `AccountId` (String)
**GSI**: StatusIndex for health monitoring

| Attribute | Type | Description |
|-----------|------|-------------|
| AccountId | String | AWS account ID |
| AssumeRoleName | String | Cross-account IAM role name |
| CrossAccountRoleArn | String | Full ARN of cross-account role |
| IsDefault | Boolean | Default account flag |
| HealthStatus | String | Account health status |
| LastHealthCheck | Number | Unix timestamp |

---

## Validation Rules

### Protection Group Validation
| Rule | Error Code |
|------|------------|
| Name required (1-64 chars) | MISSING_FIELD |
| Name globally unique | PG_NAME_EXISTS |
| Region required | MISSING_FIELD |
| Server selection mode required | INVALID_SELECTION_MODE |
| Cannot update during active execution | PG_IN_ACTIVE_EXECUTION |
| Cannot delete if referenced by plans | PG_IN_USE |

### Recovery Plan Validation
| Rule | Error Code |
|------|------------|
| Name required (1-64 chars) | MISSING_FIELD |
| Name globally unique | RP_NAME_EXISTS |
| At least one wave required | MISSING_WAVES |
| Wave size ≤ 100 servers | WAVE_SIZE_LIMIT_EXCEEDED |
| Cannot update during execution | PLAN_HAS_ACTIVE_EXECUTION |

### Execution Validation
| Rule | Error Code |
|------|------------|
| Plan must exist | RECOVERY_PLAN_NOT_FOUND |
| No server conflicts | SERVER_CONFLICT |
| DRS service limits compliance | Various limit codes |
| Healthy server replication | UNHEALTHY_SERVER_REPLICATION |

---

## References

- [Product Requirements Document](./PRODUCT_REQUIREMENTS_DOCUMENT.md)
- [UX/UI Design Specifications](./UX_UI_DESIGN_SPECIFICATIONS.md)
- [Architectural Design Document](../architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md)
- [API Reference Guide](../guides/API_REFERENCE_GUIDE.md)