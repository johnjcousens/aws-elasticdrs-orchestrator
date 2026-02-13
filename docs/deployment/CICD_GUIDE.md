# CI/CD Deployment Guide

Complete guide for deploying AWS DRS Orchestration using the local deploy.sh script with future CI/CD platform migration options.

## Table of Contents

1. [Current Deployment Method](#current-deployment-method)
2. [5-Stage Pipeline](#5-stage-pipeline)
3. [Development Workflow](#development-workflow)
4. [Deployment Options](#deployment-options)
5. [S3 Deployment Repository](#s3-deployment-repository)
6. [Future CI/CD Migration](#future-cicd-migration)
7. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

---

## Current Deployment Method

### Local Deploy Script (Primary)

All deployments use the unified `./scripts/deploy.sh` script that runs a complete 5-stage pipeline locally:

```bash
# From project directory with venv activated
cd infra/orchestration/drs-orchestration
source .venv/bin/activate
./scripts/deploy.sh dev
```

**Pipeline Features:**
- ✅ **Full Validation**: CloudFormation, Python, TypeScript quality checks
- ✅ **Security Scanning**: Bandit, cfn_nag, detect-secrets, npm audit
- ✅ **Automated Testing**: pytest (Python), vitest (frontend)
- ✅ **Git Tracking**: All changes committed and pushed
- ✅ **Stack Protection**: Prevents accidental production deployments
- ✅ **Concurrency Control**: Detects and prevents overlapping deployments

### Infrastructure

| Component | Value | Purpose |
|-----------|-------|---------|
| **Deploy Script** | `./scripts/deploy.sh` | Unified deployment orchestration |
| **Project Name** | `hrp-drs-tech-adapter` | Standardized project naming |
| **Environment** | `dev` | Current development environment |
| **Stack Name** | `hrp-drs-tech-adapter-dev` | Active CloudFormation stack |
| **Deployment Bucket** | `hrp-drs-tech-adapter-dev` | Artifact storage with versioning |
| **AWS Region** | `us-east-1` | Primary deployment region |
| **Protected Stacks** | `*-test`, `*elasticdrs*` | Production stacks (never touch) |

---

## 5-Stage Pipeline

All deployment methods (local, GitHub Actions, GitLab CI) follow the same 5-stage pipeline:

### Stage 1: Validation (~2 min)

**Code Quality:**
- `cfn-lint` - CloudFormation template validation
- `flake8` - Python linting
- `black` - Python formatting check
- TypeScript type checking

**What it catches:**
- CloudFormation syntax errors
- Python code style violations
- TypeScript type errors
- Template structure issues

### Stage 2: Security (~3 min)

**Security Tools:**
- `bandit` - Python security analysis (SAST)
- `cfn_nag` - CloudFormation security best practices
- `detect-secrets` - Credential scanning
- `shellcheck` - Shell script security (Lambda scripts only)
- `npm audit` - Frontend dependency vulnerabilities

**What it catches:**
- Hardcoded credentials
- SQL injection vulnerabilities
- Insecure CloudFormation configurations
- Known dependency vulnerabilities
- Shell script security issues

**Skip with --quick flag** (emergency only, requires approval)

### Stage 3: Tests (~2 min)

**Test Suites:**
- `pytest` - Python unit and integration tests
- `vitest` - Frontend component tests

**What it catches:**
- Regression bugs
- Breaking changes
- Integration failures
- Component rendering issues

**Skip with --quick flag** (emergency only, requires approval)

### Stage 4: Git Push (~10s)

**Git Operations:**
- Verify all changes committed
- Push to remote repository
- Create audit trail

**Skip with --skip-push flag** (local testing only)

### Stage 5: Deploy (~10-15 min)

**Deployment Steps:**
1. Build Lambda packages (7 functions)
2. Sync artifacts to S3 deployment bucket
3. Deploy CloudFormation stack
4. Update Lambda function code (if --lambda-only)
5. Rebuild and deploy frontend (if --frontend-only)

**Total Duration:** ~22 minutes for full deployment

---

## Development Workflow

### Standard Workflow (Required)

```bash
# 1. Activate virtual environment
cd infra/orchestration/drs-orchestration
source .venv/bin/activate

# 2. Make changes
vim lambda/api-handler/index.py

# 3. Commit changes
git add .
git commit -m "feat: describe your changes"

# 4. Deploy (runs full 5-stage pipeline)
./scripts/deploy.sh dev

# Monitor output for validation, security, test, and deployment results
```

### Workflow Variations

**Quick Development (Emergency Only)**:
```bash
# Skip security scans and tests (requires approval)
./scripts/deploy.sh dev --quick
```

**Lambda-Only Update**:
```bash
# Fast Lambda code update without CloudFormation
./scripts/deploy.sh dev --lambda-only
```

**Frontend-Only Update**:
```bash
# Rebuild and deploy frontend only
./scripts/deploy.sh dev --frontend-only
```

**Local Testing (No Push)**:
```bash
# Test deployment without pushing to git
./scripts/deploy.sh dev --skip-push
```

### Deployment Flexibility Options

The deploy script supports multiple deployment modes via flags:

**API-Only Deployment** (no frontend):
```bash
./scripts/deploy.sh dev --no-frontend
```

**HRP Integration** (use external orchestration role):
```bash
./scripts/deploy.sh dev --orchestration-role arn:aws:iam::123456789012:role/HRPRole
```

**Full HRP Integration** (API-only with external role):
```bash
./scripts/deploy.sh dev --no-frontend --orchestration-role arn:aws:iam::123456789012:role/HRPRole
```

---

## Deployment Options

### All Deployment Options

| Option | Command | Duration | Use Case |
|--------|---------|----------|----------|
| **Full Deployment** | `./scripts/deploy.sh dev` | ~22 min | Complete infrastructure, Lambda, and frontend |
| **Quick Deploy** | `./scripts/deploy.sh dev --quick` | ~15 min | Emergency only - skips security/tests |
| **Lambda Only** | `./scripts/deploy.sh dev --lambda-only` | ~2 min | Fast Lambda code updates |
| **Frontend Only** | `./scripts/deploy.sh dev --frontend-only` | ~5 min | Frontend rebuild and deployment |
| **No Git Push** | `./scripts/deploy.sh dev --skip-push` | varies | Local testing without remote push |
| **API Only** | `./scripts/deploy.sh dev --no-frontend` | ~18 min | Deploy without frontend (S3/CloudFront) |
| **HRP Integration** | `./scripts/deploy.sh dev --orchestration-role <arn>` | ~22 min | Use external orchestration role |

### Validation Failure Handling

When validation fails, fix the issues and re-run:

**Black Formatting**:
```bash
source .venv/bin/activate
black --line-length 79 lambda/
./scripts/deploy.sh dev
```

**cfn-lint Errors**:
```bash
cfn-lint cfn/*.yaml  # Review errors
# Fix templates, then:
./scripts/deploy.sh dev
```

**flake8 Warnings**:
```bash
source .venv/bin/activate
flake8 lambda/ --config .flake8  # Review warnings
# Fix code, then:
./scripts/deploy.sh dev
```

**Test Failures**:
```bash
source .venv/bin/activate
pytest tests/  # Run tests locally
# Fix failures, then:
./scripts/deploy.sh dev
```

### Prohibited Practices

❌ **NEVER use --quick for convenience** (emergency only)  
❌ **NEVER deploy without activating venv**  
❌ **NEVER use manual AWS CLI deployments**  
❌ **NEVER commit unformatted code**  
❌ **NEVER ignore test failures**

---

## S3 Deployment Repository

The deployment repository at `s3://hrp-drs-tech-adapter-dev` stores all deployment artifacts with versioning enabled.

### Repository Structure

```text
s3://hrp-drs-tech-adapter-dev/
├── cfn/                          # CloudFormation templates
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-gateway-*-stack.yaml  # 5 API Gateway stacks
│   ├── security-stack.yaml
│   ├── step-functions-stack.yaml
│   ├── frontend-stack.yaml
│   └── sns-stack.yaml
├── lambda/                       # Lambda deployment packages
│   ├── data-management-handler.zip
│   ├── execution-handler.zip
│   ├── query-handler.zip
│   ├── frontend-deployer.zip
│   ├── orch-sf.zip              # orchestration-stepfunctions
│   └── notification-formatter.zip
└── frontend/                     # Frontend build artifacts (optional)
    └── dist/                     # Built React application
```

### S3 Features

**Versioning**:
- Every file version preserved for recovery
- Can restore accidentally deleted files
- Complete version history available

**Deployment Modes**:
- **Full Deployment**: All CloudFormation, Lambda, and frontend
- **Lambda Only**: Just Lambda function code updates
- **Frontend Only**: Just frontend rebuild and deployment
- **API Only**: CloudFormation and Lambda without frontend (--no-frontend)

### Query S3 Versions

```bash
# View object metadata
aws s3api head-object \
  --bucket hrp-drs-tech-adapter-dev \
  --key cfn/master-template.yaml \
  --query "Metadata"

# List all versions of a file
aws s3api list-object-versions \
  --bucket hrp-drs-tech-adapter-dev \
  --prefix cfn/master-template.yaml
```

### Recovery Procedures

**Option 1: Git Revert + Redeploy** (Recommended):
```bash
# Revert to previous commit
git revert HEAD
source .venv/bin/activate
./scripts/deploy.sh dev
```

**Option 2: S3 Version Restore**:
```bash
# List versions
aws s3api list-object-versions \
  --bucket hrp-drs-tech-adapter-dev \
  --prefix cfn/master-template.yaml

# Restore specific version
aws s3api copy-object \
  --copy-source "hrp-drs-tech-adapter-dev/cfn/master-template.yaml?versionId=VERSION_ID" \
  --bucket hrp-drs-tech-adapter-dev \
  --key cfn/master-template.yaml

# Redeploy
source .venv/bin/activate
./scripts/deploy.sh dev
```

**Option 3: Lambda Rollback**:
```bash
# List Lambda package versions
aws s3api list-object-versions \
  --bucket hrp-drs-tech-adapter-dev \
  --prefix lambda/data-management-handler.zip

# Update Lambda with previous version
aws lambda update-function-code \
  --function-name hrp-drs-tech-adapter-data-management-handler-dev \
  --s3-bucket hrp-drs-tech-adapter-dev \
  --s3-key lambda/data-management-handler.zip \
  --s3-object-version <previous-version-id>
```

---

## Future CI/CD Migration

The local deploy.sh script follows the same 5-stage pipeline as GitHub Actions and GitLab CI, making migration straightforward when ready.

### Migration Benefits

**Why Migrate to CI/CD Platform:**
- ✅ **Team Visibility**: All deployments visible in centralized dashboard
- ✅ **Automatic Triggers**: Deploy on every push to main branch
- ✅ **Parallel Execution**: Run validation, security, and tests in parallel
- ✅ **Artifact Storage**: 30-day retention of security reports and build artifacts
- ✅ **Environment Management**: Separate dev/test/prod environments
- ✅ **OIDC Authentication**: No long-lived AWS credentials

**Current Local Benefits:**
- ✅ **No Platform Dependency**: Works without GitHub/GitLab access
- ✅ **Faster Iteration**: No queue wait times
- ✅ **Full Control**: Complete visibility into every step
- ✅ **Offline Capable**: Deploy without internet (if AWS accessible)

### GitHub Actions Migration

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy AWS DRS Orchestration

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'dev'
        type: choice
        options: [dev, test, prod]

# Prevent concurrent deployments
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false

env:
  AWS_REGION: us-east-1
  PROJECT_NAME: hrp-drs-tech-adapter

permissions:
  id-token: write
  contents: read

jobs:
  # Stage 1: Validation
  validate:
    name: Validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install validation tools
        run: pip install cfn-lint flake8 black
      
      - name: Validate CloudFormation
        run: cfn-lint cfn/*.yaml
      
      - name: Python code quality
        run: |
          flake8 lambda/ --config .flake8
          black --check --line-length 79 lambda/
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Frontend validation
        working-directory: frontend
        run: |
          npm ci
          npm run type-check
          npm run lint

  # Stage 2: Security
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install security tools
        run: pip install bandit detect-secrets
      
      - name: Python security
        run: |
          bandit -r lambda/ -ll
          detect-secrets scan --baseline .secrets.baseline
      
      - name: Frontend security
        working-directory: frontend
        run: |
          npm ci
          npm audit --audit-level=critical

  # Stage 3: Build
  build:
    name: Build
    runs-on: ubuntu-latest
    needs: [validate, security]
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Build Lambda packages
        run: python3 package_lambda.py
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Build frontend
        working-directory: frontend
        run: |
          npm ci
          npm run build
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: build-artifacts
          path: |
            build/
            frontend/dist/

  # Stage 4: Test
  test:
    name: Test
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install test dependencies
        run: pip install pytest moto boto3
      
      - name: Run Python tests
        run: pytest tests/ -v
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Run frontend tests
        working-directory: frontend
        run: |
          npm ci
          npm test -- --run

  # Stage 5: Deploy
  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    environment: dev
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: build-artifacts
      
      - name: Sync to S3
        run: |
          aws s3 sync cfn/ s3://${{ secrets.DEPLOYMENT_BUCKET }}/cfn/ --delete
          aws s3 sync build/lambda/ s3://${{ secrets.DEPLOYMENT_BUCKET }}/lambda/ --delete
      
      - name: Deploy CloudFormation
        run: |
          aws cloudformation deploy \
            --template-file cfn/master-template.yaml \
            --stack-name ${{ secrets.STACK_NAME }} \
            --parameter-overrides \
              ProjectName=${{ env.PROJECT_NAME }} \
              Environment=dev \
              SourceBucket=${{ secrets.DEPLOYMENT_BUCKET }} \
              AdminEmail=${{ secrets.ADMIN_EMAIL }} \
            --capabilities CAPABILITY_NAMED_IAM \
            --no-fail-on-empty-changeset
```

**Required GitHub Secrets:**
- `AWS_ROLE_ARN` - IAM role for OIDC authentication
- `DEPLOYMENT_BUCKET` - S3 bucket name
- `STACK_NAME` - CloudFormation stack name
- `ADMIN_EMAIL` - Admin email for Cognito

### GitLab CI Migration

Create `.gitlab-ci.yml`:

```yaml
# GitLab CI/CD Pipeline for DRS Orchestration
# Matches local deploy.sh workflow

variables:
  AWS_REGION: us-east-1
  PROJECT_NAME: hrp-drs-tech-adapter
  STACK_NAME: hrp-drs-tech-adapter-dev
  DEPLOYMENT_BUCKET: hrp-drs-tech-adapter-dev

# Prevent concurrent deployments
default:
  interruptible: true

# Stage 1: Validation
validate:
  image: python:3.12
  stage: build
  script:
    - pip install cfn-lint flake8 black
    - cfn-lint cfn/*.yaml
    - flake8 lambda/ --config .flake8
    - black --check --line-length 79 lambda/
    - apt-get update && apt-get install -y nodejs npm
    - npm install -g n && n 20
    - cd frontend && npm ci && npm run type-check && npm run lint

# Stage 2: Security
security:
  image: python:3.12
  stage: build
  script:
    - pip install bandit detect-secrets
    - bandit -r lambda/ -ll
    - detect-secrets scan --baseline .secrets.baseline
    - apt-get update && apt-get install -y nodejs npm
    - npm install -g n && n 20
    - cd frontend && npm ci && npm audit --audit-level=critical
  allow_failure: true

# Stage 3: Build
build:
  image: python:3.12
  stage: build
  script:
    - python3 package_lambda.py
    - apt-get update && apt-get install -y nodejs npm
    - npm install -g n && n 20
    - cd frontend && npm ci && npm run build
  artifacts:
    paths:
      - build/
      - frontend/dist/
    expire_in: 7 days

# Stage 4: Test
test:
  image: python:3.12
  stage: test
  script:
    - pip install pytest moto boto3
    - pytest tests/ -v
    - apt-get update && apt-get install -y nodejs npm
    - npm install -g n && n 20
    - cd frontend && npm ci && npm test -- --run
  allow_failure: true

# Stage 5: Deploy
deploy:
  image: amazon/aws-cli:latest
  stage: deploy
  only:
    - main
  script:
    # AWS OIDC authentication
    - |
      export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s" \
      $(aws sts assume-role-with-web-identity \
      --role-arn ${AWS_ROLE_ARN} \
      --role-session-name "gitlab-${CI_PROJECT_NAME}-${CI_PIPELINE_ID}" \
      --web-identity-token ${CI_JOB_JWT_V2} \
      --duration-seconds 3600 \
      --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
      --output text))
    
    # Sync to S3
    - aws s3 sync cfn/ s3://${DEPLOYMENT_BUCKET}/cfn/ --delete
    - aws s3 sync build/lambda/ s3://${DEPLOYMENT_BUCKET}/lambda/ --delete
    
    # Deploy CloudFormation
    - |
      aws cloudformation deploy \
        --template-file cfn/master-template.yaml \
        --stack-name ${STACK_NAME} \
        --parameter-overrides \
          ProjectName=${PROJECT_NAME} \
          Environment=dev \
          SourceBucket=${DEPLOYMENT_BUCKET} \
          AdminEmail=${ADMIN_EMAIL} \
        --capabilities CAPABILITY_NAMED_IAM \
        --no-fail-on-empty-changeset
  environment:
    name: dev
```

**Required GitLab CI/CD Variables:**
- `AWS_ROLE_ARN` - IAM role for OIDC authentication
- `ADMIN_EMAIL` - Admin email for Cognito

### Migration Checklist

**Before Migration:**
- [ ] Create OIDC IAM role in AWS
- [ ] Configure platform secrets (GitHub/GitLab)
- [ ] Test workflow file syntax
- [ ] Set up branch protection rules
- [ ] Configure environment approvals (for prod)

**During Migration:**
- [ ] Run first deployment manually to verify
- [ ] Monitor pipeline execution times
- [ ] Validate all stages complete successfully
- [ ] Test rollback procedures
- [ ] Document any platform-specific quirks

**After Migration:**
- [ ] Update team documentation
- [ ] Train team on new workflow
- [ ] Set up pipeline failure notifications
- [ ] Archive local deploy.sh (keep for emergencies)
- [ ] Monitor deployment metrics

---

## Monitoring & Troubleshooting

### Local Deployment Monitoring

**Watch deploy.sh output:**
```bash
source .venv/bin/activate
./scripts/deploy.sh dev 2>&1 | tee deployment.log
```

**Check CloudFormation status:**
```bash
aws cloudformation describe-stacks \
  --stack-name hrp-drs-tech-adapter-dev \
  --query 'Stacks[0].StackStatus'
```

**View recent stack events:**
```bash
aws cloudformation describe-stack-events \
  --stack-name hrp-drs-tech-adapter-dev \
  --max-items 10
```

### Common Issues & Solutions

#### 1. Validation Failures

**Black formatting errors:**
```bash
source .venv/bin/activate
black --line-length 79 lambda/
./scripts/deploy.sh dev
```

**cfn-lint errors:**
```bash
cfn-lint cfn/*.yaml  # Review specific errors
# Fix templates, then redeploy
```

#### 2. Security Scan Failures

**Bandit issues:**
```bash
source .venv/bin/activate
bandit -r lambda/ -ll  # Review security issues
# Fix code, then redeploy
```

**npm audit vulnerabilities:**
```bash
cd frontend
npm audit fix  # Auto-fix vulnerabilities
npm audit  # Review remaining issues
```

#### 3. Test Failures

**Python tests:**
```bash
source .venv/bin/activate
pytest tests/ -v  # Run with verbose output
# Fix failing tests, then redeploy
```

**Frontend tests:**
```bash
cd frontend
npm test -- --run  # Run tests locally
# Fix failures, then redeploy
```

#### 4. Deployment Failures

**Stack in UPDATE_ROLLBACK_FAILED:**
```bash
# deploy.sh automatically attempts recovery
# If manual intervention needed:
aws cloudformation continue-update-rollback \
  --stack-name hrp-drs-tech-adapter-dev
```

**Concurrency conflict:**
```bash
# Wait for current deployment to complete
aws cloudformation describe-stacks \
  --stack-name hrp-drs-tech-adapter-dev \
  --query 'Stacks[0].StackStatus'

# Then retry
source .venv/bin/activate
./scripts/deploy.sh dev
```

#### 5. Lambda Update Failures

**Function not found:**
```bash
# Verify function exists
aws lambda get-function \
  --function-name hrp-drs-tech-adapter-data-management-handler-dev

# If missing, run full deployment (not --lambda-only)
./scripts/deploy.sh dev
```

#### 6. Frontend Deployment Issues

**S3 sync failures:**
```bash
# Verify bucket exists
aws s3 ls s3://hrp-drs-tech-adapter-dev/

# Check IAM permissions
aws sts get-caller-identity
```

### Emergency Procedures

**Stack Protection Violation:**
```bash
# If you accidentally target a protected stack:
# 1. IMMEDIATELY cancel the operation (Ctrl+C)
# 2. Verify no changes were made:
aws cloudformation describe-stacks --stack-name <protected-stack>
# 3. Document the incident
# 4. Review stack protection rules
```

**Deployment Rollback:**
```bash
# Option 1: Git revert (recommended)
git revert HEAD
source .venv/bin/activate
./scripts/deploy.sh dev

# Option 2: S3 version restore (see S3 Repository section)

# Option 3: CloudFormation rollback
aws cloudformation cancel-update-stack \
  --stack-name hrp-drs-tech-adapter-dev
```

---

## Related Documentation

- [Developer Guide](DEVELOPER_GUIDE.md) - Development environment setup and workflow
- [Deployment Flexibility Guide](DEPLOYMENT_FLEXIBILITY_GUIDE.md) - Deployment modes and options
- [Troubleshooting Guide](../troubleshooting/README.md) - General troubleshooting procedures
- [AWS Stack Protection Rules](../../.kiro/steering/aws-stack-protection.md) - Protected stack policies
- [CI/CD Workflow Enforcement](../../.kiro/steering/cicd-workflow-enforcement.md) - Deployment policies

---

**Built for enterprise disaster recovery on AWS**
