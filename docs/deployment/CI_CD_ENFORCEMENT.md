# CI/CD Workflow Enforcement

**Last Updated**: January 26, 2026  
**Status**: ✅ Active - Enforced via steering documents

## Overview

This document establishes mandatory CI/CD workflow practices to ensure code quality, security, and deployment consistency across the DR Orchestration Platform.

## Core Principle

**ALL deployments MUST go through the full validation pipeline. There are NO exceptions.**

## Mandatory Deployment Process

### The ONLY Way to Deploy

```bash
# From the project directory with venv activated
cd infra/orchestration/drs-orchestration
source .venv/bin/activate
./scripts/deploy.sh dev
```

### Validation Pipeline (5 Stages)

#### Stage 1: Code Quality
- **cfn-lint**: CloudFormation template validation
- **flake8**: Python linting
- **black**: Python code formatting (line length 79)
- **TypeScript**: Type checking

#### Stage 2: Security
- **bandit**: Python security analysis (SAST)
- **cfn_nag**: CloudFormation security scanning
- **detect-secrets**: Credential leak detection
- **npm audit**: Frontend dependency vulnerabilities
- **shellcheck**: Shell script validation

#### Stage 3: Tests
- **pytest**: Python unit tests with coverage
- **vitest**: Frontend unit tests

#### Stage 4: Git Tracking
- All changes committed
- Pushed to remote repository
- Audit trail maintained

#### Stage 5: Deployment
- Lambda packages built
- Artifacts synced to S3 deployment bucket
- CloudFormation stack updated
- Frontend rebuilt and deployed

## Deployment Options

All options run full validation pipeline:

### Full Deployment
```bash
./scripts/deploy.sh dev
```
Deploys everything: Lambda, frontend, CloudFormation

### Lambda-Only Update
```bash
./scripts/deploy.sh dev --lambda-only
```
Updates Lambda functions only (still runs full validation)

### Frontend-Only Update
```bash
./scripts/deploy.sh dev --frontend-only
```
Rebuilds and deploys frontend only (still runs full validation)

### Skip Git Push (Testing Only)
```bash
./scripts/deploy.sh dev --skip-push
```
Skips git push step (still runs full validation)

## Prohibited Practices

### NEVER Use --quick Flag

The `--quick` flag exists for emergency situations only and requires explicit approval.

**Why it's prohibited**:
- Skips security scans that catch vulnerabilities
- Skips tests that prevent regressions
- Creates technical debt
- Violates compliance requirements
- Leads to production incidents

### NEVER Skip Validation Fixes

When validation fails:
- ❌ Don't use `--quick` to bypass
- ❌ Don't manually deploy via AWS CLI
- ❌ Don't commit without fixing issues
- ✅ Fix the validation errors
- ✅ Run the full pipeline again

### NEVER Deploy Without Virtual Environment

The deployment script requires the virtual environment because:
- Ensures consistent tool versions
- Provides required dependencies
- Matches CI/CD environment
- Prevents "works on my machine" issues

**Always activate venv first**:
```bash
source .venv/bin/activate
```

### NEVER Use Manual AWS CLI Deployments

Prohibited commands:
```bash
❌ aws lambda update-function-code
❌ aws lambda update-function-configuration
❌ aws s3 sync (for deployment)
❌ aws s3 cp (for deployment artifacts)
❌ aws cloudformation deploy (directly)
❌ aws cloudformation create-stack
❌ aws cloudformation update-stack
❌ aws cloudfront create-invalidation
```

Use the unified deploy script instead:
```bash
✅ ./scripts/deploy.sh dev --lambda-only
✅ ./scripts/deploy.sh dev --frontend-only
✅ ./scripts/deploy.sh dev
```

## Handling Validation Failures

### Black Formatting Errors

```bash
# Fix formatting
source .venv/bin/activate
black --line-length 79 lambda/

# Verify
black --check --line-length 79 lambda/

# Deploy
./scripts/deploy.sh dev
```

