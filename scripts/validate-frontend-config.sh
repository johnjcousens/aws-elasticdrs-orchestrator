#!/bin/bash

# Frontend Configuration Validation Script
# Validates that frontend configuration matches current CloudFormation stack outputs

set -e

STACK_NAME="${1:-aws-drs-orchestrator-fresh}"
REGION="${2:-us-east-1}"

echo "🔍 Validating frontend configuration against stack: $STACK_NAME"

# Get current stack outputs
echo "📋 Fetching CloudFormation stack outputs..."
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
  --output text)

API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

FRONTEND_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text)

echo "✅ Stack outputs retrieved:"
echo "  User Pool ID: $USER_POOL_ID"
echo "  Client ID: $CLIENT_ID"
echo "  API Endpoint: $API_ENDPOINT"
echo "  Frontend URL: $FRONTEND_URL"

# Check deployed frontend configuration
echo ""
echo "🌐 Checking deployed frontend configuration..."
DEPLOYED_CONFIG=$(curl -s "$FRONTEND_URL/aws-config.json" || echo "{}")

if [ "$DEPLOYED_CONFIG" = "{}" ]; then
  echo "❌ Failed to fetch deployed configuration from $FRONTEND_URL/aws-config.json"
  exit 1
fi

echo "📄 Deployed configuration:"
echo "$DEPLOYED_CONFIG" | jq .

# Validate configuration matches stack outputs
echo ""
echo "🔍 Validating configuration consistency..."

DEPLOYED_USER_POOL=$(echo "$DEPLOYED_CONFIG" | jq -r '.userPoolId // empty')
DEPLOYED_CLIENT_ID=$(echo "$DEPLOYED_CONFIG" | jq -r '.userPoolClientId // empty')
DEPLOYED_API=$(echo "$DEPLOYED_CONFIG" | jq -r '.apiEndpoint // empty')

VALIDATION_PASSED=true

if [ "$DEPLOYED_USER_POOL" != "$USER_POOL_ID" ]; then
  echo "❌ User Pool ID mismatch:"
  echo "  Stack: $USER_POOL_ID"
  echo "  Deployed: $DEPLOYED_USER_POOL"
  VALIDATION_PASSED=false
fi

if [ "$DEPLOYED_CLIENT_ID" != "$CLIENT_ID" ]; then
  echo "❌ Client ID mismatch:"
  echo "  Stack: $CLIENT_ID"
  echo "  Deployed: $DEPLOYED_CLIENT_ID"
  VALIDATION_PASSED=false
fi

if [ "$DEPLOYED_API" != "$API_ENDPOINT" ]; then
  echo "❌ API Endpoint mismatch:"
  echo "  Stack: $API_ENDPOINT"
  echo "  Deployed: $DEPLOYED_API"
  VALIDATION_PASSED=false
fi

if [ "$VALIDATION_PASSED" = true ]; then
  echo "✅ All configuration values match stack outputs"
  echo ""
  echo "🧪 Testing API connectivity..."
  
  # Test API endpoint
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_ENDPOINT/health" || echo "000")
  if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "401" ]; then
    echo "✅ API endpoint is reachable (HTTP $HTTP_STATUS)"
  else
    echo "⚠️ API endpoint returned HTTP $HTTP_STATUS"
  fi
  
  echo ""
  echo "🎯 Configuration validation PASSED"
  echo "Frontend should be working correctly with current stack"
else
  echo ""
  echo "💥 Configuration validation FAILED"
  echo "Frontend configuration does not match current stack outputs"
  echo ""
  echo "🔧 To fix this issue:"
  echo "1. Redeploy frontend via GitHub Actions to regenerate configuration"
  echo "2. Or manually update aws-config.json files to match stack outputs"
  exit 1
fi