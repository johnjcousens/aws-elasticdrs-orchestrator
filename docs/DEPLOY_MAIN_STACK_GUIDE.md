# Main Stack Deployment Guide

## Overview

The `deploy-main-stack.sh` script deploys the new nested stack architecture using `main-stack.yaml`. This architecture organizes CloudFormation templates into service-based directories (IAM, Lambda, DynamoDB, etc.) and supports both unified and function-specific IAM roles through the `UseFunctionSpecificRoles` parameter.

This is an alternative deployment method to the existing `deploy.sh` script which continues to work with `master-template.yaml` for production environments.

## Key Differences from deploy.sh

| Feature | deploy.sh | deploy-main-stack.sh |
|---------|-----------|---------------------|
| **Template** | master-template.yaml | main-stack.yaml |
| **Architecture** | Monolithic template | Nested stacks by service |
| **IAM Roles** | Unified role only | Supports function-specific roles |
| **Template Sync** | Single template | All nested stack directories |
| **Validation** | Template validation | Template + S3 URL validation |
| **Organization** | Flat structure | Service-based folders |

## When to Use Each Script

### Use `deploy.sh` (existing - master-template.yaml)
- **Production deployments** - Proven, stable architecture
- **Existing stacks** - Stacks already using master-template.yaml
- **Quick updates** - Lambda-only or frontend-only deployments
- **Unified role only** - When function-specific roles are not needed

### Use `deploy-main-stack.sh` (new - main-stack.yaml)
- **QA environment** - Integration testing with new architecture
- **Function-specific IAM roles** - Testing least privilege security model
- **Development environments** - Testing nested stack architecture
- **Modular infrastructure** - When you need service-based organization

### Recommended Strategy

1. **Production**: Continue using `deploy.sh` with `master-template.yaml`
2. **QA**: Use `deploy-main-stack.sh` with `--use-function-specific-roles` for integration testing
3. **Development**: Use either script based on testing needs
4. **Migration**: Test thoroughly in QA before migrating production to main-stack.yaml

## Usage

### Basic Deployment
```bash
./scripts/deploy-main-stack.sh test
```

### Enable Function-Specific IAM Roles
```bash
./scripts/deploy-main-stack.sh test --use-function-specific-roles
```

### Validation Only (No Deployment)
```bash
./scripts/deploy-main-stack.sh test --validate-only
```

### Full Test Suite
```bash
./scripts/deploy-main-stack.sh test --full-tests
```

## Command-Line Options

- `--use-function-specific-roles` - Enable function-specific IAM roles (default: false)
- `--validate-only` - Run validation and tests without deploying
- `--full-tests` - Run all tests including property-based tests
- `--skip-tests` - Skip all tests (emergency deployment only)
- `--force` - Force deployment even if stack is updating
- `--no-frontend` - Skip frontend deployment (API-only)
- `--orchestration-role <ARN>` - Use external orchestration role

## Environment Variables

All environment variables from `deploy.sh` are supported:

- `PROJECT_NAME` - Project name (default: aws-drs-orchestration)
- `STACK_NAME` - CloudFormation stack name
- `DEPLOYMENT_BUCKET` - S3 bucket for artifacts
- `ADMIN_EMAIL` - Admin email for Cognito
- `ENABLE_NOTIFICATIONS` - Enable email notifications (default: true)
- `USE_FUNCTION_SPECIFIC_ROLES` - Use function-specific roles (default: false)

## Deployment Process

The script follows the same 5-stage pipeline as `deploy.sh`:

1. **Validation** - cfn-lint, flake8, black, TypeScript
2. **Security** - bandit, cfn_nag, detect-secrets, npm audit, etc.
3. **Tests** - pytest, vitest
4. **Git Push** - Push to origin
5. **Deploy** - Sync templates, validate, deploy CloudFormation

### Additional Steps for Nested Stacks

The deployment stage includes extra steps:

