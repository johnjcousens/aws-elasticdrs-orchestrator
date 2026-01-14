# AWS DRS Orchestration Solution

Enterprise-grade disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

[![AWS](https://img.shields.io/badge/AWS-DRS-FF9900?logo=amazonaws)](https://aws.amazon.com/disaster-recovery/)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-232F3E?logo=amazonaws)](cfn/)
[![React](https://img.shields.io/badge/Frontend-React%2019.1.1-61DAFB?logo=react)](frontend/)
[![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?logo=python)](lambda/)
[![GitHub](https://img.shields.io/badge/Repository-GitHub-181717?logo=github)](https://github.com/johnjcousens/aws-elasticdrs-orchestrator)

## Overview

**Version**: v1.3.0 (January 2026)

AWS DRS Orchestration enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native serverless services.

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

### Comprehensive REST API
- **47+ API Endpoints**: Complete REST API across 12 categories with RBAC security
- **Cross-Account Operations**: Manage DRS across multiple AWS accounts
- **Direct Lambda Invocation**: Bypass API Gateway for AWS-native automation

## Architecture

![AWS DRS Orchestration Architecture](docs/architecture/AWS-DRS-Orchestration-Architecture.png)

### Technology Stack

| Layer      | Technology                                                    |
| ---------- | ------------------------------------------------------------- |
| Frontend   | React 19.1.1, TypeScript 5.9.3, CloudScape Design System 3.0.1148 |
| API        | Amazon API Gateway (REST), Amazon Cognito                     |
| Compute    | AWS Lambda (Python 3.12), AWS Step Functions                  |
| Database   | Amazon DynamoDB (4 tables with GSI, native camelCase schema)  |
| Hosting    | Amazon S3, Amazon CloudFront                                  |
| DR Service | AWS Elastic Disaster Recovery (DRS)                           |

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
  --stack-name aws-elasticdrs-orchestrator \
  --parameter-overrides \
    ProjectName=aws-elasticdrs-orchestrator \
    Environment=test \
    SourceBucket=your-bucket \
    AdminEmail=admin@yourcompany.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-test \
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

### CloudFormation Stacks (18 Templates)

The solution uses a modular nested stack architecture. The API Gateway is split across 6 stacks due to CloudFormation limits (500 resources/stack, 51,200 bytes template body, 1MB S3 template) and best practices for maintainability:

| Stack | Purpose | Key Resources |
| ----- | ------- | ------------- |
| `master-template.yaml` | Root orchestrator | Parameter propagation, nested stack coordination |
| `database-stack.yaml` | Data persistence | 4 DynamoDB tables with encryption (camelCase schema) |
| `lambda-stack.yaml` | Compute layer | 7 Lambda functions, IAM roles |
| `api-auth-stack.yaml` | Authentication | Cognito User Pool, Identity Pool, RBAC groups |
| `api-gateway-core-stack.yaml` | API Gateway base | REST API, Cognito authorizer |
| `api-gateway-resources-stack.yaml` | API paths | URL path resources for all endpoints |
| `api-gateway-core-methods-stack.yaml` | CRUD methods | Protection Groups, Recovery Plans, Config endpoints |
| `api-gateway-operations-methods-stack.yaml` | Execution methods | Execution, workflow, DRS operation endpoints |
| `api-gateway-infrastructure-methods-stack.yaml` | Infrastructure methods | Discovery, cross-account, health endpoints |
| `api-gateway-deployment-stack.yaml` | API deployment | Stage deployment, throttling settings |
| `step-functions-stack.yaml` | Orchestration | State machine with waitForTaskToken |
| `eventbridge-stack.yaml` | Event scheduling | Execution polling rules |
| `frontend-stack.yaml` | Frontend hosting | S3 bucket, CloudFront distribution |
| `notification-stack.yaml` | Notifications | SNS topics, email subscriptions |
| `security-stack.yaml` | Security | WAF, security groups |
| `security-monitoring-stack.yaml` | Monitoring | CloudWatch alarms, dashboards |
| `cross-account-role-stack.yaml` | Multi-account | Cross-account IAM roles |
| `github-oidc-stack.yaml` | CI/CD | GitHub Actions OIDC authentication |

### Lambda Functions (7 Active)

| Function | Directory | Purpose |
| -------- | --------- | ------- |
| `api-handler` | `lambda/api-handler/` | REST API request handling (47+ endpoints) |
| `orchestration-stepfunctions` | `lambda/orchestration-stepfunctions/` | Step Functions orchestration with launch config sync |
| `execution-finder` | `lambda/execution-finder/` | Find active executions for EventBridge polling |
| `execution-poller` | `lambda/execution-poller/` | Poll DRS job status and update execution state |
| `frontend-builder` | `lambda/frontend-builder/` | Frontend deployment automation |
| `bucket-cleaner` | `lambda/bucket-cleaner/` | S3 cleanup on stack deletion |
| `notification-formatter` | `lambda/notification-formatter/` | SNS notification formatting |

Shared utilities in `lambda/shared/` provide common functionality across all functions.

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

### Essential Guides
- [API Reference Guide](docs/guides/API_REFERENCE_GUIDE.md) - Complete REST API documentation (47+ endpoints)
- [Orchestration Integration Guide](docs/guides/ORCHESTRATION_INTEGRATION_GUIDE.md) - CLI, SSM, Step Functions integration
- [DRS Execution Walkthrough](docs/guides/DRS_EXECUTION_WALKTHROUGH.md) - Complete drill and recovery procedures
- [Troubleshooting Guide](docs/guides/TROUBLESHOOTING_GUIDE.md) - Common issues and debugging
- [Deployment and Operations Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) - Complete deployment procedures
- [Development Workflow Guide](docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md) - Development, testing, and CI/CD workflows

### Deployment Guides
- [Fresh Deployment Guide](docs/guides/deployment/FRESH_DEPLOYMENT_GUIDE.md) - Complete fresh environment setup
- [GitHub Actions CI/CD Guide](docs/guides/deployment/GITHUB_ACTIONS_CICD_GUIDE.md) - CI/CD setup and usage

### Development Guides
- [Developer Onboarding Checklist](docs/guides/development/developer-onboarding-checklist.md) - New developer setup
- [Python Coding Standards](docs/guides/development/python-coding-standards.md) - PEP 8 compliance
- [PyCharm Setup Guide](docs/guides/development/pycharm-setup.md) - IDE configuration

### Troubleshooting Guides
- [Deployment Troubleshooting](docs/guides/troubleshooting/DEPLOYMENT_TROUBLESHOOTING_GUIDE.md) - Deployment issues
- [DRS Execution Troubleshooting](docs/guides/troubleshooting/DRS_EXECUTION_TROUBLESHOOTING_GUIDE.md) - Recovery debugging

### Requirements & Architecture
- [Product Requirements Document](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) - Complete PRD
- [Software Requirements Specification](docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md) - Technical specifications
- [UX/UI Design Specifications](docs/requirements/UX_UI_DESIGN_SPECIFICATIONS.md) - User interface design
- [Architectural Design Document](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md) - System architecture

### Implementation Features
- [Cross-Account Features](docs/implementation/CROSS_ACCOUNT_FEATURES.md) - Multi-account DRS operations
- [DRS Source Server Management](docs/implementation/DRS_SOURCE_SERVER_MANAGEMENT.md) - Advanced server management
- [Automation & Orchestration](docs/implementation/AUTOMATION_AND_ORCHESTRATION.md) - Workflow automation patterns

### Reference Documentation
- [DRS IAM and Permissions Reference](docs/reference/DRS_IAM_AND_PERMISSIONS_REFERENCE.md) - Complete IAM requirements
- [DRS Service Limits and Capabilities](docs/reference/DRS_SERVICE_LIMITS_AND_CAPABILITIES.md) - Service constraints
- [DRS Cross-Account Reference](docs/reference/DRS_CROSS_ACCOUNT_REFERENCE.md) - Multi-account configuration

## CI/CD Pipeline

The project uses **GitHub Actions** for automated deployment with comprehensive security scanning and OIDC-based AWS authentication.

### Pipeline Stages

| Stage | Duration | Description |
|-------|----------|-------------|
| **Detect Changes** | ~10s | Analyzes changed files for intelligent deployment |
| **Validate** | ~2 min | CloudFormation validation, linting |
| **Security Scan** | ~2 min | Bandit, Safety security scanning |
| **Build** | ~3 min | Lambda packaging, frontend build |
| **Test** | ~2 min | Unit tests |
| **Deploy** | ~10 min | CloudFormation stack deployment |

### Pipeline Optimization
- **Documentation-only**: ~30 seconds (95% time savings)
- **Frontend-only**: ~12 minutes (45% time savings)
- **Full deployment**: ~22 minutes (complete pipeline)

### Safe Push Workflow

```bash
# RECOMMENDED: Safe push with automatic workflow checking
./scripts/safe-push.sh

# Preview deployment scope before pushing
./scripts/check-deployment-scope.sh

# Alternative: Quick check before manual push
./scripts/check-workflow.sh && git push
```

## Contributing

1. **Fork the GitHub repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make changes and test locally**
4. **Commit changes** (`git commit -m 'Add amazing feature'`)
5. **Push to GitHub** (`./scripts/safe-push.sh origin feature/amazing-feature`)
6. **Open a Pull Request**

### Local Development

```bash
# Clone repository
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
cd aws-elasticdrs-orchestrator

# Frontend development
cd frontend
npm install
npm run dev  # Development server at localhost:5173

# Backend testing
cd tests/python
pip install -r requirements.txt
pytest unit/ -v

# Validate before committing
make validate  # CloudFormation validation
```

## Directory Structure

```text
aws-elasticdrs-orchestrator/
├── .github/                      # GitHub Actions CI/CD workflows
│   └── workflows/deploy.yml      # Main deployment workflow
├── cfn/                          # CloudFormation IaC (15+ templates)
│   ├── master-template.yaml      # Root orchestrator for nested stacks
│   └── github-oidc-stack.yaml    # GitHub Actions OIDC integration
├── frontend/                     # React + CloudScape UI (32+ components)
├── lambda/                       # Python Lambda functions (7 active)
├── scripts/                      # Deployment and automation scripts
├── tests/                        # Python unit/integration tests
└── docs/                         # Comprehensive documentation (40+ files)
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete project history.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built for enterprise disaster recovery on AWS
