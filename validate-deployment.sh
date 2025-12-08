#!/bin/bash
# AWS DRS Orchestration - Deployment Validation Script

set -e

STACK_NAME="${1:-drs-orchestration-dev}"
REGION="${2:-us-east-1}"

echo "🔍 Validating AWS DRS Orchestration deployment..."
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Check CloudFormation stack status
echo "1. Checking CloudFormation stack status..."
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_FOUND")
if [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
    echo "   ✅ Stack status: $STACK_STATUS"
else
    echo "   ❌ Stack status: $STACK_STATUS"
    exit 1
fi

# Get stack outputs
echo "2. Retrieving stack outputs..."
API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' --output text)
CLIENT_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' --output text)
CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' --output text)
STATE_MACHINE_ARN=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' --output text)

echo "   API Endpoint: $API_ENDPOINT"
echo "   User Pool ID: $USER_POOL_ID"
echo "   Client ID: $CLIENT_ID"
echo "   CloudFront URL: $CLOUDFRONT_URL"
echo "   State Machine ARN: $STATE_MACHINE_ARN"

# Check Lambda functions
echo "3. Checking Lambda functions..."
FUNCTIONS=(
    "drs-orchestration-api-handler-dev"
    "drs-orchestration-orchestration-stepfunctions-dev"
    "drs-orchestration-orchestration-dev"
)

for func in "${FUNCTIONS[@]}"; do
    STATUS=$(aws lambda get-function --function-name $func --region $REGION --query 'Configuration.State' --output text 2>/dev/null || echo "NOT_FOUND")
    if [ "$STATUS" = "Active" ]; then
        echo "   ✅ $func: $STATUS"
    else
        echo "   ❌ $func: $STATUS"
    fi
done

# Check Step Functions state machine
echo "4. Checking Step Functions state machine..."
SF_STATUS=$(aws stepfunctions describe-state-machine --state-machine-arn "$STATE_MACHINE_ARN" --region $REGION --query 'status' --output text 2>/dev/null || echo "NOT_FOUND")
if [ "$SF_STATUS" = "ACTIVE" ]; then
    echo "   ✅ State Machine: $SF_STATUS"
else
    echo "   ❌ State Machine: $SF_STATUS"
fi

# Check DynamoDB tables
echo "5. Checking DynamoDB tables..."
TABLES=(
    "drs-orchestration-protection-groups-dev"
    "drs-orchestration-recovery-plans-dev"
    "drs-orchestration-execution-history-dev"
)

for table in "${TABLES[@]}"; do
    STATUS=$(aws dynamodb describe-table --table-name $table --region $REGION --query 'Table.TableStatus' --output text 2>/dev/null || echo "NOT_FOUND")
    if [ "$STATUS" = "ACTIVE" ]; then
        echo "   ✅ $table: $STATUS"
    else
        echo "   ❌ $table: $STATUS"
    fi
done

# Test API endpoint
echo "6. Testing API endpoint..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_ENDPOINT/protection-groups" || echo "000")
if [ "$HTTP_STATUS" = "401" ] || [ "$HTTP_STATUS" = "403" ]; then
    echo "   ✅ API responding (authentication required): $HTTP_STATUS"
elif [ "$HTTP_STATUS" = "200" ]; then
    echo "   ✅ API responding: $HTTP_STATUS"
else
    echo "   ❌ API not responding: $HTTP_STATUS"
fi

# Check frontend configuration
echo "7. Checking frontend configuration..."
CONFIG_STATUS=$(curl -s "$CLOUDFRONT_URL/aws-config.js" | grep -q "AWS_CONFIG" && echo "FOUND" || echo "NOT_FOUND")
if [ "$CONFIG_STATUS" = "FOUND" ]; then
    echo "   ✅ Frontend configuration found"
else
    echo "   ❌ Frontend configuration missing"
fi

# Test Step Functions Lambda
echo "8. Testing Step Functions Lambda..."
TEST_PAYLOAD='{"action":"begin","execution":"validation-test","plan":{"PlanId":"test","Waves":[]},"isDrill":true}'
LAMBDA_RESULT=$(aws lambda invoke --function-name drs-orchestration-orchestration-stepfunctions-dev --payload "$TEST_PAYLOAD" --region $REGION /tmp/lambda-response.json 2>/dev/null && cat /tmp/lambda-response.json | jq -r '.status // "ERROR"' 2>/dev/null || echo "ERROR")
if [ "$LAMBDA_RESULT" != "ERROR" ]; then
    echo "   ✅ Step Functions Lambda responding"
else
    echo "   ❌ Step Functions Lambda error"
fi

echo ""
echo "🎉 Deployment validation complete!"
echo ""
echo "Next steps:"
echo "1. Create admin user: aws cognito-idp admin-create-user --user-pool-id $USER_POOL_ID ..."
echo "2. Access application: $CLOUDFRONT_URL"
echo "3. Configure DRS source servers in your AWS account"
echo ""
echo "For troubleshooting, see: DEPLOYMENT_RECOVERY_GUIDE.md"