1. Create deployment bucket with account ID for uniqueness
2. Sync all nested stack template directories to S3:
   - `/cfn/iam/` - IAM roles
   - `/cfn/lambda/` - Lambda functions
   - `/cfn/dynamodb/` - DynamoDB tables
   - `/cfn/stepfunctions/` - Step Functions state machine
   - `/cfn/sns/` - SNS topics
   - `/cfn/eventbridge/` - EventBridge rules
   - `/cfn/s3/` - S3 buckets
   - `/cfn/cloudfront/` - CloudFront distribution
   - `/cfn/apigateway/` - API Gateway (7 nested stacks)
   - `/cfn/cognito/` - Cognito user pool
   - `/cfn/monitoring/` - CloudWatch alarms
   - `/cfn/waf/` - WAF web ACL
3. Validate all nested stack templates exist in S3
4. Deploy main-stack.yaml with nested stack references

## S3 Bucket Naming

The deployment bucket uses account ID for global uniqueness:

```
${PROJECT_NAME}-${AWS_ACCOUNT_ID}-${ENVIRONMENT}
```

Example: `aws-drs-orchestration-438465159935-test`

This prevents bucket name conflicts across AWS accounts.

## Nested Stack Template Validation

Before deployment, the script validates that all required nested stack templates exist in S3:

```bash
cfn/iam/roles-stack.yaml
cfn/lambda/functions-stack.yaml
cfn/dynamodb/tables-stack.yaml
cfn/stepfunctions/statemachine-stack.yaml
cfn/sns/topics-stack.yaml
cfn/eventbridge/rules-stack.yaml
cfn/s3/buckets-stack.yaml
cfn/cloudfront/distribution-stack.yaml
cfn/cognito/auth-stack.yaml
cfn/monitoring/alarms-stack.yaml
cfn/waf/webacl-stack.yaml
```

If any template is missing, deployment fails with an error.

## Function-Specific IAM Roles

### Overview

The `UseFunctionSpecificRoles` parameter controls the IAM architecture:

- **`false` (default)**: Uses single unified IAM role shared across all Lambda functions
- **`true`**: Creates 5 dedicated IAM roles, each with minimum required permissions

### Enabling Function-Specific Roles

```bash
# Deploy with function-specific roles
./scripts/deploy-main-stack.sh test --use-function-specific-roles

# Or set environment variable
export USE_FUNCTION_SPECIFIC_ROLES=true
./scripts/deploy-main-stack.sh test
```

### IAM Role Architecture

When `UseFunctionSpecificRoles=true`, the following roles are created:

1. **Query Handler Role** (`{ProjectName}-query-handler-role-{Environment}`)
   - DynamoDB: Read-only (GetItem, Query, Scan, BatchGetItem)
   - DRS: Describe operations only
   - EC2: Describe operations only
   - CloudWatch: Read metrics
   - Lambda: Invoke execution-handler only
   - STS: AssumeRole with ExternalId validation

2. **Data Management Role** (`{ProjectName}-data-management-role-{Environment}`)
   - DynamoDB: Full CRUD operations
   - DRS: Describe operations + tagging (TagResource, UntagResource, CreateExtendedSourceServer)
   - Lambda: Self-invocation for async tag sync
   - EventBridge: Rule management for tag sync schedule
   - STS: AssumeRole with ExternalId validation

3. **Execution Handler Role** (`{ProjectName}-execution-handler-role-{Environment}`)
   - Step Functions: Full orchestration (StartExecution, DescribeExecution, SendTask*)
   - SNS: Full notification operations
   - DynamoDB: Full CRUD operations
   - DRS: Describe + recovery operations (StartRecovery, TerminateRecoveryInstances)
   - EC2: Instance management (DescribeInstances, TerminateInstances, CreateTags)
   - Lambda: Invoke data-management-handler
   - STS: AssumeRole with ExternalId validation

4. **Orchestration Role** (`{ProjectName}-orchestration-role-{Environment}`)
   - DRS: Comprehensive read and write operations
   - EC2: Full instance and resource management
   - IAM: PassRole (restricted to drs.amazonaws.com and ec2.amazonaws.com)
   - KMS: DescribeKey, CreateGrant (restricted to EC2 and DRS services)
   - SSM: CreateOpsItem, SendCommand, GetParameter
   - SNS: Publish notifications
   - DynamoDB: Read and write operations
   - Lambda: Invoke execution-handler and query-handler
   - STS: AssumeRole with ExternalId validation

