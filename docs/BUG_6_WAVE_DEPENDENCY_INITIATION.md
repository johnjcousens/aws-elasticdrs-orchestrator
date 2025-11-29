# Bug 6: Wave Dependency Logic Not Working

## Status
**DISCOVERED** - 11/28/2025 7:48 PM

## Severity
**HIGH** - Core orchestration feature broken

## Symptoms
All waves launch simultaneously instead of respecting sequential dependencies:
```
Database-Wave: 7:45:53 PM
Application-Wave: 7:45:53 PM (should wait for Database)
Web-Wave: 7:45:54 PM (should wait for Application)
```

## Root Cause
`execute_recovery_plan_worker()` initiates all waves in single loop without waiting:

```python
# BROKEN: Initiates all waves immediately
for wave_index, wave in enumerate(waves_list):
    # Dependency check happens but doesn't prevent initiation
    dependencies = wave.get('Dependencies', [])
    if dependencies:
        # Checks if dep wave is COMPLETED
        # But at this point, previous waves are only LAUNCHING
        # So check fails and wave launches anyway
    
    wave_result = initiate_wave(...)  # Launches immediately
    wave_results.append(wave_result)
```

## Expected Behavior
**Sequential Execution by Default**:
1. Wave 1 (Database) launches immediately
2. Wave 2 (Application) waits for Wave 1 COMPLETED
3. Wave 3 (Web) waits for Wave 2 COMPLETED

**With Explicit Dependencies**: Waves respect configured Dependencies array

## Solution Options

### Option 1: ExecutionPoller Handles Dependencies (RECOMMENDED)
- Worker initiates ONLY Wave 1
- Marks dependent waves as PENDING in DynamoDB
- ExecutionPoller checks for PENDING waves when waves complete
- Initiates next wave when dependencies met

**Pros**: 
- Clean separation of concerns
- Poller already tracks completion
- No blocking in worker Lambda

**Cons**:
- More complex poller logic
- Slight delay between waves (1 poller cycle ~15s)

### Option 2: Worker Waits for Completion
- Worker initiates Wave 1
- Polls DRS until Wave 1 COMPLETED
- Initiates Wave 2, repeat...

**Pros**:
- Simpler logic
- Immediate wave transitions

**Cons**:
- Worker Lambda runs for entire execution (15+ min timeout risk)
- Doesn't scale for long executions
- Defeats async pattern

### Option 3: Step Functions State Machine
- Use Step Functions with Wait states
- Each wave is a state with conditional transitions
- Wait for completion before next wave

**Pros**:
- Built-in orchestration
- Visual workflow
- Robust error handling

**Cons**:
- Major architecture change
- Requires Step Functions deployment
- More complex for simple sequential execution

## Recommended Fix
**Implement Option 1**: ExecutionPoller-based dependency management

**Changes Needed**:

1. **Worker (lambda/index.py)**:
   ```python
   # Only initiate Wave 1 (waves with no dependencies)
   # Mark dependent waves as PENDING
   for wave_index, wave in enumerate(waves_list):
       # Check if has dependencies on previous waves
       has_deps = wave_index > 0  # Implicit sequential dependency
       
       if has_deps:
           # Don't initiate, mark as PENDING
           wave_results.append({
               'Status': 'PENDING',
               'DependsOnWave': wave_index,  # Previous wave
               ...
           })
       else:
           # Initiate immediately (no dependencies)
           wave_result = initiate_wave(...)
           wave_results.append(wave_result)
   ```

2. **ExecutionPoller (lambda/poller/execution_poller.py)**:
   ```python
   # After polling DRS job completion
   if wave_completed:
       # Check for PENDING waves that depend on this one
       for wave in execution['Waves']:
           if wave['Status'] == 'PENDING':
               deps_met = check_dependencies_met(wave, execution)
               if deps_met:
                   # Initiate the dependent wave
                   initiate_pending_wave(execution_id, wave)
   ```

## Testing Plan
1. Create recovery plan with 3 waves
2. Execute and verify sequential initiation:
   - Wave 1 launches immediately
   - Wave 2 launches after Wave 1 COMPLETED
   - Wave 3 launches after Wave 2 COMPLETED
3. Verify timing: ~5 min between wave completions

## Related Issues
- Bug 1: Wave JobId storage (FIXED)
- Bug 2: Server data population (FIXED)
- Bug 3: DateTimeDisplay null handling (FIXED)
- Bug 5: Wave dependencies analysis (DOCUMENTED)

## Impact
- **User Experience**: Defeats purpose of wave-based orchestration
- **Risk**: All infrastructure launches simultaneously → resource contention
- **Coordination**: Can't ensure DB ready before App servers
- **Testing**: Can't validate proper sequential DR execution

## Priority
**HIGH** - Must fix before production

Phase 1 MVP requires proper wave sequencing for:
- Database initialization before app servers
- Network configuration ordering
- License server dependencies
- Phased cutover scenarios
