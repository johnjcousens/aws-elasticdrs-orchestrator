# Product Requirements Document
# AWS DRS Orchestration Solution

**Version**: 2.4  
**Date**: January 7, 2026  
**Status**: Production Ready - Performance Optimized v1.4.1  
**Document Owner**: AWS DRS Orchestration Team

---

## Executive Summary

AWS DRS Orchestration is a production-ready, enterprise-grade serverless disaster recovery orchestration platform built on AWS Elastic Disaster Recovery (DRS). The solution enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, real-time monitoring, pause/resume capabilities, comprehensive DRS source server management, multi-account support, tag-based server selection, automated tag synchronization with EventBridge scheduling, enterprise security validation, performance optimizations,ls.

### Problem Statement

AWS DRS provides continuous replication but lacks native orchestration for multi-tier applications requiring coordinated recovery sequences. Organizations need wave-based execution, dependency management, pause/resume controls, automated monitoring capabilities, centralized DRS source server configuration management, multi-account orchestration, flexible server selection methods, and.

### Solution Overview

AWS DRS Orchestration provides complete orchestration and management on top of AWS DRS:
- Protection Groups for logical server organization with tag-based or explicit server selection
- Recovery Plans with wave-based execution and multi-Protection Group support per wave
- Step Functions-driven automation with pause/resume capability and existing instance detection
- Complete DRS source server management (launch settings, EC2 templates, tags, disks, replication, post-launch)
- Multi-account hub-and-spoke architecture with centralized management
- React 19 + CloudScape Design System UI with real-time updates and 37 components
- Complete REST API with 42 endpoints for automation and DevOps integration
- Tag synchronization between EC2 instances and DRS source servers
- DRS service limits validation and quota monitoring
ls
- Sgracefully

---

## Architecture

![AWS DRS Orchestration Architecture](../architecture/AWS-DRS-Orchestration-Architecture.png)

*[View/Edit Sourdrawio)*

### AWS Services

**Core Services**:
- DynamoDB: 3 tables (protection-groups, recovery-plans, execution-history)
- Lambda: 5 functions (API handler, orchestration-s
- Step Functions: Workflow orchestration with waitk pattern
- API Gateway: REST API with Cognito JWT authorizer
 CDN
- AWS DRS: Core disaster re

**Infrastructure as Code**:
- CloudFormation: 15 templates total (1 master + 14 nesteole)
 artifacts
- Multi-region

### Data Model

**Protection Groups**: `GroupId` (PK), `GroupName`, `Region`, `SourceServerIds[]`, `ServerSelectionTags{}`, dDate`
`)
**Endex

---

## Features

### 1. Protection Groups

Logical organization of DRS

**Server Selection Modes**:
e
- **Explicit Serv

**Performance Optimizations**:
- **Batch DynamoDB Operations**: Fetch multiple protection groups simultaneously
- **Efficient Server Resolution**: Optimized tag-based sers
- **Reduced API Calls**: Minimize DRS API calls through inhing
- **Smart Conflict Detection**: Fast server conflict validation withou

**Capabilities**:
 regions
- Visual server se
- Single server per group constraint (globally enforced across all users)
- Real-time search and filtering in server discovery panel
- Conflict detection prevents duplicate 
- Server validation against DRS API (prevents fa
- Tag-based server selection with preview functionality
- Launch configuration settings applied to all servers in tp

**UI Components**:
- CloudScape Table with CRUD operations, sorting, filtering, pagination
- ProtectionGroupDialog modal with tabbed server selection (Tags vs Servers)
- RegionSelector with all 30 DRS regions
- ServerDiscoveryPanel with search and filtering
- ServerSelector with checkbox selection and assignment status badges
- LaunchConfigSection for DRS launch settings configuration

ts**:
- `GET /protection-groups` - Lion mode
tion
- `GET /protection-groups/{id}` - Get single group with enriched server details
ns)
- `DELETE /protection-groupy Plan)
- `POST /protection-groups/resolve` - Preview servers matching specified tags
- `GET /drs/source-servers?region={region}` - Discover DRS servers with assignment status

### 2. Multi-Account Management

Enterprise-grade multi-account orchestration with hub-and-spoke architecture, centralized management, and cmption.

**Account Context System**:
- **Account Selection Enforcement**: Features blocked until target account selected (mult
- **Auto-Selection**: Single accounts automatically selected as default for seamless user e
- **Account Selector**: Top navigation dropdown for intuitive account switching with fs
- **Setup Wizard**: Guided first-time account configuration for new users
- **Default Preferences**: Persistent default account selection integrated into e panel
)

**Cross-Account Architecture**:
- **Hub-and-Spoke Model**: Central orchestration account maunts
- **Cross-Account Role Assumption**: STS-based role ass
- **Target Account Registration**: Register/unregisteion
- **Account Health Monitoring**: Monitor cross-accos
ounts

**Capabilities**:
- Scale beyond 300-server DRS limit per account ion
- Centralized orchestration with distributed DRS operans
- Account-specific Protection Groups and Recovery Plans
- Cross-account execution monitoring arails
n

**UI Components**:
- AccountSelector dropdown in top navigation
- AccountRequiredWrapper for feature enforcement
- AccountRequiredGuard for specific feature protection
- Account setup wizard for first-time configuration
dal

**API Endpoints**:
- `GET /accounts/current` - Get current AWS account information
- `GET /accounts/targets` - Get target accounts for multi-acons
- `POST /accounts/targets` - Register new target account with cross-acrole

- `DELETE /accounts/t

