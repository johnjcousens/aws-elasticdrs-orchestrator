# Staging Accounts Management CLI Scripts

Command-line tools for managing staging accounts in the DRS Orchestration Platform.

## Overview

These scripts provide CLI access to staging account management operations, enabling automation and DevOps workflows. All scripts invoke Lambda functions via AWS CLI and require appropriate AWS credentials.

## Prerequisites

- AWS CLI installed and configured
- Valid AWS credentials with Lambda invoke permissions
- `jq` installed for JSON parsing
- Bash shell (Linux/macOS/WSL)

## Environment Configuration

Set the environment variable to target the correct deployment:

```bash
export AWS_ENVIRONMENT=test  # or dev, staging, prod
```

Default environment is `test` if not specified.

## Scripts

### 1. add-staging-account.sh

Adds a staging account to a target account configuration.

**Usage:**
```bash
./scripts/staging-accounts/add-staging-account.sh \
  <target-account-id> \
  <staging-account-id> \
  <staging-account-name> \
  <role-arn> \
  <external-id>
```

**Example:**
```bash
./scripts/staging-accounts/add-staging-account.sh \
  111122223333 \
  444455556666 \
  STAGING_01 \
  arn:aws:iam::444455556666:role/DRSOrchestrationRole-test \
  drs-orchestration-test-444455556666
```

**Output:**
- Success message with updated staging accounts list
- Error message if operation fails

**Validates:**
- Account ID format (12 digits)
- Role ARN format
- Duplicate staging accounts

### 2. remove-staging-account.sh

Removes a staging account from a target account configuration.

**Usage:**
```bash
./scripts/staging-accounts/remove-staging-account.sh \
  <target-account-id> \
  <staging-account-id>
```

**Example:**
```bash
./scripts/staging-accounts/remove-staging-account.sh \
  111122223333 \
  444455556666
```

**Features:**
- Confirmation prompt before removal
- Displays remaining staging accounts after removal
- Warning if staging account has active servers

**Output:**
- Success message with remaining staging accounts
- Error message if operation fails

### 3. validate-staging-account.sh

Validates staging account access and DRS initialization before adding.

**Usage:**
```bash
./scripts/staging-accounts/validate-staging-account.sh \
  <account-id> \
  <role-arn> \
  <external-id> \
  [region]
```

**Example:**
```bash
./scripts/staging-accounts/validate-staging-account.sh \
  444455556666 \
  arn:aws:iam::444455556666:role/DRSOrchestrationRole-test \
  drs-orchestration-test-444455556666 \
  us-east-1
```

**Validation Checks:**
- ✓ Role accessibility (STS AssumeRole)
- ✓ DRS initialization status
- ✓ Current server counts
- ✓ Capacity impact

**Output:**
```
═══════════════════════════════════════════════════════════
                  VALIDATION RESULTS
═══════════════════════════════════════════════════════════

✓ SUCCESS: Validation passed

✓ SUCCESS: Role is accessible
✓ SUCCESS: DRS is initialized

─────────────────────────────────────────────────────────
                  CAPACITY INFORMATION
─────────────────────────────────────────────────────────

  Current Servers:       42
  Replicating Servers:   42
  Total After Adding:    267

✓ SUCCESS: Staging account has sufficient capacity (42/300 servers)

═══════════════════════════════════════════════════════════
✓ SUCCESS: Staging account is ready to be added!
═══════════════════════════════════════════════════════════
```

**Troubleshooting:**
- Provides specific error messages for role access failures
- Includes steps to initialize DRS if not initialized
- Shows capacity warnings if approaching limits

### 4. list-staging-accounts.sh

Lists all staging accounts configured for a target account.

**Usage:**
```bash
./scripts/staging-accounts/list-staging-accounts.sh <target-account-id>
```

**Example:**
```bash
./scripts/staging-accounts/list-staging-accounts.sh 111122223333
```

**Output:**
```
═══════════════════════════════════════════════════════════
              TARGET ACCOUNT INFORMATION
═══════════════════════════════════════════════════════════

  Account ID:    111122223333
  Account Name:  DEMO_TARGET

─────────────────────────────────────────────────────────
            STAGING ACCOUNTS (2)
─────────────────────────────────────────────────────────

  Account ID:    444455556666
  Account Name:  STAGING_01
  Role ARN:      arn:aws:iam::444455556666:role/DRSOrchestrationRole-test
  External ID:   drs-orchestration-test-444455556666
  ─────────────────────────────────────────────────────────

  Account ID:    777777777777
  Account Name:  STAGING_02
  Role ARN:      arn:aws:iam::777777777777:role/DRSOrchestrationRole-test
  External ID:   drs-orchestration-test-777777777777
  ─────────────────────────────────────────────────────────

✓ SUCCESS: Found 2 staging account(s)

═══════════════════════════════════════════════════════════
```

## Complete Workflow Example

### Adding a New Staging Account

