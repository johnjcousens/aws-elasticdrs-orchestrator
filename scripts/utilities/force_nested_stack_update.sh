#!/bin/bash
# Force update of nested stacks by updating the master stack with a dummy parameter change

set -e

STACK_NAME="hrp-drs-tech-adapter-dev"
REGION="us-east-2"
BUCKET="hrp-drs-tech-adapter-dev"

echo "=========================================="
echo "Force Nested Stack Update"
echo "=========================================="
echo ""
echo "This script forces CloudFormation to update nested stacks by"
echo "triggering a master stack update with current parameters."
echo ""
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Get current parameters
echo "[1/3] Getting current stack parameters..."
PARAMS=$(AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Parameters' \
  --output json)

if [ $? -ne 0 ]; then
  echo "ERROR: Failed to get stack parameters"
  exit 1
fi

echo "Current parameters retrieved"
echo ""

# Convert parameters to CLI format
echo "[2/3] Converting parameters..."
CLI_PARAMS=$(echo "$PARAMS" | jq -r '.[] | "ParameterKey=\(.ParameterKey),ParameterValue=\(.ParameterValue)"' | tr '\n' ' ')

echo "Parameters converted"
echo ""

# Update stack (this will force nested stacks to update if templates changed)
echo "[3/3] Updating CloudFormation stack..."
echo "This will force nested stacks to check for template changes..."
echo ""

AWS_PAGER="" aws cloudformation update-stack \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --template-url "https://s3.amazonaws.com/$BUCKET/cfn/master-template.yaml" \
  --parameters $CLI_PARAMS \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-cli-pager

if [ $? -eq 0 ]; then
  echo ""
  echo "✓ Stack update initiated"
  echo ""
  echo "Monitor progress:"
  echo "  AWS_PAGER=\"\" aws cloudformation describe-stack-events --stack-name $STACK_NAME --region $REGION --max-items 20"
  echo ""
  echo "Wait for completion:"
  echo "  AWS_PAGER=\"\" aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $REGION"
else
  echo ""
  echo "✗ Stack update failed or no changes detected"
  echo ""
  echo "If you see 'No updates are to be performed', the nested stacks"
  echo "may not have detected changes. Try:"
  echo "  1. Check if templates in S3 are actually updated"
  echo "  2. Add a TemplateVersion parameter to force updates"
fi
