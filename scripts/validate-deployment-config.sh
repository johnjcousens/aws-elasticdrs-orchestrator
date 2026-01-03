#!/bin/bash
# Validate deployment configuration and check for hardcoded values
# Usage: ./scripts/validate-deployment-config.sh [--check-hardcoded]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

CHECK_HARDCODED=false
ERRORS_FOUND=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-hardcoded)
            CHECK_HARDCODED=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🔍 Validating AWS DRS Orchestration deployment configuration..."
echo ""

# Function to report error
report_error() {
    echo "❌ ERROR: $1"
    ERRORS_FOUND=$((ERRORS_FOUND + 1))
}

# Function to report warning
report_warning() {
    echo "⚠️  WARNING: $1"
}

# Function to report success
report_success() {
    echo "✅ $1"
}

# Check if .env.deployment exists
if [ -f "$PROJECT_ROOT/.env.deployment" ]; then
    report_success ".env.deployment file found"
    source "$PROJECT_ROOT/.env.deployment"
else
    report_warning ".env.deployment not found - using defaults from template"
    # Load defaults from template
    if [ -f "$PROJECT_ROOT/.env.deployment.template" ]; then
        source "$PROJECT_ROOT/.env.deployment.template"
    fi
fi

# Load local overrides if they exist
if [ -f "$PROJECT_ROOT/.env.deployment.local" ]; then
    report_success ".env.deployment.local found - loading overrides"
    source "$PROJECT_ROOT/.env.deployment.local"
fi

echo ""
echo "📋 Configuration Summary:"
echo "  Deployment Bucket: ${DEPLOYMENT_BUCKET:-NOT SET}"
echo "  Deployment Region: ${DEPLOYMENT_REGION:-NOT SET}"
echo "  AWS Profile: ${AWS_PROFILE:-NOT SET}"
echo "  Project Name: ${PROJECT_NAME:-NOT SET}"
echo "  Environment: ${ENVIRONMENT:-NOT SET}"
echo "  Stack Name: ${PARENT_STACK_NAME:-NOT SET}"
echo "  Cross-Account Role: ${CROSS_ACCOUNT_ROLE_NAME:-NOT SET}"
echo ""

# Validate required variables
REQUIRED_VARS=(
    "DEPLOYMENT_BUCKET"
    "DEPLOYMENT_REGION"
    "PROJECT_NAME"
    "ENVIRONMENT"
    "PARENT_STACK_NAME"
)

echo "🔧 Validating required configuration variables..."
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        report_error "$var not set"
    else
        report_success "$var is set"
    fi
done

# Validate AWS Profile
if [ -n "$AWS_PROFILE" ]; then
    if aws configure list-profiles 2>/dev/null | grep -q "^$AWS_PROFILE$"; then
        report_success "AWS Profile '$AWS_PROFILE' exists"
    else
        report_warning "AWS Profile '$AWS_PROFILE' not found in ~/.aws/config"
    fi
fi

# Check for hardcoded values if requested
if [ "$CHECK_HARDCODED" = true ]; then
    echo ""
    echo "🔍 Checking for hardcoded values..."
    
    # Check frontend config
    if [ -f "$PROJECT_ROOT/frontend/public/aws-config.json" ]; then
        if grep -q "us-east-1_" "$PROJECT_ROOT/frontend/public/aws-config.json"; then
            report_warning "frontend/public/aws-config.json contains hardcoded Cognito User Pool ID"
            echo "   Run ./scripts/update-frontend-config.sh to update from stack outputs"
        else
            report_success "frontend/public/aws-config.json appears to be parameterized"
        fi
    fi
    
    # Check for hardcoded AWS account IDs (excluding examples in help text and this validation script)
    echo "  Checking for exposed AWS Account IDs..."
    if grep -r "***REMOVED***" "$PROJECT_ROOT/scripts/" 2>/dev/null | grep -v "validate-deployment-config.sh" | grep -v "echo.*example" | grep -q .; then
        report_error "AWS Account ID found in scripts - this should be removed"
    else
        report_success "No AWS Account IDs found in scripts"
    fi
    
    # Check for hardcoded stack names in scripts
    echo "  Checking for hardcoded stack names..."
    HARDCODED_PATTERNS=(
        "aws-elasticdrs-orchestrator-dev"
        "aws-elasticdrs-orchestrator-prod"
        "aws-elasticdrs-orchestrator-test"
    )
    
    for pattern in "${HARDCODED_PATTERNS[@]}"; do
        if grep -r "$pattern" "$PROJECT_ROOT/scripts/" 2>/dev/null | grep -v ".env.deployment" | grep -q .; then
            report_warning "Hardcoded stack name '$pattern' found in scripts"
        fi
    done
    
    # Check CloudFormation templates for proper parameterization
    echo "  Checking CloudFormation templates..."
    CFN_FILES=("$PROJECT_ROOT"/cfn/*.yaml)
    for file in "${CFN_FILES[@]}"; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            
            # Check if template has Parameters section
            if grep -q "^Parameters:" "$file"; then
                report_success "$filename has Parameters section"
            else
                report_warning "$filename has no Parameters section"
            fi
            
            # Check for hardcoded role names (except in defaults)
            if grep "aws-elasticdrs-orchestrator-cross-account-role" "$file" | grep -v "Default:" | grep -q .; then
                report_error "$filename contains hardcoded cross-account role name"
            fi
        fi
    done
fi

echo ""
if [ $ERRORS_FOUND -eq 0 ]; then
    echo "🎉 Validation completed successfully!"
    echo "✅ Configuration is ready for deployment"
    exit 0
else
    echo "💥 Validation failed with $ERRORS_FOUND error(s)"
    echo "❌ Please fix the errors above before deploying"
    exit 1
fi