#!/bin/bash

set -e
set -o pipefail

# =============================================================================
# Script: Complete AD Connector + WorkSpaces Deployment
# Description: Intelligent wrapper that checks for existing resources and only
#              executes necessary steps in the workflow
# =============================================================================

# Script version
VERSION="1.0.0"

# =============================================================================
# Default Configuration Values
# =============================================================================
# These defaults will be used if not overridden by:
#   1. --config file
#   2. Command-line arguments
# 
# To customize: Simply edit the values below for your environment
# =============================================================================

# AWS Configuration Defaults
: ${AWS_REGION:="us-west-2"}
: ${DC_INSTANCE:="i-05cc1a64d8e6abc1f"}
: ${SECRET_ARN:="arn:aws:secretsmanager:us-west-2:128121109383:secret:adconnector-8oK6zt"}

# Network Configuration Defaults
: ${VPC_ID:="vpc-0b3620f4e09f327db"}
: ${AD_SUBNET_1:="subnet-06dfabcf89e752fb0"}
: ${AD_SUBNET_2:="subnet-07142005231d6d167"}
: ${WS_SUBNET_1:="subnet-06dfabcf89e752fb0"}
: ${WS_SUBNET_2:="subnet-07142005231d6d167"}

# Active Directory Configuration Defaults
: ${DC1_IP:="10.100.216.10"}
: ${DC2_IP:="10.100.224.10"}
: ${DOMAIN_NAME:="test.aws.int"}
: ${NETBIOS_NAME:="TEST"}

# Optional Configuration Defaults (can be overridden)
: ${SIZE:="Small"}
: ${ENABLE_SELF_SERVICE:="true"}

# =============================================================================
# End of Default Configuration
# =============================================================================

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SIZE="Small"
ENABLE_SELF_SERVICE="true"
DRY_RUN=false
FORCE_ALL=false
FORCE_STEP_1=false
FORCE_STEP_2=false
FORCE_STEP_3=false
VERBOSE=false

# =============================================================================
# Usage Function
# =============================================================================

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Intelligent AD Connector + WorkSpaces deployment wrapper.
Checks for existing resources and only executes necessary steps.

Required Parameters:
  --dc-instance <ID>           Domain Controller instance ID
  --region <REGION>            AWS region (e.g., us-west-2)
  --secret-arn <ARN>           Secrets Manager ARN with AD credentials
  --vpc-id <VPC_ID>            VPC for AD Connector
  --ad-subnet-1 <SUBNET_ID>    First AD Connector subnet
  --ad-subnet-2 <SUBNET_ID>    Second AD Connector subnet
  --ws-subnet-1 <SUBNET_ID>    First WorkSpaces subnet
  --ws-subnet-2 <SUBNET_ID>    Second WorkSpaces subnet
  --dc1-ip <IP>                First Domain Controller IP
  --dc2-ip <IP>                Second Domain Controller IP
  --domain <FQDN>              AD domain name (e.g., example.com)
  --netbios <NAME>             NetBIOS name (e.g., EXAMPLE)

Optional Parameters:
  --size <Small|Large>         AD Connector size (default: Small)
  --enable-self-service <bool> Enable WorkSpaces self-service (default: true)
  --config <FILE>              Load parameters from config file

Control Options:
  --dry-run                    Show what would be done without executing
  --force-all                  Force all steps even if resources exist
  --force-step-1               Force AD account creation
  --force-step-2               Force AD Connector creation
  --force-step-3               Force WorkSpaces registration
  --verbose                    Show detailed output
  --version                    Show version and exit
  --help                       Show this help message

Configuration File Format:
  DC_INSTANCE=i-xxxxx
  AWS_REGION=us-west-2
  SECRET_ARN=arn:aws:...
  (etc.)

