# IAM Role Integration Guide for CDK

## Overview

This guide explains how to integrate the AWS CDK DR Orchestration stack with **existing IAM roles** from a previous deployment. This is useful when:

- Migrating from CloudFormation to CDK while preserving IAM roles
- Sharing IAM roles across multiple stacks
- Recreating infrastructure without recreating roles
- Implementing blue/green deployment strategies
- Maintaining consistent permissions across environments

## Table of Contents

1. [Why Import Existing Roles?](#why-import-existing-roles)
2. [Use Cases](#use-cases)
3. [CDK Import Patterns](#cdk-import-patterns)
4. [Migration Strategy](#migration-strategy)
5. [Code Examples](#code-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Scenarios](#advanced-scenarios)

## Why Import Existing Roles?

### Benefits of Importing Roles

**Permission Continuity:**
- Maintain existing trust relationships
- Preserve attached policies and permissions
- Avoid permission gaps during migration
- Keep audit trail intact

**Operational Continuity:**
- Zero downtime during infrastructure changes
- No service interruption for running operations
- Preserve cross-account access configurations
- Maintain compliance posture

**Simplified Management:**
- Centralized IAM role management
- Reuse roles across multiple stacks
- Reduce IAM role proliferation
- Simplify permission auditing

**Flexibility:**
- Decouple IAM layer from compute layer
- Enable independent stack lifecycle management
- Support multi-stack architectures
- Facilitate testing and validation


## Use Cases

### 1. CloudFormation to CDK Migration

**Scenario:** You have an existing CloudFormation deployment with an OrchestrationRole that has been carefully configured with all necessary permissions. You want to migrate to CDK without recreating the role.

**Solution:** Import the existing OrchestrationRole into CDK stack, update Lambda functions to use the imported role, then delete old CloudFormation stack.

**Timeline:** 1-2 hours with zero permission disruption

### 2. Multi-Stack Architecture

**Scenario:** You want to deploy multiple DR orchestration stacks (dev, test, staging) that share the same OrchestrationRole for centralized permission management.

**Solution:** Create a separate "IAM stack" with the OrchestrationRole, then import that role into multiple "compute stacks" with Lambda functions.

**Benefits:** Centralized permissions, independent compute deployments, simplified auditing

### 3. Stack Recreation

**Scenario:** Your CDK stack is in a failed state and needs to be deleted and recreated, but you cannot lose the IAM role's trust relationships and attached policies.

**Solution:** Set `removalPolicy: RETAIN` on the role before deletion, then import the retained role into the new stack.

**Recovery Time:** 10-15 minutes

### 4. Blue/Green Deployment

**Scenario:** You want to deploy a new version of your DR orchestration platform alongside the existing version for testing, using the same IAM role.

**Solution:** Deploy "green" stack that imports the OrchestrationRole from "blue" stack, test thoroughly, then switch traffic and delete "blue" stack.

**Risk Mitigation:** Full rollback capability, zero permission loss



## CDK Import Patterns

### Pattern 1: Import by Role Name

The simplest pattern for importing existing roles:

```typescript
import * as iam from 'aws-cdk-lib/aws-iam';

// Import existing role by name
const orchestrationRole = iam.Role.fromRoleName(
  this,
  'OrchestrationRole',
  'hrp-drs-tech-adapter-orchestration-role-test'
);

// Use imported role for Lambda functions
const queryHandler = new lambda.Function(this, 'QueryHandler', {
  runtime: lambda.Runtime.PYTHON_3_11,
  code: lambda.Code.fromAsset('../../lambda/query-handler'),
  handler: 'index.lambda_handler',
  role: orchestrationRole,
});
```

**When to use:**
- Same AWS account
- Same AWS region
- Role name is known

**Limitations:**
- Cannot modify role configuration (trust policy, permissions)
- Cannot add/remove managed policies
- Cannot change removal policy

### Pattern 2: Import by Role ARN

For cross-account or cross-region scenarios:

```typescript
// Import role by ARN
const orchestrationRole = iam.Role.fromRoleArn(
  this,
  'OrchestrationRole',
  'arn:aws:iam::123456789012:role/hrp-drs-tech-adapter-orchestration-role-test'
);

// Use imported role
const executionHandler = new lambda.Function(this, 'ExecutionHandler', {
  runtime: lambda.Runtime.PYTHON_3_11,
  code: lambda.Code.fromAsset('../../lambda/execution-handler'),
  handler: 'index.lambda_handler',
  role: orchestrationRole,
});
```

**When to use:**
- Cross-account access
- Cross-region deployments
- Full ARN is available

**Benefits:**
- Works across account boundaries
- Explicit resource identification
- Supports cross-region replication



### Pattern 3: Import with Attributes

For roles with specific configurations:

```typescript
// Import role with additional attributes
const orchestrationRole = iam.Role.fromRoleArn(
  this,
  'OrchestrationRole',
  'arn:aws:iam::123456789012:role/hrp-drs-tech-adapter-orchestration-role-test',
  {
    mutable: false,  // Prevent CDK from modifying the role
    addGrantsToResources: true,  // Allow grant methods to work
  }
);

// Grant additional permissions (adds to role's inline policies)
protectionGroupsTable.grantReadWriteData(orchestrationRole);

// Use role for Lambda
const dataManagementHandler = new lambda.Function(this, 'DataManagementHandler', {
  runtime: lambda.Runtime.PYTHON_3_11,
  code: lambda.Code.fromAsset('../../lambda/data-management-handler'),
  handler: 'index.lambda_handler',
  role: orchestrationRole,
});
```

**When to use:**
- Need to add permissions to imported role
- Want to use CDK grant methods
- Role requires additional inline policies

**Benefits:**
- Full permission management
- CDK grant method support
- Flexible policy attachment

### Pattern 4: Conditional Import vs Create

Support both new deployments and imports:

```typescript
interface DROrchestrationStackProps extends cdk.StackProps {
  projectName: string;
  environment: string;
  importExistingRole?: boolean;
  existingRoleName?: string;
}

export class DROrchestrationStack extends cdk.Stack {
  public readonly orchestrationRole: iam.IRole;
  
  constructor(scope: Construct, id: string, props: DROrchestrationStackProps) {
    super(scope, id, props);
    
    if (props.importExistingRole && props.existingRoleName) {
      // Import existing role
      this.orchestrationRole = iam.Role.fromRoleName(
        this,
        'OrchestrationRole',
        props.existingRoleName
      );
    } else {
      // Create new role
      this.orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
        roleName: `${props.projectName}-orchestration-role-${props.environment}`,
        assumedBy: new iam.CompositePrincipal(
          new iam.ServicePrincipal('lambda.amazonaws.com'),
          new iam.ServicePrincipal('states.amazonaws.com')
        ),
        managedPolicies: [
          iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        ],
        removalPolicy: cdk.RemovalPolicy.RETAIN,
      });
      
      // Add DRS permissions
      this.orchestrationRole.addToPolicy(new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'drs:DescribeSourceServers',
          'drs:StartRecovery',
          'drs:TerminateRecoveryInstances',
        ],
        resources: ['*'],
      }));
    }
  }
}
```

**When to use:**
- Supporting both greenfield and migration scenarios
- Gradual migration approach
- Testing with different configurations



## Migration Strategy

### Step-by-Step Migration from CloudFormation to CDK

#### Phase 1: Preparation (15 minutes)

**1. Identify Existing IAM Role**

```bash
# List all IAM roles in your stack
aws cloudformation describe-stack-resources \
  --stack-name hrp-drs-tech-adapter-test \
  --query 'StackResources[?ResourceType==`AWS::IAM::Role`].[LogicalResourceId,PhysicalResourceId]' \
  --output table

# Example output:
# OrchestrationRole    hrp-drs-tech-adapter-orchestration-role-test
```

**2. Document Role Configuration**

```bash
# Get role details
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --query 'Role.{Name:RoleName,ARN:Arn,AssumeRolePolicy:AssumeRolePolicyDocument}' \
  --output json

# List attached managed policies
aws iam list-attached-role-policies \
  --role-name hrp-drs-tech-adapter-orchestration-role-test

# List inline policies
aws iam list-role-policies \
  --role-name hrp-drs-tech-adapter-orchestration-role-test

# Get inline policy details
aws iam get-role-policy \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --policy-name DRSOrchestrationPolicy

# Save role ARN for CDK import
export ORCHESTRATION_ROLE_ARN="arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test"
export ORCHESTRATION_ROLE_NAME="hrp-drs-tech-adapter-orchestration-role-test"
```

**3. Document Trust Relationships**

```bash
# Get trust policy (AssumeRolePolicyDocument)
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --query 'Role.AssumeRolePolicyDocument' \
  --output json > trust-policy.json

cat trust-policy.json | jq .
```

**4. Backup Role Configuration (Recommended)**

```bash
# Export complete role configuration
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  > role-backup-$(date +%Y%m%d).json

# Export all policies
aws iam list-attached-role-policies \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  > attached-policies-backup-$(date +%Y%m%d).json

aws iam list-role-policies \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  > inline-policies-backup-$(date +%Y%m%d).json
```



#### Phase 2: Update CloudFormation Stack (10 minutes)

**1. Set Removal Policy to RETAIN**

Before deleting the CloudFormation stack, update the role's removal policy to prevent deletion:

```bash
# Update CloudFormation template to set DeletionPolicy: Retain
# Edit cfn/iam-stack.yaml:

Resources:
  OrchestrationRole:
    Type: AWS::IAM::Role
    DeletionPolicy: Retain  # Add this line
    UpdateReplacePolicy: Retain  # Add this line
    Properties:
      RoleName: hrp-drs-tech-adapter-orchestration-role-test
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - lambda.amazonaws.com
                - states.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: DRSOrchestrationPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - drs:DescribeSourceServers
                  - drs:StartRecovery
                  - drs:TerminateRecoveryInstances
                Resource: '*'
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
  --query 'StackResources[?ResourceType==`AWS::IAM::Role`].[LogicalResourceId,PhysicalResourceId]'
```



#### Phase 3: Deploy CDK Stack with Imported Role (20 minutes)

**1. Create CDK Stack with Import Configuration**

Create a new file `examples/cdk/lib/dr-orchestration-import-stack.ts`:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import { DROrchestrationStack, DROrchestrationStackProps } from './dr-orchestration-stack';

/**
 * Extended stack that imports existing IAM role
 */
export class DROrchestrationImportStack extends DROrchestrationStack {
  constructor(scope: Construct, id: string, props: DROrchestrationStackProps & {
    existingRoleName: string;
  }) {
    // Import existing role before calling parent constructor
    const importedRole = iam.Role.fromRoleName(
      scope,
      'ImportedOrchestrationRole',
      props.existingRoleName
    );
    
    // Call parent constructor
    super(scope, id, props);
    
    // Override the orchestrationRole property with imported role
    (this as any).orchestrationRole = importedRole;
    
    // Update Lambda functions to use imported role
    this.updateLambdaFunctionsWithRole(importedRole);
  }
  
  private updateLambdaFunctionsWithRole(role: iam.IRole): void {
    // Lambda functions are already created by parent constructor
    // They will use the imported role automatically
    // No additional action needed - CDK handles this
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
import { DROrchestrationStack } from '../lib/dr-orchestration-stack';

const app = new cdk.App();

const environment = process.env.ENVIRONMENT || 'dev';
const projectName = process.env.PROJECT_NAME || 'hrp-drs-tech-adapter';
const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com';

// Import existing role from CloudFormation deployment
const importExistingRole = process.env.IMPORT_EXISTING_ROLE === 'true';
const existingRoleName = process.env.EXISTING_ROLE_NAME;

if (importExistingRole && existingRoleName) {
  new DROrchestrationImportStack(app, `${projectName}-${environment}`, {
    projectName,
    environment,
    adminEmail,
    existingRoleName,
    env: {
      account: process.env.CDK_DEFAULT_ACCOUNT,
      region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
    },
  });
} else {
  // Use standard stack that creates new role
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
export IMPORT_EXISTING_ROLE=true
export EXISTING_ROLE_NAME=hrp-drs-tech-adapter-orchestration-role-test

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

# Verify Lambda functions use imported role
aws lambda get-function \
  --function-name hrp-drs-tech-adapter-query-handler-test \
  --query 'Configuration.Role'

# Should output: arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test

# Test Lambda function invocation
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

cat response.json | jq .
```



#### Phase 4: Delete Old CloudFormation Stack (10 minutes)

**1. Verify CDK Stack is Working**

```bash
# Test all Lambda functions
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

aws lambda invoke \
  --function-name hrp-drs-tech-adapter-execution-handler-test \
  --payload '{"operation":"list_executions"}' \
  response.json

aws lambda invoke \
  --function-name hrp-drs-tech-adapter-data-management-handler-test \
  --payload '{"operation":"get_target_accounts"}' \
  response.json

# Verify all functions return successful responses
cat response.json | jq .
```

**2. Verify Role Permissions**

```bash
# Check role is still attached to Lambda functions
aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `hrp-drs-tech-adapter`)].{Name:FunctionName,Role:Role}' \
  --output table

# All functions should show the same role ARN
```

**3. Delete Old CloudFormation Stack**

```bash
# Delete CloudFormation stack (role will be retained)
aws cloudformation delete-stack \
  --stack-name hrp-drs-tech-adapter-test-old

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete \
  --stack-name hrp-drs-tech-adapter-test-old
```

**4. Verify Role Still Exists**

```bash
# Verify role was not deleted
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test

# Should return role details (not "NoSuchEntity" error)
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
# Test Lambda functions
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

# Verify role is still functional
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test

# Check Lambda functions use correct role
aws lambda get-function \
  --function-name hrp-drs-tech-adapter-query-handler-test \
  --query 'Configuration.Role'
```

**3. Document Rollback Reason**

Create incident report documenting:
- What went wrong
- When rollback was initiated
- Role configuration verification results
- Lessons learned for next attempt

**4. Troubleshoot Before Retry**

Common rollback reasons:
- **Permission Issues**: Role missing required permissions
- **Trust Policy Issues**: Role cannot be assumed by Lambda/Step Functions
- **Cross-Account Issues**: Role assumption failing for target accounts
- **Policy Limits**: Inline policy size limits exceeded



## Code Examples

### Example 1: Simple Role Import

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class SimpleImportStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import existing role by name
    const orchestrationRole = iam.Role.fromRoleName(
      this,
      'OrchestrationRole',
      'hrp-drs-tech-adapter-orchestration-role-test'
    );
    
    // Create Lambda function using imported role
    const queryHandler = new lambda.Function(this, 'QueryHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      role: orchestrationRole,
      environment: {
        PROTECTION_GROUPS_TABLE: 'hrp-drs-tech-adapter-protection-groups-test',
        RECOVERY_PLANS_TABLE: 'hrp-drs-tech-adapter-recovery-plans-test',
      },
    });
    
    // Output role ARN for verification
    new cdk.CfnOutput(this, 'RoleArn', {
      value: orchestrationRole.roleArn,
      description: 'Imported OrchestrationRole ARN',
    });
  }
}
```

### Example 2: Import with Additional Permissions

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

export class ImportWithPermissionsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import existing role with mutable flag
    const orchestrationRole = iam.Role.fromRoleArn(
      this,
      'OrchestrationRole',
      'arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test',
      {
        mutable: true,  // Allow CDK to add inline policies
        addGrantsToResources: true,  // Enable grant methods
      }
    );
    
    // Import existing DynamoDB table
    const protectionGroupsTable = dynamodb.Table.fromTableName(
      this,
      'ProtectionGroupsTable',
      'hrp-drs-tech-adapter-protection-groups-test'
    );
    
    // Grant additional permissions using CDK grant methods
    // This adds an inline policy to the role
    protectionGroupsTable.grantReadWriteData(orchestrationRole);
    
    // Create Lambda function
    const dataManagementHandler = new lambda.Function(this, 'DataManagementHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/data-management-handler'),
      handler: 'index.lambda_handler',
      role: orchestrationRole,
      environment: {
        PROTECTION_GROUPS_TABLE: protectionGroupsTable.tableName,
      },
    });
  }
}
```



### Example 3: Cross-Account Role Import

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class CrossAccountImportStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import role from different account by ARN
    const orchestrationRole = iam.Role.fromRoleArn(
      this,
      'OrchestrationRole',
      'arn:aws:iam::123456789012:role/hrp-drs-tech-adapter-orchestration-role-test'
    );
    
    // Create Lambda execution role with cross-account assume role permissions
    const lambdaRole = new iam.Role(this, 'LambdaRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    
    // Add permission to assume the cross-account orchestration role
    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['sts:AssumeRole'],
      resources: [orchestrationRole.roleArn],
    }));
    
    // Create Lambda function
    const queryHandler = new lambda.Function(this, 'QueryHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      role: lambdaRole,
      environment: {
        ORCHESTRATION_ROLE_ARN: orchestrationRole.roleArn,
        TARGET_ACCOUNT_ID: '123456789012',
      },
    });
  }
}
```

**Note:** For cross-account access, you also need to update the OrchestrationRole's trust policy in the source account to allow assumption from the Lambda execution role.

**Trust Policy Update (in source account):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::987654321098:role/LambdaRole"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }
  ]
}
```



### Example 4: Conditional Import vs Create

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export interface FlexibleStackProps extends cdk.StackProps {
  projectName: string;
  environment: string;
  importExistingRole?: boolean;
  existingRoleName?: string;
}

export class FlexibleStack extends cdk.Stack {
  public readonly orchestrationRole: iam.IRole;
  public readonly queryHandler: lambda.Function;
  public readonly executionHandler: lambda.Function;
  
  constructor(scope: Construct, id: string, props: FlexibleStackProps) {
    super(scope, id, props);
    
    // Orchestration Role - Import or Create
    if (props.importExistingRole && props.existingRoleName) {
      // Import existing role
      this.orchestrationRole = iam.Role.fromRoleName(
        this,
        'OrchestrationRole',
        props.existingRoleName
      );
    } else {
      // Create new role
      this.orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
        roleName: `${props.projectName}-orchestration-role-${props.environment}`,
        assumedBy: new iam.CompositePrincipal(
          new iam.ServicePrincipal('lambda.amazonaws.com'),
          new iam.ServicePrincipal('states.amazonaws.com')
        ),
        managedPolicies: [
          iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        ],
        removalPolicy: cdk.RemovalPolicy.RETAIN,
        description: 'Unified role for DR Orchestration Lambda functions and Step Functions',
      });
      
      // Add DRS permissions
      this.orchestrationRole.addToPolicy(new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'drs:DescribeSourceServers',
          'drs:DescribeRecoverySnapshots',
          'drs:DescribeRecoveryInstances',
          'drs:DescribeJobs',
          'drs:StartRecovery',
          'drs:TerminateRecoveryInstances',
        ],
        resources: ['*'],
      }));
      
      // Add DynamoDB permissions
      this.orchestrationRole.addToPolicy(new iam.PolicyStatement({
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
          `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.projectName}-*`,
        ],
      }));
      
      // Add Step Functions permissions
      this.orchestrationRole.addToPolicy(new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'states:StartExecution',
          'states:DescribeExecution',
          'states:ListExecutions',
        ],
        resources: [
          `arn:aws:states:${this.region}:${this.account}:stateMachine:${props.projectName}-*`,
        ],
      }));
    }
    
    // Create Lambda functions using the role
    this.queryHandler = new lambda.Function(this, 'QueryHandler', {
      functionName: `${props.projectName}-query-handler-${props.environment}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      role: this.orchestrationRole,
    });
    
    this.executionHandler = new lambda.Function(this, 'ExecutionHandler', {
      functionName: `${props.projectName}-execution-handler-${props.environment}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/execution-handler'),
      handler: 'index.lambda_handler',
      role: this.orchestrationRole,
    });
    
    // Output role information
    new cdk.CfnOutput(this, 'OrchestrationRoleArn', {
      value: this.orchestrationRole.roleArn,
      description: 'OrchestrationRole ARN (imported or created)',
    });
  }
}
```

**Usage:**

```bash
# Create new role
export IMPORT_EXISTING_ROLE=false
cdk deploy

# Import existing role
export IMPORT_EXISTING_ROLE=true
export EXISTING_ROLE_NAME=hrp-drs-tech-adapter-orchestration-role-test
cdk deploy
```



### Example 5: Role with Managed Policy Attachments

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class ManagedPolicyStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import existing role
    const orchestrationRole = iam.Role.fromRoleArn(
      this,
      'OrchestrationRole',
      'arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test',
      {
        mutable: true,
      }
    );
    
    // Attach additional AWS managed policies
    // Note: This creates an inline policy that references the managed policy
    orchestrationRole.addManagedPolicy(
      iam.ManagedPolicy.fromAwsManagedPolicyName('CloudWatchLogsFullAccess')
    );
    
    // Create custom managed policy
    const customPolicy = new iam.ManagedPolicy(this, 'CustomDRSPolicy', {
      managedPolicyName: 'DRSOrchestrationCustomPolicy',
      description: 'Custom policy for DRS orchestration operations',
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            'ec2:DescribeInstances',
            'ec2:DescribeInstanceStatus',
            'ec2:CreateTags',
            'ec2:TerminateInstances',
          ],
          resources: ['*'],
        }),
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            'sns:Publish',
          ],
          resources: [
            `arn:aws:sns:${this.region}:${this.account}:hrp-drs-tech-adapter-*`,
          ],
        }),
      ],
    });
    
    // Attach custom managed policy to imported role
    orchestrationRole.addManagedPolicy(customPolicy);
    
    // Create Lambda function
    const executionHandler = new lambda.Function(this, 'ExecutionHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/execution-handler'),
      handler: 'index.lambda_handler',
      role: orchestrationRole,
    });
  }
}
```



### Example 6: Shared IAM Role Pattern

Create a separate IAM stack that multiple compute stacks import:

**IAM Stack:**
```typescript
// lib/iam-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export interface IAMStackProps extends cdk.StackProps {
  projectName: string;
  environment: string;
}

