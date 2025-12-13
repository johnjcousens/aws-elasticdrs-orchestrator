# Product Requirements Document
# AWS DRS Orchestration Solution

**Version**: 1.0  
**Date**: December 2025  
**Status**: Requirements Definition  
**Document Owner**: AWS DRS Orchestration Team

---

## Executive Summary

AWS DRS Orchestration will be an enterprise-grade, serverless disaster recovery orchestration platform built on AWS Elastic Disaster Recovery (DRS). The solution will enable organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, real-time monitoring, pause/resume capabilities, comprehensive DRS source server management, and complete audit trails.

### Problem Statement

AWS DRS provides continuous replication but lacks native orchestration for multi-tier applications requiring coordinated recovery sequences. Organizations need wave-based execution, dependency management, pause/resume controls, automated monitoring capabilities, and centralized DRS source server configuration management.

### Solution Overview

AWS DRS Orchestration will provide complete orchestration and management on top of AWS DRS:
- Protection Groups for logical server organization with automatic DRS discovery
- Recovery Plans with wave-based execution and multi-Protection Group support per wave
- Step Functions-driven automation with pause/resume capability
- Complete DRS source server management (launch settings, EC2 templates, tags, disks, replication, post-launch)
- React 19 + CloudScape Design System UI with real-time updates
- Complete REST API for automation and DevOps integration

---

## Architecture

![AWS DRS Orchestration Architecture](../architecture/AWS-DRS-Orchestration-Architecture.png)

*[View/Edit Source Diagram](../architecture/AWS-DRS-Orchestration-Architecture.drawio)*

### AWS Services

**Core Services**:
- DynamoDB: 3 tables (protection-groups, recovery-plans, execution-history)
- Lambda: 5 functions (API handler, orchestration-stepfunctions, execution-finder, execution-poller, frontend-builder)
- Step Functions: Workflow orchestration with waitForTaskToken callback pattern
- API Gateway: REST API with Cognito JWT authorizer
- S3 + CloudFront: Static website hosting with CDN
- AWS DRS: Core disaster recovery service integration

**Infrastructure as Code**:
- CloudFormation: 7 templates total (1 master + 6 nested stacks: database, lambda, api, step-functions, security, frontend)
- Single-command deployment from S3 artifacts
- Multi-region support (all 30 AWS DRS-supported regions)

### Data Model

**Protection Groups**: `GroupId` (PK), `GroupName`, `Region`, `SourceServerIds[]`, `CreatedDate`, `LastModifiedDate`
**Recovery Plans**: `PlanId` (PK), `PlanName`, `Waves[]` (with `protectionGroupIds[]`, `serverIds[]`, `pauseBeforeWave`)
**Execution History**: `ExecutionId` (PK), `PlanId` (SK), `Status`, `Waves[]`, GSI: StatusIndex, PlanIdIndex

---

## Features

### 1. Protection Groups

Logical organization of DRS source servers with automatic discovery and conflict detection.

**Capabilities**:
- Auto-discovery of DRS source servers across all 30 AWS DRS-supported regions
- Visual server selector with real-time status indicators (Available/Assigned)
- Single server per group constraint (globally enforced across all users)
- Real-time search and filtering in server discovery panel
- Conflict detection prevents duplicate server assignments
- Server validation against DRS API (prevents fake/invalid server IDs)

**UI Components**:
- CloudScape Table with CRUD operations, sorting, filtering, pagination
- ProtectionGroupDialog modal with RegionSelector and ServerDiscoveryPanel
- ServerSelector with checkbox selection and assignment status badges

**API Endpoints**:
- `GET /protection-groups` - List all groups with server details
- `POST /protection-groups` - Create group (validates name uniqueness, server existence, conflicts)
- `GET /protection-groups/{id}` - Get single group with enriched server details
- `PUT /protection-groups/{id}` - Update group (blocked during active executions)
- `DELETE /protection-groups/{id}` - Delete group (blocked if referenced by any Recovery Plan)
- `GET /drs/source-servers?region={region}` - Discover DRS servers with assignment status

### 2. Recovery Plans

Wave-based orchestration with multi-Protection Group support and pause/resume capability.

