#!/bin/bash

# AWS DRS Orchestration - Test User Creation Script
# Creates testuser@example.com with TestPassword123! and adds to Admin RBAC group

set -e

# Default configuration
PROJECT_NAME="aws-elasticdrs-orchestrator"
ENVIRONMENT="dev"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
TEST_EMAIL="testuser@example.com"
TEST_PASSWORD="TestPassword123!"
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
AWS DRS Orchestration - Test User Creation

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -p, --project-name NAME     Project name (default: aws-elasticdrs-orchestrator)
    -e, --environment ENV       Environment (default: dev)
    -r, --region REGION         AWS region (default: us-east-1)
    --test-email EMAIL          Test user email (default: testuser@example.com)
    --test-password PASSWORD    Test user password (default: TestPassword123!)
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

EXAMPLES:
    # Create test user with defaults
    $0

    # Custom configuration
    $0 --project-name my-drs-orchestrator --environment prod --region us-west-2

    # Custom test user credentials
    $0 --test-email mytest@company.com --test-password MyPassword123!

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
        --test-email)
            TEST_EMAIL="$2"
            shift 2
            ;;
        --test-password)
            TEST_PASSWORD="$2"
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

log_info "=== Test User Creation Configuration ==="
echo "Project Name: $PROJECT_NAME"
echo "Environment:  $ENVIRONMENT"
echo "Stack Name:   $STACK_NAME"
echo "AWS Region:   $AWS_REGION"
echo "Test Email:   $TEST_EMAIL"
echo "Test Password: $TEST_PASSWORD"
echo ""

# Validation
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed or not in PATH"
    exit 1
fi

# Check AWS credentials
if ! AWS_PAGER="" aws sts get-caller-identity > /dev/null 2>&1; then
    log_error "AWS credentials not configured or invalid"
    exit 1
fi

# Get User Pool ID from stack outputs
log_info "=== Getting User Pool Information ==="
USER_POOL_ID=$(AWS_PAGER="" aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query "Stacks[0].Outputs[?OutputKey==\`UserPoolId\`].OutputValue" \
    --output text 2>/dev/null)

if [[ -z "$USER_POOL_ID" || "$USER_POOL_ID" == "None" ]]; then
    log_error "Could not retrieve User Pool ID from stack: $STACK_NAME"
    log_error "Ensure the CloudFormation stack is deployed and has UserPoolId output"
    exit 1
fi

log_success "Found User Pool ID: $USER_POOL_ID"

# Check if Admin group exists
log_info "Checking for Admin RBAC group..."
if AWS_PAGER="" aws cognito-idp get-group \
    --group-name "Admin" \
    --user-pool-id "$USER_POOL_ID" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    log_success "Admin RBAC group exists"
    ADMIN_GROUP_EXISTS="true"
else
    log_warning "Admin RBAC group does not exist - user will be created without group assignment"
    ADMIN_GROUP_EXISTS="false"
fi

# Create or update test user
log_info "=== Creating Test User ==="
log_info "Creating test user: $TEST_EMAIL"

# Check if user already exists
if AWS_PAGER="" aws cognito-idp admin-get-user \
    --user-pool-id "$USER_POOL_ID" \
    --username "$TEST_EMAIL" \
    --region "$AWS_REGION" > /dev/null 2>&1; then
    
    log_info "Test user already exists - updating password and status"
    
    # Set permanent password
    AWS_PAGER="" aws cognito-idp admin-set-user-password \
        --user-pool-id "$USER_POOL_ID" \
        --username "$TEST_EMAIL" \
        --password "$TEST_PASSWORD" \
        --permanent \
        --region "$AWS_REGION" > /dev/null 2>&1
    
    # Ensure user is confirmed
    AWS_PAGER="" aws cognito-idp admin-confirm-sign-up \
        --user-pool-id "$USER_POOL_ID" \
        --username "$TEST_EMAIL" \
        --region "$AWS_REGION" > /dev/null 2>&1 || true
    
    log_success "Test user updated successfully"
    