export class IAMStack extends cdk.Stack {
  public readonly orchestrationRole: iam.Role;
  
  constructor(scope: Construct, id: string, props: IAMStackProps) {
    super(scope, id, props);
    
    // Create OrchestrationRole
    this.orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
      roleName: `${props.projectName}-orchestration-role-${props.environment}`,
      assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal('lambda.amazonaws.com'),
        new iam.ServicePrincipal('states.amazonaws.com')
      ),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
    
    // Add comprehensive DRS permissions
    this.orchestrationRole.addToPolicy(new iam.PolicyStatement({
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
        'drs:TagResource',
        'drs:UntagResource',
        'drs:ListTagsForResource',
      ],
      resources: ['*'],
    }));
    
    // Add EC2 permissions
    this.orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'ec2:DescribeInstances',
        'ec2:DescribeInstanceStatus',
        'ec2:CreateTags',
        'ec2:TerminateInstances',
      ],
      resources: ['*'],
    }));
    
    // Add DynamoDB permissions
    this.orchestrationRole.addToPolicy(new iam.PolicyStatement({
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
        `arn:aws:dynamodb:${this.region}:${this.account}:table/${props.projectName}-*`,
      ],
    }));
    
    // Add Step Functions permissions
    this.orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'states:StartExecution',
        'states:DescribeExecution',
        'states:ListExecutions',
      ],
      resources: [
        `arn:aws:states:${this.region}:${this.account}:stateMachine:${props.projectName}-*`,
      ],
    }));
    
    // Add STS AssumeRole for cross-account operations
    this.orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['sts:AssumeRole'],
      resources: [
        `arn:aws:iam::*:role/${props.projectName}-cross-account-role-*`,
        'arn:aws:iam::*:role/DRSOrchestrationRole',
      ],
    }));
    
    // Export role ARN for other stacks
    new cdk.CfnOutput(this, 'OrchestrationRoleArn', {
      value: this.orchestrationRole.roleArn,
      exportName: `${props.projectName}-orchestration-role-arn-${props.environment}`,
    });
    
    new cdk.CfnOutput(this, 'OrchestrationRoleName', {
      value: this.orchestrationRole.roleName,
      exportName: `${props.projectName}-orchestration-role-name-${props.environment}`,
    });
  }
}
```

**Compute Stack:**
```typescript
// lib/compute-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export interface ComputeStackProps extends cdk.StackProps {
  projectName: string;
  environment: string;
}

