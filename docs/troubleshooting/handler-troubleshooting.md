# Handler Troubleshooting Guide

**Date**: 2026-01-24  
**Version**: 1.0  
**Scope**: Query, Execution, and Data Management Handlers

## Overview

This guide provides troubleshooting procedures for common issues with the decomposed API handlers.

## Quick Diagnostics

### Health Check

Run this command first to check overall system health:

```bash
# Test all handlers
./scripts/test-query-handler.sh
./scripts/test-execution-handler.sh
./scripts/test-data-management-handler.sh
./scripts/test-end-to-end.sh

# Check CloudWatch Logs
aws logs tail /aws/lambda/hrp-drs-tech-adapter-query-handler-dev --since 5m
aws logs tail /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev --since 5m
aws logs tail /aws/lambda/hrp-drs-tech-adapter-data-management-handler-dev --since 5m
```

### Common Symptoms

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| 403 Forbidden | Authentication issue | Check Cognito token |
| 500 Internal Server Error | Lambda error | Check CloudWatch Logs |
| Timeout | Lambda timeout or DRS API slow | Increase timeout or check DRS |
| Cold start > 3s | Large package or memory | Optimize package or increase memory |
| DRS API throttling | Too many concurrent requests | Implement exponential backoff |
| Conflict detection false positive | Stale execution data | Check DynamoDB execution status |

---

## Query Handler Issues

### Issue 1: GET /drs/source-servers Returns Empty List

**Symptoms**:
- API returns `{"sourceServers": []}`
- Expected servers not showing up

**Diagnosis**:
```bash
# Check DRS source servers directly
aws drs describe-source-servers --region us-east-1

# Check cross-account role assumption
aws sts assume-role \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/DROrchestrationCrossAccountRole \
  --role-session-name test-session
```

**Possible Causes**:
1. No DRS source servers in the account/region
2. Cross-account role assumption failing
3. IAM permissions missing for `drs:DescribeSourceServers`

**Solutions**:

**Solution 1: Verify DRS source servers exist**
```bash
# List all DRS source servers
aws drs describe-source-servers --region us-east-1 \
  --query 'items[*].{SourceServerID:sourceServerID,Hostname:sourceProperties.identificationHints.hostname}' \
  --output table

# If empty, install DRS agent on source servers
```

**Solution 2: Fix cross-account role**
```bash
# Verify role exists
aws iam get-role --role-name DROrchestrationCrossAccountRole

# Update trust policy
aws iam update-assume-role-policy \
  --role-name DROrchestrationCrossAccountRole \
  --policy-document file://trust-policy.json
```

**Solution 3: Add IAM permissions**
```bash
# Attach DRS read policy
aws iam attach-role-policy \
  --role-name UnifiedOrchestrationRole \
  --policy-arn arn:aws:iam::aws:policy/AWSElasticDisasterRecoveryReadOnlyAccess
```

---

### Issue 2: GET /drs/quotas Returns Incorrect Capacity

**Symptoms**:
- Capacity shows 0 replicating servers when servers exist
- Capacity exceeds 300 (hard limit)

**Diagnosis**:
```bash
# Check DRS replication status
aws drs describe-source-servers --region us-east-1 \
  --query 'items[?dataReplicationInfo.dataReplicationState==`CONTINUOUS`]' \
  --output json | jq 'length'

# Check Query Handler logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-query-handler-dev \
  --filter-pattern "get_drs_account_capacity" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --limit 10
```

**Possible Causes**:
1. DRS API returning stale data
2. Query Handler caching old results
3. Filtering logic incorrect

**Solutions**:

**Solution 1: Force refresh**
```bash
# Update Lambda environment variable to force refresh
aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --environment Variables={FORCE_REFRESH=true}

# Wait for update
aws lambda wait function-updated \
  --function-name hrp-drs-tech-adapter-query-handler-dev

# Test again
curl -X GET "${API_ENDPOINT}/drs/quotas?region=us-east-1"
```

