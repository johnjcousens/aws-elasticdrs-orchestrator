# Partial Execution Status Enhancement

## Problem Statement

When a recovery plan is cancelled after some waves have completed successfully, the system shows status as "CANCELLED" without indicating partial progress. This creates confusion about what actually succeeded and prevents proper cleanup of recovery instances.

### Current Behavior Example
```
Recovery Plan: 3TierRecoveryPlan
Status: CANCELLED
Wave 1 of 3: Started Jan 26, 2026, 06:02 PM | Ended Jan 26, 2026, 06:03 PM | Duration 38s
Execution ID: 990a8744-347a-431a-a34f-3aca40ca5044
```

**Issues:**
- Status "CANCELLED" doesn't indicate Wave 1 completed successfully
- No "Terminate Recovery Instances" button available
- No clear indication of what succeeded vs what was cancelled
- Operators must dig into wave details to understand actual state

## Requirements

### 1. Enhanced Status Model

Add `PARTIAL_SUCCESS` status for executions where:
- User cancelled execution (or execution failed)
- At least one wave completed successfully
- Recovery instances exist from completed waves

**Status Flow:**
```
Current:
PENDING → IN_PROGRESS → COMPLETED
                      ↘ FAILED
                      ↘ CANCELLED

Enhanced:
PENDING → IN_PROGRESS → COMPLETED
                      ↘ FAILED
                      ↘ CANCELLED (no waves completed)
                      ↘ PARTIAL_SUCCESS (some waves completed)
```

### 2. Termination Availability

**Current Logic:**
```python
# Can terminate if:
# 1. Status in [COMPLETED, FAILED, CANCELLED, PARTIAL]
# 2. Has recovery instances (jobId exists)
# 3. Not already terminated
# 4. No active waves
```

**Issue:** `CANCELLED` executions with recovery instances should show terminate button, but currently may not due to active wave checks.

**Fix:** Ensure termination is available for `CANCELLED` and `PARTIAL_SUCCESS` executions with recovery instances, regardless of wave state (since cancellation already stopped active waves).

### 3. UI Display Enhancements

**Execution Card:**
```
Recovery Plan: 3TierRecoveryPlan
Status: PARTIAL SUCCESS (1 of 3 waves completed)
Wave 1: COMPLETED ✓
Wave 2: CANCELLED
Wave 3: CANCELLED
Duration: 38s
[Terminate Recovery Instances] button visible
```

**Status Badge Colors:**
- `COMPLETED`: Green
- `PARTIAL_SUCCESS`: Orange/Yellow
- `CANCELLED`: Red (no progress)
- `FAILED`: Red

### 4. Wave-Level Status Clarity

Each wave should clearly show:
- `COMPLETED`: Wave finished successfully
- `FAILED`: Wave failed during execution
- `CANCELLED`: Wave cancelled before completion
- `NOT_STARTED`: Wave never initiated

## Implementation Plan

### Phase 1: Backend Status Logic

**File:** `lambda/shared/execution_utils.py`

Add `PARTIAL_SUCCESS` to terminal statuses:
```python
TERMINAL_STATUSES = {"COMPLETED", "CANCELLED", "FAILED", "PARTIAL_SUCCESS"}
```

**File:** `lambda/execution-handler/index.py`

Update `cancel_execution` to set `PARTIAL_SUCCESS` when appropriate:
```python
# After marking waves as cancelled
completed_count = len(completed_waves)
has_recovery_instances = any(w.get("jobId") for w in waves)

if completed_count > 0 and has_recovery_instances:
    final_status = "PARTIAL_SUCCESS"
elif in_progress_waves:
    final_status = "CANCELLING"
else:
    final_status = "CANCELLED"
```

**File:** `lambda/orchestration-stepfunctions/index.py`

Update Step Functions polling to detect partial success:
```python
# When execution cancelled mid-flight
if exec_status == "CANCELLING":
    completed_waves = [w for w in waves if w.get("status") == "COMPLETED"]
    has_instances = any(w.get("jobId") for w in waves)
    
    if completed_waves and has_instances:
        state["status"] = "partial_success"
    else:
        state["status"] = "cancelled"
```

### Phase 2: Termination Logic Update

**File:** `lambda/shared/execution_utils.py`

Update `can_terminate_execution`:
```python
def can_terminate_execution(execution: Dict) -> Dict[str, Any]:
    """
    Determine if execution can be terminated.
    
    For CANCELLED/PARTIAL_SUCCESS: Allow termination if recovery instances exist,
    even if some waves show as "active" (they're stopped but not yet updated).
    """
    execution_status = execution.get("status", "").upper()
    
    # Terminal status check
    if execution_status not in TERMINAL_STATUSES:
        result["reason"] = "Execution not in terminal state"
        return result
    
    # Check for recovery instances
    waves = execution.get("waves", [])
    has_job_id = any(wave.get("jobId") for wave in waves)
    
    if not has_job_id:
        result["reason"] = "No recovery instances found"
        return result
    
    result["hasRecoveryInstances"] = True
    
    # Already terminated check
    if execution.get("instancesTerminated"):
        result["reason"] = "Instances already terminated"
        return result
    
    # For CANCELLED/PARTIAL_SUCCESS: Allow termination even with "active" waves
    # (waves are stopped but status may not be updated yet)
    if execution_status in {"CANCELLED", "PARTIAL_SUCCESS"}:
        result["canTerminate"] = True
        return result
    
    # For other terminal statuses: Check for active waves
    has_active = any(
        wave.get("status", "").upper() in ACTIVE_STATUSES for wave in waves
    )
    
    if has_active:
        result["reason"] = "Waves still active"
        return result
    
    result["canTerminate"] = True
    return result
```

