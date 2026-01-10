#!/bin/bash

# AWS DRS Orchestration - Emergency Rollback Script
# Quick rollback for Lambda security implementation issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_TAG="v1.3.0-pre-security-fixes"
BACKUP_DIR="backup/lambda-functions"

echo -e "${RED}=== EMERGENCY ROLLBACK SCRIPT ===${NC}"
echo "This script will rollback Lambda security changes"
echo "Timestamp: $(date)"
echo ""

# Function to print status
print_status() {
    local message="$1"
    local type="$2"
    
    case $type in
        "info")
            echo -e "${BLUE}ℹ INFO${NC} - $message"
            ;;
        "success")
            echo -e "${GREEN}✓ SUCCESS${NC} - $message"
            ;;
        "warning")
            echo -e "${YELLOW}⚠ WARNING${NC} - $message"
            ;;
        "error")
            echo -e "${RED}✗ ERROR${NC} - $message"
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# Function to rollback single Lambda function
rollback_lambda_function() {
    local function_name="$1"
    local method="$2"
    
    print_status "Rolling back $function_name using method: $method" "info"
    
    case $method in
        "git-head")
            git checkout HEAD~1 -- "lambda/$function_name/index.py"
            ;;
        "git-tag")
            git checkout "$BACKUP_TAG" -- "lambda/$function_name/index.py"
            ;;
        "backup-file")
            if [ -f "$BACKUP_DIR/$function_name/index.py" ]; then
                cp "$BACKUP_DIR/$function_name/index.py" "lambda/$function_name/"
            else
                print_status "Backup file not found for $function_name" "error"
                return 1
            fi
            ;;
        *)
            print_status "Unknown rollback method: $method" "error"
            return 1
            ;;
    esac
    
    print_status "Rolled back $function_name" "success"
}

# Function to deploy Lambda changes
deploy_lambda_changes() {
    print_status "Deploying Lambda changes..." "info"
    
    if [ -f "./scripts/sync-to-deployment-bucket.sh" ]; then
        ./scripts/sync-to-deployment-bucket.sh --update-lambda-code
        print_status "Lambda deployment completed" "success"
    else
        print_status "Deployment script not found" "error"
        return 1
    fi
}

# Function to validate system after rollback
validate_system() {
    print_status "Validating system health..." "info"
    
    if [ -f "./scripts/validate-system-health.sh" ]; then
        if ./scripts/validate-system-health.sh; then
            print_status "System validation passed" "success"
            return 0
        else
            print_status "System validation failed" "error"
            return 1
        fi
    else
        print_status "Validation script not found, skipping validation" "warning"
        return 0
    fi
}

# Show rollback options
show_rollback_options() {
    echo -e "${BLUE}Available rollback options:${NC}"
    echo "1. Single function rollback (specify function name)"
    echo "2. All functions rollback (git HEAD~1)"
    echo "3. All functions rollback (git tag: $BACKUP_TAG)"
    echo "4. All functions rollback (backup files)"
    echo "5. Critical functions only (orchestration-stepfunctions + api-handler)"
    echo "6. Background services only (execution-finder, execution-poller, etc.)"
    echo "7. Custom selection"
    echo "8. Exit"
    echo ""
}

# Rollback single function
rollback_single_function() {
    echo -e "${YELLOW}Available Lambda functions:${NC}"
    echo "- api-handler"
    echo "- orchestration-stepfunctions"
    echo "- execution-finder"
    echo "- execution-poller"
    echo "- frontend-builder"
    echo "- notification-formatter"
    echo ""
    
    read -p "Enter function name: " function_name
    
    if [ -z "$function_name" ]; then
        print_status "No function name provided" "error"
        return 1
    fi
    
    echo -e "${YELLOW}Rollback methods:${NC}"
    echo "1. git-head (HEAD~1)"
    echo "2. git-tag ($BACKUP_TAG)"
    echo "3. backup-file"
    echo ""
    
    read -p "Select method (1-3): " method_choice
    
    case $method_choice in
        1) method="git-head" ;;
        2) method="git-tag" ;;
        3) method="backup-file" ;;
        *) 
            print_status "Invalid method selection" "error"
            return 1
            ;;
    esac
    
    rollback_lambda_function "$function_name" "$method"
    deploy_lambda_changes
    validate_system
}

# Rollback all functions
rollback_all_functions() {
    local method="$1"
    
    FUNCTIONS=(
        "api-handler"
        "orchestration-stepfunctions"
        "execution-finder"
        "execution-poller"
        "frontend-builder"
        "notification-formatter"
    )
    
    print_status "Rolling back all Lambda functions using method: $method" "info"
    
    for func in "${FUNCTIONS[@]}"; do
        rollback_lambda_function "$func" "$method"
    done
    
    deploy_lambda_changes
    validate_system
}

# Rollback critical functions only
rollback_critical_functions() {
    local method="$1"
    
    CRITICAL_FUNCTIONS=(
        "orchestration-stepfunctions"
        "api-handler"
    )
    
    print_status "Rolling back critical Lambda functions using method: $method" "info"
    
    for func in "${CRITICAL_FUNCTIONS[@]}"; do
        rollback_lambda_function "$func" "$method"
    done
    
    deploy_lambda_changes
    validate_system
}

