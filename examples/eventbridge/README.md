# EventBridge Lambda Invocation Examples

## Overview

This directory contains examples for invoking Lambda functions from AWS EventBridge rules using direct invocation mode. These examples demonstrate how to automate disaster recovery operations using EventBridge scheduled rules, rate-based rules, and event-driven patterns with the DR Orchestration Platform's Lambda handlers.

## Table of Contents

1. [EventBridge Rule Definitions](#eventbridge-rule-definitions)
2. [Rule Types](#rule-types)
3. [Lambda Invocation Patterns](#lambda-invocation-patterns)
4. [Cron Expressions](#cron-expressions)
5. [Event Patterns](#event-patterns)
6. [Deployment Instructions](#deployment-instructions)
7. [Testing Procedures](#testing-procedures)
8. [Integration with CDK Stack](#integration-with-cdk-stack)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Patterns](#advanced-patterns)
11. [Best Practices](#best-practices)

## EventBridge Rule Definitions

The `lambda-invocation-example.json` file contains 8 EventBridge rules demonstrating:

- **Scheduled Rules** (cron expressions): Daily, hourly, and weekly operations
- **Rate-Based Rules**: Every 5 minutes, every 1 hour operations
- **Event-Driven Rules** (event patterns): DRS state changes, EC2 state changes, custom events

### Rule Categories

1. **Tag Synchronization Rules**
   - Daily tag sync (cron-based)
   - Hourly tag sync (rate-based)

2. **Execution Monitoring Rules**
   - Hourly execution polling (cron-based)
   - Every 5 minutes execution monitoring (rate-based)

3. **Compliance and Capacity Rules**
   - Weekly compliance check (cron-based)

4. **Event-Driven Rules**
   - DRS source server state changes
   - EC2 instance state changes
   - Custom application events


## Rule Types

### 1. Scheduled Rules (Cron Expressions)

Scheduled rules use cron expressions to trigger Lambda functions at specific times.

**Syntax**: `cron(Minutes Hours Day-of-month Month Day-of-week Year)`

**Examples from lambda-invocation-example.json**:

```json
{
  "Name": "DROrchestration-DailyTagSync",
  "ScheduleExpression": "cron(0 2 * * ? *)",
  "Description": "Daily DRS tag synchronization at 2 AM UTC"
}
```

```json
{
  "Name": "DROrchestration-HourlyExecutionPolling",
  "ScheduleExpression": "cron(0 * * * ? *)",
  "Description": "Hourly execution status polling"
}
```

```json
{
  "Name": "DROrchestration-WeeklyComplianceCheck",
  "ScheduleExpression": "cron(0 3 ? * SUN *)",
  "Description": "Weekly compliance check every Sunday at 3 AM UTC"
}
```

### 2. Rate-Based Rules

Rate-based rules trigger Lambda functions at regular intervals.

**Syntax**: `rate(value unit)` where unit is `minute`, `minutes`, `hour`, `hours`, `day`, or `days`

**Examples from lambda-invocation-example.json**:

```json
{
  "Name": "DROrchestration-Every5MinutesExecutionMonitoring",
  "ScheduleExpression": "rate(5 minutes)",
  "Description": "Monitor execution status every 5 minutes"
}
```

```json
{
  "Name": "DROrchestration-HourlyTagSyncRate",
  "ScheduleExpression": "rate(1 hour)",
  "Description": "Tag synchronization every 1 hour"
}
```

### 3. Event-Driven Rules (Event Patterns)

Event-driven rules trigger Lambda functions when specific AWS events occur.

**Examples from lambda-invocation-example.json**:

```json
{
  "Name": "DROrchestration-DRSSourceServerStateChange",
  "EventPattern": {
    "source": ["aws.drs"],
    "detail-type": ["DRS Source Server State Change"],
    "detail": {
      "state": ["DISCONNECTED", "STOPPED"]
    }
  }
}
```

```json
{
  "Name": "DROrchestration-EC2InstanceStateChange",
  "EventPattern": {
    "source": ["aws.ec2"],
    "detail-type": ["EC2 Instance State-change Notification"],
    "detail": {
      "state": ["running", "stopped", "terminated"]
    }
  }
}
```


## Lambda Invocation Patterns

### Pattern 1: Query Handler Invocation (Read Operations)

The Query Handler performs read-only operations to retrieve data from DynamoDB and AWS DRS.

**EventBridge Target Configuration**:

```json
{
  "Id": "QueryHandler",
  "Arn": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-query-handler-test",
  "Input": "{\"source\":\"aws.events\",\"operation\":\"get_drs_capacity_conflicts\"}"
}
```

**Supported Operations**:
- `list_protection_groups` - List all protection groups
- `get_protection_group` - Get specific protection group details
- `list_recovery_plans` - List all recovery plans
- `get_recovery_plan` - Get specific recovery plan details
- `list_executions` - List all executions with optional filtering
- `get_execution` - Get specific execution details
- `get_drs_source_servers` - Get DRS source servers
- `get_target_accounts` - Get registered target accounts
- `get_drs_capacity_conflicts` - Get detected capacity conflicts

**Example Event Payload**:

```json
{
  "source": "aws.events",
  "operation": "get_drs_capacity_conflicts"
}
```

### Pattern 2: Execution Handler Invocation (Recovery Operations)

The Execution Handler manages recovery execution lifecycle operations.

**EventBridge Target Configuration**:

```json
{
  "Id": "ExecutionHandler",
  "Arn": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-execution-handler-test",
  "Input": "{\"source\":\"aws.events\",\"operation\":\"poll_executions\"}"
}
```

**Supported Operations**:
- `poll_executions` - Poll for execution status updates
- `check_execution_status` - Check status of in-progress executions
- `handle_instance_state_change` - Handle EC2 instance state changes
- `start_execution` - Start a new recovery plan execution (with parameters)

**Example Event Payload**:

```json
{
  "source": "aws.events",
  "operation": "poll_executions"
}
```

### Pattern 3: Data Management Handler Invocation (CRUD Operations)

The Data Management Handler performs create, update, and delete operations.

**EventBridge Target Configuration**:

```json
{
  "Id": "DataManagementHandler",
  "Arn": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-data-management-handler-test",
  "Input": "{\"source\":\"aws.events\",\"operation\":\"sync_tags\"}"
}
```

**Supported Operations**:
- `sync_tags` - Synchronize DRS tags across accounts
- `trigger_tag_sync` - Trigger tag synchronization
- `log_event` - Log EventBridge event for audit trail

**Example Event Payload**:

```json
{
  "source": "aws.events",
  "operation": "sync_tags"
}
```


## Cron Expressions

### Cron Expression Format

EventBridge cron expressions have 6 required fields:

```
cron(Minutes Hours Day-of-month Month Day-of-week Year)
```

**Field Values**:
- **Minutes**: 0-59
- **Hours**: 0-23 (UTC)
- **Day-of-month**: 1-31
- **Month**: 1-12 or JAN-DEC
- **Day-of-week**: 1-7 or SUN-SAT (1 = Sunday)
- **Year**: 1970-2199

**Special Characters**:
- `*` (asterisk): All values
- `?` (question mark): Any value (use in day-of-month or day-of-week)
- `-` (dash): Range (e.g., `1-5` for Monday through Friday)
- `,` (comma): Multiple values (e.g., `MON,WED,FRI`)
- `/` (slash): Increments (e.g., `0/15` for every 15 minutes)

### Common Cron Patterns

**Every day at 2 AM UTC**:
```
cron(0 2 * * ? *)
```

**Every hour**:
```
cron(0 * * * ? *)
```

**Every 15 minutes**:
```
cron(0/15 * * * ? *)
```

**Every weekday at 9 AM UTC**:
```
cron(0 9 ? * MON-FRI *)
```

**First day of every month at midnight UTC**:
```
cron(0 0 1 * ? *)
```

**Every Sunday at 3 AM UTC**:
```
cron(0 3 ? * SUN *)
```

**Last day of every month at 11 PM UTC**:
```
cron(0 23 L * ? *)
```

### Timezone Considerations

- All cron expressions use **UTC timezone**
- Convert local times to UTC for scheduling
- Example: 2 AM EST = 7 AM UTC (during standard time)
- Example: 2 AM EDT = 6 AM UTC (during daylight saving time)


## Event Patterns

### Event Pattern Structure

Event patterns match incoming events and trigger Lambda functions when conditions are met.

**Basic Structure**:

```json
{
  "source": ["aws.service"],
  "detail-type": ["Event Type"],
  "detail": {
    "field": ["value1", "value2"]
  }
}
```

### DRS Source Server State Change Pattern

Triggers when DRS source servers change state (e.g., disconnected, stopped).

```json
{
  "source": ["aws.drs"],
  "detail-type": ["DRS Source Server State Change"],
  "detail": {
    "state": ["DISCONNECTED", "STOPPED"]
  }
}
```

**Example Event**:

```json
{
  "version": "0",
  "id": "12345678-1234-1234-1234-123456789012",
  "detail-type": "DRS Source Server State Change",
  "source": "aws.drs",
  "account": "123456789012",
  "time": "2025-02-01T10:00:00Z",
  "region": "us-east-1",
  "resources": ["arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0"],
  "detail": {
    "sourceServerId": "s-1234567890abcdef0",
    "state": "DISCONNECTED",
    "previousState": "CONNECTED"
  }
}
```

### EC2 Instance State Change Pattern

Triggers when EC2 instances (including recovery instances) change state.

```json
{
  "source": ["aws.ec2"],
  "detail-type": ["EC2 Instance State-change Notification"],
  "detail": {
    "state": ["running", "stopped", "terminated"]
  }
}
```

**Example Event**:

```json
{
  "version": "0",
  "id": "12345678-1234-1234-1234-123456789012",
  "detail-type": "EC2 Instance State-change Notification",
  "source": "aws.ec2",
  "account": "123456789012",
  "time": "2025-02-01T10:00:00Z",
  "region": "us-east-1",
  "resources": ["arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"],
  "detail": {
    "instance-id": "i-1234567890abcdef0",
    "state": "running"
  }
}
```

### Custom Application Event Pattern

Triggers on custom events published to EventBridge.

```json
{
  "source": ["custom.dr-orchestration"],
  "detail-type": ["Recovery Plan Execution Requested"],
  "detail": {
    "executionType": ["DRILL", "RECOVERY"]
  }
}
```

**Example Custom Event**:

```json
{
  "version": "0",
  "id": "12345678-1234-1234-1234-123456789012",
  "detail-type": "Recovery Plan Execution Requested",
  "source": "custom.dr-orchestration",
  "account": "123456789012",
  "time": "2025-02-01T10:00:00Z",
  "region": "us-east-1",
  "detail": {
    "planId": "plan-xyz789",
    "executionType": "DRILL",
    "dryRun": false,
    "requestedBy": "automation-system"
  }
}
```

### Input Transformers

Use InputTransformer to extract fields from events and pass them to Lambda functions.

```json
{
  "InputTransformer": {
    "InputPathsMap": {
      "planId": "$.detail.planId",
      "executionType": "$.detail.executionType",
      "dryRun": "$.detail.dryRun"
    },
    "InputTemplate": "{\"source\":\"aws.events\",\"operation\":\"start_execution\",\"planId\":<planId>,\"executionType\":<executionType>,\"dryRun\":<dryRun>}"
  }
}
```


## Deployment Instructions

### Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **IAM permissions** to create EventBridge rules and Lambda permissions
3. **Lambda functions deployed** (Query, Execution, Data Management handlers)
4. **DynamoDB tables created** (Protection Groups, Recovery Plans, Executions)

### Step 1: Update Function ARNs

Edit `lambda-invocation-example.json` and replace placeholders with your environment:

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

# Get your region
REGION=$(aws configure get region)

# Replace placeholders in the JSON file
sed -i "s/ACCOUNT_ID/$ACCOUNT_ID/g" lambda-invocation-example.json
sed -i "s/us-east-1/$REGION/g" lambda-invocation-example.json

# Replace 'test' with your environment name (dev, staging, prod)
sed -i 's/-test/-dev/g' lambda-invocation-example.json
```

Or manually update each `Arn` field:
- `arn:aws:lambda:REGION:ACCOUNT_ID:function:aws-drs-orchestration-query-handler-{environment}`
- `arn:aws:lambda:REGION:ACCOUNT_ID:function:aws-drs-orchestration-execution-handler-{environment}`
- `arn:aws:lambda:REGION:ACCOUNT_ID:function:aws-drs-orchestration-data-management-handler-{environment}`

### Step 2: Create EventBridge Rules

Create each rule using AWS CLI:

```bash
# Daily Tag Sync Rule
aws events put-rule \
  --name DROrchestration-DailyTagSync \
  --description "Daily DRS tag synchronization at 2 AM UTC" \
  --schedule-expression "cron(0 2 * * ? *)" \
  --state ENABLED

# Add Lambda target
aws events put-targets \
  --rule DROrchestration-DailyTagSync \
  --targets "Id=DataManagementHandler,Arn=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-data-management-handler-test,Input='{\"source\":\"aws.events\",\"operation\":\"sync_tags\"}'"

# Hourly Execution Polling Rule
aws events put-rule \
  --name DROrchestration-HourlyExecutionPolling \
  --description "Hourly execution status polling" \
  --schedule-expression "cron(0 * * * ? *)" \
  --state ENABLED

aws events put-targets \
  --rule DROrchestration-HourlyExecutionPolling \
  --targets "Id=ExecutionHandler,Arn=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-execution-handler-test,Input='{\"source\":\"aws.events\",\"operation\":\"poll_executions\"}'"

# Weekly Compliance Check Rule
aws events put-rule \
  --name DROrchestration-WeeklyComplianceCheck \
  --description "Weekly compliance check every Sunday at 3 AM UTC" \
  --schedule-expression "cron(0 3 ? * SUN *)" \
  --state ENABLED

aws events put-targets \
  --rule DROrchestration-WeeklyComplianceCheck \
  --targets "Id=QueryHandler,Arn=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-query-handler-test,Input='{\"source\":\"aws.events\",\"operation\":\"get_drs_capacity_conflicts\"}'"

# Every 5 Minutes Execution Monitoring Rule
aws events put-rule \
  --name DROrchestration-Every5MinutesExecutionMonitoring \
  --description "Monitor execution status every 5 minutes" \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule DROrchestration-Every5MinutesExecutionMonitoring \
  --targets "Id=ExecutionHandler,Arn=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-execution-handler-test,Input='{\"source\":\"aws.events\",\"operation\":\"check_execution_status\"}'"

# Hourly Tag Sync Rate Rule
aws events put-rule \
  --name DROrchestration-HourlyTagSyncRate \
  --description "Tag synchronization every 1 hour using rate expression" \
  --schedule-expression "rate(1 hour)" \
  --state ENABLED

aws events put-targets \
  --rule DROrchestration-HourlyTagSyncRate \
  --targets "Id=DataManagementHandler,Arn=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-data-management-handler-test,Input='{\"source\":\"aws.events\",\"operation\":\"trigger_tag_sync\"}'"
```

### Step 3: Create Event-Driven Rules

```bash
# DRS Source Server State Change Rule
aws events put-rule \
  --name DROrchestration-DRSSourceServerStateChange \
  --description "Trigger on DRS source server state changes" \
  --event-pattern '{"source":["aws.drs"],"detail-type":["DRS Source Server State Change"],"detail":{"state":["DISCONNECTED","STOPPED"]}}' \
  --state ENABLED

aws events put-targets \
  --rule DROrchestration-DRSSourceServerStateChange \
  --targets "Id=DataManagementHandler,Arn=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-data-management-handler-test,Input='{\"source\":\"aws.events\",\"operation\":\"log_event\",\"eventType\":\"DRS_SERVER_STATE_CHANGE\"}'"

# EC2 Instance State Change Rule
aws events put-rule \
  --name DROrchestration-EC2InstanceStateChange \
  --description "Trigger on EC2 instance state changes for recovery instances" \
  --event-pattern '{"source":["aws.ec2"],"detail-type":["EC2 Instance State-change Notification"],"detail":{"state":["running","stopped","terminated"]}}' \
  --state ENABLED

aws events put-targets \
  --rule DROrchestration-EC2InstanceStateChange \
  --targets "Id=ExecutionHandler,Arn=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-execution-handler-test,Input='{\"source\":\"aws.events\",\"operation\":\"handle_instance_state_change\"}'"

# Custom Application Event Rule
aws events put-rule \
  --name DROrchestration-CustomApplicationEvent \
  --description "Trigger on custom application events" \
  --event-pattern '{"source":["custom.dr-orchestration"],"detail-type":["Recovery Plan Execution Requested"],"detail":{"executionType":["DRILL","RECOVERY"]}}' \
  --state ENABLED

# Custom event with InputTransformer
aws events put-targets \
  --rule DROrchestration-CustomApplicationEvent \
  --targets file://custom-event-target.json
```

Create `custom-event-target.json`:

```json
[
  {
    "Id": "ExecutionHandler",
    "Arn": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-execution-handler-test",
    "InputTransformer": {
      "InputPathsMap": {
        "planId": "$.detail.planId",
        "executionType": "$.detail.executionType",
        "dryRun": "$.detail.dryRun"
      },
      "InputTemplate": "{\"source\":\"aws.events\",\"operation\":\"start_execution\",\"planId\":<planId>,\"executionType\":<executionType>,\"dryRun\":<dryRun>}"
    }
  }
]
```

### Step 4: Grant Lambda Functions Permission

Grant EventBridge permission to invoke Lambda functions:

```bash
# Query Handler
aws lambda add-permission \
  --function-name aws-drs-orchestration-query-handler-test \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:ACCOUNT_ID:rule/DROrchestration-*

# Execution Handler
aws lambda add-permission \
  --function-name aws-drs-orchestration-execution-handler-test \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:ACCOUNT_ID:rule/DROrchestration-*

# Data Management Handler
aws lambda add-permission \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:ACCOUNT_ID:rule/DROrchestration-*
```


## Testing Procedures

### Test 1: Verify Rule Creation

```bash
# List all DR Orchestration rules
AWS_PAGER="" aws events list-rules \
  --name-prefix DROrchestration- \
  --query 'Rules[*].{Name:Name,State:State,Schedule:ScheduleExpression}' \
  --output table

# Get specific rule details
AWS_PAGER="" aws events describe-rule \
  --name DROrchestration-DailyTagSync
```

### Test 2: Verify Rule Targets

```bash
# List targets for a rule
AWS_PAGER="" aws events list-targets-by-rule \
  --rule DROrchestration-DailyTagSync \
  --query 'Targets[*].{Id:Id,Arn:Arn,Input:Input}' \
  --output table
```

### Test 3: Manually Trigger a Scheduled Rule

Test a rule without waiting for the schedule:

```bash
# Create test event
cat > test-event.json << 'EOF'
{
  "source": "aws.events",
  "operation": "sync_tags"
}
EOF

# Invoke Lambda directly with EventBridge format
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload file://test-event.json \
  response.json

# View response
cat response.json | jq .
```

### Test 4: Test Event Pattern Matching

Test if an event matches a rule's event pattern:

```bash
# Create sample DRS event
cat > drs-event.json << 'EOF'
{
  "version": "0",
  "id": "12345678-1234-1234-1234-123456789012",
  "detail-type": "DRS Source Server State Change",
  "source": "aws.drs",
  "account": "123456789012",
  "time": "2025-02-01T10:00:00Z",
  "region": "us-east-1",
  "resources": ["arn:aws:drs:us-east-1:123456789012:source-server/s-1234567890abcdef0"],
  "detail": {
    "sourceServerId": "s-1234567890abcdef0",
    "state": "DISCONNECTED",
    "previousState": "CONNECTED"
  }
}
EOF

# Test event pattern
aws events test-event-pattern \
  --event-pattern '{"source":["aws.drs"],"detail-type":["DRS Source Server State Change"],"detail":{"state":["DISCONNECTED","STOPPED"]}}' \
  --event file://drs-event.json
```

### Test 5: Publish Custom Event

Test custom application events:

```bash
# Publish custom event to EventBridge
aws events put-events \
  --entries '[
    {
      "Source": "custom.dr-orchestration",
      "DetailType": "Recovery Plan Execution Requested",
      "Detail": "{\"planId\":\"plan-test-123\",\"executionType\":\"DRILL\",\"dryRun\":true,\"requestedBy\":\"test-user\"}"
    }
  ]'

# Check if event was delivered
AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-execution-handler-test --since 1m
```

### Test 6: Monitor Rule Invocations

```bash
# Get CloudWatch metrics for rule invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=RuleName,Value=DROrchestration-DailyTagSync \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum

# Get failed invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name FailedInvocations \
  --dimensions Name=RuleName,Value=DROrchestration-DailyTagSync \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum
```

### Test 7: View Lambda Logs

```bash
# Tail Lambda logs to see EventBridge invocations
AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-data-management-handler-test --follow --format short

# Search for specific operation
AWS_PAGER="" aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-data-management-handler-test \
  --filter-pattern "sync_tags" \
  --start-time $(date -u -v-1H +%s)000
```


## Integration with CDK Stack

The CDK stack in `examples/cdk/lib/dr-orchestration-stack.ts` already includes EventBridge rules. You can integrate these examples in several ways:

### Option 1: Use Existing CDK Rules

The CDK stack creates two EventBridge rules by default:

```typescript
// Tag synchronization rule (if enabled)
if (props.enableTagSync) {
  const tagSyncRule = new events.Rule(this, 'TagSyncRule', {
    ruleName: `${props.projectName}-tag-sync-${props.environment}`,
    description: 'Scheduled DRS tag synchronization every 1 hour',
    schedule: events.Schedule.rate(cdk.Duration.hours(1)),
  });
  
  tagSyncRule.addTarget(new targets.LambdaFunction(this.dataManagementHandler, {
    event: events.RuleTargetInput.fromObject({
      source: 'aws.events',
      operation: 'sync_tags',
    }),
  }));
}

// Execution polling rule
const executionPollingRule = new events.Rule(this, 'ExecutionPollingRule', {
  ruleName: `${props.projectName}-execution-polling-${props.environment}`,
  description: 'Polls for execution status updates every 5 minutes',
  schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
});

executionPollingRule.addTarget(new targets.LambdaFunction(this.executionHandler, {
  event: events.RuleTargetInput.fromObject({
    source: 'aws.events',
    operation: 'poll_executions',
  }),
}));
```

### Option 2: Add Additional Rules to CDK Stack

Extend the CDK stack with additional EventBridge rules:

```typescript
// Add to createEventBridgeRules() method in dr-orchestration-stack.ts

// Weekly compliance check
const complianceCheckRule = new events.Rule(this, 'ComplianceCheckRule', {
  ruleName: `${props.projectName}-compliance-check-${props.environment}`,
  description: 'Weekly compliance check every Sunday at 3 AM UTC',
  schedule: events.Schedule.cron({
    minute: '0',
    hour: '3',
    weekDay: 'SUN',
  }),
});

complianceCheckRule.addTarget(new targets.LambdaFunction(this.queryHandler, {
  event: events.RuleTargetInput.fromObject({
    source: 'aws.events',
    operation: 'get_drs_capacity_conflicts',
  }),
}));

// DRS source server state change
const drsStateChangeRule = new events.Rule(this, 'DRSStateChangeRule', {
  ruleName: `${props.projectName}-drs-state-change-${props.environment}`,
  description: 'Trigger on DRS source server state changes',
  eventPattern: {
    source: ['aws.drs'],
    detailType: ['DRS Source Server State Change'],
    detail: {
      state: ['DISCONNECTED', 'STOPPED'],
    },
  },
});

drsStateChangeRule.addTarget(new targets.LambdaFunction(this.dataManagementHandler, {
  event: events.RuleTargetInput.fromObject({
    source: 'aws.events',
    operation: 'log_event',
    eventType: 'DRS_SERVER_STATE_CHANGE',
  }),
}));

// EC2 instance state change
const ec2StateChangeRule = new events.Rule(this, 'EC2StateChangeRule', {
  ruleName: `${props.projectName}-ec2-state-change-${props.environment}`,
  description: 'Trigger on EC2 instance state changes',
  eventPattern: {
    source: ['aws.ec2'],
    detailType: ['EC2 Instance State-change Notification'],
    detail: {
      state: ['running', 'stopped', 'terminated'],
    },
  },
});

ec2StateChangeRule.addTarget(new targets.LambdaFunction(this.executionHandler, {
  event: events.RuleTargetInput.fromObject({
    source: 'aws.events',
    operation: 'handle_instance_state_change',
  }),
}));

// Custom application event
const customEventRule = new events.Rule(this, 'CustomEventRule', {
  ruleName: `${props.projectName}-custom-event-${props.environment}`,
  description: 'Trigger on custom application events',
  eventPattern: {
    source: ['custom.dr-orchestration'],
    detailType: ['Recovery Plan Execution Requested'],
    detail: {
      executionType: ['DRILL', 'RECOVERY'],
    },
  },
});

customEventRule.addTarget(new targets.LambdaFunction(this.executionHandler, {
  event: events.RuleTargetInput.fromEventPath('$.detail'),
}));
```

### Option 3: Import Existing Rules

If you've already deployed rules using AWS CLI, import them into CDK:

```typescript
// Import existing EventBridge rule
const tagSyncRule = events.Rule.fromRuleName(
  this,
  'ImportedTagSyncRule',
  'DROrchestration-DailyTagSync'
);

// Add additional targets if needed
tagSyncRule.addTarget(new targets.LambdaFunction(this.dataManagementHandler));
```

### Option 4: Conditional Rule Creation

Make rules conditional based on stack parameters:

```typescript
// Add to DROrchestrationStackProps interface
export interface DROrchestrationStackProps extends cdk.StackProps {
  // ... existing props ...
  enableComplianceChecks?: boolean;
  enableEventDrivenRules?: boolean;
}

// In createEventBridgeRules() method
if (props.enableComplianceChecks) {
  const complianceCheckRule = new events.Rule(this, 'ComplianceCheckRule', {
    // ... rule configuration ...
  });
}

if (props.enableEventDrivenRules) {
  const drsStateChangeRule = new events.Rule(this, 'DRSStateChangeRule', {
    // ... rule configuration ...
  });
}
```


## Troubleshooting

### Issue 1: Rule Not Triggering

**Symptoms:**
- Rule is enabled but Lambda function is not being invoked
- No CloudWatch metrics for rule invocations

**Solution:**

1. Verify rule is enabled:
   ```bash
   AWS_PAGER="" aws events describe-rule --name DROrchestration-DailyTagSync
   ```

2. Check rule targets:
   ```bash
   AWS_PAGER="" aws events list-targets-by-rule --rule DROrchestration-DailyTagSync
   ```

3. Verify Lambda permission:
   ```bash
   aws lambda get-policy --function-name aws-drs-orchestration-data-management-handler-test
   ```

4. Check CloudWatch Logs for errors:
   ```bash
   AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-data-management-handler-test --since 1h
   ```

### Issue 2: Lambda Permission Denied

**Error:**
```
User: arn:aws:events:us-east-1:123456789012:rule/DROrchestration-DailyTagSync is not authorized to perform: lambda:InvokeFunction
```

**Solution:**

Add Lambda resource-based policy:

```bash
aws lambda add-permission \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-1:ACCOUNT_ID:rule/DROrchestration-*
```

### Issue 3: Invalid Cron Expression

**Error:**
```
Parameter ScheduleExpression is not valid
```

**Solution:**

1. Verify cron expression format (6 fields required):
   ```
   cron(Minutes Hours Day-of-month Month Day-of-week Year)
   ```

2. Use `?` for day-of-month or day-of-week (not both):
   ```bash
   # CORRECT
   cron(0 2 * * ? *)  # Every day at 2 AM
   cron(0 3 ? * SUN *)  # Every Sunday at 3 AM
   
   # INCORRECT
   cron(0 2 * * * *)  # Missing ? for day-of-week
   cron(0 3 1 * SUN *)  # Cannot specify both day-of-month and day-of-week
   ```

3. Test cron expression online: https://crontab.guru/ (convert to EventBridge format)

### Issue 4: Event Pattern Not Matching

**Symptoms:**
- Event-driven rule is not triggering
- Events are being published but Lambda is not invoked

**Solution:**

1. Test event pattern:
   ```bash
   aws events test-event-pattern \
     --event-pattern '{"source":["aws.drs"],"detail-type":["DRS Source Server State Change"]}' \
     --event file://test-event.json
   ```

2. Verify event structure matches pattern:
   - Check `source` field matches exactly
   - Check `detail-type` matches exactly
   - Check `detail` fields match pattern

3. Use CloudWatch Logs Insights to view actual events:
   ```
   fields @timestamp, @message
   | filter @message like /DRS Source Server/
   | sort @timestamp desc
   | limit 20
   ```

### Issue 5: Too Many Invocations

**Symptoms:**
- Lambda function is being invoked too frequently
- High Lambda costs
- Rate limiting errors

**Solution:**

1. Disable rule temporarily:
   ```bash
   aws events disable-rule --name DROrchestration-Every5MinutesExecutionMonitoring
   ```

2. Adjust schedule expression:
   ```bash
   # Change from every 5 minutes to every 15 minutes
   aws events put-rule \
     --name DROrchestration-Every5MinutesExecutionMonitoring \
     --schedule-expression "rate(15 minutes)"
   ```

3. Re-enable rule:
   ```bash
   aws events enable-rule --name DROrchestration-Every5MinutesExecutionMonitoring
   ```

### Issue 6: Lambda Function Timeout

**Error:**
```
Task timed out after 3.00 seconds
```

**Solution:**

1. Increase Lambda timeout:
   ```bash
   aws lambda update-function-configuration \
     --function-name aws-drs-orchestration-data-management-handler-test \
     --timeout 300
   ```

2. Optimize Lambda function code to complete faster

3. Consider using Step Functions for long-running operations

### Issue 7: Missing Environment Variables

**Error:**
```
KeyError: 'EXECUTIONS_TABLE'
```

**Solution:**

1. Verify Lambda environment variables:
   ```bash
   AWS_PAGER="" aws lambda get-function-configuration \
     --function-name aws-drs-orchestration-execution-handler-test \
     --query 'Environment.Variables'
   ```

2. Update environment variables if missing:
   ```bash
   aws lambda update-function-configuration \
     --function-name aws-drs-orchestration-execution-handler-test \
     --environment "Variables={EXECUTIONS_TABLE=aws-drs-orchestration-executions-test,PROJECT_NAME=aws-drs-orchestration,ENVIRONMENT=test}"
   ```

### Issue 8: DynamoDB Table Not Found

**Error:**
```
ResourceNotFoundException: Requested resource not found
```

**Solution:**

1. Verify DynamoDB tables exist:
   ```bash
   AWS_PAGER="" aws dynamodb list-tables --query "TableNames[?contains(@, 'drs-orchestration')]"
   ```

2. Check Lambda execution role has DynamoDB permissions:
   ```bash
   aws iam get-role-policy \
     --role-name aws-drs-orchestration-orchestration-role-test \
     --policy-name DynamoDBPolicy
   ```

3. Ensure table names match environment variables


## Advanced Patterns

### Pattern 1: Dead Letter Queue (DLQ)

Configure DLQ for failed Lambda invocations:

```bash
# Create SQS queue for DLQ
aws sqs create-queue --queue-name dr-orchestration-eventbridge-dlq

# Get queue ARN
DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/dr-orchestration-eventbridge-dlq \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

# Update EventBridge target with DLQ
aws events put-targets \
  --rule DROrchestration-DailyTagSync \
  --targets "Id=DataManagementHandler,Arn=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-data-management-handler-test,Input='{\"source\":\"aws.events\",\"operation\":\"sync_tags\"}',DeadLetterConfig={Arn=$DLQ_ARN}"
```

### Pattern 2: Retry Policy

Configure retry policy for Lambda invocations:

```bash
# Update target with retry policy
aws events put-targets \
  --rule DROrchestration-DailyTagSync \
  --targets "Id=DataManagementHandler,Arn=arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-data-management-handler-test,Input='{\"source\":\"aws.events\",\"operation\":\"sync_tags\"}',RetryPolicy={MaximumRetryAttempts=3,MaximumEventAge=3600}"
```

**Retry Policy Parameters**:
- `MaximumRetryAttempts`: 0-185 (default: 185)
- `MaximumEventAge`: 60-86400 seconds (default: 86400 = 24 hours)

### Pattern 3: Multiple Targets

Invoke multiple Lambda functions from a single rule:

```bash
# Create targets file
cat > multiple-targets.json << 'EOF'
[
  {
    "Id": "DataManagementHandler",
    "Arn": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-data-management-handler-test",
    "Input": "{\"source\":\"aws.events\",\"operation\":\"sync_tags\"}"
  },
  {
    "Id": "QueryHandler",
    "Arn": "arn:aws:lambda:us-east-1:ACCOUNT_ID:function:aws-drs-orchestration-query-handler-test",
    "Input": "{\"source\":\"aws.events\",\"operation\":\"get_drs_capacity_conflicts\"}"
  }
]
EOF

# Add multiple targets
aws events put-targets \
  --rule DROrchestration-DailyTagSync \
  --targets file://multiple-targets.json
```

### Pattern 4: Cross-Account Event Bus

Send events to another AWS account:

```bash
# In source account, create rule to forward events
aws events put-rule \
  --name ForwardDRSEvents \
  --event-pattern '{"source":["aws.drs"]}' \
  --state ENABLED

# Add target to another account's event bus
aws events put-targets \
  --rule ForwardDRSEvents \
  --targets "Id=CrossAccountEventBus,Arn=arn:aws:events:us-east-1:TARGET_ACCOUNT_ID:event-bus/default,RoleArn=arn:aws:iam::SOURCE_ACCOUNT_ID:role/EventBridgeCrossAccountRole"
```

### Pattern 5: Event Filtering with Content-Based Filtering

Filter events based on specific field values:

```json
{
  "source": ["aws.drs"],
  "detail-type": ["DRS Source Server State Change"],
  "detail": {
    "state": ["DISCONNECTED"],
    "sourceServerId": [{"prefix": "s-prod-"}]
  }
}
```

**Supported Filters**:
- `prefix`: String starts with value
- `suffix`: String ends with value
- `anything-but`: Exclude specific values
- `numeric`: Numeric comparisons (>, <, >=, <=, =)
- `exists`: Field exists (true/false)

### Pattern 6: Event Archiving and Replay

Archive events for replay:

```bash
# Create event archive
aws events create-archive \
  --archive-name dr-orchestration-events \
  --event-source-arn arn:aws:events:us-east-1:ACCOUNT_ID:event-bus/default \
  --description "Archive DR orchestration events" \
  --retention-days 30 \
  --event-pattern '{"source":["aws.drs","custom.dr-orchestration"]}'

# Replay archived events
aws events start-replay \
  --replay-name dr-orchestration-replay-$(date +%s) \
  --event-source-arn arn:aws:events:us-east-1:ACCOUNT_ID:event-bus/default \
  --event-start-time $(date -u -v-1d +%Y-%m-%dT%H:%M:%SZ) \
  --event-end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --destination "Arn=arn:aws:events:us-east-1:ACCOUNT_ID:event-bus/default"
```

### Pattern 7: CloudWatch Alarms for Rule Failures

Create alarms for failed invocations:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name dr-orchestration-eventbridge-failures \
  --alarm-description "Alert on EventBridge rule failures" \
  --metric-name FailedInvocations \
  --namespace AWS/Events \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=RuleName,Value=DROrchestration-DailyTagSync \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:dr-orchestration-notifications
```

### Pattern 8: Dynamic Target Configuration

Use InputTransformer to dynamically configure Lambda input:

```json
{
  "InputTransformer": {
    "InputPathsMap": {
      "serverId": "$.detail.sourceServerId",
      "state": "$.detail.state",
      "timestamp": "$.time"
    },
    "InputTemplate": "{\"source\":\"aws.events\",\"operation\":\"log_event\",\"eventType\":\"DRS_SERVER_STATE_CHANGE\",\"serverId\":<serverId>,\"state\":<state>,\"timestamp\":<timestamp>}"
  }
}
```


## Best Practices

### 1. Use Descriptive Rule Names

Use consistent naming convention for easy identification:

```
{ProjectName}-{Operation}-{Environment}
DROrchestration-DailyTagSync-test
DROrchestration-ExecutionPolling-prod
```

### 2. Add Comprehensive Descriptions

Include purpose, schedule, and impact in rule descriptions:

```
"Daily DRS tag synchronization at 2 AM UTC - ensures tags are consistent across all accounts"
```

### 3. Use Rate Expressions for Simple Intervals

Prefer `rate()` over `cron()` for simple intervals:

```bash
# GOOD - Simple and readable
rate(5 minutes)
rate(1 hour)
rate(1 day)

# AVOID - Unnecessarily complex
cron(*/5 * * * ? *)
cron(0 * * * ? *)
cron(0 0 * * ? *)
```

### 4. Use Cron Expressions for Specific Times

Use `cron()` when you need specific times or days:

```bash
# Specific time
cron(0 2 * * ? *)  # 2 AM UTC daily

# Specific day
cron(0 3 ? * SUN *)  # 3 AM UTC every Sunday

# Business hours
cron(0 9-17 ? * MON-FRI *)  # Every hour 9 AM-5 PM UTC weekdays
```

### 5. Monitor Rule Invocations

Set up CloudWatch alarms for:
- Failed invocations
- Throttled invocations
- Invocation count anomalies

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name dr-orchestration-high-failure-rate \
  --metric-name FailedInvocations \
  --namespace AWS/Events \
  --statistic Sum \
  --period 3600 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

### 6. Use Dead Letter Queues

Configure DLQs for critical rules to capture failed events:

```bash
# Always configure DLQ for production rules
aws events put-targets \
  --rule DROrchestration-DailyTagSync \
  --targets "Id=Handler,Arn=...,DeadLetterConfig={Arn=arn:aws:sqs:...}"
```

### 7. Implement Idempotency

Ensure Lambda functions can handle duplicate invocations:

```python
def lambda_handler(event, context):
    # Use idempotency token or check if operation already completed
    operation_id = event.get("operationId")
    if is_operation_completed(operation_id):
        return {"status": "ALREADY_COMPLETED"}
    
    # Perform operation
    result = perform_operation(event)
    
    # Mark operation as completed
    mark_operation_completed(operation_id)
    
    return result
```

### 8. Use Event Filtering

Filter events at the rule level to reduce Lambda invocations:

```json
{
  "source": ["aws.drs"],
  "detail-type": ["DRS Source Server State Change"],
  "detail": {
    "state": ["DISCONNECTED", "STOPPED"],
    "sourceServerId": [{"prefix": "s-prod-"}]
  }
}
```

### 9. Tag EventBridge Rules

Tag rules for cost allocation and organization:

```bash
aws events tag-resource \
  --resource-arn arn:aws:events:us-east-1:ACCOUNT_ID:rule/DROrchestration-DailyTagSync \
  --tags Key=Environment,Value=test Key=Project,Value=DROrchestration Key=CostCenter,Value=Infrastructure
```

### 10. Document Event Schemas

Document expected event schemas for custom events:

```json
{
  "source": "custom.dr-orchestration",
  "detail-type": "Recovery Plan Execution Requested",
  "detail": {
    "planId": "string (required)",
    "executionType": "DRILL | RECOVERY (required)",
    "dryRun": "boolean (optional, default: false)",
    "requestedBy": "string (optional)"
  }
}
```

### 11. Test Rules in Non-Production First

Always test new rules in dev/test environments:

```bash
# Deploy to test first
aws events put-rule --name DROrchestration-NewRule-test ...

# Verify functionality
# Monitor for 24-48 hours

# Then deploy to production
aws events put-rule --name DROrchestration-NewRule-prod ...
```

### 12. Use Appropriate Retry Policies

Configure retry policies based on operation criticality:

```bash
# Critical operations - aggressive retries
RetryPolicy={MaximumRetryAttempts=10,MaximumEventAge=7200}

# Non-critical operations - minimal retries
RetryPolicy={MaximumRetryAttempts=2,MaximumEventAge=900}
```

### 13. Implement Circuit Breaker Pattern

Disable rules automatically if failure rate is too high:

```python
def lambda_handler(event, context):
    failure_rate = get_recent_failure_rate()
    
    if failure_rate > 0.5:  # 50% failure rate
        # Disable EventBridge rule
        events_client.disable_rule(Name='DROrchestration-DailyTagSync')
        
        # Send alert
        sns_client.publish(
            TopicArn='arn:aws:sns:...',
            Subject='EventBridge Rule Disabled',
            Message=f'Rule disabled due to high failure rate: {failure_rate}'
        )
        
        return {"status": "CIRCUIT_BREAKER_TRIGGERED"}
    
    # Normal operation
    return perform_operation(event)
```

### 14. Use CloudWatch Logs Insights

Query Lambda logs for EventBridge invocations:

```
fields @timestamp, @message
| filter @message like /aws.events/
| filter @message like /sync_tags/
| stats count() by bin(5m)
```

### 15. Archive Important Events

Archive events for compliance and replay:

```bash
aws events create-archive \
  --archive-name dr-orchestration-compliance-archive \
  --event-source-arn arn:aws:events:us-east-1:ACCOUNT_ID:event-bus/default \
  --retention-days 365 \
  --event-pattern '{"source":["aws.drs","custom.dr-orchestration"]}'
```

## Related Documentation

- **Design Document**: `.kiro/specs/direct-lambda-invocation-mode/design.md` - Complete event formats and integration patterns
- **API Reference**: `.kiro/specs/direct-lambda-invocation-mode/api-reference.md` - All operations with request/response formats
- **CDK Stack**: `examples/cdk/lib/dr-orchestration-stack.ts` - Infrastructure as code implementation
- **Step Functions Examples**: `examples/stepfunctions/README.md` - Step Functions integration patterns
- **AWS EventBridge Documentation**: https://docs.aws.amazon.com/eventbridge/latest/userguide/what-is-amazon-eventbridge.html
- **EventBridge Cron Expressions**: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html
- **EventBridge Event Patterns**: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html

## Security Considerations

1. **IAM Permissions**: EventBridge rules should follow least privilege principle
2. **Resource-Based Policies**: Lambda functions should only allow invocation from trusted EventBridge rules
3. **Event Validation**: Lambda functions should validate event structure and source
4. **Audit Logging**: Enable CloudWatch Logs for all EventBridge rule invocations
5. **Encryption**: Use encrypted SQS queues for DLQs
6. **Cross-Account Access**: Use IAM roles for cross-account event delivery

## Cost Optimization

- **Event Filtering**: Filter events at the rule level to reduce Lambda invocations
- **Batch Processing**: Combine multiple operations in a single Lambda invocation
- **Appropriate Schedules**: Use longer intervals for non-critical operations
- **DLQ Monitoring**: Monitor DLQ to identify and fix recurring failures
- **Archive Retention**: Set appropriate retention periods for event archives (7-365 days)

## Support

For issues or questions:
1. Check CloudWatch Logs for detailed error messages
2. Review EventBridge metrics in CloudWatch
3. Test event patterns using `aws events test-event-pattern`
4. Consult AWS EventBridge documentation for service-specific issues
5. Review Lambda function logs for invocation errors

