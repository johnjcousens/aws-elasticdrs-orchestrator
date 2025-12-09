# SSM Automation Implementation Guide

## Overview

Add pre-wave and post-wave SSM automation document execution to DRS Orchestration, based on `archive/drs-tools/drs-plan-automation` reference implementation.

## Problem Statement

Current implementation lacks:
- Manual approval gates before wave execution
- Health checks after wave completion
- Custom automation hooks (scripts, patches, configuration)
- Pause/resume capability during execution

## Solution Architecture

### High-Level Flow

```
Wave Execution:
1. Execute Pre-Wave Actions (SSM Documents) → Poll until complete
2. Start DRS Recovery (existing) → Poll until servers launched
3. Execute Post-Wave Actions (SSM Documents) → Poll until complete
4. Move to next wave or complete
```

### State Machine Pattern

```
ProcessWave (Choice)
  ├─> ExecutePreWaveActions → Wait → CheckPreWaveAction → Loop
  ├─> StartDRSRecovery → Wait → CheckDRSJob → Loop
  └─> ExecutePostWaveActions → Wait → CheckPostWaveAction → Loop
```

## Implementation Plan

### Phase 1: Data Model Changes

#### Recovery Plan Schema

```python
# recovery-plans-{env} table
{
    'PlanId': 'plan-123',
    'Waves': [
        {
            'WaveNumber': 1,
            'ProtectionGroupIds': ['pg-abc'],
            'PreWaveActions': [
                {
                    'ActionName': 'Approval Gate',
                    'DocumentName': 'AWS-ApproveSSMDocument',
                    'Parameters': {
                        'Message': ['Approve database tier recovery'],
                        'Approvers': ['arn:aws:iam::123:user/admin']
                    },
                    'MaxWaitTime': 3600,
                    'UpdateTime': 30
                }
            ],
            'PostWaveActions': [
                {
                    'ActionName': 'Health Check',
                    'DocumentName': 'HealthCheckDocument',
                    'Parameters': {
                        'InstanceIds': ['{{RecoveredInstanceIds}}']
                    },
                    'MaxWaitTime': 600,
                    'UpdateTime': 15
                }
            ]
        }
    ]
}
```

#### Execution History Schema

```python
# execution-history-{env} table
{
    'ExecutionId': 'exec-456',
    'Waves': [
        {
            'WaveNumber': 1,
            'PreWaveActions': [
                {
                    'ActionName': 'Approval Gate',
                    'Status': 'completed',
                    'ExecutionId': 'ssm-exec-789',
                    'StartTime': 1234567890,
                    'EndTime': 1234567920
                }
            ],
            'DRS': {
                'Status': 'in_progress',
                'JobId': 'job-abc'
            },
            'PostWaveActions': [
                {
                    'ActionName': 'Health Check',
                    'Status': 'pending'
                }
            ]
        }
    ]
}
```

### Phase 2: Lambda Handler Updates

#### Add SSM Constants

```python
# lambda/orchestration_stepfunctions.py

AUTOMATION_EXECUTION_WAIT_STATES = [
    'Pending', 'InProgress', 'Waiting', 'Cancelling',
    'PendingApproval', 'Approved', 'Scheduled'
]

AUTOMATION_EXECUTION_COMPLETE_SUCCESS_STATES = [
    'Success', 'CompletedWithSuccess'
]

AUTOMATION_EXECUTION_COMPLETE_FAILURE_STATES = [
    'TimedOut', 'Cancelled', 'Failed', 'Rejected'
]
```

#### Add SSM Helper Functions

