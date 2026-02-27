# Test Stack Deployment Summary

## Stack Information

**Deployment Date**: February 25, 2026  
**Stack Name**: `aws-drs-orchestration-test`  
**Region**: `us-east-2`  
**Account**: `438465159935`  
**Status**: `CREATE_COMPLETE`  
**Stack ARN**: `arn:aws:cloudformation:us-east-2:438465159935:stack/aws-drs-orchestration-test/ca752af0-1286-11f1-9f26-06c071e37837`

## Key Resources

### API Gateway
- **API ID**: `434getjyia`
- **Endpoint**: `https://434getjyia.execute-api.us-east-2.amazonaws.com/test`

### CloudFront
- **Distribution ID**: `E3KZFEQ5LZSFXU`
- **URL**: `https://d2hwh0tbw91md5.cloudfront.net`

### Cognito
- **User Pool ID**: `us-east-2_x8Jdxn8Z8`
- **User Pool Client ID**: `4li1onhahkjek28716a7eajhso`
- **Identity Pool ID**: `us-east-2:6499cddc-2b13-4830-9094-773b3017cb54`

### Lambda Functions
- **Data Management Handler**: `aws-drs-orchestration-data-management-handler-test`
- **Execution Handler**: `aws-drs-orchestration-execution-handler-test`
- **Query Handler**: `aws-drs-orchestration-query-handler-test`
- **Orchestration Function**: `aws-drs-orchestration-dr-orch-sf-test`

### DynamoDB Tables
- **Target Accounts**: `aws-drs-orchestration-target-accounts-test`
- **Protection Groups**: `aws-drs-orchestration-protection-groups-test`
- **Recovery Plans**: `aws-drs-orchestration-recovery-plans-test`
- **Execution History**: `aws-drs-orchestration-execution-history-test`
- **Recovery Instances Cache**: `aws-drs-orchestration-recovery-instances-test`

### S3 Buckets
- **Deployment Bucket**: `aws-drs-orchestration-438465159935-test`
- **Frontend Bucket**: `aws-drs-orchestration-fe-438465159935-test`

### IAM Roles
- **Orchestration Role**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-orchestration-role-test`
- **EventBridge Role**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-eventbridge-invoke-test`

### Step Functions
- **State Machine**: `arn:aws:states:us-east-2:438465159935:stateMachine:aws-drs-orchestration-orchestration-test`

### EventBridge Rules
- **Execution Polling**: `aws-drs-orchestration-execution-polling-schedule-test` (1 minute)
- **Inventory Sync**: `aws-drs-orchestration-inventory-sync-test` (15 minutes)
- **Recovery Instance Sync**: `aws-drs-orchestration-recovery-instance-sync-test` (5 minutes)
- **Staging Account Sync**: `aws-drs-orchestration-staging-account-sync-test` (5 minutes)
- **Tag Sync**: `aws-drs-orchestration-tag-sync-schedule-test` (1 hour)

## Nested Stacks

All nested stacks deployed successfully:

1. **ApiAuthStack** - Cognito authentication
2. **ApiGatewayCoreStack** - API Gateway base resources
3. **ApiGatewayCoreMethodsStack** - Core API methods
4. **ApiGatewayInfrastructureMethodsStack** - Infrastructure API methods
5. **ApiGatewayOperationsMethodsStack** - Operations API methods
6. **ApiGatewayResourcesStack** - API Gateway resources
7. **ApiGatewayDeploymentStack** - API Gateway deployment
8. **DatabaseStack** - DynamoDB tables
9. **EventBridgeStack** - EventBridge rules and targets
10. **FrontendStack** - S3 + CloudFront frontend hosting
11. **LambdaStack** - Lambda functions
12. **MonitoringStack** - CloudWatch alarms and dashboards
13. **NotificationStack** - SNS topics for alerts
14. **StepFunctionsStack** - Step Functions state machine

## Deployment Configuration

### Parameters Used
- **ProjectName**: `aws-drs-orchestration`
- **Environment**: `test`
- **DeploymentBucket**: `aws-drs-orchestration-438465159935-test`
- **AdminEmail**: `jocousen@amazon.com`
- **EnableWAF**: `true`
- **EnableNotifications**: `true`
- **EnableExecutionPolling**: `true`

### Region Configuration
- **Primary Region**: `us-east-2` (Lambda control plane)
- **DRS Source Regions**: Multi-region (us-east-2, us-west-2, etc.)
- Lambda functions make cross-region API calls to DRS in target regions

## Verification Commands

### Check Stack Status
```bash
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-test \
  --region us-east-2 \
  --profile AdministratorAccess-438465159935 \
  --query 'Stacks[0].StackStatus'
```

### List All Resources
```bash
AWS_PAGER="" aws cloudformation list-stack-resources \
  --stack-name aws-drs-orchestration-test \
  --region us-east-2 \
  --profile AdministratorAccess-438465159935
```

### Test API Endpoint
```bash
curl https://434getjyia.execute-api.us-east-2.amazonaws.com/test/health
```

### Test CloudFront
```bash
curl https://d2hwh0tbw91md5.cloudfront.net
```

## Manual Sync Triggers

### Trigger Inventory Sync
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"sync_source_server_inventory"}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Trigger Execution Polling
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-test \
  --payload '{"operation":"find"}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Trigger Recovery Instance Sync
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"sync_recovery_instances"}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Trigger Staging Account Sync
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"sync_staging_accounts"}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Trigger Tag Sync
```bash
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"synch_tags":true,"synch_instance_type":true}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json
```

## Next Steps

1. **Configure Target Accounts**: Add target accounts via API or DynamoDB
2. **Test Inventory Sync**: Trigger manual inventory sync to populate source servers
3. **Create Protection Groups**: Define protection groups for DR scenarios
4. **Test Recovery Plans**: Create and test recovery plans
5. **Monitor EventBridge Rules**: Verify scheduled syncs are running
6. **Test Frontend**: Access CloudFront URL and verify UI functionality

## Documentation Updates

All documentation has been updated to reflect the new test environment:

- ✅ `scripts/deploy.sh` - Default region changed to us-east-2
- ✅ `.kiro/steering/aws-stack-protection.md` - Updated to us-east-2
- ✅ `.kiro/steering/deployment-guide.md` - Updated with test stack details
- ✅ `.kiro/steering/cicd-workflow-enforcement.md` - Updated examples to test
- ✅ `docs/EVENTBRIDGE_RULES_REFERENCE.md` - Updated all Lambda ARNs and regions

## Related Documentation

- [EventBridge Rules Reference](./EVENTBRIDGE_RULES_REFERENCE.md)
- [AWS Stack Protection Rules](../.kiro/steering/aws-stack-protection.md)
- [CI/CD Workflow Enforcement](../.kiro/steering/cicd-workflow-enforcement.md)
- [Deployment Guide](../.kiro/steering/deployment-guide.md)
