# UI Display Bugs - Fix Plan

**Created**: November 30, 2024  
**Status**: In Progress

## Summary

This document outlines the plan to fix all UI display bugs discovered during Phase 2 testing.

## Issues Identified

### ✅ 1. Hardcoded "demo-user" Issue - **FIXED**

**Problem**: ExecutedBy field shows "demo-user" instead of actual authenticated user.

**Root Cause**: Hardcoded string in RecoveryPlansPage.tsx (2 locations) and api.ts fallback.

**Fix Applied**:
- Added `useAuth` hook import to RecoveryPlansPage.tsx
- Added `const { user } = useAuth();` to get current user
- Replaced `executedBy: 'demo-user'` with `executedBy: user?.username || 'unknown'` (2 locations)
- Changed api.ts fallback from `'demo-user'` to `'unknown'`

**Files Modified**:
- `frontend/src/pages/RecoveryPlansPage.tsx`
- `frontend/src/services/api.ts`

**Status**: ✅ Complete - Type-check passed

---

### 2. Wave Progress Bar Always Shows 0%

**Problem**: Wave progress displays "Wave 0 of 3" instead of actual current wave.

**Root Cause**: Backend calculation issue - `currentWave` and `totalWaves` not being computed correctly.

**Location**: `lambda/index.py` - execution status calculation

**Fix Required**:
```python
# In get_execution_status function
def calculate_wave_progress(execution_data):
    """Calculate current wave progress."""
    waves = execution_data.get('waves', [])
    if not waves:
        return 0, 0
    
    total_waves = len(waves)
    current_wave = 0
    
    # Find the first wave that's not completed
    for i, wave in enumerate(waves, 1):
        wave_status = wave.get('status', 'PENDING')
        if wave_status in ['IN_PROGRESS', 'PENDING']:
            current_wave = i
            break
        elif wave_status == 'COMPLETED':
            current_wave = i  # Last completed wave
    
    # If all completed, current = total
    if current_wave == 0:
        current_wave = total_waves
    
    return current_wave, total_waves

# Usage in get_execution_status:
current_wave, total_waves = calculate_wave_progress(execution_item)
execution_item['currentWave'] = current_wave
execution_item['totalWaves'] = total_waves
```

**Files to Modify**:
- `lambda/index.py` - Add wave progress calculation

**Testing**:
- Start new execution
- Verify wave progress shows "Wave 1 of 3"
- As waves complete, verify progress updates to "Wave 2 of 3", etc.

---

### 3. Missing Instance IDs

**Problem**: Instance ID column shows "N/A" even after instances launch.

**Root Cause**: Polling logic not capturing Instance IDs from DRS job logs.

**Location**: `lambda/poller/execution_poller.py`

**Fix Required**:
1. Parse DRS job logs for instance launch events
2. Extract EC2 Instance IDs from log events
3. Store Instance IDs in DynamoDB execution data
4. Include Instance IDs in status updates

**Key Events to Parse**:
```python
# Look for these DRS job log event types:
- "CONVERSION_START" - Indicates conversion beginning
- "LAUNCH_START" - Indicates instance launching
- "LAUNCH_COMPLETED" - Should contain Instance ID

# Example log structure:
{
    "event": "LAUNCH_COMPLETED",
    "eventData": {
        "sourceServerID": "s-xxxxx",
        "ec2InstanceID": "i-0123456789abcdef"
    }
}
```

**Implementation**:
```python
def extract_instance_ids_from_job_logs(job_id):
    """Extract Instance IDs from DRS job logs."""
    paginator = drs_client.get_paginator('describe_job_log_items')
    instance_ids = {}
    
    for page in paginator.paginate(jobID=job_id):
        for log_item in page.get('items', []):
            event = log_item.get('event')
            
            if event == 'LAUNCH_COMPLETED':
                event_data = log_item.get('eventData', {})
                source_id = event_data.get('sourceServerID')
                instance_id = event_data.get('ec2InstanceID')
                
                if source_id and instance_id:
                    instance_ids[source_id] = instance_id
    
    return instance_ids
```

**Files to Modify**:
- `lambda/poller/execution_poller.py` - Add instance ID extraction
- `lambda/index.py` - Include instance IDs in status response

**Testing**:
- Start drill execution
- Wait for conversion to complete
- Verify Instance IDs appear in execution details
- Verify Instance IDs persist across page refreshes

---

### 4. Navigation Back to Execution Details

**Problem**: Cannot click on execution rows to return to details page.

**Root Cause**: ExecutionsPage DataGrid rows not clickable - missing onRowClick handler.

**Location**: `frontend/src/pages/ExecutionsPage.tsx`

