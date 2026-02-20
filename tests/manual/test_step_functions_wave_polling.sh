#!/bin/bash
# Manual test script for Step Functions wave polling flow
# Tests PollWaveStatus -> UpdateWaveStatus state transitions

set -e

# Configuration
REGION="us-east-1"
STATE_MACHINE_ARN="arn:aws:states:us-east-1:438465159935:stateMachine:aws-drs-orchestration-orchestration-qa"
EXECUTION_TABLE="aws-drs-orchestration-execution-history-qa"
PLAN_TABLE="aws-drs-orchestration-recovery-plans-qa"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "STEP FUNCTIONS WAVE POLLING TEST"
echo "================================================================================"
echo "Region: $REGION"
echo "State Machine: aws-drs-orchestration-orchestration-qa"
echo ""

# Generate unique IDs
TIMESTAMP=$(date +%s)
PLAN_ID="test-plan-sf-${TIMESTAMP}"
EXECUTION_ID="test-exec-sf-${TIMESTAMP}"

# Function to create test recovery plan
create_test_plan() {
    echo -e "${BLUE}📝 Creating test recovery plan: $PLAN_ID${NC}"
    
    aws dynamodb put-item \
        --table-name "$PLAN_TABLE" \
        --region "$REGION" \
        --item "{
            \"planId\": {\"S\": \"$PLAN_ID\"},
            \"planName\": {\"S\": \"Test Plan for Wave Polling\"},
            \"status\": {\"S\": \"ACTIVE\"},
            \"createdAt\": {\"N\": \"$TIMESTAMP\"},
            \"createdBy\": {\"S\": \"test-user\"},
            \"waves\": {\"L\": [
                {\"M\": {
                    \"waveNumber\": {\"N\": \"1\"},
                    \"waveName\": {\"S\": \"Test Wave 1\"},
                    \"servers\": {\"L\": [
                        {\"M\": {
                            \"sourceServerId\": {\"S\": \"s-test123456789abcd\"},
                            \"targetAccountId\": {\"S\": \"438465159935\"}
                        }}
                    ]}
                }}
            ]},
            \"totalWaves\": {\"N\": \"1\"}
        }" > /dev/null
    
    echo -e "${GREEN}✅ Created test recovery plan: $PLAN_ID${NC}"
}

# Function to create test execution
create_test_execution() {
    echo -e "${BLUE}📝 Creating test execution: $EXECUTION_ID${NC}"
    
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
            \"lastUpdated\": {\"N\": \"$TIMESTAMP\"}
        }" > /dev/null
    
    echo -e "${GREEN}✅ Created test execution: $EXECUTION_ID${NC}"
}

# Function to start Step Functions execution
start_step_functions_execution() {
    echo -e "${BLUE}🚀 Starting Step Functions execution...${NC}"
    
    # Create input payload matching execution-handler format
    INPUT="{
        \"Execution\": {
            \"Id\": \"$EXECUTION_ID\"
        },
        \"Plan\": {
            \"planId\": \"$PLAN_ID\",
            \"planName\": \"Test Plan for Wave Polling\",
            \"waves\": [
                {
                    \"waveNumber\": 1,
                    \"waveName\": \"Test Wave 1\",
                    \"servers\": [
                        {
                            \"sourceServerId\": \"s-test123456789abcd\",
                            \"targetAccountId\": \"438465159935\"
                        }
                    ]
                }
            ]
        },
        \"isDrill\": true,
        \"resumeFromWave\": null,
        \"pauseBeforeExecution\": false,
        \"accountContext\": {
            \"hubAccountId\": \"438465159935\",
            \"targetAccounts\": [\"438465159935\"]
        }
    }"
    
    # Start execution
    SF_EXECUTION_ARN=$(aws stepfunctions start-execution \
        --state-machine-arn "$STATE_MACHINE_ARN" \
        --region "$REGION" \
        --name "test-wave-polling-${TIMESTAMP}" \
        --input "$INPUT" \
        --query 'executionArn' \
        --output text)
    
    echo -e "${GREEN}✅ Started Step Functions execution${NC}"
    echo "   Execution ARN: $SF_EXECUTION_ARN"
    echo ""
}

# Function to monitor Step Functions execution
monitor_execution() {
    local sf_execution_arn=$1
    local max_wait=120  # 2 minutes
    local elapsed=0
    
    echo -e "${BLUE}⏳ Monitoring Step Functions execution...${NC}"
    echo ""
    
    while [ $elapsed -lt $max_wait ]; do
        # Get execution status
        STATUS=$(aws stepfunctions describe-execution \
            --execution-arn "$sf_execution_arn" \
            --region "$REGION" \
            --query 'status' \
            --output text)
        
        echo -e "${YELLOW}   Status: $STATUS (${elapsed}s elapsed)${NC}"
        
        # Check if execution completed
        if [ "$STATUS" = "SUCCEEDED" ]; then
            echo -e "${GREEN}✅ Execution completed successfully${NC}"
            return 0
        elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "TIMED_OUT" ] || [ "$STATUS" = "ABORTED" ]; then
            echo -e "${RED}❌ Execution failed with status: $STATUS${NC}"
            return 1
        fi
        
        # Wait before next check
        sleep 5
        elapsed=$((elapsed + 5))
    done
    
    echo -e "${YELLOW}⚠ Execution still running after ${max_wait}s${NC}"
    return 2
}

