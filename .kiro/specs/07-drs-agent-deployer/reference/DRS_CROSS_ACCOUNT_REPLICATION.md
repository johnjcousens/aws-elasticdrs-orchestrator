# DRS Cross-Account Replication Guide

## Overview

This guide explains how to deploy DRS agents in a source account and replicate data to a separate staging account. This pattern is essential for enterprise DR scenarios where production workloads in one account need to replicate to a dedicated DR account.

## Architecture Pattern

### Cross-Account Replication Flow

```mermaid
flowchart LR
    subgraph Source["Source Account (160885257264)"]
        EC2[EC2 Instances]
        Agent[DRS Agents]
        EC2 --> Agent
    end
    
    subgraph Staging["Staging Account (664418995426)"]
        DRS[DRS Service]
        Staging[Staging Area]
        Recovery[Recovery Instances]
        DRS --> Staging
        Staging -.->|DR Event| Recovery
    end
    
    subgraph Orchestration["Orchestration Account (891376951562)"]
        Lambda[DRS Agent Deployer]
        Lambda -->|Assume Role| Source
        Lambda -->|Assume Role| Staging
    end
    
    Agent -->|Replicate Data| DRS
```

### Key Concepts

1. **Source Account**: Where production workloads run and DRS agents are installed
2. **Staging Account**: Where DRS staging area is created and data replicates to
3. **Orchestration Account**: Central account that manages deployment across accounts

## Deployment Patterns

### Pattern 1: Same-Account Replication

Agents installed in account replicate to the same account:

```json
{
  "source_account_id": "160885257264",
  "source_region": "us-east-1",
  "target_region": "us-west-2",
  "source_role_arn": "arn:aws:iam::160885257264:role/DRSOrchestrationRole"
}
```

**Use Case**: Single-account DR with regional failover

### Pattern 2: Cross-Account Replication

Agents installed in source account replicate to staging account:

```json
{
  "source_account_id": "160885257264",
  "staging_account_id": "664418995426",
  "source_region": "us-east-1",
  "target_region": "us-west-2",
  "source_role_arn": "arn:aws:iam::160885257264:role/DRSOrchestrationRole",
  "staging_role_arn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole"
}
```

**Use Case**: Multi-account DR with dedicated DR account

## Prerequisites

### Source Account Setup

The source account (where instances run) needs:

1. **EC2 Instances with Tags**:
```yaml
Tags:
  - Key: dr:enabled
    Value: 'true'
  - Key: dr:recovery-strategy
    Value: drs
  - Key: dr:wave
    Value: '1'
```

2. **EC2 Instance Profile**:
```yaml
Resources:
  EC2InstanceRole:
    Type: AWS::IAM::Role
    Properties:
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
        - arn:aws:iam::aws:policy/AWSElasticDisasterRecoveryAgentInstallationPolicy
```

3. **Cross-Account Role** (for orchestration):
```yaml
Resources:
  DRSOrchestrationRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: DRSOrchestrationRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: arn:aws:iam::891376951562:root
            Action: sts:AssumeRole
            Condition:
              StringEquals:
                sts:ExternalId: DRSOrchestration2024
      Policies:
        - PolicyName: DRSAgentDeployment
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - ec2:DescribeInstances
                  - ssm:SendCommand
                  - ssm:ListCommandInvocations
                  - ssm:DescribeInstanceInformation
                Resource: '*'
```

### Staging Account Setup

The staging account (where data replicates to) needs:

1. **DRS Service Initialized**:
```bash
# Initialize DRS in staging account
AWS_PROFILE=staging aws drs initialize-service --region us-west-2
```

2. **Cross-Account Role** (for orchestration):
```yaml
Resources:
  DRSOrchestrationRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: DRSOrchestrationRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: arn:aws:iam::891376951562:root
            Action: sts:AssumeRole
            Condition:
              StringEquals:
                sts:ExternalId: DRSOrchestration2024
      Policies:
        - PolicyName: DRSMonitoring
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - drs:DescribeSourceServers
                  - drs:DescribeJobs
                  - drs:DescribeReplicationConfigurationTemplates
                Resource: '*'
```

3. **Replication Configuration Template**:
```bash
# Create replication configuration in staging account
AWS_PROFILE=staging aws drs create-replication-configuration-template \
  --region us-west-2 \
  --staging-area-subnet-id subnet-xxx \
  --associate-default-security-group \
  --bandwidth-throttling 0 \
  --create-public-ip \
  --data-plane-routing PRIVATE_IP \
  --default-large-staging-disk-type GP3 \
  --ebs-encryption DEFAULT \
  --replication-server-instance-type t3.small \
  --replication-servers-security-groups-ids sg-xxx \
  --use-dedicated-replication-server false
```

## Deployment Workflow

### Step 1: Deploy Cross-Account Roles