```python
def start_ssm_action(ssm_client, document_name, parameters):
    """Start SSM automation execution"""
    try:
        response = ssm_client.start_automation_execution(
            DocumentName=document_name,
            Parameters=parameters
        )
        return {
            'status': 'success',
            'execution_id': response['AutomationExecutionId']
        }
    except Exception as e:
        print(f"Error starting SSM automation: {e}")
        return {'status': 'failed', 'error': str(e)}


def check_ssm_action_status(ssm_client, execution_id):
    """Check SSM automation execution status"""
    try:
        response = ssm_client.describe_automation_executions(
            Filters=[{'Key': 'ExecutionId', 'Values': [execution_id]}]
        )
        
        if not response.get('AutomationExecutionMetadataList'):
            return {'status': 'failed', 'error': f'No execution found'}
        
        execution = response['AutomationExecutionMetadataList'][0]
        status = execution['AutomationExecutionStatus']
        
        if status in AUTOMATION_EXECUTION_COMPLETE_SUCCESS_STATES:
            return {'status': 'completed', 'result': execution}
        elif status in AUTOMATION_EXECUTION_COMPLETE_FAILURE_STATES:
            return {'status': 'failed', 'result': execution}
        else:
            return {'status': 'in_progress', 'result': execution}
            
    except Exception as e:
        print(f"Error checking SSM status: {e}")
        return {'status': 'failed', 'error': str(e)}
```

#### Add Action Handler Functions

```python
def handle_start_pre_wave_actions(event, context):
    """Start pre-wave SSM actions"""
    wave = event['wave']
    pre_actions = wave.get('preWaveActions', [])
    
    if not pre_actions:
        return {'wave': wave, 'preActionsCompleted': True}
    
    action = pre_actions[0]
    ssm_client = boto3.client('ssm', region_name=wave['region'])
    
    result = start_ssm_action(
        ssm_client,
        action['DocumentName'],
        action['Parameters']
    )
    
    if result['status'] == 'success':
        wave['currentActionIndex'] = 0
        wave['currentActionExecutionId'] = result['execution_id']
        wave['currentActionType'] = 'pre'
        wave['actionUpdateTime'] = action['UpdateTime']
        wave['actionMaxWaitTime'] = action['MaxWaitTime']
        wave['actionTotalWaitTime'] = 0
        wave['preActionsCompleted'] = False
        
        update_wave_action_status(
            wave['executionId'], wave['waveNumber'],
            'PreWaveActions', 0, 'in_progress', result['execution_id']
        )
    else:
        wave['status'] = 'failed'
        wave['error'] = result['error']
    
    return {'wave': wave, 'status': result['status']}


def handle_check_action_status(event, context):
    """Check SSM action status and advance if complete"""
    wave = event['wave']
    action_type = event['actionType']
    
    execution_id = wave['currentActionExecutionId']
    action_index = wave['currentActionIndex']
    
    ssm_client = boto3.client('ssm', region_name=wave['region'])
    result = check_ssm_action_status(ssm_client, execution_id)
    
    wave['actionTotalWaitTime'] += wave['actionUpdateTime']
    
    # Check timeout
    if wave['actionTotalWaitTime'] >= wave['actionMaxWaitTime']:
        wave['status'] = 'timeout'
        update_wave_action_status(
            wave['executionId'], wave['waveNumber'],
            f'{action_type.capitalize()}WaveActions',
            action_index, 'timeout', execution_id
        )
        return {'wave': wave, 'status': 'timeout'}
    
    # Check completion
    if result['status'] == 'completed':
        update_wave_action_status(
            wave['executionId'], wave['waveNumber'],
            f'{action_type.capitalize()}WaveActions',
            action_index, 'completed', execution_id
        )
        
        actions_key = f'{action_type}WaveActions'
        actions = wave.get(actions_key, [])
        
        if action_index + 1 < len(actions):
            # Start next action
            next_action = actions[action_index + 1]
            next_result = start_ssm_action(
                ssm_client,
                next_action['DocumentName'],
                next_action['Parameters']
            )
            
            if next_result['status'] == 'success':
                wave['currentActionIndex'] = action_index + 1
                wave['currentActionExecutionId'] = next_result['execution_id']
                wave['actionUpdateTime'] = next_action['UpdateTime']
                wave['actionMaxWaitTime'] = next_action['MaxWaitTime']
                wave['actionTotalWaitTime'] = 0
            else:
                wave['status'] = 'failed'
        else:
            wave[f'{action_type}ActionsCompleted'] = True
    
    elif result['status'] == 'failed':
        wave['status'] = 'failed'
        update_wave_action_status(
            wave['executionId'], wave['waveNumber'],
            f'{action_type.capitalize()}WaveActions',
            action_index, 'failed', execution_id
        )
    
    return {'wave': wave, 'status': result['status']}


def update_wave_action_status(execution_id, wave_number, action_type, 
                              action_index, status, ssm_execution_id):
    """Update action status in DynamoDB"""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])
    
    table.update_item(
        Key={'ExecutionId': execution_id},
        UpdateExpression=f'SET Waves[{wave_number}].{action_type}[{action_index}].#status = :status, '
                        f'Waves[{wave_number}].{action_type}[{action_index}].ExecutionId = :exec_id',
        ExpressionAttributeNames={'#status': 'Status'},
        ExpressionAttributeValues={
            ':status': status,
            ':exec_id': ssm_execution_id
        }
    )
```

