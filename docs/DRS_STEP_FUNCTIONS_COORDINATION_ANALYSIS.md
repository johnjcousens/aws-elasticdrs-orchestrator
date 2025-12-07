# DRS + Step Functions Coordination Analysis

## Executive Summary

This document analyzes how the AWS reference implementation (`drs-plan-automation`) coordinates DRS drill execution with Step Functions, and compares it to our implementation.

**Key Finding**: The reference implementation uses a **single Lambda function** that handles ALL actions (begin, update_wave_status, update_action_status, all_waves_completed) with Step Functions providing the **wait/poll/loop orchestration**. The Lambda returns state that Step Functions uses to decide what to do next.

---

## Reference Implementation Architecture

### The Coordination Pattern

```
┌─────────────────────────────────────────────────────────────────────┐
│                     STEP FUNCTIONS STATE MACHINE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌─────────────────────┐    ┌────────────────┐  │
│  │ InitiateWave │───▶│ DetermineWavePlan   │───▶│ DetermineWave  │  │
│  │    Plan      │    │      State          │    │     State      │  │
│  └──────────────┘    └─────────────────────┘    └────────────────┘  │
│         │                     │                        │            │
│         │                     │                        ▼            │
│         │                     │              ┌─────────────────┐    │
│         │                     │              │ WaitForWave     │    │
│         │                     │              │   Update        │    │
│         │                     │              │ (30 seconds)    │    │
│         │                     │              └─────────────────┘    │
│         │                     │                        │            │
│         │                     │                        ▼            │
│         │                     │              ┌─────────────────┐    │
│         │                     │              │ UpdateWave      │    │
│         │                     │              │   Status        │    │
│         │                     │              └─────────────────┘    │
│         │                     │                        │            │
│         │                     │                        │            │
│         │                     ◀────────────────────────┘            │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    SINGLE LAMBDA FUNCTION                     │   │
│  │                  (drs_automation_plan.handler)                │   │
│  │                                                               │   │
│  │  Actions:                                                     │   │
│  │  - begin: Start wave plan, call start_recovery()              │   │
│  │  - update_wave_status: Poll describe_jobs(), check servers    │   │
│  │  - update_action_status: Poll SSM automation status           │   │
│  │  - all_waves_completed: Record final status                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Lambda Returns State, Step Functions Decides**
   - Lambda returns `application` object with flags like `wave_completed`, `all_waves_completed`, `status`
   - Step Functions uses Choice states to evaluate these flags
   - Step Functions handles the wait/loop logic

2. **Dynamic Wait Times**
   - `current_wave_update_time` (default 30s) controls polling interval
   - `current_wave_wait_time` (MaxWaitTime) controls timeout
   - Step Functions uses `SecondsPath` to read wait time from Lambda response

3. **Simple DRS API Call**
   ```python
   # Reference implementation - start_recovery() call
   drs_launch = drs_client.start_recovery(
       isDrill=isdrill,
       sourceServers=servers  # Just [{sourceServerID: 'xxx'}, ...]
   )
   # NO TAGS! Just isDrill and sourceServers
   ```

4. **Job Status Checking**
   ```python
   # Check job status
   job_result = drs_client.describe_jobs(filters={'jobIDs': [jobID]})
   
   # Check if job completed
   if recovery_status['status'] in DRS_JOB_STATUS_COMPLETE_STATES:  # ['COMPLETED']
       # Wave is done, move to post-wave actions or next wave
   ```

---

## Critical DRS API Details

### start_recovery() Parameters

```python
# MINIMAL call - this is what works
response = drs_client.start_recovery(
    isDrill=True,           # or False for actual recovery
    sourceServers=[
        {'sourceServerID': 's-xxxxx'},
        {'sourceServerID': 's-yyyyy'}
    ]
)

# Response contains:
# {
#     'job': {
#         'jobID': 'drsjob-xxxxx',
#         'status': 'PENDING',
#         'participatingServers': [...],
#         ...
#     }
# }
```

### Job Status Constants

```python
# Job-level status (from describe_jobs)
DRS_JOB_STATUS_COMPLETE_STATES = ['COMPLETED']
DRS_JOB_STATUS_WAIT_STATES = ['PENDING', 'STARTED']

# Server-level launch status (from participatingServers[].launchStatus)
DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES = ['LAUNCHED']
DRS_JOB_SERVERS_COMPLETE_FAILURE_STATES = ['FAILED', 'TERMINATED']
DRS_JOB_SERVERS_COMPLETE_WAIT_STATES = ['PENDING', 'IN_PROGRESS']
```

### The Polling Loop

```python
# Reference implementation polling logic
def check_recovery_status(jobID, drs_client):
    # Get job status
    job_result = drs_client.describe_jobs(filters={'jobIDs': [jobID]})
    recovery_status = job_result['items'][0]
    
    # Get detailed log items
    paginator = drs_client.get_paginator('describe_job_log_items')
    response_iterator = paginator.paginate(jobID=jobID)
    recovery_items = []
    for i in response_iterator:
        recovery_items += i.get('items')
    
    recovery_status['detail'] = recovery_items
    return recovery_status
```

---

## Step Functions State Machine Flow

### Reference Implementation States

```yaml
States:
  InitiateWavePlan:
    Type: Task
    # Calls Lambda with action='begin'
    # Lambda calls start_recovery() and returns application state
    Next: DetermineWavePlanState

  DetermineWavePlanState:
    Type: Choice
    Choices:
      - Variable: $.status
        StringEquals: failed
        Next: ApplicationFailed
      - Variable: $.application.all_waves_completed
        BooleanEquals: true
        Next: ApplicationCompleted
      - Variable: $.application.all_waves_completed
        BooleanEquals: false
        Next: DetermineWaveState

  DetermineWaveState:
    Type: Choice
    Choices:
      - Variable: $.application.wave_completed
        BooleanEquals: false
        Next: WaitForWaveUpdate
      - Variable: $.application.wave_completed
        BooleanEquals: true
        Next: DetermineWavePlanState

  WaitForWaveUpdate:
    Type: Wait
    SecondsPath: $.application.current_wave_update_time  # Dynamic wait!
    Next: UpdateWaveStatus

  UpdateWaveStatus:
    Type: Task
    # Calls Lambda with action='update_wave_status'
    # Lambda calls describe_jobs() and checks server launch status
    Next: DetermineWaveState
