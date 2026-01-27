# Orchestration Role Specification

## Overview

The **Unified Orchestration Role** is a consolidated IAM role that provides all necessary permissions for the DR Orchestration Platform to execute disaster recovery operations across AWS services. This role is used by all Lambda functions in the platform.

**Role Name**: `aws-drs-orchestration-orchestration-role-{environment}`

**Example ARN**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-orchestration-role-dev`

## Lambda Handler Architecture

The orchestration platform uses **6 Lambda functions** that share this unified role:

- **data-management-handler**: Protection groups, recovery plans, configuration management
- **execution-handler**: Recovery execution control, pause/resume, termination
- **query-handler**: Read-only queries, DRS status, EC2 resource discovery
- **frontend-deployer**: Frontend build and deployment operations
- **orch-sf**: Step Functions orchestration logic
- **notification-formatter**: SNS notification routing and formatting

## Purpose

This role consolidates permissions from all Lambda functions into a single unified role to:
- Execute DR orchestration workflows via Step Functions
- Manage DRS (Elastic Disaster Recovery) operations
- Coordinate cross-account DR operations
- Deploy and manage frontend applications
- Monitor and report on DR execution status

## Deployment Modes

The orchestration role supports two deployment modes:

### 1. Standalone Mode (Default)
The CloudFormation stack creates the orchestration role automatically.

**When to use**: Deploying the DR Orchestration Platform as a standalone solution.

**CloudFormation Parameter**: `OrchestrationRoleArn` = "" (empty)

### 2. HRP Integration Mode
The CloudFormation stack uses an externally-created orchestration role (provided by HRP).

**When to use**: Integrating with the HRP (High-level Recovery Platform) orchestration engine.

**CloudFormation Parameter**: `OrchestrationRoleArn` = "arn:aws:iam::ACCOUNT:role/HRPOrchestrationRole"

**Requirements for HRP Role**:
- Must include ALL policy statements documented below
- Must allow Lambda service to assume the role
- Must be created before deploying the DR Orchestration stack

## Trust Policy

The role must allow AWS Lambda service to assume it:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Managed Policies

The role requires the following AWS managed policy:

- `arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole`

This provides basic CloudWatch Logs permissions for Lambda execution.

## Custom Policy Statements

The role requires 16 custom inline policies with specific permissions:

---

### Policy 1: DynamoDB Access

**Purpose**: Read/write access to DynamoDB tables for state management, execution tracking, and resource inventory.

**Used by**: `data-management-handler`, `execution-handler`, `query-handler`, `orch-sf`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:BatchGetItem",
        "dynamodb:BatchWriteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/aws-drs-orchestration-*"
      ]
    }
  ]
}
```

**Tables accessed**:
- `aws-drs-orchestration-executions-{env}` - DR execution tracking
- `aws-drs-orchestration-resources-{env}` - Resource inventory cache
- `aws-drs-orchestration-config-{env}` - Configuration settings

---

### Policy 2: Step Functions Access

**Purpose**: Start and manage Step Functions state machine executions for DR orchestration workflows.

**Used by**: `execution-handler`

**CRITICAL**: Must include `states:SendTaskHeartbeat` for long-running tasks.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution",
        "states:DescribeExecution",
        "states:ListExecutions",
        "states:SendTaskSuccess",
        "states:SendTaskFailure",
        "states:SendTaskHeartbeat"
      ],
      "Resource": [
        "arn:aws:states:*:*:stateMachine:aws-drs-orchestration-*",
        "arn:aws:states:*:*:execution:aws-drs-orchestration-*:*"
      ]
    }
  ]
}
```

**State machines accessed**:
- `aws-drs-orchestration-orchestrator-{env}` - Main DR orchestration workflow

---

### Policy 3: DRS Read Access

**Purpose**: Read-only access to AWS Elastic Disaster Recovery (DRS) for monitoring replication status and recovery readiness.

**Used by**: `query-handler`, `execution-handler`, `orch-sf`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:DescribeSourceServers",
        "drs:DescribeRecoverySnapshots",
        "drs:DescribeRecoveryInstances",
        "drs:DescribeJobs",
        "drs:DescribeJobLogItems",
        "drs:GetLaunchConfiguration",
        "drs:GetReplicationConfiguration",
        "drs:GetFailbackReplicationConfiguration",
        "drs:DescribeLaunchConfigurationTemplates",
        "drs:DescribeReplicationConfigurationTemplates",
        "drs:ListLaunchActions",
        "drs:ListTagsForResource"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Policy 4: DRS Write Access

**Purpose**: Execute DR operations including recovery, failback, and replication management.

**Used by**: `execution-handler`, `orch-sf`

**CRITICAL**: Must include `drs:CreateRecoveryInstanceForDrs` for AllowLaunchingIntoThisInstance pattern.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:StartRecovery",
        "drs:CreateRecoveryInstanceForDrs",
        "drs:TerminateRecoveryInstances",
        "drs:DisconnectRecoveryInstance",
        "drs:StartFailbackLaunch",
        "drs:StopFailback",
        "drs:ReverseReplication",
        "drs:UpdateLaunchConfiguration",
        "drs:UpdateReplicationConfiguration",
        "drs:UpdateFailbackReplicationConfiguration",
        "drs:PutLaunchAction",
        "drs:DeleteLaunchAction",
        "drs:TagResource",
        "drs:UntagResource",
        "drs:GetAgentInstallationAssetsForDrs",
        "drs:IssueAgentCertificateForDrs",
        "drs:CreateSourceServerForDrs"
      ],
      "Resource": "*"
    }
  ]
}
```

