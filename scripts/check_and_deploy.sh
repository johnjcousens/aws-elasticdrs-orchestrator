#!/bin/bash

# AWS DRS Orchestration - Stack Deletion Monitor and Auto-Deploy Script
# This script monitors the deletion of the old stack and automatically deploys the new one

set -e

# Load deployment configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/load-deployment-config.sh"

TEMPLATE_URL="https://s3.amazonaws.com/$DEPLOYMENT_BUCKET/cfn/master-template.yaml"

echo "🔍 Monitoring stack deletion and preparing for deployment..."
echo "Stack: $STACK_NAME"
echo "Admin Email: $ADMIN_EMAIL"
echo "Template URL: $TEMPLATE_URL"
echo ""

# Function to check stack status
check_stack_status() {
    AWS_PAGER="" aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "DELETED"
}

# Function to deploy new stack
deploy_stack() {
    echo "🚀 Deploying new CloudFormation stack..."
    
    AWS_PAGER="" aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-url "$TEMPLATE_URL" \
        --parameters \
            ParameterKey=AdminEmail,ParameterValue="$ADMIN_EMAIL" \
            ParameterKey=EnablePipelineNotifications,ParameterValue=true \
        --capabilities CAPABILITY_NAMED_IAM \
        --on-failure ROLLBACK > /dev/null
    
    echo "✅ Stack creation initiated successfully!"
    echo ""
    echo "📊 Monitor deployment progress:"
    echo "AWS_PAGER=\"\" aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[0].StackStatus'"
    echo ""
    echo "🔗 View in AWS Console:"
    echo "https://console.aws.amazon.com/cloudformation/home?region=$REGION#/stacks/stackinfo?stackId=$STACK_NAME"
    echo ""
    
    # Monitor deployment
    echo "🔄 Monitoring deployment progress..."
    while true; do
        STATUS=$(check_stack_status)
        echo "$(date '+%H:%M:%S') - Stack Status: $STATUS"
        
        case "$STATUS" in
            "CREATE_COMPLETE")
                echo ""
                echo "🎉 SUCCESS! Stack deployed successfully!"
                echo ""
                echo "📧 Next Steps:"
                echo "1. Check your email ($ADMIN_EMAIL) for SNS subscription confirmation"
                echo "2. Click the confirmation link to enable notifications"
                echo "3. Test the pipeline by triggering a build failure"
                echo ""
                echo "🔗 Access your application:"
                CLOUDFRONT_URL=$(AWS_PAGER="" aws cloudformation describe-stacks \
                    --stack-name "$STACK_NAME" \
                    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
                    --output text 2>/dev/null)
                if [ "$CLOUDFRONT_URL" != "" ]; then
                    echo "Frontend: $CLOUDFRONT_URL"
                fi
                
                API_ENDPOINT=$(AWS_PAGER="" aws cloudformation describe-stacks \
                    --stack-name "$STACK_NAME" \
                    --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
                    --output text 2>/dev/null)
                if [ "$API_ENDPOINT" != "" ]; then
                    echo "API: $API_ENDPOINT"
                fi
                
                exit 0
                ;;
            "CREATE_FAILED"|"ROLLBACK_COMPLETE"|"ROLLBACK_FAILED")
                echo ""
                echo "❌ DEPLOYMENT FAILED!"
                echo ""
                echo "🔍 Check the error details:"
                echo "AWS_PAGER=\"\" aws cloudformation describe-stack-events --stack-name $STACK_NAME --query 'StackEvents[?ResourceStatus==\`CREATE_FAILED\`].[Timestamp,LogicalResourceId,ResourceStatusReason]' --output table"
                exit 1
                ;;
            "CREATE_IN_PROGRESS")
                # Continue monitoring
                ;;
            *)
                echo "⚠️  Unexpected status: $STATUS"
                ;;
        esac
        
        sleep 30
    done
}

# Monitor deletion
echo "⏳ Waiting for stack deletion to complete..."
DELETION_START_TIME=$(date +%s)

while true; do
    STATUS=$(check_stack_status)
    ELAPSED=$(($(date +%s) - DELETION_START_TIME))
    ELAPSED_MIN=$((ELAPSED / 60))
    
    echo "$(date '+%H:%M:%S') - Deletion Status: $STATUS (${ELAPSED_MIN}m elapsed)"
    
    case "$STATUS" in
        "DELETED")
            echo ""
            echo "✅ Stack deletion completed successfully!"
            echo "🕐 Total deletion time: ${ELAPSED_MIN} minutes"
            echo ""
            deploy_stack
            break
            ;;
        "DELETE_FAILED")
            echo ""
            echo "❌ Stack deletion failed!"
            echo ""
            echo "🔍 Check failed resources:"
            AWS_PAGER="" aws cloudformation describe-stack-events \
                --stack-name "$STACK_NAME" \
                --query 'StackEvents[?ResourceStatus==`DELETE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
                --output table 2>/dev/null | head -10
            echo ""
            echo "💡 You may need to manually clean up resources and retry deletion"
            exit 1
            ;;
        "DELETE_IN_PROGRESS")
            # Continue monitoring
            ;;
        *)
            echo "⚠️  Unexpected deletion status: $STATUS"
            ;;
    esac
    
    # Check every 30 seconds
    sleep 30
    
    # Safety timeout after 30 minutes
    if [ $ELAPSED -gt 1800 ]; then
        echo ""
        echo "⏰ Deletion timeout reached (30 minutes)"
        echo "❓ Stack may be stuck - check AWS console for manual intervention"
        exit 1
    fi
done