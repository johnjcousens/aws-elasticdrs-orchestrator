# DRS Capacity Scaling Architecture

## Overview

This architecture bypasses AWS DRS's 300 source servers per account limit by using a staging account pattern with extended source servers, allowing up to 600 total protected instances.

## Account Configuration

- **Target Account**: 111122223333
  - Source instances in Region A (e.g., us-east-1) - up to 300 instances
  - Recovery destination in Region B (e.g., us-west-2)
  - Views extended source servers from staging account
  
- **Staging Account**: 444455556666
  - Source instances (up to 300 instances)
  - DRS agents replicate to target account via extended source servers
  - Shared EBS encryption key for cross-account recovery

- **Orchestration Account**: 777788889999
  - Lambda function for automated agent deployment
  - Assumes roles in both target and staging accounts

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Target Account (111122223333)                                           │
│                                                                          │
│  Region A (us-east-1)              Region B (us-west-2)                 │
│  ┌──────────────────────┐          ┌──────────────────────┐            │
│  │ Source Instances     │          │ Recovery Instances   │            │
│  │ (up to 300)          │──DRS────▶│ (launched here)      │            │
│  │ + DRS Agents         │          │                      │            │
│  └──────────────────────┘          └──────────────────────┘            │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │ Extended Source Servers View                             │          │
│  │ (shows staging account source servers)                   │          │
│  └──────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
                                     ▲
                                     │
                                     │ Cross-Account Replication
                                     │ (via Extended Source Servers)
                                     │
┌─────────────────────────────────────────────────────────────────────────┐
│ Staging Account (444455556666)                                          │
│                                                                          │
│  ┌──────────────────────┐          ┌──────────────────────┐            │
│  │ Source Instances     │          │ DRS Staging Area     │            │
│  │ (up to 300)          │──DRS────▶│ (replication data)   │            │
│  │ + DRS Agents         │          │                      │            │
│  └──────────────────────┘          └──────────────────────┘            │
│                                                                          │
│  Recovery Target: 111122223333 (via extended source servers)            │
└─────────────────────────────────────────────────────────────────────────┘

Total Capacity: 600 source servers (300 in target + 300 in staging)
```

## DRS Service Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Source servers per account | 300 | Hard limit per AWS account |
| Extended source servers | Yes | Allows cross-account replication |
| Total with staging pattern | 600 | 300 in target + 300 in staging |

## Extended Source Servers

**What are Extended Source Servers?**

Extended source servers is a DRS feature that allows source servers from one account (staging) to replicate to and be viewed from another account (target). This enables:

1. **Capacity Scaling**: Bypass 300 server limit per account
2. **Centralized Recovery**: All instances recover to single target account
3. **Unified Management**: View all source servers in target account DRS console

**Configuration:**

In target account (111122223333):
```bash
# Enable extended source servers view
AWS_PAGER="" aws drs update-launch-configuration \
  --source-server-id s-XXXXXXXXX \
  --target-instance-type-right-sizing-method BASIC

# View extended source servers from staging account
AWS_PAGER="" aws drs describe-source-servers \
  --filters '{"stagingAccountIDs": ["444455556666"]}' \
  --region us-west-2
