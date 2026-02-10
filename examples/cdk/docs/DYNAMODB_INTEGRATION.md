# DynamoDB Integration Guide for CDK

## Overview

This guide explains how to integrate the AWS CDK DR Orchestration stack with **existing DynamoDB tables** from a previous deployment. This is useful when:

- Migrating from CloudFormation to CDK while preserving data
- Sharing DynamoDB tables across multiple stacks
- Recreating infrastructure without losing data
- Implementing blue/green deployment strategies

## Table of Contents

1. [Why Import Existing Tables?](#why-import-existing-tables)
2. [Use Cases](#use-cases)
3. [CDK Import Patterns](#cdk-import-patterns)
4. [Migration Strategy](#migration-strategy)
5. [Code Examples](#code-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Why Import Existing Tables?

### Benefits of Importing Tables

**Data Preservation:**
- Keep existing data during infrastructure changes
- Avoid costly data migration processes
- Maintain historical execution records

**Operational Continuity:**
- Zero downtime during stack transitions
- No service interruption for running executions
- Preserve audit trails and compliance records

**Cost Optimization:**
- Reuse existing table capacity
- Avoid duplicate storage costs
- Share tables across environments

**Flexibility:**
- Decouple data layer from compute layer
- Enable independent stack lifecycle management
- Support multi-stack architectures


## Use Cases

### 1. CloudFormation to CDK Migration

**Scenario:** You have an existing CloudFormation deployment with DynamoDB tables containing production data. You want to migrate to CDK without losing data.

**Solution:** Import existing tables into CDK stack, update Lambda functions to use imported tables, then delete old CloudFormation stack.

**Timeline:** 1-2 hours with zero downtime

### 2. Multi-Stack Architecture

**Scenario:** You want to deploy multiple DR orchestration stacks (dev, test, staging) that share the same DynamoDB tables for centralized data management.

**Solution:** Create a separate "data stack" with DynamoDB tables, then import those tables into multiple "compute stacks" with Lambda functions.

**Benefits:** Centralized data, independent compute deployments, cost savings

### 3. Stack Recreation

**Scenario:** Your CDK stack is in a failed state and needs to be deleted and recreated, but you cannot lose the data in DynamoDB tables.

**Solution:** Set `removalPolicy: RETAIN` on tables before deletion, then import the retained tables into the new stack.

**Recovery Time:** 10-15 minutes

### 4. Blue/Green Deployment

**Scenario:** You want to deploy a new version of your DR orchestration platform alongside the existing version for testing, using the same data.

**Solution:** Deploy "green" stack that imports tables from "blue" stack, test thoroughly, then switch traffic and delete "blue" stack.

**Risk Mitigation:** Full rollback capability, zero data loss


## CDK Import Patterns

### Pattern 1: Import by Table Name

The simplest pattern for importing existing tables:

```typescript
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

// Import existing table by name
const protectionGroupsTable = dynamodb.Table.fromTableName(
  this,
  'ProtectionGroupsTable',
  'aws-drs-orchestration-protection-groups-test'
);

// Use imported table
protectionGroupsTable.grantReadWriteData(lambdaRole);
```

**When to use:**
- Same AWS account
- Same AWS region
- Table name is known

**Limitations:**
- Cannot modify table configuration (billing mode, encryption, etc.)
- Cannot add/remove GSIs
- Cannot change removal policy

### Pattern 2: Import by Table ARN

For cross-account or cross-region scenarios:

```typescript
// Import table by ARN
const protectionGroupsTable = dynamodb.Table.fromTableArn(
  this,
  'ProtectionGroupsTable',
  'arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test'
);

// Use imported table
protectionGroupsTable.grantReadWriteData(lambdaRole);
```

**When to use:**
- Cross-account access
- Cross-region access
- Full ARN is available

**Benefits:**
- Works across account boundaries
- Explicit resource identification
- Supports cross-region replication


### Pattern 3: Import with Attributes

For tables with Global Secondary Indexes (GSIs):

```typescript
// Import table with GSI information
const executionsTable = dynamodb.Table.fromTableAttributes(
  this,
  'ExecutionsTable',
  {
    tableName: 'aws-drs-orchestration-executions-test',
    tableArn: 'arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-executions-test',
    globalIndexes: ['StatusIndex', 'PlanIndex'],
    localIndexes: [],
    tableStreamArn: 'arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-executions-test/stream/2025-01-31T00:00:00.000',
  }
);

// Grant permissions including GSI access
executionsTable.grantReadWriteData(lambdaRole);
```

**When to use:**
- Table has GSIs that Lambda needs to query
- Need to grant permissions on specific indexes
- Table has DynamoDB Streams

**Benefits:**
- Full permission management
- GSI-aware IAM policies
- Stream integration support

### Pattern 4: Conditional Import vs Create

Support both new deployments and imports:

```typescript
interface DROrchestrationStackProps extends cdk.StackProps {
  // ... existing props ...
  importExistingTables?: boolean;
  existingTableNames?: {
    protectionGroups?: string;
    recoveryPlans?: string;
    executions?: string;
    targetAccounts?: string;
  };
}

// In stack constructor
if (props.importExistingTables && props.existingTableNames?.protectionGroups) {
  // Import existing table
  this.protectionGroupsTable = dynamodb.Table.fromTableName(
    this,
    'ProtectionGroupsTable',
    props.existingTableNames.protectionGroups
  );
} else {
  // Create new table
  this.protectionGroupsTable = new dynamodb.Table(this, 'ProtectionGroupsTable', {
    tableName: `${props.projectName}-protection-groups-${props.environment}`,
    partitionKey: { name: 'groupId', type: dynamodb.AttributeType.STRING },
    billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    removalPolicy: cdk.RemovalPolicy.RETAIN,
  });
}
```

**When to use:**
- Supporting both greenfield and migration scenarios
- Gradual migration approach
- Testing with different configurations


## Migration Strategy

### Step-by-Step Migration from CloudFormation to CDK

#### Phase 1: Preparation (15 minutes)

**1. Identify Existing Tables**

```bash
# List all DynamoDB tables in your stack
aws cloudformation describe-stack-resources \
  --stack-name aws-drs-orchestration-test \
  --query 'StackResources[?ResourceType==`AWS::DynamoDB::Table`].[LogicalResourceId,PhysicalResourceId]' \
  --output table

# Example output:
# ProtectionGroupsTable    aws-drs-orchestration-protection-groups-test
# RecoveryPlansTable       aws-drs-orchestration-recovery-plans-test
# ExecutionsTable          aws-drs-orchestration-executions-test
# TargetAccountsTable      aws-drs-orchestration-target-accounts-test
```

**2. Document Table Configuration**

```bash
# Get table details
aws dynamodb describe-table \
  --table-name aws-drs-orchestration-protection-groups-test \
  --query 'Table.{Name:TableName,ARN:TableArn,BillingMode:BillingModeSummary.BillingMode,Encryption:SSEDescription.SSEType,GSIs:GlobalSecondaryIndexes[].IndexName}' \
  --output json

# Save table ARNs for CDK import
export PROTECTION_GROUPS_TABLE_ARN="arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test"
export RECOVERY_PLANS_TABLE_ARN="arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-recovery-plans-test"
export EXECUTIONS_TABLE_ARN="arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-executions-test"
export TARGET_ACCOUNTS_TABLE_ARN="arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-target-accounts-test"
```

**3. Backup Data (Recommended)**

```bash
# Create on-demand backups
aws dynamodb create-backup \
  --table-name aws-drs-orchestration-protection-groups-test \
  --backup-name protection-groups-pre-migration-$(date +%Y%m%d)

aws dynamodb create-backup \
  --table-name aws-drs-orchestration-recovery-plans-test \
  --backup-name recovery-plans-pre-migration-$(date +%Y%m%d)

aws dynamodb create-backup \
  --table-name aws-drs-orchestration-executions-test \
  --backup-name executions-pre-migration-$(date +%Y%m%d)

aws dynamodb create-backup \
  --table-name aws-drs-orchestration-target-accounts-test \
  --backup-name target-accounts-pre-migration-$(date +%Y%m%d)
```


#### Phase 2: Update CloudFormation Stack (10 minutes)

**1. Set Removal Policy to RETAIN**

Before deleting the CloudFormation stack, update table removal policies to prevent deletion:

```bash
# Update CloudFormation template to set DeletionPolicy: Retain
# Edit cfn/dynamodb-stack.yaml:

Resources:
  ProtectionGroupsTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain  # Add this line
    UpdateReplacePolicy: Retain  # Add this line
    Properties:
      # ... existing properties ...

  RecoveryPlansTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain  # Add this line
    UpdateReplacePolicy: Retain  # Add this line
    Properties:
      # ... existing properties ...

  ExecutionsTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain  # Add this line
    UpdateReplacePolicy: Retain  # Add this line
    Properties:
      # ... existing properties ...

  TargetAccountsTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain  # Add this line
    UpdateReplacePolicy: Retain  # Add this line
    Properties:
      # ... existing properties ...
```

**2. Deploy Updated CloudFormation Stack**

```bash
# Deploy with RETAIN policy
aws cloudformation update-stack \
  --stack-name aws-drs-orchestration-test \
  --template-body file://cfn/master-template.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for update to complete
aws cloudformation wait stack-update-complete \
  --stack-name aws-drs-orchestration-test
```

**3. Verify RETAIN Policy**

```bash
# Verify DeletionPolicy is set
aws cloudformation describe-stack-resources \
  --stack-name aws-drs-orchestration-test \
  --query 'StackResources[?ResourceType==`AWS::DynamoDB::Table`].[LogicalResourceId,PhysicalResourceId]'
```


#### Phase 3: Deploy CDK Stack with Imported Tables (20 minutes)

**1. Create CDK Stack with Import Configuration**

Create a new file `examples/cdk/lib/dr-orchestration-import-stack.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';
import { DROrchestrationStack, DROrchestrationStackProps } from './dr-orchestration-stack';

/**
 * Extended stack that imports existing DynamoDB tables
 */
export class DROrchestrationImportStack extends DROrchestrationStack {
  constructor(scope: Construct, id: string, props: DROrchestrationStackProps & {
    existingTableNames: {
      protectionGroups: string;
      recoveryPlans: string;
      executions: string;
      targetAccounts: string;
    };
  }) {
    // Don't call super() yet - we need to override table creation
    
    // Import existing tables instead of creating new ones
    const protectionGroupsTable = dynamodb.Table.fromTableName(
      scope,
      'ImportedProtectionGroupsTable',
      props.existingTableNames.protectionGroups
    );
    
    const recoveryPlansTable = dynamodb.Table.fromTableAttributes(
      scope,
      'ImportedRecoveryPlansTable',
      {
        tableName: props.existingTableNames.recoveryPlans,
        globalIndexes: ['ProtectionGroupIndex'],
      }
    );
    
    const executionsTable = dynamodb.Table.fromTableAttributes(
      scope,
      'ImportedExecutionsTable',
      {
        tableName: props.existingTableNames.executions,
        globalIndexes: ['StatusIndex', 'PlanIndex'],
      }
    );
    
    const targetAccountsTable = dynamodb.Table.fromTableName(
      scope,
      'ImportedTargetAccountsTable',
      props.existingTableNames.targetAccounts
    );
    
    // Now call parent constructor with imported tables
    super(scope, id, props);
    
    // Override the table properties
    this.protectionGroupsTable = protectionGroupsTable;
    this.recoveryPlansTable = recoveryPlansTable;
    this.executionsTable = executionsTable;
    this.targetAccountsTable = targetAccountsTable;
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

const environment = process.env.ENVIRONMENT || 'dev';
const projectName = process.env.PROJECT_NAME || 'aws-drs-orchestration';
const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com';

// Import existing tables from CloudFormation deployment
const importExistingTables = process.env.IMPORT_EXISTING_TABLES === 'true';

if (importExistingTables) {
  new DROrchestrationImportStack(app, `${projectName}-${environment}`, {
    projectName,
    environment,
    adminEmail,
    existingTableNames: {
      protectionGroups: `${projectName}-protection-groups-${environment}`,
      recoveryPlans: `${projectName}-recovery-plans-${environment}`,
      executions: `${projectName}-executions-${environment}`,
      targetAccounts: `${projectName}-target-accounts-${environment}`,
    },
    env: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
    },
  });
} else {
  // Use standard stack that creates new tables
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
export PROJECT_NAME=aws-drs-orchestration
export ADMIN_EMAIL=admin@example.com
export IMPORT_EXISTING_TABLES=true

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
  --stack-name aws-drs-orchestration-test \
  --query 'Stacks[0].StackStatus'

# Verify Lambda functions can access tables
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

cat response.json | jq .
```

#### Phase 4: Delete Old CloudFormation Stack (10 minutes)

**1. Verify CDK Stack is Working**

```bash
# Test all Lambda functions
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-test \
  --payload '{"operation":"list_executions"}' \
  response.json

# Verify data is accessible
cat response.json | jq .
```

**2. Delete Old CloudFormation Stack**

```bash
# Delete CloudFormation stack (tables will be retained)
aws cloudformation delete-stack \
  --stack-name aws-drs-orchestration-test-old

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete \
  --stack-name aws-drs-orchestration-test-old
```

**3. Verify Tables Still Exist**

```bash
# Verify tables were not deleted
aws dynamodb list-tables \
  --query 'TableNames[?contains(@, `aws-drs-orchestration`)]'

# Should show all 4 tables still exist
```


#### Phase 5: Rollback Procedure (If Needed)

If something goes wrong during migration:

**1. Immediate Rollback**

```bash
# Delete CDK stack
cdk destroy --force

# Redeploy original CloudFormation stack
aws cloudformation create-stack \
  --stack-name aws-drs-orchestration-test \
  --template-body file://cfn/master-template.yaml \
  --parameters file://cfn/parameters-test.json \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for stack creation
aws cloudformation wait stack-create-complete \
  --stack-name aws-drs-orchestration-test
```

**2. Verify Rollback**

```bash
# Test Lambda functions
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

# Verify data is intact
cat response.json | jq .
```

**3. Document Rollback Reason**

Create incident report documenting:
- What went wrong
- When rollback was initiated
- Data integrity verification results
- Lessons learned for next attempt


## Code Examples

### Example 1: Simple Table Import

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class SimpleImportStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import existing table by name
    const protectionGroupsTable = dynamodb.Table.fromTableName(
      this,
      'ProtectionGroupsTable',
      'aws-drs-orchestration-protection-groups-test'
    );
    
    // Create Lambda function
    const queryHandler = new lambda.Function(this, 'QueryHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      environment: {
        PROTECTION_GROUPS_TABLE: protectionGroupsTable.tableName,
      },
    });
    
    // Grant Lambda permissions to access imported table
    protectionGroupsTable.grantReadWriteData(queryHandler);
  }
}
```

### Example 2: Import with GSI Support

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class ImportWithGSIStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import table with GSI information
    const executionsTable = dynamodb.Table.fromTableAttributes(
      this,
      'ExecutionsTable',
      {
        tableName: 'aws-drs-orchestration-executions-test',
        globalIndexes: ['StatusIndex', 'PlanIndex'],
      }
    );
    
    // Create Lambda function
    const executionHandler = new lambda.Function(this, 'ExecutionHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/execution-handler'),
      handler: 'index.lambda_handler',
      environment: {
        EXECUTIONS_TABLE: executionsTable.tableName,
      },
    });
    
    // Grant permissions (includes GSI access)
    executionsTable.grantReadWriteData(executionHandler);
  }
}
```


### Example 3: Cross-Account Table Import

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class CrossAccountImportStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import table from different account by ARN
    const protectionGroupsTable = dynamodb.Table.fromTableArn(
      this,
      'ProtectionGroupsTable',
      'arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test'
    );
    
    // Create Lambda execution role with cross-account permissions
    const lambdaRole = new iam.Role(this, 'LambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    
    // Add cross-account DynamoDB permissions
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'dynamodb:GetItem',
        'dynamodb:PutItem',
        'dynamodb:UpdateItem',
        'dynamodb:DeleteItem',
        'dynamodb:Query',
        'dynamodb:Scan',
      ],
      resources: [
        protectionGroupsTable.tableArn,
        `${protectionGroupsTable.tableArn}/index/*`,
      ],
    }));
    
    // Create Lambda function
    const queryHandler = new lambda.Function(this, 'QueryHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      role: lambdaRole,
      environment: {
        PROTECTION_GROUPS_TABLE: protectionGroupsTable.tableName,
      },
    });
  }
}
```

**Note:** For cross-account access, you also need to update the DynamoDB table's resource policy in the source account to allow access from the Lambda execution role.


### Example 4: Conditional Import vs Create

```typescript
import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export interface FlexibleStackProps extends cdk.StackProps {
  projectName: string;
  environment: string;
  importExistingTables?: boolean;
  existingTableNames?: {
    protectionGroups?: string;
    recoveryPlans?: string;
    executions?: string;
    targetAccounts?: string;
  };
}

