# Project Context

## Product Overview

AWS DRS Orchestration is a serverless disaster recovery orchestration platform for AWS Elastic Disaster Recovery (DRS) that enables enterprise organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native services.

## Key Features

- **Wave-Based Recovery**: Execute disaster recovery in coordinated waves with explicit dependencies between tiers (database → application → web)
- **Protection Groups**: Organize DRS source servers into logical groups for coordinated recovery with automatic discovery
- **Pause/Resume Execution**: Pause execution before specific waves for manual validation, then resume when ready
- **API-First Design**: Complete REST API (42 endpoints across 12 categories) for DevOps integration and automation workflows
- **Enterprise-Grade**: Built on AWS serverless architecture with CloudFormation IaC for reproducible deployments

## Architecture

- **Serverless**: 5 Lambda functions, Step Functions, API Gateway, DynamoDB
- **Infrastructure as Code**: 7 CloudFormation templates (1 master + 6 nested stacks)
- **Frontend**: React 19.1.1 + TypeScript 5.9.3 + CloudScape Design System 3.0.1148
- **Backend**: Python 3.12 Lambda functions with boto3 and crhelper 2.0.11

## Directory Structure

```text
AWS-DRS-Orchestration/
├── .amazonq/                     # Amazon Q Developer rules and configuration
│   └── rules/                    # Amazon Q specific project context
├── .kiro/                        # Kiro AI assistant configuration
│   ├── settings/                 # MCP and other settings
│   ├── specs/                    # Active specifications (fresh-deployment)
│   └── steering/                 # AI steering documents (project-context.md)
├── buildspecs/                   # AWS CodeBuild specifications (6 active files)
│   ├── validate-buildspec.yml    # Template validation and code quality
│   ├── security-buildspec.yml    # Comprehensive security scanning
│   ├── build-buildspec.yml       # Lambda and frontend builds
│   ├── test-buildspec.yml        # Unit and integration tests
│   ├── deploy-infra-buildspec.yml # Infrastructure deployment
│   └── deploy-frontend-buildspec.yml # Frontend deployment with dynamic config
├── cfn/                          # CloudFormation Infrastructure as Code (7 templates)
├── frontend/                     # React + CloudScape UI (37 components, 9 pages)
├── lambda/                       # Python Lambda functions (5 active functions)
├── scripts/                      # Deployment and automation scripts
├── tests/                        # Python unit/integration tests (minimal, needs expansion)
└── docs/                         # Comprehensive documentation (40+ files)
```

## Core Technologies

### Frontend Stack
- React 19.1.1 with TypeScript 5.9.3
- CloudScape Design System 3.0.1148 (AWS-native UI)
- AWS Amplify 6.15.8 for authentication
- Vite 7.1.7 for build tooling
- React Router 7.9.5 for navigation

### Backend Stack
- AWS Lambda (Python 3.12 runtime)
- API Gateway with Cognito JWT authentication
- Step Functions orchestration with waitForTaskToken
- DynamoDB (3 tables: protection-groups, recovery-plans, execution-history)
- EventBridge for scheduled polling

### AWS Services
- **API Gateway**: REST API with Cognito authorizer
- **Cognito**: User authentication with 45-minute session timeout
- **Step Functions**: Orchestration state machine with waitForTaskToken
- **DynamoDB**: NoSQL database for all entities
- **S3**: Static website hosting and deployment artifact storage
- **CloudFront**: CDN for global frontend distribution
- **AWS DRS**: Elastic Disaster Recovery service integration

## Documentation Index

### Requirements (Source of Truth)
- [Product Requirements Document](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md)
- [Software Requirements Specification](docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md)
- [UX/UI Design Specifications](docs/requirements/UX_UI_DESIGN_SPECIFICATIONS.md)

### Architecture
- [Architecture Diagram (PNG)](docs/architecture/AWS-DRS-Orchestration-Architecture.png)
- [Architectural Design Document](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md)

