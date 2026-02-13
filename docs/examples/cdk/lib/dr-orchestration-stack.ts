import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

/**
 * Stack properties for DR Orchestration Platform
 */
export interface DROrchestrationStackProps extends cdk.StackProps {
  /** Project name for resource naming */
  projectName: string;
  
  /** Environment name (dev, test, staging, prod) */
  environment: string;
  
  /** Admin email for notifications */
  adminEmail: string;
  
  /** Deploy API Gateway, Cognito, and frontend (default: false for headless mode) */
  deployApiGateway?: boolean;
  
  /** Enable scheduled tag synchronization (default: true) */
  enableTagSync?: boolean;
  
  /** Enable email notifications (default: false) */
  enableNotifications?: boolean;
}

/**
 * DR Orchestration Platform Stack
 * 
 * Deploys the complete DR Orchestration Platform in headless mode with:
 * - Lambda functions for direct invocation
 * - DynamoDB tables for data persistence
 * - Step Functions for wave-based orchestration
 * - EventBridge rules for scheduled operations
 * - IAM roles with proper permissions
 * 
 * This stack demonstrates infrastructure-as-code deployment without API Gateway,
 * enabling programmatic disaster recovery operations via AWS SDK/CLI.
 */
export class DROrchestrationStack extends cdk.Stack {
  /** Unified IAM role for all Lambda functions */
  public readonly orchestrationRole: iam.Role;
  
  /** Query Handler Lambda function */
  public readonly queryHandler: lambda.Function;
  
  /** Execution Handler Lambda function */
  public readonly executionHandler: lambda.Function;
  
  /** Data Management Handler Lambda function */
  public readonly dataManagementHandler: lambda.Function;
  
  /** DynamoDB tables */
  public readonly protectionGroupsTable: dynamodb.Table;
  public readonly recoveryPlansTable: dynamodb.Table;
  public readonly executionsTable: dynamodb.Table;
  public readonly targetAccountsTable: dynamodb.Table;
  
  constructor(scope: Construct, id: string, props: DROrchestrationStackProps) {
    super(scope, id, props);
    
    // Create DynamoDB tables
    this.createDynamoDBTables(props);
    
    // Create SNS topics for notifications
    const notificationTopic = this.createNotificationTopic(props);
    
    // Create unified IAM role for Lambda functions
    this.orchestrationRole = this.createOrchestrationRole(props, notificationTopic);
    
    // Create Lambda functions
    this.createLambdaFunctions(props);
    
    // Create Step Functions state machine
    const stateMachine = this.createStepFunctionsStateMachine(props);
    
    // Create EventBridge rules
    this.createEventBridgeRules(props, stateMachine);
    
    // Output important resource ARNs
    this.createOutputs(props);
  }
  
