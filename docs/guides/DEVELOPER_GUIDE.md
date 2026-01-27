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
export PROJECT_NAME=aws-drs-orch
export STACK_NAME=aws-drs-orch-dev
export PARENT_STACK_NAME=aws-drs-orch-dev

# AWS Configuration
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=<your-account-id>
export DEPLOYMENT_BUCKET=aws-drs-orch-dev
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
- Always use `aws-drs-orch-dev` stack for development (NEVER `aws-elasticdrs-orchestrator-test`)

### Frontend Configuration (CRITICAL)

The `frontend/public/aws-config.json` file contains environment-specific Cognito and API Gateway values. **This file is gitignored and must NOT be committed.**

**Why this matters:**
- `aws-config.json` contains stack-specific values (UserPoolId, UserPoolClientId, ApiEndpoint)
- Committing old values causes "User pool client does not exist" errors after stack updates
- GitHub Actions generates this file fresh from CloudFormation outputs during deployment

**Local Development Setup:**
```bash
# Get current values from your deployed stack
STACK_NAME="aws-elasticdrs-orchestrator-{environment}"

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

### Local CI/CD Pipeline (No External Dependencies)

The project includes a complete local CI/CD pipeline that mirrors GitHub Actions, requiring no external services like GitHub, GitLab, or CodePipeline.

#### Testing the Local CI/CD Pipeline

**Quick Test:**
```bash
# 1. Make a small change
echo "# Test change" >> README.md

# 2. Commit the change
git add README.md
git commit -m "test: verify local CI/CD pipeline"

# 3. Run safe push (full pipeline)
./scripts/safe-push.sh
```

**What You'll See:**

Stage 1: Validation (Real-time Output)
```
═══════════════════════════════════════════════════════════
  STAGE 1: VALIDATION
═══════════════════════════════════════════════════════════

[1.1] CloudFormation Template Validation
✓ cfn-lint: All templates valid
✓ AWS CloudFormation: All templates valid

[1.2] Python Code Quality
✓ flake8: No issues found
✓ black: Code is formatted correctly
✓ isort: Imports are sorted correctly

[1.3] Frontend Code Quality
✓ TypeScript: No type errors
✓ ESLint: No critical issues

[1.4] CloudScape Design System Compliance
✓ CloudScape: Compliant

[1.5] CamelCase Consistency Validation
✓ CamelCase: Consistent

[1.6] API Gateway Architecture Validation
✓ API Architecture: Valid
```

Stage 2: Security Scans
```
═══════════════════════════════════════════════════════════
  STAGE 2: SECURITY SCANS
═══════════════════════════════════════════════════════════

[2.1] Python Security Scanning (Bandit)
✓ Bandit: No high severity issues

[2.2] Python Security Scanning (Semgrep)
✓ Semgrep: Scan complete

[2.3] Python Dependency Vulnerability Scan (Safety)
✓ Safety: Scan complete

[2.4] Frontend Security Scanning (NPM Audit)
✓ NPM Audit: No critical vulnerabilities

[2.5] Infrastructure Security Scanning
✓ Semgrep CFN: Scan complete

[2.6] Security Summary
✓ Security thresholds: PASSED
```

Stage 3: Tests
```
═══════════════════════════════════════════════════════════
  STAGE 3: TESTS
═══════════════════════════════════════════════════════════

[3.1] Python Unit Tests
✓ Python unit tests: PASSED

[3.2] Frontend Tests
✓ Frontend tests: PASSED
```

Stage 4: Build
```
═══════════════════════════════════════════════════════════
  BUILD STAGE
═══════════════════════════════════════════════════════════

Building Lambda packages...
✓ Lambda packages built successfully

Package sizes:
  build/lambda/api-handler.zip: 93.2 KB
  build/lambda/execution-finder.zip: 10.1 KB
  build/lambda/execution-poller.zip: 4.2 KB
  build/lambda/bucket-cleaner.zip: 7.3 KB
  build/lambda/notification-formatter.zip: 2.1 KB
  build/lambda/orchestration-stepfunctions.zip: 4.5 KB
  build/lambda/frontend-builder.zip: 1.3 MB
```

Pipeline Summary
```
═══════════════════════════════════════════════════════════
  PIPELINE SUMMARY
═══════════════════════════════════════════════════════════

✅ Local CI/CD pipeline completed successfully
Duration: 45s

Pipeline stages completed:
  ✅ Validation (CloudFormation, Python, Frontend, CloudScape)
  ✅ Security Scan (Bandit, Semgrep, Safety, NPM Audit)
  ✅ Build (Lambda packages, Frontend validation)
  ✅ Test (Python unit tests, Frontend tests)