Examples:
  # Full deployment with parameters
  $0 --dc-instance i-xxx --region us-west-2 --secret-arn arn:aws:... \\
     --vpc-id vpc-xxx --ad-subnet-1 subnet-xxx --ad-subnet-2 subnet-yyy \\
     --ws-subnet-1 subnet-xxx --ws-subnet-2 subnet-yyy \\
     --dc1-ip 10.0.0.10 --dc2-ip 10.0.0.11 \\
     --domain example.com --netbios EXAMPLE

  # Using configuration file
  $0 --config my-deployment.env

  # Dry run to see what would happen
  $0 --config my-deployment.env --dry-run

  # Force all steps (ignore existing resources)
  $0 --config my-deployment.env --force-all

EOF
    exit 1
}

# =============================================================================
# Logging Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_step() {
    echo -e "${CYAN}▶${NC} $1"
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${NC}  $1${NC}"
    fi
}

# =============================================================================
# Parameter Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --dc-instance)
            DC_INSTANCE="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --secret-arn)
            SECRET_ARN="$2"
            shift 2
            ;;
        --vpc-id)
            VPC_ID="$2"
            shift 2
            ;;
        --ad-subnet-1)
            AD_SUBNET_1="$2"
            shift 2
            ;;
        --ad-subnet-2)
            AD_SUBNET_2="$2"
            shift 2
            ;;
        --ws-subnet-1)
            WS_SUBNET_1="$2"
            shift 2
            ;;
        --ws-subnet-2)
            WS_SUBNET_2="$2"
            shift 2
            ;;
        --dc1-ip)
            DC1_IP="$2"
            shift 2
            ;;
        --dc2-ip)
            DC2_IP="$2"
            shift 2
            ;;
        --domain)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        --netbios)
            NETBIOS_NAME="$2"
            shift 2
            ;;
        --size)
            SIZE="$2"
            shift 2
            ;;
        --enable-self-service)
            ENABLE_SELF_SERVICE="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force-all)
            FORCE_ALL=true
            FORCE_STEP_1=true
            FORCE_STEP_2=true
            FORCE_STEP_3=true
            shift
            ;;
        --force-step-1)
            FORCE_STEP_1=true
            shift
            ;;
        --force-step-2)
            FORCE_STEP_2=true
            shift
            ;;
        --force-step-3)
            FORCE_STEP_3=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --version)
            echo "deploy-ad-connector-complete.sh version $VERSION"
            exit 0
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Load config file if specified
if [[ -n "$CONFIG_FILE" ]]; then
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi
    log_info "Loading configuration from: $CONFIG_FILE"
    source "$CONFIG_FILE"
fi

# =============================================================================
# Validate Prerequisites
# =============================================================================

