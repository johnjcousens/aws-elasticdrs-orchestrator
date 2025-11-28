# Session 53: Lambda Refactoring Analysis
## DRS Execution Fix - Phase 1 Implementation

**Created:** November 28, 2025  
**Session:** 53  
**Phase:** 1 - Lambda Refactoring

---

## Current Synchronous Pattern Analysis

### Problem: Lambda Timeout (15 min) vs DRS Execution (20-30 min)

**Current Flow (BROKEN):**
```
1. User triggers execution via API
2. execute_recovery_plan() creates execution record
3. Invokes execute_recovery_plan_worker() asynchronously
4. Worker executes waves sequentially with sleep delays:
   - 30 seconds between waves
   - 15 seconds between servers
   - Waits for ALL DRS jobs to complete
5. Updates final status after 20-30 minutes
6. Lambda times out at 15 minutes ❌
```

### Identified Synchronous Waiting Patterns

#### 1. execute_recovery_plan_worker() (Lines 730-820)
**Current Code:**
```python
def execute_recovery_plan_worker(payload: Dict) -> None:
    # ... initialization ...
    
    # Execute waves sequentially with delays
    wave_results = []
    for wave_index, wave in enumerate(plan['Waves']):
        # Add 30-second delay between waves (except first wave)
        if wave_index > 0:
            print(f"Waiting 30s before executing wave {wave_number}/{len(plan['Waves'])}")
            time.sleep(30)  # ❌ SYNCHRONOUS WAIT
        
        wave_result = execute_wave(wave, pg_id, execution_id, is_drill)
        # ... update progress ...
    
    # ... determine final status after ALL waves complete ...
```

**Problems:**
- Sleeps for 30 seconds between waves
- Waits for execute_wave() to complete before continuing
- Total time: (number_of_waves - 1) × 30s + wave execution time
- Exceeds Lambda timeout

#### 2. execute_wave() (Lines 823-925)
**Current Code:**
```python
def execute_wave(wave: Dict, protection_group_id: str, execution_id: str, is_drill: bool) -> Dict:
    # ... get servers ...
    
    server_results = []
    for i, server_id in enumerate(server_ids):
        # Add 15-second delay between servers (except first server)
        if i > 0:
            print(f"Waiting 15s before launching server {i+1}/{len(server_ids)}")
            time.sleep(15)  # ❌ SYNCHRONOUS WAIT
        
        job_result = start_drs_recovery_with_retry(server_id, region, is_drill, execution_id)
        server_results.append(job_result)
    
    # ... determine wave status ...
```

**Problems:**
- Sleeps for 15 seconds between server launches
- Waits for each server's DRS job to initiate before continuing
- Total time per wave: (number_of_servers - 1) × 15s + DRS API calls
- Accumulates across all waves

#### 3. start_drs_recovery_with_retry() (Lines 977-1000)
**Current Code:**
```python
def start_drs_recovery_with_retry(server_id: str, region: str, is_drill: bool, execution_id: str) -> Dict:
    max_retries = 3
    base_delay = 30  # Base delay in seconds
    
    for attempt in range(max_retries):
        try:
            return start_drs_recovery(server_id, region, is_drill, execution_id)
        except ClientError as e:
            if error_code == 'ConflictException' and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # 30s, 60s, 120s
                time.sleep(delay)  # ❌ SYNCHRONOUS WAIT (up to 120s)
                continue
```

**Problems:**
- Exponential backoff with sleep: 30s, 60s, 120s
- Can wait up to 210 seconds (3.5 minutes) per server
- Multiplied across all servers = significant delay

### Current CloudFormation Configuration

**ApiHandlerFunction:**
```yaml
Timeout: 900  # 15 minutes
MemorySize: 512
Runtime: python3.12
```

**Gap Analysis:**
- Lambda limit: 15 minutes (900 seconds)
- DRS drill execution: ~20 minutes (13m PENDING + 6m IN_PROGRESS)
- DRS recovery execution: ~30 minutes (13m PENDING + 6m IN_PROGRESS + 10m POST-LAUNCH)
- **Gap for drills:** 5 minutes over limit
- **Gap for recovery:** 15 minutes over limit

---

## Phase 1: Async Refactoring Solution

### New Pattern: Initiate and Return

**New Flow (FIXED):**
```
1. User triggers execution via API
2. execute_recovery_plan() creates execution record with Status='PENDING'
3. Invokes execute_recovery_plan_worker() asynchronously
4. Worker initiates ALL DRS jobs immediately (< 2 minutes):
   - Loops through waves
   - Loops through servers in each wave
   - Calls DRS StartRecovery API (no waiting)
   - Stores job IDs in DynamoDB
5. Updates status to 'POLLING' and returns
6. EventBridge poller tracks job completion (Phase 2)
```

### Detailed Changes Required

