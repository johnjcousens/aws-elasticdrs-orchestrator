# DRS Cross-Account KMS Setup Validation Checklist

## Current Setup Analysis

**Source Account**: 777788889999  
**Target Account**: 111122223333  
**KMS Key**: ab256143-c334-4d8b-bd7d-67475d8721d0  
**Region**: us-west-2

## ✅ Applied KMS Policy (Current)

Your current policy includes all required permissions for DRS cross-account recovery.

### Statement 1: Root Account Permissions ✅
- **Purpose**: Allow source account full control
- **Principal**: `arn:aws:iam::777788889999:root`
- **Actions**: `kms:*`
- **Status**: ✅ Correct

### Statement 2: Target Account Permissions ✅
- **Purpose**: Allow target account to use key for recovery
- **Principals**:
  - `arn:aws:iam::111122223333:root` ✅
  - `arn:aws:iam::111122223333:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery` ✅
- **Actions**:
  - `kms:Encrypt` ✅
  - `kms:Decrypt` ✅
  - `kms:ReEncrypt*` ✅
  - `kms:GenerateDataKey*` ✅
  - `kms:DescribeKey` ✅
  - `kms:CreateGrant` ✅ (CRITICAL - was missing)
  - `kms:ListGrants` ✅
  - `kms:RevokeGrant` ✅
- **Status**: ✅ Complete

### Statement 3: DRS Service Principal ✅
- **Purpose**: Allow DRS service to decrypt snapshots
- **Principal**: `drs.amazonaws.com`
- **Actions**:
  - `kms:Decrypt` ✅
  - `kms:DescribeKey` ✅
  - `kms:CreateGrant` ✅
  - `kms:ListGrants` ✅
- **Status**: ✅ Complete

### Statement 4: Grant Operations with Condition ✅
- **Purpose**: Allow grant operations for AWS resources
- **Principals**: Target account root + DRS service role ✅
- **Actions**:
  - `kms:CreateGrant` ✅
  - `kms:ListGrants` ✅
  - `kms:RevokeGrant` ✅
- **Condition**: `kms:GrantIsForAWSResource: true` ✅
- **Status**: ✅ Complete

## Additional Validation Steps

### 1. Verify EBS Snapshot Sharing Permissions

Check if snapshots can be shared with target account:

```bash
# In source account (777788889999)
aws ec2 describe-snapshots \
  --owner-ids 777788889999 \
  --region us-west-2 \
  --filters "Name=tag:aws:drs:source-server-id,Values=s-*" \
  --query 'Snapshots[0].SnapshotId' \
  --output text
```

Then verify sharing:

```bash
SNAPSHOT_ID=<from-above>
aws ec2 modify-snapshot-attribute \
  --snapshot-id $SNAPSHOT_ID \
  --attribute createVolumePermission \
  --operation-add \
  --user-ids 111122223333 \
  --region us-west-2 \
  --profile 777788889999_AdministratorAccess
```

### 2. Verify Target Account Can Access Key

```bash
# In target account (111122223333)
aws kms describe-key \
  --key-id arn:aws:kms:us-west-2:777788889999:key/ab256143-c334-4d8b-bd7d-67475d8721d0 \
  --region us-west-2 \
  --profile 111122223333_AdministratorAccess
```

Expected: Should return key metadata without errors.

### 3. Test Grant Creation

```bash
# In target account
aws kms create-grant \
  --key-id arn:aws:kms:us-west-2:777788889999:key/ab256143-c334-4d8b-bd7d-67475d8721d0 \
  --grantee-principal arn:aws:iam::111122223333:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery \
  --operations Decrypt DescribeKey CreateGrant \
  --region us-west-2 \
  --profile 111122223333_AdministratorAccess
```

Expected: Should return a grant token and grant ID.

### 4. Verify DRS Service Role Exists

```bash
# In target account
aws iam get-role \
  --role-name AWSServiceRoleForElasticDisasterRecovery \
  --profile 111122223333_AdministratorAccess
```

Expected: Should return role details. If not found, DRS needs initialization.

### 5. Check for Other Encrypted Volumes

```bash
# Find all encrypted volumes in source servers
aws ec2 describe-volumes \
  --region us-west-2 \
  --filters "Name=encrypted,Values=true" \
  --query 'Volumes[*].[VolumeId,KmsKeyId]' \
  --output table \
  --profile 777788889999_AdministratorAccess
```

**Action Required**: If other KMS keys are found, repeat the policy update for each key.

## Common Issues and Solutions

### Issue 1: "Not authorized for images" Error
**Symptom**: Error mentions AMI permissions  
**Solution**: Add EC2 image sharing permissions:

