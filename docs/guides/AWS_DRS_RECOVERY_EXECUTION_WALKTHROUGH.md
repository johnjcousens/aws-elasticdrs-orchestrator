# AWS DRS Full Recovery Execution - Complete API Call Sequence

**Document Version**: 1.0  
**Last Updated**: November 27, 2025  
**Purpose**: Step-by-step walkthrough of AWS API calls during production DRS recovery

## Overview

This document details every AWS DRS API call during a **production recovery** operation (failover to AWS). Unlike drills, production recovery launches instances intended for permanent operation and may include post-launch actions.

## Recovery vs Drill: Key Differences

| Aspect | Drill | Production Recovery |
|--------|-------|---------------------|
| `isDrill` parameter | `true` | `false` |
| Instance purpose | Testing only | Production workload |
| Post-launch actions | Optional | Typically required |
| Source replication | Continues | May stop (depends on strategy) |
| Cleanup | Always terminate | Keep running |
| Risk level | Low (isolated) | High (production impact) |

---

## Recovery Execution Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: Pre-Recovery Validation                               │
│ Phase 2: Recovery Initiation                                   │
│ Phase 3: Job Monitoring                                        │
│ Phase 4: Instance Launch Monitoring                            │
│ Phase 5: Post-Launch Actions (SSM)                             │
│ Phase 6: Production Cutover Validation                         │
│ Phase 7: Source Server Management (Optional)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Pre-Recovery Validation

### API Call 1: DescribeSourceServers

**Purpose**: Verify servers ready for production recovery

**Request**:
```python
import boto3
drs = boto3.client('drs', region_name='us-east-1')

response = drs.describe_source_servers(
    filters={'sourceServerIDs': ['s-1234567890abcdef0']}
)
```

**Critical Validation Checks**:
```python
for server in response['items']:
    data_rep = server['dataReplicationInfo']
    lifecycle = server['lifeCycle']
    
    # MUST be CONTINUOUS for production recovery
    assert data_rep['dataReplicationState'] == 'CONTINUOUS'
    assert lifecycle['state'] == 'READY_FOR_RECOVERY'
    
    # Check replication lag (should be minimal)
    lag = data_rep.get('lagDuration', 'PT0S')
    print(f"Replication lag: {lag}")  # e.g., "PT30S" = 30 seconds
```

---

## Phase 2: Recovery Initiation

### API Call 2: StartRecovery (Production Mode)

**Purpose**: Launch production recovery instances

**Request**:
```python
response = drs.start_recovery(
    sourceServers=[{
        'sourceServerID': 's-1234567890abcdef0',
        'recoveryInstanceProperties': {
            'targetInstanceTypeRightSizingMethod': 'BASIC'
        }
    }],
    isDrill=False,  # ← CRITICAL: Production recovery
    tags={
        'RecoveryPlan': 'WebApp-DR-Plan',
        'Wave': '1',
        'ExecutionType': 'Recovery',
        'Environment': 'Production'
    }
)
```

**Response Structure**:
```json
{
  "job": {
    "jobID": "job-recovery-1234567890abcdef",
    "type": "LAUNCH",
    "initiatedBy": "START_RECOVERY",
    "creationDateTime": "2025-11-27T14:30:00.000Z",
    "status": "PENDING",
    "participatingServers": [{
      "sourceServerID": "s-1234567890abcdef0",
      "launchStatus": "PENDING"
    }],
    "tags": {
      "ExecutionType": "Recovery"
    }
  }
}
```

---

## Phase 3: Job Status Monitoring

### API Call 3: DescribeJobs (Polling Loop)

**Request** (Poll every 30 seconds):
```python
job_id = "job-recovery-1234567890abcdef"

while True:
    response = drs.describe_jobs(filters={'jobIDs': [job_id]})
    job = response['items'][0]
    
    print(f"Job: {job['status']}")
    for server in job['participatingServers']:
        print(f"  {server['sourceServerID']}: {server['launchStatus']}")
    
    if job['status'] in ['COMPLETED', 'FAILED']:
        break
    
    time.sleep(30)
```

**Status Progression**:

**T+0s: PENDING**
```json
{
  "status": "PENDING",
  "participatingServers": [{
    "launchStatus": "PENDING"
  }]
}
```

**T+3m: Instance Launched**
```json
{
  "status": "STARTED",
  "participatingServers": [{
    "launchStatus": "LAUNCHED",
    "recoveryInstanceID": "i-0987654321fedcba0"
  }]
}
```

**T+8m: Post-Launch Actions Running**
```json
{
  "status": "STARTED",
  "participatingServers": [{
    "launchStatus": "LAUNCHED",
    "recoveryInstanceID": "i-0987654321fedcba0",
    "postLaunchActionsStatus": "IN_PROGRESS"
  }]
}
```

**T+15m: COMPLETED**
```json
{
  "status": "COMPLETED",
  "endDateTime": "2025-11-27T14:45:00.000Z",
  "participatingServers": [{
    "launchStatus": "LAUNCHED",
    "postLaunchActionsStatus": "COMPLETED"
  }]
}
```

---

## Phase 4: Instance Launch Monitoring

### API Call 4: DescribeRecoveryInstances

**Purpose**: Get production instance details

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
    "jobID": "job-recovery-1234567890abcdef",
    "isDrill": false,
    "pointInTime": "2025-11-27T14:29:00.000Z",
    "postLaunchActionsDeployment": {
      "status": "COMPLETED",
      "ssmAgentDiscoveryDateTime": "2025-11-27T14:35:00.000Z"
    },
    "tags": {
      "Name": "web-server-01-recovery",
      "Environment": "Production"
    }
  }]
}
```

**Key Fields for Production**:
- `isDrill`: `false` (production instance)
- `postLaunchActionsDeployment`: SSM action status
- `ec2InstanceState`: Must be `running` for cutover

---

## Phase 5: Post-Launch Actions (SSM)

### API Call 5: GetLaunchConfiguration

**Purpose**: Verify post-launch actions configured

**Request**:
```python
response = drs.get_launch_configuration(
    sourceServerID='s-1234567890abcdef0'
)
```

**Response Structure**:
```json
{
  "postLaunchActions": {
    "deployment": "TEST_AND_CUTOVER",
    "s3LogBucket": "drs-logs-bucket",
    "cloudWatchLogGroupName": "/aws/drs/post-launch",
    "ssmDocuments": [{
      "actionName": "health-check",
      "ssmDocumentName": "AWS-RunShellScript",
      "timeoutSeconds": 300,
      "mustSucceedForCutover": true,
      "parameters": {
        "commands": ["systemctl status nginx"]
      }
    }]
  }
}
```

### API Call 6: Monitor SSM Actions (via CloudWatch Logs)

**Purpose**: Track post-launch action execution

**Request** (using CloudWatch Logs):
```python
logs = boto3.client('logs')

response = logs.filter_log_events(
    logGroupName='/aws/drs/post-launch',
    logStreamNamePrefix='s-1234567890abcdef0',
    startTime=int(time.time() * 1000) - 3600000
)

for event in response['events']:
    print(event['message'])
```

**Log Output Example**:
```
[2025-11-27 14:35:00] SSM Agent discovered on i-0987654321fedcba0
[2025-11-27 14:35:30] Executing action: health-check
[2025-11-27 14:36:00] health-check: SUCCESS
[2025-11-27 14:38:30] All post-launch actions completed
```

---

## Phase 6: Production Cutover Validation

### API Call 7: EC2 DescribeInstances (Validation)

**Purpose**: Verify instance health and networking

**Request**:
```python
ec2 = boto3.client('ec2', region_name='us-east-1')

