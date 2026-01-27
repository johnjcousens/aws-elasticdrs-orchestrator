#!/bin/bash
#
# Local CI/CD Simulation Script
# Simulates deployment workflow for local development
#
# Repository Structure:
#   This script works from the repository root directory.
#   All paths are relative to the repository root.
#
# Usage:
#   ./scripts/local-deploy.sh [environment] [deployment-type]
#
# Arguments:
#   environment: dev (default), test, prod
#   deployment-type: full (default), frontend-only, lambda-only
#
# Examples:
#   ./scripts/local-deploy.sh dev full
#   ./scripts/local-deploy.sh dev frontend-only
#   ./scripts/local-deploy.sh dev lambda-only

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root for all operations
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-dev}"
DEPLOYMENT_TYPE="${2:-full}"
AWS_REGION="us-east-1"
PROJECT_NAME="aws-drs-orchestration"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
DEPLOYMENT_BUCKET="${PROJECT_NAME}-${ENVIRONMENT}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
    echo -e "${RED}❌ Invalid environment: $ENVIRONMENT${NC}"
    echo "Valid environments: dev, test, prod"
    exit 1
fi

# Validate deployment type
if [[ ! "$DEPLOYMENT_TYPE" =~ ^(full|frontend-only|lambda-only)$ ]]; then
    echo -e "${RED}❌ Invalid deployment type: $DEPLOYMENT_TYPE${NC}"
    echo "Valid types: full, frontend-only, lambda-only"
    exit 1
fi

# Stack protection check
if [[ "$STACK_NAME" == *"-test"* ]] || [[ "$STACK_NAME" == "aws-elasticdrs-orchestrator"* ]]; then
    echo -e "${RED}❌ CRITICAL: Cannot deploy to protected stack!${NC}"
    echo "Stack '$STACK_NAME' appears to be a protected production stack."
    echo "Use 'aws-drs-orchestration-dev' for development."
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AWS DRS Orchestration - Local CI/CD Deployment           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Environment:${NC}      $ENVIRONMENT"
echo -e "${GREEN}Deployment Type:${NC}  $DEPLOYMENT_TYPE"
echo -e "${GREEN}Stack Name:${NC}       $STACK_NAME"
echo -e "${GREEN}Bucket:${NC}           $DEPLOYMENT_BUCKET"
echo -e "${GREEN}Region:${NC}           $AWS_REGION"
echo ""

# Verify AWS credentials
echo -e "${BLUE}[0/6] Verifying AWS Credentials...${NC}"
if ! aws sts get-caller-identity --region "$AWS_REGION" > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✓ AWS Account: $ACCOUNT_ID${NC}"
echo ""

