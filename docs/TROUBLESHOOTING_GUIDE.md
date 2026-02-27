# Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when deploying and operating the DR Orchestration Platform with function-specific IAM roles. It covers IAM permission errors, CloudFormation deployment errors, rollback procedures, and debugging techniques.

## Common IAM Permission Errors

### AccessDenied: User is not authorized to perform action

**Symptom**: Lambda function fails with `AccessDenied` error in CloudWatch Logs

**Example Error**:
```
An error occurred (AccessDeniedException) when calling the StartRecovery operation: 
User: arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-query-handler-role-qa/aws-drs-orchestration-query-handler-qa 
is not authorized to perform: drs:StartRecovery on resource: * 
because no identity-based policy allows the drs:StartRecovery action
```

**Diagnosis**:

1. **Identify the function and operation**:
   ```bash
   # Check CloudWatch Logs for the function
   aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-qa --since 5m --region us-east-2
   ```

2. **Verify the IAM role**:
   ```bash
   # Get the function's IAM role
   aws lambda get-function-configuration \
     --function-name aws-drs-orchestration-query-handler-qa \
     --region us-east-2 \
     --query 'Role'
   
   # Get the role's policies
   aws iam get-role \
     --role-name aws-drs-orchestration-query-handler-role-qa \
     --query 'Role.AssumeRolePolicyDocument'
   
   aws iam list-attached-role-policies \
     --role-name aws-drs-orchestration-query-handler-role-qa
   
   aws iam list-role-policies \
     --role-name aws-drs-orchestration-query-handler-role-qa
   ```

3. **Check IAM Policy Simulator**:
   ```bash
   # Simulate the denied action
   aws iam simulate-principal-policy \
     --policy-source-arn arn:aws:iam::438465159935:role/aws-drs-orchestration-query-handler-role-qa \
     --action-names drs:StartRecovery \
     --resource-arns "*"
   ```

**Resolution**:

This is **expected behavior** for function-specific roles. The Query Handler is designed to have read-only permissions and should NOT be able to start recovery operations.

If this is a legitimate operation:
1. Use the correct Lambda function (Orchestration Function for recovery operations)
2. Or update the IAM role policy in `cfn/iam/roles-stack.yaml` to grant the permission
3. Redeploy the stack: `./scripts/deploy-main-stack.sh qa --use-function-specific-roles`

### AccessDenied: Resource ARN does not match policy

**Symptom**: Lambda function fails with `AccessDenied` error for a specific resource

**Example Error**:
```
An error occurred (AccessDeniedException) when calling the GetItem operation: 
User: arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-query-handler-role-qa/aws-drs-orchestration-query-handler-qa 
is not authorized to perform: dynamodb:GetItem on resource: 
arn:aws:dynamodb:us-east-2:438465159935:table/external-table 
because no identity-based policy allows the dynamodb:GetItem action
```

**Diagnosis**:

1. **Check the resource ARN pattern**:
   ```bash
   # View the IAM policy
   aws iam get-role-policy \
     --role-name aws-drs-orchestration-query-handler-role-qa \
     --policy-name DynamoDBReadPolicy
   ```

2. **Verify the resource name matches the pattern**:
   - Expected pattern: `aws-drs-orchestration-*`
   - Actual resource: `external-table`
   - **Mismatch**: Resource does not match the pattern

**Resolution**:

This is **expected behavior** for resource-level restrictions. Function-specific roles can only access resources matching the project naming pattern.

If this is a legitimate operation:
1. Rename the resource to match the pattern: `aws-drs-orchestration-external-table-qa`
2. Or update the IAM role policy in `cfn/iam/roles-stack.yaml` to allow the specific resource
3. Redeploy the stack: `./scripts/deploy-main-stack.sh qa --use-function-specific-roles`

### AccessDenied: ExternalId mismatch

**Symptom**: Cross-account STS AssumeRole fails with `AccessDenied` error

**Example Error**:
```
An error occurred (AccessDenied) when calling the AssumeRole operation: 
User: arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-orchestration-role-qa/aws-drs-orchestration-dr-orch-sf-qa 
is not authorized to perform: sts:AssumeRole on resource: 
arn:aws:iam::123456789012:role/DRSOrchestrationRole 
because the ExternalId does not match
```