export class ComputeStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);
    
    // Import OrchestrationRole from IAM stack
    const orchestrationRole = iam.Role.fromRoleArn(
      this,
      'OrchestrationRole',
      cdk.Fn.importValue(`${props.projectName}-orchestration-role-arn-${props.environment}`)
    );
    
    // Create Lambda functions using imported role
    const queryHandler = new lambda.Function(this, 'QueryHandler', {
      functionName: `${props.projectName}-query-handler-${props.environment}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/query-handler'),
      handler: 'index.lambda_handler',
      role: orchestrationRole,
    });
    
    const executionHandler = new lambda.Function(this, 'ExecutionHandler', {
      functionName: `${props.projectName}-execution-handler-${props.environment}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/execution-handler'),
      handler: 'index.lambda_handler',
      role: orchestrationRole,
    });
    
    const dataManagementHandler = new lambda.Function(this, 'DataManagementHandler', {
      functionName: `${props.projectName}-data-management-handler-${props.environment}`,
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/data-management-handler'),
      handler: 'index.lambda_handler',
      role: orchestrationRole,
    });
  }
}
```

**Deployment:**
```bash
# Deploy IAM stack once
cdk deploy IAMStack

# Deploy compute stack (can be deployed multiple times)
cdk deploy ComputeStack

