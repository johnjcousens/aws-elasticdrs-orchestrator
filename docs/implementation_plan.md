# Button Responsiveness Testing Implementation Plan

**Project**: AWS DRS Orchestration Platform  
**Issue**: "Create New" buttons unresponsive on Protection Groups and Recovery Plans pages  
**Date**: November 10, 2025  
**Version**: 1.0

---

## [Overview]

This implementation plan provides comprehensive testing strategies to diagnose and validate the fix for button responsiveness issues in the AWS DRS Orchestration frontend. The plan combines manual browser-based testing with automated Playwright end-to-end tests.

**Problem Statement**: After Session 26 deployment, the "Create Group" and "Create Plan" buttons do not respond when clicked. Source code analysis confirms proper implementation of event handlers and dialog state management.

**Root Cause Hypothesis**: Deployed JavaScript bundles in CloudFront are outdated and don't reflect current source code (similar to Session 25 Extended issue where React app was modified but never rebuilt).

**Testing Goals**:
1. Confirm button responsiveness issue in deployed environment
2. Identify root cause (stale bundles vs runtime errors vs state management)
3. Validate fix implementation with manual testing
4. Create automated regression tests with Playwright
5. Ensure all CRUD operations function correctly

**Testing Approach**:
- **Manual Testing**: Browser-based debugging with DevTools (~60 minutes)
- **Automated Testing**: Playwright test suites via Cline MCP (~10-15 minutes)
- **Test Environment**: CloudFront production deployment (`https://d20h85rw0j51j.cloudfront.net`)
- **Authentication**: Dedicated Cognito test user for automation

---

## [Types]

### Testing Configuration Types

```typescript
// Test user configuration
interface TestUser {
  username: string;
  password: string;
  userPoolId: string;
  clientId: string;
}

// Test execution configuration
interface TestConfig {
  baseUrl: string;
  testUser: TestUser;
  timeout: number;
  retries: number;
  headless: boolean;
}

// Test result types
interface TestResult {
  testName: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  error?: string;
  screenshots?: string[];
}

// Manual test checklist item
interface ChecklistItem {
  step: string;
  status: 'pending' | 'completed' | 'failed';
  observations: string;
  screenshot?: string;
}
```

### Playwright Page Object Types

```typescript
// Protection Groups page object
interface ProtectionGroupsPage {
  navigateToPage(): Promise<void>;
  clickCreateButton(): Promise<void>;
  isDialogOpen(): Promise<boolean>;
  fillGroupForm(data: GroupFormData): Promise<void>;
  submitForm(): Promise<void>;
  verifyGroupInList(name: string): Promise<boolean>;
  deleteGroup(name: string): Promise<void>;
}

// Recovery Plans page object
interface RecoveryPlansPage {
  navigateToPage(): Promise<void>;
  clickCreateButton(): Promise<void>;
  isDialogOpen(): Promise<boolean>;
  fillPlanForm(data: PlanFormData): Promise<void>;
  submitForm(): Promise<void>;
  verifyPlanInList(name: string): Promise<boolean>;
  deletePlan(name: string): Promise<void>;
}

// Form data types
interface GroupFormData {
  name: string;
  description: string;
  tagFilters: Array<{
    key: string;
    values: string[];
  }>;
}

interface PlanFormData {
  name: string;
  description: string;
  protectionGroupId: string;
  waves: WaveConfig[];
}

interface WaveConfig {
  name: string;
  delaySeconds: number;
  servers: string[];
}
```

---

## [Files]

### New Files to Create

#### Test Infrastructure

1. **`tests/playwright/playwright.config.ts`** (Playwright configuration)
   - Base URL configuration
   - Browser settings (Chromium, Firefox, WebKit)
   - Timeout settings
   - Retry configuration
   - Screenshot on failure
   - Video recording settings

2. **`tests/playwright/auth-helper.ts`** (Cognito authentication utilities)
   - AWS Cognito authentication helper
   - Token management
   - Session persistence
   - Login/logout utilities

3. **`tests/playwright/page-objects/base-page.ts`** (Base page object)
   - Common navigation methods
   - Wait utilities
   - Screenshot helpers
   - Error handling

