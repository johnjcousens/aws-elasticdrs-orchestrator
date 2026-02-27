# EventBridge Rules Reference

Complete reference for all EventBridge scheduled rules in the DR Orchestration Platform.

## Environment Details

- **Account**: 438465159935
- **Region**: us-east-2
- **Stack**: aws-drs-orchestration-test
- **Orchestration Role**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-orchestration-role-test`

## Overview

The platform uses EventBridge scheduled rules to automate background synchronization tasks. All rules invoke Lambda functions using the `aws-drs-orchestration-eventbridge-invoke-test` IAM role.

## Quick Reference Table

| Rule Name | Schedule | Lambda Function | Operation | Purpose |
|-----------|----------|-----------------|-----------|---------|
| execution-polling-schedule | 1 minute | execution-handler | `find` | Poll active DR executions |
| inventory-sync | 15 minutes | data-management-handler | `sync_source_server_inventory` | Sync DRS source servers |
| recovery-instance-sync | 5 minutes | data-management-handler | `sync_recovery_instances` | Sync recovery instances |
| staging-account-sync | 5 minutes | data-management-handler | `sync_staging_accounts` | Discover staging accounts |
| tag-sync-schedule | 1 hour | data-management-handler | Tag sync payload | Sync DRS tags to EC2 |

## Detailed Rule Documentation

### 1. Execution Polling Schedule

**Rule Name**: `aws-drs-orchestration-execution-polling-schedule-test`

**Purpose**: Continuously monitors and updates the status of active DR recovery executions.

**Schedule**: Every 1 minute

**Lambda Function**: `aws-drs-orchestration-execution-handler-test`

**Payload**:
```json
{
  "operation": "find"
}
```

**What It Does**:
- Queries DynamoDB for executions with status `IN_PROGRESS`
- Polls DRS API for job status updates
- Updates execution records with current status
- Handles completion, failures, and timeouts

**Manual Trigger**:
```bash
# Using orchestration role (recommended)
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-test \
  --payload '{"operation":"find"}' \
  --profile {orchestration-role-profile} \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json

# Using admin role
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-test \
  --payload '{"operation":"find"}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json
```

**Handler Function**: `lambda/execution-handler/index.py::find_and_poll_active_executions()`

---

### 2. Inventory Sync

**Rule Name**: `aws-drs-orchestration-inventory-sync-test`

**Purpose**: Maintains up-to-date inventory of all DRS source servers across target accounts.

**Schedule**: Every 15 minutes

**Lambda Function**: `aws-drs-orchestration-data-management-handler-test`

**Payload**:
```json
{
  "operation": "sync_source_server_inventory"
}
```

**What It Does**:
- Queries all target accounts from DynamoDB
- For each account and region:
  - Calls DRS `describe_source_servers` API
  - Enriches with EC2 instance metadata (tags, instance type, etc.)
  - Transforms data for frontend consumption
- Writes/updates records in `source-server-inventory-test` table
- Populates critical fields:
  - `sourceAccountId` (GSI partition key)
  - `replicationRegion` (GSI sort key)
  - `lastUpdated` (for freshness checks)
  - `tags` (for tag-based filtering)
  - Server metadata (hostname, IP, state, etc.)

**Manual Trigger**:
```bash
# Using orchestration role (recommended)
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"sync_source_server_inventory"}' \
  --profile {orchestration-role-profile} \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json

# Using admin role
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"sync_source_server_inventory"}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json

# View response
cat response.json | jq .
```

**Expected Response**:
```json
{
  "message": "Source server inventory sync complete",
  "totalSynced": 308,
  "totalErrors": 0,
  "timestamp": "2026-02-25T16:48:22.956827+00:00"
}
```

**Handler Function**: `lambda/data-management-handler/index.py::handle_sync_source_server_inventory()`

**Database Impact**:
- Table: `aws-drs-orchestration-source-server-inventory-test`
- Operation: Batch write (upsert)
- Records: ~300-500 per sync
- GSI: `SourceAccountIndex` (sourceAccountId + replicationRegion)

---

### 3. Recovery Instance Sync

**Rule Name**: `aws-drs-orchestration-recovery-instance-sync-test`

**Purpose**: Tracks active recovery instances launched by DRS for monitoring and cleanup.

**Schedule**: Every 5 minutes

**Lambda Function**: `aws-drs-orchestration-data-management-handler-test`

**Payload**:
```json
{
  "operation": "sync_recovery_instances"
}
```

**What It Does**:
- Queries DRS for active recovery instances
- Enriches with EC2 instance details
- Tracks instance state and lifecycle
- Enables recovery instance monitoring

**Manual Trigger**:
```bash
# Using orchestration role (recommended)
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"sync_recovery_instances"}' \
  --profile {orchestration-role-profile} \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json

