# Product Requirements Document
# AWS DRS Orchestration Solution

**Version**: 2.0  
**Date**: December 30, 2025  
**Status**: Production Ready - Full Feature Implementation Complete  
**Document Owner**: AWS DRS Orchestration Team

---

## Executive Summary

AWS DRS Orchestration is a production-ready, enterprise-grade serverless disaster recovery orchestration platform built on AWS Elastic Disaster Recovery (DRS). The solution enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, real-time monitoring, pause/resume capabilities, comprehensive DRS source server management, multi-account support, tag-based server selection, and complete audit trails.

### Problem Statement

AWS DRS provides continuous replication but lacks native orchestration for multi-tier applications requiring coordinated recovery sequences. Organizations need wave-based execution, dependency management, pause/resume controls, automated monitoring capabilities, centralized DRS source server configuration management, multi-account orchestration, and flexible server selection methods.

### Solution Overview

AWS DRS Orchestration provides complete orchestration and management on top of AWS DRS:
- Protection Groups for logical server organization with tag-based or explicit server selection
- Recovery Plans with wave-based execution and multi-Protection Group support per wave
- Step Functions-driven automation with pause/resume capability and existing instance detection
- Complete DRS source server management (launch settings, EC2 templates, tags, disks, replication, post-launch)
- Multi-account hub-and-spoke architecture with centralized management
- React 19 + CloudScape Design System UI with real-time updates and 32 components
- Complete REST API with 42 endpoints for automation and DevOps integration
- Tag synchronization between EC2 instances and DRS source servers
- DRS service limits validation and quota monitoring

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

Logical organization of DRS source servers with tag-based or explicit server selection, automatic discovery, and conflict detection.

**Server Selection Modes**:
- **Tag-Based Selection**: Dynamic server selection using EC2 tags - servers matching ALL specified tags are resolved at execution time
- **Explicit Server Selection**: Static selection - explicitly choose specific DRS source servers

**Capabilities**:
- Auto-discovery of DRS source servers across all 30 AWS DRS-supported regions
- Visual server selector with real-time status indicators (Available/Assigned)
- Single server per group constraint (globally enforced across all users)
- Real-time search and filtering in server discovery panel
- Conflict detection prevents duplicate server assignments
- Server validation against DRS API (prevents fake/invalid server IDs)
- Tag-based server selection with preview functionality
- Launch configuration settings applied to all servers in the group

**UI Components**:
- CloudScape Table with CRUD operations, sorting, filtering, pagination
- ProtectionGroupDialog modal with tabbed server selection (Tags vs Servers)
- RegionSelector with all 30 DRS regions
- ServerDiscoveryPanel with search and filtering
- ServerSelector with checkbox selection and assignment status badges
- LaunchConfigSection for DRS launch settings configuration

**API Endpoints**:
- `GET /protection-groups` - List all groups with server details and selection mode
- `POST /protection-groups` - Create group with tag-based or explicit server selection
- `GET /protection-groups/{id}` - Get single group with enriched server details
- `PUT /protection-groups/{id}` - Update group (blocked during active executions)
- `DELETE /protection-groups/{id}` - Delete group (blocked if referenced by any Recovery Plan)
- `POST /protection-groups/resolve` - Preview servers matching specified tags
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

**Existing Instance Detection**:
- Before starting a drill, checks for existing recovery instances from previous executions
- Displays warning dialog with instance details (Name tag, private IP, instance type, launch time)
- Tracks source execution ID and plan name for each recovery instance
- Warns users that starting a new drill will terminate existing instances first
- Helps prevent unexpected costs from orphaned recovery instances

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
- `GET /recovery-plans/{id}/check-existing-instances` - Check for existing recovery instances with source tracking

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

### 5. Multi-Account Management

Production-ready multi-account management system with hub-and-spoke architecture, account enforcement, auto-selection, and seamless account switching for enterprise-scale DRS orchestration.

**Architecture**:
- **Hub Account**: Central orchestration account running the DRS Orchestration solution
- **Spoke Accounts**: Target accounts containing DRS source servers and recovery resources
- **Cross-Account IAM Roles**: Secure access via AssumeRole with least-privilege permissions

**Capabilities**:
- **Account Registration**: Add target accounts with cross-account role configuration
- **Account Context System**: Centralized account state management with localStorage persistence
- **Auto-Selection**: Single accounts automatically selected as default for seamless user experience
- **Account Selector**: Top navigation dropdown for intuitive account switching with full page context updates
- **Setup Wizard**: Guided first-time account configuration for new users
- **Default Preferences**: Persistent default account selection integrated into existing 3-tab settings panel
- **Page-Level Enforcement**: Features blocked until target account selected (multi-account scenarios only)
- **Settings Integration**: Default account preference seamlessly integrated without disrupting existing 3-tab structure
- **Account Health Monitoring**: Real-time validation of cross-account role access and DRS service availability