**Solution 2: Check filtering logic**
```bash
# Review Query Handler code
grep -A 20 "def get_drs_account_capacity" lambda/query-handler/index.py

# Verify dataReplicationState filter
# Should be: dataReplicationState == 'CONTINUOUS'
```

---

### Issue 3: GET /ec2/subnets Returns 403 Forbidden

**Symptoms**:
- API returns 403 Forbidden
- Error: "User: ... is not authorized to perform: ec2:DescribeSubnets"

**Diagnosis**:
```bash
# Check IAM role permissions
aws iam get-role-policy \
  --role-name UnifiedOrchestrationRole \
  --policy-name EC2ReadPolicy

# Test EC2 API directly
aws ec2 describe-subnets --region us-east-1 --max-results 5
```

**Possible Causes**:
1. IAM role missing EC2 read permissions
2. SCP (Service Control Policy) blocking EC2 API
3. VPC endpoint policy restricting access

**Solutions**:

**Solution 1: Add EC2 permissions**
```bash
# Create EC2 read policy
cat > ec2-read-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeInstanceTypes"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Attach policy
aws iam put-role-policy \
  --role-name UnifiedOrchestrationRole \
  --policy-name EC2ReadPolicy \
  --policy-document file://ec2-read-policy.json
```

**Solution 2: Check SCP**
```bash
# List SCPs attached to account
aws organizations list-policies-for-target \
  --target-id ACCOUNT_ID \
  --filter SERVICE_CONTROL_POLICY

# Review SCP content
aws organizations describe-policy --policy-id POLICY_ID
```

---

## Execution Handler Issues

### Issue 4: POST /recovery-plans/{id}/execute Returns 500 Error

**Symptoms**:
- API returns 500 Internal Server Error
- CloudWatch Logs show Step Functions error

**Diagnosis**:
```bash
# Check Execution Handler logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --limit 10

# Check Step Functions state machine
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:ACCOUNT:stateMachine:DROrchestrator
```

**Possible Causes**:
1. Step Functions state machine not found
2. IAM role missing `states:StartExecution` permission
3. Recovery plan not found in DynamoDB
4. Wave size validation failing

**Solutions**:

**Solution 1: Verify Step Functions state machine**
```bash
# List state machines
aws stepfunctions list-state-machines \
  --query 'stateMachines[?name==`DROrchestrator`]'

# If not found, deploy Step Functions stack
./scripts/deploy.sh dev
```

**Solution 2: Add Step Functions permissions**
```bash
# Create Step Functions policy
cat > stepfunctions-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:SendTaskSuccess",
        "states:SendTaskFailure"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Attach policy
aws iam put-role-policy \
  --role-name UnifiedOrchestrationRole \
  --policy-name StepFunctionsPolicy \
  --policy-document file://stepfunctions-policy.json
```

**Solution 3: Verify recovery plan exists**
```bash
# Query DynamoDB
aws dynamodb get-item \
  --table-name drs-orchestration-recovery-plans-dev \
  --key '{"recoveryPlanId": {"S": "PLAN_ID"}}'

# If not found, create recovery plan first
curl -X POST "${API_ENDPOINT}/recovery-plans" \
  -H "Authorization: $ID_TOKEN" \
  -d '{"name":"Test Plan","protectionGroupId":"PG_ID","waves":[...]}'
```

**Solution 4: Check wave size validation**
```bash
# Review wave sizes in recovery plan
aws dynamodb get-item \
  --table-name drs-orchestration-recovery-plans-dev \
  --key '{"recoveryPlanId": {"S": "PLAN_ID"}}' \
  --query 'Item.waves.L[*].M.servers.L | [*] | length(@)'

# Each wave should have <= 100 servers
# If > 100, update recovery plan to split waves
```

---

### Issue 5: GET /executions/{id} Returns 403 Forbidden

**Symptoms**:
- API returns 403 Forbidden
- Error: "Execution not found or access denied"