### Essential Guides
- [API Reference Guide](docs/guides/API_REFERENCE_GUIDE.md) - Complete REST API documentation
- [Development Workflow Guide](docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md) - Development, testing, deployment
- [Orchestration Integration Guide](docs/guides/ORCHESTRATION_INTEGRATION_GUIDE.md) - CLI, SSM, Step Functions integration
- [Troubleshooting Guide](docs/guides/TROUBLESHOOTING_GUIDE.md) - Common issues and debugging

### Specialized Guides
- **Deployment**: [docs/guides/deployment/](docs/guides/deployment/) - Fresh deployment, CI/CD setup and activation
- **Development**: [docs/guides/development/](docs/guides/development/) - Developer onboarding, coding standards, IDE setup
- **Troubleshooting**: [docs/guides/troubleshooting/](docs/guides/troubleshooting/) - Deployment, execution, and service limit debugging

### Implementation Features
- [Cross-Account Features](docs/implementation/CROSS_ACCOUNT_FEATURES.md)
- [DRS Source Server Management](docs/implementation/DRS_SOURCE_SERVER_MANAGEMENT.md)
- [Automation & Orchestration](docs/implementation/AUTOMATION_AND_ORCHESTRATION.md)

## CI/CD Infrastructure

### AWS CodePipeline Deployment

The project uses **AWS CodePipeline** for automated deployment with the following active infrastructure:

| Component | Name | Purpose |
|-----------|------|---------|
| **Pipeline** | `aws-elasticdrs-orchestrator-pipeline-dev` | 7-stage automated deployment |
| **Primary Repository** | `aws-elasticdrs-orchestrator-dev` (CodeCommit) | Source code repository |
| **Secondary Repository** | GitHub mirror | Development collaboration |
| **Account** | 438465159935 | AWS account for all resources |
| **Deployment Bucket** | `aws-elasticdrs-orchestrator` | Artifact storage |

### Pipeline Stages

1. **Source** (~30s) - Code retrieval from CodeCommit
2. **Validate** (~2-3min) - CloudFormation validation, Python linting
3. **SecurityScan** (~3-4min) - Bandit security scan, cfn-lint checks
4. **Build** (~4-5min) - Lambda packaging, frontend builds
5. **Test** (~3-4min) - Unit tests, integration tests, coverage
6. **DeployInfrastructure** (~8-10min) - CloudFormation stack updates
7. **DeployFrontend** (~2-3min) - S3 sync, CloudFront invalidation

**Total Duration**: 15-20 minutes for complete deployment

### Development Workflow Options

#### CI/CD Pipeline (Production)
```bash
# Configure Git for CodeCommit
export AWS_PROFILE=438465159935_AdministratorAccess
git config --global credential.helper '!aws codecommit credential-helper $@'
git config --global credential.UseHttpPath true

# Add CodeCommit remote and push to trigger pipeline
git remote add aws-pipeline https://git-codecommit.us-east-1.amazonaws.com/v1/repos/aws-elasticdrs-orchestrator-dev
git push aws-pipeline main  # Triggers 15-20 minute deployment
```

#### Manual Deployment (Development)
```bash
# Fast development workflow using S3 deployment bucket
./scripts/sync-to-deployment-bucket.sh --update-lambda-code  # 5 seconds
./scripts/sync-to-deployment-bucket.sh --deploy-cfn         # 5-10 minutes
```

### S3 Deployment Bucket (Source of Truth)

```
s3://aws-elasticdrs-orchestrator/
├── cfn/                     # CloudFormation templates (7 total)
├── lambda/                  # Lambda deployment packages (5 functions)
└── frontend/                # Frontend build artifacts
```

## Key Implementation Patterns

### Pause/Resume Execution
Uses Step Functions `waitForTaskToken` callback pattern for wave-by-wave execution control.

### Real-Time Polling
- Frontend polls every 3 seconds for active executions
- EventBridge triggers execution-finder every 1 minute
- DRS job status polled until LAUNCHED or FAILED

### API-First Design
- REST API via API Gateway with Cognito JWT authentication
- Lambda functions handle all business logic
- Complete CRUD operations with validation and error handling
- Every UI function has corresponding API endpoint for automation