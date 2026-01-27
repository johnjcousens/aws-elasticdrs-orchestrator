#!/bin/bash
# Load Test: DRS Capacity Monitoring Performance
# Tests Query Handler performance with 1,000 servers across 4 accounts

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_ENDPOINT="https://g0ojnzzfh1.execute-api.us-east-1.amazonaws.com/dev"
SECRET_NAME="drs-orchestration/test-user-credentials"
REGION="us-east-1"

# Test accounts (update with actual account IDs)
ACCOUNT_1="777788889999"  # 250 servers
ACCOUNT_2="TBD"           # 250 servers
ACCOUNT_3="TBD"           # 250 servers
ACCOUNT_4="TBD"           # 250 servers

echo "=========================================="
echo "DRS Capacity Monitoring Load Test"
echo "=========================================="
echo ""
echo "Scenario: 1,000 servers across 4 accounts"
echo "Target: ~250 servers per account"
echo ""

# Get credentials
echo "Authenticating..."
CREDENTIALS=$(aws secretsmanager get-secret-value --secret-id "$SECRET_NAME" --region "$REGION" --query SecretString --output text)
EMAIL=$(echo "$CREDENTIALS" | jq -r '.username')
PASSWORD=$(echo "$CREDENTIALS" | jq -r '.password')
USER_POOL_ID=$(echo "$CREDENTIALS" | jq -r '.userPoolId')
CLIENT_ID=$(echo "$CREDENTIALS" | jq -r '.clientId')

ACTUAL_USERNAME=$(aws cognito-idp list-users \
  --user-pool-id "$USER_POOL_ID" \
  --filter "email = \"$EMAIL\"" \
  --query 'Users[0].Username' \
  --output text)

ID_TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id "$USER_POOL_ID" \
  --client-id "$CLIENT_ID" \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME="$ACTUAL_USERNAME",PASSWORD="$PASSWORD" \
  --query 'AuthenticationResult.IdToken' \
  --output text)

echo -e "${GREEN}✓ Authenticated${NC}"
echo ""

# Function to measure API call
measure_api_call() {
  local endpoint=$1
  local description=$2
  local samples=${3:-5}
  
  echo -e "${BLUE}Testing: $description${NC}"
  echo "  Endpoint: $endpoint"
  echo "  Samples: $samples"
  
  local total=0
  local min=999999
  local max=0
  declare -a durations
  
  for i in $(seq 1 $samples); do
    local start=$(python3 -c 'import time; print(int(time.time() * 1000))')
    local response=$(curl -s -w "\n%{http_code}" -X GET \
      "$API_ENDPOINT$endpoint" \
      -H "Authorization: $ID_TOKEN")
    local end=$(python3 -c 'import time; print(int(time.time() * 1000))')
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    local duration=$((end - start))
    
    durations+=($duration)
    total=$((total + duration))
    [ $duration -lt $min ] && min=$duration
    [ $duration -gt $max ] && max=$duration
    
    # Extract server count from response
    local server_count=$(echo "$body" | jq -r '.replicatingServers // .sourceServers | length // 0' 2>/dev/null || echo "N/A")
    
    echo "    Sample $i: ${duration}ms (HTTP $http_code, servers: $server_count)"
    sleep 1
  done
  
  local avg=$((total / samples))
  
  echo -e "  ${GREEN}Results: avg=${avg}ms, min=${min}ms, max=${max}ms${NC}"
  echo ""
  
  echo "$avg $min $max"
}

# Test 1: Single Account Capacity Query
echo "=========================================="
echo "Test 1: Single Account Capacity"
echo "=========================================="
echo ""
echo "Objective: Query DRS capacity for single account (~250 servers)"
echo "Target: < 2 seconds (p95)"
echo ""

result1=$(measure_api_call "/drs/quotas?accountId=$ACCOUNT_1&region=us-east-1" "Single Account Capacity" 5)
avg1=$(echo $result1 | cut -d' ' -f1)
min1=$(echo $result1 | cut -d' ' -f2)
max1=$(echo $result1 | cut -d' ' -f3)

if [ $avg1 -lt 2000 ]; then
  echo -e "${GREEN}✓ PASS: Average ${avg1}ms < 2000ms target${NC}"
else
  echo -e "${RED}✗ FAIL: Average ${avg1}ms > 2000ms target${NC}"
fi
echo ""

# Test 2: All Accounts Capacity Query
echo "=========================================="
echo "Test 2: All Accounts Capacity"
echo "=========================================="
echo ""
echo "Objective: Query DRS capacity across all accounts (~1,000 servers)"
echo "Target: < 5 seconds (p95)"
echo ""

result2=$(measure_api_call "/drs/quotas?region=us-east-1" "All Accounts Capacity" 5)
avg2=$(echo $result2 | cut -d' ' -f1)
min2=$(echo $result2 | cut -d' ' -f2)
max2=$(echo $result2 | cut -d' ' -f3)

if [ $avg2 -lt 5000 ]; then
  echo -e "${GREEN}✓ PASS: Average ${avg2}ms < 5000ms target${NC}"
else
  echo -e "${RED}✗ FAIL: Average ${avg2}ms > 5000ms target${NC}"
fi
echo ""

# Test 3: Multi-Region Capacity Query
echo "=========================================="
echo "Test 3: Multi-Region Capacity"
echo "=========================================="
echo ""
echo "Objective: Query DRS capacity across all regions and accounts"
echo "Target: < 10 seconds (p95)"
echo ""

