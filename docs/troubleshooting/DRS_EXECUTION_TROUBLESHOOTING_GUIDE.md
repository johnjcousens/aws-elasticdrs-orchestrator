# DRS Execution Troubleshooting Guide

**Version**: 2.1  
**Date**: January 1, 2026  
**Status**: Production Ready - EventBridge Security Enhancements Complete

---

## Overview

This guide consolidates all DRS execution troubleshooting, covering drill debugging procedures and failure analysis for recovery operations.

---

## Quick Validation Commands

### 1. Test Current Drill Status
```bash
# Check if API is responding
curl -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/health

# List current executions
curl -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/executions
```

### 2. Check Account Context
```bash
# Get target accounts
curl -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/accounts/targets

# Check current account detection
aws sts get-caller-identity
```

### 3. Validate DRS Setup
```bash
# Check DRS initialization
AWS_PAGER="" aws drs describe-source-servers --region us-east-1

# Check DRS quotas
curl -H "Authorization: Bearer $TOKEN" \
  "https://api-endpoint/drs/quotas?region=us-east-1"
```

### 4. Test Protection Group Resolution
```bash
# List protection groups
curl -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/protection-groups

# Test tag resolution (if using tag-based)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/protection-groups/resolve-tags \
  -d '{"Region": "us-east-1", "SelectionTags": {"Environment": "test"}}'
```

### 5. Test Drill Execution
```bash
# Execute drill
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://api-endpoint/recovery-plans/{planId}/execute \
  -d '{"ExecutionType": "DRILL", "InitiatedBy": "debug-test"}'
```

---

## CloudWatch Logs Investigation

### API Handler Logs
```bash
# Get recent API logs
AWS_PAGER="" aws logs tail /aws/lambda/drs-orchestration-api-handler-test \
  --since 10m --region us-east-1
```

### Step Functions Logs
```bash
# Get orchestration logs
AWS_PAGER="" aws logs tail /aws/lambda/drs-orchestration-orchestration-stepfunctions-test \
  --since 10m --region us-east-1
```

### Step Functions Execution
```bash
# List recent executions
AWS_PAGER="" aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:account:stateMachine:drs-orchestration-test \
  --status-filter FAILED --max-results 5 --region us-east-1
```

---

## Common Issues and Fixes

### Issue 1: Account Context Blocking
**Symptom**: Drill buttons grayed out, "Account required" messages
**Check**:
```javascript
// In browser console on Recovery Plans page
console.log(localStorage.getItem('selectedAccountId'));
console.log(window.accountContext);
```
**Fix**: Ensure account is selected in top navigation dropdown

### Issue 2: Server Conflicts
**Symptom**: "SERVER_CONFLICT" error when starting drill
**Check**: Look for other active executions using same servers
**Fix**: Wait for other executions to complete or use different servers

### Issue 3: DRS Service Limits
**Symptom**: "CONCURRENT_JOBS_LIMIT_EXCEEDED" or similar quota errors
**Check**: 
```bash
# Check active DRS jobs
AWS_PAGER="" aws drs describe-jobs --region us-east-1
```
**Fix**: Wait for jobs to complete or increase quotas

### Issue 4: Tag Resolution Failure
**Symptom**: Tag-based Protection Groups show no servers
**Check**: Verify DRS source servers have the expected tags
**Fix**: Add tags to DRS source servers or use manual selection

### Issue 5: Step Functions Timeout
**Symptom**: Executions stuck in POLLING status
**Check**: Step Functions execution history
**Fix**: Check DRS job status and server launch progress

---

## Frontend Debugging

### Browser Console Checks
```javascript
// Check account context
console.log('Account Context:', window.accountContext);

// Check API responses
// Open Network tab and look for failed API calls

// Check for JavaScript errors
// Open Console tab and look for red error messages
```

### Local Storage Inspection
```javascript
// Check stored account
localStorage.getItem('selectedAccountId');

// Check auth tokens
localStorage.getItem('amplify-signin-with-hostedUI');
```

---

## Step-by-Step Drill Test

### 1. Create Test Protection Group
- Use manual server selection (not tags initially)
- Select 1-2 servers in CONTINUOUS replication state
- Verify servers are not in other active executions

### 2. Create Test Recovery Plan
- Single wave with the test Protection Group
- No pause before wave (for simplicity)
- Save and verify plan appears in list

### 3. Execute Drill
- Click "Run Drill" button
- Confirm any existing instance warnings
- Monitor execution status on Executions page

### 4. Monitor Progress
- Watch execution status change: PENDING → POLLING → LAUNCHING → COMPLETED
- Check Step Functions execution in AWS Console
- Verify DRS job creation and completion

### 5. Validate Results
- Confirm recovery instances are created
- Check instances are tagged as drill instances
- Verify instances can be terminated

---

## DRS Drill Failure Analysis

### Root Cause: ConflictException - Concurrent Job Processing

**Primary Issue**: All DRS source servers failing drill executions due to **ConflictException** errors when attempting concurrent recovery operations.

```
Error: "An error occurred (ConflictException) when calling the StartRecovery operation: 
One or more of the Source Servers included in API call are currently being processed by a Job"
```

### Technical Root Cause

#### AWS DRS Job Queuing Limitation

1. **Sequential Execution Constraint**: DRS doesn't allow multiple concurrent recovery jobs for the same source servers
2. **Job Cleanup Delay**: Previous failed jobs may not immediately release server locks
3. **Rapid Retry Conflicts**: Current orchestration attempts all waves without sufficient delays

#### Current Implementation Issues

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

### Solutions