export class FlexibleStack extends cdk.Stack {
  public readonly protectionGroupsTable: dynamodb.ITable;
  public readonly recoveryPlansTable: dynamodb.ITable;
  public readonly executionsTable: dynamodb.ITable;
  public readonly targetAccountsTable: dynamodb.ITable;
  
  constructor(scope: Construct, id: string, props: FlexibleStackProps) {
    super(scope, id, props);
    
    // Protection Groups Table
    if (props.importExistingTables && props.existingTableNames?.protectionGroups) {
      this.protectionGroupsTable = dynamodb.Table.fromTableName(
        this,
        'ProtectionGroupsTable',
        props.existingTableNames.protectionGroups
      );
    } else {
      this.protectionGroupsTable = new dynamodb.Table(this, 'ProtectionGroupsTable', {
        tableName: `${props.projectName}-protection-groups-${props.environment}`,
        partitionKey: { name: 'groupId', type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        pointInTimeRecovery: true,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
        encryption: dynamodb.TableEncryption.AWS_MANAGED,
      });
    }
    
    // Recovery Plans Table
    if (props.importExistingTables && props.existingTableNames?.recoveryPlans) {
      this.recoveryPlansTable = dynamodb.Table.fromTableAttributes(
        this,
        'RecoveryPlansTable',
        {
          tableName: props.existingTableNames.recoveryPlans,
          globalIndexes: ['ProtectionGroupIndex'],
        }
      );
    } else {
      this.recoveryPlansTable = new dynamodb.Table(this, 'RecoveryPlansTable', {
        tableName: `${props.projectName}-recovery-plans-${props.environment}`,
        partitionKey: { name: 'planId', type: dynamodb.AttributeType.STRING },
        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        pointInTimeRecovery: true,
        removalPolicy: cdk.RemovalPolicy.RETAIN,
        encryption: dynamodb.TableEncryption.AWS_MANAGED,
      });
      
      // Add GSI only for new tables
      (this.recoveryPlansTable as dynamodb.Table).addGlobalSecondaryIndex({
        indexName: 'ProtectionGroupIndex',
        partitionKey: { name: 'protectionGroupId', type: dynamodb.AttributeType.STRING },
        projectionType: dynamodb.ProjectionType.ALL,
      });
    }
    
    // Similar pattern for executions and target accounts tables...
  }
}
```

**Usage:**

```bash
# Create new tables
export IMPORT_EXISTING_TABLES=false
cdk deploy

# Import existing tables
export IMPORT_EXISTING_TABLES=true
cdk deploy
```


## Best Practices

### 1. When to Import vs Create New Tables

**Import Existing Tables When:**
- ✅ Migrating from CloudFormation to CDK
- ✅ Data preservation is critical
- ✅ Sharing tables across multiple stacks
- ✅ Recreating failed stacks
- ✅ Blue/green deployments

**Create New Tables When:**
- ✅ Greenfield deployments
- ✅ Isolated test environments
- ✅ Different table configurations needed
- ✅ No existing data to preserve
- ✅ Complete environment isolation required

### 2. Table Naming Conventions

**Consistent Naming Pattern:**
```
{project-name}-{resource-type}-{environment}

Examples:
- aws-drs-orchestration-protection-groups-test
- aws-drs-orchestration-recovery-plans-prod
- aws-drs-orchestration-executions-dev
```

**Benefits:**
- Easy identification of table ownership
- Clear environment separation
- Predictable import patterns
- Simplified automation

### 3. Backup Strategies Before Migration

**Always Create Backups:**

```bash
# On-demand backup (recommended)
aws dynamodb create-backup \
  --table-name aws-drs-orchestration-protection-groups-test \
  --backup-name pre-migration-$(date +%Y%m%d-%H%M%S)

# Point-in-time recovery (enable if not already)
aws dynamodb update-continuous-backups \
  --table-name aws-drs-orchestration-protection-groups-test \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

**Backup Retention:**
- Keep on-demand backups for 30 days minimum
- Enable point-in-time recovery for production tables
- Document backup ARNs for quick recovery

### 4. IAM Permission Management

**Principle of Least Privilege:**

```typescript
// Grant only necessary permissions
protectionGroupsTable.grantReadData(readOnlyRole);
protectionGroupsTable.grantReadWriteData(adminRole);

// Explicit permissions for fine-grained control
lambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'dynamodb:GetItem',
    'dynamodb:Query',
    'dynamodb:Scan',
  ],
  resources: [
    protectionGroupsTable.tableArn,
    `${protectionGroupsTable.tableArn}/index/*`,
  ],
}));
```

### 5. Testing Import Configuration

**Pre-Deployment Testing:**

```bash
# 1. Synthesize CloudFormation template
cdk synth > template.yaml

# 2. Validate template
aws cloudformation validate-template --template-body file://template.yaml

# 3. Review IAM permissions
grep -A 10 "AWS::IAM::Policy" template.yaml

# 4. Check table references
grep -A 5 "DynamoDB" template.yaml
```

**Post-Deployment Verification:**

```bash
# 1. Verify Lambda can access tables
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

# 2. Check CloudWatch Logs for errors
aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-test --since 5m

# 3. Verify data integrity
aws dynamodb scan \
  --table-name aws-drs-orchestration-protection-groups-test \
  --select COUNT
```


### 6. Handling Table Configuration Drift

**Problem:** Imported tables cannot be modified by CDK (billing mode, encryption, GSIs, etc.)

**Solution 1: Accept Current Configuration**
```typescript
// Import table as-is
const table = dynamodb.Table.fromTableName(this, 'Table', 'existing-table');
// Cannot modify billing mode, encryption, or add GSIs
```

**Solution 2: Migrate to CDK-Managed Table**
```typescript
// 1. Export data from existing table
// 2. Create new CDK-managed table with desired configuration
// 3. Import data into new table
// 4. Update Lambda functions to use new table
// 5. Delete old table
```

**Solution 3: Use AWS Console/CLI for Configuration Changes**
```bash
# Update table configuration outside CDK
aws dynamodb update-table \
  --table-name aws-drs-orchestration-protection-groups-test \
  --billing-mode PAY_PER_REQUEST

# CDK will not detect or revert these changes
```

### 7. Monitoring Imported Tables

**CloudWatch Alarms:**

```typescript
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';

// Create alarms for imported tables
const readThrottleAlarm = new cloudwatch.Alarm(this, 'ReadThrottleAlarm', {
  metric: protectionGroupsTable.metricUserErrors({
    statistic: 'Sum',
    period: cdk.Duration.minutes(5),
  }),
  threshold: 10,
  evaluationPeriods: 2,
  alarmDescription: 'DynamoDB read throttling detected',
});
```

**Note:** Metrics work the same for imported and created tables.

### 8. Documentation Requirements

**Document for Each Imported Table:**
- Original source (CloudFormation stack, manual creation, etc.)
- Table ARN and region
- Billing mode and capacity settings
- Encryption configuration
- GSI names and key schemas
- Point-in-time recovery status
- Backup schedule and retention
- Access patterns and expected load

**Example Documentation:**

```markdown
## Imported DynamoDB Tables

### Protection Groups Table
- **Source:** CloudFormation stack `aws-drs-orchestration-test`
- **ARN:** `arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test`
- **Billing Mode:** PAY_PER_REQUEST
- **Encryption:** AWS_MANAGED
- **GSIs:** None
- **PITR:** Enabled
- **Backup:** Daily at 2 AM UTC
- **Access Pattern:** Read-heavy, ~100 reads/min, ~10 writes/min
```


## Troubleshooting

### Issue 1: Table Not Found

**Error:**
```
ResourceNotFoundException: Requested resource not found: Table: aws-drs-orchestration-protection-groups-test not found
```

**Causes:**
- Table name is incorrect
- Table is in different region
- Table is in different AWS account
- Table was deleted

**Solutions:**

```bash
# 1. Verify table exists
aws dynamodb describe-table \
  --table-name aws-drs-orchestration-protection-groups-test

# 2. List all tables in region
aws dynamodb list-tables

# 3. Check correct region
aws dynamodb list-tables --region us-west-2

# 4. Verify AWS account
aws sts get-caller-identity
```

**Fix in CDK:**
```typescript
// Ensure correct table name
const table = dynamodb.Table.fromTableName(
  this,
  'ProtectionGroupsTable',
  'aws-drs-orchestration-protection-groups-test'  // Verify this name
);
```

### Issue 2: Access Denied / Insufficient Permissions

**Error:**
```
AccessDeniedException: User: arn:aws:sts::123456789012:assumed-role/aws-drs-orchestration-query-handler-test-role/aws-drs-orchestration-query-handler-test is not authorized to perform: dynamodb:GetItem on resource: arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test
```

**Causes:**
- Lambda execution role lacks DynamoDB permissions
- Table resource policy blocks access
- Cross-account permissions not configured

**Solutions:**

```typescript
// 1. Grant explicit permissions
protectionGroupsTable.grantReadWriteData(lambdaRole);

// 2. Or add manual policy
lambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'dynamodb:GetItem',
    'dynamodb:PutItem',
    'dynamodb:UpdateItem',
    'dynamodb:DeleteItem',
    'dynamodb:Query',
    'dynamodb:Scan',
  ],
  resources: [
    'arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test',
    'arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test/index/*',
  ],
}));
```

**Verify Permissions:**
```bash
# Check Lambda execution role
aws iam get-role-policy \
  --role-name aws-drs-orchestration-query-handler-test-role \
  --policy-name DynamoDBAccess

# Test Lambda invocation
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json
```


### Issue 3: GSI Not Accessible

**Error:**
```
ValidationException: The provided key element does not match the schema
```

**Cause:** Lambda is trying to query a GSI that wasn't declared in `fromTableAttributes()`

**Solution:**

```typescript
// Declare all GSIs when importing
const executionsTable = dynamodb.Table.fromTableAttributes(
  this,
  'ExecutionsTable',
  {
    tableName: 'aws-drs-orchestration-executions-test',
    globalIndexes: ['StatusIndex', 'PlanIndex'],  // Must list all GSIs
  }
);

// Grant permissions (automatically includes GSI access)
executionsTable.grantReadWriteData(lambdaRole);
```

**Verify GSI Names:**
```bash
# List all GSIs for a table
aws dynamodb describe-table \
  --table-name aws-drs-orchestration-executions-test \
  --query 'Table.GlobalSecondaryIndexes[].IndexName'
```

### Issue 4: Stack Update Fails with "Resource Already Exists"

**Error:**
```
Resource of type 'AWS::DynamoDB::Table' with identifier 'aws-drs-orchestration-protection-groups-test' already exists
```

**Cause:** Trying to create a table that already exists (not importing it)

**Solution:**

```typescript
// Change from creating new table:
const table = new dynamodb.Table(this, 'ProtectionGroupsTable', {
  tableName: 'aws-drs-orchestration-protection-groups-test',
  // ...
});

// To importing existing table:
const table = dynamodb.Table.fromTableName(
  this,
  'ProtectionGroupsTable',
  'aws-drs-orchestration-protection-groups-test'
);
```

### Issue 5: Table Deleted When Stack is Destroyed

**Error:** Table was deleted even though you wanted to keep it

**Cause:** `removalPolicy` was not set to `RETAIN` before stack deletion

**Prevention:**

```typescript
// Always set RETAIN for production tables
const table = new dynamodb.Table(this, 'ProtectionGroupsTable', {
  tableName: 'aws-drs-orchestration-protection-groups-test',
  // ... other properties ...
  removalPolicy: cdk.RemovalPolicy.RETAIN,  // Critical!
});
```

**Recovery (if table was deleted):**

```bash
# 1. Check if backups exist
aws dynamodb list-backups \
  --table-name aws-drs-orchestration-protection-groups-test

# 2. Restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name aws-drs-orchestration-protection-groups-test \
  --backup-arn arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test/backup/01234567890123-abcdefgh

# 3. Or restore from point-in-time
aws dynamodb restore-table-to-point-in-time \
  --source-table-name aws-drs-orchestration-protection-groups-test \
  --target-table-name aws-drs-orchestration-protection-groups-test-restored \
  --restore-date-time 2025-01-31T12:00:00Z
```


### Issue 6: Cross-Account Access Not Working

**Error:**
```
AccessDeniedException: User is not authorized to perform: dynamodb:GetItem on resource in different account
```

**Cause:** Cross-account permissions not properly configured

**Solution:**

**Step 1: Update Source Account Table Policy**

```bash
# In source account (where table exists)
aws dynamodb update-table \
  --table-name aws-drs-orchestration-protection-groups-test \
  --resource-policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::987654321098:role/aws-drs-orchestration-query-handler-role"
        },
        "Action": [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ],
        "Resource": [
          "arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test",
          "arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test/index/*"
        ]
      }
    ]
  }'
```

**Step 2: Update Target Account IAM Role**

```typescript
// In target account CDK stack
lambdaRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'dynamodb:GetItem',
    'dynamodb:Query',
    'dynamodb:Scan',
  ],
  resources: [
    'arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test',
    'arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test/index/*',
  ],
}));
```

### Issue 7: Environment Variable Mismatch

**Error:** Lambda function cannot find table (no error, just empty results)

**Cause:** Environment variable points to wrong table name

**Solution:**

```typescript
// Ensure environment variable matches imported table name
const queryHandler = new lambda.Function(this, 'QueryHandler', {
  // ... other properties ...
  environment: {
    PROTECTION_GROUPS_TABLE: protectionGroupsTable.tableName,  // Use .tableName property
    RECOVERY_PLANS_TABLE: recoveryPlansTable.tableName,
    EXECUTIONS_TABLE: executionsTable.tableName,
    TARGET_ACCOUNTS_TABLE: targetAccountsTable.tableName,
  },
});
```

**Verify Environment Variables:**
```bash
# Check Lambda environment variables
aws lambda get-function-configuration \
  --function-name aws-drs-orchestration-query-handler-test \
  --query 'Environment.Variables'
```


## Advanced Scenarios

### Scenario 1: Gradual Migration with Dual-Stack

Deploy both old and new stacks simultaneously, gradually shifting traffic:

```typescript
export class DualStackMigration extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);
    
    // Import tables from old stack
    const oldProtectionGroupsTable = dynamodb.Table.fromTableName(
      this,
      'OldProtectionGroupsTable',
      'aws-drs-orchestration-protection-groups-test'
    );
    
    // Create new Lambda functions pointing to old tables
    const newQueryHandler = new lambda.Function(this, 'NewQueryHandler', {
      functionName: 'aws-drs-orchestration-query-handler-test-v2',
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      environment: {
        PROTECTION_GROUPS_TABLE: oldProtectionGroupsTable.tableName,
      },
    });
    
    oldProtectionGroupsTable.grantReadWriteData(newQueryHandler);
    
    // Create weighted alias for gradual traffic shift
    const version = newQueryHandler.currentVersion;
    const alias = new lambda.Alias(this, 'QueryHandlerAlias', {
      aliasName: 'live',
      version: version,
      additionalVersions: [
        {
          version: lambda.Version.fromVersionArn(
            this,
            'OldVersion',
            'arn:aws:lambda:us-east-1:123456789012:function:aws-drs-orchestration-query-handler-test:1'
          ),
          weight: 0.9,  // 90% to old version
        },
      ],
    });
  }
}
```

**Migration Steps:**
1. Deploy new stack with 10% traffic
2. Monitor for errors
3. Gradually increase traffic: 25%, 50%, 75%, 100%
4. Delete old stack

### Scenario 2: Multi-Region Table Import

Import tables from multiple regions for disaster recovery:

```typescript
export class MultiRegionImportStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);
    
    // Primary region table
    const primaryTable = dynamodb.Table.fromTableArn(
      this,
      'PrimaryTable',
      'arn:aws:dynamodb:us-east-1:123456789012:table/aws-drs-orchestration-protection-groups-test'
    );
    
    // Replica region table (DynamoDB Global Tables)
    const replicaTable = dynamodb.Table.fromTableArn(
      this,
      'ReplicaTable',
      'arn:aws:dynamodb:us-west-2:123456789012:table/aws-drs-orchestration-protection-groups-test'
    );
    
    // Lambda function with failover logic
    const queryHandler = new lambda.Function(this, 'QueryHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      environment: {
        PRIMARY_TABLE: primaryTable.tableName,
        PRIMARY_REGION: 'us-east-1',
        REPLICA_TABLE: replicaTable.tableName,
        REPLICA_REGION: 'us-west-2',
      },
    });
    
    primaryTable.grantReadWriteData(queryHandler);
    replicaTable.grantReadWriteData(queryHandler);
  }
}
```


### Scenario 3: Shared Data Layer Pattern

Create a separate data stack that multiple compute stacks import:

**Data Stack:**
```typescript
// lib/data-stack.ts
export class DataStack extends cdk.Stack {
  public readonly protectionGroupsTable: dynamodb.Table;
  public readonly recoveryPlansTable: dynamodb.Table;
  public readonly executionsTable: dynamodb.Table;
  public readonly targetAccountsTable: dynamodb.Table;
  
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);
    
    // Create all DynamoDB tables
    this.protectionGroupsTable = new dynamodb.Table(this, 'ProtectionGroupsTable', {
      tableName: 'aws-drs-orchestration-protection-groups-shared',
      partitionKey: { name: 'groupId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
    
    // ... create other tables ...
    
    // Export table names for other stacks
    new cdk.CfnOutput(this, 'ProtectionGroupsTableName', {
      value: this.protectionGroupsTable.tableName,
      exportName: 'DROrchestration-ProtectionGroupsTable',
    });
  }
}
```

**Compute Stack (Dev):**
```typescript
// lib/compute-stack-dev.ts
export class ComputeStackDev extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);
    
    // Import tables from data stack
    const protectionGroupsTable = dynamodb.Table.fromTableName(
      this,
      'ProtectionGroupsTable',
      cdk.Fn.importValue('DROrchestration-ProtectionGroupsTable')
    );
    
    // Create dev Lambda functions
    const queryHandler = new lambda.Function(this, 'QueryHandlerDev', {
      functionName: 'aws-drs-orchestration-query-handler-dev',
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      environment: {
        PROTECTION_GROUPS_TABLE: protectionGroupsTable.tableName,
      },
    });
    
    protectionGroupsTable.grantReadWriteData(queryHandler);
  }
}
```

**Compute Stack (Test):**
```typescript
// lib/compute-stack-test.ts
export class ComputeStackTest extends cdk.Stack {
  constructor(scope: Construct, id: string, props: cdk.StackProps) {
    super(scope, id, props);
    
    // Import same tables from data stack
    const protectionGroupsTable = dynamodb.Table.fromTableName(
      this,
      'ProtectionGroupsTable',
      cdk.Fn.importValue('DROrchestration-ProtectionGroupsTable')
    );
    
    // Create test Lambda functions
    const queryHandler = new lambda.Function(this, 'QueryHandlerTest', {
      functionName: 'aws-drs-orchestration-query-handler-test',
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      environment: {
        PROTECTION_GROUPS_TABLE: protectionGroupsTable.tableName,
      },
    });
    
    protectionGroupsTable.grantReadWriteData(queryHandler);
  }
}
```

**Deployment:**
```bash
# Deploy data stack once
cdk deploy DataStack

# Deploy multiple compute stacks
cdk deploy ComputeStackDev
cdk deploy ComputeStackTest
cdk deploy ComputeStackStaging
```

**Benefits:**
- Single source of truth for data
- Independent compute deployments
- Cost savings (one set of tables)
- Simplified data management


## Quick Reference

### Import Methods Comparison

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| `fromTableName()` | Same account/region | Simple, minimal code | No GSI info, no cross-account |
| `fromTableArn()` | Cross-account/region | Works across boundaries | No GSI info |
| `fromTableAttributes()` | Tables with GSIs | Full permission control | More verbose |

### Common Commands

```bash
# List existing tables
aws dynamodb list-tables

# Get table details
aws dynamodb describe-table --table-name TABLE_NAME

# Create backup
aws dynamodb create-backup --table-name TABLE_NAME --backup-name BACKUP_NAME

# List backups
aws dynamodb list-backups --table-name TABLE_NAME

# Restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name NEW_TABLE_NAME \
  --backup-arn BACKUP_ARN

# Update removal policy (CloudFormation)
aws cloudformation update-stack \
  --stack-name STACK_NAME \
  --template-body file://template.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Deploy CDK with import
export IMPORT_EXISTING_TABLES=true
cdk deploy

# Verify Lambda can access table
aws lambda invoke \
  --function-name FUNCTION_NAME \
  --payload '{"operation":"list_protection_groups"}' \
  response.json
```

### CDK Code Snippets

**Simple Import:**
```typescript
const table = dynamodb.Table.fromTableName(this, 'Table', 'table-name');
```

**Import with GSI:**
```typescript
const table = dynamodb.Table.fromTableAttributes(this, 'Table', {
  tableName: 'table-name',
  globalIndexes: ['Index1', 'Index2'],
});
```

**Cross-Account Import:**
```typescript
const table = dynamodb.Table.fromTableArn(this, 'Table', 'arn:aws:dynamodb:...');
```

**Conditional Import:**
```typescript
const table = props.import
  ? dynamodb.Table.fromTableName(this, 'Table', props.tableName)
  : new dynamodb.Table(this, 'Table', { /* config */ });
