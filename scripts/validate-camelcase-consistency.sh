#!/bin/bash

# CamelCase Consistency Validation Script
# Validates that frontend and backend use consistent camelCase field names
# Prevents PascalCase/camelCase mismatches that cause deployment failures

set -e

echo "========================================"
echo "🔍 CamelCase Consistency Validation"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

# Function to report error
report_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ERRORS=$((ERRORS + 1))
}

# Function to report warning
report_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

# Function to report success
report_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to report info
report_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "Validating camelCase consistency across frontend and backend..."
echo

# 1. Check for PascalCase field names in TypeScript files
echo "1. Checking TypeScript files for PascalCase field violations..."

# Common PascalCase patterns that should be camelCase
PASCALCASE_PATTERNS=(
    "GroupId"
    "PlanId" 
    "ExecutionId"
    "SourceServerId"
    "WaveName"
    "ProtectionGroupId"
    "RecoveryPlanName"
    "ServerSelectionTags"
    "SourceServerIds"
    "LaunchConfig"
    "SubnetId"
    "SecurityGroupIds"
    "InstanceType"
    "InstanceProfileName"
    "CopyPrivateIp"
    "CopyTags"
    "TargetInstanceTypeRightSizingMethod"
    "LaunchDisposition"
    "Licensing"
    "CreatedAt"
    "UpdatedAt"
    "StartTime"
    "EndTime"
)

# Check frontend TypeScript files
FRONTEND_FILES=$(find frontend/src -name "*.ts" -o -name "*.tsx" 2>/dev/null || true)

if [ -n "$FRONTEND_FILES" ]; then
    for pattern in "${PASCALCASE_PATTERNS[@]}"; do
        # Look for the pattern as object property access (e.g., obj.GroupId)
        # Exclude interface names, type names, import statements, and comments
        matches=$(echo "$FRONTEND_FILES" | xargs grep -n "\\b${pattern}\\b" 2>/dev/null | grep -v "interface ${pattern}" | grep -v "export interface ${pattern}" | grep -v "import.*${pattern}" | grep -v "type.*${pattern}" | grep -v "LaunchConfig" | grep -v "label=" | grep -v "\\*.*${pattern}" || true)
        if [ -n "$matches" ]; then
            report_error "Found PascalCase field '${pattern}' in frontend files:"
            echo "$matches" | while read -r line; do
                echo "  $line"
            done
            echo
        fi
        
        # Look for the pattern in interface definitions
        interface_matches=$(echo "$FRONTEND_FILES" | xargs grep -n "^[[:space:]]*${pattern}[?:]" 2>/dev/null || true)
        if [ -n "$interface_matches" ]; then
            report_error "Found PascalCase interface field '${pattern}':"
            echo "$interface_matches" | while read -r line; do
                echo "  $line"
            done
            echo
        fi
    done
else
    report_warning "No TypeScript files found in frontend/src"
fi

# 2. Check for PascalCase field names in Python Lambda files
echo "2. Checking Python Lambda files for PascalCase field violations..."

LAMBDA_FILES=$(find lambda -name "*.py" 2>/dev/null || true)

if [ -n "$LAMBDA_FILES" ]; then
    for pattern in "${PASCALCASE_PATTERNS[@]}"; do
        # Look for PascalCase in dictionary keys or DynamoDB operations
        matches=$(echo "$LAMBDA_FILES" | xargs grep -n "\"${pattern}\"\\|'${pattern}'" 2>/dev/null || true)
        if [ -n "$matches" ]; then
            # Filter out comments, transform function definitions, AWS API responses, CloudWatch metrics, EC2 template fields, and AWS service calls
            filtered_matches=$(echo "$matches" | grep -v "# Transform" | grep -v "def transform" | grep -v "subnet\[" | grep -v "profile\[" | grep -v "CloudWatch" | grep -v "Dimensions" | grep -v "network_interface\[" | grep -v "Name.*ExecutionId" | grep -v "sg\[" | grep -v "it\[" | grep -v "instance\[" | grep -v "result\[.*SecurityGroups" | grep -v "result\[.*InstanceTypes" | grep -v "ec2\\.describe" | grep -v "iam\\.list" | grep -v "paginator\\.paginate" || true)
            if [ -n "$filtered_matches" ]; then
                report_error "Found PascalCase field '${pattern}' in Lambda files:"
                echo "$filtered_matches" | while read -r line; do
                    echo "  $line"
                done
                echo
            fi
        fi
    done
