# DRS Cross-Account KMS Setup Guide

## Overview

This guide explains how to set up a Customer Managed Key (CMK) in the staging account that allows the target account to decrypt EBS snapshots created by AWS DRS during cross-account replication.

## Scenario

- **Staging Account**: 444455556666 (creates encrypted EBS snapshots)
- **Target Account**: 111122223333 (needs to decrypt snapshots for recovery)
- **Use Case**: DRS extended source servers with cross-account recovery

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Staging Account (444455556666)                              │
│                                                              │
│  ┌──────────────┐         ┌─────────────────────┐          │
│  │ Source       │         │ CMK for EBS         │          │
│  │ Instances    │─────────│ Encryption          │          │
│  │              │         │ (Customer Managed)  │          │
│  └──────────────┘         └─────────────────────┘          │
│         │                          │                        │
│         │ DRS Replication          │ Key Policy             │
│         │                          │ Grants Access          │
│         ▼                          ▼                        │
│  ┌──────────────────────────────────────────┐              │
│  │ Encrypted EBS Snapshots                  │              │
│  │ (in DRS Staging Area)                    │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ Cross-Account Access
                         │ (via KMS Key Policy)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Target Account (111122223333)                               │
│                                                              │
│  ┌──────────────────────────────────────────┐              │
│  │ DRS Service                              │              │
│  │ - Decrypts snapshots using CMK           │              │
│  │ - Launches recovery instances            │              │
│  └──────────────────────────────────────────┘              │
│                         │                                    │
│                         ▼                                    │
│  ┌──────────────────────────────────────────┐              │
│  │ Recovery Instances                       │              │
│  │ (launched from decrypted snapshots)      │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Required KMS Permissions

The target account needs the following permissions on the staging account's CMK:

| Permission | Purpose |
|------------|---------|
| `kms:DescribeKey` | View key metadata |
| `kms:CreateGrant` | Create grants for AWS services (DRS) |
| `kms:Decrypt` | Decrypt EBS snapshots |
| `kms:ReEncrypt*` | Re-encrypt data with different key |
| `kms:GenerateDataKey*` | Generate data encryption keys |

## Step-by-Step Setup

### Step 1: Create CMK in Staging Account

```bash
# In staging account (444455556666)
# Switch to appropriate region (e.g., us-east-1)

# Create the CMK
aws kms create-key \
  --description "DRS EBS encryption key for cross-account recovery" \
  --key-usage ENCRYPT_DECRYPT \
  --origin AWS_KMS \
  --region us-east-1 \
  --tags TagKey=Purpose,TagValue=DRS-Cross-Account \
  --output json > cmk-output.json

# Extract the key ID
KEY_ID=$(jq -r '.KeyMetadata.KeyId' cmk-output.json)
echo "Created CMK: $KEY_ID"

# Create an alias for easier reference
aws kms create-alias \
  --alias-name alias/drs-cross-account-ebs \
  --target-key-id $KEY_ID \
  --region us-east-1
```

### Step 2: Configure Key Policy for Cross-Account Access

Create a key policy file that grants the target account access:

```bash
# Create key policy file
cat > kms-key-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Id": "drs-cross-account-key-policy",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::444455556666:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow use of the key by target account",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::111122223333:root",
          "arn:aws:iam::111122223333:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery"
        ]
      },
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Allow attachment of persistent resources by target account",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::111122223333:root",
          "arn:aws:iam::111122223333:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery"
        ]
      },
      "Action": [
        "kms:CreateGrant",
        "kms:ListGrants",
        "kms:RevokeGrant"
      ],
      "Resource": "*",
      "Condition": {
        "Bool": {
          "kms:GrantIsForAWSResource": true
        }
      }
    },
    {
      "Sid": "Allow DRS service in staging account to use the key",
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
            "drs.us-east-1.amazonaws.com",
            "ec2.us-east-1.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "Allow DRS service in target account to use the key",
      "Effect": "Allow",
      "Principal": {
        "Service": "drs.amazonaws.com"
      },
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:CreateGrant",
        "kms:GenerateDataKey"
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

# Apply the key policy
aws kms put-key-policy \
  --key-id $KEY_ID \
  --policy-name default \
  --policy file://kms-key-policy.json \
  --region us-east-1
```

### Step 3: Configure DRS to Use the CMK

```bash
# In staging account (444455556666)
# Update DRS replication configuration to use the CMK

aws drs update-replication-configuration-template \
  --region us-east-1 \
  --ebs-encryption CUSTOM \
  --ebs-encryption-key-arn arn:aws:kms:us-east-1:444455556666:key/$KEY_ID \
  --staging-area-subnet-id subnet-XXXXXXXXX \
  --associate-default-security-group \
  --bandwidth-throttling 0 \
  --create-public-ip false \
  --data-plane-routing PRIVATE_IP \
  --default-large-staging-disk-type GP3 \
  --replication-server-instance-type t3.small \
  --use-dedicated-replication-server false
```

### Step 4: Grant Target Account IAM Permissions

In the target account, ensure the DRS service role has permissions to use the CMK:

```bash
# In target account (111122223333)
# Create IAM policy for KMS access

cat > drs-kms-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:CreateGrant",
        "kms:GenerateDataKey*",
        "kms:ReEncrypt*"
      ],
      "Resource": "arn:aws:kms:us-east-1:444455556666:key/*",
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

# Attach policy to DRS service role
aws iam put-role-policy \
  --role-name AWSServiceRoleForElasticDisasterRecovery \
  --policy-name DRSCrossAccountKMSAccess \
  --policy-document file://drs-kms-policy.json
```

### Step 5: Verify Cross-Account Access

```bash
# In target account (111122223333)
# Test that you can describe the key

aws kms describe-key \
  --key-id arn:aws:kms:us-east-1:444455556666:key/$KEY_ID \
  --region us-east-1

# Expected output should show key metadata without errors
```

## CloudFormation Template

For automated deployment, use this CloudFormation template in the staging account:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'DRS Cross-Account CMK for EBS Encryption'

Parameters:
  TargetAccountId:
    Type: String
    Description: Target account ID that needs access to decrypt snapshots
    Default: '111122223333'
  
  TargetRegion:
    Type: String
    Description: Target region where recovery instances will launch
    Default: 'us-west-2'

Resources:
  DRSCrossAccountCMK:
    Type: AWS::KMS::Key
    Properties:
      Description: DRS EBS encryption key for cross-account recovery
      KeyPolicy:
        Version: '2012-10-17'
        Id: drs-cross-account-key-policy
        Statement:
          - Sid: Enable IAM User Permissions
            Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: 'kms:*'
            Resource: '*'
          
          - Sid: Allow use of the key by target account
            Effect: Allow
            Principal:
              AWS:
                - !Sub 'arn:aws:iam::${TargetAccountId}:root'
                - !Sub 'arn:aws:iam::${TargetAccountId}:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery'
            Action:
              - 'kms:Encrypt'
              - 'kms:Decrypt'
              - 'kms:ReEncrypt*'
              - 'kms:GenerateDataKey*'
              - 'kms:DescribeKey'
            Resource: '*'
          
          - Sid: Allow attachment of persistent resources by target account
            Effect: Allow
            Principal:
              AWS:
                - !Sub 'arn:aws:iam::${TargetAccountId}:root'
                - !Sub 'arn:aws:iam::${TargetAccountId}:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery'
            Action:
              - 'kms:CreateGrant'
              - 'kms:ListGrants'
              - 'kms:RevokeGrant'
            Resource: '*'
            Condition:
              Bool:
                'kms:GrantIsForAWSResource': true
          
          - Sid: Allow DRS service in staging account to use the key
            Effect: Allow
            Principal:
              Service: drs.amazonaws.com
            Action:
              - 'kms:Decrypt'
              - 'kms:DescribeKey'
              - 'kms:CreateGrant'
            Resource: '*'
            Condition:
              StringEquals:
                'kms:ViaService':
                  - !Sub 'drs.${AWS::Region}.amazonaws.com'
                  - !Sub 'ec2.${AWS::Region}.amazonaws.com'
          
          - Sid: Allow DRS service in target account to use the key
            Effect: Allow
            Principal:
              Service: drs.amazonaws.com
            Action:
              - 'kms:Decrypt'
              - 'kms:DescribeKey'
              - 'kms:CreateGrant'
              - 'kms:GenerateDataKey'
            Resource: '*'
            Condition:
              StringEquals:
                'kms:ViaService':
                  - !Sub 'drs.${TargetRegion}.amazonaws.com'
                  - !Sub 'ec2.${TargetRegion}.amazonaws.com'
      
      Tags:
        - Key: Purpose
          Value: DRS-Cross-Account
        - Key: TargetAccount
          Value: !Ref TargetAccountId

  DRSCrossAccountCMKAlias:
    Type: AWS::KMS::Alias
    Properties:
      AliasName: alias/drs-cross-account-ebs
      TargetKeyId: !Ref DRSCrossAccountCMK

Outputs:
  CMKKeyId:
    Description: KMS Key ID
    Value: !Ref DRSCrossAccountCMK
    Export:
      Name: !Sub '${AWS::StackName}-CMK-KeyId'
  
  CMKKeyArn:
    Description: KMS Key ARN
    Value: !GetAtt DRSCrossAccountCMK.Arn
    Export:
      Name: !Sub '${AWS::StackName}-CMK-Arn'
  
  CMKAlias:
    Description: KMS Key Alias
    Value: !Ref DRSCrossAccountCMKAlias
    Export:
      Name: !Sub '${AWS::StackName}-CMK-Alias'
```

Deploy the template:

```bash
# In staging account (444455556666)
aws cloudformation deploy \
  --template-file drs-cross-account-cmk.yaml \
  --stack-name drs-cross-account-cmk \
  --parameter-overrides \
    TargetAccountId=111122223333 \
    TargetRegion=us-west-2 \
  --region us-east-1 \
  --capabilities CAPABILITY_IAM

# Get the key ARN
aws cloudformation describe-stacks \
  --stack-name drs-cross-account-cmk \
  --region us-east-1 \
  --query 'Stacks[0].Outputs[?OutputKey==`CMKKeyArn`].OutputValue' \
  --output text
