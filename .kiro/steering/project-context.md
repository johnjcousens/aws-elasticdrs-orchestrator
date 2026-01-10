# Project Context

## Product Overview

AWS DRS Orchestration is a serverless disaster recovery orchestration platform for AWS Elastic Disaster Recovery (DRS) that enables enterprise organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native services.

## Current Release Status

**Latest Version**: v1.3.0 (January 10, 2026) - **Enhanced Wave Progress UI with Consistent Server Status Display**

### Recent Major Achievements
- ✅ **Consistent Server Status Icons**: All servers show completed checkmark (✓) when wave is done
- ✅ **Wave-Aware Status Display**: Server status considers wave context for perfect consistency
- ✅ **Professional UI**: Enterprise-grade AWS console-style interface with CloudScape Design System
- ✅ **Enhanced User Experience**: Crystal clear execution progress visualization
- ✅ **Complete System Restoration**: All execution polling components working correctly

## Key Features

- **Wave-Based Recovery**: Execute disaster recovery in coordinated waves with explicit dependencies between tiers (database → application → web)
- **Protection Groups**: Organize DRS source servers into logical groups for coordinated recovery with automatic discovery
- **Pause/Resume Execution**: Pause execution before specific waves for manual validation, then resume when ready
- **API-First Design**: Complete REST API (47+ endpoints across 12 categories) for DevOps integration and automation workflows
- **Enterprise-Grade**: Built on AWS serverless architecture with CloudFormation IaC for reproducible deployments
- **Enhanced UI**: Professional wave progress display with consistent status indicators and expandable sections

## Architecture

- **Serverless**: 7 Lambda functions, Step Functions, API Gateway, DynamoDB
- **Infrastructure as Code**: 15+ CloudFormation templates (1 master + 14+ nested stacks)
- **Frontend**: React 19.1.1 + TypeScript 5.9.3 + CloudScape Design System 3.0.1148
- **Backend**: Python 3.12 Lambda functions with boto3 and crhelper 2.0.11

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
- DynamoDB (4 tables: protection-groups, recovery-plans, execution-history, target-accounts)
- EventBridge for scheduled polling

### AWS Services
- **API Gateway**: REST API with Cognito authorizer
- **Cognito**: User authentication with 45-minute session timeout
- **Step Functions**: Orchestration state machine with waitForTaskToken
- **DynamoDB**: NoSQL database for all entities
- **S3**: Static website hosting and deployment artifact storage
- **CloudFront**: CDN for global frontend distribution
- **AWS DRS**: Elastic Disaster Recovery service integration

## Current Stack Configuration (PRODUCTION READY)

### Primary Development Stack
- **Stack Name**: `aws-elasticdrs-orchestrator-dev`
- **Stack ARN**: `arn:aws:cloudformation:us-east-1:438465159935:stack/aws-elasticdrs-orchestrator-dev/00c30fb0-eb2b-11f0-9ca6-12010aae964f`
- **API Gateway URL**: `https://akp69tt2m1.execute-api.us-east-1.amazonaws.com/dev`
- **Frontend URL**: `https://dly5x2oq5f01g.cloudfront.net`
- **Cognito User Pool ID**: `us-east-1_ZpRNNnGTK`
- **Cognito Client ID**: `3b9l2jv7engtoeba2t1h2mo5ds`
- **Identity Pool ID**: `us-east-1:052133fc-f2f7-4e0f-be2c-02fd84287feb`
- **Status**: `CREATE_COMPLETE` (Fully Operational)

### Authentication (CURRENT)
- **Username**: `testuser@example.com`
- **Password**: `TestPassword123!`
- **User Pool**: `us-east-1_ZpRNNnGTK`
- **Client ID**: `3b9l2jv7engtoeba2t1h2mo5ds`
- **Group**: `DRSOrchestrationAdmin` (Full access permissions)

### Authentication Example
```bash
# Get JWT token for API access
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_ZpRNNnGTK \
  --client-id 3b9l2jv7engtoeba2t1h2mo5ds \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Use with API endpoints
curl -H "Authorization: Bearer $TOKEN" "https://akp69tt2m1.execute-api.us-east-1.amazonaws.com/dev/executions"
```

### Lambda Functions (All Operational)
- `aws-elasticdrs-orchestrator-api-handler-dev`
- `aws-elasticdrs-orchestrator-orch-sf-dev`
- `aws-elasticdrs-orchestrator-execution-finder-dev`
- `aws-elasticdrs-orchestrator-execution-poller-dev`
- `aws-elasticdrs-orchestrator-frontend-builder-dev`
- `aws-elasticdrs-orchestrator-bucket-cleaner-dev`
- `aws-elasticdrs-orchestrator-notification-formatter-dev`