**Capabilities**:
- Unlimited waves with sequential execution
- Multiple Protection Groups per wave
- Wave dependencies with circular dependency validation
- Pause-before-wave configuration for manual checkpoints
- Drill and Recovery execution modes
- Server selection within waves from assigned Protection Groups

**Wave Configuration**:
```json
{
  "waveNumber": 0,
  "name": "Database Tier",
  "description": "Primary databases",
  "protectionGroupIds": ["pg-uuid-1", "pg-uuid-2"],
  "serverIds": ["s-xxx", "s-yyy"],
  "dependsOnWaves": [],
  "pauseBeforeWave": false
}
```

**UI Components**:
- CloudScape Table with execution status, last start/end times
- RecoveryPlanDialog modal with WaveConfigEditor
- WaveConfigEditor with expandable sections, multi-select Protection Groups, ServerSelector
- Execute dropdown with Drill/Recovery options

**API Endpoints**:
- `GET /recovery-plans` - List all plans with latest execution status
- `POST /recovery-plans` - Create plan with wave configuration
- `GET /recovery-plans/{id}` - Get plan with full wave details
- `PUT /recovery-plans/{id}` - Update plan (blocked during active executions)
- `DELETE /recovery-plans/{id}` - Delete plan (blocked during active executions)

### 3. Execution Engine

Step Functions-driven recovery automation with pause/resume, instance termination, and server conflict detection.

**Server Conflict Detection**:
- Prevents starting executions when servers are already in use by another active/paused execution
- Checks ALL servers across ALL waves of the recovery plan
- For PAUSED/PENDING executions, looks up the original Recovery Plan to identify all servers
- Frontend proactively disables Drill/Recovery buttons with reason when conflicts exist
- API returns `hasServerConflict` and `conflictInfo` fields for each recovery plan

**Execution Flow**:
1. Check for server conflicts with active/paused executions
2. Validate plan and servers exist
3. Create execution record with PENDING status
4. Start Step Functions state machine
5. For each wave:
   - Check for `pauseBeforeWave` configuration
   - If paused: Enter `waitForTaskToken` state (up to 1 year timeout)
   - Call DRS `StartRecovery` API with all wave servers
   - Poll job status via Step Functions orchestration
   - Wait for all servers to reach LAUNCHED status
   - Update execution record in DynamoDB
6. Mark execution COMPLETED or FAILED

**Pause/Resume Mechanism**:
- Waves can be configured with `pauseBeforeWave: true`
- Step Functions uses `waitForTaskToken` callback pattern
- Task token stored in DynamoDB execution record
- Resume via API triggers `SendTaskSuccess` with stored token
- Maximum pause duration: 1 year (31536000 seconds)

**Instance Termination**:
- Available only for terminal states (COMPLETED, FAILED, CANCELLED)
- Terminates all EC2 recovery instances launched during execution
- Updates execution record with `instancesTerminated: true`
- Prevents duplicate termination attempts

**Status Values**: PENDING, POLLING, INITIATED, LAUNCHING, STARTED, IN_PROGRESS, RUNNING, PAUSED, COMPLETED, PARTIAL, FAILED, CANCELLED

**API Endpoints**:
- `POST /executions` - Start execution (PlanId, ExecutionType: DRILL|RECOVERY)
- `GET /executions` - List executions with pagination
- `GET /executions/{id}` - Get execution status with wave details
- `DELETE /executions/{id}` - Cancel execution (stops pending waves)
- `POST /executions/{id}/resume` - Resume paused execution
- `POST /executions/{id}/terminate-instances` - Terminate recovery EC2 instances
- `GET /executions/{id}/job-logs` - Get DRS job event logs
- `DELETE /executions` - Bulk delete completed executions

### 4. DRS Service Limits Validation

Real-time validation and enforcement of AWS DRS service limits to prevent API errors and ensure reliable operations.

**Capabilities**:
- **Hard Limit Enforcement**: 300 replicating servers per account per region (cannot be increased)
- **Job Size Validation**: Maximum 100 servers per recovery job (prevents DRS API failures)
- **Concurrent Job Monitoring**: Maximum 20 concurrent jobs across all operations
- **Total Server Tracking**: Maximum 500 servers across all active jobs
- **Real-time Quota Display**: Live usage metrics in UI with status indicators
- **Proactive Blocking**: Prevents operations that would exceed limits before API calls

