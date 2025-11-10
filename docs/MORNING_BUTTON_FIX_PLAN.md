# Morning Button Fix Execution Plan

**Session 27 Continuation - November 10, 2025**

**Problem**: "Create New" buttons on Protection Groups and Recovery Plans pages are not responding when clicked.

**Source Code Analysis**: All React components are correctly implemented. Button handlers, dialog state management, and event bindings are proper.

**Hypothesis**: Deployed JavaScript bundles in `dist/` folder are outdated and don't reflect current source code (similar to Session 25 Extended configuration fix).

---

## Pre-Work Setup (5 minutes)

**Before starting execution:**

- [ ] Open **Firefox browser** (known to work with fresh cache)
- [ ] Have terminal ready in `AWS-DRS-Orchestration/frontend/` directory
- [ ] Verify AWS CLI authenticated: `aws sts get-caller-identity`
- [ ] Clear browser cache **OR** use Private/Incognito window
- [ ] Have this document open for reference

**Application Details:**
- CloudFront URL: `https://d20h85rw0j51j.cloudfront.net`
- Stack Name: `drs-orchestration-test`
- API Endpoint: `https://etv40zymeg.execute-api.us-east-1.amazonaws.com/test`
- User Pool: `us-east-1_tj03fVI31`

---

## Phase 1: Diagnostic Testing (15 minutes)

### Step 1A: Live Browser Debugging

**Goal**: Capture exact error state and behavior

```bash
# Open application in Firefox
URL: https://d20h85rw0j51j.cloudfront.net
```

**Protection Groups Testing:**
1. [ ] Open Firefox DevTools (F12)
2. [ ] Go to Console tab
3. [ ] Navigate to Protection Groups page
4. [ ] Click "Create Group" button
5. [ ] Document observations:
   - [ ] Does button show hover effect when mousing over?
   - [ ] Any console errors appear in red?
   - [ ] Does dialog flash briefly then disappear?
   - [ ] Nothing happens at all?
6. [ ] Take screenshot of console (Cmd+Shift+4 on Mac)

**Recovery Plans Testing:**
7. [ ] Navigate to Recovery Plans page
8. [ ] Click "Create Plan" button
9. [ ] Document same observations as above
10. [ ] Take screenshot if different errors

**Record Findings Here:**
```
Protection Groups button:
- Behavior: _______________________________
- Console errors: _________________________

Recovery Plans button:
- Behavior: _______________________________
- Console errors: _________________________
```

### Step 1B: Network Tab Analysis

**Goal**: Verify JavaScript bundles are loading correctly

1. [ ] Open Firefox DevTools → Network tab
2. [ ] Clear network log
3. [ ] Reload page (Cmd+Shift+R for hard reload)
4. [ ] Filter by "JS" files
5. [ ] Check for issues:
   - [ ] Any 404 errors on JavaScript files?
   - [ ] Are bundles loading from CloudFront?
   - [ ] Check file sizes (should be hundreds of KB)
   - [ ] Response headers showing correct `content-type: application/javascript`?
6. [ ] Note any anomalies

### Step 1C: React DevTools (Optional - Advanced)

**Only if you have React DevTools extension installed:**

1. [ ] Open React DevTools → Components tab
2. [ ] Find `ProtectionGroupsPage` component
3. [ ] Watch `dialogOpen` state when clicking "Create Group"
4. [ ] Expected behavior: `false` → `true` transition
5. [ ] If it stays `false`: Event handler not firing
6. [ ] If it goes `true` → `false` quickly: Dialog mounting issue

---

## Diagnostic Decision Tree

Based on Phase 1 findings, proceed to appropriate Phase 2 section:

**→ Console shows JavaScript errors?**
- Go to **Phase 2A: Fix Runtime Errors**

**→ No console errors, buttons don't work?**
- Go to **Phase 2B: Fix Stale Bundles** ⭐ **(Most Likely)**

**→ Dialog flashes then immediately closes?**
- Go to **Phase 2C: Fix React State Issue**