response = ec2.describe_instances(
    InstanceIds=['i-0987654321fedcba0']
)
```

**Response**:
```json
{
  "Reservations": [{
    "Instances": [{
      "InstanceId": "i-0987654321fedcba0",
      "State": {"Name": "running"},
      "PrivateIpAddress": "10.0.1.100",
      "PublicIpAddress": "54.123.45.67",
      "VpcId": "vpc-12345678",
      "SubnetId": "subnet-12345678"
    }]
  }]
}
```

---

## Phase 7: Source Server Management (Optional)

### Option A: Disconnect Source Server

**Purpose**: Stop replication after successful recovery

**Request**:
```python
response = drs.disconnect_source_server(
    sourceServerID='s-1234567890abcdef0'
)
```

**Response**:
```json
{
  "sourceServerID": "s-1234567890abcdef0",
  "lifeCycle": {
    "state": "DISCONNECTED"
  },
  "dataReplicationInfo": {
    "dataReplicationState": "STOPPED"
  }
}
```

**⚠️ WARNING**: This is permanent - server must be re-added for future protection

### Option B: Reverse Replication (Failback Preparation)

**Purpose**: Prepare for eventual failback to source

**Request**:
```python
response = drs.reverse_replication(
    recoveryInstanceID='i-0987654321fedcba0'
)
```

---

## Complete Recovery Timeline

```
Time    | API Call                      | Status
--------|-------------------------------|----------------------------------
T+0s    | DescribeSourceServers         | Validate CONTINUOUS replication
T+5s    | StartRecovery (isDrill=false) | Job created (PENDING)
T+30s   | DescribeJobs                  | Job status: STARTED
T+3m    | DescribeJobs                  | launchStatus: LAUNCHED
T+5m    | DescribeRecoveryInstances     | ec2InstanceState: running
T+7m    | DescribeJobs                  | postLaunchActionsStatus: IN_PROGRESS
T+15m   | DescribeJobs                  | Job status: COMPLETED
T+16m   | EC2 DescribeInstances         | Validate networking
T+30m   | DisconnectSourceServer        | Stop source replication (optional)
```

---

## Status Marker Reference

### Job Status Progression
```
PENDING → STARTED → COMPLETED
                 ↘ FAILED
```

### Post-Launch Actions Status
```
NOT_STARTED → IN_PROGRESS → COMPLETED
                          ↘ FAILED
```

---

## Production Implementation

```python
class DRSRecoveryExecutor:
    def __init__(self, region='us-east-1'):
        self.drs = boto3.client('drs', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
    
    def execute_recovery(self, source_server_ids):
        """Execute production recovery with full validation"""
        
        # Phase 1: Validate
        if not self._validate_servers(source_server_ids):
            return False
        
        # Phase 2: Start recovery
        job_id = self._start_recovery(source_server_ids)
        if not job_id:
            return False
        
        # Phase 3: Monitor job
        if not self._monitor_job(job_id):
            return False
        
        # Phase 4: Validate instances
        instances = self._get_recovery_instances(source_server_ids)
        
        # Phase 5: Validate post-launch actions
        if not self._validate_post_launch_actions(instances):
            return False
        
        print("✅ Recovery completed successfully")
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
    
    def _start_recovery(self, server_ids):
        try:
            response = self.drs.start_recovery(
                sourceServers=[{'sourceServerID': sid} for sid in server_ids],
                isDrill=False  # Production recovery
            )
            return response['job']['jobID']
        except Exception as e:
            print(f"❌ Failed: {e}")
            return None
    
    def _monitor_job(self, job_id, timeout=3600):
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
    
    def _validate_post_launch_actions(self, instances):
        for instance in instances:
            pla = instance.get('postLaunchActionsDeployment', {})
            if pla.get('status') != 'COMPLETED':
                print(f"❌ Post-launch actions failed: {instance['sourceServerID']}")
                return False
        return True
```

---

## Summary

**Key Differences from Drill**:
- `isDrill=False` parameter
- Post-launch actions execute automatically
- Instances remain running (not terminated)
- Source replication may be stopped
- Higher validation requirements

**Total API Calls**:
1. DescribeSourceServers (validation)
2. StartRecovery (isDrill=false)
3. DescribeJobs (monitoring)
4. DescribeRecoveryInstances (instance details)
5. GetLaunchConfiguration (post-launch config)
6. CloudWatch Logs (SSM monitoring)
7. EC2 DescribeInstances (networking validation)
8. DisconnectSourceServer (optional cleanup)

**Critical Success Factors**:
- Replication state must be CONTINUOUS
- Minimize replication lag before recovery
- Monitor post-launch actions completion
- Validate application functionality
- Plan for source server management
