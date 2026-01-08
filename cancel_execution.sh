#!/bin/bash

# Cancel stuck execution via API
EXECUTION_ID="ac0bc68e-31e1-4530-8f3e-216fe1600dd3"
API_ENDPOINT="https://4btsule96b.execute-api.us-east-1.amazonaws.com/dev"

echo "🛑 Cancelling stuck execution: $EXECUTION_ID"

# Get JWT token
echo "Getting authentication token..."
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_7ClH0e1NS \
  --client-id 6fepnj59rp7qup2k3n6uda5p19 \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "None" ]; then
    echo "❌ Failed to get authentication token"
    exit 1
fi

echo "✅ Got authentication token"

# Cancel the execution
echo "Cancelling execution..."
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$API_ENDPOINT/executions/$EXECUTION_ID/cancel"

echo ""
echo "✅ Cancel request sent. The execution should be cancelled shortly."