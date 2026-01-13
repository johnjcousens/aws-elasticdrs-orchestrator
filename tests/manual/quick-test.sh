#!/bin/bash
# Quick test of critical endpoints

TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id ***REMOVED*** \
  --client-id ***REMOVED*** \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=***REMOVED***,PASSWORD=***REMOVED*** \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text 2>/dev/null)

BASE_URL="https://***REMOVED***.execute-api.us-east-1.amazonaws.com/test"

echo "🔐 Testing critical endpoints..."

# Test protection groups
echo -n "Protection Groups: "
STATUS=$(curl -s -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL/protection-groups" -o /dev/null)
echo "[$STATUS]"

# Test recovery plans  
echo -n "Recovery Plans: "
STATUS=$(curl -s -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL/recovery-plans" -o /dev/null)
echo "[$STATUS]"

# Test executions
echo -n "Executions: "
STATUS=$(curl -s -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL/executions" -o /dev/null)
echo "[$STATUS]"

# Test DRS source servers with region
echo -n "DRS Source Servers: "
STATUS=$(curl -s -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL/drs/source-servers?region=us-west-2" -o /dev/null)
echo "[$STATUS]"

# Test target accounts
echo -n "Target Accounts: "
STATUS=$(curl -s -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL/accounts/targets" -o /dev/null)
echo "[$STATUS]"

echo "✅ Quick test complete"