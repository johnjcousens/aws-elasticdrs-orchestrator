# Product Requirements Document
# AWS DRS Orchestration Solution

**Version**: 3.0  
**Date**: January 7, 2026  
**Status**: Production Ready - Complete Implementation  
**Document Owner**: AWS DRS Orchestration Team

---

## Executive Summary

AWS DRS Orchestration is a production-ready, enterprise-grade serverless disaster recovery orchestration platform built on AWS Elastic Disaster Recovery (DRS). The solution enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, real-time monitoring, pause/resume capabilities, comprehensive DRS source server management, multi-account support, tag-based server selection, automated tag synchronization with EventBridge scheduling, enterprise RBAC security, and comprehensive DRS API coverage.

### Problem Statement

AWS DRS provides continuous replication but lacks native orchestration for multi-tier applications requiring coordinated recovery sequences. Organizations need wave-based execution, dependency management, pause/resume controls, automated monitoring capabilities, centralized DRS source server configuration management, multi-account orchestration, flexible server selection methods, role-based access control, and comprehensive DRS API integration.

### Solution Overview

AWS DRS Orchestration provides complete orchestration and management on top of AWS DRS:
- Protection Groups for logical server organization with tag-based or explicit server selection
- Recovery Plans with wave-based execution and multi-Protection Group support per wave
- Step Functions-driven automation with pause/resume capability and existing instance detection
- Complete DRS source server management (launch settings, EC2 templates, tags, disks, replication, post-launch)
- Multi-account hub-and-spoke architecture with centralized management
- React 19 + CloudScape Design System UI with real-time updates and 32+ components
- Complete REST API with 47+ DRS operations across 80+ API Gateway resources
- Tag synchronization between EC2 instances and DRS source servers with EventBridge scheduling
- DRS service limits validation and quota monitoring
- Enterprise RBAC with 5 granular roles and 14 business-focused permissions
- Password reset capability for Cognito users
- Comprehensive security hardening with input validation and sanitization

---

## Architecture

![AWS DRS Orchestration Architecture](../architecture/AWS-DRS-Orchestration-Architecture.png)

*[View/Edit Source Diagram](../architecture/AWS-DRS-Orchestration-Architecture.drawio)*

### AWS Services

**Core Services**:
- DynamoDB: 4 tables (protection-groups, recovery-plans, execution-history, target-accounts)
- Lambda: 7 functions (api-handler, orchestration-stepfunctions, frontend-builder, execution-finder, execution-poller, bucket-cleaner, notification-formatter)
- Step Functions: Workflow orchestration with waitForTaskToken pattern
- API Gateway: 6-nested-stack modular architecture with 80+ resources and 47+ DRS operations
- CloudFront: CDN for global frontend distribution
- AWS DRS: Core disaster recovery service integration

**Infrastructure as Code**:
- CloudFormation: 15+ templates total (1 master + 14+ nested stacks)
- S3: Deployment artifacts and static website hosting
- Multi-region support across all 30 DRS-supported regions

### Data Model

**Protection Groups**: `GroupId` (PK), `GroupName`, `Region`, `SourceServerIds[]`, `ServerSelectionTags{}`, `LaunchConfig{}`, `CreatedDate`, `LastModifiedDate`, `Version`
**Recovery Plans**: `PlanId` (PK), `PlanName`, `Waves[]`, `CreatedDate`, `LastModifiedDate`, `Version`
**Execution History**: `ExecutionId` (PK), `PlanId` (SK), `Status`, `Waves[]`, `StartTime`, `EndTime`, `InitiatedBy`, with StatusIndex GSI
**Target Accounts**: `AccountId` (PK), `AssumeRoleName`, `CrossAccountRoleArn`, `IsDefault`, with StatusIndex GSI

---

## Key Features

### 1. Lambda Functions (7 Total)

**Production Lambda Functions**:
- **api-handler**: Main REST API handler with 47+ DRS operations and RBAC middleware
- **orchestration-stepfunctions**: Step Functions orchestration engine with wave execution
- **frontend-builder**: CloudFormation custom resource for frontend deployment
- **execution-finder**: Queries StatusIndex GSI for executions in POLLING status
- **execution-poller**: Polls DRS job status and updates execution wave states
- **bucket-cleaner**: S3 bucket cleanup for CloudFormation stack deletion
- **notification-formatter**: Formats pipeline and security scan notifications

### 2. API Gateway Architecture (6-Nested-Stack Modular Design)