4. **`tests/playwright/page-objects/protection-groups-page.ts`** (Protection Groups POM)
   - Page-specific selectors
   - Action methods
   - Validation methods

5. **`tests/playwright/page-objects/recovery-plans-page.ts`** (Recovery Plans POM)
   - Page-specific selectors
   - Action methods
   - Validation methods

#### Test Suites

6. **`tests/playwright/smoke-tests.spec.ts`** (Quick validation suite)
   - Button responsiveness checks (2-3 minutes)
   - Dialog open/close validation
   - Basic navigation tests

7. **`tests/playwright/protection-groups-crud.spec.ts`** (Full CRUD suite)
   - Create protection group
   - Edit protection group
   - Delete protection group
   - List validation
   - Form validation

8. **`tests/playwright/recovery-plans-crud.spec.ts`** (Full CRUD suite)
   - Create recovery plan
   - Edit recovery plan
   - Delete recovery plan
   - Wave configuration
   - Dependency validation

#### Configuration & Scripts

9. **`scripts/create-test-user.sh`** (Cognito test user setup)
   - AWS CLI commands to create user
   - Password configuration
   - User pool verification
   - Output credentials for tests

10. **`scripts/run-tests.sh`** (Test execution wrapper)
    - Environment variable setup
    - Test suite selection
    - Result reporting
    - Screenshot management

#### Documentation

11. **`docs/TESTING_STRATEGY.md`** (Comprehensive testing guide)
    - Testing philosophy
    - Manual vs automated testing
    - Test execution workflows
    - Troubleshooting guide

12. **`docs/PLAYWRIGHT_TEST_GUIDE.md`** (Playwright-specific guide)
    - Test suite overview
    - Running tests locally
    - Debugging failed tests
    - Extending test coverage

13. **`.env.test`** (Test environment configuration)
    - CloudFront URL
    - Cognito User Pool ID
    - Cognito Client ID
    - Test user credentials

### Existing Files to Modify

1. **`docs/MORNING_BUTTON_FIX_PLAN.md`** (Enhancement)
   - Add Phase 0: Pre-deployment verification with Playwright
   - Add Phase 6: Post-fix automated regression tests
   - Add references to new test suites
   - Add troubleshooting flowchart

2. **`package.json`** (Add test scripts)
   - Add Playwright test execution scripts
   - Add test user setup scripts
   - Add test environment configuration

3. **`.gitignore`** (Ignore test artifacts)
   - Playwright test results
   - Screenshots and videos
   - Test environment files (.env.test)
   - Test user credentials

---

## [Functions]

### Cognito Authentication Helper

**File**: `tests/playwright/auth-helper.ts`

#### Key Functions

1. **`authenticateWithCognito(username: string, password: string): Promise<AuthTokens>`**
   - Initiates Cognito authentication flow
   - Returns access token, ID token, refresh token
   - Handles MFA if enabled
   - Throws error on authentication failure

2. **`loginToApp(page: Page, username: string, password: string): Promise<void>`**
   - Navigates to login page
   - Fills in credentials
   - Submits form
   - Waits for dashboard navigation
   - Validates successful login

3. **`logout(page: Page): Promise<void>`**
   - Clicks user menu
   - Clicks logout
   - Waits for login page
   - Validates logged out state

4. **`isAuthenticated(page: Page): Promise<boolean>`**
   - Checks for auth token in localStorage
   - Validates token expiration
   - Returns authentication status

### Page Object Methods

**File**: `tests/playwright/page-objects/protection-groups-page.ts`

#### Navigation Functions

1. **`navigateToPage(): Promise<void>`**
   - Navigates to `/protection-groups`
   - Waits for page load
   - Validates URL
   - Waits for data grid to render

2. **`waitForPageLoad(): Promise<void>`**
   - Waits for DataGrid component
   - Waits for "Create Group" button
   - Validates no loading spinners

#### Button Interaction Functions

3. **`clickCreateButton(): Promise<void>`**
   - Locates "Create Group" button
   - Clicks button
   - Waits for dialog to appear
   - Validates dialog is visible

4. **`isDialogOpen(): Promise<boolean>`**
   - Checks for dialog element
   - Validates dialog visibility
   - Returns boolean status