**Infrastructure**:

- **target-accoun
- Cross-account DRS client creation with STption
- Account context propagation through

### 3. Recovery Plans

Wave-based orchestration with multi-Protection Group support, p

**Performance Optimizat
- **Mem
-renders
- **Reduced Pollin10s
- **Smart State Managements

**Capabilities**:
- Unlimited waves with sequential cution
- Multiple Protection G per wave
- Wave dependencies with con
-ckpoints
- Dmodes
roups
- Real-time executtatus
- Existing instance detection with scalable UI for large deplo

**Wave Configuration**:
```json
{
  "waveNumber": 0,
  "name": "Database Tier",
  "description": "Primary databases",
  "protectionGroupIds": ["pg-uuid-1", "pg-uuid-2"],
  "serverIds": ["s-xxx", "s-yyy"],
  "dependsOnWaves": [],

}
`

**:
- CloudScape Table with executmes
- RecoveryPlanDialog modal with WaveConfigEditor
- WaveConfigEditor with expandable sections, multi-select ctor
- Execute dropdown with Drill/Recovery options
- Performance-optimized existing instances dialog with smart rendering

ts**:
- `GET /recovery-pl status
- `POST /recovery-plans` - Create plan with wave configurat
- `GET /recovery-plans/{id}` - Getls
- `PUT /recovery-plans/{id}` - Update plan (bl
- `DELETE /recovery-plans/{id}` - Del

### 4. Execution Engine

Step Functions-driven recovery automation with pause/recks.

**Performance Optimizations**:
- **Optimized Instance Checks**: Reducedns
- **Batch DynamoDB Operations**: Fetc

- **Early Exit Conditions**
- **Reduced Scan Scope**: Execution history scan reducrds

**Server Conflict Detection**:
- Prevents starting executions when servers are already in us
- Checks ALL servers across ALL waves of the recovey plan
servers
- Frontend proactively dist
- API returns `hasServerConflict` and `conflictInfo` fields for eacan

**Existing Instance Detection**:
- **Fast API Response**: Optimized backenonds
:
  - ≤10 instances: Show full taby
  - >10 instances: Show summary with collapsible detailed view
  - >25 instances: Add pagination for very large deployments
- **Essential Information**: Focus on critical instance details (Name
- **Instance Summary**: Shows running vs stopped counts for quick assessment

on Flow**:
1. Check for server conflicts with active/paused executions
 exist
3. Check for exist
4. Create execution record with PENDING status
5. Start Step Functions state machine
6. For each wave:
   - Check for `pauseBeforeWave` configuration
   - If paused: Enter `waitForTaskToken` state (up to 1 ye)
   - Call DRS `StartRecovery` API with all wave servers
   - Poll job status via Step Functions orchestration
   - Wait for all servers to reach LAUNCHED status
   - Update execution record in DynamoDB


*:
- Waves can be configured with `pauseBeforeWave: true`
tern
- Task token stor record
- Resume via API triggers `SendTaskSuccess` with stored token
- Maximum pause duration: 1 year (31536000 seconds)

**Instance Termination**:
- Available only for terminal states (COMPLETED, FAILED, CANCELLED)
- Terminates all EC2 recovery instances launched during execution
rue`
- Prevents duplica

