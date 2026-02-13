# Step Functions Integration Guide for CDK

## Overview

This guide explains how to integrate the AWS CDK DR Orchestration stack with **existing Step Functions state machines** from a previous deployment. This is useful when:

- Migrating from CloudFormation to CDK while preserving state machine definitions
- Sharing state machines across multiple stacks
- Recreating infrastructure without redefining complex workflows
- Implementing blue/green deployment strategies for orchestration logic

## Table of Contents

1. [Why Import Existing State Machines?](#why-import-existing-state-machines)
2. [Use Cases](#use-cases)
3. [CDK Import Patterns](#cdk-import-patterns)
4. [Migration Strategy](#migration-strategy)
5. [Code Examples](#code-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Why Import Existing State Machines?

### Benefits of Importing State Machines

**Workflow Preservation:**
- Keep proven orchestration logic during infrastructure changes
- Avoid rewriting complex state machine definitions
- Maintain execution history and CloudWatch Logs integration

**Operational Continuity:**
- Zero downtime during stack transitions
- No interruption to running executions
- Preserve execution ARN patterns for monitoring

**Cost Optimization:**
- Reuse existing state machine configurations
- Avoid duplicate state transition charges
- Share state machines across environments

**Flexibility:**
- Decouple orchestration logic from compute resources
- Enable independent state machine lifecycle management
- Support multi-stack architectures


## Use Cases

### 1. CloudFormation to CDK Migration

**Scenario:** You have an existing CloudFormation deployment with Step Functions state machines orchestrating DR operations. You want to migrate to CDK without losing the proven workflow definitions.

**Solution:** Import existing state machines into CDK stack, update Lambda function references, then delete old CloudFormation stack.

**Timeline:** 1-2 hours with zero downtime

### 2. Multi-Stack Architecture

**Scenario:** You want to deploy multiple DR orchestration stacks (dev, test, staging) that share the same Step Functions orchestration logic for consistency.

**Solution:** Create a separate "orchestration stack" with Step Functions state machines, then import those state machines into multiple "compute stacks" with Lambda functions.

**Benefits:** Centralized workflow logic, independent compute deployments, consistent DR procedures

### 3. Stack Recreation

**Scenario:** Your CDK stack is in a failed state and needs to be deleted and recreated, but you cannot lose the state machine definitions and execution history.

**Solution:** Set `removalPolicy: RETAIN` on state machines before deletion, then import the retained state machines into the new stack.

**Recovery Time:** 10-15 minutes

### 4. Blue/Green Deployment

**Scenario:** You want to deploy a new version of your DR orchestration platform alongside the existing version for testing, using the same orchestration workflows.

**Solution:** Deploy "green" stack that imports state machines from "blue" stack, test thoroughly with new Lambda functions, then switch traffic and delete "blue" stack.

**Risk Mitigation:** Full rollback capability, zero workflow logic changes

### 5. Workflow Versioning

**Scenario:** You need to maintain multiple versions of orchestration workflows for different DR scenarios while sharing the same Lambda functions.

**Solution:** Create versioned state machines (v1, v2, v3) and import specific versions into different execution contexts.

**Benefits:** A/B testing of workflows, gradual rollout of changes, version-specific rollback



## CDK Import Patterns

### Pattern 1: Import by State Machine Name

The simplest pattern for importing existing state machines:

```typescript
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';

// Import existing state machine by name
const drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineName(
  this,
  'DROrchestrationStateMachine',
  'hrp-drs-tech-adapter-state-machine-test'
);

// Use imported state machine
drOrchestrationStateMachine.grantStartExecution(executionHandlerRole);
```

**When to use:**
- Same AWS account
- Same AWS region
- State machine name is known

**Limitations:**
- Cannot modify state machine definition
- Cannot change IAM role
- Cannot update logging configuration
- Cannot change removal policy

### Pattern 2: Import by State Machine ARN

For cross-account or cross-region scenarios:

```typescript
// Import state machine by ARN
const drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineArn(
  this,
  'DROrchestrationStateMachine',
  'arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test'
);

// Use imported state machine
drOrchestrationStateMachine.grantStartExecution(executionHandlerRole);
drOrchestrationStateMachine.grantRead(monitoringRole);
```

**When to use:**
- Cross-account access
- Cross-region access
- Full ARN is available

**Benefits:**
- Works across account boundaries
- Explicit resource identification
- Supports cross-region orchestration

### Pattern 3: Import with Full Attributes

For state machines requiring detailed configuration access:

```typescript
// Import state machine with full attributes
const drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineAttributes(
  this,
  'DROrchestrationStateMachine',
  {
    stateMachineArn: 'arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test',
    stateMachineName: 'hrp-drs-tech-adapter-state-machine-test',
    stateMachineType: sfn.StateMachineType.STANDARD,
  }
);

// Grant permissions
drOrchestrationStateMachine.grantStartExecution(executionHandlerRole);
drOrchestrationStateMachine.grantExecution(lambdaRole, 'states:DescribeExecution');
```

**When to use:**
- Need to specify state machine type (STANDARD vs EXPRESS)
- Require fine-grained permission management
- Working with state machine metrics and alarms

**Benefits:**
- Full permission management
- Type-aware IAM policies
- CloudWatch metrics integration

### Pattern 4: Conditional Import vs Create

Support both new deployments and imports:

```typescript
interface DROrchestrationStackProps extends cdk.StackProps {
  // ... existing props ...
  importExistingStateMachine?: boolean;
  existingStateMachineArn?: string;
}

// In stack constructor
if (props.importExistingStateMachine && props.existingStateMachineArn) {
  // Import existing state machine
  this.drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineArn(
    this,
    'DROrchestrationStateMachine',
    props.existingStateMachineArn
  );
} else {
  // Create new state machine
  this.drOrchestrationStateMachine = new sfn.StateMachine(
    this,
    'DROrchestrationStateMachine',
    {
      stateMachineName: `${props.projectName}-state-machine-${props.environment}`,
      definition: this.createStateMachineDefinition(),
      role: orchestrationRole,
      logs: {
        destination: logGroup,
        level: sfn.LogLevel.ALL,
      },
      tracingEnabled: true,
    }
  );
}
```

**When to use:**
- Supporting both greenfield and migration scenarios
- Gradual migration approach
- Testing with different configurations



## Migration Strategy

### Step-by-Step Migration from CloudFormation to CDK

#### Phase 1: Preparation (15 minutes)

**1. Identify Existing State Machines**

```bash
# List all Step Functions state machines in your stack
aws cloudformation describe-stack-resources \
  --stack-name hrp-drs-tech-adapter-test \
  --query 'StackResources[?ResourceType==`AWS::StepFunctions::StateMachine`].[LogicalResourceId,PhysicalResourceId]' \
  --output table

# Example output:
# DROrchestrationStateMachine    hrp-drs-tech-adapter-state-machine-test
```

**2. Document State Machine Configuration**

```bash
# Get state machine details
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --query '{Name:name,ARN:stateMachineArn,Type:type,Status:status,RoleArn:roleArn}' \
  --output json

# Get state machine definition
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --query 'definition' \
  --output text > state-machine-definition.json

# Save state machine ARN for CDK import
export STATE_MACHINE_ARN="arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test"
```

**3. Analyze State Machine Dependencies**

```bash
# List Lambda functions invoked by state machine
cat state-machine-definition.json | jq -r '.. | .Resource? | select(. != null) | select(contains("lambda"))'

# Example output:
# arn:aws:lambda:us-east-1:891376951562:function:hrp-drs-tech-adapter-dr-orchestration-lambda-test
# arn:aws:lambda:us-east-1:891376951562:function:hrp-drs-tech-adapter-execution-handler-test

# List DynamoDB tables accessed
cat state-machine-definition.json | jq -r '.. | .Parameters? | select(. != null) | .TableName? | select(. != null)'
```

**4. Backup State Machine Definition**

```bash
# Create backup of state machine definition
aws stepfunctions describe-state-machine \
  --state-machine-arn $STATE_MACHINE_ARN \
  --query 'definition' \
  --output text > backups/state-machine-definition-$(date +%Y%m%d-%H%M%S).json

# Document execution history (last 100 executions)
aws stepfunctions list-executions \
  --state-machine-arn $STATE_MACHINE_ARN \
  --max-results 100 \
  --query 'executions[*].{Name:name,Status:status,StartDate:startDate,StopDate:stopDate}' \
  --output json > backups/execution-history-$(date +%Y%m%d-%H%M%S).json
```

#### Phase 2: Update CloudFormation Stack (10 minutes)

**1. Set Removal Policy to RETAIN**

Before deleting the CloudFormation stack, update state machine removal policy to prevent deletion:

```bash
# Update CloudFormation template to set DeletionPolicy: Retain
# Edit cfn/step-functions-stack.yaml:

Resources:
  DROrchestrationStateMachine:
    Type: AWS::StepFunctions::StateMachine
    DeletionPolicy: Retain  # Add this line
    UpdateReplacePolicy: Retain  # Add this line
    Properties:
      # ... existing properties ...
```

**2. Deploy Updated CloudFormation Stack**

```bash
# Deploy with RETAIN policy
aws cloudformation update-stack \
  --stack-name hrp-drs-tech-adapter-test \
  --template-body file://cfn/master-template.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for update to complete
aws cloudformation wait stack-update-complete \
  --stack-name hrp-drs-tech-adapter-test
```

**3. Verify RETAIN Policy**

```bash
# Verify DeletionPolicy is set
aws cloudformation describe-stack-resources \
  --stack-name hrp-drs-tech-adapter-test \
  --query 'StackResources[?ResourceType==`AWS::StepFunctions::StateMachine`].[LogicalResourceId,PhysicalResourceId]'
```

#### Phase 3: Deploy CDK Stack with Imported State Machine (20 minutes)

**1. Create CDK Stack with Import Configuration**

Create a new file `examples/cdk/lib/dr-orchestration-import-stack.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { Construct } from 'constructs';
import { DROrchestrationStack, DROrchestrationStackProps } from './dr-orchestration-stack';

/**
 * Extended stack that imports existing Step Functions state machine
 */
export class DROrchestrationImportStack extends DROrchestrationStack {
  constructor(scope: Construct, id: string, props: DROrchestrationStackProps & {
    existingStateMachineArn: string;
  }) {
    super(scope, id, props);
    
    // Import existing state machine instead of creating new one
    const importedStateMachine = sfn.StateMachine.fromStateMachineArn(
      this,
      'ImportedStateMachine',
      props.existingStateMachineArn
    );
    
    // Override the state machine property
    this.drOrchestrationStateMachine = importedStateMachine;
    
    // Grant Lambda functions permission to start executions
    importedStateMachine.grantStartExecution(this.executionHandler);
    importedStateMachine.grantRead(this.queryHandler);
  }
}
```

**2. Update CDK App Configuration**

Edit `examples/cdk/bin/dr-orchestration.ts`:

```typescript
#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { DROrchestrationImportStack } from '../lib/dr-orchestration-import-stack';

const app = new cdk.App();

const environment = process.env.ENVIRONMENT || 'test';
const projectName = process.env.PROJECT_NAME || 'hrp-drs-tech-adapter';
const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com';

// Import existing state machine from CloudFormation deployment
const importExistingStateMachine = process.env.IMPORT_EXISTING_STATE_MACHINE === 'true';
const existingStateMachineArn = process.env.EXISTING_STATE_MACHINE_ARN;

if (importExistingStateMachine && existingStateMachineArn) {
  new DROrchestrationImportStack(app, `${projectName}-${environment}`, {
    projectName,
    environment,
    adminEmail,
    existingStateMachineArn,
    env: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
    },
  });
} else {
  // Use standard stack that creates new state machine
  new DROrchestrationStack(app, `${projectName}-${environment}`, {
    projectName,
    environment,
    adminEmail,
    env: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
    },
  });
}
```

**3. Deploy CDK Stack**

```bash
# Set environment variables
export ENVIRONMENT=test
export PROJECT_NAME=hrp-drs-tech-adapter
export ADMIN_EMAIL=admin@example.com
export IMPORT_EXISTING_STATE_MACHINE=true
export EXISTING_STATE_MACHINE_ARN="arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test"

# Build and deploy
cd examples/cdk
npm install
npm run build
cdk deploy --require-approval never
```

**4. Verify CDK Stack**

```bash
# Check CDK stack status
aws cloudformation describe-stacks \
  --stack-name hrp-drs-tech-adapter-test \
  --query 'Stacks[0].StackStatus'

# Verify Lambda functions can start executions
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-execution-handler-test \
  --payload '{"operation":"start_execution","planId":"plan-test-123","executionType":"DRILL"}' \
  response.json

cat response.json | jq .
```

#### Phase 4: Delete Old CloudFormation Stack (10 minutes)

**1. Verify CDK Stack is Working**

```bash
# Test state machine execution
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --name test-execution-$(date +%s) \
  --input '{"planId":"plan-test-123","executionType":"DRILL","waves":[{"waveNumber":1,"servers":["s-1234567890abcdef0"]}]}'

# Check execution status
aws stepfunctions describe-execution \
  --execution-arn <execution-arn-from-above>

# Verify data is accessible
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-query-handler-test \
  --payload '{"operation":"list_executions"}' \
  response.json

cat response.json | jq .
```

**2. Delete Old CloudFormation Stack**

```bash
# Delete CloudFormation stack (state machine will be retained)
aws cloudformation delete-stack \
  --stack-name hrp-drs-tech-adapter-test-old

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete \
  --stack-name hrp-drs-tech-adapter-test-old
```

**3. Verify State Machine Still Exists**

```bash
# Verify state machine was not deleted
aws stepfunctions describe-state-machine \
  --state-machine-arn $STATE_MACHINE_ARN \
  --query '{Name:name,Status:status}'

# Should show state machine is still ACTIVE
```

#### Phase 5: Rollback Procedure (If Needed)

If something goes wrong during migration:

**1. Immediate Rollback**

```bash
# Delete CDK stack
cdk destroy --force

# Redeploy original CloudFormation stack
aws cloudformation create-stack \
  --stack-name hrp-drs-tech-adapter-test \
  --template-body file://cfn/master-template.yaml \
  --parameters file://cfn/parameters-test.json \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for stack creation
aws cloudformation wait stack-create-complete \
  --stack-name hrp-drs-tech-adapter-test
```

**2. Verify Rollback**

```bash
# Test state machine execution
aws stepfunctions start-execution \
  --state-machine-arn $STATE_MACHINE_ARN \
  --name rollback-test-$(date +%s) \
  --input '{"planId":"plan-test-123","executionType":"DRILL"}'

# Verify execution completes successfully
aws stepfunctions describe-execution \
  --execution-arn <execution-arn-from-above>
```

**3. Document Rollback Reason**

Create incident report documenting:
- What went wrong
- When rollback was initiated
- State machine integrity verification results
- Lessons learned for next attempt



## Code Examples

### Example 1: Simple State Machine Import

```typescript
import * as cdk from 'aws-cdk-lib';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class SimpleImportStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import existing state machine by name
    const drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineName(
      this,
      'DROrchestrationStateMachine',
      'hrp-drs-tech-adapter-state-machine-test'
    );
    
    // Create Lambda function that starts executions
    const executionHandler = new lambda.Function(this, 'ExecutionHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/execution-handler'),
      handler: 'index.lambda_handler',
      environment: {
        STATE_MACHINE_ARN: drOrchestrationStateMachine.stateMachineArn,
      },
    });
    
    // Grant Lambda permission to start executions
    drOrchestrationStateMachine.grantStartExecution(executionHandler);
    drOrchestrationStateMachine.grantRead(executionHandler);
  }
}
```

### Example 2: Import with EventBridge Integration

```typescript
import * as cdk from 'aws-cdk-lib';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import { Construct } from 'constructs';

export class ImportWithEventBridgeStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import existing state machine
    const drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineArn(
      this,
      'DROrchestrationStateMachine',
      'arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test'
    );
    
    // Create EventBridge rule for scheduled executions
    const scheduledRule = new events.Rule(this, 'ScheduledDRDrill', {
      ruleName: 'hrp-drs-tech-adapter-scheduled-drill-test',
      description: 'Trigger DR drill execution every Sunday at 2 AM UTC',
      schedule: events.Schedule.cron({
        minute: '0',
        hour: '2',
        weekDay: 'SUN',
      }),
    });
    
    // Add state machine as target
    scheduledRule.addTarget(
      new targets.SfnStateMachine(drOrchestrationStateMachine, {
        input: events.RuleTargetInput.fromObject({
          planId: 'plan-weekly-drill',
          executionType: 'DRILL',
          dryRun: false,
        }),
      })
    );
  }
}
```

### Example 3: Cross-Account State Machine Import

```typescript
import * as cdk from 'aws-cdk-lib';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class CrossAccountImportStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import state machine from different account by ARN
    const drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineArn(
      this,
      'DROrchestrationStateMachine',
      'arn:aws:states:us-east-1:123456789012:stateMachine:hrp-drs-tech-adapter-state-machine-prod'
    );
    
    // Create Lambda execution role with cross-account permissions
    const lambdaRole = new iam.Role(this, 'LambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    
    // Add cross-account Step Functions permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'states:StartExecution',
        'states:DescribeExecution',
        'states:StopExecution',
        'states:ListExecutions',
      ],
      resources: [
        drOrchestrationStateMachine.stateMachineArn,
        `${drOrchestrationStateMachine.stateMachineArn}:*`, // For execution ARNs
      ],
    }));
    
    // Create Lambda function
    const executionHandler = new lambda.Function(this, 'ExecutionHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/execution-handler'),
      handler: 'index.lambda_handler',
      role: lambdaRole,
      environment: {
        STATE_MACHINE_ARN: drOrchestrationStateMachine.stateMachineArn,
      },
    });
  }
}
```

**Note:** For cross-account access, you also need to update the state machine's resource policy in the source account to allow access from the Lambda execution role.

### Example 4: Conditional Import vs Create

```typescript
import * as cdk from 'aws-cdk-lib';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export interface FlexibleStackProps extends cdk.StackProps {
  projectName: string;
  environment: string;
  importExistingStateMachine?: boolean;
  existingStateMachineArn?: string;
}

export class FlexibleStack extends cdk.Stack {
  public readonly drOrchestrationStateMachine: sfn.IStateMachine;
  
  constructor(scope: Construct, id: string, props: FlexibleStackProps) {
    super(scope, id, props);
    
    // Create Lambda function for DR operations
    const drOrchestrationLambda = new lambda.Function(this, 'DROrchestrationLambda', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/dr-orchestration-lambda'),
      handler: 'index.lambda_handler',
      timeout: cdk.Duration.minutes(15),
    });
    
    // State Machine: Import or Create
    if (props.importExistingStateMachine && props.existingStateMachineArn) {
      // Import existing state machine
      this.drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineArn(
        this,
        'DROrchestrationStateMachine',
        props.existingStateMachineArn
      );
    } else {
      // Create new state machine with wave-based orchestration
      const definition = this.createStateMachineDefinition(drOrchestrationLambda);
      
      // Create CloudWatch Logs group for state machine
      const logGroup = new logs.LogGroup(this, 'StateMachineLogGroup', {
        logGroupName: `/aws/vendedlogs/states/${props.projectName}-state-machine-${props.environment}`,
        retention: logs.RetentionDays.ONE_MONTH,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
      });
      
      this.drOrchestrationStateMachine = new sfn.StateMachine(
        this,
        'DROrchestrationStateMachine',
        {
          stateMachineName: `${props.projectName}-state-machine-${props.environment}`,
          definition,
          timeout: cdk.Duration.hours(2),
          tracingEnabled: true,
          logs: {
            destination: logGroup,
            level: sfn.LogLevel.ALL,
            includeExecutionData: true,
          },
          removalPolicy: cdk.RemovalPolicy.RETAIN,
        }
      );
    }
    
    // Output state machine ARN
    new cdk.CfnOutput(this, 'StateMachineArn', {
      value: this.drOrchestrationStateMachine.stateMachineArn,
      description: 'DR Orchestration State Machine ARN',
      exportName: `${props.projectName}-state-machine-arn-${props.environment}`,
    });
  }
  
  private createStateMachineDefinition(drLambda: lambda.Function): sfn.IChainable {
    // Initialize execution
    const initExecution = new tasks.LambdaInvoke(this, 'InitializeExecution', {
      lambdaFunction: drLambda,
      payload: sfn.TaskInput.fromObject({
        action: 'initialize_execution',
        'executionId.$': '$.executionId',
        'planId.$': '$.planId',
        'executionType.$': '$.executionType',
      }),
      resultPath: '$.initResult',
    });
    
    // Process each wave
    const processWave = new tasks.LambdaInvoke(this, 'ProcessWave', {
      lambdaFunction: drLambda,
      payload: sfn.TaskInput.fromObject({
        action: 'start_wave_recovery',
        'executionId.$': '$.executionId',
        'wave.$': '$.currentWave',
      }),
      resultPath: '$.waveResult',
    });
    
    // Wait for wave completion
    const waitForWave = new sfn.Wait(this, 'WaitForWaveCompletion', {
      time: sfn.WaitTime.duration(cdk.Duration.seconds(30)),
    });
    
    // Check wave status
    const checkWaveStatus = new tasks.LambdaInvoke(this, 'CheckWaveStatus', {
      lambdaFunction: drLambda,
      payload: sfn.TaskInput.fromObject({
        action: 'check_wave_status',
        'executionId.$': '$.executionId',
        'waveNumber.$': '$.currentWave.waveNumber',
      }),
      resultPath: '$.statusResult',
    });
    
    // Wave completion check
    const isWaveComplete = new sfn.Choice(this, 'IsWaveComplete')
      .when(
        sfn.Condition.stringEquals('$.statusResult.Payload.status', 'COMPLETED'),
        new sfn.Pass(this, 'WaveCompleted')
      )
      .when(
        sfn.Condition.stringEquals('$.statusResult.Payload.status', 'FAILED'),
        new sfn.Fail(this, 'WaveFailed', {
          cause: 'Wave recovery failed',
          error: 'WaveRecoveryError',
        })
      )
      .otherwise(waitForWave);
    
    // Connect wait loop
    waitForWave.next(checkWaveStatus);
    checkWaveStatus.next(isWaveComplete);
    
    // Complete execution
    const completeExecution = new tasks.LambdaInvoke(this, 'CompleteExecution', {
      lambdaFunction: drLambda,
      payload: sfn.TaskInput.fromObject({
        action: 'complete_execution',
        'executionId.$': '$.executionId',
      }),
      resultPath: '$.completeResult',
    });
    
    // Define workflow
    return initExecution
      .next(processWave)
      .next(waitForWave)
      .next(completeExecution);
  }
}
```

**Usage:**

```bash
# Create new state machine
export IMPORT_EXISTING_STATE_MACHINE=false
cdk deploy

# Import existing state machine
export IMPORT_EXISTING_STATE_MACHINE=true
export EXISTING_STATE_MACHINE_ARN="arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test"
cdk deploy
```



### Example 5: Import with Lambda Integration

```typescript
import * as cdk from 'aws-cdk-lib';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class ImportWithLambdaStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import existing state machine
    const drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineName(
      this,
      'DROrchestrationStateMachine',
      'hrp-drs-tech-adapter-state-machine-test'
    );
    
    // Import existing DynamoDB tables
    const executionsTable = dynamodb.Table.fromTableName(
      this,
      'ExecutionsTable',
      'hrp-drs-tech-adapter-executions-test'
    );
    
    // Create Execution Handler Lambda
    const executionHandler = new lambda.Function(this, 'ExecutionHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/execution-handler'),
      handler: 'index.lambda_handler',
      timeout: cdk.Duration.seconds(30),
      environment: {
        STATE_MACHINE_ARN: drOrchestrationStateMachine.stateMachineArn,
        EXECUTIONS_TABLE: executionsTable.tableName,
      },
    });
    
    // Create Query Handler Lambda
    const queryHandler = new lambda.Function(this, 'QueryHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      timeout: cdk.Duration.seconds(30),
      environment: {
        STATE_MACHINE_ARN: drOrchestrationStateMachine.stateMachineArn,
        EXECUTIONS_TABLE: executionsTable.tableName,
      },
    });
    
    // Grant permissions
    drOrchestrationStateMachine.grantStartExecution(executionHandler);
    drOrchestrationStateMachine.grantExecution(executionHandler, 'states:StopExecution');
    drOrchestrationStateMachine.grantRead(queryHandler);
    
    executionsTable.grantReadWriteData(executionHandler);
    executionsTable.grantReadData(queryHandler);
    
    // Add resource-based policy to allow state machine to invoke Lambda
    executionHandler.grantInvoke(
      new cdk.aws_iam.ServicePrincipal('states.amazonaws.com')
    );
  }
}
```

### Example 6: Import with CloudWatch Alarms

```typescript
import * as cdk from 'aws-cdk-lib';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import { Construct } from 'constructs';

export class ImportWithAlarmsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import existing state machine
    const drOrchestrationStateMachine = sfn.StateMachine.fromStateMachineArn(
      this,
      'DROrchestrationStateMachine',
      'arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test'
    );
    
    // Create SNS topic for alarms
    const alarmTopic = new sns.Topic(this, 'AlarmTopic', {
      topicName: 'hrp-drs-tech-adapter-alarms-test',
      displayName: 'DR Orchestration Alarms',
    });
    
    // Alarm for failed executions
    const failedExecutionsAlarm = new cloudwatch.Alarm(this, 'FailedExecutionsAlarm', {
      alarmName: 'hrp-drs-tech-adapter-failed-executions-test',
      alarmDescription: 'Alert when state machine executions fail',
      metric: drOrchestrationStateMachine.metricFailed({
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 1,
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    
    failedExecutionsAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));
    
    // Alarm for execution duration
    const longExecutionAlarm = new cloudwatch.Alarm(this, 'LongExecutionAlarm', {
      alarmName: 'hrp-drs-tech-adapter-long-execution-test',
      alarmDescription: 'Alert when executions take longer than expected',
      metric: drOrchestrationStateMachine.metricTime({
        statistic: 'Average',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 3600000, // 1 hour in milliseconds
      evaluationPeriods: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    
    longExecutionAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));
    
    // Alarm for throttled executions
    const throttledExecutionsAlarm = new cloudwatch.Alarm(this, 'ThrottledExecutionsAlarm', {
      alarmName: 'hrp-drs-tech-adapter-throttled-executions-test',
      alarmDescription: 'Alert when executions are throttled',
      metric: drOrchestrationStateMachine.metricThrottled({
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
      }),
      threshold: 5,
      evaluationPeriods: 2,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    
    throttledExecutionsAlarm.addAlarmAction(new actions.SnsAction(alarmTopic));
  }
}
```



## Best Practices

### 1. When to Import vs Create New State Machines

**Import Existing State Machines When:**
- ✅ Migrating from CloudFormation to CDK
- ✅ Workflow logic preservation is critical
- ✅ Sharing state machines across multiple stacks
- ✅ Recreating failed stacks
- ✅ Blue/green deployments with same orchestration logic
- ✅ Execution history must be maintained

**Create New State Machines When:**
- ✅ Greenfield deployments
- ✅ Isolated test environments
- ✅ Different workflow definitions needed
- ✅ No existing executions to preserve
- ✅ Complete environment isolation required
- ✅ State machine definition needs modification

### 2. State Machine Naming Conventions

**Consistent Naming Pattern:**
```
{project-name}-state-machine-{environment}

Examples:
- hrp-drs-tech-adapter-state-machine-test
- hrp-drs-tech-adapter-state-machine-prod
- hrp-drs-tech-adapter-state-machine-dev
```

**Benefits:**
- Easy identification of state machine ownership
- Clear environment separation
- Predictable import patterns
- Simplified automation

### 3. Backup Strategies Before Migration

**Always Backup State Machine Definitions:**

```bash
# Export state machine definition
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --query 'definition' \
  --output text > backups/state-machine-definition-$(date +%Y%m%d-%H%M%S).json

# Export execution history
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --max-results 1000 \
  --query 'executions[*].{Name:name,Status:status,StartDate:startDate,StopDate:stopDate}' \
  --output json > backups/execution-history-$(date +%Y%m%d-%H%M%S).json

# Export CloudWatch Logs configuration
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --query 'loggingConfiguration' \
  --output json > backups/logging-config-$(date +%Y%m%d-%H%M%S).json
```

**Backup Retention:**
- Keep definition backups for 90 days minimum
- Document state machine ARN for quick reference
- Store backups in version control (Git)
- Include IAM role ARN in backup documentation

### 4. IAM Permission Management

**Principle of Least Privilege:**

```typescript
// Grant only necessary permissions
drOrchestrationStateMachine.grantStartExecution(executionHandlerRole);
drOrchestrationStateMachine.grantRead(queryHandlerRole);

// Explicit permissions for fine-grained control
lambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'states:StartExecution',
    'states:DescribeExecution',
    'states:ListExecutions',
  ],
  resources: [
    drOrchestrationStateMachine.stateMachineArn,
    `${drOrchestrationStateMachine.stateMachineArn}:*`, // For execution ARNs
  ],
}));

// Grant state machine permission to invoke Lambda
drOrchestrationLambda.grantInvoke(
  new iam.ServicePrincipal('states.amazonaws.com')
);
```

**Common Permission Patterns:**

| Role | Required Permissions |
|------|---------------------|
| Execution Handler | `states:StartExecution`, `states:StopExecution`, `states:DescribeExecution` |
| Query Handler | `states:DescribeExecution`, `states:ListExecutions`, `states:GetExecutionHistory` |
| State Machine | `lambda:InvokeFunction`, `dynamodb:PutItem`, `dynamodb:UpdateItem` |
| EventBridge | `states:StartExecution` |

### 5. Testing Import Configuration

**Pre-Deployment Testing:**

```bash
# 1. Synthesize CloudFormation template
cdk synth > template.yaml

# 2. Validate template
aws cloudformation validate-template --template-body file://template.yaml

# 3. Review IAM permissions
grep -A 10 "AWS::IAM::Policy" template.yaml

# 4. Check state machine references
grep -A 5 "StateMachine" template.yaml

# 5. Verify state machine ARN format
grep "arn:aws:states" template.yaml
```

**Post-Deployment Verification:**

```bash
# 1. Verify Lambda can start executions
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-execution-handler-test \
  --payload '{"operation":"start_execution","planId":"plan-test-123","executionType":"DRILL"}' \
  response.json

# 2. Check CloudWatch Logs for errors
aws logs tail /aws/lambda/hrp-drs-tech-adapter-execution-handler-test --since 5m

# 3. Verify execution started
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --max-results 5

# 4. Check execution details
aws stepfunctions describe-execution \
  --execution-arn <execution-arn-from-above>
```

### 6. Handling State Machine Configuration Drift

**Problem:** Imported state machines cannot be modified by CDK (definition, IAM role, logging, etc.)

**Solution 1: Accept Current Configuration**
```typescript
// Import state machine as-is
const stateMachine = sfn.StateMachine.fromStateMachineName(
  this,
  'StateMachine',
  'existing-state-machine'
);
// Cannot modify definition, role, or logging configuration
```

**Solution 2: Migrate to CDK-Managed State Machine**
```typescript
// 1. Export current state machine definition
// 2. Create new CDK-managed state machine with desired configuration
// 3. Update Lambda functions to use new state machine
// 4. Test thoroughly
// 5. Delete old state machine
```

**Solution 3: Use AWS Console/CLI for Configuration Changes**
```bash
# Update state machine configuration outside CDK
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --definition file://updated-definition.json

# CDK will not detect or revert these changes
```

**Solution 4: Version State Machines**
```typescript
// Create new version with updated definition
const stateMachineV2 = new sfn.StateMachine(this, 'StateMachineV2', {
  stateMachineName: 'hrp-drs-tech-adapter-state-machine-v2-test',
  definition: updatedDefinition,
  // ... other properties
});

// Gradually migrate executions to new version
// Keep old version for rollback
```

### 7. Monitoring Imported State Machines

**CloudWatch Metrics:**

```typescript
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';

// Create dashboard for imported state machine
const dashboard = new cloudwatch.Dashboard(this, 'StateMachineDashboard', {
  dashboardName: 'hrp-drs-tech-adapter-state-machine-test',
});

// Add execution metrics
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'Execution Status',
    left: [
      drOrchestrationStateMachine.metricSucceeded({
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
        label: 'Succeeded',
      }),
      drOrchestrationStateMachine.metricFailed({
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
        label: 'Failed',
      }),
      drOrchestrationStateMachine.metricTimedOut({
        statistic: 'Sum',
        period: cdk.Duration.minutes(5),
        label: 'Timed Out',
      }),
    ],
  })
);

// Add duration metrics
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'Execution Duration',
    left: [
      drOrchestrationStateMachine.metricTime({
        statistic: 'Average',
        period: cdk.Duration.minutes(5),
        label: 'Average Duration',
      }),
      drOrchestrationStateMachine.metricTime({
        statistic: 'Maximum',
        period: cdk.Duration.minutes(5),
        label: 'Max Duration',
      }),
    ],
  })
);
```

**Note:** Metrics work the same for imported and created state machines.

### 8. Documentation Requirements

**Document for Each Imported State Machine:**
- Original source (CloudFormation stack, manual creation, etc.)
- State machine ARN and region
- State machine type (STANDARD vs EXPRESS)
- IAM role ARN
- Logging configuration
- Tracing configuration (X-Ray)
- Timeout settings
- Lambda functions invoked
- DynamoDB tables accessed
- Expected execution patterns and frequency

**Example Documentation:**

```markdown
## Imported Step Functions State Machines

### DR Orchestration State Machine
- **Source:** CloudFormation stack `hrp-drs-tech-adapter-test`
- **ARN:** `arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test`
- **Type:** STANDARD
- **IAM Role:** `arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test`
- **Logging:** CloudWatch Logs enabled, ALL level
- **Tracing:** X-Ray enabled
- **Timeout:** 2 hours
- **Lambda Functions:**
  - `hrp-drs-tech-adapter-dr-orchestration-lambda-test`
  - `hrp-drs-tech-adapter-execution-handler-test`
- **DynamoDB Tables:**
  - `hrp-drs-tech-adapter-executions-test`
  - `hrp-drs-tech-adapter-recovery-plans-test`
- **Execution Pattern:** On-demand via Lambda, scheduled via EventBridge (weekly)
- **Average Duration:** 15-30 minutes
- **Typical Executions:** 5-10 per week
```

### 9. State Machine Definition Management

**Version Control Best Practices:**

```bash
# Store state machine definitions in Git
mkdir -p state-machines/definitions

# Export current definition
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --query 'definition' \
  --output text | jq . > state-machines/definitions/dr-orchestration-v1.json

# Commit to version control
git add state-machines/definitions/dr-orchestration-v1.json
git commit -m "docs: add state machine definition v1"
```

**Definition Validation:**

```bash
# Validate JSON syntax
jq empty state-machines/definitions/dr-orchestration-v1.json

# Check for required fields
jq '.States | keys' state-machines/definitions/dr-orchestration-v1.json

# Validate state transitions
jq '.States | to_entries[] | select(.value.Next == null and .value.End != true) | .key' \
  state-machines/definitions/dr-orchestration-v1.json
```

### 10. Execution History Preservation

**Maintaining Execution History During Migration:**

```bash
# Export execution history before migration
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --max-results 1000 \
  --query 'executions[*]' \
  --output json > execution-history-pre-migration.json

# After migration, verify executions are still accessible
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --max-results 10

# Compare execution counts
BEFORE=$(jq 'length' execution-history-pre-migration.json)
AFTER=$(aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --max-results 1000 \
  --query 'executions | length(@)')

echo "Executions before migration: $BEFORE"
echo "Executions after migration: $AFTER"
```

**Note:** Execution history is preserved when importing state machines. The execution ARN format remains the same.



## Troubleshooting

### Common Issues and Solutions

#### Issue 1: State Machine Not Found

**Symptom:**
```
Error: State machine not found: hrp-drs-tech-adapter-state-machine-test
```

**Causes:**
- State machine name is incorrect
- State machine is in different region
- State machine was deleted
- Insufficient IAM permissions to describe state machine

**Solutions:**

```bash
# 1. List all state machines in current region
aws stepfunctions list-state-machines \
  --query 'stateMachines[*].{Name:name,ARN:stateMachineArn}' \
  --output table

# 2. Check if state machine exists in different region
for region in us-east-1 us-west-2 eu-west-1; do
  echo "Checking region: $region"
  aws stepfunctions list-state-machines \
    --region $region \
    --query "stateMachines[?contains(name, 'hrp-drs-tech-adapter')]"
done

# 3. Verify IAM permissions
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test

# 4. Check CloudFormation stack resources
aws cloudformation describe-stack-resources \
  --stack-name hrp-drs-tech-adapter-test \
  --query 'StackResources[?ResourceType==`AWS::StepFunctions::StateMachine`]'
```

#### Issue 2: Permission Denied When Starting Execution

**Symptom:**
```
AccessDeniedException: User: arn:aws:sts::891376951562:assumed-role/lambda-role/function-name 
is not authorized to perform: states:StartExecution on resource: 
arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test
```

**Causes:**
- Lambda execution role lacks `states:StartExecution` permission
- State machine resource policy blocks access
- IAM policy has incorrect resource ARN

**Solutions:**

```typescript
// 1. Grant StartExecution permission
drOrchestrationStateMachine.grantStartExecution(lambdaRole);

// 2. Or add explicit policy
lambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['states:StartExecution'],
  resources: [drOrchestrationStateMachine.stateMachineArn],
}));
```

```bash
# 3. Verify IAM policy
aws iam get-role-policy \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --policy-name StateMachinePolicy

# 4. Test permissions
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --name test-execution-$(date +%s) \
  --input '{}'
```

#### Issue 3: State Machine Definition Cannot Be Modified

**Symptom:**
```
Error: Cannot modify state machine definition for imported state machine
```

**Cause:**
- Imported state machines are immutable in CDK
- CDK cannot update state machine definition

**Solutions:**

**Option 1: Update via AWS CLI**
```bash
# Update state machine definition outside CDK
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --definition file://updated-definition.json
```

**Option 2: Create New Version**
```typescript
// Create new state machine with updated definition
const stateMachineV2 = new sfn.StateMachine(this, 'StateMachineV2', {
  stateMachineName: 'hrp-drs-tech-adapter-state-machine-v2-test',
  definition: updatedDefinition,
  role: orchestrationRole,
});

// Update Lambda to use new version
executionHandler.addEnvironment(
  'STATE_MACHINE_ARN',
  stateMachineV2.stateMachineArn
);
```

**Option 3: Migrate to CDK-Managed**
```bash
# 1. Export current definition
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --query 'definition' \
  --output text > current-definition.json

# 2. Delete import from CDK stack
# 3. Create new CDK-managed state machine with exported definition
# 4. Deploy and test
# 5. Delete old state machine
```

#### Issue 4: Execution History Lost After Migration

**Symptom:**
- Cannot find previous executions after CDK deployment
- Execution ARNs return "Execution does not exist"

**Cause:**
- State machine was recreated instead of imported
- Wrong state machine ARN used

**Solutions:**

```bash
# 1. Verify state machine ARN hasn't changed
aws cloudformation describe-stack-resources \
  --stack-name hrp-drs-tech-adapter-test \
  --query 'StackResources[?ResourceType==`AWS::StepFunctions::StateMachine`].PhysicalResourceId'

# 2. List executions with correct ARN
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --max-results 100

# 3. Check CloudWatch Logs for execution history
aws logs filter-log-events \
  --log-group-name /aws/vendedlogs/states/hrp-drs-tech-adapter-state-machine-test \
  --start-time $(date -d '7 days ago' +%s)000 \
  --filter-pattern "execution_arn"
```

**Prevention:**
- Always use `fromStateMachineArn()` or `fromStateMachineName()` for imports
- Never use `new sfn.StateMachine()` when migrating
- Set `removalPolicy: RETAIN` before any stack operations

#### Issue 5: Lambda Function Cannot Be Invoked by State Machine

**Symptom:**
```
States.TaskFailed: Lambda function failed to execute
AccessDeniedException: User: arn:aws:sts::891376951562:assumed-role/state-machine-role 
is not authorized to perform: lambda:InvokeFunction
```

**Causes:**
- State machine IAM role lacks `lambda:InvokeFunction` permission
- Lambda resource policy doesn't allow state machine invocation

**Solutions:**

```typescript
// 1. Grant state machine permission to invoke Lambda
drOrchestrationLambda.grantInvoke(
  new iam.ServicePrincipal('states.amazonaws.com')
);

// 2. Or add explicit resource policy
drOrchestrationLambda.addPermission('AllowStateMachineInvoke', {
  principal: new iam.ServicePrincipal('states.amazonaws.com'),
  action: 'lambda:InvokeFunction',
  sourceArn: drOrchestrationStateMachine.stateMachineArn,
});
```

```bash
# 3. Verify Lambda resource policy
aws lambda get-policy \
  --function-name hrp-drs-tech-adapter-dr-orchestration-lambda-test

# 4. Verify state machine role permissions
aws iam get-role-policy \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --policy-name LambdaInvokePolicy
```

#### Issue 6: State Machine Execution Timeout

**Symptom:**
```
States.Timeout: State machine execution timed out
```

**Causes:**
- Execution exceeded state machine timeout (default: 1 year for STANDARD)
- Individual state timeout exceeded
- Lambda function timeout too short

**Solutions:**

```typescript
// 1. Increase state machine timeout (for new state machines)
const stateMachine = new sfn.StateMachine(this, 'StateMachine', {
  // ... other properties
  timeout: cdk.Duration.hours(4), // Increase from default
});

// 2. Increase Lambda timeout
const drLambda = new lambda.Function(this, 'DRLambda', {
  // ... other properties
  timeout: cdk.Duration.minutes(15), // Increase from default 3 seconds
});

// 3. Add timeout to individual states
const processWave = new tasks.LambdaInvoke(this, 'ProcessWave', {
  lambdaFunction: drLambda,
  timeout: cdk.Duration.minutes(10),
  // ... other properties
});
```

```bash
# 4. Check execution details for timeout location
aws stepfunctions get-execution-history \
  --execution-arn <execution-arn> \
  --query 'events[?type==`TaskTimedOut` || type==`ExecutionTimedOut`]'

# 5. Monitor execution duration
aws stepfunctions describe-execution \
  --execution-arn <execution-arn> \
  --query '{Status:status,StartDate:startDate,StopDate:stopDate}'
```

#### Issue 7: CloudWatch Logs Not Working

**Symptom:**
- No logs appearing in CloudWatch Logs
- Log group exists but is empty

**Causes:**
- Logging not enabled on state machine
- IAM role lacks CloudWatch Logs permissions
- Log group doesn't exist

**Solutions:**

```typescript
// 1. Enable logging for new state machines
const logGroup = new logs.LogGroup(this, 'StateMachineLogGroup', {
  logGroupName: '/aws/vendedlogs/states/hrp-drs-tech-adapter-state-machine-test',
  retention: logs.RetentionDays.ONE_MONTH,
  removalPolicy: cdk.RemovalPolicy.RETAIN,
});

const stateMachine = new sfn.StateMachine(this, 'StateMachine', {
  // ... other properties
  logs: {
    destination: logGroup,
    level: sfn.LogLevel.ALL,
    includeExecutionData: true,
  },
});
```

```bash
# 2. Update logging configuration for existing state machine
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --logging-configuration '{
    "level": "ALL",
    "includeExecutionData": true,
    "destinations": [{
      "cloudWatchLogsLogGroup": {
        "logGroupArn": "arn:aws:logs:us-east-1:891376951562:log-group:/aws/vendedlogs/states/hrp-drs-tech-adapter-state-machine-test:*"
      }
    }]
  }'

# 3. Verify log group exists
aws logs describe-log-groups \
  --log-group-name-prefix /aws/vendedlogs/states/

# 4. Check IAM permissions
aws iam get-role-policy \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --policy-name CloudWatchLogsPolicy
```

#### Issue 8: Cross-Account Access Denied

**Symptom:**
```
AccessDeniedException: Cross-account access denied
```

**Causes:**
- Source account state machine doesn't allow cross-account access
- Target account role lacks assume role permissions
- Resource policy missing or incorrect

**Solutions:**

```bash
# 1. Update state machine resource policy in source account
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:source-state-machine \
  --resource-policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::891376951562:role/target-account-role"
      },
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:StopExecution"
      ],
      "Resource": "arn:aws:states:us-east-1:123456789012:stateMachine:source-state-machine"
    }]
  }'
```

```typescript
// 2. Add cross-account permissions in target account
lambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'states:StartExecution',
    'states:DescribeExecution',
    'states:StopExecution',
  ],
  resources: [
    'arn:aws:states:us-east-1:123456789012:stateMachine:source-state-machine',
    'arn:aws:states:us-east-1:123456789012:stateMachine:source-state-machine:*',
  ],
}));
```

#### Issue 9: State Machine ARN Format Mismatch

**Symptom:**
```
InvalidArn: State machine ARN format is invalid
```

**Causes:**
- Incorrect ARN format
- Missing region or account ID
- Typo in state machine name

**Solutions:**

```bash
# Correct ARN format:
# arn:aws:states:{region}:{account-id}:stateMachine:{state-machine-name}

# Example:
# arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test

# 1. Get correct ARN
aws stepfunctions list-state-machines \
  --query "stateMachines[?name=='hrp-drs-tech-adapter-state-machine-test'].stateMachineArn" \
  --output text

# 2. Validate ARN format
echo "arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test" | \
  grep -E '^arn:aws:states:[a-z0-9-]+:[0-9]{12}:stateMachine:[a-zA-Z0-9-_]+$'
```

#### Issue 10: CDK Diff Shows Unexpected Changes

**Symptom:**
```
cdk diff shows state machine will be replaced
```

**Causes:**
- Using `new sfn.StateMachine()` instead of import
- State machine name changed
- Logical ID changed

**Solutions:**

```bash
# 1. Review CDK diff carefully
cdk diff > diff-output.txt
grep -A 10 "StateMachine" diff-output.txt

# 2. Verify import is being used
grep "fromStateMachine" lib/*.ts

# 3. Check logical ID hasn't changed
cdk synth | grep -A 5 "DROrchestrationStateMachine"
```

```typescript
// 4. Ensure consistent logical ID
const stateMachine = sfn.StateMachine.fromStateMachineArn(
  this,
  'DROrchestrationStateMachine', // Keep this ID consistent
  props.existingStateMachineArn
);
```

### Debugging Checklist

When troubleshooting Step Functions integration issues:

- [ ] Verify state machine exists and is in correct region
- [ ] Check state machine ARN format is correct
- [ ] Confirm IAM permissions for all operations
- [ ] Verify Lambda resource policies allow state machine invocation
- [ ] Check CloudWatch Logs for execution details
- [ ] Review state machine definition for errors
- [ ] Verify DynamoDB table permissions
- [ ] Check EventBridge rule configuration
- [ ] Confirm execution input format matches state machine expectations
- [ ] Review X-Ray traces for detailed execution flow

### Getting Help

If issues persist:

1. **Check AWS Documentation:**
   - [Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/)
   - [CDK Step Functions Module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_stepfunctions-readme.html)

2. **Review CloudWatch Logs:**
   ```bash
   aws logs tail /aws/vendedlogs/states/hrp-drs-tech-adapter-state-machine-test --follow
   ```

3. **Enable X-Ray Tracing:**
   ```typescript
   const stateMachine = new sfn.StateMachine(this, 'StateMachine', {
     // ... other properties
     tracingEnabled: true,
   });
   ```

4. **Contact AWS Support:**
   - Provide state machine ARN
   - Include execution ARN for failed executions
   - Share CloudWatch Logs excerpts
   - Describe expected vs actual behavior



## AWS CLI Verification Commands

### State Machine Information

```bash
# List all state machines
aws stepfunctions list-state-machines \
  --query 'stateMachines[*].{Name:name,ARN:stateMachineArn,Type:type,CreationDate:creationDate}' \
  --output table

# Describe specific state machine
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test

# Get state machine definition
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --query 'definition' \
  --output text | jq .

# Get state machine IAM role
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --query 'roleArn' \
  --output text
```

### Execution Management

```bash
# Start execution
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --name test-execution-$(date +%s) \
  --input '{"planId":"plan-test-123","executionType":"DRILL","waves":[{"waveNumber":1,"servers":["s-1234567890abcdef0"]}]}'

# List recent executions
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --max-results 10 \
  --query 'executions[*].{Name:name,Status:status,StartDate:startDate}' \
  --output table

# Describe execution
aws stepfunctions describe-execution \
  --execution-arn <execution-arn>

# Get execution history
aws stepfunctions get-execution-history \
  --execution-arn <execution-arn> \
  --max-results 100

# Stop execution
aws stepfunctions stop-execution \
  --execution-arn <execution-arn> \
  --error "UserRequested" \
  --cause "Manual stop requested"
```



### Monitoring and Metrics

```bash
# Get execution metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/States \
  --metric-name ExecutionsFailed \
  --dimensions Name=StateMachineArn,Value=arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Get execution duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/States \
  --metric-name ExecutionTime \
  --dimensions Name=StateMachineArn,Value=arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# View CloudWatch Logs
aws logs tail /aws/vendedlogs/states/hrp-drs-tech-adapter-state-machine-test --follow

# Filter logs for specific execution
aws logs filter-log-events \
  --log-group-name /aws/vendedlogs/states/hrp-drs-tech-adapter-state-machine-test \
  --filter-pattern "<execution-arn>"
```

### IAM Permission Verification

```bash
# Check Lambda function policy
aws lambda get-policy \
  --function-name hrp-drs-tech-adapter-execution-handler-test \
  | jq .

# Check state machine role permissions
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test

aws iam list-role-policies \
  --role-name hrp-drs-tech-adapter-orchestration-role-test

aws iam get-role-policy \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --policy-name <policy-name>

# Test permissions with dry-run
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:891376951562:stateMachine:hrp-drs-tech-adapter-state-machine-test \
  --name dry-run-test-$(date +%s) \
  --input '{}' \
  --dry-run
```

## Integration with DR Orchestration Lambda Functions

### Lambda Environment Variables

When integrating imported state machines with Lambda functions, configure environment variables:

```typescript
const executionHandler = new lambda.Function(this, 'ExecutionHandler', {
  // ... other properties
  environment: {
    STATE_MACHINE_ARN: drOrchestrationStateMachine.stateMachineArn,
    EXECUTIONS_TABLE: executionsTable.tableName,
    RECOVERY_PLANS_TABLE: recoveryPlansTable.tableName,
  },
});
```

### Lambda Function Code Pattern

```python
import os
import boto3
import json
from datetime import datetime, timezone

# Initialize clients
stepfunctions = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']
EXECUTIONS_TABLE = os.environ['EXECUTIONS_TABLE']

def lambda_handler(event, context):
    """
    Execution Handler Lambda function.
    
    Supports both API Gateway and direct invocation modes.
    """
    # Detect invocation mode
    if 'requestContext' in event:
        # API Gateway invocation
        return handle_api_gateway_request(event, context)
    elif 'operation' in event:
        # Direct invocation
        return handle_direct_invocation(event, context)
    else:
        return {
            'error': 'INVALID_INVOCATION',
            'message': 'Event must contain requestContext or operation'
        }

def handle_direct_invocation(event, context):
    """Handle direct Lambda invocation."""
    operation = event.get('operation')
    
    if operation == 'start_execution':
        return start_execution(event)
    elif operation == 'stop_execution':
        return stop_execution(event)
    elif operation == 'describe_execution':
        return describe_execution(event)
    else:
        return {
            'error': 'INVALID_OPERATION',
            'message': f'Operation {operation} not supported'
        }

def start_execution(event):
    """Start Step Functions execution."""
    plan_id = event.get('planId')
    execution_type = event.get('executionType', 'DRILL')
    
    # Get recovery plan from DynamoDB
    table = dynamodb.Table(os.environ['RECOVERY_PLANS_TABLE'])
    response = table.get_item(Key={'planId': plan_id})
    
    if 'Item' not in response:
        return {
            'error': 'NOT_FOUND',
            'message': f'Recovery plan {plan_id} not found'
        }
    
    plan = response['Item']
    
    # Start Step Functions execution
    execution_name = f"{plan_id}-{execution_type}-{int(datetime.now(timezone.utc).timestamp())}"
    
    sfn_response = stepfunctions.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=execution_name,
        input=json.dumps({
            'planId': plan_id,
            'executionType': execution_type,
            'waves': plan.get('waves', []),
            'protectionGroupId': plan.get('protectionGroupId'),
        })
    )
    
    # Record execution in DynamoDB
    executions_table = dynamodb.Table(EXECUTIONS_TABLE)
    executions_table.put_item(
        Item={
            'executionId': execution_name,
            'planId': plan_id,
            'executionType': execution_type,
            'status': 'IN_PROGRESS',
            'startTime': datetime.now(timezone.utc).isoformat(),
            'stateMachineExecutionArn': sfn_response['executionArn'],
        }
    )
    
    return {
        'executionId': execution_name,
        'executionArn': sfn_response['executionArn'],
        'startDate': sfn_response['startDate'].isoformat(),
    }
```

### EventBridge Integration Pattern

```typescript
// Create EventBridge rule for scheduled executions
const scheduledRule = new events.Rule(this, 'ScheduledDRDrill', {
  ruleName: `${props.projectName}-scheduled-drill-${props.environment}`,
  description: 'Trigger DR drill execution weekly',
  schedule: events.Schedule.cron({
    minute: '0',
    hour: '2',
    weekDay: 'SUN',
  }),
});

// Add state machine as target
scheduledRule.addTarget(
  new targets.SfnStateMachine(drOrchestrationStateMachine, {
    input: events.RuleTargetInput.fromObject({
      planId: 'plan-weekly-drill',
      executionType: 'DRILL',
      dryRun: false,
      source: 'eventbridge-scheduled',
    }),
  })
);
```

## Summary

This guide covered:

✅ **Why import existing state machines** - Data preservation, operational continuity, cost optimization

✅ **Use cases** - CloudFormation to CDK migration, multi-stack architecture, stack recreation, blue/green deployment

✅ **CDK import patterns** - Import by name, ARN, with attributes, conditional import vs create

✅ **Migration strategy** - Step-by-step guide with 5 phases (preparation, CloudFormation update, CDK deployment, cleanup, rollback)

✅ **Code examples** - 6 complete TypeScript examples covering simple import, EventBridge integration, cross-account access, conditional logic, Lambda integration, and CloudWatch alarms

✅ **Best practices** - 10 comprehensive sections covering when to import, naming conventions, backups, IAM permissions, testing, configuration drift, monitoring, documentation, definition management, and execution history

✅ **Troubleshooting** - 10 common issues with detailed solutions and debugging checklist

✅ **AWS CLI commands** - Verification commands for state machines, executions, monitoring, and IAM permissions

✅ **Lambda integration** - Environment variables, code patterns, and EventBridge integration

## Next Steps

1. **Review your existing state machines** - Document ARNs, definitions, and dependencies
2. **Plan your migration** - Choose appropriate import pattern based on your use case
3. **Test in development** - Deploy CDK stack with imported state machines in dev environment
4. **Validate thoroughly** - Verify executions, permissions, and monitoring
5. **Document your setup** - Record state machine configurations and integration points
6. **Deploy to production** - Follow migration strategy with proper backups and rollback plan

## Related Documentation

- [DynamoDB Integration Guide](./DYNAMODB_INTEGRATION.md) - Import existing DynamoDB tables
- [CDK DR Orchestration Stack](../lib/dr-orchestration-stack.ts) - Main CDK stack implementation
- [Direct Lambda Invocation Mode Design](../../../.kiro/specs/direct-lambda-invocation-mode/design.md) - Architecture and design
- [AWS Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/) - Official AWS documentation
- [CDK Step Functions Module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_stepfunctions-readme.html) - CDK API reference

