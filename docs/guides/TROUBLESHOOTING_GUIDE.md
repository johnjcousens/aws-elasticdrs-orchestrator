# Troubleshooting Guide

**Version**: 2.1  
**Date**: January 1, 2026  
**Status**: Production Ready - EventBridge Security Enhancements Complete  

Complete troubleshooting guide for AWS DRS Orchestration Solution including EventBridge security validation and tag synchronization issues.

## Common Issues

### Application Issues

| Issue                     | Cause                           | Solution                                                |
| ------------------------- | ------------------------------- | ------------------------------------------------------- |
| `PG_NAME_EXISTS`        | Duplicate protection group name | Use a unique name                                       |
| `INVALID_SERVER_IDS`    | Server IDs not found in DRS     | Verify servers with `aws drs describe-source-servers` |
| `CIRCULAR_DEPENDENCY`   | Wave dependencies form a loop   | Review and fix dependency chain                         |
| `EXECUTION_IN_PROGRESS` | Plan already executing          | Wait for completion or cancel                           |

### DRS Recovery Failures

If recovery jobs fail with `UnauthorizedOperation` errors, verify the OrchestrationRole has required EC2 and DRS permissions.

**Critical Discovery**: When Lambda calls `drs:StartRecovery`, DRS uses the **calling role's IAM permissions** (not its service-linked role) to perform EC2 operations.

**Required Permissions**:
- `ec2:CreateLaunchTemplate`
- `ec2:CreateLaunchTemplateVersion`
- `ec2:ModifyLaunchTemplate`
- `ec2:StartInstances`
- `ec2:RunInstances`
- `ec2:CreateVolume`
- `ec2:AttachVolume`
- `drs:CreateRecoveryInstanceForDrs`

See [DRS Complete IAM Analysis](../reference/DRS_COMPLETE_IAM_ANALYSIS.md) for complete permission requirements.

### API Gateway Errors

#### 401 Unauthorized
**Cause**: Invalid or expired Cognito token.

**Solution**:
```bash
# Get new token
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id {client-id} \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME={email},PASSWORD={password} \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test API
curl -H "Authorization: Bearer $TOKEN" \
  https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/protection-groups
```

#### 403 Forbidden
**Cause**: Cognito authorizer rejecting token or missing permissions.

**Debugging**:
```bash
# Decode JWT token (base64)
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq .

# Check token expiration
echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq '.exp | todate'
```

#### 500 Internal Server Error
**Cause**: Lambda execution error.

**Debugging**:
```bash
# Check Lambda logs
AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestrator-api-handler-{env} \
  --since 5m \
  --region us-east-1
```

### Lambda Debugging

#### Check Lambda Configuration
```bash
AWS_PAGER="" aws lambda get-function-configuration \
  --function-name aws-drs-orchestrator-api-handler-{env} \
  --query '{Runtime:Runtime,MemorySize:MemorySize,Timeout:Timeout,Environment:Environment.Variables}' \
  --region us-east-1
```

#### Test Lambda Directly
```bash
# Create test event
cat > /tmp/test-event.json << 'EOF'
{
  "httpMethod": "GET",
  "path": "/protection-groups",
  "headers": {
    "Authorization": "Bearer xxx"
  },
  "queryStringParameters": null,
  "body": null
}
EOF

# Invoke Lambda
AWS_PAGER="" aws lambda invoke \
  --function-name aws-drs-orchestrator-api-handler-{env} \
  --payload file:///tmp/test-event.json \
  --cli-binary-format raw-in-base64-out \
  /tmp/response.json \
  --region us-east-1

cat /tmp/response.json | jq .
```

### DynamoDB Debugging

#### Query Tables Directly
```bash
# Scan Protection Groups
AWS_PAGER="" aws dynamodb scan \
  --table-name protection-groups-{env} \
  --region us-east-1

# Query specific item
AWS_PAGER="" aws dynamodb get-item \
  --table-name protection-groups-{env} \
  --key '{"GroupId": {"S": "xxx"}}' \
  --region us-east-1

# Query executions by status (using GSI)
AWS_PAGER="" aws dynamodb query \
  --table-name execution-history-{env} \
  --index-name StatusIndex \
  --key-condition-expression "#s = :status" \
  --expression-attribute-names '{"#s": "Status"}' \
  --expression-attribute-values '{":status": {"S": "PENDING"}}' \
  --region us-east-1
```

### Step Functions Debugging

#### Check Execution Status
```bash
# List recent executions
AWS_PAGER="" aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:{region}:{account}:stateMachine:xxx \
  --status-filter FAILED \
  --max-results 10 \
  --region us-east-1

# Get execution details
AWS_PAGER="" aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:{region}:{account}:execution:xxx:yyy \
  --region us-east-1

# Get execution history
AWS_PAGER="" aws stepfunctions get-execution-history \
  --execution-arn arn:aws:states:{region}:{account}:execution:xxx:yyy \
  --region us-east-1
```