### cfn-lint Errors

```bash
# Review errors
cfn-lint cfn/*.yaml

# Fix CloudFormation templates
# Then deploy
./scripts/deploy.sh dev
```

### flake8 Warnings

```bash
# Review warnings
source .venv/bin/activate
flake8 lambda/ --config .flake8

# Fix Python code issues
# Then deploy
./scripts/deploy.sh dev
```

### Test Failures

```bash
# Run tests locally
source .venv/bin/activate
pytest tests/

# Fix failing tests
# Then deploy
./scripts/deploy.sh dev
```

## Why This Matters

### Code Quality
- Catches bugs before deployment
- Maintains consistent code style
- Prevents technical debt accumulation
- Ensures maintainability

### Security
- Identifies vulnerabilities early
- Prevents credential leaks
- Ensures compliance with security standards
- Protects against supply chain attacks

### Reliability
- Tests prevent regressions
- Validation catches configuration errors
- Consistent process reduces human error
- Predictable deployment outcomes

### Audit Trail
- Git commits track all changes
- Deployment logs provide traceability
- Compliance requirements satisfied
- Incident investigation enabled

## Emergency Procedures

If you believe you need to bypass validation:

1. **Stop and assess**: Is this truly an emergency?
2. **Document**: Why is bypass necessary?
3. **Get approval**: From team lead or architect
4. **Use --quick**: Only after approval
5. **Follow up**: Fix validation issues immediately after
6. **Document**: What was bypassed and why

## Common Mistakes to Avoid

### Mistake 1: Using --quick for Convenience
**Wrong**: "Validation is slow, I'll use --quick"  
**Right**: "I'll fix the validation errors and run the full pipeline"

### Mistake 2: Deploying Without venv
**Wrong**: Running deploy script with system Python  
**Right**: Activating venv first, then deploying

### Mistake 3: Manual AWS CLI Deployments
**Wrong**: `aws lambda update-function-code ...`  
**Right**: `./scripts/deploy.sh dev --lambda-only`

### Mistake 4: Committing Unformatted Code
**Wrong**: Committing without running black  
**Right**: Running black before commit

### Mistake 5: Ignoring Test Failures
**Wrong**: "Tests are flaky, I'll deploy anyway"  
**Right**: "I'll fix the failing tests first"

## Enforcement

Violations of this policy will result in:
- Code review rejection
- Deployment rollback
- Required remediation
- Team discussion of incident
- Process improvement review

## Protected Stacks

### NEVER Touch These Stacks

The following CloudFormation stacks are **PRODUCTION CRITICAL**:

- `aws-elasticdrs-orchestrator-test` (master stack)
- `aws-elasticdrs-orchestrator-test-*` (all nested stacks)
- `aws-elasticdrs-orchestrator-github-oidc-test` (OIDC authentication)

### Development Stack (USE THIS)

- Stack name: `aws-drs-orchestration-dev`
- Environment: `dev`
- Deployment bucket: `aws-drs-orchestration-dev`

## Verification Before Operations

Before ANY CloudFormation operation, verify:
1. Stack name ends with `-dev` (not `-test`)
2. Environment parameter is `dev` (not `test`)
3. You are NOT operating on protected stacks

## Related Documentation

- [CI/CD Guide](CICD_GUIDE.md) - Complete CI/CD workflow and pipeline
- [Quick Start Guide](QUICK_START_GUIDE.md) - Step-by-step deployment instructions
- [Deployment README](README.md) - Deployment documentation index

## Steering Documents

This enforcement policy is codified in:
- `.kiro/steering/cicd-workflow-enforcement.md` - Workspace-level enforcement
- `.kiro/steering/design-agent-steering/development-principles.md` - Core principles
- `.kiro/steering/aws-stack-protection.md` - Stack protection rules

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-26 | 1.0 | Initial enforcement policy documentation |
