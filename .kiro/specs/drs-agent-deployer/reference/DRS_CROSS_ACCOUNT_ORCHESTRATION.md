# DRS Cross-Account Orchestration Guide

## Overview

This guide explains how to deploy DRS agents across multiple AWS accounts using cross-account IAM roles instead of individual account credentials. This pattern is essential for enterprise DR orchestration at scale.

## Architecture

```
Central Orchestration Account          Target Accounts
┌─────────────────────────┐           ┌──────────────────────┐
│ Orchestration Lambda    │           │ Account: 160885257264│
│ or Automation Script    │──Assume──▶│ Role: DRSOrchestration│
│                         │   Role    │ - Deploy DRS agents  │
│ Credentials:            │           │ - Monitor replication│
│ - Central account only  │           └──────────────────────┘
└─────────────────────────┘           
                                      ┌──────────────────────┐
                          ──Assume──▶│ Account: 664418995426│
                             Role    │ Role: DRSOrchestration│
                                     │ - Deploy DRS agents  │
                                     │ - Monitor replication│
                                     └──────────────────────┘
```

## Benefits

1. **Single Credential Set**: Only need credentials for central orchestration account
2. **Centralized Control**: Manage DR operations from one location
3. **Audit Trail**: All actions logged in CloudTrail with role assumption
4. **Security**: No need to distribute credentials across accounts
5. **Scalability**: Easily add new accounts without credential management

## Implementation

### 1. Create Cross-Account Role in Each Target Account

Create this IAM role in each account where you want to deploy DRS agents:

```yaml
# CloudFormation template for DRS Orchestration Role
AWSTemplateFormatVersion: '2010-09-09'
Description: Cross-account role for DRS agent deployment and orchestration

Parameters:
  OrchestrationAccountId:
    Type: String
    Description: AWS Account ID of the central orchestration account
    Default: "891376951562"

Resources:
  DRSOrchestrationRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: DRSOrchestrationRole
      Description: Allows central account to deploy and manage DRS agents
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${OrchestrationAccountId}:root'
            Action: 'sts:AssumeRole'
            Condition:
              StringEquals:
                'sts:ExternalId': 'DRSOrchestration2024'
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonSSMFullAccess
      Policies:
        - PolicyName: DRSOrchestrationPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              # EC2 Discovery
              - Effect: Allow
                Action:
                  - ec2:DescribeInstances
                  - ec2:DescribeInstanceStatus
                  - ec2:DescribeTags
                Resource: '*'
              
              # SSM Command Execution
              - Effect: Allow
                Action:
                  - ssm:SendCommand
                  - ssm:ListCommands
                  - ssm:ListCommandInvocations
                  - ssm:GetCommandInvocation
                  - ssm:DescribeInstanceInformation
                Resource: '*'
              
              # DRS Monitoring
              - Effect: Allow
                Action:
                  - drs:DescribeSourceServers
                  - drs:DescribeJobs
                  - drs:DescribeJobLogItems
                  - drs:GetReplicationConfiguration
                  - drs:DescribeReplicationConfigurationTemplates
                Resource: '*'
              
              # DRS Operations (optional - for full orchestration)
              - Effect: Allow
                Action:
                  - drs:StartRecovery
                  - drs:TerminateRecoveryInstances
                  - drs:UpdateLaunchConfiguration
                Resource: '*'

Outputs:
  RoleArn:
    Description: ARN of the DRS Orchestration Role
    Value: !GetAtt DRSOrchestrationRole.Arn
    Export:
      Name: DRSOrchestrationRoleArn
```

### 2. Deploy Role to Target Accounts

```bash
# Deploy to account 160885257264
AWS_PROFILE="160885257264_AdministratorAccess" \
  aws cloudformation deploy \
  --template-file drs-orchestration-role.yaml \
  --stack-name drs-orchestration-role \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides OrchestrationAccountId=891376951562

# Deploy to account 664418995426
AWS_PROFILE="664418995426_AdministratorAccess" \
  aws cloudformation deploy \
  --template-file drs-orchestration-role.yaml \
  --stack-name drs-orchestration-role \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides OrchestrationAccountId=891376951562
```

### 3. Use Cross-Account Role with Deployment Script

```bash
# Set the role ARN
export AWS_ROLE_ARN="arn:aws:iam::160885257264:role/DRSOrchestrationRole"

# Deploy DRS agents (script will assume the role)
./scripts/deploy_drs_agents.sh 160885257264 us-east-1 us-west-2

# Deploy to different account
export AWS_ROLE_ARN="arn:aws:iam::664418995426:role/DRSOrchestrationRole"
./scripts/deploy_drs_agents.sh 664418995426 us-east-1 us-west-2
```

## Lambda-Based Orchestration

For automated orchestration, use AWS Lambda in the central account:

