#!/bin/bash

# Test Read Operations - Query Handler Read-Only Audit Task 6.3
# Verifies all read operations still work after refactoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_ENDPOINT="https://k8uzkghqrf.execute-api.us-east-1.amazonaws.com/qa"
REGION="us-east-1"
ACCOUNT_ID="YOUR_ACCOUNT_ID"  # Replace with your AWS account ID

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Query Handler Read Operations Test${NC}"
echo -e "${BLUE}Task 6.3 - Read-Only Audit Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print test header
print_test_header() {
    echo -e "${BLUE}----------------------------------------${NC}"
    echo -e "${BLUE}Test: $1${NC}"
    echo -e "${BLUE}----------------------------------------${NC}"
}

# Function to print test result
print_test_result() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        ((TESTS_PASSED++))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        echo -e "${RED}  Details: $details${NC}"
        ((TESTS_FAILED++))
    elif [ "$status" = "SKIP" ]; then
        echo -e "${YELLOW}⊘ SKIP${NC}: $test_name - $details"
        ((TESTS_SKIPPED++))
    fi
    echo ""
}

# Function to check if authentication is configured
check_authentication() {
    print_test_header "Authentication Check"
    
    # Check if AWS credentials are configured
    if ! aws sts get-caller-identity --region "$REGION" &>/dev/null; then
        echo -e "${RED}ERROR: AWS credentials not configured${NC}"
        echo "Please configure AWS credentials with access to account $ACCOUNT_ID"
        exit 1
    fi
    
    # Get current identity
    CALLER_IDENTITY=$(aws sts get-caller-identity --region "$REGION" --output json)
    CURRENT_ACCOUNT=$(echo "$CALLER_IDENTITY" | jq -r '.Account')
    CURRENT_ARN=$(echo "$CALLER_IDENTITY" | jq -r '.Arn')
    
    echo "Current AWS Identity:"
    echo "  Account: $CURRENT_ACCOUNT"
    echo "  ARN: $CURRENT_ARN"
    echo ""
    
    if [ "$CURRENT_ACCOUNT" != "$ACCOUNT_ID" ]; then
        echo -e "${YELLOW}WARNING: Current account ($CURRENT_ACCOUNT) does not match expected account ($ACCOUNT_ID)${NC}"
        echo ""
    fi
    
    print_test_result "AWS Credentials" "PASS" ""
}

# Function to test direct Lambda invocation
test_lambda_invocation() {
    local operation="$1"
    local payload="$2"
    local test_name="$3"
    
    print_test_header "$test_name"
    
    # Invoke Lambda function
    RESPONSE=$(aws lambda invoke \
        --function-name "aws-drs-orchestration-query-handler-qa" \
        --region "$REGION" \
        --payload "$payload" \
        --cli-binary-format raw-in-base64-out \
        /tmp/lambda_response.json 2>&1)
    
    INVOKE_STATUS=$?
    
    if [ $INVOKE_STATUS -ne 0 ]; then
        print_test_result "$test_name" "FAIL" "Lambda invocation failed: $RESPONSE"
        return 1
    fi
    
    # Check response
    if [ ! -f /tmp/lambda_response.json ]; then
        print_test_result "$test_name" "FAIL" "Response file not created"
        return 1
    fi
    
    RESPONSE_BODY=$(cat /tmp/lambda_response.json)
    
    # Check for errors in response
    if echo "$RESPONSE_BODY" | jq -e '.errorType' &>/dev/null; then
        ERROR_TYPE=$(echo "$RESPONSE_BODY" | jq -r '.errorType')
        ERROR_MESSAGE=$(echo "$RESPONSE_BODY" | jq -r '.errorMessage')
        print_test_result "$test_name" "FAIL" "Lambda error: $ERROR_TYPE - $ERROR_MESSAGE"
        return 1
    fi
    
    # Check for statusCode in response
    if echo "$RESPONSE_BODY" | jq -e '.statusCode' &>/dev/null; then
        STATUS_CODE=$(echo "$RESPONSE_BODY" | jq -r '.statusCode')
        if [ "$STATUS_CODE" != "200" ]; then
            ERROR_MSG=$(echo "$RESPONSE_BODY" | jq -r '.body' 2>/dev/null || echo "Unknown error")
            print_test_result "$test_name" "FAIL" "HTTP $STATUS_CODE: $ERROR_MSG"
            return 1
        fi
    fi
    
    echo "Response preview:"
    echo "$RESPONSE_BODY" | jq '.' | head -20
    echo ""
    
    print_test_result "$test_name" "PASS" ""
    return 0
}

# Test 1: List Executions
test_list_executions() {
    local payload='{
        "operation": "list_executions",
        "queryParams": {}
    }'
    
    test_lambda_invocation "list_executions" "$payload" "List Executions"
}

