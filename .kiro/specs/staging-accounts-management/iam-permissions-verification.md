# IAM Permissions Verification for Staging Accounts Management

## Summary

All required IAM permissions for staging accounts management are already configured in the CloudFormation templates. No additional changes are needed.

## Verified Permissions

### 1. STS AssumeRole Permission

**Location:** `cfn/master-template.yaml` (Lines 328-338)

```yaml
# STS AssumeRole for cross-account DRS operations
# Assumes roles in workload accounts for multi-account recovery
- PolicyName: STSAccess
  PolicyDocument:
    Version: "2012-10-17"
    Statement:
      - Effect: Allow
        Action:
          - sts:AssumeRole
        Resource:
          - !Sub "arn:${AWS::Partition}:iam::*:role/DRSOrchestrationRole-*"
```

**Purpose:** Allows Lambda functions to assume roles in staging accounts for cross-account DRS operations.

**Scope:** Restricted to roles matching the pattern `DRSOrchestrationRole-*` in any AWS account.

### 2. DRS DescribeSourceServers Permission

**Location:** `cfn/master-template.yaml` (Lines 178-192)

```yaml
- Effect: Allow
  Action:
    - drs:DescribeSourceServers
    - drs:DescribeRecoverySnapshots
    - drs:DescribeRecoveryInstances
    - drs:DescribeJobs
    - drs:DescribeJobLogItems
    - drs:GetLaunchConfiguration
    - drs:GetReplicationConfiguration
    - drs:GetFailbackReplicationConfiguration
    - drs:DescribeLaunchConfigurationTemplates
    - drs:DescribeReplicationConfigurationTemplates
    - drs:ListLaunchActions
    - drs:ListTagsForResource
  Resource: "*"
```

**Purpose:** Allows Lambda functions to query DRS capacity and server information in both target and staging accounts.

**Scope:** All DRS resources (required for cross-account queries after assuming role).

### 3. Cross-Account Role Trust Policy

**Location:** `cfn/cross-account-role-stack.yaml` (Lines 54-63)

```yaml
AssumeRolePolicyDocument:
  Version: '2012-10-17'
  Statement:
    - Effect: Allow
      Principal:
        AWS: !Sub 'arn:${AWS::Partition}:iam::${OrchestrationAccountId}:root'
      Action: 'sts:AssumeRole'
      Condition:
        StringEquals:
          sts:ExternalId: !Ref ExternalId
```

**Purpose:** Allows the orchestration account to assume roles in staging accounts with external ID validation.

**Security:** Uses external ID to prevent confused deputy attacks.

## Workflow Verification

### Staging Account Validation Flow

1. **Query Lambda** receives validation request with staging account details
2. **STS AssumeRole** is called using the staging account's role ARN and external ID
3. **DRS DescribeSourceServers** is called in the staging account to verify:
   - DRS is initialized
   - Current server counts
   - Replication status
4. **Validation results** are returned to the frontend

### Combined Capacity Query Flow

1. **Query Lambda** retrieves target account configuration from DynamoDB
2. **For each account** (target + staging accounts):
   - **STS AssumeRole** is called to get temporary credentials
   - **DRS DescribeSourceServers** is called in all DRS-enabled regions
   - **Results are aggregated** for the account
3. **Combined metrics** are calculated across all accessible accounts
4. **Capacity data** is returned to the frontend

## Security Considerations

### Least Privilege

- STS AssumeRole is restricted to roles matching `DRSOrchestrationRole-*` pattern
- DRS permissions are read-only (Describe/Get/List operations only)
- No write permissions to DRS resources
- External ID required for cross-account role assumption

### Audit Trail

- All STS AssumeRole calls are logged in CloudTrail
- All DRS API calls are logged in CloudTrail
- Lambda execution logs capture all cross-account operations

### Error Handling

- Role assumption failures are caught and reported gracefully
- Failed staging accounts don't block queries to other accounts
- Detailed error messages help diagnose permission issues

## Conclusion

✅ **All required IAM permissions are in place**

The existing CloudFormation templates already include:
- STS AssumeRole for cross-account access
- DRS DescribeSourceServers for capacity queries
- Proper trust policies for cross-account roles
- Security best practices (external ID, least privilege)

**No CloudFormation template changes are required for Task 19.**

## Related Files

- `cfn/master-template.yaml` - Main orchestration role with STS and DRS permissions
- `cfn/cross-account-role-stack.yaml` - Cross-account role template for staging accounts
- `lambda/query-handler/index.py` - Query Lambda that uses these permissions
- `lambda/data-management-handler/index.py` - Data management Lambda for staging account CRUD

## Testing Recommendations

1. **Unit Tests:** Verify STS AssumeRole and DRS API calls in Lambda handlers (✅ Already implemented)
2. **Integration Tests:** Test cross-account role assumption with real AWS accounts
3. **Security Tests:** Verify external ID validation prevents unauthorized access
4. **Error Tests:** Verify graceful handling of permission denied errors

## Deployment Notes

When deploying to the `test` environment:

```bash
./scripts/deploy.sh test
```

The deployment will:
1. Update Lambda functions with staging account management code
2. Maintain existing IAM permissions (no changes needed)
3. Deploy API Gateway endpoints for staging account operations
4. Update frontend with new UI components

**No manual IAM permission updates are required.**
