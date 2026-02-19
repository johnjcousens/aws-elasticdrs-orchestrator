# SNS, EventBridge, and Step Functions Integration Architecture

## Overview

Event-driven architecture integrating SNS notifications, EventBridge scheduling, and Step Functions orchestration to provide real-time alerts, automated operations, and human-in-the-loop approval workflows.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EVENT-DRIVEN ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────┐
│   EventBridge    │────────▶│  Step Functions  │────────▶│     SNS      │
│   DRS Events     │         │  State Machine   │         │   Topics     │
│                  │         │                  │         │              │
└──────────────────┘         └──────────────────┘         └──────────────┘
        │                             │                            │
        │                             │                            │
        ▼                             ▼                            ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────┐
│  SNS Topics      │         │  Lambda Handlers │         │   Email      │
│  (DRS Alerts)    │         │  • execution     │         │   SMS        │
│                  │         │  • query         │         │   PagerDuty  │
│                  │         │  • orchestration │         │              │
└──────────────────┘         └──────────────────┘         └──────────────┘
        │                             │
        │                             │
        ▼                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                            DynamoDB Tables                                │
│  • execution-history  • protection-groups  • recovery-plans              │
│  • target-accounts  • drs-region-status  • source-server-inventory       │
│  • recovery-instances                                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. SNS Topics (3 Topics)

**Source Code**: [cfn/notification-stack.yaml](../../cfn/notification-stack.yaml)

#### ExecutionNotificationsTopic
**Purpose**: DR execution lifecycle events (start, complete, fail, pause)  
**Publishers**: Step Functions, Lambda (orchestration, execution-handler)  
**Subscribers**: Email (admin), future: SMS, PagerDuty, Slack  
**Message Format**: Plain text with execution details

```yaml
ExecutionNotificationsTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: '${ProjectName}-execution-notifications-${Environment}'
    DisplayName: 'DRS Orchestration Execution Notifications'
    KmsMasterKeyId: alias/aws/sns

ExecutionNotificationsSubscription:
  Type: AWS::SNS::Subscription
  Properties:
    Protocol: email
    TopicArn: !Ref ExecutionNotificationsTopic
    Endpoint: !Ref AdminEmail
```

#### DRSOperationalAlertsTopic
**Purpose**: Real-time DRS service alerts (replication stalled, launch failures)  
**Publishers**: EventBridge (DRS native events)  
**Subscribers**: Email (admin), future: PagerDuty for critical alerts  
**Message Format**: JSON transformed by EventBridge InputTransformer

```yaml
DRSOperationalAlertsTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: '${ProjectName}-drs-alerts-${Environment}'
    DisplayName: 'DRS Operational Alerts'
    KmsMasterKeyId: alias/aws/sns

DRSOperationalAlertsSubscription:
  Type: AWS::SNS::Subscription
  Properties:
    Protocol: email
    TopicArn: !Ref DRSOperationalAlertsTopic
    Endpoint: !Ref AdminEmail
```

#### ExecutionPauseTopic
**Purpose**: Human approval gates for wave transitions  
**Publishers**: Step Functions (pause state with waitForTaskToken)  
**Subscribers**: Email (admin) with CloudShell CLI commands  
**Message Format**: Plain text with resume/cancel AWS CLI commands

```yaml
ExecutionPauseTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: '${ProjectName}-execution-pause-${Environment}'
    DisplayName: 'DRS Orchestration Execution Pause'
    KmsMasterKeyId: alias/aws/sns

ExecutionPauseSubscription:
  Type: AWS::SNS::Subscription
  Properties:
    Protocol: email
    TopicArn: !Ref ExecutionPauseTopic
    Endpoint: !Ref AdminEmail
```

### 2. EventBridge Rules (2 Rules for SNS Integration)