```python
import boto3
import os

def lambda_handler(event, context):
    """
    Deploy DRS agents across multiple accounts
    """
    
    # Configuration
    accounts = [
        {
            'account_id': '160885257264',
            'role_arn': 'arn:aws:iam::160885257264:role/DRSOrchestrationRole',
            'source_region': 'us-east-1',
            'target_region': 'us-west-2'
        },
        {
            'account_id': '664418995426',
            'role_arn': 'arn:aws:iam::664418995426:role/DRSOrchestrationRole',
            'source_region': 'us-east-1',
            'target_region': 'us-west-2'
        }
    ]
    
    results = []
    
    for account in accounts:
        try:
            # Assume role in target account
            sts = boto3.client('sts')
            assumed_role = sts.assume_role(
                RoleArn=account['role_arn'],
                RoleSessionName='DRSAgentDeployment'
            )
            
            # Create clients with assumed credentials
            credentials = assumed_role['Credentials']
            ec2 = boto3.client(
                'ec2',
                region_name=account['source_region'],
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            ssm = boto3.client(
                'ssm',
                region_name=account['source_region'],
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            # Discover instances with DRS tags
            instances = ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:dr:enabled', 'Values': ['true']},
                    {'Name': 'tag:dr:recovery-strategy', 'Values': ['drs']},
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
            
            instance_ids = []
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_ids.append(instance['InstanceId'])
            
            if not instance_ids:
                results.append({
                    'account_id': account['account_id'],
                    'status': 'no_instances',
                    'message': 'No instances found with DRS tags'
                })
                continue
            
            # Deploy DRS agents via SSM
            response = ssm.send_command(
                InstanceIds=instance_ids,
                DocumentName='AWSDisasterRecovery-InstallDRAgentOnInstance',
                Parameters={
                    'Region': [account['target_region']]
                },
                Comment=f"DRS agent deployment for account {account['account_id']}"
            )
            
            results.append({
                'account_id': account['account_id'],
                'status': 'success',
                'command_id': response['Command']['CommandId'],
                'instance_count': len(instance_ids)
            })
            
        except Exception as e:
            results.append({
                'account_id': account['account_id'],
                'status': 'error',
                'error': str(e)
            })
    
    return {
        'statusCode': 200,
        'body': results
    }
```

## Step Functions Orchestration

For complex multi-account workflows:

```yaml
# Step Functions state machine for DRS orchestration
Comment: Multi-account DRS agent deployment and monitoring
StartAt: DiscoverAccounts
States:
  DiscoverAccounts:
    Type: Task
    Resource: arn:aws:lambda:us-east-1:123456789012:function:DiscoverDRSAccounts
    Next: DeployAgentsMap
  
  DeployAgentsMap:
    Type: Map
    ItemsPath: $.accounts
    MaxConcurrency: 5
    Iterator:
      StartAt: AssumeRole
      States:
        AssumeRole:
          Type: Task
          Resource: arn:aws:lambda:us-east-1:123456789012:function:AssumeAccountRole
          Next: DiscoverInstances
        
        DiscoverInstances:
          Type: Task
          Resource: arn:aws:lambda:us-east-1:123456789012:function:DiscoverDRSInstances
          Next: DeployAgents
        
        DeployAgents:
          Type: Task
          Resource: arn:aws:lambda:us-east-1:123456789012:function:DeployDRSAgents
          Next: WaitForCompletion
        
        WaitForCompletion:
          Type: Wait
          Seconds: 300
          Next: CheckStatus
        
        CheckStatus:
          Type: Task
          Resource: arn:aws:lambda:us-east-1:123456789012:function:CheckDRSStatus
          End: true
    
    Next: GenerateReport
  
  GenerateReport:
    Type: Task
    Resource: arn:aws:lambda:us-east-1:123456789012:function:GenerateDRSReport
    End: true
```

## Security Best Practices

### 1. Use External ID
Always use an External ID in the trust policy:

```json
{
  "Condition": {
    "StringEquals": {
      "sts:ExternalId": "DRSOrchestration2024"
    }
  }
}
```

### 2. Least Privilege
Grant only the minimum permissions needed:
- Read-only for discovery
- SSM command execution for agent deployment
- DRS read-only for monitoring

### 3. CloudTrail Logging
Enable CloudTrail in all accounts to audit role assumptions:

```bash
# Check who assumed the role
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=DRSOrchestrationRole \
  --max-results 10
```

### 4. Session Duration
Limit session duration in the role:

```yaml
MaxSessionDuration: 3600  # 1 hour
```

## Monitoring and Alerting

### CloudWatch Alarms

```yaml
DRSAgentDeploymentFailures:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: DRS-Agent-Deployment-Failures
    MetricName: FailedCommandInvocations
    Namespace: AWS/SSM
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanThreshold
```

### SNS Notifications

```python
# Send notification on deployment completion
sns = boto3.client('sns')
sns.publish(
    TopicArn='arn:aws:sns:us-east-1:123456789012:DRSOrchestration',
    Subject='DRS Agent Deployment Complete',
    Message=f'Deployed DRS agents to {len(results)} accounts'
)
```

## Troubleshooting

### Role Assumption Fails

```bash
# Test role assumption
aws sts assume-role \
  --role-arn arn:aws:iam::160885257264:role/DRSOrchestrationRole \
  --role-session-name test \
  --external-id DRSOrchestration2024
```

### Permission Denied

Check the role's permissions:

```bash
# Get role policy
aws iam get-role-policy \
  --role-name DRSOrchestrationRole \
  --policy-name DRSOrchestrationPolicy
```

### Agent Installation Fails

Verify instance IAM role has DRS permissions:

```bash
# Check instance profile
aws ec2 describe-instances \
  --instance-ids i-1234567890abcdef0 \
  --query 'Reservations[0].Instances[0].IamInstanceProfile.Arn'

# Check role policies
aws iam list-attached-role-policies --role-name demo-ec2-role
```

## Migration Path

### Current State (Profile-Based)
```bash
AWS_PROFILE="160885257264_AdministratorAccess" \
  ./scripts/deploy_drs_agents.sh 160885257264
```

### Future State (Role-Based)
```bash
export AWS_ROLE_ARN="arn:aws:iam::160885257264:role/DRSOrchestrationRole"
./scripts/deploy_drs_agents.sh 160885257264
```

Both methods work with the same script!

## Related Documentation

- [DRS Deployment Complete](DRS_DEPLOYMENT_COMPLETE.md) - Deployment status
- [AWS Accounts Overview](AWS_ACCOUNTS_OVERVIEW.md) - Multi-account setup
- [AWS IAM Roles Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
