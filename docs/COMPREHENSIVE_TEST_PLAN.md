# Comprehensive Test Plan for AWS DRS Orchestration Button Fix

**Session 27 Extended Testing Strategy**  
**Date Created**: November 10, 2025  
**Purpose**: Detailed testing plan to validate button fix and ensure no regressions

---

## Overview

This comprehensive test plan extends the manual testing outlined in `MORNING_BUTTON_FIX_PLAN.md` with:

1. **Automated E2E Testing** (using existing Playwright infrastructure)
2. **Regression Testing Suite**
3. **Performance & Load Testing**
4. **Edge Case & Error Handling Testing**
5. **Cross-Browser Automated Tests**
6. **API Integration Tests**
7. **Accessibility Testing**

**Total Estimated Time**: ~2 hours for complete test suite

---

## Prerequisites

- [ ] TEST environment deployed and accessible
- [ ] Firefox browser installed (primary test browser)
- [ ] AWS CLI authenticated
- [ ] Node.js and npm available
- [ ] Playwright test infrastructure in `tests/playwright/`
- [ ] Fresh browser context (Private/Incognito window)

**Application Details:**
- CloudFront URL: `https://d20h85rw0j51j.cloudfront.net`
- API Endpoint: `https://etv40zymeg.execute-api.us-east-1.amazonaws.com/test`
- User Pool: `us-east-1_tj03fVI31`

---

## Phase 6: Automated E2E Testing (30 minutes)

### Purpose
Leverage existing Playwright infrastructure to create automated validation tests for button functionality.

### Test Suite Creation

**File**: `tests/playwright/button-fix-validation.spec.ts`

```typescript
import { test, expect } from '@playwright/test';
import { AuthHelper } from './auth-helper';
import { ProtectionGroupsPage } from './page-objects/protection-groups-page';

test.describe('Button Fix Validation - Protection Groups', () => {
  let authHelper: AuthHelper;
  let protectionGroupsPage: ProtectionGroupsPage;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
    protectionGroupsPage = new ProtectionGroupsPage(page);
    
    // Login before each test
    await authHelper.login();
    await protectionGroupsPage.navigate();
  });

  test('Create button opens dialog and completes workflow', async ({ page }) => {
    // Click "Create Group" button
    await protectionGroupsPage.clickCreateButton();
    
    // Verify dialog opens
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    
    // Fill form
    await protectionGroupsPage.fillGroupForm({
      name: `E2E Test Group ${Date.now()}`,
      description: 'Automated test from Playwright',
      tags: [{ key: 'Environment', values: ['test'] }]
    });
    
    // Submit
    await protectionGroupsPage.submitForm();
    
    // Verify success toast
    await expect(page.locator('.MuiAlert-success')).toBeVisible();
    
    // Verify group appears in list
    await expect(page.locator('text=E2E Test Group')).toBeVisible();
  });

  test('Create button persists across page refreshes', async ({ page }) => {
    // Verify button exists
    await expect(protectionGroupsPage.createButton).toBeVisible();
    
    // Refresh page
    await page.reload();
    
    // Verify button still exists and clickable
    await expect(protectionGroupsPage.createButton).toBeVisible();
    await expect(protectionGroupsPage.createButton).toBeEnabled();
  });

  test('Multiple rapid clicks do not create duplicate dialogs', async ({ page }) => {
    // Click button rapidly
    await protectionGroupsPage.clickCreateButton();
    await protectionGroupsPage.clickCreateButton();
    await protectionGroupsPage.clickCreateButton();
    
    // Verify only one dialog exists
    const dialogs = await page.locator('[role="dialog"]').count();
    expect(dialogs).toBe(1);
  });

  test('Dialog keyboard navigation works correctly', async ({ page }) => {
    // Open dialog
    await protectionGroupsPage.clickCreateButton();
    
    // Press Escape
    await page.keyboard.press('Escape');
    
    // Verify dialog closes
    await expect(page.locator('[role="dialog"]')).not.toBeVisible();
  });
});

test.describe('Button Fix Validation - Recovery Plans', () => {
  // Similar tests for Recovery Plans page
  test('Create button opens dialog', async ({ page }) => {
    const authHelper = new AuthHelper(page);
    await authHelper.login();
    
    await page.goto('/recovery-plans');
    await page.click('button:has-text("Create Plan")');
    
    await expect(page.locator('[role="dialog"]')).toBeVisible();
  });
});
```

