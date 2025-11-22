# Session 45: Testing & Validation Plan

**Session**: 45  
**Date**: November 20, 2025  
**Time**: 10:05 PM EST  
**Context**: Post-Session 44 comprehensive testing

## Overview

This session focuses on validating all fixes from Sessions 42-44 and testing remaining untested functionality.

## Prerequisites

### Session 42-44 Achievements (Already Complete)
- ✅ VMware SRM schema alignment (removed bogus fields)
- ✅ Autocomplete selection bug fix (deployed to CloudFront)
- ✅ DRS server validation (real server ID enforcement)
- ✅ Git workflow completed (all changes committed to main)
- ✅ Repository cleanup (clean working tree)

### Current System State
- **DynamoDB**: 3 Protection Groups with 2 real DRS servers each
- **Lambda API**: DRS validation active
- **Frontend**: Autocomplete fix deployed (Cache ID: IPYSQE9HIFZ5AU2OBWXIQ7YCM)
- **Deployment Time**: 8:02 PM (Session 43)

## Testing Roadmap

### Phase 1: Browser Cache Refresh & UI Validation

#### Test 1.1: Browser Hard Refresh
**Objective**: Clear browser cache to load latest JavaScript

**Steps**:
1. Open browser with AWS DRS Orchestration UI
2. Perform hard refresh:
   - **Mac**: Cmd+Shift+R
   - **Windows**: Ctrl+Shift+R
   - **Linux**: Ctrl+Shift+R
3. Verify CloudFront cache timestamp
4. Check browser console for any errors

**Expected Result**: Browser loads JavaScript from post-8:02 PM deployment

**Verification**:
- Check Network tab in DevTools
- Verify JavaScript files show recent timestamp
- No 304 (cached) responses for main.js

**Status**: ⏳ PENDING USER ACTION

---

#### Test 1.2: Protection Group Dropdown (Wave 2+)
**Objective**: Verify Autocomplete fix works in Wave 2 and beyond

**Preconditions**:
- Browser cache cleared (Test 1.1 complete)
- User logged into UI
- On Recovery Plans page

**Steps**:
1. Click "New Recovery Plan"
2. Enter Plan Name: "Multi-Wave Test"
3. Enter Description: "Testing Wave 2+ dropdown behavior"
4. **Wave 1**:
   - Click "Add Wave"
   - Enter Wave Name: "Wave 1"
   - Select Protection Group: "WebServers"
   - Verify selection persists
5. **Wave 2**:
   - Click "Add Wave"
   - Enter Wave Name: "Wave 2"
   - Open Protection Group dropdown
   - Select Protection Group: "AppServers"
   - **CRITICAL**: Verify selection DOES NOT clear
   - Verify dropdown shows "(Already assigned)" for WebServers
6. **Wave 3**:
   - Click "Add Wave"
   - Enter Wave Name: "Wave 3"
   - Select Protection Group: "DatabaseServers"
   - Verify selection persists

**Expected Results**:
- ✅ Wave 1: Selection persists
- ✅ Wave 2: Selection persists (previously failed)
- ✅ Wave 3: Selection persists
- ✅ Assigned groups show "(Already assigned)" label
- ✅ Console shows onChange events firing

**Console Verification**:
```
// Should see in browser console:
"onChange fired: [selected protection group]"
"Wave [N] protection group selected: [GroupId]"
```

**Failure Indicators**:
- ❌ Selection clears immediately after selection
- ❌ Dropdown shows blank value
- ❌ Console shows no onChange events
- ❌ "(Already assigned)" labels missing

**Status**: ⏳ PENDING TEST

---

### Phase 2: Recovery Plan Operations

#### Test 2.1: Recovery Plan CREATE (Sanity Check)
**Objective**: Verify CREATE still works after all changes

**Steps**:
1. Use Recovery Plan dialog from Test 1.2 (if not cancelled)
2. Click "Create Recovery Plan"
3. Wait for success notification
4. Verify plan appears in table

**Expected Result**: Plan created successfully with all 3 waves

**Verification**:
- Plan visible in Recovery Plans table
- Shows correct Plan Name
- Shows 3 waves
- Shows correct Protection Groups

**Status**: ⏳ PENDING TEST

---

#### Test 2.2: Recovery Plan READ (View Details)
**Objective**: Verify plan details are displayed correctly

**Steps**:
1. Click on newly created plan (from Test 2.1)
2. Review plan details in dialog
3. Verify all waves are shown
4. Verify Protection Groups are correct
5. Close dialog without changes

**Expected Result**: All plan details display correctly

**Verification**:
- Plan Name matches
- Description matches
- 3 waves shown with correct names
- Protection Groups match selections
- Real DRS servers visible (not fake IDs)

**Status**: ⏳ PENDING TEST

---

#### Test 2.3: Recovery Plan UPDATE
**Objective**: Verify UPDATE operation works (untested since auth fix)