**Source Code**: [cfn/notification-stack.yaml](../../cfn/notification-stack.yaml#L110-L180)

#### DRS Recovery Failure Rule
**Purpose**: Capture DRS recovery launch failures  
**Event Pattern**: `aws.drs` source, `DRS Source Server Launch Result` detail-type, `RECOVERY_LAUNCH_FAILED` state  
**Target**: DRSOperationalAlertsTopic  
**Transformation**: InputTransformer converts event to alert message

```yaml
DRSRecoveryFailureRule:
  Type: AWS::Events::Rule
  Properties:
    EventPattern:
      source: ["aws.drs"]
      detail-type: ["DRS Source Server Launch Result"]
      detail:
        state: ["RECOVERY_LAUNCH_FAILED"]
    Targets:
      - Arn: !Ref DRSOperationalAlertsTopic
        InputTransformer:
          InputPathsMap:
            sourceServerId: "$.detail.sourceServerId"
            state: "$.detail.state"
            region: "$.region"
          InputTemplate: |
            {
              "alertType": "DRS Recovery Failure",
              "sourceServerId": "<sourceServerId>",
              "state": "<state>",
              "region": "<region>",
              "message": "DRS recovery launch failed for <sourceServerId>"
            }
```

#### DRS Replication Stalled Rule
**Purpose**: Capture DRS replication stalled events  
**Event Pattern**: `aws.drs` source, `DRS Source Server Data Replication Stalled Change` detail-type, `STALLED` state  
**Target**: DRSOperationalAlertsTopic

### 3. Step Functions State Machine

**Source Code**: [cfn/step-functions-stack.yaml](../../cfn/step-functions-stack.yaml)

#### State Machine Overview
**Name**: `${ProjectName}-orchestration-${Environment}`  
**Role**: UnifiedOrchestrationRole (shared with Lambda functions)  
**Pattern**: Sequential wave-based orchestration with pause/resume capability

#### Key States

**InitiateWavePlan** - Start execution
```yaml
InitiateWavePlan:
  Type: Task
  Resource: 'arn:aws:states:::lambda:invoke'
  Parameters:
    FunctionName: !Ref OrchestrationLambdaArn
    Payload:
      action: 'begin'
      execution.$: '$.Execution.Id'
      plan.$: '$.Plan'
  OutputPath: '$.Payload'
  Next: 'CheckPauseRequired'
```

**PauseForApproval** - Wait for human approval (waitForTaskToken pattern)
```yaml
PauseForApproval:
  Type: Task
  Resource: 'arn:aws:states:::lambda:invoke.waitForTaskToken'
  Parameters:
    FunctionName: !Ref OrchestrationLambdaArn
    Payload:
      action: 'pause'
      application.$: '$'
      taskToken.$: '$$.Task.Token'
  TimeoutSeconds: 86400  # 24 hours
  Next: 'DetermineWavePlanState'
```

**WaitForResume** - Long-term pause (1 year timeout)
```yaml
WaitForResume:
  Type: Task
  Resource: 'arn:aws:states:::lambda:invoke.waitForTaskToken'
  Parameters:
    FunctionName: !Ref OrchestrationLambdaArn
    Payload:
      action: 'store_task_token'
      application.$: '$'
      taskToken.$: '$$.Task.Token'
  TimeoutSeconds: 31536000  # 365 days
  Next: 'ResumeWavePlan'
```

## Integration Flows

### Flow 0: Step Functions Pause/Resume State Management

**How Step Functions Knows When to Pause and Resume**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP FUNCTIONS STATE MACHINE - PAUSE/RESUME MECHANISM                   │
└─────────────────────────────────────────────────────────────────────────┘

1. EXECUTION START
   ↓
   AWS CLI → Direct Lambda Invocation
   ↓
   aws lambda invoke \
     --function-name execution-handler \
     --payload '{"operation": "start_execution", "planId": "rp-prod"}'
   ↓
   execution-handler queries DynamoDB for Recovery Plan
   ↓
   execution-handler invokes Step Functions StartExecution
   ↓
   Step Functions receives Recovery Plan JSON:
   {
     "planId": "rp-prod",
     "waves": [
       {"waveNumber": 0, "pauseBeforeWave": false, ...},
       {"waveNumber": 1, "pauseBeforeWave": true, ...},   ← PAUSE FLAG
       {"waveNumber": 2, "pauseBeforeWave": true, ...}
     ]
   }

2. WAVE EXECUTION LOOP
   ↓
   For each wave:
   ↓
   CheckPauseRequired → IF pauseBeforeWave == true:
   ↓
   PauseForApproval (waitForTaskToken)
   ↓
   Lambda receives: {action: "pause", taskToken, executionId, waveNumber}
   ↓
   Lambda stores in DynamoDB:
   {
     executionId: "exec-abc123",
     status: "PAUSED",
     taskToken: "AQCEAAAAKgAAAA...",
     currentWave: 1
   }
   ↓
   Lambda sends SNS notification with CLI commands
   ↓
   Step Functions WAITS (up to 24 hours)
   ↓
   [EXECUTION PAUSED - NO AWS CHARGES]

3. RESUME FROM EMAIL
   ↓
   Admin receives email with resume/cancel commands
   ↓
   Admin runs: aws stepfunctions send-task-success --task-token 'xxx'
   ↓
   Step Functions receives task-success signal
   ↓
   Step Functions resumes at next state
   ↓
   Lambda updates DynamoDB: {status: "IN_PROGRESS", currentWave: 1}
   ↓
   Wave 1 executes → Loop continues to Wave 2

4. STATE RECONSTRUCTION
   ↓
   Lambda receives: {action: "execute_wave", executionId, waveNumber, planId}
   ↓
   Lambda queries DynamoDB execution-history table
   ↓
   Retrieves: wave config, protection groups, servers, launch configs
   ↓
   Lambda has complete execution context
   ↓
   Executes wave with DRS API calls

5. KEY INSIGHTS
   • Step Functions does NOT query DynamoDB
   • Step Functions only knows: taskToken, current state
   • Lambda queries DynamoDB for full execution context
   • pauseBeforeWave flag in Recovery Plan controls pauses
   • taskToken stored in DynamoDB enables resume from CLI
   • Step Functions waits indefinitely until task-success
```

**Source Code**:
- State Machine: [cfn/step-functions-stack.yaml](../../cfn/step-functions-stack.yaml#L50-L150)
- Lambda Pause Handler: [lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py](../../lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py#L200-L250)
- DynamoDB Schema: [cfn/database-stack.yaml](../../cfn/database-stack.yaml#L180-L250)

### Flow 1: Execution Start Notification

**Lambda Handlers Involved**:
- **execution-handler** ([lambda/execution-handler/index.py](../../lambda/execution-handler/index.py)) - Starts DR execution
- **dr-orchestration-stepfunction** ([lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py](../../lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py)) - Orchestrates waves

```
AWS CLI/SDK
    │
    ├─► aws lambda invoke --function-name execution-handler
    │
    ▼
execution-handler
    │
    ├─► DynamoDB: Query recovery-plans table
    ├─► Step Functions: StartExecution
    └─► Return: {executionId, executionArn}
    │
    ▼
Step Functions: InitiateWavePlan
    │
    ▼
dr-orchestration-stepfunction (action: 'begin')
    │
    ├─► DynamoDB: Create execution record
    └─► notifications.send_execution_started()
        │
        └─► SNS: ExecutionNotificationsTopic
            │
            └─► Email: admin@example.com
```

**CLI Example**:
```bash
# Start execution via direct Lambda invocation
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-execution-handler-dev \
  --payload '{"operation": "start_execution", "planId": "rp-prod-failover"}' \
  --region us-east-1 \
  response.json

# Response:
{
  "executionId": "exec-abc123",
  "executionArn": "arn:aws:states:us-east-1:123456789012:execution:orchestration-dev:exec-abc123",
  "startTime": "2026-01-29T10:00:00Z"
}

# Email notification sent automatically via SNS
```

**Source Code**:
- execution-handler: [lambda/execution-handler/index.py](../../lambda/execution-handler/index.py#L200-L250)
- dr-orchestration-stepfunction: [lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py](../../lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py#L100-L150)
- Notifications module: [lambda/shared/notifications.py](../../lambda/shared/notifications.py#L50-L75)

**Code Example** (lambda/shared/notifications.py):
```python
def send_execution_started(
    execution_id: str,
    plan_name: str,
    wave_count: int,
    execution_type: str = "RECOVERY",
    plan_id: Optional[str] = None,
) -> None:
    subject = f"🚀 DRS Execution Started - {plan_name}"
    message = f"""
🚀 AWS DRS Orchestration Execution Started

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Type: {execution_type}
• Total Waves: {wave_count}
• Started At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
    
    sns.publish(
        TopicArn=EXECUTION_TOPIC_ARN,
        Subject=subject,
        Message=message,
        MessageAttributes={
            "recoveryPlanId": {"DataType": "String", "StringValue": plan_id},
            "eventType": {"DataType": "String", "StringValue": "start"}
        }
    )
```

### Flow 2: Wave Pause with Email Callback

**Lambda Handlers Involved**:
- **dr-orchestration-stepfunction** ([lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py](../../lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py#L200-L250)) - Handles pause state

**Source Code**:
- Pause handler: [lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py](../../lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py#L200-L250)
- Notifications module: [lambda/shared/notifications.py](../../lambda/shared/notifications.py#L100-L150)

```
Step Functions: PauseForApproval
    │
    ├─► Generate taskToken
    │
    ▼
dr-orchestration-stepfunction (action: 'pause')
    │
    ├─► DynamoDB: Store taskToken
    └─► notifications.send_execution_paused()
        │
        └─► SNS: ExecutionPauseTopic
            │
            └─► Email: CloudShell link + CLI commands
                │
                ▼
Admin opens CloudShell
    │
    ├─► RESUME: aws stepfunctions send-task-success
    │   └─► Step Functions resumes
    │
    └─► CANCEL: aws stepfunctions send-task-failure
        └─► Step Functions fails
```



**Email Format** (plain text with CLI commands):
```
========================================================
  AWS DRS ORCHESTRATION - EXECUTION PAUSED
  ACTION REQUIRED
========================================================

  Recovery Plan:    Production DR Plan
  Execution ID:     exec-abc123
  Paused At:        2026-01-25 12:00:00 UTC
  Waiting to start: Wave 3

--------------------------------------------------------
  HOW TO RESUME OR CANCEL
--------------------------------------------------------

  1. Open AWS CloudShell:
     https://us-east-1.console.aws.amazon.com/cloudshell/home

  2. Copy ONE command below and paste into CloudShell:

========================================================
  >>> RESUME EXECUTION (Wave 3) <<<
========================================================

aws stepfunctions send-task-success \
  --task-token 'AQCEAAAAKgAAAA...' \
  --task-output '{}' \
  --region us-east-1 \
  && sleep 3 \
  && aws dynamodb query \
    --table-name execution-history-dev \
    --key-condition-expression 'executionId = :eid' \
    --expression-attribute-values '{":eid":{"S":"exec-abc123"}}' \
    --projection-expression '#s,waves' \
    --expression-attribute-names '{"#s":"status"}' \
    --region us-east-1 \
    --output table

========================================================
  >>> CANCEL EXECUTION <<<
========================================================

aws stepfunctions send-task-failure \
  --task-token 'AQCEAAAAKgAAAA...' \
  --error "UserCancelled" \
  --cause "Cancelled via email" \
  --region us-east-1 \
  && sleep 3 \
  && aws dynamodb query ...
```

**Code Example** (lambda/shared/notifications.py):
```python
def format_pause_notification(details: Dict[str, Any]) -> str:
    task_token = details.get("taskToken", "")
    region = details.get("region", "us-east-1")
    execution_id = details.get("executionId", "")
    table_name = details.get("executionHistoryTable", "")
    
    cloudshell_url = f"https://{region}.console.aws.amazon.com/cloudshell/home?region={region}"
    
    # Build status query that runs after resume/cancel
    status_query = (
        f" && sleep 3"
        f" && aws dynamodb query"
        f" --table-name {table_name}"
        f" --key-condition-expression 'executionId = :eid'"
        f" --expression-attribute-values '{{\":eid\":{{\"S\":\"{execution_id}\"}}}}}'"
        f" --projection-expression '#s,waves'"
        f" --expression-attribute-names '{{\"#s\":\"status\"}}'"
        f" --region {region}"
        f" --output table"
    )
    
    resume_cmd = (
        f"aws stepfunctions send-task-success"
        f" --task-token '{task_token}'"
        f" --task-output '{{}}'"
        f" --region {region}"
        f"{status_query}"
    )
    
    cancel_cmd = (
        f"aws stepfunctions send-task-failure"
        f" --task-token '{task_token}'"
        f" --error \"UserCancelled\""
        f" --cause \"Cancelled via email\""
        f" --region {region}"
        f"{status_query}"
    )
    
    return f"""
  1. Open AWS CloudShell: {cloudshell_url}
  2. Copy ONE command:
  
  RESUME: {resume_cmd}
  CANCEL: {cancel_cmd}
"""
```

### Flow 3: Execution Completion Notification

**Lambda Handlers Involved**:
- **dr-orchestration-stepfunction** ([lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py](../../lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py#L300-L350)) - Finalizes execution
- **query-handler** ([lambda/query-handler/index.py](../../lambda/query-handler/index.py#L150-L200)) - Queries execution status

```
Step Functions: PlanCompleted
    │
    ▼
dr-orchestration-stepfunction (action: 'finalize')
    │
    ├─► DynamoDB: Update status to COMPLETED
    └─► notifications.send_execution_completed()
        │
        └─► SNS: ExecutionNotificationsTopic
            │
            └─► Email: Completion notification

─────────────────────────────────────────────

AWS CLI/SDK (check status)
    │
    ├─► aws lambda invoke --function-name query-handler
    │
    ▼
query-handler
    │
    └─► DynamoDB: Query execution-history
        │
        └─► Return: {status, waves, results}
```

**Source Code**:
- Finalize handler: [lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py](../../lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py#L300-L350)
- Query handler: [lambda/query-handler/index.py](../../lambda/query-handler/index.py#L150-L200)
- Notifications module: [lambda/shared/notifications.py](../../lambda/shared/notifications.py#L150-L175)

### Flow 4: DRS Service Event Alert

**Lambda Handlers Involved**: None (EventBridge → SNS direct)

```
AWS DRS Service
    │
    ▼
EventBridge: DRS native event
    │
    ├─► DRSRecoveryFailureRule
    │   └─► InputTransformer: Format alert
    │       └─► SNS: DRSOperationalAlertsTopic
    │           └─► Email: Recovery failure alert
    │
    └─► DRSReplicationStalledRule
        └─► InputTransformer: Format alert
            └─► SNS: DRSOperationalAlertsTopic
                └─► Email: Replication stalled alert
```

**Source Code**:
- EventBridge rules: [cfn/notification-stack.yaml](../../cfn/notification-stack.yaml#L110-L180)

## DynamoDB Table Schemas

### 1. recovery-plans Table

**Primary Key**: `planId` (String)

**Sample Item**:
```json
{
  "planId": "rp-prod-failover",
  "planName": "Production Failover Plan",
  "description": "3-tier application recovery",
  "notificationEmail": "ops-team@example.com",
  "waves": [
    {
      "waveName": "Wave 1 - Database",
      "waveNumber": 0,
      "protectionGroupIds": ["pg-db-servers"],
      "pauseBeforeWave": false
    },
    {
      "waveName": "Wave 2 - Application",
      "waveNumber": 1,
      "protectionGroupIds": ["pg-app-servers"],
      "pauseBeforeWave": true
    }
  ],
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2025-01-20T14:45:00Z"
}
```

**notificationEmail Usage**:
- SNS notifications sent to this email when execution starts, pauses, completes, or fails
- Overrides default admin email from CloudFormation parameter
- Used in `send_execution_started()`, `send_execution_paused()`, `send_execution_completed()`, `send_execution_failed()`

### 2. execution-history Table

**Primary Key**: `executionId` (HASH) + `planId` (RANGE)

**Sample Item**:
```json
{
  "executionId": "exec-20250129-abc123",
  "planId": "rp-prod-failover",
  "status": "PAUSED",
  "taskToken": "AQCEAAAAKgAAAA...",
  "currentWave": 1,
  "notificationEmail": "ops-team@example.com",
  "waves": [
    {"waveNumber": 0, "status": "COMPLETED", "startTime": "2025-01-29T10:00:00Z"},
    {"waveNumber": 1, "status": "PENDING"}
  ],
  "startTime": "2025-01-29T10:00:00Z",
  "pausedAt": "2025-01-29T10:15:00Z",
  "initiatedBy": "admin@example.com"
}
```

### 3. protection-groups Table

**Primary Key**: `groupId` (String)

**Sample Item**:
```json
{
  "groupId": "pg-db-servers",
  "groupName": "Database Servers",
  "description": "Production database tier",
  "region": "us-west-2",
  "sourceServerIds": ["s-db001", "s-db002"],
  "launchConfig": {
    "subnetId": "subnet-db123456",
    "securityGroupIds": ["sg-db123456"],
    "instanceType": "r7a.large"
  },
  "createdAt": "2025-01-15T10:30:00Z"
}
```

### 4. target-accounts Table

**Primary Key**: `accountId` (String)

**Sample Item**:
```json
{
  "accountId": "111122223333",
  "accountName": "Production Account",
  "roleArn": "arn:aws:iam::111122223333:role/DRSOrchestrationRole",
  "externalId": "unique-external-id-123",
  "regions": ["us-east-1", "us-west-2"],
  "status": "ACTIVE"
}
```

## Notification Email Flow

### Recovery Plan Creation
```python
# User creates recovery plan with notificationEmail
recovery_plan = {
    "planId": "rp-prod",
    "planName": "Production DR",
    "notificationEmail": "ops-team@example.com",  # Custom email
    "waves": [...]
}

# Stored in recovery-plans table
dynamodb.put_item(TableName="recovery-plans", Item=recovery_plan)
```

### Execution Start
```python
# execution-handler retrieves plan from DynamoDB
plan = dynamodb.get_item(
    TableName="recovery-plans",
    Key={"planId": "rp-prod"}
)

# Copies notificationEmail to execution record
execution = {
    "executionId": "exec-abc123",
    "planId": "rp-prod",
    "notificationEmail": plan["notificationEmail"],  # Copied here
    "status": "IN_PROGRESS"
}

dynamodb.put_item(TableName="execution-history", Item=execution)

# Send notification to custom email
send_execution_started(
    execution_id="exec-abc123",
    plan_name="Production DR",
    notification_email=plan["notificationEmail"]  # ops-team@example.com
)
```

### Pause Notification
```python
# Lambda retrieves execution from DynamoDB
execution = dynamodb.get_item(
    TableName="execution-history",
    Key={"executionId": "exec-abc123", "planId": "rp-prod"}
)

# Send pause notification to custom email
send_execution_paused(
    execution_id="exec-abc123",
    plan_name="Production DR",
    wave_number=1,
    task_token="AQCEAAAAKgAAAA...",
    notification_email=execution["notificationEmail"]  # ops-team@example.com
)
```

**Email Recipient Priority**:
1. `notificationEmail` from recovery plan (if set)
2. Default admin email from CloudFormation `AdminEmail` parameter
3. SNS topic subscription email

## Environment Variables (Lambda Functions)
```bash
# SNS Topic ARNs
EXECUTION_NOTIFICATIONS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:execution-notifications-dev
DRS_ALERTS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:drs-alerts-dev

# DynamoDB Tables
EXECUTION_HISTORY_TABLE=execution-history-dev
RECOVERY_PLANS_TABLE=recovery-plans-dev
PROTECTION_GROUPS_TABLE=protection-groups-dev

# Project Configuration
PROJECT_NAME=aws-elasticdrs-orchestrator
ENVIRONMENT=dev
AWS_REGION=us-east-1
```

## Lambda Handler Integration

### Handler Overview

The architecture uses **3 Lambda handlers** for SNS/EventBridge/Step Functions integration:

| Handler | Purpose | SNS Integration | Source Code |
|---------|---------|-----------------|-------------|
| **execution-handler** | Start/control DR executions | Sends start notifications | [lambda/execution-handler/index.py](../../lambda/execution-handler/index.py) |
| **query-handler** | Read-only queries | No direct SNS (queries execution status) | [lambda/query-handler/index.py](../../lambda/query-handler/index.py) |
| **dr-orchestration-stepfunction** | Wave orchestration | Sends pause/complete/fail notifications | [lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py](../../lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py) |

### Handler Code Examples

#### execution-handler: Start Execution

**File**: [lambda/execution-handler/index.py](../../lambda/execution-handler/index.py#L200-L250)

```python
def start_execution(event: Dict[str, Any]) -> Dict[str, Any]:
    """Start DR execution via Step Functions."""
    plan_id = event.get('planId')
    
    # Query DynamoDB for recovery plan
    plan = dynamodb.get_item(
        TableName=RECOVERY_PLANS_TABLE,
        Key={'planId': {'S': plan_id}}
    )
    
    # Start Step Functions execution
    response = stepfunctions.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        input=json.dumps({
            'Plan': plan,
            'executionId': execution_id
        })
    )
    
    return {
        'executionId': execution_id,
        'executionArn': response['executionArn']
    }
```

#### query-handler: Get Execution Status

**File**: [lambda/query-handler/index.py](../../lambda/query-handler/index.py#L150-L200)

```python
def get_execution(event: Dict[str, Any]) -> Dict[str, Any]:
    """Query execution status from DynamoDB."""
    execution_id = event.get('executionId')
    
    # Query DynamoDB
    response = dynamodb.query(
        TableName=EXECUTION_HISTORY_TABLE,
        KeyConditionExpression='executionId = :eid',
        ExpressionAttributeValues={
            ':eid': {'S': execution_id}
        }
    )
    
    return {
        'executionId': execution_id,
        'status': response['Items'][0]['status']['S'],
        'waves': json.loads(response['Items'][0]['waves']['S'])
    }
```

#### dr-orchestration-stepfunction: Pause Handler

**File**: [lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py](../../lambda/dr-orchestration-stepfunction/orchestration_stepfunctions.py#L200-L250)

```python
def handle_pause(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle execution pause with SNS notification."""
    task_token = event.get('taskToken')
    execution_id = event.get('executionId')
    wave_number = event.get('waveNumber')
    
    # Store task token in DynamoDB
    dynamodb.update_item(
        TableName=EXECUTION_HISTORY_TABLE,
        Key={'executionId': {'S': execution_id}},
        UpdateExpression='SET #status = :paused, taskToken = :token',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':paused': {'S': 'PAUSED'},
            ':token': {'S': task_token}
        }
    )
    
    # Send SNS notification with resume/cancel commands
    from shared.notifications import send_execution_paused
    send_execution_paused(
        execution_id=execution_id,
        plan_name=event.get('planName'),
        wave_number=wave_number,
        task_token=task_token
    )
    
    # Step Functions waits here until send-task-success/failure
    return {'status': 'PAUSED'}
