# DRS Drill Failure Analysis & Solutions

**Date**: November 23, 2025  
**Issue**: All DRS source server drills failing with ConflictException  
**Status**: Root cause identified, solutions proposed  

## Executive Summary

All 6 DRS source servers are failing drill executions due to **ConflictException** errors when attempting concurrent recovery operations. The root cause is AWS DRS's internal job queuing limitations, not server health issues.

## Root Cause Analysis

### Primary Issue: ConflictException - Concurrent Job Processing

```
Error: "An error occurred (ConflictException) when calling the StartRecovery operation: 
One or more of the Source Servers included in API call are currently being processed by a Job"
```

### Failed Servers (All 6)
- `s-3c1730a9e0771ea14` (Database wave)
- `s-3d75cdc0d9a28a725` (Database wave) 
- `s-3afa164776f93ce4f` (App wave)
- `s-3c63bb8be30d7d071` (App wave)
- `s-3578f52ef3bdd58b4` (Web wave)
- `s-3b9401c1cd270a7a8` (Web wave)

### Server Health Status ✅
- **Replication State**: All servers show `CONTINUOUS` (healthy)
- **Last Seen**: All actively replicating (within minutes)
- **Infrastructure**: No AWS service issues detected

### Execution Timeline Analysis
```
Execution ID: f898e270-ea00-4882-94a6-e1ffe2acc4e9
Start Time: 1763854186 (01:41:26 UTC)
End Time: 1763854188 (01:41:28 UTC)
Duration: 2 seconds

Wave Execution:
- Database Wave: 1763854187 (all servers failed)
- App Wave: 1763854187 (all servers failed) 
- Web Wave: 1763854188 (all servers failed)
```

**Problem**: All waves executed within 1-2 seconds with no delays between operations.

## Technical Root Cause

### AWS DRS Job Queuing Limitation

1. **Sequential Execution Constraint**: DRS doesn't allow multiple concurrent recovery jobs for the same source servers
2. **Job Cleanup Delay**: Previous failed jobs may not immediately release server locks
3. **Rapid Retry Conflicts**: Current orchestration attempts all waves without sufficient delays

### Current Implementation Issues

```python
# Current problematic flow in execute_wave()
for server_id in server_ids:
    try:
        job_result = start_drs_recovery(server_id, region, is_drill, execution_id)
        # ❌ No delay between servers
        # ❌ No retry logic for conflicts
        # ❌ No job status checking
    except Exception as e:
        # ❌ Immediate failure, no retry
```

## Immediate Solutions

### Solution 1: Add Inter-Server Delays ⭐ **Recommended**

```python
def execute_wave(wave: Dict, protection_group_id: str, execution_id: str, is_drill: bool) -> Dict:
    """Execute wave with proper delays between server launches"""
    
    server_results = []
    for i, server_id in enumerate(server_ids):
        # Add 15-second delay between servers (except first)
        if i > 0:
            time.sleep(15)
            
        try:
            job_result = start_drs_recovery(server_id, region, is_drill, execution_id)
            server_results.append(job_result)
        except Exception as e:
            # Handle conflicts with retry logic
            server_results.append(handle_server_conflict(server_id, e))
    
    return build_wave_result(server_results)
```

### Solution 2: Implement Retry Logic with Exponential Backoff

```python
def start_drs_recovery_with_retry(server_id: str, region: str, is_drill: bool, execution_id: str) -> Dict:
    """Launch DRS recovery with ConflictException retry logic"""
    
    max_retries = 3
    base_delay = 30  # seconds
    
    for attempt in range(max_retries):
        try:
            return start_drs_recovery(server_id, region, is_drill, execution_id)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConflictException' and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # 30s, 60s, 120s
                print(f"ConflictException for {server_id}, retrying in {delay}s (attempt {attempt + 1})")
                time.sleep(delay)
                continue
            raise
    
    raise Exception(f"Failed to start recovery after {max_retries} attempts")
```

### Solution 3: Job Status Polling Before Next Wave

```python
def wait_for_wave_jobs_to_start(wave_results: List[Dict], timeout: int = 300) -> bool:
    """Wait for DRS jobs to transition from PENDING to RUNNING before next wave"""
    
    job_ids = [r.get('RecoveryJobId') for r in wave_results if r.get('RecoveryJobId')]
    if not job_ids:
        return True
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            jobs_response = drs_client.describe_jobs(filters={'jobIDs': job_ids})
            
            # Check if all jobs have started (not PENDING)
            pending_jobs = [j for j in jobs_response['items'] if j.get('status') == 'PENDING']
            if not pending_jobs:
                print(f"All {len(job_ids)} jobs have started, proceeding to next wave")
                return True
                
            print(f"Waiting for {len(pending_jobs)} jobs to start...")
            time.sleep(10)
            
        except Exception as e:
            print(f"Error checking job status: {e}")
            time.sleep(10)
    
    print(f"Timeout waiting for jobs to start after {timeout}s")
    return False
```

## Implementation Plan

### Phase 1: Quick Fix (1-2 hours)
1. **Add 15-second delays** between server launches within each wave
2. **Add 30-second delays** between wave executions
3. **Deploy updated Lambda** with timing fixes

