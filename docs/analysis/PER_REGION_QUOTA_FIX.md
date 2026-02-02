# Per-Region Quota Tracking Fix

**Date**: February 2, 2026  
**Status**: Code Complete - Awaiting Deployment  
**Priority**: CRITICAL BUG FIX

## Problem Statement

The backend was incorrectly aggregating replicating servers across ALL regions and comparing against a single 300 limit. This is fundamentally wrong because DRS quotas are **per account per region**, not per account total.

### Incorrect Behavior (Before Fix)

```
Account with:
- us-east-1: 200 replicating servers
- us-west-2: 200 replicating servers
- Total: 400 servers

OLD CODE: Status = CRITICAL (400 > 300) ❌ WRONG!
CORRECT: Status = OK (each region under 300) ✅
```

## Root Cause

In `lambda/query-handler/index.py`, the `handle_get_combined_capacity()` function was:

1. Querying all regions correctly (per-region data in `regionalBreakdown`)
2. **BUT** calculating account status based on TOTAL servers across all regions
3. Comparing total against single 300 limit

```python
# OLD CODE (WRONG)
replicating = account.get("replicatingServers", 0)  # Total across all regions
max_replicating = 300  # Single limit
account["status"] = calculate_account_status(replicating)  # Wrong!
```

## Solution Implemented

### Backend Changes (`lambda/query-handler/index.py`)

Changed Step 6 in `handle_get_combined_capacity()` to:

1. **Calculate status per-region** - Each region evaluated against its own 300 limit
2. **Track worst status** - Account status = worst region status
3. **Add per-region fields** to `regionalBreakdown`:
   - `status`: OK/INFO/WARNING/CRITICAL/HYPER-CRITICAL
   - `maxReplicating`: 300 (per region)
   - `percentUsed`: Percentage of region's 300 limit
   - `availableSlots`: Available slots in that region

4. **Add account-level fields**:
   - `activeRegions`: Number of regions with servers
   - `totalRegionalCapacity`: Total capacity across all active regions (activeRegions × 300)
   - `status`: Worst status across all regions
   - `maxReplicating`: Total regional capacity
   - `percentUsed`: Total servers / total regional capacity
   - `availableSlots`: Total available slots

5. **Update warnings** to specify which region has the issue

### Example Response Structure

```json
{
  "accounts": [
    {
      "accountId": "123456789012",
      "accountName": "Production",
      "accountType": "target",
      "replicatingServers": 400,
      "totalServers": 400,
      "status": "OK",
      "activeRegions": 2,
      "totalRegionalCapacity": 600,
      "maxReplicating": 600,
      "percentUsed": 66.67,
      "availableSlots": 200,
      "regionalBreakdown": [
        {
          "region": "us-east-1",
          "replicatingServers": 200,
          "totalServers": 200,
          "status": "OK",
          "maxReplicating": 300,
          "percentUsed": 66.67,
          "availableSlots": 100
        },
        {
          "region": "us-west-2",
          "replicatingServers": 200,
          "totalServers": 200,
          "status": "OK",
          "maxReplicating": 300,
          "percentUsed": 66.67,
          "availableSlots": 100
        }
      ],
      "warnings": []
    }
  ]
}
```

### Frontend Changes

**Updated**: `frontend/src/components/CompactCapacitySummary.tsx`
- Description now clarifies per-region quotas with example

**Removed**: Getting Started page (as requested)
- Deleted `frontend/src/pages/GettingStartedPage.tsx`
- Removed route from `frontend/src/App.tsx`
- Updated `frontend/src/pages/Dashboard.tsx` to redirect to settings modal when no accounts

## Verification Scenarios

### Scenario 1: Single Region
```
Account: us-east-1 only
- 250 servers in us-east-1
Expected: WARNING (250/300 = 83%)
```

### Scenario 2: Multi-Region Under Limit
```
Account: us-east-1 + us-west-2
- 200 servers in us-east-1 (67%)
- 200 servers in us-west-2 (67%)
- Total: 400 servers
Expected: OK (each region under 200)
```

### Scenario 3: Multi-Region One Over
```
Account: us-east-1 + us-west-2
- 150 servers in us-east-1 (50%)
- 280 servers in us-west-2 (93%)
- Total: 430 servers
Expected: HYPER-CRITICAL (worst region is us-west-2 at 93%)
Warning: "Immediate action required in us-west-2 - at 280 servers (93-100%)"
```

### Scenario 4: Multi-Region Both Over
```
Account: us-east-1 + us-west-2
- 290 servers in us-east-1 (97%)
- 295 servers in us-west-2 (98%)
- Total: 585 servers
Expected: HYPER-CRITICAL (worst region is us-west-2 at 98%)
Warning: "Immediate action required in us-west-2 - at 295 servers (93-100%)"
```

## Files Changed

### Backend
- `lambda/query-handler/index.py` - Per-region quota tracking logic

### Frontend
- `frontend/src/App.tsx` - Removed Getting Started route
- `frontend/src/pages/GettingStartedPage.tsx` - DELETED
- `frontend/src/pages/Dashboard.tsx` - Added settings modal redirect
- `frontend/src/components/CompactCapacitySummary.tsx` - Updated description

## Deployment Instructions

```bash
# 1. Authenticate to AWS
aws login

# 2. Deploy all changes
./scripts/deploy.sh test

# 3. Verify deployment
# Check Lambda was updated
AWS_PAGER="" aws lambda get-function \
  --function-name aws-drs-orchestration-query-handler-test \
  --query 'Configuration.LastModified'

# Check CloudFront invalidation
AWS_PAGER="" aws cloudfront list-invalidations \
  --distribution-id E3XXXXXXXXXX

# 4. Test capacity API
curl -H "Authorization: Bearer $TOKEN" \
  "https://mgqims9lj1.execute-api.us-east-1.amazonaws.com/test/capacity/combined?targetAccountId=123456789012"
```

## Testing Checklist

After deployment:

- [ ] API returns `activeRegions` field
- [ ] API returns `totalRegionalCapacity` field
- [ ] Each region in `regionalBreakdown` has `status`, `maxReplicating`, `percentUsed`, `availableSlots`
- [ ] Account status reflects worst region, not total
- [ ] Warnings specify which region has the issue
- [ ] Frontend displays correct capacity (total across regions)
- [ ] Getting Started page is removed (404 on `/getting-started`)
- [ ] Dashboard redirects to settings modal when no accounts

## Backward Compatibility

The changes maintain backward compatibility:

- All existing fields remain (`replicatingServers`, `totalServers`, `maxReplicating`, `percentUsed`, `availableSlots`)
- New fields added (`activeRegions`, `totalRegionalCapacity`, per-region status fields)
- Frontend will work with both old and new API responses

## Impact

**Before Fix**: False alarms for multi-region deployments
- Account with 200 servers in 2 regions = 400 total = CRITICAL ❌

**After Fix**: Accurate per-region status
- Account with 200 servers in 2 regions = OK (each region 67%) ✅

This fix is critical for customers using multi-region DRS deployments.

## Related Documentation

- [DRS Service Quotas Complete](../reference/DRS_SERVICE_QUOTAS_COMPLETE.md)
- [AWS DRS Multi-Account Documentation](https://docs.aws.amazon.com/drs/latest/userguide/multi-account.html)
