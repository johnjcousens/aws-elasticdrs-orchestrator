# DRS Modular Orchestration Component Design

## Version 1.0 | December 2024

---

## 1. Overview

### 1.1 Purpose
A modular, tag-based DRS orchestration component that can be invoked by any parent orchestration system (Step Functions, SSM Automation, CLI, EventBridge) and returns structured output for downstream processing.

### 1.2 Design Principles
- **Tag-Based Selection**: No hardcoded server lists - all servers selected by tags
- **Multi-Staging Account**: Automatically distributes work across 3 staging accounts (300-server DRS limit)
- **Idempotent**: Safe to retry failed executions
- **Observable**: CloudWatch metrics, logs, and SNS notifications at each phase
- **Composable**: Output schema designed for chaining to next orchestration phase

---

## 2. Component Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           INVOCATION LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   AWS CLI   │  │ SSM Runbook │  │ Step Func   │  │ EventBridge │          │
│  │  Invoke     │  │   Step      │  │   Task      │  │   Rule      │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
└─────────┼────────────────┼────────────────┼────────────────┼─────────────────┘
          └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      DRS ORCHESTRATION STEP FUNCTION                          │
│                      (Main Entry Point)                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Validate Input                                                       │  │
│  │ 2. Discover Servers by Tags (across all staging accounts)              │  │
│  │ 3. Partition Servers by Staging Account                                │  │
│  │ 4. Execute Recovery (parallel across staging accounts)                 │  │
│  │ 5. Aggregate Results                                                   │  │
│  │ 6. Return Structured Output                                            │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ STAGING ACCOUNT 1│    │ STAGING ACCOUNT 2│    │ STAGING ACCOUNT 3│
│ Child Step Func  │    │ Child Step Func  │    │ Child Step Func  │
│ (≤300 servers)   │    │ (≤300 servers)   │    │ (≤300 servers)   │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## 3. Input/Output Specifications

### 3.1 Input Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DRS Orchestration Input",
  "type": "object",
  "required": ["action", "tags"],
  "properties": {
    "action": {
      "type": "string",
      "enum": ["failover", "failback", "drill", "terminate", "status"],
      "description": "The DRS operation to perform"
    },
    "tags": {
      "type": "object",
      "description": "Tag key-value pairs to select source servers",
      "minProperties": 1,
      "examples": [
        {"Wave": "1", "Application": "HRP"},
        {"Role": "DBServer", "Environment": "Production"},
        {"DR-Group": "Critical-Tier1"}
      ]
    },
    "options": {
      "type": "object",
      "properties": {
        "isDrill": {
          "type": "boolean",
          "default": false,
          "description": "If true, launches as drill (can be terminated without affecting replication)"
        },
        "maxWaitMinutes": {
          "type": "integer",
          "default": 120,
          "description": "Maximum time to wait for recovery completion"
        },
        "pointInTimeSnapshot": {
          "type": "string",
          "description": "Optional snapshot ID for point-in-time recovery"
        },
        "notificationArn": {
          "type": "string",
          "description": "SNS topic ARN for progress notifications"
        },
        "continueOnFailure": {
          "type": "boolean",
          "default": false,
          "description": "If true, continues with remaining servers if some fail"
        },
        "parallelism": {
          "type": "integer",
          "default": 50,
          "description": "Max concurrent server recoveries per staging account"
        }
      }
    },
    "metadata": {
      "type": "object",
      "description": "Pass-through metadata for tracking/correlation",
      "properties": {
        "correlationId": {"type": "string"},
        "parentExecutionId": {"type": "string"},
        "ticketId": {"type": "string"},
        "initiatedBy": {"type": "string"}
      }
    }
  }
}
```

### 3.2 Output Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DRS Orchestration Output",
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "partial", "failed", "timeout"],
      "description": "Overall execution status"
    },
    "action": {
      "type": "string",
      "description": "The action that was performed"
    },
    "summary": {
      "type": "object",
      "properties": {
        "totalServers": {"type": "integer"},
        "succeeded": {"type": "integer"},
        "failed": {"type": "integer"},
        "skipped": {"type": "integer"}
      }
    },
    "timing": {
      "type": "object",
      "properties": {
        "startTime": {"type": "string", "format": "date-time"},
        "endTime": {"type": "string", "format": "date-time"},
        "durationSeconds": {"type": "integer"},
        "durationFormatted": {"type": "string", "example": "PT45M30S"}
      }
    },
    "recoveryInstances": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sourceServerId": {"type": "string"},
          "sourceServerHostname": {"type": "string"},
          "recoveryInstanceId": {"type": "string"},
          "ec2InstanceId": {"type": "string"},
          "stagingAccountId": {"type": "string"},
          "status": {"type": "string", "enum": ["launched", "failed", "timeout"]},
          "privateIp": {"type": "string"},
          "launchTime": {"type": "string", "format": "date-time"},
          "tags": {"type": "object"}
        }
      }
    },
    "failedServers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "sourceServerId": {"type": "string"},
          "sourceServerHostname": {"type": "string"},
          "stagingAccountId": {"type": "string"},
          "errorCode": {"type": "string"},
          "errorMessage": {"type": "string"}
        }
      }
    },
    "stagingAccountResults": {
      "type": "array",
      "description": "Per-staging-account breakdown",
      "items": {
        "type": "object",
        "properties": {
          "accountId": {"type": "string"},
          "region": {"type": "string"},
          "serversProcessed": {"type": "integer"},
          "succeeded": {"type": "integer"},
          "failed": {"type": "integer"},
          "jobId": {"type": "string"}
        }
      }
    },
    "metadata": {
      "type": "object",
      "description": "Pass-through metadata from input"
    },
    "nextPhaseReady": {
      "type": "boolean",
      "description": "True if downstream phases can proceed"
    }
  }
}
```

