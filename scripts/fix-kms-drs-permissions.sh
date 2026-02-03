#!/bin/bash
# Fix KMS Key Policy for DRS Authorization
# Run this script to add DRS service permissions to the KMS key

set -e

KEY_ID="ab256143-c334-4d8b-bd7d-67475d8721d0"
REGION="us-west-2"

echo "Fetching current KMS key policy..."
aws kms get-key-policy \
  --key-id "$KEY_ID" \
  --policy-name default \
  --region "$REGION" \
  --output text > /tmp/kms-policy-original.json

echo "Creating updated policy with DRS permissions..."
cat > /tmp/kms-policy-updated.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowDRSService",
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
            "ec2.us-west-2.amazonaws.com",
            "drs.us-west-2.amazonaws.com"
          ]
        }
      }
    }
  ]
}
EOF

# Merge with existing policy (you'll need to manually merge if there are existing statements)
echo ""
echo "⚠️  IMPORTANT: Review the policy before applying!"
echo "Original policy saved to: /tmp/kms-policy-original.json"
echo "New DRS statement saved to: /tmp/kms-policy-updated.json"
echo ""
echo "To apply the fix, run:"
echo ""
echo "aws kms put-key-policy \\"
echo "  --key-id $KEY_ID \\"
echo "  --policy-name default \\"
echo "  --policy file:///tmp/kms-policy-merged.json \\"
echo "  --region $REGION"
echo ""
echo "First, merge the policies manually or use the Python script with proper credentials."
