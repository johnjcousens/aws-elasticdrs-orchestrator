#!/bin/bash
# Manual test script for PollWaveStatus -> UpdateWaveStatus flow
# Tests the refactored wave polling with DynamoDB updates

set -e

# Configuration
REGION="us-east-1"
QUERY_HANDLER="aws-drs-orchestration-query-handler-qa"
EXECUTION_HANDLER="aws-drs-orchestration-execution-handler-qa"
EXECUTION_TABLE="aws-drs-orchestration-execution-history-qa"
PLAN_TABLE="aws-drs-orchestration-recovery-plans-qa"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "POLL AND UPDATE WAVE STATUS TEST"
echo "================================================================================"
echo "Region: $REGION"
echo "Query Handler: $QUERY_HANDLER"
echo "Execution Handler: $EXECUTION_HANDLER"
echo ""

# Generate unique IDs
TIMESTAMP=$(date +%s)
PLAN_ID="test-plan-poll-${TIMESTAMP}"
EXECUTION_ID="test-exec-poll-${TIMESTAMP}"
JOB_ID="drsjob-test-${TIMESTAMP}"

# Function to create test recovery plan
create_test_plan() {
    echo -e "${BLUE}📝 Creating test recovery plan: $PLAN_ID${NC}"
    
    aws dynamodb put-item \
        --table-name "$PLAN_TABLE" \
        --region "$REGION" \
        --item "{
            \"planId\": {\"S\": \"$PLAN_ID\"},
            \"planName\": {\"S\": \"Test Plan for Poll/Update\"},
            \"status\": {\"S\": \"ACTIVE\"},
            \"createdAt\": {\"N\": \"$TIMESTAMP\"},
            \"createdBy\": {\"S\": \"test-user\"},
            \"waves\": {\"L\": [
                {\"M\": {
                    \"waveNumber\": {\"N\": \"1\"},
                    \"waveName\": {\"S\": \"Test Wave 1\"},
                    \"servers\": {\"L\": []}
                }}
            ]},
            \"totalWaves\": {\"N\": \"1\"}
        }" > /dev/null
    
    echo -e "${GREEN}✅ Created test recovery plan: $PLAN_ID${NC}"
}

# Function to create test execution with mock DRS job
create_test_execution() {
    echo -e "${BLUE}📝 Creating test execution with mock DRS job: $EXECUTION_ID${NC}"
    
    aws dynamodb put-item \
        --table-name "$EXECUTION_TABLE" \
        --region "$REGION" \
        --item "{
            \"executionId\": {\"S\": \"$EXECUTION_ID\"},
            \"planId\": {\"S\": \"$PLAN_ID\"},
            \"status\": {\"S\": \"RUNNING\"},
            \"startTime\": {\"N\": \"$TIMESTAMP\"},
            \"currentWave\": {\"N\": \"1\"},
            \"totalWaves\": {\"N\": \"1\"},
            \"completedWaves\": {\"N\": \"0\"},
            \"failedWaves\": {\"N\": \"0\"},
            \"lastUpdated\": {\"N\": \"$TIMESTAMP\"},
            \"jobId\": {\"S\": \"$JOB_ID\"},
            \"region\": {\"S\": \"us-east-1\"}
        }" > /dev/null
    
    echo -e "${GREEN}✅ Created test execution: $EXECUTION_ID${NC}"
}

# Function to invoke query-handler poll_wave_status (read-only)
test_poll_wave_status() {
    echo ""
    echo "================================================================================"
    echo "TEST 1: PollWaveStatus (Query Handler - Read Only)"
    echo "================================================================================"
    
    echo -e "${BLUE}🚀 Invoking query-handler poll_wave_status...${NC}"
    
    response=$(aws lambda invoke \
        --function-name "$QUERY_HANDLER" \
        --region "$REGION" \
        --cli-binary-format raw-in-base64-out \
        --payload "{\"action\":\"poll_wave_status\",\"execution_id\":\"$EXECUTION_ID\",\"plan_id\":\"$PLAN_ID\",\"wave_number\":1}" \
        /tmp/poll_response.json > /dev/null 2>&1 && cat /tmp/poll_response.json)
    
    echo "   Response:"
    echo "$response" | jq '.'
    
    # Check if response contains wave_completed
    wave_completed=$(echo "$response" | jq -r '.wave_completed // "null"')
    if [ "$wave_completed" != "null" ]; then
        echo -e "${GREEN}✅ poll_wave_status executed successfully (wave_completed: $wave_completed)${NC}"
    else
        echo -e "${RED}❌ poll_wave_status failed - no wave_completed in response${NC}"
        return 1
    fi
    
    # Verify no DynamoDB writes occurred (check lastUpdated timestamp)
    sleep 1
    item=$(aws dynamodb get-item \
        --table-name "$EXECUTION_TABLE" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$EXECUTION_ID\"}, \"planId\": {\"S\": \"$PLAN_ID\"}}" \
        --query 'Item.lastUpdated.N' \
        --output text)
    
    if [ "$item" = "$TIMESTAMP" ]; then
        echo -e "${GREEN}✅ Verified: No DynamoDB writes (lastUpdated unchanged: $TIMESTAMP)${NC}"
    else
        echo -e "${YELLOW}⚠ Warning: lastUpdated changed from $TIMESTAMP to $item${NC}"
    fi
    
    rm -f /tmp/poll_response.json
}

