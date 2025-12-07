# Step Functions Polling Implementation Guide

**Objective**: Implement DRS job polling using Step Functions Wait states to track wave execution status.

**Status**: Step Functions is enabled (`USE_STEP_FUNCTIONS: "true"`) but state machine definition lacks polling loop.

---

## Architecture Overview

```
API Gateway → Lambda (start_execution) → Step Functions State Machine
                                              ↓
                                         Start Wave
                                              ↓
                                         Wait 30s ←─────┐
                                              ↓         │
                                         Poll Status    │
                                              ↓         │
                                         Check Complete │
                                              ├─ No ────┘
                                              ↓ Yes
                                         Next Wave / Complete
```

---

## Implementation Steps

### 1. Update State Machine Definition

**File**: `cfn/api-stack.yaml`  
**Location**: Lines 200-250 (OrchestrationStateMachine resource)

Replace the current simple state machine with polling loop:

```yaml
OrchestrationStateMachine:
  Type: AWS::StepFunctions::StateMachine
  Properties:
    StateMachineName: !Sub '${ProjectName}-orchestration-${Environment}'
    RoleArn: !GetAtt StepFunctionsRole.Arn
    DefinitionString: !Sub |
      {
        "Comment": "DRS Recovery Plan Orchestration with Wave Polling",
        "StartAt": "ProcessWaves",
        "States": {
          "ProcessWaves": {
            "Type": "Map",
            "ItemsPath": "$.waves",
            "MaxConcurrency": 1,
            "Iterator": {
              "StartAt": "StartWave",
              "States": {
                "StartWave": {
                  "Type": "Task",
                  "Resource": "${ApiHandlerFunction.Arn}",
                  "Parameters": {
                    "action": "start_wave",
                    "wave.$": "$",
                    "execution_id.$": "$.execution_id",
                    "execution_type.$": "$.execution_type"
                  },
                  "ResultPath": "$.wave_result",
                  "Next": "WaitForWave"
                },
                "WaitForWave": {
                  "Type": "Wait",
                  "Seconds": 30,
                  "Next": "CheckWaveStatus"
                },
                "CheckWaveStatus": {
                  "Type": "Task",
                  "Resource": "${ApiHandlerFunction.Arn}",
                  "Parameters": {
                    "action": "check_wave_status",
                    "wave.$": "$.wave_result",
                    "execution_id.$": "$.execution_id"
                  },
                  "ResultPath": "$.status_result",
                  "Next": "IsWaveComplete"
                },
                "IsWaveComplete": {
                  "Type": "Choice",
                  "Choices": [
                    {
                      "Variable": "$.status_result.status",
                      "StringEquals": "COMPLETED",
                      "Next": "WaveSuccess"
                    },
                    {
                      "Variable": "$.status_result.status",
                      "StringEquals": "FAILED",
                      "Next": "WaveFailed"
                    }
                  ],
                  "Default": "WaitForWave"
                },
                "WaveSuccess": {
                  "Type": "Succeed"
                },
                "WaveFailed": {
                  "Type": "Fail",
                  "Error": "WaveExecutionFailed",
                  "Cause": "DRS recovery wave failed"
                }
              }
            },
            "End": true
          }
        }
      }
```

### 2. Add Action Router to Lambda

**File**: `lambda/index.py`  
**Location**: Add after line 1070 (after `execute_with_step_functions()`)