### Phase 3: Step Functions State Machine Updates

#### Updated State Machine Definition

```json
{
  "Comment": "DRS Orchestration with SSM Actions",
  "StartAt": "ProcessWaves",
  "States": {
    "ProcessWaves": {
      "Type": "Map",
      "ItemsPath": "$.Plan.Waves",
      "MaxConcurrency": 1,
      "Iterator": {
        "StartAt": "StartPreWaveActions",
        "States": {
          "StartPreWaveActions": {
            "Type": "Task",
            "Resource": "${OrchestrationLambdaArn}",
            "Parameters": {
              "action": "start_pre_wave_actions",
              "wave.$": "$",
              "executionId.$": "$.Execution.Id"
            },
            "Next": "CheckPreWaveComplete"
          },
          "CheckPreWaveComplete": {
            "Type": "Choice",
            "Choices": [
              {
                "Variable": "$.preActionsCompleted",
                "BooleanEquals": true,
                "Next": "StartDRSRecovery"
              }
            ],
            "Default": "WaitPreWave"
          },
          "WaitPreWave": {
            "Type": "Wait",
            "SecondsPath": "$.wave.actionUpdateTime",
            "Next": "CheckPreWaveStatus"
          },
          "CheckPreWaveStatus": {
            "Type": "Task",
            "Resource": "${OrchestrationLambdaArn}",
            "Parameters": {
              "action": "check_action_status",
              "actionType": "pre",
              "wave.$": "$.wave"
            },
            "Next": "CheckPreWaveComplete"
          },
          "StartDRSRecovery": {
            "Type": "Task",
            "Resource": "${OrchestrationLambdaArn}",
            "Parameters": {
              "action": "start_drs_recovery_for_wave",
              "wave.$": "$.wave"
            },
            "Next": "CheckDRSComplete"
          },
          "CheckDRSComplete": {
            "Type": "Choice",
            "Choices": [
              {
                "Variable": "$.wave.drsCompleted",
                "BooleanEquals": true,
                "Next": "StartPostWaveActions"
              }
            ],
            "Default": "WaitDRS"
          },
          "WaitDRS": {
            "Type": "Wait",
            "Seconds": 30,
            "Next": "CheckDRSStatus"
          },
          "CheckDRSStatus": {
            "Type": "Task",
            "Resource": "${OrchestrationLambdaArn}",
            "Parameters": {
              "action": "check_drs_job_status",
              "wave.$": "$.wave"
            },
            "Next": "CheckDRSComplete"
          },
          "StartPostWaveActions": {
            "Type": "Task",
            "Resource": "${OrchestrationLambdaArn}",
            "Parameters": {
              "action": "start_post_wave_actions",
              "wave.$": "$.wave"
            },
            "Next": "CheckPostWaveComplete"
          },
          "CheckPostWaveComplete": {
            "Type": "Choice",
            "Choices": [
              {
                "Variable": "$.postActionsCompleted",
                "BooleanEquals": true,
                "Next": "WaveComplete"
              }
            ],
            "Default": "WaitPostWave"
          },
          "WaitPostWave": {
            "Type": "Wait",
            "SecondsPath": "$.wave.actionUpdateTime",
            "Next": "CheckPostWaveStatus"
          },
          "CheckPostWaveStatus": {
            "Type": "Task",
            "Resource": "${OrchestrationLambdaArn}",
            "Parameters": {
              "action": "check_action_status",
              "actionType": "post",
              "wave.$": "$.wave"
            },
            "Next": "CheckPostWaveComplete"
          },
          "WaveComplete": {
            "Type": "Succeed"
          }
        }
      },
      "End": true
    }
  }
}
```

