<!-- Copyright Amazon.com and Affiliates. All rights reserved.
     This deliverable is considered Developed Content as defined in the AWS Service Terms. -->

# Developer Guide

**Version**: 3.0  
**Date**: January 15, 2026  
**Status**: Production Ready

Complete guide for developing, testing, and deploying the AWS DRS Orchestration Solution.

---

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Local Development](#local-development)
3. [Development Workflow](#development-workflow)
4. [Testing](#testing)
5. [Deployment](#deployment)
6. [Troubleshooting](#troubleshooting)

---

## Development Environment Setup

### Prerequisites

- AWS Account with DRS configured and source servers replicating
- AWS CLI v2 configured with appropriate permissions
- Node.js 18+ and npm for frontend development
- Python 3.12+ for Lambda development
- S3 bucket for deployment artifacts

### Required Python Tools (for Local CI/CD)

```bash
# Install all development tools
pip install cfn-lint flake8 black isort bandit safety semgrep pytest pytest-cov moto

# Or use requirements file
pip install -r requirements-dev.txt
```

### Security Scanning Tools

The deployment pipeline includes comprehensive security scanning:

**Python Tools** (install in virtual environment):
```bash
source .venv/bin/activate
pip install bandit detect-secrets
```

**Ruby Tool** (cfn_nag for CloudFormation security):
```bash
# macOS
gem install cfn-nag

# Known Issue: cfn_nag has compatibility issues with Ruby 4.0
# Workaround: Use Ruby 3.x or skip cfn_nag (non-blocking)
brew install ruby@3.3
export PATH="/opt/homebrew/opt/ruby@3.3/bin:$PATH"
gem install cfn-nag
```

**Shell Script Linter**:
```bash
# macOS
brew install shellcheck

# Linux
sudo apt-get install shellcheck
```

**Frontend Security** (already included with Node.js):
- npm audit (included with npm)

**Verification**:
```bash
bandit --version
cfn_nag_scan --version
detect-secrets --version
shellcheck --version
npm --version
```

**Security Scan Coverage**:

| Tool | Scans | Detects |
|------|-------|---------|
| bandit | Python Lambda functions | SQL injection, hardcoded passwords, insecure functions |
| cfn_nag | CloudFormation templates | IAM misconfigurations, encryption gaps, security groups |
| detect-secrets | All files | Hardcoded credentials, API keys, tokens |
| shellcheck | Bash scripts | Script errors, security issues, best practices |
| npm audit | Frontend dependencies | Known CVEs in npm packages |

**Configuration Files**:
- `.cfn_nag_deny_list.yml` - Suppresses specific cfn_nag rules with justification
- `.secrets.baseline` - Baseline for detect-secrets to track known false positives

**Manual Security Scans**:
```bash
# Python SAST
bandit -r lambda/ -ll

# CloudFormation security
cfn_nag_scan --input-path cfn/

# Secrets detection
detect-secrets scan

# Shell script security
shellcheck scripts/*.sh

# Frontend dependencies
cd frontend && npm audit
```

### Virtual Environment Setup

Using a virtual environment ensures isolated dependencies and consistent tool versions.

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements-dev.txt

# Install botocore CRT extension (required for latest boto3)
pip install "botocore[crt]"
```

**Why Virtual Environment?**
- **Isolated dependencies**: Avoids conflicts with system Python packages
- **Latest versions**: Uses boto3 1.42.33, moto 5.1.20 (vs system's 1.34.34, 5.0.0)
- **Clean testing**: Zero deprecation warnings (vs 159 warnings with old versions)
- **Reproducible**: Exact versions specified in requirements-dev.txt

**Test Results:**
- With virtual environment: ✅ 687 unit tests pass (0 warnings), ✅ 84 integration tests pass (0 warnings)
- Without virtual environment: ✅ 687 unit tests pass (0 warnings), ⚠️ 84 integration tests pass (159 botocore deprecation warnings)

**Current Versions:**
- boto3: 1.42.33 (January 2026)
- botocore: 1.42.33 (January 2026)
- moto: 5.1.20 (January 2026)
- pytest: 8.0.0
- pytest-cov: 4.1.0

**Notes:**
- The `.venv/` directory is gitignored
- Lambda runtime provides boto3 automatically (not included in deployment packages)
- Virtual environment is only for local development and testing
- Deactivate with: `deactivate`

### Repository Setup

```bash
# Clone repository
git clone <repository-url>
cd infra/orchestration/drs-orchestration

# Setup environment configuration
cp .env.dev.template .env.dev
# Edit .env.dev with your configuration (see Environment Configuration below)

# Source environment variables
source .env.dev

# Frontend setup
cd frontend
npm install

# Backend setup (for testing)
cd ../tests/python
pip install -r requirements.txt
```

### Environment Configuration

The `.env.dev.template` file provides all required environment variables:

```bash
# AWS DRS Orchestration - Dev Environment Configuration
export ENVIRONMENT=dev
export PROJECT_NAME=aws-drs-orchestration
export STACK_NAME=aws-drs-orchestration-dev
export PARENT_STACK_NAME=aws-drs-orchestration-dev

# AWS Configuration
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=<your-account-id>
export DEPLOYMENT_BUCKET=aws-drs-orchestration-dev
export DEPLOYMENT_REGION=us-east-1

# Admin Configuration
export ADMIN_EMAIL=your-email@example.com

# Security Thresholds (for local CI/CD)
export SECURITY_THRESHOLD_CRITICAL=0
export SECURITY_THRESHOLD_HIGH=10
export SECURITY_THRESHOLD_TOTAL=50
```

**Important**: 
- `.env.dev` is gitignored and should NOT be committed
- Always use `aws-drs-orchestration-dev` stack for development (NEVER `aws-drs-orchestration-dev`)

### Frontend Configuration (CRITICAL)

The `frontend/public/aws-config.json` file contains environment-specific Cognito and API Gateway values. **This file is gitignored and must NOT be committed.**

**Why this matters:**
- `aws-config.json` contains stack-specific values (UserPoolId, UserPoolClientId, ApiEndpoint)
- Committing old values causes "User pool client does not exist" errors after stack updates
- GitHub Actions generates this file fresh from CloudFormation outputs during deployment

**Local Development Setup:**
```bash
# Get current values from your deployed stack
STACK_NAME="aws-drs-orchestration-{environment}"

# Create local aws-config.json from stack outputs
cat > frontend/public/aws-config.json << EOF
{
  "region": "{region}",
  "userPoolId": "$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)",
  "userPoolClientId": "$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' --output text)",
  "identityPoolId": "$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`IdentityPoolId`].OutputValue' --output text)",
  "apiEndpoint": "$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)"
}
EOF
```

**Reference template:** See `frontend/public/aws-config.template.json` for the expected structure.

---

## Local Development

### Quick Start

```bash
# Start both mock API server and frontend dev server
./start-local-dev.sh
```

This will:
- Install dependencies if needed
- Start mock API server on `http://localhost:8000`
- Start frontend dev server on `http://localhost:5173`
- Display available endpoints and usage instructions

### Access the Application

Open your browser to: **http://localhost:5173**

The application will automatically:
- Use local configuration (`aws-config.local.json`)
- Bypass Cognito authentication
- Connect to the mock API server
- Show you as logged in with mock user credentials

### Local Development Components

**Mock API Server** (`mock-api-server.js`):
- Express.js server with CORS enabled
- Mock authentication middleware
- Full target accounts CRUD API
- DRS quotas and tag sync endpoints
- Request/response logging

**Frontend Dev Server**:
- React app with Vite dev server
- Hot module replacement
- Automatic authentication bypass for localhost

### Available Endpoints

**Target Accounts Management**:
- `GET /accounts/targets` - List all target accounts
- `POST /accounts/targets` - Create new target account
- `PUT /accounts/targets/:id` - Update target account
- `DELETE /accounts/targets/:id` - Delete target account
- `POST /accounts/targets/:id/validate` - Validate target account

**DRS Operations**:
- `GET /drs/quotas?accountId=:id` - Get DRS quotas for account
- `POST /drs/tag-sync` - Trigger tag synchronization

**Health Check**:
- `GET /health` - API server health status

### Testing Local Changes

```bash
# Test API endpoints directly
./test-local-api.sh

# Test individual endpoints
curl http://localhost:8000/health
curl -H "Authorization: Bearer test-token" http://localhost:8000/accounts/targets
```

### Stopping Development Environment

```bash
# Press Ctrl+C in the terminal running start-local-dev.sh

# Or manually kill processes
pkill -f "node mock-api-server.js"
pkill -f "vite"
```

### Benefits of Local Development

1. **Faster Iteration** - No AWS deployment delays
2. **Cost Savings** - No AWS resource usage during development
3. **Offline Development** - Works without internet connection
4. **Easy Debugging** - Full request/response logging
5. **Isolated Testing** - No impact on AWS resources
6. **CORS-Free** - No cross-origin issues

---

## Development Workflow

### Deployment Pipeline (`deploy-main-stack.sh`)

The project deploys through a single entrypoint, `./scripts/deploy-main-stack.sh`, which runs a 5-stage pipeline. No external CI service (GitHub Actions, GitLab, CodePipeline) is required to validate, scan, test, or deploy.

#### Running the Pipeline

```bash
# Full pipeline: validation, security, tests, git push, deploy
./scripts/deploy-main-stack.sh qa
```

The pipeline runs these stages in order. If a stage fails, the pipeline stops before deployment.

| Stage | Name | What it runs |
|-------|------|--------------|
| 1 | Validation | cfn-lint (against `cfn/`), flake8, black, TypeScript type-check |
| 2 | Security | cfn_nag, detect-secrets, npm audit, semgrep, pip-licenses, license-checker |
| 3 | Tests | pytest (`tests/unit/`), npm test |
| 4 | Git Push | `git push origin HEAD` |
| 5 | Deploy | Builds Lambda zips, syncs `cfn/` + `lambda/` to the S3 deployment bucket, deploys the CloudFormation main stack |

Review the deploy script output to see which stage failed and why.

#### Common Invocations

```bash
# Full pipeline (validate, scan, test, push, deploy)
./scripts/deploy-main-stack.sh qa

# Validation only, no deployment (stops before stage 5)
./scripts/deploy-main-stack.sh qa --validate-only

# Update Lambda functions only
./scripts/deploy-main-stack.sh qa --lambda-only

# Rebuild and deploy the frontend only
./scripts/deploy-main-stack.sh qa --frontend-only

# Skip the test stage for faster iteration
./scripts/deploy-main-stack.sh qa --skip-tests
```

Available flags: `--lambda-only`, `--frontend-only`, `--validate-only`, `--force`, `--full-tests`, `--skip-tests`, `--no-frontend`, `--use-function-specific-roles`, `--orchestration-role <arn>`.

#### Build Artifacts

Stage 5 builds the deployed Lambda packages and syncs them to the S3 deployment bucket. The deployed functions are:

```
data-management-handler
query-handler
execution-handler
dr-orchestration-stepfunction
frontend-deployer
```

`drs-agent-deployer` also has a code directory (DRS replication agent installation via SSM), but it is in development and not deployed by the main stack.

### Pipeline Stages

| Stage | Tools Used |
|-------|------------|
| **Validation** | cfn-lint, flake8, black, TypeScript type-check |
| **Security** | cfn_nag, detect-secrets, npm audit, semgrep, pip-licenses, license-checker |
| **Tests** | pytest, npm test |
| **Git Push** | `git push origin HEAD` |
| **Deploy** | Lambda packaging (frontend-deployer handles the frontend), S3 sync, CloudFormation |

### CI/CD Reports

All CI/CD runs generate detailed reports:

```
docs/logs/
├── latest/                 # Symlink to most recent run
└── runs/                   # All pipeline runs (timestamped)
    └── YYYYMMDD_HHMMSS/
        ├── run-metadata.txt
        ├── validation/     # CloudFormation, Python, Frontend
        ├── security/       # Bandit, Semgrep, Safety, NPM Audit
        ├── tests/          # Python unit tests, Frontend tests
        ├── build/          # Lambda packages
        └── deploy/         # CloudFormation deployment logs
```

**View latest reports:**
```bash
cat docs/logs/latest/validation/flake8.txt
cat docs/logs/latest/security/summary.txt
cat docs/logs/latest/tests/python-unit.txt
```

### Git Push and CI/CD

Stage 4 of the deploy script runs `git push origin HEAD`, so a normal `./scripts/deploy-main-stack.sh qa` run validates, scans, tests, pushes, and deploys in one command. If the repository has a GitHub Actions workflow configured, the push from stage 4 triggers it.

### frontend-deployer Lambda (CloudFormation-Driven Frontend Deployment)

The solution uses a **frontend-deployer Lambda custom resource** that eliminates the need for external CI/CD for frontend deployment:

**How It Works:**
1. Lambda package includes pre-built `frontend/dist/` folder
2. During CloudFormation deployment, frontend-deployer:
   - Copies pre-built dist to temp directory
   - Generates `aws-config.json` from stack outputs
   - Injects `aws-config.js` script tag into `index.html`
   - Uploads to S3 with proper cache headers
   - Invalidates CloudFront cache

**Benefits:**
- ✅ No npm/node required at deployment time
- ✅ Frontend config always matches stack outputs
- ✅ Single CloudFormation deploy handles everything
- ✅ Works without GitHub/GitLab/CodePipeline

### Fast Lambda-Only Updates

For rapid iteration on Lambda code without rebuilding the frontend, use the `--lambda-only` flag. The pipeline still runs validation, security, tests, and git push before deploying:

```bash
./scripts/deploy-main-stack.sh qa --lambda-only
```

### Development Commands

**Frontend Development**:
```bash
cd frontend
npm install                    # Install dependencies
npm run dev                    # Start dev server (http://localhost:5173)
npm run build                  # Production build
npm run preview                # Preview production build
npm run lint                   # ESLint validation
npm run type-check             # TypeScript validation
```

**Lambda Development**:
```bash
cd lambda
pip install -r requirements.txt

# Deploy Lambda code via the deploy script
./scripts/deploy-main-stack.sh qa --lambda-only
```

**CloudFormation Validation**:
```bash
make validate    # AWS validate-template
make lint        # cfn-lint validation
make all         # Complete validation pipeline
```

### Git Workflow

**Repository Snapshots & Rollback**:

The repository uses Git tags to mark significant milestones. View available tags:

```bash
git tag -l
```

**Create a New Tag**:
```bash
# Create annotated tag (recommended)
git tag -a my-tag-name -m "Description of this milestone"

# Push tag to remote
git push origin my-tag-name
```

**Rollback to a Tag**:
```bash
# View the repository at the tagged state
git checkout tag-name

# Create a new branch from tag for development
git checkout -b my-feature-branch tag-name

# Return to main branch
git checkout main
```

---

## Testing

### Test Infrastructure

```text
tests/
├── playwright/                    # End-to-end UI tests
│   ├── page-objects/              # Page object models
│   ├── smoke-tests.spec.ts        # Critical path tests
│   └── playwright.config.ts       # Playwright configuration
│
└── python/                        # Python tests
    ├── unit/                      # Unit tests
    ├── integration/               # Integration tests
    ├── fixtures/                  # Test data and fixtures
    ├── mocks/                     # Mock implementations
    ├── conftest.py                # Pytest configuration
    └── requirements.txt           # Test dependencies
```

### Python Unit Tests

**Framework**: pytest 7.4.3 with pytest-cov, pytest-mock, hypothesis

```bash
cd tests/python
pip install -r requirements.txt

# Run all unit tests
pytest unit/ -v

# Run with coverage
pytest unit/ -v --cov=../../lambda --cov-report=html --cov-report=term

# Run specific test file
pytest unit/test_recovery_plan_delete.py -v
```

### Python Integration Tests

```bash
cd tests/python

# Run integration tests
pytest integration/ -v

# Run with AWS credentials (for real service tests)
AWS_PROFILE=your-profile pytest integration/ -v
```

### End-to-End Tests (Playwright)

```bash
cd tests/playwright
npm install

# Run all tests
npx playwright test

# Run with UI mode
npx playwright test --ui

# Run specific test file
npx playwright test smoke-tests.spec.ts

# Debug mode
npx playwright test --debug

# View test report
npx playwright show-report
```

### CloudFormation Validation

```bash
# Using Makefile
make validate    # AWS CLI validation
make lint        # cfn-lint validation

# Direct commands
cfn-lint cfn/*.yaml --config-file .cfnlintrc.yaml

# Validate specific template
aws cloudformation validate-template --template-body file://cfn/master-template.yaml
```

### Code Quality Checks

**TypeScript Type Checking**:
```bash
cd frontend
npx tsc --noEmit
```

**Python Linting**:
```bash
cd lambda

# Pylint
pylint index.py --disable=C0114,C0115,C0116,R0903,W0613,C0103

# Flake8
flake8 index.py --max-line-length=120 --ignore=E203,W503,E501

# Black (formatting check)
black --check --line-length=120 index.py
```

**Frontend Linting**:
```bash
cd frontend
npm run lint
```

### Manual Testing Checklist

**Protection Groups**:
- [ ] Create Protection Group with valid name and region
- [ ] Verify duplicate name rejection (case-insensitive)
- [ ] Verify server assignment tracking
- [ ] Edit Protection Group (add/remove servers)
- [ ] Delete Protection Group
- [ ] Verify deletion blocked if used in Recovery Plan

**Recovery Plans**:
- [ ] Create Recovery Plan with waves
- [ ] Add multiple waves with dependencies
- [ ] Edit wave configuration
- [ ] Delete Recovery Plan
- [ ] Verify deletion blocked during active execution

**Executions**:
- [ ] Start Drill execution
- [ ] Monitor wave progress in real-time
- [ ] Verify execution history recorded
- [ ] View execution details
- [ ] Clear execution history (preserves active)

**DRS Integration**:
- [ ] Server discovery by region
- [ ] Server details display (hostname, IP, status)
- [ ] Recovery job initiation
- [ ] Job status polling
- [ ] Instance launch verification (LAUNCHED status)

---

## Deployment

### S3 Deployment Bucket Structure

The S3 bucket serves as the source of truth for all deployable artifacts:

```
s3://aws-drs-orchestration/
├── cfn/                          # CloudFormation templates
├── lambda/                       # Lambda deployment packages (5 deployed functions)
│   ├── data-management-handler.zip
│   ├── query-handler.zip
│   ├── execution-handler.zip
│   ├── dr-orchestration-stepfunction.zip
│   └── frontend-deployer.zip
├── frontend/                     # Frontend build artifacts
└── scripts/                      # Deployment scripts
```

`drs-agent-deployer` has a code directory (DRS replication agent installation via SSM) but is not deployed by the main stack.

### Deployment Verification

After deployment, verify the correct resources are updated:

```bash
# Check CloudFront URL matches your environment
aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-{environment} \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text

# Verify a Lambda function was updated
aws lambda get-function \
  --function-name aws-drs-orchestration-data-management-handler-{environment} \
  --query 'Configuration.LastModified' \
  --output text

# Check API Gateway endpoint
curl https://{api-id}.execute-api.{region}.amazonaws.com/{environment}/health

# Verify all deployed Lambda functions
for func in data-management-handler query-handler execution-handler dr-orchestration-stepfunction frontend-deployer; do
  echo "Checking aws-drs-orchestration-${func}-{environment}..."
  aws lambda get-function --function-name aws-drs-orchestration-${func}-{environment} --query 'Configuration.LastModified' --output text
done
```

### Makefile Targets

```bash
make help                      # Show all available targets
make install                   # Install validation tools
make validate                  # Validate CloudFormation templates
make lint                      # Run cfn-lint
make sync-s3                   # Sync to S3 deployment bucket
make sync-s3-dry-run          # Preview S3 sync
make deploy                    # Deploy CloudFormation stack
make deploy-lambda             # Deploy Lambda code only
make deploy-frontend           # Build and deploy frontend
make create-test-user          # Create Cognito test user
make test                      # Run E2E tests
make clean                     # Clean build artifacts
```

---

## Troubleshooting

### Common Development Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Lambda deployment fails | Code not deployed to S3 | Run `./scripts/deploy-main-stack.sh qa --lambda-only` |
| Frontend not updating | CloudFront cache | Run `./scripts/deploy-main-stack.sh qa --frontend-only` |
| Permission errors | Wrong AWS profile | Set `AWS_PROFILE` in the environment before deploying |
| "User pool client does not exist" | Stale `aws-config.json` | Regenerate from stack outputs |
| CORS 403 errors | API Gateway not redeployed | Re-run `./scripts/deploy-main-stack.sh qa` to redeploy the API Gateway stage |

### Fixing "User pool client does not exist" Error

This error occurs when `aws-config.json` contains old Cognito values from a previous stack deployment.

**Solution:**
```bash
# Regenerate aws-config.json from current stack
STACK_NAME="aws-drs-orchestration-{environment}"

cat > frontend/public/aws-config.json << EOF
{
  "region": "{region}",
  "userPoolId": "$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)",
  "userPoolClientId": "$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' --output text)",
  "identityPoolId": "$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`IdentityPoolId`].OutputValue' --output text)",
  "apiEndpoint": "$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)"
}
EOF

# Rebuild and redeploy frontend
./scripts/deploy-main-stack.sh qa --frontend-only
```

**Prevention:**
- `frontend/public/aws-config.json` is gitignored - never commit it
- The frontend-deployer custom resource regenerates this file fresh from CloudFormation outputs during deployment

### Fixing CORS 403 Errors

If OPTIONS requests return 403 instead of 200, the API Gateway deployment may not have been applied to the stage.

**Solution:**
```bash
# Redeploy the stack, which redeploys the API Gateway stage
./scripts/deploy-main-stack.sh qa
```

This re-syncs the API Gateway templates to S3 and redeploys the CloudFormation stack, creating a fresh API Gateway deployment so OPTIONS preflight endpoints return 200.

### Playwright Tests Fail

1. Check if the application is deployed and accessible
2. Verify test user credentials in `.env.test`
3. Check for UI changes that may have broken selectors
4. Run with `--debug` flag for step-by-step debugging
5. Check `tests/playwright/test-results/` for screenshots and traces

### Python Tests Fail

1. Verify dependencies: `pip install -r requirements.txt`
2. Check for missing environment variables
3. Run with verbose output: `pytest -v --tb=long`
4. Check moto version compatibility with boto3

### CloudFormation Validation Fails

1. Check cfn-lint output for specific errors
2. Verify resource references are valid
3. Check for circular dependencies
4. Review `.cfnlintrc.yaml` for ignored rules

### Build Fails

1. Check for TypeScript errors: `npx tsc --noEmit`
2. Check for missing dependencies: `npm install`
3. Clear cache: `rm -rf node_modules && npm install`
4. Check Node.js version (requires Node 18+)

---

## Best Practices

1. **Always sync before deploy**: Never deploy directly from local files
2. **Use S3 versioning**: Enables rollback to previous versions
3. **Tag deployments**: Use git commit hash as S3 object metadata
4. **Validate before deploy**: Run `make validate lint` before deploying
5. **Test in dev first**: Deploy to dev environment before production
6. **Monitor deployments**: Watch CloudFormation events during deployment
7. **Keep artifacts in sync**: Local code, S3 artifacts, and deployed resources should match
8. **Use the deploy script**: Always deploy through `./scripts/deploy-main-stack.sh`
9. **Run validation first**: Use `--validate-only` to catch issues before a full deploy
10. **Never commit aws-config.json**: This file is environment-specific

---

## References

- [API Development Quick Reference](API_DEVELOPMENT_QUICK_REFERENCE.md)
- [API Endpoints Reference](../reference/API_ENDPOINTS_CURRENT.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Deploy Main Stack Guide](../deployment/DEPLOY_MAIN_STACK_GUIDE.md)
- [Troubleshooting Guide](../troubleshooting/TROUBLESHOOTING_GUIDE.md)
- [CI/CD Guide](../deployment/CICD_GUIDE.md)
