# Account Awareness - Complete Implementation Summary

**Date**: January 30, 2026  
**Status**: ✅ COMPLETE - All fixes deployed

---

## Overview

Implemented comprehensive account-awareness across the entire application to ensure proper data isolation between target accounts. Users can now switch between accounts and see only the data relevant to the selected account.

---

## Deployments

### Backend (Lambda) - Deployed 13:38 PM
- `hrp-drs-tech-adapter-data-management-handler-dev`
- `hrp-drs-tech-adapter-execution-handler-dev`
- `hrp-drs-tech-adapter-query-handler-dev`

### Frontend - Deployed 13:50 PM
- Version: `20260130-1350`
- CloudFront Distribution: `E1BBNSHA96QXQ4`

---

## Changes Implemented

### 1. Backend Filtering Logic

#### Recovery Plans (data-management-handler)
**Problem**: Recovery plans don't store `accountId` directly - they derive it from protection groups.

**Fix**: Updated filtering logic to check protection groups in waves:
```python
# Before: Checked for non-existent accountId field
if account_id:
    plan_account = plan.get("accountId")
    if not plan_account or plan_account != account_id:
        continue  # Filtered out ALL plans

# After: Derive account from protection groups
if account_id:
    plan_matches_account = False
    for wave in plan.get("waves", []):
        pg_id = wave.get("protectionGroupId")
        if pg_id:
            pg = protection_groups_table.get_item(Key={"groupId": pg_id})
            if pg.get("accountId") == account_id:
                plan_matches_account = True
                break
    if not plan_matches_account:
        continue
```

**Files Modified**:
- `lambda/data-management-handler/index.py` (lines 3437-3465)

---

### 2. Frontend API Client

#### Source Server Discovery
**Problem**: `listDRSSourceServers` didn't pass `accountId` parameter.

**Fix**: Added `accountId` as second parameter:
```typescript
// Before
public async listDRSSourceServers(
  region: string,
  currentProtectionGroupId?: string,
  filterByProtectionGroup?: string
)

// After
public async listDRSSourceServers(
  region: string,
  accountId?: string,  // NEW
  currentProtectionGroupId?: string,
  filterByProtectionGroup?: string
)
```

**Files Modified**:
- `frontend/src/services/api.ts`

---

### 3. Frontend Components

#### ServerDiscoveryPanel
**Changes**:
- Import `useAccount` hook
- Get `accountId` from `getCurrentAccountId()`
- Pass `accountId` to `listDRSSourceServers`
- Return early if no account selected

**Files Modified**:
- `frontend/src/components/ServerDiscoveryPanel.tsx`

#### ProtectionGroupDialog
**Changes**:
- Import `useAccount` hook
- Get `accountId` from `getCurrentAccountId()`
- Pass `accountId` when fetching server details
- Return early if no account selected

**Files Modified**:
- `frontend/src/components/ProtectionGroupDialog.tsx`

#### ServerSelector
**Changes**:
- Import `useAccount` hook
- Get `accountId` from `getCurrentAccountId()`
- Pass `accountId` for both server-based and tag-based protection groups
- Return early if no account selected
- Updated callback dependencies

**Files Modified**:
- `frontend/src/components/ServerSelector.tsx`

---

### 4. Test Fixes

#### ProtectionGroupDialog Tests
**Problem**: Tests failed because component now requires `AccountProvider`.

**Fix**: Added `AccountProvider` to test wrapper and mocked `getTargetAccounts` API call:
```typescript
// Before
<AuthProvider>
  <PermissionsProvider>
    {ui}
  </PermissionsProvider>
</AuthProvider>

// After
<AuthProvider>
  <AccountProvider>
    <PermissionsProvider>
      {ui}
    </PermissionsProvider>
  </AccountProvider>
</AuthProvider>
```

**Files Modified**:
- `frontend/src/components/__tests__/ProtectionGroupDialog.integration.tests.tsx`

---

## Account-Awareness Status by Component

### ✅ Fully Account-Aware

| Component/Page | Status | Notes |
|----------------|--------|-------|
| **ProtectionGroupsPage** | ✅ Complete | Backend filters by accountId |
| **RecoveryPlansPage** | ✅ Complete | Backend derives account from PGs |
| **ExecutionsPage** | ✅ Complete | Backend filters by accountId |
| **ServerDiscoveryPanel** | ✅ Complete | Passes accountId to API |
| **ProtectionGroupDialog** | ✅ Complete | Passes accountId when fetching servers |
| **ServerSelector** | ✅ Complete | Passes accountId for all PG types |
| **RecoveryPlanDialog** | ✅ Complete | Already passed accountId to PG list |

### ✅ Not Applicable (No Data Filtering)