### Execution Commands

```bash
cd AWS-DRS-Orchestration/tests/playwright/

# Create test file (manual step - copy content above)
touch button-fix-validation.spec.ts

# Install dependencies if needed
npm install

# Run new test suite (headed mode to see execution)
npx playwright test button-fix-validation.spec.ts --headed

# Run in multiple browsers
npx playwright test button-fix-validation.spec.ts --project=chromium
npx playwright test button-fix-validation.spec.ts --project=firefox
npx playwright test button-fix-validation.spec.ts --project=webkit

# Generate HTML report
npx playwright show-report

# Run with debugging
npx playwright test button-fix-validation.spec.ts --debug
```

### Success Criteria
- [ ] All automated tests pass (green)
- [ ] Test execution time < 5 minutes
- [ ] No flaky tests (run 3 times, all pass)
- [ ] Screenshots captured for each major step
- [ ] HTML report shows 100% pass rate

---

## Phase 7: Regression Testing (20 minutes)

### Purpose
Ensure the button fix didn't break existing functionality.

### Test Matrix

| Feature | Test Case | Expected Result | Priority | Status |
|---------|-----------|-----------------|----------|--------|
| **Navigation** | Dashboard → Protection Groups → Recovery Plans | All routes load correctly | HIGH | ☐ |
| **Authentication** | Login → Logout → Login | Session management works | HIGH | ☐ |
| **Data Display** | View existing Protection Groups | Data renders correctly | MEDIUM | ☐ |
| **Data Display** | View existing Recovery Plans | Data renders correctly | MEDIUM | ☐ |
| **Search/Filter** | Filter Protection Groups by tag | Results filter correctly | MEDIUM | ☐ |
| **Pagination** | Navigate through pages | Pagination works | LOW | ☐ |
| **Error Handling** | Invalid form submission | Error messages appear | HIGH | ☐ |
| **Toast Notifications** | Success/Error operations | Toasts display correctly | MEDIUM | ☐ |
| **Edit Operations** | Edit existing Protection Group | Update succeeds | HIGH | ☐ |
| **Edit Operations** | Edit existing Recovery Plan | Update succeeds | HIGH | ☐ |
| **Delete Operations** | Delete Protection Group | Deletion succeeds | HIGH | ☐ |
| **Delete Operations** | Delete Recovery Plan | Deletion succeeds | HIGH | ☐ |

### Manual Test Checklist

#### Pre-Button-Fix Functionality (Should Still Work)

**Navigation Tests:**
- [ ] Dashboard loads without errors
- [ ] All nav menu items clickable
- [ ] Breadcrumbs update correctly
- [ ] Back button doesn't break state
- [ ] URL routing works correctly
- [ ] Page titles update in browser tab

**Data Retrieval Tests:**
- [ ] Protection Groups list fetches data
- [ ] Recovery Plans list fetches data  
- [ ] Execution status updates in real-time
- [ ] API calls complete successfully (check Network tab)
- [ ] Loading spinners appear during data fetch
- [ ] Empty states display when no data

**Edit Operations (Non-Create):**
- [ ] Edit existing Protection Group works
- [ ] Edit existing Recovery Plan works
- [ ] Delete operations still work
- [ ] Confirmation dialogs appear
- [ ] Changes persist after refresh

**UI/UX Elements:**
- [ ] Loading spinners appear during API calls
- [ ] Error boundaries catch errors gracefully
- [ ] Toast notifications positioned correctly
- [ ] Modal dialogs have proper z-index
- [ ] Form validation messages clear
- [ ] Buttons have proper hover states

### Regression Test Results Template

