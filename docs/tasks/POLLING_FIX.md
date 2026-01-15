# Execution Details Page Polling Fix

## Issue
Execution details page not auto-refreshing every 3 seconds when executions first start.

**Reported URL**: https://***REMOVED***.cloudfront.net/executions/9b6f8b3d-c4a2-4d7d-96c6-81d61218e511

## Root Cause

### History of the Bug

**v1.6.0 (Working)**: Dependencies were `[execution, fetchExecution]`
- Polling started when execution loaded ✓
- But had stale closure issues after resume from pause

**Commit 33e142cc (January 15, 2026)**: Changed to `[execution?.status, executionId]`
- Fixed stale closure issue after resume ✓
- But broke initial polling startup ✗

**Current Fix (b39c32e6)**: Changed to `[execution, executionId]`
- Polling starts when execution loads ✓
- No stale closures (fetchExecution not in dependencies) ✓

### The Problem with 33e142cc

```typescript
// BROKEN (commit 33e142cc)
}, [execution?.status, executionId]);
```

When execution first loads:
1. Initial state: `execution = null`
2. useEffect runs, returns early because `!execution`
3. Execution loads with status "in_progress"
4. `execution?.status` evaluates to "in_progress" (same as before when it was undefined)
5. useEffect doesn't re-run because dependency didn't change
6. **Polling never starts**

## Fix Applied

Changed dependency to trigger when execution object loads:

```typescript
// AFTER (fixed)
}, [execution, executionId]); // Depend on execution to start polling when it loads
```

**How it works now**:
1. Initial state: `execution = null`
2. useEffect runs, returns early because `!execution`
3. Execution loads (object changes from null to populated)
4. useEffect re-runs because `execution` dependency changed
5. **Polling starts immediately**

## Technical Details

**File**: `frontend/src/pages/ExecutionDetailsPage.tsx`
**Line**: 147
**Commit**: `b39c32e6`

The fix is minimal - just one dependency change. The polling logic itself was correct, it just wasn't being triggered at the right time.

## Testing

After deployment completes (~12 minutes):
1. Start a new execution
2. Navigate to execution details page
3. Verify page updates every 3 seconds
4. Check browser console for no errors
5. Confirm wave progress updates in real-time

## Deployment Status

- **Commit**: `b39c32e6` - "fix: start polling when execution loads, not just when status changes"
- **Pushed**: January 15, 2026
- **CI/CD**: Running (GitHub Actions)
- **ETA**: ~12 minutes for full deployment

## Related Issues

This was a subtle React dependency bug. The original comment "Remove fetchExecution dependency to prevent stale closures" was correct, but removing `execution` from dependencies had the unintended side effect of preventing polling from starting when the page first loads.

The fix maintains the stale closure prevention (by not depending on `fetchExecution`) while ensuring polling starts when execution data arrives.