```

### IAM Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": [
        "arn:aws:lambda:*:*:function:*-query-handler-*",
        "arn:aws:lambda:*:*:function:*-execution-handler-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:SendTaskSuccess",
        "states:SendTaskFailure"
      ],
      "Resource": "arn:aws:states:*:*:stateMachine:*-orchestration-*"
    }
  ]
}
```

**CLI Examples**:
```bash
# Start execution
aws lambda invoke \
  --function-name execution-handler \
  --payload '{"operation": "start_execution", "planId": "rp-prod"}' \
  response.json

# Get execution status
aws lambda invoke \
  --function-name query-handler \
  --payload '{"operation": "get_execution", "executionId": "exec-abc123"}' \
  response.json
```

### IAM Permissions

**Lambda Functions (UnifiedOrchestrationRole)**:
```yaml
- Effect: Allow
  Action:
    - sns:Publish
  Resource:
    - !Ref ExecutionNotificationsTopic
    - !Ref DRSOperationalAlertsTopic
    - !Ref ExecutionPauseTopic

- Effect: Allow
  Action:
    - states:SendTaskSuccess
    - states:SendTaskFailure
    - states:SendTaskHeartbeat
  Resource: !Ref DRSOrchestrationStateMachine
```

**Step Functions (UnifiedOrchestrationRole)**:
```yaml
- Effect: Allow
  Action:
    - sns:Publish
  Resource:
    - !Ref ExecutionNotificationsTopic
    - !Ref ExecutionPauseTopic

- Effect: Allow
  Action:
    - lambda:InvokeFunction
  Resource: !Ref OrchestrationLambdaArn
```