```markdown
## Regression Test Results

**Date**: [DATE]
**Tester**: [NAME]
**Environment**: TEST

### High Priority Tests
- Navigation: ✓/✗ [notes]
- Authentication: ✓/✗ [notes]
- Error Handling: ✓/✗ [notes]
- Edit Operations: ✓/✗ [notes]
- Delete Operations: ✓/✗ [notes]

### Medium Priority Tests
- Data Display: ✓/✗ [notes]
- Search/Filter: ✓/✗ [notes]
- Toast Notifications: ✓/✗ [notes]

### Low Priority Tests
- Pagination: ✓/✗ [notes]

**Issues Found**: [Number]
**Regressions**: [Yes/No - list if yes]
```

---

## Phase 8: Performance Testing (15 minutes)

### Purpose
Verify the fix doesn't introduce performance regressions.

### Metrics to Capture

#### 1. Time to Interactive (TTI)
```bash
# Use browser DevTools Performance tab

1. Open DevTools (F12)
2. Go to Performance tab
3. Click Record
4. Navigate to Protection Groups page
5. Stop recording when page fully loaded
6. Measure time until "Create Group" button is clickable

Target: < 2 seconds
```

#### 2. Dialog Open Time
```bash
# Measure dialog rendering performance

1. Start Performance recording
2. Click "Create Group" button
3. Stop when dialog fully rendered
4. Check "Main" thread timing

Target: < 200ms
```

#### 3. Form Submission Time
```bash
# Measure end-to-end operation

1. Fill form with test data
2. Start Network recording
3. Submit form
4. Measure time until success toast appears

Target: < 1 second (excluding API latency)
```

#### 4. Memory Leak Detection
```bash
# Chrome DevTools Memory profiler

1. Open DevTools → Memory tab
2. Take heap snapshot (baseline)
3. Open/close dialog 20 times
4. Take another heap snapshot
5. Compare snapshots

Target: No consistent memory growth > 10MB
```

### Lighthouse Audit

```bash
# Run Lighthouse from Chrome DevTools
# Or use CLI:
npx lighthouse https://d20h85rw0j51j.cloudfront.net \
  --output html \
  --output-path ./lighthouse-report.html \
  --view

# Key metrics to check:
# - Performance Score > 90
# - Accessibility Score > 90
# - Best Practices Score > 90
# - First Contentful Paint < 1.8s
# - Time to Interactive < 3.8s
```

### Performance Test Results Template

| Metric | Before Fix | After Fix | Change | Status | Notes |
|--------|------------|-----------|--------|--------|-------|
| TTI (Protection Groups) | N/A | ___s | N/A | ✓/✗ | |
| Dialog Open Time | N/A | ___ms | N/A | ✓/✗ | |
| Form Submit Time | N/A | ___s | N/A | ✓/✗ | |
| Memory Usage (20x) | N/A | ___MB | N/A | ✓/✗ | |
| Lighthouse Performance | N/A | ___ | N/A | ✓/✗ | |
| Lighthouse Accessibility | N/A | ___ | N/A | ✓/✗ | |
| First Contentful Paint | N/A | ___s | N/A | ✓/✗ | |
| Largest Contentful Paint | N/A | ___s | N/A | ✓/✗ | |

---

## Phase 9: Edge Case & Error Handling (20 minutes)

### Purpose
Test boundary conditions and error scenarios.

### Protection Groups Edge Cases

#### Form Validation Tests
- [ ] Empty form submission (should show validation errors)
- [ ] Name with special characters (test: `Test!@#$%^&*()`)
- [ ] Name with only spaces (should trim or reject)
- [ ] Name > 255 characters (should truncate or error)
- [ ] Description > 1000 characters
- [ ] Invalid tag key format (spaces, special chars)
- [ ] Duplicate tag keys in same group
- [ ] Empty tag values array
- [ ] Tag key starts with `aws:` (reserved prefix)

#### Dialog Behavior Tests
- [ ] Click outside dialog (should NOT close by default)
- [ ] Press ESC key (should close)
- [ ] Click Cancel button (should close without saving)
- [ ] Click X button (should close without saving)
- [ ] Rapid open/close clicks (no race conditions)
- [ ] Open dialog twice simultaneously (second should wait)
- [ ] Close dialog during API call (should cancel request)