**Status Values**: PENDING, POLLING, INITIATED, LAUNCHING, STARTEED

**:
- `ERY)
agination
- `GET /executions/{id}` - Get 
es)
- `POST /executions/{id}/resume` - Resume paused execution

- `GET /executionlogs
- `DELETE /executions` - Bulk delete completed executions
- `GET /recovery-plans/{id}/check-existing-instances` - Performance-optimized existing insheck



Real-time validation and enforcement of AWS DRS service limits to prevent API errors s.

**Capabilities**:
- **Hard Limit Enforcement**: 300 replicating servers per account per region (cannot be increased)
- **Job Size Validation**: Maximum 100 servers per recovery job (preventss)
- **Concurrent Job Monitoring**: Maximum 20 concurrent jobs across all operations
- **Total Server Tracking**: Maximum 500 servers across all active jobs
- **Real-time Quota Display**: Live usage metrics in UI with status indicators
- **Proactive Blocking**: Prevents operations that would exceed limits before API calls

**API Endpoints**:
- `GET /drs/service-limits?region={region}` - Get current limits and usage
- `POST /drs/validate-limits` - Validate operation against limits
- `GET /drs/quotas?region={region}` - Get comprehensive quota dashboard data

n

Fixed and enhanced tag-based server selection with DRS s.

**Capabilities**:
- **DRS Source Server Tags**: Queries act
eview
- **Regional Suppo
- **Preview Enhancement**: Tag preview shows identical detailed information ion
- **Clean UX**: Removed confusing non-functional checkboxes from tag preview for cleace

**Tag Query Enhancement**:
- Uses DRS `list_tags_for_resourceags
ies
- Field consistenc
- Regional flexibility with proper error handling

**API Endpoints**:
- `POST /drs/query-servers-by-tags` - Query DRS source sels





*:
- **Automated Sch
- **Manual Triggers**: Immediate synchronization capability for urgent tag updates
- **Cross-Region Support**: Sync tags across all 30 DRS-supported regions automatically
- **Batch Processing**: Handles large server inventories with 10-server chunks to avoid API limits
- **Progress Monitoring**: Real-time progress tracking with detailed status updates and comprehensive ng
- **Selective Sync**: Choose specific servers or sync all servers in a region
acefully
- **Audit Trail**: Complet
- **Settings Integration**: Configure sync schedules via Settings moion

**EventBridge Integration**:
- **Scheduled Execution**: EventBridge rules trig
ules
- **Schedule Valid
- **Source Detection**: Differentiate between manual UI triggers and automated EventBridge triggers
ources

**:
1. Discover DRS source servers across specified regions

3. Compare existices
4. Apply tag updates to DRS source servers in batches
5. Report sync results with success/failure counts
6. Update execution history with detailed progress

**Security Model**:
- **Multi-Layer Security Validation**: Comprehensive security validation for 
- **Source IP Validation**: Verify EventBridge requests originate from legitimates
- **Request Structure Validation**: Prevent direct Lambda invocati
- **Authentication Header Validation**: Reject requests with unexpected Authorization hears

- **Comprehensive Security A
- **Zero Trust Authentication Bypass**: Scoped access with maximum security validation
- **Attack Surface Reduction**: Minimal bypass scope limited to `/drs/tag-syn

