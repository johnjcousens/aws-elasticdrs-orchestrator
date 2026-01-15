# SNS Approval Workflow Analysis

## Overview

You're correct! The reference implementation uses SNS notifications for **manual approval workflows** during paused drill/recovery executions.

## Reference Implementation Pattern

### 1. SSM Automation Document for Manual Approval

The reference uses an SSM Automation document (`RecoveryManualAction`) with the `aws:approve` action:

```yaml
# archive/.../cfn/ssm/manualapproval.yml
RecoveryManualAction:
  Type: AWS::SSM::Document
  Properties:
    Name: RecoveryManualAction
    DocumentType: Automation
    Content:
      parameters:
        Message:
          type: String
        NotificationTopicArn:
          type: String
        ApproversArns:
          type: StringList
      mainSteps:
        - name: ManualApproval
          action: aws:approve
          inputs:
            NotificationArn: "{{NotificationTopicArn}}"
            Message: "{{Message}}"
            MinRequiredApprovals: 1
            Approvers: '{{ ApproversArns }}'
```

**Key Features:**
- Uses SSM's built-in `aws:approve` action
- Sends SNS notification with approval request
- Requires 1 approval from specified approvers
- Blocks execution until approved/rejected

### 2. SNS Topic for Approvals

```yaml
# archive/.../cfn/sns/notifications.yaml
DRSPlanAutomationPipelineSNSTopic:
  Type: AWS::SNS::Topic
  Properties:
    DisplayName: SNS Topic for drs-plan-automation pipeline and approval
    TopicName: drs-plan-automation-pipeline
```

## Our Current Implementation

### 1. Step Functions Callback Pattern (waitForTaskToken)

We use a **different but equally valid** approach:

```yaml
# cfn/step-functions-stack.yaml
WaitForResume:
  Type: Task
  Resource: 'arn:aws:states:::lambda:invoke.waitForTaskToken'
  Parameters:
    FunctionName: !Ref OrchestrationLambdaArn
    Payload:
      action: 'store_task_token'
      taskToken.$: '$$.Task.Token'
  TimeoutSeconds: 31536000  # 1 year max pause
  Next: 'ResumeWavePlan'
```

**How It Works:**
1. Execution reaches `PauseBeforeWave` checkpoint
2. Step Functions generates a task token
3. Lambda stores token in DynamoDB
4. Execution **pauses** waiting for callback
5. User resumes via API: `POST /executions/{id}/resume`
6. API calls `SendTaskSuccess` with stored token
7. Execution continues to next wave

### 2. SNS Notification on Pause

```python
# lambda/orchestration-stepfunctions/index.py
if pause_before:
    print(f"⏸️ Pausing before wave {next_wave}")
    state["status"] = "paused"
    state["paused_before_wave"] = next_wave
    
    # Send execution paused notification
    send_execution_paused(execution_id, plan_name, next_wave + 1, wave_name)
    
    # Mark execution as PAUSED for manual resume
    get_execution_history_table().update_item(
        Key={"executionId": execution_id, "planId": plan_id},
        UpdateExpression="SET #status = :status, pausedBeforeWave = :wave",
        ExpressionAttributeValues={
            ":status": "PAUSED",
            ":wave": next_wave,
        }
    )
```

### 3. Notification Content

```python
# lambda/shared/notifications.py
def send_execution_paused(execution_id: str, plan_name: str, 
                         paused_before_wave: int, wave_name: str) -> None:
    """Send notification when execution is paused"""
    subject = f"⏸️ DRS Execution Paused - {plan_name}"
    message = f"""
⏸️ AWS DRS Orchestration Execution Paused

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Paused Before: Wave {paused_before_wave} ({wave_name})
• Paused At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

The execution is waiting for manual approval to continue. 
Use the DRS Orchestration console to resume.
"""
    
    sns.publish(
        TopicArn=EXECUTION_TOPIC_ARN,
        Subject=subject,
        Message=message
    )
```

## Comparison: Reference vs Our Implementation