#### API Error Scenarios
```markdown
Test each error condition:

1. **Network Offline**
   - Chrome DevTools → Network → Offline
   - Try to create group
   - Expected: Error toast with retry option

2. **401 Unauthorized**
   - Clear localStorage (token expires)
   - Try to create group
   - Expected: Redirect to login

3. **403 Forbidden**
   - Mock API to return 403
   - Expected: Error message about permissions

4. **500 Server Error**
   - Mock API to return 500
   - Expected: Generic error message, option to retry

5. **Request Timeout**
   - Chrome DevTools → Network → Throttling → Slow 3G
   - Try to create group
   - Expected: Timeout error after 30s

6. **Malformed Response**
   - Mock API to return invalid JSON
   - Expected: Parsing error handled gracefully
```

#### Concurrent Operations Tests
- [ ] Create group while another create in progress
- [ ] Edit group while viewing list (check real-time updates)
- [ ] Delete group while edit dialog open for same group
- [ ] Multiple users creating groups simultaneously

### Recovery Plans Edge Cases

#### Form Validation Tests
- [ ] Plan name validation (similar to Protection Groups)
- [ ] No waves configured (should require at least one)
- [ ] Wave with no servers (should validate)
- [ ] Wave delay negative number (should reject)
- [ ] Wave delay > 24 hours (should warn or limit)
- [ ] Circular wave dependencies (should detect and prevent)
- [ ] Wave name duplicates (should prevent or warn)

#### Wave Configuration Tests
- [ ] Add wave, remove wave, add again (state management)
- [ ] Reorder waves (drag-and-drop if implemented)
- [ ] Copy wave configuration
- [ ] Wave with 100+ servers (performance test)

### Browser Compatibility Matrix

| Browser | Version | OS | Create Works | Edit Works | Delete Works | Notes |
|---------|---------|----|--------------|-----------  |--------------|-------|
| Firefox | Latest | macOS | ☐ | ☐ | ☐ | |
| Chrome | Latest | macOS | ☐ | ☐ | ☐ | |
| Safari | Latest | macOS | ☐ | ☐ | ☐ | |
| Edge | Latest | Windows | ☐ | ☐ | ☐ | |
| Safari Mobile | Latest | iOS | ☐ | ☐ | ☐ | |
| Chrome Mobile | Latest | Android | ☐ | ☐ | ☐ | |

### Error Handling Test Script

```typescript
// Playwright test for error handling

test('Dialog handles API errors gracefully', async ({ page }) => {
  // Mock API to return 500 error
  await page.route('**/api/protection-groups', route => {
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Internal Server Error' })
    });
  });

  // Login and navigate
  await authHelper.login();
  await page.goto('/protection-groups');

  // Click create button
  await page.click('button:has-text("Create Group")');

  // Fill form
  await page.fill('[name="name"]', 'Test Group');
  await page.fill('[name="description"]', 'Test Description');

  // Submit
  await page.click('button:has-text("Create")');

  // Verify error message shown (not crashed)
  await expect(page.locator('.MuiAlert-error')).toBeVisible();
  await expect(page.locator('text=Error creating')).toBeVisible();

  // Verify dialog can be closed
  await page.click('button:has-text("Cancel")');
  await expect(page.locator('[role="dialog"]')).not.toBeVisible();

  // Verify can retry (open dialog again)
  await page.click('button:has-text("Create Group")');
  await expect(page.locator('[role="dialog"]')).toBeVisible();
});
```

---

## Phase 10: API Integration Testing (25 minutes)

### Purpose
Ensure button actions correctly interact with backend API.

### API Endpoint Testing

#### Setup
```bash
# Get authentication token
# 1. Login via browser
# 2. Open DevTools → Application → Local Storage
# 3. Find token in localStorage or sessionStorage
# 4. Or use Network tab to capture Authorization header

API_ENDPOINT="https://etv40zymeg.execute-api.us-east-1.amazonaws.com/test"
TOKEN="<paste-token-here>"
```

#### Protection Groups API Tests

