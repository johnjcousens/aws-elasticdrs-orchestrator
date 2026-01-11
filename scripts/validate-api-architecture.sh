#!/bin/bash
# API Gateway Architecture Validation Script
# Validates compliance with nested stack architecture rules

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CFN_DIR="$PROJECT_ROOT/cfn"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

echo "🔍 Validating API Gateway Architecture Compliance..."

# Function to count resources in CloudFormation template
count_resources() {
    local file="$1"
    if [[ -f "$file" ]]; then
        grep -c "Type: AWS::" "$file" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Function to get file size in KB
get_file_size_kb() {
    local file="$1"
    if [[ -f "$file" ]]; then
        local size_bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        echo $((size_bytes / 1024))
    else
        echo "0"
    fi
}

# Check if API Gateway stacks exist
API_STACKS=(
    "api-gateway-core-stack.yaml"
    "api-gateway-resources-stack.yaml"
    "api-gateway-core-methods-stack.yaml"
    "api-gateway-operations-methods-stack.yaml"
    "api-gateway-infrastructure-methods-stack.yaml"
    "api-gateway-deployment-stack.yaml"
)

echo "📋 Checking API Gateway stack files..."
for stack in "${API_STACKS[@]}"; do
    if [[ ! -f "$CFN_DIR/$stack" ]]; then
        echo -e "${RED}❌ ERROR: Missing required stack file: $stack${NC}"
        ((ERRORS++))
    else
        echo -e "${GREEN}✅ Found: $stack${NC}"
    fi
done

# Check resource counts and template sizes
echo ""
echo "📊 Checking resource counts and template sizes..."
for stack in "${API_STACKS[@]}"; do
    if [[ -f "$CFN_DIR/$stack" ]]; then
        resource_count=$(count_resources "$CFN_DIR/$stack")
        file_size_kb=$(get_file_size_kb "$CFN_DIR/$stack")
        
        echo "📄 $stack:"
        echo "   Resources: $resource_count"
        echo "   Size: ${file_size_kb}KB"
        
        # Check resource count limits
        if [[ $resource_count -gt 400 ]]; then
            echo -e "${RED}❌ ERROR: Resource count ($resource_count) exceeds limit (400)${NC}"
            ((ERRORS++))
        elif [[ $resource_count -gt 350 ]]; then
            echo -e "${YELLOW}⚠️  WARNING: Resource count ($resource_count) approaching limit (400)${NC}"
            ((WARNINGS++))
        fi
        
        # Check template size limits
        if [[ $file_size_kb -gt 800 ]]; then
            echo -e "${RED}❌ ERROR: Template size (${file_size_kb}KB) exceeds limit (800KB)${NC}"
            ((ERRORS++))
        elif [[ $file_size_kb -gt 600 ]]; then
            echo -e "${YELLOW}⚠️  WARNING: Template size (${file_size_kb}KB) approaching limit (800KB)${NC}"
            ((WARNINGS++))
        fi
    fi
done

# Check naming conventions in method stacks
echo ""
echo "🏷️  Checking naming conventions..."
METHOD_STACKS=(
    "api-gateway-core-methods-stack.yaml"
    "api-gateway-operations-methods-stack.yaml"
    "api-gateway-infrastructure-methods-stack.yaml"
)

for stack in "${METHOD_STACKS[@]}"; do
    if [[ -f "$CFN_DIR/$stack" ]]; then
        echo "📄 Checking $stack..."
        
        # Check for proper method naming pattern
        if grep -q "Type: AWS::ApiGateway::Method" "$CFN_DIR/$stack"; then
            # Look for methods that don't follow [Feature][Action]Method pattern
            bad_methods=$(grep -B2 "Type: AWS::ApiGateway::Method" "$CFN_DIR/$stack" | grep -E "^\s*[A-Za-z]+:" | grep -v -E "^\s*[A-Z][a-zA-Z]*[A-Z][a-zA-Z]*Method:" || true)
            if [[ -n "$bad_methods" ]]; then
                echo -e "${YELLOW}⚠️  WARNING: Potential naming convention violations in $stack${NC}"
                echo "$bad_methods"
                ((WARNINGS++))
            fi
        fi
        
        # Check for missing OPTIONS methods
        get_methods=$(grep -c "HttpMethod: GET" "$CFN_DIR/$stack" 2>/dev/null || echo "0")
        options_methods=$(grep -c "HttpMethod: OPTIONS" "$CFN_DIR/$stack" 2>/dev/null || echo "0")
        
        if [[ $get_methods -gt 0 && $options_methods -eq 0 ]]; then
            echo -e "${RED}❌ ERROR: Missing OPTIONS methods for CORS in $stack${NC}"
            ((ERRORS++))
        elif [[ $get_methods -gt $options_methods ]]; then
            echo -e "${YELLOW}⚠️  WARNING: Possible missing OPTIONS methods in $stack (GET: $get_methods, OPTIONS: $options_methods)${NC}"
            ((WARNINGS++))
        fi
    fi
done

# Check for API Gateway resources in wrong stacks
echo ""
echo "🔍 Checking for misplaced API Gateway resources..."
NON_API_STACKS=(
    "master-template.yaml"
    "database-stack.yaml"
    "lambda-stack.yaml"
    "step-functions-stack.yaml"
    "eventbridge-stack.yaml"
    "frontend-stack.yaml"
    "security-stack.yaml"
)

for stack in "${NON_API_STACKS[@]}"; do
    if [[ -f "$CFN_DIR/$stack" ]]; then
        api_resources=$(grep -c "Type: AWS::ApiGateway::" "$CFN_DIR/$stack" 2>/dev/null || echo "0")
        if [[ $api_resources -gt 0 ]]; then
            echo -e "${RED}❌ ERROR: Found API Gateway resources in non-API stack: $stack${NC}"
            ((ERRORS++))
        fi
    fi
done

# Check for AWS_PROXY integration pattern
echo ""
echo "🔗 Checking Lambda integration patterns..."
for stack in "${METHOD_STACKS[@]}"; do
    if [[ -f "$CFN_DIR/$stack" ]]; then
        # Check for non-AWS_PROXY integrations (excluding OPTIONS methods)
        non_proxy=$(grep -A10 "Type: AWS::ApiGateway::Method" "$CFN_DIR/$stack" | grep -B5 -A5 "Type: AWS" | grep -v "Type: AWS_PROXY" | grep -v "Type: MOCK" | grep "Type:" || true)
        if [[ -n "$non_proxy" ]]; then
            echo -e "${YELLOW}⚠️  WARNING: Non-standard integration types found in $stack${NC}"
            ((WARNINGS++))
        fi
    fi
done

# Summary
echo ""
echo "📋 Validation Summary:"
echo "   Errors: $ERRORS"
echo "   Warnings: $WARNINGS"

if [[ $ERRORS -gt 0 ]]; then
    echo -e "${RED}❌ VALIDATION FAILED: $ERRORS error(s) found${NC}"
    echo "Please fix errors before proceeding with deployment."
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  VALIDATION PASSED WITH WARNINGS: $WARNINGS warning(s) found${NC}"
    echo "Consider addressing warnings for better compliance."
    exit 0
else
    echo -e "${GREEN}✅ VALIDATION PASSED: No issues found${NC}"
    exit 0
fi