5. **`closeDialog(): Promise<void>`**
   - Clicks close button or ESC key
   - Waits for dialog to disappear
   - Validates dialog closed

#### Form Interaction Functions

6. **`fillGroupForm(data: GroupFormData): Promise<void>`**
   - Fills name field
   - Fills description field
   - Adds tag filters
   - Validates form state

7. **`addTagFilter(key: string, values: string[]): Promise<void>`**
   - Clicks "Add Filter" button
   - Fills key field
   - Adds multiple values
   - Validates filter chip appears

8. **`submitForm(): Promise<void>`**
   - Clicks "Create Group" button
   - Waits for API response
   - Validates toast notification
   - Waits for dialog to close

#### Validation Functions

9. **`verifyGroupInList(name: string): Promise<boolean>`**
   - Searches DataGrid for group name
   - Validates group appears
   - Returns boolean result

10. **`getGroupByName(name: string): Promise<ProtectionGroup | null>`**
    - Searches DataGrid for group
    - Returns group data if found
    - Returns null if not found

#### CRUD Operation Functions

11. **`editGroup(name: string, updates: Partial<GroupFormData>): Promise<void>`**
    - Clicks edit icon for group
    - Waits for edit dialog
    - Applies updates to form
    - Submits form
    - Validates success

12. **`deleteGroup(name: string): Promise<void>`**
    - Clicks delete icon for group
    - Waits for confirmation dialog
    - Confirms deletion
    - Waits for toast notification
    - Validates group removed

### Test Utility Functions

**File**: `tests/playwright/test-utils.ts`

#### Helper Functions

1. **`generateTestData(prefix: string): GroupFormData`**
   - Creates unique test data
   - Uses timestamp for uniqueness
   - Returns valid form data structure

2. **`waitForToast(page: Page, message: string): Promise<boolean>`**
   - Waits for toast notification
   - Validates message content
   - Returns success/failure
   - Handles timeout gracefully

3. **`captureScreenshot(page: Page, name: string): Promise<string>`**
   - Takes full-page screenshot
   - Saves to test artifacts
   - Returns file path
   - Includes timestamp in filename

4. **`checkConsoleErrors(page: Page): Promise<string[]>`**
   - Collects console errors
   - Filters by severity
   - Returns array of error messages
   - Useful for debugging

---

## [Classes]

### Authentication Manager

**File**: `tests/playwright/auth-helper.ts`

```typescript
export class AuthManager {
  constructor(
    private userPoolId: string,
    private clientId: string
  ) {}

  // Authenticate with Cognito
  async authenticate(username: string, password: string): Promise<AuthTokens> {
    // Implementation details
  }

  // Store tokens in browser localStorage
  async storeTokens(page: Page, tokens: AuthTokens): Promise<void> {
    // Implementation details
  }

  // Retrieve tokens from localStorage
  async getTokens(page: Page): Promise<AuthTokens | null> {
    // Implementation details
  }

  // Validate token expiration
  isTokenValid(token: string): boolean {
    // Implementation details
  }

  // Refresh expired token
  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    // Implementation details
  }
}
```

### Base Page Object

**File**: `tests/playwright/page-objects/base-page.ts`

```typescript
export abstract class BasePage {
  constructor(protected page: Page) {}

  // Navigate to page URL
  abstract navigateToPage(): Promise<void>;

  // Wait for page-specific elements
  abstract waitForPageLoad(): Promise<void>;

  // Common navigation
  async goToDashboard(): Promise<void> {
    await this.page.click('a[href="/"]');
    await this.page.waitForURL('/');
  }

  // Wait for element with timeout
  async waitForElement(selector: string, timeout: number = 5000): Promise<void> {
    await this.page.waitForSelector(selector, { timeout });
  }

  // Click with retry
  async clickWithRetry(selector: string, maxAttempts: number = 3): Promise<void> {
    // Implementation with retry logic
  }

  // Take screenshot
  async screenshot(name: string): Promise<string> {
    const path = `test-results/screenshots/${name}-${Date.now()}.png`;
    await this.page.screenshot({ path, fullPage: true });
    return path;
  }

  // Check for errors
  async hasConsoleErrors(): Promise<boolean> {
    // Implementation to check console errors
  }
}
```