**Diagnosis**:

1. **Check the ExternalId in the Lambda code**:
   ```python
   # In lambda/orchestration/index.py
   external_id = os.environ.get("EXTERNAL_ID", "aws-drs-orchestration-qa")
   ```

2. **Check the ExternalId in the target account trust policy**:
   ```bash
   # In target account (123456789012)
   aws iam get-role \
     --role-name DRSOrchestrationRole \
     --query 'Role.AssumeRolePolicyDocument'
   ```

**Resolution**:

1. **Update the target account trust policy** to require the correct ExternalId:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::438465159935:root"
         },
         "Action": "sts:AssumeRole",
         "Condition": {
           "StringEquals": {
             "sts:ExternalId": "aws-drs-orchestration-qa"
           }
         }
       }
     ]
   }
   ```

2. **Verify the ExternalId matches** the pattern: `{ProjectName}-{Environment}`

## CloudFormation Deployment Errors

### CREATE_FAILED: Resource already exists

**Symptom**: CloudFormation stack creation fails with "Resource already exists" error

**Example Error**:
```
Resource creation failed: aws-drs-orchestration-query-handler-role-qa already exists
```

**Diagnosis**:

1. **Check if the resource exists**:
   ```bash
   aws iam get-role \
     --role-name aws-drs-orchestration-query-handler-role-qa \
     --region us-east-2
   ```

2. **Check if the resource is managed by another stack**:
   ```bash
   aws cloudformation describe-stack-resources \
     --physical-resource-id aws-drs-orchestration-query-handler-role-qa \
     --region us-east-2
   ```

**Resolution**:

1. **Delete the existing resource** (if not managed by CloudFormation):
   ```bash
   aws iam delete-role \
     --role-name aws-drs-orchestration-query-handler-role-qa
   ```

2. **Or delete the existing stack** (if managed by CloudFormation):
   ```bash
   aws cloudformation delete-stack \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2
   ```

3. **Retry the deployment**:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

### UPDATE_ROLLBACK_FAILED: Stack in failed state

**Symptom**: CloudFormation stack update fails and rollback also fails

**Example Error**:
```
Stack aws-drs-orchestration-qa is in UPDATE_ROLLBACK_FAILED state and cannot be updated
```

**Diagnosis**:

1. **Check the stack status**:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2 \
     --query 'Stacks[0].StackStatus'
   ```

2. **Check the stack events**:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2 \
     --max-items 20
   ```

**Resolution**:

The deployment script automatically handles this state:

```bash
# The script will:
# 1. Identify failed nested stacks
# 2. Run continue-update-rollback with skip resources
# 3. Wait for rollback to complete
# 4. Proceed with deployment

./scripts/deploy-main-stack.sh qa --use-function-specific-roles
```

Or manually recover:

```bash
# Continue the rollback
aws cloudformation continue-update-rollback \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2

# Wait for rollback to complete
aws cloudformation wait stack-rollback-complete \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2

# Retry the deployment
./scripts/deploy-main-stack.sh qa --use-function-specific-roles
```

### Nested stack creation failed

**Symptom**: Nested stack shows CREATE_FAILED status

**Example Error**:
```
Nested stack aws-drs-orchestration-iam-stack-qa failed to create
```

**Diagnosis**:

1. **Check the nested stack events**:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name aws-drs-orchestration-iam-stack-qa \
     --region us-east-2 \
     --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'
   ```

2. **Check the template URL**:
   ```bash
   # Verify the template exists in S3
   aws s3 ls s3://aws-drs-orchestration-438465159935-qa/cfn/iam/roles-stack.yaml --region us-east-2
   ```

3. **Check the template syntax**:
   ```bash
   cfn-lint cfn/iam/roles-stack.yaml
   ```

**Resolution**:

1. **Fix the template** (if syntax error)
2. **Sync the template to S3**:
   ```bash
   aws s3 sync cfn/ s3://aws-drs-orchestration-438465159935-qa/cfn/ --region us-east-2
   ```
3. **Retry the deployment**:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

### Parameter not found

**Symptom**: CloudFormation fails with "Parameter 'X' not found" error

**Example Error**:
```
Parameter 'QueryHandlerRoleArn' not found in nested stack outputs
```