**Setup**:
- Test plan exists (from Test 2.1)
- User has valid auth token

**Steps**:
1. Click on test plan to open dialog
2. **Modify Plan Name**: Change to "Multi-Wave Test (Updated)"
3. **Modify Description**: Add " - Updated for testing"
4. **Wave 1 Modification**:
   - Change Wave Name to "Web Tier"
   - Keep same Protection Group
5. **Wave 2 Modification**:
   - Change Wave Name to "App Tier"
   - Keep same Protection Group
6. **Wave 3 Modification**:
   - Change Wave Name to "Database Tier"
   - Keep same Protection Group
7. Click "Update Recovery Plan"
8. Wait for success notification
9. Close and reopen plan to verify changes

**Expected Results**:
- ✅ Plan Name updated in table
- ✅ Description updated
- ✅ Wave names updated
- ✅ Protection Groups unchanged (not reassigned)
- ✅ Success notification shown
- ✅ Changes persist after reload

**API Verification**:
```bash
# Check DynamoDB directly
aws dynamodb get-item \
  --table-name DRS-Orchestration-RecoveryPlans \
  --key '{"PlanId": {"S": "[PLAN_ID]"}}'
```

**Failure Indicators**:
- ❌ 401 Unauthorized error (auth issue)
- ❌ Changes not saved
- ❌ Waves corrupted
- ❌ Protection Groups reassigned incorrectly

**Status**: ⏳ PENDING TEST

---

#### Test 2.4: Recovery Plan DELETE
**Objective**: Verify DELETE operation works (untested since auth fix)

**Setup**:
- Test plan exists (from Tests 2.1-2.3)
- User has valid auth token

**Steps**:
1. Locate test plan in table
2. Click delete button (trash icon)
3. Confirm deletion in dialog
4. Wait for success notification
5. Verify plan removed from table
6. Verify plan removed from DynamoDB

**Expected Results**:
- ✅ Confirmation dialog appears
- ✅ Delete succeeds without errors
- ✅ Success notification shown
- ✅ Plan removed from UI table
- ✅ Plan removed from DynamoDB

**API Verification**:
```bash
# Verify plan is gone from DynamoDB
aws dynamodb get-item \
  --table-name DRS-Orchestration-RecoveryPlans \
  --key '{"PlanId": {"S": "[PLAN_ID]"}}'
# Should return: "Item": null
```

**Failure Indicators**:
- ❌ 401 Unauthorized error (auth issue)
- ❌ Plan not deleted from DynamoDB
- ❌ Plan still visible in UI
- ❌ Error notification shown

**Status**: ⏳ PENDING TEST

---

### Phase 3: End-to-End Workflow

#### Test 3.1: Complete Recovery Plan Lifecycle
**Objective**: Full CRUD workflow validation

**Steps**:
1. **CREATE**: New plan with 3 waves
2. **READ**: View plan details
3. **UPDATE**: Modify plan details
4. **READ**: Verify updates persisted
5. **DELETE**: Remove plan
6. **VERIFY**: Confirm deletion

**Expected Result**: All operations complete without errors

**Status**: ⏳ PENDING TEST

---

#### Test 3.2: Protection Group Integration
**Objective**: Verify Protection Groups work correctly with Recovery Plans

**Steps**:
1. List all Protection Groups
2. Create Recovery Plan using all 3 groups
3. Verify groups show as "assigned" in UI
4. Attempt to select same group in multiple waves
5. Verify correct availability indicators
6. Verify real DRS servers are used

**Expected Result**: Protection Groups integrate seamlessly

**DRS Server Validation**:
```python
# Should only accept these real server IDs:
real_servers = [
    "s-3c1730a9e0771ea14",  # EC2AMAZ-4IMB9PN
    "s-3d75cdc0d9a28a725",  # EC2AMAZ-RLP9U5V
    "s-3afa164776f93ce4f",  # EC2AMAZ-H0JBE4J
    "s-3c63bb8be30d7d071",  # EC2AMAZ-8B7IRHJ
    "s-3578f52ef3bdd58b4",  # EC2AMAZ-FQTJG64
    "s-3b9401c1cd270a7a8"   # EC2AMAZ-3B0B3UD
]
```

**Status**: ⏳ PENDING TEST

---

### Phase 4: Error Handling & Edge Cases

#### Test 4.1: DRS Validation Error
**Objective**: Verify fake server IDs are rejected

**Steps**:
1. Try to create Protection Group with fake server ID
2. Use fake ID: "i-fakeweb001"
3. Verify API returns 400 error
4. Verify error message lists invalid IDs

**Expected Result**: Fake IDs rejected with clear error message

**Status**: ⏳ PENDING TEST

---

#### Test 4.2: Empty Recovery Plan
**Objective**: Verify validation for plans with no waves

**Steps**:
1. Click "New Recovery Plan"
2. Enter Plan Name and Description
3. Click "Create" without adding waves
4. Verify validation error