📊 Reports available in: docs/logs/latest/
```

**Testing Different Modes:**

Full Pipeline (Recommended):
```bash
./scripts/safe-push.sh
```
Duration: ~45-60 seconds | Runs: All validation, security, tests, build

Quick Mode (Fast Iteration):
```bash
./scripts/safe-push.sh --quick
```
Duration: ~15-20 seconds | Runs: Validation and build only (skips security and tests)

Force Mode (Emergency Only):
```bash
./scripts/safe-push.sh --force
```
Duration: ~2 seconds | Runs: Nothing - immediate push (NOT RECOMMENDED)

**Monitoring Progress:**

The pipeline provides real-time console output with:
- ✅ Green checkmarks for passed stages
- ❌ Red X marks for failed stages
- ⚠️ Yellow warnings for skipped stages
- 📊 Progress indicators
- ⏱️ Duration tracking

**Detailed Reports:**

After each run, check the `docs/logs/latest/` directory:
```bash
# View validation reports
cat docs/logs/latest/validation/flake8.txt
cat docs/logs/latest/validation/eslint.txt

# View security reports
cat docs/logs/latest/security/summary.txt
cat docs/logs/latest/security/thresholds.txt

# View test reports
cat docs/logs/latest/tests/python-unit.txt
cat docs/logs/latest/tests/frontend.txt
```

**Handling Failures:**

Validation Failure:
```bash
# 1. Check the specific report
cat reports/validation/flake8.txt

# 2. Fix the issues in your code

# 3. Re-run
./scripts/safe-push.sh
```

Security Failure:
```bash
# 1. Check security summary
cat reports/security/summary.txt
cat reports/security/thresholds.txt

# 2. Fix critical/high severity issues

# 3. Re-run
./scripts/safe-push.sh
```

Test Failure:
```bash
# 1. Check test output
cat reports/tests/python-unit.txt

# 2. Fix failing tests