**API Endpoints**:
- `GET /drs/service-limits?region={region}` - Get current limits and usage
- `POST /drs/validate-limits` - Validate operation against limits
- `GET /drs/quotas?region={region}` - Get comprehensive quota dashboard data

---

### 5. DRS Source Server Management

Complete DRS source server configuration management from the UI without navigating to AWS Console.

#### 5.1 Server Info & Recovery Dashboard

Read-only visibility into DRS source server details, replication state, recovery readiness, and lifecycle information.

**Capabilities**:
- Server details panel with hostname, OS, CPU, RAM, disks, network
- Replication status and progress with lag duration
- Recovery readiness indicators (READY_FOR_TEST, READY_FOR_CUTOVER)
- Lifecycle state display with timestamps
- Last recovery result and recovery instance details

**Data Fields**:
| Field | Description |
|-------|-------------|
| sourceServerID | Unique server identifier (s-xxx) |
| hostname | Source server hostname |
| lifeCycle | Lifecycle state and timestamps |
| dataReplicationInfo | Replication status and progress |
| sourceProperties | OS, CPU, RAM, disks, network |
| lastLaunchResult | Last recovery result |

**API Endpoints**:
- `GET /drs/source-servers/{id}?region={region}` - Get full server details

#### 5.2 DRS Launch Settings

The system shall configure DRS launch settings for recovery instances at the Protection Group level.

**Capabilities**:
- Instance Type Right Sizing method (NONE, BASIC, IN_AWS)
- Launch Disposition (STOPPED, STARTED)
- Copy Private IP option
- Copy Tags option
- OS Licensing (BYOL or AWS-provided)

**Behavior**: Settings are configured per Protection Group and applied to all servers in the group when the Protection Group is saved.

**API Endpoints**:
- `POST /protection-groups` - Create Protection Group with LaunchConfig
- `PUT /protection-groups/{id}` - Update LaunchConfig (applies to all servers)

#### 5.3 EC2 Launch Template

The system shall configure EC2 launch template settings for recovery instances at the Protection Group level.

**Capabilities**:
- Instance type selection from EC2 instance type catalog
- Subnet selection from available VPC subnets
- Security group selection (multiple)
- IAM instance profile selection

**Behavior**: Settings are stored in Protection Group's LaunchConfig field and applied to DRS source servers via the DRS UpdateLaunchConfiguration API, which updates the underlying EC2 launch templates.

**API Endpoints**:
- `GET /ec2/subnets?region={region}` - List available subnets
- `GET /ec2/security-groups?region={region}` - List security groups
- `GET /ec2/instance-profiles?region={region}` - List IAM instance profiles
- `GET /ec2/instance-types?region={region}` - List EC2 instance types

#### 5.4 Tags Management

View, add, edit, and delete tags on DRS source servers.

**Capabilities**:
- View all server tags
- Add new tags with key-value pairs
- Edit existing tag values
- Delete tags
- Tag validation (no aws: prefix, max 50 tags, key/value length limits)

**Tag Constraints**:
- Max 50 tags per resource
- Key: 1-128 characters, no `aws:` prefix
- Value: 0-256 characters
- Case-sensitive

**API Endpoints**:
- `GET /drs/source-servers/{id}/tags?region={region}` - List tags
- `PUT /drs/source-servers/{id}/tags` - Add/update tags
- `DELETE /drs/source-servers/{id}/tags` - Remove tags

#### 5.5 Disk Settings

Configure per-disk settings for DRS source servers.

**Capabilities**:
- View disk configuration (device name, size, boot disk indicator)
- Edit disk type (GP2, GP3, IO1, IO2, ST1, SC1)
- Configure IOPS (for io1/io2/gp3)
- Configure throughput (for gp3)

