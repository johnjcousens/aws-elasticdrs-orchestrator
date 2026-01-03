#!/bin/bash

# AWS DRS Orchestration - Fresh Deployment Validation Script
# This script validates that a fresh deployment is working correctly

set -e

# Default configuration
PROJECT_NAME="aws-elasticdrs-orchestrator"
ENVIRONMENT="dev"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
VERBOSE="false"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage function
usage() {
    cat << EOF
AWS DRS Orchestration - Fresh Deployment Validation

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -p, --project-name NAME     Project name (default: aws-elasticdrs-orchestrator)
    -e, --environment ENV       Environment (default: dev)
    -r, --region REGION         AWS region (default: us-east-1)
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

EXAMPLES:
    # Basic validation
    $0

    # Custom configuration
    $0 --project-name my-drs-orchestrator --environment prod --region us-west-2

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--project-name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Update stack name based on parsed parameters
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

# Set AWS region
export AWS_DEFAULT_REGION="$AWS_REGION"

log_info "=== Fresh Deployment Validation ==="
echo "Project Name: $PROJECT_NAME"
echo "Environment:  $ENVIRONMENT"
echo "Stack Name:   $STACK_NAME"
echo "AWS Region:   $AWS_REGION"
echo ""

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to run validation check
run_check() {
    local check_name="$1"
    local check_command="$2"
    local expected_result="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    log_info "Checking: $check_name"
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo "  Command: $check_command"
    fi
    
    local result
    if result=$(eval "$check_command" 2>&1); then
        if [[ -n "$expected_result" ]]; then
            if echo "$result" | grep -q "$expected_result"; then
                log_success "✓ $check_name"
                PASSED_CHECKS=$((PASSED_CHECKS + 1))
                return 0
            else
                log_error "✗ $check_name (unexpected result)"
                if [[ "$VERBOSE" == "true" ]]; then
                    echo "  Expected: $expected_result"
                    echo "  Got: $result"
                fi
                FAILED_CHECKS=$((FAILED_CHECKS + 1))
                return 1
            fi
        else
            log_success "✓ $check_name"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        fi
    else
        log_error "✗ $check_name (command failed)"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "  Error: $result"
        fi
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Check AWS credentials
log_info "=== AWS Credentials Validation ==="
run_check "AWS credentials configured" "aws sts get-caller-identity --query Account --output text" ""
echo ""

# Check CloudFormation stack
log_info "=== CloudFormation Stack Validation ==="
run_check "Stack exists and is complete" "aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --query 'Stacks[0].StackStatus' --output text" "CREATE_COMPLETE\|UPDATE_COMPLETE"

# Get stack outputs for further validation
log_info "Getting stack outputs..."
STACK_OUTPUTS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'Stacks[0].Outputs' --output json 2>/dev/null || echo "[]")

if [[ "$STACK_OUTPUTS" == "[]" ]]; then
    log_error "Could not retrieve stack outputs"
    exit 1
fi

# Extract key values from outputs
API_ENDPOINT=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="ApiEndpoint") | .OutputValue' 2>/dev/null || echo "")
USER_POOL_ID=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="UserPoolId") | .OutputValue' 2>/dev/null || echo "")
CLOUDFRONT_URL=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="CloudFrontUrl") | .OutputValue' 2>/dev/null || echo "")
FRONTEND_BUCKET=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="FrontendBucketName") | .OutputValue' 2>/dev/null || echo "")
PIPELINE_NAME=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="PipelineName") | .OutputValue' 2>/dev/null || echo "")

echo ""

# Check DynamoDB tables
log_info "=== DynamoDB Tables Validation ==="
run_check "Protection Groups table exists" "aws dynamodb describe-table --table-name ${PROJECT_NAME}-protection-groups-${ENVIRONMENT} --region $AWS_REGION --query 'Table.TableStatus' --output text" "ACTIVE"
run_check "Recovery Plans table exists" "aws dynamodb describe-table --table-name ${PROJECT_NAME}-recovery-plans-${ENVIRONMENT} --region $AWS_REGION --query 'Table.TableStatus' --output text" "ACTIVE"
run_check "Execution History table exists" "aws dynamodb describe-table --table-name ${PROJECT_NAME}-execution-history-${ENVIRONMENT} --region $AWS_REGION --query 'Table.TableStatus' --output text" "ACTIVE"
echo ""

