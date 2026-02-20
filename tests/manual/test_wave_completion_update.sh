#!/bin/bash
# Manual test script for update_wave_completion_status() function
# Tests wave completion update via direct Lambda invocation

set -e

# Configuration
REGION="us-east-1"
LAMBDA_FUNCTION="aws-drs-orchestration-execution-handler-qa"
TABLE_NAME="aws-drs-orchestration-execution-history-qa"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "WAVE COMPLETION STATUS UPDATE TESTS"
echo "================================================================================"
echo "Region: $REGION"
echo "Lambda Function: $LAMBDA_FUNCTION"
echo "DynamoDB Table: $TABLE_NAME"
echo ""

# Function to create test execution
create_test_execution() {
    local execution_id=$1
    local plan_id=$2
    local start_time=$(date +%s)
    
    echo -e "${BLUE}📝 Creating test execution: $execution_id${NC}"
    
    aws dynamodb put-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --item "{
            \"executionId\": {\"S\": \"$execution_id\"},
            \"planId\": {\"S\": \"$plan_id\"},
            \"status\": {\"S\": \"RUNNING\"},
            \"startTime\": {\"N\": \"$start_time\"},
            \"currentWave\": {\"N\": \"1\"},
            \"totalWaves\": {\"N\": \"3\"},
            \"completedWaves\": {\"N\": \"0\"},
            \"failedWaves\": {\"N\": \"0\"},
            \"lastUpdated\": {\"N\": \"$start_time\"}
        }" > /dev/null
    
    echo -e "${GREEN}✅ Created test execution: $execution_id${NC}"
    echo "$start_time"
}

# Function to invoke Lambda
invoke_lambda() {
    local payload=$1
    local output_file="/tmp/lambda_response_$$.json"
    
    echo -e "${BLUE}🚀 Invoking Lambda...${NC}"
    echo "   Payload: $payload"
    
    # Create temporary file for payload
    local payload_file="/tmp/lambda_payload_$$.json"
    echo "$payload" > "$payload_file"
    
    aws lambda invoke \
        --function-name "$LAMBDA_FUNCTION" \
        --region "$REGION" \
        --payload "file://$payload_file" \
        "$output_file" > /dev/null
    
    cat "$output_file"
    rm -f "$output_file" "$payload_file"
}

# Function to get execution from DynamoDB
get_execution() {
    local execution_id=$1
    local plan_id=$2
    
    aws dynamodb get-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$execution_id\"}, \"planId\": {\"S\": \"$plan_id\"}}" \
        --query 'Item' \
        --output json
}

# Function to cleanup test execution
cleanup_test_execution() {
    local execution_id=$1
    local plan_id=$2
    
    echo -e "${BLUE}🧹 Cleaning up test execution: $execution_id${NC}"
    
    aws dynamodb delete-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$execution_id\"}, \"planId\": {\"S\": \"$plan_id\"}}" > /dev/null
    
    echo -e "${GREEN}✅ Deleted test execution: $execution_id${NC}"
}

# Test 1: CANCELLED Status
test_cancelled_status() {
    echo ""
    echo "================================================================================"
    echo "TEST 1: CANCELLED Status"
    echo "================================================================================"
    
    local execution_id="test-exec-cancelled-001"
    local plan_id="test-plan-001"
    
    # Create test execution
    start_time=$(create_test_execution "$execution_id" "$plan_id")
    
    # Invoke Lambda
    payload="{\"action\": \"update_wave_completion_status\", \"execution_id\": \"$execution_id\", \"plan_id\": \"$plan_id\", \"status\": \"CANCELLED\"}"
    response=$(invoke_lambda "$payload")
    echo "   Response: $response"
    
    # Wait for DynamoDB consistency
    sleep 2
    
    # Verify DynamoDB update
    echo -e "${BLUE}🔍 Verifying execution status...${NC}"
    item=$(get_execution "$execution_id" "$plan_id")
    echo "   Full execution record:"
    echo "$item" | jq '.'
    
    # Check status
    status=$(echo "$item" | jq -r '.status.S')
    if [ "$status" = "CANCELLED" ]; then
        echo -e "${GREEN}✅ Status correct: $status${NC}"
    else
        echo -e "${RED}❌ Status incorrect: expected CANCELLED, got $status${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Check endTime exists
    end_time=$(echo "$item" | jq -r '.endTime.N')
    if [ "$end_time" != "null" ] && [ -n "$end_time" ]; then
        echo -e "${GREEN}✅ endTime set: $end_time${NC}"
    else
        echo -e "${RED}❌ endTime not set${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Cleanup
    cleanup_test_execution "$execution_id" "$plan_id"
    
    echo -e "${GREEN}✅ TEST 1 PASSED: CANCELLED status update works correctly${NC}"
}

