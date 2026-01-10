#!/bin/bash

# AWS DRS Orchestration - System Health Validation Script
# Used for pre/post deployment validation and rollback verification

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="https://akp69tt2m1.execute-api.us-east-1.amazonaws.com/dev"
STACK_NAME="aws-elasticdrs-orchestrator-dev"
REGION="us-east-1"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

echo -e "${BLUE}=== AWS DRS Orchestration System Health Validation ===${NC}"
echo "Timestamp: $(date)"
echo "API Base URL: $API_BASE_URL"
echo "Stack: $STACK_NAME"
echo ""

# Function to print test results
print_test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} - $test_name"
        if [ -n "$details" ]; then
            echo -e "  ${YELLOW}Details: $details${NC}"
        fi
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$test_name")
    fi
}

# Function to get JWT token
get_jwt_token() {
    echo -e "${BLUE}Getting JWT token...${NC}"
    
    TOKEN=$(aws cognito-idp admin-initiate-auth \
        --user-pool-id us-east-1_ZpRNNnGTK \
        --client-id 3b9l2jv7engtoeba2t1h2mo5ds \
        --auth-flow ADMIN_NO_SRP_AUTH \
        --auth-parameters USERNAME=testuser@example.com,PASSWORD=TestPassword123! \
        --region us-east-1 \
        --query 'AuthenticationResult.IdToken' \
        --output text 2>/dev/null)
    
    if [ -n "$TOKEN" ] && [ "$TOKEN" != "None" ]; then
        print_test_result "JWT Token Acquisition" "PASS"
        return 0
    else
        print_test_result "JWT Token Acquisition" "FAIL" "Could not obtain JWT token"
        return 1
    fi
}

# Test 1: CloudFormation Stack Status
test_cloudformation_stack() {
    echo -e "\n${BLUE}Testing CloudFormation Stack...${NC}"
    
    STACK_STATUS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "FAILED")
    
    if [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
        print_test_result "CloudFormation Stack Status" "PASS" "Status: $STACK_STATUS"
    else
        print_test_result "CloudFormation Stack Status" "FAIL" "Status: $STACK_STATUS"
    fi
}

# Test 2: Lambda Functions Health
test_lambda_functions() {
    echo -e "\n${BLUE}Testing Lambda Functions...${NC}"
    
    LAMBDA_FUNCTIONS=(
        "aws-elasticdrs-orchestrator-api-handler-dev"
        "aws-elasticdrs-orchestrator-execution-finder-dev"
        "aws-elasticdrs-orchestrator-execution-poller-dev"
        "aws-elasticdrs-orchestrator-orchestration-stepfunctions-dev"
        "aws-elasticdrs-orchestrator-frontend-builder-dev"
        "aws-elasticdrs-orchestrator-notification-formatter-dev"
        "aws-elasticdrs-orchestrator-bucket-cleaner-dev"
    )
    
    for func in "${LAMBDA_FUNCTIONS[@]}"; do
        FUNC_STATUS=$(aws lambda get-function \
            --function-name "$func" \
            --region "$REGION" \
            --query 'Configuration.State' \
            --output text 2>/dev/null || echo "FAILED")
        
        if [ "$FUNC_STATUS" = "Active" ]; then
            print_test_result "Lambda Function: $func" "PASS"
        else
            print_test_result "Lambda Function: $func" "FAIL" "Status: $FUNC_STATUS"
        fi
    done
}

# Test 3: API Gateway Health Endpoint
test_api_health() {
    echo -e "\n${BLUE}Testing API Gateway Health...${NC}"
    
    HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/health_response.json \
        "$API_BASE_URL/health" 2>/dev/null || echo "000")
    
    if [ "$HEALTH_RESPONSE" = "200" ]; then
        HEALTH_STATUS=$(cat /tmp/health_response.json | jq -r '.status' 2>/dev/null || echo "unknown")
        if [ "$HEALTH_STATUS" = "healthy" ]; then
            print_test_result "API Gateway Health Endpoint" "PASS"
        else
            print_test_result "API Gateway Health Endpoint" "FAIL" "Status: $HEALTH_STATUS"
        fi
    else
        print_test_result "API Gateway Health Endpoint" "FAIL" "HTTP Code: $HEALTH_RESPONSE"
    fi
    
    rm -f /tmp/health_response.json
}

