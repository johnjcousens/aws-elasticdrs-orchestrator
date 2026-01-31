# Standardized Cross-Account Role Migration Guide

## Overview

This guide helps you migrate existing cross-account deployments from custom role names (e.g., `DRSOrchestrationRole-dev`, `DRSOrchestrationRole-test`) to the standardized role name `DRSOrchestrationRole`.

**Migration is optional** - existing accounts with custom role names continue to work without changes. This guide is for teams who want to adopt the standardized naming convention for consistency and simplified management.

## Benefits of Migration

- **Simplified Account Addition**: No need to specify roleArn when adding new accounts
- **Consistent Naming**: Same role name across all environments and accounts
- **Easier Troubleshooting**: Predictable role ARN pattern
- **Reduced Configuration**: Less manual copying of ARNs from CloudFormation outputs

## Migration Strategy

### Option 1: Gradual Migration (Recommended)

Migrate accounts gradually without disrupting existing operations:

1. **New accounts**: Use standardized role name
2. **Existing accounts**: Keep current role names (no changes)
3. **Optional**: Migrate existing accounts one at a time during maintenance windows

### Option 2: Full Migration

Migrate all accounts at once during a planned maintenance window.

## Pre-Migration Checklist

Before starting migration:

- [ ] Review all target and staging accounts
- [ ] Document current role names for each account
- [ ] Identify accounts with active DRS replication
- [ ] Schedule maintenance window (if doing full migration)
- [ ] Backup current account configuration
- [ ] Test migration in dev environment first

## Migration Steps

### Step 1: Deploy New Cross-Account Role

Deploy the standardized role in each target/staging account:

```bash
# Switch to target account
export AWS_PROFILE=target-account

# Deploy standardized role
aws cloudformation deploy \
  --template-file cfn/cross-account-role-stack.yaml \
  --stack-name drs-orchestration-role \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    OrchestrationAccountId=YOUR_ORCHESTRATION_ACCOUNT_ID \
    ExternalId=YOUR_UNIQUE_EXTERNAL_ID
```

**Verify deployment**:
```bash
# Check role exists
AWS_PAGER="" aws iam get-role --role-name DRSOrchestrationRole

# Get role ARN
AWS_PAGER="" aws iam get-role \
  --role-name DRSOrchestrationRole \
  --query 'Role.Arn' \
  --output text
```

### Step 2: Update Account Configuration

Update the account configuration in the orchestration platform:

**Option A: Via API**
```bash
# Update account with new role ARN
curl -X PUT https://api-endpoint/accounts/target/123456789012 \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
  }'
```

**Option B: Via DynamoDB (Direct)**
```bash
# Update DynamoDB item
aws dynamodb update-item \
  --table-name aws-drs-orchestration-target-accounts-dev \
  --key '{"accountId": {"S": "123456789012"}}' \
  --update-expression "SET roleArn = :arn" \
  --expression-attribute-values '{":arn": {"S": "arn:aws:iam::123456789012:role/DRSOrchestrationRole"}}'
```

### Step 3: Test Cross-Account Operations

Verify the new role works correctly:

```bash
# Test role assumption from orchestration account
AWS_PAGER="" aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/DRSOrchestrationRole \
  --role-session-name test-migration \
  --external-id YOUR_UNIQUE_EXTERNAL_ID

# Test DRS query
curl -X GET https://api-endpoint/accounts/target/123456789012/capacity \
  -H "Authorization: Bearer $TOKEN"
```

### Step 4: Delete Old Role (Optional)

After verifying the new role works, optionally delete the old role:

```bash
# List attached policies
AWS_PAGER="" aws iam list-attached-role-policies \
  --role-name DRSOrchestrationRole-dev

# Detach policies
AWS_PAGER="" aws iam detach-role-policy \
  --role-name DRSOrchestrationRole-dev \
  --policy-arn arn:aws:iam::aws:policy/...

# Delete inline policies
AWS_PAGER="" aws iam list-role-policies \
  --role-name DRSOrchestrationRole-dev

AWS_PAGER="" aws iam delete-role-policy \
  --role-name DRSOrchestrationRole-dev \
  --policy-name PolicyName

# Delete role
AWS_PAGER="" aws iam delete-role --role-name DRSOrchestrationRole-dev
```

**Warning**: Only delete the old role after confirming all operations work with the new role.

## Migration Verification

After migration, verify:

- [ ] Can assume new role from orchestration account
- [ ] DRS capacity queries work
- [ ] Can start recovery operations
- [ ] Can query DRS job status
- [ ] All cross-account operations function correctly