```

## Verification Steps

### 1. Verify Key Policy

```bash
# In staging account (444455556666)
aws kms get-key-policy \
  --key-id alias/drs-cross-account-ebs \
  --policy-name default \
  --region us-east-1 \
  --output json | jq .
```

### 2. Test Cross-Account Access

```bash
# In target account (111122223333)
# Describe the key (should succeed)
aws kms describe-key \
  --key-id arn:aws:kms:us-east-1:444455556666:alias/drs-cross-account-ebs \
  --region us-east-1

# Try to decrypt (will fail without actual ciphertext, but should not give permission error)
aws kms decrypt \
  --key-id arn:aws:kms:us-east-1:444455556666:alias/drs-cross-account-ebs \
  --ciphertext-blob fileb://test-ciphertext.bin \
  --region us-east-1
# Expected: InvalidCiphertextException (not AccessDeniedException)
```

### 3. Verify DRS Configuration

```bash
# In staging account (444455556666)
# Check that DRS is using the CMK
aws drs get-replication-configuration-template \
  --region us-east-1 \
  --query 'ebsEncryptionKeyArn'
```

### 4. Test Agent Installation

```bash
# Install DRS agent on a test instance in staging account
# The agent should successfully create encrypted snapshots

# Check source server status
aws drs describe-source-servers \
  --region us-east-1 \
  --query 'items[].{ID:sourceServerID,State:lifeCycle.state,Encryption:dataReplicationInfo.dataReplicationState}'
```

### 5. Verify Extended Source Servers in Target Account

```bash
# In target account (111122223333)
# Check that extended source servers are visible
aws drs describe-source-servers \
  --region us-west-2 \
  --filters '{"stagingAccountIDs": ["444455556666"]}' \
  --query 'items[].[sourceServerID,arn,lifeCycle.state]' \
  --output table
```

## Troubleshooting

### Issue: AccessDeniedException when target account tries to use key

**Symptoms:**
```
An error occurred (AccessDeniedException) when calling the Decrypt operation: 
User: arn:aws:iam::111122223333:role/... is not authorized to perform: 
kms:Decrypt on resource: arn:aws:kms:us-east-1:444455556666:key/...
```

**Solutions:**
1. Verify key policy includes target account principal
2. Check that `kms:GrantIsForAWSResource` condition is present
3. Ensure DRS service role has KMS permissions
4. Verify `kms:ViaService` condition includes correct regions

### Issue: DRS replication fails with encryption error

**Symptoms:**
```
Replication failed: Unable to encrypt EBS volumes
```

**Solutions:**
1. Verify CMK is in the same region as source instances
2. Check that DRS replication configuration uses correct key ARN
3. Ensure staging account DRS service role has `kms:GenerateDataKey` permission
4. Verify key is enabled (not disabled or pending deletion)

### Issue: Recovery instances fail to launch in target account

**Symptoms:**
```
Recovery failed: Unable to decrypt EBS snapshots
```

**Solutions:**
1. Verify target account DRS service role has `kms:Decrypt` permission
2. Check key policy allows target account access
3. Ensure `kms:ViaService` condition includes target region
4. Verify network connectivity between accounts

### Issue: Key policy too restrictive

**Symptoms:**
```
Key policy does not allow operation
```

**Solutions:**
1. Add `kms:CreateGrant` permission for AWS services
2. Include both account root and DRS service role principals
3. Add `kms:ViaService` condition for both DRS and EC2 services
4. Ensure `kms:GrantIsForAWSResource` condition is set to `true`

## Security Best Practices

1. **Principle of Least Privilege**: Only grant necessary permissions
2. **Use Conditions**: Restrict access with `kms:ViaService` and `kms:GrantIsForAWSResource`
3. **Monitor Key Usage**: Enable CloudTrail logging for KMS operations
4. **Rotate Keys**: Consider key rotation policies
5. **Audit Access**: Regularly review key policy and grants
6. **Tag Keys**: Use tags for cost allocation and access control

## Cost Considerations

- **KMS Key**: $1/month per CMK
- **API Requests**: $0.03 per 10,000 requests
- **Cross-Account Data Transfer**: Standard AWS data transfer rates apply
- **DRS Replication**: Charged per source server per hour

## Related Documentation

- [AWS KMS Key Policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)
- [Share Encrypted EBS Snapshots](https://docs.aws.amazon.com/ebs/latest/userguide/share-kms-key.html)
- [DRS Cross-Account Replication](https://docs.aws.amazon.com/drs/latest/userguide/security-iam-awsmanpol-AWSElasticDisasterRecoveryCrossAccountReplicationPolicy.html)
- [DRS Capacity Scaling Architecture](DRS_CAPACITY_SCALING_ARCHITECTURE.md)

## Summary

This setup enables:
- ✅ Staging account (444455556666) creates encrypted EBS snapshots using CMK
- ✅ Target account (111122223333) can decrypt snapshots for recovery
- ✅ DRS extended source servers work across accounts
- ✅ Secure cross-account access with least privilege
- ✅ 600 total source server capacity (300 + 300)