**Disk Type Options**:
| Type | Use Case | IOPS | Throughput |
|------|----------|------|------------|
| gp3 | General purpose | 3000-16000 | 125-1000 MiB/s |
| gp2 | General purpose (legacy) | Burst to 3000 | N/A |
| io1 | High performance | Up to 64000 | N/A |
| io2 | High performance | Up to 64000 | N/A |
| st1 | Throughput optimized | N/A | Up to 500 MiB/s |
| sc1 | Cold storage | N/A | Up to 250 MiB/s |

**API Endpoints**:
- `GET /drs/source-servers/{id}/disks?region={region}` - Get disk configuration
- `PUT /drs/source-servers/{id}/disks` - Update disk configuration

#### 5.6 Replication Settings

Configure replication settings for DRS source servers.

**Capabilities**:
- Staging area subnet selection
- Security group configuration for replication servers
- Replication server instance type selection
- Dedicated vs shared replication server
- Bandwidth throttling (0 = unlimited)
- Data plane routing (PRIVATE_IP or PUBLIC_IP)
- EBS encryption settings
- Point-in-time (PIT) snapshot policy configuration

**PIT Policy Configuration**:
```json
{
  "pitPolicy": [
    { "interval": 10, "retentionDuration": 60, "units": "MINUTE", "enabled": true },
    { "interval": 1, "retentionDuration": 24, "units": "HOUR", "enabled": true },
    { "interval": 1, "retentionDuration": 7, "units": "DAY", "enabled": true }
  ]
}
```

**API Endpoints**:
- `GET /drs/source-servers/{id}/replication?region={region}` - Get replication configuration
- `PUT /drs/source-servers/{id}/replication` - Update replication configuration
- `GET /drs/staging-resources?region={region}` - Get available subnets and security groups

#### 5.7 Post-Launch Settings

Configure post-launch actions for recovery instances.

**Capabilities**:
- Deployment type (TEST_AND_CUTOVER or CUTOVER)
- SSM automation document selection
- SSM execution timeout (120-3600 seconds)
- Must succeed for cutover option
- S3 log bucket configuration
- S3 key prefix for logs

**API Endpoints**:
- `GET /drs/source-servers/{id}/post-launch?region={region}` - Get post-launch configuration
- `PUT /drs/source-servers/{id}/post-launch` - Update post-launch configuration
- `GET /ssm/documents?region={region}` - List available SSM documents
- `GET /s3/buckets?region={region}` - List available S3 buckets

### 5. User Interface

React 19.1 + TypeScript 5.9 + CloudScape Design System 3.0

**Pages**:

| Route | Component | Description |
|-------|-----------|-------------|
| /login | LoginPage | Cognito authentication with error handling |
| / | Dashboard | Metrics cards, pie chart, active executions, recent activity |
| /getting-started | GettingStartedPage | 3-step onboarding guide with quick links |
| /protection-groups | ProtectionGroupsPage | CRUD table with server counts and DRS limits validation |
| /recovery-plans | RecoveryPlansPage | CRUD table with execution status, wave counts, conflict detection |
| /executions | ExecutionsPage | Active/History tabs with real-time updates (3-second polling) |
| /executions/:id | ExecutionDetailsPage | Wave progress, DRS job events, pause/resume/terminate controls |
| /servers/:id | ServerDetailsPage | DRS source server configuration management |
| /quotas | QuotasPage | DRS service limits dashboard and monitoring |

**Key UI Features**:
- Real-time updates: 3-second polling for active executions
- DRS Job Events timeline with auto-refresh
- Pause/Resume execution controls with loading states
- Terminate recovery instances button (terminal states only)
- DRS source server management modals (7 configuration areas)
- Loading states on all action buttons (prevents double-clicks)
- Toast notifications via react-hot-toast
- Auto-logout after 45 minutes of inactivity
- Responsive design, WCAG 2.1 AA compliant

