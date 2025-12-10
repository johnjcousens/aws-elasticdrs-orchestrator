# AWS DRS Orchestration - Solution Handoff Guide

**Enterprise Disaster Recovery Orchestration Platform**  
*Handoff Date: December 2024*  
*Version: MVP Production-Ready*

## Executive Summary

This document provides everything needed to continue development of the AWS DRS Orchestration solution using Amazon Q Developer and modern AI-assisted development practices. The solution is a production-ready, serverless disaster recovery orchestration platform built on AWS native services.

**Key Metrics:**
- **Cost**: $12-40/month operational cost
- **Scale**: Supports 300+ servers across 30 AWS regions
- **Architecture**: 100% serverless with Infrastructure as Code
- **Status**: MVP complete with comprehensive testing and documentation

---

## 🏗️ Infrastructure Overview

### Architecture Components

| Layer | Technology | Location | Purpose |
|-------|------------|----------|---------|
| **Frontend** | React 19.1 + CloudScape | `frontend/` | User interface and authentication |
| **API** | API Gateway + Cognito | `cfn/api-stack.yaml` | REST API and user management |
| **Compute** | Lambda + Step Functions | `lambda/` + `cfn/step-functions-stack.yaml` | Business logic and orchestration |
| **Data** | DynamoDB | `cfn/database-stack.yaml` | Protection groups, plans, execution history |
| **Hosting** | S3 + CloudFront | `cfn/frontend-stack.yaml` | Static website hosting and CDN |
| **DR Service** | AWS DRS Integration | `lambda/index.py` | Disaster recovery operations |

### CloudFormation Stack Architecture

```
master-template.yaml (Root)
├── database-stack.yaml      # 3 DynamoDB tables
├── lambda-stack.yaml        # 5 Lambda functions + IAM
├── api-stack.yaml          # API Gateway + Cognito
├── step-functions-stack.yaml # Orchestration engine
├── security-stack.yaml     # Optional WAF + CloudTrail
└── frontend-stack.yaml     # S3 + CloudFront
```

**Deployment Bucket**: `s3://aws-drs-orchestration` (source of truth for all deployments)

---

## 🚀 Quick Start for New Developers

### 1. Environment Setup

```bash
# Clone repository
git clone <your-repo-url>
cd AWS-DRS-Orchestration

# Install frontend dependencies
cd frontend && npm install

# Install Python dependencies for testing
cd ../tests/python && pip install -r requirements.txt
```

### 2. Deploy Infrastructure

```bash
# Sync code to S3 deployment bucket
./scripts/sync-to-deployment-bucket.sh

# Deploy complete infrastructure
./scripts/sync-to-deployment-bucket.sh --deploy-cfn

# Create admin user
./scripts/create-test-user.sh
```

### 3. Verify Deployment

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name drs-orchestration-dev --region us-east-1

# Test frontend
# URL from CloudFormation outputs: CloudFrontUrl
```

---

## 🛠️ Development Workflow

### Core Development Rules

#### **CRITICAL: Always Follow CI/CD Workflow**

```bash
# 1. Make code changes
# 2. ALWAYS sync to S3 first
./scripts/sync-to-deployment-bucket.sh

# 3. Deploy changes
./scripts/sync-to-deployment-bucket.sh --update-lambda-code  # Fast (~5s)
./scripts/sync-to-deployment-bucket.sh --deploy-cfn         # Full (5-10min)

# 4. Verify S3 has latest
aws s3 ls s3://aws-drs-orchestration/lambda/ --region us-east-1
```

**Why This Matters**: S3 bucket is the source of truth. If you skip sync, you lose the ability to redeploy from scratch.

### Frontend Development

#### Technology Stack
- **React 19.1** with TypeScript 5.9
- **CloudScape Design System 3.0** (AWS native components)
- **Vite 7.1** for build tooling
- **AWS Amplify 6.15** for authentication

#### Development Commands
```bash
cd frontend
npm run dev          # Development server (localhost:5173)
npm run build        # Production build
npm run test         # Unit tests with Vitest
npm run lint         # ESLint validation
```

#### Frontend Rules
1. **Use CloudScape components only** - No custom UI components
2. **TypeScript strict mode** - All components must be typed
3. **API client pattern** - Use `src/services/apiClient.ts` for all API calls
4. **Authentication flow** - Cognito JWT tokens via Amplify Auth
5. **Error handling** - Use toast notifications for user feedback

#### Key Files
- `src/App.tsx` - Main application with routing
- `src/services/apiClient.ts` - API communication layer
- `src/types/index.ts` - TypeScript type definitions
- `src/contexts/` - React contexts for auth and API state

### Backend Development

#### Lambda Functions (5 Active)
| Function | File | Purpose |
|----------|------|---------|
| `api-handler` | `lambda/index.py` | REST API endpoints |
| `orchestration-stepfunctions` | `lambda/orchestration_stepfunctions.py` | Step Functions orchestration |
| `execution-finder` | `lambda/poller/execution_finder.py` | EventBridge scheduled poller |
| `execution-poller` | `lambda/poller/execution_poller.py` | DRS job status updates |
| `frontend-builder` | `lambda/build_and_deploy.py` | CloudFormation custom resource |

#### Backend Rules
1. **Python 3.12** with type hints for all functions
2. **Error handling pattern** - Try-except with detailed logging
3. **DRS integration** - Trust LAUNCHED status, use job-based orchestration
4. **Data transformation** - Convert PascalCase (DynamoDB) to camelCase (frontend)
5. **Validation layers** - Required fields → Business logic → External systems

---

## 🤖 Amazon Q Developer Integration

### Recommended Amazon Q Rules

Create these files in `.amazonq/rules/` for consistent AI assistance:

#### 1. Development Workflow Rule
```markdown
# .amazonq/rules/development-workflow.md