**EventBridge (EventBridgeInvokeRole)**:
```yaml
- Effect: Allow
  Action:
    - states:StartExecution
  Resource: !Ref ModularOrchestratorArn

- Effect: Allow
  Action:
    - lambda:InvokeFunction
  Resource:
    - !Ref ApiHandlerFunctionArn
    - !Ref QueryHandlerFunctionArn
```

## Error Handling

### SNS Publish Failures

All notification functions are **non-blocking**:
```python
try:
    sns.publish(TopicArn=EXECUTION_TOPIC_ARN, Subject=subject, Message=message)
    print(f"✅ Sent notification for {execution_id}")
except Exception as e:
    print(f"Warning: Failed to send notification: {e}")
    # Execution continues - notifications don't block DR operations
```

### Step Functions Task Token Timeout

**PauseForApproval** (24-hour timeout):
```yaml
PauseForApproval:
  TimeoutSeconds: 86400  # 24 hours
  Catch:
    - ErrorEquals: ['States.Timeout']
      Next: 'HandleTimeout'
```

**WaitForResume** (1-year timeout):
```yaml
WaitForResume:
  TimeoutSeconds: 31536000  # 365 days
  Catch:
    - ErrorEquals: ['States.Timeout']
      Next: 'PlanTimeout'
```

