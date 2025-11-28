# DRS Execution Fix - Implementation Plan

## Executive Summary

**Problem**: DRS executions fail because Lambda workers timeout (15 min) before operations complete (20-30+ min actual duration).

**Root Cause**: Synchronous execution pattern in an asynchronous world.

**Solution**: Implement unified async execution engine with separate polling service for long-running DRS jobs, supporting both drill and production recovery modes.

## Timeline Analysis

### Drill Execution (Testing)
```
PENDING Phase:     13 min 28 sec (808s) - 68% of total time
IN_PROGRESS Phase:  6 min 16 sec (376s) - 32% of total time
TOTAL Duration:    20 min 00 sec (1,184s)
```

### Production Recovery (Failover)
```
PENDING Phase:     13 min 28 sec (808s) - 45% of total time
IN_PROGRESS Phase:  6 min 16 sec (376s) - 21% of total time
POST-LAUNCH Phase: 10 min 00 sec (600s) - 34% of total time (SSM actions)
TOTAL Duration:    30 min 00 sec (1,784s)
```

**Lambda Constraint**: 15 minutes maximum (900s)
**Gap**: 
- Drill: 5 minutes short (284s deficit)
- Production: 15 minutes short (884s deficit)

## Execution Mode Comparison

| Feature | Drill Mode | Production Recovery |
|---------|-----------|---------------------|
| `isDrill` parameter | `true` | `false` |
| Duration | ~20 minutes | ~30 minutes |
| Post-launch actions | Optional | Required (health checks) |
| Instance cleanup | Always terminate | Keep running |
| Source replication | Continues | May stop |
| Risk level | Low (isolated) | High (production impact) |

## Current Architecture (BROKEN)

```
User Request → API Gateway → Lambda Worker (sync)
                                  ↓
                            Start DRS Job
                                  ↓
                            Wait for completion ❌ TIMES OUT
                                  ↓
                            Update DynamoDB ❌ NEVER HAPPENS
                                  ↓
                            Return result ❌ NEVER RETURNS
```

## Target Architecture (UNIFIED EXECUTION ENGINE)

```
User Request → API Gateway → Unified Execution Engine
                                  ↓
                            Determine Mode (DRILL | RECOVERY)
                                  ↓
                            Start DRS Jobs (with mode flag)
                                  ↓
                            Store execution in DynamoDB
                                  ↓
                            Return 202 Accepted ✓
                                  
EventBridge Schedule (30s) → Unified Polling Lambda
                                  ↓
                            Query DRS job status
                                  ↓
                            For RECOVERY mode:
                                  ↓
                            Monitor post-launch actions (SSM)
                                  ↓
                            Update DynamoDB
                                  ↓
                            Continue until COMPLETED/FAILED
                                  
Frontend → Poll API (15s intervals)
                                  ↓
                            Display progress (mode-aware) ✓
```

### Unified Engine Benefits

**Production Ready**:
- Complete DR capability from day one
- Both drill and production recovery supported
- Consistent behavior and monitoring

**Customer Friendly**:
- Single API endpoint for all execution types
- Consistent user experience
- Clear mode differentiation in UI

**Developer Friendly**:
- One execution engine to maintain
- Shared polling infrastructure (DRY)
- Easy to extend with new execution types
- Clear separation via `ExecutionType` field

## Implementation Plan

### Phase 1: Lambda Refactoring (Critical Path)

#### 1.1 Unified Execution Worker

**File**: `lambda/index.py`

