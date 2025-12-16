#!/bin/bash

echo "=== Testing Complete Frontend Data Flow ==="

# Step 1: Get token
echo "1. Getting Cognito token..."
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id 5bpcd63knd89c4pnbneth6u21j \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD=TestPassword123! \
  --query 'AuthenticationResult.IdToken' \
  --output text \
  --region us-east-1)

if [ -z "$TOKEN" ]; then
  echo "ERROR: Failed to get token"
  exit 1
fi

echo "Token obtained: ${TOKEN:0:50}..."

# Step 2: Make API call exactly like frontend
echo "2. Making API call like frontend..."
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://baju5jevwe.execute-api.us-east-1.amazonaws.com/dev/drs/source-servers?region=us-west-2")

echo "3. Response received, size: $(echo "$RESPONSE" | wc -c) bytes"

# Step 3: Parse response like frontend API client
echo "4. Parsing response like frontend API client..."
echo "$RESPONSE" > /tmp/api-response.json

# Check if response has expected structure
SERVERS_COUNT=$(jq '.servers | length' /tmp/api-response.json 2>/dev/null || echo "0")
echo "Servers count: $SERVERS_COUNT"

if [ "$SERVERS_COUNT" = "0" ] || [ "$SERVERS_COUNT" = "null" ]; then
  echo "ERROR: No servers found in response"
  echo "Response keys: $(jq 'keys' /tmp/api-response.json)"
  exit 1
fi

# Step 4: Test hardware data extraction like ServerListItem component
echo "5. Testing hardware data extraction..."
for i in $(seq 0 $((SERVERS_COUNT-1))); do
  HOSTNAME=$(jq -r ".servers[$i].hostname" /tmp/api-response.json)
  HARDWARE_EXISTS=$(jq ".servers[$i].hardware != null" /tmp/api-response.json)
  
  if [ "$HARDWARE_EXISTS" = "true" ]; then
    TOTAL_CORES=$(jq -r ".servers[$i].hardware.totalCores // \"Unknown\"" /tmp/api-response.json)
    RAM_GIB=$(jq -r ".servers[$i].hardware.ramGiB // \"Unknown\"" /tmp/api-response.json)
    TOTAL_DISK_GIB=$(jq -r ".servers[$i].hardware.totalDiskGiB // \"Unknown\"" /tmp/api-response.json)
    
    echo "Server $i ($HOSTNAME): CPU: $TOTAL_CORES cores | RAM: $RAM_GIB GiB | Disk: $TOTAL_DISK_GIB GiB"
  else
    echo "Server $i ($HOSTNAME): NO HARDWARE DATA"
  fi
done

# Step 5: Test the exact logic from ServerListItem component
echo "6. Testing ServerListItem logic..."
FIRST_SERVER_HARDWARE=$(jq '.servers[0].hardware' /tmp/api-response.json)
echo "First server hardware object: $FIRST_SERVER_HARDWARE"

# Test the conditional logic
if [ "$FIRST_SERVER_HARDWARE" != "null" ]; then
  echo "✅ Hardware object exists (truthy)"
  
  # Test individual field access
  TOTAL_CORES=$(jq -r '.servers[0].hardware.totalCores' /tmp/api-response.json)
  RAM_GIB=$(jq -r '.servers[0].hardware.ramGiB' /tmp/api-response.json)
  TOTAL_DISK_GIB=$(jq -r '.servers[0].hardware.totalDiskGiB' /tmp/api-response.json)
  
  echo "Individual fields:"
  echo "  totalCores: $TOTAL_CORES (type: $(echo "$TOTAL_CORES" | jq -r 'type'))"
  echo "  ramGiB: $RAM_GIB (type: $(echo "$RAM_GIB" | jq -r 'type'))"
  echo "  totalDiskGiB: $TOTAL_DISK_GIB (type: $(echo "$TOTAL_DISK_GIB" | jq -r 'type'))"
  
  # Test the || fallback logic
  CORES_WITH_FALLBACK=$(jq -r '.servers[0].hardware.totalCores // "Unknown"' /tmp/api-response.json)
  RAM_WITH_FALLBACK=$(jq -r '.servers[0].hardware.ramGiB // "Unknown"' /tmp/api-response.json)
  DISK_WITH_FALLBACK=$(jq -r '.servers[0].hardware.totalDiskGiB // "Unknown"' /tmp/api-response.json)
  
  echo "With fallback logic:"
  echo "  CPU: $CORES_WITH_FALLBACK cores"
  echo "  RAM: $RAM_WITH_FALLBACK GiB"
  echo "  Disk: $DISK_WITH_FALLBACK GiB"
  
else
  echo "❌ Hardware object is null or missing"
fi

# Step 6: Test the exact DEBUG output format from ServerListItem
echo "7. Testing DEBUG output format..."
HARDWARE_JSON=$(jq -c '.servers[0].hardware' /tmp/api-response.json)
TOTAL_CORES=$(jq -r '.servers[0].hardware.totalCores' /tmp/api-response.json)
RAM_GIB=$(jq -r '.servers[0].hardware.ramGiB' /tmp/api-response.json)
TOTAL_DISK_GIB=$(jq -r '.servers[0].hardware.totalDiskGiB' /tmp/api-response.json)

echo "DEBUG: hardware exists=true | hardware=$HARDWARE_JSON | totalCores=$TOTAL_CORES | ramGiB=$RAM_GIB | totalDiskGiB=$TOTAL_DISK_GIB"

echo "=== Test Complete ==="