### EventBridge Lambda Invocation Failures

EventBridge automatically retries Lambda invocations:
- **Retry Count**: 2 retries
- **Retry Interval**: Exponential backoff
- **Dead Letter Queue**: Not configured (failures logged to CloudWatch)

## Testing Considerations

### 1. Test SNS Notifications Locally

```python
import os
os.environ["EXECUTION_NOTIFICATIONS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123456789012:test-topic"

from shared.notifications import send_execution_started

send_execution_started(
    execution_id="test-exec-123",
    plan_name="Test Plan",
    wave_count=3,
    execution_type="DRILL"
)
```

### 2. Mock SNS Client

```python
from unittest.mock import patch

with patch('shared.notifications.sns.publish') as mock_publish:
    send_execution_started("test-exec", "Test Plan", 3)
    
    assert mock_publish.called
    assert mock_publish.call_args[1]['Subject'] == "🚀 DRS Execution Started - Test Plan"
```

### 3. Test EventBridge Rules

```bash
# Manually trigger tag sync
aws events put-events --entries '[{
  "Source": "manual.test",
  "DetailType": "Test Tag Sync",
  "Detail": "{\"test\": true}"
}]'

# Check Lambda invocation
aws logs tail /aws/lambda/query-handler --since 1m
```

### 4. Test Step Functions Pause/Resume