## Development Workflow Requirements

### ALWAYS Follow This Sequence:
1. Make code changes
2. Sync to S3: `./scripts/sync-to-deployment-bucket.sh`
3. Deploy: `--update-lambda-code` (fast) or `--deploy-cfn` (full)
4. Verify S3 has latest artifacts

### NEVER:
- Deploy without syncing to S3 first
- Skip the verification step
- Make infrastructure changes without updating CloudFormation
```

#### 2. Code Quality Rule
```markdown
# .amazonq/rules/code-quality.md

## Code Quality Standards

### Python (Lambda):
- Type hints for all function parameters and returns
- Docstrings with Args, Returns, Examples
- Error handling with try-except and logging
- Use `response()` helper for API Gateway responses

### TypeScript (Frontend):
- Strict TypeScript mode
- CloudScape components only
- Interface definitions in `types/index.ts`
- Consistent error handling with toast notifications

### Testing:
- Unit tests for all business logic
- Mock AWS services in tests
- Comprehensive test coverage for critical paths
```

### Using Amazon Q for Development

#### File Editing with Context
```
# Include specific files for context
@lambda/index.py review this API endpoint for security issues

# Include entire directories
@frontend review the authentication flow

# Include documentation
@docs/guides/DEVELOPMENT_GUIDELINES.md help me understand the coding patterns
```

#### Git Operations
```
# Commit with context
@workspace generate a commit message for these changes

# Update documentation
@README.md update the changelog section with recent changes

# Project status updates
@docs/PROJECT_STATUS.md add completed feature: DRS service limits validation
```

#### Code Generation
```
# Generate with architectural context
@cfn/lambda-stack.yaml add a new Lambda function for DRS tag synchronization

# Frontend components
@frontend/src/components create a new CloudScape table component for DRS jobs