validate_prerequisites() {
    log_step "Validating prerequisites..."
    
    # Check required parameters
    local missing_params=()
    
    [[ -z "$DC_INSTANCE" ]] && missing_params+=("--dc-instance")
    [[ -z "$AWS_REGION" ]] && missing_params+=("--region")
    [[ -z "$SECRET_ARN" ]] && missing_params+=("--secret-arn")
    [[ -z "$VPC_ID" ]] && missing_params+=("--vpc-id")
    [[ -z "$AD_SUBNET_1" ]] && missing_params+=("--ad-subnet-1")
    [[ -z "$AD_SUBNET_2" ]] && missing_params+=("--ad-subnet-2")
    [[ -z "$WS_SUBNET_1" ]] && missing_params+=("--ws-subnet-1")
    [[ -z "$WS_SUBNET_2" ]] && missing_params+=("--ws-subnet-2")
    [[ -z "$DC1_IP" ]] && missing_params+=("--dc1-ip")
    [[ -z "$DC2_IP" ]] && missing_params+=("--dc2-ip")
    [[ -z "$DOMAIN_NAME" ]] && missing_params+=("--domain")
    [[ -z "$NETBIOS_NAME" ]] && missing_params+=("--netbios")
    
    if [[ ${#missing_params[@]} -gt 0 ]]; then
        log_error "Missing required parameters: ${missing_params[*]}"
        echo ""
        usage
    fi
    
    # Check jq installed
    if ! command -v jq &>/dev/null; then
        log_error "jq is not installed. Install with: sudo yum install -y jq"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &>/dev/null; then
        log_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        log_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check required scripts exist
    local script_dir="$(dirname "$0")"
    local missing_scripts=()
    
    [[ ! -f "$script_dir/createADConnectorAcctAndGroupinAD.sh" ]] && missing_scripts+=("createADConnectorAcctAndGroupinAD.sh")
    [[ ! -f "$script_dir/createADConnectorInAWS.sh" ]] && missing_scripts+=("createADConnectorInAWS.sh")
    [[ ! -f "$script_dir/registerADConnectorWithWorkspaces.sh" ]] && missing_scripts+=("registerADConnectorWithWorkspaces.sh")
    
    if [[ ${#missing_scripts[@]} -gt 0 ]]; then
        log_error "Missing required scripts: ${missing_scripts[*]}"
        exit 1
    fi
    
    log_success "Prerequisites validated"
}

# =============================================================================
# Check Functions
# =============================================================================

check_ad_account_exists() {
    log_step "Checking if AD account exists..."
    
    # Get username from Secrets Manager
    local username
    username=$(aws secretsmanager get-secret-value \
        --secret-id "$SECRET_ARN" \
        --region "$AWS_REGION" \
        --query 'SecretString' \
        --output text 2>/dev/null | jq -r '.username' 2>/dev/null)
    
    if [[ -z "$username" || "$username" == "null" ]]; then
        log_warning "Could not retrieve username from Secrets Manager"
        return 1
    fi
    
    log_verbose "Username from secret: $username"
    
    # PowerShell script to check AD account
    local ps_script="Import-Module ActiveDirectory; \$User = Get-ADUser -Filter {SamAccountName -eq '$username'} -ErrorAction SilentlyContinue; if (\$User) { Write-Output 'EXISTS' } else { Write-Output 'NOT_FOUND' }"
    
    # Send SSM command
    local command_output
    command_output=$(aws ssm send-command \
        --document-name "AWS-RunPowerShellScript" \
        --instance-ids "$DC_INSTANCE" \
        --parameters "commands=['$ps_script']" \
        --region "$AWS_REGION" \
        --output json 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        log_warning "Could not check AD account via SSM"
        return 1
    fi
    
    local command_id
    command_id=$(echo "$command_output" | jq -r '.Command.CommandId')
    
    # Wait for command completion
    sleep 5
    
    # Get command result
    local result
    result=$(aws ssm get-command-invocation \
        --command-id "$command_id" \
        --instance-id "$DC_INSTANCE" \
        --region "$AWS_REGION" \
        --query 'StandardOutputContent' \
        --output text 2>/dev/null)
    
    if echo "$result" | grep -q "EXISTS"; then
        log_success "AD account '$username' exists"
        return 0
    else
        log_info "AD account '$username' does not exist"
        return 1
    fi
}

check_ad_connector_exists() {
    log_step "Checking if AD Connector exists..."
    
    # Search for AD Connector by domain name and VPC
    local connectors
    connectors=$(aws ds describe-directories \
        --region "$AWS_REGION" \
        --query "DirectoryDescriptions[?Name=='$DOMAIN_NAME' && Type=='ADConnector' && VpcSettings.VpcId=='$VPC_ID'].[DirectoryId,State]" \
        --output json 2>/dev/null)
    
    if [[ -z "$connectors" || "$connectors" == "[]" ]]; then
        log_info "No AD Connector found for domain '$DOMAIN_NAME' in VPC '$VPC_ID'"
        return 1
    fi
    
    # Get first Active connector
    local dir_id
    local dir_state
    dir_id=$(echo "$connectors" | jq -r '.[0][0]')
    dir_state=$(echo "$connectors" | jq -r '.[0][1]')
    
    if [[ "$dir_state" == "Active" ]]; then
        EXISTING_DIRECTORY_ID="$dir_id"
        log_success "Active AD Connector found: $dir_id"
        return 0
    else
        log_warning "AD Connector found ($dir_id) but in state: $dir_state"
        return 1
    fi
}

check_workspaces_registration() {
    log_step "Checking WorkSpaces registration..."
    
    if [[ -z "$DIRECTORY_ID" ]]; then
        log_warning "No Directory ID available to check"
        return 1
    fi
    
    local ws_state
    ws_state=$(aws workspaces describe-workspace-directories \
        --directory-ids "$DIRECTORY_ID" \
        --region "$AWS_REGION" \
        --query "Directories[0].State" \
        --output text 2>/dev/null)
    
    if [[ "$ws_state" == "REGISTERED" ]]; then
        log_success "WorkSpaces already registered for directory $DIRECTORY_ID"
        return 0
    elif [[ "$ws_state" == "REGISTERING" ]]; then
        log_warning "WorkSpaces registration in progress for directory $DIRECTORY_ID"
        return 2
    else
        log_info "WorkSpaces not registered for directory $DIRECTORY_ID"
        return 1
    fi
}

# =============================================================================
# Main Workflow
# =============================================================================

main() {
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}AD Connector + WorkSpaces Deployment${NC}"
    echo -e "${BLUE}Version: $VERSION${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
        echo ""
    fi
    
    # Validate prerequisites
    validate_prerequisites
    echo ""
    
    # Display configuration
    log_info "Configuration:"
    echo "  Region: $AWS_REGION"
    echo "  Domain: $DOMAIN_NAME"
    echo "  VPC: $VPC_ID"
    echo "  DC Instance: $DC_INSTANCE"
    echo ""
    
    # =============================================================================
    # Step 1: AD Account
    # =============================================================================
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Step 1: AD Account Management${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    STEP_1_EXECUTED=false
    
    if [[ "$FORCE_STEP_1" == "true" ]]; then
        log_warning "Force flag set - will create AD account regardless"
        STEP_1_NEEDED=true
    else
        if check_ad_account_exists; then
            STEP_1_NEEDED=false
            log_info "Step 1 will be skipped"
        else
            STEP_1_NEEDED=true
            log_info "Step 1 will be executed"
        fi
    fi
    
    echo ""
    
    if [[ "$STEP_1_NEEDED" == "true" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would execute: ./createADConnectorAcctAndGroupinAD.sh"
        else
            log_step "Executing: createADConnectorAcctAndGroupinAD.sh"
            ./createADConnectorAcctAndGroupinAD.sh \
                "$DC_INSTANCE" \
                "$AWS_REGION" \
                "$SECRET_ARN" || {
                log_error "Step 1 failed"
                exit 1
            }
            STEP_1_EXECUTED=true
            log_success "Step 1 completed"
        fi
    else
        log_success "Step 1 skipped (AD account exists)"
    fi
    
    echo ""
    
    # =============================================================================
    # Step 2: AD Connector
    # =============================================================================
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Step 2: AD Connector Creation${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    STEP_2_EXECUTED=false
    
    if [[ "$FORCE_STEP_2" == "true" ]]; then
        log_warning "Force flag set - will create AD Connector regardless"
        STEP_2_NEEDED=true
    else
        if check_ad_connector_exists; then
            STEP_2_NEEDED=false
            DIRECTORY_ID="$EXISTING_DIRECTORY_ID"
            log_info "Step 2 will be skipped (using Directory ID: $DIRECTORY_ID)"
        else
            STEP_2_NEEDED=true
            log_info "Step 2 will be executed"
        fi
    fi
    
    echo ""
    
    if [[ "$STEP_2_NEEDED" == "true" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would execute: ./createADConnectorInAWS.sh"
        else
            log_step "Executing: createADConnectorInAWS.sh"
            
            # Create temporary file for output
            local temp_output="/tmp/ad_connector_output_$$.txt"
            
            ./createADConnectorInAWS.sh \
                "$AWS_REGION" \
                "$SECRET_ARN" \
                "$VPC_ID" \
                "$AD_SUBNET_1" \
                "$AD_SUBNET_2" \
                "$DC1_IP" \
                "$DC2_IP" \
                "$DOMAIN_NAME" \
                "$NETBIOS_NAME" \
                "$SIZE" | tee "$temp_output" || {
                log_error "Step 2 failed"
                rm -f "$temp_output"
                exit 1
            }
            
            # Extract Directory ID
            DIRECTORY_ID=$(grep "^DIRECTORY_ID=" "$temp_output" | cut -d= -f2)
            rm -f "$temp_output"
            
            if [[ -z "$DIRECTORY_ID" ]]; then
                log_error "Failed to get Directory ID from Step 2"
                exit 1
            fi
            
            STEP_2_EXECUTED=true
            log_success "Step 2 completed (Directory ID: $DIRECTORY_ID)"
        fi
    else
        log_success "Step 2 skipped (AD Connector exists)"
    fi
    
    echo ""
    
    # =============================================================================
    # Step 3: WorkSpaces Registration
    # =============================================================================
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Step 3: WorkSpaces Registration${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    STEP_3_EXECUTED=false
    
    if [[ -z "$DIRECTORY_ID" && "$DRY_RUN" == "false" ]]; then
        log_error "No Directory ID available for Step 3"
        exit 1
    fi
    
    if [[ "$FORCE_STEP_3" == "true" ]]; then
        log_warning "Force flag set - will register WorkSpaces regardless"
        STEP_3_NEEDED=true
    else
        check_workspaces_registration
        local ws_check_result=$?
        
        if [[ $ws_check_result -eq 0 ]]; then
            STEP_3_NEEDED=false
            log_info "Step 3 will be skipped"
        elif [[ $ws_check_result -eq 2 ]]; then
            STEP_3_NEEDED=true
            log_info "Step 3 will wait for existing registration to complete"
        else
            STEP_3_NEEDED=true
            log_info "Step 3 will be executed"
        fi
    fi
    
    echo ""
    
    if [[ "$STEP_3_NEEDED" == "true" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would execute: ./registerADConnectorWithWorkspaces.sh"
        else
            log_step "Executing: registerADConnectorWithWorkspaces.sh"
            ./registerADConnectorWithWorkspaces.sh \
                "$DIRECTORY_ID" \
                "$AWS_REGION" \
                "$WS_SUBNET_1" \
                "$WS_SUBNET_2" \
                "$ENABLE_SELF_SERVICE" || {
                log_error "Step 3 failed"
                exit 1
            }
            STEP_3_EXECUTED=true
            log_success "Step 3 completed"
        fi
    else
        log_success "Step 3 skipped (WorkSpaces already registered)"
    fi
    
    echo ""
    
    # =============================================================================
    # Summary
    # =============================================================================
    
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}Deployment Summary${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""
    
    echo "Execution Results:"
    if [[ "$STEP_1_EXECUTED" == "true" ]]; then
        echo -e "  ${GREEN}✓${NC} Step 1: AD account created"
    else
        echo -e "  ${YELLOW}○${NC} Step 1: Skipped (already exists)"
    fi
    
    if [[ "$STEP_2_EXECUTED" == "true" ]]; then
        echo -e "  ${GREEN}✓${NC} Step 2: AD Connector created"
    else
        echo -e "  ${YELLOW}○${NC} Step 2: Skipped (already exists)"
    fi
    
    if [[ "$STEP_3_EXECUTED" == "true" ]]; then
        echo -e "  ${GREEN}✓${NC} Step 3: WorkSpaces registered"
    else
        echo -e "  ${YELLOW}○${NC} Step 3: Skipped (already registered)"
    fi
    
    echo ""
    
    if [[ "$DRY_RUN" == "false" ]]; then
        echo "Configuration Details:"
        echo "  Region: $AWS_REGION"
        echo "  Domain: $DOMAIN_NAME"
        echo "  Directory ID: ${DIRECTORY_ID:-N/A}"
        echo ""
        
        if [[ "$STEP_1_EXECUTED" == "false" && "$STEP_2_EXECUTED" == "false" && "$STEP_3_EXECUTED" == "false" ]]; then
            log_success "All resources already configured - nothing to do!"
        else
            log_success "Deployment completed successfully!"
        fi
    else
        log_info "Dry run completed - no changes made"
    fi
    
    echo ""
}

# Run main workflow
main