#### Change 1: Update execute_recovery_plan() (Lines 665-728)
**Status:** ✅ ALREADY CORRECT (no changes needed)

Current implementation already:
- Returns 202 Accepted immediately
- Creates PENDING execution record
- Invokes worker asynchronously
- Doesn't wait for worker completion

#### Change 2: Refactor execute_recovery_plan_worker() (Lines 730-820)
**Current Status:** NEEDS MAJOR REFACTORING

**Changes:**
1. Remove all `time.sleep()` calls
2. Change from "execute and wait" to "initiate and track"
3. Update to POLLING status instead of IN_PROGRESS
4. Store job IDs for external poller

**New Implementation:**
```python
def execute_recovery_plan_worker(payload: Dict) -> None:
    """Background worker - initiates DRS jobs without waiting"""
    try:
        execution_id = payload['executionId']
        plan_id = payload['planId']
        execution_type = payload['executionType']
        is_drill = payload['isDrill']
        plan = payload['plan']
        
        print(f"Worker initiating execution {execution_id}")
        
        # Update status to POLLING (not IN_PROGRESS)
        execution_history_table.update_item(
            Key={'ExecutionId': execution_id, 'PlanId': plan_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={':status': 'POLLING'}
        )
        
        # Initiate waves immediately (no delays)
        wave_results = []
        for wave_index, wave in enumerate(plan['Waves']):
            wave_number = wave_index + 1
            wave_name = wave.get('WaveName', f'Wave {wave_number}')
            pg_id = wave.get('ProtectionGroupId')
            
            if not pg_id:
                print(f"Wave {wave_number} has no Protection Group, skipping")
                continue
            
            # NO DELAY between waves - initiate immediately
            print(f"Initiating Wave {wave_number}: {wave_name}")
            
            # Initiate wave and get job IDs (no waiting)
            wave_result = initiate_wave(wave, pg_id, execution_id, is_drill)
            wave_results.append(wave_result)
            
            # Update progress in DynamoDB after each wave initiation
            execution_history_table.update_item(
                Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                UpdateExpression='SET Waves = :waves',
                ExpressionAttributeValues={':waves': wave_results}
            )
        
        # Final status is POLLING (not COMPLETED)
        # External poller will update to COMPLETED when jobs finish
        print(f"Worker completed initiation for execution {execution_id}")
        print(f"Status remains POLLING - awaiting external poller")
        
    except Exception as e:
        print(f"Worker error for execution {execution_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Mark execution as failed
        try:
            execution_history_table.update_item(
                Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                UpdateExpression='SET #status = :status, EndTime = :endtime, ErrorMessage = :error',
                ExpressionAttributeNames={'#status': 'Status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':endtime': int(time.time()),
                    ':error': str(e)
                }
            )
        except Exception as update_error:
            print(f"Failed to update error status: {str(update_error)}")
```

#### Change 3: Create New initiate_wave() Function
**Status:** NEW FUNCTION REQUIRED

**Purpose:** Replace execute_wave() - only starts jobs, doesn't wait

**New Implementation:**
```python
def initiate_wave(wave: Dict, protection_group_id: str, execution_id: str, is_drill: bool) -> Dict:
    """Initiate DRS recovery jobs for a wave without waiting for completion"""
    try:
        # Get Protection Group
        pg_result = protection_groups_table.get_item(Key={'GroupId': protection_group_id})
        if 'Item' not in pg_result:
            return {
                'WaveName': wave.get('WaveName', 'Unknown'),
                'ProtectionGroupId': protection_group_id,
                'Status': 'FAILED',
                'Error': 'Protection Group not found',
                'Servers': [],
                'StartTime': int(time.time())
            }
        
        pg = pg_result['Item']
        region = pg['Region']
        
        # Get servers from both wave and protection group
        pg_servers = pg.get('SourceServerIds', [])
        wave_servers = wave.get('ServerIds', [])
        
        # Filter to only launch servers specified in this wave
        if wave_servers:
            server_ids = [s for s in wave_servers if s in pg_servers]
            print(f"Wave specifies {len(wave_servers)} servers, {len(server_ids)} are in Protection Group")
        else:
            server_ids = pg_servers
            print(f"Wave has no ServerIds field, launching all {len(server_ids)} Protection Group servers")
        
        if not server_ids:
            return {
                'WaveName': wave.get('WaveName', 'Unknown'),
                'ProtectionGroupId': protection_group_id,
                'Status': 'INITIATED',
                'Servers': [],
                'StartTime': int(time.time())
            }
        
        print(f"Initiating recovery for {len(server_ids)} servers in region {region}")
        
        # Initiate recovery for each server (NO DELAYS)
        server_results = []
        for i, server_id in enumerate(server_ids):
            # NO DELAY between servers - initiate immediately
            try:
                job_result = start_drs_recovery(server_id, region, is_drill, execution_id)
                server_results.append(job_result)
            except Exception as e:
                print(f"Error initiating recovery for server {server_id}: {str(e)}")
                server_results.append({
                    'SourceServerId': server_id,
                    'Status': 'FAILED',
                    'Error': str(e),
                    'LaunchTime': int(time.time())
                })
        
        # Wave status is INITIATED (not IN_PROGRESS)
        # External poller will update to IN_PROGRESS/COMPLETED
        has_failures = any(s['Status'] == 'FAILED' for s in server_results)
        wave_status = 'PARTIAL' if has_failures else 'INITIATED'
        
        return {
            'WaveName': wave.get('WaveName', 'Unknown'),
            'ProtectionGroupId': protection_group_id,
            'Region': region,
            'Status': wave_status,
            'Servers': server_results,
            'StartTime': int(time.time())
        }
        
    except Exception as e:
        print(f"Error initiating wave: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'WaveName': wave.get('WaveName', 'Unknown'),
            'ProtectionGroupId': protection_group_id,
            'Status': 'FAILED',
            'Error': str(e),
            'Servers': [],
            'StartTime': int(time.time())
        }
```