# Using admin role
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"sync_recovery_instances"}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json
```

**Handler Function**: `lambda/data-management-handler/index.py::handle_recovery_instance_sync()`

**Database Impact**:
- Table: `aws-drs-orchestration-recovery-instances-test`
- Operation: Batch write (upsert)

---

### 4. Staging Account Sync

**Rule Name**: `aws-drs-orchestration-staging-account-sync-test`

**Purpose**: Automatically discovers and registers staging accounts used for DRS replication.

**Schedule**: Every 5 minutes

**Lambda Function**: `aws-drs-orchestration-data-management-handler-test`

**Payload**:
```json
{
  "operation": "sync_staging_accounts"
}
```

**What It Does**:
- Scans target accounts for DRS staging account references
- Discovers new staging accounts automatically
- Updates staging account metadata
- Maintains staging account inventory

**Manual Trigger**:
```bash
# Using orchestration role (recommended)
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"sync_staging_accounts"}' \
  --profile {orchestration-role-profile} \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json

# Using admin role
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"sync_staging_accounts"}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json
```

**Handler Function**: `lambda/data-management-handler/index.py::handle_sync_staging_accounts()`

---

### 5. Tag Sync Schedule

**Rule Name**: `aws-drs-orchestration-tag-sync-schedule-test`

**Purpose**: Synchronizes tags from DRS source servers to EC2 recovery instances.

**Schedule**: Every 1 hour

**Lambda Function**: `aws-drs-orchestration-data-management-handler-test`

**Payload**:
```json
{
  "synch_tags": true,
  "synch_instance_type": true
}
```

**What It Does**:
- Reads tag sync configuration from DynamoDB
- For each configured target account:
  - Queries DRS source servers
  - Reads EC2 instance tags
  - Syncs configured tags to DRS
  - Optionally syncs instance type
- Respects tag sync settings (enabled/disabled, tag filters)

**Manual Trigger**:
```bash
# Using orchestration role (recommended)
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"synch_tags":true,"synch_instance_type":true}' \
  --profile {orchestration-role-profile} \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json

# Using admin role
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"synch_tags":true,"synch_instance_type":true}' \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 \
  --cli-binary-format raw-in-base64-out \
  response.json
```

**Handler Function**: `lambda/data-management-handler/index.py::handle_drs_tag_sync()`

**Configuration**:
- Table: `aws-drs-orchestration-tag-sync-config-test`
- Settings: enabled, tag filters, instance type sync

---

## Event-Driven Rules (Non-Scheduled)

### Manual Trigger Rule

**Rule Name**: `aws-drs-orchestration-manual-trigger-test`

**Purpose**: Allows manual triggering of DR operations via EventBridge.

**Event Pattern**:
```json
{
  "detail-type": ["DRS Orchestration Request"],
  "source": ["aws-drs-orchestration.manual"]
}
```

**Usage**: Send custom events to EventBridge for manual orchestration.

### DRS Replication Stalled Rule

**Rule Name**: `aws-drs-orchestration-test--DRSReplicationStalledRule-*`

**Purpose**: Monitors DRS replication health and alerts on stalled replication.

**Event Pattern**:
```json
{
  "detail-type": ["DRS Source Server Data Replication Stalled Change"],
  "source": ["aws.drs"],
  "detail": {
    "state": ["STALLED"]
  }
}
```

**What It Does**: Triggers notifications when DRS replication stalls.

### DRS Recovery Failure Rule

**Rule Name**: `aws-drs-orchestration-test-Not-DRSRecoveryFailureRule-*`

**Purpose**: Monitors DR recovery launches and alerts on failures.

**Event Pattern**:
```json
{
  "detail-type": ["DRS Source Server Launch Result"],
  "source": ["aws.drs"],
  "detail": {
    "state": ["RECOVERY_LAUNCH_FAILED"]
  }
}
```

**What It Does**: Triggers notifications when recovery launches fail.

---

## IAM Roles

### EventBridge Invoke Role

**Role Name**: `aws-drs-orchestration-eventbridge-invoke-test`

**Purpose**: Allows EventBridge to invoke Lambda functions.

**Permissions**:
- `lambda:InvokeFunction` on all orchestration Lambda functions

### Unified Orchestration Role

**Role Name**: `aws-drs-orchestration-orchestration-role-test`

**Purpose**: Unified IAM role used by all Lambda functions for AWS API operations.

**Created By**: `cfn/master-template.yaml` (UnifiedOrchestrationRole resource)

**Key Permissions**:
- DRS: Full access to DRS APIs in all regions
- EC2: Read/write for instances, launch templates, volumes
- DynamoDB: Full access to orchestration tables
- STS: AssumeRole to `DRSOrchestrationRole` in target accounts
- KMS: Encrypt/decrypt for DRS replication
- EventBridge: PutEvents for notifications
- Lambda: InvokeFunction for async operations

**Cross-Account Pattern**:
```
Orchestration Account (438465159935)
  └─ UnifiedOrchestrationRole
       └─ sts:AssumeRole
            └─ Target Account (160885257264)
                 └─ DRSOrchestrationRole
                      └─ DRS/EC2 operations