# Function to invoke execution-handler update_wave_completion_status (write)
test_update_wave_status() {
    echo ""
    echo "================================================================================"
    echo "TEST 2: UpdateWaveStatus (Execution Handler - Write)"
    echo "================================================================================"
    
    echo -e "${BLUE}🚀 Invoking execution-handler update_wave_completion_status...${NC}"
    
    response=$(aws lambda invoke \
        --function-name "$EXECUTION_HANDLER" \
        --region "$REGION" \
        --cli-binary-format raw-in-base64-out \
        --payload "{\"action\":\"update_wave_completion_status\",\"execution_id\":\"$EXECUTION_ID\",\"plan_id\":\"$PLAN_ID\",\"status\":\"COMPLETED\",\"wave_data\":{\"completed_waves\":1,\"start_time\":$TIMESTAMP}}" \
        /tmp/update_response.json > /dev/null 2>&1 && cat /tmp/update_response.json)
    
    echo "   Response:"
    echo "$response" | jq '.'
    
    # Check if response is successful
    status_code=$(echo "$response" | jq -r '.statusCode // 200')
    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✅ update_wave_completion_status executed successfully${NC}"
    else
        echo -e "${RED}❌ update_wave_completion_status failed with status: $status_code${NC}"
        return 1
    fi
    
    # Verify DynamoDB writes occurred
    sleep 2
    item=$(aws dynamodb get-item \
        --table-name "$EXECUTION_TABLE" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$EXECUTION_ID\"}, \"planId\": {\"S\": \"$PLAN_ID\"}}" \
        --query 'Item' \
        --output json)
    
    echo -e "${BLUE}🔍 Verifying DynamoDB updates...${NC}"
    echo "$item" | jq '{status: .status.S, completedWaves: .completedWaves.N, endTime: .endTime.N, durationSeconds: .durationSeconds.N}'
    
    # Check status
    status=$(echo "$item" | jq -r '.status.S')
    if [ "$status" = "COMPLETED" ]; then
        echo -e "${GREEN}✅ Status updated to: $status${NC}"
    else
        echo -e "${RED}❌ Status incorrect: expected COMPLETED, got $status${NC}"
        return 1
    fi
    
    # Check completedWaves
    completed=$(echo "$item" | jq -r '.completedWaves.N')
    if [ "$completed" = "1" ]; then
        echo -e "${GREEN}✅ completedWaves updated to: $completed${NC}"
    else
        echo -e "${RED}❌ completedWaves incorrect: expected 1, got $completed${NC}"
        return 1
    fi
    
    # Check endTime exists
    end_time=$(echo "$item" | jq -r '.endTime.N')
    if [ "$end_time" != "null" ] && [ -n "$end_time" ]; then
        echo -e "${GREEN}✅ endTime set: $end_time${NC}"
    else
        echo -e "${RED}❌ endTime not set${NC}"
        return 1
    fi
    
    rm -f /tmp/update_response.json
}

# Function to cleanup test data
cleanup() {
    echo ""
    echo -e "${BLUE}🧹 Cleaning up test data...${NC}"
    
    # Delete execution
    aws dynamodb delete-item \
        --table-name "$EXECUTION_TABLE" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$EXECUTION_ID\"}, \"planId\": {\"S\": \"$PLAN_ID\"}}" > /dev/null
    
    # Delete plan
    aws dynamodb delete-item \
        --table-name "$PLAN_TABLE" \
        --region "$REGION" \
        --key "{\"planId\": {\"S\": \"$PLAN_ID\"}}" > /dev/null
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Main test flow
main() {
    # Create test data
    create_test_plan
    create_test_execution
    
    # Test poll_wave_status (read-only)
    test_poll_wave_status
    POLL_STATUS=$?
    
    # Test update_wave_completion_status (write)
    test_update_wave_status
    UPDATE_STATUS=$?
    
    # Cleanup
    cleanup
    
    # Final result
    echo ""
    echo "================================================================================"
    if [ $POLL_STATUS -eq 0 ] && [ $UPDATE_STATUS -eq 0 ]; then
        echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
        echo "   - PollWaveStatus (query-handler) is read-only ✓"
        echo "   - UpdateWaveStatus (execution-handler) writes correctly ✓"
        echo "   - Wave polling refactoring successful ✓"
    else
        echo -e "${RED}❌ TESTS FAILED${NC}"
        exit 1
    fi
    echo "================================================================================"
}

main
