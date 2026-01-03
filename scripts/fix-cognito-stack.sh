#!/bin/bash
# Fix Cognito Identity Pool Role Attachment Issue

set -e
export AWS_PAGER=""

REGION="us-east-1"
BUCKET="aws-elasticdrs-orchestrator"
NEW_STACK_NAME="elasticdrs-orchestration-fixed"

echo "🔧 Fixing Cognito Identity Pool Role Attachment Issue"
echo "======================================================"

# Deploy new stack with fixed template
echo "🚀 Creating new stack with fixed Cognito configuration..."

aws cloudformation create-stack \
  --stack-name "$NEW_STACK_NAME" \
  --template-url "https://$BUCKET.s3.$REGION.amazonaws.com/cfn/master-template.yaml" \
  --parameters \
    ParameterKey=ProjectName,ParameterValue="aws-elasticdrs-orchestrator" \
    ParameterKey=Environment,ParameterValue="dev" \
    ParameterKey=SourceBucket,ParameterValue="$BUCKET" \
    ParameterKey=AdminEmail,ParameterValue="jocousen@amazon.com" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region "$REGION"

echo "⏳ Waiting for stack creation to complete..."
aws cloudformation wait stack-create-complete --stack-name "$NEW_STACK_NAME" --region "$REGION"

echo "✅ New stack created successfully!"

# Get outputs
echo ""
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks --stack-name "$NEW_STACK_NAME" --region "$REGION" \
  --query 'Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}' \
  --output table

echo ""
echo "🎯 Next Steps:"
echo "1. Test the new stack functionality"
echo "2. Update DNS/references to point to new stack"
echo "3. Delete old stack: aws cloudformation delete-stack --stack-name drs-orch-v4 --region us-east-1"