5. **Frontend Deployer Role** (`{ProjectName}-frontend-deployer-role-{Environment}`)
   - S3: Full operations on frontend buckets (including versioned bucket cleanup)
   - CloudFront: Invalidation and distribution management
   - CloudFormation: DescribeStacks for stack status checks
   - CloudWatch: Metric publishing

### Security Benefits

Function-specific roles provide:

- **Reduced blast radius**: Compromised query function cannot execute recovery operations
- **Least privilege**: Each function has only the permissions it needs
- **Audit clarity**: CloudTrail logs clearly show which function performed which action
- **Compliance**: Meets AWS Well-Architected Framework security best practices

### When to Use Each Architecture

**Use Unified Role (`UseFunctionSpecificRoles=false`) when:**
- Simplicity is preferred over granular security
- All Lambda functions are equally trusted
- Rapid development without permission management overhead
- Backward compatibility with existing deployments

**Use Function-Specific Roles (`UseFunctionSpecificRoles=true`) when:**
- Security and compliance require least privilege
- Different functions have different trust levels
- Audit requirements need clear action attribution
- Production environments with strict security controls

## Examples

### Development Workflow
```bash
# Make changes
vim cfn/iam/roles-stack.yaml

# Validate changes
./scripts/deploy-main-stack.sh test --validate-only

# Deploy to test environment
./scripts/deploy-main-stack.sh test

# Enable function-specific roles
./scripts/deploy-main-stack.sh test --use-function-specific-roles
```

### Testing Function-Specific Roles
```bash
# Deploy with new IAM architecture
./scripts/deploy-main-stack.sh test --use-function-specific-roles

# Run full test suite
./scripts/deploy-main-stack.sh test --use-function-specific-roles --full-tests

# Rollback to unified role
./scripts/deploy-main-stack.sh test
```

## Troubleshooting

### Missing Nested Stack Templates
```
✗ Missing template: cfn/iam/roles-stack.yaml
```

**Solution:** Ensure all nested stack templates exist in the repository before deployment.

### Bucket Creation Conflicts
```
✗ Failed to create deployment bucket
```

**Solution:** The script retries 3 times. If it still fails, check AWS account permissions.

### Stack Update In Progress
```
❌ Stack is currently being updated
```

**Solution:** Wait for current deployment to complete, or use `--force` to bypass (not recommended).

## Migration Path

### Overview

Migrating from `master-template.yaml` to `main-stack.yaml` requires careful planning and testing. The two architectures are **NOT compatible** - you cannot update an existing stack from one template to the other.

### Migration Strategy

**Option 1: Create New Stack (Recommended)**

Create a new stack with main-stack.yaml alongside the existing stack:

1. **Deploy new QA stack** with main-stack.yaml:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

2. **Test thoroughly** in QA environment:
   ```bash
   # Run functional equivalence tests
   pytest tests/integration/test_functional_equivalence_function_specific.py -v
   
   # Run negative security tests
   pytest tests/integration/test_negative_security_function_specific.py -v
   
   # Run rollback tests
   pytest tests/integration/test_rollback_capability.py -v
   ```

3. **Migrate data** from old stack to new stack (if needed):
   - Export DynamoDB tables from old stack
   - Import into new stack tables
   - Update DNS/endpoints to point to new stack

4. **Cutover** when ready:
   - Update application configuration to use new stack endpoints
   - Monitor for issues
   - Keep old stack running for rollback capability

5. **Decommission old stack** after successful cutover:
   ```bash
   aws cloudformation delete-stack --stack-name aws-drs-orchestration-test
   ```

**Option 2: In-Place Migration (Not Recommended)**

In-place migration requires deleting and recreating the stack:

⚠️ **WARNING**: This approach causes downtime and data loss. Only use for non-production environments.

1. **Backup all data**:
   ```bash
   # Export DynamoDB tables
   aws dynamodb export-table-to-point-in-time \
     --table-arn arn:aws:dynamodb:us-east-2:ACCOUNT:table/TABLE_NAME \
     --s3-bucket backup-bucket \
     --s3-prefix dynamodb-backup/
   ```

2. **Delete existing stack**:
   ```bash
   aws cloudformation delete-stack --stack-name aws-drs-orchestration-test
   aws cloudformation wait stack-delete-complete --stack-name aws-drs-orchestration-test
   ```