**Fix Required**:
```typescript
// Add to ExecutionsPage component:
const handleRowClick = (params: GridRowParams) => {
  const executionId = params.row.executionId;
  navigate(`/executions/${executionId}`);
};

// Add to DataGridWrapper props:
<DataGridWrapper
  rows={rows}
  columns={columns}
  loading={loading}
  error={error}
  onRetry={fetchExecutions}
  onRowClick={handleRowClick}  // Add this
  emptyMessage="No executions found."
  height={600}
  sx={{
    '& .MuiDataGrid-row': {
      cursor: 'pointer',  // Show pointer cursor on hover
    },
  }}
/>
```

**Files to Modify**:
- `frontend/src/pages/ExecutionsPage.tsx` - Add row click handler
- `frontend/src/components/DataGridWrapper.tsx` - Pass through onRowClick prop

**Testing**:
- Navigate to Executions page
- Click on any execution row
- Verify navigation to execution details page
- Verify cursor changes to pointer on hover

---

### 5. Date/Time Display Format

**Problem**: Dates showing as "relative" format (e.g., "2 hours ago") instead of full datetime.

**Root Cause**: DateTimeDisplay component using wrong format prop in ExecutionDetails.

**Location**: `frontend/src/pages/ExecutionDetails.tsx`

**Fix Required**:
```typescript
// Change from:
<DateTimeDisplay value={execution.startTime} format="relative" />

// To:
<DateTimeDisplay value={execution.startTime} format="full" />

// Apply to all datetime fields:
// - startTime
// - endTime
// - lastUpdatedTime
// - Wave start/end times
// - Server launch times
```

**Files to Modify**:
- `frontend/src/pages/ExecutionDetails.tsx` - Change format prop to "full"

**Testing**:
- View execution details
- Verify all dates show as "Nov 30, 2024, 10:30:00 AM" format
- Verify no "2 hours ago" style dates remain

---

### 6. Duration Calculation Bug (489653h)

**Problem**: Duration shows "489653h 49m" (extremely large number) instead of actual duration.

**Root Cause**: Invalid timestamp calculation - likely treating Unix timestamp in seconds as milliseconds, or comparing null/0 values.

**Location**: `frontend/src/components/DateTimeDisplay.tsx` or calculation logic

**Fix Required**:
```typescript
// Add defensive checks for duration calculation:
export function calculateDuration(startTime: number | null, endTime: number | null): string {
  // Validate inputs
  if (!startTime || startTime === 0) {
    return 'N/A';
  }
  
  // If no end time, calculate from start to now
  const end = endTime && endTime > 0 ? endTime : Date.now();
  
  // Ensure timestamps are in milliseconds
  const start = startTime < 10000000000 ? startTime * 1000 : startTime;
  const endMs = end < 10000000000 ? end * 1000 : end;
  
  // Validate duration makes sense (not negative, not > 1 year)
  const durationMs = endMs - start;
  if (durationMs < 0 || durationMs > 365 * 24 * 60 * 60 * 1000) {
    return 'Invalid';
  }
  
  // Calculate hours and minutes
  const hours = Math.floor(durationMs / (60 * 60 * 1000));
  const minutes = Math.floor((durationMs % (60 * 60 * 1000)) / (60 * 1000));
  
  return `${hours}h ${minutes}m`;
}
```

**Files to Modify**:
- `frontend/src/components/DateTimeDisplay.tsx` - Add validation
- `frontend/src/pages/ExecutionDetails.tsx` - Use safe duration calculation

**Testing**:
- View execution details for active execution
- Verify duration shows reasonable values (e.g., "0h 15m")
- View completed execution
- Verify final duration is accurate
- Test edge cases (null start/end times)

---

## Implementation Priority

1. ✅ **Hardcoded "demo-user"** - COMPLETE
2. **Navigation back to execution details** - High priority, easy fix
3. **Date/time display format** - High priority, easy fix
4. **Duration calculation bug** - High priority, medium complexity
5. **Wave progress bar** - Medium priority, medium complexity
6. **Missing Instance IDs** - Medium priority, high complexity

## Testing Checklist

After all fixes:
- [ ] Build frontend successfully
- [ ] Deploy to S3
- [ ] Start new drill execution
- [ ] Verify "Executed By" shows actual username
- [ ] Click execution row to navigate back to details
- [ ] Verify all dates show full format
- [ ] Verify duration shows reasonable values
- [ ] Wait for wave transitions
- [ ] Verify wave progress updates correctly
- [ ] Wait for instance launch
- [ ] Verify Instance IDs appear

## Deployment Plan

1. Make frontend fixes (items 2-4)
2. Build and test locally
3. Deploy frontend to S3
4. Test in deployed environment
5. Make backend fixes (items 5-6)
6. Deploy Lambda updates
7. Full end-to-end test
8. Update PROJECT_STATUS.md

## Notes

- All frontend changes are safe and non-breaking
- Backend changes require Lambda redeployment
- Consider adding automated tests for duration calculation
- Instance ID extraction may require additional DRS API permissions