else
    report_warning "No Python files found in lambda directory"
fi

# 3. Check for transform functions (should be eliminated)
echo "3. Checking for eliminated transform functions..."

TRANSFORM_FUNCTIONS=(
    "transform_execution_to_camelcase"
    "transform_execution_to_camelcase_lightweight"
    "transform_pg_to_camelcase"
    "transform_plan_to_camelcase"
)

if [ -n "$LAMBDA_FILES" ]; then
    for func in "${TRANSFORM_FUNCTIONS[@]}"; do
        matches=$(echo "$LAMBDA_FILES" | xargs grep -n "def ${func}\\|${func}(" 2>/dev/null || true)
        if [ -n "$matches" ]; then
            report_error "Found eliminated transform function '${func}':"
            echo "$matches" | while read -r line; do
                echo "  $line"
            done
            echo
        fi
    done
fi

# 4. Check API service calls use camelCase
echo "4. Checking API service calls use camelCase..."

API_FILE="frontend/src/services/api.ts"
if [ -f "$API_FILE" ]; then
    # Check for PascalCase in API request bodies
    for pattern in "${PASCALCASE_PATTERNS[@]}"; do
        # Skip GroupId as it's often part of protectionGroupId (legitimate camelCase)
        if [ "$pattern" = "GroupId" ]; then
            matches=$(grep -n "\\b${pattern}:" "$API_FILE" 2>/dev/null | grep -v "protectionGroupId" || true)
        else
            matches=$(grep -n "${pattern}:" "$API_FILE" 2>/dev/null || true)
        fi
        if [ -n "$matches" ]; then
            report_error "Found PascalCase field '${pattern}' in API requests:"
            echo "$matches" | while read -r line; do
                echo "  $line"
            done
            echo
        fi
    done
else
    report_warning "API service file not found: $API_FILE"
fi

# 5. Check for consistent field naming in components
echo "5. Checking component field consistency..."

COMPONENT_FILES=$(find frontend/src/components -name "*.tsx" 2>/dev/null || true)

if [ -n "$COMPONENT_FILES" ]; then
    # Check for updateConfig calls with PascalCase
    for pattern in "${PASCALCASE_PATTERNS[@]}"; do
        matches=$(echo "$COMPONENT_FILES" | xargs grep -n "updateConfig('${pattern}'" 2>/dev/null || true)
        if [ -n "$matches" ]; then
            report_error "Found PascalCase updateConfig call for '${pattern}':"
            echo "$matches" | while read -r line; do
                echo "  $line"
            done
            echo
        fi
    done
fi

# 6. Validate camelCase equivalents exist
echo "6. Validating camelCase equivalents..."

# Check that camelCase versions are used in TypeScript interfaces
TYPES_FILE="frontend/src/types/index.ts"
if [ -f "$TYPES_FILE" ]; then
    # Check for specific problematic patterns
    pascal_patterns=("GroupId" "PlanId" "ExecutionId" "SourceServerId" "WaveName")
    camel_patterns=("groupId" "planId" "executionId" "sourceServerId" "waveName")
    
    for i in "${!pascal_patterns[@]}"; do
        pascal="${pascal_patterns[$i]}"
        camel="${camel_patterns[$i]}"
        
        # Check if standalone PascalCase version exists (not as part of compound names)
        camel_exists=$(grep -c "\\b${camel}[?:]" "$TYPES_FILE" 2>/dev/null || echo "0")
        pascal_exists=$(grep -c "\\b${pascal}[?:]" "$TYPES_FILE" 2>/dev/null || echo "0")
        
        # Convert to integers to handle potential "00" output
        camel_count=$(echo "$camel_exists" | sed 's/^0*//' | grep -E '^[0-9]+$' || echo "0")
        pascal_count=$(echo "$pascal_exists" | sed 's/^0*//' | grep -E '^[0-9]+$' || echo "0")
        
        # Default to 0 if empty
        camel_count=${camel_count:-0}
        pascal_count=${pascal_count:-0}
        
        if [ "$pascal_count" -gt 0 ] && [ "$camel_count" -eq 0 ]; then
            report_error "PascalCase field '${pascal}' found but camelCase '${camel}' missing in types"
        elif [ "$pascal_count" -gt 0 ] && [ "$camel_count" -gt 0 ]; then
            report_warning "Both PascalCase '${pascal}' and camelCase '${camel}' found - remove PascalCase"
        fi
    done