#### Solution 1: Add Inter-Server Delays ⭐ **Recommended**

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

#### Solution 2: Implement Retry Logic with Exponential Backoff

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

#### Solution 3: Job Status Polling Before Next Wave

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

### Implementation Plan

#### Phase 1: Quick Fix (1-2 hours)
1. **Add 15-second delays** between server launches within each wave
2. **Add 30-second delays** between wave executions
3. **Deploy updated Lambda** with timing fixes

#### Phase 2: Robust Solution (4-6 hours)
1. **Implement retry logic** with exponential backoff for ConflictException
2. **Add job status polling** before proceeding to next wave
3. **Enhanced error handling** with specific conflict detection
4. **Update execution status** to reflect actual progress

#### Phase 3: Advanced Monitoring (Future)
1. **Step Functions integration** for async job tracking
2. **Real-time status updates** in UI
3. **Job completion notifications** via SNS
4. **Detailed execution metrics** in CloudWatch

### Code Changes Required

#### File: `lambda/index.py`

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

### Testing Strategy

#### Test 1: Single Server Launch
```bash
# Test individual server recovery to verify basic functionality
aws drs start-recovery \
  --source-servers sourceServerID=s-3c1730a9e0771ea14 \
  --is-drill \
  --region us-east-1
```

#### Test 2: Sequential Wave Execution
1. Execute Recovery Plan with 1 server per wave
2. Verify 15-second delays between servers
3. Verify 30-second delays between waves
4. Confirm no ConflictException errors

#### Test 3: Full Recovery Plan
1. Execute complete 3-wave plan (6 servers)
2. Monitor DRS job creation timing
3. Verify all servers launch successfully
4. Measure total execution time (expect 2-3 minutes vs current 3 seconds)

### Expected Results

#### Before Fix
```
Execution Time: 3 seconds
Success Rate: 0% (all servers fail)
Error: ConflictException on all servers
```

#### After Fix
```
Execution Time: 2-3 minutes (with delays)
Success Rate: 95%+ (occasional AWS service issues)
Errors: Rare, with automatic retry handling
```

---

## Error Code Reference

| Error Code | Meaning | Solution |
|------------|---------|----------|
| MISSING_FIELD | Required field missing | Check API request format |
| INVALID_EXECUTION_TYPE | Wrong execution type | Use "DRILL" or "RECOVERY" |
| RECOVERY_PLAN_NOT_FOUND | Plan doesn't exist | Verify plan ID |
| PLAN_HAS_NO_WAVES | Empty plan | Add waves to recovery plan |
| PLAN_ALREADY_EXECUTING | Duplicate execution | Wait for current execution to finish |
| SERVER_CONFLICT | Server in use | Use different servers or wait |
| WAVE_SIZE_LIMIT_EXCEEDED | Too many servers | Reduce servers per wave (max 100) |
| CONCURRENT_JOBS_LIMIT_EXCEEDED | Too many DRS jobs | Wait for jobs to complete |
| UNHEALTHY_SERVER_REPLICATION | Bad replication state | Fix server replication |

---

## Success Indicators

### ✅ Drill is Working When:
1. **UI**: Drill button is enabled and clickable
2. **API**: POST to execute endpoint returns 202 with execution ID
3. **Database**: Execution record created with PENDING status
4. **Step Functions**: State machine execution starts
5. **DRS**: Recovery job created with isDrill=true
6. **Instances**: EC2 recovery instances launch
7. **Status**: Execution status updates to COMPLETED
8. **Cleanup**: Instances can be terminated after drill

### ❌ Drill is Broken When:
1. **UI**: Buttons permanently grayed out
2. **API**: Execute endpoint returns 4xx/5xx errors
3. **Step Functions**: Executions fail immediately
4. **DRS**: No recovery jobs created
5. **Instances**: No recovery instances launch
6. **Status**: Executions stuck in PENDING/POLLING

---

## Monitoring & Alerts

### CloudWatch Metrics to Track
- `DRS.ConflictException.Count` - Should drop to near zero
- `DRS.RecoveryJob.Duration` - Track job completion times
- `Orchestration.Wave.Duration` - Monitor wave execution timing

### Recommended Alarms
- **High ConflictException Rate**: > 2 per hour
- **Long Wave Duration**: > 5 minutes per wave
- **Job Failure Rate**: > 10% of recovery jobs

---

## Emergency Rollback

If drill functionality is completely broken:

```bash
# 1. Identify last working commit
git log --oneline --grep="drill" --since="1 week ago"

# 2. Create rollback branch
git checkout -b emergency-drill-rollback

# 3. Revert problematic commits (example)
git revert --no-commit 905a682  # Multi-account changes
git revert --no-commit 5b0e6db  # EC2 instance type changes

# 4. Test rollback
# Deploy and test drill functionality

# 5. If working, create emergency deployment
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

---

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

---

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

---

## Conclusion

The DRS drill failures are **not due to server health issues** but rather **AWS DRS service limitations** around concurrent job processing. The solution requires implementing proper job sequencing, retry logic, and timing delays.

**Recommended Action**: Implement Phase 1 changes immediately (15-second delays) to resolve the immediate issue, then proceed with Phase 2 for robust long-term solution.

**Estimated Fix Time**: 2-4 hours for complete solution  
**Risk Level**: Low (adding delays and retries)  
**Success Probability**: 95%+ based on AWS DRS best practices

---

## Contact Information

**For immediate assistance:**
- Check CloudWatch logs first
- Review Step Functions execution history
- Test with minimal configuration (1 server, 1 wave)
- Document exact error messages and steps to reproduce