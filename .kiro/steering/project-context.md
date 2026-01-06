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
├── .github/                      # GitHub Actions CI/CD workflows
│   └── workflows/                # Deployment automation
│       └── deploy.yml            # Main deployment workflow
├── .kiro/                        # Kiro AI assistant configuration
│   ├── settings/                 # MCP and other settings
│   ├── specs/                    # Active specifications (fresh-deployment)
│   └── steering/                 # AI steering documents (project-context.md)
├── cfn/                          # CloudFormation Infrastructure as Code (8 templates)
│   ├── master-template.yaml      # Root orchestrator for nested stacks
│   ├── github-oidc-stack.yaml    # GitHub Actions OIDC integration (deploy separately)
│   └── ...                       # Application stacks (database, lambda, api, etc.)
├── frontend/                     # React + CloudScape UI (36 components + 2 wrappers + 6 contexts, 7 pages)
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

### GitHub Actions Deployment

The project uses **GitHub Actions** for automated CI/CD deployment.

| Component | Description |
|-----------|-------------|
| **Workflow** | `.github/workflows/deploy.yml` |
| **Repository** | GitHub (primary) |
| **Account** | 438465159935 |
| **Deployment Bucket** | `aws-elasticdrs-orchestrator` |
| **OIDC Stack** | `cfn/github-oidc-stack.yaml` (deploy separately) |

### Workflow Stages

1. **Validate** (~2 min) - CloudFormation validation, Python linting, TypeScript checking
2. **Security Scan** (~2 min) - Bandit security scan, Safety dependency check
3. **Build** (~3 min) - Lambda packaging, frontend build
4. **Test** (~2 min) - Unit tests
5. **Deploy Infrastructure** (~10 min) - CloudFormation stack deployment
6. **Deploy Frontend** (~2 min) - S3 sync, CloudFront invalidation

**Total Duration**: ~20 minutes for complete deployment

### Setup Instructions

1. Deploy the GitHub OIDC stack (one-time):
```bash
aws cloudformation deploy \
  --template-file cfn/github-oidc-stack.yaml \
  --stack-name PROJECT-github-oidc \
  --parameter-overrides \
    ProjectName=PROJECT \
    Environment=ENV \
    GitHubOrg=YOUR_ORG \
    GitHubRepo=YOUR_REPO \
    DeploymentBucket=YOUR_BUCKET \
    ApplicationStackName=YOUR_APP_STACK \
  --capabilities CAPABILITY_NAMED_IAM
```

2. Add GitHub repository secrets:
   - `AWS_ROLE_ARN` - IAM role ARN from OIDC stack
   - `DEPLOYMENT_BUCKET` - S3 bucket name
   - `STACK_NAME` - CloudFormation stack name
   - `ADMIN_EMAIL` - Admin email for Cognito

3. Push to main branch to trigger deployment

### Manual Deployment (Development)

```bash
# Fast development workflow using S3 deployment bucket
./scripts/sync-to-deployment-bucket.sh --update-lambda-code  # 5 seconds
./scripts/sync-to-deployment-bucket.sh --deploy-cfn         # 5-10 minutes
```

## Deployment Discipline (CRITICAL)

### PRIMARY DEPLOYMENT METHOD: GitHub Actions

**ALL changes MUST go through GitHub Actions CI/CD pipeline:**

1. **Make changes locally**
2. **Commit changes**: `git add . && git commit -m "description"`
3. **Push to trigger pipeline**: `git push`
4. **Monitor GitHub Actions**: Verify deployment success
5. **Never bypass the pipeline** for production changes

### Manual Sync Script Usage (EMERGENCY ONLY)

The `sync-to-deployment-bucket.sh` script should ONLY be used in these emergency situations:

- **GitHub Actions is down** and critical production fix needed
- **Pipeline is broken** and needs immediate bypass for hotfix
- **Development debugging** of deployment artifacts (with immediate revert)

**NEVER use manual sync for:**
- ❌ Regular development workflow
- ❌ Feature deployments
- ❌ Production releases
- ❌ "Quick fixes" that bypass review
- ❌ Convenience to avoid waiting for pipeline

### Why GitHub Actions is Required

- **Audit trail**: All changes tracked in Git history
- **Quality gates**: Validation, linting, security scanning, testing
- **Consistent environment**: Same deployment process every time
- **Rollback capability**: Git-based rollback and deployment history
- **Team visibility**: All deployments visible to team members
- **Compliance**: Meets enterprise deployment standards

### S3 Deployment Bucket (Source of Truth)

```
s3://aws-elasticdrs-orchestrator/
├── cfn/                     # CloudFormation templates
├── lambda/                  # Lambda deployment packages (5 functions)
└── frontend/                # Frontend build artifacts
```

## Reference Stack for Testing and Comparison

### Working Reference Stack
- **Stack ARN**: `arn:aws:cloudformation:us-east-1:438465159935:stack/aws-drs-orchestrator-dev/11b25cb0-e5f7-11f0-bde4-12ca9f6188ad`
- **API Gateway URL**: `https://bu05wxn2ci.execute-api.us-east-1.amazonaws.com/dev`
- **Cognito User Pool ID**: `us-east-1_7ClH0e1NS`
- **Cognito Client ID**: `6fepnj59rp7qup2k3n6uda5p19`
- **Test User**: `testuser@example.com` / `TestPassword123!`

### Usage Guidelines
- Use reference stack to verify expected API behavior when debugging issues
- Compare CloudFormation configurations when troubleshooting deployment problems
- Test API endpoints on reference stack to understand correct response formats
- Same test user credentials work on both current and reference stacks

### Authentication Example
```bash
# Get JWT token for reference stack
aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_7ClH0e1NS \
  --client-id 6fepnj59rp7qup2k3n6uda5p19 \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text
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