# Benefits:
# - Single IAM role for all Lambda functions
# - Independent compute stack deployments
# - Centralized permission management
# - Simplified auditing
```



## Best Practices

### 1. When to Import vs Create New Roles

**Import Existing Roles When:**
- ✅ Migrating from CloudFormation to CDK
- ✅ Permission continuity is critical
- ✅ Sharing roles across multiple stacks
- ✅ Recreating failed stacks
- ✅ Blue/green deployments
- ✅ Trust relationships must be preserved

**Create New Roles When:**
- ✅ Greenfield deployments
- ✅ Isolated test environments
- ✅ Different permission requirements
- ✅ No existing roles to preserve
- ✅ Complete environment isolation required

### 2. Role Naming Conventions

**Consistent Naming Pattern:**
```
{project-name}-{role-purpose}-{environment}

Examples:
- hrp-drs-tech-adapter-orchestration-role-test
- hrp-drs-tech-adapter-orchestration-role-prod
- hrp-drs-tech-adapter-cross-account-role-dev
```

**Benefits:**
- Easy identification of role ownership
- Clear environment separation
- Predictable import patterns
- Simplified automation

### 3. Trust Policy Management

**Always Document Trust Relationships:**

```typescript
// Document who can assume this role
const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
  roleName: 'hrp-drs-tech-adapter-orchestration-role-test',
  assumedBy: new iam.CompositePrincipal(
    new iam.ServicePrincipal('lambda.amazonaws.com'),
    new iam.ServicePrincipal('states.amazonaws.com')
  ),
  description: 'Unified role for DR Orchestration Lambda functions and Step Functions',
});
```

**Verify Trust Policy:**
```bash
# Get trust policy
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --query 'Role.AssumeRolePolicyDocument' \
  --output json
```

### 4. Permission Boundary Management

**Use Permission Boundaries for Additional Security:**

```typescript
// Create permission boundary
const permissionBoundary = iam.ManagedPolicy.fromManagedPolicyArn(
  this,
  'PermissionBoundary',
  'arn:aws:iam::891376951562:policy/DRSOrchestrationBoundary'
);