### Phase 3: Frontend Display

**File:** `frontend/src/components/ExecutionCard.tsx` (or equivalent)

Update status display:
```typescript
function getStatusDisplay(execution) {
  const status = execution.status;
  const waves = execution.waves || [];
  const completedWaves = waves.filter(w => w.status === 'COMPLETED').length;
  const totalWaves = waves.length;
  
  if (status === 'PARTIAL_SUCCESS') {
    return {
      label: `PARTIAL SUCCESS (${completedWaves} of ${totalWaves} waves completed)`,
      color: 'orange',
      icon: '⚠️'
    };
  }
  
  if (status === 'CANCELLED') {
    return {
      label: completedWaves > 0 
        ? `CANCELLED (${completedWaves} of ${totalWaves} waves completed)`
        : 'CANCELLED',
      color: 'red',
      icon: '🛑'
    };
  }
  
  // ... other statuses
}
```

**File:** `frontend/src/components/WaveList.tsx` (or equivalent)

Show wave-level status clearly:
```typescript
function WaveStatusBadge({ wave }) {
  const statusConfig = {
    'COMPLETED': { icon: '✓', color: 'green', label: 'Completed' },
    'FAILED': { icon: '✗', color: 'red', label: 'Failed' },
    'CANCELLED': { icon: '⊘', color: 'gray', label: 'Cancelled' },
    'IN_PROGRESS': { icon: '⟳', color: 'blue', label: 'In Progress' },
    'NOT_STARTED': { icon: '○', color: 'gray', label: 'Not Started' }
  };
  
  const config = statusConfig[wave.status] || statusConfig['NOT_STARTED'];
  
  return (
    <Badge color={config.color}>
      {config.icon} {config.label}
    </Badge>
  );
}
```

### Phase 4: Notification Updates

**File:** `lambda/notification-formatter/index.py`

Add `PARTIAL_SUCCESS` notification template:
```python
STATUS_TEMPLATES = {
    # ... existing templates ...
    "PARTIAL_SUCCESS": {
        "subject": f"⚠️ DRS Execution Partially Completed - {recovery_plan_name}",
        "title": "Partial Success",
        "emoji": "⚠️",
        "color": "orange",
    },
}
```

Update notification body to include wave summary:
```python
def format_wave_summary(waves):
    """Format wave completion summary for notifications."""
    completed = [w for w in waves if w.get("status") == "COMPLETED"]
    failed = [w for w in waves if w.get("status") == "FAILED"]
    cancelled = [w for w in waves if w.get("status") == "CANCELLED"]
    
    summary = []
    if completed:
        summary.append(f"✓ {len(completed)} wave(s) completed")
    if failed:
        summary.append(f"✗ {len(failed)} wave(s) failed")
    if cancelled:
        summary.append(f"⊘ {len(cancelled)} wave(s) cancelled")
    
    return " | ".join(summary)
```

## Testing Requirements

### Unit Tests

1. **Status determination logic:**
   - Cancelled with no completed waves → `CANCELLED`
   - Cancelled with completed waves → `PARTIAL_SUCCESS`
   - Failed with completed waves → `PARTIAL_SUCCESS`

2. **Termination availability:**
   - `PARTIAL_SUCCESS` with instances → can terminate
   - `CANCELLED` with instances → can terminate
   - `CANCELLED` without instances → cannot terminate

3. **Wave status normalization:**
   - All wave statuses properly normalized
   - Status badges display correctly

### Integration Tests

1. **Cancel execution after wave 1 completes:**
   - Status becomes `PARTIAL_SUCCESS`
   - Terminate button appears
   - Wave 1 shows `COMPLETED`
   - Waves 2-3 show `CANCELLED`

2. **Cancel execution before any waves complete:**
   - Status becomes `CANCELLED`
   - No terminate button (no instances)
   - All waves show `CANCELLED`

3. **Execution fails after wave 1 completes:**
   - Status becomes `PARTIAL_SUCCESS`
   - Terminate button appears
   - Wave 1 shows `COMPLETED`
   - Wave 2 shows `FAILED`

## Migration Considerations

### Backward Compatibility

Existing `CANCELLED` executions in DynamoDB:
- Will continue to work with existing logic
- Frontend should handle both `CANCELLED` and `PARTIAL_SUCCESS`
- No data migration required (new status only for future executions)

### Rollback Plan

If issues arise:
1. Revert backend to use `CANCELLED` for all cancellations
2. Frontend already handles `CANCELLED` status
3. No data cleanup required

## Success Metrics

1. **Clarity:** Operators can immediately see partial progress in cancelled executions
2. **Actionability:** Terminate button available for all executions with recovery instances
3. **Accuracy:** Status accurately reflects execution outcome (complete vs partial vs none)

## Related Files

- `lambda/shared/execution_utils.py` - Status constants and termination logic
- `lambda/execution-handler/index.py` - Cancel execution endpoint
- `lambda/orchestration-stepfunctions/index.py` - Step Functions polling
- `lambda/notification-formatter/index.py` - Notification templates
- `frontend/src/components/ExecutionCard.tsx` - Execution display
- `frontend/src/components/WaveList.tsx` - Wave status display

## Timeline

- **Phase 1 (Backend):** 2-3 hours
- **Phase 2 (Termination):** 1-2 hours
- **Phase 3 (Frontend):** 3-4 hours
- **Phase 4 (Notifications):** 1 hour
- **Testing:** 2-3 hours

**Total Estimate:** 1-2 days