**Diagnosis**:

1. **Check the nested stack outputs**:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name aws-drs-orchestration-iam-stack-qa \
     --region us-east-2 \
     --query 'Stacks[0].Outputs'
   ```

2. **Check the main stack parameter passing**:
   ```yaml
   # In cfn/main-stack.yaml
   LambdaStack:
     Type: AWS::CloudFormation::Stack
     Properties:
       Parameters:
         QueryHandlerRoleArn: !GetAtt IAMStack.Outputs.QueryHandlerRoleArn
   ```

**Resolution**:

1. **Add the missing output** to the nested stack template:
   ```yaml
   # In cfn/iam/roles-stack.yaml
   Outputs:
     QueryHandlerRoleArn:
       Description: ARN of query handler role
       Value: !If [UseFunctionSpecificRoles, !GetAtt QueryHandlerRole.Arn, '']
   ```

2. **Sync the template to S3**:
   ```bash
   aws s3 sync cfn/ s3://aws-drs-orchestration-438465159935-qa/cfn/ --region us-east-2
   ```

3. **Retry the deployment**:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

## Rollback Procedures

### Rollback to Unified Role

**When to use**: Function-specific roles are causing issues and you need to revert to the unified role

**Procedure**:

1. **Update the stack with UseFunctionSpecificRoles=false**:
   ```bash
   ./scripts/deploy-main-stack.sh qa  # Removes --use-function-specific-roles flag
   ```

2. **Monitor the stack update**:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2 \
     --max-items 20
   ```

3. **Verify the unified role is created**:
   ```bash
   aws iam get-role \
     --role-name aws-drs-orchestration-unified-role-qa
   ```

4. **Verify function-specific roles are deleted**:
   ```bash
   aws iam get-role \
     --role-name aws-drs-orchestration-query-handler-role-qa
   # Should return: NoSuchEntity error
   ```

5. **Test functionality**:
   ```bash
   # Run integration tests
   pytest tests/integration/ -v
   ```

**Expected Outcome**:
- Unified role is created
- Function-specific roles are deleted
- All Lambda functions use the unified role
- No data loss in DynamoDB
- No Step Functions execution interruption

### Rollback to Old Architecture

**When to use**: New main-stack.yaml architecture is causing issues and you need to revert to the old master-template.yaml

**Procedure**:

1. **Deploy the old stack**:
   ```bash
   ./scripts/deploy.sh qa  # Uses old master-template.yaml
   ```

2. **Monitor the stack update**:
   ```bash
   aws cloudformation describe-stack-events \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2 \
     --max-items 20
   ```

3. **Verify the old architecture is restored**:
   ```bash
   # Check for old unified role
   aws iam get-role \
     --role-name aws-drs-orchestration-orchestration-role-qa
   ```

4. **Test functionality**:
   ```bash
   # Run integration tests
   pytest tests/integration/ -v
   ```

**Expected Outcome**:
- Old unified role is created
- New function-specific roles are deleted
- All Lambda functions use the old unified role
- No data loss in DynamoDB
- No Step Functions execution interruption

### Emergency Rollback

**When to use**: Production outage caused by deployment

**Procedure**:

1. **IMMEDIATELY stop the deployment**:
   ```bash
   # Cancel the CloudFormation stack update
   aws cloudformation cancel-update-stack \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2
   ```

2. **Rollback to previous version**:
   ```bash
   # CloudFormation will automatically rollback to the previous state
   aws cloudformation wait stack-update-complete \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2
   ```

3. **Verify rollback completed**:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name aws-drs-orchestration-qa \
     --region us-east-2 \
     --query 'Stacks[0].StackStatus'
   # Should return: UPDATE_ROLLBACK_COMPLETE
   ```

4. **Test functionality**:
   ```bash
   # Run integration tests
   pytest tests/integration/ -v
   ```

5. **Document the incident**:
   - What caused the outage?
   - What was the impact?
   - What was the resolution?
   - How can we prevent this in the future?

## CloudWatch Logs Queries for Debugging

### Find AccessDenied Errors

**Query**:
```
fields @timestamp, @message
| filter @message like /AccessDenied/
| sort @timestamp desc
| limit 100
```

**Usage**:
```bash
# Run query in CloudWatch Logs Insights
aws logs start-query \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /AccessDenied/ | sort @timestamp desc | limit 100' \
  --region us-east-2
