# AWS DRS Orchestration - Testing Strategy

**Version**: 1.0  
**Date**: November 10, 2025  
**Status**: Smoke Tests Ready, Button Issue Diagnosis Phase

---

## Overview

Comprehensive testing strategy for diagnosing and validating the button responsiveness issue on Protection Groups and Recovery Plans pages after Session 26 deployment.

### Problem Statement
After Session 26 deployment, "Create Group" and "Create Plan" buttons are unresponsive. Source code analysis confirms proper implementation - hypothesis is stale JavaScript bundles in CloudFront (similar to Session 25 Extended issue).

### Testing Approach
**Two-Tier Strategy:**
1. **Manual Testing**: Browser DevTools debugging (~60 minutes)
2. **Automated Testing**: Playwright end-to-end tests (~10-15 minutes)

---

## Quick Start

### Prerequisites
- ✅ Test user created in Cognito: `drs-test-user@example.com`
- ✅ Configuration file: `.env.test` (do not commit!)
- ✅ CloudFront URL: `https://d20h85rw0j51j.cloudfront.net`
- ✅ API Endpoint: `https://etv40zymeg.execute-api.us-east-1.amazonaws.com/test`

### Run Smoke Tests

```bash
cd AWS-DRS-Orchestration

# Option 1: Via script (shows instructions)
./scripts/run-tests.sh smoke

# Option 2: Direct Playwright execution
cd tests/playwright
npx playwright test smoke-tests.spec.ts --headed

# Option 3: Via Cline MCP (use browser_action tool)
# Open smoke-tests.spec.ts and use Cline's Playwright integration
```