**Changes**:
```python
# BEFORE (lines 700-800)
def execute_recovery_plan_worker(payload: Dict) -> None:
    """Background worker - executes the actual recovery (async invocation)"""
    # ... starts jobs ...
    time.sleep(30)  # ❌ REMOVE - causes timeout
    # ... waits for completion ...
    
# AFTER - Unified Execution Engine
def execute_recovery_plan_worker(payload: Dict) -> None:
    """Unified execution engine - supports DRILL and RECOVERY modes"""
    try:
        execution_id = payload['executionId']
        plan_id = payload['planId']
        plan = payload['plan']
        execution_type = payload.get('executionType', 'DRILL')  # NEW
        
        print(f"Starting {execution_type} execution {execution_id}")
        
        # Update status to IN_PROGRESS
        execution_history_table.update_item(
            Key={'ExecutionId': execution_id, 'PlanId': plan_id},
            UpdateExpression='SET #status = :status, ExecutionType = :type',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={
                ':status': 'IN_PROGRESS',
                ':type': execution_type
            }
        )
        
        # Execute waves - START JOBS ONLY (mode-aware)
        is_drill = (execution_type == 'DRILL')
        wave_results = []
        
        for wave_index, wave in enumerate(plan['Waves']):
            wave_result = initiate_wave(
                wave, 
                execution_id, 
                is_drill=is_drill  # Pass mode to wave initiation
            )
            wave_results.append(wave_result)
            
            # Store intermediate results
            execution_history_table.update_item(
                Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                UpdateExpression='SET Waves = :waves',
                ExpressionAttributeValues={':waves': wave_results}
            )
        
        # Mark as POLLING (unified status for both modes)
        execution_history_table.update_item(
            Key={'ExecutionId': execution_id, 'PlanId': plan_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={':status': 'POLLING'}
        )
        
        print(f"Worker initiated {execution_type} execution {execution_id} - polling will continue")
        
    except Exception as e:
        print(f"Worker error for execution {execution_id}: {str(e)}")
        # Mark as failed...
```

#### 1.2 Mode-Aware Wave Initiation

```python
def initiate_wave(wave: Dict, execution_id: str, is_drill: bool = True) -> Dict:
    """Initiate wave - start all jobs, return immediately (mode-aware)"""
    try:
        pg_id = wave.get('ProtectionGroupId')
        if not pg_id:
            return create_error_wave_result(wave, 'No Protection Group')
        
        # Get Protection Group
        pg_result = protection_groups_table.get_item(Key={'GroupId': pg_id})
        if 'Item' not in pg_result:
            return create_error_wave_result(wave, 'Protection Group not found')
        
        pg = pg_result['Item']
        region = pg['Region']
        server_ids = get_wave_server_ids(wave, pg)
        
        if not server_ids:
            return create_empty_wave_result(wave)
        
        mode = "DRILL" if is_drill else "RECOVERY"
        print(f"Initiating {mode} wave: {wave.get('WaveName')} with {len(server_ids)} servers")
        
        # Start jobs for all servers (NO WAITING)
        server_results = []
        for server_id in server_ids:
            job_result = start_drs_recovery_with_retry(
                server_id, 
                region, 
                execution_id,
                is_drill=is_drill  # Pass mode to DRS API
            )
            server_results.append(job_result)
        
        # Return with LAUNCHING status
        return {
            'WaveName': wave.get('WaveName', 'Unknown'),
            'ProtectionGroupId': pg_id,
            'Region': region,
            'Status': 'LAUNCHING',  # Jobs started but not complete
            'Servers': server_results,
            'StartTime': int(time.time()),
            'ExecutionMode': mode  # Track mode for polling
        }
        
    except Exception as e:
        print(f"Error initiating wave: {str(e)}")
        return create_error_wave_result(wave, str(e))

def start_drs_recovery_with_retry(
    server_id: str, 
    region: str, 
    execution_id: str,
    is_drill: bool = True,
    max_retries: int = 3
) -> Dict:
    """Start DRS recovery job with retry logic (mode-aware)"""
    drs_client = boto3.client('drs', region_name=region)
    
    for attempt in range(max_retries):
        try:
            response = drs_client.start_recovery(
                sourceServers=[{
                    'sourceServerID': server_id
                }],
                isDrill=is_drill,  # Mode flag
                tags={
                    'ExecutionId': execution_id,
                    'ExecutionType': 'DRILL' if is_drill else 'RECOVERY'
                }
            )
            
            job = response['job']
            return {
                'SourceServerId': server_id,
                'RecoveryJobId': job['jobID'],
                'Status': 'PENDING',
                'LaunchTime': int(time.time()),
                'IsDrill': is_drill
            }
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return {
                    'SourceServerId': server_id,
                    'Status': 'FAILED',
                    'Error': str(e)
                }
```

