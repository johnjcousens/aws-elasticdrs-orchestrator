# Granular Progress Tracking - Design Document

## Overview

This design implements granular progress tracking for DRS recovery operations by mapping DRS job log events to progress percentages. Instead of showing 10% progress until servers reach LAUNCHED status, the system will show incremental progress through snapshot, conversion, and launch phases.

## Architecture

### Component Architecture

```
WaveProgress Component
├── calculateProgress() - Main progress calculation
│   ├── getEffectiveWaveStatus() - Determine wave completion
│   └── getServerProgressFromJobLogs() - Map events to progress
├── getServerStatusFromJobLogs() - Get current server status
└── Display Components
    ├── ProgressBar - Overall progress
    └── Wave Containers - Individual wave details
```

### Data Flow

```
Backend API
    ↓
JobLogsResponse (DRS events)
    ↓
WaveProgress Component
    ↓
getServerProgressFromJobLogs() - Maps events to 0-100%
    ↓
calculateProgress() - Averages server progress
    ↓
ProgressBar - Displays percentage
```

## Implementation Details

### 1. Event-to-Progress Mapping

**Function**: `getServerProgressFromJobLogs(serverId, waveNumber, jobLogs)`

**Purpose**: Maps DRS job events to progress percentages for a single server.

**Event Mapping**:
```typescript
LAUNCH_END          → 100%  (1.0)   - Server fully launched
LAUNCH_START        → 75%   (0.75)  - Launching instance
CONVERSION_END      → 50%   (0.5)   - Conversion complete
CONVERSION_START    → 37.5% (0.375) - Converting volumes
SNAPSHOT_END        → 25%   (0.25)  - Snapshot complete
SNAPSHOT_START      → 12.5% (0.125) - Creating snapshot
USING_PREVIOUS_SNAPSHOT → 12.5% (0.125) - Using existing snapshot
CLEANUP_START/END   → 5%    (0.05)  - Cleanup phase
No events           → 0%    (0.0)   - Not started
```

**Algorithm**:
1. Find all events for the server in the wave's job log
2. Sort events by timestamp (most recent first)
3. Return progress percentage for the most recent event
4. Return 0 if no events found

**Edge Cases**:
- Missing job logs: Return 0 (fallback to launchStatus)
- No events for server: Return 0 (fallback to launchStatus)
- Multiple events at same time: Use most recent by timestamp

### 2. Progress Calculation

**Function**: `calculateProgress(waves, totalWaves, jobLogs)`

**Purpose**: Calculate overall progress across all waves.

**Algorithm**:
```typescript
totalProgress = 0

for each wave:
  if wave is completed:
    totalProgress += 1.0
  else if wave is in_progress:
    serverProgress = 0
    for each server in wave:
      // Try job log events first
      eventProgress = getServerProgressFromJobLogs(server, wave, jobLogs)
      if eventProgress > 0:
        serverProgress += eventProgress
      else:
        // Fallback to launchStatus
        if server.launchStatus === 'LAUNCHED':
          serverProgress += 1.0
    
    // Average server progress for this wave
    waveProgress = serverProgress / serverCount
    totalProgress += waveProgress
  // else: pending waves contribute 0

percentage = (totalProgress / totalWaves) * 100
```

**Example Calculation** (3 waves, wave 1 has 4 servers):

| State | Server 1 | Server 2 | Server 3 | Server 4 | Wave Progress | Overall |
|-------|----------|----------|----------|----------|---------------|---------|
| Start | 0% | 0% | 0% | 0% | 0% | 0% |
| S1 SNAPSHOT_START | 12.5% | 0% | 0% | 0% | 3.1% | 1% |
| S1 SNAPSHOT_END | 25% | 0% | 0% | 0% | 6.25% | 2% |
| S1 CONVERSION_START | 37.5% | 0% | 0% | 0% | 9.4% | 3% |
| S1 CONVERSION_END | 50% | 0% | 0% | 0% | 12.5% | 4% |
| S1 LAUNCH_START | 75% | 0% | 0% | 0% | 18.75% | 6% |
| S1 LAUNCH_END | 100% | 0% | 0% | 0% | 25% | 8% |
| All LAUNCH_END | 100% | 100% | 100% | 100% | 100% | 33% |

### 3. Monotonic Progress Guarantee

**Requirement**: Progress must never decrease.