else
    report_warning "Types file not found: $TYPES_FILE"
fi

# 6.1. Check for field name consistency between frontend and backend
echo "6.1. Checking API field validation consistency..."

API_HANDLER="lambda/api-handler/index.py"
if [ -f "$API_HANDLER" ]; then
    # Check createProtectionGroup field validation - but exclude AWS API field references
    if grep -n "\"GroupName\"" "$API_HANDLER" | grep -v "sg\[" | grep -v "result\[" | grep -v "ec2\\.describe" > /dev/null 2>&1; then
        report_error "Backend validates 'GroupName' (PascalCase) but frontend sends 'groupName' (camelCase)"
    fi
    
    if grep -n "\"Region\"" "$API_HANDLER" | grep -v "subnet\[" | grep -v "profile\[" | grep -v "ec2\\.describe" > /dev/null 2>&1; then
        report_error "Backend validates 'Region' (PascalCase) but frontend sends 'region' (camelCase)"
    fi
    
    if grep -n "\"PlanName\"" "$API_HANDLER" > /dev/null 2>&1; then
        report_error "Backend validates 'PlanName' (PascalCase) but frontend sends 'name' (camelCase)"
    fi
    
    # Check that backend uses camelCase validation
    if ! grep -n "\"groupName\"" "$API_HANDLER" > /dev/null 2>&1; then
        report_warning "Backend should validate 'groupName' (camelCase) for createProtectionGroup"
    fi
    
    if ! grep -n "\"region\"" "$API_HANDLER" > /dev/null 2>&1; then
        report_warning "Backend should validate 'region' (camelCase) for createProtectionGroup"
    fi
else
    report_warning "API handler file not found: $API_HANDLER"
fi

# 7. Check for deprecated field patterns
echo "7. Checking for deprecated field patterns..."

DEPRECATED_PATTERNS=(
    "ProtectionGroupIds.*PascalCase"
    "ProtectionGroupId.*PascalCase" 
    "LaunchConfig.*PascalCase"
)

if [ -n "$FRONTEND_FILES" ]; then
    for pattern in "${DEPRECATED_PATTERNS[@]}"; do
        matches=$(echo "$FRONTEND_FILES" | xargs grep -n "$pattern" 2>/dev/null || true)
        if [ -n "$matches" ]; then
            report_warning "Found deprecated pattern '$pattern':"
            echo "$matches" | while read -r line; do
                echo "  $line"
            done
            echo
        fi
    done
fi

# Summary
echo "========================================"
echo "📊 Validation Summary"
echo "========================================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    report_success "All camelCase consistency checks passed!"
    echo -e "${GREEN}✅ Frontend and backend use consistent camelCase field names${NC}"
    echo -e "${GREEN}✅ No PascalCase field violations found${NC}"
    echo -e "${GREEN}✅ Transform functions properly eliminated${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Validation completed with $WARNINGS warnings${NC}"
    echo -e "${YELLOW}⚠️  Consider addressing warnings for better consistency${NC}"
    exit 0
else
    echo -e "${RED}❌ Validation failed with $ERRORS errors and $WARNINGS warnings${NC}"
    echo
    echo -e "${RED}🚨 DEPLOYMENT BLOCKED: Fix camelCase consistency issues${NC}"
    echo
    echo "Common fixes:"
    echo "1. Update PascalCase field names to camelCase in TypeScript files"
    echo "2. Update component updateConfig calls to use camelCase"
    echo "3. Remove any remaining transform functions"
    echo "4. Ensure API requests use camelCase field names"
    echo
    echo "For help, see: camelcase-migration-plan.md"
    exit 1
fi