#### 1.3 Update Lambda Timeout

**File**: `cfn/lambda-stack.yaml`

```yaml
# BEFORE
ApiHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    Timeout: 900  # 15 minutes - TOO LONG

# AFTER
ApiHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    Timeout: 120  # 2 minutes - just for API calls
```

### Phase 2: DynamoDB Schema Updates

#### 2.1 New Execution Status Values

Add new status transitions:
- `PENDING` - Initial state
- `IN_PROGRESS` - Worker started initiating jobs
- `POLLING` - Jobs initiated, waiting for completion (**NEW**)
- `COMPLETED` - All jobs finished successfully
- `PARTIAL` - Some jobs failed
- `FAILED` - Critical failure

#### 2.2 Enhanced Server Tracking (Mode-Aware)

```python
# Current server result
{
    'SourceServerId': 's-123',
    'RecoveryJobId': 'drsjob-456',
    'Status': 'LAUNCHING',  # Static
    'LaunchTime': 1234567890
}

# Enhanced server result (UNIFIED)
{
    'SourceServerId': 's-123',
    'RecoveryJobId': 'drsjob-456',
    'Status': 'LAUNCHING',  # Dynamic, updated by poller
    'IsDrill': True,  # NEW - execution mode
    'LaunchTime': 1234567890,
    'LastPolledTime': 1234567900,  # NEW
    'PollAttempts': 5,  # NEW
    'InstanceId': None,  # NEW - populated when launched
    'LaunchedTime': None,  # NEW - when reached LAUNCHED status
    'PostLaunchActionsStatus': None,  # NEW - for RECOVERY mode only
    'PostLaunchActionsCompleted': None,  # NEW - timestamp when complete
    'TransitionHistory': [  # NEW - for debugging
        {'status': 'PENDING', 'timestamp': 1234567890},
        {'status': 'STARTED', 'timestamp': 1234567920},
        {'status': 'IN_PROGRESS', 'timestamp': 1234568000}
    ]
}
```

#### 2.3 Execution Mode Tracking

Add `ExecutionType` field to execution record:
```python
{
    'ExecutionId': 'exec-123',
    'PlanId': 'plan-456',
    'ExecutionType': 'DRILL',  # or 'RECOVERY'
    'Status': 'POLLING',
    'StartTime': 1234567890,
    'ExpectedDuration': 1200,  # 20 min for DRILL, 30 min for RECOVERY
    # ... rest of fields
}
```

### Phase 3: Polling Service

#### Option A: EventBridge + Lambda (RECOMMENDED)

**Pros**:
- Simple to implement
- Built-in scheduling
- Easy to debug
- Cost-effective

**Cons**:
- Fixed polling interval
- Separate Lambda to manage

**Implementation**:

1. Create EventBridge rule:
```yaml
# cfn/lambda-stack.yaml (add)
ExecutionPollerSchedule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub '${ProjectName}-execution-poller-${Environment}'
    Description: 'Polls DRS job status every 30 seconds'
    ScheduleExpression: 'rate(30 seconds)'
    State: ENABLED
    Targets:
      - Arn: !GetAtt ExecutionPollerFunction.Arn
        Id: ExecutionPollerTarget
```