**API Endpoints**:
- `POST /drs/tag-sync` - Sync EC2 tags to DRS source servers with progress)
ule
- `POST /tag-syncon

### 8. RBAC Security System

Enterprise-grade role-based access control with 5 gra

**Security Roles (5 Granular Roles)**:
ons
2. **Recovery Manag
3. **Plan Manager**: Create and manage Protection Groups and Recovery Plans, view executions (no execution control)
4. **Operator**: Execute drills only, view assigned Protection Groups and Recovery Plans (no editing)
5. **Read Only**: View-only access to all data with no modification capabilities

**Granular Permissions (14 Business-Focused Permissions)**:
- **Protection Groups**: `CREATE_PROTECTION_GROUP`, `UPDATE_PROTECTION_GROUP`, `DELETE_PROTECOUP`
- **Recovery Plans**: `CREATE_RECOVERY_PLAN`, `UPDATE_RECOVERY_PLAN`, `DELETE_RECOVERY`
- **Executions**: `EXECUTE_RECOVERY`, `EXECUTE_DRILL`, `CONTROL_EXECUTION`, `TERMINATE_INSTANN`

**Permission-Aware:
- **PermissionAwareButton**: Buttons that respect user permissions (disabled/hidden based on role)
- **PermissionAwareButtonDropdown**: Dropdown menus with permission-filteons
- **PermissionWrapper**: Conditional rendering wrapper for permission-basontent

- **usePermissionCheck**: React hookc


- All 42 REST API endpoints enforce identical permission boundaries
- Cognito Groups integration for role assignment
- JWT token-based permission validation
- Comprehensive audit trails with role context
- Consistent enforcement across UI, CLI, API, and automation access methods

**Security Implementation**:
- **rbac_middleware.py**: Centralized permission enforcement for all Lambda functio
nt
- **Role Mapping**: Cognito
nce
- **Audit Integration**: All actions logged with user role and permission context

**User Management**:
- Password reset capability for new users with temporary passwords
- Cognito-managed user lifecycle with group-based role assignment
- Activity-based inactivity timeout (4 hours) with comprehensive activity tracking
- Automatic token refresh every 50 minutes to prevent session expiration
- Multi-factor authentication support (Cognito-managed)

**API Endpoints**:
- `GET /user/permissions` - Get current user's permissions based on Cognito groups
- All endpoints include role-based access validation

t

Complete export/import system for configuration backup, environment migration, and disaster recove

**Export Capabilities**:
- **Full Configuration Export**: Export all Protection Groups and Recovfile
- **Portable Format**: Uses `ProtectionGroupName` instead of UUIDs for crosy
 context
- **Validation Checksums**: Buiata
- **Settings Integration**: Export functionality accessible via Setr icon

**Import Capabilities**:
- **Non-Destructive Import**: Additive-only im
- **Dry Run Validation**: Preview import results before applying changes
ort
- **Server Validation**: Val
- **Conflict Detection**: Identifies naming conflicts and provides resolution options
- **Progress Tracking**: Real-time import progress with detailed status updat

**Portable JSON Format**:
```json

  "exportMetadata": {
    "version": "1.0",
    "exportDate": "2026-01-01T12:00:00Z",
    "exportedBy": "user@example.com",
    "sourceEnvironment": "prod"
  },
  "protectionGroup [
    {
      "groupName": "Database-Tier",
-1",
      "serverSelectionTags": {"DR-Tier": "Database"},
s-yyy"]
    }
  ],
  "recoveryPlans": [
{
      "planName":,
      "waves": [
        {
          "waveName": "Database",
          "protectionGroupNames": ["Database-Tier"],
          "pauseBeforeWave": false

      ]
    }
  ]
}


**Environment Migration**:
- Export from source environment (dev/test/prod)

- Cross-account compatibility with ing
s


- **SettingsModal**: Three-tab modal (Expear icon
lity
- **ConfigImportPanel**: File upload with drag-and-drop support and validation
n

**API Endpoints**:
- `GET /config/export` - Export all Protection Groule JSON
- `POST /config/import` - Import configuration from JSON with valid support
- `POST /config/validate` - Validate impos

agement

Complete DRS source ser

#### 10.1 Server Info & Recovery Dashboard

Read-only visibility into DRS source server de

**Capabilities**:
- Server details panel with hostname, OS, Cork

- Recovery readine
- Lifecycle state display with timestamps



| Field | Description |
-|
| sourceServerID ) |
| hostname | Source server hostname |
| lifeCycle | Lifecycle state and times
| dataReplicationInfo | gress |
| sourceProperties
| lastLaunchResult | Last recovery re

**API Endpoints**:
tails

#### 10.2 DRS Launch Settings



es**:
- Instance Type Right Sizing method (NONE, BASIC, IN_AWS)
, STARTED)
- Copy Private IP option
- Copy Tags option
- OS Licensing (BYOL or AWS-provided)

**Behavior**: Settings are confived.

