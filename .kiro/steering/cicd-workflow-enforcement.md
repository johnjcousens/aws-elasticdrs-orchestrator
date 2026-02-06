# CI/CD Workflow Enforcement

## ⛔ CRITICAL RULE #1 - READ THIS FIRST ⛔

**NEVER BYPASS THE DEPLOY SCRIPT. EVER.**

```bash
# ✅ CORRECT - Always use deploy.sh
./scripts/deploy.sh test --frontend-only

# ❌ WRONG - Never use direct AWS commands
aws s3 sync frontend/dist/ s3://...
aws cloudfront create-invalidation ...
aws lambda update-function-code ...
aws cloudformation deploy ...
```

**If you bypass deploy.sh, you are doing it WRONG.**

## ⛔ CRITICAL RULE #2 - ABSOLUTELY NO DIRECT AWS DEPLOYMENT COMMANDS ⛔

**These commands are BANNED for deployment. NEVER use them:**

```bash
# ❌ BANNED - Frontend deployment
aws s3 sync dist/ s3://aws-drs-orchestration-fe-*
aws s3 cp dist/ s3://aws-drs-orchestration-fe-*
aws cloudfront create-invalidation --distribution-id *

# ❌ BANNED - Lambda deployment  
aws lambda update-function-code --function-name *
aws lambda publish-version --function-name *

# ❌ BANNED - CloudFormation deployment
aws cloudformation deploy --stack-name *
aws cloudformation create-stack --stack-name *
aws cloudformation update-stack --stack-name *

# ❌ BANNED - Any deployment bucket operations
aws s3 sync * s3://aws-drs-orchestration-*
aws s3 cp * s3://aws-drs-orchestration-*
```

**ONLY ALLOWED COMMAND:**
```bash
# ✅ The ONLY way to deploy
./scripts/deploy.sh test
./scripts/deploy.sh test --frontend-only
./scripts/deploy.sh test --lambda-only
./scripts/deploy.sh test --validate-only
```

**WHY THIS RULE EXISTS:**
- Deploy script runs validation, security scans, and tests
- Deploy script handles git commits and pushes
- Deploy script manages concurrency and rollback
- Direct AWS commands bypass ALL quality gates
- Direct AWS commands can cause deployment conflicts
- Direct AWS commands skip credential verification

**IF YOU USE A DIRECT AWS DEPLOYMENT COMMAND, YOU MUST:**
1. Stop immediately
2. Acknowledge you violated the workflow
3. Use the deploy script instead

## Purpose
This document establishes mandatory CI/CD workflow practices to ensure code quality, security, and deployment consistency across the DR Orchestration Platform.

## Core Principle

**ALL code changes MUST go through the unified deploy script.**

**NEVER use direct AWS CLI commands for deployment:**
- ❌ `aws s3 sync` for frontend
- ❌ `aws cloudfront create-invalidation`
- ❌ `aws lambda update-function-code`
- ❌ `aws cloudformation deploy`

**ALWAYS use the deploy script:**
- ✅ `./scripts/deploy.sh test`
- ✅ `./scripts/deploy.sh test --frontend-only`
- ✅ `./scripts/deploy.sh test --lambda-only`

**NO EXCEPTIONS. NO SHORTCUTS. NO "JUST THIS ONCE".**

## Unified Deploy Script

The `./scripts/deploy.sh` script combines all CI/CD operations into a single command:

### Virtual Environment Requirement

**CRITICAL: The deploy script uses Python virtual environment (.venv) for all tools.**

The script automatically activates `.venv` if it exists:
```bash
# Activate Python virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${BLUE}Activating Python virtual environment...${NC}"
    source .venv/bin/activate
    echo -e "${GREEN}✓ Python venv activated${NC}"
else
    echo -e "${YELLOW}⚠ Python .venv not found - using system Python${NC}"
fi
```

**Setup virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

**Tools installed in .venv:**
- pytest (Python testing)
- hypothesis (property-based testing)
- cfn-lint (CloudFormation validation)
- flake8 (Python linting)
- black (Python formatting)
- bandit (Python security)
- detect-secrets (credential scanning)

