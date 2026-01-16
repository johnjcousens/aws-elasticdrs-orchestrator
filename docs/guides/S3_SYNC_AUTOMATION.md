# Deployment Workflow Guide

This document covers the deployment workflow for the AWS DRS Orchestration solution.

## Overview

**Primary Deployment Method**: GitHub Actions CI/CD pipeline with intelligent optimization.

The deployment repository is maintained at `s3://aws-elasticdrs-orchestrator` with automated sync, versioning, and git commit tracking via GitHub Actions.

## Quick Start (Recommended)

```bash
# 1. Make your changes locally
vim lambda/index.py

# 2. Check deployment scope (optional but recommended)
./scripts/check-deployment-scope.sh

# 3. Commit and push (triggers GitHub Actions)
git add .
git commit -m "feat: add new feature"
./scripts/safe-push.sh  # Checks for running workflows before pushing
```

## Emergency Manual Deployment (Restricted Use)

Manual sync script is available for emergencies only:

```bash
# Fast Lambda code update (~5 seconds) - EMERGENCY ONLY
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# IMMEDIATELY follow up with proper Git commit
git add .
git commit -m "emergency: describe the critical fix"
git push
```

## GitHub Actions CI/CD Pipeline (Primary Method)

### Pipeline Stages

The GitHub Actions workflow provides intelligent deployment optimization:

1. **Detect Changes** (~10s) - Analyzes changed files to determine deployment scope
2. **Validate** (~2 min) - CloudFormation validation, Python linting, TypeScript checking (skip for docs-only)
3. **Security Scan** (~2 min) - Bandit security scan, Safety dependency check (skip for docs-only)
4. **Build** (~3 min) - Lambda packaging, frontend build (skip for docs-only)
5. **Test** (~2 min) - Unit tests (skip for docs-only)
6. **Deploy Infrastructure** (~10 min) - CloudFormation stack deployment (only if infrastructure/Lambda changed)
7. **Deploy Frontend** (~2 min) - S3 sync, CloudFront invalidation (only if frontend changed or infrastructure deployed)

### Pipeline Optimization

- **Documentation-only changes**: ~30 seconds (95% time savings)
- **Frontend-only changes**: ~12 minutes (45% time savings)
- **Full deployment**: ~22 minutes (complete pipeline)

### Workflow Configuration

- **Repository**: `johnjcousens/aws-elasticdrs-orchestrator`
- **Workflow File**: `.github/workflows/deploy.yml`
- **Target Environment**: `test` (default)
- **AWS Account**: `{account-id}`
- **Deployment Bucket**: `s3://aws-elasticdrs-orchestrator`
- **OIDC Role**: `aws-elasticdrs-orchestrator-github-actions-test`

### Safe Push Workflow

**MANDATORY**: Always check for running workflows before pushing to prevent conflicts.

```bash
# Option 1: Check deployment scope first (recommended)
./scripts/check-deployment-scope.sh

# Option 2: Use safe-push script (checks workflows automatically)
./scripts/safe-push.sh

# Option 3: Manual workflow check before push
./scripts/check-workflow.sh && git push
```

### Prerequisites for Safe Push Scripts

```bash
# One-time setup: Install GitHub CLI
brew install gh

# Authenticate with GitHub
gh auth login
```

## Features

### S3 Versioning
- Every file version preserved for recovery
- Can restore accidentally deleted files
- Complete version history available

### Git Commit Tagging
- All S3 objects tagged with source git commit hash via GitHub Actions
- Sync timestamp included in metadata
- Query S3 by commit for audit trail

### Deployment Options via GitHub Actions
- **Automatic Detection**: Pipeline detects what changed and deploys only what's needed
- **Documentation Changes**: Skip build/test/deploy stages entirely
- **Frontend Changes**: Build and deploy frontend only
- **Infrastructure Changes**: Full CloudFormation deployment
- **Lambda Changes**: Package and deploy Lambda functions

## Standard Development Workflow

### 1. Lambda Code Changes