**Diagnosis**:
```bash
# Check if execution exists
aws dynamodb get-item \
  --table-name drs-orchestration-executions-dev \
  --key '{"executionId": {"S": "EXECUTION_ID"}}'

# Check Execution Handler logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev \
  --filter-pattern "get_execution_details" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --limit 10
```

**Possible Causes**:
1. Execution ID doesn't exist
2. Execution belongs to different user (RBAC)
3. DynamoDB read permissions missing

**Solutions**:

**Solution 1: Verify execution ID**
```bash
# List all executions
curl -X GET "${API_ENDPOINT}/executions" \
  -H "Authorization: $ID_TOKEN"

# Use valid execution ID from response
```

**Solution 2: Check RBAC permissions**
```bash
# Get user permissions
curl -X GET "${API_ENDPOINT}/user/permissions" \
  -H "Authorization: $ID_TOKEN"

# Verify user has 'executions:read' permission
```

**Solution 3: Add DynamoDB permissions**
```bash
# Create DynamoDB read policy
cat > dynamodb-read-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/drs-orchestration-*"
    }
  ]
}
EOF

# Attach policy
aws iam put-role-policy \
  --role-name UnifiedOrchestrationRole \
  --policy-name DynamoDBReadPolicy \
  --policy-document file://dynamodb-read-policy.json
```

---

### Issue 6: POST /executions/{id}/terminate Times Out

**Symptoms**:
- API returns 504 Gateway Timeout
- Termination takes > 300 seconds

**Diagnosis**:
```bash
# Check DRS termination job status
aws drs describe-jobs --region us-east-1 \
  --filters name=jobID,values=JOB_ID

# Check Execution Handler logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev \
  --filter-pattern "terminate_recovery_instances" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --limit 10
```

**Possible Causes**:
1. DRS API slow to terminate instances
2. Lambda timeout too short (300s)
3. Too many instances to terminate in one call

**Solutions**:

**Solution 1: Increase Lambda timeout**
```bash
# Increase timeout to 600 seconds
aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-execution-handler-dev \
  --timeout 600

# Wait for update
aws lambda wait function-updated \
  --function-name hrp-drs-tech-adapter-execution-handler-dev
```

**Solution 2: Implement async termination**
```bash
# Modify Execution Handler to return immediately after starting termination
# Poll termination status with GET /executions/{id}/termination-status

# Start termination (returns immediately)
curl -X POST "${API_ENDPOINT}/executions/${EXECUTION_ID}/terminate" \
  -H "Authorization: $ID_TOKEN"

# Poll status (every 30 seconds)
while true; do
  STATUS=$(curl -s -X GET "${API_ENDPOINT}/executions/${EXECUTION_ID}/termination-status" \
    -H "Authorization: $ID_TOKEN" | jq -r '.status')
  
  if [ "$STATUS" == "COMPLETED" ]; then
    echo "Termination complete"
    break
  fi
  
  echo "Status: $STATUS"
  sleep 30
done
```

**Solution 3: Batch termination**
```bash
# Terminate in batches of 50 instances
# Modify Execution Handler to split large terminations into multiple DRS API calls
```

---

## Data Management Handler Issues

### Issue 7: POST /protection-groups/resolve Returns Empty List

**Symptoms**:
- API returns `{"servers": []}`
- Expected servers not matching tags

**Diagnosis**:
```bash
# Check DRS source servers with tags
aws drs describe-source-servers --region us-east-1 \
  --query 'items[*].{SourceServerID:sourceServerID,Tags:tags}' \
  --output json

# Check Data Management Handler logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-data-management-handler-dev \
  --filter-pattern "resolve_protection_group_tags" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --limit 10
```

**Possible Causes**:
1. Tags don't match (case-sensitive)
2. Tag resolution using OR logic instead of AND
3. Servers not in CONTINUOUS replication state

**Solutions**:

**Solution 1: Verify tag matching**
```bash
# Check exact tag keys and values
aws drs describe-source-servers --region us-east-1 \
  --query 'items[0].tags' \
  --output json

# Tags are case-sensitive: "Environment" != "environment"
# Use exact tag keys and values in request
```