# Test 2: Get DRS Source Servers
test_get_drs_source_servers() {
    local payload="{
        \"operation\": \"get_drs_source_servers\",
        \"queryParams\": {
            \"region\": \"$REGION\"
        }
    }"
    
    test_lambda_invocation "get_drs_source_servers" "$payload" "Get DRS Source Servers"
}

# Test 3: Get Current Account Info
test_get_current_account() {
    local payload='{
        "operation": "get_current_account_id",
        "queryParams": {}
    }'
    
    test_lambda_invocation "get_current_account_id" "$payload" "Get Current Account"
}

# Test 4: Get Target Accounts
test_get_target_accounts() {
    local payload='{
        "operation": "get_target_accounts",
        "queryParams": {}
    }'
    
    test_lambda_invocation "get_target_accounts" "$payload" "Get Target Accounts"
}

# Test 5: Get EC2 Subnets (requires VPC ID)
test_get_ec2_subnets() {
    print_test_header "Get EC2 Subnets"
    
    # First, get a VPC ID
    VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --query 'Vpcs[0].VpcId' --output text 2>/dev/null)
    
    if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "None" ]; then
        print_test_result "Get EC2 Subnets" "SKIP" "No VPCs found in region"
        return 0
    fi
    
    echo "Using VPC: $VPC_ID"
    
    local payload="{
        \"operation\": \"get_ec2_subnets\",
        \"queryParams\": {
            \"region\": \"$REGION\",
            \"vpcId\": \"$VPC_ID\"
        }
    }"
    
    test_lambda_invocation "get_ec2_subnets" "$payload" "Get EC2 Subnets"
}

# Test 6: Get EC2 Security Groups (requires VPC ID)
test_get_ec2_security_groups() {
    print_test_header "Get EC2 Security Groups"
    
    # First, get a VPC ID
    VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" --query 'Vpcs[0].VpcId' --output text 2>/dev/null)
    
    if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "None" ]; then
        print_test_result "Get EC2 Security Groups" "SKIP" "No VPCs found in region"
        return 0
    fi
    
    echo "Using VPC: $VPC_ID"
    
    local payload="{
        \"operation\": \"get_ec2_security_groups\",
        \"queryParams\": {
            \"region\": \"$REGION\",
            \"vpcId\": \"$VPC_ID\"
        }
    }"
    
    test_lambda_invocation "get_ec2_security_groups" "$payload" "Get EC2 Security Groups"
}

# Test 7: Get EC2 Instance Types
test_get_ec2_instance_types() {
    local payload="{
        \"operation\": \"get_ec2_instance_types\",
        \"queryParams\": {
            \"region\": \"$REGION\"
        }
    }"
    
    test_lambda_invocation "get_ec2_instance_types" "$payload" "Get EC2 Instance Types"
}

# Test 8: Get EC2 Instance Profiles
test_get_ec2_instance_profiles() {
    local payload="{
        \"operation\": \"get_ec2_instance_profiles\",
        \"queryParams\": {
            \"region\": \"$REGION\"
        }
    }"
    
    test_lambda_invocation "get_ec2_instance_profiles" "$payload" "Get EC2 Instance Profiles"
}

# Test 9: Export Configuration
test_export_configuration() {
    local payload='{
        "operation": "export_configuration",
        "queryParams": {}
    }'
    
    test_lambda_invocation "export_configuration" "$payload" "Export Configuration"
}

# Test 10: Get DRS Account Capacity (All Regions)
test_get_drs_capacity() {
    local payload='{
        "operation": "get_drs_account_capacity_all_regions",
        "queryParams": {}
    }'
    
    test_lambda_invocation "get_drs_account_capacity_all_regions" "$payload" "Get DRS Account Capacity (All Regions)"
}

# Main test execution
main() {
    echo "Starting read operations verification..."
    echo "API Endpoint: $API_ENDPOINT"
    echo "Region: $REGION"
    echo "Account: $ACCOUNT_ID"
    echo ""
    
    # Check authentication
    check_authentication
    
    # Run all tests
    test_list_executions
    test_get_drs_source_servers
    test_get_current_account
    test_get_target_accounts
    test_get_ec2_subnets
    test_get_ec2_security_groups
    test_get_ec2_instance_types
    test_get_ec2_instance_profiles
    test_export_configuration
    test_get_drs_capacity
    
    # Print summary
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Test Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo -e "${YELLOW}Skipped: $TESTS_SKIPPED${NC}"
    echo -e "${BLUE}Total: $((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))${NC}"
    echo ""
    
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Some tests failed. Please review the output above.${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

# Run main function
main
