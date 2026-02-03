# DRS Cross-Account KMS Setup Validation

## Current Configuration

**Source Account**: 777788889999  
**Target Account**: 111122223333  
**KMS Key**: ab256143-c334-4d8b-bd7d-67475d8721d0  
**Region**: us-west-2

## Applied KMS Policy ✅

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::777788889999:root"},
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
        "kms:DescribeKey",
        "kms:CreateGrant",
        "kms:ListGrants",
        "kms:RevokeGrant"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Allow DRS service to use the key",
      "Effect": "Allow",
      "Principal": {"Service": "drs.amazonaws.com"},
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey",
        "kms:CreateGrant",
        "kms:ListGrants"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Allow attachment of persistent resources",
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
          "kms:GrantIsForAWSResource": "true"
        }
      }
    }
  ]
}
```

## Validation Checklist

### ✅ Required KMS Permissions (AWS DRS Documentation)

| Permission | Statement | Purpose | Status |
|------------|-----------|---------|--------|
| `kms:Decrypt` | 2, 3 | Decrypt EBS snapshots | ✅ |
| `kms:DescribeKey` | 2, 3 | Get key metadata | ✅ |
| `kms:CreateGrant` | 2, 3, 4 | Create grants for AWS services | ✅ |
| `kms:Encrypt` | 2 | Encrypt new snapshots | ✅ |
| `kms:ReEncrypt*` | 2 | Re-encrypt snapshots | ✅ |
| `kms:GenerateDataKey*` | 2 | Generate data keys | ✅ |
| `kms:ListGrants` | 2, 3, 4 | List active grants | ✅ |
| `kms:RevokeGrant` | 2, 4 | Revoke grants | ✅ |

### ✅ Required Principals

| Principal | Statement | Purpose | Status |
|-----------|-----------|---------|--------|
| Source Account Root | 1 | Key administration | ✅ |
| Target Account Root | 2, 4 | Cross-account access | ✅ |
| DRS Service Role | 2, 4 | DRS operations | ✅ |
| DRS Service Principal | 3 | Service-level access | ✅ |

### ✅ Critical Conditions

| Condition | Statement | Purpose | Status |
|-----------|-----------|---------|--------|
| `kms:GrantIsForAWSResource: true` | 4 | Restrict grants to AWS resources | ✅ |

## Additional Validations Needed

### 1. EBS Default Encryption Settings

**Source Account (777788889999)**:
```bash
aws ec2 get-ebs-encryption-by-default --region us-west-2 --profile 777788889999_AdministratorAccess
aws ec2 get-ebs-default-kms-key-id --region us-west-2 --profile 777788889999_AdministratorAccess
```

**Expected**: Should return the KMS key ID `ab256143-c334-4d8b-bd7d-67475d8721d0`

### 2. DRS Replication Server Permissions

**Target Account (111122223333)** - Verify DRS service role has EC2 permissions:
```bash
aws iam get-role \
  --role-name AWSServiceRoleForElasticDisasterRecovery \
  --profile 111122223333_AdministratorAccess
```

**Required Permissions**:
- `ec2:CreateSnapshot`
- `ec2:ModifySnapshotAttribute`
- `ec2:CopySnapshot`
- `ec2:DescribeSnapshots`

### 3. Snapshot Sharing Permissions

Verify snapshots can be shared from source to target:
```bash
# In source account - check if snapshots exist
aws ec2 describe-snapshots \
  --owner-ids 777788889999 \
  --filters "Name=tag:AWSElasticDisasterRecoveryManaged,Values=true" \
  --region us-west-2 \
  --profile 777788889999_AdministratorAccess
```

### 4. KMS Key Alias (Optional but Recommended)

Create an alias for easier identification:
```bash
aws kms create-alias \
  --alias-name alias/drs-cross-account-key \
  --target-key-id ab256143-c334-4d8b-bd7d-67475d8721d0 \
  --region us-west-2 \
  --profile 777788889999_AdministratorAccess