# Stage 1: Validate
if [[ "$DEPLOYMENT_TYPE" != "frontend-only" ]]; then
    echo -e "${BLUE}[1/6] Validation Stage${NC}"
    echo "Running CloudFormation validation..."
    
    for template in cfn/*.yaml; do
        echo "  Validating $(basename $template)..."
        
        # Check file size
        FILE_SIZE=$(stat -f%z "$template" 2>/dev/null || stat -c%s "$template")
        
        if [ "$FILE_SIZE" -gt 51200 ]; then
            # Large template - use S3
            TEMPLATE_NAME=$(basename "$template")
            aws s3 cp "$template" "s3://${DEPLOYMENT_BUCKET}/cfn-validation/${TEMPLATE_NAME}" --quiet
            aws cloudformation validate-template \
                --template-url "https://${DEPLOYMENT_BUCKET}.s3.amazonaws.com/cfn-validation/${TEMPLATE_NAME}" \
                --region "$AWS_REGION" > /dev/null
            aws s3 rm "s3://${DEPLOYMENT_BUCKET}/cfn-validation/${TEMPLATE_NAME}" --quiet
        else
            # Small template - inline
            aws cloudformation validate-template \
                --template-body file://$template \
                --region "$AWS_REGION" > /dev/null
        fi
    done
    
    echo -e "${GREEN}✓ CloudFormation templates validated${NC}"
    
    # Python code quality (non-blocking)
    if command -v flake8 &> /dev/null; then
        echo "Running Python code quality checks..."
        flake8 lambda/ --config .flake8 --count --statistics || true
    fi
    
    echo ""
fi

# Stage 2: Security Scan (non-blocking)
echo -e "${BLUE}[2/6] Security Scan Stage${NC}"
echo "Running security checks..."

if command -v bandit &> /dev/null; then
    bandit -r lambda/ scripts/ -ll || true
else
    echo -e "${YELLOW}⚠ Bandit not installed - skipping Python security scan${NC}"
fi

echo -e "${GREEN}✓ Security scan complete${NC}"
echo ""

# Stage 3: Build
echo -e "${BLUE}[3/6] Build Stage${NC}"
BUILD_START=$(date +%s)

if [[ "$DEPLOYMENT_TYPE" != "frontend-only" ]]; then
    echo "Building Lambda packages..."
    echo "  → Running package_lambda.py..."
    python3 package_lambda.py
    
    # Show package sizes
    echo "  → Lambda packages created:"
    for pkg in build/lambda/*.zip; do
        if [ -f "$pkg" ]; then
            SIZE=$(ls -lh "$pkg" | awk '{print $5}')
            echo "    • $(basename $pkg): $SIZE"
        fi
    done
    
    BUILD_END=$(date +%s)
    BUILD_DURATION=$((BUILD_END - BUILD_START))
    echo -e "${GREEN}✓ Lambda packages built (${BUILD_DURATION}s)${NC}"
fi

# Note: Frontend is now built by FrontendBuilder Lambda during CloudFormation deployment
# We only need to ensure frontend source is available in the deployment bucket
if [[ "$DEPLOYMENT_TYPE" != "lambda-only" ]]; then
    echo "Preparing frontend source for FrontendBuilder Lambda..."
    
    # Ensure frontend dependencies are installed for local validation
    if [ ! -d "frontend/node_modules" ]; then
        cd frontend
        npm ci --silent
        cd ..
    fi
    
    echo -e "${GREEN}✓ Frontend source prepared (will be built by FrontendBuilder Lambda)${NC}"
fi

echo ""

# Stage 4: Test (optional - can be skipped for speed)
echo -e "${BLUE}[4/6] Test Stage${NC}"
echo -e "${YELLOW}⚠ Tests skipped for local deployment (run manually if needed)${NC}"
echo ""

# Stage 5: Deploy Infrastructure
if [[ "$DEPLOYMENT_TYPE" == "full" || "$DEPLOYMENT_TYPE" == "lambda-only" ]]; then
    echo -e "${BLUE}[5/6] Deploy Infrastructure Stage${NC}"
    
    echo "Syncing to S3 deployment bucket..."
    
    # Sync CloudFormation templates
    aws s3 sync cfn/ "s3://${DEPLOYMENT_BUCKET}/cfn/" --delete --quiet
    echo "  ✓ CloudFormation templates synced"
    
    # Sync Lambda packages
    aws s3 sync build/lambda/ "s3://${DEPLOYMENT_BUCKET}/lambda/" --delete --quiet
    echo "  ✓ Lambda packages synced"
    
    echo -e "${GREEN}✓ Artifacts synced to s3://${DEPLOYMENT_BUCKET}/${NC}"
    
    if [[ "$DEPLOYMENT_TYPE" == "full" ]]; then
        echo ""
        echo "Deploying CloudFormation stack..."
        
        DEPLOY_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
        ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
        
        aws cloudformation deploy \
            --template-file cfn/master-template.yaml \
            --stack-name "$STACK_NAME" \
            --parameter-overrides \
                ProjectName="$PROJECT_NAME" \
                Environment="$ENVIRONMENT" \
                SourceBucket="$DEPLOYMENT_BUCKET" \
                AdminEmail="$ADMIN_EMAIL" \
                ApiDeploymentTimestamp="$DEPLOY_TIMESTAMP" \
            --capabilities CAPABILITY_NAMED_IAM \
            --tags \
                Project="$PROJECT_NAME" \
                Environment="$ENVIRONMENT" \
                DeployedBy=LocalDeploy \
            --no-fail-on-empty-changeset \
            --region "$AWS_REGION"
        
        echo -e "${GREEN}✓ CloudFormation stack deployed${NC}"
        
        echo ""
        echo "Stack Outputs:"
        aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION" \
            --query 'Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}' \
            --output table
    elif [[ "$DEPLOYMENT_TYPE" == "lambda-only" ]]; then
        echo ""
        echo "Updating Lambda functions..."
        
        # Update each Lambda function
        # Current Lambda functions in the architecture:
        # - query-handler: Read-only infrastructure queries
        # - data-management-handler: Protection Groups & Recovery Plans CRUD
        # - execution-handler: DR execution lifecycle
        # - frontend-deployer: Frontend deployment automation
        # - orch-sf: Step Functions orchestration
        # - notification-formatter: SNS notification formatting
        FUNCTIONS="query-handler data-management-handler execution-handler frontend-deployer:frontend-deployer orch-sf:orchestration-stepfunctions notification-formatter"
        
        for entry in $FUNCTIONS; do
            # Parse function name and S3 key
            if [[ "$entry" == *":"* ]]; then
                func="${entry%%:*}"
                s3key="${entry##*:}"
            else
                func="$entry"
                s3key="$entry"
            fi
            
            FUNCTION_NAME="${PROJECT_NAME}-${func}-${ENVIRONMENT}"
            
            # Check if function exists
            if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$AWS_REGION" > /dev/null 2>&1; then
                echo "  Updating $FUNCTION_NAME..."
                aws lambda update-function-code \
                    --function-name "$FUNCTION_NAME" \
                    --s3-bucket "$DEPLOYMENT_BUCKET" \
                    --s3-key "lambda/${s3key}.zip" \
                    --region "$AWS_REGION" \
                    --output json > /dev/null
                echo "  ✓ $FUNCTION_NAME updated"
            else
                echo "  ⚠ $FUNCTION_NAME not found - skipping"
            fi
        done
        
        echo -e "${GREEN}✓ Lambda functions updated${NC}"
    fi
    
    echo ""
fi

# Stage 6: Deploy Frontend
if [[ "$DEPLOYMENT_TYPE" == "full" || "$DEPLOYMENT_TYPE" == "frontend-only" ]]; then
    echo -e "${BLUE}[6/6] Deploy Frontend Stage${NC}"
    
    # Frontend deployment requires CloudFormation update to trigger FrontendBuilder
    # The FrontendBuilder Lambda is a CloudFormation Custom Resource that builds
    # and deploys the frontend when its properties change
    
    echo "Triggering frontend rebuild via CloudFormation..."
    echo "  FrontendBuilder Lambda is a CloudFormation Custom Resource"
    echo "  It will build frontend from source and deploy to S3"
    
    # Generate new timestamp to force CloudFormation to update the custom resource
    FRONTEND_BUILD_TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
    
    # Check if stack is currently updating
    STACK_STATUS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "UNKNOWN")
    
    if [[ "$STACK_STATUS" == *"IN_PROGRESS"* ]]; then
        echo -e "${YELLOW}⚠ Stack is currently updating ($STACK_STATUS)${NC}"
        echo "  Waiting for stack to complete..."
        aws cloudformation wait stack-update-complete \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION" 2>/dev/null || true
    fi
    
    # Deploy with updated FrontendBuildTimestamp to trigger rebuild
    aws cloudformation deploy \
        --template-file cfn/master-template.yaml \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            ProjectName="$PROJECT_NAME" \
            Environment="$ENVIRONMENT" \
            SourceBucket="$DEPLOYMENT_BUCKET" \
            AdminEmail="$ADMIN_EMAIL" \
            FrontendBuildTimestamp="$FRONTEND_BUILD_TIMESTAMP" \
        --capabilities CAPABILITY_NAMED_IAM \
        --tags \
            Project="$PROJECT_NAME" \
            Environment="$ENVIRONMENT" \
            DeployedBy=LocalDeploy \
        --no-fail-on-empty-changeset \
        --region "$AWS_REGION"
    
    echo -e "${GREEN}✓ Frontend rebuild triggered${NC}"
    
    # Get CloudFront URL
    CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
        --output text 2>/dev/null || echo "N/A")
    
    echo ""
    echo -e "${GREEN}✓ Frontend deployed successfully${NC}"
    echo -e "${GREEN}Application URL: $CLOUDFRONT_URL${NC}"
    
    echo ""
fi

# Deployment Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Deployment Complete                                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ All stages completed successfully${NC}"
echo ""
echo "Stack: $STACK_NAME"
echo "Environment: $ENVIRONMENT"
echo "Deployment Type: $DEPLOYMENT_TYPE"
echo ""

if [[ "$DEPLOYMENT_TYPE" != "lambda-only" ]]; then
    CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
        --output text 2>/dev/null || echo "N/A")
    
    API_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
        --output text 2>/dev/null || echo "N/A")
    
    echo "Application URL: $CLOUDFRONT_URL"
    echo "API Endpoint: $API_ENDPOINT"
fi

echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test the application at the CloudFront URL"
echo "2. Verify API endpoints are responding"
echo "3. Check CloudWatch logs for any errors"
echo ""
