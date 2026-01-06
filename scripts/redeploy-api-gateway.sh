#!/bin/bash
# Redeploy API Gateway to ensure CORS and all methods are properly applied
# This script should be run after any CloudFormation deployment that touches API Gateway

set -e

STACK_NAME="${1:-aws-elasticdrs-orchestrator-dev}"
REGION="${2:-us-east-1}"

echo "🔄 Redeploying API Gateway for stack: $STACK_NAME"

# Get API ID from stack outputs
API_ID=$(AWS_PAGER="" aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiId`].OutputValue' \
    --output text \
    --region "$REGION" 2>/dev/null)

if [ -z "$API_ID" ] || [ "$API_ID" == "None" ]; then
    echo "❌ Could not find API ID in stack outputs"
    exit 1
fi

echo "  API ID: $API_ID"

# Get current stage name (usually 'dev')
STAGE_NAME=$(AWS_PAGER="" aws apigateway get-stages \
    --rest-api-id "$API_ID" \
    --query 'item[0].stageName' \
    --output text \
    --region "$REGION" 2>/dev/null)

if [ -z "$STAGE_NAME" ] || [ "$STAGE_NAME" == "None" ]; then
    STAGE_NAME="dev"
fi

echo "  Stage: $STAGE_NAME"

# Create new deployment
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
DEPLOYMENT_ID=$(AWS_PAGER="" aws apigateway create-deployment \
    --rest-api-id "$API_ID" \
    --stage-name "$STAGE_NAME" \
    --description "Post-CFN deployment $TIMESTAMP" \
    --query 'id' \
    --output text \
    --region "$REGION" 2>/dev/null)

echo "  New Deployment ID: $DEPLOYMENT_ID"

# Verify OPTIONS endpoints return 200
echo "  Verifying CORS..."
sleep 2

API_ENDPOINT="https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE_NAME}"
OPTIONS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS "${API_ENDPOINT}/protection-groups" 2>/dev/null || echo "000")

if [ "$OPTIONS_STATUS" == "200" ]; then
    echo "✅ API Gateway redeployed successfully (OPTIONS returns 200)"
else
    echo "⚠️  OPTIONS returned $OPTIONS_STATUS - may need manual verification"
fi

echo ""
echo "API Endpoint: $API_ENDPOINT"
