# Granular Progress Tracking - Requirements

## Problem Statement

The current progress bar implementation is stuck at 10% during DRS job execution because it only counts servers that have reached `LAUNCHED` status. This provides poor user experience as users see no progress updates during the lengthy snapshot, conversion, and launch phases that can take 10-30 minutes per server.

## Historical Context

### January 14, 2026 - Working Granular Implementation (Commit 574cefbb)

The system previously had a working granular progress implementation that counted individual server launches:

```typescript
// January 14, 2026 version - GRANULAR server-level tracking
const launchedServers = servers.filter(s => {
  const status = (s.launchStatus || s.status || '').toUpperCase();
  return status === 'LAUNCHED';
}).length;
totalProgress += (launchedServers / servers.length);
```

**Example with 4 servers in a wave (3 total waves):**
- 0 servers launched: 0%
- 1 server launched: 8% (0.25/3 waves)
- 2 servers launched: 17% (0.5/3 waves)
- 3 servers launched: 25% (0.75/3 waves)
- 4 servers launched: 33% (1.0/3 waves = wave complete)

This provided smooth progress updates as each server reached LAUNCHED status.

### Current Behavior (Post January 31, 2026)

The `calculateProgress` function was changed to use a base progress model:
- Gives completed waves: 1.0 (100%)
- Gives in-progress waves: 0.1 (10%) base + (launched servers / total servers * 0.9)
- Only counts servers with `launchStatus === 'LAUNCHED'` as contributing to progress
- Ignores intermediate DRS job events (SNAPSHOT_START/END, CONVERSION_START/END, LAUNCH_START)

**Example**: Wave with 4 servers
- Wave starts: 10% (base progress)
- 0 servers launched: 10%
- 1 server launched: 33% (0.1 + 0.225 = 0.325)
- All servers launched: 100%

**Problem**: During the 10-30 minutes it takes for servers to go through snapshot → conversion → launch phases, the progress bar stays stuck at 10%.

## Desired Behavior

Progress should reflect the actual DRS recovery phases for each server:

**DRS Recovery Phases** (from AWS DRS job log events):
1. SNAPSHOT_START → SNAPSHOT_END: 0-25% of server progress
2. CONVERSION_START → CONVERSION_END: 25-50% of server progress  
3. LAUNCH_START → LAUNCH_END: 50-100% of server progress

**Example**: Wave with 4 servers
- Wave starts: 3% (0.1/3 waves)
- Server 1 SNAPSHOT_START: 6% (server at 25% = 0.225/3)
- Server 1 SNAPSHOT_END: 9% (server at 25%)
- Server 1 CONVERSION_START: 11% (server at 37.5%)
- Server 1 CONVERSION_END: 14% (server at 50%)
- Server 1 LAUNCH_START: 17% (server at 75%)
- Server 1 LAUNCH_END: 19% (server at 100%)
- All 4 servers LAUNCH_END: 33% (wave complete)

## User Stories

### US-1: Real-time Progress Updates
**As a** DR coordinator  
**I want** to see progress updates as servers move through snapshot, conversion, and launch phases  
**So that** I can monitor recovery progress and estimate completion time

**Acceptance Criteria:**
1. Progress bar updates when servers enter SNAPSHOT_START phase
2. Progress bar updates when servers complete SNAPSHOT_END phase
3. Progress bar updates when servers enter CONVERSION_START phase
4. Progress bar updates when servers complete CONVERSION_END phase
5. Progress bar updates when servers enter LAUNCH_START phase
6. Progress bar updates when servers complete LAUNCH_END phase
7. Progress never decreases (monotonically increasing)
8. Progress reaches 100% only when all waves are complete

### US-2: Accurate Phase Weighting
**As a** DR coordinator  
**I want** each DRS recovery phase to contribute proportionally to overall progress  
**So that** progress reflects actual recovery work being done

**Acceptance Criteria:**
1. SNAPSHOT phase contributes 25% of server progress (0-25%)
2. CONVERSION phase contributes 25% of server progress (25-50%)
3. LAUNCH phase contributes 50% of server progress (50-100%)
4. Multiple servers in same wave contribute equally to wave progress
5. Wave progress is averaged across all servers in the wave

### US-3: Fallback to Current Behavior
**As a** system  
**I want** to fall back to current behavior when job logs are unavailable  
**So that** progress tracking still works even if DRS job logs fail to load

**Acceptance Criteria:**
1. If `jobLogs` is null/undefined, use current `launchStatus === 'LAUNCHED'` logic
2. If job logs exist but have no events for a server, use `launchStatus` as fallback
3. System logs warning when falling back to legacy behavior
4. Progress calculation never throws errors due to missing job logs

## Technical Context

### Existing Functions
- `calculateProgress(waves, totalWaves, jobLogs)` - Current progress calculation (lines 280-360)
- `getServerStatusFromJobLogs(serverId, waveNumber, jobLogs)` - Gets most recent DRS event for server (lines 360+)
- `mapEventToStatus(event)` - Maps DRS event to display status (lines 400+)
- `getEffectiveWaveStatus(wave, jobLogs)` - Determines wave status from job logs

### Data Structures
```typescript
interface JobLogsResponse {
  jobLogs: Array<{
    waveNumber: number;
    events: Array<{
      event: string; // 'SNAPSHOT_START', 'SNAPSHOT_END', etc.
      logDateTime: string;
      eventData: {
        sourceServerID?: string;
      };
    }>;
  }>;
}

interface ServerExecution {
  serverId: string;
  serverName?: string;
  hostname?: string;
  launchStatus?: string; // 'LAUNCHED', 'PENDING', etc.
  status?: string;
}

interface WaveExecution {
  waveNumber: number;
  status: string;
  serverExecutions: ServerExecution[];
}
```

### DRS Event Types (in order)
1. `SNAPSHOT_START` - Server snapshot begins
2. `SNAPSHOT_END` - Server snapshot completes
3. `CONVERSION_START` - EBS volume conversion begins
4. `CONVERSION_END` - EBS volume conversion completes
5. `LAUNCH_START` - EC2 instance launch begins
6. `LAUNCH_END` - EC2 instance launch completes (server fully recovered)

## Non-Functional Requirements

### Performance
- Progress calculation must complete in < 100ms for 10 waves with 50 servers each
- No additional API calls required (use existing `jobLogs` data)

### Reliability
- Progress must never decrease (monotonic)
- Progress must handle missing/incomplete job log data gracefully
- Progress must work with partial job logs (some servers have events, others don't)

### Maintainability
- Code must be well-documented with clear phase weighting logic
- Helper functions should be testable in isolation
- Event-to-progress mapping should be configurable

## Out of Scope

- Changing the overall progress bar UI/styling
- Adding new DRS event types beyond the 6 standard events
- Real-time polling for job log updates (use existing polling mechanism)
- Progress persistence across page refreshes
- Historical progress tracking/analytics

## Dependencies

- Existing `jobLogs` data structure from backend API
- Existing `getServerStatusFromJobLogs` function
- Existing `calculateProgress` function signature (maintain backward compatibility)

## Success Metrics

- Progress bar shows visible updates at least every 30 seconds during active recovery
- User feedback indicates improved visibility into recovery progress
- No increase in frontend errors related to progress calculation
- Progress calculation performance remains under 100ms

## References

- Current implementation: `frontend/src/components/WaveProgress.tsx` lines 280-360
- DRS job log structure: `lambda/execution-handler/index.py` DRSJobDetails interface
- AWS DRS documentation: https://docs.aws.amazon.com/drs/latest/userguide/what-is-drs.html
