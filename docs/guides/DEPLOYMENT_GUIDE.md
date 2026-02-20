# Deployment Guide

## Overview

This guide covers deployment procedures for the DR Orchestration Platform, including handler responsibilities, EventBridge routing, Step Functions integration, and the refactored query-handler read-only architecture.

## Handler Deployment Architecture

### Lambda Handlers

**data-management-handler**:
- **Purpose**: CRUD operations + data synchronization
- **Invocation**: API Gateway (frontend) + EventBridge (scheduled sync)
- **Size**: ~10,551 lines, 0.17 MB deployment package
- **Operations**: Protection groups, recovery plans, inventory sync, staging sync

**execution-handler**:
- **Purpose**: Recovery actions + wave completion sync
- **Invocation**: API Gateway (frontend) + Step Functions (wave updates)
- **Size**: ~7,831 lines, 16.06 MB deployment package
- **Operations**: Start recovery, cancel execution, terminate instances, wave status updates

**query-handler**:
- **Purpose**: Read-only queries + audit logging
- **Invocation**: API Gateway (frontend) + Step Functions (wave polling) + EventBridge (scheduled queries)
- **Size**: ~6,564 lines, 16.04 MB deployment package
- **Operations**: List executions, poll DRS jobs, server status, dashboard data
- **Critical**: NO WRITE OPERATIONS (except audit logging)

## EventBridge Scheduled Operations

### Source Server Inventory Sync

**Target**: data-management-handler

**Schedule**: Every 5 minutes

**CloudFormation**:
```yaml
SourceServerInventorySyncRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub "${ProjectName}-inventory-sync-${Environment}"
    Description: Sync DRS source server inventory
    ScheduleExpression: rate(5 minutes)
    State: ENABLED
    Targets:
      - Arn: !GetAtt DataManagementHandler.Arn
        Id: DataManagementHandlerTarget
        Input: '{"operation": "handle_sync_source_server_inventory"}'

InventorySyncPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref DataManagementHandler
    Action: lambda:InvokeFunction
    Principal: events.amazonaws.com
    SourceArn: !GetAtt SourceServerInventorySyncRule.Arn
```

### Staging Account Sync

**Target**: data-management-handler

**Schedule**: Every 15 minutes

**CloudFormation**:
```yaml
StagingAccountSyncRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub "${ProjectName}-staging-sync-${Environment}"
    Description: Sync staging account servers
    ScheduleExpression: rate(15 minutes)
    State: ENABLED
    Targets:
      - Arn: !GetAtt DataManagementHandler.Arn
        Id: DataManagementHandlerTarget
        Input: '{"operation": "handle_sync_staging_accounts"}'

StagingSyncPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref DataManagementHandler
    Action: lambda:InvokeFunction
    Principal: events.amazonaws.com
    SourceArn: !GetAtt StagingAccountSyncRule.Arn
```

### Recovery Instance Sync

**Target**: data-management-handler

**Schedule**: Every 10 minutes

**CloudFormation**:
```yaml
RecoveryInstanceSyncRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub "${ProjectName}-recovery-instance-sync-${Environment}"
    Description: Sync recovery instance inventory
    ScheduleExpression: rate(10 minutes)
    State: ENABLED
    Targets:
      - Arn: !GetAtt DataManagementHandler.Arn
        Id: DataManagementHandlerTarget
        Input: '{"operation": "handle_sync_recovery_instances"}'
```

## Step Functions Integration

### Wave Polling with Dual Handler Invocation

The Step Functions state machine invokes both query-handler (read) and execution-handler (write) for wave status polling:

```json
{
  "WavePoll": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:query-handler",
    "Comment": "Poll DRS job status (READ-ONLY)",
    "Parameters": {
      "operation": "poll_wave_status",
      "execution_id.$": "$.execution_id",
      "plan_id.$": "$.plan_id",
      "job_id.$": "$.job_id",
      "current_wave_number.$": "$.current_wave_number",
      "servers.$": "$.servers"
    },
    "ResultPath": "$.wave_status",
    "Next": "UpdateWaveStatus"
  },
  "UpdateWaveStatus": {
    "Type": "Task",
    "Resource": "arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:execution-handler",
    "Comment": "Update wave completion status (WRITE)",
    "Parameters": {
      "action": "update_wave_completion_status",
      "executionId.$": "$.execution_id",
      "planId.$": "$.plan_id",
      "waveNumber.$": "$.current_wave_number",
      "status.$": "$.wave_status.job_status",
      "waveData.$": "$.wave_status"
    },
    "ResultPath": "$.update_result",
    "Next": "CheckWaveComplete"
  },
  "CheckWaveComplete": {
    "Type": "Choice",
    "Choices": [
      {
        "Variable": "$.wave_status.wave_completed",
        "BooleanEquals": true,
        "Next": "WaveCompleted"
      }
    ],
    "Default": "WaitForWaveProgress"
  }
}
```

## Deployment Procedures

### Standard Deployment

Use the unified deploy script for all deployments:

```bash
# Full deployment (validation, security, tests, deploy)
./scripts/deploy.sh qa

# Lambda-only update (fast code update)
./scripts/deploy.sh qa --lambda-only

# Frontend-only update
./scripts/deploy.sh qa --frontend-only

# Validation only (no deployment)
./scripts/deploy.sh qa --validate-only
```

### Handler-Specific Deployments

**Deploy data-management-handler only**:
```bash
# Update CloudFormation with data-management-handler changes
./scripts/deploy.sh qa --lambda-only

# Verify EventBridge rules
aws events list-rules --name-prefix "aws-drs-orchestration" --region us-east-2

# Test inventory sync
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-qa \
  --payload '{"operation": "handle_sync_source_server_inventory"}' \
  response.json
```

**Deploy execution-handler only**:
```bash
# Update CloudFormation with execution-handler changes
./scripts/deploy.sh qa --lambda-only

# Test wave completion update
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-qa \
  --payload '{"action": "update_wave_completion_status", "executionId": "test", "planId": "test", "waveNumber": 1, "status": "completed", "waveData": {}}' \
  response.json
```

**Deploy query-handler only**:
```bash
# Update CloudFormation with query-handler changes
./scripts/deploy.sh qa --lambda-only

# Test read-only operation
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-qa \
  --payload '{"operation": "list_executions"}' \
  response.json

# Verify NO write operations
grep -r "update_item\|put_item\|delete_item" lambda/query-handler/index.py
# Should only find audit logging writes
```

### Verify Deployment

**Check Lambda Functions**:
```bash
# List all Lambda functions
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `aws-drs-orchestration`)].{Name:FunctionName,Size:CodeSize,Modified:LastModified}' \
  --output table

# Check specific handler
aws lambda get-function \
  --function-name aws-drs-orchestration-query-handler-qa \
  --query 'Configuration.{Runtime:Runtime,Memory:MemorySize,Timeout:Timeout,Size:CodeSize}'
```

**Check EventBridge Rules**:
```bash
# List EventBridge rules
aws events list-rules \
  --name-prefix "aws-drs-orchestration" \
  --region us-east-2 \
  --query 'Rules[].{Name:Name,State:State,Schedule:ScheduleExpression}'

# Check rule targets
aws events list-targets-by-rule \
  --rule aws-drs-orchestration-inventory-sync-qa \
  --region us-east-2
```

**Check Step Functions State Machine**:
```bash
# Describe state machine
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-2:891376951562:stateMachine:dr-orchestration-qa \
  --query '{Name:name,Status:status,Created:creationDate}'

# List recent executions
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-2:891376951562:stateMachine:dr-orchestration-qa \
  --max-results 10
```

## Rollback Procedures

### Rollback Lambda Function