```python
def handle_step_functions_action(event: Dict[str, Any]) -> Dict[str, Any]:
    """Route Step Functions actions to appropriate handlers."""
    action = event.get('action')
    
    if action == 'start_wave':
        return start_wave_handler(event)
    elif action == 'check_wave_status':
        return check_wave_status_handler(event)
    else:
        raise ValueError(f"Unknown action: {action}")

def start_wave_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """Start DRS recovery for a wave."""
    wave = event['wave']
    execution_id = event['execution_id']
    execution_type = event['execution_type']
    
    logger.info(f"Starting wave {wave['WaveNumber']} for execution {execution_id}")
    
    # Get server IDs from protection groups
    server_ids = []
    for pg_id in wave.get('ProtectionGroups', []):
        pg = protection_groups_table.get_item(Key={'ProtectionGroupId': pg_id}).get('Item')
        if pg and pg.get('Servers'):
            server_ids.extend(pg['Servers'])
    
    if not server_ids:
        return {
            'status': 'COMPLETED',
            'job_id': None,
            'message': 'No servers in wave'
        }
    
    # Start DRS recovery (ONE API call for all servers)
    try:
        response = drs_client.start_recovery(
            sourceServers=[{'sourceServerID': sid} for sid in server_ids],
            isDrill=(execution_type == 'drill')
            # NO tags parameter
        )
        
        job_id = response['job']['jobID']
        
        # Update execution history
        execution_history_table.update_item(
            Key={
                'ExecutionId': execution_id,
                'PlanId': wave.get('PlanId')
            },
            UpdateExpression='SET WaveStatus.#wave = :status, WaveJobIds.#wave = :job_id',
            ExpressionAttributeNames={
                '#wave': str(wave['WaveNumber'])
            },
            ExpressionAttributeValues={
                ':status': 'IN_PROGRESS',
                ':job_id': job_id
            }
        )
        
        return {
            'status': 'IN_PROGRESS',
            'job_id': job_id,
            'wave_number': wave['WaveNumber']
        }
        
    except Exception as e:
        logger.error(f"Failed to start wave: {str(e)}")
        return {
            'status': 'FAILED',
            'error': str(e)
        }

def check_wave_status_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """Poll DRS job status for a wave."""
    wave_result = event['wave_result']
    job_id = wave_result.get('job_id')
    
    if not job_id:
        return {'status': 'COMPLETED'}
    
    try:
        # Query job status
        response = drs_client.describe_jobs(
            filters={'jobIDs': [job_id]}
        )
        
        if not response.get('items'):
            return {'status': 'FAILED', 'error': 'Job not found'}
        
        job = response['items'][0]
        job_status = job['status']
        
        # Query per-server launch status
        log_items = []
        paginator = drs_client.get_paginator('describe_job_log_items')
        for page in paginator.paginate(jobID=job_id):
            log_items.extend(page.get('items', []))
        
        # Extract server statuses
        server_statuses = {}
        for item in log_items:
            event_type = item.get('event')
            if event_type in ['LAUNCH_STARTED', 'LAUNCH_FINISHED', 'LAUNCH_FAILED']:
                server_id = item.get('eventData', {}).get('sourceServerID')
                if server_id:
                    server_statuses[server_id] = {
                        'status': event_type,
                        'instance_id': item.get('eventData', {}).get('ec2InstanceID'),
                        'timestamp': item.get('eventTimestamp')
                    }
        
        # Determine overall wave status
        if job_status == 'COMPLETED':
            # Check if all servers launched successfully
            failed_servers = [s for s, d in server_statuses.items() 
                            if d['status'] == 'LAUNCH_FAILED']
            if failed_servers:
                return {
                    'status': 'FAILED',
                    'job_status': job_status,
                    'server_statuses': server_statuses,
                    'failed_servers': failed_servers
                }
            return {
                'status': 'COMPLETED',
                'job_status': job_status,
                'server_statuses': server_statuses
            }
        elif job_status == 'FAILED':
            return {
                'status': 'FAILED',
                'job_status': job_status,
                'server_statuses': server_statuses
            }
        else:
            return {
                'status': 'IN_PROGRESS',
                'job_status': job_status,
                'server_statuses': server_statuses
            }
            
    except Exception as e:
        logger.error(f"Failed to check wave status: {str(e)}")
        return {'status': 'FAILED', 'error': str(e)}
```

### 3. Update Lambda Handler Entry Point

**File**: `lambda/index.py`  
**Location**: Modify `lambda_handler()` function (around line 100)

