# AWS DRS Drill Execution - Complete API Call Sequence

**Document Version**: 1.0  
**Last Updated**: November 27, 2025  
**Purpose**: Step-by-step walkthrough of AWS API calls during DRS Drill execution

## Overview

This document provides a detailed walkthrough of every AWS DRS API call that occurs when initiating and monitoring a drill operation, including all status markers, state transitions, and response structures.

## Drill Execution Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Pre-Drill Validation (Optional but Recommended)       │
│ Phase 2: Drill Initiation                                      │
│ Phase 3: Job Monitoring                                        │
│ Phase 4: Instance Launch Monitoring                            │
│ Phase 5: Post-Launch Validation                                │
│ Phase 6: Drill Termination                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Pre-Drill Validation

### API Call 1: DescribeSourceServers

**Purpose**: Verify source servers are ready for drill

**Request**:
```python
import boto3
drs = boto3.client('drs', region_name='us-east-1')

response = drs.describe_source_servers(
    filters={
        'sourceServerIDs': ['s-1234567890abcdef0', 's-abcdef1234567890']
    }
)
```

**Response Structure**:
```json
{
  "items": [
    {
      "sourceServerID": "s-1234567890abcdef0",
      "arn": "arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0",
      "dataReplicationInfo": {
        "dataReplicationState": "CONTINUOUS",
        "lagDuration": "PT30S"
      },
      "lifeCycle": {
        "state": "READY_FOR_RECOVERY"
      },
      "sourceProperties": {
        "identificationHints": {
          "hostname": "web-server-01"
        },
        "recommendedInstanceType": "m5.large"
      }
    }
  ]
}
```

**Key Status Checks**:
- ✅ `dataReplicationState` = `"CONTINUOUS"` (ready for drill)
- ✅ `lifeCycle.state` = `"READY_FOR_RECOVERY"`
- ❌ `dataReplicationState` = `"INITIAL_SYNC"` (not ready)
- ❌ `dataReplicationState` = `"STALLED"` (replication issue)

---

## Phase 2: Drill Initiation

### API Call 2: StartRecovery (Drill Mode)

**Purpose**: Launch drill instances

**Request**:
```python
response = drs.start_recovery(
    sourceServers=[
        {
            'sourceServerID': 's-1234567890abcdef0',
            'recoveryInstanceProperties': {
                'targetInstanceTypeRightSizingMethod': 'BASIC'
            }
        }
    ],
    isDrill=True,  # ← CRITICAL: This makes it a drill
    tags={
        'RecoveryPlan': 'WebApp-DR-Plan',
        'Wave': '1',
        'ExecutionType': 'Drill'
    }
)
```

**Response Structure**:
```json
{
  "job": {
    "jobID": "job-drill-1234567890abcdef",
    "arn": "arn:aws:drs:us-east-1:123456789012:job/job-drill-1234567890abcdef",
    "type": "LAUNCH",
    "initiatedBy": "START_RECOVERY",
    "creationDateTime": "2025-11-27T14:30:00.000Z",
    "status": "PENDING",
    "participatingServers": [
      {
        "sourceServerID": "s-1234567890abcdef0",
        "launchStatus": "PENDING"
      }
    ],
    "tags": {
      "ExecutionType": "Drill"
    }
  }
}
```

**Key Response Fields**:
- `jobID`: Unique identifier for tracking
- `status`: Initial state is `"PENDING"`
- `participatingServers`: List of servers in this drill
- `launchStatus`: Per-server status (initially `"PENDING"`)

---

## Phase 3: Job Status Monitoring

### API Call 3: DescribeJobs (Polling Loop)

**Purpose**: Monitor drill job progress

**Request** (Poll every 30 seconds):
```python
import time

job_id = "job-drill-1234567890abcdef"

while True:
    response = drs.describe_jobs(filters={'jobIDs': [job_id]})
    job = response['items'][0]
    print(f"Job Status: {job['status']}")
    
    if job['status'] in ['COMPLETED', 'FAILED']:
        break
    
    time.sleep(30)
```

**Response Progression**:

**State 1: PENDING → STARTED** (0-30 seconds)
```json
{
  "items": [{
    "jobID": "job-drill-1234567890abcdef",
    "status": "STARTED",
    "participatingServers": [{
      "sourceServerID": "s-1234567890abcdef0",
      "launchStatus": "PENDING"
    }]
  }]
}
```

**State 2: STARTED (Launching)** (30 seconds - 5 minutes)
```json
{
  "items": [{
    "status": "STARTED",
    "participatingServers": [{
      "sourceServerID": "s-1234567890abcdef0",
      "launchStatus": "LAUNCHED",
      "recoveryInstanceID": "i-0987654321fedcba0"
    }]
  }]
}
```

**State 3: COMPLETED** (5-15 minutes)
```json
{
  "items": [{
    "status": "COMPLETED",
    "endDateTime": "2025-11-27T14:38:45.000Z",
    "participatingServers": [{
      "sourceServerID": "s-1234567890abcdef0",
      "launchStatus": "LAUNCHED",
      "recoveryInstanceID": "i-0987654321fedcba0"
    }]
  }]
}
```

**Job Status Values**:
- `PENDING`: Job queued, not started
- `STARTED`: Job in progress, instances launching
- `COMPLETED`: All instances launched successfully
- `FAILED`: One or more instances failed to launch

---

## Phase 4: Instance Launch Monitoring

### API Call 4: DescribeRecoveryInstances

**Purpose**: Get detailed instance information

**Request**:
```python
response = drs.describe_recovery_instances(
    filters={'sourceServerIDs': ['s-1234567890abcdef0']}
)
```