// Apply to role
const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
  roleName: 'hrp-drs-tech-adapter-orchestration-role-test',
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
  permissionsBoundary: permissionBoundary,
});
```

**Benefits:**
- Limits maximum permissions
- Prevents privilege escalation
- Enforces organizational policies
- Simplifies compliance

### 5. Inline vs Managed Policies

**Inline Policies:**
- Use for role-specific permissions
- Deleted when role is deleted
- Cannot be reused across roles

**Managed Policies:**
- Use for shared permissions
- Can be attached to multiple roles
- Versioned and reusable

**Best Practice:**
```typescript
// Use managed policies for common permissions
orchestrationRole.addManagedPolicy(
  iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole')
);

// Use inline policies for role-specific permissions
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['drs:StartRecovery'],
  resources: ['*'],
}));
```

### 6. Least Privilege Principle

**Start with Minimum Permissions:**

```typescript
// Start with read-only permissions
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'drs:DescribeSourceServers',
    'drs:DescribeRecoveryInstances',
    'drs:DescribeJobs',
  ],
  resources: ['*'],
}));

// Add write permissions only when needed
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'drs:StartRecovery',
    'drs:TerminateRecoveryInstances',
  ],
  resources: ['*'],
  conditions: {
    StringEquals: {
      'aws:RequestedRegion': ['us-east-1', 'us-west-2'],
    },
  },
}));
```

### 7. Role Session Duration

**Configure Appropriate Session Duration:**

```typescript
const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
  roleName: 'hrp-drs-tech-adapter-orchestration-role-test',
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
  maxSessionDuration: cdk.Duration.hours(1),  // Default: 1 hour
});
```

**Guidelines:**
- Lambda functions: 15 minutes to 12 hours
- Step Functions: Match longest execution time
- Cross-account access: Minimum required duration

### 8. Removal Policy Strategy

**Always Set RETAIN for Production Roles:**

```typescript
const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
  roleName: 'hrp-drs-tech-adapter-orchestration-role-test',
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
  removalPolicy: cdk.RemovalPolicy.RETAIN,  // Critical!
});
```

**Environment-Specific Policies:**
```typescript
const removalPolicy = props.environment === 'prod'
  ? cdk.RemovalPolicy.RETAIN
  : cdk.RemovalPolicy.DESTROY;

const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
  roleName: `${props.projectName}-orchestration-role-${props.environment}`,
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
  removalPolicy,
});
```

### 9. Cross-Account Role Assumption

**Secure Cross-Account Access:**

```typescript
// In target account: Create role that can be assumed
const crossAccountRole = new iam.Role(this, 'CrossAccountRole', {
  roleName: 'DRSOrchestrationRole',
  assumedBy: new iam.AccountPrincipal('891376951562'),  // Source account
  externalIds: ['unique-external-id'],  // Prevent confused deputy
});

// In source account: Grant assume role permission
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['sts:AssumeRole'],
  resources: ['arn:aws:iam::123456789012:role/DRSOrchestrationRole'],
}));
```

**External ID Best Practices:**
- Use unique, random external IDs
- Store external IDs securely (Secrets Manager)
- Rotate external IDs periodically
- Document external ID requirements

### 10. Monitoring and Auditing

**Enable CloudTrail Logging:**

```typescript
// CloudTrail automatically logs IAM actions
// Monitor for:
// - AssumeRole events
// - Policy changes
// - Permission boundary modifications
// - Trust policy updates
```

**CloudWatch Alarms for Role Usage:**

```typescript
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';

// Create alarm for unauthorized assume role attempts
const assumeRoleAlarm = new cloudwatch.Alarm(this, 'AssumeRoleFailureAlarm', {
  metric: new cloudwatch.Metric({
    namespace: 'AWS/CloudTrail',
    metricName: 'AssumeRoleFailure',
    dimensionsMap: {
      RoleName: orchestrationRole.roleName,
    },
    statistic: 'Sum',
    period: cdk.Duration.minutes(5),
  }),
  threshold: 5,
  evaluationPeriods: 1,
  alarmDescription: 'Alert on multiple failed assume role attempts',
});
```

### 11. Documentation Requirements

**Document for Each IAM Role:**
- Purpose and responsibilities
- Trust relationships (who can assume)
- Attached policies (managed and inline)
- Permission boundaries (if applicable)
- Cross-account access patterns
- Session duration configuration
- Removal policy and retention
- Last review date

**Example Documentation:**

```markdown
## OrchestrationRole

- **Purpose:** Unified IAM role for DR Orchestration Lambda functions and Step Functions
- **ARN:** `arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test`
- **Trust Policy:** Lambda, Step Functions
- **Managed Policies:** AWSLambdaBasicExecutionRole
- **Inline Policies:** DRSOrchestrationPolicy (DRS, DynamoDB, EC2, STS permissions)
- **Permission Boundary:** None
- **Session Duration:** 1 hour
- **Removal Policy:** RETAIN
- **Cross-Account Access:** Can assume DRSOrchestrationRole in target accounts
- **Last Reviewed:** 2025-01-31
```

### 12. Testing Role Permissions

**Validate Permissions Before Deployment:**

```bash
# Test role assumption
aws sts assume-role \
  --role-arn arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test \
  --role-session-name test-session

# Test specific permissions
aws drs describe-source-servers \
  --region us-east-1 \
  --profile assumed-role-profile

# Use IAM Policy Simulator
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test \
  --action-names drs:StartRecovery \
  --resource-arns "*"
```



## Troubleshooting

### Issue 1: Role Not Found

**Error:**
```
NoSuchEntity: The role with name hrp-drs-tech-adapter-orchestration-role-test cannot be found
```

**Causes:**
- Role name is incorrect
- Role is in different AWS account
- Role was deleted
- Typo in role name

**Solutions:**

```bash
# 1. Verify role exists
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test

# 2. List all roles with similar names
aws iam list-roles \
  --query 'Roles[?contains(RoleName, `orchestration`)].RoleName'

# 3. Check correct AWS account
aws sts get-caller-identity

# 4. Search CloudFormation stacks for role
aws cloudformation describe-stack-resources \
  --stack-name hrp-drs-tech-adapter-test \
  --query 'StackResources[?ResourceType==`AWS::IAM::Role`]'
```

**Fix in CDK:**
```typescript
// Ensure correct role name
const orchestrationRole = iam.Role.fromRoleName(
  this,
  'OrchestrationRole',
  'hrp-drs-tech-adapter-orchestration-role-test'  // Verify this name
);
```

### Issue 2: Access Denied / Insufficient Permissions

**Error:**
```
AccessDeniedException: User: arn:aws:sts::891376951562:assumed-role/hrp-drs-tech-adapter-orchestration-role-test/hrp-drs-tech-adapter-query-handler-test is not authorized to perform: drs:DescribeSourceServers
```

**Causes:**
- Role lacks required permissions
- Permission boundary restricts access
- Service Control Policy (SCP) blocks action
- Resource-based policy denies access

**Solutions:**

```bash
# 1. Check role policies
aws iam list-attached-role-policies \
  --role-name hrp-drs-tech-adapter-orchestration-role-test

aws iam list-role-policies \
  --role-name hrp-drs-tech-adapter-orchestration-role-test

