# Multi-Wave Execution Lifecycle Fix - Design

## Executive Summary

This design consolidates execution-finder and execution-poller into execution-handler, fixes premature execution finalization, and adds real-time server data enrichment. The solution centralizes execution lifecycle management in a single Lambda function while ensuring Step Functions controls when executions complete.

**Key Changes**:
- Consolidate 3 Lambdas → 1 execution-handler with operation routing
- Remove finalization logic from polling operations
- Add DRS + EC2 data enrichment during polling
- Update CloudFormation templates for simplified architecture

## Architecture Overview

### Current Architecture (Broken)

```
Step Functions
    ↓
execution-handler (create execution)
    ↓
DynamoDB (wave 1 created)
    ↓
execution-finder (finds POLLING executions)
    ↓
execution-poller (polls DRS, sees wave 1 complete)
    ↓
finalize_execution() ← BUG: Marks COMPLETED prematurely
    ↓
Step Functions still RUNNING (waves 2, 3 pending)
```

### New Architecture (Fixed)

```
Step Functions
    ↓
execution-handler (operation: "create")
    ↓
DynamoDB (wave 1 created)
    ↓
execution-handler (operation: "poll")
    ├─ Query DRS job status
    ├─ Query EC2 instance details
    ├─ Normalize and enrich data
    └─ Update wave status only (no finalization)
    ↓
Step Functions (checks all waves complete)
    ↓
execution-handler (operation: "finalize")
    ↓
DynamoDB (status: COMPLETED)
```

## Component Design

### 1. Consolidated Execution Handler

**File**: `lambda/execution-handler/index.py`

**Operation Routing**:
```python
def lambda_handler(event, context):
    """
    Unified execution handler with operation-based routing.
    
    Supported operations:
    - create: Create new execution
    - find: Find executions by status
    - poll: Poll DRS job status and enrich data
    - update: Update execution fields
    - finalize: Mark execution complete
    - pause: Pause execution between waves
    - resume: Resume paused execution
    """
    operation = event.get('operation')
    
    if operation == 'create':
        return handle_create(event)
    elif operation == 'find':
        return handle_find(event)
    elif operation == 'poll':
        return handle_poll(event)
    elif operation == 'update':
        return handle_update(event)
    elif operation == 'finalize':
        return handle_finalize(event)
    elif operation == 'pause':
        return handle_pause(event)
    elif operation == 'resume':
        return handle_resume(event)
    else:
        raise ValueError(f"Unknown operation: {operation}")
```

**Key Functions**:

#### `handle_poll(event)` - Core Polling Logic
```python
def handle_poll(event):
    """
    Poll DRS job status and enrich server data.
    
    Steps:
    1. Get execution from DynamoDB
    2. Query DRS for job status
    3. Query EC2 for instance details
    4. Normalize and combine data
    5. Update wave status in DynamoDB
    6. Update lastPolledTime
    7. Return wave status (NOT execution status)
    
    CRITICAL: Never calls finalize_execution()
    """
    execution_id = event['executionId']
    
    # Get execution record
    execution = get_execution(execution_id)
    
    # Get active waves
    active_waves = [w for w in execution['waves'] if w['status'] == 'POLLING']
    
    for wave in active_waves:
        # Query DRS job status
        job_details = get_drs_job_details(wave['jobId'])
        
        # Enrich server data with EC2 details
        enriched_servers = enrich_server_data(
            job_details['participatingServers']
        )
        
        # Update wave status
        update_wave_status(
            execution_id=execution_id,
            wave_number=wave['waveNumber'],
            status=job_details['status'],
            servers=enriched_servers
        )
        
        # Update last polled time
        update_last_polled_time(execution_id)
    
    # Return wave statuses (Step Functions decides if complete)
    return {
        'executionId': execution_id,
        'waves': execution['waves'],
        'allWavesComplete': all(w['status'] == 'COMPLETED' for w in execution['waves'])
    }
```