**Response Structure**:
```json
{
  "items": [{
    "recoveryInstanceID": "i-0987654321fedcba0",
    "sourceServerID": "s-1234567890abcdef0",
    "ec2InstanceID": "i-0987654321fedcba0",
    "ec2InstanceState": "running",
    "jobID": "job-drill-1234567890abcdef",
    "isDrill": true,
    "pointInTime": "2025-11-27T14:29:00.000Z",
    "tags": {
      "Name": "DRS-Drill-web-server-01",
      "DRS-Drill": "true"
    }
  }]
}
```

**Key Fields**:
- `isDrill`: `true` (confirms this is a drill instance)
- `ec2InstanceState`: EC2 instance state (`pending`, `running`, `terminated`)
- `ec2InstanceID`: Actual EC2 instance ID for console access

---

## Phase 5: Post-Launch Validation

### API Call 5: DescribeRecoverySnapshots

**Purpose**: Verify recovery point used

**Request**:
```python
response = drs.describe_recovery_snapshots(
    sourceServerID='s-1234567890abcdef0'
)
```

**Response Structure**:
```json
{
  "items": [{
    "sourceServerID": "s-1234567890abcdef0",
    "snapshotID": "snap-0123456789abcdef0",
    "timestamp": "2025-11-27T14:29:15.000Z",
    "ebsSnapshots": [{
      "snapshotID": "snap-ebs-0123456789",
      "volumeSize": 100
    }]
  }]
}
```

---

## Phase 6: Drill Termination

### API Call 6: TerminateRecoveryInstances

**Purpose**: Clean up drill instances

**Request**:
```python
response = drs.terminate_recovery_instances(
    recoveryInstanceIDs=['i-0987654321fedcba0']
)
```

**Response Structure**:
```json
{
  "job": {
    "jobID": "job-terminate-9876543210fedcba",
    "type": "TERMINATE",
    "status": "STARTED",
    "participatingServers": [{
      "sourceServerID": "s-1234567890abcdef0",
      "recoveryInstanceID": "i-0987654321fedcba0"
    }]
  }
}
```

---

## Complete Drill Execution Timeline

```
Time    | API Call                    | Status
--------|-----------------------------|---------------------------------
T+0s    | DescribeSourceServers       | Validate servers ready
T+5s    | StartRecovery (isDrill)     | Job created (PENDING)
T+30s   | DescribeJobs                | Job status: STARTED
T+3m    | DescribeJobs                | launchStatus: LAUNCHED
T+8m    | DescribeJobs                | Job status: COMPLETED
T+8m    | DescribeRecoveryInstances   | Get instance details
T+30m   | TerminateRecoveryInstances  | Cleanup initiated
T+40m   | DescribeJobs (termination)  | Termination COMPLETED
```

---

## Status Marker Reference

### Job Status Progression
```
PENDING → STARTED → COMPLETED
                 ↘ FAILED
```

### Launch Status Progression (Per Server)
```
PENDING → IN_PROGRESS → LAUNCHED
                      ↘ FAILED
```

### EC2 Instance State Progression
```
pending → running → stopping → terminated
```

---

## Production Implementation Example

```python
import boto3
import time

class DRSDrillExecutor:
    def __init__(self, region='us-east-1'):
        self.drs = boto3.client('drs', region_name=region)
    
    def execute_drill(self, source_server_ids):
        """Execute complete drill with monitoring"""
        
        # Phase 1: Validate
        if not self._validate_servers(source_server_ids):
            return False
        
        # Phase 2: Start drill
        job_id = self._start_drill(source_server_ids)
        if not job_id:
            return False
        
        # Phase 3: Monitor job
        if not self._monitor_job(job_id):
            return False
        
        # Phase 4: Get instance details
        instances = self._get_recovery_instances(source_server_ids)
        print(f"✅ Drill completed: {len(instances)} instances launched")
        return True
    
    def _validate_servers(self, server_ids):
        response = self.drs.describe_source_servers(
            filters={'sourceServerIDs': server_ids}
        )
        
        for server in response['items']:
            state = server['dataReplicationInfo']['dataReplicationState']
            if state != 'CONTINUOUS':
                print(f"❌ Server {server['sourceServerID']}: {state}")
                return False
        return True
    
    def _start_drill(self, server_ids):
        try:
            response = self.drs.start_recovery(
                sourceServers=[{'sourceServerID': sid} for sid in server_ids],
                isDrill=True
            )
            return response['job']['jobID']
        except Exception as e:
            print(f"❌ Failed: {e}")
            return None
    
    def _monitor_job(self, job_id, timeout=1800):
        start = time.time()
        
        while time.time() - start < timeout:
            response = self.drs.describe_jobs(filters={'jobIDs': [job_id]})
            job = response['items'][0]
            
            if job['status'] == 'COMPLETED':
                return True
            elif job['status'] == 'FAILED':
                return False
            
            time.sleep(30)
        return False
    
    def _get_recovery_instances(self, server_ids):
        response = self.drs.describe_recovery_instances(
            filters={'sourceServerIDs': server_ids}
        )
        return response['items']
```

---

## Summary

**Total API Calls for Complete Drill**:
1. DescribeSourceServers (validation)
2. StartRecovery (initiation)
3. DescribeJobs (monitoring - multiple polls)
4. DescribeRecoveryInstances (instance details)
5. DescribeRecoverySnapshots (optional validation)
6. TerminateRecoveryInstances (cleanup)
7. DescribeJobs (termination monitoring)

**Key Takeaways**:
- Drill uses `isDrill=True` parameter in StartRecovery
- Job status progresses: PENDING → STARTED → COMPLETED
- Poll every 30 seconds for status updates
- Drill instances tagged with `isDrill: true`
- Termination is a separate job that must be monitored
- Replication continues unaffected during drill