# Test 2: PAUSED Status
test_paused_status() {
    echo ""
    echo "================================================================================"
    echo "TEST 2: PAUSED Status"
    echo "================================================================================"
    
    local execution_id="test-exec-paused-001"
    local plan_id="test-plan-001"
    
    # Create test execution
    start_time=$(create_test_execution "$execution_id" "$plan_id")
    
    # Invoke Lambda
    payload="{\"action\": \"update_wave_completion_status\", \"execution_id\": \"$execution_id\", \"plan_id\": \"$plan_id\", \"status\": \"PAUSED\", \"wave_data\": {\"paused_before_wave\": 2}}"
    response=$(invoke_lambda "$payload")
    echo "   Response: $response"
    
    # Wait for DynamoDB consistency
    sleep 2
    
    # Verify DynamoDB update
    echo -e "${BLUE}🔍 Verifying execution status...${NC}"
    item=$(get_execution "$execution_id" "$plan_id")
    echo "   Full execution record:"
    echo "$item" | jq '.'
    
    # Check status
    status=$(echo "$item" | jq -r '.status.S')
    if [ "$status" = "PAUSED" ]; then
        echo -e "${GREEN}✅ Status correct: $status${NC}"
    else
        echo -e "${RED}❌ Status incorrect: expected PAUSED, got $status${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Check pausedBeforeWave
    paused_wave=$(echo "$item" | jq -r '.pausedBeforeWave.N')
    if [ "$paused_wave" = "2" ]; then
        echo -e "${GREEN}✅ pausedBeforeWave correct: $paused_wave${NC}"
    else
        echo -e "${RED}❌ pausedBeforeWave incorrect: expected 2, got $paused_wave${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Cleanup
    cleanup_test_execution "$execution_id" "$plan_id"
    
    echo -e "${GREEN}✅ TEST 2 PASSED: PAUSED status update works correctly${NC}"
}

# Test 3: COMPLETED Status
test_completed_status() {
    echo ""
    echo "================================================================================"
    echo "TEST 3: COMPLETED Status"
    echo "================================================================================"
    
    local execution_id="test-exec-completed-001"
    local plan_id="test-plan-001"
    
    # Create test execution
    start_time=$(create_test_execution "$execution_id" "$plan_id")
    
    # Invoke Lambda
    payload="{\"action\": \"update_wave_completion_status\", \"execution_id\": \"$execution_id\", \"plan_id\": \"$plan_id\", \"status\": \"COMPLETED\", \"wave_data\": {\"completed_waves\": 3, \"start_time\": $start_time}}"
    response=$(invoke_lambda "$payload")
    echo "   Response: $response"
    
    # Wait for DynamoDB consistency
    sleep 2
    
    # Verify DynamoDB update
    echo -e "${BLUE}🔍 Verifying execution status...${NC}"
    item=$(get_execution "$execution_id" "$plan_id")
    echo "   Full execution record:"
    echo "$item" | jq '.'
    
    # Check status
    status=$(echo "$item" | jq -r '.status.S')
    if [ "$status" = "COMPLETED" ]; then
        echo -e "${GREEN}✅ Status correct: $status${NC}"
    else
        echo -e "${RED}❌ Status incorrect: expected COMPLETED, got $status${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Check endTime exists
    end_time=$(echo "$item" | jq -r '.endTime.N')
    if [ "$end_time" != "null" ] && [ -n "$end_time" ]; then
        echo -e "${GREEN}✅ endTime set: $end_time${NC}"
    else
        echo -e "${RED}❌ endTime not set${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Check completedWaves
    completed_waves=$(echo "$item" | jq -r '.completedWaves.N')
    if [ "$completed_waves" = "3" ]; then
        echo -e "${GREEN}✅ completedWaves correct: $completed_waves${NC}"
    else
        echo -e "${RED}❌ completedWaves incorrect: expected 3, got $completed_waves${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Check durationSeconds exists
    duration=$(echo "$item" | jq -r '.durationSeconds.N')
    if [ "$duration" != "null" ] && [ -n "$duration" ] && [ "$duration" -gt 0 ]; then
        echo -e "${GREEN}✅ durationSeconds set: $duration${NC}"
    else
        echo -e "${RED}❌ durationSeconds not set or invalid${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Cleanup
    cleanup_test_execution "$execution_id" "$plan_id"
    
    echo -e "${GREEN}✅ TEST 3 PASSED: COMPLETED status update works correctly${NC}"
}

