#!/bin/bash
set -e

# DRS Cross-Account KMS Verification Script
# This script verifies the cross-account KMS setup

# Configuration
STAGING_ACCOUNT="444455556666"
TARGET_ACCOUNT="111122223333"
STAGING_REGION="us-east-1"
TARGET_REGION="us-west-2"
KEY_ALIAS="drs-cross-account-ebs"
STAGING_PROFILE="444455556666_AdministratorAccess"
TARGET_PROFILE="111122223333_AdministratorAccess"

echo "=========================================="
echo "DRS Cross-Account KMS Verification"
echo "=========================================="
echo "Staging Account: $STAGING_ACCOUNT"
echo "Target Account: $TARGET_ACCOUNT"
echo "=========================================="
echo ""

# Step 1: Verify key exists in staging account
echo "Step 1: Verifying key exists in staging account..."
KEY_ID=$(AWS_PAGER="" aws kms list-aliases \
    --profile $STAGING_PROFILE \
    --region $STAGING_REGION \
    --query "Aliases[?AliasName=='alias/$KEY_ALIAS'].TargetKeyId" \
    --output text 2>/dev/null || echo "")

if [ -z "$KEY_ID" ]; then
    echo "❌ ERROR: Key not found with alias 'alias/$KEY_ALIAS'"
    echo "Run ./scripts/setup-cross-account-kms.sh first"
    exit 1
fi

echo "✅ Key found: $KEY_ID"

# Get key ARN
KEY_ARN=$(AWS_PAGER="" aws kms describe-key \
    --profile $STAGING_PROFILE \
    --key-id "$KEY_ID" \
    --region $STAGING_REGION \
    --query 'KeyMetadata.Arn' \
    --output text)

echo "   Key ARN: $KEY_ARN"
echo ""

# Step 2: Verify key policy
echo "Step 2: Verifying key policy..."
KEY_POLICY=$(AWS_PAGER="" aws kms get-key-policy \
    --profile $STAGING_PROFILE \
    --key-id "$KEY_ID" \
    --policy-name default \
    --region $STAGING_REGION \
    --output json)

# Check if target account is in policy
if echo "$KEY_POLICY" | grep -q "$TARGET_ACCOUNT"; then
    echo "✅ Key policy includes target account ($TARGET_ACCOUNT)"
else
    echo "❌ ERROR: Key policy does not include target account"
    exit 1
fi

# Check for required permissions
REQUIRED_ACTIONS=("kms:Decrypt" "kms:DescribeKey" "kms:CreateGrant" "kms:GenerateDataKey")
for action in "${REQUIRED_ACTIONS[@]}"; do
    if echo "$KEY_POLICY" | grep -q "$action"; then
        echo "✅ Policy includes: $action"
    else
        echo "⚠️  WARNING: Policy may not include: $action"
    fi
done
echo ""

# Step 3: Test cross-account access from target account
echo "Step 3: Testing cross-account access from target account..."
TARGET_ACCOUNT_CHECK=$(AWS_PAGER="" aws sts get-caller-identity \
    --profile $TARGET_PROFILE \
    --query 'Account' \
    --output text)

if [ "$TARGET_ACCOUNT_CHECK" != "$TARGET_ACCOUNT" ]; then
    echo "❌ ERROR: Target profile is not for target account"
    echo "Expected: $TARGET_ACCOUNT"
    echo "Got: $TARGET_ACCOUNT_CHECK"
    exit 1
fi

echo "✅ Authenticated to target account"

# Try to describe the key from target account
if AWS_PAGER="" aws kms describe-key \
    --profile $TARGET_PROFILE \
    --key-id "$KEY_ARN" \
    --region $STAGING_REGION \
    --output json > /dev/null 2>&1; then
    echo "✅ Target account can describe the key"
else
    echo "❌ ERROR: Target account cannot describe the key"
    echo "Check key policy permissions"
    exit 1
fi
echo ""

# Step 4: Verify DRS service role exists in target account
echo "Step 4: Verifying DRS service role in target account..."
if AWS_PAGER="" aws iam get-role \
    --profile $TARGET_PROFILE \
    --role-name AWSServiceRoleForElasticDisasterRecovery \
    --output json > /dev/null 2>&1; then
    echo "✅ DRS service role exists in target account"
else
    echo "⚠️  WARNING: DRS service role not found in target account"
    echo "   Initialize DRS service first: aws drs initialize-service"
fi
echo ""

# Step 5: Check DRS replication configuration in staging account
echo "Step 5: Checking DRS replication configuration..."
DRS_CONFIG=$(AWS_PAGER="" aws drs get-replication-configuration-template \
    --profile $STAGING_PROFILE \
    --region $STAGING_REGION \
    --output json 2>/dev/null || echo "{}")

if [ "$DRS_CONFIG" != "{}" ]; then
    CONFIGURED_KEY=$(echo "$DRS_CONFIG" | jq -r '.ebsEncryptionKeyArn // empty')
    if [ "$CONFIGURED_KEY" == "$KEY_ARN" ]; then
        echo "✅ DRS is configured to use the cross-account key"
    else
        echo "⚠️  WARNING: DRS is not configured to use this key"
        echo "   Current key: $CONFIGURED_KEY"
        echo "   Expected key: $KEY_ARN"
        echo ""
        echo "   Update with:"
        echo "   aws drs update-replication-configuration-template \\"
        echo "     --profile $STAGING_PROFILE \\"
        echo "     --region $STAGING_REGION \\"
        echo "     --ebs-encryption CUSTOM \\"
        echo "     --ebs-encryption-key-arn $KEY_ARN"
    fi
else
    echo "⚠️  WARNING: DRS replication configuration not found"
    echo "   Initialize DRS first or create replication configuration"
fi
echo ""

# Step 6: Summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo "Key ID: $KEY_ID"
echo "Key ARN: $KEY_ARN"
echo "Alias: alias/$KEY_ALIAS"
echo ""
echo "✅ Key exists in staging account"
echo "✅ Key policy includes target account"
echo "✅ Target account can access the key"
echo ""
echo "Next Steps:"
echo "1. Update DRS replication configuration (if not done):"
echo "   aws drs update-replication-configuration-template \\"
echo "     --profile $STAGING_PROFILE \\"
echo "     --region $STAGING_REGION \\"
echo "     --ebs-encryption CUSTOM \\"
echo "     --ebs-encryption-key-arn $KEY_ARN"
echo ""
echo "2. Install DRS agents on source instances"
echo ""
echo "3. Verify source servers appear in target account:"
echo "   aws drs describe-source-servers \\"
echo "     --profile $TARGET_PROFILE \\"
echo "     --region $TARGET_REGION \\"
echo "     --filters '{\"stagingAccountIDs\": [\"$STAGING_ACCOUNT\"]}'"
echo "=========================================="
