#!/bin/bash

# Deploy DRS Agent Deployer Lambda Function
#
# Usage: ./deploy-drs-lambda.sh [environment] [options]
#
# Examples:
#   ./deploy-drs-lambda.sh dev
#   ./deploy-drs-lambda.sh test --sns-topic arn:aws:sns:us-east-1:123456789012:drs-notifications

set -e

# Parse parameters
ENVIRONMENT="${1:-dev}"
SNS_TOPIC_ARN=""

shift || true
while [[ $# -gt 0 ]]; do
  case $1 in
    --sns-topic)
      SNS_TOPIC_ARN="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

PROJECT_NAME="drs-orchestration"
STACK_NAME="${PROJECT_NAME}-drs-agent-deployer-${ENVIRONMENT}"
LAMBDA_DIR="lambda/drs-agent-deployer"
BUILD_DIR="build/drs-agent-deployer"
DEPLOYMENT_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}"

echo "=========================================="
echo "DRS Agent Deployer Lambda Deployment"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Stack Name: $STACK_NAME"
echo "Deployment Bucket: $DEPLOYMENT_BUCKET"
echo ""

# Step 1: Package Lambda function
echo "[1/4] Packaging Lambda function..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy Lambda code
cp "$LAMBDA_DIR/index.py" "$BUILD_DIR/"
cp "$LAMBDA_DIR/requirements.txt" "$BUILD_DIR/"

# Install dependencies
if [ -f "$BUILD_DIR/requirements.txt" ]; then
  echo "Installing Python dependencies..."
  pip install -r "$BUILD_DIR/requirements.txt" -t "$BUILD_DIR/" --quiet
fi

# Create ZIP package
cd "$BUILD_DIR"
zip -r ../drs-agent-deployer.zip . -q
cd - > /dev/null

echo "✅ Lambda package created: build/drs-agent-deployer.zip"

# Step 2: Upload to S3
echo ""
echo "[2/4] Uploading Lambda package to S3..."
AWS_PAGER="" aws s3 cp \
  build/drs-agent-deployer.zip \
  "s3://${DEPLOYMENT_BUCKET}/lambda/drs-agent-deployer.zip"

echo "✅ Lambda package uploaded"

# Step 3: Deploy CloudFormation stack
echo ""
echo "[3/4] Deploying CloudFormation stack..."

PARAMS=(
  "ParameterKey=ProjectName,ParameterValue=${PROJECT_NAME}"
  "ParameterKey=Environment,ParameterValue=${ENVIRONMENT}"
  "ParameterKey=TargetRegion,ParameterValue=us-west-2"
  "ParameterKey=ExternalId,ParameterValue=DRSOrchestration2024"
)

if [ -n "$SNS_TOPIC_ARN" ]; then
  PARAMS+=("ParameterKey=SNSTopicArn,ParameterValue=${SNS_TOPIC_ARN}")
fi

AWS_PAGER="" aws cloudformation deploy \
  --template-file cfn/drs-agent-deployer-lambda-stack.yaml \
  --stack-name "$STACK_NAME" \
  --parameter-overrides "${PARAMS[@]}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset

echo "✅ CloudFormation stack deployed"

# Step 4: Update Lambda function code
echo ""
echo "[4/4] Updating Lambda function code..."

FUNCTION_NAME="${PROJECT_NAME}-drs-agent-deployer-${ENVIRONMENT}"

AWS_PAGER="" aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --s3-bucket "$DEPLOYMENT_BUCKET" \
  --s3-key "lambda/drs-agent-deployer.zip" \
  --publish > /dev/null

echo "✅ Lambda function code updated"

# Get function details
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

FUNCTION_ARN=$(AWS_PAGER="" aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --query 'Configuration.FunctionArn' \
  --output text)

echo "Function Name: $FUNCTION_NAME"
echo "Function ARN: $FUNCTION_ARN"
echo ""
echo "Test the function:"
echo "  aws lambda invoke \\"
echo "    --function-name $FUNCTION_NAME \\"
echo "    --payload file://test-event.json \\"
echo "    response.json"
echo ""
echo "View logs:"
echo "  aws logs tail /aws/lambda/$FUNCTION_NAME --follow"
echo ""
