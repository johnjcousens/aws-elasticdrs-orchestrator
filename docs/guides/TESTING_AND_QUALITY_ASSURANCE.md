# Testing and Quality Assurance

**Version**: 2.1
**Date**: December 2025
**Status**: MVP Drill Only Prototype

---

## Overview

This document describes the testing strategy and quality assurance procedures for the AWS DRS Orchestration system.

**Note**: The `tests/` directory is currently gitignored. Test jobs in CI/CD are disabled until tests are added to version control.

---

## Test Infrastructure

### Directory Structure

```text
tests/
├── playwright/                    # End-to-end UI tests
│   ├── page-objects/              # Page object models
│   ├── smoke-tests.spec.ts        # Critical path tests
│   ├── protection-group-selection.spec.ts
│   ├── test-protection-group-dropdown.spec.ts
│   ├── auth-helper.ts             # Authentication utilities
│   └── playwright.config.ts       # Playwright configuration
│
└── python/                        # Python tests
    ├── unit/                      # Unit tests
    │   ├── test_recovery_plan_delete.py
    │   ├── test_wave_transformation.py
    │   ├── test_data_generator.py
    │   └── test_mock_drs_client.py
    ├── integration/               # Integration tests
    ├── e2e/                       # End-to-end API tests
    ├── fixtures/                  # Test data and fixtures
    ├── mocks/                     # Mock implementations
    ├── utils/                     # Test utilities
    ├── conftest.py                # Pytest configuration
    ├── requirements.txt           # Test dependencies
    └── pytest.ini                 # Pytest settings
```

---

## Test Types

### 1. Python Unit Tests

**Location**: `tests/python/unit/`
**Framework**: pytest 7.4.3 with pytest-cov, pytest-mock, hypothesis
**Purpose**: Test Lambda function logic in isolation

**Running Tests**:

```bash
cd tests/python
pip install -r requirements.txt

# Run all unit tests
pytest unit/ -v

# Run with coverage
pytest unit/ -v --cov=../../lambda --cov-report=html --cov-report=term

# Run specific test file
pytest unit/test_recovery_plan_delete.py -v

# Run with hypothesis property-based testing
pytest unit/ -v --hypothesis-show-statistics
```

**Test Dependencies**:

```text
pytest==7.4.3
pytest-cov==4.1.0
pytest-asyncio==0.21.1
pytest-mock==3.12.0
pytest-benchmark==4.0.0
moto[all]==4.2.9
hypothesis==6.92.1
boto3==1.34.0
freezegun==1.4.0
```

### 2. Python Integration Tests

**Location**: `tests/python/integration/`
**Purpose**: Test Lambda functions with mocked AWS services using moto

**Running Tests**:

```bash
cd tests/python

# Run integration tests
pytest integration/ -v

# Run with AWS credentials (for real service tests)
AWS_PROFILE=your-profile pytest integration/ -v
```

### 3. End-to-End Tests (Playwright)

**Location**: `tests/playwright/`
**Framework**: Playwright with TypeScript
**Purpose**: Validate critical user journeys through the UI

**Running Tests**:

```bash
cd tests/playwright
npm install

# Run all tests
npx playwright test

# Run with UI mode
npx playwright test --ui

# Run specific test file
npx playwright test smoke-tests.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug

# View test report
npx playwright show-report
```

**Configuration** (`playwright.config.ts`):

- Base URL: CloudFront distribution URL (from `.env.test`)
- Browser: Chromium (default)
- Timeout: 2 minutes per test
- Retries: 2 (configurable via `TEST_RETRIES` env var)
- Screenshots: On failure only
- Video: Retained on failure

### 4. CloudFormation Validation

**Purpose**: Validate infrastructure templates before deployment

**Running Validation**:

```bash
# Using Makefile
make validate    # AWS CLI validation
make lint        # cfn-lint validation

# Direct commands
cfn-lint cfn/*.yaml --config-file .cfnlintrc.yaml

# Validate specific template
aws cloudformation validate-template --template-body file://cfn/master-template.yaml
```

### 5. TypeScript Type Checking

**Purpose**: Catch type errors in frontend code

```bash
cd frontend
npx tsc --noEmit
```

### 6. Python Linting

**Purpose**: Code quality for Lambda functions

```bash
cd lambda

# Pylint
pylint index.py --disable=C0114,C0115,C0116,R0903,W0613,C0103

# Flake8
flake8 index.py --max-line-length=120 --ignore=E203,W503,E501

# Black (formatting check)
black --check --line-length=120 index.py
```

