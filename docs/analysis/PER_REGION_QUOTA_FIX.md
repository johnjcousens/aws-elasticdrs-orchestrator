# Per-Region Quota Tracking Fix + UI Consolidation

**Date**: February 2, 2026  
**Status**: ✅ COMPLETE  
**Deployment**: hrp-drs-tech-adapter-dev (build 20260202-0102)

## Critical Bug Fixed

### The Problem
The backend was incorrectly aggregating replicating servers across ALL regions and comparing against a single 300 limit. This violated AWS DRS quota rules.

**Incorrect Behavior (Before Fix)**:
- Account with 200 servers in us-east-1 + 200 servers in us-west-2 = 400 total
- OLD CODE: Status = CRITICAL (400 > 300) ❌ **WRONG!**
- CORRECT: Status = OK (each region under 300) ✅

### AWS DRS Quota Rules (Verified)
All DRS quotas are **per account per region**, not total across regions:
- **300 replicating servers**: Per account per region
- **4,000 source servers**: Per account per region (adjustable)
- **20 concurrent jobs**: Per account per region
- **500 servers in active jobs**: Per account per region
- **100 servers per job**: Universal limit

**Source**: https://docs.aws.amazon.com/drs/latest/userguide/multi-account.html

## Backend Changes (lambda/query-handler/index.py)

### 1. Per-Region Capacity Tracking
Changed `handle_get_combined_capacity()` to track capacity per region:

```python
# Calculate per-region status and find worst status
worst_status = "OK"
worst_region = None
worst_region_count = 0
active_regions = 0
total_regional_capacity = 0

for region_data in regional_breakdown:
    region = region_data.get("region")
    replicating = region_data.get("replicatingServers", 0)
    
    if replicating > 0:
        active_regions += 1
        total_regional_capacity += 300  # Each region has 300 limit
    
    # Calculate status for this region
    region_status = calculate_account_status(replicating)
    region_data["status"] = region_status
    region_data["maxReplicating"] = 300
    region_data["percentUsed"] = round((replicating / 300 * 100), 2)
    region_data["availableSlots"] = 300 - replicating
```

### 2. New Response Fields
Added to account-level response:
- `activeRegions`: Number of regions with servers
- `totalRegionalCapacity`: Total capacity across all regions (activeRegions × 300)
- Per-region fields: `maxReplicating`, `percentUsed`, `availableSlots`, `status`

### 3. Status Calculation
Overall account status based on **worst region**, not total:

```python
# Track worst status across all regions
status_priority = {
    "OK": 0,
    "INFO": 1,
    "WARNING": 2,
    "CRITICAL": 3,
    "HYPER-CRITICAL": 4,
}

if status_priority.get(region_status, 0) > status_priority.get(worst_status, 0):
    worst_status = region_status
    worst_region = region
    worst_region_count = replicating

# Set account-level status to worst region status
account["status"] = worst_status
```

### 4. Regional Warnings
Warnings now reference specific regions:

```python
if worst_status == "WARNING":
    account_warnings.append(
        f"Plan capacity in {worst_region} - at {worst_region_count} servers (75-83%)"
    )
```

## Frontend Changes

### 1. Removed System Status Page
- **Deleted**: `frontend/src/pages/SystemStatusPage.tsx`
- **Reason**: Redundant with Dashboard capacity visualizations

### 2. Removed Getting Started Page
- **Deleted**: `frontend/src/pages/GettingStartedPage.tsx`
- **Reason**: Unnecessary navigation clutter
- **New Behavior**: Dashboard redirects to settings modal when no accounts exist

### 3. Consolidated Capacity Visualizations
Moved all 6 capacity gauges from System Status to Dashboard:

1. **Replication Capacity** - Shows per-region tracking
2. **Recovery Capacity** - Total recovery instances
3. **Available Slots** - Combined available capacity
4. **Concurrent Recovery Jobs** - Active jobs vs 20 limit
5. **Servers in Active Jobs** - Servers in jobs vs 500 limit
6. **Max Servers Per Job** - Largest job vs 100 limit

### 4. Updated Navigation
Removed from `frontend/src/components/cloudscape/AppLayout.tsx`:
- System Status link (line 64)
- Getting Started link

### 5. Updated Routes
Removed from `frontend/src/App.tsx`:
- `/system-status` route
- `/getting-started` route

Both routes now return React Router's catch-all redirect to `/`.

## Testing & Verification

### Backend Tests Fixed
- `test_account_breakdown_completeness_property.py`: Fixed to handle zero-server regions correctly

### Code Formatting
- Ran `black --line-length 79 lambda/` before deployment

### Deployment Process
1. ✅ Code committed to git with proper commit message
2. ✅ Deployed backend via `./scripts/deploy.sh test` (completed 02:10:53 UTC)
3. ✅ Frontend stack updated (completed 06:03:26 UTC)
4. ✅ CloudFront invalidation completed (06:03:26 UTC)
5. ✅ Build version: 20260202-0102

