# AWS DRS Status Monitoring API Reference

**Document Version**: 1.0  
**Last Updated**: November 27, 2025  
**AWS DRS API Version**: 2020-02-26  

## Overview

This document provides a comprehensive reference for monitoring AWS Elastic Disaster Recovery (DRS) operations including source servers, recovery jobs, drills, and conversions. Essential for building orchestration solutions that need real-time status tracking.

## Core Monitoring Operations

### 1. Source Server Status Monitoring

#### DescribeSourceServers
Monitor replication status and server health.

```python
import boto3

drs = boto3.client('drs', region_name='us-east-1')

# Get all source servers
response = drs.describe_source_servers(maxResults=200)

for server in response['items']:
    server_id = server['sourceServerID']
    
    # Replication status
    data_rep = server.get('dataReplicationInfo', {})
    rep_state = data_rep.get('dataReplicationState')  # CONTINUOUS, INITIAL_SYNC, etc.
    lag_duration = data_rep.get('lagDuration')
    
    # Lifecycle state
    lifecycle = server.get('lifeCycle', {})
    state = lifecycle.get('state')  # READY_FOR_RECOVERY, SYNCING, etc.
    
    # Server properties
    props = server.get('sourceProperties', {})
    hostname = props.get('identificationHints', {}).get('hostname')
    
    print(f"Server {server_id}: {hostname} - {rep_state} (lag: {lag_duration})")
```

**Key Status Fields**:
- `dataReplicationState`: STOPPED, INITIATING, INITIAL_SYNC, BACKLOG, CONTINUOUS, PAUSED, STALLED, DISCONNECTED
- `lifeCycle.state`: READY_FOR_RECOVERY, SYNCING, STOPPED, DISCONNECTED
- `lagDuration`: Replication lag (ISO 8601 duration format)

### 2. Recovery Job Monitoring

#### DescribeJobs
Track recovery, drill, and conversion operations.

```python
# Monitor all jobs
jobs_response = drs.describe_jobs(
    filters={
        'jobIDs': ['job-12345'],  # Optional: specific job IDs
        'fromDate': '2025-11-27T00:00:00Z',
        'toDate': '2025-11-27T23:59:59Z'
    }
)

for job in jobs_response['items']:
    job_id = job['jobID']
    job_type = job['type']  # LAUNCH, TERMINATE, CREATE_CONVERTED_SNAPSHOT
    status = job['status']  # PENDING, STARTED, COMPLETED, FAILED
    
    # Participating servers
    servers = job.get('participatingServers', [])
    
    # Job progress
    initiated_by = job.get('initiatedBy')
    creation_time = job['creationDateTime']
    end_time = job.get('endDateTime')
    
    print(f"Job {job_id}: {job_type} - {status} ({len(servers)} servers)")
    
    # Check for errors
    if status == 'FAILED':
        error = job.get('arn')  # Error details in ARN field sometimes
        print(f"  Error: {error}")
```

**Job Types**:
- `LAUNCH`: Recovery or drill launch
- `TERMINATE`: Terminate recovery instances
- `CREATE_CONVERTED_SNAPSHOT`: Conversion operation

**Job Status Values**:
- `PENDING`: Job queued
- `STARTED`: Job in progress
- `COMPLETED`: Job finished successfully
- `FAILED`: Job failed with errors

### 3. Recovery Instance Monitoring

#### DescribeRecoveryInstances
Monitor launched recovery instances.

```python
# Get recovery instances
instances_response = drs.describe_recovery_instances()

for instance in instances_response['items']:
    instance_id = instance.get('ec2InstanceID')
    source_server_id = instance['sourceServerID']
    
    # Recovery instance state
    state = instance.get('recoveryInstanceState')  # LAUNCHING, RUNNING, TERMINATED
    
    # Job information
    job_id = instance.get('jobID')
    is_drill = instance.get('isDrill', False)
    
    # Launch configuration
    launch_config = instance.get('launchConfiguration', {})
    instance_type = launch_config.get('ec2LaunchTemplateID')
    
    print(f"Instance {instance_id}: {source_server_id} - {state} ({'drill' if is_drill else 'recovery'})")
```

### 4. Recovery Snapshots

#### DescribeRecoverySnapshots
Monitor available recovery points.

```python
# Get recovery snapshots for a source server
snapshots_response = drs.describe_recovery_snapshots(
    sourceServerID='s-1234567890abcdef0'
)

for snapshot in snapshots_response['items']:
    snapshot_id = snapshot['snapshotID']
    timestamp = snapshot['timestamp']
    expected_timestamp = snapshot.get('expectedTimestamp')
    
    # Snapshot properties
    ebs_snapshots = snapshot.get('ebsSnapshots', [])
    
    print(f"Snapshot {snapshot_id}: {timestamp} ({len(ebs_snapshots)} EBS snapshots)")
```

## Status Polling Patterns

### 1. Real-Time Job Monitoring

