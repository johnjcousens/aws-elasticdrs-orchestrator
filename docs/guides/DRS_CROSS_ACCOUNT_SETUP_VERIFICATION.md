# DRS Cross-Account Setup Verification Guide

## Account Configuration

- **Staging Account**: 444455556666 (source instances + DRS replication staging area)
- **Target/Recovery Account**: 111122223333 (where recovery instances launch via shared EBS encryption key)
- **Orchestration Account**: 777788889999 (where Lambda runs)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Staging Account (444455556666)                                  │
│                                                                  │
│  Source Instances → DRS Agents → DRS Staging Area               │
│  (with DR tags)     (installed)   (replication data)            │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                                 │ Recovery Launch
                                 │ (via shared EBS key)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Target Account (111122223333)                                   │
│                                                                  │
│  Recovery Instances (launched from DRS staging data)            │
│  (shared EBS encryption key for cross-account recovery)         │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites Checklist

### ✅ Already Complete (Per User)
- [x] DRS initialized in staging account (444455556666)
- [x] DRS initialized in target account (111122223333)
- [x] Trusted account roles setup in DRS for both accounts
- [x] Shared EBS encryption key configured for cross-account recovery

### 🔍 Need to Verify

#### 1. DRS Service Initialization

**Staging Account (444455556666) - Where source instances live**
```bash
# Switch to staging account
export AWS_PROFILE=staging-account  # or use appropriate credentials

# Verify DRS is initialized
AWS_PAGER="" aws drs describe-source-servers --region us-east-1

# Check replication configuration template
AWS_PAGER="" aws drs get-replication-configuration-template --region us-east-1

# Verify staging area subnet configuration
AWS_PAGER="" aws drs describe-replication-configuration-templates --region us-east-1
```

**Target Account (111122223333) - Where recovery instances launch**
```bash
# Switch to target account
export AWS_PROFILE=target-account

# Verify DRS is initialized (for receiving recovery launches)
AWS_PAGER="" aws drs describe-source-servers --region us-west-2

# Check if account is configured as recovery target
AWS_PAGER="" aws drs get-replication-configuration-template --region us-west-2
```

#### 2. Shared EBS Encryption Key

**Verify KMS key sharing between accounts**
```bash
# In target account (111122223333)
# List KMS keys
AWS_PAGER="" aws kms list-aliases --region us-west-2

# Get key policy for shared EBS key
AWS_PAGER="" aws kms get-key-policy \
  --key-id alias/drs-shared-ebs-key \
  --policy-name default \
  --region us-west-2 \
  --output json | jq .
```

**Expected Key Policy** (should allow staging account to use key):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Allow staging account to use key",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::444455556666:root"
      },
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:CreateGrant"
      ],
      "Resource": "*"
    }
  ]
}
```

#### 2. Cross-Account IAM Roles

**Check if DRSOrchestrationRole exists in Staging Account**
```bash
# In staging account (444455556666)
AWS_PAGER="" aws iam get-role --role-name DRSOrchestrationRole

# Check trust policy
AWS_PAGER="" aws iam get-role --role-name DRSOrchestrationRole \
  --query 'Role.AssumeRolePolicyDocument' --output json | jq .
```

**Expected Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::777788889999:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "drs-orchestration-dev-444455556666"
        }
      }
    }
  ]
}
```

**Check if DRSOrchestrationRole exists in Target Account**
```bash
# In target account (111122223333)
AWS_PAGER="" aws iam get-role --role-name DRSOrchestrationRole-dev

# Check trust policy
AWS_PAGER="" aws iam get-role --role-name DRSOrchestrationRole-dev \
  --query 'Role.AssumeRolePolicyDocument' --output json | jq .
```

#### 3. Test Role Assumption from Orchestration Account

**From Orchestration Account (777788889999)**
```bash
# Test assume role to staging account
AWS_PAGER="" aws sts assume-role \
  --role-arn arn:aws:iam::444455556666:role/DRSOrchestrationRole-dev \
  --role-session-name test-session \
  --external-id drs-orchestration-dev-444455556666

# Test assume role to target account
AWS_PAGER="" aws sts assume-role \
  --role-arn arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev \
  --role-session-name test-session \
  --external-id drs-orchestration-dev-111122223333
```

#### 4. EC2 Instances in Staging Account

**Check for DR-tagged instances**
```bash
# In staging account (444455556666)
AWS_PAGER="" aws ec2 describe-instances \
  --region us-east-1 \
  --filters \
    "Name=tag:dr:enabled,Values=true" \
    "Name=tag:dr:recovery-strategy,Values=drs" \
    "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name]' \
  --output table
```

#### 5. SSM Agent Status

**Check SSM agents are online**
```bash
# In staging account (444455556666)
AWS_PAGER="" aws ssm describe-instance-information \
  --region us-east-1 \
  --query 'InstanceInformationList[].[InstanceId,PingStatus,PlatformType]' \
  --output table
```