```bash
# 1. Create Protection Group
curl -X POST "$API_ENDPOINT/protection-groups" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Test Group",
    "description": "Testing API directly",
    "tagFilters": [
      {
        "key": "Environment",
        "values": ["test", "staging"]
      }
    ]
  }' | jq '.'

# Expected: 201 Created with group object containing id

# 2. List Protection Groups
curl -X GET "$API_ENDPOINT/protection-groups" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Expected: 200 OK with array including newly created group

# 3. Get Single Protection Group
GROUP_ID="<id-from-create>"
curl -X GET "$API_ENDPOINT/protection-groups/$GROUP_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Expected: 200 OK with group object

# 4. Update Protection Group
curl -X PUT "$API_ENDPOINT/protection-groups/$GROUP_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated via API test"
  }' | jq '.'

# Expected: 200 OK with updated object

# 5. Delete Protection Group
curl -X DELETE "$API_ENDPOINT/protection-groups/$GROUP_ID" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 204 No Content

# 6. Verify deletion
curl -X GET "$API_ENDPOINT/protection-groups/$GROUP_ID" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 404 Not Found
```

#### Recovery Plans API Tests

```bash
# 1. Create Recovery Plan
curl -X POST "$API_ENDPOINT/recovery-plans" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Test Plan",
    "description": "Testing Recovery Plans API",
    "protectionGroupId": "<valid-group-id>",
    "waves": [
      {
        "name": "Wave 1",
        "delaySeconds": 300,
        "servers": ["i-1234567890abcdef0"]
      }
    ]
  }' | jq '.'

# Expected: 201 Created with plan object

# 2. List Recovery Plans
curl -X GET "$API_ENDPOINT/recovery-plans" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Expected: 200 OK with array including new plan

# 3. Update Recovery Plan
PLAN_ID="<id-from-create>"
curl -X PUT "$API_ENDPOINT/recovery-plans/$PLAN_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated plan description"
  }' | jq '.'

# Expected: 200 OK with updated object

# 4. Delete Recovery Plan
curl -X DELETE "$API_ENDPOINT/recovery-plans/$PLAN_ID" \
  -H "Authorization: Bearer $TOKEN"

# Expected: 204 No Content
```

### Integration Test Checklist

**Protection Groups API:**
- [ ] POST /protection-groups creates resource (201)
- [ ] GET /protection-groups returns list (200)
- [ ] GET /protection-groups/:id returns single resource (200)
- [ ] PUT /protection-groups/:id updates resource (200)
- [ ] DELETE /protection-groups/:id removes resource (204)
- [ ] POST with invalid data returns 400
- [ ] POST without auth returns 401
- [ ] GET non-existent resource returns 404

**Recovery Plans API:**
- [ ] POST /recovery-plans creates plan (201)
- [ ] GET /recovery-plans returns plans (200)
- [ ] GET /recovery-plans/:id returns single plan (200)
- [ ] PUT /recovery-plans/:id updates plan (200)
- [ ] DELETE /recovery-plans/:id removes plan (204)
- [ ] POST with circular wave dependencies returns 400
- [ ] POST without protection group returns 400

**General API Tests:**
- [ ] All responses have correct Content-Type header
- [ ] Response payloads match expected schema
- [ ] Authorization enforced (401 without valid token)
- [ ] CORS headers present for browser requests
- [ ] Rate limiting headers present (if implemented)
- [ ] Error responses include helpful messages

### API Test Results Template

```markdown
## API Integration Test Results

**Date**: [DATE]
**Environment**: TEST
**API Endpoint**: https://etv40zymeg.execute-api.us-east-1.amazonaws.com/test

### Protection Groups API
- Create (POST): ✓/✗ - Status: ___ - Time: ___ms
- List (GET): ✓/✗ - Status: ___ - Time: ___ms
- Get Single (GET): ✓/✗ - Status: ___ - Time: ___ms
- Update (PUT): ✓/✗ - Status: ___ - Time: ___ms
- Delete (DELETE): ✓/✗ - Status: ___ - Time: ___ms

### Recovery Plans API
- Create (POST): ✓/✗ - Status: ___ - Time: ___ms
- List (GET): ✓/✗ - Status: ___ - Time: ___ms
- Get Single (GET): ✓/✗ - Status: ___ - Time: ___ms
- Update (PUT): ✓/✗ - Status: ___ - Time: ___ms
- Delete (DELETE): ✓/✗ - Status: ___ - Time: ___ms

### Error Handling
- 400 Bad Request: ✓/✗ - [scenario tested]
- 401 Unauthorized: ✓/✗ - [scenario tested]
- 404 Not Found: ✓/✗ - [scenario tested]
- 500 Server Error: ✓/✗ - [scenario tested]

**Issues Found**: [Number]
**API Response Times**: Avg ___ms, Max ___ms
```