**API Endpoints**:
g
- `PUT /protection

#### 10.3 EC2 Launch Template

Configure EC2 launch template settings for recovery instances at the .

**Capabilities**:
g
- Subnet selection from available VPC subnets
(multiple)
- IAM instance prtion

**Behavior**: Settings are stored i

**API Endpoin*:
- `GET /ec2/subnets?region={region}` - List available subnets
roups
- `GET /ec2/instances
- `GET /ec2/instance-types

#### 10.4 Tags Management

.

**Capabilities**:
- View all server tags
- Add new tags with key-value pairs

- Delete tags
imits)

s**:
- Max 50 tags per
- Key: 1-128 characters, no `aws:` prefix
- Value: 0-256 characters
- Case-sensitive

:
- `GET /drs/source-sers
- `PUT /drs/source-servers/{id}/tags` - tags
- `DELETE /drs/source-servers/{id}/tagsgs

#### 10.5 Disk Settings

Configure per-disk settings for DRS source ser.

**Capabilities**:
tor)
- Edit disk type (SC1)
- Configure IOPS (for io1/io2/gp3)
- Configure throughput (for gp3)

**Disk Type Options**:

|------|----------|------|------------|
|
| gp2 | General p/A |
| io1 | High performance | Up tA |
| io2 | High performance | Up to 64000 | N/A |
| st1 | Throughput optimized | N/A | Up to 5/s |
| sc1 | Cold storage | N/A | Up to 250 M

**API Endpoints**:
- `GET /drs/source-servern
- `PUT /drs/source-servers/{id}/disks` - Update disration

#### 10.6 Replication Setting

Crs.

**Capabilities**:
- Staging area subnet selection
- Security group configuration for replication servers
- Ron
-
- B
IC_IP)
- EBS encryption s
- Point-in-time (PIT) snapshot policy configuration

**PIT Policy Configuration**:
on
{

    { "interval": 10, "retentionDuration": 60, "units
 },
    { "interval":
  ]
}
```

**API Endpoints**:
- `GET /drs/source-servetion
ion
- `GET /drs/staginoups

#### 10.7 Post-Launch Settings

Configure post-launch actions for recovery instances.

**Capabilities**:
_ONLY)
- SSM automation document selection
)
- Must succeed for cutovoption
- S3 log bucket configuration
- S3 key prefix for logs

**API Endpoints**:
- `GET /drs/source-servers/{id}/post-launch?region={region}` - Get post-launch configura
ion
- `GET /ssm/documents?rents
- `GET /s3/buckets?region={region}` - List available S3 buckets

### 11. Security Vulnerability Fixes

Comprehensive security hardening addressing critical vulnerability classes with inputtices.



**SQL I**:
-
- **Fix**: Implemente
- **Scope**: All Lambs.py)
- **Validation**: Input sanitization befo

**Cross-Site Scripting (CWE-20,9, 80)**:
- **sers
- **Fix**: Comprehensivs
- **S
- **Implementation**: HTML encodingpractices

**OS Command Injection (CWE-78, 77, 88)**:
- **Risk**: Malicious input could execute snds
- **Fl files
- **ands
- **Validation**: St

**Log Injection (CWE-117)**:
- **Risk**: Mali
- **Fix**
- **Scope**: All logging statemenntend
- **Implementation**: Log sanitization middleware an

**Securitils**:
- **Inputs
- **O
- *erations
-acks
- *internals