  /**
   * Create DynamoDB tables for data persistence
   */
  private createDynamoDBTables(props: DROrchestrationStackProps): void {
    // Protection Groups table
    this.protectionGroupsTable = new dynamodb.Table(this, 'ProtectionGroupsTable', {
      tableName: `${props.projectName}-protection-groups-${props.environment}`,
      partitionKey: {
        name: 'groupId',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    });
    
    // Recovery Plans table
    this.recoveryPlansTable = new dynamodb.Table(this, 'RecoveryPlansTable', {
      tableName: `${props.projectName}-recovery-plans-${props.environment}`,
      partitionKey: {
        name: 'planId',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    });
    
    // Add GSI for querying plans by protection group
    this.recoveryPlansTable.addGlobalSecondaryIndex({
      indexName: 'ProtectionGroupIndex',
      partitionKey: {
        name: 'protectionGroupId',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });
    
    // Executions table
    this.executionsTable = new dynamodb.Table(this, 'ExecutionsTable', {
      tableName: `${props.projectName}-executions-${props.environment}`,
      partitionKey: {
        name: 'executionId',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
    });
    
    // Add GSI for querying executions by status
    this.executionsTable.addGlobalSecondaryIndex({
      indexName: 'StatusIndex',
      partitionKey: {
        name: 'status',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'startTime',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });
    
    // Add GSI for querying executions by plan
    this.executionsTable.addGlobalSecondaryIndex({
      indexName: 'PlanIndex',
      partitionKey: {
        name: 'planId',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'startTime',
        type: dynamodb.AttributeType.STRING,
      },
      projectionType: dynamodb.ProjectionType.ALL,
    });
    
    // Target Accounts table
    this.targetAccountsTable = new dynamodb.Table(this, 'TargetAccountsTable', {
      tableName: `${props.projectName}-target-accounts-${props.environment}`,
      partitionKey: {
        name: 'accountId',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    });
  }
  
  /**
   * Create SNS topic for notifications
   */
  private createNotificationTopic(props: DROrchestrationStackProps): sns.Topic {
    const topic = new sns.Topic(this, 'NotificationTopic', {
      topicName: `${props.projectName}-notifications-${props.environment}`,
      displayName: 'DR Orchestration Notifications',
    });
    
    // Add email subscription if notifications are enabled
    if (props.enableNotifications) {
      topic.addSubscription(
        new cdk.aws_sns_subscriptions.EmailSubscription(props.adminEmail)
      );
    }
    
    return topic;
  }
  
  /**
   * Create unified IAM role for all Lambda functions
   * 
   * This role provides permissions for:
   * - DynamoDB read/write operations
   * - DRS operations (describe, start recovery, terminate instances)
   * - Step Functions execution
   * - SNS notifications
   * - EC2 operations for recovery instances
   * - Cross-account role assumption
   */
  private createOrchestrationRole(
    props: DROrchestrationStackProps,
    notificationTopic: sns.Topic
  ): iam.Role {
    const role = new iam.Role(this, 'OrchestrationRole', {
      roleName: `${props.projectName}-orchestration-role-${props.environment}`,
      assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal('lambda.amazonaws.com'),
        new iam.ServicePrincipal('states.amazonaws.com')
      ),
      description: 'Unified role for DR Orchestration Lambda functions and Step Functions',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    
    // DynamoDB permissions
    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'dynamodb:GetItem',
        'dynamodb:PutItem',
        'dynamodb:UpdateItem',
        'dynamodb:DeleteItem',
        'dynamodb:Query',
        'dynamodb:Scan',
        'dynamodb:BatchGetItem',
        'dynamodb:BatchWriteItem',
      ],
      resources: [
        this.protectionGroupsTable.tableArn,
        this.recoveryPlansTable.tableArn,
        this.executionsTable.tableArn,
        this.targetAccountsTable.tableArn,
        `${this.protectionGroupsTable.tableArn}/index/*`,
        `${this.recoveryPlansTable.tableArn}/index/*`,
        `${this.executionsTable.tableArn}/index/*`,
      ],
    }));
    
    // DRS permissions
    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'drs:DescribeSourceServers',
        'drs:DescribeRecoverySnapshots',
        'drs:DescribeRecoveryInstances',
        'drs:DescribeJobs',
        'drs:DescribeJobLogItems',
        'drs:GetReplicationConfiguration',
        'drs:GetLaunchConfiguration',
        'drs:StartRecovery',
        'drs:TerminateRecoveryInstances',
        'drs:UpdateLaunchConfiguration',
        'drs:CreateExtendedSourceServer',
        'drs:DeleteSourceServer',
        'drs:TagResource',
        'drs:UntagResource',
        'drs:ListTagsForResource',
      ],
      resources: ['*'], // DRS requires wildcard resources
    }));
    