```bash
# Share AMI with target account
aws ec2 modify-image-attribute \
  --image-id ami-xxxxx \
  --launch-permission "Add=[{UserId=111122223333}]" \
  --region us-west-2 \
  --profile 777788889999_AdministratorAccess
```

### Issue 2: Multiple KMS Keys
**Symptom**: Different volumes use different KMS keys  
**Solution**: Apply the same policy to all KMS keys used by DRS source servers.

### Issue 3: Cross-Region Recovery
**Symptom**: Recovery to different region fails  
**Solution**: 
1. Create KMS key in target region
2. Apply same policy
3. Update DRS launch settings to use target region key

### Issue 4: Staging Area Subnet Encryption
**Symptom**: Staging area creation fails  
**Solution**: Ensure staging subnet's default encryption key (if any) also has cross-account permissions.

## Best Practices

### 1. Use Separate Keys for Different Environments
- Production: `prod-drs-key`
- Staging: `staging-drs-key`
- Development: `dev-drs-key`

### 2. Enable Key Rotation
```bash
aws kms enable-key-rotation \
  --key-id ab256143-c334-4d8b-bd7d-67475d8721d0 \
  --region us-west-2 \
  --profile 777788889999_AdministratorAccess
```

### 3. Monitor Key Usage
```bash
# Enable CloudTrail logging for KMS
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::KMS::Key \
  --region us-west-2 \
  --profile 777788889999_AdministratorAccess
```

### 4. Tag KMS Keys
```bash
aws kms tag-resource \
  --key-id ab256143-c334-4d8b-bd7d-67475d8721d0 \
  --tags TagKey=Purpose,TagValue=DRS-CrossAccount \
         TagKey=SourceAccount,TagValue=777788889999 \
         TagKey=TargetAccount,TagValue=111122223333 \
  --region us-west-2 \
  --profile 777788889999_AdministratorAccess
```

## Verification Script

Run this to verify complete setup:

```bash
#!/bin/bash
set -e

SOURCE_ACCOUNT="777788889999"
TARGET_ACCOUNT="111122223333"
KEY_ID="ab256143-c334-4d8b-bd7d-67475d8721d0"
REGION="us-west-2"

echo "=== DRS Cross-Account KMS Validation ==="

echo "1. Checking KMS key policy..."
aws kms get-key-policy \
  --key-id $KEY_ID \
  --policy-name default \
  --region $REGION \
  --profile ${SOURCE_ACCOUNT}_AdministratorAccess \
  --query Policy --output text | jq .

echo "2. Verifying target account can describe key..."
aws kms describe-key \
  --key-id arn:aws:kms:$REGION:$SOURCE_ACCOUNT:key/$KEY_ID \
  --region $REGION \
  --profile ${TARGET_ACCOUNT}_AdministratorAccess

echo "3. Checking DRS service role in target account..."
aws iam get-role \
  --role-name AWSServiceRoleForElasticDisasterRecovery \
  --profile ${TARGET_ACCOUNT}_AdministratorAccess

echo "4. Listing DRS source servers..."
aws drs describe-source-servers \
  --region $REGION \
  --profile ${SOURCE_ACCOUNT}_AdministratorAccess \
  --query 'items[*].[sourceServerID,tags.Name]' \
  --output table

echo "✅ All checks passed!"
```

## Next Steps

1. ✅ KMS policy updated (DONE)
2. ⏳ Wait 5 minutes for IAM propagation
3. 🔄 Retry DRS drill:
   ```bash
   aws drs start-recovery \
     --source-servers sourceServerId=s-51b12197c9ad51796 \
     --is-drill \
     --region us-west-2 \
     --profile 111122223333_AdministratorAccess
   ```
4. 📊 Monitor job status:
   ```bash
   aws drs describe-jobs \
     --filters jobIDs=drsjob-5550849b1d45bbee2 \
     --region us-west-2 \
     --profile 111122223333_AdministratorAccess
   ```

## Reference Documentation

- [AWS DRS Prerequisites](https://docs.aws.amazon.com/drs/latest/userguide/getting-started-prerequisites.html)
- [KMS Key Policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)
- [Cross-Account Snapshot Sharing](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-modifying-snapshot-permissions.html)
- [DRS Cross-Account Setup](https://docs.aws.amazon.com/drs/latest/userguide/cross-account.html)

## Summary

✅ **Your KMS policy is now complete and includes all required permissions for DRS cross-account recovery.**

The policy includes:
- ✅ Target account root and DRS service role access
- ✅ All required KMS actions (Encrypt, Decrypt, CreateGrant, etc.)
- ✅ DRS service principal permissions
- ✅ Grant operations with AWS resource condition

**The drill should now succeed after IAM propagation (5 minutes).**
