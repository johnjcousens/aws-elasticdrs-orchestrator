# AWS DRS Orchestration Solution

Enterprise-grade disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

[![AWS](https://img.shields.io/badge/AWS-DRS-FF9900?logo=amazonaws)](https://aws.amazon.com/disaster-recovery/)
[![Version](https://img.shields.io/badge/version-4.0.0-blue)](CHANGELOG.md)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-232F3E?logo=amazonaws)](cfn/)
[![React](https://img.shields.io/badge/Frontend-React%2019.1.1-61DAFB?logo=react)](frontend/)
[![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?logo=python)](lambda/)
[![GitHub](https://img.shields.io/badge/Repository-GitHub-181717?logo=github)](https://github.com/johnjcousens/aws-elasticdrs-orchestrator)

## Overview

AWS DRS Orchestration enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native serverless services.

**Latest Release**: [v4.0.0 - Repository Consolidation and GitLab Integration](CHANGELOG.md) (January 26, 2026)
- Complete GitLab-to-GitHub repository merge with 1,474 files
- Lambda handler decomposition: 3 specialized handlers replacing monolithic api-handler
- 150,000+ lines of comprehensive documentation (Confluence, HealthEdge, compliance)
- Enhanced testing infrastructure: 8,000+ lines of test coverage
- Unified deployment script with 5-stage CI/CD pipeline
- 51% cost reduction and 50% faster cold starts

**Recent Milestones**: See [CHANGELOG.md](CHANGELOG.md) for complete project history including repository consolidation, handler decomposition, intelligent conflict detection, execution details UI, and HealthEdge standards compliance.

### 🚧 Next Priority Fix

**Partial Execution Status Enhancement** - Improve status handling for cancelled executions with partial progress

**Problem**: When a recovery plan is cancelled after some waves complete successfully, the system shows "CANCELLED" without indicating partial progress. This creates confusion about what succeeded and prevents proper cleanup of recovery instances.

**Solution**: Implement `PARTIAL_SUCCESS` status for executions where some waves completed before cancellation/failure. Enable "Terminate Recovery Instances" button for all cancelled executions with recovery instances.

**Details**: See [Partial Execution Status Enhancement](docs/requirements/PARTIAL_EXECUTION_STATUS_ENHANCEMENT.md)

**Estimate**: 1-2 days

### 📚 Project History

**Complete architectural evolution and version history**: [GitHub History Archive](archive/GitHubHistory/README.md)

The archive contains 27 snapshots tracking the project's evolution from initial prototype (November 2025) through the major v4.0.0 repository consolidation (January 2026), including:
- Tagged releases with detailed analysis
- Date-specific snapshots of key milestones
- Architecture evolution documentation
- Schema migration history (PascalCase → camelCase)
- Complete CloudFormation and Lambda evolution tracking
- Original GitHub repository contents preserved in `archive/GitHubRepoArchive/`

**Latest Major Milestone**: v4.0.0 successfully merged complete GitLab repository (1,474 files, +177,551 lines) with enhanced Lambda architecture, comprehensive documentation, and unified deployment pipeline.

### Key Capabilities

- **Cost-Effective**: $12-40/month operational cost with pay-per-use serverless pricing
- **Unlimited Waves**: Flexible wave-based orchestration with no artificial constraints
- **Platform Agnostic**: Supports any source platform (physical servers, cloud instances, virtual machines)
- **Sub-Second RPO**: Leverages AWS DRS continuous replication capabilities
- **Fully Serverless**: No infrastructure to manage, scales automatically
- **Launch Config Sync**: Automatically applies Protection Group launch configurations to DRS at execution time

## Key Features

### Wave-Based Orchestration Engine
- **Step Functions Integration**: `waitForTaskToken` pattern enables pause/resume with up to 1-year timeouts
- **Dependency Management**: Waves execute only after dependencies complete successfully
- **Manual Validation Points**: Pause before critical waves for human approval
- **Real-Time Control**: Resume, cancel, or terminate operations during execution
- **Parallel Execution**: Servers within waves launch in parallel with DRS-safe 15-second delays
- **Launch Config Sync**: Protection Group settings (subnet, security groups, instance type) applied to DRS before recovery

### Dynamic Tag Synchronization
- **EventBridge Scheduling**: Automated EC2 → DRS tag sync with configurable intervals (1-24 hours)
- **Immediate Sync Triggers**: Automatic manual sync when settings are updated
- **Multi-Region Support**: Synchronizes across all 30 AWS DRS regions automatically

### Protection Groups & Recovery Plans
- **Tag-Based Selection**: Servers automatically included/excluded based on current tags
- **Multi-Protection-Group Waves**: Single wave can orchestrate multiple protection groups
- **Conflict Detection**: Prevents servers from being assigned to multiple groups globally
- **Launch Configuration Inheritance**: Group-level settings applied to all member servers at execution time
- **Bulk Launch Settings Management**: Configure subnet, security groups, instance type, and tags once at the Protection Group level - settings automatically sync to all DRS launch templates for member servers
- **Simplified DRS Management**: Eliminates need to manually configure each server's launch template in the DRS console

### Comprehensive REST API
- **47+ API Endpoints**: Complete REST API across 12 categories with RBAC security
- **Cross-Account Operations**: Manage DRS across multiple AWS accounts
- **Direct Lambda Invocation**: Bypass API Gateway for AWS-native automation
- **DRS Operations**: Supports core orchestration operations (describe servers, start recovery, get/update launch configuration, describe jobs and events, describe recovery instances) - administrative operations like disconnect/delete server remain in DRS console

## Architecture

### Full-Stack Architecture (CloudFront + Cognito + API Gateway)

![AWS DRS Orchestration - Comprehensive Architecture](docs/architecture/AWS-DRS-Orchestration-Architecture-Comprehensive.png)

**Components**: CloudFront CDN, S3 Static Hosting, Cognito User Pool, API Gateway, 5 Lambda Functions, Step Functions, DynamoDB (4 tables), EventBridge, CloudWatch, SNS, AWS DRS, Cross-Account IAM Roles

**User Roles**: DRSOrchestrationAdmin, DRSRecoveryManager, DRSPlanManager, DRSOperator, DRSReadOnly

### Backend-Only Architecture (Direct Lambda Invocation)

![AWS DRS Orchestration - Backend Only](docs/architecture/AWS-DRS-Orchestration-Backend-Only.png)

**Use Case**: CLI/SDK automation, internal operations tools, CI/CD pipeline integration

**Benefits**: 60% lower cost (no API Gateway), simpler architecture, native AWS authentication, ideal for automation

**Deployment**: Use `--no-frontend` flag to deploy backend-only mode

### Technology Stack

| Layer      | Technology                                                    |
| ---------- | ------------------------------------------------------------- |
| Frontend   | React 19.1.1, TypeScript 5.9.3, CloudScape Design System 3.0.1148 |
| API        | Amazon API Gateway (REST), Amazon Cognito                     |
| Compute    | AWS Lambda (Python 3.12), AWS Step Functions                  |
| Database   | Amazon DynamoDB (4 tables with GSI, native camelCase schema)  |
| Hosting    | Amazon S3, Amazon CloudFront                                  |
| DR Service | AWS Elastic Disaster Recovery (DRS)                           |

## Deployment Flexibility

The solution supports **4 flexible deployment modes** to accommodate different use cases:

| Mode | IAM Role | Frontend | Use Case |
|------|----------|----------|----------|
| **Default Standalone** | Created | ✅ Deployed | Complete standalone solution |
| **API-Only Standalone** | Created | ❌ Skipped | Custom frontend or CLI/SDK only |
| **External Role + Frontend** | External Provided | ✅ Deployed | External IAM integration with DRS UI |
| **Full External Integration** | External Provided | ❌ Skipped | External unified frontend |

### Unified Orchestration Role

All Lambda functions use a **single unified IAM role** that consolidates permissions from 7 individual function roles:

**Key Benefits:**
- **Simplified Management**: One role instead of seven (~500 lines of CloudFormation removed)
- **Consistent Permissions**: All functions have access to required services
- **External Role Support**: Integrate with HRP's centralized permission management
- **16 Policy Statements**: Comprehensive permissions for DRS, EC2, Step Functions, DynamoDB, and more

**Critical Permissions Included:**
- `states:SendTaskHeartbeat` - Long-running Step Functions tasks
- `drs:CreateRecoveryInstanceForDrs` - AllowLaunchingIntoThisInstance pattern (IP preservation)
- `ec2:CreateLaunchTemplateVersion` - Launch template updates for pre-provisioned instances
- `ssm:CreateOpsItem` - Operational tracking and visibility

**For External Integration:** See [Orchestration Role Specification](docs/reference/ORCHESTRATION_ROLE_SPECIFICATION.md) for complete role requirements.

### Deployment Mode Examples

```bash
# Mode 1: Default Standalone (no parameters needed)
./scripts/deploy.sh dev

# Mode 2: API-Only Standalone
./scripts/deploy.sh dev --no-frontend

# Mode 3: External Integration with Frontend
./scripts/deploy.sh dev --orchestration-role arn:aws:iam::123456789012:role/ExternalOrchestrationRole

# Mode 4: Full External Integration (API-Only)
./scripts/deploy.sh dev --no-frontend --orchestration-role arn:aws:iam::123456789012:role/ExternalOrchestrationRole
```

### CloudFormation Parameters

**New Parameters:**
- `OrchestrationRoleArn` (String, optional) - External IAM role ARN for HRP integration
- `DeployFrontend` (String, default: 'true') - Controls frontend deployment

**Example CloudFormation Deployment:**
```bash
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration-dev \
    AdminEmail=admin@example.com \
    OrchestrationRoleArn=arn:aws:iam::123456789012:role/ExternalOrchestrationRole \
    DeployFrontend=false \
  --capabilities CAPABILITY_NAMED_IAM
```

**See [Deployment Flexibility Guide](docs/guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md) for complete documentation.**

## Quick Start

### Prerequisites

- AWS Account with DRS configured and source servers replicating
- AWS CLI v2 configured with appropriate permissions
- Node.js 18+ and npm (for frontend development)
- Python 3.12+ (for Lambda development and local CI/CD)
- S3 bucket for deployment artifacts

### Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd aws-drs-orchestration

# Copy environment template and configure
cp .env.dev.template .env.dev
# Edit .env.dev with your configuration

# Source environment variables
source .env.dev

# Setup Python virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Deploy with Unified Deploy Script (Recommended)

The solution uses a **unified deployment script** that handles validation, security scanning, testing, and deployment in a single command.

```bash
# Full deployment pipeline (validate, test, deploy)
./scripts/deploy.sh dev

# Quick deployment (skip security scans and tests)
./scripts/deploy.sh dev --quick

# Validation only (no deployment)
./scripts/deploy.sh dev --validate-only

# Lambda-only update (fastest - ~30-60 seconds)
./scripts/deploy.sh dev --lambda-only

# Frontend-only update
./scripts/deploy.sh dev --frontend-only

# Skip git push (local testing)
./scripts/deploy.sh dev --skip-push
```

#### Deployment Pipeline Stages

| Stage | Duration | Description |
|-------|----------|-------------|
| **[1/5] Validation** | ~1 min | cfn-lint, flake8, black, TypeScript type checking |
| **[2/5] Security** | ~1 min | bandit, cfn_nag, detect-secrets, npm audit (skipped with `--quick`) |
| **[3/5] Tests** | ~1 min | pytest, vitest (skipped with `--quick`) |
| **[4/5] Git Push** | ~5 sec | Push to remote (skipped with `--skip-push` or `--validate-only`) |
| **[5/5] Deploy** | ~5-10 min | Lambda packaging, S3 sync, CloudFormation deployment |

**Total Time**: 3-5 minutes (full), 2-3 minutes (quick), 30-60 seconds (lambda-only)

### Alternative: Direct CloudFormation Deployment

```bash
# Direct CloudFormation deployment (after manual artifact sync)
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    SourceBucket=aws-drs-orchestration-dev \
    AdminEmail=your-email@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-dev \
  --query 'Stacks[0].Outputs' \
  --output table
```

| Output           | Description              |
| ---------------- | ------------------------ |
| CloudFrontURL    | Frontend application URL |
| ApiEndpoint      | REST API endpoint        |
| UserPoolId       | Cognito User Pool ID     |
| UserPoolClientId | Cognito App Client ID    |

## AWS DRS Regional Availability

The solution orchestrates disaster recovery in all **30 AWS regions** where Elastic Disaster Recovery (DRS) is available:

| Region Group                   | Count | Regions                                                                                                    |
| ------------------------------ | ----- | ---------------------------------------------------------------------------------------------------------- |
| **Americas**             | 6     | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America (São Paulo) |
| **Europe**               | 8     | Ireland, London, Frankfurt, Paris, Stockholm, Milan, Spain, Zurich                                         |
| **Asia Pacific**         | 10    | Tokyo, Seoul, Osaka, Singapore, Sydney, Mumbai, Hyderabad, Jakarta, Melbourne, Hong Kong                   |
| **Middle East & Africa** | 4     | Bahrain, UAE, Cape Town, Tel Aviv                                                                          |
| **GovCloud**             | 2     | US-East, US-West                                                                                           |

## Infrastructure

### CloudFormation Stacks (16 Templates)

The solution uses a modular nested stack architecture. The API Gateway is split across 6 stacks due to CloudFormation limits (500 resources/stack, 51,200 bytes template body, 1MB S3 template) and best practices for maintainability:

| Stack | Purpose | Key Resources |
| ----- | ------- | ------------- |
| `master-template.yaml` | Root orchestrator | Parameter propagation, nested stack coordination, **UnifiedOrchestrationRole** (consolidates 7 individual roles) |
| `database-stack.yaml` | Data persistence | 4 DynamoDB tables with encryption (camelCase schema) |
| `lambda-stack.yaml` | Compute layer | 8 Lambda functions (all use unified role) |
| `api-auth-stack.yaml` | Authentication | Cognito User Pool, Identity Pool, RBAC groups |
| `api-gateway-core-stack.yaml` | API Gateway base | REST API, Cognito authorizer |
| `api-gateway-resources-stack.yaml` | API paths | URL path resources for all endpoints |
| `api-gateway-core-methods-stack.yaml` | CRUD methods | Protection Groups, Recovery Plans, Config endpoints |
| `api-gateway-operations-methods-stack.yaml` | Execution methods | Execution, workflow, DRS operation endpoints |
| `api-gateway-infrastructure-methods-stack.yaml` | Infrastructure methods | Discovery, cross-account, health endpoints |
| `api-gateway-deployment-stack.yaml` | API deployment | Stage deployment, throttling settings |
| `step-functions-stack.yaml` | Orchestration | State machine with waitForTaskToken |
| `eventbridge-stack.yaml` | Event scheduling | Execution polling rules |
| `frontend-stack.yaml` | Frontend hosting | S3 bucket, CloudFront distribution (conditional) |
| `notification-stack.yaml` | Notifications | SNS topics, email subscriptions |
| `cross-account-role-stack.yaml` | Multi-account | Cross-account IAM roles |
| `github-oidc-stack.yaml` | CI/CD | OIDC authentication (legacy, not actively used) |

**Note:** The UnifiedOrchestrationRole consolidates permissions from 7 individual Lambda roles, simplifying IAM management while maintaining security. See [Deployment Flexibility Guide](docs/guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md) for details.

### Lambda Functions (6 Handlers)

All Lambda functions use the **UnifiedOrchestrationRole** (or externally-provided role in external integration mode). Shared utilities in `lambda/shared/` provide common functionality across all functions.

| Function | Directory | Purpose | Endpoints |
| -------- | --------- | ------- | --------- |
| `data-management-handler` | `lambda/data-management-handler/` | Protection groups, recovery plans, configuration management | 21 |
| `execution-handler` | `lambda/execution-handler/` | Recovery execution control, pause/resume, termination | 11 |
| `query-handler` | `lambda/query-handler/` | Read-only queries, DRS status, EC2 resource discovery | 12 |
| `orchestration-stepfunctions` | `lambda/orchestration-stepfunctions/` | Step Functions orchestration with launch config sync | N/A |
| `frontend-deployer` | `lambda/frontend-deployer/` | Frontend deployment automation (CloudFormation Custom Resource) | N/A |
| `notification-formatter` | `lambda/notification-formatter/` | SNS notification formatting | N/A |

**Total API Endpoints**: 44 endpoints across 3 API handlers

### DynamoDB Tables (Native camelCase Schema)

| Table                       | Purpose             | Key Schema                            |
| --------------------------- | ------------------- | ------------------------------------- |
| `protection-groups-{env}` | Server groupings    | `groupId` (PK)                      |
| `recovery-plans-{env}`    | Wave configurations | `planId` (PK)                       |
| `execution-history-{env}` | Audit trail         | `executionId` (PK), `planId` (SK) |
| `target-accounts-{env}`   | Multi-account       | `accountId` (PK)                    |

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

## Security & RBAC

### Role-Based Access Control
The solution implements comprehensive RBAC with 5 granular DRS-specific roles:

| Role | Description |
|------|-------------|
| **DRSOrchestrationAdmin** | Full administrative access |
| **DRSRecoveryManager** | Recovery operations lead |
| **DRSPlanManager** | DR planning focus |
| **DRSOperator** | On-call operations |
| **DRSReadOnly** | Audit and monitoring |

### Security Features
- **Encryption**: All data encrypted at rest and in transit
- **Authentication**: Cognito JWT token-based authentication (45-minute session timeout)
- **Authorization**: API-level RBAC enforcement
- **Audit Trails**: Complete user action logging

## Documentation

### User Guides
- [Deployment Flexibility Guide](docs/guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md) - 4 deployment modes, external IAM integration, migration guide
- [Developer Guide](docs/guides/DEVELOPER_GUIDE.md) - Local development, testing, debugging workflows
- [DRS Execution Walkthrough](docs/guides/DRS_EXECUTION_WALKTHROUGH.md) - Complete drill and recovery procedures
- [DRS Pre-Provisioned Instance Recovery](docs/guides/DRS_PRE_PROVISIONED_INSTANCE_RECOVERY.md) - AllowLaunchingIntoThisInstance pattern for IP preservation
- [DRS Recovery and Failback Complete Guide](docs/guides/DRS_RECOVERY_AND_FAILBACK_COMPLETE_GUIDE.md) - End-to-end recovery procedures
- [API Development Quick Reference](docs/guides/API_DEVELOPMENT_QUICK_REFERENCE.md) - API development patterns and examples

### Deployment & CI/CD
- [Quick Start Guide](docs/deployment/QUICK_START_GUIDE.md) - Fast deployment walkthrough
- [CI/CD Guide](docs/deployment/CICD_GUIDE.md) - Deployment workflows and automation
- [CI/CD Enforcement](docs/deployment/CI_CD_ENFORCEMENT.md) - Deployment policy and validation requirements

### Requirements & Architecture
- [Product Requirements Document](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) - Complete PRD with feature specifications
- [Software Requirements Specification](docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md) - Technical specifications and system requirements
- [UX/UI Design Specifications](docs/requirements/UX_UI_DESIGN_SPECIFICATIONS.md) - User interface design and component specifications
- [Architecture](docs/architecture/ARCHITECTURE.md) - System architecture and AWS service integration

### Reference Documentation
- [API Endpoints Reference](docs/reference/API_ENDPOINTS_CURRENT.md) - Complete API endpoint documentation (44 endpoints)
- [Orchestration Role Specification](docs/reference/ORCHESTRATION_ROLE_SPECIFICATION.md) - Complete IAM role requirements for external integration
- [DRS IAM and Permissions Reference](docs/reference/DRS_IAM_AND_PERMISSIONS_REFERENCE.md) - Comprehensive IAM policy analysis
- [DRS Service Limits and Capabilities](docs/reference/DRS_SERVICE_LIMITS_AND_CAPABILITIES.md) - Service quotas and constraints
- [DRS Cross-Account Reference](docs/reference/DRS_CROSS_ACCOUNT_REFERENCE.md) - Multi-account configuration and cross-account roles
- [DRS Launch Configuration Reference](docs/reference/DRS_LAUNCH_CONFIGURATION_REFERENCE.md) - Launch template management and configuration
- [DR Wave Priority Mapping](docs/reference/DR_WAVE_PRIORITY_MAPPING.md) - Wave and priority assignment strategy

### Troubleshooting
- [Deployment Troubleshooting Guide](docs/troubleshooting/DEPLOYMENT_TROUBLESHOOTING_GUIDE.md) - Common deployment issues and solutions
- [DRS Execution Troubleshooting Guide](docs/troubleshooting/DRS_EXECUTION_TROUBLESHOOTING_GUIDE.md) - Recovery execution debugging
- [Authentication Issues](docs/troubleshooting/AUTHENTICATION_ISSUES.md) - Cognito and API Gateway authentication troubleshooting
- [Known Issues](docs/troubleshooting/KNOWN_ISSUES.md) - Current known issues and workarounds

## CI/CD Pipeline

The project uses a **unified deployment script** that provides comprehensive validation, security scanning, and testing.

### Unified Deploy Script

**Recommended for all deployment scenarios.**

```bash
# Full deployment pipeline (validate, security, test, deploy)
./scripts/deploy.sh dev

# Quick deployment (skip security scans and tests)
./scripts/deploy.sh dev --quick

# Validation only (no deployment)
./scripts/deploy.sh dev --validate-only

# Lambda-only update (fastest - ~30-60 seconds)
./scripts/deploy.sh dev --lambda-only

# Frontend-only deployment
./scripts/deploy.sh dev --frontend-only

# Skip git push (local testing)
./scripts/deploy.sh dev --skip-push
```

#### Deployment Pipeline Stages

| Stage | Duration | Description | Skip With |
|-------|----------|-------------|-----------|
| **[1/5] Validation** | ~1 min | cfn-lint, flake8, black, TypeScript | N/A (always runs) |
| **[2/5] Security** | ~1 min | bandit, cfn_nag, detect-secrets, npm audit | `--quick` |
| **[3/5] Tests** | ~1 min | pytest, vitest | `--quick` |
| **[4/5] Git Push** | ~5 sec | Push to remote | `--skip-push`, `--validate-only` |
| **[5/5] Deploy** | ~5-10 min | Lambda packaging, S3 sync, CloudFormation | `--validate-only` |

**Total Time**: 
- Full pipeline: 3-5 minutes
- Quick deployment: 2-3 minutes  
- Lambda-only: 30-60 seconds
- Validation-only: 2-3 minutes (no deployment)

### Built-in Protections

The deploy script includes automatic safety checks:

- **Stack Protection**: Blocks deployment to protected `-test` stacks
- **Concurrency Protection**: Prevents overlapping deployments
- **Credential Check**: Verifies AWS credentials before starting
- **Validation Gates**: Stops deployment if validation fails
- **Rollback Recovery**: Automatically handles `UPDATE_ROLLBACK_FAILED` states

### Makefile Shortcuts

```bash
make validate-only          # Run validation without deployment
make deploy-dev             # Full deployment to dev
make deploy-dev-quick       # Quick deployment (skip security/tests)
make deploy-lambda-only     # Update Lambda functions only
make deploy-frontend-only   # Update frontend only
```

## Contributing

1. **Clone the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make changes and test locally**
4. **Run validation** (`./scripts/deploy.sh dev --validate-only`)
5. **Commit changes** (`git commit -m 'Add amazing feature'`)
6. **Push to remote** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd aws-drs-orchestration

# Setup Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Setup environment
cp .env.dev.template .env.dev
# Edit .env.dev with your configuration
source .env.dev

# Frontend development
cd frontend
npm install
npm run dev  # Development server at localhost:5173

# Backend testing
pytest tests/python/unit/ -v
pytest tests/integration/ -v

# Run validation before committing
./scripts/deploy.sh dev --validate-only

# Full deployment
./scripts/deploy.sh dev
```

### Deployment Options

```bash
# Full deployment with validation, security, and tests
./scripts/deploy.sh dev

# Quick deployment (skip security/tests)
./scripts/deploy.sh dev --quick

# Validation only (no deployment)
./scripts/deploy.sh dev --validate-only

# Lambda-only update (fastest)
./scripts/deploy.sh dev --lambda-only

# Frontend-only update
./scripts/deploy.sh dev --frontend-only
```

## Directory Structure

```text
aws-drs-orchestration/
├── cfn/                          # CloudFormation IaC (16 templates)
│   ├── master-template.yaml      # Root orchestrator for nested stacks
│   └── github-oidc-stack.yaml    # OIDC integration (legacy, not actively used)
├── frontend/                     # React + CloudScape UI (32+ components)
├── lambda/                       # Python Lambda functions (6 handlers + shared utilities)
│   ├── data-management-handler/  # Protection groups, recovery plans CRUD
│   ├── execution-handler/        # Recovery execution control
│   ├── query-handler/            # Read-only queries, DRS status
│   ├── orchestration-stepfunctions/  # Step Functions orchestration
│   ├── frontend-deployer/        # Frontend deployment automation
│   ├── notification-formatter/   # SNS notification formatting
│   └── shared/                   # Shared utilities (RBAC, DRS, security)
├── scripts/                      # Deployment and automation scripts
│   ├── deploy.sh                 # Unified deployment script (recommended)
│   ├── package_lambda.py         # Lambda packaging utility
│   └── *.sh                      # Additional utility scripts
├── tests/                        # Python unit/integration tests
│   ├── python/unit/              # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── docs/                         # Comprehensive documentation (40+ files)
│   ├── guides/                   # User guides and walkthroughs
│   ├── reference/                # API and technical reference
│   ├── architecture/             # Architecture diagrams and docs
│   ├── deployment/               # Deployment guides
│   └── troubleshooting/          # Troubleshooting guides
├── .venv/                        # Python virtual environment (local)
├── Makefile                      # Build automation shortcuts
├── mise.toml                     # Tool version management
└── README.md                     # This file
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete project history.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built for enterprise disaster recovery on AWS
