#!/bin/bash

echo "=== Testing API Flow ==="

# Step 1: Get Cognito token
echo "1. Getting Cognito token..."
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id 5bpcd63knd89c4pnbneth6u21j \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=***REMOVED***,PASSWORD=***REMOVED*** \
  --query 'AuthenticationResult.IdToken' \
  --output text \
  --region us-east-1)

echo "Token obtained: ${TOKEN:0:50}..."

# Step 2: Make API call and save response
echo "2. Making API call..."
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://baju5jevwe.execute-api.us-east-1.amazonaws.com/dev/drs/source-servers?region=us-west-2" \
  > /tmp/api-response.json

# Step 3: Analyze response
echo "3. Response size: $(wc -c < /tmp/api-response.json) bytes"
echo "4. Response structure:"
jq 'keys' /tmp/api-response.json

echo "5. Servers count:"
jq '.servers | length' /tmp/api-response.json

echo "6. First server keys:"
jq '.servers[0] | keys' /tmp/api-response.json

echo "7. First server hardware:"
jq '.servers[0].hardware' /tmp/api-response.json

echo "8. Hardware field types:"
jq '.servers[0].hardware | to_entries | map({key: .key, type: (.value | type), value: .value})' /tmp/api-response.json

echo "9. Testing nullish coalescing logic:"
TOTAL_CORES=$(jq -r '.servers[0].hardware.totalCores // "Unknown"' /tmp/api-response.json)
RAM_GIB=$(jq -r '.servers[0].hardware.ramGiB // "Unknown"' /tmp/api-response.json)
TOTAL_DISK_GIB=$(jq -r '.servers[0].hardware.totalDiskGiB // "Unknown"' /tmp/api-response.json)

echo "CPU: $TOTAL_CORES cores"
echo "RAM: $RAM_GIB GiB"
echo "Disk: $TOTAL_DISK_GIB GiB"

echo "10. All servers hardware summary:"
jq -r '.servers[] | "Server: \(.hostname) | CPU: \(.hardware.totalCores // "Unknown") cores | RAM: \(.hardware.ramGiB // "Unknown") GiB | Disk: \(.hardware.totalDiskGiB // "Unknown") GiB"' /tmp/api-response.json

echo "=== Test Complete ==="