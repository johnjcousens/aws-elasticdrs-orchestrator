#!/bin/bash

# API Gateway Architecture Validation Script
# Ensures CloudFormation templates follow the nested stack architecture pattern

set -e

echo "========================================"
echo "🏗️  API Gateway Architecture Validation"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
WARNINGS=0
ERRORS=0
CHECKS=0

# Function to print status
print_status() {
    local status=$1
    local message=$2
    CHECKS=$((CHECKS + 1))
    
    case $status in
        "PASS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  $message${NC}"
            WARNINGS=$((WARNINGS + 1))
            ;;
        "FAIL")
            echo -e "${RED}❌ $message${NC}"
            ERRORS=$((ERRORS + 1))
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Check if CloudFormation templates exist
check_template_existence() {
    echo ""
    echo "1. Checking CloudFormation template existence..."
    
    local templates=(
        "cfn/api-gateway-core-stack.yaml"
        "cfn/api-gateway-resources-stack.yaml"
        "cfn/api-gateway-core-methods-stack.yaml"
        "cfn/api-gateway-operations-methods-stack.yaml"
        "cfn/api-gateway-infrastructure-methods-stack.yaml"
        "cfn/api-gateway-deployment-stack.yaml"
        "cfn/api-auth-stack.yaml"
    )
    
    for template in "${templates[@]}"; do
        if [[ -f "$template" ]]; then
            print_status "PASS" "Template exists: $template"
        else
            print_status "FAIL" "Missing template: $template"
        fi
    done
}

# Check resource counts in each template
check_resource_counts() {
    echo ""
    echo "2. Checking resource counts per template..."
    
    local templates=(
        "cfn/api-gateway-core-stack.yaml"
        "cfn/api-gateway-resources-stack.yaml"
        "cfn/api-gateway-core-methods-stack.yaml"
        "cfn/api-gateway-operations-methods-stack.yaml"
        "cfn/api-gateway-infrastructure-methods-stack.yaml"
        "cfn/api-gateway-deployment-stack.yaml"
    )
    
    for template in "${templates[@]}"; do
        if [[ -f "$template" ]]; then
            # Count resources (lines starting with two spaces and ending with colon, excluding comments)
            local resource_count=$(grep -E "^  [A-Za-z][A-Za-z0-9]*:$" "$template" | grep -v "^  #" | wc -l | tr -d ' ')
            
            if [[ $resource_count -lt 350 ]]; then
                print_status "PASS" "$template: $resource_count resources (under 350 threshold)"
            elif [[ $resource_count -lt 400 ]]; then
                print_status "WARN" "$template: $resource_count resources (approaching 400 limit)"
            elif [[ $resource_count -lt 450 ]]; then
                print_status "WARN" "$template: $resource_count resources (near 450 action threshold)"
            else
                print_status "FAIL" "$template: $resource_count resources (exceeds safe limits)"
            fi
        fi
    done
}

# Check template file sizes
check_template_sizes() {
    echo ""
    echo "3. Checking template file sizes..."
    
    local templates=(
        "cfn/api-gateway-core-stack.yaml"
        "cfn/api-gateway-resources-stack.yaml"
        "cfn/api-gateway-core-methods-stack.yaml"
        "cfn/api-gateway-operations-methods-stack.yaml"
        "cfn/api-gateway-infrastructure-methods-stack.yaml"
        "cfn/api-gateway-deployment-stack.yaml"
    )
    
    for template in "${templates[@]}"; do
        if [[ -f "$template" ]]; then
            local size_bytes=$(stat -f%z "$template" 2>/dev/null || stat -c%s "$template" 2>/dev/null || echo "0")
            local size_kb=$((size_bytes / 1024))
            
            if [[ $size_kb -lt 400 ]]; then
                print_status "PASS" "$template: ${size_kb}KB (under 400KB threshold)"
            elif [[ $size_kb -lt 800 ]]; then
                print_status "WARN" "$template: ${size_kb}KB (approaching 800KB warning)"
            elif [[ $size_kb -lt 900 ]]; then
                print_status "WARN" "$template: ${size_kb}KB (near 900KB action threshold)"
            else
                print_status "FAIL" "$template: ${size_kb}KB (exceeds safe limits)"
            fi
        fi
    done
}

