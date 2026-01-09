#!/bin/bash

# Create S3 Bucket for Archive Test Stack Deployment
# This script creates the required S3 bucket for the archive test stack artifacts

set -e

BUCKET_NAME="aws-drs-orchestrator-archive-test-bucket"
REGION="us-east-1"

echo "=== Creating S3 Bucket for Archive Test Stack ==="
echo "Bucket: $BUCKET_NAME"
echo "Region: $REGION"

# Create S3 bucket
echo "Creating S3 bucket..."
aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"

# Enable versioning
echo "Enabling versioning..."
aws s3api put-bucket-versioning \
  --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

# Create lifecycle policy to clean up old versions
echo "Setting up lifecycle policy..."
cat > /tmp/bucket-lifecycle.json << EOF
{
  "Rules": [
    {
      "ID": "DeleteOldVersions",
      "Status": "Enabled",
      "Filter": {},
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 30
      }
    },
    {
      "ID": "DeleteIncompleteMultipartUploads",
      "Status": "Enabled",
      "Filter": {},
      "AbortIncompleteMultipartUpload": {
        "DaysAfterInitiation": 7
      }
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET_NAME" \
  --lifecycle-configuration file:///tmp/bucket-lifecycle.json

# Set bucket policy for GitHub Actions access
echo "Setting bucket policy..."
cat > /tmp/bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GitHubActionsAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::777788889999:role/GitHubActionsRole"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::$BUCKET_NAME",
        "arn:aws:s3:::$BUCKET_NAME/*"
      ]
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket "$BUCKET_NAME" \
  --policy file:///tmp/bucket-policy.json

# Clean up temp files
rm -f /tmp/bucket-lifecycle.json /tmp/bucket-policy.json

echo "✅ S3 bucket created successfully: s3://$BUCKET_NAME"
echo "✅ Versioning enabled"
echo "✅ Lifecycle policy configured"
echo "✅ Bucket policy set for GitHub Actions access"
echo ""
echo "Next steps:"
echo "1. Add GitHub repository secrets as documented in GITHUB_SECRETS_SETUP.md"
echo "2. Push a change to trigger the multi-stack deployment"
echo "3. Monitor GitHub Actions for successful deployment to both stacks"