# Test 4: Authentication System
test_authentication() {
    echo -e "\n${BLUE}Testing Authentication System...${NC}"
    
    if ! get_jwt_token; then
        return 1
    fi
    
    # Test authenticated endpoint
    AUTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/auth_response.json \
        -H "Authorization: Bearer $TOKEN" \
        "$API_BASE_URL/user/permissions" 2>/dev/null || echo "000")
    
    if [ "$AUTH_RESPONSE" = "200" ]; then
        print_test_result "Authenticated API Access" "PASS"
    else
        print_test_result "Authenticated API Access" "FAIL" "HTTP Code: $AUTH_RESPONSE"
    fi
    
    rm -f /tmp/auth_response.json
}

# Test 5: DynamoDB Tables
test_dynamodb_tables() {
    echo -e "\n${BLUE}Testing DynamoDB Tables...${NC}"
    
    TABLES=(
        "aws-elasticdrs-orchestrator-protection-groups-dev"
        "aws-elasticdrs-orchestrator-recovery-plans-dev"
        "aws-elasticdrs-orchestrator-execution-history-dev"
        "aws-elasticdrs-orchestrator-target-accounts-dev"
    )
    
    for table in "${TABLES[@]}"; do
        TABLE_STATUS=$(aws dynamodb describe-table \
            --table-name "$table" \
            --region "$REGION" \
            --query 'Table.TableStatus' \
            --output text 2>/dev/null || echo "FAILED")
        
        if [ "$TABLE_STATUS" = "ACTIVE" ]; then
            print_test_result "DynamoDB Table: $table" "PASS"
        else
            print_test_result "DynamoDB Table: $table" "FAIL" "Status: $TABLE_STATUS"
        fi
    done
}

# Test 6: Protection Groups API
test_protection_groups_api() {
    echo -e "\n${BLUE}Testing Protection Groups API...${NC}"
    
    if [ -z "$TOKEN" ]; then
        print_test_result "Protection Groups API" "FAIL" "No authentication token"
        return 1
    fi
    
    PG_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/pg_response.json \
        -H "Authorization: Bearer $TOKEN" \
        "$API_BASE_URL/protection-groups" 2>/dev/null || echo "000")
    
    if [ "$PG_RESPONSE" = "200" ]; then
        print_test_result "Protection Groups API" "PASS"
    else
        print_test_result "Protection Groups API" "FAIL" "HTTP Code: $PG_RESPONSE"
    fi
    
    rm -f /tmp/pg_response.json
}

# Test 7: Recovery Plans API
test_recovery_plans_api() {
    echo -e "\n${BLUE}Testing Recovery Plans API...${NC}"
    
    if [ -z "$TOKEN" ]; then
        print_test_result "Recovery Plans API" "FAIL" "No authentication token"
        return 1
    fi
    
    RP_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/rp_response.json \
        -H "Authorization: Bearer $TOKEN" \
        "$API_BASE_URL/recovery-plans" 2>/dev/null || echo "000")
    
    if [ "$RP_RESPONSE" = "200" ]; then
        print_test_result "Recovery Plans API" "PASS"
    else
        print_test_result "Recovery Plans API" "FAIL" "HTTP Code: $RP_RESPONSE"
    fi
    
    rm -f /tmp/rp_response.json
}

# Test 8: Executions API
test_executions_api() {
    echo -e "\n${BLUE}Testing Executions API...${NC}"
    
    if [ -z "$TOKEN" ]; then
        print_test_result "Executions API" "FAIL" "No authentication token"
        return 1
    fi
    
    EXEC_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/exec_response.json \
        -H "Authorization: Bearer $TOKEN" \
        "$API_BASE_URL/executions" 2>/dev/null || echo "000")
    
    if [ "$EXEC_RESPONSE" = "200" ]; then
        print_test_result "Executions API" "PASS"
    else
        print_test_result "Executions API" "FAIL" "HTTP Code: $EXEC_RESPONSE"
    fi
    
    rm -f /tmp/exec_response.json
}