```bash
# List function versions
aws lambda list-versions-by-function \
  --function-name aws-drs-orchestration-query-handler-qa

# Update alias to previous version
aws lambda update-alias \
  --function-name aws-drs-orchestration-query-handler-qa \
  --name live \
  --function-version 5  # Previous version
```

### Rollback CloudFormation Stack

```bash
# Cancel stack update
aws cloudformation cancel-update-stack \
  --stack-name aws-drs-orchestration-qa

# Or rollback to previous version
aws cloudformation continue-update-rollback \
  --stack-name aws-drs-orchestration-qa
```

### Rollback EventBridge Rules

```bash
# Disable rule
aws events disable-rule \
  --name aws-drs-orchestration-inventory-sync-qa

# Update rule target
aws events put-targets \
  --rule aws-drs-orchestration-inventory-sync-qa \
  --targets Id=1,Arn=arn:aws:lambda:us-east-2:891376951562:function:query-handler  # Old target
```

## Monitoring and Validation

### CloudWatch Metrics

**Lambda Invocations**:
```bash
# Query handler invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=aws-drs-orchestration-query-handler-qa \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

**Lambda Errors**:
```bash
# Query handler errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=aws-drs-orchestration-query-handler-qa \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### CloudWatch Logs

**Query Lambda Logs**:
```bash
# Query handler logs
aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-qa --since 1h

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Audit Log Validation

**Verify Audit Logging**:
```bash
# Query recent audit logs
aws dynamodb scan \
  --table-name aws-drs-orchestration-audit-logs-qa \
  --filter-expression "attribute_exists(invocation_mode)" \
  --limit 10

# Query by invocation mode
aws dynamodb query \
  --table-name aws-drs-orchestration-audit-logs-qa \
  --index-name InvocationModeIndex \
  --key-condition-expression "invocation_mode = :mode" \
  --expression-attribute-values '{":mode": {"S": "DIRECT_LAMBDA"}}'
```

## Troubleshooting

### Issue: EventBridge rule not triggering

**Diagnosis**:
```bash
# Check rule state
aws events describe-rule --name aws-drs-orchestration-inventory-sync-qa

# Check rule targets
aws events list-targets-by-rule --rule aws-drs-orchestration-inventory-sync-qa

# Check Lambda permissions
aws lambda get-policy --function-name aws-drs-orchestration-data-management-handler-qa
```

**Solution**:
1. Verify rule is ENABLED
2. Verify target Lambda function ARN is correct
3. Verify Lambda permission allows EventBridge invocation

### Issue: Step Functions execution fails at UpdateWaveStatus

**Diagnosis**:
```bash
# Get execution history
aws stepfunctions get-execution-history \
  --execution-arn arn:aws:states:us-east-2:891376951562:execution:dr-orchestration-qa:exec-123

# Check execution-handler logs
aws logs tail /aws/lambda/aws-drs-orchestration-execution-handler-qa --since 1h
```

**Solution**:
1. Verify execution-handler has `update_wave_completion_status` function
2. Verify DynamoDB permissions for execution-handler
3. Check Step Functions IAM role has `lambda:InvokeFunction` permission

### Issue: Query-handler performing write operations

**Diagnosis**:
```bash
# Search for write operations in query-handler
grep -r "update_item\|put_item\|delete_item" lambda/query-handler/index.py

# Check CloudWatch Logs for DynamoDB writes
aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-qa \
  --filter-pattern "update_item" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

**Solution**:
1. Verify query-handler code has NO write operations (except audit logging)
2. Redeploy query-handler with corrected code
3. Verify EventBridge rules target correct handlers

## Related Documentation

- [Handler Responsibilities](../architecture/HANDLER_RESPONSIBILITIES.md)
- [Dual Invocation Mode Architecture](../architecture/DUAL_INVOCATION_MODE.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Deployment Flexibility Guide](DEPLOYMENT_FLEXIBILITY_GUIDE.md)
