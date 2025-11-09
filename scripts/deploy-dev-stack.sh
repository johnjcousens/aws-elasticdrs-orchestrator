#!/bin/bash

# DEV Stack Deployment Script
# Purpose: Deploy to fresh DEV environment with fixed Lambda packages
# Date: November 9, 2025

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AWS DRS Orchestration - DEV Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
STACK_NAME="drs-orchestration-dev"
REGION="us-east-1"
S3_BUCKET="drs-orchestration-prod-1762661820"
ADMIN_EMAIL="your-email@example.com"
ENVIRONMENT="dev"

echo -e "${GREEN}📋 Deployment Configuration:${NC}"
echo "  Stack Name:    ${STACK_NAME}"
echo "  Region:        ${REGION}"
echo "  S3 Bucket:     ${S3_BUCKET}"
echo "  Environment:   ${ENVIRONMENT}"
echo "  Admin Email:   ${ADMIN_EMAIL}"
echo ""

# Verify S3 bucket exists
echo -e "${YELLOW}🔍 Verifying S3 bucket...${NC}"
if aws s3 ls "s3://${S3_BUCKET}" --region ${REGION} >/dev/null 2>&1; then
    echo -e "${GREEN}✅ S3 bucket found${NC}"
else
    echo -e "${RED}❌ S3 bucket not found: ${S3_BUCKET}${NC}"
    exit 1
fi

# Check if stack already exists
echo -e "${YELLOW}🔍 Checking if stack exists...${NC}"
if aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${REGION} >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Stack ${STACK_NAME} already exists. Deleting...${NC}"
    aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${REGION}
    echo -e "${YELLOW}⏳ Waiting for stack deletion...${NC}"
    aws cloudformation wait stack-delete-complete --stack-name ${STACK_NAME} --region ${REGION}
    echo -e "${GREEN}✅ Stack deleted${NC}"
fi

# Deploy stack
echo ""
echo -e "${BLUE}🚀 Starting DEV deployment...${NC}"
echo ""

aws cloudformation create-stack \
  --stack-name ${STACK_NAME} \
  --template-body file://cfn/master-template.yaml \
  --parameters \
    ParameterKey=Environment,ParameterValue=${ENVIRONMENT} \
    ParameterKey=AdminEmail,ParameterValue=${ADMIN_EMAIL} \
    ParameterKey=SourceBucket,ParameterValue=${S3_BUCKET} \
    ParameterKey=EnableWAF,ParameterValue=false \
  --capabilities CAPABILITY_NAMED_IAM \
  --disable-rollback \
  --region ${REGION}

echo -e "${GREEN}✅ Stack creation initiated${NC}"
echo ""

# Monitor deployment
echo -e "${YELLOW}⏳ Monitoring deployment progress...${NC}"
echo "   This will take approximately 15-20 minutes"
echo ""
echo "Stack events:"
echo "-------------"

# Initial wait for stack to be created
sleep 5

# Monitor stack events
while true; do
    STATUS=$(aws cloudformation describe-stacks \
        --stack-name ${STACK_NAME} \
        --region ${REGION} \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "PENDING")
    
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} Current Status: ${STATUS}"
    
    # Show latest event
    aws cloudformation describe-stack-events \
        --stack-name ${STACK_NAME} \
        --region ${REGION} \
        --max-items 1 \
        --query 'StackEvents[0].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
        --output text 2>/dev/null | head -1
    
    case ${STATUS} in
        CREATE_COMPLETE)
            echo ""
            echo -e "${GREEN}✅ Stack deployment SUCCESSFUL!${NC}"
            break
            ;;
        CREATE_FAILED|ROLLBACK_COMPLETE|ROLLBACK_FAILED)
            echo ""
            echo -e "${RED}❌ Stack deployment FAILED!${NC}"
            echo ""
            echo "Failed resources:"
            aws cloudformation describe-stack-events \
                --stack-name ${STACK_NAME} \
                --region ${REGION} \
                --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[Timestamp,LogicalResourceId,ResourceStatusReason]' \
                --output table
            exit 1
            ;;
    esac
    
    sleep 30
done

# Display outputs
echo ""
echo -e "${GREEN}📊 Stack Outputs:${NC}"
echo "================"
aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --region ${REGION} \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo -e "${GREEN}🎉 DEV Environment Ready!${NC}"
echo ""
echo "Next steps:"
echo "  1. Create Cognito user: aws cognito-idp admin-create-user ..."
echo "  2. Test API endpoint"
echo "  3. Access CloudFront URL"
echo ""
