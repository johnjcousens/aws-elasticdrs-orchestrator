# Step Functions Lambda Invocation Examples

## Overview

This directory contains examples for invoking Lambda functions from AWS Step Functions state machines using direct invocation mode. These examples demonstrate how to orchestrate disaster recovery operations using Step Functions with the DR Orchestration Platform's Lambda handlers.

## Table of Contents

1. [State Machine Definition](#state-machine-definition)
2. [Lambda Invocation Patterns](#lambda-invocation-patterns)
3. [Error Handling Strategies](#error-handling-strategies)
4. [Deployment Instructions](#deployment-instructions)
5. [Testing Procedures](#testing-procedures)
6. [Integration with CDK Stack](#integration-with-cdk-stack)
7. [Troubleshooting](#troubleshooting)

## State Machine Definition

The `lambda-invocation-example.json` file contains a complete Step Functions state machine definition that demonstrates:

- **Direct Lambda invocation** using the `arn:aws:states:::lambda:invoke` resource
- **Operation-based event format** for all three Lambda handlers
- **Sequential wave processing** with Map state
- **Comprehensive error handling** with retry and catch blocks
- **Result transformation** using ResultSelector
- **State data flow** using ResultPath

### State Machine Flow

```
InitializeExecution (Data Management Handler)
    ↓
GetRecoveryPlan (Query Handler)
    ↓
ProcessWaves (Map State - Sequential)
    ├─ StartWaveRecovery (Execution Handler)
    ├─ WaitForWaveCompletion (Wait 30s)
    ├─ CheckWaveStatus (Query Handler)
    └─ IsWaveComplete (Choice)
        ├─ COMPLETED → WaveSuccess
        ├─ FAILED → WaveFailed
        └─ IN_PROGRESS → WaitForWaveCompletion
    ↓
GetRecoveryInstances (Execution Handler)
    ↓
FinalizeExecution (Data Management Handler)
    ↓
ExecutionSuccess
```


## Lambda Invocation Patterns

### Pattern 1: Query Handler Invocation (Read Operations)

The Query Handler performs read-only operations to retrieve data from DynamoDB and AWS DRS.

**Example: Get Recovery Plan**

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Parameters": {
    "FunctionName": "aws-drs-orchestration-query-handler-test",
    "Payload": {
      "operation": "get_recovery_plan",
      "planId.$": "$.planId"
    }
  },
  "ResultPath": "$.planDetails",
  "ResultSelector": {
    "plan.$": "$.Payload"
  }
}
```

**Supported Operations:**
- `list_protection_groups` - List all protection groups
- `get_protection_group` - Get specific protection group details
- `list_recovery_plans` - List all recovery plans
- `get_recovery_plan` - Get specific recovery plan details
- `list_executions` - List all executions with optional filtering
- `get_execution` - Get specific execution details
- `get_drs_source_servers` - Get DRS source servers
- `get_target_accounts` - Get registered target accounts
- `get_wave_status` - Get wave recovery status

**Response Format:**

Query Handler returns data directly without API Gateway wrapping:

```json
{
  "planId": "plan-xyz789",
  "name": "Production DR Plan",
  "protectionGroupId": "pg-abc123",
  "waves": [
    {
      "waveNumber": 1,
      "name": "Database Tier",
      "servers": ["s-1234567890abcdef0"]
    }
  ]
}
```


### Pattern 2: Execution Handler Invocation (Recovery Operations)

The Execution Handler manages recovery execution lifecycle operations.

**Example: Start Wave Recovery**

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Parameters": {
    "FunctionName": "aws-drs-orchestration-execution-handler-test",
    "Payload": {
      "operation": "start_wave_recovery",
      "executionId.$": "$.executionId",
      "waveNumber.$": "$.waveNumber",
      "servers.$": "$.servers"
    }
  },
  "ResultPath": "$.waveStartResult",
  "ResultSelector": {
    "jobId.$": "$.Payload.jobId",
    "status.$": "$.Payload.status"
  }
}
```

**Supported Operations:**
- `start_execution` - Start a new recovery plan execution
- `cancel_execution` - Cancel an in-progress execution
- `pause_execution` - Pause an in-progress execution
- `resume_execution` - Resume a paused execution
- `terminate_instances` - Terminate recovery instances
- `get_recovery_instances` - Get recovery instance details
- `start_wave_recovery` - Start recovery for a specific wave

**Response Format:**

```json
{
  "jobId": "drsjob-abc123",
  "status": "IN_PROGRESS",
  "waveNumber": 1,
  "startTime": "2025-02-01T10:00:00Z"
}
```


### Pattern 3: Data Management Handler Invocation (CRUD Operations)

The Data Management Handler performs create, update, and delete operations.

**Example: Initialize Execution**

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Parameters": {
    "FunctionName": "aws-drs-orchestration-data-management-handler-test",
    "Payload": {
      "operation": "initialize_execution",
      "executionId.$": "$.executionId",
      "planId.$": "$.planId",
      "executionType.$": "$.executionType"
    }
  },
  "ResultPath": "$.initResult"
}
```

**Supported Operations:**
- `create_protection_group` - Create a new protection group
- `update_protection_group` - Update protection group details
- `delete_protection_group` - Delete a protection group
- `create_recovery_plan` - Create a new recovery plan
- `update_recovery_plan` - Update recovery plan details
- `delete_recovery_plan` - Delete a recovery plan
- `initialize_execution` - Initialize a new execution
- `finalize_execution` - Finalize execution and update status
- `log_error` - Log error information

**Response Format:**

```json
{
  "executionId": "exec-123456",
  "status": "INITIALIZED",
  "timestamp": "2025-02-01T10:00:00Z"
}
```


## Error Handling Strategies

### Strategy 1: Retry with Exponential Backoff

All Lambda invocations include retry logic for transient failures:

```json
"Retry": [
  {
    "ErrorEquals": [
      "Lambda.ServiceException",
      "Lambda.AWSLambdaException",
      "Lambda.SdkClientException"
    ],
    "IntervalSeconds": 2,
    "MaxAttempts": 3,
    "BackoffRate": 2
  }
]
```

**Retry Behavior:**
- First retry: Wait 2 seconds
- Second retry: Wait 4 seconds (2 × 2)
- Third retry: Wait 8 seconds (4 × 2)
- After 3 attempts: Move to Catch block

### Strategy 2: Error Catching and Logging

Catch blocks capture errors and route to error handling states:

```json
"Catch": [
  {
    "ErrorEquals": ["States.ALL"],
    "ResultPath": "$.error",
    "Next": "HandleInitializationError"
  }
]
```

**Error Information Captured:**
- Error type (e.g., "Lambda.ServiceException")
- Error message
- Stack trace (if available)
- Original input that caused the error

### Strategy 3: Graceful Degradation

Error handling states log errors and provide meaningful failure messages:

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Parameters": {
    "FunctionName": "aws-drs-orchestration-data-management-handler-test",
    "Payload": {
      "operation": "log_error",
      "executionId.$": "$.executionId",
      "error.$": "$.error",
      "stage": "INITIALIZATION"
    }
  },
  "ResultPath": null,
  "Next": "ExecutionFailed"
}
```


## Deployment Instructions

### Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **IAM permissions** to create Step Functions state machines
3. **Lambda functions deployed** (Query, Execution, Data Management handlers)
4. **DynamoDB tables created** (Protection Groups, Recovery Plans, Executions)

### Step 1: Update Function Names

Edit `lambda-invocation-example.json` and replace function names with your environment:

```bash
# Replace 'test' with your environment name (dev, staging, prod)
sed -i 's/-test/-dev/g' lambda-invocation-example.json
```

Or manually update each `FunctionName` parameter:
- `aws-drs-orchestration-query-handler-{environment}`
- `aws-drs-orchestration-execution-handler-{environment}`
- `aws-drs-orchestration-data-management-handler-{environment}`

### Step 2: Create IAM Role for State Machine

Create an IAM role that allows Step Functions to invoke Lambda functions:

```bash
# Create trust policy
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "states.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
  --role-name DROrchestrationStepFunctionsRole \
  --assume-role-policy-document file://trust-policy.json

# Attach Lambda invocation policy
cat > lambda-invoke-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:*:*:function:aws-drs-orchestration-*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name DROrchestrationStepFunctionsRole \
  --policy-name LambdaInvokePolicy \
  --policy-document file://lambda-invoke-policy.json
```


### Step 3: Create State Machine

```bash
# Get the IAM role ARN
ROLE_ARN=$(aws iam get-role \
  --role-name DROrchestrationStepFunctionsRole \
  --query 'Role.Arn' \
  --output text)

# Create state machine
aws stepfunctions create-state-machine \
  --name aws-drs-orchestration-lambda-invocation-example \
  --definition file://lambda-invocation-example.json \
  --role-arn $ROLE_ARN \
  --type STANDARD \
  --logging-configuration level=ALL,includeExecutionData=true,destinations=[{cloudWatchLogsLogGroup={logGroupArn=arn:aws:logs:us-east-1:ACCOUNT_ID:log-group:/aws/vendedlogs/states/dr-orchestration}}] \
  --tracing-configuration enabled=true

# Save the state machine ARN
STATE_MACHINE_ARN=$(aws stepfunctions list-state-machines \
  --query "stateMachines[?name=='aws-drs-orchestration-lambda-invocation-example'].stateMachineArn" \
  --output text)

echo "State Machine ARN: $STATE_MACHINE_ARN"
```

### Step 4: Grant Lambda Functions Permission

Ensure Lambda functions have resource-based policies allowing Step Functions invocation:

```bash
# Query Handler
aws lambda add-permission \
  --function-name aws-drs-orchestration-query-handler-test \
  --statement-id AllowStepFunctionsInvoke \
  --action lambda:InvokeFunction \
  --principal states.amazonaws.com \
  --source-arn $STATE_MACHINE_ARN

# Execution Handler
aws lambda add-permission \
  --function-name aws-drs-orchestration-execution-handler-test \
  --statement-id AllowStepFunctionsInvoke \
  --action lambda:InvokeFunction \
  --principal states.amazonaws.com \
  --source-arn $STATE_MACHINE_ARN

# Data Management Handler
aws lambda add-permission \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --statement-id AllowStepFunctionsInvoke \
  --action lambda:InvokeFunction \
  --principal states.amazonaws.com \
  --source-arn $STATE_MACHINE_ARN
```


## Testing Procedures

### Test 1: Start State Machine Execution

```bash
# Create test input
cat > test-input.json << 'EOF'
{
  "executionId": "exec-test-001",
  "planId": "plan-test-123",
  "executionType": "DRILL"
}
EOF

# Start execution
EXECUTION_ARN=$(aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --name test-execution-$(date +%s) \
  --input file://test-input.json \
  --query 'executionArn' \
  --output text)

echo "Execution ARN: $EXECUTION_ARN"
```

### Test 2: Monitor Execution Progress

```bash
# Check execution status
aws stepfunctions describe-execution \
  --execution-arn $EXECUTION_ARN \
  --query '{Status:status,StartDate:startDate,StopDate:stopDate}' \
  --output table

# Get execution history
aws stepfunctions get-execution-history \
  --execution-arn $EXECUTION_ARN \
  --max-results 50 \
  --query 'events[*].{Timestamp:timestamp,Type:type,State:stateEnteredEventDetails.name}' \
  --output table
```

### Test 3: View CloudWatch Logs

```bash
# Get log group name
LOG_GROUP="/aws/vendedlogs/states/dr-orchestration"

# View recent logs
aws logs tail $LOG_GROUP --follow --format short
```

### Test 4: Test Individual Lambda Invocations

Test each Lambda handler independently before running the full state machine:

```bash
# Test Query Handler
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json && cat response.json | jq .

# Test Execution Handler
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-test \
  --payload '{"operation":"get_recovery_instances","executionId":"exec-test-001"}' \
  response.json && cat response.json | jq .

# Test Data Management Handler
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation":"initialize_execution","executionId":"exec-test-001","planId":"plan-test-123","executionType":"DRILL"}' \
  response.json && cat response.json | jq .
```


## Integration with CDK Stack

The CDK stack in `examples/cdk/lib/dr-orchestration-stack.ts` already includes a Step Functions state machine. You can integrate this example in two ways:

### Option 1: Replace Existing State Machine Definition

Update the CDK stack to use this state machine definition:

```typescript
// In dr-orchestration-stack.ts
import * as fs from 'fs';
import * as path from 'path';

// Read state machine definition from JSON file
const stateMachineDefinitionJson = fs.readFileSync(
  path.join(__dirname, '../../stepfunctions/lambda-invocation-example.json'),
  'utf-8'
);

// Create state machine with imported definition
const stateMachine = new sfn.StateMachine(this, 'StateMachine', {
  stateMachineName: `${props.projectName}-orchestration-${props.environment}`,
  definitionBody: sfn.DefinitionBody.fromString(stateMachineDefinitionJson),
  role: this.orchestrationRole,
  logs: {
    destination: logGroup,
    level: sfn.LogLevel.ALL,
  },
  tracingEnabled: true,
});
```

### Option 2: Import Existing State Machine

If you've already deployed the state machine using AWS CLI, import it into CDK:

```typescript
// Import existing state machine by name
const stateMachine = sfn.StateMachine.fromStateMachineName(
  this,
  'ImportedStateMachine',
  'aws-drs-orchestration-lambda-invocation-example'
);

// Grant Lambda functions permission to be invoked by state machine
this.queryHandler.grantInvoke(
  new iam.ServicePrincipal('states.amazonaws.com')
);
this.executionHandler.grantInvoke(
  new iam.ServicePrincipal('states.amazonaws.com')
);
this.dataManagementHandler.grantInvoke(
  new iam.ServicePrincipal('states.amazonaws.com')
);
```

### Option 3: Use CDK to Define State Machine

Convert the JSON definition to CDK constructs for better type safety:

```typescript
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';

// Initialize execution
const initExecution = new tasks.LambdaInvoke(this, 'InitializeExecution', {
  lambdaFunction: this.dataManagementHandler,
  payload: sfn.TaskInput.fromObject({
    operation: 'initialize_execution',
    'executionId.$': '$.executionId',
    'planId.$': '$.planId',
    'executionType.$': '$.executionType',
  }),
  resultPath: '$.initResult',
});

// Get recovery plan
const getRecoveryPlan = new tasks.LambdaInvoke(this, 'GetRecoveryPlan', {
  lambdaFunction: this.queryHandler,
  payload: sfn.TaskInput.fromObject({
    operation: 'get_recovery_plan',
    'planId.$': '$.planId',
  }),
  resultPath: '$.planDetails',
});

// Define workflow
const definition = initExecution
  .next(getRecoveryPlan)
  .next(/* ... additional states ... */);

// Create state machine
const stateMachine = new sfn.StateMachine(this, 'StateMachine', {
  stateMachineName: `${props.projectName}-orchestration-${props.environment}`,
  definition,
  role: this.orchestrationRole,
});
```


## Troubleshooting

### Issue 1: Lambda Function Not Found

**Error:**
```
Lambda.ResourceNotFoundException: Function not found
```

**Solution:**
1. Verify Lambda function exists:
   ```bash
   aws lambda get-function --function-name aws-drs-orchestration-query-handler-test
   ```

2. Check function name matches environment:
   ```bash
   aws lambda list-functions --query "Functions[?contains(FunctionName, 'drs-orchestration')].FunctionName"
   ```

3. Update state machine definition with correct function names

### Issue 2: Access Denied

**Error:**
```
Lambda.AccessDeniedException: User is not authorized to perform: lambda:InvokeFunction
```

**Solution:**
1. Verify Step Functions role has Lambda invoke permissions:
   ```bash
   aws iam get-role-policy \
     --role-name DROrchestrationStepFunctionsRole \
     --policy-name LambdaInvokePolicy
   ```

2. Add Lambda resource-based policy:
   ```bash
   aws lambda add-permission \
     --function-name aws-drs-orchestration-query-handler-test \
     --statement-id AllowStepFunctionsInvoke \
     --action lambda:InvokeFunction \
     --principal states.amazonaws.com
   ```

### Issue 3: Invalid Operation

**Error:**
```
{
  "error": "INVALID_OPERATION",
  "message": "Operation 'xyz' is not supported"
}
```

**Solution:**
1. Check operation name spelling in state machine definition
2. Verify operation is supported by the Lambda handler
3. Review design document for correct operation names:
   - Query Handler: `list_protection_groups`, `get_recovery_plan`, etc.
   - Execution Handler: `start_execution`, `cancel_execution`, etc.
   - Data Management Handler: `create_protection_group`, `update_recovery_plan`, etc.

### Issue 4: State Machine Execution Timeout

**Error:**
```
States.Timeout: State machine execution timed out
```

**Solution:**
1. Increase state machine timeout:
   ```bash
   aws stepfunctions update-state-machine \
     --state-machine-arn $STATE_MACHINE_ARN \
     --definition file://lambda-invocation-example.json \
     --timeout-seconds 7200
   ```

2. Optimize wait times in state machine (reduce from 30s if appropriate)

3. Check Lambda function timeout settings:
   ```bash
   aws lambda get-function-configuration \
     --function-name aws-drs-orchestration-execution-handler-test \
     --query 'Timeout'
   ```


### Issue 5: Wave Processing Fails

**Error:**
```
WaveRecoveryFailed: Wave recovery failed - check logs for details
```

**Solution:**
1. Check execution history for specific wave that failed:
   ```bash
   aws stepfunctions get-execution-history \
     --execution-arn $EXECUTION_ARN \
     --query 'events[?type==`TaskFailed`]'
   ```

2. Review Lambda function logs:
   ```bash
   aws logs tail /aws/lambda/aws-drs-orchestration-execution-handler-test --follow
   ```

3. Verify DRS source servers are in correct state:
   ```bash
   aws lambda invoke \
     --function-name aws-drs-orchestration-query-handler-test \
     --payload '{"operation":"get_drs_source_servers"}' \
     response.json && cat response.json | jq .
   ```

### Issue 6: Missing Required Parameters

**Error:**
```
{
  "error": "MISSING_PARAMETER",
  "message": "executionId is required"
}
```

**Solution:**
1. Verify input event contains all required parameters
2. Check JSONPath expressions in state machine (e.g., `"executionId.$": "$.executionId"`)
3. Review state output to ensure data is passed correctly between states

### Issue 7: DynamoDB Table Not Found

**Error:**
```
{
  "error": "DYNAMODB_ERROR",
  "message": "Requested resource not found"
}
```

**Solution:**
1. Verify DynamoDB tables exist:
   ```bash
   aws dynamodb list-tables --query "TableNames[?contains(@, 'drs-orchestration')]"
   ```

2. Check Lambda environment variables:
   ```bash
   aws lambda get-function-configuration \
     --function-name aws-drs-orchestration-query-handler-test \
     --query 'Environment.Variables'
   ```

3. Ensure Lambda execution role has DynamoDB permissions:
   ```bash
   aws iam get-role-policy \
     --role-name aws-drs-orchestration-orchestration-role-test \
     --policy-name DynamoDBPolicy
   ```


## Advanced Patterns

### Pattern 1: Parallel Wave Processing

Modify the Map state to process waves in parallel:

```json
{
  "Type": "Map",
  "ItemsPath": "$.planDetails.plan.waves",
  "MaxConcurrency": 3,
  "ResultPath": "$.waveResults",
  "Iterator": {
    "StartAt": "StartWaveRecovery",
    "States": { /* ... */ }
  }
}
```

**Note:** Use with caution - parallel wave processing may violate recovery plan dependencies.

### Pattern 2: Dynamic Wait Time

Use calculated wait times based on wave size:

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke",
  "Parameters": {
    "FunctionName": "aws-drs-orchestration-query-handler-test",
    "Payload": {
      "operation": "calculate_wait_time",
      "serverCount.$": "$.currentWave.serverCount"
    }
  },
  "ResultPath": "$.waitTime",
  "Next": "DynamicWait"
},
{
  "Type": "Wait",
  "SecondsPath": "$.waitTime.seconds",
  "Next": "CheckWaveStatus"
}
```

### Pattern 3: Conditional Error Handling

Handle different error types with different strategies:

```json
"Catch": [
  {
    "ErrorEquals": ["Lambda.TooManyRequestsException"],
    "ResultPath": "$.error",
    "Next": "WaitAndRetry"
  },
  {
    "ErrorEquals": ["Lambda.ServiceException"],
    "ResultPath": "$.error",
    "Next": "LogErrorAndContinue"
  },
  {
    "ErrorEquals": ["States.ALL"],
    "ResultPath": "$.error",
    "Next": "ExecutionFailed"
  }
]
```

### Pattern 4: Notification Integration

Add SNS notifications for execution milestones:

```json
{
  "Type": "Task",
  "Resource": "arn:aws:states:::sns:publish",
  "Parameters": {
    "TopicArn": "arn:aws:sns:us-east-1:ACCOUNT_ID:dr-orchestration-notifications",
    "Message.$": "$.executionResult",
    "Subject": "DR Execution Completed"
  },
  "Next": "ExecutionSuccess"
}
```


## Best Practices

### 1. Use ResultPath Wisely

Preserve original input while adding results:

```json
"ResultPath": "$.planDetails"  // Adds planDetails to existing state
"ResultPath": null              // Discards result, keeps original state
"ResultPath": "$"               // Replaces entire state with result
```

### 2. Implement Idempotency

Ensure operations can be safely retried:

```json
{
  "operation": "initialize_execution",
  "executionId": "exec-unique-id",  // Use unique, deterministic IDs
  "idempotencyToken": "token-123"   // Include idempotency tokens
}
```

### 3. Use Descriptive State Names

Make state machine flow easy to understand:

```json
"InitializeExecution"      // Clear what this state does
"GetRecoveryPlan"          // Describes the action
"WaitForWaveCompletion"    // Explains the wait purpose
```

### 4. Add Comments

Document complex logic in state definitions:

```json
{
  "Type": "Choice",
  "Comment": "Check if wave recovery is complete. COMPLETED continues to next wave, FAILED terminates execution, IN_PROGRESS loops back to wait state.",
  "Choices": [ /* ... */ ]
}
```

### 5. Monitor Execution Metrics

Set up CloudWatch alarms for:
- Execution failures
- Execution duration exceeding threshold
- Lambda invocation errors
- State transition failures

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name dr-orchestration-execution-failures \
  --alarm-description "Alert on Step Functions execution failures" \
  --metric-name ExecutionsFailed \
  --namespace AWS/States \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=StateMachineArn,Value=$STATE_MACHINE_ARN
```

### 6. Use Tags for Organization

Tag state machines for cost allocation and organization:

```bash
aws stepfunctions tag-resource \
  --resource-arn $STATE_MACHINE_ARN \
  --tags Key=Environment,Value=test Key=Project,Value=DROrchestration Key=CostCenter,Value=Infrastructure
```


## Related Documentation

- **Design Document**: `.kiro/specs/direct-lambda-invocation-mode/design.md` - Complete event formats and integration patterns
- **API Reference**: `.kiro/specs/direct-lambda-invocation-mode/api-reference.md` - All operations with request/response formats
- **CDK Stack**: `examples/cdk/lib/dr-orchestration-stack.ts` - Infrastructure as code implementation
- **CDK Step Functions Integration**: `examples/cdk/docs/STEPFUNCTIONS_INTEGRATION.md` - Detailed CDK integration patterns
- **AWS Step Functions Documentation**: https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html

## Example Execution Input

```json
{
  "executionId": "exec-20250201-100000",
  "planId": "plan-production-dr",
  "executionType": "DRILL",
  "dryRun": false,
  "notificationEmail": "ops-team@example.com"
}
```

## Example Execution Output

```json
{
  "executionId": "exec-20250201-100000",
  "planId": "plan-production-dr",
  "executionType": "DRILL",
  "status": "COMPLETED",
  "startTime": "2025-02-01T10:00:00Z",
  "completionTime": "2025-02-01T10:45:23Z",
  "waveResults": [
    {
      "waveNumber": 1,
      "status": "SUCCESS",
      "completedServers": 5,
      "failedServers": 0
    },
    {
      "waveNumber": 2,
      "status": "SUCCESS",
      "completedServers": 10,
      "failedServers": 0
    }
  ],
  "recoveryInstances": {
    "instances": [
      {
        "instanceId": "i-1234567890abcdef0",
        "sourceServerId": "s-1234567890abcdef0",
        "state": "RUNNING"
      }
    ],
    "count": 15
  }
}
```

## Security Considerations

1. **IAM Permissions**: State machine role should follow least privilege principle
2. **Resource-Based Policies**: Lambda functions should only allow invocation from trusted principals
3. **Encryption**: Enable encryption at rest for state machine execution history
4. **Audit Logging**: Enable CloudWatch Logs for all state machine executions
5. **Network Isolation**: Deploy Lambda functions in VPC if accessing private resources

## Cost Optimization

- **State Transitions**: Minimize unnecessary state transitions (each transition is billed)
- **Wait States**: Use Wait states instead of polling Lambda functions repeatedly
- **Map State Concurrency**: Balance parallelism with cost (more concurrent executions = higher cost)
- **Execution Duration**: Optimize Lambda function performance to reduce execution time
- **Log Retention**: Set appropriate CloudWatch Logs retention period (7-30 days recommended)

## Support

For issues or questions:
1. Check CloudWatch Logs for detailed error messages
2. Review execution history in Step Functions console
3. Test Lambda functions independently before debugging state machine
4. Consult AWS Step Functions documentation for service-specific issues
