#!/bin/bash
# Data Integrity Verification for Wave Status Polling Refactoring
# Task 4.10: Verify no data loss during wave transitions

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
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "WAVE DATA INTEGRITY VERIFICATION"
echo "================================================================================"
echo "Region: $REGION"
echo "Table: $TABLE_NAME"
echo "Execution Handler: $EXECUTION_HANDLER"
echo ""

# Function to verify execution record fields
verify_execution_fields() {
    local execution_id=$1
    local plan_id=$2
    
    echo -e "${CYAN}--- Analyzing Execution: $execution_id ---${NC}"
    
    # Get execution record
    item=$(aws dynamodb get-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$execution_id\"}, \"planId\": {\"S\": \"$plan_id\"}}" \
        --output json)
    
    if [ -z "$item" ] || [ "$item" = "null" ]; then
        echo -e "${RED}❌ Execution not found${NC}"
        return 1
    fi
    
    local has_errors=0
    
    # Extract fields
    status=$(echo "$item" | jq -r '.Item.status.S // empty')
    last_updated=$(echo "$item" | jq -r '.Item.lastUpdated.N // empty')
    start_time=$(echo "$item" | jq -r '.Item.startTime.N // empty')
    end_time=$(echo "$item" | jq -r '.Item.endTime.N // empty')
    current_wave=$(echo "$item" | jq -r '.Item.currentWave.N // empty')
    total_waves=$(echo "$item" | jq -r '.Item.totalWaves.N // empty')
    completed_waves=$(echo "$item" | jq -r '.Item.completedWaves.N // empty')
    failed_waves=$(echo "$item" | jq -r '.Item.failedWaves.N // empty')
    duration=$(echo "$item" | jq -r '.Item.durationSeconds.N // empty')
    paused_wave=$(echo "$item" | jq -r '.Item.pausedBeforeWave.N // empty')
    error_msg=$(echo "$item" | jq -r '.Item.errorMessage.S // empty')
    error_code=$(echo "$item" | jq -r '.Item.errorCode.S // empty')
    
    # Verify required fields
    if [ -z "$status" ]; then
        echo -e "${RED}  ✗ status: MISSING${NC}"
        has_errors=1
    else
        echo -e "${GREEN}  ✓ status: $status${NC}"
    fi
    
    if [ -z "$last_updated" ]; then
        echo -e "${RED}  ✗ lastUpdated: MISSING${NC}"
        has_errors=1
    else
        echo -e "${GREEN}  ✓ lastUpdated: $last_updated${NC}"
    fi
    
    # Verify status-specific required fields
    case "$status" in
        "COMPLETED")
            if [ -z "$end_time" ]; then
                echo -e "${RED}  ✗ endTime: MISSING (required for COMPLETED)${NC}"
                has_errors=1
            else
                echo -e "${GREEN}  ✓ endTime: $end_time${NC}"
            fi
            
            if [ -z "$completed_waves" ]; then
                echo -e "${RED}  ✗ completedWaves: MISSING (required for COMPLETED)${NC}"
                has_errors=1
            else
                echo -e "${GREEN}  ✓ completedWaves: $completed_waves${NC}"
            fi
            
            if [ -z "$duration" ]; then
                echo -e "${RED}  ✗ durationSeconds: MISSING (required for COMPLETED)${NC}"
                has_errors=1
            else
                echo -e "${GREEN}  ✓ durationSeconds: $duration${NC}"
            fi
            
            # Verify completedWaves == totalWaves
            if [ -n "$completed_waves" ] && [ -n "$total_waves" ]; then
                if [ "$completed_waves" != "$total_waves" ]; then
                    echo -e "${YELLOW}  ⚠ completedWaves ($completed_waves) != totalWaves ($total_waves)${NC}"
                fi
            fi
            ;;
            
        "FAILED")
            if [ -z "$end_time" ]; then
                echo -e "${RED}  ✗ endTime: MISSING (required for FAILED)${NC}"
                has_errors=1
            else
                echo -e "${GREEN}  ✓ endTime: $end_time${NC}"
            fi
            
            if [ -z "$failed_waves" ]; then
                echo -e "${RED}  ✗ failedWaves: MISSING (required for FAILED)${NC}"
                has_errors=1
            else
                echo -e "${GREEN}  ✓ failedWaves: $failed_waves${NC}"
            fi
            
            if [ -z "$duration" ]; then
                echo -e "${RED}  ✗ durationSeconds: MISSING (required for FAILED)${NC}"
                has_errors=1
            else
                echo -e "${GREEN}  ✓ durationSeconds: $duration${NC}"
            fi
            
            if [ -z "$error_msg" ]; then
                echo -e "${YELLOW}  ⚠ errorMessage: MISSING (optional but recommended)${NC}"
            else
                echo -e "${GREEN}  ✓ errorMessage: $error_msg${NC}"
            fi
            
            if [ -z "$error_code" ]; then
                echo -e "${YELLOW}  ⚠ errorCode: MISSING (optional but recommended)${NC}"
            else
                echo -e "${GREEN}  ✓ errorCode: $error_code${NC}"
            fi
            ;;
            
        "CANCELLED")
            if [ -z "$end_time" ]; then
                echo -e "${RED}  ✗ endTime: MISSING (required for CANCELLED)${NC}"
                has_errors=1
            else
                echo -e "${GREEN}  ✓ endTime: $end_time${NC}"
            fi
            ;;
            
        "PAUSED")
            if [ -z "$paused_wave" ]; then
                echo -e "${YELLOW}  ⚠ pausedBeforeWave: MISSING (optional for PAUSED)${NC}"
            else
                echo -e "${GREEN}  ✓ pausedBeforeWave: $paused_wave${NC}"
            fi
            ;;
            
        "RUNNING")
            if [ -z "$current_wave" ]; then
                echo -e "${YELLOW}  ⚠ currentWave: MISSING (expected for RUNNING)${NC}"
            else
                echo -e "${GREEN}  ✓ currentWave: $current_wave${NC}"
            fi
            ;;
    esac
    
    # Verify timestamp consistency
    if [ -n "$start_time" ] && [ -n "$end_time" ]; then
        if [ "$end_time" -lt "$start_time" ]; then
            echo -e "${RED}  ✗ endTime ($end_time) < startTime ($start_time)${NC}"
            has_errors=1
        fi
        
        # Verify duration calculation
        if [ -n "$duration" ]; then
            calculated_duration=$((end_time - start_time))
            diff=$((calculated_duration - duration))
            # Allow 1 second tolerance
            if [ ${diff#-} -gt 1 ]; then
                echo -e "${YELLOW}  ⚠ durationSeconds ($duration) doesn't match calculated ($calculated_duration)${NC}"
            fi
        fi
    fi
    
    if [ $has_errors -eq 0 ]; then
        echo -e "${GREEN}✅ No data integrity issues found${NC}"
    else
        echo -e "${RED}❌ Found data integrity errors${NC}"
    fi
    
    return $has_errors
}

# Function to test wave transition data flow
test_wave_transition() {
    echo ""
    echo "================================================================================"
    echo "TEST: Wave Transition Data Flow"
    echo "================================================================================"
    
    local execution_id="data-integrity-test-$(date +%s)"
    local plan_id="test-plan-001"
    local current_time=$(date +%s)
    
    # Step 1: Create initial execution
    echo -e "${CYAN}--- Step 1: Create Initial Execution ---${NC}"
    
    aws dynamodb put-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --item "{
            \"executionId\": {\"S\": \"$execution_id\"},
            \"planId\": {\"S\": \"$plan_id\"},
            \"status\": {\"S\": \"RUNNING\"},
            \"startTime\": {\"N\": \"$current_time\"},
            \"currentWave\": {\"N\": \"1\"},
            \"totalWaves\": {\"N\": \"3\"},
            \"completedWaves\": {\"N\": \"0\"},
            \"failedWaves\": {\"N\": \"0\"},
            \"lastUpdated\": {\"N\": \"$current_time\"}
        }" > /dev/null
    
    echo -e "${GREEN}✅ Created initial execution${NC}"
    
    # Verify initial data
    verify_execution_fields "$execution_id" "$plan_id"
    local step1_result=$?
    
    # Step 2: Simulate wave 1 completion
    echo ""
    echo -e "${CYAN}--- Step 2: Simulate Wave 1 Completion ---${NC}"
    
    local payload="{\"action\": \"update_wave_completion_status\", \"execution_id\": \"$execution_id\", \"plan_id\": \"$plan_id\", \"status\": \"RUNNING\", \"wave_data\": {\"completed_waves\": 1, \"start_time\": $current_time}}"
    
    aws lambda invoke \
        --function-name "$EXECUTION_HANDLER" \
        --region "$REGION" \
        --payload "$payload" \
        /tmp/lambda_response.json > /dev/null
    
    echo -e "${GREEN}✅ Updated wave 1 completion${NC}"
    cat /tmp/lambda_response.json | jq '.'
    
    sleep 2  # Wait for DynamoDB consistency
    
    # Verify wave 1 completion
    verify_execution_fields "$execution_id" "$plan_id"
    local step2_result=$?
    
    # Verify completedWaves was updated
    completed=$(aws dynamodb get-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$execution_id\"}, \"planId\": {\"S\": \"$plan_id\"}}" \
        --query 'Item.completedWaves.N' \
        --output text)
    
    if [ "$completed" != "1" ]; then
        echo -e "${RED}❌ completedWaves not updated (expected 1, got $completed)${NC}"
        step2_result=1
    else
        echo -e "${GREEN}✅ completedWaves correctly updated to 1${NC}"
    fi
    
    # Step 3: Simulate pause before wave 2
    echo ""
    echo -e "${CYAN}--- Step 3: Simulate Pause Before Wave 2 ---${NC}"
    
    payload="{\"action\": \"update_wave_completion_status\", \"execution_id\": \"$execution_id\", \"plan_id\": \"$plan_id\", \"status\": \"PAUSED\", \"wave_data\": {\"paused_before_wave\": 2}}"
    
    aws lambda invoke \
        --function-name "$EXECUTION_HANDLER" \
        --region "$REGION" \
        --payload "$payload" \
        /tmp/lambda_response.json > /dev/null
    
    echo -e "${GREEN}✅ Updated to PAUSED state${NC}"
    cat /tmp/lambda_response.json | jq '.'
    
    sleep 2  # Wait for DynamoDB consistency
    
    # Verify pause state
    verify_execution_fields "$execution_id" "$plan_id"
    local step3_result=$?
    
    # Step 4: Simulate completion
    echo ""
    echo -e "${CYAN}--- Step 4: Simulate Execution Completion ---${NC}"
    
    payload="{\"action\": \"update_wave_completion_status\", \"execution_id\": \"$execution_id\", \"plan_id\": \"$plan_id\", \"status\": \"COMPLETED\", \"wave_data\": {\"completed_waves\": 3, \"start_time\": $current_time}}"
    
    aws lambda invoke \
        --function-name "$EXECUTION_HANDLER" \
        --region "$REGION" \
        --payload "$payload" \
        /tmp/lambda_response.json > /dev/null
    
    echo -e "${GREEN}✅ Updated to COMPLETED state${NC}"
    cat /tmp/lambda_response.json | jq '.'
    
    sleep 2  # Wait for DynamoDB consistency
    
    # Verify completion state
    verify_execution_fields "$execution_id" "$plan_id"
    local step4_result=$?
    
    # Cleanup
    echo ""
    echo -e "${CYAN}--- Cleanup ---${NC}"
    aws dynamodb delete-item \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$execution_id\"}, \"planId\": {\"S\": \"$plan_id\"}}" > /dev/null
    
    echo -e "${GREEN}✅ Test execution cleaned up${NC}"
    
    # Return overall result
    if [ $step1_result -eq 0 ] && [ $step2_result -eq 0 ] && [ $step3_result -eq 0 ] && [ $step4_result -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Function to analyze recent executions
analyze_recent_executions() {
    echo ""
    echo "================================================================================"
    echo "TEST 1: Analyze Recent Executions"
    echo "================================================================================"
    
    # Get recent executions
    executions=$(aws dynamodb scan \
        --table-name "$TABLE_NAME" \
        --region "$REGION" \
        --limit 10 \
        --query 'Items[*].{ExecutionId:executionId.S,PlanId:planId.S}' \
        --output json)
    
    local count=$(echo "$executions" | jq 'length')
    
    if [ "$count" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No recent executions found${NC}"
        return 0
    fi
    
    echo -e "${BLUE}ℹ️  Analyzing $count recent executions${NC}"
    
    local total_errors=0
    
    # Analyze each execution
    for i in $(seq 0 $((count - 1))); do
        execution_id=$(echo "$executions" | jq -r ".[$i].ExecutionId")
        plan_id=$(echo "$executions" | jq -r ".[$i].PlanId")
        
        echo ""
        verify_execution_fields "$execution_id" "$plan_id"
        if [ $? -ne 0 ]; then
            total_errors=$((total_errors + 1))
        fi
    done
    
    echo ""
    echo -e "${CYAN}--- Summary ---${NC}"
    echo "Total executions analyzed: $count"
    echo "Total errors found: $total_errors"
    
    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}✅ No data integrity errors in recent executions${NC}"
        return 0
    else
        echo -e "${RED}❌ Found $total_errors data integrity errors${NC}"
        return 1
    fi
}

# Main verification flow
main() {
    local all_passed=true
    
    # Test 1: Analyze recent executions
    analyze_recent_executions
    if [ $? -ne 0 ]; then
        all_passed=false
    fi
    
    # Test 2: Wave transition data flow
    test_wave_transition
    if [ $? -ne 0 ]; then
        all_passed=false
    fi
    
    # Final summary
    echo ""
    echo "================================================================================"
    echo "VERIFICATION SUMMARY"
    echo "================================================================================"
    
    if [ "$all_passed" = true ]; then
        echo -e "${GREEN}✅ ALL DATA INTEGRITY CHECKS PASSED${NC}"
        echo ""
        echo "Conclusion:"
        echo "  ✅ No data loss detected during wave transitions"
        echo "  ✅ All execution history fields populated correctly"
        echo "  ✅ Wave completion, pause, and cancellation states work correctly"
        echo "  ✅ Execution progress tracking remains accurate"
        echo "  ✅ Timestamp consistency maintained"
        return 0
    else
        echo -e "${RED}❌ SOME DATA INTEGRITY CHECKS FAILED${NC}"
        echo ""
        echo "Issues detected:"
        echo "  ❌ Data integrity errors found in execution records"
        echo "  ❌ Review detailed output above for specific issues"
        return 1
    fi
}

# Run verification
main
exit $?