# 2. Get inline policy details
aws iam get-role-policy \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --policy-name DRSOrchestrationPolicy

# 3. Check permission boundary
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --query 'Role.PermissionsBoundary'

# 4. Test with IAM Policy Simulator
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test \
  --action-names drs:DescribeSourceServers \
  --resource-arns "*"
```

**Fix in CDK:**
```typescript
// Add missing permissions
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'drs:DescribeSourceServers',
    'drs:DescribeRecoveryInstances',
    'drs:DescribeJobs',
  ],
  resources: ['*'],
}));
```

### Issue 3: Cannot Assume Role

**Error:**
```
AccessDenied: User: arn:aws:lambda:us-east-1:891376951562:function:hrp-drs-tech-adapter-query-handler-test is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test
```

**Cause:** Trust policy doesn't allow Lambda to assume the role

**Solution:**

```bash
# Check trust policy
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --query 'Role.AssumeRolePolicyDocument'
```

**Fix Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "lambda.amazonaws.com",
          "states.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Update Trust Policy:**
```bash
# Create trust policy file
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "lambda.amazonaws.com",
          "states.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Update role trust policy
aws iam update-assume-role-policy \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --policy-document file://trust-policy.json
```

### Issue 4: Role Deleted When Stack is Destroyed

**Error:** Role was deleted even though you wanted to keep it

**Cause:** `removalPolicy` was not set to `RETAIN` before stack deletion

**Prevention:**

```typescript
// Always set RETAIN for important roles
const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
  roleName: 'hrp-drs-tech-adapter-orchestration-role-test',
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
  removalPolicy: cdk.RemovalPolicy.RETAIN,  // Critical!
});
```

**Recovery (if role was deleted):**

```bash
# 1. Check CloudTrail for role configuration
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=hrp-drs-tech-adapter-orchestration-role-test \
  --max-results 50

# 2. Recreate role with same configuration
# Use backed-up role configuration from Phase 1

# 3. Redeploy CDK stack
cdk deploy
```

### Issue 5: Cross-Account Assume Role Failure

**Error:**
```
AccessDenied: User: arn:aws:sts::891376951562:assumed-role/hrp-drs-tech-adapter-orchestration-role-test/hrp-drs-tech-adapter-execution-handler-test is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::123456789012:role/DRSOrchestrationRole
```

**Causes:**
- Source role lacks sts:AssumeRole permission
- Target role trust policy doesn't allow source account
- External ID mismatch
- Resource-based policy blocks access

**Solutions:**

**Step 1: Verify Source Role Permissions**
```bash
# Check source role has sts:AssumeRole permission
aws iam get-role-policy \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --policy-name DRSOrchestrationPolicy \
  --query 'PolicyDocument.Statement[?Action==`sts:AssumeRole`]'
```

**Step 2: Verify Target Role Trust Policy**
```bash
# In target account (123456789012)
aws iam get-role \
  --role-name DRSOrchestrationRole \
  --query 'Role.AssumeRolePolicyDocument'
```

**Step 3: Update Target Role Trust Policy**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }
  ]
}
```

**Step 4: Update Source Role Permissions**
```typescript
// In source account CDK stack
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['sts:AssumeRole'],
  resources: ['arn:aws:iam::123456789012:role/DRSOrchestrationRole'],
}));
```

### Issue 6: Policy Size Limit Exceeded

**Error:**
```
LimitExceeded: Cannot exceed quota for PoliciesPerRole: 10
```

**Cause:** Role has too many inline policies (limit: 10) or policy size too large (limit: 10,240 characters per inline policy)

**Solutions:**

**Option 1: Consolidate Inline Policies**
```typescript
// Instead of multiple small policies
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['drs:DescribeSourceServers'],
  resources: ['*'],
}));
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['drs:StartRecovery'],
  resources: ['*'],
}));

// Combine into single policy
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'drs:DescribeSourceServers',
    'drs:StartRecovery',
    'drs:TerminateRecoveryInstances',
  ],
  resources: ['*'],
}));
```

**Option 2: Use Managed Policies**
```typescript
// Create custom managed policy
const drsPolicy = new iam.ManagedPolicy(this, 'DRSPolicy', {
  managedPolicyName: 'DRSOrchestrationPolicy',
  statements: [
    new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['drs:*'],
      resources: ['*'],
    }),
  ],
});

// Attach to role
orchestrationRole.addManagedPolicy(drsPolicy);
```

### Issue 7: Lambda Function Cannot Use Imported Role

**Error:**
```
InvalidParameterValueException: The role defined for the function cannot be assumed by Lambda
```

**Cause:** Imported role's trust policy doesn't include lambda.amazonaws.com

**Solution:**

```bash
# Verify trust policy includes Lambda
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --query 'Role.AssumeRolePolicyDocument.Statement[?Principal.Service==`lambda.amazonaws.com`]'

# If empty, update trust policy to include Lambda
```

### Issue 8: Role ARN Mismatch

**Error:**
```
ValidationError: Role ARN does not match expected format
```

**Cause:** Incorrect ARN format or region/account mismatch

**Solution:**

```bash
# Get correct role ARN
aws iam get-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --query 'Role.Arn' \
  --output text

# ARN format: arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME
```

**Fix in CDK:**
```typescript
// Use correct ARN format
const orchestrationRole = iam.Role.fromRoleArn(
  this,
  'OrchestrationRole',
  'arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test'
);
```

### Issue 9: Cannot Modify Imported Role

**Error:**
```
Error: Cannot modify imported role
```

**Cause:** Imported role with `mutable: false` (default)

**Solution:**

```typescript
// Import with mutable flag
const orchestrationRole = iam.Role.fromRoleArn(
  this,
  'OrchestrationRole',
  'arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test',
  {
    mutable: true,  // Allow modifications
    addGrantsToResources: true,  // Enable grant methods
  }
);

// Now you can add policies
orchestrationRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['dynamodb:GetItem'],
  resources: ['*'],
}));
```

### Issue 10: Session Duration Too Short

**Error:**
```
ExpiredToken: The security token included in the request is expired
```

**Cause:** Role session duration is too short for long-running operations

**Solution:**

```typescript
// Increase session duration
const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
  roleName: 'hrp-drs-tech-adapter-orchestration-role-test',
  assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
  maxSessionDuration: cdk.Duration.hours(12),  // Max for Lambda
});
```

**For existing roles:**
```bash
# Update max session duration
aws iam update-role \
  --role-name hrp-drs-tech-adapter-orchestration-role-test \
  --max-session-duration 43200  # 12 hours in seconds
```



## Advanced Scenarios

### Scenario 1: Multi-Region Role Deployment

