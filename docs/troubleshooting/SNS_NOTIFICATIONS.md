# SNS Notifications Troubleshooting

## Overview

This guide consolidates all SNS notification troubleshooting for the DR Orchestration platform, including execution notifications and approval workflows.

## Common Issues

### 1. SNS Notifications Not Working

**Symptoms**:
- No email notifications received for execution events
- CloudWatch logs show no SNS publish attempts
- No errors in logs

**Root Cause**:
IAM policy issue in Lambda stack - `!Ref` was used on parameter values that are already ARNs.

**Fix Applied** (✅ Resolved):

Changed from:
```yaml
# INCORRECT - !Ref doesn't work on parameter ARNs
Resource:
  - !Ref ExecutionNotificationsTopicArn
  - !Ref DRSAlertsTopicArn
```

To:
```yaml
# CORRECT - !Sub properly substitutes parameter values
Resource:
  - !Sub "${ExecutionNotificationsTopicArn}"
  - !Sub "${DRSAlertsTopicArn}"
```

**Files Modified**: `cfn/lambda-stack.yaml` (line ~742-749)

**Verification**:
1. ✅ Environment Variables: OrchestrationStepFunctionsFunction has correct SNS topic ARN environment variables
2. ✅ IAM Permissions: OrchestrationRole now has valid SNS publish permissions
3. ✅ Topic Configuration: Notification stack properly creates and exports SNS topic ARNs
4. ✅ Master Template: Correctly passes topic ARNs from NotificationStack to LambdaStack

### 2. Approval Workflow Notifications

**Current Implementation**:

We use Step Functions `waitForTaskToken` pattern for pause/resume functionality:

```yaml
# cfn/step-functions-stack.yaml
WaitForResume:
  Type: Task
  Resource: 'arn:aws:states:::lambda:invoke.waitForTaskToken'
  Parameters:
    FunctionName: !Ref OrchestrationLambdaArn
    Payload:
      action: 'store_task_token'
      taskToken.$: '$.Task.Token'
  TimeoutSeconds: 31536000  # 1 year max pause
  Next: 'ResumeWavePlan'
```

**How It Works**:
1. Execution reaches `PauseBeforeWave` checkpoint
2. Step Functions generates a task token
3. Lambda stores token in DynamoDB
4. Execution **pauses** waiting for callback
5. SNS notification sent to subscribers
6. User resumes via API: `POST /executions/{id}/resume`
7. API calls `SendTaskSuccess` with stored token
8. Execution continues to next wave

**Notification Content**:

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

## Comparison: Reference Implementation vs Our Implementation

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

## Testing SNS Notifications

### Test Execution Notifications

1. Start a recovery execution
2. Check CloudWatch Logs for the orchestration Lambda
3. Look for SNS publish log entries
4. Verify email notification received
5. Confirm no IAM permission errors in logs

### Test Pause Notifications

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

## Diagnostic Steps

### Check 1: Verify SNS Topic ARNs

```bash
# Get topic ARNs from CloudFormation
aws cloudformation describe-stacks \
  --stack-name aws-drs-orch-notification-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ExecutionNotificationsTopicArn`].OutputValue' \
  --output text
```

### Check 2: Verify Lambda Environment Variables

```bash
# Check Lambda environment variables
aws lambda get-function-configuration \
  --function-name aws-drs-orch-orchestration-stepfunctions-dev \
  --query 'Environment.Variables' \
  --output json
```

Look for:
- `EXECUTION_NOTIFICATIONS_TOPIC_ARN`
- `DRS_ALERTS_TOPIC_ARN`

### Check 3: Verify IAM Permissions

```bash
# Get Lambda role ARN
aws lambda get-function \
  --function-name aws-drs-orch-orchestration-stepfunctions-dev \
  --query 'Configuration.Role' \
  --output text

# Check role policies
aws iam list-attached-role-policies \
  --role-name <ROLE_NAME>
```

Verify SNS publish permissions exist for the topic ARNs.

### Check 4: Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/aws-drs-orch-orchestration-stepfunctions-dev --follow
```

Look for:
- SNS publish attempts
- IAM permission errors
- Topic ARN values in logs

### Check 5: Test SNS Topic Directly

```bash
# Test publish to topic
aws sns publish \
  --topic-arn <TOPIC_ARN> \
  --subject "Test Notification" \
  --message "This is a test message"
```

If this works but Lambda doesn't → IAM permission issue
If this fails → SNS topic configuration issue

## Enhancement Opportunities

### Add Approval Links to Notifications

```python
# Enhanced notification with approval links
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
    
    sns.publish(
        TopicArn=EXECUTION_TOPIC_ARN,
        Subject=subject,
        Message=message
    )
```

## Related Documentation

- [Notification Stack](../../cfn/notification-stack.yaml) - SNS topic definitions
- [Lambda Stack](../../cfn/lambda-stack.yaml) - IAM permissions
- [Notifications Module](../../lambda/shared/notifications.py) - Notification functions