Deploy the DRSOrchestrationRole to both accounts:

```bash
# Deploy to source account
AWS_PROFILE=source aws cloudformation deploy \
  --template-file cfn/cross-account-role-stack.yaml \
  --stack-name drs-orchestration-role \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides OrchestrationAccountId=891376951562

# Deploy to staging account
AWS_PROFILE=staging aws cloudformation deploy \
  --template-file cfn/cross-account-role-stack.yaml \
  --stack-name drs-orchestration-role \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides OrchestrationAccountId=891376951562
```

### Step 2: Initialize DRS in Staging Account

```bash
AWS_PROFILE=staging aws drs initialize-service --region us-west-2
```

### Step 3: Deploy DRS Agents

**Option A: Direct Lambda Invocation**

```bash
aws lambda invoke \
  --function-name hrp-drs-tech-adapter-drs-agent-deployer-dev \
  --payload file://test-events/cross-account.json \
  response.json

cat response.json | jq .
```

**Option B: API Endpoint**

```bash
curl -X POST https://api.example.com/drs/agents/deploy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_account_id": "160885257264",
    "staging_account_id": "664418995426",
    "source_region": "us-east-1",
    "target_region": "us-west-2",
    "source_role_arn": "arn:aws:iam::160885257264:role/DRSOrchestrationRole",
    "staging_role_arn": "arn:aws:iam::664418995426:role/DRSOrchestrationRole"
  }'
```

**Option C: Python SDK**

```python
import boto3
import json

lambda_client = boto3.client('lambda')

payload = {
    'source_account_id': '160885257264',
    'staging_account_id': '664418995426',
    'source_region': 'us-east-1',
    'target_region': 'us-west-2',
    'source_role_arn': 'arn:aws:iam::160885257264:role/DRSOrchestrationRole',
    'staging_role_arn': 'arn:aws:iam::664418995426:role/DRSOrchestrationRole'
}

response = lambda_client.invoke(
    FunctionName='hrp-drs-tech-adapter-drs-agent-deployer-dev',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
print(json.dumps(result, indent=2))
```

### Step 4: Verify Replication

**Check source servers in staging account**:

```bash
AWS_PROFILE=staging aws drs describe-source-servers \
  --region us-west-2 \
  --query 'items[*].[sourceServerID,tags.Name,dataReplicationInfo.dataReplicationState]' \
  --output table
```

**Monitor replication progress**:

```bash
AWS_PROFILE=staging aws drs describe-source-servers \
  --region us-west-2 \
  --query 'items[*].dataReplicationInfo' \
  --output json
```

## How It Works

### Agent Installation Process

1. **Orchestration Lambda** assumes role in source account
2. **Discovers EC2 instances** with DR tags in source account
3. **Verifies SSM agents** are online on instances
4. **Sends SSM command** to install DRS agents with staging account ID
5. **Agents register** with DRS service in staging account
6. **Orchestration Lambda** assumes role in staging account
7. **Verifies source servers** appear in staging account's DRS console

### DRS Agent Configuration

When installing agents, the SSM command includes:

```bash
# The agent is configured to replicate to staging account
aws ssm send-command \
  --instance-ids i-xxx \
  --document-name AWSDisasterRecovery-InstallDRAgentOnInstance \
  --parameters Region=us-west-2,StagingAccountID=664418995426
```

### Data Replication Flow

1. **DRS agent** on source instance captures block-level changes
2. **Data encrypted** in transit using TLS
3. **Replication** to staging area in staging account
4. **Staging area** stores point-in-time snapshots
5. **Recovery instances** can be launched from staging area during DR event

## Monitoring and Verification

### Check Deployment Status

```bash
# View Lambda logs
aws logs tail /aws/lambda/hrp-drs-tech-adapter-drs-agent-deployer-dev --follow

# Check SSM command status
aws ssm list-command-invocations \
  --command-id abc123-def456 \
  --details
```

### Verify Source Servers

```bash
# List source servers in staging account
AWS_PROFILE=staging aws drs describe-source-servers \
  --region us-west-2

# Check replication state
AWS_PROFILE=staging aws drs describe-source-servers \
  --region us-west-2 \
  --query 'items[*].[sourceServerID,dataReplicationInfo.dataReplicationState]' \
  --output table
```

### Monitor Replication Lag

```bash
# Check replication lag for each server
AWS_PROFILE=staging aws drs describe-source-servers \
  --region us-west-2 \
  --query 'items[*].[sourceServerID,dataReplicationInfo.lagDuration]' \
  --output table
```

## Troubleshooting

### Issue: Agents Not Appearing in Staging Account

**Symptoms**: Agents installed but no source servers in staging account DRS console

**Solutions**:

1. **Verify DRS initialized in staging account**:
```bash
AWS_PROFILE=staging aws drs describe-replication-configuration-templates \
  --region us-west-2
```

2. **Check agent logs on source instance**:
```bash
# Linux
sudo tail -f /var/log/aws-replication-agent/agent.log

# Windows
Get-Content "C:\Program Files\AWS Replication Agent\logs\agent.log" -Tail 50
```

3. **Verify network connectivity**:
```bash
# Test connectivity to DRS endpoints from source instance
curl -v https://drs.us-west-2.amazonaws.com
```

### Issue: Permission Denied

**Symptoms**: "AccessDeniedException" or "UnauthorizedOperation"

**Solutions**:

1. **Verify cross-account roles exist**:
```bash
aws iam get-role --role-name DRSOrchestrationRole
```

2. **Check external ID matches**:
```bash
aws iam get-role --role-name DRSOrchestrationRole \
  --query 'Role.AssumeRolePolicyDocument'
```

3. **Verify instance profile has DRS permissions**:
```bash
aws iam list-attached-role-policies --role-name EC2InstanceRole
```

### Issue: Replication Stalled

**Symptoms**: Replication state stuck at "INITIAL_SYNC" or "STALLED"

**Solutions**:

1. **Check replication server status**:
```bash
AWS_PROFILE=staging aws ec2 describe-instances \
  --filters "Name=tag:AWSElasticDisasterRecoveryService,Values=*" \
  --region us-west-2
```

2. **Verify bandwidth throttling**:
```bash
AWS_PROFILE=staging aws drs get-replication-configuration \
  --source-server-id s-xxx \
  --region us-west-2
```

3. **Check CloudWatch metrics**:
```bash
AWS_PROFILE=staging aws cloudwatch get-metric-statistics \
  --namespace AWS/DRS \
  --metric-name ReplicationLag \
  --dimensions Name=SourceServerID,Value=s-xxx \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average
```

## Security Considerations

### 1. Least Privilege

Each role should have minimum permissions:

- **Source account role**: EC2 read, SSM command execution only
- **Staging account role**: DRS read-only for monitoring
- **Instance profile**: SSM managed instance core + DRS agent installation

### 2. External ID

Always use external ID for cross-account role assumption:

```yaml
Condition:
  StringEquals:
    sts:ExternalId: DRSOrchestration2024
```

### 3. Encryption

- **In-transit**: DRS uses TLS for replication traffic
- **At-rest**: Staging area uses encrypted EBS volumes
- **KMS**: Use customer-managed keys for additional control

### 4. Network Isolation

- **VPC endpoints**: Use VPC endpoints for DRS API calls
- **Private subnets**: Deploy replication servers in private subnets
- **Security groups**: Restrict replication server access

## Cost Optimization

### DRS Pricing (Cross-Account)

- **Per source server**: ~$0.028/hour (~$20/month per server)
- **Staging area storage**: EBS snapshots (incremental)
- **Data transfer**: Free within same region, charged for cross-region
- **Replication servers**: t3.small instances (on-demand or spot)

### Cost Optimization Tips

1. **Use spot instances** for replication servers
2. **Enable compression** to reduce data transfer
3. **Optimize snapshot retention** in staging area
4. **Use GP3 volumes** instead of GP2 for staging
5. **Monitor and remove** unused source servers

## Best Practices

### 1. Tag Strategy

Use consistent tags across all DR-enabled instances:

```yaml
Tags:
  - Key: dr:enabled
    Value: 'true'
  - Key: dr:recovery-strategy
    Value: drs
  - Key: dr:wave
    Value: '1'
  - Key: dr:staging-account
    Value: '664418995426'
  - Key: dr:target-region
    Value: us-west-2
```

### 2. Testing

- **Test in non-production** accounts first
- **Perform regular DR drills** to verify recovery
- **Document recovery procedures** for each wave
- **Automate testing** using Step Functions

### 3. Monitoring

Set up CloudWatch alarms for:

- Replication lag exceeding threshold
- Source server disconnections
- Staging area disk space
- Failed recovery drills

### 4. Documentation

Maintain documentation for:

- Account mappings (source → staging)
- Network topology and connectivity
- Recovery procedures by wave
- Runbook for common issues

## Related Documentation

- [DRS Agent Deployment Guide](DRS_AGENT_DEPLOYMENT_GUIDE.md) - Complete deployment guide
- [DRS Cross-Account Orchestration](../DRS_CROSS_ACCOUNT_ORCHESTRATION.md) - Orchestration patterns
- [AWS DRS Documentation](https://docs.aws.amazon.com/drs/) - Official AWS documentation

## Support

For issues or questions:

1. Check CloudWatch Logs for Lambda errors
2. Review this guide's troubleshooting section
3. Verify cross-account roles and permissions
4. Consult AWS DRS documentation
5. Contact platform team