**Files Hardened**:
- **Backend**: `lambda/index.py`, `lambda/orches
- **Frontend**: All React components with user input or data 
- **Infrastructure**: CloudFormation templates with secure g

:
- Addresses OWASP ks
- Implements secure coding best practices
- Regular security scanning and validation with 6 security tools
- Comprehensive input/output sanitization



React 19.1 + TypeScript 5.9 + CloudScape Design System 3.0 with performance-optimized com.

**Pages (7 Total)**:

| Route | Compres |
|-------|-----------|-------------|---------------------|
| /login | LoginPage | Cognito authentication with error handling | Local  |
| / | Dashboard | Metrics cards, pie chart, active executions, recent a|
| /getting-started | GettingStartedPage | 3-step onboarding guide wt |
| /protection-groups | ProtectionGroupsPage | CRUD table with server lling |
ling |
| /executions | ExecutionsPage | Act
dates |

ns**:
- **Memoized Column Definitions**: Prender
-renders
- **Reduced Polling Frequen 10s)
- **Smart State Management**: Efficient data structures (Map, Sece
- **Activity-Based Timeout**: 4-hour inactivity timeout with comprehensive activit
- **Automatic Token Refresh**: 50-minute token refresh to prevent session expiration
- **Local Asset Loading**: AWS logos served locally to avoid CO issues

**Key UI Features**:
- Real-time updates with optimized polling frequencies
- DRS Job Events timeline with auto-refresh
- Pause/Resume execution controls with loading states
- Terminate recovery instances button (terminal states only)
eas)
- Loading states on all action buttons (prcks)
- Toast notifications via react-hot-toast
- Activity-based auto-logout with comprehensive activity detection
- Responsive design, WCAG 2.1 AA compliant
- Multi-account context switching with enforcement
view
- Scalable existing instance)

**Component Library (37 Components + 2 CloudScape Wrappers + 6 Contexts = 4:

| Category | Components | Count | Performance Features |

| **CloudScape Wrappers** | AppLayou
| **Layout** | ErrorBoundary, ErrorFallback, ErrorState, LoadingState, C
| **Multi-Account** | AccountSelector, AccountRequiredWrappeare |
| **RBAC & Permissions** | PermissionAwareButton, PermissionAwareButtonDropdown | 2 |  caching |
| **Dialogs** | ProtectionGroupDialog, RecoveryPlanDialog, ConfirmDialog, on |
| **Server Management** | ServerSelector, ServerDiscoveryPanel, ServerListItem
ng |
| **Status Display*
| **Execution** | ExecutionDetails | 1 | Real-time optimization |
| **React Contexts** | AuthContext, PermissionsContext, Notificationent |

**:
- **Large Servents
- **Existing Instance Dialog**: Collaps
- **Batch Operations**: Efficient handlinns
- **Memory Management**: Proper cleanup anon



ference

n.

nts)
- `GET /protection-groups` - List als
- `POST /protection-groups` - Creat
- `GET /protection-groups/{id}` - Get Protection Group details with
- `PUT /protection-groups/{id}` - Update Protection Group (blocked during activeons)
- `DELETE /protection-groups/{id}` - Delete Protection Group (blocked if referenced ns)
- `POST /protection-groups/resolve` - Preview servers matching specified tags
- `GET /protection-groups/{id}/launch-config` - Get launch configuration settings

### Recovery Plans API (6 endpoints)
e counts
- `POST /recovery-plcies
- `GET /recovery-plans/{id}` - Get Recovery Plan details wi
- `PUT /recovery-plans/{id}` - Update Recovns)
- `DELETE /recovery-plans/{id}` - Delete Recovery Plans)
- `GET /recovery-plans/{id}/check-existing-instances` - Perfck

### Executions API (7 endpoints)
- `GET /executions` - List executions wit
- `POST /executions` - Start new execution (
- `GET /executions/{id}` - Get execution dtatus
- `POST /executions/{id}/resume` - Resume paused etion
- `DELETE /executions/{id}` - Cancel runncution
- `POST /executions/{id}/terminate-instances` - T
ecutions

)
- `GET /drs/source-servers` - Disus
- `GET /drs/quotas` - Get DRS serion
- `POST /drs/query-servers-by-tags` - Query servers by tagdetails
- `POST /drs/tag-sync` - Sync EC2 instance tags to DRS source servers

### DRS Server Management API (7 endpoints)
- `GET /drs/source-servers/{id}` - Get comprehensive server details and configuration
- `GET /drs/source-servers/{id}/launch-settings` - Get DRS launch configuration
- `PUT /drs/source-servers/{id}/launch-settings` - Update DRS launch configurati
- `GET /drs/source-servers/{id}/tags` - Get server tags
- `PUT /drs/source-servers/{id}/tags` - rver tags
- `DELETE /drs/source-servers/{id}/tags` - Remove server tags
 server


- `GET /ec2/subnets` - Liion
on
- `GET /ec2/instance-profiles` - List IAM instance profiles for EC2 instances


### Multi-Account Management API (4 endpoints)
- `GET /accounts/targets` - List registered target accounts with health status
- `POST /accounts/targets` - Register new target account with cross-account role
- `PUT /accounts/targets/{id}` - Update target account configuration
- `DELETE /accounts/targets/{id}` - Remove target account registration

### Configuration Management API (2 endpoints)

- `POST /config/import` - Import con

### System API (1 endpoint)
- `GET /health` - Health check endpoint for monitoring and load balancers

**Total: 42 REST API Endpoints**



## Technical Specifications

