#!/bin/bash
# Quick Lambda deployment script
set -e

LAMBDA_NAME="${1:-api-handler}"
REGION="${2:-us-east-1}"
BUCKET="${3:-aws-drs-orch-dev}"

echo "Deploying Lambda: $LAMBDA_NAME"

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Copy Lambda code
cp lambda/$LAMBDA_NAME/index.py $TEMP_DIR/
cp -r lambda/shared $TEMP_DIR/

# Install dependencies
pip3 install -q boto3 urllib3 crhelper -t $TEMP_DIR/

# Create zip
cd $TEMP_DIR
zip -qr /tmp/$LAMBDA_NAME.zip .
cd -

# Upload to S3
aws s3 cp /tmp/$LAMBDA_NAME.zip s3://$BUCKET/lambda/$LAMBDA_NAME.zip --region $REGION

# Update Lambda function
aws lambda update-function-code \
  --function-name aws-drs-orch-$LAMBDA_NAME-dev \
  --s3-bucket $BUCKET \
  --s3-key lambda/$LAMBDA_NAME.zip \
  --region $REGION \
  --no-cli-pager

echo "✅ Lambda $LAMBDA_NAME deployed"
