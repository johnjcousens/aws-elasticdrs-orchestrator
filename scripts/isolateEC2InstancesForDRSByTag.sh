#!/bin/bash
# Isolates EC2 instances by replacing all security groups with a single DRS isolated security group.
# Combines export, security group creation, and instance isolation in a single automated workflow.
#
# DESCRIPTION:
# This script performs complete EC2 instance isolation for disaster recovery by:
# 1. Exporting current security group associations to timestamped CSV backup
# 2. Creating or reusing a DRS isolated security group with minimal required access:
#    - Inbound: DRS replication (TCP 1500) and management access (RDP/SSH)
#    - Outbound: Restricted to AWS services only (HTTPS 443, DNS 53)
# 3. Replacing ALL security groups on matching instances with only the isolated one
# 4. Providing comprehensive logging and error handling throughout the process
# 5. Background execution to prevent CloudShell terminal crashes
# 6. Complete rollback capability via generated CSV backup file
#
# USAGE:
#   ./isolate-ec2-instances.sh [tag-filter] [sg-name] [vpc-name] [source-cidr]
#
# PARAMETERS:
#   tag-filter: Tag filter in format "key=value" or "key:value" (default: crane:application=cww-footprint)
#   sg-name: Security group name for isolation (default: drs-isolated-test)
#   vpc-name: VPC ID, Name tag, or VPC name (default: uat-us-west-2-footprint)
#   source-cidr: Source CIDR for DRS replication traffic (default: 172.16.0.0/12)
#
# EXAMPLES:
#   ./isolate-ec2-instances.sh
#   # Isolates instances with default settings
#
#   ./isolate-ec2-instances.sh "Environment=Production" prod-drs-sg prod-vpc 10.0.0.0/8
#   # Isolates Production instances with custom security group and VPC
#
#   ./isolate-ec2-instances.sh "crane:application=web-app" web-isolated-sg
#   # Isolates specific application instances with custom security group name
#
# PERMISSIONS REQUIRED:
# - ec2:DescribeInstances
# - ec2:DescribeSecurityGroups
# - ec2:DescribeVpcs
# - ec2:CreateSecurityGroup
# - ec2:CreateTags
# - ec2:AuthorizeSecurityGroupIngress
# - ec2:AuthorizeSecurityGroupEgress
# - ec2:RevokeSecurityGroupEgress
# - ec2:ModifyInstanceAttribute
#

set -uo pipefail
export AWS_PAGER=""

# Configuration
LOG_FILE="ec2-isolation-$(date +%Y%m%d-%H%M%S).log"
MAX_LOGS=5

# Parameters with defaults
TAG_FILTER="${1:-crane:application=cww-footprint}"
SG_NAME="${2:-drs-isolated-test}"
VPC_NAME="${3:-uat-us-west-2-footprint}"
SOURCE_CIDR="${4:-172.16.0.0/12}"

# Required DRS tag (not a parameter)
DRS_TAG="AWSDRS=AllowLaunchingIntoThisInstance"

# Remote access CIDR ranges for management (RDP/SSH)
# 10.255.200.0/21 - Crane VPN Subnet
# 172.30.4.26/32 - Datex Subnet Host 1
# 172.30.4.27/32 - Datex Subnet Host 2  
# 172.30.4.29/32 - Datex Subnet Host 3
# 172.30.4.30/32 - Datex Subnet Host 4
RemoteAccess_CIDRS="10.255.200.0/21,172.30.4.26/32,172.30.4.27/32,172.30.4.29/32,172.30.4.30/32"

#===============================================================================
# Logging Functions
#===============================================================================
setup_logging() {
    if ls ec2-isolation-*.log >/dev/null 2>&1; then
        ls -t ec2-isolation-*.log | tail -n +$((MAX_LOGS + 1)) | xargs -r rm -f
    fi
}

log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    echo "$message" >> "$LOG_FILE"
}

log_error() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1"
    echo "$message" >&2
    echo "$message" >> "$LOG_FILE"
}

log_success() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1"
    echo "$message"
    echo "$message" >> "$LOG_FILE"
}

