#!/bin/bash

# Update GitHub OIDC Stack Permissions for Multi-Stack Support
# This script updates the existing OIDC stack to support both current and archive test stacks

set -e

# Configuration
OIDC_STACK_NAME="aws-elasticdrs-orchestrator-github-oidc"
PROJECT_NAME="aws-elasticdrs-orchestrator"
ENVIRONMENT="dev"
GITHUB_ORG="jocousen"
GITHUB_REPO="aws-elasticdrs-orchestrator"
DEPLOYMENT_BUCKET="aws-elasticdrs-orchestrator"
APPLICATION_STACK_NAME="aws-elasticdrs-orchestrator-dev"

echo "=== Updating GitHub OIDC Stack Permissions ==="
echo "Stack: $OIDC_STACK_NAME"
echo "Project: $PROJECT_NAME"
echo "Environment: $ENVIRONMENT"
echo ""

# Check if stack exists
echo "Checking if OIDC stack exists..."
if aws cloudformation describe-stacks --stack-name "$OIDC_STACK_NAME" >/dev/null 2>&1; then
    echo "✅ OIDC stack exists: $OIDC_STACK_NAME"
else
    echo "❌ OIDC stack does not exist: $OIDC_STACK_NAME"
    echo "Please deploy the OIDC stack first using:"
    echo "  aws cloudformation deploy --template-file cfn/github-oidc-stack.yaml --stack-name $OIDC_STACK_NAME --capabilities CAPABILITY_NAMED_IAM --parameter-overrides ..."
    exit 1
fi

# Update the stack with new permissions
echo ""
echo "Updating OIDC stack with multi-stack permissions..."
aws cloudformation deploy \
    --template-file cfn/github-oidc-stack.yaml \
    --stack-name "$OIDC_STACK_NAME" \
    --parameter-overrides \
        ProjectName="$PROJECT_NAME" \
        Environment="$ENVIRONMENT" \
        GitHubOrg="$GITHUB_ORG" \
        GitHubRepo="$GITHUB_REPO" \
        DeploymentBucket="$DEPLOYMENT_BUCKET" \
        ApplicationStackName="$APPLICATION_STACK_NAME" \
    --capabilities CAPABILITY_NAMED_IAM \
    --tags \
        Project="$PROJECT_NAME" \
        Environment="$ENVIRONMENT" \
        Purpose="GitHubActions-OIDC" \
    --no-fail-on-empty-changeset

echo ""
echo "✅ OIDC stack updated successfully!"
echo ""

# Get the role ARN
ROLE_ARN=$(aws cloudformation describe-stacks --stack-name "$OIDC_STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`GitHubActionsRoleArn`].OutputValue' --output text)

echo "=== Updated Permissions Summary ==="
echo "Role ARN: $ROLE_ARN"
echo ""
echo "✅ CloudFormation: Access to both aws-*drs-orchestrat* and aws-*elasticdrs-orchestrat* stacks"
echo "✅ S3 Deployment: Access to both deployment buckets"
echo "✅ S3 Frontend: Access to both frontend bucket patterns"
echo "✅ All other AWS services: Full access for both stacks"
echo ""

echo "=== GitHub Secrets Verification ==="
echo "Verify these secrets are set in your GitHub repository:"
echo "  ARCHIVE_AWS_ROLE_ARN = $ROLE_ARN"
echo "  AWS_ROLE_ARN = $ROLE_ARN (should be the same)"
echo ""

echo "=== Next Steps ==="
echo "1. Verify GitHub secrets are correct"
echo "2. Push changes to trigger GitHub Actions deployment"
echo "3. Monitor deployment for both stacks"
echo ""
echo "The updated permissions should resolve the CloudFormation AccessDenied errors."