```bash
# Step 1: Validate the staging account
./scripts/staging-accounts/validate-staging-account.sh \
  444455556666 \
  arn:aws:iam::444455556666:role/DRSOrchestrationRole-test \
  drs-orchestration-test-444455556666 \
  us-east-1

# Step 2: If validation passes, add the staging account
./scripts/staging-accounts/add-staging-account.sh \
  111122223333 \
  444455556666 \
  STAGING_01 \
  arn:aws:iam::444455556666:role/DRSOrchestrationRole-test \
  drs-orchestration-test-444455556666

# Step 3: Verify the staging account was added
./scripts/staging-accounts/list-staging-accounts.sh 111122223333
```

### Removing a Staging Account

```bash
# Step 1: List current staging accounts
./scripts/staging-accounts/list-staging-accounts.sh 111122223333

# Step 2: Remove the staging account
./scripts/staging-accounts/remove-staging-account.sh \
  111122223333 \
  444455556666

# Step 3: Verify removal
./scripts/staging-accounts/list-staging-accounts.sh 111122223333
```

## Automation Examples

### Batch Add Multiple Staging Accounts

```bash
#!/bin/bash

TARGET_ACCOUNT="111122223333"
ENVIRONMENT="test"

# Array of staging accounts
declare -a STAGING_ACCOUNTS=(
  "444455556666:STAGING_01"
  "777777777777:STAGING_02"
  "888888888888:STAGING_03"
)

for account in "${STAGING_ACCOUNTS[@]}"; do
  IFS=':' read -r ACCOUNT_ID ACCOUNT_NAME <<< "$account"
  
  ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/DRSOrchestrationRole-${ENVIRONMENT}"
  EXTERNAL_ID="drs-orchestration-${ENVIRONMENT}-${ACCOUNT_ID}"
  
  echo "Adding ${ACCOUNT_NAME} (${ACCOUNT_ID})..."
  
  # Validate first
  if ./scripts/staging-accounts/validate-staging-account.sh \
      "$ACCOUNT_ID" "$ROLE_ARN" "$EXTERNAL_ID" "us-east-1"; then
    
    # Add if validation passes
    ./scripts/staging-accounts/add-staging-account.sh \
      "$TARGET_ACCOUNT" "$ACCOUNT_ID" "$ACCOUNT_NAME" "$ROLE_ARN" "$EXTERNAL_ID"
  else
    echo "Skipping ${ACCOUNT_NAME} due to validation failure"
  fi
  
  echo ""
done
```

### Monitoring Script

```bash
#!/bin/bash

# Monitor staging accounts and alert if any fail validation

TARGET_ACCOUNT="111122223333"

# Get staging accounts
STAGING_ACCOUNTS=$(./scripts/staging-accounts/list-staging-accounts.sh "$TARGET_ACCOUNT" | \
  jq -r '.stagingAccounts[] | "\(.accountId):\(.roleArn):\(.externalId)"')

for account in $STAGING_ACCOUNTS; do
  IFS=':' read -r ACCOUNT_ID ROLE_ARN EXTERNAL_ID <<< "$account"
  
  if ! ./scripts/staging-accounts/validate-staging-account.sh \
      "$ACCOUNT_ID" "$ROLE_ARN" "$EXTERNAL_ID" "us-east-1" > /dev/null 2>&1; then
    
    echo "ALERT: Staging account ${ACCOUNT_ID} validation failed!"
    # Send alert (SNS, email, Slack, etc.)
  fi
done
```

## Error Handling

All scripts:
- Return exit code 0 on success
- Return exit code 1 on failure
- Print colored output (green for success, red for errors, yellow for warnings)
- Validate input parameters before execution
- Provide detailed error messages with troubleshooting steps

## Security Considerations

- Scripts use AWS CLI with your configured credentials
- External IDs prevent confused deputy attacks
- Role ARNs are validated before use
- No credentials are stored in scripts
- All operations are logged in CloudTrail

## Troubleshooting

### "Lambda invocation failed"
- Verify AWS credentials are configured: `aws sts get-caller-identity`
- Verify Lambda function exists: `aws lambda get-function --function-name aws-drs-orchestration-data-management-test`
- Check IAM permissions for Lambda invoke

### "Role is not accessible"
- Verify role ARN is correct
- Check role trust policy allows assumption from orchestration account
- Verify external ID matches
- Check IAM permissions in staging account

### "DRS is not initialized"
- Log into staging account
- Navigate to AWS DRS console
- Initialize DRS service
- Accept service terms

### "jq: command not found"
- Install jq: `sudo apt-get install jq` (Ubuntu/Debian)
- Or: `brew install jq` (macOS)

## Related Documentation

- [Staging Accounts Management Design](../../.kiro/specs/staging-accounts-management/design.md)
- [IAM Permissions Verification](../../.kiro/specs/staging-accounts-management/iam-permissions-verification.md)
- [API Documentation](../../docs/api/staging-accounts.md)

## Support

For issues or questions:
1. Check CloudWatch Logs for Lambda function errors
2. Review CloudTrail for API call details
3. Verify IAM permissions and role trust policies
4. Consult the design documentation for architecture details