**Solution 2: Verify AND logic**
```bash
# Review tag resolution code
grep -A 30 "def query_drs_servers_by_tags" lambda/shared/drs_utils.py

# Should use AND logic: all tags must match
# Example: {"Environment": "Production", "Purpose": "Database"}
# Only servers with BOTH tags will match
```

**Solution 3: Check replication state**
```bash
# Verify servers are in CONTINUOUS state
aws drs describe-source-servers --region us-east-1 \
  --query 'items[?dataReplicationInfo.dataReplicationState==`CONTINUOUS`].sourceServerID' \
  --output json

# Only CONTINUOUS servers are included in tag resolution
```

---

### Issue 8: POST /protection-groups Returns 409 Conflict

**Symptoms**:
- API returns 409 Conflict
- Error: "Servers are in active executions"

**Diagnosis**:
```bash
# Check active executions
curl -X GET "${API_ENDPOINT}/executions?status=IN_PROGRESS" \
  -H "Authorization: $ID_TOKEN"

# Check conflict detection logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-data-management-handler-dev \
  --filter-pattern "check_server_conflicts" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --limit 10
```

**Possible Causes**:
1. Servers are in active DR executions
2. Stale execution data in DynamoDB
3. Conflict detection false positive

**Solutions**:

**Solution 1: Wait for execution to complete**
```bash
# Check execution status
curl -X GET "${API_ENDPOINT}/executions/${EXECUTION_ID}/status" \
  -H "Authorization: $ID_TOKEN"

# Wait for execution to complete or cancel it
curl -X POST "${API_ENDPOINT}/executions/${EXECUTION_ID}/cancel" \
  -H "Authorization: $ID_TOKEN"
```

**Solution 2: Clean up stale executions**
```bash
# List completed executions
curl -X GET "${API_ENDPOINT}/executions?status=COMPLETED" \
  -H "Authorization: $ID_TOKEN"

# Delete completed executions
curl -X DELETE "${API_ENDPOINT}/executions" \
  -H "Authorization: $ID_TOKEN" \
  -d '{"executionIds": ["EXEC_ID_1", "EXEC_ID_2"]}'
```

**Solution 3: Force create (bypass conflict detection)**
```bash
# Add force flag to request (use with caution)
curl -X POST "${API_ENDPOINT}/protection-groups" \
  -H "Authorization: $ID_TOKEN" \
  -d '{"name":"Test PG","servers":[...],"force":true}'
```

---

### Issue 9: PUT /protection-groups/{id} Returns 412 Precondition Failed

**Symptoms**:
- API returns 412 Precondition Failed
- Error: "Version conflict detected"

**Diagnosis**:
```bash
# Check current version
curl -X GET "${API_ENDPOINT}/protection-groups/${PG_ID}" \
  -H "Authorization: $ID_TOKEN" | jq '.version'

# Check Data Management Handler logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-data-management-handler-dev \
  --filter-pattern "update_protection_group" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --limit 10
```

**Possible Causes**:
1. Protection group was updated by another user
2. Optimistic locking version mismatch
3. Stale data in client

**Solutions**:

**Solution 1: Refresh and retry**
```bash
# Get latest version
LATEST=$(curl -s -X GET "${API_ENDPOINT}/protection-groups/${PG_ID}" \
  -H "Authorization: $ID_TOKEN")

VERSION=$(echo "$LATEST" | jq -r '.version')

# Update with latest version
curl -X PUT "${API_ENDPOINT}/protection-groups/${PG_ID}" \
  -H "Authorization: $ID_TOKEN" \
  -d "{\"name\":\"Updated PG\",\"version\":$VERSION,...}"
```

**Solution 2: Force update (bypass version check)**
```bash
# Add force flag to request (use with caution)
curl -X PUT "${API_ENDPOINT}/protection-groups/${PG_ID}" \
  -H "Authorization: $ID_TOKEN" \
  -d '{"name":"Updated PG","force":true,...}'
```

---

## Performance Issues

### Issue 10: Cold Start > 3 Seconds

