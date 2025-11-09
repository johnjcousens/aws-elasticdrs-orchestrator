#!/bin/bash
set -e

echo "========================================"
echo "🚀 DRS Orchestration - Deployment #8"
echo "    DEV ENVIRONMENT TEST"
echo "    WITH RESOURCE RETENTION"
echo "========================================"
echo ""
echo "Key Changes:"
echo "  ✅ Fixed frontend-builder Lambda (14.3 MB with dependencies)"
echo "  ✅ Fixed s3-cleanup Lambda (14.3 MB with crhelper)"
echo "  ⚠️  Resources will be RETAINED on failure for troubleshooting"
echo "  🔒 WAF DISABLED for test run"
echo "  🧪 Using DEV environment for testing"
echo ""

# Variables
STACK_NAME="drs-orchestration-dev"
REGION="us-east-1"
BUCKET=$(cat /tmp/prod-bucket-name.txt)  # Using same bucket as PROD (contains fixed Lambdas)
ADMIN_EMAIL="***REMOVED***"

echo "📋 Configuration:"
echo "   Stack: $STACK_NAME"
echo "   Environment: DEV"
echo "   Region: $REGION"
echo "   Bucket: $BUCKET"
echo "   Admin: $ADMIN_EMAIL"
echo "   WAF: DISABLED (test run)"
echo ""

# Check if stack exists
echo "⏳ Checking stack status..."
STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_FOUND")

if [[ "$STATUS" == "NOT_FOUND" ]]; then
    echo "✅ Stack does not exist. Will create new DEV stack."
    echo ""
    OPERATION="create-stack"
elif [[ "$STATUS" == "ROLLBACK_IN_PROGRESS" ]] || [[ "$STATUS" == *"IN_PROGRESS"* ]]; then
    echo "⚠️  Stack is in progress state: $STATUS"
    echo "   Waiting for operation to complete..."
    echo ""
    
    while true; do
        STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].StackStatus' --output text 2>/dev/null)
        echo "   $(date '+%H:%M:%S') - Status: $STATUS"
        
        if [[ "$STATUS" == "ROLLBACK_COMPLETE" ]] || [[ "$STATUS" == "UPDATE_ROLLBACK_COMPLETE" ]] || [[ "$STATUS" == "CREATE_COMPLETE" ]] || [[ "$STATUS" == "UPDATE_COMPLETE" ]]; then
            echo ""
            echo "✅ Stack ready. Proceeding with update..."
            echo ""
            OPERATION="update-stack"
            break
        elif [[ "$STATUS" == *"FAILED"* ]]; then
            echo ""
            echo "❌ Stack in failed state. Exiting."
            exit 1
        fi
        
        sleep 10
    done
else
    echo "✅ Stack exists with status: $STATUS"
    echo "   Will update existing stack."
    echo ""
    OPERATION="update-stack"
fi

# Check if both Lambda packages exist
echo "🔍 Verifying Lambda packages in S3..."
if ! aws s3 ls s3://${BUCKET}/lambda/frontend-builder.zip >/dev/null 2>&1; then
    echo "❌ frontend-builder.zip not found in S3"
    exit 1
fi
if ! aws s3 ls s3://${BUCKET}/lambda/custom-resources.zip >/dev/null 2>&1; then
    echo "❌ custom-resources.zip not found in S3"
    exit 1
fi
echo "✅ Both Lambda packages found in S3"
echo ""

# Deploy with resource retention (disable-rollback) and WAF disabled
echo "🚀 Starting deployment with --disable-rollback..."
echo "   This will RETAIN resources on failure for troubleshooting"
echo ""

if [[ "$OPERATION" == "create-stack" ]]; then
    aws cloudformation create-stack \
      --stack-name $STACK_NAME \
      --template-body file://cfn/master-template.yaml \
      --parameters \
        ParameterKey=ProjectName,ParameterValue=drs-orchestration \
        ParameterKey=Environment,ParameterValue=dev \
        ParameterKey=SourceBucket,ParameterValue=$BUCKET \
        ParameterKey=AdminEmail,ParameterValue=$ADMIN_EMAIL \
        ParameterKey=EnableWAF,ParameterValue=false \
        ParameterKey=CognitoDomainPrefix,ParameterValue=drs-orch-dev-$(date +%s) \
        ParameterKey=NotificationEmail,ParameterValue=$ADMIN_EMAIL \
        ParameterKey=EnableCloudTrail,ParameterValue=false \
        ParameterKey=EnableSecretsManager,ParameterValue=false \
      --capabilities CAPABILITY_NAMED_IAM \
      --disable-rollback \
      --region $REGION
else
    aws cloudformation update-stack \
      --stack-name $STACK_NAME \
      --template-body file://cfn/master-template.yaml \
      --parameters \
        ParameterKey=ProjectName,ParameterValue=drs-orchestration \
        ParameterKey=Environment,ParameterValue=dev \
        ParameterKey=SourceBucket,ParameterValue=$BUCKET \
        ParameterKey=AdminEmail,ParameterValue=$ADMIN_EMAIL \
        ParameterKey=EnableWAF,ParameterValue=false \
        ParameterKey=CognitoDomainPrefix,UsePreviousValue=true \
        ParameterKey=NotificationEmail,UsePreviousValue=true \
        ParameterKey=EnableCloudTrail,UsePreviousValue=true \
        ParameterKey=EnableSecretsManager,UsePreviousValue=true \
      --capabilities CAPABILITY_NAMED_IAM \
      --disable-rollback \
      --region $REGION
fi

echo ""
echo "✅ Deployment #8 (DEV) initiated with resource retention"
echo ""
echo "📊 Monitor progress with:"
echo "   watch -n 10 'aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query \"Stacks[0].StackStatus\"'"
echo ""
echo "📝 View events with:"
echo "   aws cloudformation describe-stack-events --stack-name $STACK_NAME --region $REGION --max-items 20 --query 'StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' --output table"
echo ""
echo "⚠️  IMPORTANT: Resources will be RETAINED if deployment fails"
echo "   You can inspect Lambda logs and debug before cleanup"
echo ""
