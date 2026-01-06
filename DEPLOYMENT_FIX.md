# IAM Permission Fix

## Issue
Protection Groups creation returns 400 Bad Request due to missing `drs:UpdateLaunchConfiguration` IAM permission.

## Root Cause
The deployed Lambda IAM policy is missing the `drs:UpdateLaunchConfiguration` permission that exists in the CloudFormation template. The deployed policy only has read-only DRS permissions.

## Solution
Deploy the CloudFormation stack to update the IAM policy with the correct permissions.

## Error Details
```
User: arn:aws:sts::***REMOVED***:assumed-role/aws-elasticdrs-orchestrator-dev-Lamb-ApiHandlerRole-mgni4Le6HWh7/aws-elasticdrs-orchestrator-api-handler-dev is not authorized to perform: drs:UpdateLaunchConfiguration
```

## CloudFormation Template Status
The `cfn/lambda-stack.yaml` template already includes the correct permission on line 316:
```yaml
- drs:UpdateLaunchConfiguration
```

## Deployment Required
This fix requires CloudFormation stack deployment via GitHub Actions to update the IAM policy.