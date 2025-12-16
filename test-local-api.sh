#!/bin/bash

# Test Local API Endpoints
# This script tests the mock API server endpoints

API_BASE="http://localhost:8000"
TOKEN="Bearer test-token"

echo "🧪 Testing Local API Endpoints"
echo "=============================="

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s "$API_BASE/health" | jq '.'
echo ""

# Test get target accounts
echo "2. Testing GET /accounts/targets..."
curl -s -H "Authorization: $TOKEN" "$API_BASE/accounts/targets" | jq '.'
echo ""

# Test create target account
echo "3. Testing POST /accounts/targets..."
curl -s -X POST -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "accountId": "987654321098",
    "name": "Test Target Account",
    "description": "A test target account for multi-account setup",
    "crossAccountRoleArn": "arn:aws:iam::987654321098:role/DRSOrchestrationCrossAccountRole",
    "stagingAccountId": "555666777888"
  }' \
  "$API_BASE/accounts/targets" | jq '.'
echo ""

# Test get target accounts again (should show 2 accounts now)
echo "4. Testing GET /accounts/targets (should show 2 accounts)..."
curl -s -H "Authorization: $TOKEN" "$API_BASE/accounts/targets" | jq '.'
echo ""

# Test update target account
echo "5. Testing PUT /accounts/targets/987654321098..."
curl -s -X PUT -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Test Account",
    "description": "Updated description for test account"
  }' \
  "$API_BASE/accounts/targets/987654321098" | jq '.'
echo ""

# Test validate target account
echo "6. Testing POST /accounts/targets/987654321098/validate..."
curl -s -X POST -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  "$API_BASE/accounts/targets/987654321098/validate" | jq '.'
echo ""

# Test DRS quotas
echo "7. Testing GET /drs/quotas..."
curl -s -H "Authorization: $TOKEN" "$API_BASE/drs/quotas?accountId=123456789012" | jq '.'
echo ""

# Test tag sync
echo "8. Testing POST /drs/tag-sync..."
curl -s -X POST -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"accountId": "123456789012"}' \
  "$API_BASE/drs/tag-sync" | jq '.'
echo ""

# Test delete target account
echo "9. Testing DELETE /accounts/targets/987654321098..."
curl -s -X DELETE -H "Authorization: $TOKEN" "$API_BASE/accounts/targets/987654321098" | jq '.'
echo ""

# Final check - should be back to 1 account
echo "10. Final check - GET /accounts/targets (should show 1 account)..."
curl -s -H "Authorization: $TOKEN" "$API_BASE/accounts/targets" | jq '.'
echo ""

echo "✅ API testing complete!"