#### Change 4: Update start_drs_recovery() (Lines 928-974)
**Status:** MINOR CHANGES NEEDED

**Changes:**
1. Add ExecutionType tagging
2. Remove any waiting logic

**Updated Implementation:**
```python
def start_drs_recovery(server_id: str, region: str, is_drill: bool, execution_id: str, execution_type: str = 'DRILL') -> Dict:
    """Launch DRS recovery for a single source server"""
    try:
        drs_client = boto3.client('drs', region_name=region)
        
        print(f"Starting {execution_type} {'drill' if is_drill else 'recovery'} for server {server_id}")
        
        # Start recovery job
        response = drs_client.start_recovery(
            sourceServers=[{
                'sourceServerID': server_id
            }],
            isDrill=is_drill,
            tags={
                'ExecutionId': execution_id,
                'ExecutionType': execution_type,  # NEW: Tag with execution type
                'ManagedBy': 'DRS-Orchestration'
            }
        )
        
        job = response.get('job', {})
        job_id = job.get('jobID', 'unknown')
        
        print(f"Started recovery job {job_id} for server {server_id}")
        
        return {
            'SourceServerId': server_id,
            'RecoveryJobId': job_id,
            'Status': 'LAUNCHING',
            'InstanceId': None,  # Will be populated by poller
            'LaunchTime': int(time.time()),
            'Error': None
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"Failed to start recovery for server {server_id}: {error_msg}")
        return {
            'SourceServerId': server_id,
            'Status': 'FAILED',
            'Error': error_msg,
            'LaunchTime': int(time.time())
        }
```

#### Change 5: Update start_drs_recovery_with_retry()
**Status:** REMOVE OR SIMPLIFY

**Options:**
1. **Option A (Recommended):** Remove entirely - Let poller handle ConflictExceptions
2. **Option B:** Keep but remove time.sleep() - Return immediately on ConflictException

**Option A Implementation (Recommended):**
```python
# REMOVE start_drs_recovery_with_retry() entirely
# Call start_drs_recovery() directly
# Let poller handle ConflictExceptions during status polling
```

**Option B Implementation (If retry needed):**
```python
def start_drs_recovery_with_retry(server_id: str, region: str, is_drill: bool, execution_id: str, execution_type: str = 'DRILL') -> Dict:
    """Attempt to launch DRS recovery with immediate retry on ConflictException"""
    from botocore.exceptions import ClientError
    
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            return start_drs_recovery(server_id, region, is_drill, execution_id, execution_type)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # On ConflictException, try again immediately (no sleep)
            if error_code == 'ConflictException' and attempt < max_attempts - 1:
                print(f"ConflictException for server {server_id} (attempt {attempt + 1}/{max_attempts})")
                print(f"Server is being processed by another job, retrying immediately...")
                continue  # NO SLEEP - try again immediately
            
            # Re-raise if not ConflictException or last attempt
            raise
        except Exception as e:
            # Re-raise non-ClientError exceptions immediately
            raise
    
    # Should never reach here
    return {
        'SourceServerId': server_id,
        'Status': 'FAILED',
        'Error': 'Max retry attempts exceeded',
        'LaunchTime': int(time.time())
    }
```

#### Change 6: Update CloudFormation - Lambda Timeout
**Status:** SIMPLE CONFIG CHANGE

**File:** `cfn/lambda-stack.yaml` Line 263

**Change:**
```yaml
# BEFORE:
Timeout: 900  # 15 minutes

# AFTER:
Timeout: 120  # 2 minutes (only need time to initiate jobs)
```

**Rationale:**
- Lambda only initiates DRS jobs (< 30 seconds typically)
- Add buffer for retries and error handling
- 2 minutes is more than sufficient
- Reduces cost (shorter execution time)