---

## 4. Supported Actions

### 4.1 Action: `failover`
Initiates DRS recovery to launch instances in DR region.

| Phase | Description |
|-------|-------------|
| Discover | Find source servers matching tags across all staging accounts |
| Validate | Verify replication state is CONTINUOUS for all servers |
| Launch | Call StartRecovery API (parallel across staging accounts) |
| Monitor | Poll job status until COMPLETED or timeout |
| Output | Return recovery instance details |

### 4.2 Action: `failback`
Initiates failback from DR region to primary region.

| Phase | Description |
|-------|-------------|
| Discover | Find recovery instances matching tags |
| Validate | Verify failback replication is ready |
| Launch | Call StartFailbackLaunch API |
| Monitor | Poll until failback complete |
| Output | Return source server status |

### 4.3 Action: `drill`
Same as failover but with `isDrill=true` flag.

| Phase | Description |
|-------|-------------|
| Same as failover | But instances tagged as drill |
| Output | Includes drill-specific metadata |

### 4.4 Action: `terminate`
Terminates recovery instances (for drill cleanup or failback completion).

| Phase | Description |
|-------|-------------|
| Discover | Find recovery instances matching tags |
| Terminate | Call TerminateRecoveryInstances API |
| Monitor | Poll until termination complete |
| Output | Confirmation of terminated instances |

### 4.5 Action: `status`
Returns current state without making changes.

| Phase | Description |
|-------|-------------|
| Discover | Find source servers and recovery instances matching tags |
| Report | Return replication state, recovery instance state |
| Output | Current status snapshot |

---

## 5. Tag-Based Server Selection

### 5.1 Tag Strategy

Servers are selected using AND logic across all provided tags:

```python
# Example: Find servers with Wave=1 AND Application=HRP
input_tags = {"Wave": "1", "Application": "HRP"}

# Matches server with tags: {Wave: "1", Application: "HRP", Role: "DBServer"}
# Does NOT match: {Wave: "2", Application: "HRP"}
```

### 5.2 Recommended Tag Schema

| Tag Key | Purpose | Example Values |
|---------|---------|----------------|
| `DR-Wave` | Recovery sequence order | `1`, `2`, `3`, `4` |
| `DR-Application` | Application grouping | `HRP`, `HealthEdge`, `Connectors` |
| `DR-Role` | Server role within app | `DBServer`, `AppServer`, `WebServer` |
| `DR-Tier` | Criticality tier | `Critical`, `Standard`, `NonCritical` |
| `DR-StagingAccount` | Which staging account | `staging-1`, `staging-2`, `staging-3` |
| `DR-Enabled` | Include in DR automation | `true`, `false` |

### 5.3 Tag Discovery Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    TAG DISCOVERY LAMBDA                          │
└─────────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    ▼                         ▼                         ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ Staging     │       │ Staging     │       │ Staging     │
│ Account 1   │       │ Account 2   │       │ Account 3   │
│             │       │             │       │             │
│ AssumeRole  │       │ AssumeRole  │       │ AssumeRole  │
│     ↓       │       │     ↓       │       │     ↓       │
│ DRS API:    │       │ DRS API:    │       │ DRS API:    │
│ describe_   │       │ describe_   │       │ describe_   │
│ source_     │       │ source_     │       │ source_     │
│ servers()   │       │ servers()   │       │ servers()   │
│     ↓       │       │     ↓       │       │     ↓       │
│ Filter by   │       │ Filter by   │       │ Filter by   │
│ tags        │       │ tags        │       │ tags        │
└─────────────┘       └─────────────┘       └─────────────┘
    │                         │                         │
    └─────────────────────────┼─────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │ Merged Server   │
                    │ List with       │
                    │ Account Mapping │
                    └─────────────────┘