```python
import time
from datetime import datetime, timedelta

def monitor_recovery_job(job_id, timeout_minutes=30):
    """Monitor a recovery job until completion or timeout"""
    start_time = datetime.now()
    timeout = timedelta(minutes=timeout_minutes)
    
    while datetime.now() - start_time < timeout:
        try:
            jobs = drs.describe_jobs(filters={'jobIDs': [job_id]})
            
            if not jobs['items']:
                print(f"Job {job_id} not found")
                return None
                
            job = jobs['items'][0]
            status = job['status']
            
            print(f"Job {job_id}: {status}")
            
            if status in ['COMPLETED', 'FAILED']:
                return job
                
            time.sleep(30)  # Poll every 30 seconds
            
        except Exception as e:
            print(f"Error monitoring job: {e}")
            time.sleep(60)  # Wait longer on error
    
    print(f"Job {job_id} monitoring timed out after {timeout_minutes} minutes")
    return None

# Usage
job_result = monitor_recovery_job('job-12345')
if job_result and job_result['status'] == 'COMPLETED':
    print("Recovery completed successfully")
```

### 2. Source Server Health Check

```python
def check_server_ready_for_recovery(source_server_id):
    """Check if source server is ready for recovery"""
    try:
        servers = drs.describe_source_servers(
            filters={'sourceServerIDs': [source_server_id]}
        )
        
        if not servers['items']:
            return False, "Server not found"
            
        server = servers['items'][0]
        
        # Check replication state
        data_rep = server.get('dataReplicationInfo', {})
        rep_state = data_rep.get('dataReplicationState')
        
        # Check lifecycle state
        lifecycle = server.get('lifeCycle', {})
        life_state = lifecycle.get('state')
        
        # Ready conditions
        if rep_state == 'CONTINUOUS' and life_state == 'READY_FOR_RECOVERY':
            return True, "Ready for recovery"
        elif rep_state in ['INITIAL_SYNC', 'BACKLOG']:
            return False, f"Still syncing: {rep_state}"
        elif rep_state == 'STALLED':
            return False, "Replication stalled"
        elif rep_state == 'DISCONNECTED':
            return False, "Server disconnected"
        else:
            return False, f"Unknown state: {rep_state}/{life_state}"
            
    except Exception as e:
        return False, f"Error checking server: {e}"

# Usage
ready, message = check_server_ready_for_recovery('s-1234567890abcdef0')
print(f"Server ready: {ready} - {message}")
```

## Error Handling & Limitations

### Common Exceptions

```python
from botocore.exceptions import ClientError

try:
    response = drs.start_recovery(
        sourceServers=[{'sourceServerID': 's-1234567890abcdef0'}],
        isDrill=True
    )
except ClientError as e:
    error_code = e.response['Error']['Code']
    
    if error_code == 'ConflictException':
        print("Server is busy with another operation")
        # Implement retry logic with exponential backoff
        
    elif error_code == 'ValidationException':
        print("Invalid parameters provided")
        
    elif error_code == 'ResourceNotFoundException':
        print("Source server not found")
        
    elif error_code == 'UninitializedAccountException':
        print("DRS not initialized in this region")
        
    else:
        print(f"Unexpected error: {error_code}")
```

### Rate Limiting

AWS DRS APIs have rate limits. Implement exponential backoff:

```python
import random

def exponential_backoff_retry(func, max_retries=5):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt == max_retries - 1:
                    raise
                
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
            else:
                raise
```

### DRS Service Limitations

1. **Concurrent Operations**: Only one recovery/drill operation per source server at a time
2. **Job Retention**: Job history retained for 90 days
3. **API Rate Limits**: Varies by operation (typically 10-100 requests per second)
4. **Regional**: DRS operations are region-specific
5. **Cross-Account**: Requires proper IAM role assumptions

## Monitoring Best Practices

### 1. Polling Intervals

- **Job Status**: 30-60 seconds during active operations
- **Server Health**: 5-10 minutes for routine monitoring
- **Recovery Instances**: 30 seconds during launch, 5 minutes when stable

### 2. Timeout Handling

- **Recovery Jobs**: 30-60 minutes typical timeout
- **Drill Jobs**: 15-30 minutes typical timeout
- **Termination Jobs**: 5-10 minutes typical timeout

### 3. Status Aggregation

```python
def get_recovery_plan_status(source_server_ids):
    """Get aggregated status for multiple servers"""
    status_summary = {
        'ready': 0,
        'syncing': 0,
        'issues': 0,
        'total': len(source_server_ids)
    }
    
    server_details = []
    
    for server_id in source_server_ids:
        ready, message = check_server_ready_for_recovery(server_id)
        
        server_details.append({
            'serverId': server_id,
            'ready': ready,
            'status': message
        })
        
        if ready:
            status_summary['ready'] += 1
        elif 'syncing' in message.lower():
            status_summary['syncing'] += 1
        else:
            status_summary['issues'] += 1
    
    return status_summary, server_details
```

