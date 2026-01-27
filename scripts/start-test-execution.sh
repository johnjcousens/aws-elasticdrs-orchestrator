#!/bin/bash
# Start a test DR execution for E2E testing

set -e

API_ENDPOINT="https://g0ojnzzfh1.execute-api.us-east-1.amazonaws.com/dev"
PLAN_ID="85230bb6-feba-48c0-9011-188953c89967"
SECRET_NAME="drs-orchestration/test-user-credentials"
REGION="us-east-1"

echo "Starting DR execution for plan: 3TierRecoveryPlan"
echo "Plan ID: $PLAN_ID"
echo ""

# Get credentials from Secrets Manager
echo "Fetching test credentials..."
CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id "$SECRET_NAME" --region "$REGION" --query SecretString --output text)
EMAIL=$(echo "$CREDENTIALS" | jq -r '.username')
PASSWORD=$(echo "$CREDENTIALS" | jq -r '.password')
USER_POOL_ID=$(echo "$CREDENTIALS" | jq -r '.userPoolId')
CLIENT_ID=$(echo "$CREDENTIALS" | jq -r '.clientId')

# Get actual username (UUID) from email
echo "Looking up user..."
ACTUAL_USERNAME=$(aws cognito-idp list-users \
  --user-pool-id "$USER_POOL_ID" \
  --filter "email = \"$EMAIL\"" \
  --query 'Users[0].Username' \
  --output text)

if [ -z "$ACTUAL_USERNAME" ] || [ "$ACTUAL_USERNAME" = "None" ]; then
  echo "✗ User not found: $EMAIL"
  exit 1
fi

# Authenticate with Cognito
echo "Authenticating with Cognito..."
ID_TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id "$USER_POOL_ID" \
  --client-id "$CLIENT_ID" \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME="$ACTUAL_USERNAME",PASSWORD="$PASSWORD" \
  --query 'AuthenticationResult.IdToken' \
  --output text)

if [ -z "$ID_TOKEN" ] || [ "$ID_TOKEN" = "null" ]; then
  echo "✗ Authentication failed"
  exit 1
fi

echo "✓ Authentication successful"
echo ""

# Start execution
echo "Starting execution..."
RESPONSE=$(curl -s -X POST "${API_ENDPOINT}/executions" \
  -H "Authorization: $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"planId\": \"${PLAN_ID}\",
    \"executionType\": \"DRILL\",
    \"description\": \"E2E Test 1 - Server Enrichment & Execution Details\",
    \"initiatedBy\": \"${EMAIL}\"
  }")

echo "Response:"
echo "$RESPONSE" | jq '.'

# Extract execution ID
EXECUTION_ID=$(echo "$RESPONSE" | jq -r '.executionId // .execution.executionId // empty')

if [ -n "$EXECUTION_ID" ]; then
  echo ""
  echo "✅ Execution started successfully!"
  echo "Execution ID: $EXECUTION_ID"
  echo ""
  echo "Monitor execution:"
  echo "  CloudWatch Logs: aws logs tail /aws/lambda/aws-drs-orchestration-execution-handler-dev --follow"
  echo "  DynamoDB: aws dynamodb get-item --table-name aws-drs-orchestration-execution-history-dev --key '{\"executionId\":{\"S\":\"$EXECUTION_ID\"}}'"
  echo "  Frontend: https://d1ksi7eif6291h.cloudfront.net/executions/$EXECUTION_ID"
else
  echo ""
  echo "❌ Failed to start execution"
  exit 1
fi