#### `handle_finalize(event)` - Execution Finalization
```python
def handle_finalize(event):
    """
    Finalize execution when all waves complete.
    
    Called ONLY by Step Functions after verifying all waves complete.
    Idempotent - safe to call multiple times.
    """
    execution_id = event['executionId']
    
    # Get execution record
    execution = get_execution(execution_id)
    
    # Verify all waves complete (safety check)
    if not all(w['status'] == 'COMPLETED' for w in execution['waves']):
        raise ValueError("Cannot finalize: not all waves complete")
    
    # Update execution status
    update_execution_status(
        execution_id=execution_id,
        status='COMPLETED',
        completed_time=int(time.time())
    )
    
    # Send completion notification
    send_notification(
        execution_id=execution_id,
        status='COMPLETED',
        message=f"All {len(execution['waves'])} waves completed successfully"
    )
    
    return {
        'executionId': execution_id,
        'status': 'COMPLETED',
        'totalWaves': len(execution['waves'])
    }
```

### 2. Server Data Enrichment

**File**: `lambda/shared/drs_utils.py` (enhancements)

#### New Function: `enrich_server_data()`
```python
def enrich_server_data(
    participating_servers: List[Dict],
    drs_client,
    ec2_client
) -> List[Dict]:
    """
    Enrich server data with DRS and EC2 details.
    
    For each server:
    1. Normalize DRS fields (sourceServerId, launchStatus, etc.)
    2. Query EC2 for instance details if instanceId available
    3. Extract: privateIp, hostname, instanceType
    4. Combine into normalized server dict
    
    Args:
        participating_servers: List of DRS ParticipatingServer objects
        drs_client: boto3 DRS client
        ec2_client: boto3 EC2 client
        
    Returns:
        List of enriched server dicts
    """
    enriched = []
    
    # Collect instance IDs for batch query
    instance_ids = [
        s.get('recoveryInstanceID') 
        for s in participating_servers 
        if s.get('recoveryInstanceID')
    ]
    
    # Batch query EC2 instances
    ec2_instances = {}
    if instance_ids:
        ec2_instances = batch_describe_ec2_instances(instance_ids, ec2_client)
    
    # Enrich each server
    for server in participating_servers:
        # Normalize DRS fields
        normalized = normalize_drs_response(server)
        
        # Add EC2 details if available
        instance_id = normalized.get('recoveryInstanceId')
        if instance_id and instance_id in ec2_instances:
            ec2_data = ec2_instances[instance_id]
            normalized.update({
                'instanceId': ec2_data.get('instanceId', ''),
                'privateIp': ec2_data.get('privateIpAddress', ''),
                'hostname': ec2_data.get('privateDnsName', ''),
                'instanceType': ec2_data.get('instanceType', ''),
                'instanceState': ec2_data.get('state', {}).get('name', '')
            })
        
        enriched.append(normalized)
    
    return enriched
```

#### New Function: `batch_describe_ec2_instances()`
```python
def batch_describe_ec2_instances(
    instance_ids: List[str],
    ec2_client
) -> Dict[str, Dict]:
    """
    Query multiple EC2 instances efficiently.
    
    Returns dict mapping instanceId -> instance details.
    Handles pagination and throttling.
    
    Args:
        instance_ids: List of EC2 instance IDs
        ec2_client: boto3 EC2 client
        
    Returns:
        Dict mapping instanceId to normalized instance details
    """
    if not instance_ids:
        return {}
    
    instances = {}
    
    try:
        response = ec2_client.describe_instances(
            InstanceIds=instance_ids
        )
        
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_id = instance['InstanceId']
                instances[instance_id] = {
                    'instanceId': instance_id,
                    'instanceType': instance.get('InstanceType', ''),
                    'privateIpAddress': instance.get('PrivateIpAddress', ''),
                    'privateDnsName': instance.get('PrivateDnsName', ''),
                    'state': instance.get('State', {}),
                    'launchTime': instance.get('LaunchTime')
                }
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidInstanceID.NotFound':
            # Some instances not yet available - return partial results
            logger.warning(f"Some instances not found: {e}")
        else:
            raise
    
    return instances
```