```

## Deployment Patterns

### Pattern 1: Target Account Instances (Same Account)

**Scenario**: Deploy agents to instances in target account Region A, replicate to Region B

```json
{
  "source_account_id": "111122223333",
  "staging_account_id": "111122223333",
  "source_region": "us-east-1",
  "target_region": "us-west-2",
  "source_role_arn": "arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev",
  "staging_role_arn": "arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev",
  "external_id": "drs-orchestration-dev-111122223333",
  "deployment_pattern": "same-account"
}
```

**Result**: Up to 300 source servers in target account

### Pattern 2: Staging Account Instances (Extended Source Servers)

**Scenario**: Deploy agents to instances in staging account, replicate to target account via extended source servers

```json
{
  "source_account_id": "444455556666",
  "staging_account_id": "444455556666",
  "target_account_id": "111122223333",
  "source_region": "us-east-1",
  "target_region": "us-west-2",
  "source_role_arn": "arn:aws:iam::444455556666:role/DRSOrchestrationRole-dev",
  "staging_role_arn": "arn:aws:iam::444455556666:role/DRSOrchestrationRole-dev",
  "external_id": "drs-orchestration-dev-444455556666",
  "deployment_pattern": "extended-source-servers",
  "extended_source_server_config": {
    "target_account_id": "111122223333",
    "shared_kms_key_arn": "arn:aws:kms:us-west-2:111122223333:key/XXXXXXXX"
  }
}
```

**Result**: Up to 300 additional source servers visible in target account via extended source servers

### Pattern 3: Combined (Maximum Capacity)

Deploy to both accounts for 600 total source servers:

1. Deploy 300 agents to target account instances (Pattern 1)
2. Deploy 300 agents to staging account instances (Pattern 2)
3. View all 600 source servers in target account DRS console

## Prerequisites

### Target Account (111122223333)

- [x] DRS initialized in source region (us-east-1)
- [x] DRS initialized in target region (us-west-2)
- [ ] Extended source servers enabled
- [ ] Shared EBS encryption key created
- [ ] KMS key policy allows staging account
- [ ] DRSOrchestrationRole created
- [ ] EC2 instances tagged for DR

### Staging Account (444455556666)

- [x] DRS initialized
- [x] Trusted accounts configured (target account)
- [ ] DRSOrchestrationRole created
- [ ] EC2 instances tagged for DR
- [ ] Replication configuration points to target account

### Orchestration Account (777788889999)

- [ ] Lambda function deployed
- [ ] Can assume roles in target and staging accounts
- [ ] DynamoDB table for deployment tracking

## Setup Steps

### Step 1: Configure Extended Source Servers in Target Account

```bash
# In target account (111122223333)
# Enable extended source servers

# Update DRS settings to accept extended source servers
AWS_PAGER="" aws drs update-replication-configuration-template \
  --region us-west-2 \
  --associate-default-security-group \
  --bandwidth-throttling 0 \
  --create-public-ip false \
  --data-plane-routing PRIVATE_IP \
  --default-large-staging-disk-type GP3 \
  --ebs-encryption DEFAULT \
  --replication-server-instance-type t3.small \
  --use-dedicated-replication-server false

# Verify extended source servers setting
AWS_PAGER="" aws drs get-replication-configuration-template \
  --region us-west-2
```

### Step 2: Configure Staging Account to Replicate to Target

```bash
# In staging account (444455556666)
# Configure DRS to replicate to target account

# Add target account as trusted account
AWS_PAGER="" aws drs update-replication-configuration-template \
  --region us-east-1 \
  --staging-area-subnet-id subnet-XXXXXXXXX \
  --associate-default-security-group \
  --bandwidth-throttling 0 \
  --create-public-ip false \
  --data-plane-routing PRIVATE_IP \
  --default-large-staging-disk-type GP3 \
  --ebs-encryption DEFAULT \
  --replication-server-instance-type t3.small \
  --use-dedicated-replication-server false
```

### Step 3: Configure Shared EBS Encryption Key

```bash
# In target account (111122223333)
# Create or update KMS key policy

cat > kms-key-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111122223333:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow staging account to use key for DRS",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::444455556666:root",
          "arn:aws:iam::444455556666:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery"
        ]
      },
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:CreateGrant",
        "kms:RetireGrant"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "drs.us-west-2.amazonaws.com",
            "ec2.us-west-2.amazonaws.com"
          ]
        }
      }
    }
  ]
}
EOF

# Apply key policy
aws kms put-key-policy \
  --key-id alias/drs-shared-ebs-key \
  --policy-name default \
  --policy file://kms-key-policy.json \
  --region us-west-2
```

### Step 4: Tag Instances

**Target Account Instances:**
```bash
# In target account (111122223333)
aws ec2 create-tags \
  --region us-east-1 \
  --resources i-XXXXXXXXX i-YYYYYYYYY \
  --tags \
    Key=dr:enabled,Value=true \
    Key=dr:recovery-strategy,Value=drs \
    Key=dr:wave,Value=wave-1 \
    Key=dr:priority,Value=1 \
    Key=dr:account-type,Value=target \
    Key=dr:target-region,Value=us-west-2
```

**Staging Account Instances:**
```bash
# In staging account (444455556666)
aws ec2 create-tags \
  --region us-east-1 \
  --resources i-XXXXXXXXX i-YYYYYYYYY \
  --tags \
    Key=dr:enabled,Value=true \
    Key=dr:recovery-strategy,Value=drs \
    Key=dr:wave,Value=wave-1 \
    Key=dr:priority,Value=1 \
    Key=dr:account-type,Value=staging \
    Key=dr:target-account,Value=111122223333 \
    Key=dr:target-region,Value=us-west-2
