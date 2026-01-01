# AWS DRS Orchestration Solution

Enterprise-grade disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

[![AWS](https://img.shields.io/badge/AWS-DRS-FF9900?logo=amazonaws)](https://aws.amazon.com/disaster-recovery/)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-232F3E?logo=amazonaws)](cfn/)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB?logo=react)](frontend/)
[![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?logo=python)](lambda/)
[![Release](https://img.shields.io/badge/Release-v1.2.0%20Tag%20Sync-green)](https://github.com/your-repo/releases/tag/v1.2.0)

## 🚀 **Latest Release: v1.2.0 - Tag Synchronization**

**Latest Version**: v1.2.0 - Tag Synchronization (January 1, 2026)  
**Git Tag**: `v1.2.0`

### 🔄 **What's New in v1.2.0**

- **Automated Tag Synchronization**: EventBridge-scheduled sync from EC2 instances to DRS source servers
- **Flexible Scheduling**: Configure sync intervals from 15 minutes to 24 hours via Settings modal
- **Manual Triggers**: Immediate synchronization capability for urgent tag updates
- **Multi-Region Support**: Automatically processes all 28 commercial AWS DRS regions
- **EventBridge Fix**: Resolved schedule expression validation error for "1 hour" intervals
- **Enhanced Protection Groups**: Tag-based server selection now works reliably with synced tags
- **Real-Time Progress**: Live status updates and comprehensive error handling during sync operations
- **Enterprise Security** 🆕: Multi-layer security validation for EventBridge authentication bypass (v1.2.1)

**[View Complete v1.2.0 Release Notes →](CHANGELOG.md#120---january-1-2026)**

## Overview

AWS DRS Orchestration enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native serverless services.

### Key Capabilities

- **Cost-Effective**: $12-40/month operational cost with pay-per-use serverless pricing
- **Unlimited Waves**: Flexible wave-based orchestration with no artificial constraints
- **Platform Agnostic**: Supports any source platform (physical servers, cloud instances, virtual machines)
- **Sub-Second RPO**: Leverages AWS DRS continuous replication capabilities
- **Fully Serverless**: No infrastructure to manage, scales automatically

## Key Features

### Multi-Account Management 🆕

- **Account Context System**: Complete account management with enforcement logic and persistent state
- **Auto-Selection**: Single accounts automatically selected as default for seamless user experience
- **Account Selector**: Top navigation dropdown for intuitive account switching with full page context updates
- **Setup Wizard**: Guided first-time account configuration for new users
- **Default Preferences**: Persistent default account selection integrated into existing 3-tab settings panel
- **Page-Level Enforcement**: Features blocked until target account selected (multi-account scenarios only)
- **Enterprise Scale**: Foundation for managing DRS across multiple AWS accounts

### Protection Groups

- **Automatic Server Discovery**: Real-time DRS source server discovery across all AWS DRS-supported regions
- **Enhanced Tag-Based Selection** 🆕: Fixed to query DRS source server tags (not EC2 instance tags) with complete hardware details
- **Hardware Information Display**: Comprehensive server details including CPU cores, RAM (GiB), and IP address displayed in clean format during server selection
- **Tag-Based Server Selection**: Define Protection Groups using DRS source server tags (e.g., `DR-Application=HRP`, `DR-Tier=Database`)
- **Automated Tag Synchronization** 🆕: EventBridge-scheduled sync from EC2 instances to DRS source servers
  - Configurable schedules (15min to 24hr intervals) via Settings modal
  - Manual trigger capability for immediate synchronization
  - Batch processing across all 28 commercial AWS DRS regions
  - Real-time progress tracking and comprehensive error handling
- **Visual Server Selection**: Intuitive interface with assignment status indicators and detailed hardware specifications
- **Conflict Prevention**: Single server per group constraint prevents recovery conflicts; tag conflicts detected automatically
- **Real-Time Search**: Filter servers by hostname, Server ID, or Protection Group name

### Recovery Plans

- **Wave-Based Orchestration**: Define multi-wave recovery sequences with unlimited flexibility
- **Dependency Management**: Automatic wave dependency handling with circular dependency detection
- **Drill Mode**: Test recovery procedures without impacting production
- **Automation Hooks**: Pre-wave and post-wave actions for validation and health checks

### Execution Monitoring

- **Real-Time Dashboard**: Live execution progress with wave-level status tracking
- **Invocation Source Tracking**: Track execution origin (UI, CLI, API, EVENTBRIDGE, SSM, STEPFUNCTIONS)
- **Enhanced History Management** 🆕: Improved History page with selective deletion, fixed invocation source filtering, and descriptive search functionality
- **Date Range Filtering** 🆕: Comprehensive date filtering for execution history with American date format (MM-DD-YYYY), quick filter buttons (Last Hour, Today, Last Week, etc.), and custom date range selection
- **Pause/Resume Control**: Pause executions between waves for validation and resume when ready
- **Instance Termination**: Terminate recovery instances after successful testing with accurate progress tracking
- **DRS Job Events**: Real-time DRS job event monitoring with 3-second auto-refresh and collapsible view
- **Execution History**: Complete audit trail of all recovery executions with source badges and selective cleanup
- **CloudWatch Integration**: Deep-link to CloudWatch Logs for troubleshooting
- **Auto-Refresh**: All pages auto-refresh (30s for lists, 3-5s for active executions)

### EC2 Launch Configuration

- **Launch Template Management**: Configure EC2 launch settings per Protection Group
- **Complete Instance Type Support** 🆕: Access to ALL available EC2 instance types supported by DRS in each region (968+ types including modern families like m6a, m7i, c7g, r7i, and all current-generation instances)
- **Network Configuration**: Select subnets and security groups for recovery
- **IAM Instance Profiles**: Assign instance profiles to recovery instances
- **DRS Launch Settings**: Instance type right sizing, launch disposition, copy private IP/tags, OS licensing
- **Automatic Application**: Settings applied to all servers in Protection Group on save

### Configuration Export/Import

- **Full Backup**: Export all Protection Groups and Recovery Plans to JSON file
- **Portable Format**: Uses `ProtectionGroupName` instead of IDs for cross-environment portability
- **Non-Destructive Import**: Additive-only import skips existing resources by name
- **Name Resolution**: Automatically resolves Protection Group names to IDs during import
- **Dry Run Mode**: Validate import without making changes
- **Server Validation**: Verifies DRS source servers exist before import
- **Settings Modal**: Access via gear icon in top navigation bar

### Tag Synchronization 🆕

- **Automated Scheduling**: EventBridge-triggered tag sync from EC2 instances to DRS source servers
- **Flexible Intervals**: Configure sync schedules from 15 minutes to 24 hours
- **Manual Triggers**: Immediate synchronization capability for urgent updates
- **Multi-Region Support**: Processes all 28 commercial AWS DRS regions automatically
- **Batch Processing**: Handles large server inventories with 10-server chunks
- **Progress Tracking**: Real-time status updates and comprehensive error reporting
- **Settings Integration**: Configure via Settings modal accessible from top navigation
- **Enterprise Security**: Multi-layer security validation for EventBridge authentication bypass with comprehensive audit logging

## Architecture

![AWS DRS Orchestration Architecture](docs/architecture/AWS-DRS-Orchestration-Architecture.png)

*[View/Edit Source Diagram](docs/architecture/AWS-DRS-Orchestration-Architecture.drawio)*

The solution follows a serverless, event-driven architecture with clear separation between frontend, API, compute, data, and DRS integration layers. Users access the React frontend via CloudFront, authenticate through Cognito, and interact with the REST API backed by Lambda functions. Step Functions orchestrates wave-based recovery execution, coordinating with AWS DRS to launch recovery instances.

### Technology Stack

| Layer      | Technology                                               |
| ---------- | -------------------------------------------------------- |
| Frontend   | React 19.1, TypeScript 5.9, CloudScape Design System 3.0 |
| API        | Amazon API Gateway (REST), Amazon Cognito                |
| Compute    | AWS Lambda (Python 3.12), AWS Step Functions             |
| Database   | Amazon DynamoDB (3 tables with GSI)                      |
| Hosting    | Amazon S3, Amazon CloudFront                             |
| DR Service | AWS Elastic Disaster Recovery (DRS)                      |

## AWS DRS Regional Availability

The solution orchestrates disaster recovery in all **30 AWS regions** where Elastic Disaster Recovery (DRS) is available:

| Region Group                   | Count | Regions                                                                                                    |
| ------------------------------ | ----- | ---------------------------------------------------------------------------------------------------------- |
| **Americas**             | 6     | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America (São Paulo) |
| **Europe**               | 8     | Ireland, London, Frankfurt, Paris, Stockholm, Milan, Spain, Zurich                                         |
| **Asia Pacific**         | 10    | Tokyo, Seoul, Osaka, Singapore, Sydney, Mumbai, Hyderabad, Jakarta, Melbourne, Hong Kong                   |
| **Middle East & Africa** | 4     | Bahrain, UAE, Cape Town, Tel Aviv                                                                          |
| **GovCloud**             | 2     | US-East, US-West                                                                                           |

*Regional availability determined by AWS DRS service. As AWS expands DRS, the solution automatically supports new regions.*

## Quick Start

### Prerequisites

- AWS Account with DRS configured and source servers replicating
- AWS CLI v2 configured with appropriate permissions
- S3 bucket for deployment artifacts

### Deploy with CloudFormation

```bash
# Deploy the complete solution
aws cloudformation deploy \
  --template-url https://your-bucket.s3.us-east-1.amazonaws.com/cfn/master-template.yaml \
  --stack-name drs-orchestration \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    Environment=prod \
    SourceBucket=your-bucket \
    AdminEmail=admin@yourcompany.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Deployment takes approximately 20-30 minutes.

### Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs' \
  --output table
```

| Output           | Description              |
| ---------------- | ------------------------ |
| CloudFrontURL    | Frontend application URL |
| ApiEndpoint      | REST API endpoint        |
| UserPoolId       | Cognito User Pool ID     |
| UserPoolClientId | Cognito App Client ID    |

### Create Admin User

```bash
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@yourcompany.com \
  --user-attributes Name=email,Value=admin@yourcompany.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin@yourcompany.com \
  --password "YourSecurePassword123!" \
  --permanent
```

## Usage Guide

### Creating a Protection Group

1. Navigate to **Protection Groups** in the sidebar
2. Click **Create Protection Group**
3. Enter a unique name and select the AWS region
4. Select source servers from the discovery list (green = available, red = assigned)
5. Click **Create**

### Creating a Recovery Plan

1. Navigate to **Recovery Plans** in the sidebar
2. Click **Create Recovery Plan**
3. Enter plan name and configure waves:

| Wave | Tier        | Protection Groups        | Depends On |
| ---- | ----------- | ------------------------ | ---------- |
| 1    | Database    | DB-Primary, DB-Secondary | -          |
| 2    | Application | App-Servers              | Wave 1     |
| 3    | Web         | Web-Servers              | Wave 2     |

4. Configure optional pre/post-wave automation
5. Click **Create**

### Executing a Recovery

1. Navigate to **Recovery Plans**
2. Select a plan and click **Execute**
3. Choose execution type:
   - **Drill**: Test recovery without production impact
   - **Recovery**: Full disaster recovery execution
4. Monitor progress in **Executions** page
5. **Control execution**:
   - **Pause**: Stop between waves for validation
   - **Resume**: Continue paused execution
   - **Cancel**: Stop execution and cleanup
   - **Terminate Instances**: Remove recovery instances after testing

## Infrastructure

### CloudFormation Stacks

The solution uses a modular nested stack architecture for maintainability:

| Stack                         | Purpose             | Key Resources                     |
| ----------------------------- | ------------------- | --------------------------------- |
| `master-template.yaml`      | Root orchestrator   | Parameter propagation, outputs    |
| `database-stack.yaml`       | Data persistence    | 4 DynamoDB tables with encryption |
| `lambda-stack.yaml`         | Compute layer       | Lambda functions, IAM roles     |
| `api-stack-rbac.yaml`       | API & Auth with RBAC | API Gateway, Cognito, RBAC endpoints |
| `step-functions-stack.yaml` | Orchestration       | Step Functions state machine      |
| `eventbridge-stack.yaml`    | Event scheduling    | EventBridge rules for polling     |
| `security-stack.yaml`       | Security (optional) | WAF, CloudTrail                   |
| `frontend-stack.yaml`       | Frontend hosting    | S3, CloudFront                    |
| `cross-account-role-stack.yaml` | Multi-account (optional) | Cross-account IAM roles |

### DynamoDB Tables

| Table                       | Purpose             | Key Schema                            |
| --------------------------- | ------------------- | ------------------------------------- |
| `protection-groups-{env}` | Server groupings    | `GroupId` (PK)                      |
| `recovery-plans-{env}`    | Wave configurations | `PlanId` (PK)                       |
| `execution-history-{env}` | Audit trail         | `ExecutionId` (PK), `PlanId` (SK) |
| `target-accounts-{env}`   | Multi-account management | `AccountId` (PK), StatusIndex GSI |

## Cost Estimate

| Component       | Monthly Cost (Est.)    |
| --------------- | ---------------------- |
| Lambda          | $1-5                   |
| API Gateway     | $3-10                  |
| DynamoDB        | $1-5                   |
| CloudFront      | $1-5                   |
| S3              | <$1                    |
| Step Functions  | $1-5                   |
| Cognito         | Free tier              |
| **Total** | **$12-40/month** |

*Costs vary based on usage. DRS replication costs are separate and depend on protected server count.*

## Security & RBAC

### Role-Based Access Control (RBAC)

The solution implements comprehensive role-based access control with 5 granular DRS-specific roles, each providing specific permissions for disaster recovery operations. RBAC enforcement occurs at the API level, ensuring all access methods (UI, CLI, SDK, direct API calls) respect identical security boundaries.

#### RBAC Roles & Permissions

| Role | Description | Key Permissions | Use Case |
|------|-------------|-----------------|----------|
| **DRSOrchestrationAdmin** | Full administrative access | All operations including configuration export/import | System administrators, DR team leads |
| **DRSRecoveryManager** | Recovery operations and configuration | Execute plans, manage configuration, export/import settings | DR managers, recovery coordinators |
| **DRSPlanManager** | Plan management focus | Create/modify protection groups & recovery plans, execute plans | Infrastructure teams, DR architects |
| **DRSOperator** | Execution operations only | Execute/pause/resume recovery plans, terminate instances | Operations teams, on-call engineers |
| **DRSReadOnly** | View-only access | Complete read-only access to all DRS configuration and status | Auditors, compliance officers |

#### Detailed Permission Matrix

The RBAC system implements 14 granular permissions mapped to business functionality:

| Permission | Admin | Recovery Manager | Plan Manager | Operator | Read Only |
|------------|-------|------------------|--------------|----------|-----------|
| **Protection Groups** |
| CREATE_PROTECTION_GROUP | ✅ | ❌ | ✅ | ❌ | ❌ |
| READ_PROTECTION_GROUP | ✅ | ✅ | ✅ | ✅ | ✅ |
| UPDATE_PROTECTION_GROUP | ✅ | ❌ | ✅ | ❌ | ❌ |
| DELETE_PROTECTION_GROUP | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Recovery Plans** |
| CREATE_RECOVERY_PLAN | ✅ | ✅ | ✅ | ❌ | ❌ |
| READ_RECOVERY_PLAN | ✅ | ✅ | ✅ | ✅ | ✅ |
| UPDATE_RECOVERY_PLAN | ✅ | ✅ | ✅ | ❌ | ❌ |
| DELETE_RECOVERY_PLAN | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Executions** |
| EXECUTE_RECOVERY_PLAN | ✅ | ✅ | ✅ | ✅ | ❌ |
| READ_EXECUTION | ✅ | ✅ | ✅ | ✅ | ✅ |
| CANCEL_EXECUTION | ✅ | ✅ | ✅ | ✅ | ❌ |
| TERMINATE_INSTANCES | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Configuration** |
| EXPORT_CONFIGURATION | ✅ | ✅ | ❌ | ❌ | ❌ |
| IMPORT_CONFIGURATION | ✅ | ✅ | ❌ | ❌ | ❌ |

#### User Management

Users are managed through AWS Cognito Groups. To assign roles to users:

1. **Create Cognito Groups** (if not already created):
   ```bash
   USER_POOL_ID="your-user-pool-id"
   
   # Create RBAC groups
   aws cognito-idp create-group --group-name DRSOrchestrationAdmin --user-pool-id $USER_POOL_ID --description "Full administrative access"
   aws cognito-idp create-group --group-name DRSRecoveryManager --user-pool-id $USER_POOL_ID --description "Recovery operations and configuration"
   aws cognito-idp create-group --group-name DRSPlanManager --user-pool-id $USER_POOL_ID --description "Plan management focus"
   aws cognito-idp create-group --group-name DRSOperator --user-pool-id $USER_POOL_ID --description "Execution operations only"
   aws cognito-idp create-group --group-name DRSReadOnly --user-pool-id $USER_POOL_ID --description "View-only access"
   ```

2. **Assign Users to Groups**:
   ```bash
   # Add user to admin group
   aws cognito-idp admin-add-user-to-group \
     --user-pool-id $USER_POOL_ID \
     --username admin@yourcompany.com \
     --group-name DRSOrchestrationAdmin
   
   # Add user to operator group
   aws cognito-idp admin-add-user-to-group \
     --user-pool-id $USER_POOL_ID \
     --username operator@yourcompany.com \
     --group-name DRSOperator
   ```

3. **View User's Groups**:
   ```bash
   aws cognito-idp admin-list-groups-for-user \
     --user-pool-id $USER_POOL_ID \
     --username admin@yourcompany.com
   ```

#### UI Permission Enforcement

The frontend dynamically shows/hides functionality based on user permissions:

- **Settings Modal**: Export/Import tabs only visible to users with `EXPORT_CONFIGURATION` and `IMPORT_CONFIGURATION` permissions
- **Action Buttons**: Create, Edit, Delete buttons only appear for users with appropriate permissions
- **Navigation**: Menu items filtered based on user capabilities
- **Error Messages**: Clear indication when actions are restricted due to insufficient permissions

#### API-First Security Enforcement

- **Unified Security Model**: All access methods enforce identical role-based permissions
- **No Bypass Possible**: UI restrictions reflect actual API-level RBAC enforcement
- **Cognito Integration**: Roles managed through AWS Cognito Groups with JWT token validation
- **Granular Protection**: 40+ API endpoints mapped to specific permissions
- **Real-Time Validation**: Every API call validates user permissions before execution

#### Password Reset for New Users

- **Forced Password Change**: New users must change temporary passwords on first login
- **Secure Workflow**: Cognito-managed password reset with email verification
- **Admin User Creation**: Administrators can create users with temporary passwords
- **Self-Service Reset**: Users can initiate password reset through standard Cognito flows

### Traditional Security Features

- **Encryption at Rest**: All data encrypted (DynamoDB, S3)
- **Encryption in Transit**: HTTPS enforced via CloudFront
- **Authentication**: Cognito JWT token-based authentication with 45-minute sessions
- **Authorization**: IAM least-privilege policies with comprehensive DRS permissions
- **Audit Trails**: Complete user action logging with role context
- **Optional**: WAF protection and CloudTrail audit logging

### Security Vulnerability Fixes (v1.1.1)

The platform has been hardened against multiple security vulnerabilities with comprehensive fixes deployed to production:

#### Resolved Vulnerabilities

- **SQL Injection (CWE-89)**: Fixed DynamoDB operations with proper `ConditionExpression` usage to prevent injection attacks through non-existent keys
- **Cross-Site Scripting (CWE-20,79,80)**: Sanitized user inputs in React components to prevent XSS attacks and malicious script execution
- **OS Command Injection (CWE-78,77,88)**: Added regex sanitization across multiple files to prevent command injection vulnerabilities
- **Log Injection (CWE-117)**: Removed newline characters and sanitized user-controlled data before logging to prevent log manipulation

#### Security Enhancements

- **Input Validation**: Enhanced UUID format checking and type conversion for all user-controlled data
- **Database Security**: Added condition expressions to DynamoDB operations to prevent injection attacks
- **Frontend Security**: Comprehensive input sanitization patterns implemented across all React components
- **Error Handling**: Improved structured error responses and validation across all Lambda functions
- **Performance Security**: Fixed memory leaks and implemented proper singleton patterns to prevent resource exhaustion

#### Code Quality Improvements

- **Maintainability**: Addressed readability issues and improved code structure for better security review
- **Error Handling**: Enhanced error handling patterns to prevent information disclosure
- **Input Sanitization**: Consistent sanitization patterns using regex replacement and validation
- **Type Safety**: Improved TypeScript usage and fixed syntax errors for better compile-time security

All security fixes have been deployed to production and are actively protecting the platform against these vulnerability classes.

### EventBridge Security Validation (v1.2.1)

Enhanced security validation for automated tag synchronization ensures EventBridge requests are legitimate while maintaining operational security:

#### Multi-Layer Security Validation

- **Source IP Validation**: Verify EventBridge requests originate from legitimate AWS sources (`sourceIp: 'eventbridge'`)
- **Request Structure Validation**: Prevent direct Lambda invocation attempts by validating API Gateway context
- **Authentication Header Validation**: Reject requests with unexpected Authorization headers to prevent bypass abuse
- **EventBridge Rule Name Validation**: Verify rule names match expected patterns (`aws-drs-orchestrator-tag-sync-schedule-*`)
- **Invocation Source Verification**: Validate `invocationSource` equals 'EVENTBRIDGE' for automated requests

#### Security Audit Logging

- **Comprehensive Request Logging**: Log requestId, stage, accountId, and rule name for all EventBridge requests
- **Security Event Tracking**: Detailed audit trail for monitoring and compliance
- **Attack Prevention Logging**: Log and reject invalid EventBridge attempts for security monitoring

#### Zero Trust Authentication Bypass

- **Scoped Access**: Only `/drs/tag-sync` endpoint allows EventBridge authentication bypass
- **Multiple Validation Layers**: Prevent authentication bypass abuse through comprehensive validation
- **Complete Audit Trail**: All EventBridge requests logged with security-relevant information
- **Attack Surface Reduction**: Minimal bypass scope with maximum security validation

This security model enables automated tag synchronization while maintaining enterprise-grade security standards and complete audit compliance.

## Documentation

### Essential Guides

| Document | Description |
|----------|-------------|
| [API Reference Guide](docs/guides/API_REFERENCE_GUIDE.md) | Complete REST API documentation with examples |
| [Development Workflow Guide](docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md) | Development, testing, and deployment procedures |
| [Troubleshooting Guide](docs/guides/TROUBLESHOOTING_GUIDE.md) | Common issues and debugging procedures |
| [Deployment Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) | Step-by-step deployment instructions |
| [Multi-Account Setup Guide](docs/guides/MULTI_ACCOUNT_SETUP_GUIDE.md) | Complete multi-account hub and spoke setup |
| [Orchestration Integration](docs/guides/ORCHESTRATION_INTEGRATION_GUIDE.md) | CLI, SSM, Step Functions, API integration |
| [RBAC Security Testing Status](docs/security/RBAC_SECURITY_TESTING_STATUS.md) | Role-based access control security testing documentation |

### Requirements & Architecture

| Document | Description |
|----------|-------------|
| [Product Requirements](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) | Complete PRD with features and specifications |
| [Architecture Design](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md) | System architecture and design decisions |
| [Architecture Diagrams](docs/architecture/ARCHITECTURE_DIAGRAMS.md) | Visual reference - Complete mermaid diagrams |

### Implementation & Testing

| Document | Description |
|----------|-------------|
| [Testing Guide](docs/guides/TESTING_AND_QUALITY_ASSURANCE.md) | Testing procedures and quality assurance |
| [Local Development](docs/guides/LOCAL_DEVELOPMENT.md) | Development environment setup |
| [Manual Test Instructions](docs/guides/MANUAL_TEST_INSTRUCTIONS.md) | Manual testing procedures |

For complete documentation index, see [Documentation Index](.kiro/steering/docs-index.md).

## Future Enhancements

### Active Development Roadmap

| Priority | Feature Category | LOE | Description | Status |
|----------|------------------|-----|-------------|--------|
| 6 | **Scheduled Drills** | 3-5d | Automated scheduled drill executions with EventBridge rules | Planned |
| 7 | **SNS Notification Integration** | 1-2w | Real-time notifications for execution status changes via Email, SMS, Slack | Planned |
| 9 | **Step Functions Visualization** | 2-3w | Real-time visualization of Step Functions state machine execution | Planned |
| 10-18 | **Cross-Account Features** | 8-12w | Cross-account orchestration, monitoring, and extended source servers | Planned |
| 12 | **DRS Source Server Management** | 8-10w | Complete DRS server configuration including tags, disk settings, replication | Planned |

For detailed implementation plans, see:
- [Cross-Account Features](docs/implementation/CROSS_ACCOUNT_FEATURES.md)
- [DRS Source Server Management](docs/implementation/DRS_SOURCE_SERVER_MANAGEMENT.md)
- [Automation & Orchestration](docs/implementation/AUTOMATION_AND_ORCHESTRATION.md)
- [Notifications & Monitoring](docs/implementation/NOTIFICATIONS_AND_MONITORING.md)
- [Recovery Enhancements](docs/implementation/RECOVERY_ENHANCEMENTS.md)
- [Infrastructure Improvements](docs/implementation/INFRASTRUCTURE_IMPROVEMENTS.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Repository Snapshots & Rollback

The repository uses Git tags to mark significant milestones:

| Tag | Description | Date | Commit |
|-----|-------------|------|--------|
| `RBAC-Prototype-with-Password-Reset-capability-v1.0` | **RBAC Prototype v1.0** - Comprehensive role-based access control with 6 granular roles, API-first enforcement, and password reset capability for new users | December 31, 2025 | `TBD` |
| `MVP-DRILL-PROTOTYPE` | **MVP Drill Prototype Complete** - Complete disaster recovery orchestration platform with multi-account support, tag-based selection, and comprehensive drill capabilities | December 30, 2025 | `a34c5b7` |
| `v2.0.0-mvp-drill-prototype` | **MVP Drill Only Prototype v2.0** - Core drill functionality with comprehensive documentation | December 30, 2025 | - |
| `mvp-demo-ready` | MVP Demo Ready - Complete working state with all core features | December 9, 2025 | - |

### Rollback to a Tag

```bash
# View the repository at the tagged state
git checkout mvp-demo-ready

# Create a new branch from tag for development
git checkout -b my-feature-branch mvp-demo-ready

# Return to main branch
git checkout main
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete project history since November 8, 2025.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built for enterprise disaster recovery on AWS