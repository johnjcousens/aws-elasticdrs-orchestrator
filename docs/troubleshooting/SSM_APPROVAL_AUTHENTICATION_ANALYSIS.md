# SSM Approval Authentication Analysis

## How Archive Solution Handles Authentication

The archive solution **doesn't use clickable approval links** at all. Instead, it uses **AWS Systems Manager (SSM) Automation's built-in approval mechanism**.

## SSM `aws:approve` Action - How It Works

### 1. SSM Document Definition

```yaml
# archive/.../cfn/ssm/manualapproval.yml
RecoveryManualAction:
  Type: AWS::SSM::Document
  Properties:
    Name: RecoveryManualAction
    DocumentType: Automation
    Content:
      mainSteps:
        - name: ManualApproval
          action: aws:approve
          inputs:
            NotificationArn: "{{NotificationTopicArn}}"
            Message: "{{Message}}"
            MinRequiredApprovals: 1
            Approvers: '{{ ApproversArns }}'  # IAM ARNs of approvers
```

### 2. Authentication Flow

**Step 1: SSM Automation Starts**
```python
# Lambda or Step Functions calls SSM
ssm.start_automation_execution(
    DocumentName='RecoveryManualAction',
    Parameters={
        'Message': ['Approve wave 2 recovery?'],
        'NotificationTopicArn': ['arn:aws:sns:...'],
        'ApproversArns': [
            'arn:aws:iam::123456789012:user/john.doe',
            'arn:aws:iam::123456789012:role/DRSApprovers'
        ]
    }
)
```

**Step 2: SNS Notification Sent**
- SSM automatically sends SNS notification
- Email contains: execution ID, message, but **NO clickable approval links**
- Email is informational only

**Step 3: Approval via AWS Console or CLI**

Approvers must authenticate to AWS and use one of these methods:

#### Option A: AWS Console (Web UI)
1. Log into AWS Console with IAM credentials
2. Navigate to: **Systems Manager → Automation → Executions**
3. Find the execution (shows "Waiting for approval")
4. Click execution ID
5. Click **"Approve"** or **"Reject"** button
6. Execution continues or stops

#### Option B: AWS CLI (Command Line)
```bash
# Approver must have AWS credentials configured
aws ssm send-automation-signal \
  --automation-execution-id "abc-123-def-456" \
  --signal-type Approve \
  --region us-east-1

# Or reject
aws ssm send-automation-signal \
  --automation-execution-id "abc-123-def-456" \
  --signal-type Reject \
  --region us-east-1
```

#### Option C: AWS SDK (Programmatic)
```python
import boto3

ssm = boto3.client('ssm')
ssm.send_automation_signal(
    AutomationExecutionId='abc-123-def-456',
    SignalType='Approve'
)
```

### 3. IAM-Based Authorization

**Authentication is handled by AWS IAM:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:SendAutomationSignal",
        "ssm:GetAutomationExecution",
        "ssm:DescribeAutomationExecutions"
      ],
      "Resource": "arn:aws:ssm:*:*:automation-execution/*",
      "Condition": {
        "StringEquals": {
          "ssm:resourceTag/ApprovalRequired": "true"
        }
      }
    }
  ]
}
```

**Key Points:**
- Approvers must be authenticated AWS IAM users/roles
- Approvers must have `ssm:SendAutomationSignal` permission
- No custom authentication needed - AWS handles it
- No clickable links - must use AWS Console/CLI/SDK

## Why No Clickable Approval Links?

### Security Reasons

1. **No Token in Email**: Embedding approval tokens in email is insecure
   - Email can be forwarded
   - Email can be intercepted
   - Token could be stolen

2. **IAM Authentication Required**: AWS forces proper authentication
   - Must log into AWS Console
   - Must have valid IAM credentials
   - Must have specific SSM permissions

3. **Audit Trail**: All approvals logged in CloudTrail
   - Who approved (IAM principal)
   - When approved (timestamp)
   - From where (source IP)

### Workflow Comparison

| Method | Archive (SSM) | Clickable Links |
|--------|---------------|-----------------|
| **Email Content** | Informational only | Contains approval token |
| **Authentication** | AWS IAM (Console/CLI) | Custom token validation |
| **Authorization** | IAM policies | Application logic |
| **Audit** | CloudTrail automatic | Custom logging required |
| **Security** | AWS-managed | Custom implementation |
| **User Experience** | Must log into AWS | Click link in email |

## Our Implementation Options

### Option 1: Keep Current Approach (Recommended)

**What we have:**
- Step Functions `waitForTaskToken`
- API endpoint: `POST /executions/{id}/resume`
- Cognito authentication required
- CloudScape UI for approval

**Pros:**
- API-first design (automation-friendly)
- Flexible authorization (Cognito groups)
- Better UX (visual UI)
- No SSM dependency

**Cons:**
- No email-based approval
- Requires UI or API access

### Option 2: Add SSM Approval (Like Archive)

**Implementation:**
```yaml
# Add SSM document
ManualApprovalDocument:
  Type: AWS::SSM::Document
  Properties:
    Name: !Sub '${ProjectName}-manual-approval-${Environment}'
    DocumentType: Automation
    Content:
      mainSteps:
        - name: ManualApproval
          action: aws:approve
          inputs:
            NotificationArn: !Ref ApprovalWorkflowTopicArn
            Message: "Approve wave recovery?"
            MinRequiredApprovals: 1
            Approvers: 
              - !Sub 'arn:aws:iam::${AWS::AccountId}:role/DRSApprovers'
