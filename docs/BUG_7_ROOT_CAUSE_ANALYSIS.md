# Bug #7: Root Cause Analysis - ConflictException

**Created**: November 28, 2025
**Status**: DIAGNOSED - Root cause identified

## Error Message

```
ConflictException: One or more of the Source Servers included in API call are 
currently being processed by a Job
```

## Investigation Results

### DynamoDB Execution Data
- **ExecutionId**: ee8da9cc-c284-45a6-a7f9-cf0df80d12f2
- **Status**: TIMEOUT
- **ALL 3 waves have SAME launch time**: 1764362654-55 (within 1 second)
- **ALL servers failed with ConflictException**

### DRS Job History
Most recent jobs (all COMPLETED):
- `drsjob-3dc9e00fd56beaac9` - Web-Wave servers (00:45:53)
- `drsjob-3a1fa13b116fe8284` - Application-Wave servers (00:45:53)  
- `drsjob-3d42fc5c5db4d5cc1` - Database-Wave servers (00:45:52)

**Pattern**: 3 separate jobs created within 1 second - confirms simultaneous launch.

## Root Cause

**BUG #4 (Wave Dependencies) was NEVER properly fixed!**

### Current Code Flow (lambda/index.py)

```python
def execute_recovery_plan_worker(payload: Dict) -> None:
    # Initiate waves immediately (NO DELAYS)
    wave_results = []
    waves_list = plan.get('Waves', [])
    
    for wave_index, wave in enumerate(waves_list):
        # Dependency check logic
        dependencies = wave.get('Dependencies', [])
        if dependencies:
            dependencies_met = True
            for dep_wave_num in dependencies:
                dep_index = dep_wave_num - 1
                if dep_index < len(wave_results):
                    dep_status = wave_results[dep_index].get('Status', '')
                    if dep_status != 'COMPLETED':  # ← BUG HERE!
                        dependencies_met = False
                        break
            
            if not dependencies_met:
                wave_results.append({
                    'Status': 'PENDING',
                    'StatusMessage': f'Waiting for dependencies: {dependencies}'
                })
                continue
        
        # Initiate wave (happens for ALL waves in tight loop)
        wave_result = initiate_wave(wave, pg_id, execution_id, is_drill, execution_type)
        wave_results.append(wave_result)
```

### The Bug Explained

1. **Wave 1 launches** → Status = 'INITIATED' (NOT 'COMPLETED')
2. **Wave 2 dependency check**:
   - Checks if Wave 1 status == 'COMPLETED'
   - Wave 1 status is 'INITIATED'
   - Logic says "dependencies not met"
   - **Adds Wave 2 as 'PENDING'**... but then **CONTINUES LOOP**
3. **Wave 3 dependency check**: Same as Wave 2
4. **CRITICAL**: All waves still launch because:
   - The `continue` statement only skips current iteration
   - Next iteration still processes next wave
   - **NO WAITING between waves**
   - All `initiate_wave()` calls happen in < 1 second

### Why ConflictException?

When all 3 waves try to launch SIMULTANEOUSLY:
1. Wave 1 calls DRS API for servers 1-2 → Gets jobID
2. Wave 2 calls DRS API for servers 3-4 → Gets jobID  
3. Wave 3 calls DRS API for servers 5-6 → **DRS says "servers busy"**

OR (more likely given same timestamps):
1. All waves call DRS API within milliseconds
2. DRS processes requests in parallel
3. Race condition - multiple requests for same/related servers
4. DRS rejects with ConflictException

### Additional Evidence

Looking at `initiate_wave()` function:
- Calls `start_drs_recovery_for_wave()` immediately
- No waiting, no delays
- Returns status 'INITIATED' or 'PARTIAL'
- **Never returns 'COMPLETED'** - that only comes from poller

## The Design Flaw

**Async execution model + synchronous dependency checking = broken**

The system was designed as:
1. Worker initiates all waves ASAP (async/fire-and-forget)
2. Poller updates status to COMPLETED later
3. Dependency checks run DURING initiation (too early!)

**This can't work!** Dependency checks during initiation will NEVER see 'COMPLETED' status because:
- Waves just started (status = INITIATED)
- Poller hasn't run yet
- Takes 5-15 minutes for jobs to complete

## Solution Options

### Option 1: Sequential Wave Execution (Proper Fix)
Change `execute_recovery_plan_worker()` to:
1. Launch Wave 1
2. **WAIT** for Wave 1 to complete (poll DRS job status)
3. Launch Wave 2
4. **WAIT** for Wave 2 to complete
5. Launch Wave 3

