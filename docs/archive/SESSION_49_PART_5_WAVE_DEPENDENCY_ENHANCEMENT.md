# Session 49 Part 5: Wave Dependency Enhancement (TODO)

**Status**: Documented for Next Session  
**Priority**: HIGH  
**Impact**: Prevents wave overlapping and potential conflicts  
**Created**: November 22, 2025 - 9:16 PM EST

---

## Problem Statement

**Current Implementation Issue**:
The ConflictException fix (Part 4) added delays between waves, but does NOT wait for wave completion before starting dependent waves.

**What Currently Happens**:
```python
Wave 1: Starts 2 server launches (takes 5-10 min to complete)
↓ 30s delay
Wave 2: Starts 2 server launches (Wave 1 still launching!)
↓ 30s delay  
Wave 3: Starts 2 server launches (Wave 1 & 2 still launching!)
```

**Result**: All waves overlap during execution, only startup is delayed

## What Should Happen

### Scenario 1: Waves With DependsOn
```python
Wave 1: Starts 2 servers
↓ WAIT for Wave 1 to COMPLETE (all servers LAUNCHED status)
Wave 2 (depends on Wave 1): Starts 2 servers  
↓ WAIT for Wave 2 to COMPLETE
Wave 3 (depends on Wave 2): Starts 2 servers
```

### Scenario 2: Waves Without DependsOn
```python
Wave 1: Starts 2 servers
Wave 2: Starts immediately after Wave 1 starts (parallel)
Wave 3: Starts immediately after Wave 2 starts (parallel)
```

## Implementation Requirements

### 1. Parse Wave Dependencies
```python
def get_wave_dependencies(wave: Dict) -> List[int]:
    """Extract wave numbers that this wave depends on"""
    depends_on = []
    for dep in wave.get('Dependencies', []):
        wave_id = dep.get('DependsOnWaveId', '')
        # Parse wave number from WaveId format: "plan-wave-2"
        if wave_id and '-' in wave_id:
            wave_num = int(wave_id.split('-')[-1])
            depends_on.append(wave_num)
    return depends_on
```

### 2. Poll DRS Job Completion
```python
def wait_for_wave_completion(wave_jobs: List[str], region: str, timeout: int = 3600) -> bool:
    """
    Poll DRS jobs until all reach terminal state
    
    Args:
        wave_jobs: List of DRS job IDs to monitor
        region: AWS region
        timeout: Max seconds to wait (default 1 hour)
    
    Returns:
        True if all jobs completed successfully, False if any failed
    """
    drs_client = boto3.client('drs', region_name=region)
    start_time = time.time()
    
    pending_jobs = set(wave_jobs)
    
    while pending_jobs and (time.time() - start_time) < timeout:
        # Check job statuses
        response = drs_client.describe_jobs(
            filters={'jobIDs': list(pending_jobs)}
        )
        
        for job in response.get('items', []):
            job_id = job['jobID']
            status = job.get('status', 'UNKNOWN')
            
            # Terminal states
            if status in ['COMPLETED', 'FAILED']:
                pending_jobs.remove(job_id)
                if status == 'FAILED':
                    print(f"Job {job_id} failed: {job.get('error', 'Unknown error')}")
                    return False
        
        if pending_jobs:
            time.sleep(30)  # Poll every 30 seconds
    
    if pending_jobs:
        print(f"Timeout waiting for jobs: {pending_jobs}")
        return False
    
    return True
```