**Verification Script**:
```bash
#!/bin/bash
# verify-migration.sh

ACCOUNT_ID="123456789012"
EXTERNAL_ID="YOUR_UNIQUE_EXTERNAL_ID"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/DRSOrchestrationRole"

echo "Testing role assumption..."
aws sts assume-role \
  --role-arn $ROLE_ARN \
  --role-session-name verify-migration \
  --external-id $EXTERNAL_ID \
  --query 'Credentials.AccessKeyId' \
  --output text

if [ $? -eq 0 ]; then
  echo "✓ Role assumption successful"
else
  echo "✗ Role assumption failed"
  exit 1
fi

echo "Testing DRS operations..."
# Add your DRS operation tests here

echo "✓ Migration verification complete"
```

## Rollback Procedure

If issues arise during migration:

### Step 1: Revert Account Configuration

```bash
# Revert to old role ARN
curl -X PUT https://api-endpoint/accounts/target/123456789012 \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole-dev"
  }'
```

### Step 2: Verify Old Role Still Works

```bash
# Test old role
AWS_PAGER="" aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/DRSOrchestrationRole-dev \
  --role-session-name rollback-test \
  --external-id YOUR_UNIQUE_EXTERNAL_ID
```

### Step 3: Keep Both Roles

You can keep both roles deployed if needed:
- Old role: `DRSOrchestrationRole-dev` (for existing operations)
- New role: `DRSOrchestrationRole` (for future use)

## Migration Timeline Example

**Week 1: Planning**
- Review all accounts
- Document current configuration
- Test migration in dev environment

**Week 2: Dev Environment**
- Migrate dev accounts
- Verify all operations work
- Document any issues

**Week 3: Test Environment**
- Migrate test accounts
- Run full test suite
- Verify integration tests pass

**Week 4: Staging Environment**
- Migrate staging accounts
- Run production-like workloads
- Monitor for issues

**Week 5: Production Environment**
- Migrate production accounts during maintenance window
- Monitor closely for 24 hours
- Keep old roles for 1 week before deletion

## Troubleshooting

### Issue: Role Assumption Fails

**Symptoms**:
- Error: "User is not authorized to perform: sts:AssumeRole"

**Solutions**:
1. Verify trust policy includes orchestration account
2. Check external ID matches exactly
3. Ensure orchestration role has `sts:AssumeRole` permission

### Issue: DRS Operations Fail

**Symptoms**:
- Error: "Access Denied" when querying DRS

**Solutions**:
1. Verify new role has all necessary DRS permissions
2. Check role policy includes required actions
3. Compare permissions with old role

### Issue: Account Not Found

**Symptoms**:
- Error: "Account not found in DynamoDB"

**Solutions**:
1. Verify account ID is correct
2. Check DynamoDB table name
3. Ensure account was added successfully

## Best Practices

1. **Test First**: Always test migration in dev environment
2. **One at a Time**: Migrate accounts gradually, not all at once
3. **Keep Old Roles**: Don't delete old roles immediately
4. **Monitor Closely**: Watch for errors after migration
5. **Document Changes**: Keep record of which accounts migrated
6. **Communicate**: Inform team members of migration schedule

## FAQ

**Q: Do I have to migrate existing accounts?**
A: No, migration is optional. Existing accounts continue to work with custom role names.

**Q: Can I mix standardized and custom role names?**
A: Yes, the system supports both. Some accounts can use `DRSOrchestrationRole` while others use custom names.

**Q: What happens if I don't migrate?**
A: Nothing. Your existing accounts continue to work exactly as before.

**Q: Can I migrate back to custom role names?**
A: Yes, simply update the account configuration with the old role ARN.

**Q: Do I need to update Lambda functions?**
A: No, the Lambda functions automatically support both standardized and custom role names.

**Q: Will migration cause downtime?**
A: No, if done correctly. Deploy the new role first, then update configuration. The old role remains functional during migration.

## Support

If you encounter issues during migration:

1. Check [Troubleshooting Guide](../troubleshooting/DEPLOYMENT_TROUBLESHOOTING_GUIDE.md)
2. Review [DRS Cross-Account Reference](../reference/DRS_CROSS_ACCOUNT_REFERENCE.md)
3. Open an issue on GitHub with migration details

## Related Documentation

- [DRS Cross-Account Setup Guide](DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md)
- [DRS Cross-Account Reference](../reference/DRS_CROSS_ACCOUNT_REFERENCE.md)
- [Deployment Guide](../deployment/QUICK_START_GUIDE.md)
