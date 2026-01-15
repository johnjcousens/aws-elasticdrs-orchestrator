# SNS Notification Fix

## Problem Identified

The SNS notifications were not working due to an IAM policy issue in the Lambda stack.

## Root Cause

In `cfn/lambda-stack.yaml`, the `OrchestrationRole` SNS policy was using `!Ref` on parameter values that are already ARNs:

```yaml
# INCORRECT - !Ref doesn't work on parameter ARNs
Resource:
  - !Ref ExecutionNotificationsTopicArn
  - !Ref DRSAlertsTopicArn
```

This caused the IAM policy to have invalid resource ARNs, preventing the Lambda function from publishing to SNS topics.

## Fix Applied

Changed the policy to use `!Sub` to properly reference the parameter values:

```yaml
# CORRECT - !Sub properly substitutes parameter values
Resource:
  - !Sub "${ExecutionNotificationsTopicArn}"
  - !Sub "${DRSAlertsTopicArn}"
```

## Verification

The fix ensures:

1. ✅ **Environment Variables**: OrchestrationStepFunctionsFunction has correct SNS topic ARN environment variables
2. ✅ **IAM Permissions**: OrchestrationRole now has valid SNS publish permissions
3. ✅ **Topic Configuration**: Notification stack properly creates and exports SNS topic ARNs
4. ✅ **Master Template**: Correctly passes topic ARNs from NotificationStack to LambdaStack

## Files Modified

- `cfn/lambda-stack.yaml` - Fixed SNS policy resource references (line ~742-749)

## Testing

After deploying this fix:

1. Start a recovery execution
2. Check CloudWatch Logs for the orchestration Lambda
3. Verify SNS notifications are sent (check email)
4. Confirm no IAM permission errors in logs

## Reference Implementation

The fix aligns with the reference implementation from `archive/HealthEdge/HRP-DR-Orchestration/archive/drs-tools/drs-plan-automation/` which uses similar SNS notification patterns.
