#!/bin/bash

# Update Frontend Configuration from CloudFormation Stack
# This script ensures the frontend always has the correct Cognito configuration

set -e

STACK_NAME="${1:-drs-orch-v4}"
REGION="${2:-us-east-1}"
CONFIG_FILE="frontend/public/aws-config.json"
ENV_FILE=".env.$STACK_NAME"

echo "=== Updating Frontend Configuration ==="
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo "Config file: $CONFIG_FILE"
echo "Environment file: $ENV_FILE"

# Get stack outputs
echo "Fetching CloudFormation stack outputs..."
OUTPUTS=$(AWS_PAGER="" aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs' \
  --output json)

if [ "$OUTPUTS" = "null" ] || [ -z "$OUTPUTS" ]; then
  echo "❌ Error: Could not fetch stack outputs for $STACK_NAME"
  exit 1
fi

# Extract values from outputs
USER_POOL_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="UserPoolId") | .OutputValue')
CLIENT_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="UserPoolClientId") | .OutputValue')
API_ENDPOINT=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="ApiEndpoint") | .OutputValue')
CLOUDFRONT_URL=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="CloudFrontUrl") | .OutputValue')
CLOUDFRONT_DIST_ID=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="CloudFrontDistributionId") | .OutputValue')
FRONTEND_BUCKET=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="FrontendBucketName") | .OutputValue')
API_HANDLER_ARN=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="ApiHandlerFunctionArn") | .OutputValue')

# Validate required values
if [ "$USER_POOL_ID" = "null" ] || [ -z "$USER_POOL_ID" ]; then
  echo "❌ Error: UserPoolId not found in stack outputs"
  exit 1
fi

if [ "$CLIENT_ID" = "null" ] || [ -z "$CLIENT_ID" ]; then
  echo "❌ Error: UserPoolClientId not found in stack outputs"
  exit 1
fi

if [ "$API_ENDPOINT" = "null" ] || [ -z "$API_ENDPOINT" ]; then
  echo "❌ Error: ApiEndpoint not found in stack outputs"
  exit 1
fi

echo "Retrieved configuration:"
echo "  User Pool ID: $USER_POOL_ID"
echo "  Client ID: $CLIENT_ID"
echo "  API Endpoint: $API_ENDPOINT"
echo "  CloudFront URL: $CLOUDFRONT_URL"
echo "  CloudFront Distribution ID: $CLOUDFRONT_DIST_ID"
echo "  Frontend Bucket: $FRONTEND_BUCKET"

# Create/update aws-config.json
echo "Updating $CONFIG_FILE..."
cat > "$CONFIG_FILE" << EOF
{
  "region": "$REGION",
  "userPoolId": "$USER_POOL_ID",
  "userPoolClientId": "$CLIENT_ID",
  "apiEndpoint": "$API_ENDPOINT"
}
EOF

echo "✅ Frontend configuration updated successfully"

# Update environment file if it exists
if [ -f "$ENV_FILE" ]; then
  echo "Updating $ENV_FILE..."
  
  # Update Cognito configuration
  sed -i.bak "s/^COGNITO_USER_POOL_ID=.*/COGNITO_USER_POOL_ID=$USER_POOL_ID/" "$ENV_FILE"
  sed -i.bak "s/^COGNITO_CLIENT_ID=.*/COGNITO_CLIENT_ID=$CLIENT_ID/" "$ENV_FILE"
  
  # Update API configuration
  sed -i.bak "s|^API_ENDPOINT=.*|API_ENDPOINT=$API_ENDPOINT|" "$ENV_FILE"
  
  # Update CloudFront configuration if available
  if [ "$CLOUDFRONT_URL" != "null" ] && [ -n "$CLOUDFRONT_URL" ]; then
    sed -i.bak "s|^CLOUDFRONT_URL=.*|CLOUDFRONT_URL=$CLOUDFRONT_URL|" "$ENV_FILE"
  fi
  
  if [ "$CLOUDFRONT_DIST_ID" != "null" ] && [ -n "$CLOUDFRONT_DIST_ID" ]; then
    sed -i.bak "s/^CLOUDFRONT_DISTRIBUTION_ID=.*/CLOUDFRONT_DISTRIBUTION_ID=$CLOUDFRONT_DIST_ID/" "$ENV_FILE"
  fi
  
  if [ "$FRONTEND_BUCKET" != "null" ] && [ -n "$FRONTEND_BUCKET" ]; then
    sed -i.bak "s/^FRONTEND_BUCKET=.*/FRONTEND_BUCKET=$FRONTEND_BUCKET/" "$ENV_FILE"
  fi
  
  # Extract function name from ARN if available
  if [ "$API_HANDLER_ARN" != "null" ] && [ -n "$API_HANDLER_ARN" ]; then
    API_HANDLER_FUNCTION=$(echo "$API_HANDLER_ARN" | cut -d':' -f7)
    sed -i.bak "s/^API_HANDLER_FUNCTION=.*/API_HANDLER_FUNCTION=$API_HANDLER_FUNCTION/" "$ENV_FILE"
  fi
  
  # Remove backup file
  rm -f "$ENV_FILE.bak"
  
  echo "✅ Environment file updated successfully"
else
  echo "⚠️  Environment file $ENV_FILE not found, skipping update"
fi

# Validate the JSON
if ! jq . "$CONFIG_FILE" > /dev/null 2>&1; then
  echo "❌ Error: Generated JSON is invalid"
  exit 1
fi

echo "✅ Configuration validated"
echo ""
echo "Contents of $CONFIG_FILE:"
cat "$CONFIG_FILE"

# Show timestamp of update
echo ""
echo "Configuration updated at: $(date)"
echo "✅ All configuration files are now in sync with CloudFormation stack $STACK_NAME"