### Protection Groups Page Object

**File**: `tests/playwright/page-objects/protection-groups-page.ts`

```typescript
export class ProtectionGroupsPage extends BasePage {
  // Selectors
  private readonly selectors = {
    createButton: 'button:has-text("Create Group")',
    dialog: '[role="dialog"]',
    nameField: 'input[name="name"]',
    descriptionField: 'textarea[name="description"]',
    addFilterButton: 'button:has-text("Add Filter")',
    submitButton: 'button:has-text("Create Group")',
    dataGrid: '[role="grid"]',
    editButton: (name: string) => `[data-group-name="${name}"] button[aria-label="Edit"]`,
    deleteButton: (name: string) => `[data-group-name="${name}"] button[aria-label="Delete"]`,
    confirmDeleteButton: 'button:has-text("Delete")',
    toast: '.Toastify__toast',
  };

  async navigateToPage(): Promise<void> {
    await this.page.goto('/protection-groups');
    await this.waitForPageLoad();
  }

  async waitForPageLoad(): Promise<void> {
    await this.page.waitForSelector(this.selectors.dataGrid);
    await this.page.waitForSelector(this.selectors.createButton);
  }

  async clickCreateButton(): Promise<void> {
    await this.page.click(this.selectors.createButton);
    await this.page.waitForSelector(this.selectors.dialog);
  }

  async isDialogOpen(): Promise<boolean> {
    return await this.page.isVisible(this.selectors.dialog);
  }

  async fillGroupForm(data: GroupFormData): Promise<void> {
    await this.page.fill(this.selectors.nameField, data.name);
    await this.page.fill(this.selectors.descriptionField, data.description);
    
    for (const filter of data.tagFilters) {
      await this.addTagFilter(filter.key, filter.values);
    }
  }

  async addTagFilter(key: string, values: string[]): Promise<void> {
    await this.page.click(this.selectors.addFilterButton);
    await this.page.fill('input[name="tagKey"]', key);
    
    for (const value of values) {
      await this.page.fill('input[name="tagValue"]', value);
      await this.page.press('input[name="tagValue"]', 'Enter');
    }
  }

  async submitForm(): Promise<void> {
    await this.page.click(this.selectors.submitButton);
    await this.waitForToast();
    await this.page.waitForSelector(this.selectors.dialog, { state: 'hidden' });
  }

  async verifyGroupInList(name: string): Promise<boolean> {
    const cellSelector = `[role="gridcell"]:has-text("${name}")`;
    return await this.page.isVisible(cellSelector);
  }

  async deleteGroup(name: string): Promise<void> {
    await this.page.click(this.selectors.deleteButton(name));
    await this.page.click(this.selectors.confirmDeleteButton);
    await this.waitForToast();
  }

  private async waitForToast(): Promise<void> {
    await this.page.waitForSelector(this.selectors.toast);
    await this.page.waitForSelector(this.selectors.toast, { state: 'hidden' });
  }
}
```

### Recovery Plans Page Object

**File**: `tests/playwright/page-objects/recovery-plans-page.ts`

```typescript
export class RecoveryPlansPage extends BasePage {
  // Similar structure to ProtectionGroupsPage
  // Specific selectors and methods for Recovery Plans
  
  private readonly selectors = {
    createButton: 'button:has-text("Create Plan")',
    dialog: '[role="dialog"]',
    nameField: 'input[name="name"]',
    descriptionField: 'textarea[name="description"]',
    protectionGroupSelect: 'select[name="protectionGroupId"]',
    addWaveButton: 'button:has-text("Add Wave")',
    submitButton: 'button:has-text("Create Plan")',
    // ... other selectors
  };

  // Implementation similar to ProtectionGroupsPage
  // with Recovery Plan-specific logic
}
```

---

## [Dependencies]

### NPM Packages

No new npm packages required - Playwright already available via Cline MCP integration.

**Verification**:
```bash
# Verify Playwright MCP is available
# Check Cline extension settings
```

### AWS Services Integration

1. **AWS Cognito** (Existing)
   - User Pool: `us-east-1_tj03fVI31`
   - Required for test user creation
   - Required for authentication in tests