3. **Deploy new stack**:
   ```bash
   ./scripts/deploy-main-stack.sh test --use-function-specific-roles
   ```

4. **Restore data** from backups

### Migration Checklist

Before migrating production:

- [ ] QA stack deployed with main-stack.yaml
- [ ] Function-specific roles tested in QA
- [ ] All functional equivalence tests passing
- [ ] All negative security tests passing
- [ ] Rollback capability verified
- [ ] Performance benchmarks meet requirements (within 10% of unified role)
- [ ] Monitoring and alarms configured
- [ ] Runbooks updated for new architecture
- [ ] Team trained on new IAM architecture
- [ ] Rollback plan documented and tested
- [ ] Stakeholder approval obtained

### Rollback Procedures

#### Rollback from Function-Specific to Unified Role

If issues occur with function-specific roles, rollback to unified role:

```bash
# Deploy with unified role (UseFunctionSpecificRoles=false)
./scripts/deploy-main-stack.sh test

# Verify all functions operational
pytest tests/integration/test_functional_equivalence_unified.py -v
```

**Rollback characteristics:**
- **Downtime**: None - CloudFormation update completes without service interruption
- **Data loss**: None - DynamoDB tables and executions preserved
- **Duration**: 5-10 minutes for CloudFormation update
- **Verification**: All Lambda functions immediately use unified role

#### Rollback from main-stack.yaml to master-template.yaml

If critical issues occur with nested stack architecture:

⚠️ **WARNING**: This requires deleting and recreating the stack (causes downtime).

1. **Backup all data** (DynamoDB tables, configuration)

2. **Delete main-stack.yaml stack**:
   ```bash
   aws cloudformation delete-stack --stack-name aws-drs-orchestration-test
   aws cloudformation wait stack-delete-complete --stack-name aws-drs-orchestration-test
   ```

3. **Deploy master-template.yaml stack**:
   ```bash
   ./scripts/deploy.sh test
   ```

4. **Restore data** from backups

5. **Verify functionality**:
   ```bash
   pytest tests/integration/ -v
   ```

### Post-Migration Validation

After migration, verify:

1. **API Gateway endpoints** respond correctly
2. **Lambda functions** execute without errors
3. **DynamoDB tables** contain expected data
4. **Step Functions** workflows complete successfully
5. **CloudWatch alarms** are not triggering
6. **CloudTrail logs** show expected IAM role usage
7. **Frontend** loads and functions correctly
8. **Cross-account operations** work with ExternalId validation

## QA Environment Deployment

### Overview

The QA environment (`aws-drs-orchestration-qa`) is the primary integration testing environment for the new nested stack architecture with function-specific IAM roles.

### QA Environment Configuration

- **Stack Name**: `aws-drs-orchestration-qa`
- **Environment**: `qa`
- **Region**: `us-east-2` (US East Ohio)
- **Account**: `438465159935`
- **Deployment Bucket**: `aws-drs-orchestration-438465159935-qa`
- **IAM Architecture**: Function-specific roles (5 dedicated roles)
- **WAF**: Enabled with rate limiting and geo-blocking
- **Notifications**: Enabled with SNS email alerts
- **CloudWatch Alarms**: Enabled for AccessDenied errors

### Deploying to QA

```bash
# Full deployment with function-specific roles
./scripts/deploy-main-stack.sh qa --use-function-specific-roles

# Validation only (no deployment)
./scripts/deploy-main-stack.sh qa --use-function-specific-roles --validate-only

# With full test suite
./scripts/deploy-main-stack.sh qa --use-function-specific-roles --full-tests
```

### QA Environment Features

**Function-Specific IAM Roles:**
- Query Handler Role: Read-only access to DRS, DynamoDB, EC2
- Data Management Role: DynamoDB CRUD + DRS metadata
- Execution Handler Role: Step Functions + SNS orchestration
- Orchestration Role: Comprehensive DRS + EC2 permissions
- Frontend Deployer Role: S3 + CloudFront operations

**Security Controls:**
- WAF Web ACL with rate limiting (2000 requests per 5 minutes)
- Geo-blocking for non-US traffic
- ExternalId validation for cross-account STS AssumeRole
- IAM condition keys restricting DRS writes to deployment region
- KMS operations restricted to EC2 and DRS services via condition keys

