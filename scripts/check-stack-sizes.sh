#!/bin/bash
# Check CloudFormation stack sizes and resource counts
# Used by API Gateway architecture validation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CFN_DIR="$PROJECT_ROOT/cfn"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 CloudFormation Stack Size Analysis${NC}"
echo "========================================"

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

# All CloudFormation templates
ALL_STACKS=(
    "master-template.yaml"
    "database-stack.yaml"
    "lambda-stack.yaml"
    "api-auth-stack.yaml"
    "api-gateway-core-stack.yaml"
    "api-gateway-resources-stack.yaml"
    "api-gateway-core-methods-stack.yaml"
    "api-gateway-operations-methods-stack.yaml"
    "api-gateway-infrastructure-methods-stack.yaml"
    "api-gateway-deployment-stack.yaml"
    "step-functions-stack.yaml"
    "eventbridge-stack.yaml"
    "frontend-stack.yaml"
    "security-stack.yaml"
    "cross-account-role-stack.yaml"
)

# Track totals
total_resources=0
total_size_kb=0
warning_count=0
error_count=0

printf "%-45s %10s %10s %8s\n" "Stack File" "Resources" "Size (KB)" "Status"
printf "%-45s %10s %10s %8s\n" "----------" "---------" "---------" "------"

for stack in "${ALL_STACKS[@]}"; do
    if [[ -f "$CFN_DIR/$stack" ]]; then
        resource_count=$(count_resources "$CFN_DIR/$stack")
        file_size_kb=$(get_file_size_kb "$CFN_DIR/$stack")
        
        total_resources=$((total_resources + resource_count))
        total_size_kb=$((total_size_kb + file_size_kb))
        
        # Determine status
        status="OK"
        color="$GREEN"
        
        # Check for warnings/errors
        if [[ $resource_count -gt 400 || $file_size_kb -gt 800 ]]; then
            status="ERROR"
            color="$RED"
            ((error_count++))
        elif [[ $resource_count -gt 350 || $file_size_kb -gt 600 ]]; then
            status="WARN"
            color="$YELLOW"
            ((warning_count++))
        fi
        
        printf "%-45s %10d %10d ${color}%8s${NC}\n" "$stack" "$resource_count" "$file_size_kb" "$status"
    else
        printf "%-45s %10s %10s ${RED}%8s${NC}\n" "$stack" "N/A" "N/A" "MISSING"
        ((error_count++))
    fi
done

echo ""
echo "========================================"
printf "%-45s %10d %10d\n" "TOTAL" "$total_resources" "$total_size_kb"
echo ""

# Summary
echo -e "${BLUE}📋 Summary:${NC}"
echo "   Total Resources: $total_resources"
echo "   Total Size: ${total_size_kb}KB"
echo "   Errors: $error_count"
echo "   Warnings: $warning_count"

# API Gateway specific analysis
echo ""
echo -e "${BLUE}🔍 API Gateway Stack Analysis:${NC}"
API_STACKS=(
    "api-gateway-core-stack.yaml"
    "api-gateway-resources-stack.yaml"
    "api-gateway-core-methods-stack.yaml"
    "api-gateway-operations-methods-stack.yaml"
    "api-gateway-infrastructure-methods-stack.yaml"
    "api-gateway-deployment-stack.yaml"
)

api_total_resources=0
api_total_size=0

for stack in "${API_STACKS[@]}"; do
    if [[ -f "$CFN_DIR/$stack" ]]; then
        resource_count=$(count_resources "$CFN_DIR/$stack")
        file_size_kb=$(get_file_size_kb "$CFN_DIR/$stack")
        api_total_resources=$((api_total_resources + resource_count))
        api_total_size=$((api_total_size + file_size_kb))
    fi
done

echo "   API Gateway Resources: $api_total_resources"
echo "   API Gateway Size: ${api_total_size}KB"

# Recommendations
echo ""
echo -e "${BLUE}💡 Recommendations:${NC}"

if [[ $error_count -gt 0 ]]; then
    echo -e "${RED}❌ CRITICAL: $error_count stack(s) exceed limits${NC}"
    echo "   - Split stacks with >400 resources"
    echo "   - Split templates >800KB"
fi

if [[ $warning_count -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  WARNING: $warning_count stack(s) approaching limits${NC}"
    echo "   - Monitor stacks with >350 resources"
    echo "   - Monitor templates >600KB"
fi

# Capacity analysis
echo ""
echo -e "${BLUE}📈 Capacity Analysis:${NC}"
for stack in "${API_STACKS[@]}"; do
    if [[ -f "$CFN_DIR/$stack" ]]; then
        resource_count=$(count_resources "$CFN_DIR/$stack")
        file_size_kb=$(get_file_size_kb "$CFN_DIR/$stack")
        
        resource_capacity=$((400 - resource_count))
        size_capacity=$((800 - file_size_kb))
        
        if [[ $resource_capacity -lt 50 || $size_capacity -lt 100 ]]; then
            echo -e "${YELLOW}   $stack: ${resource_capacity} resources, ${size_capacity}KB remaining${NC}"
        fi
    fi
done

# Exit codes
if [[ $error_count -gt 0 ]]; then
    exit 1
elif [[ $warning_count -gt 0 ]]; then
    exit 2
else
    exit 0
fi