2. Create unified poller Lambda:
```python
# lambda/execution_poller.py
def lambda_handler(event, context):
    """Unified poller for DRILL and RECOVERY executions"""
    
    # Query for executions in POLLING status
    response = execution_history_table.scan(
        FilterExpression=Attr('Status').eq('POLLING')
    )
    
    active_executions = response.get('Items', [])
    print(f"Found {len(active_executions)} active executions to poll")
    
    # Poll each execution (mode-aware)
    for execution in active_executions:
        execution_type = execution.get('ExecutionType', 'DRILL')
        print(f"Polling {execution_type} execution: {execution['ExecutionId']}")
        poll_execution_status(execution)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'polled': len(active_executions),
            'timestamp': int(time.time())
        })
    }

def poll_execution_status(execution: Dict):
    """Poll status for a single execution"""
    execution_id = execution['ExecutionId']
    plan_id = execution['PlanId']
    waves = execution.get('Waves', [])
    
    print(f"Polling execution {execution_id}")
    
    all_complete = True
    updated_waves = []
    
    for wave in waves:
        # Skip completed waves
        if wave.get('Status') in ['COMPLETED', 'FAILED']:
            updated_waves.append(wave)
            continue
        
        all_complete = False
        updated_wave = poll_wave_status(wave)
        updated_waves.append(updated_wave)
    
    # Update DynamoDB with latest status
    execution_history_table.update_item(
        Key={'ExecutionId': execution_id, 'PlanId': plan_id},
        UpdateExpression='SET Waves = :waves',
        ExpressionAttributeValues={':waves': updated_waves}
    )
    
    # Check if all waves complete
    if all_complete:
        finalize_execution(execution_id, plan_id, updated_waves)

def poll_wave_status(wave: Dict) -> Dict:
    """Unified polling for DRILL and RECOVERY modes"""
    region = wave.get('Region')
    servers = wave.get('Servers', [])
    execution_mode = wave.get('ExecutionMode', 'DRILL')
    is_recovery = (execution_mode == 'RECOVERY')
    
    drs_client = boto3.client('drs', region_name=region)
    
    updated_servers = []
    all_launched = True
    all_post_launch_complete = True if is_recovery else True  # Only check for RECOVERY
    
    for server in servers:
        job_id = server.get('RecoveryJobId')
        if not job_id:
            updated_servers.append(server)
            continue
        
        # Query DRS for job status
        try:
            job_response = drs_client.describe_jobs(
                filters={'jobIDs': [job_id]}
            )
            
            if job_response.get('items'):
                job = job_response['items'][0]
                job_status = job.get('status')
                
                # Update server with latest status
                updated_server = {**server}
                updated_server['Status'] = job_status
                updated_server['LastPolledTime'] = int(time.time())
                updated_server['PollAttempts'] = server.get('PollAttempts', 0) + 1
                
                # Extract instance ID if launched
                if job_status == 'COMPLETED':
                    launched_instances = job.get('participatingServers', [])
                    for instance in launched_instances:
                        if instance.get('sourceServerID') == server['SourceServerId']:
                            updated_server['InstanceId'] = instance.get('recoveryInstanceID')
                            updated_server['LaunchedTime'] = int(time.time())
                            updated_server['Status'] = 'LAUNCHED'
                            
                            # For RECOVERY mode: check post-launch actions
                            if is_recovery:
                                pla_status = instance.get('postLaunchActionsDeployment', {}).get('status')
                                updated_server['PostLaunchActionsStatus'] = pla_status
                                
                                if pla_status == 'COMPLETED':
                                    updated_server['PostLaunchActionsCompleted'] = int(time.time())
                                elif pla_status in ['IN_PROGRESS', 'NOT_STARTED']:
                                    all_post_launch_complete = False
                            
                            break
                
                updated_servers.append(updated_server)
                
                # Check completion criteria
                if updated_server['Status'] != 'LAUNCHED':
                    all_launched = False
                elif is_recovery and updated_server.get('PostLaunchActionsStatus') != 'COMPLETED':
                    all_post_launch_complete = False
                    
            else:
                updated_servers.append(server)
                all_launched = False
                
        except Exception as e:
            print(f"Error polling job {job_id}: {str(e)}")
            updated_servers.append(server)
            all_launched = False
    
    # Update wave status (mode-aware completion)
    updated_wave = {**wave}
    updated_wave['Servers'] = updated_servers
    
    # Wave is complete when:
    # - DRILL: all instances launched
    # - RECOVERY: all instances launched AND post-launch actions complete
    if all_launched and (not is_recovery or all_post_launch_complete):
        updated_wave['Status'] = 'COMPLETED'
        updated_wave['EndTime'] = int(time.time())
    
    return updated_wave

def finalize_execution(execution_id: str, plan_id: str, waves: List[Dict]):
    """Mark execution as complete"""
    
    # Check for failures
    has_failures = any(
        s.get('Status') == 'FAILED'
        for wave in waves
        for s in wave.get('Servers', [])
    )
    
    final_status = 'PARTIAL' if has_failures else 'COMPLETED'
    end_time = int(time.time())
    
    execution_history_table.update_item(
        Key={'ExecutionId': execution_id, 'PlanId': plan_id},
        UpdateExpression='SET #status = :status, EndTime = :endtime',
        ExpressionAttributeNames={'#status': 'Status'},
        ExpressionAttributeValues={
            ':status': final_status,
            ':endtime': end_time
        }
    )
    
    print(f"Execution {execution_id} finalized with status: {final_status}")
```

