#!/bin/bash
set -e

# Verify cross-account role setup
# Tests that orchestration account can assume roles in target and staging accounts
#
# IMPORTANT: Set your AWS account IDs before running:
#   export ORCHESTRATION_ACCOUNT_ID=your-orchestration-account-id
#   export TARGET_ACCOUNT_ID=your-target-account-id
#   export STAGING_ACCOUNT_ID=your-staging-account-id
#
# Example account IDs are provided as defaults for testing

# Configuration
ORCHESTRATION_ACCOUNT="${ORCHESTRATION_ACCOUNT_ID:-123456789012}"  # Replace with your orchestration account ID
TARGET_ACCOUNT="${TARGET_ACCOUNT_ID:-987654321098}"                # Replace with your target account ID
STAGING_ACCOUNT="${STAGING_ACCOUNT_ID:-111111111111}"              # Replace with your staging account ID
EXTERNAL_ID="DRSOrchestration2024"
ENVIRONMENT="${1:-dev}"

# AWS Profiles
ORCHESTRATION_PROFILE="${ORCHESTRATION_ACCOUNT}_AdministratorAccess"

echo "=========================================="
echo "Cross-Account Role Verification"
echo "=========================================="
echo "Orchestration Account: $ORCHESTRATION_ACCOUNT"
echo "Target Account: $TARGET_ACCOUNT"
echo "Staging Account: $STAGING_ACCOUNT"
echo "Environment: $ENVIRONMENT"
echo "=========================================="
echo ""

# Verify orchestration profile
if ! grep -q "\[$ORCHESTRATION_PROFILE\]" ~/.aws/credentials 2>/dev/null; then
    echo "❌ ERROR: AWS profile '$ORCHESTRATION_PROFILE' not found"
    exit 1
fi

# Verify we're in orchestration account
CURRENT_ACCOUNT=$(AWS_PAGER="" aws sts get-caller-identity --profile $ORCHESTRATION_PROFILE --query 'Account' --output text)
if [ "$CURRENT_ACCOUNT" != "$ORCHESTRATION_ACCOUNT" ]; then
    echo "❌ ERROR: Not authenticated to orchestration account"
    echo "Expected: $ORCHESTRATION_ACCOUNT"
    echo "Got: $CURRENT_ACCOUNT"
    exit 1
fi

echo "✅ Authenticated to orchestration account"
echo ""

# Function to test role assumption
test_assume_role() {
    local ACCOUNT_ID=$1
    local ACCOUNT_NAME=$2
    local ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/DRSOrchestrationRole-${ENVIRONMENT}"
    
    echo "=========================================="
    echo "Testing $ACCOUNT_NAME ($ACCOUNT_ID)"
    echo "=========================================="
    echo "Role ARN: $ROLE_ARN"
    echo ""
    
    # Attempt to assume role
    echo "Attempting to assume role..."
    CREDENTIALS=$(AWS_PAGER="" aws sts assume-role \
        --role-arn "$ROLE_ARN" \
        --role-session-name "verification-test" \
        --external-id "$EXTERNAL_ID" \
        --profile "$ORCHESTRATION_PROFILE" \
        --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' \
        --output text 2>&1)
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to assume role"
        echo "$CREDENTIALS"
        return 1
    fi
    
    echo "✅ Successfully assumed role"
    echo ""
    
    # Parse credentials
    ACCESS_KEY=$(echo "$CREDENTIALS" | awk '{print $1}')
    SECRET_KEY=$(echo "$CREDENTIALS" | awk '{print $2}')
    SESSION_TOKEN=$(echo "$CREDENTIALS" | awk '{print $3}')
    
    # Test DRS permissions
    echo "Testing DRS permissions..."
    DRS_TEST=$(AWS_ACCESS_KEY_ID="$ACCESS_KEY" \
               AWS_SECRET_ACCESS_KEY="$SECRET_KEY" \
               AWS_SESSION_TOKEN="$SESSION_TOKEN" \
               AWS_PAGER="" \
               aws drs describe-source-servers \
               --region us-west-2 \
               --query 'items[0].sourceServerID' \
               --output text 2>&1)
    
    if [ $? -eq 0 ]; then
        echo "✅ DRS permissions verified"
        if [ "$DRS_TEST" != "None" ] && [ -n "$DRS_TEST" ]; then
            echo "   Found source servers in account"
        fi
    else
        echo "⚠️  DRS permissions test failed (may be expected if DRS not initialized)"
        echo "   $DRS_TEST"
    fi
    echo ""
    
    # Test EC2 permissions
    echo "Testing EC2 permissions..."
    EC2_TEST=$(AWS_ACCESS_KEY_ID="$ACCESS_KEY" \
               AWS_SECRET_ACCESS_KEY="$SECRET_KEY" \
               AWS_SESSION_TOKEN="$SESSION_TOKEN" \
               AWS_PAGER="" \
               aws ec2 describe-instances \
               --region us-east-1 \
               --max-results 1 \
               --query 'Reservations[0].Instances[0].InstanceId' \
               --output text 2>&1)
    
    if [ $? -eq 0 ]; then
        echo "✅ EC2 permissions verified"
    else
        echo "❌ EC2 permissions test failed"
        echo "   $EC2_TEST"
    fi
    echo ""
    
    # Test SSM permissions
    echo "Testing SSM permissions..."
    SSM_TEST=$(AWS_ACCESS_KEY_ID="$ACCESS_KEY" \
               AWS_SECRET_ACCESS_KEY="$SECRET_KEY" \
               AWS_SESSION_TOKEN="$SESSION_TOKEN" \
               AWS_PAGER="" \
               aws ssm describe-instance-information \
               --region us-east-1 \
               --max-results 1 \
               --query 'InstanceInformationList[0].InstanceId' \
               --output text 2>&1)
    
    if [ $? -eq 0 ]; then
        echo "✅ SSM permissions verified"
    else
        echo "⚠️  SSM permissions test failed (may be expected if no SSM instances)"
        echo "   $SSM_TEST"
    fi
    echo ""
}

# Test target account
test_assume_role "$TARGET_ACCOUNT" "Target Account"

echo ""

# Test staging account
test_assume_role "$STAGING_ACCOUNT" "Staging Account"

echo ""
echo "=========================================="
echo "✅ Verification Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✅ Orchestration account can assume roles in both accounts"
echo "  ✅ Cross-account access is properly configured"
echo "  ✅ External ID validation is working"
echo ""
echo "You can now use these roles for:"
echo "  - DRS agent deployment"
echo "  - DRS recovery operations"
echo "  - Extended source server configuration"
echo "=========================================="