### Frontend Stack
| Technology | Version | Purpose | Performance Features |
|------------|---------|---------|--------------------
| React | 19.1.1 | UI framework with hooks | Concurrent features, automatic batching |
| TypeScript | 5.9.3 | Type safety | Compile-time optimizion |

| Vite | 7.1.7 | Build tool and dev sds |
| AWS Amplify | 6.15.8 | Cognito authentication | Auto token refresh |
| Axios | 1.13.2 | HTTP client | Request/response interceptors |
| React Router | 7.9.5 | Client-side routing | Code splitting support |
| react-hot-toast | 2.6.0 | Toast notifications | Lightweight, perfor
kable |

### Backend Stack
| Technology | Version | Purpose | Performance Features |
|------------|---------|---------|---------------------|
| Python | 3.12 | Lambda runtime | Latest performance i
| boto3 | (runtime) | AWS SDK | Connection pooling |
| crhelper | 2.0.11 | CloudFormation custom resources | Effic|



**Backend Performance**:
- **Batch DynamoDB Operations**: Reduce API calls through batch operations
- **Optimized Query Patterns**: Efficient data access patterns
- **Connection Pooling**: Reuse AWS service connections
ssible
- **Reduced Scan Scope**: Limit data scanning l records

**Frontend Performance**:
- **Memoization**: React.memo, useMemo, useCallback throughout
- **Optimized Polling**: Reduced frequencies (plans: 60s, executions: 10s)
e
- **Activity Tracking**: Efficient user activi detection
- **Local Assets**: Avoid external CORS requests

ntication
- Cognito User Pool with JWns
- Automatic token refresh every 50 minutes
ut)
- 401 handling with redirect to 
alls)

on

ry.

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

- drs:UpdateRepliration
- drs:ListTagsForResource
- drs:TagResource
- drs:UntagResource

# EC2 Permissions (required by DRS during recovery)
ces
- ec2:DescribeInstancetatus
- ec2:DescribeInstanceTypes
- ec2:DescribeLaunchTemplates
- ec2:DescribeLaunchTemplateVersions
- ec2:CreateLaunchTemplate
n
- ec2:ModifyLaunchTemplate

- ec2:RunInstances
tances
- ec2:TerminateInstances
- ec2:Colume
- ec2:AttachVolume
- ec2:CreateTags
- ec2:CreateNetworkface
- ec2:DeleteNetwor
- ec2:DescribeSubnets
- ec2:DescribeSecurityGroups
- ec2:DescribeVpcs

# SSM Permissions (for post-lau
- ssm:ListDocuments
- ssm:DescribeDocument

# S3 Permissions 
- s3:ListAllMyBucke


# IAM Permissions (for es)
- iam:ListInstanceProfiles
```

**Recovery Flow Timeline**:
1. Snapshot Creation: 1-2 minutes
2. Conversion Server Launch: 1-2 es
3. Launch Template Creatio
4. Recovery Instance Launcutes
5. Total per wave:minutes

---

## Deployment

### Prerequisites
- AWS Account with DRS enabl
- DRS source servers ting
- S3 bucket for deployment a
- Admin email for n

### GitHub Actions CI/CD Pipeline

**Pipeline Stages** (~total):
king
2. **Security Scan** (~2 min) - 6 securudit
3. **Build** (~3 min)
4. **Test** (~2 min) -
s
6. **Deploy Frontend** (~2 min) - S3 syncon

**Sols**:
lysis
- **Safety v2.3.4**: Depending
- **Semgrep v1.146.0**: Advanced 
- **CFN-Lint v0.83.8**: CloudFormation ss
- **ESLint**: Frontend security rules
- **NPM Audit**: Frontend dependency sca

fail

tructure
```

├── cfn/         
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
ml
│   ├── security-stack.yaml
│  tack.yaml
├── lambda/              ages
│   ├── api-handler.zip
│   ├── orchestration-stepfu.zip
│   ├── execution-finder.zip
│   ├── execution-poller.
│   └── frontend-buildzip
└── frontend/                    rtifacts
    └── dist/
```

### Deploy Command
```bash
aws cloudformation deploy \
  --template-url https://{bul \
  --stack-name drs-orchestra
  --parameter-overrides \
    ProjectNa\
   v} \
} \
    AdminEmail={eml} \
  --cap \
  --region {region}
