# Staging Account Refresh Fix

## Problem Statement

When users remove old extended source servers, remove a staging account, add a new staging account, and add new extended source servers, the settings modal and dashboard don't automatically pick up the changes. The dashboard still references the old staging account instead of the new one.

## Root Cause

The issue was a **stale data/caching problem** across multiple frontend layers:

1. **AccountContext** - Cached the list of target accounts but didn't refresh when staging accounts changed
2. **Dashboard** - Fetched capacity data on mount and interval, but didn't force refresh after staging account changes
3. **TargetAccountSettingsModal** - Displayed staging accounts from props without fetching fresh data from the backend

When staging accounts were added/removed:
- ✅ DynamoDB was updated correctly (backend working)
- ❌ Frontend components didn't refetch the updated data
- ❌ Users saw stale staging account information

## Solution Architecture

### 1. Custom Hook: `useStagingAccountRefresh`

Created a coordination hook to orchestrate refreshes across all affected components:

```typescript
// frontend/src/hooks/useStagingAccountRefresh.ts
export const useStagingAccountRefresh = (callbacks?: {
  onRefreshCapacity?: () => void;
  onRefreshTargetAccount?: () => void;
}) => {
  const { refreshAccounts } = useAccount();

  const refreshAfterStagingAccountChange = useCallback(async () => {
    // 1. Refresh account list with cache bust
    await refreshAccounts(true);
    
    // 2. Refresh capacity data
    callbacks?.onRefreshCapacity?.();
    
    // 3. Refresh target account details
    callbacks?.onRefreshTargetAccount?.();
  }, [refreshAccounts, callbacks]);

  return { refreshAfterStagingAccountChange };
};
```

### 2. AccountContext Enhancement

Added cache busting parameter to `refreshAccounts`:

```typescript
// frontend/src/contexts/AccountContext.tsx
const refreshAccounts = useCallback(async (bustCache = false) => {
  // ... fetch accounts ...
  
  // If bustCache is true, force refresh selected account's full details
  if (bustCache && selectedAccount?.value) {
    const fullAccount = await apiClient.getTargetAccount(selectedAccount.value);
    console.log('Refreshed account details after cache bust:', fullAccount);
  }
}, [isAuthenticated, authLoading, selectedAccount]);
```

### 3. Dashboard Enhancement

Added cache busting to capacity data fetch:

```typescript
// frontend/src/pages/Dashboard.tsx
const fetchCapacityData = useCallback(async (accountId: string, bustCache = false) => {
  if (!capacityData || bustCache) {
    setCapacityLoading(true);
  }
  
  const data = await getCombinedCapacity(accountId, false);
  setCapacityData(data);
}, [capacityData]);

// Setup refresh coordination
const refreshCapacityData = useCallback(() => {
  const accountId = getCurrentAccountId();
  if (accountId) {
    fetchCapacityData(accountId, true); // Force cache bust
  }
}, [getCurrentAccountId]);

useStagingAccountRefresh({
  onRefreshCapacity: refreshCapacityData,
});
```

### 4. TargetAccountSettingsModal Enhancement

Added automatic data refresh when modal opens:

```typescript
// frontend/src/components/TargetAccountSettingsModal.tsx
const [freshAccountData, setFreshAccountData] = useState(null);
const [loading, setLoading] = useState(false);

// Fetch fresh account data when modal opens
useEffect(() => {
  if (visible && targetAccount.accountId) {
    setLoading(true);
    
    apiClient.getTargetAccount(targetAccount.accountId)
      .then((data) => setFreshAccountData(data))
      .catch((err) => {
        console.error('Error fetching fresh account data:', err);
        setFreshAccountData(targetAccount); // Fallback to prop
      })
      .finally(() => setLoading(false));
  }
}, [visible, targetAccount.accountId]);

// Use fresh data if available
const displayAccount = freshAccountData || targetAccount;
const stagingAccounts = displayAccount.stagingAccounts || [];
```

## Data Flow After Fix

### Before (Broken):
```
User Action: Remove/Add Staging Account
    ↓
Backend: DynamoDB Updated ✅
    ↓
Frontend: Components show stale data ❌
```

### After (Fixed):
```
User Action: Remove/Add Staging Account
    ↓
Backend: DynamoDB Updated ✅
    ↓
useStagingAccountRefresh.refreshAfterStagingAccountChange()
    ↓
    ├─→ AccountContext.refreshAccounts(bustCache=true)
    │       ↓
    │   Fetch fresh account list + staging accounts ✅
    │
    ├─→ Dashboard.refreshCapacityData()
    │       ↓
    │   Fetch fresh capacity data with cache bust ✅
    │
    └─→ TargetAccountSettingsModal (on next open)
            ↓
        Fetch fresh account details ✅
```

## Usage Pattern

### When to Call Refresh

Call `refreshAfterStagingAccountChange()` after:

1. **Adding a staging account** via AddStagingAccountModal
2. **Removing a staging account** via settings
3. **Adding extended source servers** in DRS (changes staging account discovery)
4. **Removing extended source servers** in DRS (changes staging account discovery)

### Example Integration

```typescript
// In AddStagingAccountModal or AccountManagementPanel
const { refreshAfterStagingAccountChange } = useStagingAccountRefresh();

const handleAddStagingAccount = async (accountData) => {
  await addStagingAccount(targetAccountId, accountData);
  
  // Trigger coordinated refresh
  await refreshAfterStagingAccountChange();
  
  toast.success('Staging account added and data refreshed');
};
```

## Benefits

1. **Automatic Synchronization** - All components stay in sync automatically
2. **No Manual Refresh Required** - Users don't need to refresh the page
3. **Transparent to User** - Changes appear immediately after operations complete
4. **Centralized Coordination** - Single hook manages all refresh logic
5. **Cache Busting** - Forces fresh data fetch, bypassing browser/component caches

## Testing Checklist

- [ ] Add staging account → Dashboard shows new account immediately
- [ ] Remove staging account → Dashboard removes old account immediately
- [ ] Add extended source servers → Settings modal shows updated staging accounts
- [ ] Remove extended source servers → Settings modal reflects changes
- [ ] Open settings modal → Always shows fresh data from backend
- [ ] Capacity gauges update after staging account changes
- [ ] No page refresh required for any operation

## Related Files

- `frontend/src/hooks/useStagingAccountRefresh.ts` - Coordination hook
- `frontend/src/contexts/AccountContext.tsx` - Account list management
- `frontend/src/pages/Dashboard.tsx` - Capacity display
- `frontend/src/components/TargetAccountSettingsModal.tsx` - Account details modal
- `frontend/src/services/staging-accounts-api.ts` - API client
- `lambda/data-management-handler/index.py` - Backend handler

## Deployment

Deploy using the standard workflow:

```bash
./scripts/deploy.sh test --frontend-only
```

This will rebuild and deploy the frontend with the refresh fixes.