**CloudFormation Stack Architecture**:
- **api-gateway-core-stack**: REST API, authorizer, validator
- **api-gateway-resources-stack**: 80+ API path definitions
- **api-gateway-core-methods-stack**: Health, User, Protection Groups, Recovery Plans methods
- **api-gateway-operations-methods-stack**: All Execution endpoints
- **api-gateway-infrastructure-methods-stack**: DRS, EC2, Config, Target Accounts methods
- **api-gateway-deployment-stack**: Deployment orchestrator and stage

**DRS API Coverage (47+ Operations)**:
- Failover Operations: start-recovery, terminate-instances, disconnect-instance
- Failback Operations: reverse-replication, start-failback, stop-failback, configuration
- Replication Management: start, stop, pause, resume, retry, configuration, template
- Source Server Management: disconnect, archive, extended-servers, extensible-servers
- Source Network Management: recovery, replication, stack, template
- Launch Configuration: configuration, template, launch-actions
- Job Management: jobs, logs, status tracking
- Service Management: initialize, recovery-instances, recovery-snapshots

### 3. RBAC Security System

**Security Roles (5 Granular Roles)**:
1. **DRSOrchestrationAdmin**: Full administrative access including configuration export/import
2. **DRSRecoveryManager**: Recovery operations and configuration management
3. **DRSPlanManager**: Create and manage Protection Groups and Recovery Plans, view executions
4. **DRSOperator**: Execute drills only, view assigned Protection Groups and Recovery Plans
5. **DRSReadOnly**: View-only access to all data with no modification capabilities

**Permission-Aware UI Components**:
- **PermissionAware**: Conditional rendering wrapper for permission-based content
- **PasswordChangeForm**: UI component for secure password changes with Cognito integration
- **ProtectedRoute**: Route-level permission enforcement

**Security Implementation**:
- **rbac_middleware.py**: Centralized permission enforcement for all Lambda functions
- **security_utils.py**: Input validation, sanitization, and security headers
- JWT token-based permission validation with comprehensive audit trails

### 4. Frontend Application (7 Pages, 32+ Components)

**Pages**:
- **Dashboard**: Metrics cards, pie chart, active executions, DRS quotas
- **LoginPage**: Cognito authentication with password reset capability
- **GettingStartedPage**: 3-step onboarding guide
- **ProtectionGroupsPage**: CRUD table with tag/server selection modes
- **RecoveryPlansPage**: Wave-based plan management with execution controls
- **ExecutionsPage**: Active and historical execution monitoring
- **ExecutionDetailsPage**: Detailed execution view with wave progress

**Key Components**:
- **AccountSelector**: Multi-account context switching
- **ServerDiscoveryPanel**: Real-time DRS server discovery with conflict detection
- **WaveConfigEditor**: Multi-wave configuration with dependency management
- **DRSQuotaStatus**: Real-time service limits monitoring
- **TagSyncConfigPanel**: EventBridge tag synchronization configuration

### 5. Multi-Account Management

**Cross-Account Architecture**:
- Hub-and-spoke model with centralized orchestration
- STS-based role assumption for target accounts
- Account context propagation through all operations
- Scale beyond 300-server DRS limit per account

**Target Accounts Table**: Stores cross-account role configurations with health monitoring

### 6. Tag Synchronization with EventBridge

**Automated Tag Synchronization**:
- EventBridge-triggered synchronization with configurable intervals
- Multi-layer security validation for EventBridge authentication bypass
- Cross-region support for all 30 DRS-supported regions
- Batch processing with comprehensive error handling

**Security Model**:
- Source IP validation for EventBridge requests
- Request structure validation to prevent direct Lambda invocation
- Authentication header validation with comprehensive audit logging

---

## API Specifications

### Complete REST API (47+ DRS Operations)

**Protection Groups API**:
- `GET /protection-groups` - List with account filtering
- `POST /protection-groups` - Create with server selection validation
- `POST /protection-groups/resolve` - Preview tag-based server matching

**Recovery Plans API**:
- `GET /recovery-plans` - List with conflict detection
- `POST /recovery-plans` - Create with wave validation
- `GET /recovery-plans/{id}/check-existing-instances` - Performance-optimized instance check

**Executions API**:
- `POST /executions` - Start execution with comprehensive validation
- `POST /executions/{id}/resume` - Resume paused execution
- `POST /executions/{id}/terminate-instances` - Terminate recovery instances

**DRS Integration API**:
- `GET /drs/source-servers` - Server discovery with assignment status
- `GET /drs/quotas` - Service limits and usage monitoring
- `POST /drs/tag-sync` - EC2 to DRS tag synchronization

**Multi-Account API**:
- `GET /accounts/targets` - List registered target accounts
- `POST /accounts/targets` - Register cross-account role

**Configuration API**:
- `GET /config/export` - Export Protection Groups and Recovery Plans
- `POST /config/import` - Import configuration with validation