### 3. Step Functions State Machine Updates

**File**: `cfn/step-functions-stack.yaml`

**Key State Changes**:

```yaml
# Create Wave State
CreateWave:
  Type: Task
  Resource: !GetAtt ExecutionHandlerFunction.Arn
  Parameters:
    operation: create
    executionId.$: $.executionId
    wave.$: $.currentWave
  Next: PollWaveStatus

# Poll Wave Status State
PollWaveStatus:
  Type: Task
  Resource: !GetAtt ExecutionHandlerFunction.Arn
  Parameters:
    operation: poll
    executionId.$: $.executionId
  Next: CheckWaveComplete
  Retry:
    - ErrorEquals: [States.ALL]
      IntervalSeconds: 30
      MaxAttempts: 3
      BackoffRate: 2.0

# Check Wave Complete State
CheckWaveComplete:
  Type: Choice
  Choices:
    - Variable: $.allWavesComplete
      BooleanEquals: true
      Next: FinalizeExecution
    - Variable: $.currentWave.pauseBeforeNext
      BooleanEquals: true
      Next: PauseExecution
  Default: WaitBeforeNextPoll

# Wait Before Next Poll
WaitBeforeNextPoll:
  Type: Wait
  Seconds: 30
  Next: PollWaveStatus

# Finalize Execution State
FinalizeExecution:
  Type: Task
  Resource: !GetAtt ExecutionHandlerFunction.Arn
  Parameters:
    operation: finalize
    executionId.$: $.executionId
  End: true

# Pause Execution State
PauseExecution:
  Type: Task
  Resource: !GetAtt ExecutionHandlerFunction.Arn
  Parameters:
    operation: pause
    executionId.$: $.executionId
  Next: WaitForResume

# Wait For Resume State
WaitForResume:
  Type: Task
  Resource: arn:aws:states:::lambda:invoke.waitForTaskToken
  Parameters:
    FunctionName: !GetAtt ExecutionHandlerFunction.Arn
    Payload:
      operation: waitForResume
      executionId.$: $.executionId
      taskToken.$: $$.Task.Token
  Next: CreateWave
```

### 4. CloudFormation Template Updates

#### Lambda Stack Changes

**File**: `cfn/lambda-stack.yaml`

```yaml
# Remove these resources:
# - ExecutionFinderFunction
# - ExecutionPollerFunction
# - ExecutionFinderLogGroup
# - ExecutionPollerLogGroup

# Update ExecutionHandlerFunction
ExecutionHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub ${EnvironmentName}-execution-handler
    Runtime: python3.11
    Handler: index.lambda_handler
    Timeout: 900  # 15 minutes (increased for polling operations)
    MemorySize: 512  # Increased for EC2 queries
    Environment:
      Variables:
        DYNAMODB_TABLE: !Ref ExecutionTable
        ENVIRONMENT: !Ref EnvironmentName
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref ExecutionTable
      - Statement:
          - Effect: Allow
            Action:
              - drs:DescribeRecoveryInstances
              - drs:DescribeJobs
              - drs:DescribeSourceServers
            Resource: '*'
          - Effect: Allow
            Action:
              - ec2:DescribeInstances
              - ec2:DescribeTags
            Resource: '*'
          - Effect: Allow
            Action:
              - sns:Publish
            Resource: !Ref NotificationTopic

# Remove these outputs:
# - ExecutionFinderFunctionArn
# - ExecutionPollerFunctionArn
```

#### EventBridge Stack Changes

**File**: `cfn/eventbridge-stack.yaml`