**Symptoms**:
- First invocation takes > 3 seconds
- CloudWatch Logs show high init duration

**Diagnosis**:
```bash
# Check cold start times
aws logs filter-log-events \
  --log-group-name /aws/lambda/hrp-drs-tech-adapter-query-handler-dev \
  --filter-pattern "REPORT" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --limit 10 | grep "Init Duration"

# Check package size
ls -lh build/query-handler.zip
```

**Possible Causes**:
1. Large Lambda package (> 100 KB)
2. Too many dependencies
3. Insufficient memory allocation

**Solutions**:

**Solution 1: Optimize package size**
```bash
# Remove unnecessary dependencies
pip uninstall <unused-package>

# Rebuild package
python3 package_lambda.py

# Verify size reduction
ls -lh build/query-handler.zip
```

**Solution 2: Increase memory**
```bash
# Increase memory (more CPU allocated)
aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --memory-size 512

# Wait for update
aws lambda wait function-updated \
  --function-name hrp-drs-tech-adapter-query-handler-dev

# Test cold start again
./scripts/benchmark-handlers.sh
```

**Solution 3: Enable Provisioned Concurrency**
```bash
# Keep 2 instances warm
aws lambda put-provisioned-concurrency-config \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --provisioned-concurrent-executions 2 \
  --qualifier live

# Check status
aws lambda get-provisioned-concurrency-config \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --qualifier live
```

---

### Issue 11: API Response Time > 1 Second

**Symptoms**:
- API consistently takes > 1 second to respond
- CloudWatch Logs show high duration

**Diagnosis**:
```bash
# Check Lambda duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=hrp-drs-tech-adapter-query-handler-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --extended-statistics p95,p99

# Enable X-Ray tracing
aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --tracing-config Mode=Active
```

**Possible Causes**:
1. DRS API slow to respond
2. DynamoDB query inefficient
3. Too many cross-account API calls
4. No caching for read-only data

**Solutions**:

**Solution 1: Implement caching**
```bash
# Enable API Gateway caching
aws apigateway update-stage \
  --rest-api-id ${API_ID} \
  --stage-name dev \
  --patch-operations \
    op=replace,path=/cacheClusterEnabled,value=true \
    op=replace,path=/cacheClusterSize,value=0.5 \
    op=replace,path=/*/GET/caching/ttlInSeconds,value=300
```

**Solution 2: Optimize DynamoDB queries**
```bash
# Add GSI for common query patterns
aws dynamodb update-table \
  --table-name drs-orchestration-protection-groups-dev \
  --attribute-definitions \
    AttributeName=customerId,AttributeType=S \
    AttributeName=createdAt,AttributeType=N \
  --global-secondary-index-updates \
    '[{"Create":{"IndexName":"CustomerIndex","KeySchema":[{"AttributeName":"customerId","KeyType":"HASH"},{"AttributeName":"createdAt","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"},"ProvisionedThroughput":{"ReadCapacityUnits":5,"WriteCapacityUnits":5}}}]'
```

**Solution 3: Implement exponential backoff**
```bash
# Review DRS API call retry logic
grep -A 10 "def create_drs_client" lambda/shared/cross_account.py

# Should use boto3 retry config with exponential backoff
```

---

## Authentication Issues

### Issue 12: Cognito Authentication Failing

**Symptoms**:
- API returns 401 Unauthorized
- Error: "Invalid authentication token"

**Diagnosis**:
```bash
# Check Cognito user pool
aws cognito-idp describe-user-pool \
  --user-pool-id ${USER_POOL_ID}

# Check user exists
aws cognito-idp list-users \
  --user-pool-id ${USER_POOL_ID} \
  --filter "email = \"${EMAIL}\""
```

**Possible Causes**:
1. ID token expired (1 hour TTL)
2. User doesn't exist or is disabled
3. Cognito user pool misconfigured

**Solutions**:

**Solution 1: Refresh ID token**
```bash
# Get new ID token
ID_TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id "$USER_POOL_ID" \
  --client-id "$CLIENT_ID" \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME="$EMAIL",PASSWORD="$PASSWORD" \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test with new token
curl -X GET "${API_ENDPOINT}/health" \
  -H "Authorization: $ID_TOKEN"
```

**Solution 2: Enable user**
```bash
# Check user status
aws cognito-idp admin-get-user \
  --user-pool-id ${USER_POOL_ID} \
  --username ${USERNAME}

# Enable user if disabled
aws cognito-idp admin-enable-user \
  --user-pool-id ${USER_POOL_ID} \
  --username ${USERNAME}
```

**Solution 3: Reset password**
```bash
# Reset password
aws cognito-idp admin-set-user-password \
  --user-pool-id ${USER_POOL_ID} \
  --username ${USERNAME} \
  --password ${NEW_PASSWORD} \
  --permanent
```

---

## Monitoring and Debugging

### Enable Detailed Logging

```bash
# Enable DEBUG logging for all handlers
aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-query-handler-dev \
  --environment Variables={LOG_LEVEL=DEBUG}

aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-execution-handler-dev \
  --environment Variables={LOG_LEVEL=DEBUG}

aws lambda update-function-configuration \
  --function-name hrp-drs-tech-adapter-data-management-handler-dev \
  --environment Variables={LOG_LEVEL=DEBUG}
```

### Enable X-Ray Tracing

```bash
# Enable X-Ray for all handlers
for HANDLER in query-handler execution-handler data-management-handler; do
  aws lambda update-function-configuration \
    --function-name hrp-drs-tech-adapter-${HANDLER}-dev \
    --tracing-config Mode=Active
done

# View traces
aws xray get-trace-summaries \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --filter-expression 'service("hrp-drs-tech-adapter-query-handler-dev")'
```

### CloudWatch Insights Queries

**Error Rate by Handler**:
```sql
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by bin(5m)
```

**Cold Start Times**:
```sql
fields @timestamp, @initDuration
| filter @type = "REPORT"
| stats avg(@initDuration), max(@initDuration), min(@initDuration)
```

**API Latency by Endpoint**:
```sql
fields @timestamp, @duration, httpMethod, path
| filter @type = "REPORT"
| stats avg(@duration), p95(@duration), p99(@duration) by path
```

**DRS API Calls**:
```sql
fields @timestamp, @message
| filter @message like /drs:Describe/
| stats count() by bin(5m)
```

---

## Escalation Procedures

### Level 1: Self-Service

1. Check this troubleshooting guide
2. Review CloudWatch Logs
3. Run integration tests
4. Check AWS Service Health Dashboard

### Level 2: Team Support

If issue persists after Level 1:

1. Gather diagnostics:
```bash
# Collect logs
aws logs tail /aws/lambda/hrp-drs-tech-adapter-query-handler-dev --since 1h > query-handler.log
aws logs tail /aws/lambda/hrp-drs-tech-adapter-execution-handler-dev --since 1h > execution-handler.log
aws logs tail /aws/lambda/hrp-drs-tech-adapter-data-management-handler-dev --since 1h > data-management-handler.log

# Collect metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=hrp-drs-tech-adapter-query-handler-dev \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum > metrics.txt
```

2. Create support ticket with:
   - Issue description
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs and metrics
   - Environment (dev/test/prod)

### Level 3: AWS Support

If issue is AWS service-related:

1. Open AWS Support case
2. Provide:
   - AWS account ID
   - Region
   - Service (Lambda, DRS, API Gateway, etc.)
   - Error messages
   - CloudWatch Logs
   - X-Ray traces

---

## Related Documentation

- [API Handler Decomposition Architecture](../architecture/api-handler-decomposition.md)
- [Deployment Guide](../deployment/handler-deployment-guide.md)
- [Performance Benchmark Results](../performance/benchmark-results-20260124.md)
- [Load Testing Plan](../performance/load-testing-plan.md)

---

**Document Owner**: DR Orchestration Team  
**Review Frequency**: After each major release  
**Last Updated**: 2026-01-24