#### 6. Instance IAM Profiles

**Verify instances have IAM profile with DRS permissions**
```bash
# Get instance profile for a specific instance
AWS_PAGER="" aws ec2 describe-instances \
  --region us-east-1 \
  --instance-ids i-XXXXXXXXX \
  --query 'Reservations[0].Instances[0].IamInstanceProfile.Arn'

# Check the role attached to the profile
AWS_PAGER="" aws iam get-instance-profile \
  --instance-profile-name YOUR_PROFILE_NAME \
  --query 'InstanceProfile.Roles[0].RoleName'

# Check if role has DRS agent installation policy
AWS_PAGER="" aws iam list-attached-role-policies \
  --role-name YOUR_ROLE_NAME
```

**Required Policy for Instance Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "drs:SendAgentMetricsForDrs",
        "drs:SendAgentLogsForDrs",
        "drs:UpdateAgentSourcePropertiesForDrs",
        "drs:UpdateAgentReplicationInfoForDrs",
        "drs:UpdateAgentConversionInfoForDrs",
        "drs:GetAgentCommandForDrs",
        "drs:GetAgentConfirmedResumeInfoForDrs",
        "drs:GetAgentReplicationInfoForDrs",
        "drs:GetAgentRuntimeConfigurationForDrs",
        "drs:UpdateAgentBacklogForDrs",
        "drs:GetAgentSnapshotCreditsForDrs"
      ],
      "Resource": "*"
    }
  ]
}
```

## Setup Steps (If Missing)

### Step 1: Create DRSOrchestrationRole in Staging Account

```bash
# Create role in staging account (444455556666)
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::777788889999:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "drs-orchestration-dev-111122223333"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name DRSOrchestrationRole-dev \
  --assume-role-policy-document file://trust-policy.json

# Attach permissions policy
cat > permissions-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:DescribeTags"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:SendCommand",
        "ssm:ListCommandInvocations",
        "ssm:GetCommandInvocation",
        "ssm:DescribeInstanceInformation"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "drs:DescribeSourceServers",
        "drs:DescribeJobs",
        "drs:DescribeJobLogItems",
        "drs:StartRecovery"
      ],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name DRSOrchestrationRole \
  --policy-name DRSAgentDeployment \
  --policy-document file://permissions-policy.json
```

### Step 2: Create DRSOrchestrationRole in Target Account

```bash
# Create role in target account (111122223333)
# Use same trust-policy.json

aws iam create-role \
  --role-name DRSOrchestrationRole \
  --assume-role-policy-document file://trust-policy.json

# Attach permissions for recovery operations
cat > target-permissions-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeInstanceStatus",
        "ec2:RunInstances",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "drs:DescribeSourceServers",
        "drs:DescribeJobs",
        "drs:DescribeJobLogItems",
        "drs:DescribeRecoveryInstances"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:CreateGrant"
      ],
      "Resource": "arn:aws:kms:*:111122223333:key/*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "drs.us-west-2.amazonaws.com"
        }
      }
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name DRSOrchestrationRole \
  --policy-name DRSRecoveryOperations \
  --policy-document file://target-permissions-policy.json
```

### Step 3: Configure Shared EBS Encryption Key

```bash
# In target account (111122223333)
# Update KMS key policy to allow staging account

# Get current key policy
aws kms get-key-policy \
  --key-id alias/drs-shared-ebs-key \
  --policy-name default \
  --region us-west-2 > current-key-policy.json

# Edit to add staging account permissions
cat > updated-key-policy.json << 'EOF'
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
        "AWS": "arn:aws:iam::444455556666:root"
      },
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:CreateGrant"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "drs.us-west-2.amazonaws.com"
        }
      }
    }
  ]
}
EOF

# Apply updated policy
aws kms put-key-policy \
  --key-id alias/drs-shared-ebs-key \
  --policy-name default \
  --policy file://updated-key-policy.json \
  --region us-west-2
```

### Step 4: Tag EC2 Instances in Staging Account

```bash
# In staging account (444455556666)
# Tag instances for DR
aws ec2 create-tags \
  --region us-east-1 \
  --resources i-XXXXXXXXX i-YYYYYYYYY \
  --tags \
    Key=dr:enabled,Value=true \
    Key=dr:recovery-strategy,Value=drs \
    Key=dr:wave,Value=wave-1 \
    Key=dr:priority,Value=1 \
    Key=dr:target-account,Value=111122223333
```

### Step 5: Verify SSM Agent

```bash
# If SSM agent not online, install it
# Amazon Linux 2
sudo yum install -y amazon-ssm-agent
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent

# Ubuntu
sudo snap install amazon-ssm-agent --classic
sudo snap start amazon-ssm-agent
```

### Step 6: Configure DRS Replication Settings

```bash
# In staging account (444455556666)
# Configure replication to use target account for recovery

# Update replication configuration template
aws drs update-replication-configuration-template \
  --region us-east-1 \
  --staging-area-subnet-id subnet-XXXXXXXXX \
  --associate-default-security-group \
  --bandwidth-throttling 0 \
  --create-public-ip false \
  --data-plane-routing PRIVATE_IP \
  --default-large-staging-disk-type GP3 \
  --ebs-encryption DEFAULT \
  --replication-server-instance-type t3.small \
  --replication-servers-security-groups-ids sg-XXXXXXXXX \
  --use-dedicated-replication-server false
```

## Test Deployment

### Test Event for Staging-to-Target Recovery

Create `test-staging-to-target-deployment.json`:
```json
{
  "staging_account_id": "444455556666",
  "target_account_id": "111122223333",
  "staging_region": "us-east-1",
  "target_region": "us-west-2",
  "staging_role_arn": "arn:aws:iam::444455556666:role/DRSOrchestrationRole-dev",
  "target_role_arn": "arn:aws:iam::111122223333:role/DRSOrchestrationRole-dev",
  "external_id": "drs-orchestration-dev-444455556666",
  "wait_for_completion": true,
  "timeout_seconds": 600,
  "deployment_pattern": "staging-to-target"
}
```

### Test Lambda Function Locally

```bash
# From orchestration account (777788889999)
cd lambda/drs-agent-deployer

# Test the function
python3 << 'EOF'
import json
from index import lambda_handler

with open('test-staging-to-target-deployment.json') as f:
    event = json.load(f)

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
EOF
```

## Verification Checklist

After setup, verify:

- [ ] DRS initialized in staging account (444455556666)
- [ ] DRS initialized in target account (111122223333)
- [ ] Shared EBS encryption key configured with cross-account access
- [ ] DRSOrchestrationRole exists in staging account
- [ ] DRSOrchestrationRole exists in target account
- [ ] Can assume role from orchestration account to staging account
- [ ] Can assume role from orchestration account to target account
- [ ] EC2 instances in staging account tagged with `dr:enabled=true` and `dr:recovery-strategy=drs`
- [ ] EC2 instances tagged with `dr:target-account=111122223333`
- [ ] SSM agents online on all DR instances in staging account
- [ ] Instance IAM profiles have DRS agent permissions
- [ ] Test deployment completes successfully
- [ ] Source servers appear in staging account DRS console
- [ ] Recovery instances can launch in target account (111122223333)

## Troubleshooting

### Issue: Cannot assume role
**Error**: `An error occurred (AccessDenied) when calling the AssumeRole operation`

**Solution**: 
- Verify trust policy includes orchestration account
- Verify external ID matches
- Check orchestration account has `sts:AssumeRole` permission

### Issue: SSM agent offline
**Error**: `SSM agent not responding`

**Solution**:
- Verify SSM agent installed and running
- Check instance has internet connectivity or VPC endpoints
- Verify instance IAM role has SSM permissions

### Issue: DRS agent installation fails
**Error**: `Failed to install DRS agent`

**Solution**:
- Verify instance IAM role has DRS agent permissions
- Check DRS service is initialized in target account
- Verify network connectivity to DRS endpoints

### Issue: Source servers not appearing in staging account
**Error**: `No source servers found in staging account`

**Solution**:
- Verify DRS agents installed successfully on instances
- Check DRS service is initialized in staging account
- Verify network connectivity to DRS endpoints
- Check instance IAM role has DRS agent permissions

### Issue: Cannot launch recovery instances in target account
**Error**: `Failed to launch recovery instance in target account`

**Solution**:
- Verify shared EBS encryption key policy allows staging account
- Check target account has sufficient EC2 capacity
- Verify DRS trusted accounts configuration
- Check network configuration in target account (VPC, subnets, security groups)

### Issue: KMS key access denied
**Error**: `AccessDenied when using KMS key`

**Solution**:
- Verify KMS key policy includes staging account principal
- Check kms:ViaService condition includes DRS service
- Verify DRS service role has kms:CreateGrant permission

## Next Steps

Once verification is complete:
1. Update Phase 5 tasks in `tasks.md` to mark completed items
2. Proceed with Phase 2 (CloudFormation Integration)
3. Test deployment via Lambda function
4. Integrate with API Gateway and Frontend

## Reference

- [DRS Agent Deployment Guide](.kiro/specs/drs-agent-deployer/reference/DRS_AGENT_DEPLOYMENT_GUIDE.md)
- [DRS Cross-Account Replication](.kiro/specs/drs-agent-deployer/reference/DRS_CROSS_ACCOUNT_REPLICATION.md)
- [AWS DRS Documentation](https://docs.aws.amazon.com/drs/)
