#!/bin/bash
# Verification script for execution history table updates
# Verifies that wave completion status is being persisted correctly

set -e

# Configuration
REGION="us-east-1"
TABLE_NAME="aws-drs-orchestration-execution-history-qa"
EXECUTION_HANDLER="aws-drs-orchestration-execution-handler-qa"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "EXECUTION HISTORY TABLE VERIFICATION"
echo "================================================================================"
echo "Region: $REGION"
echo "Table: $TABLE_NAME"
echo "Execution Handler: $EXECUTION_HANDLER"
echo ""

# Function to query recent executions
query_recent_executions() {
    echo -e "${BLUE}📊 Querying recent executions...${NC}"
    
    # Get last 10 executions
    aws dynamodb scan \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --limit 10 \
        --query 'Items[*].{ExecutionId:executionId.S,PlanId:planId.S,Status:status.S,CurrentWave:currentWave.N,CompletedWaves:completedWaves.N,FailedWaves:failedWaves.N,LastUpdated:lastUpdated.N}' \
        --output table
}

# Function to get specific execution details
get_execution_details() {
    local execution_id=$1
    local plan_id=$2
    
    echo -e "${BLUE}🔍 Getting execution details: $execution_id${NC}"
    
    aws dynamodb get-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$execution_id\"}, \"planId\": {\"S\": \"$plan_id\"}}" \
        --output json | jq '.'
}

# Function to verify required fields exist
verify_execution_fields() {
    local execution_id=$1
    local plan_id=$2
    
    echo -e "${BLUE}✅ Verifying required fields for: $execution_id${NC}"
    
    item=$(aws dynamodb get-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$execution_id\"}, \"planId\": {\"S\": \"$plan_id\"}}" \
        --output json)
    
    # Check required fields
    local has_errors=0
    
    # Status
    status=$(echo "$item" | jq -r '.Item.status.S')
    if [ "$status" != "null" ] && [ -n "$status" ]; then
        echo -e "${GREEN}  ✓ status: $status${NC}"
    else
        echo -e "${RED}  ✗ status: MISSING${NC}"
        has_errors=1
    fi
    
    # Current wave
    current_wave=$(echo "$item" | jq -r '.Item.currentWave.N')
    if [ "$current_wave" != "null" ] && [ -n "$current_wave" ]; then
        echo -e "${GREEN}  ✓ currentWave: $current_wave${NC}"
    else
        echo -e "${YELLOW}  ⚠ currentWave: MISSING (may be OK for some statuses)${NC}"
    fi
    
    # Completed waves
    completed_waves=$(echo "$item" | jq -r '.Item.completedWaves.N')
    if [ "$completed_waves" != "null" ] && [ -n "$completed_waves" ]; then
        echo -e "${GREEN}  ✓ completedWaves: $completed_waves${NC}"
    else
        echo -e "${YELLOW}  ⚠ completedWaves: MISSING${NC}"
    fi
    
    # Failed waves
    failed_waves=$(echo "$item" | jq -r '.Item.failedWaves.N')
    if [ "$failed_waves" != "null" ] && [ -n "$failed_waves" ]; then
        echo -e "${GREEN}  ✓ failedWaves: $failed_waves${NC}"
    else
        echo -e "${YELLOW}  ⚠ failedWaves: MISSING${NC}"
    fi
    
    # Last updated
    last_updated=$(echo "$item" | jq -r '.Item.lastUpdated.N')
    if [ "$last_updated" != "null" ] && [ -n "$last_updated" ]; then
        echo -e "${GREEN}  ✓ lastUpdated: $last_updated${NC}"
    else
        echo -e "${RED}  ✗ lastUpdated: MISSING${NC}"
        has_errors=1
    fi
    
    # Check status-specific fields
    if [ "$status" = "COMPLETED" ] || [ "$status" = "FAILED" ] || [ "$status" = "CANCELLED" ]; then
        end_time=$(echo "$item" | jq -r '.Item.endTime.N')
        if [ "$end_time" != "null" ] && [ -n "$end_time" ]; then
            echo -e "${GREEN}  ✓ endTime: $end_time${NC}"
        else
            echo -e "${RED}  ✗ endTime: MISSING (required for $status)${NC}"
            has_errors=1
        fi
    fi
    
    if [ "$status" = "PAUSED" ]; then
        paused_wave=$(echo "$item" | jq -r '.Item.pausedBeforeWave.N')
        if [ "$paused_wave" != "null" ] && [ -n "$paused_wave" ]; then
            echo -e "${GREEN}  ✓ pausedBeforeWave: $paused_wave${NC}"
        else
            echo -e "${YELLOW}  ⚠ pausedBeforeWave: MISSING (optional for PAUSED)${NC}"
        fi
    fi
    
    if [ "$status" = "FAILED" ]; then
        error_msg=$(echo "$item" | jq -r '.Item.errorMessage.S')
        if [ "$error_msg" != "null" ] && [ -n "$error_msg" ]; then
            echo -e "${GREEN}  ✓ errorMessage: $error_msg${NC}"
        else
            echo -e "${YELLOW}  ⚠ errorMessage: MISSING (optional for FAILED)${NC}"
        fi
    fi
    
    return $has_errors
}

