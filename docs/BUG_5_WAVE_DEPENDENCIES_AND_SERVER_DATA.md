# Bug Report: Wave Dependencies Not Working + Server Data Not Populated

**Date:** November 28, 2025  
**Severity:** CRITICAL  
**Status:** IDENTIFIED  
**Execution ID:** 36443af3-a0ab-4170-a39c-190951f1a786

---

## Symptoms

### 1. All Waves Launch Simultaneously
Despite having dependencies configured, all 3 waves launched at the same time:
- **Wave 1 (Database):** StartTime = 1764376400
- **Wave 2 (Application):** StartTime = 1764376400 (SAME SECOND!)
- **Wave 3 (Web):** StartTime = 1764376401 (only 1 second later)

Expected: Wave 2 should wait for Wave 1 completion, Wave 3 should wait for Wave 2.

### 2. Server Data Not Populated
All servers showing:
```json
{
  "Status": "UNKNOWN",
  "HostName": "",
  "LaunchTime": 0
}
```

### 3. UI Date Display Shows 1969
Frontend showing "12/31/1969, 7:00:00 PM" for LaunchTime=0 (Unix epoch 0).

---

## Root Cause Analysis

### Issue 1: Wave Dependencies Logic
The `initiate_wave()` function doesn't check wave dependencies before launching.

**Current Code (lambda/index.py):**
```python
def initiate_wave(execution_id, plan_id, wave_data, is_drill):
    # No dependency check - launches immediately
    wave_servers = wave_data.get('Servers', [])
    source_server_ids = [s['SourceServerId'] for s in wave_servers]
    
    response = drs_client.start_recovery(
        sourceServerIDs=source_server_ids,
        isDrill=is_drill,
        tags=get_drs_tags(execution_id, plan_id, wave_id)
    )
```

**Missing Logic:**
- Check if dependent waves are complete
- If dependencies not met, don't launch wave
- ExecutionPoller should re-check pending waves

### Issue 2: Server Data Not Updated by Poller
The `ExecutionPoller` creates JobId but doesn't fetch server details from DRS job.

**Current Code (lambda/poller/execution_poller.py):**
```python
def check_wave_completion(execution_id, wave):
    job_id = wave.get('JobId')
    
    job = drs_client.describe_jobs(
        filters={'jobIDs': [job_id]}
    )['items'][0]
    
    # Only checks job status - doesn't update server details!
    job_status = job['status']
```

**Missing Logic:**
- Extract `participatingServers` from DRS job
- Update each server's Status, InstanceId, LaunchTime
- Fetch hostname from EC2 if available

### Issue 3: Frontend Epoch 0 Handling
`DateTimeDisplay` component doesn't handle LaunchTime=0.

---

## Fix Implementation

### Fix 1: Wave Dependency Check

Update `lambda/index.py`:

```python
def check_wave_dependencies(execution_id, wave_id, waves):
    """Check if all dependent waves are complete."""
    
    current_wave = next(w for w in waves if w['WaveId'] == wave_id)
    dependencies = current_wave.get('Dependencies', [])
    
    if not dependencies:
        return True  # No dependencies
    
    for dep_wave_id in dependencies:
        dep_wave = next(w for w in waves if w['WaveId'] == dep_wave_id)
        if dep_wave.get('Status') != 'COMPLETED':
            return False
    
    return True


def initiate_wave(execution_id, plan_id, wave_data, is_drill, all_waves):
    """Enhanced with dependency checking."""
    
    wave_id = wave_data['WaveId']
    
    # CHECK DEPENDENCIES BEFORE LAUNCHING
    if not check_wave_dependencies(execution_id, wave_id, all_waves):
        print(f"Wave {wave_id} dependencies not met - skipping for now")
        wave_data['Status'] = 'PENDING'
        return {
            'WaveId': wave_id,
            'Status': 'PENDING',
            'Message': 'Waiting for dependencies'
        }
    
    # Continue with existing launch logic...
```

### Fix 2: Server Data Population

Update `lambda/poller/execution_poller.py`:

```python
def update_server_details_from_job(wave, job):
    """Extract server details from DRS job and update wave."""
    
    participating_servers = job.get('participatingServers', [])
    wave_servers = wave.get('Servers', [])
    
    for wave_server in wave_servers:
        source_server_id = wave_server.get('SourceServerId', '')
        
        # Find matching server in DRS job
        drs_server = next(
            (s for s in participating_servers if s['sourceServerID'] == source_server_id),
            None
        )
        
        if drs_server:
            launch_status = drs_server.get('launchStatus', 'UNKNOWN')
            
            # Update server data
            wave_server['Status'] = launch_status
            wave_server['LaunchTime'] = int(time.time())  # Current timestamp
            
            # Get recovery instance ID if launched
            if 'recoveryInstanceID' in drs_server:
                wave_server['InstanceId'] = drs_server['recoveryInstanceID']
                
                # Fetch instance details for hostname
                try:
                    ec2_client = boto3.client('ec2', region_name=wave.get('Region', 'us-east-2'))
                    instances = ec2_client.describe_instances(
                        InstanceIds=[drs_server['recoveryInstanceID']]
                    )
                    
                    if instances['Reservations']:
                        instance = instances['Reservations'][0]['Instances'][0]
                        
                        # Try to get hostname from tags
                        tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
                        hostname = tags.get('Name', instance.get('PrivateDnsName', ''))
                        
                        wave_server['HostName'] = hostname
                        wave_server['PrivateIpAddress'] = instance.get('PrivateIpAddress', '')
                        
                except Exception as e:
                    print(f"Error fetching instance details: {str(e)}")


def check_wave_completion(execution_id, wave):
    """Enhanced with server data population."""
    
    job_id = wave.get('JobId')
    
    job = drs_client.describe_jobs(
        filters={'jobIDs': [job_id]}
    )['items'][0]
    
    job_status = job['status']
    
    # UPDATE SERVER DETAILS FROM JOB
    update_server_details_from_job(wave, job)
    
    # Check completion
    if job_status == 'COMPLETED':
        wave['Status'] = 'COMPLETED'
        return True
    
    # Still running - but data updated
    return False
```

### Fix 3: Frontend Epoch 0 Handling

Update `frontend/src/components/DateTimeDisplay.tsx`:

```typescript
export const DateTimeDisplay: React.FC<DateTimeDisplayProps> = ({ timestamp, format = 'full' }) => {
  // Handle null, undefined, or 0 (epoch 0)
  if (!timestamp || timestamp === 0) {
    return <span className="text-gray-500">-</span>;
  }
  
  const date = new Date(timestamp * 1000);
  // ... rest of component
};
```

### Fix 4: ExecutionPoller Wave Dependency Re-Check

Update `lambda/poller/execution_poller.py`:

```python
def check_pending_waves(execution):
    """Check if any PENDING waves can now be launched."""
    
    waves = execution.get('Waves', [])
    execution_id = execution['ExecutionId']
    plan_id = execution['PlanId']
    is_drill = execution.get('ExecutionType') == 'DRILL'
    
    for wave in waves:
        if wave.get('Status') == 'PENDING':
            # Check if dependencies now met
            if check_wave_dependencies(execution_id, wave['WaveId'], waves):
                print(f"Dependencies now met for wave {wave['WaveId']} - launching")
                
                # Launch the wave
                initiate_wave(execution_id, plan_id, wave, is_drill, waves)
```

---

## Testing Plan

1. **Create new recovery plan** with proper wave dependencies:
   - Wave 1: No dependencies
   - Wave 2: Depends on Wave 1
   - Wave 3: Depends on Wave 2

2. **Execute drill** and verify:
   - Wave 1 launches immediately
   - Wave 2 waits for Wave 1 COMPLETED
   - Wave 3 waits for Wave 2 COMPLETED

3. **Verify server data** populates:
   - Status updates from UNKNOWN → LAUNCHING → LAUNCHED
   - HostName appears
   - LaunchTime shows current timestamp
   - UI displays correct dates (not 1969)

---

## Files to Modify

1. `lambda/index.py` - Add dependency checking
2. `lambda/poller/execution_poller.py` - Add server data population
3. `frontend/src/components/DateTimeDisplay.tsx` - Handle epoch 0

---

## Priority

**CRITICAL** - Breaks core functionality:
- Dependencies are fundamental to wave-based recovery
- Server data is essential for monitoring
- Date display affects user experience

## Next Steps

1. Implement fixes in order (dependency check → server data → UI)
2. Deploy Lambda updates
3. Test with new execution
4. Verify all 3 bugs resolved