# Test 4: FAILED Status
test_failed_status() {
    echo ""
    echo "================================================================================"
    echo "TEST 4: FAILED Status"
    echo "================================================================================"
    
    local execution_id="test-exec-failed-001"
    local plan_id="test-plan-001"
    
    # Create test execution
    start_time=$(create_test_execution "$execution_id" "$plan_id")
    
    # Invoke Lambda
    payload="{\"action\": \"update_wave_completion_status\", \"execution_id\": \"$execution_id\", \"plan_id\": \"$plan_id\", \"status\": \"FAILED\", \"wave_data\": {\"error\": \"DRS job failed: LaunchFailed\", \"error_code\": \"LAUNCH_FAILED\", \"failed_waves\": 1, \"start_time\": $start_time}}"
    response=$(invoke_lambda "$payload")
    echo "   Response: $response"
    
    # Wait for DynamoDB consistency
    sleep 2
    
    # Verify DynamoDB update
    echo -e "${BLUE}🔍 Verifying execution status...${NC}"
    item=$(get_execution "$execution_id" "$plan_id")
    echo "   Full execution record:"
    echo "$item" | jq '.'
    
    # Check status
    status=$(echo "$item" | jq -r '.status.S')
    if [ "$status" = "FAILED" ]; then
        echo -e "${GREEN}✅ Status correct: $status${NC}"
    else
        echo -e "${RED}❌ Status incorrect: expected FAILED, got $status${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Check endTime exists
    end_time=$(echo "$item" | jq -r '.endTime.N')
    if [ "$end_time" != "null" ] && [ -n "$end_time" ]; then
        echo -e "${GREEN}✅ endTime set: $end_time${NC}"
    else
        echo -e "${RED}❌ endTime not set${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Check errorMessage
    error_msg=$(echo "$item" | jq -r '.errorMessage.S')
    if [ "$error_msg" = "DRS job failed: LaunchFailed" ]; then
        echo -e "${GREEN}✅ errorMessage correct: $error_msg${NC}"
    else
        echo -e "${RED}❌ errorMessage incorrect: expected 'DRS job failed: LaunchFailed', got '$error_msg'${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Check errorCode
    error_code=$(echo "$item" | jq -r '.errorCode.S')
    if [ "$error_code" = "LAUNCH_FAILED" ]; then
        echo -e "${GREEN}✅ errorCode correct: $error_code${NC}"
    else
        echo -e "${RED}❌ errorCode incorrect: expected 'LAUNCH_FAILED', got '$error_code'${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Check failedWaves
    failed_waves=$(echo "$item" | jq -r '.failedWaves.N')
    if [ "$failed_waves" = "1" ]; then
        echo -e "${GREEN}✅ failedWaves correct: $failed_waves${NC}"
    else
        echo -e "${RED}❌ failedWaves incorrect: expected 1, got $failed_waves${NC}"
        cleanup_test_execution "$execution_id" "$plan_id"
        exit 1
    fi
    
    # Cleanup
    cleanup_test_execution "$execution_id" "$plan_id"
    
    echo -e "${GREEN}✅ TEST 4 PASSED: FAILED status update works correctly${NC}"
}

# Test 5: Non-existent Execution
test_nonexistent_execution() {
    echo ""
    echo "================================================================================"
    echo "TEST 5: Non-Existent Execution"
    echo "================================================================================"
    
    local execution_id="test-exec-nonexistent-001"
    local plan_id="test-plan-001"
    
    # Invoke Lambda (no test execution created)
    payload="{\"action\": \"update_wave_completion_status\", \"execution_id\": \"$execution_id\", \"plan_id\": \"$plan_id\", \"status\": \"COMPLETED\"}"
    response=$(invoke_lambda "$payload")
    echo "   Response: $response"
    
    # Check for 404 error
    status_code=$(echo "$response" | jq -r '.statusCode')
    if [ "$status_code" = "404" ]; then
        echo -e "${GREEN}✅ Correct status code: $status_code${NC}"
    else
        echo -e "${RED}❌ Incorrect status code: expected 404, got $status_code${NC}"
        exit 1
    fi
    
    # Check error message
    error=$(echo "$response" | jq -r '.error')
    if echo "$error" | grep -qi "not found"; then
        echo -e "${GREEN}✅ Correct error message: $error${NC}"
    else
        echo -e "${RED}❌ Incorrect error message: $error${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ TEST 5 PASSED: Non-existent execution handled correctly${NC}"
}

# Run all tests
main() {
    test_cancelled_status
    test_paused_status
    test_completed_status
    test_failed_status
    test_nonexistent_execution
    
    echo ""
    echo "================================================================================"
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo "================================================================================"
}

main