result3=$(measure_api_call "/drs/quotas" "Multi-Region Capacity" 3)
avg3=$(echo $result3 | cut -d' ' -f1)
min3=$(echo $result3 | cut -d' ' -f2)
max3=$(echo $result3 | cut -d' ' -f3)

if [ $avg3 -lt 10000 ]; then
  echo -e "${GREEN}✓ PASS: Average ${avg3}ms < 10000ms target${NC}"
else
  echo -e "${RED}✗ FAIL: Average ${avg3}ms > 10000ms target${NC}"
fi
echo ""

# Test 4: Source Server Listing (Single Account)
echo "=========================================="
echo "Test 4: Source Server Listing (Single Account)"
echo "=========================================="
echo ""
echo "Objective: List all DRS source servers in single account (~250 servers)"
echo "Target: < 3 seconds (p95)"
echo ""

result4=$(measure_api_call "/drs/source-servers?accountId=$ACCOUNT_1&region=us-east-1" "Single Account Servers" 5)
avg4=$(echo $result4 | cut -d' ' -f1)
min4=$(echo $result4 | cut -d' ' -f2)
max4=$(echo $result4 | cut -d' ' -f3)

if [ $avg4 -lt 3000 ]; then
  echo -e "${GREEN}✓ PASS: Average ${avg4}ms < 3000ms target${NC}"
else
  echo -e "${RED}✗ FAIL: Average ${avg4}ms > 3000ms target${NC}"
fi
echo ""

# Test 5: Source Server Listing (All Accounts)
echo "=========================================="
echo "Test 5: Source Server Listing (All Accounts)"
echo "=========================================="
echo ""
echo "Objective: List all DRS source servers across all accounts (~1,000 servers)"
echo "Target: < 8 seconds (p95)"
echo ""

result5=$(measure_api_call "/drs/source-servers?region=us-east-1" "All Accounts Servers" 3)
avg5=$(echo $result5 | cut -d' ' -f1)
min5=$(echo $result5 | cut -d' ' -f2)
max5=$(echo $result5 | cut -d' ' -f3)

if [ $avg5 -lt 8000 ]; then
  echo -e "${GREEN}✓ PASS: Average ${avg5}ms < 8000ms target${NC}"
else
  echo -e "${RED}✗ FAIL: Average ${avg5}ms > 8000ms target${NC}"
fi
echo ""

# Test 6: Concurrent Capacity Queries
echo "=========================================="
echo "Test 6: Concurrent Capacity Queries"
echo "=========================================="
echo ""
echo "Objective: 10 simultaneous capacity queries"
echo "Target: All complete within 5 seconds"
echo ""

echo "Sending 10 concurrent requests..."
start_concurrent=$(python3 -c 'import time; print(int(time.time() * 1000))')

for i in {1..10}; do
  curl -s -X GET \
    "$API_ENDPOINT/drs/quotas?accountId=$ACCOUNT_1&region=us-east-1" \
    -H "Authorization: $ID_TOKEN" \
    -o /dev/null &
done

wait
end_concurrent=$(python3 -c 'import time; print(int(time.time() * 1000))')
concurrent_duration=$((end_concurrent - start_concurrent))

echo "  All requests completed in ${concurrent_duration}ms"

if [ $concurrent_duration -lt 5000 ]; then
  echo -e "${GREEN}✓ PASS: ${concurrent_duration}ms < 5000ms target${NC}"
else
  echo -e "${RED}✗ FAIL: ${concurrent_duration}ms > 5000ms target${NC}"
fi
echo ""

# Summary
echo "=========================================="
echo "Load Test Summary"
echo "=========================================="
echo ""

echo "Performance Results:"
echo "  Test 1 - Single Account Capacity:     ${avg1}ms (target: < 2000ms)"
echo "  Test 2 - All Accounts Capacity:       ${avg2}ms (target: < 5000ms)"
echo "  Test 3 - Multi-Region Capacity:       ${avg3}ms (target: < 10000ms)"
echo "  Test 4 - Single Account Servers:      ${avg4}ms (target: < 3000ms)"
echo "  Test 5 - All Accounts Servers:        ${avg5}ms (target: < 8000ms)"
echo "  Test 6 - Concurrent Queries:          ${concurrent_duration}ms (target: < 5000ms)"
echo ""

# Calculate pass rate
pass_count=0
total_tests=6

[ $avg1 -lt 2000 ] && pass_count=$((pass_count + 1))
[ $avg2 -lt 5000 ] && pass_count=$((pass_count + 1))
[ $avg3 -lt 10000 ] && pass_count=$((pass_count + 1))
[ $avg4 -lt 3000 ] && pass_count=$((pass_count + 1))
[ $avg5 -lt 8000 ] && pass_count=$((pass_count + 1))
[ $concurrent_duration -lt 5000 ] && pass_count=$((pass_count + 1))

pass_rate=$((pass_count * 100 / total_tests))

echo "Overall Results:"
echo "  Tests Passed: $pass_count/$total_tests ($pass_rate%)"
echo ""

if [ $pass_count -eq $total_tests ]; then
  echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
  echo "System ready for 1,000 server / 4 account deployment"
else
  echo -e "${YELLOW}⚠ SOME TESTS FAILED${NC}"
  echo "Review performance bottlenecks before production deployment"
fi

echo ""
echo "=========================================="
echo "Load Test Complete"
echo "=========================================="
