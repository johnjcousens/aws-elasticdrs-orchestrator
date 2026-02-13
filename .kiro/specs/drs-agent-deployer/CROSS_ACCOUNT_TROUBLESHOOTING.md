# Cross-Account DRS Agent Installation Troubleshooting

## Problem

Cross-account DRS agent installations (03/04 instances) are failing because the staging account (891376951562) is missing the required trusted account configuration.

## Root Cause

When using `--account-id` parameter, the DRS agent needs to:
1. Use the EC2 instance profile (✓ Verified: `demo-ec2-profile` with `AWSElasticDisasterRecoveryEc2InstancePolicy`)
2. Assume a role in the target account (❌ Missing: `DRSFailbackRole_160885257264` doesn't exist)

## Solution

Add source account (160885257264) as a "Trusted Account" in the staging account (891376951562).

### Step 1: Add Trusted Account via DRS Console

**In Staging Account (891376951562)**:

1. Navigate to: https://console.aws.amazon.com/drs/home?region=us-east-1#/settings
2. Click on **"Trusted accounts"** tab
3. Click **"Add trusted accounts and create roles"**
4. Enter source account ID: **160885257264**
5. **CRITICAL**: Select **"Failback and in-AWS right-sizing roles"** checkbox
6. Click **"Add"**

This creates the IAM role: `DRSFailbackRole_160885257264`

### Step 2: Verify Role Creation

```bash
# In staging account (891376951562)
aws iam get-role --role-name DRSFailbackRole_160885257264
```

Expected output:
```json
{
    "Role": {
        "RoleName": "DRSFailbackRole_160885257264",
        "Arn": "arn:aws:iam::891376951562:role/service-role/DRSFailbackRole_160885257264",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::160885257264:root"
                },
                "Action": "sts:AssumeRole"
            }]
        }
    }
}
```

### Step 3: Retry Agent Installation

Once the trusted account is configured, retry the cross-account deployments:

```bash
# Retry web-03-04
.kiro/specs/drs-agent-deployer/scripts/deploy-using-ssm-document.sh web-03-04

# Or deploy all 03/04 instances
.kiro/specs/drs-agent-deployer/scripts/deploy-using-ssm-document.sh all-03-04
```

## How It Works

### Authentication Flow

```
Source Instance (160885257264)
    ↓
EC2 Instance Profile (demo-ec2-profile)
    ↓
Assume Role: DRSFailbackRole_160885257264 in staging account
    ↓
DRS Agent registers in Staging Account (891376951562)
    ↓
Replication begins
```

### Why It Failed Before

Without the `DRSFailbackRole_160885257264` role:
- Agent tries to assume role in staging account
- Role doesn't exist
- AssumeRole fails
- Agent installation fails silently

### Why It Will Work After

With the `DRSFailbackRole_160885257264` role:
- Agent uses instance profile credentials
- Successfully assumes role in staging account
- Registers source server in staging account
- Replication begins

## Alternative: CLI Method

If you prefer CLI over console:

```bash
# This is typically done via console, but you can create the role manually
# Note: DRS service creates this automatically when you add trusted account via console

# 1. Create trust policy
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::160885257264:root"
    },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "drs-failback-160885257264"
      }
    }
  }]
}
EOF

# 2. Create role
aws iam create-role \
  --role-name DRSFailbackRole_160885257264 \
  --assume-role-policy-document file://trust-policy.json \
  --path /service-role/

# 3. Attach required policies (DRS service manages these)
# Note: It's better to use the console method as DRS attaches the correct policies automatically
```

**Recommendation**: Use the DRS Console method - it's simpler and ensures correct policy attachments.

## Verification Checklist

Before retrying agent installation:

- [ ] Staging account (891376951562) has DRS initialized
- [ ] Source account (160885257264) added as trusted account
- [ ] "Failback and in-AWS right-sizing roles" checkbox was selected
- [ ] `DRSFailbackRole_160885257264` role exists in staging account
- [ ] Source instances have `demo-ec2-profile` attached (already verified ✓)
- [ ] Instance profile has `AWSElasticDisasterRecoveryEc2InstancePolicy` (already verified ✓)

## Expected Results After Fix

Once trusted account is configured:

**Same-Account (01/02)**:
- ✓ web-01-02: Replicating in account 160885257264
- ✓ app-01-02: Replicating in account 160885257264
- ✓ db-01-02: Replicating in account 160885257264

**Cross-Account (03/04)**:
- ✓ web-03-04: Replicating in account 891376951562
- ✓ app-03-04: Replicating in account 891376951562
- ✓ db-03-04: Replicating in account 891376951562

## References

- [Adding Trusted Accounts](https://docs.aws.amazon.com/drs/latest/userguide/adding-trusted-account.html)
- [DRS Failback Roles](https://docs.aws.amazon.com/drs/latest/userguide/failback-roles.html)
- [Cross-Account Replication](https://docs.aws.amazon.com/drs/latest/userguide/cross-account-replication.html)
