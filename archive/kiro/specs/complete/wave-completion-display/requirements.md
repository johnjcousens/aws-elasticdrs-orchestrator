# Wave Completion Display - Requirements

## Problem Statement

When a recovery plan completes successfully, there are two critical display issues:

1. **Wave Status Not Updating to Green**: The wave status indicator remains in its in-progress state (blue 🔄) instead of updating to completed (green ✅) when all waves in the recovery plan are complete.

2. **Missing Server EC2 Information**: After recovery completes, the server table shows empty fields (—) for Instance ID, Type, Private IP, and Launch Time instead of displaying the actual EC2 instance information from the recovered instances.

3. **Server ID Column Label Confusion**: The column header says "Server ID" but displays server Name tags, which is correct behavior but the label is misleading.

## Current Behavior

### Issue 1: Wave Status Display
**Observed**:
```
Recovery Plan: TargetAccountOnlyCompleted
Wave 1 of 1
Started: Feb 11, 2026, 12:51 PM
Ended: Feb 11, 2026, 01:14 PM
Duration: 22m 50s
Status: 🔄 (blue, in-progress indicator)
```

**Expected**:
```
Recovery Plan: TargetAccountOnlyCompleted
Wave 1 of 1
Started: Feb 11, 2026, 12:51 PM
Ended: Feb 11, 2026, 01:14 PM
Duration: 22m 50s
Status: ✅ (green, completed indicator)
```

### Issue 2: Server Information Display
**Observed**:
```
Server ID          | Status | Instance ID | Type | Private IP | Launch Time
hrp-core-db02-az1 | ✓      | —           | —    | —          | —
hrp-core-db01-az1 | ✓      | —           | —    | —          | —
```

**Expected**:
```
Server Name        | Status | Instance ID      | Type       | Private IP  | Launch Time
hrp-core-db02-az1 | ✓      | i-0abc123def456  | t3.medium  | 10.0.1.45   | Feb 11, 2026, 01:10 PM
hrp-core-db01-az1 | ✓      | i-0def789ghi012  | t3.medium  | 10.0.1.46   | Feb 11, 2026, 01:12 PM
```

### Issue 3: Column Header Mislabeling
**Current**: Column header says "Server ID" but displays server Name tags
**Desired**: Column header should say "Server Name" to match what's actually displayed

## Root Cause Analysis

### Issue 1: Wave Status Logic
The `getEffectiveWaveStatus()` function checks multiple conditions to determine wave completion:
1. Wave status from backend
2. All servers have `launchStatus === 'LAUNCHED'`
3. Job logs show `LAUNCH_END` events for all servers

**Problem**: The function may not be correctly identifying completion when:
- Wave status is "started" or "polling" (not explicitly "completed")
- Job logs show completion but wave status hasn't updated
- All servers show ✓ status but wave indicator doesn't update

### Issue 2: Missing Server Data
The server table displays data from `ServerExecution` interface:
- `recoveredInstanceId` - EC2 instance ID
- `instanceType` - EC2 instance type
- `privateIp` - Private IP address
- `launchTime` - Launch timestamp

**Problem**: The backend DOES populate these fields by calling DRS `describe_recovery_instances()` and EC2 `describe_instances()` APIs during polling. However, there appears to be a timing issue where:
1. Frontend polls execution status
2. Backend hasn't finished enriching EC2 data yet
3. Frontend displays empty fields before data is available
4. Subsequent polls may not trigger re-enrichment if wave status hasn't changed

### Issue 3: Column Header
The column definition uses `header: 'Server ID'` but the cell displays `server.serverName || server.hostname || server.serverId`.

**Problem**: Simple labeling issue - header doesn't match displayed content.

## User Stories

### US-1: Wave Completion Status
**As a** DR coordinator  
**I want** the wave status indicator to show green ✅ when all waves complete successfully  
**So that** I can quickly see that the recovery plan finished successfully

**Acceptance Criteria:**
1. When all servers in a wave reach LAUNCHED status, wave shows green ✅
2. When wave has `endTime` set and all servers launched, wave shows green ✅
3. When job logs show LAUNCH_END for all servers, wave shows green ✅
4. Wave status updates automatically when completion is detected
5. Overall progress bar shows 100% when all waves complete
6. Wave status badge shows "Completed" text