```

---

## 6. Multi-Staging Account Architecture

### 6.1 Account Configuration (SSM Parameter Store)

```json
{
  "stagingAccounts": [
    {
      "accountId": "111111111111",
      "region": "us-east-2",
      "roleArn": "arn:aws:iam::111111111111:role/DRS-Orchestration-Role",
      "maxServers": 300,
      "priority": 1
    },
    {
      "accountId": "222222222222",
      "region": "us-east-2",
      "roleArn": "arn:aws:iam::222222222222:role/DRS-Orchestration-Role",
      "maxServers": 300,
      "priority": 2
    },
    {
      "accountId": "333333333333",
      "region": "us-east-2",
      "roleArn": "arn:aws:iam::333333333333:role/DRS-Orchestration-Role",
      "maxServers": 300,
      "priority": 3
    }
  ]
}
```

### 6.2 Cross-Account Execution Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│              ORCHESTRATOR ACCOUNT (Central)                      │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           MAIN DRS STEP FUNCTION                          │   │
│  │                                                           │   │
│  │  1. Read staging account config from SSM                  │   │
│  │  2. Discover servers by tags (parallel across accounts)   │   │
│  │  3. Map: For each staging account with matching servers   │   │
│  │     → Start child execution (parallel)                    │   │
│  │  4. Wait for all child executions                         │   │
│  │  5. Aggregate results                                     │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │ Cross-Account Invocation
         ┌─────────────────────┼─────────────────────────┐
         ▼                     ▼                         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ STAGING ACCT 1  │  │ STAGING ACCT 2  │  │ STAGING ACCT 3  │
│                 │  │                 │  │                 │
│ Child Step Func │  │ Child Step Func │  │ Child Step Func │
│ - StartRecovery │  │ - StartRecovery │  │ - StartRecovery │
│ - Monitor Jobs  │  │ - Monitor Jobs  │  │ - Monitor Jobs  │
│ - Return Result │  │ - Return Result │  │ - Return Result │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 6.3 IAM Role in Each Staging Account

```yaml
DRSOrchestrationRole:
  Type: AWS::IAM::Role
  Properties:
    RoleName: DRS-Orchestration-Role
    AssumeRolePolicyDocument:
      Version: "2012-10-17"
      Statement:
        - Effect: Allow
          Principal:
            AWS: !Sub "arn:aws:iam::${OrchestratorAccountId}:root"
          Action: sts:AssumeRole
          Condition:
            StringEquals:
              aws:PrincipalOrgID: !Ref OrganizationId
    Policies:
      - PolicyName: DRS-Operations
        PolicyDocument:
          Version: "2012-10-17"
          Statement:
            - Effect: Allow
              Action:
                - drs:DescribeSourceServers
                - drs:StartRecovery
                - drs:DescribeJobs
                - drs:DescribeRecoveryInstances
                - drs:TerminateRecoveryInstances
                - drs:StartFailbackLaunch
                - drs:ReverseReplication
                - drs:StopReplication
                - drs:DisconnectSourceServer
              Resource: "*"
            - Effect: Allow
              Action:
                - ec2:DescribeInstances
                - ec2:DescribeTags
              Resource: "*"
```

---

## 7. Step Function Definition

### 7.1 Main Orchestrator State Machine

```yaml
Comment: "DRS Modular Orchestration - Main Entry Point"
StartAt: ValidateInput
States:

  ValidateInput:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-orchestration-validate
    ResultPath: $.validation
    Next: DiscoverServers
    Catch:
      - ErrorEquals: ["ValidationError"]
        Next: FailValidation

  DiscoverServers:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-orchestration-discover
    Comment: "Find servers matching tags across all staging accounts"
    ResultPath: $.discovery
    Next: CheckServersFound

  CheckServersFound:
    Type: Choice
    Choices:
      - Variable: $.discovery.totalServers
        NumericEquals: 0
        Next: NoServersFound
    Default: PartitionByAccount

  PartitionByAccount:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-orchestration-partition
    Comment: "Group servers by staging account"
    ResultPath: $.partitions
    Next: ExecutePerAccount

  ExecutePerAccount:
    Type: Map
    ItemsPath: $.partitions.accounts
    MaxConcurrency: 3
    Parameters:
      accountId.$: $$.Map.Item.Value.accountId
      servers.$: $$.Map.Item.Value.servers
      action.$: $.action
      options.$: $.options
      metadata.$: $.metadata
    Iterator:
      StartAt: AssumeRoleAndExecute
      States:
        AssumeRoleAndExecute:
          Type: Task
          Resource: arn:aws:states:::states:startExecution.sync:2
          Parameters:
            StateMachineArn.$: States.Format('arn:aws:states:{}:{}:stateMachine:drs-staging-account-executor', $.region, $.accountId)
            Input:
              servers.$: $.servers
              action.$: $.action
              options.$: $.options
          ResultPath: $.accountResult
          End: true
    ResultPath: $.accountResults
    Next: AggregateResults

  AggregateResults:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-orchestration-aggregate
    ResultPath: $.finalResult
    Next: SendNotification

  SendNotification:
    Type: Task
    Resource: arn:aws:states:::sns:publish
    Parameters:
      TopicArn.$: $.options.notificationArn
      Message.$: States.JsonToString($.finalResult)
      Subject: "DRS Orchestration Complete"
    ResultPath: null
    Next: ReturnOutput

  ReturnOutput:
    Type: Pass
    OutputPath: $.finalResult
    End: true

  NoServersFound:
    Type: Pass
    Result:
      status: "success"
      summary:
        totalServers: 0
        succeeded: 0
        failed: 0
      message: "No servers found matching the specified tags"
      nextPhaseReady: true
    End: true

  FailValidation:
    Type: Fail
    Error: "ValidationError"
    Cause: "Input validation failed"