```yaml
# Update polling rule to call execution-handler
ExecutionPollingRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub ${EnvironmentName}-execution-polling
    Description: Poll active executions every 30 seconds
    ScheduleExpression: rate(30 seconds)
    State: ENABLED
    Targets:
      - Arn: !GetAtt ExecutionHandlerFunction.Arn  # Changed from ExecutionPollerFunction
        Id: ExecutionHandler
        Input: |
          {
            "operation": "find",
            "status": "POLLING"
          }
```

## Data Flow

### Polling Cycle with Enrichment

```
1. EventBridge triggers execution-handler (operation: "find")
   ↓
2. execution-handler finds executions with status=POLLING
   ↓
3. For each execution, call execution-handler (operation: "poll")
   ↓
4. Query DRS: DescribeRecoveryInstances
   - Get: sourceServerId, launchStatus, launchTime, recoveryInstanceId
   ↓
5. Extract instance IDs from DRS response
   ↓
6. Query EC2: DescribeInstances (batch)
   - Get: privateIp, hostname, instanceType, state
   ↓
7. Normalize DRS fields (PascalCase → camelCase)
   ↓
8. Combine DRS + EC2 data
   ↓
9. Update DynamoDB:
   - wave.status = job.status
   - wave.serverStatuses = enriched_servers
   - execution.lastPolledTime = now()
   ↓
10. Return wave statuses to Step Functions
    ↓
11. Step Functions checks if all waves complete
    ↓
12. If complete: call execution-handler (operation: "finalize")
```

### DynamoDB Schema

**Execution Record** (unchanged):
```json
{
  "executionId": "uuid",
  "status": "POLLING|PAUSED|COMPLETED|FAILED",
  "totalWaves": 3,
  "waves": [
    {
      "waveNumber": 0,
      "waveName": "DBWave1",
      "status": "COMPLETED",
      "jobId": "drs-job-123",
      "serverStatuses": [
        {
          "sourceServerId": "s-51b12197c9ad51796",
          "serverName": "WINDBSRV02",
          "launchStatus": "LAUNCHED",
          "launchTime": 1769370497,
          "instanceId": "i-0abc123def456",
          "privateIp": "10.0.1.50",
          "hostname": "ip-10-0-1-50.ec2.internal",
          "instanceType": "t3.medium",
          "instanceState": "running"
        }
      ]
    }
  ],
  "lastPolledTime": 1769370500,
  "createdTime": 1769370000,
  "completedTime": null
}
```

## API Contracts

### Execution Handler Input

```json
{
  "operation": "poll|create|find|update|finalize|pause|resume",
  "executionId": "uuid",
  "status": "POLLING",  // For find operation
  "wave": {},  // For create operation
  "taskToken": "token"  // For waitForResume operation
}
```

### Execution Handler Output

```json
{
  "executionId": "uuid",
  "status": "POLLING|COMPLETED",
  "waves": [
    {
      "waveNumber": 0,
      "status": "COMPLETED",
      "serverStatuses": [...]
    }
  ],
  "allWavesComplete": false
}
```

## Migration Strategy

### Phase 1: Add Consolidated Handler (No Breaking Changes)
1. Deploy execution-handler with all operations
2. Keep execution-finder and execution-poller running
3. Test execution-handler in parallel
4. Verify data enrichment works correctly

### Phase 2: Update Step Functions
1. Update Step Functions to call execution-handler
2. Add operation parameter to all task states
3. Deploy Step Functions changes
4. Monitor executions for 24 hours

### Phase 3: Remove Old Functions
1. Disable EventBridge rules for old functions
2. Monitor for 48 hours
3. Remove execution-finder and execution-poller from CloudFormation
4. Clean up IAM roles and log groups

## Error Handling