**Key operations**:
- `drs:StartRecovery` - Initiate DR failover
- `drs:CreateRecoveryInstanceForDrs` - Launch recovery instances with IP preservation
- `drs:ReverseReplication` - Enable failback replication
- `drs:StartFailbackLaunch` - Execute failback to primary region

---

### Policy 5: EC2 Access

**Purpose**: Manage EC2 instances, launch templates, and networking for DR operations.

**Used by**: `execution-handler`, `query-handler`, `orch-sf`

**CRITICAL**: Must include `ec2:CreateLaunchTemplateVersion` for AllowLaunchingIntoThisInstance pattern.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeInstanceAttribute",
        "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots",
        "ec2:DescribeImages",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSubnets",
        "ec2:DescribeVpcs",
        "ec2:DescribeAvailabilityZones",
        "ec2:DescribeAccountAttributes",
        "ec2:CreateTags",
        "ec2:DescribeTags",
        "ec2:CreateLaunchTemplateVersion",
        "ec2:DescribeLaunchTemplates",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:ModifyLaunchTemplate"
      ],
      "Resource": "*"
    }
  ]
}
```

**Key operations**:
- `ec2:CreateLaunchTemplateVersion` - Create launch template versions for IP preservation
- `ec2:CreateTags` - Tag recovery instances with metadata
- `ec2:DescribeInstances` - Monitor instance status during recovery

---

### Policy 6: IAM Access

**Purpose**: Pass IAM roles to DRS and EC2 services for recovery instance profiles.

**Used by**: `execution-handler`, `orch-sf`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole",
        "iam:GetInstanceProfile",
        "iam:ListInstanceProfiles",
        "iam:ListRoles"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": [
            "drs.amazonaws.com",
            "ec2.amazonaws.com"
          ]
        }
      }
    }
  ]
}
```

**Condition**: Role passing is restricted to DRS and EC2 services only.

---

### Policy 7: STS Access

**Purpose**: Assume cross-account roles for multi-account DR operations.

**Used by**: `execution-handler`, `query-handler`, `orch-sf`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole"
      ],
      "Resource": [
        "arn:aws:iam::*:role/aws-drs-orchestration-cross-account-*"
      ]
    }
  ]
}
```

**Cross-account pattern**: Assumes roles in workload accounts with naming pattern `aws-drs-orchestration-cross-account-{env}`.

---

### Policy 8: KMS Access

**Purpose**: Access KMS keys for encrypted EBS volumes and DRS replication.

**Used by**: `execution-handler`, `orch-sf`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:DescribeKey",
        "kms:ListAliases",
        "kms:CreateGrant"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "ec2.REGION.amazonaws.com",
            "drs.REGION.amazonaws.com"
          ]
        }
      }
    }
  ]
}
```

**Condition**: KMS operations are restricted to EC2 and DRS services only.

**Note**: Replace `REGION` with your AWS region (e.g., `us-east-1`).

---

### Policy 9: CloudFormation Access

**Purpose**: Describe CloudFormation stacks for deployment coordination and custom resource management.

**Used by**: `frontend-deployer`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResource",
        "cloudformation:DescribeStackResources",
        "cloudformation:ListStacks"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Policy 10: S3 Access