| Aspect | Reference Implementation | Our Implementation |
|--------|-------------------------|-------------------|
| **Approval Method** | SSM Automation `aws:approve` | Step Functions `waitForTaskToken` |
| **Notification** | SNS via SSM action | SNS via Lambda function |
| **Resume Method** | SSM approval response | API call with `SendTaskSuccess` |
| **Approvers** | IAM ARNs in SSM document | Any authenticated user via API |
| **Timeout** | SSM automation timeout | 1 year (Step Functions max) |
| **Integration** | Tight SSM coupling | Flexible API-based |

## Advantages of Our Approach

1. **API-First Design**: Resume via REST API enables automation and CI/CD integration
2. **Flexible Authorization**: Use Cognito groups for approval permissions
3. **Better UX**: CloudScape UI with visual approval workflow
4. **Audit Trail**: All actions logged in DynamoDB execution history
5. **No SSM Dependency**: Pure Step Functions + Lambda pattern

## Advantages of Reference Approach

1. **Built-in Approval**: SSM `aws:approve` is purpose-built for approvals
2. **Email Approval**: Can approve directly from email (SNS notification)
3. **IAM-Based**: Approvers defined by IAM ARNs (strong security)
4. **Simpler**: No custom API endpoints needed

## Enhancement Opportunity: Approval Workflow Topic

We could add a **dedicated approval workflow topic** similar to the reference:

```yaml
# cfn/notification-stack.yaml (ALREADY EXISTS!)
ApprovalWorkflowTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: !Sub '${ProjectName}-approval-workflow-${Environment}'
    DisplayName: 'DRS Orchestration Approval Workflow'
```

### Enhanced Notification with Approval Links

```python
# lambda/shared/notifications.py
def send_execution_paused(execution_id: str, plan_name: str, 
                         paused_before_wave: int, wave_name: str) -> None:
    """Send notification with approval links"""
    
    # Generate approval URLs
    api_base = os.environ.get('API_GATEWAY_URL')
    approve_url = f"{api_base}/executions/{execution_id}/resume"
    reject_url = f"{api_base}/executions/{execution_id}/cancel"
    
    subject = f"⏸️ Approval Required: Wave {paused_before_wave} - {plan_name}"
    message = f"""
⏸️ AWS DRS Orchestration - Approval Required

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Paused Before: Wave {paused_before_wave} ({wave_name})
• Paused At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Actions Required:
Please review the wave configuration and choose one of the following:

✅ APPROVE: Continue with the execution
{approve_url}

❌ REJECT: Cancel the execution
{reject_url}

Note: This approval request will expire after 24 hours.
"""
    
    # Send to BOTH topics
    sns.publish(
        TopicArn=EXECUTION_TOPIC_ARN,
        Subject=subject,
        Message=message
    )
    
    sns.publish(
        TopicArn=APPROVAL_WORKFLOW_TOPIC_ARN,
        Subject=subject,
        Message=message
    )
```

## Current Status

✅ **Already Implemented:**
- Pause/resume functionality with `waitForTaskToken`
- SNS notification on pause
- API endpoints for resume/cancel
- DynamoDB task token storage
- Approval workflow SNS topic (created but not used)

❌ **Not Yet Implemented:**
- Approval links in pause notifications
- Separate approval workflow topic usage
- Email-based approval (requires API authentication)

## Recommendation

Your SNS implementation is **already working correctly** for pause notifications. The fix I applied will ensure notifications are sent.

**Optional Enhancement**: Add approval URLs to pause notifications so users can click to approve/reject directly (requires authentication handling).

## Testing the Pause Notification

1. Create a recovery plan with `pauseBeforeWave: true` on a wave
2. Start execution
3. When execution reaches that wave, it will:
   - Pause execution
   - Store task token in DynamoDB
   - Send SNS notification to your email
   - Wait for resume API call

4. Resume via API or UI:
   ```bash
   curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     "https://API_URL/executions/{executionId}/resume"
   ```

The notification email will arrive with pause details and instructions to resume via the console.
