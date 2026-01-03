#!/bin/bash

# AWS DRS Orchestration - Fresh Deployment Setup Script
# This script sets up a complete fresh deployment of the AWS DRS Orchestration platform
# with the new naming convention and CI/CD pipeline

set -e  # Exit on any error

# Default configuration
PROJECT_NAME="aws-elasticdrs-orchestrator"
ENVIRONMENT="dev"
DEPLOYMENT_BUCKET="aws-elasticdrs-orchestrator"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
ADMIN_EMAIL=""
ENABLE_CICD="true"
DRY_RUN="false"
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
AWS DRS Orchestration - Fresh Deployment Setup

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -p, --project-name NAME     Project name (default: aws-elasticdrs-orchestrator)
    -e, --environment ENV       Environment (default: dev)
    -b, --bucket BUCKET         S3 deployment bucket (default: aws-elasticdrs-orchestrator)
    -r, --region REGION         AWS region (default: us-east-1)
    -a, --admin-email EMAIL     Admin email for Cognito (REQUIRED)
    --enable-cicd               Enable CI/CD pipeline (default: true)
    --disable-cicd              Disable CI/CD pipeline
    --dry-run                   Show what would be done without executing
    -v, --verbose               Enable verbose output
    -h, --help                  Show this help message

EXAMPLES:
    # Basic fresh deployment
    $0 --admin-email admin@company.com

    # Custom configuration
    $0 --project-name my-drs-orchestrator \\
       --environment prod \\
       --region us-west-2 \\
       --admin-email admin@company.com

    # Dry run to see what would be deployed
    $0 --admin-email admin@company.com --dry-run

PREREQUISITES:
    - AWS CLI configured with appropriate permissions
    - jq installed for JSON processing
    - Valid AWS credentials with CloudFormation, S3, IAM permissions

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
        -b|--bucket)
            DEPLOYMENT_BUCKET="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -a|--admin-email)
            ADMIN_EMAIL="$2"
            shift 2
            ;;
        --enable-cicd)
            ENABLE_CICD="true"
            shift
            ;;
        --disable-cicd)
            ENABLE_CICD="false"
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
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

# Validation
if [[ -z "$ADMIN_EMAIL" ]]; then
    log_error "Admin email is required. Use --admin-email option."
    exit 1
fi

if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed or not in PATH"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    log_error "jq is not installed or not in PATH"
    exit 1
fi