```bash
# Start execution
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:orchestration-dev \
  --input '{"Plan": {...}, "isDrill": true}'

# Get task token from DynamoDB
aws dynamodb get-item \
  --table-name execution-history-dev \
  --key '{"executionId": {"S": "exec-123"}}'

# Resume execution
aws stepfunctions send-task-success \
  --task-token 'AQCEAAAAKgAAAA...' \
  --task-output '{}'

# Cancel execution
aws stepfunctions send-task-failure \
  --task-token 'AQCEAAAAKgAAAA...' \
  --error "UserCancelled" \
  --cause "Test cancellation"
```

## Monitoring and Observability

### CloudWatch Metrics

**SNS Metrics**:
- `NumberOfMessagesPublished` - Messages sent to topics
- `NumberOfNotificationsFailed` - Failed email deliveries
- `NumberOfNotificationsDelivered` - Successful deliveries

**Step Functions Metrics**:
- `ExecutionsStarted` - Total executions started
- `ExecutionsSucceeded` - Successful completions
- `ExecutionsFailed` - Failed executions
- `ExecutionTime` - Execution duration

**EventBridge Metrics**:
- `Invocations` - Rule invocations
- `FailedInvocations` - Failed Lambda invocations
- `TriggeredRules` - Rules that matched events

### CloudWatch Logs