# Check naming conventions
check_naming_conventions() {
    echo ""
    echo "4. Checking resource naming conventions..."
    
    local method_templates=(
        "cfn/api-gateway-core-methods-stack.yaml"
        "cfn/api-gateway-operations-methods-stack.yaml"
        "cfn/api-gateway-infrastructure-methods-stack.yaml"
    )
    
    for template in "${method_templates[@]}"; do
        if [[ -f "$template" ]]; then
            # Check for proper method naming: [Feature][Action]Method
            local bad_names=$(grep -E "^  [A-Za-z][A-Za-z0-9]*:$" "$template" | grep -v "Method:$" | grep -v "^  #" | wc -l | tr -d ' ')
            
            if [[ $bad_names -eq 0 ]]; then
                print_status "PASS" "$template: All resources follow naming conventions"
            else
                print_status "WARN" "$template: $bad_names resources may not follow naming conventions"
            fi
        fi
    done
}

# Check CORS consistency
check_cors_consistency() {
    echo ""
    echo "5. Checking CORS consistency..."
    
    local method_templates=(
        "cfn/api-gateway-core-methods-stack.yaml"
        "cfn/api-gateway-operations-methods-stack.yaml"
        "cfn/api-gateway-infrastructure-methods-stack.yaml"
    )
    
    for template in "${method_templates[@]}"; do
        if [[ -f "$template" ]]; then
            # Check for OPTIONS methods
            local options_count=$(grep -c "HttpMethod: OPTIONS" "$template" 2>/dev/null || echo "0")
            local non_options_count=$(grep -c "HttpMethod: GET\|HttpMethod: POST\|HttpMethod: PUT\|HttpMethod: DELETE" "$template" 2>/dev/null || echo "0")
            
            if [[ $options_count -gt 0 ]] && [[ $non_options_count -gt 0 ]]; then
                print_status "PASS" "$template: Has OPTIONS methods for CORS ($options_count OPTIONS, $non_options_count other methods)"
            elif [[ $non_options_count -gt 0 ]]; then
                print_status "WARN" "$template: Has $non_options_count methods but no OPTIONS methods for CORS"
            else
                print_status "INFO" "$template: No HTTP methods found"
            fi
        fi
    done
}

# Check parameter passing between stacks
check_parameter_passing() {
    echo ""
    echo "6. Checking parameter passing between stacks..."
    
    # Check if core stack exports required outputs
    if [[ -f "cfn/api-gateway-core-stack.yaml" ]]; then
        local has_rest_api_export=$(grep -c "RestApiId" "cfn/api-gateway-core-stack.yaml" 2>/dev/null || echo "0")
        local has_authorizer_export=$(grep -c "AuthorizerId" "cfn/api-gateway-core-stack.yaml" 2>/dev/null || echo "0")
        
        if [[ $has_rest_api_export -gt 0 ]] && [[ $has_authorizer_export -gt 0 ]]; then
            print_status "PASS" "Core stack exports RestApiId and AuthorizerId"
        else
            print_status "WARN" "Core stack may be missing required exports"
        fi
    fi
    
    # Check if resources stack exports resource IDs
    if [[ -f "cfn/api-gateway-resources-stack.yaml" ]]; then
        local resource_exports=$(grep -c "ResourceId" "cfn/api-gateway-resources-stack.yaml" 2>/dev/null || echo "0")
        
        if [[ $resource_exports -gt 10 ]]; then
            print_status "PASS" "Resources stack exports $resource_exports resource IDs"
        else
            print_status "WARN" "Resources stack may be missing resource ID exports"
        fi
    fi
}

# Check for hardcoded values that should be parameters
check_hardcoded_values() {
    echo ""
    echo "7. Checking for hardcoded values..."
    
    local templates=(
        "cfn/api-gateway-core-methods-stack.yaml"
        "cfn/api-gateway-operations-methods-stack.yaml"
        "cfn/api-gateway-infrastructure-methods-stack.yaml"
    )
    
    for template in "${templates[@]}"; do
        if [[ -f "$template" ]]; then
            # Check for hardcoded REST API IDs (should use !Ref RestApiId)
            local hardcoded_apis=$(grep -E "RestApiId: [a-z0-9]" "$template" 2>/dev/null | wc -l | tr -d ' ')
            
            if [[ $hardcoded_apis -eq 0 ]]; then
                print_status "PASS" "$template: No hardcoded REST API IDs found"
            else
                print_status "FAIL" "$template: Found $hardcoded_apis hardcoded REST API IDs"
            fi
        fi
    done
}