```bash
# Edit Lambda code
vim lambda/api-handler/index.py

# Commit and push (triggers GitHub Actions)
git add lambda/
git commit -m "feat: add new API endpoint"
./scripts/safe-push.sh

# Monitor pipeline in GitHub Actions tab
# Pipeline will automatically deploy Lambda changes
```

### 2. Frontend Changes

```bash
# Edit frontend code
vim frontend/src/components/MyComponent.tsx

# Commit and push
git add frontend/
git commit -m "feat: add new component"
./scripts/safe-push.sh

# Pipeline will build and deploy frontend automatically
```

### 3. CloudFormation Changes

```bash
# Edit CloudFormation template
vim cfn/lambda-stack.yaml

# Commit and push
git add cfn/
git commit -m "feat: add new Lambda function"
./scripts/safe-push.sh

# Pipeline will deploy all infrastructure changes
```

### 4. Documentation Changes

```bash
# Edit documentation
vim docs/guides/DEPLOYMENT.md

# Commit and push
git add docs/
git commit -m "docs: update deployment guide"
./scripts/safe-push.sh

# Pipeline completes in ~30 seconds (skips build/test/deploy)
```

## Emergency Manual Deployment (Restricted)

### When Manual Sync is Allowed

- **GitHub Actions service outage** (confirmed AWS/GitHub issue)
- **Critical production hotfix** when pipeline is broken
- **Pipeline debugging** (with immediate revert to Git-based deployment)

### Emergency Procedure

```bash
# ONLY in genuine emergencies
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# IMMEDIATELY follow up with proper Git commit
git add .
git commit -m "emergency: describe the critical fix"
git push
```

### Why Manual Sync is Restricted

- ❌ No audit trail (changes not tracked in Git)
- ❌ No quality gates (skip validation, testing, security scans)
- ❌ Inconsistent deployments (different process than production)
- ❌ Team blindness (other developers unaware of changes)
- ❌ Rollback impossible (no Git history to revert to)
- ❌ Compliance violation (breaks enterprise deployment standards)

## S3 Repository Structure

```text
s3://aws-elasticdrs-orchestrator/
├── cfn/                          # CloudFormation templates (18 templates)
│   ├── master-template.yaml      # Root orchestrator
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-gateway-resources-stack.yaml
│   ├── api-gateway-core-methods-stack.yaml
│   ├── api-gateway-operations-methods-stack.yaml
│   ├── api-gateway-infrastructure-methods-stack.yaml
│   ├── api-gateway-deployment-stack.yaml
│   ├── security-stack.yaml
│   ├── step-functions-stack.yaml
│   ├── frontend-stack.yaml
│   ├── sns-stack.yaml
│   └── github-oidc-stack.yaml
├── lambda/                       # Lambda deployment packages
│   ├── api-handler.zip
│   ├── orchestration-stepfunctions.zip
│   ├── execution-finder.zip
│   ├── execution-poller.zip
│   ├── frontend-build.zip
│   ├── bucket-cleaner.zip
│   └── notification-formatter.zip
├── frontend/                     # Frontend build artifacts
│   └── dist/                     # Built React application
└── docs/                         # Documentation
```

## Monitoring Deployments

### GitHub Actions Dashboard

1. Navigate to repository: `https://github.com/johnjcousens/aws-elasticdrs-orchestrator`
2. Click "Actions" tab
3. View running/completed workflows
4. Click workflow run for detailed logs

### CloudFormation Console

```bash
# View stack status
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator-test \
  --region us-east-1 \
  --query 'Stacks[0].StackStatus'

# View recent stack events
AWS_PAGER="" aws cloudformation describe-stack-events \
  --stack-name aws-elasticdrs-orchestrator-test \
  --region us-east-1 \
  --max-items 10
```

## Query S3 by Git Commit

```bash
# View object metadata (includes git commit from GitHub Actions)
AWS_PAGER="" aws s3api head-object \
  --bucket aws-elasticdrs-orchestrator \
  --key cfn/master-template.yaml \
  --query "Metadata"

# List all versions of a file
AWS_PAGER="" aws s3api list-object-versions \
  --bucket aws-elasticdrs-orchestrator \
  --prefix cfn/master-template.yaml
```