**User Management API**:
- `GET /user/permissions` - Get current user's RBAC permissions

---

## Technical Specifications

### Frontend Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.1.1 | UI framework with concurrent features |
| TypeScript | 5.9.3 | Type safety and compile-time optimization |
| CloudScape Design System | 3.0.1148 | AWS-native UI components |
| Vite | 7.1.7 | Build tool and development server |
| AWS Amplify | 6.15.8 | Cognito authentication with auto token refresh |

### Backend Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Lambda runtime with latest performance improvements |
| boto3 | (runtime) | AWS SDK with connection pooling |
| crhelper | 2.0.11 | CloudFormation custom resources |

### CloudFormation Architecture
- **Master Template**: Orchestrates 14+ nested stacks
- **Modular Design**: API Gateway split into 6 stacks for maintainability
- **Parameter Propagation**: Centralized configuration management
- **Output Aggregation**: Stack outputs available at master level

---

## Deployment

### GitHub Actions CI/CD Pipeline

**Pipeline Stages** (~22 minutes total):
1. **Validate** (~2 min) - CloudFormation validation, Python linting, TypeScript checking
2. **Security Scan** (~3 min) - 6 security tools with enterprise-grade scanning
3. **Build** (~3 min) - Lambda packaging, frontend build
4. **Test** (~2 min) - Unit and integration tests
5. **Deploy Infrastructure** (~10 min) - CloudFormation stack deployment
6. **Deploy Frontend** (~2 min) - S3 sync, CloudFront invalidation

**Security Tools**:
- **Bandit v1.9.2**: Python security analysis
- **Safety v2.3.4**: Dependency vulnerability scanning
- **Semgrep v1.146.0**: Advanced security pattern matching
- **CFN-Lint v0.83.8**: CloudFormation security linting
- **ESLint**: Frontend security rules
- **NPM Audit**: Frontend dependency scanning

### Deployment Command
```bash
aws cloudformation deploy \
  --template-url https://{bucket}.s3.amazonaws.com/cfn/master-template.yaml \
  --stack-name aws-elasticdrs-orchestrator \
  --parameter-overrides \
    ProjectName=aws-elasticdrs-orchestrator \
    Environment=prod \
    SourceBucket={bucket} \
    AdminEmail={email} \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region {region}
```

---

## Performance & Cost

### Performance Optimizations
- **Backend**: Batch DynamoDB operations, optimized query patterns, connection pooling
- **Frontend**: Memoization, optimized polling frequencies, activity-based timeout
- **API**: Reduced scan scope, smart conflict detection, efficient server resolution

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
| **Total** | **$12-40/month** |

---

## AWS DRS Regional Availability

The solution supports all **30 AWS regions** where Elastic Disaster Recovery (DRS) is available:

| Region Group | Count | Regions |
|--------------|-------|---------|
| **Americas** | 6 | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America (São Paulo) |
| **Europe** | 8 | Ireland, London, Frankfurt, Paris, Stockholm, Milan, Spain, Zurich |
| **Asia Pacific** | 10 | Tokyo, Seoul, Osaka, Singapore, Sydney, Mumbai, Hyderabad, Jakarta, Melbourne, Hong Kong |
| **Middle East & Africa** | 4 | Bahrain, UAE, Cape Town, Tel Aviv |
| **GovCloud** | 2 | US-East, US-West |

---

## Version History

### v1.4.2 (Current) - Performance Optimizations
- **Backend Performance**: Optimized existing instance checks (2-3 second improvement)
- **Frontend Performance**: Memoized components, reduced polling, scalable UI
- **Security**: Comprehensive security scanning with 6 tools
- **UX**: Activity-based timeout, automatic token refresh, password reset capability

### v1.4.1 - Critical Bug Fixes
- Fixed async worker validation bug preventing Step Functions orchestration
- Enhanced existing instances dialog UX for large server deployments

### v1.4.0 - API Gateway 6-Nested-Stack Architecture
- Complete API Gateway modular architecture with 80+ resources
- 47+ DRS API operations across comprehensive categories
- Multi-account management with hub-and-spoke architecture
- Tag synchronization with EventBridge scheduling and enterprise security validation

---

## References

- [Software Requirements Specification](./SOFTWARE_REQUIREMENTS_SPECIFICATION.md)
- [UX/UI Design Specifications](./UX_UI_DESIGN_SPECIFICATIONS.md)
- [Architectural Design Document](../architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md)
- [API Reference Guide](../guides/API_REFERENCE_GUIDE.md)
- [GitHub Actions CI/CD Guide](../guides/deployment/GITHUB_ACTIONS_CICD_GUIDE.md)