#### Option B: Step Functions Wait States

**Pros**:
- Native AWS orchestration
- Visual workflow
- Better error handling
- Built-in retry logic

**Cons**:
- More complex setup
- Higher cost for long-running executions
- Harder to debug

**Decision**: Use Option A (EventBridge) for simplicity and cost-effectiveness.

### Phase 4: Frontend Updates

#### 4.1 Extended Polling Duration

**File**: `frontend/src/pages/ExecutionDetailsPage.tsx`

```typescript
// BEFORE
const [pollingEnabled, setPollingEnabled] = useState(true);
const [countdown, setCountdown] = useState(15);

// Poll every 15 seconds

// AFTER
const [pollingEnabled, setPollingEnabled] = useState(true);
const [countdown, setCountdown] = useState(15);
const [elapsedTime, setElapsedTime] = useState(0);  // NEW
const EXPECTED_DURATION = 20 * 60;  // 20 minutes in seconds

// Add elapsed time tracker
useEffect(() => {
  if (!execution || execution.status !== 'in_progress') return;
  
  const timer = setInterval(() => {
    const elapsed = Math.floor(Date.now() / 1000) - execution.startTime;
    setElapsedTime(elapsed);
  }, 1000);
  
  return () => clearInterval(timer);
}, [execution]);

// Display progress indicator
<Box mb={2}>
  <Typography variant="body2" color="text.secondary">
    Elapsed: {formatDuration(elapsedTime)} / Expected: ~20 minutes
  </Typography>
  <LinearProgress 
    variant="determinate" 
    value={Math.min((elapsedTime / EXPECTED_DURATION) * 100, 100)} 
  />
</Box>
```

#### 4.2 Mode-Aware Status Display

Add execution mode awareness to status messages:

```typescript
const getStatusMessage = (
  status: string, 
  elapsedTime: number, 
  executionType: 'DRILL' | 'RECOVERY'
): string => {
  const isDrill = executionType === 'DRILL';
  const expectedDuration = isDrill ? 20 : 30; // minutes
  
  switch (status) {
    case 'PENDING':
      return `Initializing ${isDrill ? 'drill' : 'production recovery'}...`;
      
    case 'IN_PROGRESS':
      if (elapsedTime < 60) {
        return `Starting DRS ${isDrill ? 'drill' : 'recovery'} jobs...`;
      } else if (elapsedTime < 300) {
        return 'DRS jobs queued, waiting for AWS processing...';
      } else if (elapsedTime < 900) {
        return 'DRS creating recovery snapshots (10-15 minutes)...';
      } else if (elapsedTime < 1200) {
        return 'DRS launching recovery instances...';
      } else if (!isDrill && elapsedTime < 1800) {
        return 'Running post-launch health checks (SSM)...';
      } else {
        return 'Finalizing launch...';
      }
      
    case 'POLLING':
      if (!isDrill && elapsedTime > 1200) {
        return 'Monitoring post-launch actions...';
      }
      return 'Jobs initiated, monitoring progress...';
      
    case 'COMPLETED':
      return isDrill 
        ? 'Drill completed successfully! Instances will auto-terminate.' 
        : 'Production recovery completed! Instances are running.';
        
    case 'PARTIAL':
      return 'Some instances failed - review details below';
      
    case 'FAILED':
      return `${isDrill ? 'Drill' : 'Recovery'} execution failed`;
      
    default:
      return status;
  }
};

// Update progress bar calculation
const calculateProgress = (elapsedTime: number, executionType: string): number => {
  const expectedDuration = executionType === 'DRILL' ? 1200 : 1800; // 20 or 30 min
  return Math.min((elapsedTime / expectedDuration) * 100, 100);
};
```