| Component/Page | Status | Notes |
|----------------|--------|-------|
| **GettingStartedPage** | N/A | Documentation only, no API calls |
| **ConfigExportPanel** | N/A | Works with local data |
| **ConfigImportPanel** | N/A | Works with local data |
| **SettingsModal** | N/A | Manages account settings, not data |
| **AccountManagementPanel** | N/A | Manages accounts themselves |

### ✅ Correctly Scoped (Orchestration Account)

| Component | Status | Notes |
|-----------|--------|-------|
| **LaunchConfigSection** | ✅ Correct | Queries orchestration account EC2 resources |
| **ServerLaunchConfigDialog** | ✅ Correct | Queries orchestration account EC2 resources |

**Why Orchestration Account?**
- EC2 resources (subnets, security groups, instance types) are queried from the orchestration account
- Recovery instances are launched in the target account via cross-account role assumption
- DRS automatically uses target account's VPC/subnets during recovery

---

## Data Model

### Protection Groups
```json
{
  "groupId": "pg-123",
  "groupName": "My Group",
  "accountId": "160885257264",  // ✅ Stored directly
  "region": "us-west-2",
  "sourceServerIds": ["s-123", "s-456"]
}
```

### Recovery Plans
```json
{
  "planId": "plan-123",
  "planName": "My Plan",
  // ❌ No accountId field - derived from protection groups
  "waves": [
    {
      "waveNumber": 1,
      "protectionGroupId": "pg-123"  // References PG with accountId
    }
  ]
}
```

### Executions
```json
{
  "executionId": "exec-123",
  "planId": "plan-123",
  "accountId": "160885257264",  // ✅ Stored directly
  "status": "COMPLETED"
}
```

---

## User Action Required

### 🔴 CRITICAL: Hard Refresh Browser

You **MUST perform a hard refresh** to clear CloudFront cache:

**macOS**: `Cmd + Shift + R`  
**Windows/Linux**: `Ctrl + Shift + R`

---

## Verification Steps

After hard refresh:

1. **Select Account**: Choose "DEMO_TARGET (160885257264)" from dropdown
2. **Check Protection Groups**: Should only show groups for that account
3. **Check Recovery Plans**: Should only show plans with PGs for that account
4. **Check Executions**: Should only show executions for that account
5. **Create Protection Group**: 
   - Select region "us-west-2"
   - Should only see servers from account 160885257264
   - Should NOT see servers from account 891376951562

### Browser DevTools Verification

1. Open DevTools (F12) → Network tab
2. Select an account
3. Verify API requests include `?accountId=160885257264`
4. Check responses only contain items for selected account

---

## Expected Behavior

### Protection Groups Page
- ✅ Shows only groups with matching `accountId`
- ✅ Empty if no groups exist for account
- ✅ Server discovery filtered by account

### Recovery Plans Page
- ✅ Shows only plans whose protection groups match account
- ✅ Plan appears if ANY wave has a PG for the account
- ✅ Empty if no plans have PGs for account

### Executions Page
- ✅ Shows only executions with matching `accountId`
- ✅ Empty if no executions exist for account

### Server Discovery
- ✅ Only shows servers from selected account
- ✅ Applies to protection group creation
- ✅ Applies to recovery plan wave configuration

---

## Architecture Notes

### Why Recovery Plans Don't Store accountId

Recovery plans are **multi-account aware** by design:
- A single plan can contain waves with PGs from different accounts
- Each protection group has its own `accountId`
- Filtering must check all PGs in all waves

### Performance Considerations

The new recovery plan filtering queries DynamoDB for each PG:
- **Complexity**: O(plans × waves × protection_groups)
- **Impact**: Minimal for typical deployments (< 100 plans)
- **Optimization**: Could cache PG accounts in memory if needed

---

## Commits

1. `cbc1a04f` - fix: derive recovery plan account from protection groups
2. `4dcca7a9` - style: apply black formatting
3. `f1856f4a` - fix: pass accountId to source server discovery API
4. `e0fc7b9a` - test: add AccountProvider to ProtectionGroupDialog tests

---

## Known Issues (Separate Tracking)

### 1. Invalid Date in Last Validated Column
**Status**: Not fixed  
**Location**: Account Management Panel  
**Cause**: Backend not returning `lastValidated` in correct format

### 2. Default Account Gets Unset in Settings Modal
**Status**: Investigating  
**Reported**: User feedback  
**Next Steps**: Reproduce and debug

---

## Related Documentation

- [Account Filtering Fix Summary](ACCOUNT_FILTERING_FIX_SUMMARY.md)
- [Multi-Account Setup Guide](docs/guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md)
- [API Endpoints Reference](docs/reference/API_ENDPOINTS_CURRENT.md)
- [Architecture Overview](docs/architecture/ARCHITECTURE.md)