---

## Expected Performance Improvements

### Current Performance (BROKEN)
- **Total Lambda Execution Time:** 20-30 minutes
- **Lambda Timeout:** 15 minutes
- **Result:** Execution fails with timeout ❌

### New Performance (FIXED)
- **Total Lambda Execution Time:** < 2 minutes
- **Lambda Timeout:** 2 minutes
- **Result:** Lambda completes successfully ✅
- **Poller tracks completion:** 20-30 minutes (Phase 2)

### Time Breakdown Comparison

**Current (Synchronous):**
```
Execution Start → Create Record: 1s
  ↓
Wave 1: Initiate servers (15s × 5 servers) = 75s
  ↓
Wait for Wave 1 completion: 20-30 minutes ❌
  ↓
Delay before Wave 2: 30s
  ↓
Wave 2: Initiate servers (15s × 3 servers) = 45s
  ↓
Wait for Wave 2 completion: 20-30 minutes ❌
  ↓
Update final status: 1s
  ↓
Total: 40-60 minutes (EXCEEDS 15-MIN LIMIT) ❌
```

**New (Async):**
```
Execution Start → Create Record: 1s
  ↓
Wave 1: Initiate servers (1s × 5 servers) = 5s
  ↓
Wave 2: Initiate servers (1s × 3 servers) = 3s
  ↓
Update status to POLLING: 1s
  ↓
Lambda completes: 10s total ✅
  ↓
[External poller tracks for 20-30 minutes]
  ↓
Poller updates to COMPLETED
```

---

## Testing Strategy

### Unit Tests
1. **Test initiate_wave()** - Verify job IDs returned without waiting
2. **Test worker completion** - Verify POLLING status set correctly
3. **Test start_drs_recovery()** - Verify ExecutionType tagging

### Integration Tests
1. **Full execution flow** - Trigger execution, verify Lambda completes < 2 min
2. **DynamoDB status** - Verify POLLING status set correctly
3. **DRS job creation** - Verify jobs initiated in DRS console

### Performance Tests
1. **Multiple concurrent executions** - Verify no throttling
2. **Large wave (10+ servers)** - Verify < 2 min completion
3. **Multi-wave plans** - Verify sequential initiation

---

## Deployment Checklist

### Pre-Deployment
- [ ] Backup current Lambda code
- [ ] Test changes in development environment
- [ ] Verify CloudFormation changes validate
- [ ] Document rollback procedure

### Deployment Steps
1. [ ] Update Lambda code (lambda/index.py)
2. [ ] Update CloudFormation template (cfn/lambda-stack.yaml)
3. [ ] Deploy CloudFormation stack update
4. [ ] Verify Lambda timeout changed to 120s
5. [ ] Test single execution
6. [ ] Monitor CloudWatch logs
7. [ ] Verify DRS jobs initiated successfully

### Post-Deployment
- [ ] Run integration tests
- [ ] Monitor execution latency
- [ ] Check DynamoDB for POLLING status
- [ ] Verify no Lambda timeouts
- [ ] Document any issues

---

## Risk Mitigation

### Identified Risks

1. **Risk:** ConflictException without retry delays
   - **Mitigation:** Keep immediate retry logic, let poller handle persistent conflicts

2. **Risk:** DRS API rate limiting
   - **Mitigation:** Monitor CloudWatch for throttling errors, add exponential backoff if needed

3. **Risk:** DynamoDB write throttling with rapid updates
   - **Mitigation:** Use batch writes, increase WCU if needed

4. **Risk:** Execution appears "stuck" in POLLING
   - **Mitigation:** Implement poller in Phase 2, add timeout alerting

### Rollback Plan

**If deployment fails:**
1. Revert CloudFormation stack to previous version
2. Restore Lambda code from backup
3. Verify system operational
4. Investigate failure root cause
5. Re-attempt with fixes

---

## Phase 2 Preview: EventBridge Poller

**Next Steps (not in this session):**
1. Create EventBridge rule (30s intervals)
2. Create `lambda/execution_poller.py`
3. Implement unified polling logic for DRILL/RECOVERY modes
4. Update DynamoDB with completion status
5. Frontend polling continues to work (polls API, not Lambda)

---

## Summary

Phase 1 transforms Lambda from:
- ❌ **Synchronous execution** (20-30 min) → Lambda timeout
- ✅ **Async initiation** (< 2 min) → External polling

**Key Changes:**
1. Remove all `time.sleep()` calls
2. Create `initiate_wave()` function
3. Update status to POLLING instead of COMPLETED
4. Change Lambda timeout: 900s → 120s

**Result:**
- Lambda completes in < 2 minutes ✅
- DRS jobs initiated successfully ✅
- External poller tracks completion (Phase 2) ✅