**Expected Result**: Error message: "At least one wave is required"

**Status**: ⏳ PENDING TEST

---

#### Test 4.3: Duplicate Wave Names
**Objective**: Verify wave name uniqueness validation

**Steps**:
1. Create plan with Wave 1: "Production"
2. Add Wave 2 with same name: "Production"
3. Verify validation error

**Expected Result**: Error message about duplicate wave names

**Status**: ⏳ PENDING TEST

---

## Testing Tools & Scripts

### Available Python Scripts

**Test Data Management**:
```bash
# Create fresh test data with real DRS servers
python tests/python/create_real_test_data.py

# Create test Recovery Plan
python tests/python/create_test_plan.py

# Check Protection Group responses
python tests/python/check_pg_response.py

# Cleanup all test data
python tests/python/cleanup_all_data.py
```

**DRS Validation Testing**:
```bash
# Test DRS validation logic
python tests/python/test_drs_validation.py
```

### Browser DevTools

**Console Commands**:
```javascript
// Check localStorage for auth token
localStorage.getItem('authToken')

// Check session storage
sessionStorage

// Clear all storage
localStorage.clear()
sessionStorage.clear()
```

**Network Tab**:
- Monitor API calls
- Check response codes
- Verify auth headers
- Watch for CORS errors

---

## Success Criteria

### Must Pass
- ✅ Browser cache refresh successful
- ✅ Wave 2+ dropdown selections persist (Session 43 fix)
- ✅ Recovery Plan UPDATE works without 401 errors
- ✅ Recovery Plan DELETE works without 401 errors
- ✅ DRS validation rejects fake server IDs
- ✅ All CRUD operations complete successfully

### Should Pass
- ✅ Wave name uniqueness validation
- ✅ Empty plan validation
- ✅ Protection Group availability indicators
- ✅ Console logs clean (no errors)

### Nice to Have
- ✅ Responsive design validation
- ✅ Loading states display correctly
- ✅ Error messages are user-friendly

---

## Known Issues & Limitations

### From Session 44

**Issue**: Region hardcoded to us-east-1 in Lambda
- **Impact**: Only works in us-east-1
- **TODO**: Make region dynamic from request
- **Workaround**: Only test in us-east-1

**Issue**: Browser cache may serve old JavaScript
- **Impact**: User may not see Autocomplete fix
- **Solution**: Hard browser refresh required
- **Status**: Addressed in Test 1.1

---

## Test Results Template

```markdown
## Test Results - Session 45

**Date**: [Date]
**Tester**: [Name]
**Browser**: [Browser/Version]

### Phase 1: Browser & UI
- [ ] Test 1.1: Browser cache refresh - PASS/FAIL
- [ ] Test 1.2: Wave 2+ dropdown - PASS/FAIL

### Phase 2: Recovery Plan Operations
- [ ] Test 2.1: CREATE sanity check - PASS/FAIL
- [ ] Test 2.2: READ details - PASS/FAIL
- [ ] Test 2.3: UPDATE operation - PASS/FAIL
- [ ] Test 2.4: DELETE operation - PASS/FAIL

### Phase 3: End-to-End
- [ ] Test 3.1: Complete lifecycle - PASS/FAIL
- [ ] Test 3.2: Protection Group integration - PASS/FAIL

### Phase 4: Error Handling
- [ ] Test 4.1: DRS validation error - PASS/FAIL
- [ ] Test 4.2: Empty plan validation - PASS/FAIL
- [ ] Test 4.3: Duplicate wave names - PASS/FAIL

### Issues Found
[List any issues discovered during testing]

### Recommendations
[List any recommended fixes or improvements]
```

---

## Next Steps After Testing

### If All Tests Pass
1. Document successful validation in PROJECT_STATUS.md
2. Create Session 45 checkpoint
3. Consider production deployment
4. Plan next feature development

### If Tests Fail
1. Document failure details
2. Create debug session
3. Fix identified issues
4. Retest failed scenarios
5. Update SESSION_45_TESTING_PLAN.md with results

---

## Reference Documentation

**Session Context**:
- `docs/SESSION_44_DETAILED_ANALYSIS.md` - Previous session details
- `docs/PROJECT_STATUS.md` - Overall project status
- `history/checkpoints/checkpoint_session_20251120_211815_27b089_2025-11-20_21-18-15.md` - Latest checkpoint

**API References**:
- `docs/AWS_DRS_API_REFERENCE.md` - AWS DRS API documentation
- `docs/DRS_SRM_API_MAPPING.md` - DRS to VMware SRM mapping
- `docs/VMware_SRM_REST_API_Summary.md` - VMware SRM API reference

**Code References**:
- `lambda/index.py` - Lambda API implementation (DRS validation)
- `frontend/src/components/WaveConfigEditor.tsx` - Autocomplete fix
- `frontend/src/components/RecoveryPlanDialog.tsx` - Main dialog component

---

## End of Testing Plan