**Lambda Logs**:
```bash
# Orchestration Lambda
/aws/lambda/dr-orchestration-stepfunction

# Query Handler (tag sync)
/aws/lambda/query-handler

# Execution Handler
/aws/lambda/execution-handler
```

**Step Functions Logs**:
```bash
# State machine execution history
aws stepfunctions get-execution-history \
  --execution-arn arn:aws:states:us-east-1:123456789012:execution:orchestration-dev:exec-123
```

## Best Practices

### 1. SNS Topic Organization
- **Separate topics by purpose**: Execution events, operational alerts, pause notifications
- **Use message attributes**: Enable SNS filter policies for targeted subscriptions
- **Encrypt at rest**: Use KMS encryption (alias/aws/sns)

### 2. EventBridge Rule Design
- **Specific event patterns**: Avoid overly broad patterns that match unintended events
- **InputTransformer**: Format events before sending to SNS for cleaner notifications
- **Conditional deployment**: Use CloudFormation conditions to enable/disable rules

### 3. Step Functions Integration
- **waitForTaskToken pattern**: Enables pause/resume with external callbacks
- **Long timeouts**: Support multi-day approval workflows (1-year max)
- **State reconstruction**: Store full state in DynamoDB for resume operations

### 4. Error Handling
- **Non-blocking notifications**: Never fail DR operations due to notification errors
- **Retry logic**: Use exponential backoff for transient failures
- **Dead letter queues**: Capture failed messages for investigation (future enhancement)