Deploy the same role configuration across multiple regions:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export class MultiRegionRoleStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Create role in primary region
    const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
      roleName: 'hrp-drs-tech-adapter-orchestration-role-global',
      assumedBy: new iam.CompositePrincipal(
        new iam.ServicePrincipal('lambda.amazonaws.com'),
        new iam.ServicePrincipal('states.amazonaws.com')
      ),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    
    // Add multi-region DRS permissions
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'drs:DescribeSourceServers',
        'drs:StartRecovery',
        'drs:TerminateRecoveryInstances',
      ],
      resources: ['*'],
      conditions: {
        StringEquals: {
          'aws:RequestedRegion': ['us-east-1', 'us-west-2', 'eu-west-1'],
        },
      },
    }));
    
    // Add multi-region DynamoDB permissions
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'dynamodb:GetItem',
        'dynamodb:PutItem',
        'dynamodb:UpdateItem',
        'dynamodb:Query',
      ],
      resources: [
        'arn:aws:dynamodb:us-east-1:*:table/hrp-drs-tech-adapter-*',
        'arn:aws:dynamodb:us-west-2:*:table/hrp-drs-tech-adapter-*',
        'arn:aws:dynamodb:eu-west-1:*:table/hrp-drs-tech-adapter-*',
      ],
    }));
  }
}
```

**Deployment:**
```bash
# Deploy to multiple regions
cdk deploy --region us-east-1
cdk deploy --region us-west-2
cdk deploy --region eu-west-1

# Note: IAM roles are global, but Lambda functions are regional
# The same role can be used by Lambda functions in all regions
```

### Scenario 2: Role Assumption Chain

Implement a chain of role assumptions for enhanced security:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class RoleChainStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Level 1: Lambda Execution Role (minimal permissions)
    const lambdaExecutionRole = new iam.Role(this, 'LambdaExecutionRole', {
      roleName: 'hrp-drs-tech-adapter-lambda-execution-role',
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });
    
    // Level 2: Orchestration Role (DRS permissions)
    const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
      roleName: 'hrp-drs-tech-adapter-orchestration-role',
      assumedBy: new iam.ArnPrincipal(lambdaExecutionRole.roleArn),
      externalIds: ['lambda-to-orchestration'],
    });
    
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['drs:*'],
      resources: ['*'],
    }));
    
    // Level 3: Cross-Account Role (target account access)
    // This role is created in target account
    const crossAccountRoleArn = 'arn:aws:iam::123456789012:role/DRSOrchestrationRole';
    
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['sts:AssumeRole'],
      resources: [crossAccountRoleArn],
    }));
    
    // Grant Lambda permission to assume orchestration role
    lambdaExecutionRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['sts:AssumeRole'],
      resources: [orchestrationRole.roleArn],
    }));
    
    // Create Lambda function
    const executionHandler = new lambda.Function(this, 'ExecutionHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('../../lambda/execution-handler'),
      handler: 'index.lambda_handler',
      role: lambdaExecutionRole,
      environment: {
        ORCHESTRATION_ROLE_ARN: orchestrationRole.roleArn,
        EXTERNAL_ID: 'lambda-to-orchestration',
      },
    });
  }
}
```

**Lambda Code for Role Chain:**
```python
import boto3
import os

def lambda_handler(event, context):
    # Assume orchestration role
    sts_client = boto3.client('sts')
    
    assumed_role = sts_client.assume_role(
        RoleArn=os.environ['ORCHESTRATION_ROLE_ARN'],
        RoleSessionName='lambda-session',
        ExternalId=os.environ['EXTERNAL_ID']
    )
    
    # Create DRS client with assumed credentials
    drs_client = boto3.client(
        'drs',
        aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
        aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
        aws_session_token=assumed_role['Credentials']['SessionToken']
    )
    
    # Perform DRS operations
    response = drs_client.describe_source_servers()
    return response
```

### Scenario 3: Service-Linked Role Integration

Integrate with AWS service-linked roles:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export class ServiceLinkedRoleStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Import DRS service-linked role
    const drsServiceLinkedRole = iam.Role.fromRoleArn(
      this,
      'DRSServiceLinkedRole',
      'arn:aws:iam::891376951562:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery'
    );
    
    // Create orchestration role that works with service-linked role
    const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
      roleName: 'hrp-drs-tech-adapter-orchestration-role',
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    
    // Add permissions to work with DRS service-linked role
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'iam:GetRole',
        'iam:PassRole',
      ],
      resources: [drsServiceLinkedRole.roleArn],
      conditions: {
        StringEquals: {
          'iam:PassedToService': 'drs.amazonaws.com',
        },
      },
    }));
    
    // Add DRS permissions
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['drs:*'],
      resources: ['*'],
    }));
  }
}
```

### Scenario 4: Temporary Elevated Permissions

Implement temporary permission elevation for sensitive operations:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';

export class ElevatedPermissionsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Standard orchestration role (read-only)
    const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
      roleName: 'hrp-drs-tech-adapter-orchestration-role',
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'drs:DescribeSourceServers',
        'drs:DescribeRecoveryInstances',
        'drs:DescribeJobs',
      ],
      resources: ['*'],
    }));
    
    // Elevated role (write permissions) with short session duration
    const elevatedRole = new iam.Role(this, 'ElevatedRole', {
      roleName: 'hrp-drs-tech-adapter-elevated-role',
      assumedBy: new iam.ArnPrincipal(orchestrationRole.roleArn),
      maxSessionDuration: cdk.Duration.minutes(15),  // Short duration
      externalIds: ['elevation-required'],
    });
    
    elevatedRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'drs:StartRecovery',
        'drs:TerminateRecoveryInstances',
      ],
      resources: ['*'],
    }));
    
    // Grant orchestration role permission to assume elevated role
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['sts:AssumeRole'],
      resources: [elevatedRole.roleArn],
      conditions: {
        StringEquals: {
          'aws:MultiFactorAuthPresent': 'true',  // Require MFA
        },
      },
    }));
  }
}
```

### Scenario 5: Role with Resource Tags

Use resource tags for fine-grained access control:

```typescript
import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export class TagBasedAccessStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // Create role with tags
    const orchestrationRole = new iam.Role(this, 'OrchestrationRole', {
      roleName: 'hrp-drs-tech-adapter-orchestration-role',
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
    });
    
    // Add tags to role
    cdk.Tags.of(orchestrationRole).add('Environment', 'test');
    cdk.Tags.of(orchestrationRole).add('Application', 'DROrchestration');
    cdk.Tags.of(orchestrationRole).add('CostCenter', 'Engineering');
    
    // Add tag-based permissions
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['drs:StartRecovery'],
      resources: ['*'],
      conditions: {
        StringEquals: {
          'aws:ResourceTag/Environment': 'test',
          'aws:ResourceTag/Application': 'DROrchestration',
        },
      },
    }));
    
    // Deny operations on production resources
    orchestrationRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.DENY,
      actions: ['drs:TerminateRecoveryInstances'],
      resources: ['*'],
      conditions: {
        StringEquals: {
          'aws:ResourceTag/Environment': 'production',
        },
      },
    }));
  }
}
```



## Quick Reference

### Import Methods Comparison

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| `fromRoleName()` | Same account/region | Simple, minimal code | Cannot modify role, no cross-account |
| `fromRoleArn()` | Cross-account/region | Works across boundaries | Cannot modify role by default |
| `fromRoleArn()` with `mutable: true` | Need to add permissions | Can add inline policies | More complex |

### Common Commands