**→ Network tab shows 404 errors on JS files?**
- Go to **Phase 2B** then check CloudFormation stack outputs

---

## Phase 2A: Fix Runtime Errors

**Use this section if console shows errors like:**
- "Cannot read property 'open' of undefined"
- "setDialogOpen is not a function"
- Any React or MUI component errors

### Commands:

```bash
# Navigate to frontend directory
cd AWS-DRS-Orchestration/frontend/

# Check for missing dependencies
npm install

# Clear Vite cache
rm -rf node_modules/.vite

# Fresh build
npx vite build

# Verify build succeeded
echo "Build exit code: $?"
ls -lh dist/assets/*.js | head -5
```

**After build completes, proceed to Phase 3: Deployment**

---

## Phase 2B: Fix Stale Bundles ⭐ (Most Likely Scenario)

**This mirrors the Session 25 Extended fix pattern**

The source code is correct, but the deployed bundles don't reflect current code. This happens when:
- Code changes made without rebuilding `dist/`
- Build artifacts were not uploaded to S3
- Old bundles cached by CloudFront/browser

### Commands:

```bash
# Navigate to frontend directory
cd AWS-DRS-Orchestration/frontend/

# Step 1: Clean all build artifacts
rm -rf dist/
rm -rf node_modules/.vite

# Step 2: Fresh build with Vite
npx vite build

# Step 3: Verify build output
ls -lh dist/
ls -lh dist/assets/

# Should see fresh timestamps on:
# - index-[hash].js (main bundle)
# - aws-config.js (configuration)
# - Various chunk files

# Step 4: Optional - Verify bundle contents
echo "Checking for handleCreate function in bundles..."
grep -r "handleCreate" dist/assets/*.js | wc -l
# Should see multiple matches (>0)

# Step 5: Check bundle sizes (sanity check)
du -sh dist/
# Should be a few MB total
```

**Expected Output:**
```
dist/
  index.html
  assets/
    aws-config.js
    index-[hash].js      (~500-800 KB)
    index-[hash].css     (~50-100 KB)
    [various chunks]
```

**After successful build, proceed to Phase 3: Deployment**

---

## Phase 2C: Fix React State Issue

**Use this section if:**
- Dialog flashes briefly then immediately closes
- No console errors present
- Buttons trigger visual feedback

**This suggests parent component unmounting or re-rendering**

### Investigation Steps:

```bash
# Check for React warnings in console
# Look for: "Warning: Can't perform a React state update on an unmounted component"

# Common causes:
# 1. PageTransition component wrapper timing
# 2. Error boundary catching and resetting
# 3. Route changes triggering remounts
```

### Potential Fixes:

Check these files for issues:
- `frontend/src/components/PageTransition.tsx`
- `frontend/src/components/ErrorBoundary.tsx`
- `frontend/src/pages/ProtectionGroupsPage.tsx`

**If you identify the issue, fix it, then rebuild and proceed to Phase 3**

**If unclear, document findings and seek assistance**

---

## Phase 3: Deployment (10 minutes)

### Step 3A: Upload to S3

```bash
# Navigate to frontend directory (if not already there)
cd AWS-DRS-Orchestration/frontend/

# Get S3 bucket name from CloudFormation stack
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

echo "S3 Bucket: $BUCKET_NAME"
# Should output something like: drs-orchestration-test-frontend-bucket-xxxxx

# Verify bucket exists
aws s3 ls s3://${BUCKET_NAME}/ | head -5

# Sync dist/ to S3 with proper cache headers
# Most files: long cache (1 year, immutable)
aws s3 sync dist/ s3://${BUCKET_NAME}/ \
  --delete \
  --cache-control "max-age=31536000,public,immutable" \
  --exclude "*.html" \
  --exclude "aws-config.js"

# HTML files: no cache (always fresh)
aws s3 cp dist/index.html s3://${BUCKET_NAME}/index.html \
  --cache-control "no-cache,must-revalidate"

# Config file: no cache (contains dynamic values)
aws s3 cp dist/assets/aws-config.js s3://${BUCKET_NAME}/assets/aws-config.js \
  --cache-control "no-cache,must-revalidate"

# Verify upload
aws s3 ls s3://${BUCKET_NAME}/assets/ | grep "\.js" | head -10
```

