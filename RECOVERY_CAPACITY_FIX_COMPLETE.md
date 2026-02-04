# Recovery Capacity Calculation Fix - Complete

**Date**: February 4, 2026  
**Status**: ✅ COMPLETE  
**Commit**: 814e6848  
**Deployed**: test environment (2026-02-04 17:28 PST)

## Problem Summary

Recovery capacity was incorrectly counting ALL source servers (including STOPPED ones) instead of only actively replicating servers (CONTINUOUS state).

### Incorrect UI Display

**Before Fix**:
- us-east-1: Replication 12, Recovery 18 ❌ (recovery > replication is impossible)
- us-west-2: Replication 0, Recovery 12 ❌ (no replicating servers but showing recovery capacity)

### Actual Server State

- **Target account us-east-1**: 12 servers (6 native CONTINUOUS + 6 extended CONTINUOUS)
- **Target account us-west-2**: 6 servers (0 native + 6 extended STOPPED - broken instances)
- **Orchestration account us-east-1**: 6 native servers
- **Orchestration account us-west-2**: 6 native servers

### Why This Was Wrong

1. **Recovery capacity exceeded replication capacity** - This is impossible. You can't recover more servers than are actively replicating.
2. **STOPPED servers were counted** - The 6 STOPPED servers in us-west-2 cannot be recovered but were being counted.
3. **Misleading capacity metrics** - Users saw available recovery capacity that didn't actually exist.

## Root Cause

The `calculate_recovery_capacity()` function in `lambda/query-handler/index.py` was receiving `all_total_servers` (sum of totalServers from all accounts), which included STOPPED servers.

**Problematic Code** (lines 4743-4775):
```python
# Sum totalServers from all accounts (target + staging)
all_total_servers = sum(acc.get("totalServers", 0) for acc in account_results)

# ...

recovery_capacity = calculate_recovery_capacity(all_total_servers, combined_regional_list)
```

## Solution

Changed recovery capacity calculation to only count actively replicating servers (CONTINUOUS state):

### Code Changes

**File**: `lambda/query-handler/index.py`

**1. Updated function docstring** (lines 4006-4040):
```python
def calculate_recovery_capacity(total_servers: int, regional_breakdown: List[Dict] = None) -> Dict:
    """
    Calculate recovery capacity metrics for actively replicating servers (target + staging accounts).
    
    CRITICAL: Recovery capacity should ONLY count actively replicating servers (CONTINUOUS state).
    STOPPED servers cannot be recovered and should NOT count toward recovery capacity.
    Recovery capacity should NEVER exceed replication capacity.
    
    Args:
        total_servers: Total number of ACTIVELY REPLICATING servers across ALL accounts
            (target + staging, only includes servers in CONTINUOUS state that can be recovered)
    """
```

**2. Changed calculation logic** (lines 4743-4785):
```python
# Sum replicatingServers from all accounts (target + staging)
# Use replicatingServers (not totalServers) because only CONTINUOUS servers can be recovered
all_replicating_servers = sum(acc.get("replicatingServers", 0) for acc in account_results)

# Combine regional breakdowns from ALL accounts (target + staging)
# For recovery capacity, only count actively replicating servers
combined_regional_breakdown = {}
for account in account_results:
    for region_data in account.get("regionalBreakdown", []):
        region = region_data.get("region")
        if region:
            if region not in combined_regional_breakdown:
                combined_regional_breakdown[region] = {
                    "region": region,
                    "replicatingServers": 0,
                    "totalServers": 0,
                }
            # Sum replicating servers from all accounts in this region
            # Recovery capacity should only count actively replicating servers
            combined_regional_breakdown[region]["replicatingServers"] += region_data.get(
                "replicatingServers", 0
            )
            combined_regional_breakdown[region]["totalServers"] += region_data.get("totalServers", 0)

# Pass replicatingServers (not totalServers) for recovery capacity
# Recovery capacity = servers that can be recovered (must be actively replicating)
recovery_capacity = calculate_recovery_capacity(all_replicating_servers, combined_regional_list)
print(
    f"Recovery capacity calculated: {recovery_capacity.get('currentServers')}/"
    f"{recovery_capacity.get('maxRecoveryInstances')} "
    f"({len(combined_regional_list)} regions × 4,000 per region, "
    f"using replicatingServers from all accounts={all_replicating_servers})"
)
```

## Expected Results

**After Fix**:
- us-east-1: Replication 12, Recovery 12 ✅ (matches replication capacity)
- us-west-2: Replication 0, Recovery 0 ✅ (no actively replicating servers)
- Recovery capacity never exceeds replication capacity ✅

## Key Principles

1. **Recovery capacity = actively replicating servers only**
   - Only servers in CONTINUOUS state can be recovered
   - STOPPED servers cannot be recovered

2. **Recovery capacity ≤ replication capacity**
   - Recovery capacity should never exceed replication capacity
   - This is a fundamental constraint

3. **Regional breakdown matters**
   - Each region has a 4,000 server limit
   - Recovery capacity is calculated per region

## Testing

### Deployment
- **Environment**: test
- **Method**: Lambda-only update (`./scripts/deploy.sh test --lambda-only`)
- **Duration**: ~1 minute
- **Result**: ✅ All 6 Lambda functions updated successfully

### Verification Steps
1. Open UI: https://d319nadlgk4oj.cloudfront.net
2. Navigate to target account capacity view
3. Verify recovery capacity numbers:
   - us-east-1: Recovery = 12 (not 18)
   - us-west-2: Recovery = 0 (not 12)

## Related Issues

This fix is part of the larger staging account functionality restoration:
- See `docs/analysis/STAGING_ACCOUNT_REFRESH_FIX.md` for the full context
- See `docs/analysis/AUTOMATIC_STAGING_ACCOUNT_SYNC.md` for auto-extend implementation

## Files Changed

- `lambda/query-handler/index.py` (lines 4006-4040, 4743-4785)

## Commit Details

```
commit 814e6848
Author: John Cousens
Date: 2026-02-04

fix: recovery capacity should only count actively replicating servers

PROBLEM:
- Recovery capacity was counting ALL source servers (including STOPPED ones)
- us-east-1 showed Recovery: 18 when only 12 servers were replicating
- us-west-2 showed Recovery: 12 when 0 servers were replicating
- Recovery capacity exceeded replication capacity (impossible)

ROOT CAUSE:
- calculate_recovery_capacity() was receiving all_total_servers
- This included STOPPED servers that cannot be recovered
- Combined regional breakdown was summing totalServers

SOLUTION:
- Changed to use all_replicating_servers (sum of replicatingServers)
- Recovery capacity now only counts CONTINUOUS state servers
- Updated docstring to clarify this requirement
- Added comments explaining the logic

EXPECTED RESULTS:
- us-east-1: Recovery = 12 (matches replication capacity)
- us-west-2: Recovery = 0 (no actively replicating servers)
- Recovery capacity never exceeds replication capacity
```