2. **AWS CLI** (Existing)
   - Required for `create-test-user.sh` script
   - Must be authenticated with valid credentials

### Environment Variables

Create `.env.test` file with:

```bash
# Application URLs
CLOUDFRONT_URL=https://d20h85rw0j51j.cloudfront.net
API_ENDPOINT=https://etv40zymeg.execute-api.us-east-1.amazonaws.com/test

# Cognito Configuration
COGNITO_USER_POOL_ID=us-east-1_tj03fVI31
COGNITO_CLIENT_ID=<from-stack-outputs>
COGNITO_REGION=us-east-1

# Test User Credentials (created by script)
TEST_USER_USERNAME=drs-test-user
TEST_USER_PASSWORD=<generated-by-script>
TEST_USER_EMAIL=<your-test-email>

# Test Configuration
TEST_TIMEOUT=30000
TEST_RETRIES=2
HEADLESS=false
```

---

## [Testing]

### Manual Testing Strategy

**Reference Document**: `docs/MORNING_BUTTON_FIX_PLAN.md` (existing)

#### Phase 0: Pre-Deployment Verification (NEW)

Run Playwright smoke tests before deploying fixes:

```bash
# Navigate to project
cd AWS-DRS-Orchestration/

# Run smoke tests against current deployment
bash scripts/run-tests.sh smoke

# Expected result: Tests should FAIL confirming button issue
# If tests PASS, button issue may be intermittent or resolved
```

#### Phase 1-5: Existing Manual Testing Phases

Follow existing MORNING_BUTTON_FIX_PLAN.md for:
- Phase 1: Diagnostic Testing (15 minutes)
- Phase 2: Fix Implementation (5-10 minutes)
- Phase 3: Deployment (10 minutes)
- Phase 4: Verification Testing (15 minutes)
- Phase 5: Documentation (10 minutes)

#### Phase 6: Post-Fix Regression Tests (NEW)

After successful manual verification:

```bash
# Run comprehensive Playwright tests
bash scripts/run-tests.sh all

# Expected result: All tests PASS
# If any tests fail, investigate and fix before marking complete
```

### Automated Playwright Testing Strategy

#### Test Suite Organization

1. **Smoke Tests** (`smoke-tests.spec.ts`)
   - **Purpose**: Quick validation of critical functionality
   - **Duration**: 2-3 minutes
   - **When to Run**: After every deployment
   - **Coverage**:
     - Login functionality
     - Protection Groups button responsiveness
     - Recovery Plans button responsiveness
     - Dialog open/close behavior
     - Navigation between pages

2. **Protection Groups CRUD** (`protection-groups-crud.spec.ts`)
   - **Purpose**: Comprehensive Protection Groups testing
   - **Duration**: 5-7 minutes
   - **When to Run**: Before production deployments
   - **Coverage**:
     - Create protection group with tag filters
     - Edit protection group
     - Delete protection group
     - List view validation
     - Form validation
     - API integration
     - Toast notifications

3. **Recovery Plans CRUD** (`recovery-plans-crud.spec.ts`)
   - **Purpose**: Comprehensive Recovery Plans testing
   - **Duration**: 5-7 minutes
   - **When to Run**: Before production deployments
   - **Coverage**:
     - Create recovery plan with waves
     - Edit recovery plan
     - Delete recovery plan
     - Wave configuration
     - Protection group selection
     - Form validation
     - API integration

#### Test Execution Workflows

**Daily Development**:
```bash
# Quick smoke test
npm run test:smoke

# Or via Cline MCP Playwright tool
# Navigate to smoke-tests.spec.ts and run tests
```

**Pre-Deployment**:
```bash
# Full test suite
npm run test:all

# Or run specific suite
npm run test:protection-groups
npm run test:recovery-plans
```

**Post-Deployment Verification**:
```bash
# Run against production CloudFront URL
npm run test:smoke -- --base-url=https://d20h85rw0j51j.cloudfront.net

# Check for regressions
npm run test:all -- --base-url=https://d20h85rw0j51j.cloudfront.net
```

#### Test Data Management