### Phase 4: Frontend Updates

#### Recovery Plan Form Updates

```typescript
// frontend/src/components/RecoveryPlanForm.tsx

interface WaveAction {
  actionName: string;
  documentName: string;
  parameters: Record<string, any>;
  maxWaitTime: number;
  updateTime: number;
}

interface Wave {
  waveNumber: number;
  protectionGroupIds: string[];
  dependsOn?: number[];
  preWaveActions?: WaveAction[];
  postWaveActions?: WaveAction[];
}

// Add to wave configuration form
const WaveActionsSection = ({ wave, onUpdate }) => {
  return (
    <ExpandableSection headerText="Wave Actions">
      <SpaceBetween size="m">
        <FormField label="Pre-Wave Actions">
          <Button onClick={() => addAction('pre')}>Add Pre-Wave Action</Button>
          {wave.preWaveActions?.map((action, index) => (
            <ActionEditor key={index} action={action} onUpdate={onUpdate} />
          ))}
        </FormField>
        
        <FormField label="Post-Wave Actions">
          <Button onClick={() => addAction('post')}>Add Post-Wave Action</Button>
          {wave.postWaveActions?.map((action, index) => (
            <ActionEditor key={index} action={action} onUpdate={onUpdate} />
          ))}
        </FormField>
      </SpaceBetween>
    </ExpandableSection>
  );
};

const ActionEditor = ({ action, onUpdate }) => {
  return (
    <Container>
      <SpaceBetween size="s">
        <FormField label="Action Name">
          <Input value={action.actionName} onChange={onUpdate} />
        </FormField>
        <FormField label="SSM Document">
          <Input value={action.documentName} onChange={onUpdate} />
        </FormField>
        <FormField label="Max Wait Time (seconds)">
          <Input type="number" value={action.maxWaitTime} onChange={onUpdate} />
        </FormField>
      </SpaceBetween>
    </Container>
  );
};
```

#### Execution Status Updates

```typescript
// frontend/src/components/ExecutionDetails.tsx

const WaveStatusCard = ({ wave }) => {
  return (
    <Container>
      <SpaceBetween size="s">
        <Header variant="h3">Wave {wave.waveNumber}</Header>
        
        {wave.preWaveActions && (
          <StatusIndicator type={getActionStatus(wave.preWaveActions)}>
            Pre-Wave Actions: {getActionSummary(wave.preWaveActions)}
          </StatusIndicator>
        )}
        
        <StatusIndicator type={getDRSStatus(wave.drs)}>
          DRS Recovery: {wave.drs?.status || 'pending'}
        </StatusIndicator>
        
        {wave.postWaveActions && (
          <StatusIndicator type={getActionStatus(wave.postWaveActions)}>
            Post-Wave Actions: {getActionSummary(wave.postWaveActions)}
          </StatusIndicator>
        )}
      </SpaceBetween>
    </Container>
  );
};
```

## SSM Document Examples

### Approval Gate Document

```yaml
# ssm-documents/ApprovalGateDocument.yaml
schemaVersion: '0.3'
description: Manual approval gate for wave execution
assumeRole: '{{ AutomationAssumeRole }}'
parameters:
  Message:
    type: String
    description: Approval message
  Approvers:
    type: StringList
    description: List of approver ARNs
    
mainSteps:
  - name: RequestApproval
    action: 'aws:approve'
    inputs:
      NotificationArn: '{{ SNSTopicArn }}'
      Message: '{{ Message }}'
      MinRequiredApprovals: 1
      Approvers: '{{ Approvers }}'
```