### Step 3B: Invalidate CloudFront Cache

```bash
# Get CloudFront distribution ID
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text)

echo "CloudFront Distribution: $DISTRIBUTION_ID"
# Should output something like: E1ABCDEFG12345

# Create invalidation for all paths
INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id ${DISTRIBUTION_ID} \
  --paths "/*" \
  --query 'Invalidation.Id' \
  --output text)

echo "Invalidation ID: $INVALIDATION_ID"

# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id ${DISTRIBUTION_ID} \
  --id ${INVALIDATION_ID} \
  --query 'Invalidation.Status' \
  --output text

# Status will be "InProgress" initially, then "Completed"
```

**⏰ Wait Time**: CloudFront invalidation takes **2-5 minutes**

**While waiting:**
- [ ] Take a break
- [ ] Review Phase 4 testing checklist
- [ ] Prepare fresh browser window

**Check invalidation status:**
```bash
# Run this command every 60 seconds
aws cloudfront get-invalidation \
  --distribution-id ${DISTRIBUTION_ID} \
  --id ${INVALIDATION_ID} \
  --query 'Invalidation.Status' \
  --output text

# When it shows "Completed", proceed to Phase 4
```

---

## Phase 4: Verification Testing (15 minutes)

### Step 4A: Fresh Browser Setup

**CRITICAL**: Use a **completely fresh browser context**

**Option 1: Private/Incognito Window (Recommended)**
```bash
# Firefox: Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows/Linux)
# Chrome: Cmd+Shift+N (Mac) or Ctrl+Shift+N (Windows/Linux)
```

**Option 2: Clear Cache**
```bash
# Firefox: Cmd+Shift+Delete → Check "Cache" → Clear Now
```

**Why this matters**: Your regular browser may still serve old JavaScript from cache despite CloudFront invalidation.

### Step 4B: Login Test

1. [ ] Open private window
2. [ ] Navigate to: `https://d20h85rw0j51j.cloudfront.net`
3. [ ] Open DevTools Console (F12) - keep it open throughout testing
4. [ ] Log in with credentials
5. [ ] Verify dashboard loads
6. [ ] Check console for any errors during login

### Step 4C: Protection Groups CRUD Test

**Create Test:**
1. [ ] Navigate to Protection Groups page
2. [ ] Click "Create Group" button
3. [ ] **✓ VERIFY**: Dialog opens successfully
4. [ ] Fill form:
   - Name: `Test Group Morning [Timestamp]`
   - Description: `Testing button fix from Session 27`
   - Tag Filter: 
     - Key: `Environment`
     - Values: `production`
5. [ ] Click "Create Group" button in dialog
6. [ ] **✓ VERIFY**: Success toast appears (green notification)
7. [ ] **✓ VERIFY**: Group appears in list with correct data
8. [ ] **✓ VERIFY**: No console errors

**Edit Test:**
9. [ ] Find the newly created group in list
10. [ ] Click Edit icon (pencil) on the group
11. [ ] **✓ VERIFY**: Edit dialog opens with existing data
12. [ ] Change description to: `Updated at [Time]`
13. [ ] Click "Save Changes"
14. [ ] **✓ VERIFY**: Success toast appears
15. [ ] **✓ VERIFY**: Updated description shows in list

**Delete Test:**
16. [ ] Click Delete icon (trash) on the test group
17. [ ] **✓ VERIFY**: Confirmation dialog appears
18. [ ] Click "Delete" to confirm
19. [ ] **✓ VERIFY**: Success toast appears
20. [ ] **✓ VERIFY**: Group removed from list

### Step 4D: Recovery Plans CRUD Test

