# Deployment Scripts Update Summary

## Overview
Updated all deployment scripts to work from this repository structure (standalone repository, not nested in parent repo).

## Changes Made

### 1. Repository Structure Updates

All scripts now:
- Work from repository root directory
- Use relative paths from repo root
- Include proper script directory detection
- Change to project root before operations

### 2. Default Configuration Updates

**Old Configuration (nested repo):**
- Project: `aws-elasticdrs-orchestrator`
- Stack: `aws-elasticdrs-orchestrator-test` (production)
- Bucket: `aws-elasticdrs-orchestrator`
- Environment: `test`

**New Configuration (standalone repo):**
- Project: `aws-drs-orchestration`
- Stack: `aws-drs-orchestration-dev` (development)
- Bucket: `aws-drs-orchestration-dev`
- Environment: `dev`

### 3. Updated Scripts

#### scripts/deploy.sh
- Added repository structure documentation
- Added script directory detection and cd to project root
- Maintains all existing functionality
- Stack protection still enforced

#### scripts/local-deploy.sh
- Updated project name: `aws-drs-orchestration`
- Updated Lambda function list to match current architecture:
  - query-handler
  - data-management-handler
  - execution-handler
  - frontend-deployer
  - orch-sf (orchestration-stepfunctions)
  - notification-formatter
  - bucket-cleaner
- Enhanced stack protection to catch any `-test` suffix
- Added script directory detection

#### scripts/sync-to-deployment-bucket.sh
- Updated default bucket: `aws-drs-orchestration-dev`
- Updated project name: `aws-drs-orchestration`
- Updated environment: `dev`
- Removed references to old production stack
- Added script directory detection

#### scripts/integrated-deploy.sh
- Added repository structure documentation
- Added script directory detection and cd to project root
- Maintains all existing functionality

#### scripts/deploy-with-validation.sh
- Updated project name: `aws-drs-orchestration`
- Enhanced stack protection
- Added script directory detection

#### scripts/prepare-deployment-bucket.sh
- Updated default bucket: `aws-drs-orchestration-dev`
- Updated Lambda function list to match current architecture
- Added script directory detection

#### package_lambda.py
- Updated Lambda function list to current architecture
- Removed legacy functions (api-handler, frontend-builder, execution-finder, execution-poller)
- Added repository structure documentation
- Maintains all existing packaging functionality

#### Makefile
- Removed hardcoded stack-specific URLs and IDs
- Updated test commands to work from repository root
- Added `package-lambda` target for Lambda packaging
- Added `verify-structure` target to check repository integrity
- Updated `clean` target to include build/ directory
- Stack info now dynamically fetches from AWS instead of hardcoded values

### 4. Stack Protection

All scripts now protect against:
- Any stack containing `-test` suffix
- Any stack starting with `aws-elasticdrs-orchestrator`
- Ensures only `-dev` stacks are used for development

### 5. Lambda Functions

Updated function list across all scripts:
- ✅ query-handler (read-only queries)
- ✅ data-management-handler (Protection Groups & Recovery Plans)
- ✅ execution-handler (DR execution lifecycle)
- ✅ frontend-deployer (frontend deployment)
- ✅ orch-sf (Step Functions orchestration)
- ✅ notification-formatter (SNS formatting)

Removed legacy functions:
- ❌ api-handler (monolithic, replaced by decomposed handlers)
- ❌ execution-finder (legacy)
- ❌ execution-poller (legacy)
- ❌ frontend-builder (replaced by frontend-deployer)
- ❌ bucket-cleaner (not implemented in current architecture)

## Usage

### Standard Deployment
```bash
./scripts/deploy.sh dev                    # Full pipeline
./scripts/deploy.sh dev --quick            # Skip security/tests
./scripts/deploy.sh dev --lambda-only      # Just update Lambda code
./scripts/deploy.sh dev --frontend-only    # Just rebuild frontend
./scripts/deploy.sh dev --skip-push        # Skip git push
```

### Validation Only (No Deployment)
```bash
./scripts/deploy.sh dev --validate-only    # Run all checks without deploying
```
This runs:
- Stage 1: Validation (cfn-lint, flake8, black, TypeScript)
- Stage 2: Security (bandit, npm audit)
- Stage 3: Tests (pytest, vitest)
- **Skips**: Git push and deployment

Perfect for testing your changes before committing!

### Local Development
```bash
./scripts/local-deploy.sh dev full         # Full deployment
./scripts/local-deploy.sh dev lambda-only  # Lambda only
./scripts/local-deploy.sh dev frontend-only # Frontend only
```

### Sync to S3
```bash
./scripts/sync-to-deployment-bucket.sh                    # Basic sync
./scripts/sync-to-deployment-bucket.sh --build-frontend   # Build + sync
./scripts/sync-to-deployment-bucket.sh --validate         # Run CI checks
```

### Prepare Deployment Bucket
```bash
./scripts/prepare-deployment-bucket.sh aws-drs-orchestration-dev
```

### Using Makefile

Quick commands for common tasks:

```bash
# Validation only (no deployment)
make validate-only         # Run all checks without deploying

# Development setup
make dev-setup             # Install dependencies
make verify-structure      # Check repository structure

# CI/CD checks
make ci-checks             # Full validation + security + tests
make ci-checks-quick       # Quick validation only

# Deployment
make deploy-dev            # Full deployment with validation
make deploy-dev-lambda     # Lambda functions only
make deploy-dev-frontend   # Frontend only

# Package and build
make package-lambda        # Package all Lambda functions
make clean                 # Clean build artifacts

# Stack information
make stack-info            # Show stack configuration
make stack-status          # Check deployment status
make stack-outputs         # Show all stack outputs

# Security
make security-scan         # Run all security scans
make security-fix          # Fix auto-fixable issues
```

## Environment Variables

All scripts support these environment variables:
- `PROJECT_NAME` - Project name (default: aws-drs-orchestration)
- `ENVIRONMENT` - Environment (default: dev)
- `STACK_NAME` - Stack name (default: ${PROJECT_NAME}-${ENVIRONMENT})
- `DEPLOYMENT_BUCKET` - S3 bucket (default: ${PROJECT_NAME}-${ENVIRONMENT})
- `ADMIN_EMAIL` - Admin email (default: jocousen@amazon.com)
- `AWS_REGION` - AWS region (default: us-east-1)

## Protected Resources

### NEVER TOUCH (Production)
- `aws-elasticdrs-orchestrator-test` (master stack)
- `aws-elasticdrs-orchestrator-test-*` (nested stacks)
- `aws-elasticdrs-orchestrator-github-oidc-test` (OIDC)

### USE FOR DEVELOPMENT
- `aws-drs-orchestration-dev` (development stack)
- `aws-drs-orchestration-dev` (deployment bucket)

## Verification

To verify the updates work correctly:

1. Check script can find project root:
```bash
./scripts/deploy.sh dev --skip-push --dry-run
```

2. Verify Lambda packaging:
```bash
python3 package_lambda.py
ls -lh build/lambda/
```

3. Test sync (dry run):
```bash
./scripts/sync-to-deployment-bucket.sh --dry-run
```

## Notes

- All scripts now work from repository root
- No more nested path references
- Stack protection enforced in all scripts
- Lambda function list updated to match current architecture
- Default configuration uses development environment
- Production stacks remain protected
