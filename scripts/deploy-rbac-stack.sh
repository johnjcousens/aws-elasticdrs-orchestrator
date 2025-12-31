#!/bin/bash
#
# Deploy RBAC-enabled DRS Orchestration Stack
# Handles deployment with new RBAC CloudFormation template and user setup
#

set -e

# Default values
ENVIRONMENT="test"
REGION="us-east-1"
PROFILE=""
ADMIN_EMAIL=""
DEPLOYMENT_BUCKET="aws-drs-orchestration"
PROJECT_NAME="drs-orchestration"
DRY_RUN=false
SKIP_USER_SETUP=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Deploy DRS Orchestration with RBAC support"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV     Environment (test, dev, prod) [default: test]"
    echo "  -r, --region REGION       AWS Region [default: us-east-1]"
    echo "  -p, --profile PROFILE     AWS Profile to use"
    echo "  -a, --admin-email EMAIL   Admin email for Cognito (required)"
    echo "  -b, --bucket BUCKET       S3 deployment bucket [default: aws-drs-orchestration]"
    echo "  -n, --project-name NAME   Project name [default: drs-orchestration]"
    echo "  --dry-run                 Show what would be deployed without executing"
    echo "  --skip-user-setup         Skip initial user setup"
    echo "  -h, --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --admin-email admin@company.com"
    echo "  $0 --environment prod --admin-email admin@company.com --profile production"
    echo "  $0 --dry-run --admin-email admin@company.com"
}

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -a|--admin-email)
            ADMIN_EMAIL="$2"
            shift 2
            ;;
        -b|--bucket)
            DEPLOYMENT_BUCKET="$2"
            shift 2
            ;;
        -n|--project-name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-user-setup)
            SKIP_USER_SETUP=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate required parameters
if [[ -z "$ADMIN_EMAIL" ]]; then
    error "Admin email is required. Use --admin-email option."
fi