**Create Test:**
1. [ ] Navigate to Recovery Plans page
2. [ ] Click "Create Plan" button
3. [ ] **✓ VERIFY**: Dialog opens successfully
4. [ ] Fill form - Basic Info:
   - Plan Name: `Test Plan Morning [Timestamp]`
   - Description: `Testing from Session 27`
5. [ ] Select Protection Group (if list is empty, create one first)
6. [ ] **✓ VERIFY**: Wave configuration section appears
7. [ ] Configure Wave 1:
   - Name: `Wave 1`
   - Delay: `300` seconds
   - Add at least one server
8. [ ] Click "Create Plan"
9. [ ] **✓ VERIFY**: Success toast appears
10. [ ] **✓ VERIFY**: Plan appears in list
11. [ ] **✓ VERIFY**: Wave count shows "1 wave"

**Edit Test:**
12. [ ] Click Edit icon on test plan
13. [ ] **✓ VERIFY**: Edit dialog opens with data
14. [ ] Change description
15. [ ] Click "Update Plan"
16. [ ] **✓ VERIFY**: Success toast and update reflected

**Delete Test:**
17. [ ] Click Delete icon on test plan
18. [ ] Confirm deletion
19. [ ] **✓ VERIFY**: Plan removed from list

### Step 4E: Console Verification

**Throughout all testing above:**
- [ ] Console remained clear of errors
- [ ] No red error messages appeared
- [ ] No React warnings about unmounted components
- [ ] All API calls returned successfully (check Network tab)

### Step 4F: Cross-Browser Testing (Optional)

**Test in other browsers to verify cache isn't browser-specific:**

**Chrome (Private Window):**
1. [ ] Repeat Step 4B-4D in Chrome
2. [ ] Document if same or different behavior

**Safari (Private Window):**
1. [ ] Repeat Step 4B-4D in Safari
2. [ ] Document if same or different behavior

**Expected**: After 24 hours, all browsers should work. If Chrome/Safari fail immediately, it's aggressive browser caching.

---

## Phase 5: Documentation (10 minutes)

### Step 5A: Update PROJECT_STATUS.md

```bash
cd AWS-DRS-Orchestration/docs/

# Open PROJECT_STATUS.md for editing
code PROJECT_STATUS.md
```

**Add Session 27 entry in "Session Checkpoints" section:**

```markdown
**Session 27: Button Fix** (2025-11-10 - [Time Range])
- **Checkpoint**: `.cline_memory/conversations/conversation_export_[timestamp].md`
- **Git Commit**: `[hash if applicable]` - [message if code changed]
- **Summary**: Fixed "Create New" button responsiveness issue
- **Root Cause**: [Document what was found - e.g., "Outdated dist/ bundles not reflecting current source code"]
- **Solution**: [Document fix - e.g., "Rebuilt React app with vite build, uploaded fresh bundles to S3, invalidated CloudFront"]
- **Technical Achievements**:
  - Diagnosed button handler implementation (source code correct)
  - Identified stale build artifact deployment issue
  - Successfully rebuilt and redeployed frontend
  - Verified complete CRUD operations for Protection Groups
  - Verified complete CRUD operations for Recovery Plans
- **Result**: Buttons now working correctly, all CRUD operations functional
- **Lines of Code**: [If source code changed, note lines]
- **Browser Notes**: Firefox working immediately, Chrome/Safari may need 24h cache expiry
- **Next Steps**: Complete Phase 7.7 User Preferences (4% remaining for MVP 100%)
```

### Step 5B: Create Session Summary

**Create file:** `AWS-DRS-Orchestration/docs/SESSION_27_SUMMARY.md`

