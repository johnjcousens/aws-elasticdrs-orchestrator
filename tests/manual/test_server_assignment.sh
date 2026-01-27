#!/bin/bash

# Test script to check server assignment logic

API_ENDPOINT="https://g0ojnzzfh1.execute-api.us-east-1.amazonaws.com/dev"
REGION="us-east-1"

echo "=== Testing /drs/source-servers endpoint ==="
echo ""

# Get Cognito token
echo "Getting Cognito token..."
TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id arn:aws:secretsmanager:us-east-1:777788889999:secret:drs-orchestration-dev-cognito-test-user-Ks0Aqo \
  --query SecretString --output text | jq -r '.idToken')

if [ -z "$TOKEN" ]; then
  echo "ERROR: Failed to get Cognito token"
  exit 1
fi

echo "Token obtained successfully"
echo ""

# Query DRS source servers
echo "Querying DRS source servers in $REGION..."
RESPONSE=$(curl -s -X GET \
  "${API_ENDPOINT}/drs/source-servers?region=${REGION}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json")

echo "Response:"
echo "$RESPONSE" | jq '.'
echo ""

# Extract server assignment info
echo "=== Server Assignment Summary ==="
echo "$RESPONSE" | jq -r '.servers[] | "\(.hostname) (\(.sourceServerID)): selectable=\(.selectable), assigned=\(.assignedToProtectionGroup)"'
echo ""

# Count servers
TOTAL=$(echo "$RESPONSE" | jq '.servers | length')
SELECTABLE=$(echo "$RESPONSE" | jq '[.servers[] | select(.selectable == true)] | length')
ASSIGNED=$(echo "$RESPONSE" | jq '[.servers[] | select(.selectable == false)] | length')

echo "Total servers: $TOTAL"
echo "Selectable: $SELECTABLE"
echo "Assigned: $ASSIGNED"