```

### Step 5: Install DRS Agents

**Option A: Via Lambda (Automated)**
```bash
# Deploy to target account instances
aws lambda invoke \
  --function-name drs-agent-deployer \
  --payload file://target-account-deployment.json \
  response.json

# Deploy to staging account instances
aws lambda invoke \
  --function-name drs-agent-deployer \
  --payload file://staging-account-deployment.json \
  response.json
```

**Option B: Via SSM (Manual)**
```bash
# Target account
aws ssm send-command \
  --document-name "AWSDisasterRecovery-InstallDRAgentOnInstance" \
  --instance-ids i-XXXXXXXXX \
  --parameters "ReplicationServerRegion=us-west-2" \
  --region us-east-1

# Staging account (with target account ID)
aws ssm send-command \
  --document-name "AWSDisasterRecovery-InstallDRAgentOnInstance" \
  --instance-ids i-XXXXXXXXX \
  --parameters "ReplicationServerRegion=us-west-2,StagingAccountID=111122223333" \
  --region us-east-1
```

## Verification

### Check Source Servers in Target Account

```bash
# In target account (111122223333)
# View all source servers (including extended from staging)
AWS_PAGER="" aws drs describe-source-servers \
  --region us-west-2 \
  --query 'items[].[sourceServerID,arn,tags.Name,lifeCycle.state]' \
  --output table

# Filter by staging account extended source servers
AWS_PAGER="" aws drs describe-source-servers \
  --region us-west-2 \
  --filters '{"stagingAccountIDs": ["444455556666"]}' \
  --query 'items[].[sourceServerID,arn,tags.Name]' \
  --output table
```

### Verify Total Capacity

```bash
# Count source servers in target account (direct)
TARGET_COUNT=$(aws drs describe-source-servers \
  --region us-west-2 \
  --query 'length(items[?!contains(arn, `444455556666`)])' \
  --output text)

# Count extended source servers from staging
STAGING_COUNT=$(aws drs describe-source-servers \
  --region us-west-2 \
  --filters '{"stagingAccountIDs": ["444455556666"]}' \
  --query 'length(items)' \
  --output text)

echo "Target account source servers: $TARGET_COUNT"
echo "Staging account extended source servers: $STAGING_COUNT"
echo "Total capacity: $((TARGET_COUNT + STAGING_COUNT))"
```

## Troubleshooting

### Issue: Extended source servers not visible in target account

**Solution:**
- Verify DRS trusted accounts configured in staging account
- Check staging account agents installed with `StagingAccountID` parameter
- Verify shared KMS key policy allows staging account
- Check DRS service-linked role has permissions

### Issue: Cannot exceed 300 source servers in target account

**Solution:**
- This is expected - 300 is the hard limit per account
- Use staging account for additional 300 via extended source servers
- Verify extended source servers are counted separately

### Issue: Recovery instances fail to launch from staging account source servers

**Solution:**
- Verify shared EBS encryption key accessible
- Check target account has sufficient EC2 capacity
- Verify network configuration (VPC, subnets, security groups)
- Check IAM permissions for cross-account recovery

## Benefits

1. **Capacity Scaling**: 600 total source servers (300 + 300)
2. **Centralized Management**: View all source servers in target account
3. **Unified Recovery**: All instances recover to target account
4. **Cost Optimization**: Single recovery infrastructure
5. **Simplified Operations**: One DRS console for all source servers

## Limitations

1. **Per-Account Limit**: Still 300 source servers per account
2. **Cross-Account Complexity**: Requires KMS key sharing and trusted accounts
3. **Network Requirements**: Cross-account replication requires proper networking
4. **Cost**: Replication costs for cross-account data transfer

## Related Documentation

- [DRS Cross-Account Setup Verification](DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md)
- [DRS Agent Deployment Guide](.kiro/specs/drs-agent-deployer/reference/DRS_AGENT_DEPLOYMENT_GUIDE.md)
- [AWS DRS Extended Source Servers](https://docs.aws.amazon.com/drs/latest/userguide/extended-source-servers.html)
