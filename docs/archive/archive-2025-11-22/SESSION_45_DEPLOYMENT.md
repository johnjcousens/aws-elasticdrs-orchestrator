# Session 45 - Deployment Instructions

**Date**: November 22, 2025 - 9:44 AM EST  
**Status**: Fresh vite build ready for deployment  
**Critical Issue**: Protection Group dropdown completely broken (onChange not firing)

---

## 🚨 CRITICAL ISSUE SUMMARY

**Problem**: Protection Group Autocomplete dropdown is completely broken
- User can see all options in dropdown (WebServers, AppServers, DatabaseServers)
- **Clicking on any option does NOTHING** - no selection occurs
- Affects ALL waves (not just Wave 2+)
- onChange handler not firing at all

**Root Cause**: Suspected deployment/cache issue
- Session 43 fix (commit 6ed89e6) was committed at 8:19 PM on Nov 20
- Build at 9:39 PM should have included the fix
- User's browser shows broken behavior → old code still cached

**Solution**: Fresh deployment with CloudFront invalidation

---

## 📦 DEPLOYMENT STEPS

### Step 1: Refresh AWS Credentials

Your AWS credentials have expired. Refresh them:

```bash
# Option 1: Using AWS SSO
aws sso login --profile your-profile

# Option 2: Using ada credentials
ada credentials update --account=YOUR_ACCOUNT --role=YOUR_ROLE --provider=isengard

# Verify credentials work
aws sts get-caller-identity
```

### Step 2: Get CloudFront and S3 Details

```bash
cd /Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS/CODE/GITHUB/AWS-DRS-Orchestration

# Get frontend stack outputs
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket` || OutputKey==`CloudFrontDistributionId`].[OutputKey,OutputValue]' \
  --output text

# This will show:
# FrontendBucket           drs-orchestration-frontend-xxxx
# CloudFrontDistributionId E1234567890ABC
```

### Step 3: Deploy Fresh Build to S3

The fresh vite build is ready in `frontend/dist/` (built at 9:43 AM):

```bash
# Get bucket name from Step 2, then:
BUCKET_NAME="drs-orchestration-frontend-xxxx"  # Replace with actual bucket

# Sync new build to S3
aws s3 sync frontend/dist/ s3://${BUCKET_NAME}/ --delete

# Verify upload
aws s3 ls s3://${BUCKET_NAME}/assets/ --recursive | head -5
```

### Step 4: Invalidate CloudFront Cache

**CRITICAL**: CloudFront caching is why user sees old code

```bash
# Get distribution ID from Step 2, then:
DISTRIBUTION_ID="E1234567890ABC"  # Replace with actual distribution

# Create invalidation for all files
aws cloudfront create-invalidation \
  --distribution-id ${DISTRIBUTION_ID} \
  --paths "/*"

# Monitor invalidation status (takes 1-3 minutes)
aws cloudfront list-invalidations \
  --distribution-id ${DISTRIBUTION_ID} \
  --max-items 1
```

### Step 5: Verify Deployment

```bash
# Check CloudFront URL (from stack outputs)
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-frontend \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
  --output text

# Should return: https://dxxxxxxxxxxxx.cloudfront.net
```

---

## 🧪 TESTING AFTER DEPLOYMENT

### Test 1: Browser Hard Refresh
1. Open CloudFront URL in browser
2. Press **Cmd+Shift+R** (Mac) or **Ctrl+Shift+F5** (Windows) for hard refresh
3. Check DevTools Console (F12) for any JavaScript errors

### Test 2: Protection Group Dropdown (ALL Waves)

**Wave 1 Test:**
1. Click "New Recovery Plan"
2. Add Wave 1
3. Click Protection Groups dropdown
4. Try to select "WebServers"
5. **VERIFY**: Selection appears as chip/tag
6. **VERIFY**: Servers show up in server dropdown below

**Wave 2 Test:**
1. Add Wave 2 to same plan
2. Click Protection Groups dropdown
3. Try to select "AppServers"
4. **VERIFY**: Selection appears as chip/tag
5. **VERIFY**: Servers show up in server dropdown

**Expected Behavior:**
- Clicking on any Protection Group should select it immediately
- Selected PG appears as chip/tag in the field
- Servers from that PG appear in server dropdown below
- No JavaScript errors in console

### Test 3: Recovery Plan Operations

Once Protection Group selection works:

```bash
cd tests/python/e2e

# Test CREATE (should still work)
python test_recovery_plan_api_crud.py -k test_create_recovery_plan

# Test UPDATE (needs testing)
python test_recovery_plan_api_crud.py -k test_update_recovery_plan

# Test DELETE (needs testing)
python test_recovery_plan_api_crud.py -k test_delete_recovery_plan
```

---

## 🔍 TROUBLESHOOTING

### If Protection Group dropdown still doesn't work:

1. **Check browser DevTools Console** for JavaScript errors
   - Look for red error messages
   - Look for "Autocomplete" or "onChange" related errors

2. **Verify new code is loaded**:
   - In DevTools → Network tab
   - Hard refresh (Cmd+Shift+R)
   - Look for `index-*.js` files
   - Check file hash in filename matches new build
   - New build file: `index-ZNr9IfMZ.js` (from 9:43 AM build)

3. **Check CloudFront invalidation completed**:
   ```bash
   aws cloudfront get-invalidation \
     --distribution-id ${DISTRIBUTION_ID} \
     --id <INVALIDATION_ID_FROM_STEP_4>
   ```

4. **If still broken**: The fix in commit 6ed89e6 may not be sufficient
   - Will need to investigate actual Autocomplete component behavior
   - May need to add console.log debugging to onChange handler

---

## 📊 BUILD ARTIFACTS

**Fresh Build Location**: `frontend/dist/`  
**Build Time**: November 22, 2025 - 9:43:01 AM EST  
**Build Tool**: vite 7.2.2  
**Build Size**: ~1.3 MB total (265KB main bundle)

**Key Files**:
- `index-ZNr9IfMZ.js` (266.42 KB) - Main bundle with WaveConfigEditor fix
- `vendor-mui-core-Cce6iq33.js` (413.96 KB) - MUI components including Autocomplete
- `index.html` (2.30 KB) - Entry point

---

## 📝 NEXT STEPS AFTER DEPLOYMENT

1. ✅ Verify Protection Group dropdown works in ALL waves
2. ✅ Test Recovery Plan UPDATE operation
3. ✅ Test Recovery Plan DELETE operation
4. ✅ Run full end-to-end test suite
5. ✅ Update SESSION_45_TESTING_PLAN.md with results
6. ✅ Commit and document successful deployment

---

## 🆘 IF YOU NEED HELP

If deployment fails or Protection Group dropdown still broken after deployment:

1. **Check this file** for troubleshooting steps above
2. **Check browser console** for JavaScript errors (F12 → Console)
3. **Share error messages** so we can diagnose the real issue
4. **Verify CloudFront invalidation** completed successfully

The fresh build at 9:43 AM should fix the issue. If it doesn't, we need to dig deeper into why the Autocomplete onChange handler isn't firing.