### 3. Update Wave Execution Logic
```python
def execute_recovery_plan(body: Dict) -> Dict:
    """Execute Recovery Plan with proper wave dependency handling"""
    
    wave_results = {}  # Track completion status per wave
    
    for wave_index, wave in enumerate(plan['Waves']):
        wave_number = wave_index + 1
        
        # Check dependencies
        depends_on = get_wave_dependencies(wave)
        
        if depends_on:
            # Wait for dependent waves to complete
            for dep_wave_num in depends_on:
                if dep_wave_num not in wave_results:
                    raise Exception(f"Wave {wave_number} depends on Wave {dep_wave_num} which hasn't executed yet")
                
                if not wave_results[dep_wave_num]['completed']:
                    # Wait for dependent wave completion
                    dep_jobs = wave_results[dep_wave_num]['jobs']
                    success = wait_for_wave_completion(dep_jobs, region)
                    wave_results[dep_wave_num]['completed'] = True
                    
                    if not success:
                        # Dependent wave failed, skip this wave
                        print(f"Skipping Wave {wave_number} - dependent Wave {dep_wave_num} failed")
                        continue
        
        # Execute wave
        wave_result = execute_wave(wave, pg_id, execution_id, is_drill)
        
        # Track jobs for this wave
        wave_jobs = [s['RecoveryJobId'] for s in wave_result['Servers'] if s.get('RecoveryJobId')]
        wave_results[wave_number] = {
            'jobs': wave_jobs,
            'completed': False,  # Will be set to True when dependent waves wait
            'result': wave_result
        }
```

### 4. Update Execution History Schema
Add completion tracking to wave results:
```python
{
    'WaveName': 'Database',
    'Status': 'COMPLETED',  # IN_PROGRESS → COMPLETED when all jobs finish
    'StartTime': 1732323600,
    'EndTime': 1732323900,  # Actual completion time
    'CompletionDuration': 300,  # Seconds from start to complete
    'Servers': [...]
}
```

## Testing Plan

### Test Case 1: Sequential Dependencies
```
Wave 1: Database (2 servers) - no dependencies
Wave 2: App (2 servers) - depends on Wave 1  
Wave 3: Web (2 servers) - depends on Wave 2

Expected:
- Wave 1 starts immediately
- Wave 2 waits ~5-10 minutes for Wave 1 completion
- Wave 3 waits ~5-10 minutes for Wave 2 completion
- Total: ~15-30 minutes
```

### Test Case 2: Parallel Waves
```
Wave 1: Database (2 servers) - no dependencies
Wave 2: Cache (2 servers) - no dependencies
Wave 3: Monitoring (2 servers) - no dependencies

Expected:
- All 3 waves start immediately (within 30s)
- All 6 servers launching concurrently
- Total: ~5-10 minutes
```

### Test Case 3: Complex Dependencies
```
Wave 1: Database (2 servers) - no dependencies
Wave 2: App1 (2 servers) - depends on Wave 1
Wave 3: App2 (2 servers) - depends on Wave 1
Wave 4: Web (2 servers) - depends on Wave 2 AND Wave 3

Expected:
- Wave 1 starts immediately
- Wave 2 & 3 start after Wave 1 completes (parallel)
- Wave 4 waits for BOTH Wave 2 & 3 to complete
```

## Current Workaround

**For now**, users should:
1. Use sequential wave configuration (no overlapping)
2. Expect waves to start sequentially with 30s delays
3. Monitor CloudWatch logs to verify no ConflictException errors
4. Wait for full execution to complete before starting another execution

## Files to Modify (Next Session)

1. **lambda/index.py** (~line 290-350):
   - Add `get_wave_dependencies()` function
   - Add `wait_for_wave_completion()` function
   - Update `execute_recovery_plan()` with dependency logic
   - Update `execute_wave()` to return job IDs

2. **DynamoDB ExecutionHistory Schema**:
   - Add `CompletionDuration` field to waves
   - Update `Status` field to track COMPLETED vs IN_PROGRESS

3. **Frontend ExecutionDetailsPage.tsx**:
   - Show wave completion time
   - Display "Waiting for Wave X completion..." messages
   - Update status polling to check wave completion

## Estimated Implementation Time

- Lambda changes: 1-2 hours
- Testing: 30-60 minutes
- Documentation: 30 minutes
- **Total**: 2-3 hours

## Success Criteria

- ✅ Waves with DependsOn wait for completion before starting
- ✅ Waves without DependsOn start immediately (parallel)
- ✅ No ConflictException errors during execution
- ✅ Execution history shows accurate completion times
- ✅ Frontend displays wave completion status correctly

---

**Next Steps**:
1. Implement dependency logic in lambda/index.py
2. Add DRS job polling with timeout
3. Update execution history schema
4. Test with real DRS launches
5. Update frontend to show completion status