```

### 7.2 Staging Account Executor State Machine

```yaml
Comment: "DRS Staging Account Executor - Runs in each staging account"
StartAt: DetermineAction
States:

  DetermineAction:
    Type: Choice
    Choices:
      - Variable: $.action
        StringEquals: "failover"
        Next: StartRecovery
      - Variable: $.action
        StringEquals: "drill"
        Next: StartRecovery
      - Variable: $.action
        StringEquals: "failback"
        Next: StartFailback
      - Variable: $.action
        StringEquals: "terminate"
        Next: TerminateInstances
      - Variable: $.action
        StringEquals: "status"
        Next: GetStatus
    Default: InvalidAction

  StartRecovery:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-start-recovery
    Parameters:
      sourceServerIds.$: $.servers[*].sourceServerId
      isDrill.$: $.options.isDrill
      tags:
        DR-Orchestration: "true"
        DR-CorrelationId.$: $.metadata.correlationId
    ResultPath: $.recoveryJob
    Next: MonitorRecoveryJob

  MonitorRecoveryJob:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-monitor-job
    Parameters:
      jobId.$: $.recoveryJob.jobId
      maxWaitMinutes.$: $.options.maxWaitMinutes
    ResultPath: $.jobStatus
    Retry:
      - ErrorEquals: ["JobInProgress"]
        IntervalSeconds: 30
        MaxAttempts: 240
        BackoffRate: 1
    Next: GetRecoveryInstances

  GetRecoveryInstances:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-get-recovery-instances
    Parameters:
      jobId.$: $.recoveryJob.jobId
    ResultPath: $.recoveryInstances
    Next: FormatOutput

  StartFailback:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-start-failback
    Parameters:
      recoveryInstanceIds.$: $.servers[*].recoveryInstanceId
    ResultPath: $.failbackJob
    Next: MonitorFailbackJob

  MonitorFailbackJob:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-monitor-failback
    Parameters:
      recoveryInstanceIds.$: $.servers[*].recoveryInstanceId
      maxWaitMinutes.$: $.options.maxWaitMinutes
    ResultPath: $.failbackStatus
    Retry:
      - ErrorEquals: ["FailbackInProgress"]
        IntervalSeconds: 60
        MaxAttempts: 120
        BackoffRate: 1
    Next: FormatOutput

  TerminateInstances:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-terminate-instances
    Parameters:
      recoveryInstanceIds.$: $.servers[*].recoveryInstanceId
    ResultPath: $.terminateResult
    Next: FormatOutput

  GetStatus:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-get-status
    Parameters:
      sourceServerIds.$: $.servers[*].sourceServerId
    ResultPath: $.statusResult
    Next: FormatOutput

  FormatOutput:
    Type: Task
    Resource: arn:aws:lambda:${Region}:${AccountId}:function:drs-format-output
    End: true

  InvalidAction:
    Type: Fail
    Error: "InvalidAction"
    Cause: "Unknown action specified"
```

---

## 8. Invocation Methods

### 8.1 AWS CLI Invocation

```bash
# Start a drill for Wave 1 servers
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:drs-orchestration-main \
  --input '{
    "action": "drill",
    "tags": {"DR-Wave": "1", "DR-Application": "HRP"},
    "options": {
      "isDrill": true,
      "maxWaitMinutes": 90,
      "notificationArn": "arn:aws:sns:us-east-1:123456789012:dr-notifications"
    },
    "metadata": {
      "correlationId": "drill-2024-12-12-001",
      "initiatedBy": "jsmith"
    }
  }'