#### 4.3 Mode Indicator Badge

Add visual indicator for execution mode:

```typescript
<Box display="flex" alignItems="center" gap={1} mb={2}>
  <Chip 
    label={execution.executionType || 'DRILL'}
    color={execution.executionType === 'RECOVERY' ? 'error' : 'primary'}
    size="small"
    icon={execution.executionType === 'RECOVERY' ? <WarningIcon /> : <TestIcon />}
  />
  <Typography variant="body2" color="text.secondary">
    Expected duration: ~{execution.executionType === 'RECOVERY' ? '30' : '20'} minutes
  </Typography>
</Box>
```

### Phase 5: Monitoring & Observability

#### 5.1 CloudWatch Metrics

Add custom metrics:

```python
cloudwatch = boto3.client('cloudwatch')

def record_execution_metrics(execution_id: str, metrics: Dict):
    """Record execution metrics to CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='DRS-Orchestration',
        MetricData=[
            {
                'MetricName': 'ExecutionDuration',
                'Value': metrics['duration'],
                'Unit': 'Seconds',
                'Dimensions': [
                    {'Name': 'ExecutionId', 'Value': execution_id},
                    {'Name': 'Status', 'Value': metrics['status']}
                ]
            },
            {
                'MetricName': 'ServerLaunchSuccess',
                'Value': metrics['success_count'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'ServerLaunchFailure',
                'Value': metrics['failure_count'],
                'Unit': 'Count'
            }
        ]
    )
```

#### 5.2 Execution Timeline Logging

```python
def log_execution_timeline(execution_id: str, event: str):
    """Log execution timeline for debugging"""
    print(json.dumps({
        'executionId': execution_id,
        'event': event,
        'timestamp': int(time.time()),
        'timestampISO': datetime.utcnow().isoformat()
    }))
```

### Phase 6: Testing Strategy

#### 6.1 Unit Tests

```python
# tests/test_execution_poller.py
def test_poll_wave_status_all_launched():
    """Test wave polling when all servers launched"""
    wave = create_test_wave_with_jobs()
    
    # Mock DRS response
    mock_drs_response = {
        'items': [{
            'jobID': 'drsjob-123',
            'status': 'COMPLETED',
            'participatingServers': [{
                'sourceServerID': 's-123',
                'recoveryInstanceID': 'i-abc123'
            }]
        }]
    }
    
    with mock.patch('boto3.client') as mock_client:
        mock_client.return_value.describe_jobs.return_value = mock_drs_response
        
        updated_wave = poll_wave_status(wave)
        
        assert updated_wave['Status'] == 'COMPLETED'
        assert updated_wave['Servers'][0]['Status'] == 'LAUNCHED'
        assert updated_wave['Servers'][0]['InstanceId'] == 'i-abc123'
```

#### 6.2 Integration Tests

```bash
# Test full workflow
./tests/integration/test_drill_execution.sh
```

#### 6.3 Load Tests

```python
# Simulate 10 concurrent executions
for i in range(10):
    start_execution(f"test-plan-{i}")
    
# Monitor poller performance
time.sleep(600)  # Wait 10 minutes
verify_all_executions_complete()
```

## Deployment Plan

### Step 1: Backup Current System
```bash
# Export current Lambda code
aws lambda get-function --function-name drs-orchestration-api-handler-prod \
  --query 'Code.Location' --output text | xargs wget -O lambda-backup.zip

# Export DynamoDB tables
aws dynamodb scan --table-name ExecutionHistory-prod > backup-executions.json
```

### Step 2: Deploy Lambda Changes
```bash
# Update Lambda code
cd lambda
zip -r api-handler.zip index.py
aws s3 cp api-handler.zip s3://deployment-bucket/lambda/

# Update function
aws lambda update-function-code \
  --function-name drs-orchestration-api-handler-prod \
  --s3-bucket deployment-bucket \
  --s3-key lambda/api-handler.zip
```

