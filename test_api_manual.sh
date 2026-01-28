#!/bin/bash
# Manual API Testing Script for Test Environment
# Run this to verify the Protection Groups API returns sourceServerIds

echo "🔐 Getting Cognito credentials..."
SECRET=$(aws secretsmanager get-secret-value \
  --secret-id arn:aws:secretsmanager:us-east-1:777788889999:secret:drs-orchestration/test-user-credentials-vV4S44 \
  --region us-east-1 \
  --query 'SecretString' \
  --output text)

USERNAME=$(echo $SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['username'])")
PASSWORD=$(echo $SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['password'])")
USER_POOL_ID=$(echo $SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['userPoolId'])")
CLIENT_ID=$(echo $SECRET | python3 -c "import sys, json; print(json.load(sys.stdin)['clientId'])")

echo "Username: $USERNAME"
echo "User Pool: $USER_POOL_ID"
echo ""

echo "🔑 Authenticating with Cognito..."
AUTH_RESPONSE=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id $USER_POOL_ID \
  --client-id $CLIENT_ID \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=$USERNAME,PASSWORD=$PASSWORD \
  --region us-east-1)

ID_TOKEN=$(echo $AUTH_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['AuthenticationResult']['IdToken'])")

echo "✅ Authenticated successfully"
echo ""

echo "📡 Testing GET /protection-groups..."
curl -s -X GET \
  "https://q9hfc15oh1.execute-api.us-east-1.amazonaws.com/test/protection-groups" \
  -H "Authorization: $ID_TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool

echo ""
echo "✅ Test complete"