### Polling Errors
```python
def handle_poll(event):
    try:
        # Poll DRS and EC2
        ...
    except ClientError as e:
        if e.response['Error']['Code'] == 'ThrottlingException':
            # Retry with exponential backoff
            logger.warning("DRS API throttled, will retry")
            raise  # Let Step Functions retry
        elif e.response['Error']['Code'] == 'InvalidInstanceID.NotFound':
            # Some instances not yet available - continue with partial data
            logger.warning("Some EC2 instances not found yet")
            # Return partial results
        else:
            # Unexpected error - fail execution
            logger.error(f"Polling failed: {e}")
            raise
```

### Finalization Errors
```python
def handle_finalize(event):
    try:
        # Finalize execution
        ...
    except ConditionalCheckFailedException:
        # Already finalized - idempotent operation
        logger.info("Execution already finalized")
        return get_execution(event['executionId'])
    except Exception as e:
        # Finalization failed - retry
        logger.error(f"Finalization failed: {e}")
        raise
```

## Performance Considerations

### API Call Optimization
- **Batch EC2 Queries**: Query all instances in single API call
- **Caching**: Cache EC2 data for 60 seconds (in-memory)
- **Parallel Queries**: Query DRS and EC2 in parallel when possible
- **Adaptive Polling**: Increase interval when no changes detected

### DynamoDB Optimization
- **Conditional Writes**: Use conditional expressions to prevent race conditions
- **Batch Updates**: Update multiple waves in single transaction
- **Projection Expressions**: Only fetch required fields

### Lambda Optimization
- **Memory**: 512 MB (balance between cost and performance)
- **Timeout**: 15 minutes (handle long-running polls)
- **Concurrency**: Reserved concurrency = 10 (prevent throttling)

## Testing Strategy

### Unit Tests
```python
# test_execution_handler.py

def test_handle_poll_enriches_server_data():
    """Test polling enriches server data with EC2 details."""
    event = {
        'operation': 'poll',
        'executionId': 'test-123'
    }
    
    # Mock DRS and EC2 responses
    mock_drs_response = {...}
    mock_ec2_response = {...}
    
    result = lambda_handler(event, None)
    
    assert result['waves'][0]['serverStatuses'][0]['privateIp'] == '10.0.1.50'
    assert result['waves'][0]['serverStatuses'][0]['instanceType'] == 't3.medium'

def test_handle_poll_never_finalizes():
    """Test polling never changes execution status."""
    event = {
        'operation': 'poll',
        'executionId': 'test-123'
    }
    
    result = lambda_handler(event, None)
    
    # Verify execution status unchanged
    execution = get_execution('test-123')
    assert execution['status'] == 'POLLING'  # Not COMPLETED

def test_handle_finalize_requires_all_waves_complete():
    """Test finalization fails if waves incomplete."""
    event = {
        'operation': 'finalize',
        'executionId': 'test-123'
    }
    
    # Setup execution with incomplete waves
    create_execution_with_incomplete_waves('test-123')
    
    with pytest.raises(ValueError, match="not all waves complete"):
        lambda_handler(event, None)
```

### Integration Tests
```python
def test_multi_wave_execution_completes_all_waves():
    """Test 3-wave execution completes all waves."""
    # Start execution with 3 waves
    execution_id = start_execution(waves=3)
    
    # Wait for wave 1 to complete
    wait_for_wave_complete(execution_id, wave=0)
    
    # Verify execution still POLLING
    execution = get_execution(execution_id)
    assert execution['status'] == 'POLLING'
    
    # Wait for wave 2 to complete
    wait_for_wave_complete(execution_id, wave=1)
    assert execution['status'] == 'POLLING'
    
    # Wait for wave 3 to complete
    wait_for_wave_complete(execution_id, wave=2)
    
    # Verify execution now COMPLETED
    execution = get_execution(execution_id)
    assert execution['status'] == 'COMPLETED'
    assert len(execution['waves']) == 3
```

## Monitoring and Observability

