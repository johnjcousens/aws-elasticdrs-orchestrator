# Staging Account Auto-Extend Restoration Plan

## Problem
After refactoring, the auto-extend functionality was lost. Currently:
- `list-staging-accounts` returns empty because no extended source servers exist
- The 6 DRS agents in staging account 777788889999 are NOT extended to target 111122223333
- UI shows 0 staging accounts

## Solution Architecture

### Step 1: Manual Staging Account Addition (Already Working)
User manually adds staging account 777788889999 to target account 111122223333 via UI.

### Step 2: Auto-Discovery & Auto-Extend (MISSING - Need to Restore)
EventBridge triggers every 5 minutes → `handle_sync_staging_accounts()` → `auto_extend_staging_servers()`

Workflow:
1. For each target account with staging accounts configured
2. Query staging account for its DRS source servers
3. Check which are already extended to target
4. Auto-extend missing servers using `create_extended_source_server`

### Step 3: Discovery Works (Will Work After Step 2)
Once servers are extended, `list-staging-accounts` returns staging account 777788889999.

## Code to Restore

### Location: `lambda/query-handler/index.py`

### 1. Add to `handle_sync_staging_accounts()` (around line 4230)
After the staging account sync loop, add:
```python
# Step 2: Auto-extend new servers from staging accounts
print("\n=== Starting auto-extend of staging account servers ===")
extend_results = auto_extend_staging_servers(target_accounts)
sync_results["autoExtend"] = extend_results
```

### 2. Add Helper Functions (at end of file, before lambda_handler)

```python
def auto_extend_staging_servers(target_accounts: List[Dict]) -> Dict:
    """Auto-extend new DRS source servers from staging accounts to target accounts."""
    # Implementation from commit 7e6c896a
    
def get_extended_source_servers(target_account_id: str, role_arn: str, external_id: str) -> set:
    """Get set of extended source server ARNs in target account."""
    # Implementation from commit 7e6c896a
    
def get_staging_account_servers(staging_account_id: str, role_arn: str, external_id: str) -> List[Dict]:
    """Get DRS source servers in staging account."""
    # Implementation from commit 7e6c896a
    
def extend_source_server(target_account_id: str, target_role_arn: str, target_external_id: str, staging_server_arn: str) -> None:
    """Extend a source server from staging account to target account."""
    # Implementation from commit 7e6c896a
```

## Testing Plan

1. Deploy the restored code
2. Manually add staging account 777788889999 to target 111122223333
3. Wait 5 minutes for EventBridge trigger OR manually invoke sync
4. Verify 6 servers are extended
5. Verify `list-staging-accounts` now returns 777788889999
6. Verify UI shows staging account with 6 servers

## Region Configuration
**IMPORTANT**: The code uses `us-west-2` as primary region. Verify this matches your DRS configuration.