# Check Lambda functions
log_info "=== Lambda Functions Validation ==="
run_check "API Handler function exists" "aws lambda get-function --function-name ${PROJECT_NAME}-api-handler-${ENVIRONMENT} --region $AWS_REGION --query 'Configuration.State' --output text" "Active"
run_check "Orchestration function exists" "aws lambda get-function --function-name ${PROJECT_NAME}-orchestration-stepfunctions-${ENVIRONMENT} --region $AWS_REGION --query 'Configuration.State' --output text" "Active"
run_check "Execution Finder function exists" "aws lambda get-function --function-name ${PROJECT_NAME}-execution-finder-${ENVIRONMENT} --region $AWS_REGION --query 'Configuration.State' --output text" "Active"
run_check "Execution Poller function exists" "aws lambda get-function --function-name ${PROJECT_NAME}-execution-poller-${ENVIRONMENT} --region $AWS_REGION --query 'Configuration.State' --output text" "Active"
run_check "Frontend Builder function exists" "aws lambda get-function --function-name ${PROJECT_NAME}-frontend-builder-${ENVIRONMENT} --region $AWS_REGION --query 'Configuration.State' --output text" "Active"
echo ""

# Check API Gateway
log_info "=== API Gateway Validation ==="
if [[ -n "$API_ENDPOINT" ]]; then
    run_check "API Gateway endpoint accessible" "curl -s -o /dev/null -w '%{http_code}' $API_ENDPOINT/health" "200\|401\|403"
    log_success "API Endpoint: $API_ENDPOINT"
else
    log_error "API endpoint not found in stack outputs"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# Check Cognito User Pool
log_info "=== Cognito User Pool Validation ==="
if [[ -n "$USER_POOL_ID" ]]; then
    run_check "User Pool exists and is active" "aws cognito-idp describe-user-pool --user-pool-id $USER_POOL_ID --region $AWS_REGION --query 'UserPool.Status' --output text" "Enabled"
    
    # Check for test user
    if aws cognito-idp admin-get-user --user-pool-id "$USER_POOL_ID" --username "***REMOVED***" --region "$AWS_REGION" > /dev/null 2>&1; then
        log_success "✓ Test user exists"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_warning "⚠ Test user does not exist"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
else
    log_error "User Pool ID not found in stack outputs"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# Check S3 and CloudFront
log_info "=== Frontend Validation ==="
if [[ -n "$FRONTEND_BUCKET" ]]; then
    run_check "Frontend S3 bucket exists" "aws s3 ls s3://$FRONTEND_BUCKET --region $AWS_REGION" ""
    
    # Check if index.html exists
    if aws s3 ls "s3://$FRONTEND_BUCKET/index.html" --region "$AWS_REGION" > /dev/null 2>&1; then
        log_success "✓ Frontend deployed (index.html found)"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        log_warning "⚠ Frontend not deployed (index.html missing)"
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
else
    log_error "Frontend bucket name not found in stack outputs"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

if [[ -n "$CLOUDFRONT_URL" ]]; then
    run_check "CloudFront distribution accessible" "curl -s -o /dev/null -w '%{http_code}' $CLOUDFRONT_URL" "200\|403"
    log_success "CloudFront URL: $CLOUDFRONT_URL"
else
    log_error "CloudFront URL not found in stack outputs"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
echo ""

# Check CI/CD Pipeline (if enabled)
log_info "=== CI/CD Pipeline Validation ==="
if [[ -n "$PIPELINE_NAME" ]]; then
    run_check "CodePipeline exists" "aws codepipeline get-pipeline --name $PIPELINE_NAME --region $AWS_REGION --query 'pipeline.name' --output text" "$PIPELINE_NAME"
    
    # Check pipeline status
    PIPELINE_STATUS=$(aws codepipeline get-pipeline-state --name "$PIPELINE_NAME" --region "$AWS_REGION" --query 'stageStates[0].latestExecution.status' --output text 2>/dev/null || echo "Unknown")
    log_info "Pipeline Status: $PIPELINE_STATUS"
else
    log_info "CI/CD Pipeline not enabled or not found"
fi
echo ""

# Check Step Functions
log_info "=== Step Functions Validation ==="
run_check "State Machine exists" "aws stepfunctions list-state-machines --region $AWS_REGION --query 'stateMachines[?contains(name, \`${PROJECT_NAME}-${ENVIRONMENT}\`)].name' --output text" ""
echo ""

# Summary
log_info "=== Validation Summary ==="
echo "Total Checks: $TOTAL_CHECKS"
echo "Passed: $PASSED_CHECKS"
echo "Failed: $FAILED_CHECKS"
echo ""

if [[ $FAILED_CHECKS -eq 0 ]]; then
    log_success "🎉 All validation checks passed! Fresh deployment is working correctly."
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Access the frontend: $CLOUDFRONT_URL"
    echo "   2. Login with test user: ***REMOVED*** / ***REMOVED***"
    echo "   3. Test API endpoints: $API_ENDPOINT"
    echo "   4. Configure protection groups and recovery plans"
    echo ""
    exit 0
else
    log_error "❌ $FAILED_CHECKS validation checks failed. Please review the errors above."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Check CloudFormation stack events for deployment issues"
    echo "   2. Verify AWS permissions for all required services"
    echo "   3. Check CloudWatch logs for Lambda function errors"
    echo "   4. Ensure all required resources are deployed correctly"
    echo ""
    exit 1
fi