```bash
# List existing roles
aws iam list-roles --query 'Roles[?contains(RoleName, `orchestration`)].RoleName'

# Get role details
aws iam get-role --role-name ROLE_NAME

# Get trust policy
aws iam get-role --role-name ROLE_NAME --query 'Role.AssumeRolePolicyDocument'

# List attached managed policies
aws iam list-attached-role-policies --role-name ROLE_NAME

# List inline policies
aws iam list-role-policies --role-name ROLE_NAME

# Get inline policy details
aws iam get-role-policy --role-name ROLE_NAME --policy-name POLICY_NAME

# Test role assumption
aws sts assume-role --role-arn ROLE_ARN --role-session-name test-session

# Update trust policy
aws iam update-assume-role-policy --role-name ROLE_NAME --policy-document file://trust-policy.json

# Update max session duration
aws iam update-role --role-name ROLE_NAME --max-session-duration 43200

# Deploy CDK with import
export IMPORT_EXISTING_ROLE=true
export EXISTING_ROLE_NAME=hrp-drs-tech-adapter-orchestration-role-test
cdk deploy

# Verify Lambda uses correct role
aws lambda get-function --function-name FUNCTION_NAME --query 'Configuration.Role'
```

### CDK Code Snippets

**Simple Import:**
```typescript
const role = iam.Role.fromRoleName(this, 'Role', 'role-name');
```

**Import by ARN:**
```typescript
const role = iam.Role.fromRoleArn(this, 'Role', 'arn:aws:iam::...');
```

**Import with Mutable Flag:**
```typescript
const role = iam.Role.fromRoleArn(this, 'Role', 'arn:aws:iam::...', {
  mutable: true,
  addGrantsToResources: true,
});
```

**Conditional Import:**
```typescript
const role = props.import
  ? iam.Role.fromRoleName(this, 'Role', props.roleName)
  : new iam.Role(this, 'Role', { /* config */ });
```

### AWS CLI Verification Commands

```bash
# Verify role exists
aws iam get-role --role-name hrp-drs-tech-adapter-orchestration-role-test

# Verify Lambda uses role
aws lambda get-function \
  --function-name hrp-drs-tech-adapter-query-handler-test \
  --query 'Configuration.Role'

# Test Lambda invocation
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-query-handler-test \
  --payload '{"operation":"list_protection_groups"}' \
  response.json

# Check CloudWatch Logs for errors
aws logs tail /aws/lambda/hrp-drs-tech-adapter-query-handler-test --since 5m

# Verify role permissions with Policy Simulator
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::891376951562:role/hrp-drs-tech-adapter-orchestration-role-test \
  --action-names drs:StartRecovery \
  --resource-arns "*"
```

## Checklist: Pre-Migration

Before migrating from CloudFormation to CDK with role import:

- [ ] **Backup role configuration** with AWS CLI commands
- [ ] **Document trust relationships** (AssumeRolePolicyDocument)
- [ ] **List all attached managed policies**
- [ ] **Export all inline policies**
- [ ] **Document permission boundaries** (if applicable)
- [ ] **Verify role ARN** matches expected format
- [ ] **Check cross-account trust relationships**
- [ ] **Update CloudFormation templates** with `DeletionPolicy: Retain`
- [ ] **Deploy CloudFormation update** to set retention policy
- [ ] **Test CDK stack** in dev environment first
- [ ] **Verify Lambda functions** can assume role
- [ ] **Create rollback plan** with documented steps
- [ ] **Schedule maintenance window** (if needed)
- [ ] **Notify team** of migration timeline

## Checklist: Post-Migration

After completing migration:

- [ ] **Verify Lambda functions** use imported role
- [ ] **Check CloudWatch Logs** for permission errors
- [ ] **Run integration tests** to validate functionality
- [ ] **Test all operations** (query, execution, data management)
- [ ] **Verify cross-account access** (if applicable)
- [ ] **Confirm trust relationships** are intact
- [ ] **Test role assumption** from Lambda/Step Functions
- [ ] **Monitor CloudWatch metrics** for anomalies
- [ ] **Verify IAM permissions** with Policy Simulator
- [ ] **Delete old CloudFormation stack** (if applicable)
- [ ] **Update documentation** with new stack details
- [ ] **Archive role backups** with retention policy
- [ ] **Document lessons learned** for future migrations

## Additional Resources

### AWS Documentation

- [IAM Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [CDK IAM Module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam-readme.html)
- [AssumeRole API](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- [IAM Policy Simulator](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html)
- [Cross-Account Access](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html)

### DR Orchestration Documentation

- [CDK Example README](../README.md)
- [DynamoDB Integration Guide](./DYNAMODB_INTEGRATION.md)
- [Step Functions Integration Guide](./STEPFUNCTIONS_INTEGRATION.md)
- [Python Examples](../../python/README.md)
- [Bash Examples](../../bash/README.md)
- [API Reference](../../../.kiro/specs/direct-lambda-invocation-mode/api-reference.md)
- [Design Document](../../../.kiro/specs/direct-lambda-invocation-mode/design.md)

### CDK Resources

- [CDK Workshop](https://cdkworkshop.com/)
- [CDK Patterns](https://cdkpatterns.com/)
- [CDK Best Practices](https://docs.aws.amazon.com/cdk/latest/guide/best-practices.html)
- [CDK Examples](https://github.com/aws-samples/aws-cdk-examples)

### Security Resources

- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [IAM Security Audit](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_getting-report.html)
- [AWS CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/)
- [AWS Config IAM Rules](https://docs.aws.amazon.com/config/latest/developerguide/managed-rules-by-aws-config.html)

## Summary

Importing existing IAM roles into CDK enables:

✅ **Zero-disruption migrations** from CloudFormation to CDK
✅ **Permission continuity** during infrastructure changes
✅ **Multi-stack architectures** with shared IAM roles
✅ **Blue/green deployments** with minimal risk
✅ **Simplified management** through centralized IAM

**Key Takeaways:**

1. **Always backup** role configuration before migration
2. **Set `removalPolicy: RETAIN`** before deleting stacks
3. **Use `fromRoleName()`** for simple same-account imports
4. **Use `fromRoleArn()` with `mutable: true`** to add permissions
5. **Test thoroughly** in dev before production migration
6. **Document everything** for future reference
7. **Verify trust relationships** after migration
8. **Monitor CloudWatch Logs** for permission errors
9. **Use IAM Policy Simulator** to validate permissions
10. **Follow least privilege** principle for all permissions

**Common Pitfalls to Avoid:**

- ❌ Not setting `removalPolicy: RETAIN` before stack deletion
- ❌ Forgetting to update trust policies for Lambda/Step Functions
- ❌ Exceeding inline policy size limits (10,240 characters)
- ❌ Not documenting cross-account trust relationships
- ❌ Skipping permission validation with Policy Simulator
- ❌ Not testing role assumption before production deployment
- ❌ Ignoring CloudWatch Logs for permission errors
- ❌ Not backing up role configuration before migration

For questions or issues, refer to the troubleshooting section or consult the AWS IAM documentation.

---

**Last Updated:** January 2025  
**Version:** 1.0  
**Maintainer:** DR Orchestration Platform Team