# Validate email format
if [[ ! "$ADMIN_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    error "Invalid email format: $ADMIN_EMAIL"
fi

# Set AWS CLI profile if provided
AWS_CMD="aws"
if [[ -n "$PROFILE" ]]; then
    AWS_CMD="aws --profile $PROFILE"
    export AWS_PROFILE="$PROFILE"
fi

STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

log "Starting RBAC deployment for DRS Orchestration"
log "Environment: $ENVIRONMENT"
log "Region: $REGION"
log "Stack Name: $STACK_NAME"
log "Admin Email: $ADMIN_EMAIL"
log "Deployment Bucket: $DEPLOYMENT_BUCKET"
if [[ -n "$PROFILE" ]]; then
    log "AWS Profile: $PROFILE"
fi

if [[ "$DRY_RUN" == "true" ]]; then
    warning "DRY RUN MODE - No actual deployment will occur"
fi

# Check if deployment bucket exists
log "Checking deployment bucket..."
if ! $AWS_CMD s3api head-bucket --bucket "$DEPLOYMENT_BUCKET" --region "$REGION" >/dev/null 2>&1; then
    error "Deployment bucket '$DEPLOYMENT_BUCKET' does not exist or is not accessible in region '$REGION'"
fi

# Check if RBAC template exists in S3
log "Verifying RBAC CloudFormation template..."
if ! $AWS_CMD s3api head-object --bucket "$DEPLOYMENT_BUCKET" --key "cfn/api-stack-rbac.yaml" --region "$REGION" >/dev/null 2>&1; then
    error "RBAC template 'cfn/api-stack-rbac.yaml' not found in deployment bucket. Please sync templates first."
fi

# Check if master template is updated to use RBAC stack
log "Verifying master template uses RBAC stack..."
MASTER_TEMPLATE_URL="https://s3.amazonaws.com/${DEPLOYMENT_BUCKET}/cfn/master-template.yaml"

if [[ "$DRY_RUN" == "false" ]]; then
    # Download and check master template
    TEMP_MASTER=$(mktemp)
    $AWS_CMD s3 cp "s3://${DEPLOYMENT_BUCKET}/cfn/master-template.yaml" "$TEMP_MASTER" --region "$REGION" >/dev/null 2>&1
    
    if ! grep -q "api-stack-rbac.yaml" "$TEMP_MASTER"; then
        warning "Master template may not be using RBAC stack. Continuing anyway..."
    fi
    
    rm -f "$TEMP_MASTER"
fi

# Prepare CloudFormation parameters
PARAMETER_OVERRIDES="ProjectName=$PROJECT_NAME Environment=$ENVIRONMENT SourceBucket=$DEPLOYMENT_BUCKET AdminEmail=$ADMIN_EMAIL"

# Check if stack exists
STACK_EXISTS=false
if $AWS_CMD cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" >/dev/null 2>&1; then
    STACK_EXISTS=true
    log "Stack '$STACK_NAME' exists - will update"
else
    log "Stack '$STACK_NAME' does not exist - will create"
fi

if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY RUN: Would deploy CloudFormation stack with parameters:"
    echo "  - $PARAMETER_OVERRIDES"
    log "DRY RUN: Template URL: $MASTER_TEMPLATE_URL"
    exit 0
fi

# Deploy CloudFormation stack
log "Deploying CloudFormation stack..."

# Download template locally for deploy command
TEMP_TEMPLATE=$(mktemp)
$AWS_CMD s3 cp "s3://${DEPLOYMENT_BUCKET}/cfn/master-template.yaml" "$TEMP_TEMPLATE" --region "$REGION" >/dev/null 2>&1

DEPLOY_CMD="$AWS_CMD cloudformation deploy \
    --template-file $TEMP_TEMPLATE \
    --stack-name $STACK_NAME \
    --parameter-overrides $PARAMETER_OVERRIDES \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --region $REGION \
    --no-fail-on-empty-changeset"

echo "Executing: $DEPLOY_CMD"

if $DEPLOY_CMD; then
    success "CloudFormation stack deployed successfully"
    rm -f "$TEMP_TEMPLATE"
else
    rm -f "$TEMP_TEMPLATE"
    error "CloudFormation deployment failed"
fi

# Get stack outputs
log "Retrieving stack outputs..."

USER_POOL_ID=$($AWS_CMD cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text)

API_ENDPOINT=$($AWS_CMD cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
    --output text)

CLOUDFRONT_URL=$($AWS_CMD cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
    --output text)

if [[ -z "$USER_POOL_ID" ]]; then
    error "Failed to retrieve User Pool ID from stack outputs"
fi

success "Stack deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  Stack Name: $STACK_NAME"
echo "  User Pool ID: $USER_POOL_ID"
echo "  API Endpoint: $API_ENDPOINT"
echo "  Frontend URL: https://$CLOUDFRONT_URL"
echo ""

# User setup
if [[ "$SKIP_USER_SETUP" == "false" ]]; then
    log "Setting up initial admin user..."
    
    # Check if user management script exists
    USER_SCRIPT="scripts/manage-user-roles.py"
    if [[ ! -f "$USER_SCRIPT" ]]; then
        warning "User management script not found at $USER_SCRIPT"
        warning "You'll need to create users manually in the Cognito console"
    else
        # Generate temporary password
        TEMP_PASSWORD=$(openssl rand -base64 12 | tr -d "=+/" | cut -c1-12)
        
        log "Creating admin user with email: $ADMIN_EMAIL"
        
        # Create admin user with DRS-Administrator role
        if python3 "$USER_SCRIPT" \
            --user-pool-id "$USER_POOL_ID" \
            --region "$REGION" \
            create-user \
            --email "$ADMIN_EMAIL" \
            --temp-password "$TEMP_PASSWORD" \
            --role "DRS-Administrator"; then
            
            success "Admin user created successfully!"
            echo ""
            echo "🔐 Admin User Credentials:"
            echo "  Email: $ADMIN_EMAIL"
            echo "  Temporary Password: $TEMP_PASSWORD"
            echo "  Role: DRS-Administrator (Full Access)"
            echo ""
            warning "The user must change their password on first login"
            
        else
            warning "Failed to create admin user automatically"
            warning "Please create the user manually using the Cognito console"
        fi
    fi
else
    log "Skipping user setup (--skip-user-setup specified)"
fi

# Display next steps
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Access the application:"
echo "   Frontend: https://$CLOUDFRONT_URL"
echo "   API: $API_ENDPOINT"
echo ""
echo "2. Manage users and roles:"
echo "   python3 scripts/manage-user-roles.py --user-pool-id $USER_POOL_ID list-users"
echo "   python3 scripts/manage-user-roles.py --user-pool-id $USER_POOL_ID list-roles"
echo ""
echo "3. Add more users:"
echo "   python3 scripts/manage-user-roles.py --user-pool-id $USER_POOL_ID create-user \\"
echo "     --email user@company.com --temp-password TempPass123! --role DRS-Operator"
echo ""
echo "4. Test the RBAC system:"
echo "   - Login with different user roles"
echo "   - Verify permission restrictions work correctly"
echo "   - Check API endpoints return appropriate 403 errors for unauthorized access"
echo ""

success "RBAC deployment completed successfully! 🎉"