```


## Checklist: Pre-Migration

Before migrating from CloudFormation to CDK with table import:

- [ ] **Backup all tables** with on-demand backups
- [ ] **Enable point-in-time recovery** on production tables
- [ ] **Document table ARNs** and configuration
- [ ] **Verify table names** match expected format
- [ ] **Check GSI names** for tables with indexes
- [ ] **Update CloudFormation templates** with `DeletionPolicy: Retain`
- [ ] **Deploy CloudFormation update** to set retention policy
- [ ] **Test CDK stack** in dev environment first
- [ ] **Verify IAM permissions** for Lambda functions
- [ ] **Create rollback plan** with documented steps
- [ ] **Schedule maintenance window** (if needed)
- [ ] **Notify team** of migration timeline

## Checklist: Post-Migration

After completing migration:

- [ ] **Verify Lambda functions** can access tables
- [ ] **Check CloudWatch Logs** for errors
- [ ] **Run integration tests** to validate functionality
- [ ] **Monitor CloudWatch metrics** for anomalies
- [ ] **Verify data integrity** with sample queries
- [ ] **Test all CRUD operations** (create, read, update, delete)
- [ ] **Confirm GSI queries** work correctly
- [ ] **Delete old CloudFormation stack** (if applicable)
- [ ] **Update documentation** with new stack details
- [ ] **Archive backups** with retention policy
- [ ] **Document lessons learned** for future migrations

## Additional Resources

### AWS Documentation

- [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/)
- [CDK DynamoDB Module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_dynamodb-readme.html)
- [DynamoDB Backup and Restore](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/BackupRestore.html)
- [DynamoDB Global Tables](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html)

### DR Orchestration Documentation

- [CDK Example README](../README.md)
- [Python Examples](../../python/README.md)
- [Bash Examples](../../bash/README.md)
- [API Reference](../../../docs/api-reference/QUERY_HANDLER_API.md)
- [Migration Guide](../../../docs/guides/MIGRATION_GUIDE.md)

### CDK Resources

- [CDK Workshop](https://cdkworkshop.com/)
- [CDK Patterns](https://cdkpatterns.com/)
- [CDK Best Practices](https://docs.aws.amazon.com/cdk/latest/guide/best-practices.html)

## Summary

Importing existing DynamoDB tables into CDK enables:

✅ **Zero-downtime migrations** from CloudFormation to CDK
✅ **Data preservation** during infrastructure changes
✅ **Multi-stack architectures** with shared data layers
✅ **Blue/green deployments** with minimal risk
✅ **Cost optimization** through table sharing

**Key Takeaways:**

1. **Always backup** before migration
2. **Set `removalPolicy: RETAIN`** before deleting stacks
3. **Use `fromTableName()`** for simple same-account imports
4. **Use `fromTableAttributes()`** for tables with GSIs
5. **Test thoroughly** in dev before production migration
6. **Document everything** for future reference

For questions or issues, refer to the troubleshooting section or consult the AWS CDK documentation.

---

**Last Updated:** January 2025  
**Version:** 1.0  
**Maintainer:** DR Orchestration Platform Team