**Pros**: True sequential execution, proper dependencies
**Cons**: Lambda execution time limits (15 minutes max)

### Option 2: Step Functions (Best Long-term)
Move orchestration to Step Functions:
- State machine with sequential steps
- Each wave is a separate state
- Built-in waiting/polling
- No Lambda timeout issues

**Pros**: Proper async orchestration, scalable
**Cons**: Requires infrastructure changes

### Option 3: Remove Wave Dependencies (Quick Fix)
Document that wave dependencies don't work yet:
- All waves launch simultaneously
- User manually spaces out executions if needed
- Fix properly in Phase 3

**Pros**: Quick, honest documentation
**Cons**: Feature doesn't work as advertised

### Option 4: Add Artificial Delays (Hacky Fix)
Add delays between wave launches:
```python
time.sleep(300)  # 5 minutes between waves
```

**Pros**: Simple code change
**Cons**: 
- Wastes Lambda execution time
- Still hits 15-minute limit
- Doesn't properly check completion

## Recommended Fix

**CORRECT DIAGNOSIS AFTER HISTORIAN ANALYSIS:**

Session 53 (Nov 28, 2025) correctly identified the need to remove delays and use external polling. The bug is that **ExecutionPoller was never updated to handle wave dependencies**.

**IMMEDIATE (This Session)**: Option 1A - Add dependency checking to ExecutionPoller
**NEXT SESSION**: Option 2 - Step Functions for enterprise-grade orchestration

### Option 1A: Poller-Based Dependency Checking (CORRECT FIX)

Update `lambda/poller/execution_poller.py` to check dependencies before initiating waves:

```python
def should_initiate_wave(execution: Dict, wave_index: int) -> bool:
    """Check if wave can be initiated based on dependencies"""
    waves = execution.get('Waves', [])
    current_wave = waves[wave_index]
    
    # Check if wave already initiated or completed
    wave_status = current_wave.get('Status', '')
    if wave_status in ['INITIATED', 'POLLING', 'LAUNCHING', 'COMPLETED', 'FAILED', 'TIMEOUT']:
        return False  # Already processed
    
    # Check dependencies
    dependencies = current_wave.get('Dependencies', [])
    if not dependencies:
        return True  # No dependencies, can initiate
    
    # Verify all dependent waves are COMPLETED
    for dep in dependencies:
        dep_wave_id = dep.get('DependsOnWaveId', '')
        # Parse wave number from "plan-wave-2" format
        if '-' in dep_wave_id:
            dep_wave_num = int(dep_wave_id.split('-')[-1])
            dep_index = dep_wave_num - 1
            
            if dep_index >= len(waves):
                logger.warning(f"Dependency wave {dep_wave_num} not found")
                return False
            
            dep_status = waves[dep_index].get('Status', '')
            if dep_status != 'COMPLETED':
                logger.info(f"Wave {wave_index + 1} waiting for Wave {dep_wave_num} (status: {dep_status})")
                return False
    
    return True  # All dependencies met

def poll_execution(execution_id: str, plan_id: str):
    """Poll execution and initiate pending waves"""
    # ... existing code ...
    
    # Check for pending waves that can be initiated
    waves = execution.get('Waves', [])
    for wave_index, wave in enumerate(waves):
        if should_initiate_wave(execution, wave_index):
            logger.info(f"Initiating Wave {wave_index + 1} (dependencies met)")
            # Call Lambda to initiate this wave
            lambda_client.invoke(
                FunctionName=os.environ['API_FUNCTION_NAME'],
                InvocationType='Event',
                Payload=json.dumps({
                    'action': 'initiate_wave',
                    'executionId': execution_id,
                    'planId': plan_id,
                    'waveIndex': wave_index
                })
            )
```

## Files Affected

- `lambda/index.py` - `execute_recovery_plan_worker()` function
- `lambda/index.py` - Wave dependency logic (lines 845-875)
- `docs/BUG_4_WAVE_DEPENDENCY_ANALYSIS.md` - Update with actual cause
- `docs/BUG_6_WAVE_DEPENDENCY_INITIATION.md` - Merge into this doc

## Testing Evidence

All recent executions show same pattern:
- Multiple waves launch simultaneously
- ConflictException on all servers
- Status TIMEOUT after 30 minutes
- No successful multi-wave execution

## Conclusion

**Wave dependencies are completely broken** due to fundamental architectural mismatch between async execution model and synchronous dependency checking.

The "fix" in Bug #4 documentation was theoretical - code was never actually updated to handle dependencies properly.

**Next Action**: Choose solution option and implement.