**Monitoring:**
- CloudWatch alarms for AccessDenied errors (5 errors in 5 minutes)
- SNS notifications to admin email
- CloudWatch Logs for all Lambda functions
- CloudWatch metrics for Lambda duration and errors

**Notifications:**
- SNS topics for execution alerts
- Email subscriptions for admin notifications
- Alarm notifications for security events

### QA Testing Workflow

1. **Deploy to QA**:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

2. **Run functional equivalence tests**:
   ```bash
   pytest tests/integration/test_functional_equivalence_function_specific.py -v
   ```

3. **Run negative security tests**:
   ```bash
   pytest tests/integration/test_negative_security_function_specific.py -v
   ```

4. **Run rollback tests**:
   ```bash
   pytest tests/integration/test_rollback_capability.py -v
   ```

5. **Verify monitoring**:
   ```bash
   pytest tests/integration/test_alarm_trigger.py -v
   ```

6. **Test cross-account operations** with ExternalId validation

7. **Verify EventBridge rules** are not duplicated

### QA Environment Endpoints

- **API Gateway**: `https://{api-id}.execute-api.us-east-2.amazonaws.com/qa`
- **CloudFront**: `https://{distribution-id}.cloudfront.net`
- **Cognito User Pool**: `{pool-id}.us-east-2.amazoncognito.com`

### QA Environment Verification

After deployment, verify:

```bash
# Check stack status
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2 \
  --query 'Stacks[0].StackStatus'

# Check IAM roles created
AWS_PAGER="" aws iam list-roles \
  --query 'Roles[?contains(RoleName, `aws-drs-orchestration`) && contains(RoleName, `qa`)].RoleName' \
  --region us-east-2

# Check Lambda functions
AWS_PAGER="" aws lambda list-functions \
  --query 'Functions[?contains(FunctionName, `aws-drs-orchestration-qa`)].FunctionName' \
  --region us-east-2

# Check CloudWatch alarms
AWS_PAGER="" aws cloudwatch describe-alarms \
  --alarm-name-prefix aws-drs-orchestration-qa \
  --region us-east-2

# Check WAF Web ACL
AWS_PAGER="" aws wafv2 list-web-acls \
  --scope REGIONAL \
  --region us-east-2 \
  --query 'WebACLs[?contains(Name, `aws-drs-orchestration-qa`)]'
```

### QA Environment Cleanup

To delete the QA environment:

```bash
# Delete stack (includes all nested stacks)
aws cloudformation delete-stack \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2

# Wait for deletion to complete
aws cloudformation wait stack-delete-complete \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2

# Verify deletion
AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name aws-drs-orchestration-qa \
  --region us-east-2
```

**Note**: Deletion may fail if S3 buckets contain objects. Empty buckets manually if needed:

```bash
# Empty frontend bucket
aws s3 rm s3://aws-drs-orchestration-qa-fe-438465159935 --recursive

# Empty deployment bucket
aws s3 rm s3://aws-drs-orchestration-438465159935-qa --recursive
```


## Troubleshooting

### Common Issues

#### Issue: Stack Update In Progress
```
❌ Stack is currently being updated
```

**Cause**: Another deployment is in progress or stack is in UPDATE_IN_PROGRESS state.

**Solution**:
1. Wait for current deployment to complete
2. Check stack status:
   ```bash
   AWS_PAGER="" aws cloudformation describe-stacks \
     --stack-name aws-drs-orchestration-qa \
     --query 'Stacks[0].StackStatus'
   ```
3. If stuck, use `--force` flag (not recommended)

#### Issue: Missing Nested Stack Templates
```
✗ Missing template: cfn/iam/roles-stack.yaml
```

**Cause**: Nested stack template not found in S3 deployment bucket.

**Solution**:
1. Verify template exists locally:
   ```bash
   ls -la cfn/iam/roles-stack.yaml
   ```
2. Re-run deployment (script syncs templates automatically)
3. Manually sync if needed:
   ```bash
   aws s3 sync cfn/ s3://aws-drs-orchestration-438465159935-qa/cfn/
   ```