**Account Context Behavior**:
- **Single Account**: Automatically selected as default, no enforcement needed
- **No Accounts**: Setup wizard guides user to add first account
- **Multiple Accounts**: User must explicitly select account, enforcement blocks features until selection
- **Account Switching**: Full page context updates with proper state management

**Cross-Account Security**:
- IAM roles with least-privilege DRS and EC2 permissions
- Secure credential management via AWS STS AssumeRole
- Account isolation and validation
- Audit trail of cross-account operations

**UI Components**:
- AccountSelector component in top navigation following AWS Console patterns
- AccountRequiredWrapper component for consistent enforcement across protected pages
- AccountManagementPanel with default account preference dropdown (maintains existing 3-tab structure)
- Setup wizard for first-time account configuration
- Account health status indicators

**API Endpoints**:
- `GET /accounts/targets` - List available target accounts with health status
- `POST /accounts/targets` - Add new target account with role validation
- `PUT /accounts/targets/{id}` - Update account configuration
- `DELETE /accounts/targets/{id}` - Remove target account
- `GET /accounts/targets/{id}/health` - Check account health and role access

### 6. Enhanced Tag-Based Server Selection

Fixed and enhanced tag-based server selection with DRS source server tags and complete hardware details.

**Capabilities**:
- **DRS Source Server Tags**: Queries actual DRS source server tags (not EC2 instance tags)
- **Complete Hardware Details**: CPU cores, RAM, disks, FQDN, OS info, network interfaces displayed in tag preview
- **Regional Support**: Full support for all 30 DRS-supported regions with us-west-2 testing validation
- **Preview Enhancement**: Tag preview shows identical detailed information as manual server selection
- **Clean UX**: Removed confusing non-functional checkboxes from tag preview for cleaner interface

**Tag Query Enhancement**:
- Uses DRS `list_tags_for_resource` API instead of EC2 instance tags
- Comprehensive server hardware information collection from DRS source properties
- Field consistency: `sourceServerID` naming alignment across frontend and backend
- Regional flexibility with proper error handling

**API Endpoints**:
- `POST /drs/query-servers-by-tags` - Query DRS source servers by tags with hardware details

### 8. DRS Tag Synchronization

Automated synchronization of EC2 instance tags to DRS source servers across all regions.

**Capabilities**:
- **Bulk Tag Sync**: Synchronize tags from EC2 instances to corresponding DRS source servers
- **Cross-Region Support**: Sync tags across all 30 DRS-supported regions
- **Selective Sync**: Choose specific servers or sync all servers in a region
- **Progress Monitoring**: Real-time progress tracking with detailed status updates
- **Conflict Resolution**: Handle tag conflicts and validation errors gracefully
- **Audit Trail**: Complete logging of sync operations and results

**Sync Process**:
1. Discover DRS source servers across specified regions
2. Match DRS servers to EC2 instances by source server ID
3. Compare existing tags and identify differences
4. Apply tag updates to DRS source servers
5. Report sync results with success/failure counts

**API Endpoints**:
- `POST /drs/tag-sync` - Sync EC2 tags to DRS source servers with progress tracking

### 9. Configuration Management

Export and import system configuration for backup, migration, and environment promotion.

**Capabilities**:
- **Full Configuration Export**: Export all Protection Groups, Recovery Plans, and settings
- **Selective Export**: Export specific components or filtered data
- **Configuration Import**: Import configuration from exported files
- **Environment Migration**: Promote configurations between dev/test/prod environments
- **Backup and Restore**: Create configuration backups for disaster recovery

**Export Formats**:
- JSON format with complete metadata
- Structured data with relationships preserved
- Validation checksums for integrity verification

**API Endpoints**:
- `GET /config/export` - Export system configuration
- `POST /config/import` - Import configuration from file

### 7. DRS Source Server Management

Complete DRS source server configuration management from the UI without navigating to AWS Console.

#### 7.1 Server Info & Recovery Dashboard

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

#### 7.2 DRS Launch Settings

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

#### 7.3 EC2 Launch Template

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

#### 7.4 Tags Management

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

#### 7.5 Disk Settings

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

#### 7.6 Replication Settings

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

#### 7.7 Post-Launch Settings

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

### 10. User Interface

React 19.1 + TypeScript 5.9 + CloudScape Design System 3.0 with 32 components and 7 pages.

**Pages**:

| Route | Component | Description |
|-------|-----------|-------------|
| /login | LoginPage | Cognito authentication with error handling |
| / | Dashboard | Metrics cards, pie chart, active executions, recent activity |
| /getting-started | GettingStartedPage | 3-step onboarding guide with quick links |
| /protection-groups | ProtectionGroupsPage | CRUD table with server counts, tag-based selection, and DRS limits validation |
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
- Multi-account context switching with enforcement
- Tag-based server selection with preview
- Existing instance detection and warning dialogs

**Component Library (32 Components)**:

| Category | Components | Count |
|----------|------------|-------|
| **Layout** | ErrorBoundary, ErrorFallback, ErrorState, LoadingState, CardSkeleton, DataTableSkeleton, PageTransition, ProtectedRoute, AppLayout, ContentLayout | 10 |
| **Multi-Account** | AccountSelector, AccountRequiredWrapper, AccountManagementPanel | 3 |
| **Dialogs** | ProtectionGroupDialog, RecoveryPlanDialog, ConfirmDialog, TagsEditor, DiskSettingsEditor, ReplicationSettingsEditor, PostLaunchSettingsEditor | 7 |
| **Server Management** | ServerSelector, ServerDiscoveryPanel, ServerListItem, ServerInfoPanel, PitPolicyEditor | 5 |
| **Form Controls** | RegionSelector, WaveConfigEditor | 2 |
| **Status Display** | StatusBadge, WaveProgress, DateTimeDisplay, DRSQuotaStatus, InvocationSourceBadge, JobEventsTimeline | 6 |
| **Execution** | ExecutionDetails | 1 |
| **Launch Config** | LaunchConfigSection | 1 |
| **CloudScape Wrappers** | AppLayout, ContentLayout | 2 |

**Total: 32 Components**

## Complete API Reference

The solution provides a comprehensive REST API with 32+ endpoints across 9 categories for complete automation and DevOps integration.

### Protection Groups API (7 endpoints)
- `GET /protection-groups` - List all Protection Groups with server details
- `POST /protection-groups` - Create Protection Group with tag-based or explicit server selection
- `GET /protection-groups/{id}` - Get Protection Group details with enriched server information
- `PUT /protection-groups/{id}` - Update Protection Group (blocked during active executions)
- `DELETE /protection-groups/{id}` - Delete Protection Group (blocked if referenced by Recovery Plans)
- `POST /protection-groups/resolve` - Preview servers matching specified tags
- `GET /protection-groups/{id}/launch-config` - Get launch configuration settings

### Recovery Plans API (6 endpoints)
- `GET /recovery-plans` - List all Recovery Plans with execution status and wave counts
- `POST /recovery-plans` - Create Recovery Plan with wave configuration and dependencies
- `GET /recovery-plans/{id}` - Get Recovery Plan details with full wave configuration
- `PUT /recovery-plans/{id}` - Update Recovery Plan (blocked during active executions)
- `DELETE /recovery-plans/{id}` - Delete Recovery Plan (blocked during active executions)
- `GET /recovery-plans/{id}/check-existing-instances` - Check for existing recovery instances

### Executions API (7 endpoints)
- `GET /executions` - List executions with filtering, pagination, and real-time status
- `POST /executions` - Start new execution (drill or recovery mode)
- `GET /executions/{id}` - Get execution details with wave progress and server status
- `POST /executions/{id}/resume` - Resume paused execution
- `DELETE /executions/{id}` - Cancel running execution
- `POST /executions/{id}/terminate-instances` - Terminate recovery instances after completion
- `DELETE /executions` - Bulk delete completed executions

### DRS Integration API (4 endpoints)
- `GET /drs/source-servers` - Discover DRS source servers by region with assignment status
- `GET /drs/quotas` - Get DRS service limits and current usage by region
- `POST /drs/query-servers-by-tags` - Query servers by tags with hardware details
- `POST /drs/tag-sync` - Sync EC2 instance tags to DRS source servers

### DRS Server Management API (7 endpoints)
- `GET /drs/source-servers/{id}` - Get comprehensive server details and configuration
- `GET /drs/source-servers/{id}/launch-settings` - Get DRS launch configuration
- `PUT /drs/source-servers/{id}/launch-settings` - Update DRS launch configuration
- `GET /drs/source-servers/{id}/tags` - Get server tags
- `PUT /drs/source-servers/{id}/tags` - Add/update server tags
- `DELETE /drs/source-servers/{id}/tags` - Remove server tags
- `POST /drs/source-servers/{id}/sync-tags` - Sync EC2 tags to DRS server

### EC2 Resources API (4 endpoints)
- `GET /ec2/subnets` - List available subnets for launch template configuration
- `GET /ec2/security-groups` - List security groups for launch template configuration
- `GET /ec2/instance-profiles` - List IAM instance profiles for EC2 instances
- `GET /ec2/instance-types` - List available EC2 instance types

### Multi-Account Management API (4 endpoints)
- `GET /accounts/targets` - List registered target accounts with health status
- `POST /accounts/targets` - Register new target account with cross-account role
- `PUT /accounts/targets/{id}` - Update target account configuration
- `DELETE /accounts/targets/{id}` - Remove target account registration

### Configuration Management API (2 endpoints)
- `GET /config/export` - Export system configuration (Protection Groups, Recovery Plans)
- `POST /config/import` - Import configuration from exported file

### System API (1 endpoint)
- `GET /health` - Health check endpoint for monitoring and load balancers

**Total: 42 REST API Endpoints**

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