### US-2: Server EC2 Information Display
**As a** DR coordinator  
**I want** to see the EC2 instance details for recovered servers  
**So that** I can verify the instances launched correctly and access them if needed

**Acceptance Criteria:**
1. Instance ID column shows actual EC2 instance ID (e.g., i-0abc123def456)
2. Instance ID is a clickable link to AWS Console
3. Type column shows EC2 instance type (e.g., t3.medium, m5.large)
4. Private IP column shows the instance's private IP address
5. Launch Time column shows when the instance was launched
6. All fields update automatically when recovery completes
7. Fields show "—" only when data is truly unavailable (not when it exists but isn't displayed)

### US-3: Clear Column Headers
**As a** DR coordinator  
**I want** column headers to accurately describe the displayed data  
**So that** I understand what information I'm looking at

**Acceptance Criteria:**
1. Column header says "Server Name" when displaying server names
2. Column header matches the primary data displayed in that column
3. Secondary information (hostname, server ID) shown as subtext when different from name

## Technical Context

### Data Flow

```
Backend API (execution-handler)
    ↓
    Fetches DRS job details
    ↓
    Polls for server status updates
    ↓
    Updates DynamoDB with server execution data
    ↓
Frontend API Client
    ↓
    Polls execution status endpoint
    ↓
WaveProgress Component
    ↓
    Displays wave and server information
```

### Relevant Data Structures

```typescript
interface WaveExecution {
  waveNumber: number;
  waveName?: string;
  status: string;           // 'started', 'completed', 'failed', etc.
  jobId?: string;
  startTime?: number;       // Unix timestamp
  endTime?: number;         // Unix timestamp - set when wave completes
  serverExecutions: ServerExecution[];
}

interface ServerExecution {
  serverId: string;                    // DRS source server ID
  serverName?: string;                 // EC2 Name tag
  hostname?: string;                   // Server hostname
  launchStatus?: string;               // 'LAUNCHED', 'PENDING', etc.
  status?: string;                     // Alternative status field
  
  // EC2 Instance Information (may be missing)
  recoveredInstanceId?: string;        // EC2 instance ID
  instanceType?: string;               // EC2 instance type
  privateIp?: string;                  // Private IP address
  region?: string;                     // AWS region
  launchTime?: number;                 // Launch timestamp
  startTime?: number;                  // Alternative timestamp field
}
```

### Current Implementation

**Wave Status Logic** (`getEffectiveWaveStatus()`):
```typescript
// Checks in order:
1. If wave.status is 'completed'/'failed'/'cancelled' → return that
2. If all servers have launchStatus === 'LAUNCHED' → return 'completed'
3. If any server failed → return 'failed'
4. If job logs show LAUNCH_END for all servers → return 'completed'
5. If any server in progress → return 'in_progress'
6. Map wave.status to display status
```

**Server Table Columns**:
- Server ID: Shows `serverName || hostname || serverId`
- Status: Shows badge based on `launchStatus` or `status`
- Instance ID: Shows `recoveredInstanceId` with AWS Console link
- Type: Shows `instanceType`
- Private IP: Shows `privateIp`
- Launch Time: Shows `launchTime || startTime`

## Investigation Questions

### Backend Data Population ✅ VERIFIED
1. ✅ **YES** - Backend populates all fields via `describe_recovery_instances()` and `describe_instances()` (execution-handler lines 7200-7280)
2. ✅ **During polling** - Enrichment happens in poll operation when wave status is checked
3. ✅ **YES** - Poll operation enriches data, but may not re-enrich if wave status unchanged
4. ✅ **YES** - Calls `describe_recovery_instances()` filtered by sourceServerIDs, then `describe_instances()` for EC2 details

### Frontend Data Handling ⚠️ NEEDS INVESTIGATION
1. ❓ **Unknown** - Need to verify API response includes enriched data
2. ❓ **Unknown** - Need to check if API client transforms/filters response
3. ❓ **Unknown** - Need to verify polling continues after LAUNCHED status
4. ⚠️ **LIKELY YES** - Timing issue where frontend polls before backend enrichment completes

### Wave Status Updates ⚠️ NEEDS INVESTIGATION
1. ❓ **Unknown** - Need to verify when backend sets wave.status to "completed"
2. ❓ **Unknown** - Need to verify if backend sets wave.endTime field
3. ⚠️ **LIKELY YES** - Frontend `getEffectiveWaveStatus()` doesn't check `endTime` field, only server statuses and job logs

## Proposed Solutions

### Solution 1: Enhanced Wave Completion Detection

**Approach**: Improve `getEffectiveWaveStatus()` to better detect completion.

**Changes**:
1. Check if `wave.endTime` is set (indicates wave finished)
2. Verify all servers have `launchStatus === 'LAUNCHED'`
3. Check job logs for `JOB_END` event (authoritative completion signal)
4. Consider wave completed if all three conditions are met

**Pros**:
- More reliable completion detection
- Uses multiple signals for confirmation
- Handles edge cases where status field lags

**Cons**:
- Doesn't fix root cause if backend isn't setting endTime
- May still have timing issues

### Solution 2: Backend Investigation and Fix

**Approach**: Investigate and fix backend data population.

**Changes**:
1. Verify backend calls DRS `DescribeRecoveryInstances` API
2. Ensure backend populates all EC2 fields in server execution data
3. Confirm backend updates wave status to "completed" and sets endTime
4. Add logging to track when EC2 data is fetched and stored

**Pros**:
- Fixes root cause
- Ensures data is available for all use cases
- Improves overall system reliability

**Cons**:
- Requires backend code changes
- May need additional DRS API calls
- Could impact performance if not optimized

### Solution 3: Frontend Data Refresh

**Approach**: Add explicit data refresh after completion detected.

**Changes**:
1. When wave reaches completed status, trigger additional API call
2. Fetch latest execution details to get EC2 information
3. Update component state with refreshed data
4. Continue polling for a short period after completion

**Pros**:
- Works around backend timing issues
- Ensures UI has latest data
- Can be implemented quickly

**Cons**:
- Adds extra API calls
- Doesn't fix root cause
- May cause UI flicker during refresh

## Recommended Approach

**Hybrid Solution**: Combine frontend improvements with backend investigation.

**Phase 1: Frontend Quick Fixes**
1. Fix column header: "Server ID" → "Server Name"
2. Enhance `getEffectiveWaveStatus()` to check `wave.endTime` field as completion signal
3. Add logging to track when EC2 data is/isn't available
4. Investigate if polling continues after wave completion to allow data enrichment

**Phase 2: Backend Investigation**
1. ✅ **VERIFIED** - Backend does populate EC2 data via DRS/EC2 APIs
2. ✅ **VERIFIED** - `describe_recovery_instances()` and `describe_instances()` are called
3. ❓ **INVESTIGATE** - Verify when wave.status changes to "completed" and if endTime is set
4. ❓ **INVESTIGATE** - Check if enrichment happens on every poll or only on status change
5. Add backend logging to track enrichment timing

**Phase 3: Comprehensive Fix**
1. Implement backend fixes if issues found
2. Add frontend data refresh if needed
3. Improve error handling for missing data
4. Add user feedback when data is loading

## Success Criteria

### Functional Requirements
- Wave status shows green ✅ when all waves complete
- Wave status badge shows "Completed" text
- Overall progress shows 100% when complete
- Instance ID displays actual EC2 instance ID with working link
- Instance Type displays correct EC2 instance type
- Private IP displays actual private IP address
- Launch Time displays actual launch timestamp
- Column header says "Server Name" not "Server ID"

### Non-Functional Requirements
- Status updates within 30 seconds of completion
- EC2 data appears within 1 minute of instance launch
- No console errors or warnings
- No unnecessary API calls
- Graceful handling of missing data

## Out of Scope

- Real-time WebSocket updates (continue using polling)
- Historical recovery data display
- Server health monitoring after recovery
- Automatic retry of failed recoveries
- Custom column configuration

## Dependencies

- Backend execution-handler Lambda function
- DRS API for instance details
- DynamoDB for execution data storage
- Frontend polling mechanism
- AWS Console link generation

## References

- Current implementation: `frontend/src/components/WaveProgress.tsx`
- Backend handler: `lambda/execution-handler/index.py`
- DRS API documentation: https://docs.aws.amazon.com/drs/latest/APIReference/
- Related spec: `.kiro/specs/granular-progress-tracking/`