**Test Data Strategy**:
- Generate unique data per test run using timestamps
- Clean up test data after test completion
- Use descriptive naming: `Test Group [Timestamp]`
- Isolate tests to prevent interference

**Example Test Data**:
```typescript
const testGroup: GroupFormData = {
  name: `Test Group ${Date.now()}`,
  description: `Created by automated test at ${new Date().toISOString()}`,
  tagFilters: [
    {
      key: 'Environment',
      values: ['test', 'staging']
    },
    {
      key: 'Application',
      values: ['web-app']
    }
  ]
};
```

#### Test Result Reporting

**Success Reporting**:
- All tests pass → Console output + test report HTML
- Screenshots saved on failure
- Test execution summary

**Failure Reporting**:
- Failed test details with error messages
- Full-page screenshots at failure point
- Console logs captured
- Network request/response logs
- Step-by-step trace

**Example Output**:
```
Smoke Tests Suite
  ✓ User can login successfully (2.3s)
  ✓ Protection Groups button opens dialog (0.8s)
  ✓ Recovery Plans button opens dialog (0.7s)
  ✓ Dialog can be closed (0.5s)

Protection Groups CRUD Suite
  ✓ Create protection group (3.2s)
  ✓ Edit protection group (2.5s)
  ✓ Delete protection group (1.8s)

Recovery Plans CRUD Suite
  ✓ Create recovery plan (4.1s)
  ✓ Edit recovery plan (3.3s)
  ✓ Delete recovery plan (2.0s)

Total: 10 tests, 10 passed, 0 failed
Duration: 21.2 seconds
```

---

## [Implementation Order]

Execute in this specific sequence to ensure dependencies are met and testing can proceed incrementally.

### Step 1: Environment Setup (30 minutes)

1. **Create test user in Cognito**
   ```bash
   # Create and run script
   bash scripts/create-test-user.sh
   ```
   - Creates dedicated test user
   - Outputs credentials
   - Saves to `.env.test`

2. **Configure environment variables**
   - Copy `.env.test.example` to `.env.test`
   - Fill in CloudFront URL
   - Fill in Cognito configuration
   - Add test user credentials

3. **Verify Playwright MCP connection**
   - Check Cline extension settings
   - Verify Playwright server running
   - Test basic navigation

**Validation**: Can authenticate test user and access CloudFront URL

### Step 2: Create Test Infrastructure (45 minutes)

4. **Create Playwright configuration**
   - File: `tests/playwright/playwright.config.ts`
   - Configure browsers (Chromium, Firefox)
   - Set base URL from environment
   - Configure timeouts and retries
   - Set up screenshot/video options

5. **Create authentication helper**
   - File: `tests/playwright/auth-helper.ts`
   - Implement Cognito authentication
   - Token management
   - Login/logout utilities

6. **Create base page object**
   - File: `tests/playwright/page-objects/base-page.ts`
   - Common navigation methods
   - Wait utilities
   - Screenshot helpers

**Validation**: Can authenticate and navigate to dashboard

### Step 3: Create Page Objects (60 minutes)

7. **Create Protection Groups page object**
   - File: `tests/playwright/page-objects/protection-groups-page.ts`
   - All CRUD operation methods
   - Selector definitions
   - Validation methods

8. **Create Recovery Plans page object**
   - File: `tests/playwright/page-objects/recovery-plans-page.ts`
   - All CRUD operation methods
   - Selector definitions
   - Wave configuration methods

9. **Create test utilities**
   - File: `tests/playwright/test-utils.ts`
   - Test data generators
   - Toast notification helpers
   - Console error checkers

**Validation**: Page objects can navigate and interact with UI

### Step 4: Create Smoke Tests (30 minutes)

10. **Write smoke test suite**
    - File: `tests/playwright/smoke-tests.spec.ts`
    - Login test
    - Button responsiveness tests
    - Dialog open/close tests
    - Navigation tests

11. **Run smoke tests against current deployment**
    ```bash
    npm run test:smoke
    ```

**Validation**: Smoke tests FAIL confirming button issue

### Step 5: Create CRUD Test Suites (90 minutes)

