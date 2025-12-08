# S3 Deployment Repository Automation

This document covers the S3 sync and deployment workflow for the AWS DRS Orchestration solution.

## Overview

The deployment repository is maintained at `s3://aws-drs-orchestration` with automated sync, versioning, and git commit tracking. The sync script supports both S3 synchronization and direct AWS deployments.

## Quick Start

```bash
# Basic sync to S3 (no deployment)
./scripts/sync-to-deployment-bucket.sh

# Fast Lambda code update (~5 seconds)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# Build and deploy frontend
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend

# Full deployment via CloudFormation (5-10 minutes)
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

## Features

### S3 Versioning
- Every file version preserved for recovery
- Can restore accidentally deleted files
- Complete version history available

### Git Commit Tagging
- All S3 objects tagged with source git commit hash
- Sync timestamp included in metadata
- Query S3 by commit for audit trail

### Multiple Deployment Options
- **Basic Sync**: Upload files to S3 only
- **Fast Lambda Update**: Direct Lambda code update (~5 seconds)
- **Stack Deployment**: Individual stack updates via CloudFormation
- **Full Deployment**: All stacks via parent CloudFormation (5-10 minutes)

## Command Reference

### Basic Usage

```bash
./scripts/sync-to-deployment-bucket.sh [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--profile PROFILE` | AWS credentials profile (uses script default if not specified) |
| `--build-frontend` | Build frontend before syncing |
| `--dry-run` | Preview changes without executing |
| `--clean-orphans` | Remove orphaned directories from S3 |
| `--list-profiles` | List available AWS profiles and exit |
| `--help` | Show help message |

### Deployment Options

| Option | Description | Duration |
|--------|-------------|----------|
| `--update-lambda-code` | Update Lambda code directly (bypass CloudFormation) | ~5 seconds |
| `--deploy-lambda` | Deploy Lambda stack via CloudFormation | ~30 seconds |
| `--deploy-frontend` | Deploy Frontend stack via CloudFormation | ~2 minutes |
| `--deploy-cfn` | Deploy ALL stacks via parent CloudFormation | 5-10 minutes |

## Common Workflows

### 1. Lambda Code Changes (Fastest)

When you only change Lambda Python code:

```bash
# Edit Lambda code
vim lambda/index.py

# Sync to S3 and update Lambda directly
./scripts/sync-to-deployment-bucket.sh --update-lambda-code
```

### 2. Frontend Changes

When you change React/TypeScript code:

```bash
# Edit frontend code
vim frontend/src/components/MyComponent.tsx

# Build and deploy frontend
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend
```

### 3. CloudFormation Changes

When you change infrastructure templates:

```bash
# Edit CloudFormation template
vim cfn/lambda-stack.yaml

# Deploy all stacks
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

### 4. Preview Changes (Dry Run)

```bash
# See what would be synced without making changes
./scripts/sync-to-deployment-bucket.sh --dry-run

# Preview with cleanup
./scripts/sync-to-deployment-bucket.sh --dry-run --clean-orphans
```

### 5. Using Different AWS Profile

```bash
# List available profiles
./scripts/sync-to-deployment-bucket.sh --list-profiles

# Use specific profile
./scripts/sync-to-deployment-bucket.sh --profile MyProfile --update-lambda-code
```

## S3 Repository Structure

```text
s3://aws-drs-orchestration/
├── cfn/                          # CloudFormation templates
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── security-stack.yaml
│   ├── step-functions-stack.yaml
│   └── frontend-stack.yaml
├── lambda/                       # Lambda source code (synced as files)
│   ├── index.py                  # Main API handler
│   ├── drs_orchestrator.py       # Legacy orchestrator
│   ├── orchestration_stepfunctions.py
│   ├── build_and_deploy.py
│   ├── poller/                   # Poller functions
│   │   ├── execution_finder.py
│   │   └── execution_poller.py
│   └── deployment-package.zip    # Created by --deploy-cfn or --deploy-lambda
├── frontend/                     # Frontend application
│   ├── dist/                     # Built frontend (if --build-frontend used)
│   ├── src/                      # Source code
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── scripts/                      # Automation scripts
├── ssm-documents/                # SSM automation documents
├── docs/                         # Documentation
├── README.md
├── .gitignore
└── Makefile
```

> **Note**: The `deployment-package.zip` is only created when using `--deploy-cfn` or `--deploy-lambda` options. Basic sync uploads Lambda source files directly without packaging.

## Makefile Targets

```bash
# Manual sync
make sync-s3

# Build frontend and sync
make sync-s3-build

# Preview changes (dry-run)
make sync-s3-dry-run
```

## Query S3 by Git Commit

```bash
# View object metadata (includes git commit)
AWS_PAGER="" aws s3api head-object \
  --bucket aws-drs-orchestration \
  --key cfn/master-template.yaml \
  --query "Metadata"

# List all versions of a file
AWS_PAGER="" aws s3api list-object-versions \
  --bucket aws-drs-orchestration \
  --prefix cfn/master-template.yaml
```

## Recovery Procedures

### Option 1: Git Checkout + Re-sync (Recommended)

```bash
# Restore to previous commit
git checkout abc1234
./scripts/sync-to-deployment-bucket.sh --deploy-cfn

# Return to main
git checkout main
```

### Option 2: S3 Version Restore

```bash
# List all versions of a file
AWS_PAGER="" aws s3api list-object-versions \
  --bucket aws-drs-orchestration \
  --prefix cfn/master-template.yaml

# Restore specific version
aws s3api copy-object \
  --copy-source "aws-drs-orchestration/cfn/master-template.yaml?versionId=VERSION_ID" \
  --bucket aws-drs-orchestration \
  --key cfn/master-template.yaml
```

### Option 3: Lambda Rollback

```bash
# List Lambda package versions in S3
AWS_PAGER="" aws s3api list-object-versions \
  --bucket aws-drs-orchestration \
  --prefix lambda/deployment-package.zip

# Update Lambda with previous version from S3
aws lambda update-function-code \
  --function-name drs-orchestration-api-handler-dev \
  --s3-bucket aws-drs-orchestration \
  --s3-key lambda/deployment-package.zip \
  --s3-object-version <previous-version-id>
```

> **Note**: This only works if you previously deployed using `--deploy-cfn` or `--deploy-lambda`, which creates the `deployment-package.zip` in S3.

## Cleanup Orphaned Files

The script can detect and remove files in S3 that are no longer in the approved directory list:

```bash
# Preview orphaned files
./scripts/sync-to-deployment-bucket.sh --dry-run --clean-orphans

# Remove orphaned files (with confirmation prompt)
./scripts/sync-to-deployment-bucket.sh --clean-orphans
```

**Approved directories**: `cfn`, `docs`, `frontend`, `lambda`, `scripts`, `ssm-documents`

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
  --stack-name drs-orchestration-dev \
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
