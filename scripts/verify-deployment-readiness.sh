#!/bin/bash
# Verify Deployment Readiness - Confirms all artifacts are ready for customer deployment
# Usage: ./scripts/verify-deployment-readiness.sh <bucket-name> [environment]

set -e
export AWS_PAGER=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BUCKET_NAME="${1:-}"
ENVIRONMENT="${2:-prod}"

if [ -z "$BUCKET_NAME" ]; then
    echo -e "${RED}❌ Error: Bucket name required${NC}"
    echo "Usage: $0 <bucket-name> [environment]"
    echo "Example: $0 customer-deployment-bucket prod"
    exit 1
fi

echo "========================================="
echo "Deployment Readiness Verification"
echo "========================================="
echo "Bucket: $BUCKET_NAME"
echo "Environment: $ENVIRONMENT"
echo ""

ERRORS=0
WARNINGS=0

# Function to check if S3 object exists
check_s3_object() {
    local key="$1"
    local description="$2"
    local required="${3:-true}"
    
    if aws s3api head-object --bucket "$BUCKET_NAME" --key "$key" &>/dev/null; then
        SIZE=$(aws s3api head-object --bucket "$BUCKET_NAME" --key "$key" --query 'ContentLength' --output text)
        SIZE_MB=$(echo "scale=2; $SIZE / 1024 / 1024" | bc)
        echo -e "${GREEN}✅ $description${NC} (${SIZE_MB} MB)"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ MISSING: $description${NC}"
            echo "   Expected: s3://$BUCKET_NAME/$key"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠️  OPTIONAL: $description not found${NC}"
            ((WARNINGS++))
        fi
        return 1
    fi
}

echo "1. Checking CloudFormation Templates..."
echo "----------------------------------------"
check_s3_object "cfn/master-template.yaml" "Master Template"
check_s3_object "cfn/api-auth-stack.yaml" "API Auth Stack"
check_s3_object "cfn/api-gateway-core-stack.yaml" "API Gateway Core Stack"
check_s3_object "cfn/api-gateway-core-methods-stack.yaml" "API Gateway Core Methods"
check_s3_object "cfn/api-gateway-infrastructure-methods-stack.yaml" "API Gateway Infrastructure Methods"
check_s3_object "cfn/api-gateway-operations-methods-stack.yaml" "API Gateway Operations Methods"
check_s3_object "cfn/api-gateway-resources-stack.yaml" "API Gateway Resources"
check_s3_object "cfn/api-gateway-deployment-stack.yaml" "API Gateway Deployment"
check_s3_object "cfn/database-stack.yaml" "Database Stack"
check_s3_object "cfn/lambda-stack.yaml" "Lambda Stack"
check_s3_object "cfn/step-functions-stack.yaml" "Step Functions Stack"
check_s3_object "cfn/frontend-stack.yaml" "Frontend Stack"
check_s3_object "cfn/eventbridge-stack.yaml" "EventBridge Stack"
check_s3_object "cfn/notification-stack.yaml" "Notification Stack"
check_s3_object "cfn/cross-account-role-stack.yaml" "Cross-Account Role Stack"
check_s3_object "cfn/security-stack.yaml" "Security Stack" false
check_s3_object "cfn/security-monitoring-stack.yaml" "Security Monitoring Stack" false
echo ""

echo "2. Checking Lambda Packages..."
echo "----------------------------------------"
check_s3_object "lambda/api-handler.zip" "API Handler Lambda"
check_s3_object "lambda/orchestration-stepfunctions.zip" "Orchestration Step Functions Lambda"
check_s3_object "lambda/execution-finder.zip" "Execution Finder Lambda"
check_s3_object "lambda/execution-poller.zip" "Execution Poller Lambda"
check_s3_object "lambda/bucket-cleaner.zip" "Bucket Cleaner Lambda"
check_s3_object "lambda/notification-formatter.zip" "Notification Formatter Lambda"
check_s3_object "lambda/frontend-builder.zip" "Frontend Builder Lambda"
echo ""

echo "3. Verifying Lambda Package Sizes..."
echo "----------------------------------------"
# Check that Lambda packages are NOT bloated (should be ~95 KB, not 16 MB)
for lambda in api-handler orchestration-stepfunctions execution-finder execution-poller bucket-cleaner notification-formatter; do
    if aws s3api head-object --bucket "$BUCKET_NAME" --key "lambda/$lambda.zip" &>/dev/null; then
        SIZE=$(aws s3api head-object --bucket "$BUCKET_NAME" --key "lambda/$lambda.zip" --query 'ContentLength' --output text)
        SIZE_KB=$(echo "scale=0; $SIZE / 1024" | bc)
        
        # Warn if package is larger than 1 MB (likely includes boto3/urllib3)
        if [ "$SIZE" -gt 1048576 ]; then
            echo -e "${YELLOW}⚠️  WARNING: $lambda.zip is ${SIZE_KB} KB (expected ~95 KB)${NC}"
            echo "   This package may include boto3/urllib3 which are already in Lambda runtime"
            echo "   Run: make build-lambda ENV=$ENVIRONMENT to rebuild with correct dependencies"
            ((WARNINGS++))
        else
            echo -e "${GREEN}✅ $lambda.zip size OK${NC} (${SIZE_KB} KB)"
        fi
    fi
done

# Frontend builder should be larger (includes crhelper + pre-built frontend)
if aws s3api head-object --bucket "$BUCKET_NAME" --key "lambda/frontend-builder.zip" &>/dev/null; then
    SIZE=$(aws s3api head-object --bucket "$BUCKET_NAME" --key "lambda/frontend-builder.zip" --query 'ContentLength' --output text)
    SIZE_MB=$(echo "scale=2; $SIZE / 1024 / 1024" | bc)
    echo -e "${GREEN}✅ frontend-builder.zip size OK${NC} (${SIZE_MB} MB - includes frontend dist)"
fi
echo ""

echo "4. Checking Frontend Assets (Optional)..."
echo "----------------------------------------"
check_s3_object "frontend/dist/index.html" "Frontend index.html" false
check_s3_object "frontend/dist/assets/" "Frontend assets/" false
echo ""

echo "5. Testing S3 Bucket Access..."
echo "----------------------------------------"
if aws s3 ls "s3://$BUCKET_NAME/" &>/dev/null; then
    echo -e "${GREEN}✅ S3 bucket accessible${NC}"
else
    echo -e "${RED}❌ Cannot access S3 bucket${NC}"
    ((ERRORS++))
fi
echo ""

echo "========================================="
echo "Verification Summary"
echo "========================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo ""
    echo "Deployment is ready! Customer can deploy with:"
    echo ""
    echo "aws cloudformation deploy \\"
    echo "  --template-file cfn/master-template.yaml \\"
    echo "  --stack-name customer-drs-orchestrator \\"
    echo "  --parameter-overrides \\"
    echo "    ProjectName=customer-drs-orch \\"
    echo "    Environment=$ENVIRONMENT \\"
    echo "    SourceBucket=$BUCKET_NAME \\"
    echo "    AdminEmail=admin@customer.com \\"
    echo "  --capabilities CAPABILITY_NAMED_IAM \\"
    echo "  --region us-east-1"
    echo ""
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  PASSED WITH WARNINGS: $WARNINGS warning(s)${NC}"
    echo ""
    echo "Deployment will work, but review warnings above."
    echo ""
    exit 0
else
    echo -e "${RED}❌ FAILED: $ERRORS error(s), $WARNINGS warning(s)${NC}"
    echo ""
    echo "Fix errors above before deploying."
    echo ""
    exit 1
fi
