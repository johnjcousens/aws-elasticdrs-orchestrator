# IAM Role Reference

## Overview

This document provides comprehensive reference documentation for the function-specific IAM roles implemented in the DR Orchestration Platform. Each Lambda function has a dedicated IAM role scoped to the minimum permissions required, following the principle of least privilege.

## Architecture Summary

The platform uses five function-specific IAM roles, each tailored to its Lambda function's operational requirements:

1. **Query Handler Role**: Read-only access for status queries and configuration retrieval
2. **Data Management Role**: DynamoDB CRUD and DRS metadata operations (no recovery execution)
3. **Execution Handler Role**: Step Functions orchestration and SNS notifications
4. **Orchestration Role**: Comprehensive DRS and EC2 permissions for recovery operations
5. **Frontend Deployer Role**: S3 and CloudFront deployment operations

### Role Selection

The platform supports two IAM architectures through the `UseFunctionSpecificRoles` CloudFormation parameter:

- **UseFunctionSpecificRoles=true**: Each Lambda function uses its dedicated role (recommended)
- **UseFunctionSpecificRoles=false**: All Lambda functions share a unified role (legacy, backward compatibility)

### Naming Convention

All IAM roles follow the pattern: `{ProjectName}-{function}-role-{Environment}`

**Examples**:
- `aws-drs-orchestration-query-handler-role-test`
- `aws-drs-orchestration-data-management-role-test`
- `aws-drs-orchestration-execution-handler-role-test`
- `aws-drs-orchestration-orchestration-role-test`
- `aws-drs-orchestration-frontend-deployer-role-test`

## Cross-Account Access Pattern

All roles that perform cross-account DRS operations include STS AssumeRole permission with ExternalId validation for enhanced security.

### ExternalId Format

```
{ProjectName}-{Environment}
```

**Example**: `aws-drs-orchestration-test`

### Trust Policy Requirement

Workload account roles must include the ExternalId in their trust policy:

```yaml
AssumeRolePolicyDocument:
  Version: "2012-10-17"
  Statement:
    - Effect: Allow
      Principal:
        AWS: !Sub "arn:aws:iam::{OrchestrationAccountId}:root"
      Action: sts:AssumeRole
      Condition:
        StringEquals:
          sts:ExternalId: !Sub "${ProjectName}-${Environment}"
```


---

## 1. Query Handler Role

**Role Name**: `{ProjectName}-query-handler-role-{Environment}`

**Lambda Function**: Query Handler

**Purpose**: Provides read-only access to DRS, DynamoDB, EC2, and CloudWatch for status queries and configuration retrieval. This role cannot perform any write operations or execute disaster recovery operations.

### Permissions Summary

| Service | Operations | Resource Scope |
|---------|-----------|----------------|
| DynamoDB | GetItem, Query, Scan, BatchGetItem | `{ProjectName}-*` tables |
| DRS | Describe* operations | All resources (no resource-level support) |
| EC2 | Describe* operations | All resources (no resource-level support) |
| IAM | ListInstanceProfiles | All resources |
| STS | AssumeRole | Cross-account DRS roles with ExternalId |
| Lambda | InvokeFunction | Execution Handler only |
| CloudWatch | GetMetricData, GetMetricStatistics | All resources |

### DynamoDB Permissions

**Allowed Operations**:
- `dynamodb:GetItem` - Retrieve single item by primary key
- `dynamodb:Query` - Query items using primary key or GSI
- `dynamodb:Scan` - Scan entire table (use sparingly)
- `dynamodb:BatchGetItem` - Retrieve multiple items in single request

**Resource Restriction**:
```
arn:aws:dynamodb:{Region}:{AccountId}:table/{ProjectName}-*
```

**Example Allowed Resources**:
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-protection-groups-test`
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-recovery-plans-test`
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-execution-history-test`

**Example Denied Resources**:
- `arn:aws:dynamodb:us-east-2:438465159935:table/other-project-table` (doesn't match pattern)
- Any table not prefixed with `{ProjectName}-`

**Denied Operations**:
- `dynamodb:PutItem` - Cannot create items
- `dynamodb:UpdateItem` - Cannot modify items
- `dynamodb:DeleteItem` - Cannot delete items
- `dynamodb:BatchWriteItem` - Cannot batch write items

### DRS Permissions

**Allowed Operations**:
- `drs:DescribeSourceServers` - List and describe source servers
- `drs:DescribeJobs` - List and describe recovery jobs
- `drs:DescribeRecoveryInstances` - List and describe recovery instances
- `drs:DescribeRecoverySnapshots` - List and describe recovery snapshots
- `drs:GetLaunchConfiguration` - Retrieve launch configuration
- `drs:GetReplicationConfiguration` - Retrieve replication configuration
- `drs:ListTagsForResource` - List tags on DRS resources

**Resource Restriction**: None (DRS Describe* operations do not support resource-level permissions per AWS service limitations)

**Denied Operations**:
- `drs:StartRecovery` - Cannot initiate disaster recovery
- `drs:TerminateRecoveryInstances` - Cannot terminate recovery instances
- `drs:CreateRecoveryInstanceForDrs` - Cannot create recovery instances
- `drs:UpdateLaunchConfiguration` - Cannot modify launch configuration
- `drs:TagResource` - Cannot add tags
- `drs:UntagResource` - Cannot remove tags

### EC2 Permissions

**Allowed Operations**:
- `ec2:DescribeInstances` - List and describe EC2 instances
- `ec2:DescribeSubnets` - List and describe VPC subnets
- `ec2:DescribeSecurityGroups` - List and describe security groups
- `ec2:DescribeVpcs` - List and describe VPCs
- `ec2:DescribeAvailabilityZones` - List availability zones
- `ec2:DescribeInstanceTypes` - List available instance types

**Resource Restriction**: None (EC2 Describe* operations do not support resource-level permissions)

**Denied Operations**:
- `ec2:RunInstances` - Cannot launch instances
- `ec2:TerminateInstances` - Cannot terminate instances
- `ec2:CreateTags` - Cannot add tags
- `ec2:CreateLaunchTemplate` - Cannot create launch templates

### Lambda Permissions

**Allowed Operations**:
- `lambda:InvokeFunction` - Invoke Execution Handler for async operations

**Resource Restriction**:
```
arn:aws:lambda:{Region}:{AccountId}:function:{ProjectName}-execution-handler-{Environment}
```

**Example Allowed Resource**:
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-execution-handler-test`

**Example Denied Resources**:
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-data-management-handler-test` (wrong function)
- `arn:aws:lambda:us-east-2:438465159935:function:other-project-function` (wrong project)

### STS Permissions

**Allowed Operations**:
- `sts:AssumeRole` - Assume cross-account DRS roles

**Resource Restriction**:
```
arn:aws:iam::*:role/DRSOrchestrationRole
```

**Condition Key**:
```yaml
Condition:
  StringEquals:
    sts:ExternalId: !Sub "${ProjectName}-${Environment}"
```

**Example Allowed Operation**:
```python
sts.assume_role(
    RoleArn='arn:aws:iam::123456789012:role/DRSOrchestrationRole',
    RoleSessionName='query-handler',
    ExternalId='aws-drs-orchestration-test'  # Matches {ProjectName}-{Environment}
)
```

**Example Denied Operation**:
```python
sts.assume_role(
    RoleArn='arn:aws:iam::123456789012:role/DRSOrchestrationRole',
    RoleSessionName='query-handler',
    ExternalId='wrong-external-id'  # Doesn't match
)
```

### CloudWatch Permissions

**Allowed Operations**:
- `cloudwatch:GetMetricData` - Retrieve metric data points
- `cloudwatch:GetMetricStatistics` - Retrieve metric statistics

**Resource Restriction**: None (CloudWatch metrics do not support resource-level permissions)

### Security Controls

**Read-Only Enforcement**:
- NO write, update, or delete permissions on any service
- NO DRS recovery operations (StartRecovery, TerminateRecoveryInstances)
- NO DynamoDB write operations (PutItem, UpdateItem, DeleteItem)
- NO EC2 instance operations (RunInstances, TerminateInstances)

**Resource-Level Restrictions**:
- DynamoDB operations restricted to `{ProjectName}-*` tables
- Lambda invocation restricted to Execution Handler only
- STS AssumeRole requires ExternalId matching `{ProjectName}-{Environment}`

**Blast Radius**:
- **Minimal**: Compromised Query Handler can only read data, not modify or execute recovery operations
- **Impact**: Information disclosure only, no data loss or service disruption


---

## 2. Data Management Role

**Role Name**: `{ProjectName}-data-management-role-{Environment}`

**Lambda Function**: Data Management Handler

**Purpose**: Provides DynamoDB CRUD operations and DRS metadata management without recovery execution capabilities. This role can create, read, update, and delete DynamoDB items, and manage DRS tags and extended source servers, but cannot execute disaster recovery operations.

### Permissions Summary

| Service | Operations | Resource Scope |
|---------|-----------|----------------|
| DynamoDB | Full CRUD (GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan, BatchGetItem, BatchWriteItem) | `{ProjectName}-*` tables |
| DRS | Describe* operations, TagResource, UntagResource, CreateExtendedSourceServer | All resources (Describe*), specific resources (Tag*) |
| Lambda | InvokeFunction | Self-invocation only |
| EventBridge | DescribeRule, PutRule | `{ProjectName}-*` rules |
| STS | AssumeRole | Cross-account DRS roles with ExternalId |
| CloudWatch | PutMetricData | All resources |

### DynamoDB Permissions

**Allowed Operations**:
- `dynamodb:GetItem` - Retrieve single item by primary key
- `dynamodb:PutItem` - Create new item or replace existing item
- `dynamodb:UpdateItem` - Modify existing item attributes
- `dynamodb:DeleteItem` - Delete item by primary key
- `dynamodb:Query` - Query items using primary key or GSI
- `dynamodb:Scan` - Scan entire table
- `dynamodb:BatchGetItem` - Retrieve multiple items in single request
- `dynamodb:BatchWriteItem` - Create or delete multiple items in single request

**Resource Restriction**:
```
arn:aws:dynamodb:{Region}:{AccountId}:table/{ProjectName}-*
```

**Example Allowed Resources**:
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-protection-groups-test`
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-recovery-plans-test`
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-execution-history-test`
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-target-accounts-test`

**Example Denied Resources**:
- `arn:aws:dynamodb:us-east-2:438465159935:table/other-project-table` (doesn't match pattern)

### DRS Permissions

**Allowed Operations**:
- `drs:DescribeSourceServers` - List and describe source servers
- `drs:DescribeJobs` - List and describe recovery jobs
- `drs:DescribeRecoveryInstances` - List and describe recovery instances
- `drs:TagResource` - Add tags to DRS resources
- `drs:UntagResource` - Remove tags from DRS resources
- `drs:CreateExtendedSourceServer` - Create extended source server metadata
- `drs:ListTagsForResource` - List tags on DRS resources

**Resource Restriction**: None for Describe* operations (AWS service limitation), specific resource ARNs for Tag* operations

**Denied Operations**:
- `drs:StartRecovery` - Cannot initiate disaster recovery
- `drs:TerminateRecoveryInstances` - Cannot terminate recovery instances
- `drs:CreateRecoveryInstanceForDrs` - Cannot create recovery instances
- `drs:UpdateLaunchConfiguration` - Cannot modify launch configuration
- `drs:DisconnectRecoveryInstance` - Cannot disconnect recovery instances

**Security Rationale**: Data Management Handler manages metadata and tags but cannot execute recovery operations, reducing blast radius if compromised.

### Lambda Permissions

**Allowed Operations**:
- `lambda:InvokeFunction` - Invoke itself for async tag sync operations

**Resource Restriction**:
```
arn:aws:lambda:{Region}:{AccountId}:function:{ProjectName}-data-management-handler-{Environment}
```

**Example Allowed Resource**:
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-data-management-handler-test`