## Recovery Procedures

### Option 1: Git Revert + Push (Recommended)

```bash
# Revert to previous commit
git revert HEAD
git push

# Or checkout previous commit and push
git checkout abc1234
git push origin main --force  # Use with caution

# GitHub Actions will automatically deploy the reverted code
```

### Option 2: S3 Version Restore

```bash
# List all versions of a file
AWS_PAGER="" aws s3api list-object-versions \
  --bucket aws-elasticdrs-orchestrator \
  --prefix cfn/master-template.yaml

# Restore specific version
aws s3api copy-object \
  --copy-source "aws-elasticdrs-orchestrator/cfn/master-template.yaml?versionId=VERSION_ID" \
  --bucket aws-elasticdrs-orchestrator \
  --key cfn/master-template.yaml

# Then trigger CloudFormation update manually
```

### Option 3: Lambda Rollback

```bash
# List Lambda package versions in S3
AWS_PAGER="" aws s3api list-object-versions \
  --bucket aws-elasticdrs-orchestrator \
  --prefix lambda/api-handler.zip

# Update Lambda with previous version from S3
aws lambda update-function-code \
  --function-name aws-elasticdrs-orchestrator-api-handler-test \
  --s3-bucket aws-elasticdrs-orchestrator \
  --s3-key lambda/api-handler.zip \
  --s3-object-version <previous-version-id> \
  --region us-east-1
```

## Workflow Conflict Prevention

### MANDATORY: Check for Running Workflows

**NEVER push while a GitHub Actions workflow is running** - this causes deployment conflicts and failures.

### Safe Push Scripts

```bash
# Option 1: Check deployment scope first (recommended)
./scripts/check-deployment-scope.sh

# Option 2: Safe push with automatic workflow check
./scripts/safe-push.sh

# Option 3: Manual workflow check
./scripts/check-workflow.sh && git push

# Emergency force push (skip workflow check)
./scripts/safe-push.sh --force
```

### Workflow Status Indicators

- ✅ **Safe to push**: No workflows running
- ⏳ **Wait required**: Deployment in progress (wait for completion)
- ❌ **Conflict risk**: Multiple workflows would overlap
- 🚨 **Emergency only**: Use `--force` flag only for critical hotfixes

## Environment Requirements

### Prerequisites

1. **AWS CLI** installed and configured
2. **AWS credentials** with deployment permissions
3. **Node.js 22+** (for frontend builds)
4. **Python 3.12** (for Lambda packaging)

### Environment Files

- `.env.dev` - Required for frontend builds (contains Cognito and API config)
- `.env.test.template` - Template for creating `.env.dev`

## Troubleshooting

### AWS Credentials Error

```text
❌ ERROR: AWS credentials not configured or profile not found
```

**Solution**:
```bash
# List available profiles
./scripts/sync-to-deployment-bucket.sh --list-profiles

# Use correct profile
./scripts/sync-to-deployment-bucket.sh --profile YOUR_PROFILE
```

### Frontend Build Skipped

```text
⚠️ WARNING: .env.dev not found in project root
```

**Solution**: Create `.env.dev` from template:
```bash
cp .env.test.template .env.dev
# Edit .env.dev with your Cognito and API values
```

### Stack Update Failed

```text
❌ Stack update failed
```

**Solution**: Check CloudFormation console for detailed error, or run:
```bash
AWS_PAGER="" aws cloudformation describe-stack-events \
  --stack-name aws-drs-orchestrator-dev \
  --query 'StackEvents[?ResourceStatus==`UPDATE_FAILED`]'
```

## Integration with GitLab CI/CD

The sync script is designed for local development. For CI/CD deployments, use the GitLab pipeline which:

1. Builds Lambda packages with dependencies
2. Builds frontend with Vite
3. Uploads artifacts to S3
4. Deploys via CloudFormation

See [CICD_PIPELINE_GUIDE.md](./CICD_PIPELINE_GUIDE.md) for CI/CD details.

## References

- [CI/CD Pipeline Guide](./CICD_PIPELINE_GUIDE.md)
- [Project README](../../README.md)
