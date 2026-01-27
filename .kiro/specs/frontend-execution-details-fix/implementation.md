# Implementation Plan: Frontend Execution Details Fix

## Problem Analysis

The frontend shows "No DRS job events available yet" because of TWO field name mismatches:

1. **Backend stores**: `waves` array in DynamoDB
   **Frontend expects**: `waveExecutions` array (TypeScript types line 254)

2. **Backend writes**: `serverStatuses` array in each wave (execution-poller line 633)
   **Frontend expects**: `serverExecutions` array (TypeScript types line 256)

## Root Cause

The execution poller writes to DynamoDB:
```python
wave["serverStatuses"] = updated_server_statuses  # Line 633
```

The execution handler returns:
```python
execution["waves"] = [...]  # DynamoDB field name
```

But the frontend expects:
```typescript
interface Execution {
  waveExecutions: WaveExecution[];  // Not "waves"
}

interface WaveExecution {
  serverExecutions: ServerExecution[];  // Not "serverStatuses"
}
```

## Solution

Transform both field names in the execution handler when returning data to the frontend:
1. `waves` → `waveExecutions` (top level)
2. `serverStatuses` → `serverExecutions` (within each wave)

## Changes Made

### 1. `lambda/execution-handler/index.py` - `get_execution_details()` (line ~1460)

**Added:**
```python
# Transform field names for frontend compatibility
for wave in execution.get("waves", []):
    # Backend writes serverStatuses, frontend expects serverExecutions
    if "serverStatuses" in wave and "serverExecutions" not in wave:
        wave["serverExecutions"] = wave["serverStatuses"]
    elif "serverExecutions" not in wave:
        wave["serverExecutions"] = []

# Frontend expects waveExecutions, backend stores waves
execution["waveExecutions"] = execution["waves"]
```

### 2. `lambda/execution-handler/index.py` - `get_execution_details_fast()` (line ~4760)

Added the same transformation logic for the fast endpoint.

## Testing Plan

1. Start an execution with DRS jobs
2. Wait for execution poller to update DynamoDB with server statuses
3. Open execution details in frontend
4. Verify:
   - Wave progress displays correctly (reads from `waveExecutions`)
   - Server statuses show (reads from `serverExecutions`)
   - Server details populate (instance ID, IP, type)
   - No "No DRS job events available yet" message

## Deployment

Use the unified deploy script:
```bash
./scripts/deploy.sh dev --lambda-only
```

This will:
- Package the updated execution-handler Lambda
- Deploy to S3
- Update the Lambda function code
- No CloudFormation changes needed