# Function to get execution history
get_execution_history() {
    local sf_execution_arn=$1
    
    echo ""
    echo -e "${BLUE}📜 Fetching execution history...${NC}"
    
    aws stepfunctions get-execution-history \
        --execution-arn "$sf_execution_arn" \
        --region "$REGION" \
        --query 'events[?type==`TaskStateEntered` || type==`TaskStateExited` || type==`TaskFailed`].{Type:type,Name:stateEnteredEventDetails.name,Timestamp:timestamp}' \
        --output table
}

# Function to check specific states
check_state_execution() {
    local sf_execution_arn=$1
    local state_name=$2
    
    echo ""
    echo -e "${BLUE}🔍 Checking $state_name state execution...${NC}"
    
    # Get events for this state
    events=$(aws stepfunctions get-execution-history \
        --execution-arn "$sf_execution_arn" \
        --region "$REGION" \
        --query "events[?stateEnteredEventDetails.name=='$state_name' || stateExitedEventDetails.name=='$state_name']" \
        --output json)
    
    # Check if state was entered
    entered=$(echo "$events" | jq '[.[] | select(.type=="TaskStateEntered")] | length')
    if [ "$entered" -gt 0 ]; then
        echo -e "${GREEN}✅ $state_name state was entered${NC}"
    else
        echo -e "${RED}❌ $state_name state was NOT entered${NC}"
        return 1
    fi
    
    # Check if state exited successfully
    exited=$(echo "$events" | jq '[.[] | select(.type=="TaskStateExited")] | length')
    if [ "$exited" -gt 0 ]; then
        echo -e "${GREEN}✅ $state_name state exited successfully${NC}"
    else
        echo -e "${RED}❌ $state_name state did NOT exit successfully${NC}"
        return 1
    fi
    
    return 0
}

# Function to verify DynamoDB updates
verify_dynamodb_updates() {
    echo ""
    echo -e "${BLUE}🔍 Verifying DynamoDB updates...${NC}"
    
    # Get execution record
    item=$(aws dynamodb get-item \
        --table-name "$EXECUTION_TABLE" \
        --region "$REGION" \
        --key "{\"executionId\": {\"S\": \"$EXECUTION_ID\"}, \"planId\": {\"S\": \"$PLAN_ID\"}}" \
        --query 'Item' \
        --output json)
    
    echo "   Execution record:"
    echo "$item" | jq '{status: .status.S, currentWave: .currentWave.N, completedWaves: .completedWaves.N, lastUpdated: .lastUpdated.N}'
    
    # Check if lastUpdated was modified
    last_updated=$(echo "$item" | jq -r '.lastUpdated.N')
    if [ "$last_updated" -gt "$TIMESTAMP" ]; then
        echo -e "${GREEN}✅ Execution record was updated (lastUpdated: $last_updated > $TIMESTAMP)${NC}"
    else
        echo -e "${YELLOW}⚠ Execution record may not have been updated (lastUpdated: $last_updated)${NC}"
    fi
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
    
    # Start Step Functions execution
    start_step_functions_execution
    
    # Get the execution ARN from the global variable
    local SF_EXECUTION_ARN="arn:aws:states:us-east-1:438465159935:execution:aws-drs-orchestration-orchestration-qa:test-wave-polling-${TIMESTAMP}"
    
    # Monitor execution
    if monitor_execution "$SF_EXECUTION_ARN"; then
        # Get execution history
        get_execution_history "$SF_EXECUTION_ARN"
        
        # Check specific states
        check_state_execution "$SF_EXECUTION_ARN" "PollWaveStatus"
        POLL_STATUS=$?
        
        check_state_execution "$SF_EXECUTION_ARN" "UpdateWaveStatus"
        UPDATE_STATUS=$?
        
        # Verify DynamoDB updates
        verify_dynamodb_updates
        
        # Cleanup
        cleanup
        
        # Final result
        echo ""
        echo "================================================================================"
        if [ $POLL_STATUS -eq 0 ] && [ $UPDATE_STATUS -eq 0 ]; then
            echo -e "${GREEN}✅ TEST PASSED: Wave polling flow works correctly${NC}"
            echo "   - PollWaveStatus state executed successfully"
            echo "   - UpdateWaveStatus state executed successfully"
            echo "   - State transitions are correct"
        else
            echo -e "${RED}❌ TEST FAILED: Some states did not execute correctly${NC}"
            exit 1
        fi
        echo "================================================================================"
    else
        echo -e "${RED}❌ Step Functions execution did not complete successfully${NC}"
        cleanup
        exit 1
    fi
}

main