```

**Pros:**
- AWS-managed authentication
- CloudTrail audit trail
- No custom auth code

**Cons:**
- Requires SSM Console access
- Less flexible than API
- Tighter AWS coupling

### Option 3: Hybrid Approach

**Combine both methods:**
1. Send SNS notification with execution details
2. Provide **two approval paths**:
   - **Path A**: Log into AWS Console → Use CloudScape UI → Click "Resume"
   - **Path B**: Log into AWS Console → Use SSM → Approve automation

**Email Content:**
```
⏸️ DRS Execution Paused - Approval Required

Execution ID: exec-123
Recovery Plan: Production Failover
Paused Before: Wave 2 (Application Servers)

To approve this execution, choose one of the following:

Option 1: DRS Orchestration Console (Recommended)
1. Log into AWS Console
2. Navigate to DRS Orchestration
3. Click "Resume Execution" button

Option 2: Systems Manager Console
1. Log into AWS Console
2. Navigate to Systems Manager → Automation
3. Find execution: exec-123
4. Click "Approve"

Note: You must have appropriate IAM permissions to approve.
```

## Recommendation

**Keep our current implementation** (Option 1) because:

1. ✅ **Better UX**: Visual CloudScape UI vs SSM console
2. ✅ **API-First**: Enables automation and CI/CD integration
3. ✅ **Flexible Auth**: Cognito groups for fine-grained control
4. ✅ **Already Working**: Pause/resume fully functional
5. ✅ **Modern Pattern**: Step Functions callback is AWS best practice

**Don't add clickable approval links** because:
- ❌ Security risk (token in email)
- ❌ Complex to implement securely
- ❌ Not how AWS services do it (SSM, CodePipeline, etc.)
- ❌ Audit trail challenges

## How Users Approve in Our System

### Current Workflow (After SNS Fix)

1. **Execution Pauses**
   - Email notification sent via SNS
   - Execution marked as PAUSED in DynamoDB
   - Task token stored for callback

2. **User Receives Email**
   ```
   ⏸️ DRS Execution Paused - Production Failover
   
   Execution ID: exec-abc123
   Paused Before: Wave 2 (Application Servers)
   
   To resume:
   1. Log into DRS Orchestration Console
   2. Navigate to Executions
   3. Click "Resume" button
   ```

3. **User Approves**
   - Log into CloudScape UI (Cognito auth)
   - Navigate to Executions page
   - Find paused execution
   - Click "Resume" button
   - API calls `SendTaskSuccess` with stored token
   - Execution continues

4. **Audit Trail**
   - Cognito logs: Who logged in
   - API Gateway logs: Who called resume API
   - DynamoDB: Execution state changes
   - CloudWatch: Lambda execution logs

## Conclusion

The archive solution **doesn't use clickable approval links**. It uses **SSM Automation's `aws:approve` action** which requires users to:
1. Authenticate to AWS (IAM)
2. Navigate to SSM Console
3. Manually approve the automation execution

This is **more secure** than clickable links but **less user-friendly** than our CloudScape UI approach.

Our implementation is **better** because it provides a modern, API-first approval workflow with a professional UI, while maintaining security through Cognito authentication and proper audit trails.