**Purpose**: Read/write access to S3 buckets for frontend deployment and artifact storage.

**Used by**: `frontend-deployer`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::aws-drs-orchestration-*",
        "arn:aws:s3:::aws-drs-orchestration-*/*"
      ]
    }
  ]
}
```

**Buckets accessed**:
- Frontend hosting buckets
- Deployment artifact buckets

---

### Policy 11: CloudFront Access

**Purpose**: Invalidate CloudFront cache after frontend deployments.

**Used by**: `frontend-deployer`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation",
        "cloudfront:ListInvalidations"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Policy 12: Lambda Invoke Access

**Purpose**: Invoke other Lambda functions for orchestration coordination.

**Used by**: `execution-handler`, `data-management-handler`

```json
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
```

**Functions invoked**:
- `aws-drs-orchestration-execution-poller-{env}` - Invoked by ExecutionFinder

---

### Policy 13: EventBridge Access

**Purpose**: Manage EventBridge rules for scheduled operations and event-driven workflows.

**Used by**: `data-management-handler`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:DeleteRule",
        "events:DescribeRule",
        "events:EnableRule",
        "events:DisableRule",
        "events:PutTargets",
        "events:RemoveTargets"
      ],
      "Resource": [
        "arn:aws:events:*:*:rule/aws-drs-orchestration-*"
      ]
    }
  ]
}
```

---

### Policy 14: SSM Access

**Purpose**: Execute SSM commands and automation for post-recovery configuration.

**Used by**: `orch-sf`

**CRITICAL**: Must include `ssm:CreateOpsItem` for operational incident tracking.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:DescribeDocument",
        "ssm:DescribeInstanceInformation",
        "ssm:SendCommand",
        "ssm:StartAutomationExecution",
        "ssm:ListDocuments",
        "ssm:ListCommandInvocations",
        "ssm:GetParameter",
        "ssm:PutParameter",
        "ssm:GetDocument",
        "ssm:GetAutomationExecution",
        "ssm:CreateOpsItem"
      ],
      "Resource": "*"
    }
  ]
}
```

**Key operations**:
- `ssm:SendCommand` - Execute commands on recovered instances
- `ssm:CreateOpsItem` - Create operational incidents for DR events
- `ssm:GetParameter` - Retrieve configuration parameters

---

### Policy 15: SNS Access

**Purpose**: Publish notifications for DR execution events and alerts.

**Used by**: `orch-sf`, `notification-formatter`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": [
        "arn:aws:sns:*:*:aws-drs-orchestration-*"
      ]
    }
  ]
}
```

**Topics accessed**:
- `aws-drs-orchestration-execution-notifications-{env}` - Execution status updates
- `aws-drs-orchestration-drs-alerts-{env}` - DRS operational alerts
- `aws-drs-orchestration-execution-pause-{env}` - Execution pause notifications

---

### Policy 16: CloudWatch Access

**Purpose**: Publish custom metrics for DR execution monitoring.