### Health Check Document

```yaml
# ssm-documents/HealthCheckDocument.yaml
schemaVersion: '0.3'
description: Health check for recovered instances
parameters:
  InstanceIds:
    type: StringList
    description: Instance IDs to check
    
mainSteps:
  - name: CheckInstanceStatus
    action: 'aws:executeAwsApi'
    inputs:
      Service: ec2
      Api: DescribeInstanceStatus
      InstanceIds: '{{ InstanceIds }}'
    outputs:
      - Name: InstanceStatuses
        Selector: $.InstanceStatuses
        Type: MapList
        
  - name: ValidateHealth
    action: 'aws:executeScript'
    inputs:
      Runtime: python3.8
      Handler: validate_health
      Script: |
        def validate_health(events, context):
          statuses = events['InstanceStatuses']
          for status in statuses:
            if status['InstanceStatus']['Status'] != 'ok':
              raise Exception(f"Instance {status['InstanceId']} not healthy")
          return {'status': 'healthy'}
      InputPayload:
        InstanceStatuses: '{{ CheckInstanceStatus.InstanceStatuses }}'
```

## Testing Strategy

### Unit Tests

```python
# tests/python/unit/test_ssm_actions.py

def test_start_ssm_action_success(mock_ssm):
    mock_ssm.start_automation_execution.return_value = {
        'AutomationExecutionId': 'exec-123'
    }
    
    result = start_ssm_action(mock_ssm, 'TestDoc', {})
    
    assert result['status'] == 'success'
    assert result['execution_id'] == 'exec-123'


def test_check_ssm_action_completed(mock_ssm):
    mock_ssm.describe_automation_executions.return_value = {
        'AutomationExecutionMetadataList': [{
            'AutomationExecutionStatus': 'Success'
        }]
    }
    
    result = check_ssm_action_status(mock_ssm, 'exec-123')
    
    assert result['status'] == 'completed'
```

### Integration Tests

```python
# tests/python/integration/test_ssm_integration.py

def test_approval_gate_workflow():
    """Test complete approval gate workflow"""
    # Create test recovery plan with approval action
    plan = create_test_plan_with_approval()
    
    # Start execution
    execution = start_execution(plan['PlanId'], is_drill=True)
    
    # Verify approval request created
    assert_approval_pending(execution['executionId'])
    
    # Approve and verify completion
    approve_execution(execution['executionId'])
    assert_execution_completed(execution['executionId'])
```

## Deployment

### CloudFormation Updates

```yaml
# cfn/lambda-stack.yaml - Add SSM permissions
OrchestrationRole:
  Properties:
    Policies:
      - PolicyName: SSMAutomationPolicy
        PolicyDocument:
          Statement:
            - Effect: Allow
              Action:
                - ssm:StartAutomationExecution
                - ssm:DescribeAutomationExecutions
                - ssm:StopAutomationExecution
              Resource: '*'
```

### Deployment Steps

```bash
# 1. Deploy SSM documents
aws ssm create-document \
  --name "DRS-ApprovalGate" \
  --document-type "Automation" \
  --content file://ssm-documents/ApprovalGateDocument.yaml

# 2. Update Lambda code
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# 3. Update Step Functions
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

## Migration Strategy

### Backward Compatibility

- Existing recovery plans without actions continue to work
- New `preWaveActions` and `postWaveActions` fields are optional
- State machine handles missing action arrays gracefully

### Rollout Plan

1. **Phase 1**: Deploy Lambda updates (no breaking changes)
2. **Phase 2**: Deploy Step Functions updates
3. **Phase 3**: Deploy frontend updates
4. **Phase 4**: Create SSM documents and test

## Success Metrics

- Recovery plans can define pre/post-wave actions
- SSM documents execute successfully during wave processing
- Approval gates pause execution until approved
- Health checks validate recovery success
- Execution history tracks all action statuses

This implementation adds SSM automation capabilities while maintaining backward compatibility and following existing architectural patterns.ction_index}].#status = :status, '
                        f'Waves[{wave_number}].{action_type}[{action_index}].ExecutionId = :exec_id',
        ExpressionAttributeNames={'#status': 'Status'},
        ExpressionAttributeValues={
            ':status': status,
            ':exec_id': ssm_execution_id
        }
    )
```