# Rollback background services only
rollback_background_services() {
    local method="$1"
    
    BACKGROUND_FUNCTIONS=(
        "execution-finder"
        "execution-poller"
        "frontend-builder"
        "notification-formatter"
    )
    
    print_status "Rolling back background service Lambda functions using method: $method" "info"
    
    for func in "${BACKGROUND_FUNCTIONS[@]}"; do
        rollback_lambda_function "$func" "$method"
    done
    
    deploy_lambda_changes
    validate_system
}

# Custom selection rollback
rollback_custom_selection() {
    echo -e "${YELLOW}Enter function names separated by spaces:${NC}"
    echo "Available: api-handler orchestration-stepfunctions execution-finder execution-poller frontend-builder notification-formatter"
    echo ""
    
    read -p "Functions: " -a selected_functions
    
    if [ ${#selected_functions[@]} -eq 0 ]; then
        print_status "No functions selected" "error"
        return 1
    fi
    
    echo -e "${YELLOW}Rollback methods:${NC}"
    echo "1. git-head (HEAD~1)"
    echo "2. git-tag ($BACKUP_TAG)"
    echo "3. backup-file"
    echo ""
    
    read -p "Select method (1-3): " method_choice
    
    case $method_choice in
        1) method="git-head" ;;
        2) method="git-tag" ;;
        3) method="backup-file" ;;
        *) 
            print_status "Invalid method selection" "error"
            return 1
            ;;
    esac
    
    for func in "${selected_functions[@]}"; do
        rollback_lambda_function "$func" "$method"
    done
    
    deploy_lambda_changes
    validate_system
}

# Main menu
main_menu() {
    while true; do
        show_rollback_options
        read -p "Select option (1-8): " choice
        
        case $choice in
            1)
                rollback_single_function
                ;;
            2)
                rollback_all_functions "git-head"
                ;;
            3)
                rollback_all_functions "git-tag"
                ;;
            4)
                rollback_all_functions "backup-file"
                ;;
            5)
                echo -e "${YELLOW}Rollback method for critical functions:${NC}"
                echo "1. git-head (HEAD~1)"
                echo "2. git-tag ($BACKUP_TAG)"
                echo "3. backup-file"
                read -p "Select method (1-3): " method_choice
                case $method_choice in
                    1) rollback_critical_functions "git-head" ;;
                    2) rollback_critical_functions "git-tag" ;;
                    3) rollback_critical_functions "backup-file" ;;
                    *) print_status "Invalid method selection" "error" ;;
                esac
                ;;
            6)
                echo -e "${YELLOW}Rollback method for background services:${NC}"
                echo "1. git-head (HEAD~1)"
                echo "2. git-tag ($BACKUP_TAG)"
                echo "3. backup-file"
                read -p "Select method (1-3): " method_choice
                case $method_choice in
                    1) rollback_background_services "git-head" ;;
                    2) rollback_background_services "git-tag" ;;
                    3) rollback_background_services "backup-file" ;;
                    *) print_status "Invalid method selection" "error" ;;
                esac
                ;;
            7)
                rollback_custom_selection
                ;;
            8)
                print_status "Exiting rollback script" "info"
                exit 0
                ;;
            *)
                print_status "Invalid option. Please select 1-8." "error"
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue or Ctrl+C to exit..."
        echo ""
    done
}

# Check prerequisites
check_prerequisites() {
    # Check if we're in the right directory
    if [ ! -f "lambda-compliance-analysis.md" ] || [ ! -d "lambda" ]; then
        print_status "This script must be run from the project root directory" "error"
        exit 1
    fi
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        print_status "Git is required but not installed" "error"
        exit 1
    fi
    
    # Check if backup tag exists
    if ! git tag -l | grep -q "$BACKUP_TAG"; then
        print_status "Backup tag $BACKUP_TAG not found. Creating it now..." "warning"
        git tag -a "$BACKUP_TAG" -m "Emergency backup tag created by rollback script"
    fi
    
    print_status "Prerequisites check passed" "success"
}

# Emergency mode (non-interactive)
emergency_mode() {
    print_status "EMERGENCY MODE: Rolling back all critical functions immediately" "error"
    
    # Rollback critical functions using git tag (most reliable)
    rollback_critical_functions "git-tag"
    
    print_status "Emergency rollback completed" "success"
    
    # Show next steps
    echo -e "\n${YELLOW}Next steps:${NC}"
    echo "1. Check system health: ./scripts/validate-system-health.sh"
    echo "2. Monitor CloudWatch logs for any remaining issues"
    echo "3. Investigate root cause of the security implementation failure"
    echo "4. Plan corrective actions before re-attempting security fixes"
}

# Parse command line arguments
if [ "$1" = "--emergency" ]; then
    check_prerequisites
    emergency_mode
    exit 0
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "AWS DRS Orchestration Emergency Rollback Script"
    echo ""
    echo "Usage:"
    echo "  $0                 # Interactive mode"
    echo "  $0 --emergency     # Emergency mode (rollback critical functions immediately)"
    echo "  $0 --help          # Show this help"
    echo ""
    echo "This script helps rollback Lambda security implementation changes"
    echo "when issues are detected in the system."
    exit 0
fi

# Main execution
print_status "Starting emergency rollback script in interactive mode" "info"
check_prerequisites
main_menu