12. **Write Protection Groups CRUD tests**
    - File: `tests/playwright/protection-groups-crud.spec.ts`
    - Create test with tag filters
    - Edit test with validation
    - Delete test with confirmation
    - List view verification

13. **Write Recovery Plans CRUD tests**
    - File: `tests/playwright/recovery-plans-crud.spec.ts`
    - Create test with waves
    - Edit test with wave updates
    - Delete test with confirmation
    - Protection group selection

**Validation**: CRUD tests written and can be executed (expect failures)

### Step 6: Create Execution Scripts (30 minutes)

14. **Create test execution wrapper**
    - File: `scripts/run-tests.sh`
    - Environment setup
    - Suite selection (smoke/crud/all)
    - Result reporting

15. **Add npm test scripts**
    - Update `package.json`
    - Add `test:smoke`, `test:crud`, `test:all`
    - Add `test:watch` for development

16. **Update `.gitignore`**
    - Ignore test artifacts
    - Ignore `.env.test`
    - Ignore screenshots/videos

**Validation**: Can run tests via npm scripts

### Step 7: Documentation (45 minutes)

17. **Create TESTING_STRATEGY.md**
    - File: `docs/TESTING_STRATEGY.md`
    - Overview of testing approach
    - Manual vs automated testing
    - Execution workflows
    - Troubleshooting guide

18. **Create PLAYWRIGHT_TEST_GUIDE.md**
    - File: `docs/PLAYWRIGHT_TEST_GUIDE.md`
    - Test suite details
    - Running tests locally
    - Debugging failed tests
    - Extending coverage

19. **Enhance MORNING_BUTTON_FIX_PLAN.md**
    - Add Phase 0: Pre-deployment verification
    - Add Phase 6: Post-fix regression tests
    - Add references to automated tests
    - Add troubleshooting flowchart

**Validation**: Documentation complete and accurate

### Step 8: Execute Manual Testing (60 minutes)

20. **Follow MORNING_BUTTON_FIX_PLAN.md phases**
    - Phase 1: Diagnostic testing
    - Phase 2: Implement fix (rebuild React app)
    - Phase 3: Deploy to S3/CloudFront
    - Phase 4: Verification testing
    - Phase 5: Documentation

**Validation**: Button responsiveness fixed manually

### Step 9: Post-Fix Validation (15 minutes)

21. **Run smoke tests against fixed deployment**
    ```bash
    npm run test:smoke
    ```

22. **Run full CRUD test suites**
    ```bash
    npm run test:all
    ```

**Validation**: All automated tests PASS

### Step 10: Final Documentation (15 minutes)

23. **Update PROJECT_STATUS.md**
    - Add Session 27 entry
    - Document testing strategy
    - Note test coverage
    - Update MVP percentage

24. **Create SESSION_27_SUMMARY.md**
    - Problem statement
    - Root cause analysis
    - Solution implemented
    - Testing results
    - Lessons learned

**Validation**: Complete documentation of testing strategy and results

---

## Expected Outcomes

### Success Criteria

#### Manual Testing Success

**Phase 1 Diagnostics**:
- ✅ Console errors identified and documented
- ✅ Network requests captured and analyzed
- ✅ Root cause confirmed (stale bundles vs runtime error)

**Phase 2 Fix Implementation**:
- ✅ React app rebuilt with `npx vite build`
- ✅ New dist/ folder created with fresh bundles
- ✅ Bundle contents verified (handleCreate functions present)

**Phase 3 Deployment**:
- ✅ Fresh dist/ uploaded to S3
- ✅ CloudFront invalidation completed
- ✅ New bundles served to users

**Phase 4 Verification**:
- ✅ Protection Groups "Create Group" button works
- ✅ Dialog opens and form is functional
- ✅ Create/Edit/Delete operations work
- ✅ Recovery Plans "Create Plan" button works
- ✅ Dialog opens and form is functional
- ✅ Create/Edit/Delete operations work
- ✅ Console shows no errors
- ✅ Toast notifications display correctly

#### Automated Testing Success

**Smoke Tests**:
- ✅ All 4 smoke tests pass
- ✅ Button clicks trigger dialogs
- ✅ Dialogs can be closed
- ✅ No console errors detected
- ✅ Execution time: < 3