### CloudWatch Metrics
```python
# Emit custom metrics
cloudwatch.put_metric_data(
    Namespace='DROrchestration',
    MetricData=[
        {
            'MetricName': 'PollingDuration',
            'Value': duration_ms,
            'Unit': 'Milliseconds'
        },
        {
            'MetricName': 'EC2EnrichmentCount',
            'Value': len(instance_ids),
            'Unit': 'Count'
        },
        {
            'MetricName': 'WaveCompletionTime',
            'Value': completion_time,
            'Unit': 'Seconds'
        }
    ]
)
```

### CloudWatch Logs
```python
# Structured logging
logger.info("Polling execution", extra={
    'executionId': execution_id,
    'waveNumber': wave_number,
    'serverCount': len(servers),
    'drsApiCalls': drs_call_count,
    'ec2ApiCalls': ec2_call_count,
    'duration': duration_ms
})
```

### Alarms
- **High Polling Duration**: Alert if polling takes >5 seconds
- **API Throttling**: Alert if DRS/EC2 throttling detected
- **Finalization Failures**: Alert if finalization fails
- **Stale Executions**: Alert if execution not polled in 5 minutes

## Security Considerations

### IAM Permissions
```yaml
ExecutionHandlerRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Statement:
        - Effect: Allow
          Principal:
            Service: lambda.amazonaws.com
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
    Policies:
      - PolicyName: DRSAccess
        PolicyDocument:
          Statement:
            - Effect: Allow
              Action:
                - drs:DescribeRecoveryInstances
                - drs:DescribeJobs
                - drs:DescribeSourceServers
              Resource: '*'
      - PolicyName: EC2ReadOnly
        PolicyDocument:
          Statement:
            - Effect: Allow
              Action:
                - ec2:DescribeInstances
                - ec2:DescribeTags
              Resource: '*'
      - PolicyName: DynamoDBAccess
        PolicyDocument:
          Statement:
            - Effect: Allow
              Action:
                - dynamodb:GetItem
                - dynamodb:PutItem
                - dynamodb:UpdateItem
                - dynamodb:Query
              Resource: !GetAtt ExecutionTable.Arn
```

### Data Protection
- **Encryption at Rest**: DynamoDB encryption enabled
- **Encryption in Transit**: TLS 1.2+ for all API calls
- **Sensitive Data**: No PII stored in execution records
- **Access Logging**: CloudTrail logs all API calls

## Rollback Plan

### If Deployment Fails
1. Revert CloudFormation stack to previous version
2. Old execution-finder and execution-poller still running
3. No data loss - DynamoDB schema unchanged
4. Investigate failure, fix, redeploy

### If Bugs Discovered Post-Deployment
1. Disable EventBridge rule for execution-handler
2. Re-enable rules for execution-finder and execution-poller
3. Monitor for 24 hours
4. Fix bugs in execution-handler
5. Redeploy and re-enable

## Success Criteria

### Functional
- ✅ Multi-wave executions complete all waves
- ✅ Execution status accurate throughout lifecycle
- ✅ Server data enriched with EC2 details
- ✅ No premature finalization
- ✅ Pause/resume works correctly

### Performance
- ✅ Polling completes in <5 seconds p95
- ✅ Finalization completes in <1 second p95
- ✅ EC2 API calls <10 per poll cycle
- ✅ DRS API calls <5 per poll cycle

### Operational
- ✅ Zero downtime during deployment
- ✅ CloudWatch logs show enrichment working
- ✅ No increase in Lambda errors
- ✅ Frontend displays enriched data

## References

- Requirements: #[[file:.kiro/specs/multi-wave-execution-fix/requirements.md]]
- DRS Utils: #[[file:infra/orchestration/drs-orchestration/lambda/shared/drs_utils.py]]
- Multi-Wave Bug Analysis: #[[file:.kiro/specs/missing-function-migration/MULTI_WAVE_BUG_ANALYSIS.md]]
- Normalization Bug Summary: #[[file:.kiro/specs/missing-function-migration/NORMALIZATION_BUG_SUMMARY.md]]
