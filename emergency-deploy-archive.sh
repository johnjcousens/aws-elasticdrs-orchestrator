#!/bin/bash

# EMERGENCY: Deploy Archive Test Stack with Correct Archive Code
# This is an emergency deployment to fix the architecture mismatch issue

set -e

echo "=== EMERGENCY DEPLOYMENT: Archive Test Stack ==="
echo "Deploying WORKING archive code (5-stack architecture)"
echo "This will be immediately followed by Git commit to restore CI/CD tracking"
echo ""

# Configuration
STACK_NAME="aws-drs-orchestrator-archive-test"
BUCKET="aws-drs-orchestrator-archive-test-bucket"
ARCHIVE_DIR="archive/commit-9546118-uncorrupted"

echo "Stack: $STACK_NAME"
echo "Bucket: $BUCKET"
echo "Archive: $ARCHIVE_DIR"
echo ""

# 1. Sync archive CloudFormation templates
echo "1. Syncing archive CloudFormation templates..."
aws s3 sync "$ARCHIVE_DIR/cfn/" "s3://$BUCKET/cfn/" --delete
echo "✅ Archive CFN templates synced"

# 2. Build and sync archive Lambda packages (proper ZIP format)
echo "2. Building archive Lambda packages..."
mkdir -p build/archive-lambda

# Package the archive orchestration Lambda (the working one)
cd "$ARCHIVE_DIR"
zip -q ../../build/archive-lambda/orchestration_stepfunctions.zip orchestration_stepfunctions.py
cd ../..

# Package other archive Lambda functions
cd "$ARCHIVE_DIR"
for func in api_handler execution_finder execution_poller notification_formatter frontend_builder bucket_cleaner; do
    if [ -f "${func}.py" ]; then
        echo "  Packaging ${func}.py..."
        zip -q ../../build/archive-lambda/${func}.zip ${func}.py
    fi
done
cd ../..

# Sync Lambda packages
aws s3 sync build/archive-lambda/ "s3://$BUCKET/lambda/" --delete
echo "✅ Archive Lambda packages synced"

# 3. Deploy the archive stack using archive master template
echo "3. Deploying archive stack..."
aws cloudformation deploy \
    --template-file "$ARCHIVE_DIR/cfn/master-template.yaml" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        ProjectName="aws-drs-orchestrator" \
        Environment="dev" \
        SourceBucket="$BUCKET" \
        AdminEmail="***REMOVED***" \
    --capabilities CAPABILITY_NAMED_IAM \
    --tags \
        Project="aws-drs-orchestrator" \
        Environment="dev" \
        DeployedBy="EmergencyDeployment" \
        Architecture="Archive-5-Stack" \
    --no-fail-on-empty-changeset

echo ""
echo "✅ EMERGENCY DEPLOYMENT COMPLETE"
echo ""
echo "=== Next Steps ==="
echo "1. Test the archive stack Lambda functions"
echo "2. Verify orchestration works correctly"
echo "3. Compare with broken current implementation"
echo "4. This deployment will be committed to Git immediately"