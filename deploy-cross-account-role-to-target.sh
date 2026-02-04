#!/bin/bash
# Deploy updated cross-account role to target account (111122223333)
# with hardcoded ExternalId: drs-orchestration-cross-account

set -e

echo "=========================================="
echo "Deploying Cross-Account Role to Target Account"
echo "Target Account: 111122223333"
echo "Role Name: DRSOrchestrationRole"
echo "ExternalId: drs-orchestration-cross-account"
echo "=========================================="

# Check current account
CURRENT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
echo "Current AWS Account: $CURRENT_ACCOUNT"

if [ "$CURRENT_ACCOUNT" != "111122223333" ]; then
    echo ""
    echo "ERROR: You must be logged into target account 111122223333"
    echo "Current account: $CURRENT_ACCOUNT"
    echo ""
    echo "Please switch to the target account using AWS SSO or profile:"
    echo "  aws sso login --profile <target-account-profile>"
    echo "  export AWS_PROFILE=<target-account-profile>"
    exit 1
fi

echo ""
echo "Deploying cross-account role stack..."
echo ""

aws cloudformation deploy \
  --template-file cfn/cross-account-role-stack.yaml \
  --stack-name drs-orchestration-cross-account-role \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    OrchestrationAccountId=777788889999 \
    ExternalId=drs-orchestration-cross-account \
    ProjectName=drs-orchestration \
  --region us-east-1

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Role ARN: arn:aws:iam::111122223333:role/DRSOrchestrationRole"
echo "ExternalId: drs-orchestration-cross-account"
echo ""
echo "Next steps:"
echo "1. Update Target Accounts DynamoDB table with new ExternalId"
echo "2. Deploy Lambda changes: ./scripts/deploy.sh test --lambda-only"
echo "3. Test protection group creation via UI"