**Reusable Components**:
- ProtectionGroupDialog, RecoveryPlanDialog, ConfirmDialog
- ServerSelector, ServerDiscoveryPanel, ServerListItem, RegionSelector
- WaveConfigEditor, WaveProgress, StatusBadge, DateTimeDisplay
- LoadingState, ErrorState, ErrorBoundary, ErrorFallback
- CardSkeleton, DataTableSkeleton, PageTransition, ProtectedRoute
- DRSLimitsValidator, QuotaDisplay, ServiceLimitsAlert
- ConflictDetector, ExecutionControls, JobEventsTimeline
- ServerInfoPanel, LaunchSettingsEditor, EC2TemplateEditor
- TagsEditor, DiskSettingsEditor, ReplicationSettingsEditor, PostLaunchSettingsEditor
- TagSyncManager, MultiAccountManager, NotificationCenter

---

## Technical Specifications

### Frontend Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.1.1 | UI framework with hooks |
| TypeScript | 5.9.3 | Type safety |
| CloudScape | 3.0.1148 | AWS-native UI components |
| Vite | 7.1.7 | Build tool and dev server |
| AWS Amplify | 6.15.8 | Cognito authentication |
| Axios | 1.13.2 | HTTP client |
| React Router | 7.9.5 | Client-side routing |
| react-hot-toast | 2.6.0 | Toast notifications |
| date-fns | 4.1.0 | Date formatting |

### Backend Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Lambda runtime |
| boto3 | (runtime) | AWS SDK |
| crhelper | 2.0.11 | CloudFormation custom resources |

### API Authentication
- Cognito User Pool with JWT tokens
- Token auto-refresh on expiration
- 401 handling with redirect to login
- 45-minute session timeout (frontend)

### DRS Integration

**Critical Requirement**: DRS uses the calling Lambda role's IAM permissions for EC2 operations during recovery.

**Required Lambda IAM Permissions**:
```yaml
# DRS Permissions
- drs:DescribeSourceServers
- drs:StartRecovery
- drs:DescribeJobs
- drs:DescribeJobLogItems
- drs:DescribeRecoveryInstances
- drs:CreateRecoveryInstanceForDrs
- drs:GetLaunchConfiguration
- drs:UpdateLaunchConfiguration
- drs:GetReplicationConfiguration
- drs:UpdateReplicationConfiguration
- drs:ListTagsForResource
- drs:TagResource
- drs:UntagResource

# EC2 Permissions (required by DRS during recovery)
- ec2:DescribeInstances
- ec2:DescribeInstanceStatus
- ec2:DescribeInstanceTypes
- ec2:DescribeLaunchTemplates
- ec2:DescribeLaunchTemplateVersions
- ec2:CreateLaunchTemplate
- ec2:CreateLaunchTemplateVersion
- ec2:ModifyLaunchTemplate
- ec2:DeleteLaunchTemplate
- ec2:RunInstances
- ec2:StartInstances
- ec2:TerminateInstances
- ec2:CreateVolume
- ec2:AttachVolume
- ec2:CreateTags
- ec2:CreateNetworkInterface
- ec2:DeleteNetworkInterface
- ec2:DescribeSubnets
- ec2:DescribeSecurityGroups
- ec2:DescribeVpcs

# SSM Permissions (for post-launch)
- ssm:ListDocuments
- ssm:DescribeDocument

# S3 Permissions (for post-launch logs)
- s3:ListAllMyBuckets
- s3:GetBucketLocation

# IAM Permissions (for instance profiles)
- iam:ListInstanceProfiles
```

**Recovery Flow Timeline**:
1. Snapshot Creation: 1-2 minutes
2. Conversion Server Launch: 1-2 minutes
3. Launch Template Creation: <1 minute
4. Recovery Instance Launch: 1-2 minutes
5. Total per wave: ~15-20 minutes

---

## Deployment

### Prerequisites
- AWS Account with DRS enabled in target region
- DRS source servers actively replicating
- S3 bucket for deployment artifacts
- Admin email for Cognito user creation

### Deployment Bucket Structure
```
s3://{deployment-bucket}/
├── cfn/                          # CloudFormation templates
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── step-functions-stack.yaml
│   ├── security-stack.yaml
│   └── frontend-stack.yaml
├── lambda/                       # Lambda deployment packages
│   ├── api-handler.zip
│   ├── orchestration-stepfunctions.zip
│   ├── execution-finder.zip
│   ├── execution-poller.zip
│   └── frontend-builder.zip
└── frontend/                     # Frontend build artifacts
    └── dist/
```