### 7. Frontend Linting

**Purpose**: Code quality for React frontend

```bash
cd frontend
npm run lint
```

---

## CI/CD Pipeline Testing

The GitLab CI/CD pipeline (`.gitlab-ci.yml`) includes automated testing stages:

| Stage | Job | Description | Trigger |
|-------|-----|-------------|---------|
| validate | `validate:cloudformation` | cfn-lint + AWS CLI validation | On cfn/ changes |
| validate | `validate:frontend-types` | TypeScript type checking | On frontend/ changes |
| lint | `lint:python` | pylint, black, flake8 | On lambda/ changes |
| lint | `lint:frontend` | ESLint | On frontend/ changes |
| build | `build:lambda` | Package Lambda functions | On main/dev push |
| build | `build:frontend` | Vite production build | On main/dev push |
| test | `test:python-unit` | Python unit tests | **DISABLED** |
| test | `test:python-integration` | Python integration tests | **DISABLED** |
| test | `test:playwright` | Playwright E2E tests | **DISABLED** |

**Note**: Test jobs are disabled because `tests/` is gitignored. To enable:

1. Remove `tests/` from `.gitignore`
2. Commit the test files
3. Uncomment the test jobs in `.gitlab-ci.yml`

---

## Manual Testing Checklist

### Protection Groups

- [ ] Create Protection Group with valid name and region
- [ ] Verify duplicate name rejection (case-insensitive)
- [ ] Verify server assignment tracking
- [ ] Edit Protection Group (add/remove servers)
- [ ] Delete Protection Group
- [ ] Verify deletion blocked if used in Recovery Plan

### Recovery Plans

- [ ] Create Recovery Plan with waves
- [ ] Add multiple waves with dependencies
- [ ] Edit wave configuration
- [ ] Delete Recovery Plan
- [ ] Verify deletion blocked during active execution

### Executions

- [ ] Start Drill execution
- [ ] Monitor wave progress in real-time
- [ ] Verify execution history recorded
- [ ] View execution details
- [ ] Clear execution history (preserves active)

### DRS Integration

- [ ] Server discovery by region
- [ ] Server details display (hostname, IP, status)
- [ ] Recovery job initiation
- [ ] Job status polling
- [ ] Instance launch verification (LAUNCHED status)

---

## Test Environments

| Environment | Purpose | URL |
|-------------|---------|-----|
| Local | Development | `http://localhost:5173` |
| Test | CI/CD Testing | CloudFront URL from stack outputs |
| QA | Manual Testing | CloudFront URL from stack outputs |
| Production | Live | CloudFront URL from stack outputs |

**Environment Variables** (`.env.test`):

```bash
CLOUDFRONT_URL=https://your-distribution.cloudfront.net
TEST_USERNAME=testuser@example.com
TEST_PASSWORD=your-test-password
TEST_TIMEOUT=30000
TEST_RETRIES=2
HEADLESS=true
```

---

## Quality Gates

Before deployment to production:

1. **Build Success**: `npm run build` completes without errors
2. **Type Check**: `npx tsc --noEmit` passes
3. **Lint**: No critical linting errors
4. **CloudFormation**: Templates validate successfully (`make validate lint`)
5. **Smoke Tests**: Critical user journeys pass (when enabled)

---

## Troubleshooting Test Failures

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
4. Check Node.js version (requires Node 22)

---

## Test Data

### Test User Credentials

Configured via Cognito User Pool. Create test users with:

```bash
# Using the helper script
./scripts/create-test-user.sh

# Or manually
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser@example.com \
  --user-attributes Name=email,Value=testuser@example.com \
  --temporary-password "TempPass123!"
```

### Sample DRS Servers

Tests require DRS source servers in the target region. Verify servers are available:

```bash
AWS_PAGER="" aws drs describe-source-servers --region us-east-1
```

---

## Reporting Issues

When reporting test failures, include:

1. Test name and file
2. Error message and stack trace
3. Steps to reproduce
4. Environment (local/test/QA/prod)
5. Browser and version (for UI tests)
6. Screenshots if applicable
7. Relevant log output

---

## References

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Pytest Documentation](https://docs.pytest.org/)
- [cfn-lint Documentation](https://github.com/aws-cloudformation/cfn-lint)
- [Moto Documentation](https://docs.getmoto.org/)
