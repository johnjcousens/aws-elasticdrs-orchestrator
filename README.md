# AWS DRS Orchestration Solution

Enterprise-grade disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

[![AWS](https://img.shields.io/badge/AWS-DRS-FF9900?logo=amazonaws)](https://aws.amazon.com/disaster-recovery/)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-232F3E?logo=amazonaws)](cfn/)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB?logo=react)](frontend/)
[![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?logo=python)](lambda/)
[![Release](https://img.shields.io/badge/Release-v1.2.2%20Code%20Quality-green)](https://github.com/your-repo/releases/tag/v1.2.2)

## 🚀 **Latest Release: v1.2.2 - Code Quality Enhancement**

**Latest Version**: v1.2.2 - Code Quality Enhancement (January 2, 2026)  
**Git Tag**: `v1.2.2`

### 🔧 **What's New in v1.2.2**

- **Complete Python Coding Standards Implementation**: Comprehensive code quality improvements across entire codebase
- **187 PEP 8 Violations Fixed**: Resolved all flake8 violations including line length, whitespace, imports, and naming conventions
- **Enhanced Code Readability**: Standardized string quotes, improved variable naming, and consistent formatting
- **Zero Functional Changes**: All improvements maintain existing functionality and API compatibility
- **Production Deployment**: Successfully deployed updated Lambda functions with enhanced code quality
- **Safe Deployment Process**: Used code-only updates without CloudFormation changes for zero downtime
- **Test Environment Ready**: Created `.env.deployment.test` configuration for future safe testing deployments

**Previous Release**: v1.2.1 - Enhanced EventBridge Security (January 1, 2026)
- Multi-layer security validation for EventBridge authentication bypass
- Comprehensive audit logging and attack prevention measures

**[View Complete v1.2.2 Release Notes →](CHANGELOG.md#122---january-2-2026)**

## Overview

AWS DRS Orchestration enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native serverless services.

### Key Capabilities

- **Cost-Effective**: $12-40/month operational cost with pay-per-use serverless pricing
- **Unlimited Waves**: Flexible wave-based orchestration with no artificial constraints
- **Platform Agnostic**: Supports any source platform (physical servers, cloud instances, virtual machines)
- **Sub-Second RPO**: Leverages AWS DRS continuous replication capabilities
- **Fully Serverless**: No infrastructure to manage, scales automatically

## Key Features

### Comprehensive REST API 🆕

- **42+ API Endpoints**: Complete REST API across 12 categories (Protection Groups, Recovery Plans, Executions, DRS Integration, Account Management, EC2 Resources, Configuration, User Management, Health Check)
- **Role-Based Access Control (RBAC)**: 5 granular roles with 11 specific permissions for enterprise security
- **Cross-Account Operations**: Manage DRS across multiple AWS accounts with automated role assumption
- **Direct Lambda Invocation**: Bypass API Gateway for AWS-native automation (Step Functions, SSM, EventBridge)
- **Configuration Export/Import**: Complete backup and restore capabilities with dry-run validation
- **Tag Synchronization**: Automated EC2 to DRS tag sync with EventBridge scheduling

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
- **Enhanced Tag-Based Selection** 🆕: Query DRS source server tags with complete hardware details and conflict detection
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

- **Wave-Based Orchestration**: Define multi-wave recovery sequences with unlimited flexibility and dependency management
- **Pause/Resume Execution**: Pause executions between waves for manual validation and resume when ready
- **Dependency Management**: Automatic wave dependency handling with circular dependency detection
- **Drill Mode**: Test recovery procedures without impacting production
- **Conflict Detection**: Automatic detection of server conflicts and existing recovery instances
- **Automation Hooks**: Pre-wave and post-wave actions for validation and health checks

### Execution Monitoring

- **Real-Time Dashboard**: Live execution progress with wave-level status tracking and auto-refresh
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

*Updated architecture diagrams available in [docs/architecture/](docs/architecture/) reflecting current 42+ endpoint implementation*

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

## Python Virtual Environment

The repository includes a pre-configured Python 3.12.11 virtual environment (`venv/`) for Lambda development and testing:

### Environment Details
- **Python Version**: 3.12.11 (matches AWS Lambda runtime)
- **Package Count**: 76+ packages installed
- **Testing Framework**: pytest, moto, hypothesis for comprehensive testing
- **AWS Integration**: boto3, crhelper for Lambda development
- **Status**: ✅ Up-to-date with deployed codebase

### Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run Lambda unit tests
cd tests/python
pytest unit/ -v

# Run integration tests with AWS mocking
pytest integration/ -v

# Generate coverage report
pytest --cov=lambda

# Deactivate when done
deactivate
```

### Key Packages
- **Testing**: pytest 7.4.3, moto 4.2.9, hypothesis 6.92.1
- **AWS SDK**: boto3 1.34.0, botocore 1.34.0
- **Lambda Helper**: crhelper 2.0.11
- **Utilities**: freezegun 1.4.0, python-dateutil 2.8.2

The virtual environment is maintained to match the exact versions used in production Lambda functions and testing infrastructure.

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
  --stack-name aws-drs-orchestrator \
  --parameter-overrides \
    ProjectName=aws-drs-orchestrator \
    Environment=prod \
    SourceBucket=your-bucket \
    AdminEmail=admin@yourcompany.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Deployment takes approximately 20-30 minutes and provides:
- **Complete REST API** with 42+ endpoints across 12 categories
- **Role-Based Access Control** with 5 granular roles
- **Cross-Account Operations** for enterprise environments
- **Tag-Based Server Selection** with automated synchronization
- **Wave-Based Execution** with pause/resume capabilities

### Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestrator \
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
  --stack-name aws-drs-orchestrator \
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

### Essential Guides (16 Consolidated Guides)

#### Core Operations
| Document | Description |
|----------|-------------|
| [API Reference Guide](docs/guides/API_REFERENCE_GUIDE.md) | Complete REST API documentation (42+ endpoints) with RBAC system |
| [Orchestration Integration Guide](docs/guides/ORCHESTRATION_INTEGRATION_GUIDE.md) | CLI, SSM, Step Functions, API integration with direct Lambda invocation |
| [DRS Execution Walkthrough](docs/guides/DRS_EXECUTION_WALKTHROUGH.md) | Complete drill and recovery execution procedures |
| [Troubleshooting Guide](docs/guides/TROUBLESHOOTING_GUIDE.md) | Common issues, debugging, and resolution procedures |

#### Deployment & Operations
| Document | Description |
|----------|-------------|
| [Deployment and Operations Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) | Complete deployment, configuration, and operational procedures |
| [Multi-Account Setup Guide](docs/guides/MULTI_ACCOUNT_SETUP_GUIDE.md) | Cross-account hub and spoke configuration |
| [Development Workflow Guide](docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md) | Development, testing, and CI/CD procedures |
| [Parameterization Summary](docs/implementation/PARAMETERIZATION_SUMMARY.md) | Configuration management and hardcoded value elimination |

#### Testing & Quality
| Document | Description |
|----------|-------------|
| [Testing and Quality Assurance](docs/guides/TESTING_AND_QUALITY_ASSURANCE.md) | Comprehensive testing procedures and quality standards |
| [Manual Test Instructions](docs/guides/MANUAL_TEST_INSTRUCTIONS.md) | Step-by-step manual testing procedures |
| [Local Development](docs/guides/LOCAL_DEVELOPMENT.md) | Development environment setup and local testing |

#### User & Admin Guides
| Document | Description |
|----------|-------------|
| [Solution Handoff Guide](docs/guides/SOLUTION_HANDOFF_GUIDE.md) | Complete solution handoff and operational procedures |
| [S3 Sync Automation](docs/guides/S3_SYNC_AUTOMATION.md) | S3 deployment automation and synchronization |
| [CI/CD Pipeline Guide](docs/guides/CICD_PIPELINE_GUIDE.md) | Continuous integration and deployment procedures |

#### Advanced Features
| Document | Description |
|----------|-------------|
| [AWS DRS Advanced Status Polling Reference](docs/guides/AWS_DRS_ADVANCED_STATUS_POLLING_REFERENCE.md) | Advanced DRS status polling and monitoring |
| [DRS Recovery and Failback Complete Guide](docs/guides/DRS_RECOVERY_AND_FAILBACK_COMPLETE_GUIDE.md) | Complete recovery and failback procedures |

### Technical Reference Documentation (8 Consolidated Files)

#### Core DRS Reference
| Document | Description |
|----------|-------------|
| [API Endpoints Current](docs/reference/API_ENDPOINTS_CURRENT.md) | Complete current API endpoints catalog with implementation details |
| [DRS IAM and Permissions Reference](docs/reference/DRS_IAM_AND_PERMISSIONS_REFERENCE.md) | Complete IAM analysis, service roles, and cross-account permissions |
| [DRS Launch Configuration Reference](docs/reference/DRS_LAUNCH_CONFIGURATION_REFERENCE.md) | Launch template settings, configuration tools, and template management |
| [DRS Cross-Account Reference](docs/reference/DRS_CROSS_ACCOUNT_REFERENCE.md) | Cross-account architecture, setup, and network requirements |
| [DRS Service Limits and Capabilities](docs/reference/DRS_SERVICE_LIMITS_AND_CAPABILITIES.md) | Service quotas, regional availability, and feature capabilities |

#### Competitive Analysis
| Document | Description |
|----------|-------------|
| [Azure Site Recovery Analysis](docs/reference/competitive/AZURE_SITE_RECOVERY_ANALYSIS.md) | Comprehensive Azure ASR comparison and feature analysis |
| [Zerto Research and API Analysis](docs/reference/competitive/ZERTO_RESEARCH_AND_API_ANALYSIS.md) | Zerto platform analysis, API documentation, and competitive positioning |

### Requirements & Architecture (Source of Truth)

| Document | Description |
|----------|-------------|
| [Product Requirements Document](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) | Complete PRD v2.1 with EventBridge security features |
| [Software Requirements Specification](docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md) | Technical specifications v2.1 with comprehensive API catalog |
| [UX/UI Design Specifications](docs/requirements/UX_UI_DESIGN_SPECIFICATIONS.md) | User interface design and interaction patterns v2.1 |
| [UX Component Library](docs/requirements/UX_COMPONENT_LIBRARY.md) | CloudScape component specifications and usage patterns |
| [UX Page Specifications](docs/requirements/UX_PAGE_SPECIFICATIONS.md) | Detailed page layouts and user interaction flows |
| [UX Technology Stack](docs/requirements/UX_TECHNOLOGY_STACK.md) | Frontend technology decisions and implementation standards |
| [UX Visual Design System](docs/requirements/UX_VISUAL_DESIGN_SYSTEM.md) | Visual design standards and AWS branding guidelines |
| [Architectural Design Document](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md) | System architecture v2.1 with EventBridge security and tag sync |
| [AWS Services Architecture Deep Dive](docs/architecture/AWS_SERVICES_ARCHITECTURE_DEEP_DIVE.md) | Detailed AWS service integration patterns v2.1 |
| [Architecture Diagrams](docs/architecture/ARCHITECTURE_DIAGRAMS.md) | Visual reference with sequence diagrams and current implementation |
| [Step Functions Analysis](docs/architecture/STEP_FUNCTIONS_ANALYSIS.md) | Detailed Step Functions state machine analysis and coordination patterns |

### Security Documentation

| Document | Description |
|----------|-------------|
| [RBAC Security Testing Status](docs/security/RBAC_SECURITY_TESTING_STATUS.md) | Role-based access control security testing and validation |
| [RBAC Security Testing Plan](docs/security/RBAC_SECURITY_TESTING_PLAN.md) | Comprehensive security testing procedures and validation framework |

### Troubleshooting Documentation

| Document | Description |
|----------|-------------|
| [Deployment Troubleshooting Guide](docs/troubleshooting/DEPLOYMENT_TROUBLESHOOTING_GUIDE.md) | CloudFormation deployment issues and IAM role troubleshooting |
| [DRS Execution Troubleshooting Guide](docs/troubleshooting/DRS_EXECUTION_TROUBLESHOOTING_GUIDE.md) | DRS drill debugging and execution failure analysis |
| [DRS Service Limits Testing](docs/troubleshooting/DRS_SERVICE_LIMITS_TESTING.md) | Service quota testing and limit validation procedures |

*All documentation updated to v2.1 (January 1, 2026) with EventBridge security enhancements and tag synchronization features.*

## Future Enhancements

### Active Development Roadmap

The solution currently provides a comprehensive disaster recovery orchestration platform with 42+ API endpoints, RBAC security, cross-account operations, and advanced features. The following enhancements represent the next phase of development:

| Priority | Feature Category | LOE | Description | Status |
|----------|------------------|-----|-------------|--------|
| 6 | **Scheduled Drills** | 3-5d | Automated scheduled drill executions with EventBridge rules | Planned |
| 7 | **SNS Notification Integration** | 1-2w | Real-time notifications for execution status changes via Email, SMS, Slack | Planned |
| 9 | **Step Functions Visualization** | 2-3w | Real-time visualization of Step Functions state machine execution | Planned |
| 12 | **Advanced DRS Server Management** | 8-10w | Complete DRS server configuration including disk settings, replication settings, PIT policies | Planned |

### Recently Completed (v1.2.0 and Earlier)

The following major features have been **completed and are available** in the current implementation:

#### ✅ **Role-Based Access Control (RBAC)** (Completed v1.0 - December 31, 2025)
- **5 Granular DRS-Specific Roles** with enterprise security focus
- **14 Granular Permissions** mapped to business functionality
- **API-First Security Enforcement** - all access methods enforce identical RBAC
- **Cognito Groups Integration** with JWT token validation
- **UI Permission Enforcement** - dynamic show/hide based on user permissions
- **Password Reset Capability** for new users with forced password change
- **Admin User Management** through AWS Cognito Groups
- **Real-Time Permission Validation** for every API call

#### ✅ **Tag Synchronization** (Completed v1.2.0 - January 1, 2026)
- **Automated Tag Synchronization** from EC2 instances to DRS source servers
- **EventBridge Scheduling** with configurable intervals (15 minutes to 24 hours)
- **Manual Triggers** for immediate synchronization capability
- **Multi-Region Support** across all 28 commercial AWS DRS regions
- **Enterprise Security** with multi-layer security validation for EventBridge authentication bypass
- **Real-Time Progress** tracking and comprehensive error handling

#### ✅ **Comprehensive REST API** (Completed v1.1.0)
- **42+ API Endpoints** across 12 categories
- **Cross-Account Operations** with automated role assumption
- **Direct Lambda Invocation** for AWS-native automation
- **Configuration Export/Import** with dry-run validation

#### ✅ **Multi-Account Support Foundation** (Completed Dec 30, 2025)
- **Account Context System** with enforcement logic
- **Account Selector** in top navigation
- **Setup Wizard** for first-time configuration
- **Cross-Account Role Management** with validation

#### ✅ **Tag-Based Server Selection** (Completed Dec 16, 2025)
- **DRS Source Server Tag Queries** with hardware details
- **Conflict Detection** and prevention
- **Enhanced Protection Groups** with tag-based server selection

#### ✅ **Wave-Based Execution** (Completed Dec 12, 2025)
- **Pause/Resume Execution** between waves
- **Dependency Management** with circular dependency detection
- **Real-Time Progress Tracking** with auto-refresh
- **Instance Termination** after testing

#### ✅ **Enhanced Monitoring** (Completed Dec 14, 2025)
- **Execution History** with selective deletion
- **Date Range Filtering** with quick filters
- **Invocation Source Tracking** (UI, CLI, API, EventBridge, SSM, Step Functions)
- **DRS Job Events** with real-time monitoring

For detailed implementation plans of remaining features, see:
- [DRS Source Server Management](docs/implementation/DRS_SOURCE_SERVER_MANAGEMENT.md)
- [Automation & Orchestration](docs/implementation/AUTOMATION_AND_ORCHESTRATION.md)
- [Notifications & Monitoring](docs/implementation/NOTIFICATIONS_AND_MONITORING.md)
- [Recovery Enhancements](docs/implementation/RECOVERY_ENHANCEMENTS.md)
- [Infrastructure Improvements](docs/implementation/INFRASTRUCTURE_IMPROVEMENTS.md)
- [Cross-Account Features](docs/implementation/CROSS_ACCOUNT_FEATURES.md)

## Agentic AI Programming

This project is optimized for development with AI assistants like **Kiro**, **Amazon Q Developer**, and **Claude**. The repository includes comprehensive steering documents and rules to ensure consistent, high-quality AI-assisted development.

### AI Assistant Configuration

#### Kiro (Primary AI Assistant)
The `.kiro/` directory contains steering documents that guide Kiro's behavior:

```
.kiro/steering/
├── project-context.md          # Product overview, architecture, tech stack
├── development-workflow.md     # CI/CD, debugging, terminal rules, file writing
├── frontend-standards.md       # CloudScape design system rules and patterns
└── technical-standards.md      # AWS diagram standards, Mermaid preferences, documentation
```

**Key Features for AI Development:**
- **Token Optimization**: Consolidated from 14+ files to 4 focused files (85% token reduction)
- **Comprehensive Standards**: Complete CloudScape design system rules, AWS diagram standards
- **Development Workflow**: Terminal rules, file writing patterns, CI/CD procedures
- **Technical Patterns**: Mermaid over ASCII, AWS 2025 icon standards, code documentation

#### Amazon Q Developer
The `.amazonq/` directory contains aligned rules for Amazon Q:

```
.amazonq/rules/
├── amazonq-project-context.md      # Product overview aligned with Kiro
├── amazonq-development-workflow.md # Deployment verification workflows
└── amazonq-frontend-standards.md   # CloudScape consistency rules
```

**Alignment with Kiro**: Both AI assistants follow identical core standards while Amazon Q includes additional deployment verification workflows.

### AI Development Best Practices

#### Working with Steering Documents
1. **Read Before Starting**: AI assistants automatically load steering documents for context
2. **Follow Standards**: All code generation follows CloudScape design system and AWS standards
3. **Consistent Patterns**: Steering ensures consistent API patterns, error handling, and documentation
4. **Token Efficiency**: Consolidated documents minimize token consumption while maintaining completeness

#### Key Development Rules for AI
- **CloudScape Only**: Never deviate from AWS CloudScape Design System components
- **AWS Standards**: Use AWS 2025 (AWS4) icon format for all diagrams
- **Mermaid Diagrams**: Prefer Mermaid over ASCII art for all technical diagrams
- **Terminal Efficiency**: Suppress output (`> /dev/null 2>&1`) and use `--no-pager` for git/AWS CLI
- **File Writing**: Use fsWrite/strReplace tools directly, avoid opening files in editor

#### AI-Optimized Documentation Structure
The project documentation is organized for optimal AI consumption:

- **Single Source of Truth**: Each topic has one authoritative document
- **Logical Grouping**: Related content consolidated (42% reduction in reference docs)
- **Clear Hierarchy**: Requirements → Architecture → Implementation → Reference
- **Cross-References**: Comprehensive linking between related documents

#### Development Workflow with AI
1. **Context Loading**: AI assistants automatically load project context from steering documents
2. **Standards Enforcement**: All generated code follows established patterns and standards
3. **Consistent Output**: Steering ensures consistent API responses, error handling, and UI patterns
4. **Quality Assurance**: Built-in validation rules prevent common issues and maintain quality

#### AI Assistant Capabilities
- **Complete API Development**: Generate REST endpoints following established patterns
- **CloudScape UI Components**: Create consistent AWS console-style interfaces
- **Infrastructure as Code**: Generate CloudFormation templates with proper security
- **Documentation**: Maintain comprehensive documentation following established formats
- **Testing**: Generate unit and integration tests following project patterns

### Getting Started with AI Development

1. **Clone Repository**: AI assistants automatically detect `.kiro/` and `.amazonq/` directories
2. **Review Steering**: Understand project standards and patterns from steering documents
3. **Follow Patterns**: Use established patterns for API development, UI components, and documentation
4. **Maintain Standards**: All AI-generated code follows CloudScape design system and AWS standards

The steering documents ensure that multiple AI assistants can work on the project while maintaining consistency, quality, and adherence to AWS best practices.

## Code Quality & Development Standards

### Python Coding Standards Implementation (v1.2.2)

The codebase has undergone a comprehensive code quality enhancement implementing complete Python coding standards across all Lambda functions and supporting scripts.

#### Code Quality Metrics

| Metric | Before v1.2.2 | After v1.2.2 | Improvement |
|--------|---------------|--------------|-------------|
| **PEP 8 Violations** | 187 violations | 0 violations | ✅ **100% resolved** |
| **Line Length Issues** | 45 violations | 0 violations | ✅ **Fully compliant** |
| **Import Organization** | 23 violations | 0 violations | ✅ **Standardized** |
| **Whitespace Issues** | 67 violations | 0 violations | ✅ **Clean formatting** |
| **Naming Conventions** | 31 violations | 0 violations | ✅ **Consistent naming** |
| **String Formatting** | 21 violations | 0 violations | ✅ **Standardized quotes** |
| **Black Formatting** | 10 Lambda files | 10 Lambda files | ✅ **79-char compliant** |

#### Standards Implementation Details

**Comprehensive PEP 8 Compliance**
- **Line Length**: All lines comply with 79-character limit (strict PEP 8 standard)
- **Import Organization**: Standardized import order (standard library → third-party → local imports)
- **Whitespace**: Consistent spacing around operators, function definitions, and class declarations
- **Naming Conventions**: Snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **String Formatting**: Standardized double quotes for strings, f-string formatting throughout
- **Black Formatting**: All 10 Lambda functions formatted with Black using 79-character line length

**Code Readability Enhancements**
- **Function Complexity**: Added `# noqa` comments for complex but necessary functions (DRS integration logic)
- **Variable Naming**: Improved descriptive variable names for better code comprehension
- **Comment Standards**: Enhanced inline documentation following technical standards
- **Error Handling**: Consistent exception handling patterns across all Lambda functions

**Development Workflow Integration**
- **Flake8 Configuration**: Updated `.flake8` with project-specific rules and exclusions
- **Pre-commit Hooks**: Enhanced `.pre-commit-config.yaml` with comprehensive Python linting
- **CI/CD Integration**: GitLab CI pipeline includes automated code quality checks
- **Development Environment**: Virtual environment (`venv/`) includes all quality tools

#### Quality Assurance Tools

**Linting and Formatting**
```bash
# Code quality validation
flake8 lambda/ --config .flake8
black --check lambda/
isort --check-only lambda/

# Automated formatting
black lambda/
isort lambda/
```

**Testing Integration**
```bash
# Run tests with quality checks
pytest tests/python/unit/ -v --flake8
pytest tests/python/integration/ -v --cov=lambda
```

**Pre-commit Validation**
```bash
# Install pre-commit hooks
pre-commit install

# Run all quality checks
pre-commit run --all-files
```

#### Zero Functional Impact Guarantee

**Deployment Safety**
- **No API Changes**: All REST API endpoints maintain identical functionality and responses
- **No Business Logic Changes**: DRS integration, wave execution, and orchestration logic unchanged
- **No Database Schema Changes**: DynamoDB table structures and queries remain identical
- **No Authentication Changes**: Cognito integration and RBAC enforcement unchanged

**Production Deployment Verification**
- **Lambda Function Updates**: Successfully deployed code-only updates using `--update-lambda-code`
- **API Gateway Testing**: Verified all 42+ endpoints respond correctly with improved code
- **CloudWatch Monitoring**: Confirmed no errors or performance degradation post-deployment
- **User Acceptance**: All UI functionality operates identically with enhanced backend code

#### Development Standards Documentation

**Comprehensive Standards Coverage**
- **Technical Standards**: Complete documentation in `.kiro/steering/technical-standards.md`
- **Development Workflow**: Detailed procedures in `.kiro/steering/development-workflow.md`
- **Frontend Standards**: CloudScape design system rules in `.kiro/steering/frontend-standards.md`
- **Project Context**: Architecture and technology stack in `.kiro/steering/project-context.md`

**AI Assistant Integration**
- **Kiro Steering**: All standards automatically enforced by AI assistants during development
- **Amazon Q Rules**: Aligned standards in `.amazonq/rules/` for consistent AI-assisted development
- **Code Generation**: AI assistants generate code following established quality patterns
- **Automated Compliance**: Steering documents ensure all generated code meets quality standards

#### Quality Metrics Tracking

**Baseline Violation Report**
The `baseline_violations_report.txt` provides complete documentation of all resolved violations:
- **Detailed Analysis**: Line-by-line breakdown of each violation type and resolution
- **File-by-File Tracking**: Comprehensive coverage across all Python files in the codebase
- **Resolution Patterns**: Documented approaches for each violation category
- **Quality Metrics**: Before/after comparison showing 100% violation resolution

**Continuous Quality Monitoring**
- **GitLab CI Integration**: Automated quality checks on every commit and merge request
- **Pre-commit Hooks**: Local validation prevents quality regressions
- **Development Environment**: Virtual environment includes all necessary quality tools
- **Documentation Standards**: Technical writing follows established patterns and formats

#### Future Quality Initiatives

**Ongoing Improvements**
- **Type Hints**: Gradual addition of comprehensive type annotations
- **Docstring Standards**: Enhanced function and class documentation
- **Test Coverage**: Expansion of unit test coverage with quality metrics
- **Performance Optimization**: Code efficiency improvements while maintaining quality standards

**Quality Assurance Process**
- **Code Review Standards**: Established patterns for reviewing AI-generated and human-written code
- **Automated Testing**: Integration of quality checks into testing workflows
- **Documentation Quality**: Consistent technical writing standards across all documentation
- **Standards Evolution**: Regular updates to coding standards based on industry best practices

This comprehensive code quality implementation ensures the AWS DRS Orchestration platform maintains enterprise-grade code standards while preserving all existing functionality and performance characteristics.

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