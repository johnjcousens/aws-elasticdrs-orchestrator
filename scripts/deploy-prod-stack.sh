#!/bin/bash
# Deploy Production RBAC Stack
# Purpose: Deploy the full DRS Orchestration solution with RBAC to production

set -e

# Load deployment configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/load-deployment-config.sh"

# Disable AWS CLI pager
export AWS_PAGER=""

echo "======================================="
echo "🚀 Production Stack Deployment"
echo "======================================="
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_NAME"
echo "Admin Email: $ADMIN_EMAIL"
echo ""

# Check if stack exists
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" >/dev/null 2>&1; then
    echo "📋 Stack exists, checking status..."
    STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].StackStatus' --output text)
    echo "Current status: $STACK_STATUS"
    
    if [[ "$STACK_STATUS" == "CREATE_IN_PROGRESS" || "$STACK_STATUS" == "UPDATE_IN_PROGRESS" ]]; then
        echo "⏳ Stack operation in progress, monitoring..."
        aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$REGION" || \
        aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME" --region "$REGION"
    elif [[ "$STACK_STATUS" == "CREATE_COMPLETE" || "$STACK_STATUS" == "UPDATE_COMPLETE" ]]; then
        echo "✅ Stack already deployed successfully"
    else
        echo "❌ Stack in unexpected state: $STACK_STATUS"
        exit 1
    fi
else
    echo "🆕 Creating new stack..."
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-url "https://$DEPLOYMENT_BUCKET.s3.$REGION.amazonaws.com/cfn/master-template.yaml" \
        --parameters \
            ParameterKey=ProjectName,ParameterValue="$PROJECT_NAME" \
            ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
            ParameterKey=SourceBucket,ParameterValue="$DEPLOYMENT_BUCKET" \
            ParameterKey=AdminEmail,ParameterValue="$ADMIN_EMAIL" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region "$REGION"
    
    echo "⏳ Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME" --region "$REGION"
fi

echo ""
echo "======================================="
echo "📊 Stack Outputs"
echo "======================================="

# Get stack outputs
aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
    --query 'Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}' \
    --output table

echo ""
echo "======================================="
echo "🔐 RBAC Groups Created"
echo "======================================="

# Get User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)

echo "User Pool ID: $USER_POOL_ID"
echo ""
echo "Available RBAC Groups:"
echo "  • DRS-Administrator (Full access)"
echo "  • DRS-Infrastructure-Admin (Infrastructure management)"
echo "  • DRS-Recovery-Plan-Manager (Recovery plan management)"
echo "  • DRS-Operator (Execute operations)"
echo "  • DRS-Recovery-Plan-Viewer (View recovery plans)"
echo "  • DRS-Read-Only (Read-only access)"

echo ""
echo "======================================="
echo "🎯 Next Steps"
echo "======================================="
echo "1. Access the application:"
CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' --output text 2>/dev/null || echo "Pending...")
echo "   URL: $CLOUDFRONT_URL"

echo ""
echo "2. Manage user roles:"
echo "   ./scripts/manage-user-roles.py --user-pool-id $USER_POOL_ID --region $REGION"

echo ""
echo "3. Create additional users:"
echo "   ./scripts/manage-user-roles.py create-user --email user@example.com --user-pool-id $USER_POOL_ID"

echo ""
echo "✅ Production deployment complete!"