#### Issue: AccessDenied Errors After Enabling Function-Specific Roles
```
AccessDeniedException: User is not authorized to perform: drs:StartRecovery
```

**Cause**: Function-specific role missing required permission.

**Solution**:
1. Check CloudWatch Logs for denied action:
   ```bash
   AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-qa --since 10m
   ```
2. Verify IAM role has required permission:
   ```bash
   AWS_PAGER="" aws iam get-role-policy \
     --role-name aws-drs-orchestration-query-handler-role-qa \
     --policy-name QueryHandlerPolicy
   ```
3. Update IAM role in `cfn/iam/roles-stack.yaml`
4. Redeploy:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

#### Issue: Rollback Failed State
```
UPDATE_ROLLBACK_FAILED
```

**Cause**: CloudFormation rollback encountered an error.

**Solution**:
The deploy script automatically attempts recovery:
1. Identifies failed nested stacks
2. Runs `continue-update-rollback` with skip resources
3. Waits for rollback to complete
4. Proceeds with deployment

If automatic recovery fails:
```bash
# Manually continue rollback
aws cloudformation continue-update-rollback \
  --stack-name aws-drs-orchestration-qa \
  --resources-to-skip FailedResourceLogicalId

# Wait for rollback to complete
aws cloudformation wait stack-rollback-complete \
  --stack-name aws-drs-orchestration-qa
```

#### Issue: Bucket Creation Conflicts
```
✗ Failed to create deployment bucket
```

**Cause**: Bucket name already exists or insufficient permissions.

**Solution**:
1. Check if bucket exists:
   ```bash
   AWS_PAGER="" aws s3 ls s3://aws-drs-orchestration-438465159935-qa
   ```
2. Verify AWS credentials have s3:CreateBucket permission
3. Script retries 3 times automatically
4. If persistent, check for bucket name conflicts in other accounts

#### Issue: Lambda Function Not Using New Role
```
Lambda function still using unified role after enabling function-specific roles
```

**Cause**: CloudFormation update did not complete successfully.

**Solution**:
1. Check Lambda function configuration:
   ```bash
   AWS_PAGER="" aws lambda get-function-configuration \
     --function-name aws-drs-orchestration-query-handler-qa \
     --query 'Role'
   ```
2. Verify stack parameter:
   ```bash
   AWS_PAGER="" aws cloudformation describe-stacks \
     --stack-name aws-drs-orchestration-qa \
     --query 'Stacks[0].Parameters[?ParameterKey==`UseFunctionSpecificRoles`].ParameterValue'
   ```
3. Redeploy with explicit parameter:
   ```bash
   ./scripts/deploy-main-stack.sh qa --use-function-specific-roles
   ```

### Debugging Commands

**Check stack events:**
```bash
AWS_PAGER="" aws cloudformation describe-stack-events \
  --stack-name aws-drs-orchestration-qa \
  --max-items 20 \
  --query 'StackEvents[*].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId,ResourceStatusReason]' \
  --output table
```

**Check nested stack status:**
```bash
AWS_PAGER="" aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `aws-drs-orchestration-qa`)].{Name:StackName,Status:StackStatus}' \
  --output table
```

**Check Lambda logs:**
```bash
# Query Handler
AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-qa --since 10m

# Data Management Handler
AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-data-management-handler-qa --since 10m

# Execution Handler
AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-execution-handler-qa --since 10m
```

**Check CloudWatch alarms:**
```bash
AWS_PAGER="" aws cloudwatch describe-alarms \
  --alarm-name-prefix aws-drs-orchestration-qa \
  --state-value ALARM \
  --query 'MetricAlarms[*].[AlarmName,StateValue,StateReason]' \
  --output table
```

## Related Documentation

- [Deployment Guide](deployment-guide.md) - General deployment practices
- [Migration Guide](MIGRATION_GUIDE.md) - Migrating to nested stacks
- [QA Deployment Configuration](QA_DEPLOYMENT_CONFIGURATION.md) - QA environment details
- [IAM Role Reference](IAM_ROLE_REFERENCE.md) - IAM role permissions
- [Development Principles](development-principles.md) - Development standards
- [CI/CD Workflow Enforcement](cicd-workflow-enforcement.md) - Deployment workflow rules