**Used by**: `execution-handler`, `orch-sf`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```

**Metrics published**:
- DR execution duration
- Wave completion times
- Recovery instance counts
- Execution success/failure rates

---

## Complete IAM Role CloudFormation Template

For HRP integration, use this CloudFormation template to create the orchestration role:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'HRP Orchestration Role for DRS Orchestration Platform'

Parameters:
  ProjectName:
    Type: String
    Default: 'aws-drs-orchestration'
    Description: 'Project name for resource naming'

  Environment:
    Type: String
    Default: 'dev'
    Description: 'Environment name (dev, test, prod)'

Resources:
  HRPOrchestrationRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub "${ProjectName}-orchestration-role-${Environment}"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        # Policy 1: DynamoDB Access
        - PolicyName: DynamoDBAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - dynamodb:GetItem
                  - dynamodb:PutItem
                  - dynamodb:UpdateItem
                  - dynamodb:DeleteItem
                  - dynamodb:Query
                  - dynamodb:Scan
                  - dynamodb:BatchGetItem
                  - dynamodb:BatchWriteItem
                Resource:
                  - !Sub "arn:${AWS::Partition}:dynamodb:${AWS::Region}:${AWS::AccountId}:table/${ProjectName}-*"
        
        # Policy 2: Step Functions Access
        - PolicyName: StepFunctionsAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - states:StartExecution
                  - states:DescribeExecution
                  - states:ListExecutions
                  - states:SendTaskSuccess
                  - states:SendTaskFailure
                  - states:SendTaskHeartbeat
                Resource:
                  - !Sub "arn:${AWS::Partition}:states:${AWS::Region}:${AWS::AccountId}:stateMachine:${ProjectName}-*"
                  - !Sub "arn:${AWS::Partition}:states:${AWS::Region}:${AWS::AccountId}:execution:${ProjectName}-*:*"
        
        # Policy 3: DRS Read Access
        - PolicyName: DRSReadAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - drs:DescribeSourceServers
                  - drs:DescribeRecoverySnapshots
                  - drs:DescribeRecoveryInstances
                  - drs:DescribeJobs
                  - drs:DescribeJobLogItems
                  - drs:GetLaunchConfiguration
                  - drs:GetReplicationConfiguration
                  - drs:GetFailbackReplicationConfiguration
                  - drs:DescribeLaunchConfigurationTemplates
                  - drs:DescribeReplicationConfigurationTemplates
                  - drs:ListLaunchActions
                  - drs:ListTagsForResource
                Resource: "*"
        
        # Policy 4: DRS Write Access
        - PolicyName: DRSWriteAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - drs:StartRecovery
                  - drs:CreateRecoveryInstanceForDrs
                  - drs:TerminateRecoveryInstances
                  - drs:DisconnectRecoveryInstance
                  - drs:StartFailbackLaunch
                  - drs:StopFailback
                  - drs:ReverseReplication
                  - drs:UpdateLaunchConfiguration
                  - drs:UpdateReplicationConfiguration
                  - drs:UpdateFailbackReplicationConfiguration
                  - drs:PutLaunchAction
                  - drs:DeleteLaunchAction
                  - drs:TagResource
                  - drs:UntagResource
                  - drs:GetAgentInstallationAssetsForDrs
                  - drs:IssueAgentCertificateForDrs
                  - drs:CreateSourceServerForDrs
                Resource: "*"
        
        # Policy 5: EC2 Access
        - PolicyName: EC2Access
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - ec2:DescribeInstances
                  - ec2:DescribeInstanceStatus
                  - ec2:DescribeInstanceTypes
                  - ec2:DescribeInstanceAttribute
                  - ec2:DescribeVolumes
                  - ec2:DescribeSnapshots
                  - ec2:DescribeImages
                  - ec2:DescribeSecurityGroups
                  - ec2:DescribeSubnets
                  - ec2:DescribeVpcs
                  - ec2:DescribeAvailabilityZones
                  - ec2:DescribeAccountAttributes
                  - ec2:CreateTags
                  - ec2:DescribeTags
                  - ec2:CreateLaunchTemplateVersion
                  - ec2:DescribeLaunchTemplates
                  - ec2:DescribeLaunchTemplateVersions
                  - ec2:ModifyLaunchTemplate
                Resource: "*"
        
        # Policy 6: IAM Access
        - PolicyName: IAMAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - iam:PassRole
                  - iam:GetInstanceProfile
                  - iam:ListInstanceProfiles
                  - iam:ListRoles
                Resource: "*"
                Condition:
                  StringEquals:
                    iam:PassedToService:
                      - drs.amazonaws.com
                      - ec2.amazonaws.com
        
        # Policy 7: STS Access
        - PolicyName: STSAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - sts:AssumeRole
                Resource:
                  - !Sub "arn:${AWS::Partition}:iam::*:role/${ProjectName}-cross-account-*"
        
        # Policy 8: KMS Access
        - PolicyName: KMSAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - kms:DescribeKey
                  - kms:ListAliases
                  - kms:CreateGrant
                Resource: "*"
                Condition:
                  StringEquals:
                    kms:ViaService:
                      - !Sub "ec2.${AWS::Region}.amazonaws.com"
                      - !Sub "drs.${AWS::Region}.amazonaws.com"
        
        # Policy 9: CloudFormation Access
        - PolicyName: CloudFormationAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - cloudformation:DescribeStacks
                  - cloudformation:DescribeStackEvents
                  - cloudformation:DescribeStackResource
                  - cloudformation:DescribeStackResources
                  - cloudformation:ListStacks
                Resource: "*"
        
        # Policy 10: S3 Access
        - PolicyName: S3Access
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                  - s3:DeleteObject
                  - s3:ListBucket
                Resource:
                  - !Sub "arn:${AWS::Partition}:s3:::${ProjectName}-*"
                  - !Sub "arn:${AWS::Partition}:s3:::${ProjectName}-*/*"
        
        # Policy 11: CloudFront Access
        - PolicyName: CloudFrontAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - cloudfront:CreateInvalidation
                  - cloudfront:GetInvalidation
                  - cloudfront:ListInvalidations
                Resource: "*"
        
        # Policy 12: Lambda Invoke Access
        - PolicyName: LambdaInvokeAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - lambda:InvokeFunction
                Resource:
                  - !Sub "arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${ProjectName}-*"
        
        # Policy 13: EventBridge Access
        - PolicyName: EventBridgeAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - events:PutRule
                  - events:DeleteRule
                  - events:DescribeRule
                  - events:EnableRule
                  - events:DisableRule
                  - events:PutTargets
                  - events:RemoveTargets
                Resource:
                  - !Sub "arn:${AWS::Partition}:events:${AWS::Region}:${AWS::AccountId}:rule/${ProjectName}-*"
        
        # Policy 14: SSM Access
        - PolicyName: SSMAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - ssm:DescribeDocument
                  - ssm:DescribeInstanceInformation
                  - ssm:SendCommand
                  - ssm:StartAutomationExecution
                  - ssm:ListDocuments
                  - ssm:ListCommandInvocations
                  - ssm:GetParameter
                  - ssm:PutParameter
                  - ssm:GetDocument
                  - ssm:GetAutomationExecution
                  - ssm:CreateOpsItem
                Resource: "*"
        
        # Policy 15: SNS Access
        - PolicyName: SNSAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - sns:Publish
                Resource:
                  - !Sub "arn:${AWS::Partition}:sns:${AWS::Region}:${AWS::AccountId}:${ProjectName}-*"
        
        # Policy 16: CloudWatch Access
        - PolicyName: CloudWatchAccess
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - cloudwatch:PutMetricData
                  - cloudwatch:GetMetricStatistics
                Resource: "*"
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

Outputs:
  OrchestrationRoleArn:
    Description: 'ARN of the HRP Orchestration Role'
    Value: !GetAtt HRPOrchestrationRole.Arn
    Export:
      Name: !Sub '${AWS::StackName}-OrchestrationRoleArn'

  OrchestrationRoleName:
    Description: 'Name of the HRP Orchestration Role'
    Value: !Ref HRPOrchestrationRole
    Export:
      Name: !Sub '${AWS::StackName}-OrchestrationRoleName'
```

