#!/bin/bash

# Update GitHub OIDC permissions for QA stack

set -e

echo "=== Updating GitHub OIDC Stack for QA Stack Permissions ==="

aws cloudformation deploy \
    --template-file cfn/github-oidc-stack.yaml \
    --stack-name aws-drs-orchestrator-github-oidc \
    --parameter-overrides \
        ProjectName=aws-elasticdrs-orchestrator \
        Environment=dev \
        GitHubOrg=johnjcousens \
        GitHubRepo=aws-elasticdrs-orchestrator \
        DeploymentBucket=aws-elasticdrs-orchestrator \
        ApplicationStackName=aws-elasticdrs-orchestrator-dev \
    --capabilities CAPABILITY_NAMED_IAM \
    --no-fail-on-empty-changeset

echo "✅ GitHub OIDC stack updated with QA stack permissions"