# Test 9: Step Functions State Machine
test_step_functions() {
    echo -e "\n${BLUE}Testing Step Functions State Machine...${NC}"
    
    # Get state machine ARN from CloudFormation outputs
    STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`OrchestrationStateMachineArn`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$STATE_MACHINE_ARN" ] && [ "$STATE_MACHINE_ARN" != "None" ]; then
        SF_STATUS=$(aws stepfunctions describe-state-machine \
            --state-machine-arn "$STATE_MACHINE_ARN" \
            --region "$REGION" \
            --query 'status' \
            --output text 2>/dev/null || echo "FAILED")
        
        if [ "$SF_STATUS" = "ACTIVE" ]; then
            print_test_result "Step Functions State Machine" "PASS"
        else
            print_test_result "Step Functions State Machine" "FAIL" "Status: $SF_STATUS"
        fi
    else
        print_test_result "Step Functions State Machine" "FAIL" "Could not find state machine ARN"
    fi
}

# Test 10: EventBridge Rules
test_eventbridge_rules() {
    echo -e "\n${BLUE}Testing EventBridge Rules...${NC}"
    
    # Check for execution finder rule
    RULE_STATUS=$(aws events describe-rule \
        --name "aws-elasticdrs-orchestrator-execution-finder-schedule-dev" \
        --region "$REGION" \
        --query 'State' \
        --output text 2>/dev/null || echo "FAILED")
    
    if [ "$RULE_STATUS" = "ENABLED" ]; then
        print_test_result "EventBridge Execution Finder Rule" "PASS"
    else
        print_test_result "EventBridge Execution Finder Rule" "FAIL" "Status: $RULE_STATUS"
    fi
}

# Test 11: CloudFront Distribution
test_cloudfront() {
    echo -e "\n${BLUE}Testing CloudFront Distribution...${NC}"
    
    # Get distribution ID from CloudFormation outputs
    DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$DISTRIBUTION_ID" ] && [ "$DISTRIBUTION_ID" != "None" ]; then
        CF_STATUS=$(aws cloudfront get-distribution \
            --id "$DISTRIBUTION_ID" \
            --query 'Distribution.Status' \
            --output text 2>/dev/null || echo "FAILED")
        
        if [ "$CF_STATUS" = "Deployed" ]; then
            print_test_result "CloudFront Distribution" "PASS"
        else
            print_test_result "CloudFront Distribution" "FAIL" "Status: $CF_STATUS"
        fi
    else
        print_test_result "CloudFront Distribution" "FAIL" "Could not find distribution ID"
    fi
}

# Test 12: Recent Lambda Logs (No Errors)
test_lambda_logs() {
    echo -e "\n${BLUE}Testing Recent Lambda Logs...${NC}"
    
    # Check for recent errors in critical Lambda functions
    CRITICAL_FUNCTIONS=(
        "aws-elasticdrs-orchestrator-api-handler-dev"
        "aws-elasticdrs-orchestrator-orchestration-stepfunctions-dev"
    )
    
    for func in "${CRITICAL_FUNCTIONS[@]}"; do
        ERROR_COUNT=$(aws logs filter-log-events \
            --log-group-name "/aws/lambda/$func" \
            --start-time $(($(date +%s) - 300))000 \
            --filter-pattern "ERROR" \
            --region "$REGION" \
            --query 'length(events)' \
            --output text 2>/dev/null || echo "0")
        
        if [ "$ERROR_COUNT" = "0" ]; then
            print_test_result "Recent Errors: $func" "PASS"
        else
            print_test_result "Recent Errors: $func" "FAIL" "$ERROR_COUNT errors in last 5 minutes"
        fi
    done
}

# Main execution
main() {
    echo -e "${BLUE}Starting system health validation...${NC}\n"
    
    # Run all tests
    test_cloudformation_stack
    test_lambda_functions
    test_api_health
    test_authentication
    test_dynamodb_tables
    test_protection_groups_api
    test_recovery_plans_api
    test_executions_api
    test_step_functions
    test_eventbridge_rules
    test_cloudfront
    test_lambda_logs
    
    # Print summary
    echo -e "\n${BLUE}=== Test Summary ===${NC}"
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "\n${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}✗${NC} $test"
        done
        echo ""
        echo -e "${YELLOW}System health validation FAILED. Check failed tests before proceeding.${NC}"
        exit 1
    else
        echo -e "\n${GREEN}✓ All tests passed! System is healthy.${NC}"
        exit 0
    fi
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed. Please install jq first.${NC}"
    exit 1
fi

# Run main function
main "$@"