### Phase 3: Step Functions Updates

Add action states to state machine:

```yaml
# cfn/step-functions-stack.yaml

States:
  ProcessWave:
    Type: Choice
    Choices:
      - Variable: '$.wave.preActionsCompleted'
        BooleanEquals: false
        Next: 'ExecutePreWaveActions'
      - Variable: '$.wave.drsCompleted'
        BooleanEquals: false
        Next: 'StartDRSRecovery'
      - Variable: '$.wave.postActionsCompleted'
        BooleanEquals: false
        Next: 'ExecutePostWaveActions'
    Default: 'WaveCompleted'
  
  ExecutePreWaveActions:
    Type: Task
    Resource: 'arn:aws:states:::lambda:invoke'
    Parameters:
      FunctionName: !Ref OrchestrationLambdaArn
      Payload:
        action: 'start_pre_wave_actions'
        wave.$: '$.wave'
    ResultPath: '$.result'
    Next: 'WaitForPreWaveAction'
  
  WaitForPreWaveAction:
    Type: Wait
    SecondsPath: '$.wave.actionUpdateTime'
    Next: 'CheckPreWaveAction'
  
  CheckPreWaveAction:
    Type: Task
    Resource: 'arn:aws:states:::lambda:invoke'
    Parameters:
      FunctionName: !Ref OrchestrationLambdaArn
      Payload:
        action: 'check_action_status'
        wave.$: '$.wave'
        actionType: 'pre'
    ResultPath: '$.result'
    Next: 'ProcessWave'
```

### Phase 4: Frontend Updates

#### Wave Action Form Component

```typescript
// frontend/src/components/WaveActionForm.tsx

interface WaveAction {
  actionName: string;
  documentName: string;
  parameters: Record<string, string[]>;
  maxWaitTime: number;
  updateTime: number;
}

export function WaveActionForm({ 
  actions, 
  onChange, 
  actionType 
}: {
  actions: WaveAction[];
  onChange: (actions: WaveAction[]) => void;
  actionType: 'pre' | 'post';
}) {
  return (
    <Container header={<Header>{actionType === 'pre' ? 'Pre-Wave' : 'Post-Wave'} Actions</Header>}>
      {actions.map((action, index) => (
        <FormField key={index} label={`Action ${index + 1}`}>
          <Input
            value={action.actionName}
            placeholder="Action name"
          />
          <Input
            value={action.documentName}
            placeholder="SSM Document name"
          />
        </FormField>
      ))}
      <Button onClick={addAction}>Add Action</Button>
    </Container>
  );
}
```

#### Execution Monitor

```typescript
// frontend/src/components/ExecutionWaveDetails.tsx

<ColumnLayout columns={3}>
  <Box>
    <Header variant="h3">Pre-Wave Actions</Header>
    {wave.preWaveActions?.map((action, idx) => (
      <StatusIndicator type={getStatusType(action.status)}>
        {action.actionName}: {action.status}
      </StatusIndicator>
    ))}
  </Box>
  
  <Box>
    <Header variant="h3">DRS Recovery</Header>
    <StatusIndicator type={getStatusType(wave.drs.status)}>
      Job {wave.drs.jobId}: {wave.drs.status}
    </StatusIndicator>
  </Box>
  
  <Box>
    <Header variant="h3">Post-Wave Actions</Header>
    {wave.postWaveActions?.map((action, idx) => (
      <StatusIndicator type={getStatusType(action.status)}>
        {action.actionName}: {action.status}
      </StatusIndicator>
    ))}
  </Box>
</ColumnLayout>
```

