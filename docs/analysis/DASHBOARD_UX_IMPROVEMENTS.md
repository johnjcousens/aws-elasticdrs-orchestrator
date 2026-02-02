# Dashboard UX Improvements - Per-Account Breakdown

**Date**: February 2, 2026  
**Status**: ✅ COMPLETE  
**Deployment**: aws-drs-orchestration-test (build 20260202-0800)

## Changes Implemented

### 1. Removed Duplicate "Refresh Capacity" Button
**Issue**: The DRS Service Capacity container had its own "Refresh Capacity" button, creating redundancy with the main page "Refresh" button.

**Solution**: Removed the duplicate button from the container header. The main "Refresh" button in the page header already refreshes both executions and capacity data.

**Files Modified**:
- `frontend/src/pages/Dashboard.tsx` (line ~350)

### 2. Added Per-Account Breakdown Table
**Issue**: After removing System Status page, the detailed per-account capacity view was lost.

**Solution**: Added comprehensive per-account capacity table to Dashboard showing:

#### Table Columns
1. **Account** - Account name and ID with type badge
2. **Type** - Target or Staging (color-coded)
3. **Replicating Servers** - Current/Max with format "200 / 300"
4. **Percentage Used** - Numeric percentage with color-coded progress bar
   - Green: < 67%
   - Yellow: 67-83%
   - Red: > 83%
5. **Available Slots** - Remaining capacity
6. **Status** - Color-coded status indicator
   - Success (green): OK
   - Info (blue): INFO
   - Warning (yellow): WARNING
   - Error (red): CRITICAL/HYPER-CRITICAL
7. **Regions** - Per-region breakdown with:
   - Region code (e.g., us-east-1)
   - Server count per region
   - Regional status indicator (when not OK)

#### Table Features
- Sortable by all columns
- Embedded variant for clean integration
- Shows regional status when region status is not OK
- Responsive layout with proper spacing
- Empty state handling

#### Account-Specific Warnings
- Displayed below the table
- Grouped by account with account name in header
- Color-coded by severity (info/warning/error)
- Only shown for accounts with warnings

**Files Modified**:
- `frontend/src/pages/Dashboard.tsx` (added table after gauges)
- `frontend/src/types/staging-accounts.ts` (added missing fields to RegionalCapacity)

### 3. Updated RegionalCapacity Type
**Issue**: TypeScript compilation errors due to missing fields in RegionalCapacity interface.

**Solution**: Added optional fields to RegionalCapacity:
- `maxReplicating?: number` - Maximum servers allowed (300 per region)
- `percentUsed?: number` - Percentage of capacity used
- `availableSlots?: number` - Available capacity
- `status?: CapacityStatus` - Regional status (OK/INFO/WARNING/CRITICAL)

All fields are optional to maintain backward compatibility with existing code.

**Files Modified**:
- `frontend/src/types/staging-accounts.ts` (lines 125-145)

## Visual Layout

```
Dashboard
├── Execution Metrics (4 columns)
│   ├── Active Executions
│   ├── Completed
│   ├── Failed
│   └── Success Rate
│
├── DRS Service Capacity
│   ├── Warnings (if any)
│   │
│   ├── Primary Metrics (3 columns)
│   │   ├── Replication Capacity (gauge + status)
│   │   ├── Recovery Capacity (gauge + status)
│   │   └── Available Slots (number + account count)
│   │
│   ├── Service Limits (3 columns)
│   │   ├── Concurrent Recovery Jobs (gauge)
│   │   ├── Servers in Active Jobs (gauge)
│   │   └── Max Servers Per Job (gauge)
│   │
│   └── Per-Account Breakdown (table) ← NEW
│       ├── Account columns (7 total)
│       └── Account-specific warnings ← NEW
│
└── Execution Status & Active Executions (2 columns)
    ├── Pie chart
    └── Active executions list
```

## Example Table Output

| Account | Type | Replicating Servers | % Used | Available | Status | Regions |
|---------|------|---------------------|--------|-----------|--------|---------|
| **Production**<br>123456789012 | Target | 400 / 600 | 66.7%<br>[████████░░] | 200 | INFO | **us-east-1:** 200 servers<br>**us-west-2:** 200 servers |
| **Staging-East**<br>987654321098 | Staging | 150 / 300 | 50.0%<br>[█████░░░░░] | 150 | OK | **us-east-1:** 150 servers |

## Benefits

### User Experience
- ✅ Single source of truth for all capacity metrics
- ✅ Detailed per-account visibility without navigation
- ✅ Regional breakdown shows exactly where capacity is used
- ✅ Color-coded status indicators for quick assessment
- ✅ Reduced UI clutter (removed duplicate button)

### Technical
- ✅ Type-safe with proper TypeScript interfaces
- ✅ Sortable table for flexible data exploration
- ✅ Responsive design with CloudScape components
- ✅ Consistent with AWS console patterns

### Operational
- ✅ Quickly identify which accounts/regions need attention
- ✅ See exact server counts per region
- ✅ Understand capacity distribution across multi-region deployments
- ✅ Actionable warnings with specific region references

## Deployment Info

- **Environment**: test
- **Stack**: aws-drs-orchestration-test
- **CloudFront URL**: https://d319nadlgk4oj.cloudfront.net
- **Build Version**: 20260202-0800
- **Deployed**: 2026-02-02 13:01:02 UTC
- **CloudFront Invalidation**: Completed 13:01:02 UTC

## Testing Checklist

- [x] TypeScript compilation successful
- [x] All unit tests passing (167 tests)
- [x] Frontend build successful
- [x] Deployed to test environment
- [x] CloudFront invalidation completed
- [x] Code committed to git
- [x] Changes pushed to remote

## Related Changes

This change completes the UI consolidation started in the per-region quota fix:
- Backend: Per-region quota tracking (lambda/query-handler/index.py)
- Frontend: Removed System Status page
- Frontend: Removed Getting Started page
- Frontend: Consolidated all capacity views into Dashboard

## Files Changed

### Modified
1. `frontend/src/pages/Dashboard.tsx`
   - Removed duplicate "Refresh Capacity" button
   - Added per-account breakdown table
   - Added account-specific warnings section
   - Added Table and ProgressBar imports

2. `frontend/src/types/staging-accounts.ts`
   - Added maxReplicating, percentUsed, availableSlots, status to RegionalCapacity

### Commits
1. `9dbd2324` - fix: remove duplicate Refresh Capacity button and add per-account breakdown table
2. `93cc2de6` - fix: add missing fields to RegionalCapacity type

## Next Steps

1. Monitor Dashboard performance with large account lists
2. Consider adding pagination if account list grows beyond 20-30 accounts
3. Gather user feedback on table layout and column priorities
4. Consider adding export functionality for capacity data

## Related Documentation

- [Per-Region Quota Fix](PER_REGION_QUOTA_FIX.md) - Backend changes for per-region tracking
- [DRS Service Quotas Complete](../reference/DRS_SERVICE_QUOTAS_COMPLETE.md) - Quota reference