---

## Phase 11: Accessibility Testing (15 minutes)

### Purpose
Ensure buttons and dialogs are accessible to all users.

### Keyboard Navigation Tests

**Protection Groups Page:**
- [ ] Tab key moves focus to "Create Group" button
- [ ] Enter key activates button (opens dialog)
- [ ] Space key activates button (opens dialog)
- [ ] Tab order logical within dialog
- [ ] Tab cycles through: Name field → Description → Tag inputs → Buttons
- [ ] Shift+Tab reverses tab order
- [ ] Escape key closes dialog
- [ ] Focus trapped within dialog when open (cannot tab to background)
- [ ] Focus returns to "Create Group" button after dialog closes
- [ ] Arrow keys work in dropdowns/selects

**Recovery Plans Page:**
- [ ] Same keyboard navigation tests as Protection Groups
- [ ] Wave configuration fields keyboard accessible
- [ ] Server selection keyboard accessible

### Screen Reader Testing

**Using NVDA (Windows) or VoiceOver (Mac):**

```markdown
Test with screen reader enabled:

1. **Button Announcement**
   - [ ] "Create Group" announced as "button"
   - [ ] Button has descriptive label
   - [ ] Button state announced (enabled/disabled)

2. **Dialog Announcement**
   - [ ] Dialog role announced
   - [ ] Dialog title read first
   - [ ] Form fields have associated labels
   - [ ] Labels read before field values

3. **Form Field Announcements**
   - [ ] "Name" field: "Name, required, edit text"
   - [ ] "Description" field announced with label
   - [ ] Tag filters announced correctly
   - [ ] Error messages announced when present

4. **Action Feedback**
   - [ ] Success toast announced to screen reader
   - [ ] Error messages announced
   - [ ] Loading states announced
```

### Visual Accessibility Tests

```markdown
**Color Contrast:**
- [ ] Button text vs. background: Ratio ≥ 4.5:1
- [ ] Dialog title vs. background: Ratio ≥ 4.5:1
- [ ] Form labels vs. background: Ratio ≥ 4.5:1
- [ ] Error text vs. background: Ratio ≥ 4.5:1

**Focus Indicators:**
- [ ] Button has visible focus indicator (outline or shadow)
- [ ] Focus indicator has ≥ 3:1 contrast ratio
- [ ] Focus indicator does not rely on color alone
- [ ] Focus indicator visible in all color modes

**Touch Targets:**
- [ ] Button size meets 44x44px minimum
- [ ] Adequate spacing between interactive elements
- [ ] Touch targets work on mobile devices

**Zoom & Scaling:**
- [ ] Text readable at 200% zoom
- [ ] Layout doesn't break at 200% zoom
- [ ] No horizontal scrolling at 400% zoom (WCAG AAA)
- [ ] Content reflows properly
```

### ARIA Attributes Validation

```html
<!-- Button should have proper ARIA attributes -->
<button
  aria-label="Create new protection group"
  type="button"
>
  Create Group
</button>

<!-- Dialog should have proper ARIA attributes -->
<div
  role="dialog"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
  aria-modal="true"
>
  <h2 id="dialog-title">Create Protection Group</h2>
  <p id="dialog-description">Configure protection group settings</p>
  <!-- Form fields with proper labels -->
</div>
```

