#!/bin/bash
# Check execution status via API

set -e

API_ENDPOINT="https://g0ojnzzfh1.execute-api.us-east-1.amazonaws.com/dev"
EXECUTION_ID="$1"
SECRET_NAME="drs-orchestration/test-user-credentials"
REGION="us-east-1"

if [ -z "$EXECUTION_ID" ]; then
  echo "Usage: $0 <execution-id>"
  exit 1
fi

# Get credentials
CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id "$SECRET_NAME" --region "$REGION" --query SecretString --output text)
EMAIL=$(echo "$CREDENTIALS" | jq -r '.username')
PASSWORD=$(echo "$CREDENTIALS" | jq -r '.password')
USER_POOL_ID=$(echo "$CREDENTIALS" | jq -r '.userPoolId')
CLIENT_ID=$(echo "$CREDENTIALS" | jq -r '.clientId')

# Get username
ACTUAL_USERNAME=$(aws cognito-idp list-users \
  --user-pool-id "$USER_POOL_ID" \
  --filter "email = \"$EMAIL\"" \
  --query 'Users[0].Username' \
  --output text)

# Authenticate
ID_TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id "$USER_POOL_ID" \
  --client-id "$CLIENT_ID" \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME="$ACTUAL_USERNAME",PASSWORD="$PASSWORD" \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Get execution details
echo "Fetching execution details for: $EXECUTION_ID"
echo ""

RESPONSE=$(curl -s -X GET "${API_ENDPOINT}/executions/${EXECUTION_ID}" \
  -H "Authorization: $ID_TOKEN")

echo "$RESPONSE" | jq '.'