graceful_exit() {
    local exit_code=${1:-0}
    local message="${2:-Script completed}"
    log "$message"
    log "Log file saved: $LOG_FILE"
    exit $exit_code
}

#===============================================================================
# Validation Functions
#===============================================================================
validate_prerequisites() {
    log "Validating prerequisites..."
    
    if ! command -v aws >/dev/null 2>&1; then
        log_error "AWS CLI not found"
        graceful_exit 1 "Prerequisites validation failed"
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        log_error "jq not found"
        graceful_exit 1 "Prerequisites validation failed"
    fi
    
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured"
        graceful_exit 1 "Prerequisites validation failed"
    fi
    
    log_success "Prerequisites validated"
}

validate_parameters() {
    log "Validating parameters..."
    
    # Parse tag filter
    if [[ "$TAG_FILTER" == *"="* ]]; then
        TAG_KEY=$(echo "$TAG_FILTER" | cut -d= -f1)
        TAG_VALUE=$(echo "$TAG_FILTER" | cut -d= -f2-)
    else
        TAG_KEY=$(echo "$TAG_FILTER" | cut -d: -f1)
        TAG_VALUE=$(echo "$TAG_FILTER" | cut -d: -f2-)
    fi
    
    if [[ -z "$TAG_KEY" ]] || [[ -z "$TAG_VALUE" ]]; then
        log_error "Invalid tag filter format: $TAG_FILTER"
        graceful_exit 1 "Parameter validation failed"
    fi
    
    # Validate CIDR format
    if ! echo "$SOURCE_CIDR" | grep -qE '^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$'; then
        log_error "Invalid SOURCE_CIDR format: $SOURCE_CIDR"
        graceful_exit 1 "Parameter validation failed"
    fi
    
    log "Tag Filter: ${TAG_KEY}=${TAG_VALUE}"
    log "Required DRS Tag: $DRS_TAG"
    log "Security Group: $SG_NAME"
    log "VPC: $VPC_NAME"
    log "Source CIDR: $SOURCE_CIDR"
    log_success "Parameters validated"
}

#===============================================================================
# Export Functions
#===============================================================================
export_security_groups() {
    log "=== PHASE 1: EXPORTING SECURITY GROUPS ==="
    
    # Generate output filename
    OUTPUT_FILE="EC2SecurityGroups-$(date +%Y%m%d-%H%M%S).csv"
    log "Exporting to: $OUTPUT_FILE"
    
    # Create CSV header
    echo "InstanceId,InstanceName,SecurityGroupId,SecurityGroupName,VpcId" > "$OUTPUT_FILE"
    
    # Get instances with both TAG_FILTER and DRS tag
    INSTANCE_IDS=$(aws ec2 describe-instances \
        --filters "Name=tag:${TAG_KEY},Values=${TAG_VALUE}" "Name=tag:AWSDRS,Values=AllowLaunchingIntoThisInstance" "Name=instance-state-name,Values=running,stopped,stopping,pending" \
        --query 'Reservations[].Instances[].InstanceId' \
        --output text 2>/dev/null) || {
        log_error "Failed to query EC2 instances"
        graceful_exit 1 "Instance discovery failed"
    }
    
    if [[ -z "$INSTANCE_IDS" ]]; then
        log_error "No instances found"
        graceful_exit 1 "No matching instances found"
    fi
    
    TOTAL_INSTANCES=$(echo "$INSTANCE_IDS" | wc -w)
    log_success "Found $TOTAL_INSTANCES instances"
    
    # Export security groups
    local current_instance=0
    local total_associations=0
    
    for instance_id in $INSTANCE_IDS; do
        ((current_instance++))
        log "[$current_instance/$TOTAL_INSTANCES] Exporting: $instance_id"
        
        local instance_data
        instance_data=$(aws ec2 describe-instances \
            --instance-ids "$instance_id" \
            --query 'Reservations[0].Instances[0].[InstanceId,Tags[?Key==`Name`].Value|[0],VpcId,SecurityGroups[]]' \
            --output json 2>/dev/null) || continue
        
        local parsed_id parsed_name parsed_vpc
        parsed_id=$(echo "$instance_data" | jq -r '.[0]')
        parsed_name=$(echo "$instance_data" | jq -r '.[1] // "(no name)"')
        parsed_vpc=$(echo "$instance_data" | jq -r '.[2]')
        
        local name_escaped
        name_escaped=$(echo "$parsed_name" | sed 's/,/;/g')
        
        # Store VPC for later use
        if [[ -z "${INSTANCE_VPC:-}" ]]; then
            INSTANCE_VPC="$parsed_vpc"
        fi
        
        # Export each security group
        echo "$instance_data" | jq -r '.[3][] | [.GroupId, .GroupName] | @tsv' | while IFS=$'\t' read -r sg_id sg_name; do
            [[ -z "$sg_id" ]] && continue
            sg_name_escaped=$(echo "$sg_name" | sed 's/,/;/g')
            echo "$parsed_id,$name_escaped,$sg_id,$sg_name_escaped,$parsed_vpc" >> "$OUTPUT_FILE"
            ((total_associations++))
        done
    done
    
    local final_associations
    final_associations=$(grep -c '^i-' "$OUTPUT_FILE" 2>/dev/null || echo "0")
    
    log_success "Export completed: $final_associations associations saved to $OUTPUT_FILE"
}