### 5. Security
- **Least privilege IAM**: Grant only required SNS/Step Functions permissions
- **Topic policies**: Restrict publishers to specific AWS services
- **Encryption**: Use KMS for SNS topics and DynamoDB tables

## Future Enhancements

### 1. SQS Dead Letter Queues
**Status**: Not yet implemented  
**Purpose**: Capture failed SNS deliveries for retry/investigation

```yaml
ExecutionNotificationsDLQ:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: '${ProjectName}-execution-notifications-dlq-${Environment}'
    MessageRetentionPeriod: 1209600  # 14 days
    KmsMasterKeyId: alias/aws/sqs

ExecutionNotificationsSubscription:
  Type: AWS::SNS::Subscription
  Properties:
    Protocol: email
    TopicArn: !Ref ExecutionNotificationsTopic
    Endpoint: !Ref AdminEmail
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt ExecutionNotificationsDLQ.Arn
```

### 2. Multi-Channel Notifications
**Status**: Planned  
**Channels**: SMS, PagerDuty, Slack, Microsoft Teams

```python
def send_execution_started_multi_channel(execution_id, plan_name, wave_count):
    # Email (existing)
    send_execution_started(execution_id, plan_name, wave_count)
    
    # SMS (future)
    send_sms_alert(f"DR Execution Started: {plan_name}")
    
    # PagerDuty (future)
    trigger_pagerduty_incident(execution_id, plan_name)
    
    # Slack (future)
    post_slack_message(f"🚀 DR Execution Started: {plan_name}")
```

### 3. SNS Filter Policies
**Status**: Partially implemented (recoveryPlanId filtering)  
**Enhancement**: Add severity-based filtering

```json
{
  "recoveryPlanId": ["plan-123"],
  "eventType": ["fail", "pause"],
  "severity": ["high", "critical"]
}
```

### 4. EventBridge Event Bus
**Status**: Not implemented  
**Purpose**: Custom event bus for DR orchestration events

```yaml
DROrchestrationEventBus:
  Type: AWS::Events::EventBus
  Properties:
    Name: '${ProjectName}-events-${Environment}'
```

## Conclusion

The integration of SNS, EventBridge, and Step Functions provides a robust, scalable, and maintainable event-driven architecture for DR orchestration. Key benefits:

- **Real-time notifications**: Immediate alerts for execution events and DRS service issues
- **Human-in-the-loop**: Email-based pause/resume with CloudShell CLI commands
- **Automated operations**: EventBridge schedules tag sync and inventory updates
- **Non-blocking design**: Notification failures don't impact DR operations
- **Extensible**: Easy to add new notification channels and event sources

This architecture ensures operations teams stay informed throughout the DR lifecycle while maintaining system reliability and operational excellence.