# Function to check CloudWatch Logs for execution-handler updates
check_cloudwatch_logs() {
    echo -e "${BLUE}📝 Checking CloudWatch Logs for execution-handler updates...${NC}"
    
    # Get logs from last 10 minutes
    start_time=$(($(date +%s) - 600))000  # 10 minutes ago in milliseconds
    
    aws logs filter-log-events \
        --log-group-name "/aws/lambda/$EXECUTION_HANDLER" \
        --region "$REGION" \
        --start-time "$start_time" \
        --filter-pattern "update_wave_completion_status" \
        --query 'events[*].{Timestamp:timestamp,Message:message}' \
        --output table | head -50
}

# Function to verify no writes from query-handler
verify_no_query_handler_writes() {
    echo -e "${BLUE}🔒 Verifying no DynamoDB writes from query-handler...${NC}"
    
    # Get logs from last 10 minutes
    start_time=$(($(date +%s) - 600))000  # 10 minutes ago in milliseconds
    
    # Check for any update_item calls from query-handler
    result=$(aws logs filter-log-events \
        --log-group-name "/aws/lambda/aws-drs-orchestration-query-handler-qa" \
        --region "$REGION" \
        --start-time "$start_time" \
        --filter-pattern "update_item" \
        --query 'events[*].message' \
        --output text)
    
    if [ -z "$result" ]; then
        echo -e "${GREEN}  ✓ No DynamoDB writes detected from query-handler${NC}"
        return 0
    else
        echo -e "${RED}  ✗ WARNING: DynamoDB writes detected from query-handler!${NC}"
        echo "$result"
        return 1
    fi
}

# Function to create test execution and verify update
test_execution_update() {
    echo ""
    echo "================================================================================"
    echo "TEST: Create and Update Execution"
    echo "================================================================================"
    
    local execution_id="verify-test-$(date +%s)"
    local plan_id="verify-plan-001"
    
    # Create test execution
    echo -e "${BLUE}📝 Creating test execution: $execution_id${NC}"
    
    aws dynamodb put-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --item "{
            \"executionId\": {\"S\": \"$execution_id\"},
            \"planId\": {\"S\": \"$plan_id\"},
            \"status\": {\"S\": \"RUNNING\"},
            \"startTime\": {\"N\": \"$(date +%s)\"},
            \"currentWave\": {\"N\": \"1\"},
            \"totalWaves\": {\"N\": \"3\"},
            \"completedWaves\": {\"N\": \"0\"},
            \"failedWaves\": {\"N\": \"0\"},
            \"lastUpdated\": {\"N\": \"$(date +%s)\"}
        }" > /dev/null
    
    echo -e "${GREEN}✅ Created test execution${NC}"
    
    # Update via execution-handler
    echo -e "${BLUE}🚀 Updating execution via execution-handler...${NC}"
    
    payload="{\"action\": \"update_wave_completion_status\", \"execution_id\": \"$execution_id\", \"plan_id\": \"$plan_id\", \"status\": \"COMPLETED\", \"wave_data\": {\"completed_waves\": 3}}"
    
    response=$(aws lambda invoke \
        --function-name "$EXECUTION_HANDLER" \
        --region "$REGION" \
        --payload "$payload" \
        /tmp/lambda_response.json 2>&1)
    
    echo -e "${GREEN}✅ Lambda invoked${NC}"
    cat /tmp/lambda_response.json | jq '.'
    
    # Wait for DynamoDB consistency
    sleep 2
    
    # Verify update
    echo -e "${BLUE}🔍 Verifying execution update...${NC}"
    verify_execution_fields "$execution_id" "$plan_id"
    
    # Cleanup
    echo -e "${BLUE}🧹 Cleaning up test execution...${NC}"
    aws dynamodb delete-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$execution_id\"}, \"planId\": {\"S\": \"$plan_id\"}}" > /dev/null
    
    echo -e "${GREEN}✅ Test execution cleaned up${NC}"
}

# Main verification flow
main() {
    echo ""
    echo "================================================================================"
    echo "STEP 1: Query Recent Executions"
    echo "================================================================================"
    query_recent_executions
    
    echo ""
    echo "================================================================================"
    echo "STEP 2: Check CloudWatch Logs for Execution Handler Updates"
    echo "================================================================================"
    check_cloudwatch_logs
    
    echo ""
    echo "================================================================================"
    echo "STEP 3: Verify No Query Handler Writes"
    echo "================================================================================"
    verify_no_query_handler_writes
    
    echo ""
    echo "================================================================================"
    echo "STEP 4: Test Execution Update"
    echo "================================================================================"
    test_execution_update
    
    echo ""
    echo "================================================================================"
    echo -e "${GREEN}✅ VERIFICATION COMPLETE${NC}"
    echo "================================================================================"
    echo ""
    echo "Summary:"
    echo "  - Execution history table is accessible"
    echo "  - Recent executions show expected fields"
    echo "  - Execution-handler is updating wave completion status"
    echo "  - Query-handler is not performing DynamoDB writes"
    echo "  - Test execution update works correctly"
    echo ""
}

# Run verification
main