# Check integration patterns
check_integration_patterns() {
    echo ""
    echo "8. Checking Lambda integration patterns..."
    
    local method_templates=(
        "cfn/api-gateway-core-methods-stack.yaml"
        "cfn/api-gateway-operations-methods-stack.yaml"
        "cfn/api-gateway-infrastructure-methods-stack.yaml"
    )
    
    for template in "${method_templates[@]}"; do
        if [[ -f "$template" ]]; then
            # Check for AWS_PROXY integration type
            local proxy_integrations=$(grep -c "Type: AWS_PROXY" "$template" 2>/dev/null || echo "0")
            local total_integrations=$(grep -c "Type: AWS\|Type: MOCK" "$template" 2>/dev/null || echo "0")
            
            if [[ $proxy_integrations -gt 0 ]] && [[ $total_integrations -gt 0 ]]; then
                local proxy_percentage=$((proxy_integrations * 100 / total_integrations))
                if [[ $proxy_percentage -gt 80 ]]; then
                    print_status "PASS" "$template: ${proxy_percentage}% AWS_PROXY integrations (${proxy_integrations}/${total_integrations})"
                else
                    print_status "WARN" "$template: Only ${proxy_percentage}% AWS_PROXY integrations (${proxy_integrations}/${total_integrations})"
                fi
            else
                print_status "INFO" "$template: No integrations found"
            fi
        fi
    done
}

# Generate architecture summary
generate_summary() {
    echo ""
    echo "9. Architecture Summary..."
    
    local total_resources=0
    local total_size_kb=0
    local template_count=0
    
    local templates=(
        "cfn/api-gateway-core-stack.yaml"
        "cfn/api-gateway-resources-stack.yaml"
        "cfn/api-gateway-core-methods-stack.yaml"
        "cfn/api-gateway-operations-methods-stack.yaml"
        "cfn/api-gateway-infrastructure-methods-stack.yaml"
        "cfn/api-gateway-deployment-stack.yaml"
    )
    
    for template in "${templates[@]}"; do
        if [[ -f "$template" ]]; then
            local resource_count=$(grep -E "^  [A-Za-z][A-Za-z0-9]*:$" "$template" | grep -v "^  #" | wc -l | tr -d ' ')
            local size_bytes=$(stat -f%z "$template" 2>/dev/null || stat -c%s "$template" 2>/dev/null || echo "0")
            local size_kb=$((size_bytes / 1024))
            
            total_resources=$((total_resources + resource_count))
            total_size_kb=$((total_size_kb + size_kb))
            template_count=$((template_count + 1))
        fi
    done
    
    print_status "INFO" "Total API Gateway templates: $template_count"
    print_status "INFO" "Total resources across all templates: $total_resources"
    print_status "INFO" "Total template size: ${total_size_kb}KB"
    print_status "INFO" "Average resources per template: $((total_resources / template_count))"
    print_status "INFO" "Average template size: $((total_size_kb / template_count))KB"
}

# Main execution
main() {
    check_template_existence
    check_resource_counts
    check_template_sizes
    check_naming_conventions
    check_cors_consistency
    check_parameter_passing
    check_hardcoded_values
    check_integration_patterns
    generate_summary
    
    echo ""
    echo "========================================"
    echo "📊 Validation Summary"
    echo "========================================"
    echo "Total checks: $CHECKS"
    echo -e "Passed: ${GREEN}$((CHECKS - WARNINGS - ERRORS))${NC}"
    echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
    echo -e "Errors: ${RED}$ERRORS${NC}"
    
    if [[ $ERRORS -gt 0 ]]; then
        echo ""
        echo -e "${RED}❌ Architecture validation failed with $ERRORS errors${NC}"
        echo "Please fix the errors above before proceeding."
        exit 1
    elif [[ $WARNINGS -gt 0 ]]; then
        echo ""
        echo -e "${YELLOW}⚠️  Architecture validation passed with $WARNINGS warnings${NC}"
        echo "Consider addressing the warnings above."
        exit 0
    else
        echo ""
        echo -e "${GREEN}✅ Architecture validation passed successfully${NC}"
        echo "All API Gateway templates follow the nested stack architecture pattern."
        exit 0
    fi
}

# Run main function
main "$@"