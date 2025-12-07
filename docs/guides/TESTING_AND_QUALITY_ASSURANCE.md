# Testing and Quality Assurance
# AWS DRS Orchestration System

**Version**: 2.0  
**Date**: December 2025  
**Status**: Production Ready

---

## Overview

This document describes the testing strategy and quality assurance procedures for the AWS DRS Orchestration system.

---

## Test Types

### 1. End-to-End Tests (Playwright)

**Location**: `tests/playwright/`  
**Framework**: Playwright with TypeScript  
**Purpose**: Validate critical user journeys through the UI

**Running Tests**:
```bash
cd tests/playwright
npm install
npx playwright test              # Run all tests
npx playwright test --ui         # Run with UI
npx playwright show-report       # View test report
```

**Test Coverage**:
- Authentication flow (login/logout)
- Protection Groups CRUD operations
- Recovery Plans CRUD operations
- Execution monitoring
- Server discovery

### 2. CloudFormation Validation

**Purpose**: Validate infrastructure templates before deployment

**Running Validation**:
```bash
# Syntax validation
make validate

# Lint with cfn-lint
make lint

# Or directly:
cfn-lint cfn/*.yaml --ignore-checks W2001 W3002 W3005 W3037
```

### 3. TypeScript Type Checking

**Purpose**: Catch type errors in frontend code

```bash
cd frontend
npx tsc --noEmit
```

### 4. Python Linting

**Purpose**: Code quality for Lambda functions

```bash
cd lambda
pylint index.py --disable=C0114,C0115,C0116
flake8 index.py --max-line-length=120
```

---

## CI/CD Pipeline Testing

The GitLab CI/CD pipeline (`.gitlab-ci.yml`) includes automated testing stages:

| Stage | Tests | Trigger |
|-------|-------|---------|
| validate | CloudFormation validation, TypeScript type check | On push |
| lint | Python linting, ESLint | On push |
| build | Lambda packaging, Frontend build | On push to main/dev |
| test | Unit tests, Playwright E2E | Manual trigger |

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
- [ ] Instance launch verification

---

## Test Environments

| Environment | Purpose | URL |
|-------------|---------|-----|
| Local | Development | `http://localhost:5173` |
| QA | Testing | CloudFront URL from stack outputs |
| Production | Live | CloudFront URL from stack outputs |

---

## Quality Gates

Before deployment to production:

1. **Build Success**: `npm run build` completes without errors
2. **Type Check**: `npx tsc --noEmit` passes
3. **Lint**: No critical linting errors
4. **CloudFormation**: Templates validate successfully
5. **Smoke Tests**: Critical user journeys pass

---

## Troubleshooting Test Failures

### Playwright Tests Fail

1. Check if the application is running
2. Verify test user credentials are valid
3. Check for UI changes that may have broken selectors
4. Run with `--debug` flag for step-by-step debugging

### CloudFormation Validation Fails

1. Check cfn-lint output for specific errors
2. Verify resource references are valid
3. Check for circular dependencies

### Build Fails

1. Check for TypeScript errors: `npx tsc --noEmit`
2. Check for missing dependencies: `npm install`
3. Clear cache: `rm -rf node_modules && npm install`

---

## Test Data

### Test User Credentials

Configured via Cognito User Pool. Create test users with:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username testuser@example.com \
  --user-attributes Name=email,Value=testuser@example.com \
  --temporary-password "TempPass123!"
```

### Sample DRS Servers

Tests require DRS source servers in the target region. Verify servers are available:

```bash
aws drs describe-source-servers --region us-east-1
```

---

## Reporting Issues

When reporting test failures, include:

1. Test name and file
2. Error message and stack trace
3. Steps to reproduce
4. Environment (local/QA/prod)
5. Browser and version (for UI tests)
6. Screenshots if applicable