```

**Get Role ARN**:
```bash
# From CloudFormation stack output
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-test \
  --query 'Stacks[0].Outputs[?OutputKey==`OrchestrationRoleArn`].OutputValue' \
  --output text \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2
```

---

## Manual Trigger Examples

### Using AWS CLI with Orchestration Role

First, configure AWS CLI profile for the orchestration role:

```bash
# Get the orchestration role ARN
ROLE_ARN=$(AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-test \
  --query 'Stacks[0].Outputs[?OutputKey==`OrchestrationRoleArn`].OutputValue' \
  --output text \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2)

echo "Orchestration Role ARN: $ROLE_ARN"

# Assume the role
aws sts assume-role \
  --role-arn "$ROLE_ARN" \
  --role-session-name manual-trigger-session \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2
```

### Trigger All Syncs (Full Refresh)

```bash
#!/bin/bash
# Trigger all background sync operations

ENV="test"
PROFILE="AdministratorAccess-438465159935"
REGION="us-east-1"

echo "Triggering all sync operations for environment: $ENV"

# 1. Inventory Sync (15 min schedule)
echo "1/4 Triggering inventory sync..."
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-$ENV \
  --payload '{"operation":"sync_source_server_inventory"}' \
  --profile $PROFILE \
  --region $REGION \
  --cli-binary-format raw-in-base64-out \
  inventory-sync-response.json
cat inventory-sync-response.json | jq .
echo ""

# 2. Recovery Instance Sync (5 min schedule)
echo "2/4 Triggering recovery instance sync..."
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-$ENV \
  --payload '{"operation":"sync_recovery_instances"}' \
  --profile $PROFILE \
  --region $REGION \
  --cli-binary-format raw-in-base64-out \
  recovery-sync-response.json
cat recovery-sync-response.json | jq .
echo ""

# 3. Staging Account Sync (5 min schedule)
echo "3/4 Triggering staging account sync..."
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-$ENV \
  --payload '{"operation":"sync_staging_accounts"}' \
  --profile $PROFILE \
  --region $REGION \
  --cli-binary-format raw-in-base64-out \
  staging-sync-response.json
cat staging-sync-response.json | jq .
echo ""

# 4. Tag Sync (1 hour schedule)
echo "4/4 Triggering tag sync..."
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-$ENV \
  --payload '{"synch_tags":true,"synch_instance_type":true}' \
  --profile $PROFILE \
  --region $REGION \
  --cli-binary-format raw-in-base64-out \
  tag-sync-response.json
cat tag-sync-response.json | jq .
echo ""

echo "All sync operations triggered successfully"
```

---

## Monitoring and Troubleshooting

### Check Rule Status

```bash
# List all rules
AWS_PAGER="" aws events list-rules \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 | jq '.Rules[] | select(.Name | contains("test"))'

# Check specific rule
AWS_PAGER="" aws events describe-rule \
  --name aws-drs-orchestration-inventory-sync-test \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2
```

### View Lambda Logs

```bash
# Tail logs for inventory sync
AWS_PAGER="" aws logs tail \
  /aws/lambda/aws-drs-orchestration-data-management-handler-test \
  --since 10m \
  --follow \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2
```

### Check Last Sync Time

```bash
# Query inventory table for last sync timestamp
AWS_PAGER="" aws dynamodb scan \
  --table-name aws-drs-orchestration-source-server-inventory-test \
  --limit 1 \
  --projection-expression "lastUpdated" \
  --profile AdministratorAccess-438465159935 \
  --region us-east-2 | jq '.Items[0].lastUpdated.S'
```

---

## Related Documentation

- [Deployment Guide](../docs/guides/DEPLOYMENT_GUIDE.md)
- [Developer Guide](../docs/guides/DEVELOPER_GUIDE.md)
- [Architecture Overview](../docs/ARCHITECTURE.md)