```markdown
# Session 27: Button Fix Summary

## Problem Statement
"Create New" buttons on Protection Groups and Recovery Plans pages were unresponsive when clicked. Users could navigate the application and view data, but could not create new resources.

## Investigation Process

### Source Code Analysis
- Examined `ProtectionGroupsPage.tsx` - button handlers correct
- Examined `RecoveryPlansPage.tsx` - button handlers correct
- Examined `ProtectionGroupDialog.tsx` - dialog state management correct
- Examined `RecoveryPlanDialog.tsx` - dialog state management correct

**Conclusion**: Source code properly implemented.

### Live Debugging
[Document what you found in Phase 1]
- Browser console errors: [Yes/No - describe if yes]
- Network issues: [Yes/No - describe if yes]
- React state issues: [Yes/No - describe if yes]

## Root Cause
[Document the actual root cause identified]

Example: "The deployed JavaScript bundles in dist/ folder were outdated and did not reflect the current source code. Despite correct implementation in source files, the production bundles served to users contained old code without the button handlers."

## Solution Implemented
[Document what you actually did]

Example:
1. Cleaned build artifacts (dist/ and node_modules/.vite)
2. Rebuilt React application with `npx vite build`
3. Uploaded fresh dist/ folder to S3 bucket
4. Invalidated CloudFront cache with `/*` path
5. Tested in fresh Firefox browser window

## Testing Results
- Protection Groups Create: [✓ Working / ✗ Failed]
- Protection Groups Edit: [✓ Working / ✗ Failed]
- Protection Groups Delete: [✓ Working / ✗ Failed]
- Recovery Plans Create: [✓ Working / ✗ Failed]
- Recovery Plans Edit: [✓ Working / ✗ Failed]
- Recovery Plans Delete: [✓ Working / ✗ Failed]

## Lessons Learned

### What Worked
- [List what worked well]
- Example: "Fresh browser context essential for testing"

### What Didn't Work
- [List any challenges]
- Example: "Chrome aggressively cached old bundles even after invalidation"

### Key Takeaways
1. Always rebuild React app after source code changes
2. Verify dist/ folder contents before deployment
3. Use fresh browser context for testing major changes
4. CloudFront invalidation takes 2-5 minutes to propagate

## Next Steps
1. [ ] Complete Phase 7.7: User Preferences (4% remaining)
2. [ ] Deploy to production environment
3. [ ] Update README with deployment best practices
4. [ ] Consider CI/CD automation to prevent similar issues
```

### Step 5C: Git Commit (If Code Changed)

**Only if you modified source code files:**

```bash
cd AWS-DRS-Orchestration/

# Check what changed
git status

# If source code was modified:
git add frontend/src/

git commit -m "fix: Resolve Create New button responsiveness issue

- Root cause: [brief description]
- Solution: [brief description]
- Testing: All CRUD operations verified working

Related: Session 27"

# If only documentation changed:
git add docs/

git commit -m "docs: Add Session 27 button fix documentation

- Created MORNING_BUTTON_FIX_PLAN.md execution guide
- Created SESSION_27_SUMMARY.md with findings
- Updated PROJECT_STATUS.md with session entry"
```

---

## Rollback Plan

**If Phase 4 testing fails after deployment:**

### Option 1: Revert to Previous Dist Version

```bash
cd AWS-DRS-Orchestration/

# Check git history
git -P log --oneline frontend/dist/ | head -10

# Identify last known working commit
# Example: 3e71648 was Session 26 (known working)

# Revert dist/ folder
git checkout 3e71648 -- frontend/dist/

# Re-upload to S3
cd frontend/
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text)

aws s3 sync dist/ s3://${BUCKET_NAME}/ --delete

# Invalidate CloudFront
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id ${DISTRIBUTION_ID} \
  --paths "/*"
```

### Option 2: Revert Source Code Changes

**If you modified source files and they caused issues:**

```bash
# See what was changed
git diff HEAD frontend/src/

# Revert specific file
git checkout HEAD -- frontend/src/pages/ProtectionGroupsPage.tsx

# Or revert all frontend changes
git checkout HEAD -- frontend/src/

# Rebuild
cd frontend/
npx vite build

# Redeploy (see Phase 3)
```

### Option 3: Request Assistance

**If unable to resolve:**

1. Document all findings in SESSION_27_SUMMARY.md
2. Include screenshots of console errors
3. Note exact steps taken and results
4. Create detailed issue report for collaboration

---

## Success Criteria

### Must Pass All of These:

✅ **Phase 4B-4C: Protection Groups**
- "Create Group" button opens dialog
- Form submission creates group successfully
- Group appears in list with correct data
- Edit operation works
- Delete operation works

✅ **Phase 4D: Recovery Plans**
- "Create Plan" button opens dialog
- Form submission creates plan successfully
- Plan appears in list with correct data
- Edit operation works
- Delete operation works

✅ **Phase 4E: Console Clean**
- No JavaScript errors during any operation
- No React warnings
- No network errors

✅ **Phase 4F: Browser Compatibility**
- Works in Firefox (minimum requirement)
- Works in Chrome after cache clears (within 24h)
- Works in Safari after cache clears (within 24h)

---

## Time Estimates

| Phase | Activity | Estimated Time |
|-------|----------|----------------|
| Pre-Work | Setup and authentication | 5 minutes |
| Phase 1 | Diagnostic testing | 15 minutes |
| Phase 2 | Implement fix | 5-10 minutes |
| Phase 3 | Deploy to S3/CloudFront | 10 minutes |
|  | *Wait for invalidation* | 2-5 minutes |
| Phase 4 | Verification testing | 15 minutes |
| Phase 5 | Documentation | 10 minutes |
| **Total** | | **~60 minutes** |

---

## Quick Reference Commands

**Get Stack Outputs:**
```bash
# S3 Bucket
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' \
  --output text

# CloudFront Distribution
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' \
  --output text

# CloudFront URL
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text
```

**Build & Deploy (Quick Reference):**
```bash
cd AWS-DRS-Orchestration/frontend/
rm -rf dist/ node_modules/.vite
npx vite build

BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name drs-orchestration-test-frontend --query 'Stacks[0].Outputs[?OutputKey==`BucketName`].OutputValue' --output text)

aws s3 sync dist/ s3://${BUCKET_NAME}/ --delete --cache-control "max-age=31536000,public,immutable" --exclude "*.html" --exclude "aws-config.js"
aws s3 cp dist/index.html s3://${BUCKET_NAME}/index.html --cache-control "no-cache,must-revalidate"
aws s3 cp dist/assets/aws-config.js s3://${BUCKET_NAME}/assets/aws-config.js --cache-control "no-cache,must-revalidate"

DISTRIBUTION_ID=$(aws cloudformation describe-stacks --stack-name drs-orchestration-test-frontend --query 'Stacks[0].Outputs[?OutputKey==`DistributionId`].OutputValue' --output text)

aws cloudfront create-invalidation --distribution-id ${DISTRIBUTION_ID} --paths "/*"
```

---

## Completion Checklist

**When done, verify you've completed:**

- [ ] All diagnostic tests documented
- [ ] Fix implemented and tested
- [ ] Deployment successful
- [ ] All CRUD operations verified working
- [ ] Console clean of errors
- [ ] PROJECT_STATUS.md updated with Session 27 entry
- [ ] SESSION_27_SUMMARY.md created with findings
- [ ] Git commit made (if applicable)
- [ ] Ready to proceed to Phase 7.7: User Preferences

**Current MVP Status After Success:**
- Phase 1-6: 100% Complete ✅
- Phase 7.1-7.6: 100% Complete ✅
- Phase 7.7 User Preferences: Pending (4% remaining)
- **Overall: 96% → Target 100%**

---

## Notes Section

**Use this space to document any deviations or observations:**

```
[Your notes here during execution]

Example:
- Phase 1: Found console error "Cannot read property..."
- Phase 2A: Fixed typo in ProtectionGroupsPage.tsx line 87
- Phase 4: Chrome still caching, Firefox works perfectly
- Next: Will wait 24h for Chrome cache to expire naturally
```

---

**Good luck! This plan is designed to be self-contained and executable even without real-time assistance.**