# API endpoints
@lambda/index.py add a new endpoint for DRS launch settings management
```

---

## 🔄 GitHub Enterprise CI/CD

### Recommended Pipeline Structure

#### 1. GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: AWS DRS Orchestration CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate CloudFormation
        run: make validate
      - name: TypeScript Check
        run: cd frontend && npm run type-check

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Python Tests
        run: cd tests/python && pytest
      - name: Frontend Tests
        run: cd frontend && npm test

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Lambda Packages
        run: make build-lambda
      - name: Build Frontend
        run: cd frontend && npm run build

  deploy-dev:
    if: github.ref == 'refs/heads/develop'
    needs: [validate, test, build]
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Development
        run: ./scripts/sync-to-deployment-bucket.sh --deploy-cfn
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

  deploy-prod:
    if: github.ref == 'refs/heads/main'
    needs: [validate, test, build]
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to Production
        run: ./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

#### 2. Branch Strategy
- `main` - Production deployments
- `develop` - Development environment
- `feature/*` - Feature branches with PR reviews
- `hotfix/*` - Emergency production fixes

#### 3. Required Secrets
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN (if using temporary credentials)
```

---

## 📝 Documentation Maintenance

### Key Documents to Update

#### 1. README.md Updates
```bash
# Use Amazon Q to update changelog
@README.md add to changelog: "Added DRS service limits validation with 48 unit tests"

# Update architecture diagrams
@docs/architecture/ARCHITECTURE_DIAGRAMS.md update the mermaid diagram to include new component
```

#### 2. PROJECT_STATUS.md Updates
```markdown
# Template for status updates
## [Date] - [Feature Name]
**Status**: Complete/In Progress/Planned
**Description**: Brief description of changes
**Files Modified**: List of key files
**Testing**: Test coverage details
**Documentation**: Links to relevant docs
```

---

## 🧪 Testing Strategy

### Test Structure
```
tests/
├── python/
│   ├── unit/           # Lambda function unit tests
│   ├── integration/    # AWS service integration tests
│   └── e2e/           # End-to-end API tests
└── playwright/         # Frontend E2E tests
    ├── page-objects/
    └── smoke-tests.spec.ts
```

### Running Tests
```bash
# Python unit tests
cd tests/python && pytest unit/ -v

# Frontend unit tests
cd frontend && npm test

# E2E tests
cd tests/playwright && npx playwright test

# Coverage reports
pytest --cov=lambda --cov-report=html
```

---

## 🔧 Common Development Tasks

### Adding a New API Endpoint

1. **Update Lambda function** (`lambda/index.py`):
```python
def handle_new_endpoint(event: Dict) -> Dict:
    """Handle new endpoint request"""
    try:
        # Implementation
        return response(200, result)
    except Exception as e:
        return response(500, {'error': str(e)})

# Add to router
if path == '/new-endpoint' and method == 'POST':
    return handle_new_endpoint(event)
```

2. **Update API Gateway** (`cfn/api-stack.yaml`):
```yaml
NewEndpointResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    ParentId: !Ref ApiGatewayRootResource
    PathPart: new-endpoint
    RestApiId: !Ref ApiGateway
```

3. **Update frontend API client** (`frontend/src/services/apiClient.ts`):
```typescript
export const newEndpoint = async (data: NewEndpointRequest): Promise<NewEndpointResponse> => {
  const response = await apiClient.post('/new-endpoint', data);
  return response.data;
};
```

4. **Deploy**:
```bash
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

---

## 🚨 Troubleshooting Guide

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `PG_NAME_EXISTS` | Duplicate protection group name | Use unique name |
| `INVALID_SERVER_IDS` | Server IDs not found in DRS | Verify with `aws drs describe-source-servers` |
| `CIRCULAR_DEPENDENCY` | Wave dependencies form loop | Review dependency chain |
| `UnauthorizedOperation` | Missing IAM permissions | Check OrchestrationRole permissions |
| Frontend auth fails | Wrong `aws-config.js` format | Use `Auth.Cognito.userPoolClientId` not `cognito.clientId` |

### Debug Commands
```bash
# Check CloudFormation stack
aws cloudformation describe-stacks --stack-name drs-orchestration-dev

# View Lambda logs
aws logs tail /aws/lambda/drs-orchestration-api-handler-dev --follow

# Check S3 sync status
aws s3 ls s3://aws-drs-orchestration/lambda/ --region us-east-1

# Validate CloudFormation templates
make validate
```

---

## 📋 Development Checklist

### Before Starting Development
- [ ] Repository cloned and dependencies installed
- [ ] AWS credentials configured
- [ ] Infrastructure deployed and verified
- [ ] Amazon Q rules configured in `.amazonq/rules/`
- [ ] Test environment accessible

### For Each Feature
- [ ] Implementation plan created in `docs/implementation/`
- [ ] Code changes made following architectural patterns
- [ ] Unit tests written and passing
- [ ] Integration tests updated
- [ ] Documentation updated
- [ ] Synced to S3 deployment bucket
- [ ] Deployed and verified
- [ ] PROJECT_STATUS.md updated

### Before Production Release
- [ ] Full test suite passing
- [ ] Security review completed
- [ ] Performance testing done
- [ ] Documentation complete
- [ ] Deployment verified in staging
- [ ] Rollback plan prepared

---

## 🎯 Next Steps & Roadmap

### Immediate Priorities (Next 30 Days)
1. **CodeBuild Migration** - Move from GitLab to AWS-native CI/CD
2. **DRS Launch Settings** - UI for configuring EC2 launch templates
3. **Multi-Account Support** - Scale beyond 300 servers

### Medium Term (3-6 Months)
4. **SSM Automation Integration** - Pre/post-wave automation
5. **Step Functions Visualization** - Real-time state machine UI
6. **DRS Tag Synchronization** - Automated EC2 tag sync

### Implementation Plans Available
All features have detailed implementation plans in `docs/implementation/`:
- `CODEBUILD_CODECOMMIT_MIGRATION_PLAN.md`
- `DRS_LAUNCH_SETTINGS_IMPLEMENTATION_PLAN.md`
- `MULTI_ACCOUNT_DRS_IMPLEMENTATION.md`
- `SSM_AUTOMATION_IMPLEMENTATION.md`
- `STEP_FUNCTIONS_VISUALIZATION_IMPLEMENTATION.md`
- `DRS_TAG_SYNC_IMPLEMENTATION_PLAN.md`

---

## 📞 Support & Resources

### Documentation Index
- **Architecture**: `docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md`
- **Deployment**: `docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md`
- **API Reference**: `docs/guides/AWS_DRS_API_REFERENCE.md`
- **Testing**: `docs/guides/TESTING_AND_QUALITY_ASSURANCE.md`
- **Troubleshooting**: `docs/troubleshooting/`

### Key Commands Reference
```bash
# Development
./scripts/sync-to-deployment-bucket.sh                    # Sync all
./scripts/sync-to-deployment-bucket.sh --update-lambda-code  # Fast update
./scripts/sync-to-deployment-bucket.sh --deploy-cfn       # Full deploy

# Testing
cd tests/python && pytest unit/ -v                        # Python tests
cd frontend && npm test                                    # Frontend tests
cd tests/playwright && npx playwright test                # E2E tests

# Validation
make validate                                              # CloudFormation
make lint                                                  # Code quality
```

### Amazon Q Usage Tips
- Use `@workspace` for broad context
- Use `@filename` for specific file context
- Use `@docs/` for documentation context
- Always include architectural constraints in prompts
- Reference existing patterns when requesting new features

---

**This solution is production-ready and fully documented. Continue development with confidence using Amazon Q Developer and the established patterns.**

*For questions or clarification, refer to the comprehensive documentation in the `docs/` directory.*