## Integration with Orchestration

### Wave-Based Execution Monitoring

```python
def monitor_wave_execution(wave_servers, job_ids):
    """Monitor multiple recovery jobs for wave-based execution"""
    completed_jobs = set()
    failed_jobs = set()
    
    while len(completed_jobs) + len(failed_jobs) < len(job_ids):
        for job_id in job_ids:
            if job_id in completed_jobs or job_id in failed_jobs:
                continue
                
            jobs = drs.describe_jobs(filters={'jobIDs': [job_id]})
            if jobs['items']:
                job = jobs['items'][0]
                status = job['status']
                
                if status == 'COMPLETED':
                    completed_jobs.add(job_id)
                    print(f"Job {job_id} completed successfully")
                elif status == 'FAILED':
                    failed_jobs.add(job_id)
                    print(f"Job {job_id} failed")
        
        time.sleep(30)
    
    return {
        'completed': len(completed_jobs),
        'failed': len(failed_jobs),
        'success_rate': len(completed_jobs) / len(job_ids) * 100
    }
```

## CloudWatch Integration

### Custom Metrics

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_drs_metrics(source_server_id, rep_state, lag_duration):
    """Publish DRS metrics to CloudWatch"""
    
    # Replication state metric
    state_value = 1 if rep_state == 'CONTINUOUS' else 0
    
    cloudwatch.put_metric_data(
        Namespace='DRS/Orchestration',
        MetricData=[
            {
                'MetricName': 'ReplicationHealthy',
                'Dimensions': [
                    {'Name': 'SourceServerID', 'Value': source_server_id}
                ],
                'Value': state_value,
                'Unit': 'Count'
            },
            {
                'MetricName': 'ReplicationLag',
                'Dimensions': [
                    {'Name': 'SourceServerID', 'Value': source_server_id}
                ],
                'Value': parse_lag_duration(lag_duration),
                'Unit': 'Seconds'
            }
        ]
    )

def parse_lag_duration(lag_duration):
    """Convert ISO 8601 duration to seconds"""
    # Simple parser for PT30S format
    if lag_duration and lag_duration.startswith('PT') and lag_duration.endswith('S'):
        return int(lag_duration[2:-1])
    return 0
```

## Troubleshooting Guide

### Common Issues

1. **ConflictException**: Server busy with another operation
   - **Solution**: Implement retry with 30-60 second delays
   - **Prevention**: Check job status before starting new operations

2. **ValidationException**: Invalid source server ID
   - **Solution**: Validate server exists with DescribeSourceServers
   - **Prevention**: Maintain server inventory with regular discovery

3. **ResourceNotFoundException**: Server not found
   - **Solution**: Refresh server list, check region
   - **Prevention**: Regular server discovery and validation

4. **UninitializedAccountException**: DRS not set up
   - **Solution**: Initialize DRS in the region first
   - **Prevention**: Check initialization status before operations

### Debugging Tools

```python
def debug_drs_operation(source_server_id):
    """Comprehensive debugging for DRS operations"""
    print(f"Debugging DRS for server: {source_server_id}")
    
    # 1. Check server exists
    try:
        servers = drs.describe_source_servers(
            filters={'sourceServerIDs': [source_server_id]}
        )
        if not servers['items']:
            print("❌ Server not found")
            return
        
        server = servers['items'][0]
        print("✅ Server found")
        
        # 2. Check replication status
        data_rep = server.get('dataReplicationInfo', {})
        rep_state = data_rep.get('dataReplicationState')
        print(f"📊 Replication state: {rep_state}")
        
        # 3. Check for active jobs
        jobs = drs.describe_jobs(
            filters={'fromDate': (datetime.now() - timedelta(hours=1)).isoformat()}
        )
        
        active_jobs = [j for j in jobs['items'] 
                      if source_server_id in [s['sourceServerID'] for s in j.get('participatingServers', [])]
                      and j['status'] in ['PENDING', 'STARTED']]
        
        if active_jobs:
            print(f"⚠️  {len(active_jobs)} active jobs found")
            for job in active_jobs:
                print(f"   Job {job['jobID']}: {job['type']} - {job['status']}")
        else:
            print("✅ No active jobs")
            
    except Exception as e:
        print(f"❌ Error: {e}")
```

---

## Summary

This API reference provides the essential operations for monitoring AWS DRS status in orchestration solutions. Key takeaways:

1. **Use DescribeSourceServers** for health monitoring
2. **Use DescribeJobs** for operation tracking  
3. **Implement proper error handling** for ConflictException
4. **Use appropriate polling intervals** (30-60 seconds)
5. **Monitor both replication and lifecycle states**
6. **Implement exponential backoff** for rate limiting

For production orchestration, combine these APIs with CloudWatch metrics and proper timeout handling to build robust disaster recovery automation.