# Get execution result
aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:us-east-1:123456789012:execution:drs-orchestration-main:drill-2024-12-12-001
```

### 8.2 SSM Automation Document Integration

```yaml
description: "Invoke DRS Orchestration as part of DR Runbook"
schemaVersion: "0.3"
assumeRole: "{{AutomationAssumeRole}}"
parameters:
  Action:
    type: String
    allowedValues: ["failover", "failback", "drill", "terminate", "status"]
  WaveNumber:
    type: String
    default: "1"
  Application:
    type: String
    default: "HRP"
  IsDrill:
    type: Boolean
    default: true
  MaxWaitMinutes:
    type: Integer
    default: 120
  AutomationAssumeRole:
    type: String

mainSteps:
  - name: InvokeDRSOrchestration
    action: aws:executeStateMachine
    inputs:
      stateMachineArn: arn:aws:states:us-east-1:123456789012:stateMachine:drs-orchestration-main
      input: |
        {
          "action": "{{Action}}",
          "tags": {
            "DR-Wave": "{{WaveNumber}}",
            "DR-Application": "{{Application}}"
          },
          "options": {
            "isDrill": {{IsDrill}},
            "maxWaitMinutes": {{MaxWaitMinutes}}
          },
          "metadata": {
            "correlationId": "{{automation:EXECUTION_ID}}",
            "parentExecutionId": "{{automation:EXECUTION_ID}}"
          }
        }
    outputs:
      - Name: DRSResult
        Selector: $.output
        Type: String
    nextStep: ParseDRSOutput

  - name: ParseDRSOutput
    action: aws:executeScript
    inputs:
      Runtime: python3.9
      Handler: parse_output
      Script: |
        def parse_output(events, context):
            import json
            result = json.loads(events['DRSResult'])
            return {
                'status': result['status'],
                'succeeded': result['summary']['succeeded'],
                'failed': result['summary']['failed'],
                'nextPhaseReady': result['nextPhaseReady'],
                'recoveryInstances': result.get('recoveryInstances', [])
            }
      InputPayload:
        DRSResult: "{{InvokeDRSOrchestration.DRSResult}}"
    outputs:
      - Name: Status
        Selector: $.Payload.status
        Type: String
      - Name: NextPhaseReady
        Selector: $.Payload.nextPhaseReady
        Type: Boolean
      - Name: RecoveryInstances
        Selector: $.Payload.recoveryInstances
        Type: StringList
    isEnd: true
```

### 8.3 EventBridge Rule (Scheduled or Event-Triggered)

```yaml
DRSOrchestrationScheduledRule:
  Type: AWS::Events::Rule
  Properties:
    Name: drs-weekly-drill-wave1
    Description: "Weekly DR drill for Wave 1 servers"
    ScheduleExpression: "cron(0 6 ? * SAT *)"  # Every Saturday at 6 AM UTC
    State: ENABLED
    Targets:
      - Id: DRSOrchestrationTarget
        Arn: !GetAtt DRSOrchestrationStateMachine.Arn
        RoleArn: !GetAtt EventBridgeInvokeRole.Arn
        Input: |
          {
            "action": "drill",
            "tags": {"DR-Wave": "1"},
            "options": {
              "isDrill": true,
              "maxWaitMinutes": 120,
              "notificationArn": "arn:aws:sns:us-east-1:123456789012:dr-notifications"
            },
            "metadata": {
              "correlationId": "scheduled-drill",
              "initiatedBy": "eventbridge-schedule"
            }
          }
```

### 8.4 Parent Step Function Integration

```yaml
# In parent DR orchestration Step Function
InvokeDRSWave1:
  Type: Task
  Resource: arn:aws:states:::states:startExecution.sync:2
  Parameters:
    StateMachineArn: arn:aws:states:us-east-1:123456789012:stateMachine:drs-orchestration-main
    Input:
      action: "failover"
      tags:
        DR-Wave: "1"
      options:
        isDrill.$: $.isDrill
        maxWaitMinutes: 90
      metadata:
        correlationId.$: $$.Execution.Id
        parentExecutionId.$: $$.Execution.Id
  ResultPath: $.wave1Result
  Next: CheckWave1Success

CheckWave1Success:
  Type: Choice
  Choices:
    - Variable: $.wave1Result.Output.status
      StringEquals: "success"
      Next: InvokeDRSWave2
    - Variable: $.wave1Result.Output.status
      StringEquals: "partial"
      Next: HandlePartialFailure
  Default: HandleFailure

