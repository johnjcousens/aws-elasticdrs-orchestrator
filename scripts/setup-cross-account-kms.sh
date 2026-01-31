#!/bin/bash
set -e

# DRS Cross-Account KMS Setup Script
# This script sets up a CMK in the staging account that the target account can use
#
# IMPORTANT: Set your AWS account IDs before running:
#   export STAGING_ACCOUNT_ID=your-staging-account-id
#   export TARGET_ACCOUNT_ID=your-target-account-id
#
# Example account IDs are provided as defaults for testing

# Configuration
STAGING_ACCOUNT="${STAGING_ACCOUNT_ID:-123456789012}"  # Replace with your staging account ID
TARGET_ACCOUNT="${TARGET_ACCOUNT_ID:-987654321098}"    # Replace with your target account ID
STAGING_REGION="us-east-1"
TARGET_REGION="us-west-2"
KEY_ALIAS="drs-cross-account-ebs"
STAGING_PROFILE="${STAGING_ACCOUNT}_AdministratorAccess"

echo "=========================================="
echo "DRS Cross-Account KMS Setup"
echo "=========================================="
echo "Staging Account: $STAGING_ACCOUNT"
echo "Target Account: $TARGET_ACCOUNT"
echo "Staging Region: $STAGING_REGION"
echo "Target Region: $TARGET_REGION"
echo "AWS Profile: $STAGING_PROFILE"
echo "=========================================="
echo ""

# Verify profile exists
if ! grep -q "\[$STAGING_PROFILE\]" ~/.aws/credentials 2>/dev/null; then
    echo "❌ ERROR: AWS profile '$STAGING_PROFILE' not found in ~/.aws/credentials"
    exit 1
fi

# Check account
CURRENT_ACCOUNT=$(AWS_PAGER="" aws sts get-caller-identity --profile $STAGING_PROFILE --query 'Account' --output text)
echo "Current AWS Account: $CURRENT_ACCOUNT"
echo ""

if [ "$CURRENT_ACCOUNT" != "$STAGING_ACCOUNT" ]; then
    echo "❌ ERROR: Profile is not for staging account"
    echo "Expected: $STAGING_ACCOUNT"
    echo "Got: $CURRENT_ACCOUNT"
    exit 1
fi

echo "✅ Authenticated to staging account"
echo ""

# Step 1: Check if key already exists
echo "Step 1: Checking for existing key..."
EXISTING_KEY=$(AWS_PAGER="" aws kms list-aliases \
    --profile $STAGING_PROFILE \
    --region $STAGING_REGION \
    --query "Aliases[?AliasName=='alias/$KEY_ALIAS'].TargetKeyId" \
    --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_KEY" ]; then
    echo "⚠️  Key already exists: $EXISTING_KEY"
    echo "Alias: alias/$KEY_ALIAS"
    read -p "Do you want to update the existing key policy? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting without changes."
        exit 0
    fi
    KEY_ID="$EXISTING_KEY"
else
    echo "No existing key found. Creating new key..."
    
    # Step 2: Create the CMK
    echo ""
    echo "Step 2: Creating CMK in staging account..."
    
    KEY_OUTPUT=$(AWS_PAGER="" aws kms create-key \
        --profile $STAGING_PROFILE \
        --description "DRS EBS encryption key for cross-account recovery" \
        --key-usage ENCRYPT_DECRYPT \
        --origin AWS_KMS \
        --region $STAGING_REGION \
        --tags TagKey=Purpose,TagValue=DRS-Cross-Account TagKey=TargetAccount,TagValue=$TARGET_ACCOUNT \
        --output json)
    
    KEY_ID=$(echo "$KEY_OUTPUT" | jq -r '.KeyMetadata.KeyId')
    KEY_ARN=$(echo "$KEY_OUTPUT" | jq -r '.KeyMetadata.Arn')
    
    echo "✅ Created CMK"
    echo "   Key ID: $KEY_ID"
    echo "   Key ARN: $KEY_ARN"
    
    # Step 3: Create alias
    echo ""
    echo "Step 3: Creating alias..."
    AWS_PAGER="" aws kms create-alias \
        --profile $STAGING_PROFILE \
        --alias-name "alias/$KEY_ALIAS" \
        --target-key-id "$KEY_ID" \
        --region $STAGING_REGION
    
    echo "✅ Created alias: alias/$KEY_ALIAS"
fi

# Step 4: Create and apply key policy
echo ""
echo "Step 4: Creating cross-account key policy..."

cat > /tmp/kms-key-policy.json << EOF
{
  "Version": "2012-10-17",
  "Id": "drs-cross-account-key-policy",
  "Statement": [
    {
      "Sid": "Enable IAM User Permissions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${STAGING_ACCOUNT}:root"
      },
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "Allow use of the key by target account",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::${TARGET_ACCOUNT}:root",
          "arn:aws:iam::${TARGET_ACCOUNT}:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery"
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
          "arn:aws:iam::${TARGET_ACCOUNT}:root",
          "arn:aws:iam::${TARGET_ACCOUNT}:role/aws-service-role/drs.amazonaws.com/AWSServiceRoleForElasticDisasterRecovery"
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
        "kms:CreateGrant",
        "kms:GenerateDataKey"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": [
            "drs.${STAGING_REGION}.amazonaws.com",
            "ec2.${STAGING_REGION}.amazonaws.com"
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
            "drs.${TARGET_REGION}.amazonaws.com",
            "ec2.${TARGET_REGION}.amazonaws.com"
          ]
        }
      }
    }
  ]
}
EOF

echo "Key policy created at /tmp/kms-key-policy.json"
echo ""
echo "Applying key policy..."

AWS_PAGER="" aws kms put-key-policy \
    --profile $STAGING_PROFILE \
    --key-id "$KEY_ID" \
    --policy-name default \
    --policy file:///tmp/kms-key-policy.json \
    --region $STAGING_REGION

echo "✅ Key policy applied"

# Get final key details
KEY_ARN=$(AWS_PAGER="" aws kms describe-key \
    --profile $STAGING_PROFILE \
    --key-id "$KEY_ID" \
    --region $STAGING_REGION \
    --query 'KeyMetadata.Arn' \
    --output text)

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Key Details:"
echo "  Key ID: $KEY_ID"
echo "  Key ARN: $KEY_ARN"
echo "  Alias: alias/$KEY_ALIAS"
echo "  Region: $STAGING_REGION"
echo ""
echo "Next Steps:"
echo "1. Update DRS replication configuration to use this key:"
echo "   aws drs update-replication-configuration-template \\"
echo "     --region $STAGING_REGION \\"
echo "     --ebs-encryption CUSTOM \\"
echo "     --ebs-encryption-key-arn $KEY_ARN"
echo ""
echo "2. Verify cross-account access from target account ($TARGET_ACCOUNT):"
echo "   aws kms describe-key \\"
echo "     --key-id $KEY_ARN \\"
echo "     --region $STAGING_REGION"
echo ""
echo "3. Install DRS agents with the configured encryption"
echo ""
echo "Key policy saved to: /tmp/kms-key-policy.json"
echo "=========================================="

# Cleanup
rm -f /tmp/kms-key-policy.json
