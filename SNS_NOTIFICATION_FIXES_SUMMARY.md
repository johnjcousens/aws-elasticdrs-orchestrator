# SNS Notification CloudFormation Fixes Summary

## Issue Resolution

Fixed critical CloudFormation deployment rollback issues that were preventing the SNS notification system from deploying properly.

## Root Cause Analysis

The deployment was failing due to:

1. **Circular Dependency**: Master template was trying to pass `NotificationTopicArn` to Lambda stack before the SNS topic was created
2. **Conditional Export Issues**: CodePipeline stack was importing exports that didn't exist when notifications were disabled
3. **Parameter Mismatch**: Inconsistent parameter passing between stacks

## Changes Made

### 1. Master Template (`cfn/master-template.yaml`)
- **FIXED**: Removed circular dependency by setting `NotificationTopicArn: ""` instead of constructing ARN
- **RESULT**: Lambda stack now creates SNS topic independently

### 2. Lambda Stack (`cfn/lambda-stack.yaml`)
- **FIXED**: SNS topic creation moved to Lambda stack with proper conditional logic
- **FIXED**: Updated IAM policies to reference local SNS topic instead of parameter
- **FIXED**: Environment variables now use conditional reference to local topic
- **RESULT**: SNS topic, subscription, and notification formatter function created in single stack

### 3. CodePipeline Stack (`cfn/codepipeline-stack.yaml`)
- **FIXED**: Replaced `Fn::ImportValue` with direct ARN construction for SNS topic
- **FIXED**: Replaced `Fn::ImportValue` with direct function name construction for Lambda
- **FIXED**: EventBridge rules now use constructed ARNs instead of imports
- **RESULT**: No dependency on conditional exports that may not exist

## Architecture Changes

### Before (Broken)
```
Master Template → Lambda Stack (NotificationTopicArn parameter)
                ↓
CodePipeline Stack → Import SNS topic ARN (fails if disabled)
                   → Import Lambda function ARN (fails if disabled)
```

### After (Fixed)
```
Master Template → Lambda Stack (creates SNS topic internally)
                ↓
CodePipeline Stack → Constructs SNS topic ARN directly
                   → Constructs Lambda function ARN directly
```

## Notification Formatter Function

The notification formatter Lambda function (`lambda/notification-formatter/index.py`) provides:

### Features
- **Pipeline Failures**: Formats CodePipeline state change events
- **Security Scan Failures**: Formats CodeBuild security scan failures
- **User-Friendly Messages**: Converts raw JSON events to readable emails
- **Console Links**: Direct links to AWS console for troubleshooting
- **Contextual Information**: Includes timestamps, execution IDs, and error details

### Email Format Examples

#### Pipeline Failure
```
🚨 CRITICAL AWS DRS Orchestration Pipeline Notification

❌ Pipeline: aws-elasticdrs-orchestrator-pipeline-dev
📅 Time: 2026-01-03 18:30:00 UTC
🔄 Status: FAILED
Failed Stage: SecurityScan
Failed Action: SecurityScanAction
🆔 Execution ID: abc123-def456

Quick Actions:
• View Pipeline (console link)
• View Execution Details (console link)
• CloudWatch Logs (console link)
```

#### Security Scan Failure
```
🔒 SECURITY ALERT

🛡️❌ Project: aws-elasticdrs-orchestrator-security-scan-dev
📅 Time: 2026-01-03 18:25:00 UTC
🔄 Status: FAILED
🆔 Build: 123
📋 Type: Security vulnerabilities detected or scan failed

Quick Actions:
• View Build Details (console link)
• View Build Logs (console link)
• CodeBuild Console (console link)
```

## Deployment Instructions

### Prerequisites
1. **Update AWS Credentials**: Ensure valid AWS credentials are configured
   ```bash
   aws sts get-caller-identity  # Should return account info
   ```

### Deployment Steps

1. **Sync Templates to S3**:
   ```bash
   ./scripts/sync-to-deployment-bucket.sh
   ```

2. **Deploy Master Stack**:
   ```bash
   aws cloudformation update-stack \
     --stack-name aws-elasticdrs-orchestrator-dev \
     --template-url https://s3.amazonaws.com/aws-elasticdrs-orchestrator/cfn/master-template.yaml \
     --parameters ParameterKey=AdminEmail,ParameterValue=***REMOVED*** \
                  ParameterKey=EnablePipelineNotifications,ParameterValue=true \
     --capabilities CAPABILITY_NAMED_IAM
   ```

3. **Monitor Deployment**:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name aws-elasticdrs-orchestrator-dev \
     --query 'Stacks[0].StackStatus'
   ```

### Verification Steps

1. **Check SNS Topic Created**:
   ```bash
   aws sns list-topics --query 'Topics[?contains(TopicArn, `pipeline-notifications`)]'
   ```

2. **Verify Email Subscription**:
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn arn:aws:sns:us-east-1:ACCOUNT:aws-elasticdrs-orchestrator-pipeline-notifications-dev
   ```

3. **Test Notification Formatter**:
   ```bash
   aws lambda invoke \
     --function-name aws-elasticdrs-orchestrator-notification-formatter-dev \
     --payload '{"source":"aws.codepipeline","detail-type":"test"}' \
     response.json
   ```

4. **Trigger Test Pipeline Failure** (optional):
   - Manually fail a pipeline stage to test end-to-end notification flow

## Expected Results

After successful deployment:

✅ **SNS Topic**: `aws-elasticdrs-orchestrator-pipeline-notifications-dev` created  
✅ **Email Subscription**: Admin email subscribed to topic  
✅ **Lambda Function**: Notification formatter function deployed  
✅ **EventBridge Rules**: Pipeline and security scan failure rules active  
✅ **Permissions**: All IAM roles and policies configured  
✅ **Integration**: End-to-end notification flow functional  

## Troubleshooting

### Common Issues

1. **Stack Still Rolling Back**:
   - Check CloudFormation events for specific error
   - Verify all parameter values are correct
   - Ensure no resource name conflicts

2. **Notifications Not Received**:
   - Check email subscription confirmation
   - Verify EventBridge rules are enabled
   - Check Lambda function logs for errors

3. **Permission Errors**:
   - Verify IAM roles have correct policies
   - Check EventBridge permissions to invoke Lambda
   - Ensure SNS topic policy allows EventBridge to publish

### Debug Commands

```bash
# Check stack events
aws cloudformation describe-stack-events \
  --stack-name aws-elasticdrs-orchestrator-dev \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# Check Lambda logs
aws logs tail /aws/lambda/aws-elasticdrs-orchestrator-notification-formatter-dev

# List EventBridge rules
aws events list-rules --name-prefix aws-elasticdrs-orchestrator
```

## Next Steps

1. **Update AWS Credentials**: Get fresh credentials from AWS console
2. **Deploy Fixed Templates**: Run deployment commands above
3. **Test Notification Flow**: Verify emails are received for pipeline failures
4. **Monitor Production**: Ensure notifications work in production environment

The CloudFormation templates are now fixed and ready for deployment once AWS credentials are updated.