**Example Denied Resources**:
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-query-handler-test` (different function)
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-execution-handler-test` (different function)

**Use Case**: Self-invocation for async tag synchronization operations that may take longer than API Gateway timeout.

### EventBridge Permissions

**Allowed Operations**:
- `events:DescribeRule` - Retrieve EventBridge rule configuration
- `events:PutRule` - Create or update EventBridge rule for tag sync schedule

**Resource Restriction**:
```
arn:aws:events:{Region}:{AccountId}:rule/{ProjectName}-*
```

**Example Allowed Resources**:
- `arn:aws:events:us-east-2:438465159935:rule/aws-drs-orchestration-tag-sync-schedule-test`

**Example Denied Resources**:
- `arn:aws:events:us-east-2:438465159935:rule/other-project-rule` (doesn't match pattern)

### STS Permissions

**Allowed Operations**:
- `sts:AssumeRole` - Assume cross-account DRS roles

**Resource Restriction**:
```
arn:aws:iam::*:role/DRSOrchestrationRole
```

**Condition Key**:
```yaml
Condition:
  StringEquals:
    sts:ExternalId: !Sub "${ProjectName}-${Environment}"
```

### CloudWatch Permissions

**Allowed Operations**:
- `cloudwatch:PutMetricData` - Publish custom metrics for monitoring

**Resource Restriction**: None (CloudWatch metrics do not support resource-level permissions)

### Security Controls

**Write Operations Allowed**:
- DynamoDB: Full CRUD on project tables
- DRS: Tag management and extended source server creation
- EventBridge: Rule management for tag sync

**Write Operations Denied**:
- DRS recovery operations (StartRecovery, TerminateRecoveryInstances, CreateRecoveryInstanceForDrs)
- Lambda invocation of other functions (only self-invocation)
- DynamoDB operations on non-project tables

**Resource-Level Restrictions**:
- DynamoDB operations restricted to `{ProjectName}-*` tables
- Lambda invocation restricted to self only
- EventBridge operations restricted to `{ProjectName}-*` rules
- STS AssumeRole requires ExternalId matching `{ProjectName}-{Environment}`

**Blast Radius**:
- **Medium**: Compromised Data Management Handler can modify DynamoDB data and DRS tags, but cannot execute recovery operations
- **Impact**: Data corruption possible, but no disaster recovery execution or instance termination


---

## 3. Execution Handler Role

**Role Name**: `{ProjectName}-execution-handler-role-{Environment}`

**Lambda Function**: Execution Handler

**Purpose**: Orchestrates Step Functions workflows, sends SNS notifications, and coordinates recovery operations without direct DRS write access. This role manages the execution lifecycle but delegates actual recovery operations to the Orchestration Function.

### Permissions Summary

| Service | Operations | Resource Scope |
|---------|-----------|----------------|
| Step Functions | StartExecution, DescribeExecution, SendTaskSuccess, SendTaskFailure, SendTaskHeartbeat | `{ProjectName}-*` state machines |
| SNS | Publish, Subscribe, Unsubscribe, ListSubscriptionsByTopic, SetSubscriptionAttributes | `{ProjectName}-*` topics |
| DynamoDB | Full CRUD | `{ProjectName}-*` tables |
| DRS | Describe* operations, StartRecovery, TerminateRecoveryInstances, UpdateLaunchConfiguration, GetLaunchConfiguration | All resources (Describe*), specific resources (write operations) |
| EC2 | DescribeInstances, TerminateInstances, CreateTags | All resources (Describe*), specific instances (write operations) |
| Lambda | InvokeFunction | Data Management Handler only |
| STS | AssumeRole | Cross-account DRS roles with ExternalId |
| CloudWatch | PutMetricData | All resources |

### Step Functions Permissions

**Allowed Operations**:
- `states:StartExecution` - Start new state machine execution
- `states:DescribeExecution` - Retrieve execution status and details
- `states:SendTaskSuccess` - Signal task completion with success
- `states:SendTaskFailure` - Signal task completion with failure
- `states:SendTaskHeartbeat` - Send heartbeat to prevent task timeout

**Resource Restriction**:
```
arn:aws:states:{Region}:{AccountId}:stateMachine:{ProjectName}-*
arn:aws:states:{Region}:{AccountId}:execution:{ProjectName}-*:*
```

**Example Allowed Resources**:
- `arn:aws:states:us-east-2:438465159935:stateMachine:aws-drs-orchestration-dr-orch-sf-test`
- `arn:aws:states:us-east-2:438465159935:execution:aws-drs-orchestration-dr-orch-sf-test:12345678-1234-1234-1234-123456789012`

**Example Denied Resources**:
- `arn:aws:states:us-east-2:438465159935:stateMachine:other-project-state-machine` (doesn't match pattern)

### SNS Permissions

**Allowed Operations**:
- `sns:Publish` - Send notification messages to topics
- `sns:Subscribe` - Create subscription to topic
- `sns:Unsubscribe` - Remove subscription from topic
- `sns:ListSubscriptionsByTopic` - List all subscriptions for a topic
- `sns:SetSubscriptionAttributes` - Modify subscription attributes (e.g., filter policy)

**Resource Restriction**:
```
arn:aws:sns:{Region}:{AccountId}:{ProjectName}-*
```

**Example Allowed Resources**:
- `arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-execution-alerts-test`
- `arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-security-alerts-test`

**Example Denied Resources**:
- `arn:aws:sns:us-east-2:438465159935:other-project-topic` (doesn't match pattern)

### DynamoDB Permissions

**Allowed Operations**:
- Full CRUD: GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan, BatchGetItem, BatchWriteItem

**Resource Restriction**:
```
arn:aws:dynamodb:{Region}:{AccountId}:table/{ProjectName}-*
```

**Use Case**: Update execution history, recovery plan status, and protection group state during orchestration.

### DRS Permissions

**Allowed Operations**:
- `drs:DescribeSourceServers` - List and describe source servers
- `drs:DescribeJobs` - List and describe recovery jobs
- `drs:DescribeRecoveryInstances` - List and describe recovery instances
- `drs:StartRecovery` - Initiate disaster recovery for source servers
- `drs:TerminateRecoveryInstances` - Terminate recovery instances
- `drs:UpdateLaunchConfiguration` - Modify launch configuration
- `drs:GetLaunchConfiguration` - Retrieve launch configuration

**Resource Restriction**: None (DRS operations do not support resource-level permissions per AWS service limitations)

**Security Note**: Execution Handler can initiate recovery operations but typically delegates to Orchestration Function for actual execution.

### EC2 Permissions

**Allowed Operations**:
- `ec2:DescribeInstances` - List and describe EC2 instances
- `ec2:TerminateInstances` - Terminate EC2 instances (recovery instances)
- `ec2:CreateTags` - Add tags to EC2 instances

**Resource Restriction**: None for Describe* operations, all instances for write operations

**Use Case**: Terminate recovery instances after drill completion, add tags for tracking.

### Lambda Permissions

**Allowed Operations**:
- `lambda:InvokeFunction` - Invoke Data Management Handler for async recovery instance sync

**Resource Restriction**:
```
arn:aws:lambda:{Region}:{AccountId}:function:{ProjectName}-data-management-handler-{Environment}
```

**Example Allowed Resource**:
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-data-management-handler-test`

**Example Denied Resources**:
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-query-handler-test` (different function)

### STS Permissions

**Allowed Operations**:
- `sts:AssumeRole` - Assume cross-account DRS roles

**Resource Restriction**:
```
arn:aws:iam::*:role/DRSOrchestrationRole
```

**Condition Key**:
```yaml
Condition:
  StringEquals:
    sts:ExternalId: !Sub "${ProjectName}-${Environment}"
```

### CloudWatch Permissions

**Allowed Operations**:
- `cloudwatch:PutMetricData` - Publish custom metrics for monitoring

**Resource Restriction**: None (CloudWatch metrics do not support resource-level permissions)

### Security Controls

**Orchestration Capabilities**:
- Step Functions: Full execution lifecycle management
- SNS: Full notification management
- DynamoDB: Full CRUD for execution tracking
- DRS: Recovery initiation and termination
- EC2: Instance termination and tagging

**Resource-Level Restrictions**:
- Step Functions operations restricted to `{ProjectName}-*` state machines
- SNS operations restricted to `{ProjectName}-*` topics
- DynamoDB operations restricted to `{ProjectName}-*` tables
- Lambda invocation restricted to Data Management Handler only
- STS AssumeRole requires ExternalId matching `{ProjectName}-{Environment}`

**Blast Radius**:
- **High**: Compromised Execution Handler can initiate recovery operations, terminate instances, and modify execution state
- **Impact**: Service disruption possible through unauthorized recovery execution or instance termination
- **Mitigation**: CloudWatch alarms detect unauthorized operations, Step Functions provides audit trail


---

## 4. Orchestration Role

**Role Name**: `{ProjectName}-orchestration-role-{Environment}`

**Lambda Function**: DR Orchestration Step Function (Orchestration Function)

**Purpose**: Provides comprehensive DRS and EC2 permissions for executing disaster recovery operations with additional security controls. This is the most privileged role, responsible for actual recovery instance creation, launch template management, and recovery execution.

### Permissions Summary

| Service | Operations | Resource Scope |
|---------|-----------|----------------|
| DRS | All read operations (Describe*, Get*, List*) and write operations (StartRecovery, CreateRecoveryInstanceForDrs, TerminateRecoveryInstances, DisconnectRecoveryInstance, UpdateLaunchConfiguration, TagResource, UntagResource) | All resources (AWS service limitation) |
| EC2 | Comprehensive operations including DescribeInstances, RunInstances, TerminateInstances, CreateLaunchTemplate, CreateLaunchTemplateVersion, CreateTags, CreateVolume, CreateNetworkInterface | All resources (Describe*), specific resources (write operations) |
| IAM | PassRole | Restricted to drs.amazonaws.com and ec2.amazonaws.com via condition key |
| STS | AssumeRole | Cross-account DRS roles with ExternalId |
| KMS | DescribeKey, CreateGrant | Restricted to EC2 and DRS services via condition key |
| SSM | CreateOpsItem, SendCommand, GetParameter | All resources |
| SNS | Publish | `{ProjectName}-*` topics |
| DynamoDB | GetItem, PutItem, UpdateItem, Query, Scan | `{ProjectName}-*` tables |
| CloudWatch | PutMetricData | All resources |
| Lambda | InvokeFunction | Execution Handler and Query Handler only |

### DRS Permissions

**Allowed Read Operations**:
- `drs:DescribeSourceServers` - List and describe source servers
- `drs:DescribeJobs` - List and describe recovery jobs
- `drs:DescribeRecoveryInstances` - List and describe recovery instances
- `drs:DescribeRecoverySnapshots` - List and describe recovery snapshots
- `drs:GetLaunchConfiguration` - Retrieve launch configuration
- `drs:GetReplicationConfiguration` - Retrieve replication configuration
- `drs:ListTagsForResource` - List tags on DRS resources

**Allowed Write Operations**:
- `drs:StartRecovery` - Initiate disaster recovery for source servers
- `drs:CreateRecoveryInstanceForDrs` - Create recovery instance from source server
- `drs:TerminateRecoveryInstances` - Terminate recovery instances
- `drs:DisconnectRecoveryInstance` - Disconnect recovery instance from source
- `drs:UpdateLaunchConfiguration` - Modify launch configuration
- `drs:TagResource` - Add tags to DRS resources
- `drs:UntagResource` - Remove tags from DRS resources

**Resource Restriction**: None (DRS operations do not support resource-level permissions per AWS service limitations)

**Condition Key for Write Operations**:
```yaml
Condition:
  StringEquals:
    aws:RequestedRegion: !Ref AWS::Region
```

**Security Rationale**: DRS write operations are restricted to the deployment region to prevent accidental cross-region recovery execution.

**Example Allowed Operation**:
```python
# In us-east-2 deployment
drs.start_recovery(
    sourceServers=[{'sourceServerID': 's-1234567890abcdef0'}]
)  # Succeeds because aws:RequestedRegion matches deployment region
```

**Example Denied Operation**:
```python
# In us-east-2 deployment, attempting operation in us-west-2
drs_west = boto3.client('drs', region_name='us-west-2')
drs_west.start_recovery(
    sourceServers=[{'sourceServerID': 's-1234567890abcdef0'}]
)  # Fails because aws:RequestedRegion doesn't match deployment region
```

### EC2 Permissions

**Allowed Read Operations**:
- `ec2:DescribeInstances` - List and describe EC2 instances
- `ec2:DescribeSubnets` - List and describe VPC subnets
- `ec2:DescribeSecurityGroups` - List and describe security groups
- `ec2:DescribeVpcs` - List and describe VPCs
- `ec2:DescribeAvailabilityZones` - List availability zones
- `ec2:DescribeInstanceTypes` - List available instance types
- `ec2:DescribeLaunchTemplates` - List and describe launch templates
- `ec2:DescribeLaunchTemplateVersions` - List launch template versions

**Allowed Write Operations**:
- `ec2:RunInstances` - Launch EC2 instances (recovery instances)
- `ec2:TerminateInstances` - Terminate EC2 instances
- `ec2:CreateLaunchTemplate` - Create launch template for recovery instances
- `ec2:CreateLaunchTemplateVersion` - Create new version of launch template
- `ec2:CreateTags` - Add tags to EC2 resources
- `ec2:CreateVolume` - Create EBS volumes for recovery instances
- `ec2:CreateNetworkInterface` - Create network interfaces for recovery instances

**Resource Restriction**: None for Describe* operations, all resources for write operations

**Use Case**: Create launch templates for recovery instances, launch recovery instances with specific configurations, terminate instances after drill completion.

### IAM Permissions

**Allowed Operations**:
- `iam:PassRole` - Pass IAM role to DRS and EC2 services

**Resource Restriction**: All roles

**Condition Key**:
```yaml
Condition:
  StringEquals:
    iam:PassedToService:
      - drs.amazonaws.com
      - ec2.amazonaws.com
```

**Security Rationale**: PassRole is restricted to DRS and EC2 services only, preventing the Orchestration Function from passing roles to other services.

**Example Allowed Operation**:
```python
ec2.run_instances(
    ImageId='ami-12345678',
    InstanceType='t3.medium',
    IamInstanceProfile={'Arn': 'arn:aws:iam::123456789012:instance-profile/MyProfile'}
)  # Succeeds because role is passed to ec2.amazonaws.com
```

**Example Denied Operation**:
```python
lambda_client.create_function(
    FunctionName='my-function',
    Role='arn:aws:iam::123456789012:role/MyRole'
)  # Fails because role is passed to lambda.amazonaws.com (not allowed)
```

### KMS Permissions

**Allowed Operations**:
- `kms:DescribeKey` - Retrieve KMS key metadata
- `kms:CreateGrant` - Create grant for EC2 and DRS to use KMS key

**Resource Restriction**: All KMS keys

**Condition Key**:
```yaml
Condition:
  StringEquals:
    kms:ViaService:
      - !Sub "ec2.${AWS::Region}.amazonaws.com"
      - !Sub "drs.${AWS::Region}.amazonaws.com"
```

**Security Rationale**: KMS operations are restricted to EC2 and DRS services only, preventing direct KMS key usage by the Orchestration Function.

**Example Allowed Operation**:
```python
# EC2 uses KMS key to encrypt EBS volume
ec2.run_instances(
    ImageId='ami-12345678',
    BlockDeviceMappings=[{
        'DeviceName': '/dev/sda1',
        'Ebs': {
            'Encrypted': True,
            'KmsKeyId': 'arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012'
        }
    }]
)  # Succeeds because KMS is accessed via ec2.amazonaws.com
```

**Example Denied Operation**:
```python
# Direct KMS key usage
kms.encrypt(
    KeyId='arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012',
    Plaintext=b'sensitive data'
)  # Fails because KMS is not accessed via ec2 or drs service
```

### SSM Permissions

**Allowed Operations**:
- `ssm:CreateOpsItem` - Create OpsCenter item for incident tracking
- `ssm:SendCommand` - Send command to EC2 instances via Systems Manager
- `ssm:GetParameter` - Retrieve parameter from Parameter Store

**Resource Restriction**: None (SSM operations do not support resource-level permissions for these actions)

**Use Case**: Create OpsCenter items for recovery failures, send commands to recovery instances for validation, retrieve configuration parameters.

### SNS Permissions

**Allowed Operations**:
- `sns:Publish` - Send notification messages to topics

**Resource Restriction**:
```
arn:aws:sns:{Region}:{AccountId}:{ProjectName}-*
```

**Example Allowed Resources**:
- `arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-execution-alerts-test`

**Example Denied Resources**:
- `arn:aws:sns:us-east-2:438465159935:other-project-topic` (doesn't match pattern)

### DynamoDB Permissions

**Allowed Operations**:
- `dynamodb:GetItem` - Retrieve single item by primary key
- `dynamodb:PutItem` - Create new item or replace existing item
- `dynamodb:UpdateItem` - Modify existing item attributes
- `dynamodb:Query` - Query items using primary key or GSI
- `dynamodb:Scan` - Scan entire table

**Resource Restriction**:
```
arn:aws:dynamodb:{Region}:{AccountId}:table/{ProjectName}-*
```

**Use Case**: Update execution history, recovery plan status, and protection group state during recovery operations.

### Lambda Permissions

**Allowed Operations**:
- `lambda:InvokeFunction` - Invoke Execution Handler and Query Handler

**Resource Restriction**:
```
arn:aws:lambda:{Region}:{AccountId}:function:{ProjectName}-execution-handler-{Environment}
arn:aws:lambda:{Region}:{AccountId}:function:{ProjectName}-query-handler-{Environment}
```

**Example Allowed Resources**:
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-execution-handler-test`
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-query-handler-test`

**Example Denied Resources**:
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-data-management-handler-test` (different function)

### STS Permissions

**Allowed Operations**:
- `sts:AssumeRole` - Assume cross-account DRS roles

**Resource Restriction**:
```
arn:aws:iam::*:role/DRSOrchestrationRole
```

**Condition Key**:
```yaml
Condition:
  StringEquals:
    sts:ExternalId: !Sub "${ProjectName}-${Environment}"
```

### CloudWatch Permissions

**Allowed Operations**:
- `cloudwatch:PutMetricData` - Publish custom metrics for monitoring

**Resource Restriction**: None (CloudWatch metrics do not support resource-level permissions)

### Security Controls

**Comprehensive Recovery Capabilities**:
- DRS: All read and write operations for disaster recovery
- EC2: Instance launch, termination, launch template management
- IAM: PassRole restricted to DRS and EC2 services
- KMS: Key operations restricted to EC2 and DRS services
- SSM: OpsCenter, Run Command, Parameter Store access

**IAM Condition Keys**:
- DRS write operations: `aws:RequestedRegion` matching deployment region
- IAM PassRole: `iam:PassedToService` restricted to `drs.amazonaws.com` and `ec2.amazonaws.com`
- KMS operations: `kms:ViaService` restricted to `ec2.{Region}.amazonaws.com` and `drs.{Region}.amazonaws.com`
- STS AssumeRole: `sts:ExternalId` matching `{ProjectName}-{Environment}`

**Resource-Level Restrictions**:
- DynamoDB operations restricted to `{ProjectName}-*` tables
- SNS operations restricted to `{ProjectName}-*` topics
- Lambda invocation restricted to Execution Handler and Query Handler only

**Blast Radius**:
- **Critical**: Compromised Orchestration Role can execute full disaster recovery operations, launch/terminate instances, and modify launch configurations
- **Impact**: Complete service disruption possible through unauthorized recovery execution, instance termination, or launch template modification
- **Mitigation**: 
  - IAM condition keys restrict operations to deployment region and specific services
  - CloudWatch alarms detect unauthorized operations
  - Step Functions provides complete audit trail
  - ExternalId validation prevents unauthorized cross-account access


---

## 5. Frontend Deployer Role

**Role Name**: `{ProjectName}-frontend-deployer-role-{Environment}`

**Lambda Function**: Frontend Deployer

**Purpose**: Provides S3, CloudFront, and CloudFormation permissions for frontend deployment and versioned bucket cleanup. This role is completely isolated from DRS, DynamoDB, and disaster recovery operations.

### Permissions Summary

| Service | Operations | Resource Scope |
|---------|-----------|----------------|
| S3 | ListBucket, ListBucketVersions, GetObject, GetBucketLocation, PutObject, PutObjectAcl, DeleteObject, DeleteObjectVersion | `{ProjectName}-*-fe-*` buckets |
| CloudFront | CreateInvalidation, GetInvalidation, ListInvalidations, GetDistribution | Distributions with tag `Project={ProjectName}` |
| CloudFormation | DescribeStacks | `{ProjectName}-*` stacks |
| CloudWatch | PutMetricData | All resources |

### S3 Permissions

**Allowed Operations**:
- `s3:ListBucket` - List objects in bucket
- `s3:ListBucketVersions` - List object versions in versioned bucket
- `s3:GetObject` - Retrieve object from bucket
- `s3:GetBucketLocation` - Get bucket region
- `s3:PutObject` - Upload object to bucket
- `s3:PutObjectAcl` - Set object ACL (for public read access)
- `s3:DeleteObject` - Delete object from bucket
- `s3:DeleteObjectVersion` - Delete specific object version (for versioned bucket cleanup)

**Resource Restriction**:
```
arn:aws:s3:::{ProjectName}-*-fe-*
arn:aws:s3:::{ProjectName}-*-fe-*/*
```

**Example Allowed Resources**:
- `arn:aws:s3:::aws-drs-orchestration-438465159935-fe-test` (bucket)
- `arn:aws:s3:::aws-drs-orchestration-438465159935-fe-test/*` (objects)
- `arn:aws:s3:::aws-drs-orchestration-438465159935-fe-qa` (bucket)
- `arn:aws:s3:::aws-drs-orchestration-438465159935-fe-qa/*` (objects)

**Example Denied Resources**:
- `arn:aws:s3:::aws-drs-orchestration-438465159935-test` (deployment bucket, not frontend)
- `arn:aws:s3:::other-project-fe-bucket` (doesn't match pattern)

**Use Case**: Deploy frontend build artifacts, clean up old object versions to reduce storage costs, set public read ACLs for static website hosting.

**Versioned Bucket Cleanup**:
The Frontend Deployer includes `DeleteObjectVersion` permission to clean up old object versions in versioned S3 buckets. This is critical for cost management as versioned buckets retain all object versions indefinitely by default.

```python
# Example: Clean up old versions
s3 = boto3.client('s3')
versions = s3.list_object_versions(Bucket='aws-drs-orchestration-438465159935-fe-test')

for version in versions.get('Versions', []):
    if not version.get('IsLatest'):
        s3.delete_object(
            Bucket='aws-drs-orchestration-438465159935-fe-test',
            Key=version['Key'],
            VersionId=version['VersionId']
        )
```

### CloudFront Permissions

**Allowed Operations**:
- `cloudfront:CreateInvalidation` - Invalidate cached objects in distribution
- `cloudfront:GetInvalidation` - Retrieve invalidation status
- `cloudfront:ListInvalidations` - List all invalidations for distribution
- `cloudfront:GetDistribution` - Retrieve distribution configuration

**Resource Restriction**: Distributions with tag `Project={ProjectName}`

**Example Allowed Resources**:
- CloudFront distribution with tag `Project=aws-drs-orchestration`

**Example Denied Resources**:
- CloudFront distribution without `Project` tag
- CloudFront distribution with tag `Project=other-project`

**Use Case**: Invalidate CloudFront cache after frontend deployment to ensure users receive latest version.

```python
# Example: Create invalidation
cloudfront = boto3.client('cloudfront')
cloudfront.create_invalidation(
    DistributionId='E1234567890ABC',
    InvalidationBatch={
        'Paths': {
            'Quantity': 1,
            'Items': ['/*']
        },
        'CallerReference': str(time.time())
    }
)
```

### CloudFormation Permissions

**Allowed Operations**:
- `cloudformation:DescribeStacks` - Retrieve stack status and outputs

**Resource Restriction**:
```
arn:aws:cloudformation:{Region}:{AccountId}:stack/{ProjectName}-*/*
```

**Example Allowed Resources**:
- `arn:aws:cloudformation:us-east-2:438465159935:stack/aws-drs-orchestration-test/*`
- `arn:aws:cloudformation:us-east-2:438465159935:stack/aws-drs-orchestration-qa/*`

**Example Denied Resources**:
- `arn:aws:cloudformation:us-east-2:438465159935:stack/other-project-stack/*` (doesn't match pattern)

**Use Case**: Check stack status during DELETE operations to determine when frontend bucket can be safely cleaned up.

### CloudWatch Permissions

**Allowed Operations**:
- `cloudwatch:PutMetricData` - Publish custom metrics for monitoring

**Resource Restriction**: None (CloudWatch metrics do not support resource-level permissions)

**Use Case**: Publish deployment metrics (duration, object count, invalidation time).

### Security Controls

**Frontend-Only Operations**:
- S3: Full CRUD on frontend buckets including versioned object cleanup
- CloudFront: Invalidation and distribution management
- CloudFormation: Read-only stack status checks

**Complete Isolation from Core Services**:
- NO DRS permissions (cannot access source servers or recovery operations)
- NO EC2 permissions (cannot access instances)
- NO DynamoDB permissions (cannot access protection groups or recovery plans)
- NO Step Functions permissions (cannot access orchestration workflows)
- NO SNS permissions (cannot send notifications)
- NO Lambda permissions (cannot invoke other functions)

**Resource-Level Restrictions**:
- S3 operations restricted to `{ProjectName}-*-fe-*` buckets only
- CloudFront operations restricted to distributions with tag `Project={ProjectName}`
- CloudFormation operations restricted to `{ProjectName}-*` stacks

**Blast Radius**:
- **Minimal**: Compromised Frontend Deployer can only modify frontend static assets and invalidate CloudFront cache
- **Impact**: Website defacement possible, but no access to backend data, DRS operations, or disaster recovery capabilities
- **Mitigation**: S3 bucket versioning enables rollback to previous frontend version, CloudFront invalidation is logged in CloudTrail


---

## IAM Condition Keys Reference

IAM condition keys provide additional security controls beyond resource-level permissions. The function-specific IAM roles use several condition keys to enforce security policies.

### aws:RequestedRegion

**Purpose**: Restricts DRS write operations to the deployment region only.

**Applied To**: Orchestration Role - DRS write operations

**Condition**:
```yaml
Condition:
  StringEquals:
    aws:RequestedRegion: !Ref AWS::Region
```

**Effect**: DRS write operations (StartRecovery, CreateRecoveryInstanceForDrs, TerminateRecoveryInstances) can only be executed in the deployment region.

**Example Allowed Operation**:
```python
# In us-east-2 deployment
drs = boto3.client('drs', region_name='us-east-2')
drs.start_recovery(
    sourceServers=[{'sourceServerID': 's-1234567890abcdef0'}]
)  # Succeeds - region matches deployment region
```

**Example Denied Operation**:
```python
# In us-east-2 deployment, attempting operation in us-west-2
drs_west = boto3.client('drs', region_name='us-west-2')
drs_west.start_recovery(
    sourceServers=[{'sourceServerID': 's-1234567890abcdef0'}]
)  # Fails - region doesn't match deployment region
```

**Security Rationale**: Prevents accidental cross-region recovery execution, which could launch instances in unexpected regions and incur unexpected costs.

### iam:PassedToService

**Purpose**: Restricts IAM PassRole to DRS and EC2 services only.

**Applied To**: Orchestration Role - IAM PassRole permission

**Condition**:
```yaml
Condition:
  StringEquals:
    iam:PassedToService:
      - drs.amazonaws.com
      - ec2.amazonaws.com
```

**Effect**: The Orchestration Function can only pass IAM roles to DRS and EC2 services, not to other AWS services.

**Example Allowed Operation**:
```python
# Pass role to EC2 for instance profile
ec2.run_instances(
    ImageId='ami-12345678',
    InstanceType='t3.medium',
    IamInstanceProfile={'Arn': 'arn:aws:iam::123456789012:instance-profile/MyProfile'}
)  # Succeeds - role passed to ec2.amazonaws.com
```

**Example Denied Operation**:
```python
# Attempt to pass role to Lambda
lambda_client.create_function(
    FunctionName='my-function',
    Role='arn:aws:iam::123456789012:role/MyRole'
)  # Fails - role passed to lambda.amazonaws.com (not allowed)
```

**Security Rationale**: Prevents privilege escalation by restricting which services can receive IAM roles from the Orchestration Function.

### kms:ViaService

**Purpose**: Restricts KMS operations to EC2 and DRS services only.

**Applied To**: Orchestration Role - KMS DescribeKey and CreateGrant permissions

**Condition**:
```yaml
Condition:
  StringEquals:
    kms:ViaService:
      - !Sub "ec2.${AWS::Region}.amazonaws.com"
      - !Sub "drs.${AWS::Region}.amazonaws.com"
```

**Effect**: KMS operations can only be performed when called by EC2 or DRS services, not directly by the Orchestration Function.

**Example Allowed Operation**:
```python
# EC2 uses KMS key to encrypt EBS volume
ec2.run_instances(
    ImageId='ami-12345678',
    BlockDeviceMappings=[{
        'DeviceName': '/dev/sda1',
        'Ebs': {
            'Encrypted': True,
            'KmsKeyId': 'arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012'
        }
    }]
)  # Succeeds - KMS accessed via ec2.amazonaws.com
```

**Example Denied Operation**:
```python
# Direct KMS key usage
kms.encrypt(
    KeyId='arn:aws:kms:us-east-2:123456789012:key/12345678-1234-1234-1234-123456789012',
    Plaintext=b'sensitive data'
)  # Fails - KMS not accessed via ec2 or drs service
```

**Security Rationale**: Prevents direct KMS key usage by the Orchestration Function, ensuring KMS keys are only used for their intended purpose (EBS encryption, DRS snapshot encryption).

### sts:ExternalId

**Purpose**: Validates cross-account role assumption with a shared secret.

**Applied To**: All roles with cross-account access - STS AssumeRole permission

**Condition**:
```yaml
Condition:
  StringEquals:
    sts:ExternalId: !Sub "${ProjectName}-${Environment}"
```

**Effect**: Cross-account role assumption requires the ExternalId to match `{ProjectName}-{Environment}`.

**Example Allowed Operation**:
```python
# Assume cross-account role with correct ExternalId
sts.assume_role(
    RoleArn='arn:aws:iam::123456789012:role/DRSOrchestrationRole',
    RoleSessionName='orchestration',
    ExternalId='aws-drs-orchestration-test'  # Matches {ProjectName}-{Environment}
)  # Succeeds
```

**Example Denied Operation**:
```python
# Assume cross-account role with incorrect ExternalId
sts.assume_role(
    RoleArn='arn:aws:iam::123456789012:role/DRSOrchestrationRole',
    RoleSessionName='orchestration',
    ExternalId='wrong-external-id'  # Doesn't match
)  # Fails
```

**Security Rationale**: Prevents unauthorized cross-account access by requiring a shared secret (ExternalId) that both the orchestration account and workload account must know. This protects against the "confused deputy" problem where an attacker tricks the orchestration account into assuming a role in their account.

**Workload Account Trust Policy**:
```yaml
AssumeRolePolicyDocument:
  Version: "2012-10-17"
  Statement:
    - Effect: Allow
      Principal:
        AWS: !Sub "arn:aws:iam::{OrchestrationAccountId}:root"
      Action: sts:AssumeRole
      Condition:
        StringEquals:
          sts:ExternalId: !Sub "${ProjectName}-${Environment}"
```


---

## Resource ARN Patterns

All IAM policies use specific ARN patterns to restrict permissions to project resources only. This section documents the ARN patterns used across all roles.

### DynamoDB Table ARN Pattern

**Pattern**: `arn:aws:dynamodb:{Region}:{AccountId}:table/{ProjectName}-*`

**Example ARNs**:
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-protection-groups-test`
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-recovery-plans-test`
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-execution-history-test`
- `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-target-accounts-test`

**Applied To**: Query Handler Role, Data Management Role, Execution Handler Role, Orchestration Role

**Security Benefit**: Prevents access to DynamoDB tables belonging to other projects or applications.

### Lambda Function ARN Pattern

**Pattern**: `arn:aws:lambda:{Region}:{AccountId}:function:{ProjectName}-{function-name}-{Environment}`

**Example ARNs**:
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-query-handler-test`
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-data-management-handler-test`
- `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-execution-handler-test`

**Applied To**: Query Handler Role (Execution Handler only), Data Management Role (self only), Execution Handler Role (Data Management only), Orchestration Role (Execution Handler and Query Handler only)

**Security Benefit**: Prevents Lambda functions from invoking arbitrary functions, limiting lateral movement in case of compromise.

### Step Functions State Machine ARN Pattern

**Pattern**: `arn:aws:states:{Region}:{AccountId}:stateMachine:{ProjectName}-*`

**Example ARNs**:
- `arn:aws:states:us-east-2:438465159935:stateMachine:aws-drs-orchestration-dr-orch-sf-test`

**Applied To**: Execution Handler Role

**Security Benefit**: Prevents execution of state machines belonging to other projects.

### Step Functions Execution ARN Pattern

**Pattern**: `arn:aws:states:{Region}:{AccountId}:execution:{ProjectName}-*:*`

**Example ARNs**:
- `arn:aws:states:us-east-2:438465159935:execution:aws-drs-orchestration-dr-orch-sf-test:12345678-1234-1234-1234-123456789012`

**Applied To**: Execution Handler Role

**Security Benefit**: Prevents management of executions belonging to other projects.

### SNS Topic ARN Pattern

**Pattern**: `arn:aws:sns:{Region}:{AccountId}:{ProjectName}-*`

**Example ARNs**:
- `arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-execution-alerts-test`
- `arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-security-alerts-test`

**Applied To**: Execution Handler Role, Orchestration Role

**Security Benefit**: Prevents publishing to SNS topics belonging to other projects.

### EventBridge Rule ARN Pattern

**Pattern**: `arn:aws:events:{Region}:{AccountId}:rule/{ProjectName}-*`

**Example ARNs**:
- `arn:aws:events:us-east-2:438465159935:rule/aws-drs-orchestration-tag-sync-schedule-test`
- `arn:aws:events:us-east-2:438465159935:rule/aws-drs-orchestration-execution-polling-schedule-test`

**Applied To**: Data Management Role

**Security Benefit**: Prevents modification of EventBridge rules belonging to other projects.

### S3 Bucket ARN Pattern (Frontend)

**Pattern**: `arn:aws:s3:::{ProjectName}-*-fe-*`

**Example ARNs**:
- `arn:aws:s3:::aws-drs-orchestration-438465159935-fe-test` (bucket)
- `arn:aws:s3:::aws-drs-orchestration-438465159935-fe-test/*` (objects)
- `arn:aws:s3:::aws-drs-orchestration-438465159935-fe-qa` (bucket)
- `arn:aws:s3:::aws-drs-orchestration-438465159935-fe-qa/*` (objects)

**Applied To**: Frontend Deployer Role

**Security Benefit**: Restricts S3 access to frontend buckets only, preventing access to deployment buckets or other S3 resources.

### CloudFormation Stack ARN Pattern

**Pattern**: `arn:aws:cloudformation:{Region}:{AccountId}:stack/{ProjectName}-*/*`

**Example ARNs**:
- `arn:aws:cloudformation:us-east-2:438465159935:stack/aws-drs-orchestration-test/*`
- `arn:aws:cloudformation:us-east-2:438465159935:stack/aws-drs-orchestration-qa/*`

**Applied To**: Frontend Deployer Role

**Security Benefit**: Prevents access to CloudFormation stacks belonging to other projects.

### Cross-Account Role ARN Pattern

**Pattern**: `arn:aws:iam::*:role/DRSOrchestrationRole`

**Example ARNs**:
- `arn:aws:iam::123456789012:role/DRSOrchestrationRole` (workload account 1)
- `arn:aws:iam::234567890123:role/DRSOrchestrationRole` (workload account 2)

**Applied To**: Query Handler Role, Data Management Role, Execution Handler Role, Orchestration Role

**Security Benefit**: Allows cross-account access to any AWS account, but requires ExternalId validation to prevent unauthorized access.


---

## Usage Examples

This section provides practical examples of how each role is used in the DR Orchestration Platform.

### Query Handler Role - Status Query

**Scenario**: Retrieve protection group status and source server details.

```python
import boto3
import json

def lambda_handler(event, context):
    """Query Handler function - read-only operations."""
    
    # DynamoDB - Read protection group
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName='aws-drs-orchestration-protection-groups-test',
        Key={'Id': {'S': 'pg-12345'}}
    )
    protection_group = response.get('Item', {})
    
    # DRS - Describe source servers
    drs = boto3.client('drs')
    source_servers = drs.describe_source_servers(
        filters={'sourceServerIDs': ['s-1234567890abcdef0']}
    )
    
    # EC2 - Describe instances
    ec2 = boto3.client('ec2')
    instances = ec2.describe_instances(
        InstanceIds=['i-1234567890abcdef0']
    )
    
    # CloudWatch - Get metrics
    cloudwatch = boto3.client('cloudwatch')
    metrics = cloudwatch.get_metric_data(
        MetricDataQueries=[{
            'Id': 'replication_lag',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/DRS',
                    'MetricName': 'ReplicationLag',
                    'Dimensions': [{'Name': 'SourceServerID', 'Value': 's-1234567890abcdef0'}]
                },
                'Period': 300,
                'Stat': 'Average'
            }
        }],
        StartTime='2025-01-28T00:00:00Z',
        EndTime='2025-01-28T23:59:59Z'
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'protectionGroup': protection_group,
            'sourceServers': source_servers,
            'instances': instances,
            'metrics': metrics
        })
    }
```

**Allowed Operations**: All read operations succeed.

**Denied Operations**: Any write operation (PutItem, StartRecovery, TerminateInstances) fails with AccessDenied.

### Data Management Role - Protection Group Creation

**Scenario**: Create new protection group and sync tags to DRS source servers.

```python
import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    """Data Management Handler - DynamoDB CRUD and DRS metadata."""
    
    # DynamoDB - Create protection group
    dynamodb = boto3.client('dynamodb')
    dynamodb.put_item(
        TableName='aws-drs-orchestration-protection-groups-test',
        Item={
            'Id': {'S': 'pg-12345'},
            'Name': {'S': 'Production Web Servers'},
            'SourceServerIds': {'L': [
                {'S': 's-1234567890abcdef0'},
                {'S': 's-0987654321fedcba0'}
            ]},
            'CreatedAt': {'S': datetime.utcnow().isoformat()},
            'Status': {'S': 'ACTIVE'}
        }
    )
    
    # DRS - Tag source servers
    drs = boto3.client('drs')
    for server_id in ['s-1234567890abcdef0', 's-0987654321fedcba0']:
        drs.tag_resource(
            resourceArn=f'arn:aws:drs:us-east-2:438465159935:source-server/{server_id}',
            tags={
                'ProtectionGroup': 'pg-12345',
                'Environment': 'production',
                'Application': 'web-servers'
            }
        )
    
    # Lambda - Invoke self for async tag sync
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName='aws-drs-orchestration-data-management-handler-test',
        InvocationType='Event',  # Async invocation
        Payload=json.dumps({
            'operation': 'sync_tags',
            'protectionGroupId': 'pg-12345'
        })
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Protection group created successfully',
            'protectionGroupId': 'pg-12345'
        })
    }
```

**Allowed Operations**: DynamoDB CRUD, DRS tag management, self-invocation.

**Denied Operations**: DRS StartRecovery, TerminateRecoveryInstances fail with AccessDenied.

### Execution Handler Role - Recovery Orchestration

**Scenario**: Start Step Functions execution and send SNS notification.

```python
import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    """Execution Handler - orchestrate recovery workflows."""
    
    # Step Functions - Start execution
    sfn = boto3.client('stepfunctions')
    execution = sfn.start_execution(
        stateMachineArn='arn:aws:states:us-east-2:438465159935:stateMachine:aws-drs-orchestration-dr-orch-sf-test',
        name=f'recovery-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}',
        input=json.dumps({
            'protectionGroupId': 'pg-12345',
            'recoveryType': 'drill',
            'targetAccountId': '123456789012'
        })
    )
    
    # DynamoDB - Record execution
    dynamodb = boto3.client('dynamodb')
    dynamodb.put_item(
        TableName='aws-drs-orchestration-execution-history-test',
        Item={
            'ExecutionId': {'S': execution['executionArn'].split(':')[-1]},
            'ProtectionGroupId': {'S': 'pg-12345'},
            'RecoveryType': {'S': 'drill'},
            'Status': {'S': 'IN_PROGRESS'},
            'StartTime': {'S': datetime.utcnow().isoformat()}
        }
    )
    
    # SNS - Send notification
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-execution-alerts-test',
        Subject='DR Drill Started',
        Message=json.dumps({
            'protectionGroupId': 'pg-12345',
            'executionId': execution['executionArn'].split(':')[-1],
            'recoveryType': 'drill',
            'startTime': datetime.utcnow().isoformat()
        })
    )
    
    # Lambda - Invoke Data Management for async sync
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName='aws-drs-orchestration-data-management-handler-test',
        InvocationType='Event',
        Payload=json.dumps({
            'operation': 'sync_recovery_instances',
            'executionId': execution['executionArn'].split(':')[-1]
        })
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Recovery execution started',
            'executionArn': execution['executionArn']
        })
    }
```

**Allowed Operations**: Step Functions execution, SNS publish, DynamoDB CRUD, Lambda invocation (Data Management only).

**Denied Operations**: Lambda invocation of Query Handler or Frontend Deployer fails with AccessDenied.

### Orchestration Role - Recovery Execution

**Scenario**: Execute disaster recovery with launch template creation and instance launch.

```python
import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    """Orchestration Function - execute DRS recovery operations."""
    
    # Extract parameters from Step Functions input
    protection_group_id = event['protectionGroupId']
    target_account_id = event['targetAccountId']
    recovery_type = event['recoveryType']
    
    # STS - Assume cross-account role
    sts = boto3.client('sts')
    assumed_role = sts.assume_role(
        RoleArn=f'arn:aws:iam::{target_account_id}:role/DRSOrchestrationRole',
        RoleSessionName='orchestration',
        ExternalId='aws-drs-orchestration-test'  # Required for security
    )
    
    # Create DRS client with assumed role credentials
    drs = boto3.client(
        'drs',
        aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
        aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
        aws_session_token=assumed_role['Credentials']['SessionToken']
    )
    
    # EC2 - Create launch template
    ec2 = boto3.client('ec2')
    launch_template = ec2.create_launch_template(
        LaunchTemplateName=f'drs-recovery-{protection_group_id}',
        LaunchTemplateData={
            'InstanceType': 't3.medium',
            'SecurityGroupIds': ['sg-1234567890abcdef0'],
            'SubnetId': 'subnet-1234567890abcdef0',
            'IamInstanceProfile': {
                'Arn': 'arn:aws:iam::123456789012:instance-profile/DRSRecoveryProfile'
            },
            'TagSpecifications': [{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'ProtectionGroup', 'Value': protection_group_id},
                    {'Key': 'RecoveryType', 'Value': recovery_type}
                ]
            }]
        }
    )
    
    # DRS - Update launch configuration
    drs.update_launch_configuration(
        sourceServerID='s-1234567890abcdef0',
        launchDisposition='STARTED',
        targetInstanceTypeRightSizingMethod='BASIC',
        copyPrivateIp=False,
        copyTags=True
    )
    
    # DRS - Start recovery
    recovery_job = drs.start_recovery(
        sourceServers=[
            {'sourceServerID': 's-1234567890abcdef0'},
            {'sourceServerID': 's-0987654321fedcba0'}
        ],
        isDrill=(recovery_type == 'drill'),
        tags={
            'ProtectionGroup': protection_group_id,
            'RecoveryType': recovery_type,
            'ExecutionTime': datetime.utcnow().isoformat()
        }
    )
    
    # DynamoDB - Update execution status
    dynamodb = boto3.client('dynamodb')
    dynamodb.update_item(
        TableName='aws-drs-orchestration-execution-history-test',
        Key={'ExecutionId': {'S': event['executionId']}},
        UpdateExpression='SET #status = :status, RecoveryJobId = :jobId',
        ExpressionAttributeNames={'#status': 'Status'},
        ExpressionAttributeValues={
            ':status': {'S': 'RECOVERY_IN_PROGRESS'},
            ':jobId': {'S': recovery_job['job']['jobID']}
        }
    )
    
    # SNS - Send notification
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-execution-alerts-test',
        Subject='Recovery Job Started',
        Message=json.dumps({
            'protectionGroupId': protection_group_id,
            'recoveryJobId': recovery_job['job']['jobID'],
            'recoveryType': recovery_type
        })
    )
    
    return {
        'statusCode': 200,
        'recoveryJobId': recovery_job['job']['jobID'],
        'launchTemplateId': launch_template['LaunchTemplate']['LaunchTemplateId']
    }
```

**Allowed Operations**: DRS recovery operations, EC2 launch template creation, IAM PassRole (to EC2/DRS only), KMS operations (via EC2/DRS only), cross-account access with ExternalId.

**Denied Operations**: IAM PassRole to Lambda fails, KMS direct encryption fails, cross-account access without ExternalId fails.

### Frontend Deployer Role - Frontend Deployment

**Scenario**: Deploy frontend build artifacts and invalidate CloudFront cache.

```python
import boto3
import json
import os
from datetime import datetime

def lambda_handler(event, context):
    """Frontend Deployer - deploy static assets to S3 and invalidate CloudFront."""
    
    # S3 - Upload frontend artifacts
    s3 = boto3.client('s3')
    bucket_name = 'aws-drs-orchestration-438465159935-fe-test'
    
    # Upload index.html
    s3.put_object(
        Bucket=bucket_name,
        Key='index.html',
        Body=open('/tmp/build/index.html', 'rb'),
        ContentType='text/html',
        ACL='public-read'
    )
    
    # Upload JavaScript bundles
    for js_file in os.listdir('/tmp/build/static/js'):
        s3.put_object(
            Bucket=bucket_name,
            Key=f'static/js/{js_file}',
            Body=open(f'/tmp/build/static/js/{js_file}', 'rb'),
            ContentType='application/javascript',
            ACL='public-read'
        )
    
    # S3 - Clean up old versions (cost optimization)
    versions = s3.list_object_versions(Bucket=bucket_name)
    for version in versions.get('Versions', []):
        if not version.get('IsLatest'):
            # Delete old versions to reduce storage costs
            s3.delete_object(
                Bucket=bucket_name,
                Key=version['Key'],
                VersionId=version['VersionId']
            )
    
    # CloudFront - Create invalidation
    cloudfront = boto3.client('cloudfront')
    invalidation = cloudfront.create_invalidation(
        DistributionId='E1234567890ABC',
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': ['/*']
            },
            'CallerReference': str(datetime.utcnow().timestamp())
        }
    )
    
    # CloudWatch - Publish deployment metrics
    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(
        Namespace='DROrchestration/Frontend',
        MetricData=[{
            'MetricName': 'DeploymentDuration',
            'Value': 45.2,
            'Unit': 'Seconds',
            'Timestamp': datetime.utcnow()
        }]
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Frontend deployed successfully',
            'bucket': bucket_name,
            'invalidationId': invalidation['Invalidation']['Id']
        })
    }
```

**Allowed Operations**: S3 upload/delete (frontend buckets only), CloudFront invalidation, CloudWatch metrics.

**Denied Operations**: S3 access to deployment bucket fails, DynamoDB access fails, DRS operations fail, Lambda invocation fails.


---

## Security Best Practices

### Principle of Least Privilege

Each IAM role grants only the minimum permissions required for its Lambda function to operate:

1. **Query Handler**: Read-only access prevents data modification or recovery execution
2. **Data Management**: DynamoDB CRUD and DRS metadata without recovery capabilities
3. **Execution Handler**: Orchestration permissions without direct DRS write access
4. **Orchestration**: Comprehensive recovery permissions with IAM condition key restrictions
5. **Frontend Deployer**: Complete isolation from backend services and disaster recovery operations

### Defense in Depth

Multiple security layers protect the platform:

1. **Resource-Level Permissions**: ARN patterns restrict access to project resources only
2. **IAM Condition Keys**: Additional restrictions on region, service, and ExternalId
3. **CloudWatch Alarms**: Detect AccessDenied errors and unauthorized operations
4. **CloudTrail Logging**: Complete audit trail of all IAM actions
5. **ExternalId Validation**: Prevents confused deputy attacks in cross-account access

### Monitoring and Alerting

**CloudWatch Alarms**:
- AccessDenied errors trigger security alerts after 5 errors in 5 minutes
- Alarms send notifications to security alert SNS topic
- Alarms cover all Lambda functions and all IAM roles

**CloudWatch Logs Insights Queries**:

Query 1: AccessDenied errors by function and action
```
fields @timestamp, @message, @logStream
| filter @message like /AccessDenied/
| parse @message /Action: (?<action>[^\s,]+)/
| parse @logStream /\/aws\/lambda\/(?<function>[^\/]+)/
| stats count() by function, action
| sort count desc
```

Query 2: Cross-account role assumptions
```
fields @timestamp, @message
| filter @message like /AssumeRole/
| parse @message /RoleArn: (?<roleArn>[^\s,]+)/
| parse @message /ExternalId: (?<externalId>[^\s,]+)/
| stats count() by roleArn, externalId
```

Query 3: IAM condition key violations
```
fields @timestamp, @message
| filter @message like /aws:RequestedRegion|iam:PassedToService|kms:ViaService|sts:ExternalId/
| parse @message /Condition: (?<condition>[^\s,]+)/
| parse @message /Value: (?<value>[^\s,]+)/
| stats count() by condition, value
```

### Incident Response

**AccessDenied Error Response**:
1. CloudWatch Alarm triggers after 5 errors in 5 minutes
2. SNS notification sent to security alert topic
3. Security team investigates CloudWatch Logs for error details
4. Determine if error is legitimate (missing permission) or attack (unauthorized operation)
5. If legitimate: Add missing permission to function-specific role
6. If attack: Investigate source, rotate credentials, review CloudTrail logs

**Cross-Account Access Failure Response**:
1. Verify ExternalId matches `{ProjectName}-{Environment}` in both accounts
2. Verify workload account trust policy includes correct ExternalId
3. Verify orchestration account role has STS AssumeRole permission
4. Check CloudTrail logs for AssumeRole API calls and error details
5. If ExternalId mismatch: Update workload account trust policy
6. If trust policy missing: Add trust policy to workload account role

**IAM Condition Key Violation Response**:
1. Identify which condition key was violated (aws:RequestedRegion, iam:PassedToService, kms:ViaService, sts:ExternalId)
2. Review CloudWatch Logs for operation details (region, service, ExternalId)
3. Determine if violation is legitimate (code bug) or attack (unauthorized operation)
4. If legitimate: Fix code to comply with condition key requirements
5. If attack: Investigate source, rotate credentials, review CloudTrail logs

### Compliance Considerations

**AWS Well-Architected Framework**:
- ✅ Security Pillar: Least privilege IAM roles
- ✅ Operational Excellence: CloudWatch monitoring and alerting
- ✅ Reliability: Rollback capability via CloudFormation parameter
- ✅ Performance Efficiency: Resource-level permissions reduce IAM policy evaluation time
- ✅ Cost Optimization: Minimal permissions reduce risk of unauthorized resource creation

**Industry Standards**:
- ✅ SOC 2: Least privilege access controls
- ✅ ISO 27001: Access control policy and procedures
- ✅ PCI DSS: Restrict access by business need-to-know
- ✅ HIPAA: Minimum necessary access to protected health information

**Audit Requirements**:
- CloudTrail logs all IAM actions with role ARN, function name, and timestamp
- CloudWatch Logs retain all Lambda function logs for 30 days (configurable)
- IAM policies are version-controlled in CloudFormation templates
- All IAM changes require CloudFormation stack update (audit trail)


---

## Troubleshooting

### Common Issues and Resolutions

#### AccessDenied: User is not authorized to perform operation

**Symptom**: Lambda function logs show `AccessDenied` error when attempting operation.

**Example Error**:
```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) when calling the StartRecovery operation: User: arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-query-handler-role-test/aws-drs-orchestration-query-handler-test is not authorized to perform: drs:StartRecovery on resource: * because no identity-based policy allows the drs:StartRecovery action
```

**Root Cause**: Lambda function is using a role that doesn't have the required permission.

**Resolution**:
1. Identify which role the Lambda function is using (check CloudFormation parameter `UseFunctionSpecificRoles`)
2. Review the role's IAM policies to verify the permission is granted
3. If permission is missing: Add permission to the function-specific role
4. If permission should not be granted: This is expected behavior (e.g., Query Handler cannot execute StartRecovery)

**Example Fix** (if permission should be granted):
```yaml
# Add missing permission to role
- Effect: Allow
  Action:
    - drs:StartRecovery
  Resource: "*"
```

#### AccessDenied: Resource ARN doesn't match pattern

**Symptom**: Lambda function logs show `AccessDenied` error when accessing resource that doesn't match ARN pattern.

**Example Error**:
```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) when calling the GetItem operation: User: arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-query-handler-role-test/aws-drs-orchestration-query-handler-test is not authorized to perform: dynamodb:GetItem on resource: arn:aws:dynamodb:us-east-2:438465159935:table/other-project-table because no identity-based policy allows the dynamodb:GetItem action on that resource
```

**Root Cause**: Lambda function is attempting to access a resource that doesn't match the ARN pattern in the IAM policy.

**Resolution**:
1. Verify the resource ARN matches the pattern `{ProjectName}-*`
2. If resource ARN is correct: Check if IAM policy resource restriction is too narrow
3. If resource ARN is incorrect: Fix code to use correct resource name

**Example Fix** (if code is incorrect):
```python
# ❌ Wrong - doesn't match pattern
dynamodb.get_item(
    TableName='other-project-table',
    Key={'Id': {'S': 'test-id'}}
)

# ✅ Correct - matches pattern
dynamodb.get_item(
    TableName='aws-drs-orchestration-protection-groups-test',
    Key={'Id': {'S': 'test-id'}}
)
```

#### AccessDenied: IAM condition key violation

**Symptom**: Lambda function logs show `AccessDenied` error with condition key mentioned.

**Example Error**:
```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) when calling the StartRecovery operation: User: arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-orchestration-role-test/aws-drs-orchestration-dr-orch-sf-test is not authorized to perform: drs:StartRecovery with an explicit deny in an identity-based policy due to condition key 'aws:RequestedRegion'
```

**Root Cause**: Operation violates IAM condition key requirement (e.g., wrong region, wrong service, wrong ExternalId).

**Resolution**:
1. Identify which condition key was violated (aws:RequestedRegion, iam:PassedToService, kms:ViaService, sts:ExternalId)
2. Review operation parameters to verify they meet condition requirements
3. Fix code to comply with condition key requirements

**Example Fix** (aws:RequestedRegion violation):
```python
# ❌ Wrong - attempting operation in wrong region
drs_west = boto3.client('drs', region_name='us-west-2')
drs_west.start_recovery(sourceServers=[...])  # Fails if deployment region is us-east-2

# ✅ Correct - operation in deployment region
drs = boto3.client('drs', region_name='us-east-2')
drs.start_recovery(sourceServers=[...])  # Succeeds
```

#### AccessDenied: Cross-account AssumeRole failure

**Symptom**: Lambda function logs show `AccessDenied` error when assuming cross-account role.

**Example Error**:
```
botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the AssumeRole operation: User: arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-orchestration-role-test/aws-drs-orchestration-dr-orch-sf-test is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::123456789012:role/DRSOrchestrationRole
```

**Root Cause**: ExternalId doesn't match, or workload account trust policy is missing/incorrect.

**Resolution**:
1. Verify ExternalId matches `{ProjectName}-{Environment}` (e.g., `aws-drs-orchestration-test`)
2. Verify workload account trust policy includes correct ExternalId
3. Verify workload account trust policy includes orchestration account principal

**Example Fix** (workload account trust policy):
```yaml
# Workload account role trust policy
AssumeRolePolicyDocument:
  Version: "2012-10-17"
  Statement:
    - Effect: Allow
      Principal:
        AWS: "arn:aws:iam::438465159935:root"  # Orchestration account
      Action: sts:AssumeRole
      Condition:
        StringEquals:
          sts:ExternalId: "aws-drs-orchestration-test"  # Must match
```

#### CloudFormation: Role ARN does not exist

**Symptom**: CloudFormation stack update fails with error about role ARN not existing.

**Example Error**:
```
Resource handler returned message: "Invalid request provided: Role ARN arn:aws:iam::438465159935:role/aws-drs-orchestration-query-handler-role-test does not exist" (RequestToken: 12345678-1234-1234-1234-123456789012, HandlerErrorCode: InvalidRequest)
```

**Root Cause**: CloudFormation condition logic is incorrect, or IAM stack hasn't created the role yet.

**Resolution**:
1. Verify `UseFunctionSpecificRoles` parameter is set correctly
2. Verify IAM stack has completed successfully before Lambda stack update
3. Verify CloudFormation condition logic in Lambda stack template

**Example Fix** (CloudFormation condition):
```yaml
# Lambda function role selection
QueryHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    Role: !If
      - UseFunctionSpecificRoles
      - !GetAtt IAMStack.Outputs.QueryHandlerRoleArn  # Function-specific role
      - !GetAtt IAMStack.Outputs.UnifiedRoleArn       # Unified role
```

#### Lambda: Cannot invoke other function

**Symptom**: Lambda function logs show `AccessDenied` error when invoking another Lambda function.

**Example Error**:
```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) when calling the Invoke operation: User: arn:aws:sts::438465159935:assumed-role/aws-drs-orchestration-query-handler-role-test/aws-drs-orchestration-query-handler-test is not authorized to perform: lambda:InvokeFunction on resource: arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-data-management-handler-test because no identity-based policy allows the lambda:InvokeFunction action on that resource
```

**Root Cause**: Lambda function is attempting to invoke a function it doesn't have permission to invoke.

**Resolution**:
1. Review which functions each role can invoke:
   - Query Handler: Execution Handler only
   - Data Management: Self only
   - Execution Handler: Data Management only
   - Orchestration: Execution Handler and Query Handler only
   - Frontend Deployer: None
2. If invocation is required: Add permission to the role
3. If invocation should not be allowed: This is expected behavior

**Example Fix** (if invocation should be allowed):
```yaml
# Add Lambda invocation permission to role
- Effect: Allow
  Action:
    - lambda:InvokeFunction
  Resource:
    - !Sub "arn:${AWS::Partition}:lambda:${AWS::Region}:${AWS::AccountId}:function:${ProjectName}-data-management-handler-${Environment}"
```


---

## Migration Guide

### Switching from Unified Role to Function-Specific Roles

**Prerequisites**:
- CloudFormation stack deployed with `UseFunctionSpecificRoles=false` (unified role)
- All Lambda functions operational with unified role
- Comprehensive testing completed in dev/test environment

**Migration Steps**:

1. **Update CloudFormation Stack**:
```bash
# Update stack parameter to enable function-specific roles
aws cloudformation update-stack \
  --stack-name aws-drs-orchestration-test \
  --use-previous-template \
  --parameters \
    ParameterKey=ProjectName,UsePreviousValue=true \
    ParameterKey=Environment,UsePreviousValue=true \
    ParameterKey=DeploymentBucket,UsePreviousValue=true \
    ParameterKey=AdminEmail,UsePreviousValue=true \
    ParameterKey=UseFunctionSpecificRoles,ParameterValue=true \
  --capabilities CAPABILITY_NAMED_IAM
```

2. **Monitor Stack Update**:
```bash
# Watch stack events
aws cloudformation describe-stack-events \
  --stack-name aws-drs-orchestration-test \
  --max-items 20 \
  --query 'StackEvents[*].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId]' \
  --output table
```

3. **Verify Role Creation**:
```bash
# List IAM roles created
aws iam list-roles \
  --query 'Roles[?contains(RoleName, `aws-drs-orchestration`) && contains(RoleName, `test`)].RoleName' \
  --output table
```

Expected output:
```
aws-drs-orchestration-query-handler-role-test
aws-drs-orchestration-data-management-role-test
aws-drs-orchestration-execution-handler-role-test
aws-drs-orchestration-orchestration-role-test
aws-drs-orchestration-frontend-deployer-role-test
```

4. **Verify Lambda Function Role Assignment**:
```bash
# Check Query Handler role
aws lambda get-function-configuration \
  --function-name aws-drs-orchestration-query-handler-test \
  --query 'Role'

# Expected: arn:aws:iam::438465159935:role/aws-drs-orchestration-query-handler-role-test
```

5. **Execute Smoke Tests**:
```bash
# Test Query Handler (read-only)
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation": "list_protection_groups"}' \
  response.json

# Test Data Management (DynamoDB CRUD)
aws lambda invoke \
  --function-name aws-drs-orchestration-data-management-handler-test \
  --payload '{"operation": "create_protection_group", "name": "test-pg"}' \
  response.json

# Test Execution Handler (orchestration)
aws lambda invoke \
  --function-name aws-drs-orchestration-execution-handler-test \
  --payload '{"operation": "start_execution", "protectionGroupId": "pg-12345"}' \
  response.json
```

6. **Monitor CloudWatch Logs**:
```bash
# Check for AccessDenied errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/aws-drs-orchestration-query-handler-test \
  --filter-pattern "AccessDenied" \
  --start-time $(date -u -d '5 minutes ago' +%s)000
```

7. **Verify CloudWatch Alarms**:
```bash
# Check alarm state
aws cloudwatch describe-alarms \
  --alarm-names aws-drs-orchestration-access-denied-test \
  --query 'MetricAlarms[*].[AlarmName,StateValue,StateReason]' \
  --output table
```

Expected: Alarm state should be `OK` (no AccessDenied errors).

### Rolling Back to Unified Role

**Scenario**: Function-specific roles cause issues, need to rollback to unified role.

**Rollback Steps**:

1. **Update CloudFormation Stack**:
```bash
# Rollback to unified role
aws cloudformation update-stack \
  --stack-name aws-drs-orchestration-test \
  --use-previous-template \
  --parameters \
    ParameterKey=ProjectName,UsePreviousValue=true \
    ParameterKey=Environment,UsePreviousValue=true \
    ParameterKey=DeploymentBucket,UsePreviousValue=true \
    ParameterKey=AdminEmail,UsePreviousValue=true \
    ParameterKey=UseFunctionSpecificRoles,ParameterValue=false \
  --capabilities CAPABILITY_NAMED_IAM
```

2. **Monitor Stack Update**:
```bash
# Watch stack events
aws cloudformation describe-stack-events \
  --stack-name aws-drs-orchestration-test \
  --max-items 20
```

3. **Verify Unified Role Recreation**:
```bash
# Check unified role exists
aws iam get-role \
  --role-name aws-drs-orchestration-unified-role-test
```

4. **Verify Lambda Function Role Assignment**:
```bash
# Check Query Handler now uses unified role
aws lambda get-function-configuration \
  --function-name aws-drs-orchestration-query-handler-test \
  --query 'Role'

# Expected: arn:aws:iam::438465159935:role/aws-drs-orchestration-unified-role-test
```

5. **Verify Function-Specific Roles Deleted**:
```bash
# Verify function-specific roles no longer exist
aws iam get-role \
  --role-name aws-drs-orchestration-query-handler-role-test

# Expected: NoSuchEntity error
```

6. **Execute Smoke Tests**:
```bash
# Test all Lambda functions with unified role
aws lambda invoke \
  --function-name aws-drs-orchestration-query-handler-test \
  --payload '{"operation": "list_protection_groups"}' \
  response.json
```

7. **Verify No Data Loss**:
```bash
# Check DynamoDB tables
aws dynamodb scan \
  --table-name aws-drs-orchestration-protection-groups-test \
  --select COUNT

# Verify count matches pre-rollback count
```

**Rollback Guarantees**:
- ✅ No DynamoDB data loss
- ✅ No Step Functions execution interruption
- ✅ All Lambda functions immediately use unified role
- ✅ CloudFormation update completes within 5 minutes
- ✅ No service downtime


---

## Reference Tables

### Role Permission Matrix

| Service | Query Handler | Data Management | Execution Handler | Orchestration | Frontend Deployer |
|---------|--------------|-----------------|-------------------|---------------|-------------------|
| **DynamoDB** | Read-only | Full CRUD | Full CRUD | Read + Write | ❌ No access |
| **DRS Describe*** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No access |
| **DRS StartRecovery** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ❌ No access |
| **DRS TerminateRecoveryInstances** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ❌ No access |
| **DRS TagResource** | ❌ No | ✅ Yes | ❌ No | ✅ Yes | ❌ No access |
| **DRS CreateRecoveryInstanceForDrs** | ❌ No | ❌ No | ❌ No | ✅ Yes | ❌ No access |
| **EC2 Describe*** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes | ❌ No access |
| **EC2 RunInstances** | ❌ No | ❌ No | ❌ No | ✅ Yes | ❌ No access |
| **EC2 TerminateInstances** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ❌ No access |
| **EC2 CreateLaunchTemplate** | ❌ No | ❌ No | ❌ No | ✅ Yes | ❌ No access |
| **Step Functions** | ❌ No | ❌ No | ✅ Yes | ❌ No | ❌ No access |
| **SNS** | ❌ No | ❌ No | ✅ Yes | ✅ Yes | ❌ No access |
| **Lambda InvokeFunction** | Execution Handler only | Self only | Data Management only | Execution Handler + Query Handler | ❌ No access |
| **EventBridge** | ❌ No | ✅ Yes | ❌ No | ❌ No | ❌ No access |
| **S3** | ❌ No | ❌ No | ❌ No | ❌ No | Frontend buckets only |
| **CloudFront** | ❌ No | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **IAM PassRole** | ❌ No | ❌ No | ❌ No | DRS + EC2 only | ❌ No access |
| **KMS** | ❌ No | ❌ No | ❌ No | Via EC2/DRS only | ❌ No access |
| **SSM** | ❌ No | ❌ No | ❌ No | ✅ Yes | ❌ No access |
| **STS AssumeRole** | ✅ Yes (ExternalId) | ✅ Yes (ExternalId) | ✅ Yes (ExternalId) | ✅ Yes (ExternalId) | ❌ No access |
| **CloudWatch PutMetricData** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |

### IAM Condition Keys by Role

| Role | Condition Key | Condition Value | Applied To |
|------|--------------|-----------------|------------|
| Orchestration | aws:RequestedRegion | Deployment region | DRS write operations |
| Orchestration | iam:PassedToService | drs.amazonaws.com, ec2.amazonaws.com | IAM PassRole |
| Orchestration | kms:ViaService | ec2.{Region}.amazonaws.com, drs.{Region}.amazonaws.com | KMS operations |
| All roles | sts:ExternalId | {ProjectName}-{Environment} | STS AssumeRole |

### Resource ARN Patterns by Service

| Service | ARN Pattern | Example |
|---------|------------|---------|
| DynamoDB | `arn:aws:dynamodb:{Region}:{AccountId}:table/{ProjectName}-*` | `arn:aws:dynamodb:us-east-2:438465159935:table/aws-drs-orchestration-protection-groups-test` |
| Lambda | `arn:aws:lambda:{Region}:{AccountId}:function:{ProjectName}-{function}-{Environment}` | `arn:aws:lambda:us-east-2:438465159935:function:aws-drs-orchestration-query-handler-test` |
| Step Functions | `arn:aws:states:{Region}:{AccountId}:stateMachine:{ProjectName}-*` | `arn:aws:states:us-east-2:438465159935:stateMachine:aws-drs-orchestration-dr-orch-sf-test` |
| SNS | `arn:aws:sns:{Region}:{AccountId}:{ProjectName}-*` | `arn:aws:sns:us-east-2:438465159935:aws-drs-orchestration-execution-alerts-test` |
| EventBridge | `arn:aws:events:{Region}:{AccountId}:rule/{ProjectName}-*` | `arn:aws:events:us-east-2:438465159935:rule/aws-drs-orchestration-tag-sync-schedule-test` |
| S3 (Frontend) | `arn:aws:s3:::{ProjectName}-*-fe-*` | `arn:aws:s3:::aws-drs-orchestration-438465159935-fe-test` |
| CloudFormation | `arn:aws:cloudformation:{Region}:{AccountId}:stack/{ProjectName}-*/*` | `arn:aws:cloudformation:us-east-2:438465159935:stack/aws-drs-orchestration-test/*` |
| Cross-Account | `arn:aws:iam::*:role/DRSOrchestrationRole` | `arn:aws:iam::123456789012:role/DRSOrchestrationRole` |

### Blast Radius Comparison

| Role | Blast Radius | Impact if Compromised | Mitigation |
|------|-------------|----------------------|------------|
| Query Handler | **Minimal** | Information disclosure only | Read-only permissions, CloudWatch alarms |
| Data Management | **Medium** | Data corruption possible | No recovery operations, CloudWatch alarms |
| Execution Handler | **High** | Service disruption possible | Step Functions audit trail, CloudWatch alarms |
| Orchestration | **Critical** | Complete service disruption | IAM condition keys, CloudWatch alarms, ExternalId validation |
| Frontend Deployer | **Minimal** | Website defacement only | S3 versioning, CloudFront invalidation logs, complete isolation from backend |

---

## Related Documentation

- [ADR-001: Function-Specific IAM Roles and CloudFormation Reorganization](architecture/ADR-001-function-specific-iam-roles.md)
- [Design Document](.kiro/specs/function-specific-iam-roles/design.md)
- [Requirements Document](.kiro/specs/function-specific-iam-roles/requirements.md)
- [QA Deployment Configuration](QA_DEPLOYMENT_CONFIGURATION.md)
- [Functional Equivalence Test Results](../tests/integration/TASK_18_6_FUNCTIONAL_EQUIVALENCE_SUMMARY.md)
- [Negative Security Test Results](../tests/integration/TASK_18_7_NEGATIVE_SECURITY_TESTS.md)
- [Rollback Test Guide](../tests/integration/TASK_18_8_ROLLBACK_TEST_GUIDE.md)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-01-28 | 1.0 | Platform Engineering Team | Initial release - comprehensive IAM role reference documentation |

