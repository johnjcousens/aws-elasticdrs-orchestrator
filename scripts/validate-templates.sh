#!/bin/bash
# CloudFormation Template Validation Script
# Comprehensive validation for AD-PKI-AIRGAPPED CloudFormation templates

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATE_DIR="$PROJECT_ROOT/cfn"
if [[ ! -d "$TEMPLATE_DIR" ]]; then
    TEMPLATE_DIR="$PROJECT_ROOT/templates"
fi

# Global variables
FAILED_TESTS=0
TOTAL_TESTS=0
VERBOSE=false

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_success() {
    print_status "$GREEN" "✅ $1"
}

print_error() {
    print_status "$RED" "❌ $1"
}

print_warning() {
    print_status "$YELLOW" "⚠️  $1"
}

print_info() {
    print_status "$BLUE" "ℹ️  $1"
}

# Function to increment test counters
record_test() {
    local result=$1
    ((TOTAL_TESTS++))
    if [[ $result != "0" ]]; then
        ((FAILED_TESTS++))
    fi
}

# Function to check if required tools are installed
check_dependencies() {
    print_info "Checking dependencies..."
    
    local missing_tools=()
    
    if ! command -v cfn-lint &> /dev/null; then
        missing_tools+=("cfn-lint")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_info "Run 'make install' to install missing dependencies"
        return 1
    fi
    
    print_success "All dependencies found"
    return 0
}

# Function to validate template syntax
validate_yaml_syntax() {
    local template=$1
    print_info "Validating YAML syntax: $(basename "$template")"
    
    if python3 -c "import yaml; yaml.safe_load(open('$template'))" 2>/dev/null; then
        print_success "YAML syntax valid"
        return 0
    else
        print_error "YAML syntax invalid"
        return 1
    fi
}

# Function to run cfn-lint
run_cfn_lint() {
    local template=$1
    print_info "Running cfn-lint: $(basename "$template")"
    
    if cfn-lint "$template" --config-file "$PROJECT_ROOT/.cfnlintrc.yaml"; then
        print_success "cfn-lint validation passed"
        return 0
    else
        print_error "cfn-lint validation failed"
        return 1
    fi
}

# Function to check AMI parameters
check_ami_parameters() {
    local template=$1
    print_info "Checking AMI parameters: $(basename "$template")"
    
    local ami_issues=0
    
    # Check for Windows Server 2022 references (should be 2025)
    if grep -q "Windows_Server-2022-English-Full-Base" "$template"; then
        print_warning "Found Windows Server 2022 AMI reference (should be 2025)"
        ami_issues=1
    fi
    
    # Check for Windows Server 2025 references (correct)
    if grep -q "Windows_Server-2025-English-Full-Base" "$template"; then
        print_success "Found Windows Server 2025 AMI reference"
    else
        print_warning "No Windows Server 2025 AMI reference found"
        ami_issues=1
    fi
    
    return $ami_issues
}

# Function to check description formatting
check_description_formatting() {
    local template=$1
    print_info "Checking description formatting: $(basename "$template")"
    
    local format_issues=0
    
    # Check for common typos
    if grep -i "suboordinate" "$template" >/dev/null; then
        print_warning "Found typo: 'Suboordinate' (should be 'Subordinate')"
        format_issues=1
    fi
    
    if grep -i "deploed" "$template" >/dev/null; then
        print_warning "Found typo: 'deploed' (should be 'deployed')"
        format_issues=1
    fi
    
    # Check for inconsistent multi-line description formatting
    if grep -E "^Description: >-" "$template" >/dev/null; then
        print_warning "Found '>-' description formatting (should be '>')"
        format_issues=1
    fi
    
    if [[ $format_issues -eq 0 ]]; then
        print_success "Description formatting looks good"
    fi
    
    return $format_issues
}

# Function to check metadata and ignore rules
check_metadata() {
    local template=$1
    print_info "Checking metadata and ignore rules: $(basename "$template")"
    
    # Check if cfn-lint ignore rules are present
    if grep -q "cfn-lint:" "$template"; then
        print_success "cfn-lint ignore rules found"
        
        # Show which rules are being ignored
        if [[ $VERBOSE == true ]]; then
            print_info "Ignored rules:"
            grep -A 5 "cfn-lint:" "$template" | grep -E "(W[0-9]{4}|E[0-9]{4})" | sed 's/^/    /'
        fi
        return 0
    else
        print_warning "No cfn-lint ignore rules found"
        return 1
    fi
}

# Function to validate a single template
validate_template() {
    local template=$1
    print_info "========================================"
    print_info "Validating: $(basename "$template")"
    print_info "========================================"
    
    local template_errors=0
    
    # YAML syntax validation
    validate_yaml_syntax "$template"
    record_test $?
    template_errors=$((template_errors + $?))
    
    # cfn-lint validation
    run_cfn_lint "$template"
    record_test $?
    template_errors=$((template_errors + $?))
    
    # AMI parameter validation
    check_ami_parameters "$template"
    record_test $?
    template_errors=$((template_errors + $?))
    
    # Description formatting validation
    check_description_formatting "$template"
    record_test $?
    template_errors=$((template_errors + $?))
    
    # Metadata validation
    check_metadata "$template"
    record_test $?
    # Note: Don't count metadata warnings as errors
    
    if [[ $template_errors -eq 0 ]]; then
        print_success "Template validation passed: $(basename "$template")"
    else
        print_error "Template validation failed: $(basename "$template") ($template_errors issues)"
    fi
    
    return $template_errors
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [TEMPLATE_FILES...]

CloudFormation Template Validation Script

OPTIONS:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    -d, --dir DIR   Specify template directory (default: templates)
    
EXAMPLES:
    $0                                          # Validate all templates
    $0 templates/activedirectory-on-ec2.yaml   # Validate specific template
    $0 -v                                       # Validate with verbose output
    
EOF
}

# Function to find all templates
find_templates() {
    local template_dir=${1:-$TEMPLATE_DIR}
    find "$template_dir" -name "*.yaml" -o -name "*.yml" | sort
}

# Main function
main() {
    local templates=()
    local template_dir="$TEMPLATE_DIR"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -d|--dir)
                template_dir="$2"
                shift 2
                ;;
            *.yaml|*.yml)
                templates+=("$1")
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Header
    print_info "AD-PKI-AIRGAPPED CloudFormation Template Validation"
    print_info "===================================================="
    echo
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    echo
    
    # Determine templates to validate
    if [[ ${#templates[@]} -eq 0 ]]; then
        print_info "No specific templates provided, validating all templates in $template_dir"
        readarray -t templates < <(find_templates "$template_dir")
    fi
    
    if [[ ${#templates[@]} -eq 0 ]]; then
        print_error "No CloudFormation templates found"
        exit 1
    fi
    
    print_info "Found ${#templates[@]} template(s) to validate"
    echo
    
    # Validate each template
    local overall_errors=0
    for template in "${templates[@]}"; do
        if [[ ! -f "$template" ]]; then
            print_error "Template not found: $template"
            ((overall_errors++))
            continue
        fi
        
        validate_template "$template"
        overall_errors=$((overall_errors + $?))
        echo
    done
    
    # Summary
    print_info "========================================"
    print_info "VALIDATION SUMMARY"
    print_info "========================================"
    print_info "Templates validated: ${#templates[@]}"
    print_info "Total tests run: $TOTAL_TESTS"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        print_success "All tests passed! ✨"
        exit 0
    else
        print_error "Failed tests: $FAILED_TESTS"
        print_error "Overall validation failed"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