### Deploy Command
```bash
aws cloudformation deploy \
  --template-url https://{bucket}.s3.{region}.amazonaws.com/cfn/master-template.yaml \
  --stack-name drs-orchestration-{env} \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    Environment={env} \
    SourceBucket={bucket} \
    AdminEmail={email} \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region {region}
```

### Stack Outputs
- `CloudFrontURL`: Frontend application URL
- `ApiEndpoint`: REST API endpoint
- `UserPoolId`: Cognito User Pool ID
- `UserPoolClientId`: Cognito App Client ID
- `FrontendBucketName`: S3 bucket for frontend assets

### Post-Deployment Steps
1. Create Cognito admin user via AWS Console or CLI
2. Configure DRS source servers in target region
3. Access CloudFront URL and sign in
4. Create Protection Groups, Recovery Plans, execute drills

---

## Success Metrics

### Operational Targets
| Metric | Target |
|--------|--------|
| Recovery Time Objective (RTO) | <15 minutes per wave |
| Recovery Point Objective (RPO) | <5 minutes (DRS native) |
| Execution Success Rate | >99.5% |
| API Availability | >99.9% |

### Cost Estimates (Monthly)
| Service | Estimate |
|---------|----------|
| Lambda | $1-5 |
| API Gateway | $3-10 |
| DynamoDB | $1-5 |
| CloudFront | $1-5 |
| S3 | <$1 |
| Step Functions | $1-5 |
| Cognito | Free tier |
| **Total** | **$12-40** |

### User Experience Targets
| Task | Target Time |
|------|-------------|
| Create Protection Group | <5 minutes |
| Create Recovery Plan | <15 minutes |
| Execute Drill | <30 minutes |
| Configure Server Launch Settings | <2 minutes |
| Configure Server Replication | <5 minutes |

---

## AWS DRS Regional Availability

The solution will support all **30 AWS regions** where Elastic Disaster Recovery (DRS) is available:

| Region Group | Count | Regions |
|--------------|-------|---------|
| **Americas** | 6 | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America (São Paulo) |
| **Europe** | 8 | Ireland, London, Frankfurt, Paris, Stockholm, Milan, Spain, Zurich |
| **Asia Pacific** | 10 | Tokyo, Seoul, Osaka, Singapore, Sydney, Mumbai, Hyderabad, Jakarta, Melbourne, Hong Kong |
| **Middle East & Africa** | 4 | Bahrain, UAE, Cape Town, Tel Aviv |
| **GovCloud** | 2 | US-East, US-West |

*Regional availability is determined by AWS DRS service. As AWS expands DRS to additional regions, the solution automatically supports them.*

---

## DRS Service Limits Compliance

The solution will enforce AWS DRS service limits to prevent API errors:

| Limit | Value | Enforcement |
|-------|-------|-------------|
| Max replicating servers | 300 | UI validation, API validation |
| Max servers in all jobs | 500 | Execution validation |
| Max concurrent jobs | 20 | Execution queue management |

---

## References

- [Software Requirements Specification](./SOFTWARE_REQUIREMENTS_SPECIFICATION.md)
- [UX/UI Design Specifications](./UX_UI_DESIGN_SPECIFICATIONS.md)
- [Deployment Guide](../guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md)
- [Architecture Design](../architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md)
- [DRS Server Info Implementation](../implementation/DRS_SERVER_INFO_MVP_PLAN.md)
- [DRS Launch Settings Implementation](../implementation/DRS_LAUNCH_SETTINGS_MVP_PLAN.md)
- [EC2 Launch Template Implementation](../implementation/EC2_LAUNCH_TEMPLATE_MVP_PLAN.md)
- [DRS Tags Implementation](../implementation/DRS_TAGS_MVP_PLAN.md)
- [DRS Disk Settings Implementation](../implementation/DRS_DISK_SETTINGS_MVP_PLAN.md)
- [DRS Replication Settings Implementation](../implementation/DRS_REPLICATION_SETTINGS_MVP_PLAN.md)
- [DRS Post-Launch Implementation](../implementation/DRS_POST_LAUNCH_MVP_PLAN.md)