---

## Integration with DRS Orchestration Stack

When deploying the DRS Orchestration stack with an externally-created orchestration role:

1. **Create the orchestration role first** using the CloudFormation template above
2. **Note the role ARN** from the stack outputs
3. **Deploy the DRS Orchestration stack** with the `OrchestrationRoleArn` parameter:

```bash
aws cloudformation create-stack \
  --stack-name drs-orchestration-dev \
  --template-url https://s3.amazonaws.com/BUCKET/cfn/master-template.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=aws-drs-orchestration \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=OrchestrationRoleArn,ParameterValue=arn:aws:iam::ACCOUNT:role/ROLE_NAME \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_NAMED_IAM
```

---

## Validation Checklist

Before deploying with an external orchestration role, verify:

- [ ] Trust policy allows Lambda service to assume the role
- [ ] All 16 custom policies are included
- [ ] AWS managed policy `AWSLambdaBasicExecutionRole` is attached
- [ ] Critical permissions are present:
  - [ ] `states:SendTaskHeartbeat` (Policy 2)
  - [ ] `drs:CreateRecoveryInstanceForDrs` (Policy 4)
  - [ ] `ec2:CreateLaunchTemplateVersion` (Policy 5)
  - [ ] `ssm:CreateOpsItem` (Policy 14)
- [ ] Resource patterns match your naming convention
- [ ] Region-specific conditions are updated (Policy 8)
- [ ] Cross-account role pattern matches your setup (Policy 7)

---

## Troubleshooting

### Common Issues

**Issue**: Lambda functions fail with "AccessDenied" errors

**Solution**: Verify the role ARN is correct and all policies are attached. Check CloudWatch Logs for specific permission errors.

**Issue**: DRS operations fail with "CreateRecoveryInstanceForDrs" permission error