**Validation Checklist:**
- [ ] Button has `role="button"` or is a `<button>` element
- [ ] Button has descriptive `aria-label` or visible text
- [ ] Dialog has `role="dialog"`
- [ ] Dialog has `aria-modal="true"`
- [ ] Dialog has `aria-labelledby` pointing to title
- [ ] Dialog has `aria-describedby` if description exists
- [ ] Form fields have associated `<label>` elements
- [ ] Required fields marked with `aria-required="true"`
- [ ] Error messages have `role="alert"` or `aria-live="polite"`

### Accessibility Testing Tools

#### 1. Chrome DevTools Lighthouse
```bash
# Run accessibility audit
npx lighthouse https://d20h85rw0j51j.cloudfront.net \
  --only-categories=accessibility \
  --output html \
  --output-path ./accessibility-report.html \
  --view

# Target: Accessibility Score ≥ 90
```

#### 2. axe DevTools Extension
```markdown
1. Install axe DevTools:
   - Chrome: https://chrome.google.com/webstore/detail/axe-devtools
   - Firefox: https://addons.mozilla.org/en-US/firefox/addon/axe-devtools/

2. Navigate to Protection Groups page

3. Open DevTools → axe DevTools tab

4. Click "Scan ALL of my page"

5. Review violations:
   - Critical: Must fix immediately
   - Serious: Should fix
   - Moderate: Consider fixing
   - Minor: Nice to have

6. Generate report

7. Repeat for Recovery Plans page
```

#### 3. WAVE Extension
```markdown
1. Install WAVE:
   - Chrome: https://chrome.google.com/webstore/detail/wave-evaluation-tool

2. Navigate to page under test

3. Click WAVE icon

4. Review:
   - Errors (red)
   - Alerts (yellow)
   - Features (green)
   - Structural Elements (blue)
   - ARIA (purple)

5. Fix any errors before deployment
```

### Accessibility Test Results Template

```markdown
## Accessibility Test Results

**Date**: [DATE]
**Tool Used**: Lighthouse / axe / WAVE
**Pages Tested**: Protection Groups, Recovery Plans

### Keyboard Navigation
- Tab Navigation: ✓/✗
- Enter/Space Activation: ✓/✗
- Escape to Close: ✓/✗
- Focus Management: ✓/✗
- Focus Trapping: ✓/✗

### Screen Reader
- Button Announcement: ✓/✗
- Dialog Announcement: ✓/✗
- Form Labels: ✓/✗
- Error Messages: ✓/✗

### Visual Accessibility
- Color Contrast: ✓/✗ - Ratio: ___:1
- Focus Indicators: ✓/✗
- Touch Targets: ✓/✗ - Size: ___x___px
- 200% Zoom: ✓/✗

### ARIA Attributes
- Button ARIA: ✓/✗
- Dialog ARIA: ✓/✗
- Form ARIA: ✓/✗
- Live Regions: ✓/✗

### Tool Scores
- Lighthouse: ___/100
- axe Violations: ___ (Critical: ___, Serious: ___)
- WAVE Errors: ___

**WCAG 2.1 Compliance**: Level A / AA / AAA
**Issues Found**: [Number]
**Blockers**: [Yes/No - list if yes]
```

---

## Test Execution Order

### Quick Validation Path (30 minutes)
**When time is limited, execute this sequence:**

1. ✅ **Phase 4 from MORNING_BUTTON_FIX_PLAN** - Manual browser testing
2. ✅ **Phase 7 (High Priority Only)** - Critical regression tests
3. ✅ **Phase 6 (Smoke Tests Only)** - Run existing Playwright tests

### Standard Testing Path (90 minutes)
**Recommended for typical deployments:**

1. ✅ **Phase 4** - Complete manual verification
2. ✅ **Phase 7** - Full regression suite
3. ✅ **Phase 6** - Automated E2E tests
4. ✅ **Phase 9** - Edge case testing
5. ✅ **Phase 10** - API integration tests (quick curl tests)

### Comprehensive Testing Path (2 hours)
**For major releases or critical fixes:**

1. ✅ **Phase 4** - Manual verification
2. ✅ **Phase 6** - Create and run automated tests
3. ✅ **Phase 7** - Complete regression suite
4. ✅ **Phase 8** - Performance testing
5. ✅ **