### Usage
```bash
./scripts/deploy.sh [environment] [options]

# Examples:
./scripts/deploy.sh dev                    # Full pipeline (validation, security, tests, deploy)
./scripts/deploy.sh test                   # Deploy to test environment
./scripts/deploy.sh staging                # Deploy to staging environment
./scripts/deploy.sh dev --lambda-only      # Just update Lambda functions
./scripts/deploy.sh dev --frontend-only    # Just rebuild frontend
./scripts/deploy.sh dev --validate-only    # Run validation only (no deployment)
```

### What It Does (5 Stages)

1. **[1/5] Validation**
   - cfn-lint (CloudFormation) - uses `.venv/bin/cfn-lint`
   - flake8 (Python linting) - uses `.venv/bin/flake8`
   - black (Python formatting) - uses `.venv/bin/black`
   - TypeScript type checking

2. **[2/5] Security** (ALWAYS runs)
   - Bandit (Python security) - uses `.venv/bin/bandit`
   - npm audit (frontend vulnerabilities)
   - cfn_nag (CloudFormation security)
   - detect-secrets (credential scanning) - uses `.venv/bin/detect-secrets`
   - shellcheck (shell script security)

3. **[3/5] Tests** (ALWAYS runs)
   - pytest (Python unit tests) - uses `.venv/bin/pytest`
   - vitest (frontend tests)

4. **[4/5] Git Push** (ALWAYS runs)
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

## Running Tests Manually

**ALWAYS use the virtual environment for manual test runs:**

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all unit tests
.venv/bin/pytest tests/unit/ -v

# Run specific test file
.venv/bin/pytest tests/unit/test_account_utils_unit.py -v

# Run property-based tests
.venv/bin/pytest tests/unit/test_account_utils_property.py -v --hypothesis-show-statistics

# Run with coverage
.venv/bin/pytest --cov=lambda --cov-report=term tests/unit/
```

**NEVER run pytest without activating .venv:**
```bash
# ❌ WRONG - May use wrong Python version or missing dependencies
pytest tests/unit/

# ✅ CORRECT - Always use .venv
source .venv/bin/activate
.venv/bin/pytest tests/unit/
```

## Recommended Workflows

### Standard Development Workflow
```bash
# 1. Make changes
vim lambda/data-management-handler/index.py

# 2. Commit changes
git add .
git commit -m "feat: add new endpoint"

# 3. Deploy (validates, security scans, tests, pushes, deploys)
./scripts/deploy.sh dev
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

## Command Execution Rules

### ⛔ NEVER Use These Command Patterns

**NEVER redirect stderr and pipe to tail:**
```bash
# ❌ WRONG - Hides errors and truncates output unpredictably
npm run build 2>&1 | tail -50
pytest tests/ 2>&1 | tail -20
./scripts/deploy.sh test 2>&1 | tail -100
```

**Why this is dangerous:**
- Hides critical error messages that appear early in output
- Makes debugging impossible when things fail
- Truncates important warnings and validation messages
- Creates false sense of success when errors occurred

**ALWAYS let commands show full output:**
```bash
# ✅ CORRECT - See all output including errors
npm run build
pytest tests/
./scripts/deploy.sh test

# ✅ If output is too long, save to file instead
npm run build > build.log 2>&1
cat build.log  # Review full output
```

## Best Practices

### DO These Things
- ✅ Use the deploy script for all deployments
- ✅ Run validation before deploying: `--validate-only`
- ✅ Commit changes before deploying
- ✅ Use descriptive commit messages
- ✅ Test in dev before deploying to test/staging
- ✅ Review CloudFormation changes before applying
- ✅ Monitor deployments in CloudFormation console
- ✅ Let commands show full output (no tail truncation)
- ✅ Save long output to files if needed for review

### AVOID These Things
- ⚠️ Deploying uncommitted changes
- ⚠️ Running multiple deployments simultaneously to same stack
- ⚠️ Deploying directly via AWS CLI (bypasses quality gates)
- ⚠️ Skipping validation checks
- ⚠️ Using `2>&1 | tail` to truncate command output
- ⚠️ Hiding errors with output redirection

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
| `./scripts/deploy.sh dev` | Full pipeline (validation, security, tests, deploy) | 3-5 min |
| `./scripts/deploy.sh dev --lambda-only` | Lambda update only | 30-60s |
| `./scripts/deploy.sh dev --frontend-only` | Frontend rebuild only | 2-3 min |
| `./scripts/deploy.sh dev --validate-only` | Validation only (no deployment) | 1-2 min |

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
