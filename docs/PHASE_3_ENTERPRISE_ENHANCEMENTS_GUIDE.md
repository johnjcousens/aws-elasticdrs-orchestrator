# Phase 3: Enterprise Enhancements Implementation Guide

**Document Version:** 1.0  
**Last Updated:** November 28, 2025  
**Status:** Implementation Ready

---

## Executive Summary

This comprehensive guide extends the AWS DRS Orchestration solution from basic wave-based recovery (Phase 1) to an enterprise-grade disaster recovery automation platform. Based on analysis of AWS's DRS Plan Automation sample solution, this implementation adds:

- ✅ **Multi-Account Support** - Central control plane managing DR across multiple AWS accounts
- ✅ **Pre/Post Wave Hooks** - Automated managed service orchestration (RDS, Route53, etc.)
- ✅ **SSM Automation Integration** - Leverage AWS Systems Manager for complex workflows
- ✅ **Cross-Account IAM** - Secure role assumption for target account access

**Estimated Implementation Time:** 16-20 hours across 5 phases  
**Complexity Level:** Advanced (requires IAM, cross-account, SSM expertise)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Multi-Account Architecture](#2-multi-account-architecture)  
3. [Pre/Post Wave Hooks Design](#3-prepost-wave-hooks-design)
4. [Database Schema Enhancements](#4-database-schema-enhancements)
5. [Lambda Implementation](#5-lambda-implementation)
6. [CloudFormation Templates](#6-cloudformation-templates)
7. [Frontend Enhancements](#7-frontend-enhancements)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Testing & Validation](#9-testing--validation)
10. [Production Use Cases](#10-production-use-cases)
11. [Troubleshooting Guide](#11-troubleshooting-guide)

---

## 1. Architecture Overview

### 1.1 Current State (Phase 1)

```
Central Account Only
├── Frontend (React + Amplify Auth)
├── API Gateway + Lambda
├── DynamoDB (Plans, Executions)
├── ExecutionPoller (EventBridge)
└── DRS API Calls (Same Account)
```

### 1.2 Target State (Phase 3)

```
Central Orchestration Account
├── Frontend (Multi-Account UI)
├── API Gateway (Cognito Auth)
├── Lambda (Cross-Account Client)
├── DynamoDB
│   ├── Plans
│   ├── Executions
│   └── Accounts ◄── NEW
├── EventBridge Triggers
└── STS AssumeRole ─┐
                     │
    ┌────────────────┴────────────────┐
    │                                  │
DR Account 1            DR Account 2            DR Account 3
├── DRS Jobs            ├── DRS Jobs            ├── DRS Jobs
├── SSM Automation      ├── SSM Automation      ├── SSM Automation
├── RDS/Route53/etc     ├── RDS/Route53/etc     ├── RDS/Route53/etc
└── CrossAccountRole    └── CrossAccountRole    └── CrossAccountRole
```

---

## 2. Multi-Account Architecture

### 2.1 Account Configuration Table

**DynamoDB Table:** `drs-orchestration-accounts-test`

```python
{
    'AccountId': 'string',           # PARTITION KEY
    'Region': 'string',              # SORT KEY  
    'AccountName': 'string',         # Display name
    'AssumeRoleArn': 'string',       # Cross-account role ARN
    'Description': 'string',
    'Environment': 'string',         # prod/staging/dev
    'Status': 'string',              # ACTIVE/INACTIVE
    'CreatedAt': 'string',          # ISO timestamp
    'UpdatedAt': 'string'
}
```

### 2.2 Cross-Account IAM Setup

#### Step 1: Central Account Lambda Role

Add to existing `drs-orchestration-lambda-role`:

```yaml
# Add to cfn/lambda-stack.yaml
- PolicyName: CrossAccountAssumeRole
  PolicyDocument:
    Statement:
      - Effect: Allow
        Action:
          - sts:AssumeRole
        Resource: 
          - 'arn:aws:iam::*:role/DRSOrchestrationCrossAccountRole'
```

#### Step 2: Target Account Role (Deploy in each DR account)

```yaml
# cfn/cross-account-role-template.yaml (NEW FILE)
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Cross-account role for DRS Orchestration'

Parameters:
  CentralAccountId:
    Type: String
    Description: Central orchestration account ID

Resources:
  DRSOrchestrationCrossAccountRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: DRSOrchestrationCrossAccountRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${CentralAccountId}:role/drs-orchestration-lambda-role-test'
            Action: 'sts:AssumeRole'
            Condition:
              StringEquals:
                'sts:ExternalId': 'DRSOrchestration2025'
      ManagedPolicyArns:
        - 'arn:aws:iam::aws:policy/AWSElasticDisasterRecoveryRecoveryInstancePolicy'
      Policies:
        - PolicyName: DRSOrchestrationAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              # DRS Permissions
              - Effect: Allow
                Action:
                  - 'drs:*'
                Resource: '*'
              
              # SSM Automation
              - Effect: Allow
                Action:
                  - 'ssm:StartAutomationExecution'
                  - 'ssm:GetAutomationExecution'
                  - 'ssm:DescribeAutomationExecutions'
                  - 'ssm:DescribeAutomationStepExecutions'
                  - 'ssm:StopAutomationExecution'
                  - 'ssm:SendCommand'
                  - 'ssm:GetCommandInvocation'
                Resource: '*'
              
              # RDS Snapshots
              - Effect: Allow
                Action:
                  - 'rds:CreateDBSnapshot'
                  - 'rds:DescribeDBSnapshots'
                  - 'rds:DescribeDBInstances'
                Resource: '*'
              
              # Route53 DNS
              - Effect: Allow
                Action:
                  - 'route53:ChangeResourceRecordSets'
                  - 'route53:GetChange'
                  - 'route53:ListResourceRecordSets'
                Resource: '*'
              
              # EC2 for health checks
              - Effect: Allow
                Action:
                  - 'ec2:DescribeInstances'
                  - 'ec2:DescribeInstanceStatus'
                  - 'ec2:DescribeVolumes'
                  - 'ec2:CreateSnapshot'
                  - 'ec2:DescribeSnapshots'
                Resource: '*'
              
              # Lambda invocation
              - Effect: Allow
                Action:
                  - 'lambda:InvokeFunction'
                Resource: !Sub 'arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:function:*'
              
              # SNS notifications
              - Effect: Allow
                Action:
                  - 'sns:Publish'
                Resource: !Sub 'arn:aws:sns:${AWS::Region}:${AWS::AccountId}:*'
              
              # CloudWatch Logs
              - Effect: Allow
                Action:
                  - 'logs:CreateLogGroup'
                  - 'logs:CreateLogStream'
                  - 'logs:PutLogEvents'
                Resource: '*'

Outputs:
  RoleArn:
    Description: Cross-account role ARN
    Value: !GetAtt DRSOrchestrationCrossAccountRole.Arn
    Export:
      Name: !Sub '${AWS::StackName}-RoleArn'
```

### 2.3 Lambda Cross-Account Client

```python
# lambda/cross_account_client.py (NEW FILE)

import boto3
import os
from typing import Dict

class CrossAccountClient:
    """Manages cross-account AWS service clients."""
    
    def __init__(self):
        self.sts_client = boto3.client('sts')
        self.accounts_table = boto3.resource('dynamodb').Table(
            os.environ['ACCOUNTS_TABLE_NAME']
        )
        self._credential_cache = {}
    
    def get_account_config(self, account_id: str, region: str) -> Dict:
        """Fetch account configuration from DynamoDB."""
        response = self.accounts_table.get_item(
            Key={'AccountId': account_id, 'Region': region}
        )
        
        if 'Item' not in response:
            raise ValueError(f"Account {account_id} in {region} not configured")
        
        account = response['Item']
        
        if account.get('Status') != 'ACTIVE':
            raise ValueError(f"Account {account_id} is not ACTIVE")
        
        return account
    
    def assume_role(self, role_arn: str) -> Dict:
        """Assume role and return temporary credentials."""
        cache_key = role_arn
        
        # Check cache (credentials valid for 1 hour)
        if cache_key in self._credential_cache:
            cached = self._credential_cache[cache_key]
            # Simple expiration check (credentials expire in 1 hour)
            # In production, implement proper expiration tracking
            return cached['credentials']
        
        response = self.sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName='DRSOrchestration',
            DurationSeconds=3600,  # 1 hour
            ExternalId='DRSOrchestration2025'
        )
        
        credentials = response['Credentials']
        
        # Cache credentials
        self._credential_cache[cache_key] = {
            'credentials': credentials,
            'expiration': credentials['Expiration']
        }
        
        return credentials
    
    def get_client(self, service_name: str, account_id: str, region: str):
        """Get boto3 client for service in target account."""
        
        # Get account configuration
        account = self.get_account_config(account_id, region)
        
        # Assume role
        credentials = self.assume_role(account['AssumeRoleArn'])
        
        # Create client with assumed credentials
        return boto3.client(
            service_name,
            region_name=region,
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )

# Global instance
cross_account_client = CrossAccountClient()
```

---

## 3. Pre/Post Wave Hooks Design

### 3.1 Enhanced Wave Data Model

```python
# Enhanced Wave structure with actions
{
    'WaveId': 'uuid',
    'WaveName': 'Database Tier',
    'AccountId': '123456789012',     # NEW
    'Region': 'us-east-2',           # NEW
    'Servers': [...],
    'WaitTime': 300,
    'Dependencies': [],
    
    'PreWaveActions': [              # NEW
        {
            'ActionId': 'uuid',
            'ActionName': 'Snapshot RDS',
            'ActionType': 'SSM_AUTOMATION',
            'DocumentName': 'AWS-CreateRDSSnapshot',
            'Parameters': {
                'DBInstanceIdentifier': ['prod-db'],
                'DBSnapshotIdentifier': ['pre-recovery-{timestamp}']
            },
            'MaxWaitTime': 900,
            'Required': True,
            'Order': 1
        }
    ],
    
    'PostWaveActions': [             # NEW
        {
            'ActionId': 'uuid',
            'ActionName': 'Verify Health',
            'ActionType': 'SSM_AUTOMATION',
            'DocumentName': 'Custom-HealthCheck',
            'Parameters': {...},
            'MaxWaitTime': 300,
            'Required': False,
            'Order': 1
        }
    ]
}
```

### 3.2 Action Execution Logic

```python
# lambda/wave_actions.py (NEW FILE)

import json
from typing import Dict, List, Any
from cross_account_client import cross_account_client

def execute_wave_actions(
    actions: List[Dict],
    execution_id: str,
    wave_id: str,
    account_id: str,
    region: str
) -> List[Dict]:
    """Execute list of actions sequentially."""
    
    results = []
    
    # Sort actions by order
    sorted_actions = sorted(actions, key=lambda x: x.get('Order', 999))
    
    for action in sorted_actions:
        print(f"Executing action: {action['ActionName']}")
        
        # Add execution context
        action['ExecutionId'] = execution_id
        action['WaveId'] = wave_id
        action['AccountId'] = account_id
        action['Region'] = region
        
        # Execute based on type
        result = execute_action(action)
        results.append(result)
        
        # Check if required action failed
        if action.get('Required') and result['Status'] != 'Success':
            error_msg = f"Required action '{action['ActionName']}' failed"
            print(error_msg)
            raise Exception(error_msg)
        
        print(f"Action '{action['ActionName']}' completed with status: {result['Status']}")
    
    return results


def execute_action(action: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch action to appropriate handler."""
    
    action_type = action.get('ActionType', '').upper()
    
    if action_type == 'SSM_AUTOMATION':
        return execute_ssm_automation(action)
    elif action_type == 'LAMBDA':
        return execute_lambda_action(action)
    elif action_type == 'SNS':
        return execute_sns_notification(action)
    else:
        return {
            'ActionId': action['ActionId'],
            'ActionName': action['ActionName'],
            'Status': 'Failed',
            'Error': f'Unsupported action type: {action_type}'
        }


def execute_ssm_automation(action: Dict) -> Dict:
    """Execute SSM Automation document."""
    
    account_id = action['AccountId']
    region = action['Region']
    
    try:
        # Get SSM client for target account
        ssm_client = cross_account_client.get_client('ssm', account_id, region)
        
        # Start automation
        response = ssm_client.start_automation_execution(
            DocumentName=action['DocumentName'],
            Parameters=action.get('Parameters', {}),
            Tags=[
                {'Key': 'ExecutionId', 'Value': action['ExecutionId']},
                {'Key': 'WaveId', 'Value': action['WaveId']},
                {'Key': 'ManagedBy', 'Value': 'DRSOrchestration'}
            ]
        )
        
        automation_id = response['AutomationExecutionId']
        print(f"Started SSM Automation: {automation_id}")
        
        # Poll for completion
        status = poll_ssm_execution(
            ssm_client,
            automation_id,
            action.get('MaxWaitTime', 600)
        )
        
        return {
            'ActionId': action['ActionId'],
            'ActionName': action['ActionName'],
            'ActionType': 'SSM_AUTOMATION',
            'ExecutionId': automation_id,
            'Status': status,
            'DocumentName': action['DocumentName']
        }
    
    except Exception as e:
        print(f"SSM Automation error: {str(e)}")
        return {
            'ActionId': action['ActionId'],
            'ActionName': action['ActionName'],
            'ActionType': 'SSM_AUTOMATION',
            'Status': 'Failed',
            'Error': str(e)
        }


def poll_ssm_execution(ssm_client, execution_id: str, max_wait: int) -> str:
    """Poll SSM automation until complete."""
    import time
    
    start_time = time.time()
    terminal_statuses = ['Success', 'Failed', 'TimedOut', 'Cancelled']
    
    while time.time() - start_time < max_wait:
        response = ssm_client.describe_automation_executions(
            Filters=[{'Key': 'ExecutionId', 'Values': [execution_id]}]
        )
        
        if response['AutomationExecutionMetadataList']:
            status = response['AutomationExecutionMetadataList'][0]['AutomationExecutionStatus']
            
            if status in terminal_statuses:
                return status
        
        time.sleep(10)
    
    return 'TimedOut'


def execute_lambda_action(action: Dict) -> Dict:
    """Invoke Lambda function."""
    
    account_id = action['AccountId']
    region = action['Region']
    
    try:
        lambda_client = cross_account_client.get_client('lambda', account_id, region)
        
        response = lambda_client.invoke(
            FunctionName=action['FunctionArn'],
            InvocationType='RequestResponse',
            Payload=json.dumps(action.get('Payload', {}))
        )
        
        status = 'Success' if response['StatusCode'] == 200 else 'Failed'
        
        return {
            'ActionId': action['ActionId'],
            'ActionName': action['ActionName'],
            'ActionType': 'LAMBDA',
            'Status': status,
            'FunctionArn': action['FunctionArn']
        }
    
    except Exception as e:
        return {
            'ActionId': action['ActionId'],
            'ActionName': action['ActionName'],
            'ActionType': 'LAMBDA',
            'Status': 'Failed',
            'Error': str(e)
        }


def execute_sns_notification(action: Dict) -> Dict:
    """Send SNS notification."""
    
    account_id = action.get('AccountId')
    region = action['Region']
    
    try:
        if account_id:
            sns_client = cross_account_client.get_client('sns', account_id, region)
        else:
            sns_client = boto3.client('sns', region_name=region)
        
        response = sns_client.publish(
            TopicArn=action['TopicArn'],
            Message=action.get('Message', ''),
            Subject=action.get('Subject', 'DRS Orchestration')
        )
        
        return {
            'ActionId': action['ActionId'],
            'ActionName': action['ActionName'],
            'ActionType': 'SNS',
            'Status': 'Success',
            'MessageId': response['MessageId']
        }
    
    except Exception as e:
        return {
            'ActionId': action['ActionId'],
            'ActionName': action['ActionName'],
            'ActionType': 'SNS',
            'Status': 'Failed',
            'Error': str(e)
        }
```

---

## 4. Database Schema Enhancements

### 4.1 Accounts Table

```yaml
# cfn/database-stack.yaml - Add new table

  AccountsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub 'drs-orchestration-accounts-${Environment}'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: AccountId
          AttributeType: S
        - AttributeName: Region
          AttributeType: S
      KeySchema:
        - AttributeName: AccountId
          KeyType: HASH
        - AttributeName: Region
          KeyType: RANGE
      Tags:
        - Key: Application
          Value: DRS-Orchestration
```

### 4.2 Enhanced Recovery Plan Schema

Add to existing RecoveryPlans table items:

```python
# Enhanced Plan structure
{
    'PlanId': 'uuid',
    'PlanName': 'Production Recovery',
    'DefaultAccountId': '123456789012',  # NEW: Default target account
    'DefaultRegion': 'us-east-2',        # NEW: Default target region
    'Waves': [
        {
            'WaveId': 'uuid',
            'WaveName': 'Database Tier',
            'AccountId': '123456789012',  # NEW: Override default
            'Region': 'us-east-2',        # NEW: Override default
            'Servers': [...],
            'PreWaveActions': [...],      # NEW
            'PostWaveActions': [...]      # NEW
        }
    ]
}
```

---

## 5. Lambda Implementation

### 5.1 Enhanced initiate_wave Function

```python
# lambda/index.py - Update existing function

def initiate_wave(execution_id, plan_id, wave_data, is_drill):
    """
    Enhanced wave initiation with pre/post hooks.
    
    Execution flow:
    1. Execute PreWave actions
    2. Launch DRS recovery
    3. Poll DRS job
    4. Execute PostWave actions
    """
    
    wave_id = wave_data['WaveId']
    wave_name = wave_data['WaveName']
    account_id = wave_data.get('AccountId')
    region = wave_data.get('Region', 'us-east-2')
    
    print(f"Initiating wave: {wave_name} (Account: {account_id}, Region: {region})")
    
    action_results = []
    
    try:
        # ===== STEP 1: PreWave Actions =====
        if wave_data.get('PreWaveActions'):
            print(f"Executing {len(wave_data['PreWaveActions'])} PreWave actions...")
            
            pre_results = execute_wave_actions(
                wave_data['PreWaveActions'],
                execution_id,
                wave_id,
                account_id,
                region
            )
            
            action_results.extend(pre_results)
            print("PreWave actions completed")
        
        # ===== STEP 2: DRS Recovery (Existing Phase 1 Logic) =====
        print("Starting DRS recovery...")
        
        wave_servers = wave_data.get('Servers', [])
        
        if not wave_servers:
            raise Exception(f"Wave {wave_name} has no servers")
        
        # Use cross-account DRS client if account specified
        if account_id:
            drs_client = cross_account_client.get_client('drs', account_id, region)
        else:
            drs_client = boto3.client('drs', region_name=region)
        
        # Launch recovery for all servers in wave (single DRS job)
        source_server_ids = [s['SourceServerId'] for s in wave_servers]
        
        response = drs_client.start_recovery(
            sourceServerIDs=source_server_ids,
            isDrill=is_drill,
            tags=get_drs_tags(execution_id, plan_id, wave_id)
        )
        
        job_id = response['job']['jobID']
        wave_data['JobId'] = job_id
        wave_data['Status'] = 'INITIATED'
        
        print(f"DRS job started: {job_id}")
        
        # Update wave in execution
        update_wave_in_execution(execution_id, wave_data)
        
        # ===== STEP 3: DRS Job Polling =====
        # Note: ExecutionPoller handles this asynchronously
        print(f"Wave {wave_name} DRS job launched. Poller will monitor completion.")
        
        # ===== STEP 4: PostWave Actions =====
        # Note: These run AFTER DRS job completes (handled by poller)
        # Store PostWave actions in wave data for poller execution
        
        return {
            'WaveId': wave_id,
            'WaveName': wave_name,
            'JobId': job_id,
            'Status': 'INITIATED',
            'ActionResults': action_results
        }
    
    except Exception as e:
        error_msg = f"Wave initiation failed: {str(e)}"
        print(error_msg)
        
        wave_data['Status'] = 'FAILED'
        wave_data['Error'] = error_msg
        wave_data['ActionResults'] = action_results
        
        update_wave_in_execution(execution_id, wave_data)
        
        raise


def execute_post_wave_actions(execution_id, wave_data):
    """
    Execute PostWave actions after DRS job completes.
    Called by ExecutionPoller when wave status becomes COMPLETED.
    """
    
    if not wave_data.get('PostWaveActions'):
        print("No PostWave actions to execute")
        return []
    
    wave_id = wave_data['WaveId']
    account_id = wave_data.get('AccountId')
    region = wave_data.get('Region', 'us-east-2')
    
    print(f"Executing {len(wave_data['PostWaveActions'])} PostWave actions...")
    
    try:
        results = execute_wave_actions(
            wave_data['PostWaveActions'],
            execution_id,
            wave_id,
            account_id,
            region
        )
        
        print("PostWave actions completed")
        return results
    
    except Exception as e:
        print(f"PostWave actions failed: {str(e)}")
        return [{
            'Status': 'Failed',
            'Error': str(e)
        }]
```

### 5.2 Enhanced ExecutionPoller

```python
# lambda/poller/execution_poller.py - Update

def check_wave_completion(execution_id, wave):
    """Enhanced to execute PostWave actions when DRS job completes."""
    
    job_id = wave.get('JobId')
    account_id = wave.get('AccountId')
    region = wave.get('Region', 'us-east-2')
    
    # Get DRS client (cross-account if needed)
    if account_id:
        drs_client = cross_account_client.get_client('drs', account_id, region)
    else:
        drs_client = boto3.client('drs', region_name=region)
    
    # Check job status
    job = drs_client.describe_jobs(
        filters={'jobIDs': [job_id]}
    )['items'][0]
    
    job_status = job['status']
    
    if job_status == 'COMPLETED':
        # DRS job complete - execute PostWave actions
        print(f"Wave {wave['WaveName']} DRS job completed. Executing PostWave actions...")
        
        post_results = execute_post_wave_actions(execution_id, wave)
        
        wave['Status'] = 'COMPLETED'
        wave['PostWaveActionResults'] = post_results
        wave['CompletedAt'] = datetime.utcnow().isoformat()
        
        return True
    
    elif job_status in ['FAILED', 'PARTIAL']:
        wave['Status'] = job_status
        wave['CompletedAt'] = datetime.utcnow().isoformat()
        return True
    
    # Still running
    return False
```

---

## 6. CloudFormation Templates

### 6.1 Deploy Accounts Table

```bash
# Deploy accounts table
aws cloudformation deploy \
  --template-file cfn/database-stack.yaml \
  --stack-name drs-orchestration-database-test \
  --parameter-overrides Environment=test \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

### 6.2 Deploy Cross-Account Roles (In Each DR Account)

```bash
# Deploy in DR account 1
aws cloudformation deploy \
  --template-file cfn/cross-account-role-template.yaml \
  --stack-name drs-orchestration-cross-account-role \
  --parameter-overrides CentralAccountId=YOUR_CENTRAL_ACCOUNT_ID \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-2 \
  --profile dr-account-1

# Get role ARN
aws cloudformation describe-stacks \
  --stack-name drs-orchestration-cross-account-role \
  --query 'Stacks[0].Outputs[?OutputKey==`RoleArn`].OutputValue' \
  --output text \
  --region us-east-2 \
  --profile dr-account-1
```

### 6.3 Add Account Configuration

```python
# Add account to DynamoDB
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
accounts_table = dynamodb.Table('drs-orchestration-accounts-test')

account = {
    'AccountId': '123456789012',
    'Region': 'us-east-2',
    'AccountName': 'Production DR Account',
    'AssumeRoleArn': 'arn:aws:iam::123456789012:role/DRSOrchestrationCrossAccountRole',
    'Description': 'Production workloads DR in Ohio',
    'Environment': 'production',
    'Status': 'ACTIVE',
    'CreatedAt': '2025-11-28T00:00:00Z',
    'UpdatedAt': '2025-11-28T00:00:00Z'
}

accounts_table.put_item(Item=account)
```

---

## 7. Frontend Enhancements

### 7.1 Account Management Page

Create `frontend/src/pages/AccountsPage.tsx`:

```typescript
// Account management UI for multi-account configuration
// Features:
// - List configured accounts
// - Add/Edit/Delete accounts
// - Test cross-account access
// - View account status
```

### 7.2 Enhanced Recovery Plan Dialog

Update `frontend/src/components/RecoveryPlanDialog.tsx`:

```typescript
// Add fields:
// - Default Account selector
// - Default Region selector
// - Per-wave account/region override
// - PreWave Actions configuration
// - PostWave Actions configuration
```

### 7.3 Action Configuration Component

Create `frontend/src/components/WaveActionDialog.tsx`:

```typescript
// Wave action configuration UI
// - Action type selector (SSM/Lambda/SNS)
// - SSM Document picker
// - Parameter editor (JSON)
// - Timeout configuration
// - Required checkbox
// - Order field
```

---

## 8. Implementation Roadmap

### Phase 3A: Multi-Account Foundation (4 hours)

**Tasks:**
1. ✅ Deploy accounts table
2.
