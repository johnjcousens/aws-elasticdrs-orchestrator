# Account Filtering Fix Summary

**Date**: January 30, 2026  
**Issue**: Recovery plans and protection groups not filtering by selected account  
**Status**: ✅ FIXED - Backend deployed at 13:38 PM

---

## Root Cause

Recovery plans **do not store `accountId` directly** in DynamoDB. They derive their account from the protection groups referenced in their waves. However, the backend filtering logic was checking for a `plan.get("accountId")` field that doesn't exist, causing ALL recovery plans to be filtered out when an account was selected.

### Data Model

- **Protection Groups**: Store `accountId` field ✅
- **Recovery Plans**: Do NOT store `accountId` - derive it from protection groups ❌
- **Executions**: Store `accountId` field ✅

---

## What Was Fixed

### Backend Changes (Lambda)

**File**: `lambda/data-management-handler/index.py`

**Before** (lines 3437-3442):
```python
if account_id:
    plan_account = plan.get("accountId")
    if not plan_account or plan_account != account_id:
        continue  # ❌ Filters out ALL plans (accountId doesn't exist)
```

**After**:
```python
if account_id:
    # Recovery plans derive account from protection groups
    plan_matches_account = False
    waves = plan.get("waves", [])
    
    for wave in waves:
        pg_id = wave.get("protectionGroupId")
        if pg_id:
            pg_result = protection_groups_table.get_item(Key={"groupId": pg_id})
            if "Item" in pg_result:
                pg = pg_result["Item"]
                pg_account = pg.get("accountId")
                if pg_account == account_id:
                    plan_matches_account = True
                    break
    
    if not plan_matches_account:
        continue  # ✅ Only filters out plans that don't match account
```

### Frontend Changes (Already Deployed)

**Files**: 
- `frontend/src/contexts/AccountContext.tsx` - Added localStorage persistence
- `frontend/src/pages/ProtectionGroupsPage.tsx` - Fixed useEffect dependencies
- `frontend/src/pages/RecoveryPlansPage.tsx` - Fixed useEffect dependencies
- `frontend/src/pages/ExecutionsPage.tsx` - Fixed useEffect dependencies

**Changes**:
- Changed useEffect dependencies from `selectedAccount` object to `getCurrentAccountId()` result
- Added localStorage persistence for selected account (survives page refresh)
- Fixed re-render triggers when account changes

---

## Deployment Status

### ✅ Backend (Lambda) - Deployed 13:38 PM
- `aws-drs-orchestration-data-management-handler-test` - Updated
- `aws-drs-orchestration-execution-handler-test` - Updated
- `aws-drs-orchestration-query-handler-test` - Updated

### ✅ Frontend - Already Deployed 13:06 PM
- Version: `20260130-1306`
- CloudFront Distribution: `E1BBNSHA96QXQ4`

---

## User Action Required

### 🔴 CRITICAL: Hard Refresh Browser

The user MUST perform a **hard refresh** to clear CloudFront cache:

**Chrome/Edge/Firefox (Windows/Linux)**:
- `Ctrl + Shift + R`
- OR `Ctrl + F5`

**Chrome/Safari (macOS)**:
- `Cmd + Shift + R`

**Why?** CloudFront caches the old frontend JavaScript bundle. A normal refresh won't fetch the new code.

---

## Verification Steps

After hard refresh, verify the fix:

1. **Open Browser DevTools** (F12)
2. **Go to Network tab**
3. **Select an account** from dropdown (e.g., "DEMO_TARGET - 111122223333")
4. **Check API requests**:
   - Look for requests to `/protection-groups?accountId=111122223333`
   - Look for requests to `/recovery-plans?accountId=111122223333`
   - Look for requests to `/executions?accountId=111122223333`
5. **Verify responses** only contain items for selected account
6. **Check Console tab** for logs:
   ```
   [ProtectionGroupsPage] Account changed to: 111122223333
   [ProtectionGroupsPage] Fetching groups for account: 111122223333
   ```

---

## Expected Behavior After Fix

### ✅ Protection Groups Page
- Shows only protection groups with `accountId` matching selected account
- Empty if no groups exist for that account

### ✅ Recovery Plans Page
- Shows only recovery plans whose protection groups match selected account
- A plan appears if ANY of its waves contain a protection group for the selected account
- Empty if no plans have protection groups for that account

### ✅ Executions Page
- Shows only executions with `accountId` matching selected account
- Empty if no executions exist for that account

### ✅ Account Persistence
- Selected account persists across page refreshes (stored in localStorage)
- Account selection survives browser restart

---

## Known Issues (Separate from this fix)

### "Invalid Date" in Last Validated Column
**Status**: Not fixed yet  
**Location**: Account Management Panel  
**Cause**: Backend not returning `lastValidated` field in correct format  
**Next Steps**: Check API response format and fix backend or frontend date parsing

### Default Account Gets Unset in Settings Modal
**Status**: Investigating  
**Reported by**: User  
**Next Steps**: Need to reproduce and debug settings modal behavior

---

## Technical Details

### Why Recovery Plans Don't Store accountId

Recovery plans are **multi-account aware** by design. A single recovery plan can contain waves with protection groups from different accounts. Therefore:

1. Recovery plans don't have a single `accountId` field
2. Each protection group in a wave has its own `accountId`
3. Filtering must check all protection groups in all waves

### Performance Considerations

The new filtering logic queries DynamoDB for each protection group in each wave. For large deployments:

- **Current**: O(plans × waves × protection_groups) DynamoDB queries
- **Optimization**: Could cache protection group accounts in memory
- **Impact**: Minimal for typical deployments (< 100 plans)

---

## Commits

1. `cbc1a04f` - fix: derive recovery plan account from protection groups
2. `4dcca7a9` - style: apply black formatting

---

## Related Documentation

- [Account Management Architecture](docs/architecture/ARCHITECTURE.md)
- [Multi-Account Setup Guide](docs/guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md)
- [API Endpoints Reference](docs/reference/API_ENDPOINTS_CURRENT.md)