### DynamoDB Tables (All Operational)
- `aws-elasticdrs-orchestrator-protection-groups-dev`
- `aws-elasticdrs-orchestrator-recovery-plans-dev`
- `aws-elasticdrs-orchestrator-execution-history-dev`
- `aws-elasticdrs-orchestrator-target-accounts-dev`

## CI/CD Infrastructure

### GitHub Actions Deployment (PRIMARY METHOD)

**ALL deployments MUST use GitHub Actions CI/CD pipeline.**

| Component | Description |
|-----------|-------------|
| **Workflow** | `.github/workflows/deploy.yml` |
| **Repository** | GitHub (primary) |
| **Account** | 438465159935 |
| **Deployment Bucket** | `aws-elasticdrs-orchestrator` |
| **OIDC Stack** | `cfn/github-oidc-stack.yaml` (deploy separately) |

### Workflow Stages (Intelligent Optimization)

1. **Detect Changes** (~10s) - Analyzes changed files to determine deployment scope
2. **Validate** (~2 min) - CloudFormation validation, Python linting, TypeScript checking (skip for docs-only)
3. **Security Scan** (~2 min) - Bandit security scan, Safety dependency check (skip for docs-only)
4. **Build** (~3 min) - Lambda packaging, frontend build (skip for docs-only)
5. **Test** (~2 min) - Unit tests (skip for docs-only)
6. **Deploy Infrastructure** (~10 min) - CloudFormation stack deployment (only if infrastructure/Lambda changed)
7. **Deploy Frontend** (~2 min) - S3 sync, CloudFront invalidation (only if frontend changed or infrastructure deployed)

**Pipeline Optimization**:
- **Documentation-only**: ~30 seconds (95% time savings)
- **Frontend-only**: ~12 minutes (45% time savings)  
- **Full deployment**: ~22 minutes (complete pipeline)

### Developer Tools
- `./scripts/check-deployment-scope.sh` - Preview deployment scope before pushing
- `./scripts/safe-push.sh` - Automated workflow conflict prevention
- `./scripts/check-workflow.sh` - Quick workflow status check

## Key Implementation Patterns

### Pause/Resume Execution
Uses Step Functions `waitForTaskToken` callback pattern for wave-by-wave execution control.

### Real-Time Polling
- Frontend polls every 3 seconds for active executions
- EventBridge triggers execution-finder every 1 minute
- DRS job status polled until LAUNCHED or FAILED

### Enhanced Wave Progress UI
- Wave-aware server status display ensures consistency
- Expandable sections for servers and DRS job events
- Professional AWS CloudScape design system integration
- Real-time status updates with 3-second polling

### API-First Design
- REST API via API Gateway with Cognito JWT authentication
- Lambda functions handle all business logic
- Complete CRUD operations with validation and error handling
- Every UI function has corresponding API endpoint for automation

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

## Directory Structure

```text
AWS-DRS-Orchestration/
├── .github/                      # GitHub Actions CI/CD workflows
│   └── workflows/deploy.yml      # Main deployment workflow
├── .kiro/                        # Kiro AI assistant configuration
│   ├── settings/mcp.json         # MCP server configurations
│   └── steering/                 # AI steering documents
├── cfn/                          # CloudFormation Infrastructure as Code (15+ templates)
│   ├── master-template.yaml      # Root orchestrator for nested stacks
│   └── github-oidc-stack.yaml    # GitHub Actions OIDC integration
├── frontend/                     # React + CloudScape UI (32+ components, 7 pages)
├── lambda/                       # Python Lambda functions (7 active functions)
├── scripts/                      # Deployment and automation scripts
├── tests/                        # Python unit/integration tests
└── docs/                         # Comprehensive documentation (40+ files)
```

## Current System Status

- ✅ **All Systems Operational**: Stack, API, Frontend, Authentication working perfectly
- ✅ **Enhanced UI**: Wave progress display with consistent server status icons
- ✅ **Execution Polling**: Real-time updates and status synchronization working
- ✅ **CI/CD Pipeline**: GitHub Actions deployment with intelligent optimization
- ✅ **Security**: Comprehensive security scanning and RBAC implementation
- ✅ **Documentation**: Up-to-date requirements and implementation guides
- ✅ **Production Ready**: Enterprise-grade reliability and consistency

## Development Guidelines

1. **ALWAYS use GitHub Actions CI/CD pipeline** for deployments
2. **Use safe-push.sh script** to prevent workflow conflicts
3. **Check deployment scope** before pushing changes
4. **Follow AWS CloudScape Design System** for frontend development
5. **Maintain wave-aware status consistency** in UI components
6. **Use current stack configuration** for all development and testing
7. **Take historian snapshots** for major milestones and achievements