### Frontend Debugging

#### Check Browser Console
Common issues:
- CORS errors: Check API Gateway CORS configuration
- 401 errors: Check Cognito token refresh
- Network errors: Check API endpoint URL

#### Check CloudFront
```bash
# Get distribution status
AWS_PAGER="" aws cloudfront get-distribution \
  --id {distribution-id} \
  --query 'Distribution.{Status:Status,DomainName:DomainName}' \
  --region us-east-1

# Check for recent invalidations
AWS_PAGER="" aws cloudfront list-invalidations \
  --distribution-id {distribution-id} \
  --region us-east-1
```

#### Check S3 Frontend Bucket
```bash
# List files
AWS_PAGER="" aws s3 ls s3://{frontend-bucket}/ --recursive

# Check aws-config.json
AWS_PAGER="" aws s3 cp s3://{frontend-bucket}/aws-config.json - | jq .
```

## DRS Integration Debugging

### Understanding DRS Recovery Flow

When Lambda calls `drs:StartRecovery`, the following happens:

1. **Lambda calls drs:StartRecovery** → DRS creates recovery job
2. **DRS uses CALLER's IAM permissions** → Lambda's IAM role must have EC2 + DRS permissions
3. **DRS creates conversion server** → Requires: `ec2:RunInstances`, `ec2:CreateVolume`
4. **DRS creates launch template** → Requires: `ec2:CreateLaunchTemplate`, `ec2:CreateLaunchTemplateVersion`
5. **DRS launches recovery instance** → Requires: `ec2:RunInstances`, `drs:CreateRecoveryInstanceForDrs`
6. **DRS registers recovery instance** → Requires: `drs:CreateRecoveryInstanceForDrs`

### Common DRS Errors and Solutions

#### Error: UnauthorizedOperation on CreateLaunchTemplateVersion
```
UnauthorizedOperation when calling CreateLaunchTemplateVersion operation
```

**Cause**: Lambda IAM role missing EC2 launch template permissions.

**Solution**: Add to Lambda IAM role:
```yaml
- ec2:CreateLaunchTemplate
- ec2:CreateLaunchTemplateVersion
- ec2:ModifyLaunchTemplate
- ec2:DeleteLaunchTemplate
- ec2:DeleteLaunchTemplateVersions
```

#### Error: AccessDeniedException on CreateRecoveryInstanceForDrs
```
AccessDeniedException when calling CreateRecoveryInstanceForDrs operation
```

**Cause**: Lambda IAM role missing DRS permission to register recovery instances.

**Solution**: Add to Lambda IAM role:
```yaml
- drs:CreateRecoveryInstanceForDrs
```

#### Error: LAUNCH_FAILED with No Recovery Instances
**Symptom**: DRS job shows LAUNCH_START then LAUNCH_FAILED, no recovery instances created.

**Debugging Steps**:
```bash
# 1. Get job details
AWS_PAGER="" aws drs describe-jobs \
  --filters jobIDs=drsjob-xxx \
  --region us-east-1

# 2. Get job log items for specific errors
AWS_PAGER="" aws drs describe-job-log-items \
  --job-id drsjob-xxx \
  --region us-east-1

# 3. Check CloudTrail for EC2 API failures
AWS_PAGER="" aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=RunInstances \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --region us-east-1
```

## Performance Debugging

### Lambda Cold Starts
```bash
# Check Lambda metrics
AWS_PAGER="" aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=aws-drs-orchestrator-api-handler-{env} \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average Maximum \
  --region us-east-1
```

### DynamoDB Performance
```bash
# Check consumed capacity
AWS_PAGER="" aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=protection-groups-{env} \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region us-east-1
```

## Useful Debugging Commands

### Quick Health Check Script
```bash
#!/bin/bash
# scripts/health-check.sh

REGION=${1:-us-east-1}
ENV=${2:-test}

echo "=== Health Check ==="

# Check Lambda
echo "Lambda:"
AWS_PAGER="" aws lambda get-function \
  --function-name aws-drs-orchestrator-api-handler-$ENV \
  --query 'Configuration.{State:State,LastModified:LastModified}' \
  --region $REGION

# Check API Gateway
echo "API Gateway:"
API_ID=$(aws apigateway get-rest-apis \
  --query "items[?name=='aws-drs-orchestrator-api-$ENV'].id" \
  --output text --region $REGION)
echo "API ID: $API_ID"

# Check DynamoDB tables
echo "DynamoDB Tables:"
for table in protection-groups recovery-plans execution-history; do
  AWS_PAGER="" aws dynamodb describe-table \
    --table-name $table-$ENV \
    --query 'Table.{Name:TableName,Status:TableStatus,ItemCount:ItemCount}' \
    --region $REGION 2>/dev/null || echo "$table-$ENV: NOT FOUND"
done

# Check CloudFront
echo "CloudFront:"
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestrator-$ENV \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text --region $REGION

echo "=== Health Check Complete ==="
```