**Implementation**:
- Events are sorted by timestamp (most recent first)
- Only the most recent event determines progress
- Once a server reaches a phase, it cannot go backwards
- Wave completion is final (cannot revert to in_progress)

**Validation**:
- Unit tests verify progress never decreases
- Property-based tests verify monotonicity across random event sequences

### 4. Fallback Behavior

**Scenario**: Job logs unavailable or incomplete.

**Fallback Strategy**:
```typescript
if (jobLogs is null or undefined):
  // Use current behavior
  if (server.launchStatus === 'LAUNCHED'):
    serverProgress = 1.0
  else:
    serverProgress = 0
else if (no events for server):
  // Use launchStatus as fallback
  if (server.launchStatus === 'LAUNCHED'):
    serverProgress = 1.0
  else:
    serverProgress = 0
else:
  // Use job log events
  serverProgress = getServerProgressFromJobLogs(...)
```

**Logging**:
- Log warning when falling back to launchStatus
- Include server ID and wave number in warning
- Track fallback frequency for monitoring

## Data Structures

### Input Types

```typescript
interface JobLogsResponse {
  executionId: string;
  jobLogs: Array<{
    jobId: string;
    waveNumber: number;
    events: JobLogEvent[];
  }>;
}

interface JobLogEvent {
  event: string; // Event type
  logDateTime: string; // ISO timestamp
  sourceServerId?: string;
  conversionServerId?: string;
  eventData?: Record<string, any>;
  error?: string;
}

interface WaveExecution {
  waveNumber: number;
  waveName?: string;
  status: string;
  jobId?: string;
  startTime?: number;
  endTime?: number;
  serverExecutions: ServerExecution[];
}

interface ServerExecution {
  serverId: string;
  serverName?: string;
  hostname?: string;
  launchStatus?: string;
  status?: string;
  region?: string;
}
```

### Output Types

```typescript
interface ProgressResult {
  percentage: number; // 0-100
  completed: number;  // Count of completed waves
  total: number;      // Total wave count
}
```

## Component Integration

### WaveProgress Component

**Location**: `frontend/src/components/WaveProgress.tsx`

**Modified Functions**:
1. `getServerProgressFromJobLogs()` - NEW (lines 289-337)
2. `calculateProgress()` - MODIFIED (lines 339-420)

**Unchanged Functions**:
- `getEffectiveWaveStatus()` - Wave status determination
- `getServerStatusFromJobLogs()` - Current server status
- `formatJobLogEvent()` - Event display formatting
- All display/rendering logic

**Props**:
```typescript
interface WaveProgressProps {
  waves: WaveExecution[];
  currentWave?: number;
  totalWaves?: number;
  jobLogs?: JobLogsResponse | null; // REQUIRED for granular progress
}
```

### Parent Component Integration

**No changes required** - Parent components already pass `jobLogs` prop:
- `ExecutionDetails.tsx` fetches job logs via API
- `WaveProgress` receives job logs as prop
- Existing polling mechanism continues to work

## Performance Considerations

### Complexity Analysis

**getServerProgressFromJobLogs()**:
- Time: O(E) where E = events per server (typically 6-10)
- Space: O(1) - no additional storage

**calculateProgress()**:
- Time: O(W × S × E) where:
  - W = waves (typically 3-10)
  - S = servers per wave (typically 2-20)
  - E = events per server (typically 6-10)
- Space: O(1) - no additional storage

**Worst Case** (10 waves, 50 servers, 10 events):
- Operations: 10 × 50 × 10 = 5,000
- Expected time: < 5ms (well under 100ms requirement)

### Optimization Strategies

1. **Event Sorting**: Sort once per wave, not per server
2. **Early Exit**: Return immediately if no job logs
3. **Memoization**: Consider memoizing server progress if performance issues arise

## Error Handling

### Error Scenarios

1. **Missing Job Logs**
   - Cause: API failure, network timeout
   - Handling: Fall back to launchStatus
   - User Impact: Progress updates less granular but still functional

2. **Malformed Event Data**
   - Cause: Backend data corruption, API version mismatch
   - Handling: Skip malformed events, use next valid event
   - User Impact: Progress may skip phases but remains monotonic

3. **Missing Server Events**
   - Cause: DRS job hasn't started for server yet
   - Handling: Return 0, fall back to launchStatus
   - User Impact: Server shows 0% until first event