**Solution**: Ensure Policy 4 includes `drs:CreateRecoveryInstanceForDrs` action.

**Issue**: Step Functions executions timeout

**Solution**: Verify Policy 2 includes `states:SendTaskHeartbeat` for long-running tasks.

**Issue**: Cross-account operations fail

**Solution**: Verify Policy 7 resource pattern matches your cross-account role naming convention.

---

## Security Considerations

1. **Least Privilege**: The role follows least privilege principles with specific resource patterns where possible
2. **Service Restrictions**: IAM PassRole is restricted to DRS and EC2 services only (Policy 6)
3. **KMS Restrictions**: KMS operations are restricted to EC2 and DRS services (Policy 8)
4. **Resource Patterns**: Most policies use resource patterns to limit scope to project resources
5. **Audit Trail**: All role usage is logged via CloudTrail

---

## Maintenance

### Adding New Permissions

When adding new Lambda functions or features:

1. Identify required AWS service permissions
2. Add new policy statement to appropriate policy (or create new policy)
3. Update this documentation with the new policy
4. Test in non-production environment first
5. Update CloudFormation template

### Removing Permissions

When deprecating features:

1. Identify unused permissions via CloudTrail logs
2. Remove from CloudFormation template
3. Test in non-production environment
4. Update this documentation
5. Deploy to production

---

## Related Documentation

- [DRS IAM and Permissions Reference](DRS_IAM_AND_PERMISSIONS_REFERENCE.md) - Detailed DRS-specific permissions
- [Cross-Account Role Specification](../../cfn/cross-account-role-stack.yaml) - Cross-account role template
- [Master Template](../../cfn/master-template.yaml) - Complete stack deployment
- [Lambda Stack](../../cfn/lambda-stack.yaml) - Lambda function definitions

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | January 16, 2026 | Initial documentation with all 16 policies |
| 1.1 | January 16, 2026 | Added complete CloudFormation template for HRP integration |

---

**Last Updated**: January 16, 2026  
**Role ARN**: `arn:aws:iam::438465159935:role/aws-drs-orchestration-orchestration-role-dev`  
**Status**: Production Ready
        "kms:CreateGrant"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "ec2.us-east-1.amazonaws.com",
            "drs.us-east-1.amazonaws.com"
          ]
        }
      }
    }
  ]
}
```

**Condition**: KMS access is restricted to EC2 and DRS services only.

**Note**: Replace `us-east-1` with your deployment region.

---

### Policy 9: CloudFormation Access

**Purpose**: Query CloudFormation stack status for custom resource handlers and deployment validation.

**Used by**: `frontend-deployer`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudformation:DescribeStacks",
        "cloudformation:DescribeStackEvents",
        "cloudformation:DescribeStackResource",
        "cloudformation:DescribeStackResources",
        "cloudformation:ListStacks"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Policy 10: S3 Access

**Purpose**: Deploy frontend applications and manage deployment artifacts.

**Used by**: `frontend-deployer`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::aws-drs-orchestration-*",
        "arn:aws:s3:::aws-drs-orchestration-*/*"
      ]
    }
  ]
}
```

**Buckets accessed**:
- `aws-drs-orchestration-frontend-{env}` - Frontend hosting bucket
- `aws-drs-orchestration-{env}` - Deployment artifacts bucket

---

### Policy 11: CloudFront Access

**Purpose**: Invalidate CloudFront cache after frontend deployments.

**Used by**: `frontend-deployer`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation",
        "cloudfront:ListInvalidations"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Policy 12: Lambda Invoke Access

**Purpose**: Invoke other Lambda functions for asynchronous processing and execution polling.

**Used by**: `execution-handler`, `data-management-handler`

```json
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
```

---

### Policy 13: EventBridge Access

**Purpose**: Manage EventBridge rules for scheduled DR operations and tag synchronization.

**Used by**: `data-management-handler`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:DeleteRule",
        "events:DescribeRule",
        "events:EnableRule",
        "events:DisableRule",
        "events:PutTargets",
        "events:RemoveTargets"
      ],
      "Resource": [
        "arn:aws:events:*:*:rule/aws-drs-orchestration-*"
      ]
    }
  ]
}
```

---

### Policy 14: SSM Access

**Purpose**: Execute SSM automation documents and create OpsItems for DR operations.

**Used by**: `orch-sf`

**CRITICAL**: Must include `ssm:CreateOpsItem` for operational tracking.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:DescribeDocument",
        "ssm:DescribeInstanceInformation",
        "ssm:SendCommand",
        "ssm:StartAutomationExecution",
        "ssm:ListDocuments",
        "ssm:ListCommandInvocations",
        "ssm:GetParameter",
        "ssm:PutParameter",
        "ssm:GetDocument",
        "ssm:GetAutomationExecution",
        "ssm:CreateOpsItem"
      ],
      "Resource": "*"
    }
  ]
}
```