else
    log_info "Creating new test user"
    
    # Create new user
    AWS_PAGER="" aws cognito-idp admin-create-user \
        --user-pool-id "$USER_POOL_ID" \
        --username "$TEST_EMAIL" \
        --user-attributes Name=email,Value="$TEST_EMAIL" Name=email_verified,Value=true \
        --temporary-password "$TEST_PASSWORD" \
        --message-action SUPPRESS \
        --region "$AWS_REGION" > /dev/null 2>&1
    
    # Set permanent password (no password change required)
    AWS_PAGER="" aws cognito-idp admin-set-user-password \
        --user-pool-id "$USER_POOL_ID" \
        --username "$TEST_EMAIL" \
        --password "$TEST_PASSWORD" \
        --permanent \
        --region "$AWS_REGION" > /dev/null 2>&1
    
    log_success "Test user created successfully"
fi

# Add user to Admin group if it exists
if [[ "$ADMIN_GROUP_EXISTS" == "true" ]]; then
    log_info "=== Configuring RBAC Group Assignment ==="
    
    # Check if user is already in Admin group
    if AWS_PAGER="" aws cognito-idp admin-list-groups-for-user \
        --user-pool-id "$USER_POOL_ID" \
        --username "$TEST_EMAIL" \
        --region "$AWS_REGION" \
        --query "Groups[?GroupName=='Admin']" \
        --output text | grep -q "Admin" 2>/dev/null; then
        
        log_success "Test user is already in Admin RBAC group"
    else
        log_info "Adding test user to Admin RBAC group"
        
        if AWS_PAGER="" aws cognito-idp admin-add-user-to-group \
            --user-pool-id "$USER_POOL_ID" \
            --username "$TEST_EMAIL" \
            --group-name "Admin" \
            --region "$AWS_REGION" > /dev/null 2>&1; then
            
            log_success "Test user added to Admin RBAC group successfully"
        else
            log_error "Failed to add test user to Admin RBAC group"
            exit 1
        fi
    fi
else
    log_warning "Admin RBAC group does not exist - user created without group assignment"
    log_info "The user may have limited access until RBAC groups are properly configured"
fi

# Verify user configuration
log_info "=== Verifying Test User Configuration ==="

# Get user details
USER_STATUS=$(AWS_PAGER="" aws cognito-idp admin-get-user \
    --user-pool-id "$USER_POOL_ID" \
    --username "$TEST_EMAIL" \
    --region "$AWS_REGION" \
    --query "UserStatus" \
    --output text 2>/dev/null)

USER_GROUPS=$(AWS_PAGER="" aws cognito-idp admin-list-groups-for-user \
    --user-pool-id "$USER_POOL_ID" \
    --username "$TEST_EMAIL" \
    --region "$AWS_REGION" \
    --query "Groups[].GroupName" \
    --output text 2>/dev/null)

log_success "=== Test User Configuration Complete ==="
echo ""
echo "📋 Test User Details:"
echo "  Email:      $TEST_EMAIL"
echo "  Password:   $TEST_PASSWORD"
echo "  Status:     $USER_STATUS"
echo "  Groups:     ${USER_GROUPS:-None}"
echo ""
echo "🔐 Login Instructions:"
echo "  1. Access the frontend application"
echo "  2. Use the credentials above to login"
echo "  3. No password change required - permanent password set"
if [[ "$ADMIN_GROUP_EXISTS" == "true" && -n "$USER_GROUPS" ]]; then
    echo "  4. Full administrative access available"
else
    echo "  4. Limited access - configure RBAC groups for full functionality"
fi
echo ""

# Get application URLs from stack outputs for convenience
log_info "=== Application Access Information ==="
STACK_OUTPUTS=$(AWS_PAGER="" aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --query 'Stacks[0].Outputs' \
    --output json 2>/dev/null || echo "[]")

if [[ "$STACK_OUTPUTS" != "[]" ]]; then
    CLOUDFRONT_URL=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="CloudFrontUrl") | .OutputValue' 2>/dev/null || echo "")
    API_ENDPOINT=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="ApiEndpoint") | .OutputValue' 2>/dev/null || echo "")
    
    if [[ -n "$CLOUDFRONT_URL" && "$CLOUDFRONT_URL" != "null" ]]; then
        echo "🌐 Frontend URL: $CLOUDFRONT_URL"
    fi
    if [[ -n "$API_ENDPOINT" && "$API_ENDPOINT" != "null" ]]; then
        echo "🔗 API Endpoint: $API_ENDPOINT"
    fi
else
    log_warning "Could not retrieve application URLs from stack outputs"
fi

echo ""
log_success "🎉 Test user configuration completed successfully!"