InvokeDRSWave2:
  Type: Task
  Resource: arn:aws:states:::states:startExecution.sync:2
  Parameters:
    StateMachineArn: arn:aws:states:us-east-1:123456789012:stateMachine:drs-orchestration-main
    Input:
      action: "failover"
      tags:
        DR-Wave: "2"
      options:
        isDrill.$: $.isDrill
        maxWaitMinutes: 90
      metadata:
        correlationId.$: $$.Execution.Id
        wave1Instances.$: $.wave1Result.Output.recoveryInstances
  ResultPath: $.wave2Result
  Next: ProceedToNextPhase
```

---

## 9. Lambda Functions

### 9.1 Function Inventory

| Function Name | Purpose | Runtime |
|---------------|---------|---------|
| `drs-orchestration-validate` | Validate input schema | Python 3.11 |
| `drs-orchestration-discover` | Find servers by tags across accounts | Python 3.11 |
| `drs-orchestration-partition` | Group servers by staging account | Python 3.11 |
| `drs-orchestration-aggregate` | Combine results from all accounts | Python 3.11 |
| `drs-start-recovery` | Call DRS StartRecovery API | Python 3.11 |
| `drs-monitor-job` | Poll DRS job status | Python 3.11 |
| `drs-get-recovery-instances` | Get launched instance details | Python 3.11 |
| `drs-start-failback` | Call DRS StartFailbackLaunch API | Python 3.11 |
| `drs-monitor-failback` | Poll failback status | Python 3.11 |
| `drs-terminate-instances` | Call DRS TerminateRecoveryInstances | Python 3.11 |
| `drs-get-status` | Get current replication/recovery status | Python 3.11 |
| `drs-format-output` | Format output for return | Python 3.11 |

### 9.2 Key Lambda: drs-orchestration-discover

```python
import boto3
import json
import os
from concurrent.futures import ThreadPoolExecutor

