what sgoi g why are we skipping #!/bin/bash
set -e

# Deploy cross-account roles to target and staging accounts
# This script deploys the DRSOrchestrationRole to both accounts so the orchestration account can manage them

# Configuration
ORCHESTRATION_ACCOUNT="777788889999"
TARGET_ACCOUNT="111122223333"
STAGING_ACCOUNT="444455556666"
ENVIRONMENT="${1:-dev}"
PROJECT_NAME="drs-orchestration"
REGION="us-west-2"  # Default region for cross-account roles

# Auto-generate External IDs based on account
TARGET_EXTERNAL_ID="${PROJECT_NAME}-${ENVIRONMENT}-${TARGET_ACCOUNT}"
STAGING_EXTERNAL_ID="${PROJECT_NAME}-${ENVIRONMENT}-${STAGING_ACCOUNT}"

# AWS Profiles
TARGET_PROFILE="111122223333_AdministratorAccess"
STAGING_PROFILE="444455556666_AdministratorAccess"

echo "=========================================="
echo "DRS Cross-Account Role Deployment"
echo "=========================================="
echo "Orchestration Account: $ORCHESTRATION_ACCOUNT"
echo "Target Account: $TARGET_ACCOUNT"
echo "Staging Account: $STAGING_ACCOUNT"
echo "Environment: $ENVIRONMENT"
echo "Target External ID: $TARGET_EXTERNAL_ID"
echo "Staging External ID: $STAGING_EXTERNAL_ID"
echo "=========================================="
echo ""

# Verify profiles exist
if ! grep -q "\[$TARGET_PROFILE\]" ~/.aws/credentials 2>/dev/null; then
    echo "❌ ERROR: AWS profile '$TARGET_PROFILE' not found in ~/.aws/credentials"
    exit 1
fi

if ! grep -q "\[$STAGING_PROFILE\]" ~/.aws/credentials 2>/dev/null; then
    echo "❌ ERROR: AWS profile '$STAGING_PROFILE' not found in ~/.aws/credentials"
    exit 1
fi

echo "✅ AWS profiles verified"
echo ""

# Function to deploy stack
deploy_stack() {
    local ACCOUNT_ID=$1
    local PROFILE=$2
    local ACCOUNT_NAME=$3
    local EXTERNAL_ID=$4
    
    echo "=========================================="
    echo "Deploying to $ACCOUNT_NAME ($ACCOUNT_ID)"
    echo "=========================================="
    
    # Verify account
    CURRENT_ACCOUNT=$(AWS_PAGER="" aws sts get-caller-identity --profile $PROFILE --query 'Account' --output text)
    if [ "$CURRENT_ACCOUNT" != "$ACCOUNT_ID" ]; then
        echo "❌ ERROR: Profile is not for $ACCOUNT_NAME"
        echo "Expected: $ACCOUNT_ID"
        echo "Got: $CURRENT_ACCOUNT"
        return 1
    fi
    
    echo "✅ Authenticated to $ACCOUNT_NAME"
    echo ""
    
    # Deploy stack
    STACK_NAME="${PROJECT_NAME}-cross-account-role-${ENVIRONMENT}"
    
    echo "Deploying stack: $STACK_NAME"
    echo "Template: cfn/cross-account-role-stack.yaml"
    echo "External ID: $EXTERNAL_ID"
    echo ""
    
    AWS_PAGER="" aws cloudformation deploy \
        --template-file cfn/cross-account-role-stack.yaml \
        --stack-name "$STACK_NAME" \
        --profile "$PROFILE" \
        --region "$REGION" \
        --capabilities CAPABILITY_NAMED_IAM \
        --parameter-overrides \
            OrchestrationAccountId="$ORCHESTRATION_ACCOUNT" \
            ExternalId="$EXTERNAL_ID" \
            Environment="$ENVIRONMENT" \
            ProjectName="$PROJECT_NAME" \
        --tags \
            Environment="$ENVIRONMENT" \
            ManagedBy=CloudFormation \
            OrchestrationAccount="$ORCHESTRATION_ACCOUNT"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Stack deployed successfully to $ACCOUNT_NAME"
        echo ""
        
        # Get outputs
        echo "Stack Outputs:"
        AWS_PAGER="" aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --profile "$PROFILE" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
            --output table
        echo ""
    else
        echo "❌ Stack deployment failed for $ACCOUNT_NAME"
        return 1
    fi
}

# Deploy to target account
deploy_stack "$TARGET_ACCOUNT" "$TARGET_PROFILE" "Target Account" "$TARGET_EXTERNAL_ID"

echo ""
echo "=========================================="
echo ""

# Deploy to staging account
deploy_stack "$STAGING_ACCOUNT" "$STAGING_PROFILE" "Staging Account" "$STAGING_EXTERNAL_ID"

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Both accounts now have DRSOrchestrationRole that can be assumed by:"
echo "  Orchestration Account: $ORCHESTRATION_ACCOUNT"
echo "  External ID: $EXTERNAL_ID"
echo ""
echo "Role ARNs:"
echo "  Target:  arn:aws:iam::${TARGET_ACCOUNT}:role/DRSOrchestrationRole-${ENVIRONMENT}"
echo "  Staging: arn:aws:iam::${STAGING_ACCOUNT}:role/DRSOrchestrationRole-${ENVIRONMENT}"
echo ""
echo "Next Steps:"
echo "1. Update orchestration account Lambda functions with these role ARNs"
echo "2. Test cross-account access from orchestration account"
echo "3. Deploy DRS agents using the orchestration Lambda"
echo "=========================================="