```

### Find Errors by Function

**Query**:
```
fields @timestamp, @message, @logStream
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

**Usage**:
```bash
# Run query for specific function
aws logs start-query \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message, @logStream | filter @message like /ERROR/ | sort @timestamp desc | limit 100' \
  --region us-east-2
```

### Find IAM Actions Performed

**Query**:
```
fields @timestamp, @message
| filter @message like /Calling AWS API/
| parse @message /Calling AWS API: (?<action>[^ ]+)/
| stats count() by action
| sort count desc
```

**Usage**:
```bash
# Run query to see all IAM actions
aws logs start-query \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /Calling AWS API/ | parse @message /Calling AWS API: (?<action>[^ ]+)/ | stats count() by action | sort count desc' \
  --region us-east-2
```

### Find Slow Lambda Invocations

**Query**:
```
fields @timestamp, @duration, @requestId
| filter @duration > 5000
| sort @duration desc
| limit 100
```

**Usage**:
```bash
# Run query to find slow invocations (>5 seconds)
aws logs start-query \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @duration, @requestId | filter @duration > 5000 | sort @duration desc | limit 100' \
  --region us-east-2
```

### Find Lambda Cold Starts

**Query**:
```
fields @timestamp, @initDuration, @requestId
| filter @type = "REPORT"
| filter @initDuration > 0
| sort @initDuration desc
| limit 100
```

**Usage**:
```bash
# Run query to find cold starts
aws logs start-query \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @initDuration, @requestId | filter @type = "REPORT" | filter @initDuration > 0 | sort @initDuration desc | limit 100' \
  --region us-east-2
```

## Using IAM Policy Simulator

### Simulate IAM Action

**Purpose**: Test if an IAM role has permission to perform a specific action

**Usage**:
```bash
# Simulate DynamoDB GetItem action
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::438465159935:role/aws-drs-orchestration-query-handler-role-qa \
  --action-names dynamodb:GetItem \
  --resource-arns "arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-protection-groups-qa"

# Output:
# {
#   "EvaluationResults": [
#     {
#       "EvalActionName": "dynamodb:GetItem",
#       "EvalResourceName": "arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-protection-groups-qa",
#       "EvalDecision": "allowed",
#       "MatchedStatements": [...]
#     }
#   ]
# }
```

### Simulate Multiple Actions

**Purpose**: Test multiple IAM actions at once

**Usage**:
```bash
# Simulate multiple DynamoDB actions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::438465159935:role/aws-drs-orchestration-query-handler-role-qa \
  --action-names dynamodb:GetItem dynamodb:PutItem dynamodb:DeleteItem \
  --resource-arns "arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-protection-groups-qa"

# Output shows which actions are allowed/denied
```

### Simulate with Context Keys

**Purpose**: Test IAM actions with condition keys (e.g., ExternalId)

**Usage**:
```bash
# Simulate STS AssumeRole with ExternalId
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::438465159935:role/aws-drs-orchestration-orchestration-role-qa \
  --action-names sts:AssumeRole \
  --resource-arns "arn:aws:iam::123456789012:role/DRSOrchestrationRole" \
  --context-entries "ContextKeyName=sts:ExternalId,ContextKeyValues=aws-drs-orchestration-qa,ContextKeyType=string"

# Output shows if the action is allowed with the ExternalId
```

## Performance Issues

### Lambda Function Timeout

**Symptom**: Lambda function times out before completing

**Diagnosis**:

1. **Check the function timeout**:
   ```bash
   aws lambda get-function-configuration \
     --function-name aws-drs-orchestration-query-handler-qa \
     --region us-east-2 \
     --query 'Timeout'
   ```

2. **Check CloudWatch Logs for duration**:
   ```bash
   aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-qa --since 5m --region us-east-2 | grep Duration
   ```

**Resolution**:

1. **Increase the function timeout** in `cfn/lambda/functions-stack.yaml`:
   ```yaml
   QueryHandlerFunction:
     Type: AWS::Lambda::Function
     Properties:
       Timeout: 300  # Increase from 60 to 300 seconds
   ```