## Verification Checklist

- [x] Backend Lambda deployed successfully
- [x] Frontend built and deployed to S3
- [x] CloudFront invalidation completed
- [x] System Status page deleted (file removed)
- [x] Getting Started page deleted (file removed)
- [x] Routes removed from App.tsx
- [x] Navigation updated in AppLayout.tsx
- [x] All 6 capacity gauges visible on Dashboard
- [x] Per-region quota tracking implemented
- [x] Tests passing
- [x] Code formatted with black

## Example: Multi-Region Scenario

**Before Fix**:
- Account with 200 servers in us-east-1 + 200 servers in us-west-2
- Total: 400 servers
- Status: CRITICAL (400 > 300) ❌ **WRONG!**

**After Fix**:
- us-east-1: 200/300 servers (67%) - Status: INFO
- us-west-2: 200/300 servers (67%) - Status: INFO
- Overall Status: INFO (worst region) ✅ **CORRECT!**
- Total Regional Capacity: 600 (2 regions × 300)
- Available Slots: 400 (600 - 200)

## API Response Example

```json
{
  "combined": {
    "totalReplicating": 400,
    "maxReplicating": 600,
    "percentUsed": 66.67,
    "availableSlots": 200,
    "status": "INFO",
    "activeRegions": 2,
    "totalRegionalCapacity": 600
  },
  "accounts": [
    {
      "accountId": "123456789012",
      "accountType": "target",
      "replicatingServers": 400,
      "totalServers": 400,
      "maxReplicating": 600,
      "percentUsed": 66.67,
      "availableSlots": 200,
      "status": "INFO",
      "activeRegions": 2,
      "totalRegionalCapacity": 600,
      "regionalBreakdown": [
        {
          "region": "us-east-1",
          "replicatingServers": 200,
          "totalServers": 200,
          "maxReplicating": 300,
          "percentUsed": 66.67,
          "availableSlots": 100,
          "status": "INFO"
        },
        {
          "region": "us-west-2",
          "replicatingServers": 200,
          "totalServers": 200,
          "maxReplicating": 300,
          "percentUsed": 66.67,
          "availableSlots": 100,
          "status": "INFO"
        }
      ],
      "warnings": [
        "Monitor capacity in us-east-1 - at 200 servers (67-75%)"
      ]
    }
  ]
}
```

## Files Modified

### Backend
- `lambda/query-handler/index.py` (lines 3577-3900)
  - Per-region capacity tracking
  - Regional status calculation
  - Regional warnings

### Frontend
- `frontend/src/pages/Dashboard.tsx`
  - Added all 6 capacity gauges
  - Added global Refresh button
  - Removed individual refresh buttons
- `frontend/src/components/cloudscape/AppLayout.tsx`
  - Removed System Status navigation link
  - Removed Getting Started navigation link
- `frontend/src/App.tsx`
  - Removed System Status route
  - Removed Getting Started route

### Deleted Files
- `frontend/src/pages/SystemStatusPage.tsx`
- `frontend/src/pages/GettingStartedPage.tsx`

### Tests
- `tests/unit/test_account_breakdown_completeness_property.py`
  - Fixed to handle zero-server regions

## Deployment Info

- **Environment**: test
- **Stack**: hrp-drs-tech-adapter-dev
- **CloudFront URL**: https://d1kqe40a9vwn47.cloudfront.net
- **Build Version**: 20260202-0102
- **Backend Deployed**: 2026-02-02 02:10:53 UTC
- **Frontend Deployed**: 2026-02-02 06:03:26 UTC
- **CloudFront Invalidation**: Completed 06:03:26 UTC

## Impact

### Correctness
- ✅ Fixed critical bug in quota tracking
- ✅ Now correctly handles multi-region deployments
- ✅ Accurate status reporting per region

### User Experience
- ✅ Simplified navigation (removed redundant pages)
- ✅ All capacity metrics in one place (Dashboard)
- ✅ Clearer per-region quota information
- ✅ Better warnings with specific region references

### Performance
- ✅ No performance impact (same API calls)
- ✅ Reduced frontend bundle size (2 fewer pages)

## Next Steps

1. Monitor Dashboard capacity visualizations in production
2. Verify multi-region scenarios work correctly
3. Test with accounts that have servers in 3+ regions
4. Consider adding per-region drill-down view if needed

## Related Documentation

- [DRS Service Quotas Complete](../reference/DRS_SERVICE_QUOTAS_COMPLETE.md)
- [DRS Service Limits and Capabilities](../reference/DRS_SERVICE_LIMITS_AND_CAPABILITIES.md)
- [AWS Multi-Account DRS Documentation](https://docs.aws.amazon.com/drs/latest/userguide/multi-account.html)
