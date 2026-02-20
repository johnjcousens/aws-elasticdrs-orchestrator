#!/bin/bash

# Wave Completion Status Update Test Script
# Tests the update_wave_completion_status() function in execution-handler

set -e

# Configuration
FUNCTION_NAME="aws-drs-orchestration-execution-handler-qa"
REGION="us-east-1"
TABLE_NAME="aws-drs-orchestration-execution-history-qa"
TEST_EXEC_ID="test-exec-001"
TEST_PLAN_ID="test-plan-001"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Wave Completion Status Update Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity --region $REGION > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured or expired${NC}"
    echo -e "${YELLOW}Please run: aws login${NC}"
    exit 1
fi
echo -e "${GREEN}✅ AWS credentials valid${NC}"
echo ""

# Create test execution record
echo -e "${YELLOW}Creating test execution record...${NC}"
CURRENT_TIME=$(date +%s)
aws dynamodb put-item \
  --table-name $TABLE_NAME \
  --region $REGION \
  --item "{
    \"executionId\": {\"S\": \"$TEST_EXEC_ID\"},
    \"planId\": {\"S\": \"$TEST_PLAN_ID\"},
    \"status\": {\"S\": \"RUNNING\"},
    \"startTime\": {\"N\": \"$CURRENT_TIME\"},
    \"lastUpdated\": {\"N\": \"$CURRENT_TIME\"}
  }" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test execution record created${NC}"
else
    echo -e "${RED}❌ Failed to create test execution record${NC}"
    exit 1
fi
echo ""

# Function to run a test
run_test() {
    local test_name=$1
    local test_file=$2
    local expected_status=$3
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Test: $test_name${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Invoke Lambda
    echo -e "${YELLOW}Invoking Lambda function...${NC}"
    aws lambda invoke \
      --function-name $FUNCTION_NAME \
      --region $REGION \
      --payload file://$test_file \
      --cli-binary-format raw-in-base64-out \
      response-$test_name.json > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Lambda invocation successful${NC}"
        
        # Display response
        echo -e "${YELLOW}Response:${NC}"
        cat response-$test_name.json | jq .
        echo ""
        
        # Verify DynamoDB update
        echo -e "${YELLOW}Verifying DynamoDB update...${NC}"
        sleep 2  # Wait for DynamoDB consistency
        
        ACTUAL_STATUS=$(aws dynamodb get-item \
          --table-name $TABLE_NAME \
          --region $REGION \
          --key "{\"executionId\": {\"S\": \"$TEST_EXEC_ID\"}, \"planId\": {\"S\": \"$TEST_PLAN_ID\"}}" \
          --query 'Item.status.S' \
          --output text)
        
        if [ "$ACTUAL_STATUS" == "$expected_status" ]; then
            echo -e "${GREEN}✅ Status correctly updated to $expected_status${NC}"
            
            # Display full record
            echo -e "${YELLOW}Execution record:${NC}"
            aws dynamodb get-item \
              --table-name $TABLE_NAME \
              --region $REGION \
              --key "{\"executionId\": {\"S\": \"$TEST_EXEC_ID\"}, \"planId\": {\"S\": \"$TEST_PLAN_ID\"}}" \
              --output json | jq '.Item | {
                status: .status.S,
                lastUpdated: .lastUpdated.N,
                endTime: .endTime.N,
                pausedBeforeWave: .pausedBeforeWave.N,
                completedWaves: .completedWaves.N,
                failedWaves: .failedWaves.N,
                errorMessage: .errorMessage.S,
                errorCode: .errorCode.S,
                durationSeconds: .durationSeconds.N
              }'
        else
            echo -e "${RED}❌ Status mismatch: expected $expected_status, got $ACTUAL_STATUS${NC}"
        fi
    else
        echo -e "${RED}❌ Lambda invocation failed${NC}"
        cat response-$test_name.json
    fi
    
    echo ""
}

# Run all tests
run_test "cancelled" "tests/manual/wave-completion-test-events/test-cancelled.json" "CANCELLED"
run_test "paused" "tests/manual/wave-completion-test-events/test-paused.json" "PAUSED"
run_test "completed" "tests/manual/wave-completion-test-events/test-completed.json" "COMPLETED"
run_test "failed" "tests/manual/wave-completion-test-events/test-failed.json" "FAILED"

# Cleanup
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Cleanup${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}Deleting test execution record...${NC}"
aws dynamodb delete-item \
  --table-name $TABLE_NAME \
  --region $REGION \
  --key "{\"executionId\": {\"S\": \"$TEST_EXEC_ID\"}, \"planId\": {\"S\": \"$TEST_PLAN_ID\"}}" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test execution record deleted${NC}"
else
    echo -e "${RED}❌ Failed to delete test execution record${NC}"
fi

echo -e "${YELLOW}Deleting response files...${NC}"
rm -f response-*.json
echo -e "${GREEN}✅ Response files deleted${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All tests completed!${NC}"
echo -e "${BLUE}========================================${NC}"
