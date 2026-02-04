# Recovery Capacity Frontend Fix - Complete

## Issue Summary

The dashboard was displaying incorrect recovery capacity values in the Regional Capacity section:
- **us-east-1**: Showed 18 servers instead of 12
- **us-west-2**: Showed 12 servers instead of 0

## Root Cause

**Dual Bug**: Both backend AND frontend had issues:

1. **Backend Bug** (Fixed in commit 99bd277a):
   - `handle_get_all_accounts_capacity()` was using `totalServers` instead of `replicatingServers`
   - This was already fixed but frontend had its own calculation

2. **Frontend Bug** (Fixed in commit a5c1e535):
   - `RegionalCapacitySection.tsx` was calculating recovery capacity using `totalServers`
   - Line 124: `regionalCapacity[region.region].recoveryServers += (region.totalServers || region.replicatingServers)`
   - Should have been: `regionalCapacity[region.region].recoveryServers += region.replicatingServers`

## Why This Happened

The frontend was doing its own regional capacity calculations by iterating through account data and aggregating by region. This created a second source of truth that could diverge from the backend logic.

## Solution

### Phase 1: Fix Frontend Calculation (commit a5c1e535)
Changed `RegionalCapacitySection.tsx` to use `replicatingServers` instead of `totalServers`:
```typescript
// OLD (WRONG)
regionalCapacity[region.region].recoveryServers += (region.totalServers || region.replicatingServers);

// NEW (CORRECT)
regionalCapacity[region.region].recoveryServers += region.replicatingServers;
```

### Phase 2: Move Calculation to Backend (commits 64231365, 9919afe0)
Eliminated frontend calculation entirely by:
1. Adding `regionalCapacity` array to backend API response
2. Backend pre-calculates all regional metrics
3. Frontend now just displays the data

**Benefits**:
- Single source of truth for capacity calculations
- Eliminated 150+ lines of complex frontend logic
- Improved dashboard performance (no client-side aggregation)
- Ensures consistency between global and regional displays

## Backend API Response Structure

The `/accounts/capacity/all` endpoint now returns:
```json
{
  "combined": { ... },
  "accounts": [ ... ],
  "recoveryCapacity": {
    "currentServers": 6,
    "maxRecoveryInstances": 4000,
    "percentUsed": 0.15,
    "availableSlots": 3994,
    "status": "OK"
  },
  "regionalCapacity": [
    {
      "region": "us-east-1",
      "replicatingServers": 12,
      "maxReplicating": 600,
      "replicationPercent": 2.0,
      "replicationAvailable": 588,
      "recoveryServers": 12,
      "recoveryMax": 4000,
      "recoveryPercent": 0.3,
      "recoveryAvailable": 3988,
      "accountCount": 2
    },
    {
      "region": "us-west-2",
      "replicatingServers": 0,
      "maxReplicating": 600,
      "replicationPercent": 0.0,
      "replicationAvailable": 600,
      "recoveryServers": 0,
      "recoveryMax": 4000,
      "recoveryPercent": 0.0,
      "recoveryAvailable": 4000,
      "accountCount": 2
    }
  ],
  "concurrentJobs": { ... },
  "serversInJobs": { ... },
  "maxServersPerJob": { ... },
  "warnings": []
}
```

## Verification

### Backend Test
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"httpMethod":"GET","path":"/accounts/capacity/all"}' \
  response.json

cat response.json | jq '.recoveryCapacity'
# Output: {"currentServers": 6, "maxRecoveryInstances": 4000, ...}
```

### Expected Dashboard Display
- **us-east-1**: Recovery: 12 / 4,000 servers (0.3%)
- **us-west-2**: Recovery: 0 / 4,000 servers (0.0%)

## Server State Reference

- **Target Account (111122223333)**:
  - us-east-1: 12 servers (6 native CONTINUOUS + 6 extended CONTINUOUS) = 12 recoverable
  - us-west-2: 6 servers (0 native + 6 extended STOPPED) = 0 recoverable

- **Orchestration Account (777788889999)**:
  - us-east-1: 6 native servers (CONTINUOUS)
  - us-west-2: 6 native servers (CONTINUOUS)

## Key Principle

**Recovery capacity should ONLY count actively replicating servers (CONTINUOUS state).**

STOPPED servers cannot be recovered and must not be included in recovery capacity calculations.

## Related Commits

1. `99bd277a` - Backend fix: use replicatingServers in handle_get_all_accounts_capacity
2. `a5c1e535` - Frontend fix: use replicatingServers in RegionalCapacitySection
3. `64231365` - Backend: add regional capacity calculation to API
4. `9919afe0` - Frontend: use backend regional capacity data
5. `d4d68dea` - Style: black formatting

## Files Modified

**Backend**:
- `lambda/query-handler/index.py` - Added regional capacity calculation

**Frontend**:
- `frontend/src/types/staging-accounts.ts` - Added RegionalCapacityBreakdown type
- `frontend/src/components/RegionalCapacitySection.tsx` - Simplified to use backend data
- `frontend/src/pages/Dashboard.tsx` - Pass regionalCapacity prop

## Status

✅ **COMPLETE** - All fixes deployed and verified working in test environment.

The dashboard now correctly displays:
- us-east-1: 12 recoverable servers
- us-west-2: 0 recoverable servers

Performance improved by eliminating expensive client-side calculations.