    // EC2 permissions for recovery instances
    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'ec2:DescribeInstances',
        'ec2:DescribeInstanceStatus',
        'ec2:DescribeInstanceTypes',
        'ec2:DescribeImages',
        'ec2:DescribeSecurityGroups',
        'ec2:DescribeSubnets',
        'ec2:DescribeVpcs',
        'ec2:DescribeVolumes',
        'ec2:DescribeSnapshots',
        'ec2:CreateTags',
        'ec2:TerminateInstances',
      ],
      resources: ['*'],
    }));
    
    // Step Functions permissions
    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'states:StartExecution',
        'states:DescribeExecution',
        'states:ListExecutions',
        'states:SendTaskSuccess',
        'states:SendTaskFailure',
        'states:SendTaskHeartbeat',
      ],
      resources: [
        `arn:aws:states:${this.region}:${this.account}:stateMachine:${props.projectName}-*`,
        `arn:aws:states:${this.region}:${this.account}:execution:${props.projectName}-*:*`,
      ],
    }));
    
    // SNS permissions for notifications
    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'sns:Publish',
      ],
      resources: [notificationTopic.topicArn],
    }));
    
    // Lambda invocation permissions (for cross-function calls)
    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'lambda:InvokeFunction',
      ],
      resources: [
        `arn:aws:lambda:${this.region}:${this.account}:function:${props.projectName}-*`,
      ],
    }));
    
    // STS AssumeRole for cross-account operations
    role.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'sts:AssumeRole',
      ],
      resources: [
        `arn:aws:iam::*:role/${props.projectName}-cross-account-role-*`,
        'arn:aws:iam::*:role/DRSOrchestrationRole',
      ],
    }));
    
    return role;
  }
  
  /**
   * Create Lambda functions for query, execution, and data management
   */
  private createLambdaFunctions(props: DROrchestrationStackProps): void {
    // Common Lambda configuration
    const commonConfig = {
      runtime: lambda.Runtime.PYTHON_3_11,
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      role: this.orchestrationRole,
      environment: {
        PROTECTION_GROUPS_TABLE: this.protectionGroupsTable.tableName,
        RECOVERY_PLANS_TABLE: this.recoveryPlansTable.tableName,
        EXECUTIONS_TABLE: this.executionsTable.tableName,
        TARGET_ACCOUNTS_TABLE: this.targetAccountsTable.tableName,
        PROJECT_NAME: props.projectName,
        ENVIRONMENT: props.environment,
        ORCHESTRATION_ROLE_ARN: this.orchestrationRole.roleArn,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    };
    
    // Query Handler - Read-only operations
    this.queryHandler = new lambda.Function(this, 'QueryHandler', {
      ...commonConfig,
      functionName: `${props.projectName}-query-handler-${props.environment}`,
      description: 'Handles read-only queries for protection groups, recovery plans, and executions',
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
    });
    
    // Execution Handler - Recovery execution lifecycle
    this.executionHandler = new lambda.Function(this, 'ExecutionHandler', {
      ...commonConfig,
      functionName: `${props.projectName}-execution-handler-${props.environment}`,
      description: 'Manages recovery execution lifecycle (start, cancel, pause, resume, terminate)',
      code: lambda.Code.fromAsset('../../lambda/execution-handler'),
      handler: 'index.lambda_handler',
      timeout: cdk.Duration.minutes(15), // Longer timeout for execution operations
    });
    
    // Data Management Handler - CRUD operations
    this.dataManagementHandler = new lambda.Function(this, 'DataManagementHandler', {
      ...commonConfig,
      functionName: `${props.projectName}-data-management-handler-${props.environment}`,
      description: 'Handles CRUD operations for protection groups, recovery plans, and configurations',
      code: lambda.Code.fromAsset('../../lambda/data-management-handler'),
      handler: 'index.lambda_handler',
    });
    
    // Grant Lambda functions permission to be invoked by OrchestrationRole
    // This enables direct invocation via AWS SDK/CLI
    this.queryHandler.grantInvoke(this.orchestrationRole);
    this.executionHandler.grantInvoke(this.orchestrationRole);
    this.dataManagementHandler.grantInvoke(this.orchestrationRole);
  }
  
  /**
   * Create Step Functions state machine for wave-based orchestration
   */
  private createStepFunctionsStateMachine(props: DROrchestrationStackProps): sfn.StateMachine {
    // Create DR Orchestration Lambda for Step Functions
    const drOrchestrationLambda = new lambda.Function(this, 'DROrchestrationLambda', {
      functionName: `${props.projectName}-stepfunction-${props.environment}`,
      description: 'Orchestrates wave-based disaster recovery operations',
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/dr-orchestration-stepfunction'),
      handler: 'index.lambda_handler',
      timeout: cdk.Duration.minutes(15),
      memorySize: 512,
      role: this.orchestrationRole,
      environment: {
        EXECUTIONS_TABLE: this.executionsTable.tableName,
        PROJECT_NAME: props.projectName,
        ENVIRONMENT: props.environment,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });
    
    // Create state machine definition (simplified for example)
    const definition = sfn.DefinitionBody.fromString(JSON.stringify({
      Comment: 'Wave-based disaster recovery orchestration',
      StartAt: 'InitializeExecution',
      States: {
        InitializeExecution: {
          Type: 'Task',
          Resource: 'arn:aws:states:::lambda:invoke',
          Parameters: {
            FunctionName: drOrchestrationLambda.functionArn,
            Payload: {
              'action': 'initialize',
              'executionId.$': '$.executionId',
            },
          },
          Next: 'ProcessWaves',
        },
        ProcessWaves: {
          Type: 'Map',
          ItemsPath: '$.waves',
          MaxConcurrency: 1,
          Iterator: {
            StartAt: 'StartWaveRecovery',
            States: {
              StartWaveRecovery: {
                Type: 'Task',
                Resource: 'arn:aws:states:::lambda:invoke',
                Parameters: {
                  FunctionName: drOrchestrationLambda.functionArn,
                  Payload: {
                    'action': 'start_wave_recovery',
                    'executionId.$': '$.executionId',
                    'waveNumber.$': '$.waveNumber',
                  },
                },
                Next: 'WaitForWaveCompletion',
              },
              WaitForWaveCompletion: {
                Type: 'Wait',
                Seconds: 30,
                Next: 'CheckWaveStatus',
              },
              CheckWaveStatus: {
                Type: 'Task',
                Resource: 'arn:aws:states:::lambda:invoke',
                Parameters: {
                  FunctionName: drOrchestrationLambda.functionArn,
                  Payload: {
                    'action': 'check_wave_status',
                    'executionId.$': '$.executionId',
                    'waveNumber.$': '$.waveNumber',
                  },
                },
                Next: 'IsWaveComplete',
              },
              IsWaveComplete: {
                Type: 'Choice',
                Choices: [
                  {
                    Variable: '$.status',
                    StringEquals: 'COMPLETED',
                    Next: 'WaveSuccess',
                  },
                  {
                    Variable: '$.status',
                    StringEquals: 'FAILED',
                    Next: 'WaveFailed',
                  },
                ],
                Default: 'WaitForWaveCompletion',
              },
              WaveSuccess: {
                Type: 'Succeed',
              },
              WaveFailed: {
                Type: 'Fail',
                Error: 'WaveRecoveryFailed',
                Cause: 'Wave recovery failed',
              },
            },
          },
          Next: 'FinalizeExecution',
        },
        FinalizeExecution: {
          Type: 'Task',
          Resource: 'arn:aws:states:::lambda:invoke',
          Parameters: {
            FunctionName: drOrchestrationLambda.functionArn,
            Payload: {
              'action': 'finalize',
              'executionId.$': '$.executionId',
            },
          },
          End: true,
        },
      },
    }));
    
    // Create state machine
    const stateMachine = new sfn.StateMachine(this, 'StateMachine', {
      stateMachineName: `${props.projectName}-orchestration-${props.environment}`,
      definitionBody: definition,
      role: this.orchestrationRole,
      logs: {
        destination: new logs.LogGroup(this, 'StateMachineLogGroup', {
          logGroupName: `/aws/vendedlogs/states/${props.projectName}-orchestration-${props.environment}`,
          retention: logs.RetentionDays.ONE_WEEK,
          removalPolicy: cdk.RemovalPolicy.DESTROY,
        }),
        level: sfn.LogLevel.ALL,
      },
      tracingEnabled: true,
    });
    
    return stateMachine;
  }
  
  /**
   * Create EventBridge rules for scheduled operations
   */
  private createEventBridgeRules(
    props: DROrchestrationStackProps,
    stateMachine: sfn.StateMachine
  ): void {
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
    
    // Execution polling rule (checks for stuck executions)
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
  }
  
  /**
   * Create CloudFormation outputs
   */
  private createOutputs(props: DROrchestrationStackProps): void {
    // Lambda function ARNs
    new cdk.CfnOutput(this, 'QueryHandlerArn', {
      value: this.queryHandler.functionArn,
      description: 'Query Handler Lambda function ARN',
      exportName: `${props.projectName}-query-handler-arn-${props.environment}`,
    });
    
    new cdk.CfnOutput(this, 'ExecutionHandlerArn', {
      value: this.executionHandler.functionArn,
      description: 'Execution Handler Lambda function ARN',
      exportName: `${props.projectName}-execution-handler-arn-${props.environment}`,
    });
    
    new cdk.CfnOutput(this, 'DataManagementHandlerArn', {
      value: this.dataManagementHandler.functionArn,
      description: 'Data Management Handler Lambda function ARN',
      exportName: `${props.projectName}-data-management-handler-arn-${props.environment}`,
    });
    
    // IAM role ARN
    new cdk.CfnOutput(this, 'OrchestrationRoleArn', {
      value: this.orchestrationRole.roleArn,
      description: 'Orchestration IAM role ARN',
      exportName: `${props.projectName}-orchestration-role-arn-${props.environment}`,
    });
    
    // DynamoDB table names
    new cdk.CfnOutput(this, 'ProtectionGroupsTableName', {
      value: this.protectionGroupsTable.tableName,
      description: 'Protection Groups DynamoDB table name',
    });
    
    new cdk.CfnOutput(this, 'RecoveryPlansTableName', {
      value: this.recoveryPlansTable.tableName,
      description: 'Recovery Plans DynamoDB table name',
    });
    
    new cdk.CfnOutput(this, 'ExecutionsTableName', {
      value: this.executionsTable.tableName,
      description: 'Executions DynamoDB table name',
    });
    
    // Example invocation commands
    new cdk.CfnOutput(this, 'ExampleInvocationCommand', {
      value: `aws lambda invoke --function-name ${this.queryHandler.functionName} --payload '{"operation":"list_protection_groups"}' response.json`,
      description: 'Example AWS CLI command to invoke Query Handler',
    });
  }
}