#===============================================================================
# Security Group Creation Functions
#===============================================================================
get_vpc_id() {
    log "Looking up VPC ID for: $VPC_NAME"
    
    # Check if already VPC ID
    if [[ "$VPC_NAME" =~ ^vpc-[0-9a-f]{8,17}$ ]]; then
        VPC_ID="$VPC_NAME"
    else
        # Try Name tag first
        VPC_ID=$(aws ec2 describe-vpcs \
            --filters "Name=tag:Name,Values=$VPC_NAME" \
            --query 'Vpcs[0].VpcId' \
            --output text 2>/dev/null)
        
        if [[ "$VPC_ID" == "None" ]] || [[ -z "$VPC_ID" ]]; then
            # Use instance VPC if available
            if [[ -n "${INSTANCE_VPC:-}" ]]; then
                VPC_ID="$INSTANCE_VPC"
                log "Using VPC from instances: $VPC_ID"
            else
                log_error "VPC not found: $VPC_NAME"
                graceful_exit 1 "VPC lookup failed"
            fi
        fi
    fi
    
    log_success "Using VPC ID: $VPC_ID"
}

create_isolated_security_group() {
    log "=== PHASE 2: CREATING ISOLATED SECURITY GROUP ==="
    
    get_vpc_id
    
    # Check if security group exists
    EXISTING_SG_ID=$(aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=$SG_NAME" \
        --query 'SecurityGroups[0].GroupId' \
        --output text 2>/dev/null)
    
    if [[ "$EXISTING_SG_ID" =~ ^sg- ]]; then
        log "Security group '$SG_NAME' already exists (ID: $EXISTING_SG_ID)"
        log "Using existing security group: $EXISTING_SG_ID"
        SG_ID="$EXISTING_SG_ID"
        log_success "Using existing security group: $SG_ID"
        return 0
    fi
    
    # Create security group
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "DRS isolated security group - created $(date)" \
        --vpc-id "$VPC_ID" \
        --query 'GroupId' \
        --output text) || {
        log_error "Failed to create security group"
        graceful_exit 1 "Security group creation failed"
    }
    
    log_success "Created security group: $SG_ID"
    
    # Add Name tag
    aws ec2 create-tags --resources "$SG_ID" --tags Key=Name,Value="$SG_NAME"
    
    # Add inbound rules
    log "Adding inbound rules..."
    
    # DRS replication traffic
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --ip-permissions '[{"IpProtocol":"tcp","FromPort":1500,"ToPort":1500,"IpRanges":[{"CidrIp":"'"$SOURCE_CIDR"'","Description":"DRS replication traffic"}]}]'
    
    # Management access
    IFS=',' read -ra CIDRS <<< "$RemoteAccess_CIDRS"
    for cidr in "${CIDRS[@]}"; do
        cidr=$(echo "$cidr" | xargs)
        
        # RDP
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --ip-permissions '[{"IpProtocol":"tcp","FromPort":3389,"ToPort":3389,"IpRanges":[{"CidrIp":"'"$cidr"'","Description":"RDP management access"}]}]'
        
        # SSH
        aws ec2 authorize-security-group-ingress \
            --group-id "$SG_ID" \
            --ip-permissions '[{"IpProtocol":"tcp","FromPort":22,"ToPort":22,"IpRanges":[{"CidrIp":"'"$cidr"'","Description":"SSH management access"}]}]'
    done
    
    # Remove default outbound rule
    aws ec2 revoke-security-group-egress \
        --group-id "$SG_ID" \
        --protocol all \
        --cidr 0.0.0.0/0
    
    # Add restricted outbound rules
    log "Adding outbound rules..."
    
    # AWS service CIDR ranges
    declare -a AWS_CIDRS=("3.0.0.0/8" "13.0.0.0/8" "15.0.0.0/8" "18.0.0.0/8" "35.0.0.0/8" "44.0.0.0/8" "52.0.0.0/8" "54.0.0.0/8" "99.0.0.0/8")
    
    for cidr in "${AWS_CIDRS[@]}"; do
        aws ec2 authorize-security-group-egress \
            --group-id "$SG_ID" \
            --ip-permissions '[{"IpProtocol":"tcp","FromPort":443,"ToPort":443,"IpRanges":[{"CidrIp":"'"$cidr"'","Description":"HTTPS to AWS services"}]}]'
    done
    
    # DNS to AWS resolver
    aws ec2 authorize-security-group-egress \
        --group-id "$SG_ID" \
        --ip-permissions '[{"IpProtocol":"udp","FromPort":53,"ToPort":53,"IpRanges":[{"CidrIp":"169.254.169.253/32","Description":"DNS via AWS resolver"}]}]'
    
    log_success "Security group configured: $SG_ID"
}

