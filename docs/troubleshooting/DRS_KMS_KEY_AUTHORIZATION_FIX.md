# DRS KMS Key Authorization Fix

## Problem

DRS recovery job fails with:
```
Error: An error occurred (AuthFailure) when calling the ModifySnapshotAttribute operation: 
Not authorized to use key arn:aws:kms:us-west-2:ACCOUNT_ID:key/KEY_ID
```

## Root Cause

The KMS key used to encrypt source EBS volumes doesn't grant DRS service permissions to decrypt/use the key during recovery.

## Solution

### Option 1: Update KMS Key Policy (Recommended)

Add this statement to the KMS key policy:

```json
{
  "Sid": "Allow DRS to use the key",
  "Effect": "Allow",
  "Principal": {
    "Service": "drs.amazonaws.com"
  },
  "Action": [
    "kms:Decrypt",
    "kms:DescribeKey",
    "kms:CreateGrant"
  ],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "kms:ViaService": [
        "ec2.us-west-2.amazonaws.com",
        "drs.us-west-2.amazonaws.com"
      ]
    }
  }
}
```

### Option 2: Grant Cross-Account Access (Multi-Account Setup)

If using cross-account DRS, add this statement:

```json
{
  "Sid": "Allow target account to use the key",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::TARGET_ACCOUNT_ID:root"
  },
  "Action": [
    "kms:Decrypt",
    "kms:DescribeKey",
    "kms:CreateGrant",
    "kms:ReEncrypt*"
  ],
  "Resource": "*"
}
```

### Apply the Fix

#### AWS Console
1. Go to **KMS Console** → **Customer managed keys**
2. Find key: `ab256143-c334-4d8b-bd7d-67475d8721d0`
3. Click **Key policy** tab
4. Click **Edit**
5. Add the statement above
6. Click **Save changes**

#### AWS CLI
```bash
# Get current policy
aws kms get-key-policy \
  --key-id ab256143-c334-4d8b-bd7d-67475d8721d0 \
  --policy-name default \
  --region us-west-2 \
  --output text > policy.json

# Edit policy.json to add the statement

# Update policy
aws kms put-key-policy \
  --key-id ab256143-c334-4d8b-bd7d-67475d8721d0 \
  --policy-name default \
  --policy file://policy.json \
  --region us-west-2
```

## Verification

After updating the KMS key policy:

1. **Retry the drill**:
   ```bash
   aws drs start-recovery \
     --source-servers sourceServerId=s-569b0c7877c6b6e29 \
     --is-drill \
     --region us-west-2
   ```

2. **Check job status**:
   ```bash
   aws drs describe-jobs \
     --filters jobIDs=drsjob-525a55ed775968205 \
     --region us-west-2
   ```

## Prevention

To prevent this issue for all future servers:

### 1. Use AWS-Managed Keys
Switch to AWS-managed keys (`aws/ebs`) which automatically grant DRS permissions.

### 2. Update Default EBS Encryption Key Policy
If using customer-managed keys by default, update the key policy template to include DRS permissions.

### 3. Automate Key Policy Updates
Create an EventBridge rule to detect new KMS keys and automatically add DRS permissions:

```python
import boto3

def add_drs_to_kms_key(key_id, region):
    kms = boto3.client('kms', region_name=region)
    
    # Get current policy
    response = kms.get_key_policy(KeyId=key_id, PolicyName='default')
    policy = json.loads(response['Policy'])
    
    # Add DRS statement
    drs_statement = {
        "Sid": "Allow DRS to use the key",
        "Effect": "Allow",
        "Principal": {"Service": "drs.amazonaws.com"},
        "Action": ["kms:Decrypt", "kms:DescribeKey", "kms:CreateGrant"],
        "Resource": "*",
        "Condition": {
            "StringEquals": {
                "kms:ViaService": [
                    f"ec2.{region}.amazonaws.com",
                    f"drs.{region}.amazonaws.com"
                ]
            }
        }
    }
    
    policy['Statement'].append(drs_statement)
    
    # Update policy
    kms.put_key_policy(
        KeyId=key_id,
        PolicyName='default',
        Policy=json.dumps(policy)
    )
```

## Related Issues

- **Issue**: Snapshot sharing fails
- **Issue**: Recovery instance launch fails with encryption errors
- **Issue**: Cross-region replication fails

All have the same root cause: KMS key permissions.

## References

- [AWS DRS Prerequisites](https://docs.aws.amazon.com/drs/latest/userguide/getting-started-prerequisites.html)
- [KMS Key Policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)
- [DRS IAM Permissions](https://docs.aws.amazon.com/drs/latest/userguide/security-iam.html)