**Key operations**:
- `ssm:StartAutomationExecution` - Execute DR automation workflows
- `ssm:CreateOpsItem` - Create operational tracking items
- `ssm:SendCommand` - Execute commands on recovery instances

---

### Policy 15: SNS Access

**Purpose**: Send notifications for DR execution status and alerts.

**Used by**: `orch-sf`, `notification-formatter`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": [
        "arn:aws:sns:*:*:aws-drs-orchestration-*"
      ]
    }
  ]
}
```

**Topics accessed**:
- `aws-drs-orchestration-notifications-{env}` - DR execution notifications

---

### Policy 16: CloudWatch Access

**Purpose**: Publish custom metrics for DR execution monitoring and dashboards.

**Used by**: `execution-handler`, `orch-sf`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```

**Metrics published**:
- `DROrchestration/ExecutionDuration` - DR execution time
- `DROrchestration/RecoverySuccess` - Recovery success rate
- `DROrchestration/ResourcesRecovered` - Number of resources recovered

---

## Critical Permissions Summary

The following permissions are **CRITICAL** for core DR functionality and must not be omitted:

1. **`states:SendTaskHeartbeat`** (Policy 2) - Required for long-running Step Functions tasks
2. **`drs:CreateRecoveryInstanceForDrs`** (Policy 4) - Required for AllowLaunchingIntoThisInstance pattern (IP preservation)
3. **`ec2:CreateLaunchTemplateVersion`** (Policy 5) - Required for AllowLaunchingIntoThisInstance pattern
4. **`ssm:CreateOpsItem`** (Policy 14) - Required for operational tracking

## Resource Naming Conventions

All resources follow the naming pattern: `aws-drs-orchestration-{resource-type}-{environment}`

**Examples**:
- Role: `aws-drs-orchestration-orchestration-role-dev`
- State Machine: `aws-drs-orchestration-orchestrator-dev`
- DynamoDB Table: `aws-drs-orchestration-executions-dev`
- Lambda Function: `aws-drs-orchestration-api-handler-dev`

## HRP Integration Checklist

When creating the orchestration role for HRP integration, ensure:

- [ ] Trust policy allows Lambda service to assume the role
- [ ] AWS managed policy `AWSLambdaBasicExecutionRole` is attached
- [ ] All 16 custom policy statements are included (see above)
- [ ] Critical permissions are present (SendTaskHeartbeat, CreateRecoveryInstanceForDrs, etc.)
- [ ] Resource ARN patterns match your project naming convention
- [ ] KMS ViaService condition uses correct AWS region
- [ ] Role ARN is provided to CloudFormation via `OrchestrationRoleArn` parameter

## Testing the Role

After creating the role, validate it has correct permissions:

```bash
# Test DRS read access
aws drs describe-source-servers --region us-east-1

# Test Step Functions access
aws stepfunctions list-state-machines --region us-east-1

# Test DynamoDB access
aws dynamodb list-tables --region us-east-1
```

## Security Considerations

1. **Least Privilege**: The role follows least privilege principles with resource-scoped permissions where possible
2. **Service Restrictions**: IAM PassRole and KMS access are restricted to specific services via conditions
3. **Resource Scoping**: Most permissions are scoped to resources with `aws-drs-orchestration-*` naming pattern
4. **Cross-Account**: Cross-account access requires explicit role assumption with specific naming pattern

## Related Documentation

- [ADR-006: Reference Architecture Integration](../../docs/architecture/ADR-006-reference-architecture-integration.md)
- [Deployment Flexibility Spec](.kiro/specs/deployment-flexibility/)
- [Master Template](../../cfn/master-template.yaml) - Lines 100-380

## Support

For questions about the orchestration role or HRP integration:
- Review the CloudFormation template: `cfn/master-template.yaml`
- Check deployment logs: CloudWatch Logs `/aws/lambda/aws-drs-orchestration-*`
- Contact: DR Orchestration Platform Team