# Validate email format
if [[ ! "$ADMIN_EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    log_error "Invalid email format: $ADMIN_EMAIL"
    exit 1
fi

# Display configuration
log_info "=== Fresh Deployment Configuration ==="
echo "Project Name:      $PROJECT_NAME"
echo "Environment:       $ENVIRONMENT"
echo "Stack Name:        $STACK_NAME"
echo "Deployment Bucket: $DEPLOYMENT_BUCKET"
echo "AWS Region:        $AWS_REGION"
echo "Admin Email:       $ADMIN_EMAIL"
echo "Enable CI/CD:      $ENABLE_CICD"
echo "Dry Run:           $DRY_RUN"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    log_warning "DRY RUN MODE - No actual changes will be made"
    echo ""
fi

# Function to execute commands with dry run support
execute_command() {
    local cmd="$1"
    local description="$2"
    
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Command: $cmd"
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would execute: $description"
        return 0
    else
        log_info "Executing: $description"
        if [[ "$VERBOSE" == "true" ]]; then
            eval "$cmd"
        else
            eval "$cmd" > /dev/null 2>&1
        fi
        return $?
    fi
}

# Check AWS credentials and permissions
check_aws_credentials() {
    log_info "=== Checking AWS Credentials and Permissions ==="
    
    # Check if AWS credentials are configured
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        log_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    local account_id
    local user_arn
    account_id=$(aws sts get-caller-identity --query Account --output text)
    user_arn=$(aws sts get-caller-identity --query Arn --output text)
    
    log_success "AWS credentials valid"
    echo "Account ID: $account_id"
    echo "User/Role:  $user_arn"
    echo "Region:     $AWS_REGION"
    echo ""
    
    # Test basic permissions
    log_info "Testing AWS permissions..."
    
    # Test S3 permissions
    if aws s3 ls > /dev/null 2>&1; then
        log_success "S3 permissions: OK"
    else
        log_error "S3 permissions: FAILED"
        exit 1
    fi
    
    # Test CloudFormation permissions
    if aws cloudformation list-stacks --region "$AWS_REGION" > /dev/null 2>&1; then
        log_success "CloudFormation permissions: OK"
    else
        log_error "CloudFormation permissions: FAILED"
        exit 1
    fi
    
    # Test IAM permissions
    if aws iam list-roles --max-items 1 > /dev/null 2>&1; then
        log_success "IAM permissions: OK"
    else
        log_warning "IAM permissions: LIMITED (may cause deployment issues)"
    fi
    
    echo ""
}

# Create or verify S3 deployment bucket
setup_deployment_bucket() {
    log_info "=== Setting Up Deployment Bucket ==="
    
    # Check if bucket exists
    if aws s3 ls "s3://$DEPLOYMENT_BUCKET" > /dev/null 2>&1; then
        log_success "Deployment bucket exists: s3://$DEPLOYMENT_BUCKET"
    else
        log_info "Creating deployment bucket: s3://$DEPLOYMENT_BUCKET"
        
        if [[ "$AWS_REGION" == "us-east-1" ]]; then
            execute_command "aws s3 mb s3://$DEPLOYMENT_BUCKET --region $AWS_REGION" \
                "Create S3 bucket in us-east-1"
        else
            execute_command "aws s3 mb s3://$DEPLOYMENT_BUCKET --region $AWS_REGION --create-bucket-configuration LocationConstraint=$AWS_REGION" \
                "Create S3 bucket in $AWS_REGION"
        fi
        
        # Enable versioning
        execute_command "aws s3api put-bucket-versioning --bucket $DEPLOYMENT_BUCKET --versioning-configuration Status=Enabled" \
            "Enable bucket versioning"
        
        # Block public access
        execute_command "aws s3api put-public-access-block --bucket $DEPLOYMENT_BUCKET --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
            "Block public access"
        
        log_success "Deployment bucket created and configured"
    fi
    
    echo ""
}

# Upload deployment artifacts
upload_artifacts() {
    log_info "=== Uploading Deployment Artifacts ==="
    
    # Check if we're in the project root
    if [[ ! -f "cfn/master-template.yaml" ]]; then
        log_error "Must run from project root directory (cfn/master-template.yaml not found)"
        exit 1
    fi
    
    # Upload CloudFormation templates
    execute_command "aws s3 sync cfn/ s3://$DEPLOYMENT_BUCKET/cfn/ --delete --exclude '*.md'" \
        "Upload CloudFormation templates"
    
    # Upload BuildSpec files
    if [[ -d "buildspecs" ]]; then
        execute_command "aws s3 sync buildspecs/ s3://$DEPLOYMENT_BUCKET/buildspecs/ --delete" \
            "Upload BuildSpec files"
    fi
    
    # Upload scripts
    execute_command "aws s3 sync scripts/ s3://$DEPLOYMENT_BUCKET/scripts/ --delete --exclude '*.md'" \
        "Upload deployment scripts"
    
    # Build and upload Lambda packages if they exist
    if [[ -d "lambda" ]]; then
        log_info "Building and uploading Lambda packages..."
        
        cd lambda
        for dir in */; do
            if [[ -d "$dir" && -f "$dir/index.py" ]]; then
                log_info "Building Lambda package: $dir"
                
                cd "$dir"
                
                # Install dependencies if requirements.txt exists
                if [[ -f "requirements.txt" ]]; then
                    execute_command "pip install -r requirements.txt -t . --no-deps" \
                        "Install dependencies for $dir"
                fi
                
                # Create deployment package
                execute_command "zip -r ../${dir%/}.zip . -x '*.pyc' '__pycache__/*' 'tests/*' '*.md' '.git*' 'requirements.txt'" \
                    "Create deployment package for $dir"
                
                cd ..
            fi
        done
        
        # Upload Lambda packages
        execute_command "aws s3 sync . s3://$DEPLOYMENT_BUCKET/lambda/ --exclude '*' --include '*.zip' --delete" \
            "Upload Lambda packages"
        
        cd ..
    fi
    
    # Build and upload frontend if it exists
    if [[ -d "frontend" && -f "frontend/package.json" ]]; then
        log_info "Building and uploading frontend..."
        
        cd frontend
        
        execute_command "npm ci" "Install frontend dependencies"
        execute_command "npm run build" "Build frontend application"
        execute_command "aws s3 sync dist/ s3://$DEPLOYMENT_BUCKET/frontend/ --delete" \
            "Upload frontend build"
        
        cd ..
    fi
    
    log_success "All artifacts uploaded to s3://$DEPLOYMENT_BUCKET/"
    echo ""
}

# Deploy CloudFormation stack
deploy_infrastructure() {
    log_info "=== Deploying Infrastructure ==="
    
    # Check if stack exists
    local stack_exists="false"
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
        stack_exists="true"
        log_info "Stack $STACK_NAME exists - will update"
    else
        log_info "Stack $STACK_NAME does not exist - will create"
    fi
    
    # Prepare parameters
    local parameters=(
        "ParameterKey=ProjectName,ParameterValue=$PROJECT_NAME"
        "ParameterKey=Environment,ParameterValue=$ENVIRONMENT"
        "ParameterKey=SourceBucket,ParameterValue=$DEPLOYMENT_BUCKET"
        "ParameterKey=AdminEmail,ParameterValue=$ADMIN_EMAIL"
        "ParameterKey=EnableAutomatedDeployment,ParameterValue=$ENABLE_CICD"
        "ParameterKey=EnableSecurityStack,ParameterValue=false"
        "ParameterKey=GitHubRepositoryUrl,ParameterValue=https://github.com/johnjcousens/aws-elasticdrs-orchestrator"
    )
    
    local param_string=""
    for param in "${parameters[@]}"; do
        param_string="$param_string $param"
    done
    
    # Deploy stack
    local deploy_cmd="aws cloudformation deploy \
        --template-file cfn/master-template.yaml \
        --stack-name $STACK_NAME \
        --region $AWS_REGION \
        --parameter-overrides $param_string \
        --capabilities CAPABILITY_NAMED_IAM \
        --tags \
            Project=$PROJECT_NAME \
            Environment=$ENVIRONMENT \
            DeployedBy=FreshDeploymentScript \
        --no-fail-on-empty-changeset"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would deploy CloudFormation stack with parameters:"
        for param in "${parameters[@]}"; do
            echo "  $param"
        done
        echo ""
        return 0
    fi
    
    log_info "Deploying CloudFormation stack (this may take 15-30 minutes)..."
    
    if [[ "$VERBOSE" == "true" ]]; then
        eval "$deploy_cmd"
    else
        eval "$deploy_cmd" 2>&1 | grep -E "(CREATE|UPDATE|DELETE)_" || true
    fi
    
    if eval "$deploy_cmd" > /dev/null 2>&1; then
        log_success "Infrastructure deployment completed"
    else
        log_error "Infrastructure deployment failed"
        exit 1
    fi
    
    echo ""
}

# Get and display stack outputs
display_outputs() {
    log_info "=== Deployment Outputs ==="
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would display stack outputs"
        return 0
    fi
    
    local outputs
    outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs' \
        --output json 2>/dev/null)
    
    if [[ $? -eq 0 && "$outputs" != "null" ]]; then
        echo "$outputs" | jq -r '.[] | "\(.OutputKey): \(.OutputValue)"' | while read -r line; do
            echo "  $line"
        done
        
        # Extract key URLs
        local api_endpoint
        local cloudfront_url
        local pipeline_url
        api_endpoint=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="ApiEndpoint") | .OutputValue')
        cloudfront_url=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="CloudFrontUrl") | .OutputValue')
        pipeline_url=$(echo "$outputs" | jq -r '.[] | select(.OutputKey=="PipelineUrl") | .OutputValue')
        
        echo ""
        log_success "=== Application URLs ==="
        if [[ "$cloudfront_url" != "null" && -n "$cloudfront_url" ]]; then
            echo "🌐 Frontend:  $cloudfront_url"
        fi
        if [[ "$api_endpoint" != "null" && -n "$api_endpoint" ]]; then
            echo "🔗 API:       $api_endpoint"
        fi
        if [[ "$pipeline_url" != "null" && -n "$pipeline_url" && "$ENABLE_CICD" == "true" ]]; then
            echo "🚀 Pipeline:  $pipeline_url"
        fi
    else
        log_warning "Could not retrieve stack outputs"
    fi
    
    echo ""
}