# 3. Re-run
./scripts/safe-push.sh
```

**Performance Benchmarks:**

| Mode | Duration | Stages |
|------|----------|--------|
| Full | 45-60s | All stages |
| Quick | 15-20s | Validation + Build |
| Force | 2s | None (immediate push) |

**Best Practices:**
1. Always use full pipeline for production code: `./scripts/safe-push.sh`
2. Use quick mode for rapid iteration during development: `./scripts/safe-push.sh --quick`
3. Never use force mode unless emergency: `./scripts/safe-push.sh --force`
4. Check reports after failures: `cat reports/validation/*.txt`
5. Clean up reports periodically: `rm -rf reports/`

#### Full Local Deployment

```bash
# Source environment configuration
source .env.dev

# Run full CI/CD pipeline: Validate → Security → Build → Test → Deploy
./scripts/local-deploy.sh dev full

# Quick deployment (skip validation for faster iteration)
./scripts/local-deploy.sh dev full --quick
```

#### Local CI Checks Only (No Deployment)

```bash
# Full validation pipeline
./scripts/local-ci-checks.sh

# Quick validation (skip tests and security)
./scripts/local-ci-checks.sh --quick

# Skip only tests
./scripts/local-ci-checks.sh --skip-tests

# Skip only security scans
./scripts/local-ci-checks.sh --skip-security
```

#### Fast Deployment Options

```bash
# Lambda-only update (~5 seconds)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Frontend-only deployment
./scripts/local-deploy.sh dev frontend-only

# CloudFormation deployment only
./scripts/sync-to-deployment-bucket.sh --deploy-cfn

# Sync to S3 with validation
./scripts/sync-to-deployment-bucket.sh --validate
```

### Local CI/CD Stages

| Stage | Duration | Tools Used |
|-------|----------|------------|
| **Validation** | ~2 min | cfn-lint, flake8, black, isort, TypeScript, ESLint |
| **Security** | ~2 min | Bandit, Semgrep, Safety, NPM Audit |
| **Build** | ~3 min | Lambda packaging (FrontendBuilder handles frontend) |
| **Test** | ~2 min | pytest, vitest |
| **Deploy** | ~10 min | CloudFormation |

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

### GitHub Actions CI/CD (Optional)

For repositories hosted on GitHub with OIDC authentication:

```bash
# Check workflow status before pushing (optional but recommended)
./scripts/check-workflow.sh && git push

# OR use the safe push script (RECOMMENDED)
./scripts/safe-push.sh

# Monitor deployment at GitHub Actions page
```

**Workflow Behavior**:
1. **First push** triggers workflow → starts running
2. **Second push** triggers workflow → **automatically queued** (waits for first)
3. **Third push** triggers workflow → **automatically queued** (waits for second)
4. Workflows run sequentially, never overlapping

### FrontendBuilder Lambda (100% CloudFormation Deployment)

The solution uses a **FrontendBuilder Lambda Custom Resource** that eliminates the need for external CI/CD for frontend deployment:

**How It Works:**
1. Lambda package includes pre-built `frontend/dist/` folder
2. During CloudFormation deployment, FrontendBuilder:
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

### Emergency Manual Deployment (RESTRICTED)

**ONLY use manual deployment for:**
- CI/CD service outage (confirmed issue)
- Critical production hotfix when pipeline is broken
- Pipeline debugging (with immediate Git follow-up)

```bash
# EMERGENCY ONLY: Fast Lambda code update
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# IMMEDIATELY follow up with proper Git commit
git add .
git commit -m "emergency: describe the critical fix"
git push  # Restores proper CI/CD tracking
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

# Use sync script for deployment (recommended)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code
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
s3://aws-elasticdrs-orchestrator/
├── cfn/                          # CloudFormation templates
├── lambda/                       # Lambda deployment packages (7 functions)
│   ├── api-handler.zip
│   ├── orchestration-stepfunctions.zip
│   ├── execution-finder.zip
│   ├── execution-poller.zip
│   ├── frontend-builder.zip
│   ├── bucket-cleaner.zip
│   └── notification-formatter.zip
├── frontend/                     # Frontend build artifacts
└── scripts/                      # Deployment scripts
```

### Deployment Verification

After deployment, verify the correct resources are updated:

```bash
# Check CloudFront URL matches your environment
aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-{environment} \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text

# Verify Lambda function was updated
aws lambda get-function \
  --function-name aws-elasticdrs-orchestrator-api-handler-{environment} \
  --query 'Configuration.LastModified' \
  --output text

# Check API Gateway endpoint
curl https://{api-id}.execute-api.{region}.amazonaws.com/{environment}/health

# Verify all Lambda functions are deployed
for func in api-handler orchestration-stepfunctions execution-finder execution-poller frontend-builder bucket-cleaner notification-formatter; do
  echo "Checking aws-elasticdrs-orchestrator-${func}-{environment}..."
  aws lambda get-function --function-name aws-elasticdrs-orchestrator-${func}-{environment} --query 'Configuration.LastModified' --output text
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
| Lambda deployment fails | Code not synced to S3 | Run sync script first |
| Frontend not updating | CloudFront cache | Run with `--deploy-frontend` |
| Permission errors | Wrong AWS profile | Use `--profile` option |
| "User pool client does not exist" | Stale `aws-config.json` | Regenerate from stack outputs |
| CORS 403 errors | API Gateway not redeployed | Run `scripts/redeploy-api-gateway.sh` |

### Fixing "User pool client does not exist" Error

This error occurs when `aws-config.json` contains old Cognito values from a previous stack deployment.

**Solution:**
```bash
# Regenerate aws-config.json from current stack
STACK_NAME="aws-elasticdrs-orchestrator-{environment}"

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
cd frontend && npm run build && cd ..
./scripts/sync-to-deployment-bucket.sh --deploy-frontend
```

**Prevention:**
- `frontend/public/aws-config.json` is gitignored - never commit it
- GitHub Actions generates this file fresh from CloudFormation outputs
- The sync script excludes `aws-config.json` and regenerates it from stack outputs

### Fixing CORS 403 Errors

If OPTIONS requests return 403 instead of 200, the API Gateway deployment may not have been applied to the stage.

**Solution:**
```bash
# Redeploy API Gateway
./scripts/redeploy-api-gateway.sh aws-elasticdrs-orchestrator-{environment} {region}
```

This script:
1. Gets the API ID from CloudFormation outputs
2. Creates a new API Gateway deployment
3. Verifies OPTIONS endpoints return 200

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
8. **Use GitHub Actions**: Always use CI/CD pipeline for deployments
9. **Check workflow status**: Use safe-push script to avoid conflicts
10. **Never commit aws-config.json**: This file is environment-specific

---

## References

- [API and Integration Guide](API_AND_INTEGRATION_GUIDE.md)
- [Deployment and Operations Guide](DEPLOYMENT_AND_OPERATIONS_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING_GUIDE.md)
- [GitHub Actions CI/CD Guide](deployment/GITHUB_ACTIONS_CICD_GUIDE.md)
