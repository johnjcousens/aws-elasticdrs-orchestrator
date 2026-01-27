# Validation & Testing Guide

## Running Checks Without Deployment

You can now run all validation, security, and tests **without deploying anything** to AWS.

## Quick Start

### Option 1: Using deploy.sh (Recommended)
```bash
./scripts/deploy.sh dev --validate-only
```

### Option 2: Using Makefile
```bash
make validate-only
```

### Option 3: Using CI checks script
```bash
make ci-checks
# or
./scripts/local-ci-checks.sh
```

## What Gets Tested

### Stage 1: Validation ✅
- **CloudFormation**: cfn-lint validates all templates
- **Python Linting**: flake8 checks code style
- **Python Formatting**: black verifies formatting
- **TypeScript**: Type checking for frontend

### Stage 2: Security ✅
- **Python Security**: Bandit scans for vulnerabilities
- **Frontend Security**: npm audit checks dependencies
- **Secrets Detection**: detect-secrets (if available)
- **CloudFormation Security**: cfn_nag (if available)

### Stage 3: Tests ✅
- **Python Unit Tests**: pytest runs all unit tests
- **Python Integration Tests**: pytest integration tests
- **Frontend Tests**: vitest runs frontend tests

### What's Skipped ❌
- Git push
- Lambda packaging
- S3 sync
- CloudFormation deployment
- AWS API calls

## Comparison of Options

| Command | Validation | Security | Tests | Deploy | Duration |
|---------|-----------|----------|-------|--------|----------|
| `./scripts/deploy.sh dev --validate-only` | ✅ | ✅ | ✅ | ❌ | 2-3 min |
| `./scripts/deploy.sh dev --quick --skip-push` | ✅ | ❌ | ❌ | ✅ | 1-2 min |
| `./scripts/deploy.sh dev --skip-push` | ✅ | ✅ | ✅ | ✅ | 4-5 min |
| `make ci-checks` | ✅ | ✅ | ✅ | ❌ | 2-3 min |
| `make ci-checks-quick` | ✅ | ❌ | ❌ | ❌ | 30-60s |
| `make validate-only` | ✅ | ✅ | ✅ | ❌ | 2-3 min |

## Recommended Workflows

### Before Committing
```bash
# Run full validation
./scripts/deploy.sh dev --validate-only

# If all passes, commit and deploy
git add .
git commit -m "your message"
./scripts/deploy.sh dev
```

### Quick Iteration
```bash
# Quick validation only
make ci-checks-quick

# Fix issues, then full check
make validate-only
```

### Pre-Deployment Check
```bash
# Full validation before deploying
make validate-only

# If passes, deploy
make deploy-dev
```

## Individual Check Commands

### Validation Only
```bash
# CloudFormation
cfn-lint cfn/*.yaml

# Python linting
flake8 lambda/ --config .flake8

# Python formatting
black --check lambda/ --line-length 79

# TypeScript
cd frontend && npm run type-check
```

### Security Only
```bash
# Python security
bandit -r lambda/ -ll

# Frontend security
cd frontend && npm audit

# CloudFormation security
cfn_nag_scan --input-path cfn/
```

### Tests Only
```bash
# Python tests
pytest tests/python/unit/ -v
pytest tests/integration/ -v

# Frontend tests
cd frontend && npm test -- --run
```

## Exit Codes

- **0**: All checks passed ✅
- **1**: Validation failed ❌

## Example Output

```bash
$ ./scripts/deploy.sh dev --validate-only

═══════════════════════════════════════════════════════════
  Deploy: aws-drs-orchestration-dev
═══════════════════════════════════════════════════════════

[1/5] Validation
  ✓ cfn-lint
  ✓ flake8
  ✓ black
  ✓ TypeScript

[2/5] Security
  ✓ bandit (Python SAST)
  ✓ cfn_nag (IaC security)
  ✓ detect-secrets
  ✓ npm audit (dependencies)

[3/5] Tests
  ✓ pytest

═══════════════════════════════════════════════════════════
  ✓ Validation Complete (No Deployment)
═══════════════════════════════════════════════════════════

All validation checks passed!
To deploy, run without --validate-only flag
```

## Troubleshooting

### If validation fails:
```bash
# See detailed errors
./scripts/deploy.sh dev --validate-only

# Fix issues, then re-run
./scripts/deploy.sh dev --validate-only
```

### If tests fail:
```bash
# Run tests with verbose output
pytest tests/python/unit/ -v

# Run specific test
pytest tests/python/unit/test_specific.py -v
```

### If security scan fails:
```bash
# See detailed security issues
bandit -r lambda/ -ll -v

# Check frontend vulnerabilities
cd frontend && npm audit --audit-level moderate
```

## Integration with CI/CD

The `--validate-only` flag is perfect for:
- Pre-commit hooks
- Local development
- Pull request validation
- CI/CD pipelines (validation stage)

## Notes

- ✅ No AWS credentials required for validation-only mode
- ✅ Safe to run multiple times
- ✅ Fast feedback loop
- ✅ Catches issues before deployment
- ✅ No risk of accidentally deploying

## Related Commands

```bash
# Package Lambda functions (no deployment)
make package-lambda

# Verify repository structure
make verify-structure

# Clean build artifacts
make clean

# Full deployment (after validation passes)
./scripts/deploy.sh dev
```