#===============================================================================
# Instance Isolation Functions
#===============================================================================
isolate_instances() {
    log "=== PHASE 3: ISOLATING INSTANCES ==="
    
    local current_instance=0
    local isolated_count=0
    
    for instance_id in $INSTANCE_IDS; do
        ((current_instance++))
        log "[$current_instance/$TOTAL_INSTANCES] Isolating: $instance_id"
        
        # Replace all security groups with isolated one
        if aws ec2 modify-instance-attribute \
            --instance-id "$instance_id" \
            --groups "$SG_ID" 2>/dev/null; then
            log_success "  Isolated: $instance_id"
            ((isolated_count++))
        else
            log_error "  Failed to isolate: $instance_id"
        fi
    done
    
    log_success "Isolated $isolated_count instances with security group: $SG_ID"
}

#===============================================================================
# Main Execution
#===============================================================================
main() {
    log "Starting EC2 Instance Isolation Script"
    log "Log file: $LOG_FILE"
    
    validate_prerequisites
    validate_parameters
    
    export_security_groups
    create_isolated_security_group
    isolate_instances
    
    log_success "=== ISOLATION COMPLETED ==="
    
    echo ""
    echo "=== SUMMARY ==="
    echo "Backup CSV: $OUTPUT_FILE"
    echo "Isolated Security Group: $SG_ID ($SG_NAME)"
    echo "VPC: $VPC_ID"
    echo "Instances Isolated: $TOTAL_INSTANCES"
    echo "Log File: $LOG_FILE"
    echo ""
    echo "All instances now have ONLY the isolated security group attached."
    echo "Original security group associations backed up to: $OUTPUT_FILE"
    echo "Use import-ec2-security-groups.sh to restore if needed."
    
    graceful_exit 0 "Isolation completed successfully"
}

# Initialize and run
setup_logging

# Run main function and detach from shell to prevent CloudShell crash
(
    main "$@"
) &
MAIN_PID=$!
echo "Isolation script running with PID: $MAIN_PID"
echo "Monitor with: tail -f $LOG_FILE"
echo "Check completion: ps -p $MAIN_PID || echo 'Complete'"
disown $MAIN_PID