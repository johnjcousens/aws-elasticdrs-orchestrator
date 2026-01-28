# CI/CD Workflow Enforcement

## Purpose
This document establishes mandatory CI/CD workflow practices to ensure code quality, security, and deployment consistency across the DR Orchestration Platform.

## Core Principle
**ALL code changes SHOULD go through the unified deploy script for consistency and quality gates.**

## Unified Deploy Script

The `./scripts/deploy.sh` script combines all CI/CD operations into a single command:

### Usage
```bash
./scripts/deploy.sh [environment] [options]

# Examples:
./scripts/deploy.sh dev                    # Full pipeline
./scripts/deploy.sh test                   # Deploy to test environment
./scripts/deploy.sh staging                # Deploy to staging environment
./scripts/deploy.sh dev --quick            # Skip security scans and tests
./scripts/deploy.sh dev --lambda-only      # Just update Lambda functions
./scripts/deploy.sh dev --frontend-only    # Just rebuild frontend
./scripts/deploy.sh dev --skip-push        # Skip git push
```

### What It Does (5 Stages)

1. **[1/5] Validation**
   - cfn-lint (CloudFormation)
   - flake8 (Python linting)
   - black (Python formatting)
   - TypeScript type checking

2. **[2/5] Security** (skipped with `--quick`)
   - Bandit (Python security)
   - npm audit (frontend vulnerabilities)
   - cfn_nag (CloudFormation security)
   - detect-secrets (credential scanning)
   - shellcheck (shell script security)

3. **[3/5] Tests** (skipped with `--quick`)
   - pytest (Python unit tests)
   - vitest (frontend tests)

4. **[4/5] Git Push** (skipped with `--skip-push`)
   - Pushes to remote

5. **[5/5] Deploy**
   - Builds Lambda packages
   - Syncs to S3 deployment bucket
   - Deploys CloudFormation stack

### Built-in Protections

- **Concurrency Protection**: Blocks if stack is already updating
- **Credential Check**: Verifies AWS credentials before starting
- **Validation Gates**: Stops deployment if validation fails
- **Rollback Recovery**: Handles UPDATE_ROLLBACK_FAILED state

## Recommended Workflows

### Standard Development Workflow
```bash
# 1. Make changes
vim lambda/data-management-handler/index.py

# 2. Commit changes
git add .
git commit -m "feat: add new endpoint"

# 3. Deploy (validates, tests, pushes, deploys)
./scripts/deploy.sh dev
```

### Quick Development Workflow
```bash
# Skip security scans and tests for faster iteration
git add .
git commit -m "fix: minor update"
./scripts/deploy.sh dev --quick
```

### Lambda-Only Update
```bash
# Fast Lambda code update without CloudFormation
git add .
git commit -m "fix: lambda bug"
./scripts/deploy.sh dev --lambda-only
```

### Frontend-Only Update
```bash
# Rebuild and deploy frontend only
git add .
git commit -m "fix: UI change"
./scripts/deploy.sh dev --frontend-only
```

### Local Testing (No Push)
```bash
# Test deployment without pushing to git
./scripts/deploy.sh dev --skip-push
```

### Validation Only
```bash
# Run all checks without deploying
./scripts/deploy.sh dev --validate-only
```

## Environment Strategy

### Development Environments
- **dev**: Primary development environment
- **dev2**: Secondary development environment
- **dev-{feature}**: Feature-specific environments

### Test Environments
- **test**: Integration testing environment
- **staging**: Pre-production staging environment

### Production Environment
- **prod**: Production environment (requires additional approvals)

## Best Practices

### DO These Things
- ✅ Use the deploy script for all deployments
- ✅ Run validation before deploying: `--validate-only`
- ✅ Commit changes before deploying
- ✅ Use descriptive commit messages
- ✅ Test in dev before deploying to test/staging
- ✅ Review CloudFormation changes before applying
- ✅ Monitor deployments in CloudFormation console

### AVOID These Things
- ⚠️ Deploying without validation (use `--quick` sparingly)
- ⚠️ Skipping tests for production deployments
- ⚠️ Deploying uncommitted changes
- ⚠️ Running multiple deployments simultaneously to same stack
- ⚠️ Deploying directly via AWS CLI (bypasses quality gates)

## Handling Failures

### Validation Failure
```bash
# Fix the issue, then re-run
./scripts/deploy.sh dev
```

### Concurrency Conflict
```bash
# Wait for current deployment to complete
aws cloudformation describe-stacks --stack-name aws-drs-orchestration-dev --query 'Stacks[0].StackStatus'

# Then retry
./scripts/deploy.sh dev
```

### Deployment Failure
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name aws-drs-orchestration-dev --max-items 10

# Fix issue and retry
./scripts/deploy.sh dev
```

### Rollback Failed State
The deploy script automatically attempts to recover from `UPDATE_ROLLBACK_FAILED` state by:
1. Identifying failed nested stacks
2. Running `continue-update-rollback` with skip resources
3. Waiting for rollback to complete
4. Proceeding with deployment

## Quick Reference

| Command | Description | Duration |
|---------|-------------|----------|
| `./scripts/deploy.sh dev` | Full pipeline | 3-5 min |
| `./scripts/deploy.sh dev --quick` | Skip security/tests | 2-3 min |
| `./scripts/deploy.sh dev --lambda-only` | Lambda update only | 30-60s |
| `./scripts/deploy.sh dev --frontend-only` | Frontend rebuild only | 2-3 min |
| `./scripts/deploy.sh dev --skip-push` | No git push | varies |
| `./scripts/deploy.sh dev --validate-only` | Validation only | 1-2 min |

## Alternative Deployment Methods

For public repository users without access to the deploy script:

### Direct CloudFormation Deployment
```bash
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name aws-drs-orchestration-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ProjectName=aws-drs-orchestration \
    Environment=dev \
    DeploymentBucket=aws-drs-orchestration-dev \
    AdminEmail=admin@example.com
```

See [README.md](../../README.md) for complete deployment examples.

## Related Documentation

- [AWS Stack Protection](aws-stack-protection.md) - Stack safety guidelines
- [Deployment Flexibility Guide](../../docs/guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md) - Deployment modes
- [Developer Guide](../../docs/guides/DEVELOPER_GUIDE.md) - Complete development workflow
