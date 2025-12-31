#!/bin/bash
# Monitor Production Stack Deployment
# Purpose: Monitor the deployment and update environment files when complete

set -e

# Disable AWS CLI pager
export AWS_PAGER=""

# Configuration
STACK_NAME="aws-dr-orchestrator-prod"
REGION="us-east-1"
ENV_FILE=".env.prod"

echo "======================================="
echo "📊 Monitoring Production Deployment"
echo "======================================="
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Function to get stack status
get_stack_status() {
    aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
        --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_FOUND"
}

# Function to update environment file
update_env_file() {
    echo "🔄 Updating $ENV_FILE with stack outputs..."
    
    # Get stack outputs
    USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)
    
    CLIENT_ID=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' --output text)
    
    API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
    
    # Update .env.prod file
    cat > "$ENV_FILE" << EOF
# AWS Configuration for Frontend Build - Production Environment
# Generated from CloudFormation stack outputs

# AWS Region where your resources are deployed
COGNITO_REGION=$REGION

# Cognito User Pool ID
COGNITO_USER_POOL_ID=$USER_POOL_ID

# Cognito App Client ID
COGNITO_CLIENT_ID=$CLIENT_ID

# API Gateway Endpoint URL
API_ENDPOINT=$API_ENDPOINT
EOF
    
    echo "✅ Environment file updated: $ENV_FILE"
}

# Monitor deployment
while true; do
    STATUS=$(get_stack_status)
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$TIMESTAMP] Stack Status: $STATUS"
    
    case "$STATUS" in
        "CREATE_COMPLETE")
            echo ""
            echo "🎉 Stack deployment completed successfully!"
            update_env_file
            
            echo ""
            echo "======================================="
            echo "📋 Final Stack Outputs"
            echo "======================================="
            aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
                --query 'Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}' --output table
            
            echo ""
            echo "🌐 Application URL:"
            CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
                --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' --output text)
            echo "$CLOUDFRONT_URL"
            
            echo ""
            echo "✅ Production deployment monitoring complete!"
            exit 0
            ;;
        "CREATE_FAILED"|"ROLLBACK_COMPLETE"|"ROLLBACK_FAILED")
            echo ""
            echo "❌ Stack deployment failed!"
            echo "Checking recent events for errors..."
            aws cloudformation describe-stack-events --stack-name "$STACK_NAME" --region "$REGION" \
                --query 'StackEvents[?contains(ResourceStatus, `FAILED`)].{Time:Timestamp,Resource:LogicalResourceId,Status:ResourceStatus,Reason:ResourceStatusReason}' \
                --output table
            exit 1
            ;;
        "CREATE_IN_PROGRESS")
            # Check frontend stack specifically
            FRONTEND_STACK=$(aws cloudformation describe-stacks --region "$REGION" \
                --query 'Stacks[?contains(StackName, `aws-dr-orchestrator-prod-FrontendStack`)].StackName' \
                --output text 2>/dev/null)
            
            if [[ -n "$FRONTEND_STACK" ]]; then
                FRONTEND_STATUS=$(aws cloudformation describe-stacks --stack-name "$FRONTEND_STACK" --region "$REGION" \
                    --query 'Stacks[0].StackStatus' --output text 2>/dev/null)
                echo "    Frontend Stack: $FRONTEND_STATUS"
                
                # Show CloudFront creation progress
                if [[ "$FRONTEND_STATUS" == "CREATE_IN_PROGRESS" ]]; then
                    CF_STATUS=$(aws cloudformation describe-stack-events --stack-name "$FRONTEND_STACK" --region "$REGION" \
                        --query 'StackEvents[?LogicalResourceId==`CloudFrontDistribution`] | [0].ResourceStatus' \
                        --output text 2>/dev/null)
                    if [[ "$CF_STATUS" == "CREATE_IN_PROGRESS" ]]; then
                        echo "    CloudFront Distribution: Creating (this takes 15-45 minutes)"
                    fi
                fi
            fi
            ;;
        "NOT_FOUND")
            echo "❌ Stack not found!"
            exit 1
            ;;
    esac
    
    echo "    Checking again in 60 seconds..."
    sleep 60
done