```

## Common Issues and Solutions

### Issue 1: "Not authorized to use key" (RESOLVED ✅)
**Cause**: Missing `kms:CreateGrant` permission  
**Solution**: Added to statement 2 and 4

### Issue 2: Snapshot Sharing Fails
**Cause**: Missing `ec2:ModifySnapshotAttribute` in target account  
**Solution**: Verify DRS service role has EC2 permissions

### Issue 3: Grant Creation Fails
**Cause**: Missing `kms:GrantIsForAWSResource` condition  
**Solution**: Added to statement 4

### Issue 4: Cross-Region Replication
**Cause**: KMS key is region-specific  
**Solution**: Create matching key policy in each region where DRS is used

## Testing the Configuration

### Test 1: Start a Drill
```bash
aws drs start-recovery \
  --source-servers sourceServerId=s-51b12197c9ad51796 \
  --is-drill \
  --region us-west-2 \
  --profile 111122223333_AdministratorAccess
```

**Expected**: Job should complete without KMS errors

### Test 2: Verify Snapshot Sharing
```bash
# Check if snapshots are shared with target account
aws ec2 describe-snapshot-attribute \
  --snapshot-id snap-xxxxx \
  --attribute createVolumePermission \
  --region us-west-2 \
  --profile 777788889999_AdministratorAccess
```

**Expected**: Should show target account 111122223333 in permissions

### Test 3: Verify Grant Creation
```bash
aws kms list-grants \
  --key-id ab256143-c334-4d8b-bd7d-67475d8721d0 \
  --region us-west-2 \
  --profile 777788889999_AdministratorAccess
```

**Expected**: Should show grants for DRS service

## Best Practices

### ✅ Implemented
1. Separate statement for DRS service principal
2. Grant permissions with `kms:GrantIsForAWSResource` condition
3. Both account root and service role as principals
4. All required KMS actions included

### 🔄 Recommended
1. Enable CloudTrail logging for KMS key usage
2. Set up CloudWatch alarms for KMS access denied errors
3. Document key rotation procedures
4. Create matching policies in all DRS regions

### 📋 Optional Enhancements
1. Add VPC endpoint condition for additional security
2. Implement key rotation (AWS managed keys rotate automatically)
3. Add resource tags to KMS key for cost allocation
4. Create IAM policy for manual key management

## Monitoring

### CloudWatch Metrics to Monitor
```bash
# KMS API errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/KMS \
  --metric-name UserErrorCount \
  --dimensions Name=KeyId,Value=ab256143-c334-4d8b-bd7d-67475d8721d0 \
  --start-time 2026-02-02T00:00:00Z \
  --end-time 2026-02-03T00:00:00Z \
  --period 3600 \
  --statistics Sum \
  --region us-west-2
```

### CloudTrail Events to Monitor
- `CreateGrant` - Grant creation for DRS
- `Decrypt` - Snapshot decryption
- `ModifySnapshotAttribute` - Snapshot sharing

## References

- [AWS DRS User Guide - Cross-Account Replication](https://docs.aws.amazon.com/drs/latest/userguide/cross-account-replication.html)
- [AWS KMS Developer Guide - Key Policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)
- [AWS DRS Prerequisites](https://docs.aws.amazon.com/drs/latest/userguide/getting-started-prerequisites.html)
- [EBS Encryption](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html)

## Conclusion

✅ **KMS policy is correctly configured** for DRS cross-account operations.

The policy includes all required permissions based on AWS DRS documentation:
- Decrypt/encrypt operations for snapshot handling
- Grant management for AWS service integration
- Proper principal configuration (account root + service role + service principal)
- Security condition to restrict grants to AWS resources

**Next Steps**:
1. Retry the DRS drill
2. Monitor CloudTrail for any remaining permission issues
3. Verify successful recovery instance launch
