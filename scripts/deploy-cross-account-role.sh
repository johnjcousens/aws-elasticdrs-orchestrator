#!/bin/bash
set -e

# Deploy Cross-Account Role for DRS Orchestration
# This script deploys the cross-account role in a spoke account

# Configuration
HUB_ACCOUNT_ID="${HUB_ACCOUNT_ID:-438465159935}"
ENVIRONMENT="${ENVIRONMENT:-test}"
REGION="${REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-drs-orchestration}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Deploy cross-account role for DRS Orchestration in spoke account"
    echo ""
    echo "Options:"
    echo "  -h, --hub-account-id ACCOUNT_ID    Hub account ID (default: $HUB_ACCOUNT_ID)"
    echo "  -e, --environment ENV              Environment (default: $ENVIRONMENT)"
    echo "  -r, --region REGION                AWS region (default: $REGION)"
    echo "  -p, --profile PROFILE              AWS profile to use"
    echo "  --validate                         Validate deployment after creation"
    echo "  --help                             Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  HUB_ACCOUNT_ID                     Hub account ID"
    echo "  ENVIRONMENT                        Environment name"
    echo "  REGION                             AWS region"
    echo "  AWS_PROFILE                        AWS profile to use"
    echo ""
    echo "Examples:"
    echo "  $0 --hub-account-id 123456789012 --environment prod"
    echo "  $0 --profile spoke-account --validate"
}

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
VALIDATE=false
AWS_PROFILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--hub-account-id)
            HUB_ACCOUNT_ID="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -p|--profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --validate)
            VALIDATE=true
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ ! "$HUB_ACCOUNT_ID" =~ ^[0-9]{12}$ ]]; then
    error "Invalid hub account ID: $HUB_ACCOUNT_ID (must be 12 digits)"
    exit 1
fi

if [[ ! "$ENVIRONMENT" =~ ^(dev|test|qa|prod)$ ]]; then
    error "Invalid environment: $ENVIRONMENT (must be dev, test, qa, or prod)"
    exit 1
fi

# Set AWS profile if provided
if [[ -n "$AWS_PROFILE" ]]; then
    export AWS_PROFILE
    log "Using AWS profile: $AWS_PROFILE"
fi

# Get current account ID
log "Getting current account ID..."
CURRENT_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text --region "$REGION")
if [[ $? -ne 0 ]]; then
    error "Failed to get current account ID. Check AWS credentials."
    exit 1
fi

log "Current account ID: $CURRENT_ACCOUNT_ID"
log "Hub account ID: $HUB_ACCOUNT_ID"

if [[ "$CURRENT_ACCOUNT_ID" == "$HUB_ACCOUNT_ID" ]]; then
    warning "You are deploying in the hub account. This should be deployed in spoke accounts."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Deployment cancelled"
        exit 0
    fi
fi

# Check if CloudFormation template exists
TEMPLATE_FILE="cfn/cross-account-role-stack.yaml"
if [[ ! -f "$TEMPLATE_FILE" ]]; then
    error "CloudFormation template not found: $TEMPLATE_FILE"
    error "Please run this script from the project root directory"
    exit 1
fi

# Deploy the stack
STACK_NAME="drs-orchestration-cross-account-role-${ENVIRONMENT}"

log "Deploying cross-account role stack..."
log "Stack name: $STACK_NAME"
log "Template: $TEMPLATE_FILE"
log "Region: $REGION"

aws cloudformation deploy \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        SourceAccountNumber="$HUB_ACCOUNT_ID" \
        Environment="$ENVIRONMENT" \
        ProjectName="$PROJECT_NAME" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --no-fail-on-empty-changeset

if [[ $? -eq 0 ]]; then
    success "Cross-account role stack deployed successfully"
else
    error "Failed to deploy cross-account role stack"
    exit 1
fi

# Get stack outputs
log "Getting stack outputs..."
ROLE_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`CrossAccountRoleArn`].OutputValue' \
    --output text \
    --region "$REGION")

ROLE_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`CrossAccountRoleName`].OutputValue' \
    --output text \
    --region "$REGION")

EXTERNAL_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ExternalId`].OutputValue' \
    --output text \
    --region "$REGION")

success "Cross-account role created:"
echo "  Role ARN: $ROLE_ARN"
echo "  Role Name: $ROLE_NAME"
echo "  External ID: $EXTERNAL_ID"

# Validation
if [[ "$VALIDATE" == true ]]; then
    log "Validating cross-account role..."
    
    # Check if role exists
    aws iam get-role --role-name "$ROLE_NAME" --region "$REGION" > /dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        success "Role exists and is accessible"
    else
        error "Role validation failed"
        exit 1
    fi
    
    # Check trust policy
    log "Checking trust policy..."
    TRUST_POLICY=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.AssumeRolePolicyDocument' --region "$REGION")
    if echo "$TRUST_POLICY" | grep -q "$HUB_ACCOUNT_ID"; then
        success "Trust policy includes hub account"
    else
        warning "Trust policy may not include hub account correctly"
    fi
    
    success "Validation completed"
fi

# Registration instructions
echo ""
echo "============================================================"
echo "Next Steps:"
echo "============================================================"
echo ""
echo "1. Register this account in the hub account:"
echo ""
echo "   aws dynamodb put-item \\"
echo "     --table-name accounts-${ENVIRONMENT} \\"
echo "     --item '{"
echo "       \"AccountId\": {\"S\": \"${CURRENT_ACCOUNT_ID}\"},"
echo "       \"AccountName\": {\"S\": \"Spoke Account\"},"
echo "       \"CrossAccountRoleArn\": {\"S\": \"${ROLE_ARN}\"},"
echo "       \"Regions\": {\"SS\": [\"us-east-1\", \"us-west-2\"]},"
echo "       \"RegisteredAt\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"},"
echo "       \"Status\": {\"S\": \"ACTIVE\"}"
echo "     }' \\"
echo "     --region ${REGION}"
echo ""
echo "2. Test role assumption from hub account:"
echo ""
echo "   aws sts assume-role \\"
echo "     --role-arn \"${ROLE_ARN}\" \\"
echo "     --role-session-name \"test-cross-account\" \\"
echo "     --external-id \"${EXTERNAL_ID}\""
echo ""
echo "3. Create protection groups with account ID:"
echo ""
echo "   Protection Group ID format: pg-name-${CURRENT_ACCOUNT_ID}"
echo ""
echo "============================================================"

success "Cross-account role deployment completed!"