### Phase 5: IAM Permissions

```yaml
# cfn/lambda-stack.yaml

OrchestrationLambdaRole:
  Policies:
    - PolicyName: SSMAutomationPolicy
      PolicyDocument:
        Statement:
          - Effect: Allow
            Action:
              - ssm:StartAutomationExecution
              - ssm:DescribeAutomationExecutions
              - ssm:GetAutomationExecution
              - ssm:StopAutomationExecution
            Resource:
              - !Sub 'arn:aws:ssm:*:${AWS::AccountId}:automation-definition/*'
              - !Sub 'arn:aws:ssm:*:${AWS::AccountId}:automation-execution/*'
```

## Example SSM Documents

### Manual Approval

```yaml
# ssm-documents/manual-approval.yaml

schemaVersion: '0.3'
description: Manual approval gate for DR execution
parameters:
  Message:
    type: String
  Approvers:
    type: StringList
  NotificationTopic:
    type: String

mainSteps:
  - name: ApprovalGate
    action: aws:approve
    inputs:
      NotificationArn: '{{ NotificationTopic }}'
      Message: '{{ Message }}'
      MinRequiredApprovals: 1
      Approvers: '{{ Approvers }}'
```

### Health Check

```yaml
# ssm-documents/health-check.yaml

schemaVersion: '0.3'
description: Health check recovered instances
parameters:
  InstanceIds:
    type: StringList

mainSteps:
  - name: WaitForInstances
    action: aws:waitForAwsResourceProperty
    inputs:
      Service: ec2
      Api: DescribeInstanceStatus
      InstanceIds: '{{ InstanceIds }}'
      PropertySelector: '$.InstanceStatuses[0].InstanceStatus.Status'
      DesiredValues:
        - ok
    timeoutSeconds: 600
  
  - name: RunHealthCheck
    action: aws:runCommand
    inputs:
      DocumentName: AWS-RunShellScript
      InstanceIds: '{{ InstanceIds }}'
      Parameters:
        commands:
          - curl -f http://localhost/health || exit 1
```

## Testing Strategy

### Unit Tests

```python
# tests/python/unit/test_ssm_actions.py

def test_start_ssm_action_success(mock_ssm_client):
    mock_ssm_client.start_automation_execution.return_value = {
        'AutomationExecutionId': 'exec-123'
    }
    
    result = start_ssm_action(
        mock_ssm_client,
        'TestDocument',
        {'Param1': ['value1']}
    )
    
    assert result['status'] == 'success'
    assert result['execution_id'] == 'exec-123'
```

### Integration Tests

```python
# tests/python/integration/test_wave_with_actions.py

def test_wave_execution_with_pre_actions():
    plan = create_test_plan_with_actions()
    execution = start_execution(plan['PlanId'], is_drill=True)
    wait_for_action_completion(execution['ExecutionId'], wave=0, action_type='pre')
    assert_drs_job_started(execution['ExecutionId'], wave=0)
```

## Deployment Steps

```bash
# 1. Deploy schema changes
./scripts/sync-to-deployment-bucket.sh --deploy-cfn

# 2. Deploy Lambda updates
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# 3. Deploy frontend
./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-frontend
```

## Timeline Estimate

| Phase | Duration |
|-------|----------|
| Phase 1: Data Model | 1 day |
| Phase 2: Lambda Updates | 3 days |
| Phase 3: Step Functions | 2 days |
| Phase 4: Frontend | 3 days |
| Phase 5: IAM & Testing | 3 days |
| **Total** | **12 days** |

## Success Criteria

- [ ] Recovery plans can define pre/post wave actions
- [ ] SSM documents execute before/after waves
- [ ] Manual approval gates pause execution
- [ ] Health checks validate recovered instances
- [ ] Execution history tracks action status
- [ ] Frontend displays action progress
- [ ] Timeouts handled correctly
- [ ] Failures fail the wave appropriately