4. **Timestamp Parsing Errors**
   - Cause: Invalid timestamp format
   - Handling: Use current time as fallback
   - User Impact: Event ordering may be incorrect but progress still updates

### Error Logging

```typescript
// Log fallback usage
if (!jobLogs) {
  console.warn('Job logs unavailable, using launchStatus fallback');
}

// Log missing events
if (serverEvents.length === 0) {
  console.debug(`No events for server ${serverId} in wave ${waveNumber}`);
}

// Log malformed data
if (!event.logDateTime) {
  console.error('Event missing timestamp', event);
}
```

## Testing Strategy

### Unit Tests

**Test File**: `frontend/src/components/__tests__/WaveProgress.test.tsx`

**Test Cases**:

1. **Event Mapping Tests**
   ```typescript
   test('maps SNAPSHOT_START to 12.5%', () => {
     const progress = getServerProgressFromJobLogs(
       'server-1',
       0,
       mockJobLogsWithEvent('SNAPSHOT_START')
     );
     expect(progress).toBe(0.125);
   });
   ```

2. **Progress Calculation Tests**
   ```typescript
   test('calculates wave progress as average of server progress', () => {
     const waves = [mockWaveWithServers(4)];
     const jobLogs = mockJobLogsWithMixedProgress();
     const result = calculateProgress(waves, 3, jobLogs);
     expect(result.percentage).toBeGreaterThan(0);
     expect(result.percentage).toBeLessThan(100);
   });
   ```

3. **Fallback Tests**
   ```typescript
   test('falls back to launchStatus when job logs missing', () => {
     const waves = [mockWaveWithLaunchedServers()];
     const result = calculateProgress(waves, 3, null);
     expect(result.percentage).toBe(33); // 1 wave complete out of 3
   });
   ```

4. **Monotonic Progress Tests**
   ```typescript
   test('progress never decreases', () => {
     const events = ['SNAPSHOT_START', 'CONVERSION_START', 'LAUNCH_END'];
     const progressValues = events.map(event => 
       getServerProgressFromJobLogs('s1', 0, mockJobLogsWithEvent(event))
     );
     
     for (let i = 1; i < progressValues.length; i++) {
       expect(progressValues[i]).toBeGreaterThanOrEqual(progressValues[i-1]);
     }
   });
   ```

## Deployment Strategy

### Phase 1: Implementation (Current)
- ✅ Implement `getServerProgressFromJobLogs()`
- ✅ Update `calculateProgress()` to use job log events
- ✅ Add fallback logic for missing job logs
- ✅ Update requirements document with historical context

### Phase 2: Testing
- [ ] Write unit tests for event mapping
- [ ] Write unit tests for progress calculation
- [ ] Write integration tests for full recovery flow
- [ ] Write property-based tests for monotonicity
- [ ] Manual testing with real DRS jobs

### Phase 3: Deployment
- [ ] Build frontend: `cd frontend && npm run build`
- [ ] Deploy to test environment: `./scripts/deploy.sh test --frontend-only`
- [ ] Monitor CloudWatch logs for errors
- [ ] Verify progress updates in UI during active recovery

### Phase 4: Validation
- [ ] Run actual DRS recovery job
- [ ] Verify progress updates through all phases
- [ ] Verify progress reaches 100% on completion
- [ ] Verify no console errors
- [ ] Collect user feedback

## Success Criteria

### Functional Requirements

- ✅ Progress updates when servers enter SNAPSHOT phase
- ✅ Progress updates when servers enter CONVERSION phase
- ✅ Progress updates when servers enter LAUNCH phase
- ✅ Progress never decreases (monotonic)
- ✅ Progress reaches 100% only when all waves complete
- ✅ Fallback to launchStatus when job logs unavailable

### Non-Functional Requirements

- [ ] Progress calculation < 100ms (target: < 5ms)
- [ ] No increase in frontend errors
- [ ] Progress updates at least every 30 seconds during recovery
- [ ] User feedback indicates improved visibility

## References

- Requirements: `.kiro/specs/granular-progress-tracking/requirements.md`
- Implementation: `frontend/src/components/WaveProgress.tsx` (lines 289-420)
- AWS DRS Events: https://docs.aws.amazon.com/drs/latest/userguide/drs-job-log-events.html
- Historical Implementation: Git commit `574cefbb` (January 14, 2026)