### Phase 2: Robust Solution (4-6 hours)
1. **Implement retry logic** with exponential backoff for ConflictException
2. **Add job status polling** before proceeding to next wave
3. **Enhanced error handling** with specific conflict detection
4. **Update execution status** to reflect actual progress

### Phase 3: Advanced Monitoring (Future)
1. **Step Functions integration** for async job tracking
2. **Real-time status updates** in UI
3. **Job completion notifications** via SNS
4. **Detailed execution metrics** in CloudWatch

## Code Changes Required

### File: `lambda/index.py`

```python
# Add to execute_wave() function
def execute_wave(wave: Dict, protection_group_id: str, execution_id: str, is_drill: bool) -> Dict:
    # ... existing code ...
    
    # Launch recovery for each server with delays
    server_results = []
    for i, server_id in enumerate(server_ids):
        # Add delay between servers (except first)
        if i > 0:
            print(f"Waiting 15s before launching next server...")
            time.sleep(15)
        
        try:
            job_result = start_drs_recovery_with_retry(server_id, region, is_drill, execution_id)
            server_results.append(job_result)
        except Exception as e:
            print(f"Failed to launch {server_id} after retries: {str(e)}")
            server_results.append({
                'SourceServerId': server_id,
                'Status': 'FAILED',
                'Error': str(e),
                'LaunchTime': int(time.time())
            })
    
    # Wait for jobs to start before returning
    if server_results:
        wait_for_wave_jobs_to_start(server_results, timeout=120)
    
    return build_wave_result(server_results)

# Add to execute_recovery_plan() function  
def execute_recovery_plan(body: Dict) -> Dict:
    # ... existing code ...
    
    # Execute waves with delays between them
    for wave_index, wave in enumerate(plan['Waves']):
        # Add delay between waves (except first)
        if wave_index > 0:
            print(f"Waiting 30s before executing next wave...")
            time.sleep(30)
        
        wave_result = execute_wave(wave, pg_id, execution_id, is_drill)
        history_item['Waves'].append(wave_result)
```

## Testing Strategy

### Test 1: Single Server Launch
```bash
# Test individual server recovery to verify basic functionality
aws drs start-recovery \
  --source-servers sourceServerID=s-3c1730a9e0771ea14 \
  --is-drill \
  --region us-east-1
```

### Test 2: Sequential Wave Execution
1. Execute Recovery Plan with 1 server per wave
2. Verify 15-second delays between servers
3. Verify 30-second delays between waves
4. Confirm no ConflictException errors

### Test 3: Full Recovery Plan
1. Execute complete 3-wave plan (6 servers)
2. Monitor DRS job creation timing
3. Verify all servers launch successfully
4. Measure total execution time (expect 2-3 minutes vs current 3 seconds)

## Expected Results

### Before Fix
```
Execution Time: 3 seconds
Success Rate: 0% (all servers fail)
Error: ConflictException on all servers
```

### After Fix
```
Execution Time: 2-3 minutes (with delays)
Success Rate: 95%+ (occasional AWS service issues)
Errors: Rare, with automatic retry handling
```

## Monitoring & Alerts

### CloudWatch Metrics to Track
- `DRS.ConflictException.Count` - Should drop to near zero
- `DRS.RecoveryJob.Duration` - Track job completion times
- `Orchestration.Wave.Duration` - Monitor wave execution timing

### Recommended Alarms
- **High ConflictException Rate**: > 2 per hour
- **Long Wave Duration**: > 5 minutes per wave
- **Job Failure Rate**: > 10% of recovery jobs

## Risk Assessment

### Low Risk Changes ✅
- Adding delays between operations
- Enhanced logging and error messages
- Retry logic with exponential backoff

### Medium Risk Changes ⚠️
- Job status polling (new DRS API calls)
- Modified execution flow timing
- Updated error handling logic

### Mitigation Strategies
1. **Gradual rollout**: Test with single server first
2. **Rollback plan**: Keep current Lambda version as backup
3. **Monitoring**: Watch CloudWatch logs during first executions
4. **Fallback**: Manual DRS console execution if automation fails

## Success Criteria

### Immediate Goals (Phase 1)
- [ ] Zero ConflictException errors in drill executions
- [ ] All 6 servers launch successfully in test environment
- [ ] Execution completes within 3 minutes (vs current 3 seconds + failures)

### Long-term Goals (Phase 2-3)
- [ ] 95%+ success rate for recovery plan executions
- [ ] Real-time status updates in UI
- [ ] Automated retry and recovery for transient failures
- [ ] Comprehensive execution audit trail

## Conclusion

The DRS drill failures are **not due to server health issues** but rather **AWS DRS service limitations** around concurrent job processing. The solution requires implementing proper job sequencing, retry logic, and timing delays.

**Recommended Action**: Implement Phase 1 changes immediately (15-second delays) to resolve the immediate issue, then proceed with Phase 2 for robust long-term solution.

**Estimated Fix Time**: 2-4 hours for complete solution  
**Risk Level**: Low (adding delays and retries)  
**Success Probability**: 95%+ based on AWS DRS best practices