# Create test user (post-deployment)
create_test_user() {
    log_info "=== Creating Test User ==="
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create test user: testuser@example.com"
        return 0
    fi
    
    # Get User Pool ID from stack outputs
    local user_pool_id
    user_pool_id=$(AWS_PAGER="" aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey==\`UserPoolId\`].OutputValue" \
        --output text 2>/dev/null)
    
    if [[ -z "$user_pool_id" || "$user_pool_id" == "None" ]]; then
        log_warning "Could not retrieve User Pool ID - test user creation will be handled by post-deployment script"
        log_info "Run scripts/create-test-user.sh after deployment completes"
        return 0
    fi
    
    # Create test user for immediate testing
    local test_email="testuser@example.com"
    local test_password="TestPassword123!"
    
    log_info "Creating test user: $test_email"
    
    # Check if user already exists
    if AWS_PAGER="" aws cognito-idp admin-get-user \
        --user-pool-id "$user_pool_id" \
        --username "$test_email" \
        --region "$AWS_REGION" > /dev/null 2>&1; then
        log_info "Test user already exists - updating password"
        
        AWS_PAGER="" aws cognito-idp admin-set-user-password \
            --user-pool-id "$user_pool_id" \
            --username "$test_email" \
            --password "$test_password" \
            --permanent \
            --region "$AWS_REGION" > /dev/null 2>&1
    else
        # Create new user
        AWS_PAGER="" aws cognito-idp admin-create-user \
            --user-pool-id "$user_pool_id" \
            --username "$test_email" \
            --user-attributes Name=email,Value="$test_email" Name=email_verified,Value=true \
            --temporary-password "$test_password" \
            --message-action SUPPRESS \
            --region "$AWS_REGION" > /dev/null 2>&1
        
        # Set permanent password
        AWS_PAGER="" aws cognito-idp admin-set-user-password \
            --user-pool-id "$user_pool_id" \
            --username "$test_email" \
            --password "$test_password" \
            --permanent \
            --region "$AWS_REGION" > /dev/null 2>&1
    fi
    
    # Add user to Admin group (if it exists)
    if AWS_PAGER="" aws cognito-idp admin-add-user-to-group \
        --user-pool-id "$user_pool_id" \
        --username "$test_email" \
        --group-name "Admin" \
        --region "$AWS_REGION" > /dev/null 2>&1; then
        log_success "Test user added to Admin RBAC group"
    else
        log_warning "Could not add user to Admin group - will be handled by post-deployment script"
    fi
    
    log_success "Test user created successfully"
    echo "  Email:    $test_email"
    echo "  Password: $test_password"
    echo ""
}

# Main execution
main() {
    log_info "Starting AWS DRS Orchestration Fresh Deployment"
    echo ""
    
    # Set AWS region
    export AWS_DEFAULT_REGION="$AWS_REGION"
    
    # Execute deployment steps
    check_aws_credentials
    setup_deployment_bucket
    upload_artifacts
    deploy_infrastructure
    display_outputs
    create_test_user
    
    # Final success message
    log_success "=== Fresh Deployment Completed Successfully! ==="
    echo ""
    echo "🎉 Your AWS DRS Orchestration platform is now deployed!"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Access the frontend using the CloudFront URL above"
    echo "   2. Login with admin email: jocousen@amazon.com (check email for temp password)"
    echo "   3. Create test user: ./scripts/create-test-user.sh"
    echo "   4. Configure your first protection group"
    echo "   5. Set up cross-account roles for DRS operations"
    echo ""
    if [[ "$ENABLE_CICD" == "true" ]]; then
        echo "🚀 CI/CD Pipeline:"
        echo "   - Your CodePipeline is ready for automated deployments"
        echo "   - Push code to the CodeCommit repository to trigger builds"
        echo "   - Monitor pipeline progress in the AWS Console"
        echo ""
    fi
    echo "🔧 Test User Creation:"
    echo "   - Run: ./scripts/create-test-user.sh"
    echo "   - Creates: testuser@example.com / TestPassword123!"
    echo "   - Adds user to Admin RBAC group for full access"
    echo ""
    echo "📚 Documentation: docs/deployment/FRESH_DEPLOYMENT_GUIDE.md"
    echo "🔧 Troubleshooting: docs/guides/TROUBLESHOOTING_GUIDE.md"
    echo ""
}

# Execute main function
main "$@"