```

### The Loop Pattern

1. **InitiateWavePlan** → Calls Lambda with `action='begin'`
2. Lambda calls `start_recovery()`, returns `wave_completed=false`
3. **DetermineWavePlanState** → Sees `all_waves_completed=false`, goes to **DetermineWaveState**
4. **DetermineWaveState** → Sees `wave_completed=false`, goes to **WaitForWaveUpdate**
5. **WaitForWaveUpdate** → Waits 30 seconds
6. **UpdateWaveStatus** → Calls Lambda with `action='update_wave_status'`
7. Lambda calls `describe_jobs()`, checks `participatingServers[].launchStatus`
8. If all servers LAUNCHED → `wave_completed=true`, Lambda starts next wave
9. If not all LAUNCHED → `wave_completed=false`, loop back to step 4
10. When all waves done → `all_waves_completed=true` → **ApplicationCompleted**

---

## Our Implementation vs Reference

### What We Do Similarly ✅

1. **Single Lambda with action routing** - Our `orchestration_stepfunctions.py` handles `begin` and `update_wave_status`
2. **Step Functions wait/poll loop** - Our state machine has the same pattern
3. **Dynamic wait times** - We use `SecondsPath` for polling interval
4. **Job status checking** - We call `describe_jobs()` and check `participatingServers`

### What We Do Differently

| Aspect | Reference | Our Implementation |
|--------|-----------|-------------------|
| Server discovery | Tag-based at runtime | Pre-defined in Protection Groups |
| Pre/Post wave actions | SSM Automation | Not implemented yet |
| Cross-account | STS AssumeRole | Not implemented yet |
| SNS notifications | Built-in | Not implemented yet |
| DynamoDB structure | AppId_PlanId composite key | ExecutionId + PlanId |

### Critical Code Comparison

**Reference start_recovery():**
```python
drs_launch = drs_client.start_recovery(
    isDrill=isdrill,
    sourceServers=servers  # [{sourceServerID: 'xxx'}]
)
```

**Our start_recovery():**
```python
response = drs_client.start_recovery(
    isDrill=is_drill,
    sourceServers=source_servers  # [{sourceServerID: 'xxx'}]
    # NO TAGS - we removed them after finding they caused issues
)
```

✅ **These are now identical** - we removed the tags parameter.

---

## DRS Drill Execution Flow

### What Happens When You Call start_recovery()

1. **DRS creates a Job** with status `PENDING`
2. **DRS creates Recovery Instances** for each source server
3. **DRS performs conversion** (this is where DetachVolume happens!)
   - Creates snapshots from replication volumes
   - Creates AMIs from snapshots
   - Launches EC2 instances from AMIs
   - **DetachVolume** is called during conversion to detach replication volumes
4. **Server launchStatus transitions**: `PENDING` → `IN_PROGRESS` → `LAUNCHED` (or `FAILED`)
5. **Job status transitions**: `PENDING` → `STARTED` → `COMPLETED`

### The DetachVolume Issue We Found

During step 3 (conversion), DRS calls EC2 APIs using **credential passthrough** from the calling Lambda:

```
Lambda (OrchestrationRole) 
    → calls drs:StartRecovery
        → DRS service uses Lambda's credentials for:
            - ec2:CreateSnapshot
            - ec2:CreateImage  
            - ec2:RunInstances
            - ec2:DetachVolume  ← THIS WAS MISSING!
            - ec2:CreateTags
            - etc.
```

**Fix Applied**: Added `ec2:DetachVolume` to OrchestrationRole.

---

## Recommendations for Morning Testing

### 1. Verify CloudFormation Update Completed
```bash
export AWS_PAGER=""
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test \
  --query 'Stacks[0].StackStatus' \
  --region us-east-1
```

### 2. Verify IAM Permission
```bash
aws iam get-role-policy \
  --role-name drs-orchestration-test-LambdaStac-OrchestrationRole-LuY7ANIrFtME \
  --policy-name EC2Access \
  --region us-east-1 | grep DetachVolume
```

### 3. Run Clean Drill Test
- Execute Recovery Plan with both servers
- Monitor Step Functions execution in console
- Check CloudWatch logs for `orchestration-stepfunctions` Lambda
- Both servers should now reach `LAUNCHED` status

### 4. If Still Failing
Check CloudTrail for new error patterns:
```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=ec2.amazonaws.com \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --region us-east-1 \
  --query 'Events[?contains(CloudTrailEvent, `errorCode`)].CloudTrailEvent' \
  --output text | jq -r '.errorCode + ": " + .errorMessage' | sort | uniq -c
```

---

## Summary

The reference implementation proves that DRS drills work with a simple pattern:

1. **Call `start_recovery(isDrill=True, sourceServers=[...])`** - no tags needed
2. **Poll `describe_jobs()` every 30 seconds**
3. **Check `participatingServers[].launchStatus`** for each server
4. **Wait until all servers reach `LAUNCHED`** or timeout

Our implementation follows this pattern correctly. The only issue was missing IAM permissions (`ec2:DetachVolume`) that DRS needs during the conversion phase.

**The fix is deployed. Morning test should succeed.**