2. **Optimize the function code** to reduce execution time
3. **Redeploy the stack**:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

### DynamoDB Throttling

**Symptom**: Lambda function fails with `ProvisionedThroughputExceededException`

**Diagnosis**:

1. **Check DynamoDB metrics**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/DynamoDB \
     --metric-name ConsumedReadCapacityUnits \
     --dimensions Name=TableName,Value=aws-drs-orchestration-protection-groups-qa \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 300 \
     --statistics Sum \
     --region us-east-2
   ```

**Resolution**:

1. **Enable DynamoDB auto-scaling** in `cfn/dynamodb/tables-stack.yaml`
2. **Or increase provisioned capacity**
3. **Or switch to on-demand billing mode**
4. **Redeploy the stack**:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

## Monitoring and Alerting Issues

### CloudWatch Alarm Not Triggering

**Symptom**: AccessDenied errors occur but CloudWatch alarm does not trigger

**Diagnosis**:

1. **Check the alarm configuration**:
   ```bash
   aws cloudwatch describe-alarms \
     --alarm-names aws-drs-orchestration-access-denied-qa \
     --region us-east-2
   ```

2. **Check the metric filter**:
   ```bash
   aws logs describe-metric-filters \
     --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
     --region us-east-2
   ```

3. **Check the metric data**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace aws-drs-orchestration/Security \
     --metric-name AccessDeniedErrors \
     --dimensions Name=FunctionName,Value=aws-drs-orchestration-query-handler-qa \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 300 \
     --statistics Sum \
     --region us-east-2
   ```

**Resolution**:

1. **Verify the metric filter pattern** matches the error message
2. **Verify the alarm threshold** is appropriate (default: 5 errors in 5 minutes)
3. **Verify the SNS topic** is subscribed to the correct email
4. **Test the alarm** by intentionally causing an AccessDenied error

### SNS Notification Not Received

**Symptom**: CloudWatch alarm triggers but SNS notification is not received

**Diagnosis**:

1. **Check the SNS subscription**:
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-security-alerts-qa \
     --region us-east-2
   ```

2. **Check the subscription status**:
   - Status should be "Confirmed"
   - If "PendingConfirmation", check email for confirmation link

**Resolution**:

1. **Confirm the SNS subscription** by clicking the link in the confirmation email
2. **Or resubscribe**:
   ```bash
   aws sns subscribe \
     --topic-arn arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-security-alerts-qa \
     --protocol email \
     --notification-endpoint jocousen@amazon.com \
     --region us-east-2
   ```

## Best Practices

### 1. Always Check CloudWatch Logs First

Before investigating IAM permission issues, check CloudWatch Logs for the exact error message:

```bash
aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-qa --since 5m --region us-east-2
```

### 2. Use IAM Policy Simulator for Testing

Test IAM permissions before deploying:

```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::438465159935:role/aws-drs-orchestration-query-handler-role-qa \
  --action-names dynamodb:GetItem \
  --resource-arns "arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-protection-groups-qa"
```

### 3. Test in QA Before Production

Always test changes in the QA environment before deploying to production:

```bash
# Deploy to QA
./scripts/deploy-main-stack.sh qa --use-function-specific-roles

# Run integration tests
pytest tests/integration/ -v

# Deploy to production (only after QA validation)
./scripts/deploy-main-stack.sh prod --use-function-specific-roles
```

### 4. Monitor CloudWatch Alarms

Set up CloudWatch alarms for AccessDenied errors and monitor them regularly:

```bash
# Check alarm status
aws cloudwatch describe-alarms \
  --alarm-names aws-drs-orchestration-access-denied-qa \
  --region us-east-2
```

### 5. Document All Changes

Document all IAM policy changes and deployment issues for future reference.

## Related Documentation

- [IAM Role Reference](IAM_ROLE_REFERENCE.md) - Detailed IAM role permissions
- [Testing Guide](TESTING_GUIDE.md) - Testing procedures
- [CloudFormation Template Organization](CFN_TEMPLATE_ORGANIZATION.md) - Template structure
- [QA Deployment Configuration](QA_DEPLOYMENT_CONFIGURATION.md) - QA environment setup