### Step 3: Deploy Poller Lambda
```bash
# Create poller package
cd lambda
zip -r execution-poller.zip execution_poller.py
aws s3 cp execution-poller.zip s3://deployment-bucket/lambda/

# Deploy poller stack
aws cloudformation update-stack \
  --stack-name drs-orchestration-poller-prod \
  --template-body file://cfn/poller-stack.yaml \
  --parameters ParameterKey=SourceBucket,ParameterValue=deployment-bucket
```

### Step 4: Deploy Frontend Changes
```bash
cd frontend
npm run build
aws s3 sync dist/ s3://frontend-bucket/ --delete
aws cloudfront create-invalidation --distribution-id E123456 --paths "/*"
```

### Step 5: Verification
```bash
# Start a test drill
curl -X POST https://api.example.com/executions \
  -d '{"PlanId": "test-plan", "ExecutionType": "DRILL"}'

# Monitor for 25 minutes
for i in {1..100}; do
  curl https://api.example.com/executions/${EXECUTION_ID}
  sleep 15
done
```

## Success Criteria

- [ ] Lambda worker completes in < 2 minutes
- [ ] Poller successfully tracks jobs for 20+ minutes
- [ ] All servers reach LAUNCHED status
- [ ] Frontend displays accurate progress
- [ ] No Lambda timeouts in CloudWatch Logs
- [ ] Execution marked COMPLETED when all servers launched

## Rollback Plan

If issues occur:

```bash
# Rollback Lambda
aws lambda update-function-code \
  --function-name drs-orchestration-api-handler-prod \
  --s3-bucket deployment-bucket \
  --s3-key lambda/api-handler-backup.zip

# Disable poller
aws events disable-rule --name drs-orchestration-execution-poller-prod

# Rollback frontend
aws s3 sync s3://frontend-bucket-backup/ s3://frontend-bucket/ --delete
```

## Future Enhancements

1. **Adaptive Polling**: Increase frequency during critical phases
2. **Predictive Timing**: ML model to predict completion time
3. **Multi-Region Support**: Parallel polling across regions
4. **Status Webhooks**: Push notifications via SNS
5. **Execution Pausing**: Allow manual pause/resume

## Appendix A: API Response Changes

### Before
```json
{
  "executionId": "abc-123",
  "status": "COMPLETED",  // Premature
  "waves": [{
    "status": "COMPLETED",  // Wrong
    "servers": [{
      "status": "LAUNCHING",  // Never updated
      "instanceId": null  // Never populated
    }]
  }]
}
```

### After
```json
{
  "executionId": "abc-123",
  "status": "POLLING",  // Accurate
  "waves": [{
    "status": "LAUNCHING",  // Accurate
    "servers": [{
      "status": "IN_PROGRESS",  // Updated by poller
      "instanceId": "i-abc123",  // Populated when ready
      "lastPolledTime": 1234567900,
      "pollAttempts": 15
    }]
  }]
}
```

## Appendix B: Timing Breakdown

Based on successful drill walkthrough:

```
T+0:00   - User initiates drill
T+0:01   - Lambda starts DRS job (immediate)
T+0:02   - Lambda returns 202 Accepted
T+0:02   - Frontend starts polling (15s intervals)
T+0:30   - Poller checks status: PENDING
T+1:00   - Poller checks status: PENDING
T+2:00   - Poller checks status: PENDING
...
T+13:28  - Poller checks status: STARTED (transition!)
T+14:00  - Poller checks status: IN_PROGRESS
T+15:00  - Poller checks status: IN_PROGRESS
...
T+19:44  - Poller checks status: COMPLETED
T+19:45  - Poller extracts instance ID
T+20:00  - Frontend shows: LAUNCHED ✓
```

## Conclusion

This implementation plan addresses the root cause of DRS execution failures by:
1. Removing synchronous waiting from Lambda workers
2. Implementing dedicated polling service
3. Extending frontend polling duration
4. Tracking detailed job status transitions

Expected outcome: 100% success rate for DRS drills with accurate status reporting throughout the 20-minute execution window.

---
**Document Version**: 1.0  
**Last Updated**: 2025-11-28  
**Status**: Ready for Implementation