```

### Stack Outputs
- `CloudFrontURL`: Frontend applica
- `ApiEndpoint`: REST AI endpoint
- `UserPoolId`: Cognito Use ID
- `UserPoolClientId`: CoD
- `FrontendBucketName`: S3 bucket for frontend assets

###
CLI
2. Configure DRS n
3. Access CloudFront URL and sign in
4. Create Protection Groups, Recovills

---

s

### Operational Targets
| Metric | Target | Current Performance |
|--------|--------|-----------------|
| Recovery Time Objective (RTO) | <15 minutes per wave | ~1
tes |
| E

| UI Response Time |
 |

### Performance Imp
| Operation | Befornt |
|-----------|--------|-------|-------------|
| Run Drill Click | 5-8 seconds | 2-3 seconds | 60% faster |
| Existing Instance Check | O(n*m*k
| Table Rendering | Re-render|
ad |

### Cost Estimates (Mothly)
| Service | Estimate |
|---------|--------|
| Lambda | $1-5 |
| API Gateway | $3-0 |
| DynamoDB | $1-5 |
| CloudFront1-5 |
| S3 | <$1 |
| Step Functions | $1-5 |
| Cognito | Free tier |
|

### User Experience Targets
| Task | Target Time |ormance |
|------|-------------|-------------------|
| Create Protection Group | <5 minutes
| Create Recovery Plan | <15 miminutes |
| Execute Drill | <30 minutes | <25 minutes |
| Configure Server Launch Settings | <2 minut |
es |
| L

---

## AWS DRS Regional Availability

The solution supports all **30 AWS

| Region Group | Count | Regions |
|--------------|-------|---------|
| **Americas** | 6 | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America ( |
| **Europe** | 8 | Ireland, London, Frankfurt, Paris, Stockholm, Milch |
| **Asia Pacific** | 10 | Tokyo, Seoul,ong |

| **GovCloud** | 2 | US-East, US-West |

*Rem.*

---

## DRS Service Limits Compliance

The solution enforces AWS DRS s errors:

| Limit | Value | Enforcement |
|-------|-------|-------------|
| Max replicating servers | 300 | UI validation, API vali|
dation |
| M|
 |

---

## Version History

### v1.4.1 (Current) - Performance Optimized
- **Backend Performance**: Optimized existing instance checks (2-3 second improve
- **Frontend Performance**: Memoized components, reduced polling, scalable UI
- **Security**: Comprehensive security scanning with 6 tools
- **UX**: Activity-based timeout, automatic token refresh, local AWgos

### v1.4.0 - Multi-Account & Tag Sync
- Multi-account management with hub-and-spoke architecture
G_GUIDE.md)LESHOOTIN/TROUBe](../guidesGuidng hootioublesE.md)
- [TrLOW_GUIDT_WORKFENLOPMDEVEes//guide](.. Guidowflnt Work[Developme
- UIDE.md)ERENCE_Gs/API_REFe](../guideence Guid- [API Refer)
T.mdUMEN_DOC_DESIGNRALCHITECTUcture/ARchitear](../cture Designrchite
- [A_GUIDE.md)ICDS_CB_ACTIONGITHUloyment/./guides/depCD Guide](.I/ctions C A [GitHub.md)
-TIONSECIFICAESIGN_SPUI_D(./UX_cations]pecifiUI Design S
- [UX/FICATION.md)SPECIIREMENTS_E_REQU/SOFTWARon](.atiSpecificments Require [Software 

-cesen## Refer


---
rastructuren infloudFormatioation
- Ctichen autk
- CognitoUI frameworpe udScation
- CloDRS integraic tion
- Basda0 - Foun# v1.1.

##monitoringe execution imeal-tesume
- Rwith pause/rtomation unctions autep F
- Sselectioner servps with ion GrouProtectn
- orchestratiovery ed recoave-basration
- Westre Orch2.0 - Co### v1.
y fixes
rabilitulnecurity v Seons
- 14 permissi roles and 5system withecurity h)
- RBAC s, Post-LauncionReplicats, , Tags, Disk, EC2 Launch (Info,gement areas manaserverent
- 7  managemiononfiguraterver c sceurplete DRS soomt
- CagemenServer Man.0 - DRS  v1.3
###system
t port/imporguration ex Confier tags
-ource servS s with DRlectionrver seag-based senhanced tuling
- EBridge sched Eventon withnizati synchroagted tma- Auto