### Expected Results (Initial Run)
**Tests should FAIL** - confirming button issue exists:
- ✓ Login test: PASS
- ✗ Protection Groups button: FAIL (dialog doesn't open)
- ✗ Recovery Plans button: FAIL (dialog doesn't open)
- ✗ Dialog open/close: FAIL

---

## Test Suite Structure

### Smoke Tests (`smoke-tests.spec.ts`)
**Duration**: < 3 minutes  
**Purpose**: Quick validation of critical functionality

**Tests:**
1. `User can login successfully`
   - Authenticates with Cognito test user
   - Verifies redirect to dashboard
   - Confirms auth token in localStorage

2. `Protection Groups "Create Group" button opens dialog`
   - Navigates to /protection-groups
   - Clicks "Create Group" button
   - **Expected to FAIL**: Dialog doesn't open
   - Captures screenshots and console errors

3. `Recovery Plans "Create Plan" button opens dialog`
   - Navigates to /recovery-plans
   - Clicks "Create Plan" button
   - **Expected to FAIL**: Dialog doesn't open
   - Captures screenshots and console errors

4. `Dialog can be opened and closed`
   - Tests dialog lifecycle
   - **Expected to FAIL**: Depends on button responsiveness

### Test Infrastructure

**Configuration** (`playwright.config.ts`):
- Browser: Chromium (Desktop Chrome)
- Viewport: 1280x720
- Timeout: 30 seconds per action
- Retries: 2 attempts
- Screenshots: On failure only
- Sequential execution (not parallel)

**Authentication** (`auth-helper.ts`):
- Cognito login automation
- Token management
- Session persistence
- Logout utilities

**Page Objects** (`page-objects/`):
- `BasePage`: Common functionality (navigation, waiting, screenshots)
- `ProtectionGroupsPage`: Protection Groups CRUD operations
- Ready for: RecoveryPlansPage, ExecutionsPage

---

## Manual Testing Workflow

Follow `docs/MORNING_BUTTON_FIX_PLAN.md` for detailed manual testing:

### Phase 1: Diagnostic Testing (15 minutes)
1. Open CloudFront URL in browser
2. Login with test user
3. Open DevTools Console
4. Navigate to Protection Groups
5. Click "Create Group" - observe behavior
6. Check console for errors
7. Inspect network requests
8. Review JavaScript bundles loaded

### Phase 2: Fix Implementation (5-10 minutes)
If stale bundles confirmed:
```bash
cd AWS-DRS-Orchestration/frontend
npx vite build
aws s3 sync dist/ s3://drs-orchestration-fe-***REMOVED***-test/ --delete
aws cloudfront create-invalidation --distribution-id E3EHO8EL65JUV4 --paths "/*"
```

### Phase 3: Verification Testing (15 minutes)
1. Wait for CloudFront invalidation (30-60 seconds)
2. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
3. Test all CRUD operations
4. Verify toast notifications
5. Check console for errors

---

## Test Execution

### Via Cline MCP (Recommended)
Use Cline's Playwright MCP integration for seamless testing:

1. Open `smoke-tests.spec.ts`
2. Use Cline's `browser_action` tool
3. Tests execute in controlled browser
4. Results captured automatically

### Via Command Line
```bash
# Smoke tests only
cd tests/playwright
npx playwright test smoke-tests.spec.ts

# All tests
npx playwright test

# With UI mode (interactive)
npx playwright test --ui

# Debug mode
npx playwright test --debug
```

### Via Script Wrapper
```bash
# Smoke tests (< 3 minutes)
./scripts/run-tests.sh smoke

# CRUD tests (< 15 minutes)
./scripts/run-tests.sh crud

# All tests (< 20 minutes)
./scripts/run-tests.sh all
```

---

## Test Results

### Artifacts Location
- **Screenshots**: `test-results/screenshots/`
- **Videos**: `test-results/artifacts/`
- **HTML Report**: `test-results/html-report/index.html`
- **JSON Results**: `test-results/test-results.json`

### Success Criteria

**Smoke Tests (Post-Fix)**:
- ✅ All 4 tests pass
- ✅ Buttons responsive (<500ms)
- ✅ Dialogs open correctly
- ✅ No console errors
- ✅ Toast notifications work

**CRUD Tests (Future)**:
- ✅ Protection Groups: Create, Edit, Delete
- ✅ Recovery Plans: Create, Edit, Delete
- ✅ Form validation working
- ✅ API integration functional
- ✅ Data persistence verified

---

## Troubleshooting

### Tests Timeout
```bash
# Increase timeout in .env.test
TEST_TIMEOUT=60000  # 60 seconds
```

### Login Fails
```bash
# Verify test user exists
aws cognito-idp admin-get-user \
  --user-pool-id us-east-1_tj03fVI31 \
  --username drs-test-user@example.com

# Recreate if needed
./scripts/create-test-user.sh
```

### Screenshots Missing
```bash
# Create directory
mkdir -p test-results/screenshots
```

### CloudFront Cache Issues
```bash
# Force invalidation
aws cloudfront create-invalidation \
  --distribution-id E3EHO8EL65JUV4 \
  --paths "/*"

# Wait 30-60 seconds
# Hard refresh browser: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)
```

---

## Next Steps

### Immediate (Session 27)
1. ✅ Run smoke tests (confirm button issue)
2. ⏳ Execute manual testing workflow
3. ⏳ Fix button responsiveness (rebuild React app)
4. ⏳ Deploy fixed bundles to S3/CloudFront
5. ⏳ Re-run smoke tests (should pass)

### Short-Term (Session 28)
1. Create CRUD test suites
2. Add Recovery Plans page object
3. Implement test data cleanup
4. Document test coverage

### Long-Term
1. Integration test suites
2. Performance testing
3. Cross-browser testing
4. CI/CD integration
5. Automated regression testing

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `.env.test` | Test configuration (not committed) |
| `scripts/create-test-user.sh` | Cognito test user setup |
| `scripts/run-tests.sh` | Test execution wrapper |
| `tests/playwright/playwright.config.ts` | Playwright configuration |
| `tests/playwright/auth-helper.ts` | Authentication utilities |
| `tests/playwright/smoke-tests.spec.ts` | Critical smoke tests |
| `tests/playwright/page-objects/base-page.ts` | Base page object class |
| `tests/playwright/page-objects/protection-groups-page.ts` | Protection Groups page object |
| `docs/MORNING_BUTTON_FIX_PLAN.md` | Manual testing workflow |

---

## Resources

- **Playwright Documentation**: https://playwright.dev
- **Cline MCP Documentation**: https://docs.cline.bot/mcp
- **AWS Cognito User Pools**: https://docs.aws.amazon.com/cognito/
- **CloudFront Invalidation**: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html

---

**Last Updated**: November 10, 2025  
**MVP Progress**: 96% (Phase 7.7 remaining)  
**Test Coverage**: Smoke tests complete, CRUD tests pending