def lambda_handler(event, context):
    """
    Discover DRS source servers matching tags across all staging accounts.
    """
    input_tags = event['tags']
    staging_accounts = json.loads(os.environ['STAGING_ACCOUNTS'])
    
    all_servers = []
    
    def discover_in_account(account_config):
        """Discover servers in a single staging account."""
        sts = boto3.client('sts')
        credentials = sts.assume_role(
            RoleArn=account_config['roleArn'],
            RoleSessionName='drs-orchestration-discover'
        )['Credentials']
        
        drs = boto3.client(
            'drs',
            region_name=account_config['region'],
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        
        servers = []
        paginator = drs.get_paginator('describe_source_servers')
        
        for page in paginator.paginate():
            for server in page['items']:
                server_tags = server.get('tags', {})
                
                # Check if all input tags match
                if all(server_tags.get(k) == v for k, v in input_tags.items()):
                    servers.append({
                        'sourceServerId': server['sourceServerID'],
                        'hostname': server['sourceProperties']['identificationHints'].get('hostname', 'unknown'),
                        'replicationState': server['dataReplicationInfo']['dataReplicationState'],
                        'stagingAccountId': account_config['accountId'],
                        'stagingRegion': account_config['region'],
                        'tags': server_tags
                    })
        
        return servers
    
    # Parallel discovery across all staging accounts
    with ThreadPoolExecutor(max_workers=len(staging_accounts)) as executor:
        results = executor.map(discover_in_account, staging_accounts)
        for account_servers in results:
            all_servers.extend(account_servers)
    
    return {
        'totalServers': len(all_servers),
        'servers': all_servers,
        'byAccount': group_by_account(all_servers)
    }

def group_by_account(servers):
    """Group servers by staging account."""
    grouped = {}
    for server in servers:
        account_id = server['stagingAccountId']
        if account_id not in grouped:
            grouped[account_id] = []
        grouped[account_id].append(server)
    return grouped
```

---

## 10. Observability

### 10.1 CloudWatch Metrics

| Metric | Namespace | Dimensions | Description |
|--------|-----------|------------|-------------|
| `ExecutionCount` | `DRS/Orchestration` | Action, Status | Count of executions by action and status |
| `ServersProcessed` | `DRS/Orchestration` | Action, StagingAccount | Servers processed per execution |
| `ExecutionDuration` | `DRS/Orchestration` | Action | Time to complete execution (seconds) |
| `FailedServers` | `DRS/Orchestration` | Action, StagingAccount | Count of failed server recoveries |
| `RecoveryLaunchTime` | `DRS/Orchestration` | StagingAccount | Time from StartRecovery to instance running |

### 10.2 CloudWatch Dashboard

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "DRS Orchestration Executions",
        "metrics": [
          ["DRS/Orchestration", "ExecutionCount", "Action", "failover", "Status", "success"],
          ["...", "Status", "failed"],
          ["...", "Action", "drill", "Status", "success"],
          ["...", "Status", "failed"]
        ],
        "period": 3600,
        "stat": "Sum"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Servers Processed by Staging Account",
        "metrics": [
          ["DRS/Orchestration", "ServersProcessed", "StagingAccount", "111111111111"],
          ["...", "StagingAccount", "222222222222"],
          ["...", "StagingAccount", "333333333333"]
        ],
        "period": 3600,
        "stat": "Sum"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Average Recovery Duration",
        "metrics": [
          ["DRS/Orchestration", "ExecutionDuration", "Action", "failover"],
          ["...", "Action", "drill"]
        ],
        "period": 86400,
        "stat": "Average"
      }
    }
  ]
}
```

### 10.3 SNS Notifications

```json
{
  "notificationTypes": {
    "executionStarted": {
      "subject": "DRS Orchestration Started: {{action}} for {{tags}}",
      "body": "Execution {{correlationId}} started at {{startTime}}"
    },
    "executionCompleted": {
      "subject": "DRS Orchestration {{status}}: {{action}}",
      "body": "Completed: {{succeeded}}/{{total}} servers. Duration: {{duration}}"
    },
    "executionFailed": {
      "subject": "ALERT: DRS Orchestration Failed",
      "body": "Failed servers: {{failedServers}}. Error: {{errorMessage}}"
    },
    "partialSuccess": {
      "subject": "WARNING: DRS Orchestration Partial Success",
      "body": "{{succeeded}} succeeded, {{failed}} failed. Review required."
    }
  }
}
```

---

## 11. Error Handling

### 11.1 Error Categories

| Error Type | Retry | Action |
|------------|-------|--------|
| `ThrottlingException` | Yes (exponential backoff) | Automatic retry |
| `ValidationError` | No | Return error to caller |
| `ServerNotReady` | Yes (fixed interval) | Wait for replication state |
| `JobTimeout` | No | Mark as timeout, continue if `continueOnFailure` |
| `CrossAccountAccessDenied` | No | Alert, skip account |
| `DRSServiceError` | Yes (3 attempts) | Retry then fail |

### 11.2 Retry Configuration

```yaml
RetryPolicy:
  - ErrorEquals: ["ThrottlingException", "ServiceUnavailable"]
    IntervalSeconds: 5
    MaxAttempts: 5
    BackoffRate: 2
  - ErrorEquals: ["DRSServiceError"]
    IntervalSeconds: 30
    MaxAttempts: 3
    BackoffRate: 1.5
  - ErrorEquals: ["JobInProgress"]
    IntervalSeconds: 30
    MaxAttempts: 240  # 2 hours max wait
    BackoffRate: 1
```

### 11.3 Graceful Degradation

When `continueOnFailure: true`:
1. Failed servers are logged but don't stop execution
2. Remaining servers continue processing
3. Final status is `partial` instead of `failed`
4. Output includes both `recoveryInstances` and `failedServers`
5. `nextPhaseReady` is `true` if >50% succeeded (configurable)

---

## 12. Security Considerations

### 12.1 IAM Least Privilege

```yaml
# Orchestrator account role - can only assume staging account roles
OrchestratorRole:
  Policies:
    - PolicyName: AssumeStaginAccountRoles
      PolicyDocument:
        Statement:
          - Effect: Allow
            Action: sts:AssumeRole
            Resource:
              - arn:aws:iam::111111111111:role/DRS-Orchestration-Role
              - arn:aws:iam::222222222222:role/DRS-Orchestration-Role
              - arn:aws:iam::333333333333:role/DRS-Orchestration-Role
            Condition:
              StringEquals:
                aws:PrincipalOrgID: o-xxxxxxxxxx

# Staging account role - DRS operations only
StagingAccountRole:
  Policies:
    - PolicyName: DRSOperations
      PolicyDocument:
        Statement:
          - Effect: Allow
            Action:
              - drs:Describe*
              - drs:StartRecovery
              - drs:TerminateRecoveryInstances
              - drs:StartFailbackLaunch
            Resource: "*"
          - Effect: Deny
            Action:
              - drs:DeleteSourceServer
              - drs:DisconnectSourceServer
            Resource: "*"
            Condition:
              StringNotEquals:
                aws:PrincipalTag/DR-Orchestration: "cleanup-authorized"
```

### 12.2 Encryption

- All Lambda environment variables encrypted with KMS
- Step Function execution history encrypted
- SNS notifications encrypted in transit
- CloudWatch Logs encrypted with customer-managed key

### 12.3 Audit Trail

- All executions logged to CloudWatch Logs
- CloudTrail captures all DRS API calls
- Step Function execution history retained for 90 days
- SNS notifications include correlation IDs for tracing

---

## 13. Deployment

### 13.1 CloudFormation Stack Structure

```
drs-orchestration/
├── templates/
│   ├── main-orchestrator.yaml       # Main Step Function + Lambdas
│   ├── staging-account-executor.yaml # Child Step Function (deploy to each staging account)
│   ├── iam-roles.yaml               # Cross-account roles
│   └── observability.yaml           # Dashboard, alarms, SNS
├── lambda/
│   ├── discover/
│   ├── partition/
│   ├── aggregate/
│   ├── start-recovery/
│   ├── monitor-job/
│   └── ...
└── config/
    └── staging-accounts.json
```

### 13.2 Deployment Order

1. Deploy IAM roles to each staging account
2. Deploy staging-account-executor to each staging account
3. Deploy main-orchestrator to central account
4. Deploy observability stack
5. Configure SSM parameters with staging account details
6. Test with `status` action first

---

## 14. Testing Strategy

### 14.1 Test Scenarios

| Test | Input | Expected Output |
|------|-------|-----------------|
| Single server drill | `{"action": "drill", "tags": {"DR-Test": "single"}}` | 1 server recovered |
| Wave 1 drill | `{"action": "drill", "tags": {"DR-Wave": "1"}}` | All Wave 1 servers recovered |
| Multi-account drill | Tags spanning 2+ staging accounts | Parallel execution, aggregated results |
| No matching servers | Tags with no matches | `status: success`, `totalServers: 0` |
| Partial failure | Mix of healthy and unhealthy servers | `status: partial`, both lists populated |
| Timeout handling | Server stuck in recovery | `status: timeout` after maxWaitMinutes |
| Terminate drill | `{"action": "terminate", "tags": {"DR-Test": "single"}}` | Instances terminated |

### 14.2 Integration Test Script

```bash
#!/bin/bash
# test-drs-orchestration.sh

# Test 1: Status check (non-destructive)
echo "Test 1: Status check..."
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"action": "status", "tags": {"DR-Wave": "1"}}' \
  --query 'executionArn' --output text

# Test 2: Single server drill
echo "Test 2: Single server drill..."
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --input '{"action": "drill", "tags": {"DR-Test": "single"}, "options": {"isDrill": true}}' \
  --query 'executionArn' --output text

# Wait and check result
sleep 300
# ... check execution status
```

---

## 15. Appendix

### 15.1 Complete Input Example

```json
{
  "action": "failover",
  "tags": {
    "DR-Wave": "1",
    "DR-Application": "HRP",
    "DR-Enabled": "true"
  },
  "options": {
    "isDrill": false,
    "maxWaitMinutes": 120,
    "continueOnFailure": true,
    "parallelism": 50,
    "notificationArn": "arn:aws:sns:us-east-1:123456789012:dr-notifications"
  },
  "metadata": {
    "correlationId": "DR-2024-12-12-PROD-001",
    "parentExecutionId": "arn:aws:states:us-east-1:123456789012:execution:dr-master:exec-123",
    "ticketId": "INC0012345",
    "initiatedBy": "jsmith@company.com"
  }
}
```

### 15.2 Complete Output Example

```json
{
  "status": "success",
  "action": "failover",
  "summary": {
    "totalServers": 150,
    "succeeded": 150,
    "failed": 0,
    "skipped": 0
  },
  "timing": {
    "startTime": "2024-12-12T14:00:00Z",
    "endTime": "2024-12-12T14:45:30Z",
    "durationSeconds": 2730,
    "durationFormatted": "PT45M30S"
  },
  "recoveryInstances": [
    {
      "sourceServerId": "s-abc123",
      "sourceServerHostname": "web-server-01",
      "recoveryInstanceId": "i-xyz789",
      "ec2InstanceId": "i-xyz789",
      "stagingAccountId": "111111111111",
      "status": "launched",
      "privateIp": "10.0.1.50",
      "launchTime": "2024-12-12T14:15:00Z",
      "tags": {"DR-Wave": "1", "DR-Application": "HRP", "Role": "WebServer"}
    }
  ],
  "failedServers": [],
  "stagingAccountResults": [
    {
      "accountId": "111111111111",
      "region": "us-east-2",
      "serversProcessed": 75,
      "succeeded": 75,
      "failed": 0,
      "jobId": "drsjob-111-abc"
    },
    {
      "accountId": "222222222222",
      "region": "us-east-2",
      "serversProcessed": 75,
      "succeeded": 75,
      "failed": 0,
      "jobId": "drsjob-222-def"
    }
  ],
  "metadata": {
    "correlationId": "DR-2024-12-12-PROD-001",
    "parentExecutionId": "arn:aws:states:us-east-1:123456789012:execution:dr-master:exec-123",
    "ticketId": "INC0012345"
  },
  "nextPhaseReady": true
}
```