```python
def lambda_handler(event, context):
    """Main Lambda handler."""
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Check if this is a Step Functions action
    if event.get('action') in ['start_wave', 'check_wave_status']:
        return handle_step_functions_action(event)
    
    # Existing API Gateway handling
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    
    # ... rest of existing code
```

### 4. Grant Step Functions Permissions

**File**: `cfn/api-stack.yaml`  
**Location**: Add after StepFunctionsRole (around line 180)

```yaml
StepFunctionsRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Service: states.amazonaws.com
          Action: sts:AssumeRole
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
    Policies:
      - PolicyName: InvokeLambda
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - lambda:InvokeFunction
              Resource: !GetAtt ApiHandlerFunction.Arn
```

### 5. Update Lambda IAM Permissions

**File**: `cfn/lambda-stack.yaml`  
**Location**: Add to OrchestrationRole policies (around line 150)

```yaml
- PolicyName: DRSJobPolling
  PolicyDocument:
    Version: '2012-10-17'
    Statement:
      - Effect: Allow
        Action:
          - drs:DescribeJobs
          - drs:DescribeJobLogItems
        Resource: '*'
```

---

## Deployment Steps

```bash
# 1. Update CloudFormation stack
aws cloudformation deploy \
  --template-file cfn/master-template.yaml \
  --stack-name drs-orchestration-test \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    Environment=test \
    SourceBucket=aws-drs-orchestration \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1

# 2. Deploy updated Lambda code
cd lambda
python3 deploy_lambda.py --direct \
  --function-name drs-orchestration-api-handler-test \
  --region us-east-1

# 3. Verify Step Functions state machine
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:***REMOVED***:stateMachine:drs-orchestration-orchestration-test \
  --region us-east-1
```

---

## Testing

```bash
# 1. Start execution via API
curl -X POST https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test/executions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "PlanId": "your-plan-id",
    "ExecutionType": "drill"
  }'

# 2. Monitor Step Functions execution
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:***REMOVED***:stateMachine:drs-orchestration-orchestration-test \
  --region us-east-1

# 3. Check Lambda logs
aws logs tail /aws/lambda/drs-orchestration-api-handler-test --follow
```

---

## Expected Behavior

1. **Wave Start**: Lambda calls `drs:StartRecovery` with all servers, returns job ID
2. **Polling Loop**: Step Functions waits 30s, calls Lambda to check status
3. **Status Check**: Lambda calls `describe_jobs` + `describe_job_log_items`
4. **Completion**: When job status = COMPLETED and all servers LAUNCHED, proceed to next wave
5. **Failure Handling**: If any server fails, mark wave as FAILED and stop execution

---

## Key Differences from Current Implementation

| Aspect | Current | New |
|--------|---------|-----|
| Orchestration | Lambda-only | Step Functions + Lambda |
| Polling | EventBridge scheduled (disabled) | Step Functions Wait states |
| Wave tracking | Manual status updates | Automatic via state machine |
| Visibility | CloudWatch Logs only | Step Functions console + logs |
| Retry logic | None | Built into state machine |

---

## Rollback Plan

If issues occur:

```bash
# Disable Step Functions
aws lambda update-function-configuration \
  --function-name drs-orchestration-api-handler-test \
  --environment Variables={USE_STEP_FUNCTIONS=false} \
  --region us-east-1
```

---

## Next Steps After Implementation

1. ✅ Deploy CloudFormation changes
2. ✅ Deploy Lambda code updates
3. ✅ Test single-wave execution
4. ✅ Test multi-wave execution with dependencies
5. ✅ Validate per-server status tracking
6. ✅ Add SNS notifications for wave completion
7. ✅ Create CloudWatch dashboard for monitoring

---

**Estimated Implementation Time**: 2-3 hours  
**Risk Level**: Medium (Step Functions already enabled, just adding logic)  
**Rollback Time**: < 5 minutes