## Rollback Procedures

If a deployment fails:

```bash
# 1. Identify the last working version
AWS_PAGER="" aws s3api list-object-versions \
  --bucket {deployment-bucket} \
  --prefix lambda/api-handler.zip \
  --query 'Versions[0:5].[VersionId,LastModified]'

# 2. Restore previous Lambda version
aws lambda update-function-code \
  --function-name aws-drs-orchestrator-api-handler-{env} \
  --s3-bucket {deployment-bucket} \
  --s3-key lambda/api-handler.zip \
  --s3-object-version {previous-version-id}

# 3. Or rollback CloudFormation
aws cloudformation rollback-stack \
  --stack-name aws-drs-orchestrator-{env}
```

## Additional Resources

- [DRS Drill Failure Analysis](../troubleshooting/DRS_DRILL_FAILURE_ANALYSIS.md) - Common drill failure patterns
- [IAM Permission Troubleshooting](../troubleshooting/IAM_ROLE_ANALYSIS_DRS_PERMISSIONS.md) - IAM permission requirements
- [CloudFormation Deployment Issues](../troubleshooting/CLOUDFORMATION_DEPLOYMENT_ISSUES.md) - CloudFormation problems
- [Drill Debugging Checklist](../troubleshooting/DRILL_DEBUGGING_CHECKLIST.md) - Step-by-step drill troubleshooting

---

## EventBridge Security Issues (v2.1)

### EventBridge Security Validation Failures

| Issue | Cause | Solution |
|-------|-------|----------|
| `SECURITY_VALIDATION_FAILED` | IP not in whitelist | Add client IP to allowed CIDR ranges |
| `TEMPORAL_VALIDATION_FAILED` | Operation outside allowed time window | Check time-based access controls |
| `REQUEST_STRUCTURE_INVALID` | Malformed EventBridge event | Validate event structure against schema |
| `RULE_NAME_VALIDATION_FAILED` | EventBridge rule name not approved | Use approved rule naming patterns |

**Debugging Commands**:
```bash
# Check EventBridge security validation logs
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/drs-orchestration-eventbridge-security \
  --filter-pattern "SECURITY_VALIDATION_FAILED" \
  --start-time $(($(date +%s) - 3600))000 | head -10

# Verify EventBridge rule configuration
AWS_PAGER="" aws events describe-rule \
  --name drs-orchestration-tag-sync | head -20
```

### Tag Synchronization Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `TAG_SYNC_FAILED` | DRS API permissions missing | Add `drs:TagResource` and `drs:UntagResource` permissions |
| `EC2_TAG_READ_FAILED` | EC2 permissions missing | Add `ec2:DescribeTags` permission |
| `TAG_CONFLICT_DETECTED` | Conflicting tag values | Review conflict resolution policy |
| `SYNC_FREQUENCY_EXCEEDED` | Too many sync operations | Adjust EventBridge schedule frequency |

**Debugging Commands**:
```bash
# Check tag sync execution logs
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/drs-orchestration-tag-sync \
  --filter-pattern "TAG_SYNC" \
  --start-time $(($(date +%s) - 3600))000 | head -15

# Monitor tag sync Lambda errors
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/drs-orchestration-tag-sync \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s) - 86400))000 | head -10
```

---

## Version 2.1 Specific Issues

### EventBridge Rule Deployment Failures

**Issue**: CloudFormation fails to create EventBridge rules
**Cause**: Missing EventBridge permissions in deployment role
**Solution**:
```bash
# Add EventBridge permissions to deployment role
aws iam attach-role-policy \
  --role-name CloudFormation-Deployment-Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess
```

### Security Validation Performance Issues

**Issue**: High latency in API responses due to security validation
**Cause**: Multiple security validation layers
**Solution**: Optimize validation by caching IP whitelist and time windows

### Tag Sync Lambda Timeout

**Issue**: Tag sync Lambda function timing out
**Cause**: Large number of EC2 instances to process
**Solution**: Implement pagination and batch processing:
```python
# Process EC2 instances in batches
BATCH_SIZE = 50
for i in range(0, len(instances), BATCH_SIZE):
    batch = instances[i:i + BATCH_SIZE]
    process_tag_sync_batch(batch)
```