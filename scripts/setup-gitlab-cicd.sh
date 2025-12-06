#!/bin/bash
# Setup script for GitLab CI/CD pipeline
# This script helps configure GitLab CI/CD variables and validates the setup

set -e

echo "========================================="
echo "AWS DRS Orchestration - GitLab CI/CD Setup"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${NC}ℹ${NC} $1"
}

# Check if running in GitLab CI
if [ -n "$CI" ]; then
    print_error "This script should not be run in CI/CD environment"
    exit 1
fi

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install: https://aws.amazon.com/cli/"
    exit 1
fi
print_success "AWS CLI installed"

# Check Git
if ! command -v git &> /dev/null; then
    print_error "Git not found. Please install Git"
    exit 1
fi
print_success "Git installed"

# Check if in git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a Git repository"
    exit 1
fi
print_success "Git repository detected"

echo ""
echo "========================================="
echo "GitLab Repository Setup"
echo "========================================="
echo ""

# Get GitLab repository URL
read -p "Enter your GitLab repository URL (e.g., git@gitlab.aws.dev:username/aws-drs-orchestration.git): " GITLAB_URL

if [ -z "$GITLAB_URL" ]; then
    print_error "GitLab URL is required"
    exit 1
fi

# Check if GitLab remote exists
if git remote | grep -q "gitlab"; then
    print_warning "GitLab remote already exists. Updating..."
    git remote set-url gitlab "$GITLAB_URL"
else
    print_info "Adding GitLab remote..."
    git remote add gitlab "$GITLAB_URL"
fi

print_success "GitLab remote configured: $GITLAB_URL"

echo ""
echo "========================================="
echo "AWS Configuration"
echo "========================================="
echo ""

# Get AWS credentials
print_info "AWS credentials are required for CI/CD deployments"
print_warning "These will be displayed on screen. Store them securely in GitLab CI/CD variables."
echo ""

read -p "Enter AWS Access Key ID: " AWS_ACCESS_KEY_ID
read -sp "Enter AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
echo ""
read -p "Enter AWS Region [us-east-1]: " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Enter Admin Email for Cognito: " ADMIN_EMAIL

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$ADMIN_EMAIL" ]; then
    print_error "AWS credentials and admin email are required"
    exit 1
fi

echo ""
echo "========================================="
echo "Validating AWS Credentials"
echo "========================================="
echo ""

# Test AWS credentials
export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="$AWS_REGION"

if aws sts get-caller-identity > /dev/null 2>&1; then
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS credentials valid"
    print_info "AWS Account ID: $ACCOUNT_ID"
    print_info "AWS Region: $AWS_REGION"
else
    print_error "AWS credentials invalid"
    exit 1
fi

echo ""
echo "========================================="
echo "Checking S3 Deployment Bucket"
echo "========================================="
echo ""

DEPLOYMENT_BUCKET="aws-drs-orchestration"

if aws s3 ls "s3://$DEPLOYMENT_BUCKET" > /dev/null 2>&1; then
    print_success "S3 bucket exists: $DEPLOYMENT_BUCKET"
else
    print_warning "S3 bucket does not exist: $DEPLOYMENT_BUCKET"
    read -p "Create bucket? (y/n): " CREATE_BUCKET
    if [ "$CREATE_BUCKET" = "y" ]; then
        aws s3 mb "s3://$DEPLOYMENT_BUCKET" --region "$AWS_REGION"
        aws s3api put-bucket-versioning --bucket "$DEPLOYMENT_BUCKET" --versioning-configuration Status=Enabled
        print_success "S3 bucket created with versioning enabled"
    else
        print_error "S3 bucket required for CI/CD pipeline"
        exit 1
    fi
fi

echo ""
echo "========================================="
echo "GitLab CI/CD Variables Configuration"
echo "========================================="
echo ""

print_info "Configure these variables in GitLab:"
print_info "Settings → CI/CD → Variables → Add Variable"
echo ""

cat << EOF
┌─────────────────────────────┬──────────────────────────────────────────┬──────────┐
│ Variable Name               │ Value                                    │ Masked   │
├─────────────────────────────┼──────────────────────────────────────────┼──────────┤
│ AWS_ACCESS_KEY_ID           │ $AWS_ACCESS_KEY_ID                       │ Yes      │
│ AWS_SECRET_ACCESS_KEY       │ ****************************************│ Yes      │
│ ADMIN_EMAIL                 │ $ADMIN_EMAIL                             │ No       │
│ AWS_DEFAULT_REGION          │ $AWS_REGION                              │ No       │
│ DEPLOYMENT_BUCKET           │ $DEPLOYMENT_BUCKET                       │ No       │
└─────────────────────────────┴──────────────────────────────────────────┴──────────┘
EOF

echo ""
print_warning "IMPORTANT: Store AWS_SECRET_ACCESS_KEY securely!"
echo ""

# Save configuration to file
CONFIG_FILE=".gitlab-ci-config"
cat > "$CONFIG_FILE" << EOF
# GitLab CI/CD Configuration
# Generated: $(date)
# DO NOT COMMIT THIS FILE - ADD TO .gitignore

AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
ADMIN_EMAIL=$ADMIN_EMAIL
AWS_DEFAULT_REGION=$AWS_REGION
DEPLOYMENT_BUCKET=$DEPLOYMENT_BUCKET
GITLAB_URL=$GITLAB_URL
EOF

print_success "Configuration saved to $CONFIG_FILE"
print_warning "Add $CONFIG_FILE to .gitignore to prevent accidental commits"

# Add to .gitignore if not already present
if ! grep -q "$CONFIG_FILE" .gitignore 2>/dev/null; then
    echo "$CONFIG_FILE" >> .gitignore
    print_success "Added $CONFIG_FILE to .gitignore"
fi

echo ""
echo "========================================="
echo "Next Steps"
echo "========================================="
echo ""

print_info "1. Configure GitLab CI/CD variables (see table above)"
print_info "2. Push code to GitLab:"
echo "   git push gitlab main"
print_info "3. Monitor pipeline in GitLab UI"
print_info "4. Review deployment in AWS Console"
echo ""

print_success "Setup complete!"
echo ""
print_info "For more information, see: docs/CICD_PIPELINE_GUIDE.md"
