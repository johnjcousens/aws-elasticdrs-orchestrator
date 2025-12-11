#!/bin/bash
# Export EC2 instances and their security group associations to CSV
# Creates a timestamped CSV file with all EC2 instances matching specified tags
# and their associated security groups for backup and migration purposes.
#
# DESCRIPTION:
# This script exports EC2 instances and their security group associations by:
# 1. Filtering instances by tag key=value pairs (supports both = and : formats)
# 2. Retrieving all security groups attached to each matching instance
# 3. Creating one CSV row per security group association
# 4. Including instance metadata (ID, Name, VPC) for complete context
# 5. Generating timestamped output files for version control
#
# USAGE:
#   ./export-ec2-security-groups.sh [TAG_FILTER]
#
# PARAMETERS:
#   TAG_FILTER: Tag filter in format "key=value" or "key:value" (default: crane:application=cww-footprint)
#
# EXAMPLES:
#   ./export-ec2-security-groups.sh
#   # Exports instances with default tag filter
#
#   ./export-ec2-security-groups.sh "Environment=Production"
#   # Exports all Production environment instances
#
#   ./export-ec2-security-groups.sh "crane:application=web-app"
#   # Exports instances with specific crane application tag
#
# OUTPUT:
#   CSV file: EC2SecurityGroups-YYYYMMDD-HHMMSS.csv
#   Format: InstanceId,InstanceName,SecurityGroupId,SecurityGroupName,VpcId
#
# PERMISSIONS REQUIRED:
# - ec2:DescribeInstances
# - ec2:DescribeSecurityGroups
#

set -uo pipefail  # Undefined vars, pipe failures (removed -e to prevent crashes)
export AWS_PAGER=""  # Disable AWS CLI pager for non-interactive use

# Configuration
LOG_FILE="ec2-sg-export-$(date +%Y%m%d-%H%M%S).log"
MAX_LOGS=5

# Parameters with defaults
TAG_FILTER="${1:-crane:application=cww-footprint}"

# Trap to handle clean exit and prevent CloudShell crash
trap 'exec >/dev/null 2>&1; exit 0' EXIT

#===============================================================================
# Logging Functions
#===============================================================================
setup_logging() {
    # Clean up old logs - keep only the most recent
    if ls ec2-sg-export-*.log >/dev/null 2>&1; then
        ls -t ec2-sg-export-*.log | tail -n +$((MAX_LOGS + 1)) | xargs -r rm -f
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

# Graceful exit function
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
    
    # Check AWS CLI
    if ! command -v aws >/dev/null 2>&1; then
        log_error "AWS CLI not found. Please install AWS CLI."
        graceful_exit 1 "Prerequisites validation failed"
    fi
    
    # Check jq for JSON parsing
    if ! command -v jq >/dev/null 2>&1; then
        log_error "jq not found. Please install jq for JSON parsing."
        graceful_exit 1 "Prerequisites validation failed"
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured or invalid."
        graceful_exit 1 "Prerequisites validation failed"
    fi
    
    log_success "Prerequisites validated"
}

validate_parameters() {
    log "Validating parameters..."
    
    # Parse tag filter into key and value
    if [[ "$TAG_FILTER" == *"="* ]]; then
        TAG_KEY=$(echo "$TAG_FILTER" | cut -d= -f1)
        TAG_VALUE=$(echo "$TAG_FILTER" | cut -d= -f2-)
    else
        TAG_KEY=$(echo "$TAG_FILTER" | cut -d: -f1)
        TAG_VALUE=$(echo "$TAG_FILTER" | cut -d: -f2-)
    fi
    
    # Validate tag components
    if [[ -z "$TAG_KEY" ]] || [[ -z "$TAG_VALUE" ]]; then
        log_error "Invalid tag filter format: $TAG_FILTER"
        graceful_exit 1 "Parameter validation failed"
    fi
    
    log "Tag: ${TAG_KEY}=${TAG_VALUE}"
    log_success "Parameters validated"
}

#===============================================================================
# Export Functions
#===============================================================================
initialize_export() {
    # Generate output filename with timestamp
    OUTPUT_FILE="EC2SecurityGroups-$(date +%Y%m%d-%H%M%S).csv"
    
    log "Initializing export to: $OUTPUT_FILE"
    
    # Create CSV header
    if ! echo "InstanceId,InstanceName,SecurityGroupId,SecurityGroupName,VpcId" > "$OUTPUT_FILE"; then
        log_error "Failed to create output file: $OUTPUT_FILE"
        graceful_exit 1 "Export initialization failed"
    fi
    
    log_success "Export file initialized"
}

find_instances() {
    log "Searching for instances..."
    
    # Get instances with the specified tag
    INSTANCE_IDS=$(aws ec2 describe-instances \
        --filters "Name=tag:${TAG_KEY},Values=${TAG_VALUE}" "Name=instance-state-name,Values=running,stopped,stopping,pending" \
        --query 'Reservations[].Instances[].InstanceId' \
        --output text 2>/dev/null) || {
        log_error "Failed to query EC2 instances"
        graceful_exit 1 "Instance discovery failed"
    }
    
    if [[ -z "$INSTANCE_IDS" ]] || [[ "$INSTANCE_IDS" == "None" ]]; then
        log_error "No instances found"
        rm -f "$OUTPUT_FILE"
        graceful_exit 1 "No matching instances found"
    fi
    
    TOTAL_INSTANCES=$(echo "$INSTANCE_IDS" | wc -w)
    log_success "Found $TOTAL_INSTANCES instances"
}

process_instances() {
    log "Processing $TOTAL_INSTANCES instances..."
    local current_instance=0
    local total_associations=0
    local errors=0
    
    # Process each instance individually to properly handle multiple security groups
    for instance_id in $INSTANCE_IDS; do
        ((current_instance++))
        log "[$current_instance/$TOTAL_INSTANCES] Processing instance: $instance_id"
        
        # Get instance details including all security groups
        local instance_data
        instance_data=$(aws ec2 describe-instances \
            --instance-ids "$instance_id" \
            --query 'Reservations[0].Instances[0].[InstanceId,Tags[?Key==`Name`].Value|[0],VpcId,SecurityGroups[]]' \
            --output json 2>/dev/null) || {
            log_error "Failed to get details for instance: $instance_id"
            ((errors++))
            continue
        }
        
        # Parse JSON data with error handling
        local parsed_instance_id parsed_instance_name parsed_vpc_id
        parsed_instance_id=$(echo "$instance_data" | jq -r '.[0]' 2>/dev/null) || {
            log_error "Failed to parse instance ID for: $instance_id"
            ((errors++))
            continue
        }
        
        parsed_instance_name=$(echo "$instance_data" | jq -r '.[1] // "(no name)"' 2>/dev/null) || {
            log_error "Failed to parse instance name for: $instance_id"
            parsed_instance_name="(parse error)"
        }
        
        parsed_vpc_id=$(echo "$instance_data" | jq -r '.[2]' 2>/dev/null) || {
            log_error "Failed to parse VPC ID for: $instance_id"
            parsed_vpc_id="(unknown)"
        }
        
        # Escape commas in instance name for CSV
        local instance_name_escaped
        instance_name_escaped=$(echo "$parsed_instance_name" | sed 's/,/;/g')
        
        # Count security groups for this instance
        local sg_count
        sg_count=$(echo "$instance_data" | jq -r '.[3] | length' 2>/dev/null) || sg_count=0
        
        if [[ "$sg_count" -eq 0 ]]; then
            log_error "  No security groups found for: $instance_id"
            ((errors++))
            continue
        fi
        
        # Process each security group for this instance using temporary file
        local sg_processed=0
        local temp_sg_file="/tmp/sg_temp_$$_$current_instance"
        
        # Extract security groups to temp file
        echo "$instance_data" | jq -r '.[3][] | [.GroupId, .GroupName] | @tsv' 2>/dev/null > "$temp_sg_file"
        
        # Process each security group
        while IFS=$'\t' read -r sg_id sg_name; do
            if [[ -z "$sg_id" ]]; then
                continue
            fi
            
            # Escape commas in SG name for CSV
            local sg_name_escaped
            sg_name_escaped=$(echo "$sg_name" | sed 's/,/;/g')
            
            # Write to CSV
            if echo "$parsed_instance_id,$instance_name_escaped,$sg_id,$sg_name_escaped,$parsed_vpc_id" >> "$OUTPUT_FILE"; then
                ((sg_processed++))
                ((total_associations++))
            else
                log_error "    Failed to write security group: $sg_id"
                ((errors++))
            fi
        done < "$temp_sg_file"
        
        # Clean up temp file
        rm -f "$temp_sg_file"
        
        log "  Exported $sg_processed security groups"
    done
    
    # Export summary
    log "Export processing completed:"
    log "  Instances processed: $current_instance"
    log "  Security group associations: $total_associations"
    log "  Errors encountered: $errors"
    
    if [[ $errors -gt 0 ]]; then
        log_error "Export completed with $errors errors"
        return 1
    fi
    
    log_success "All instances processed successfully"
    return 0
}

#===============================================================================
# Main Execution
#===============================================================================
main() {
    log "Starting EC2 Security Groups export script"
    log "Log file: $LOG_FILE"
    
    validate_prerequisites
    validate_parameters
    initialize_export
    find_instances
    
    if process_instances; then
        # Count associations without using tail (might be causing hang)
        local final_associations=0
        if [[ -f "$OUTPUT_FILE" ]]; then
            final_associations=$(grep -c '^i-' "$OUTPUT_FILE" 2>/dev/null || echo "0")
        fi
        
        # Log final results to file only
        {
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: Export completed successfully!"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: Instances processed: $TOTAL_INSTANCES"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: Security group associations exported: $final_associations"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: Data saved to: $OUTPUT_FILE"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Export completed successfully"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Log file saved: $LOG_FILE"
        } >> "$LOG_FILE"
        
        # Clean exit
        exit 0
    else
        graceful_exit 1 "Export completed with errors"
    fi
}

# Initialize logging and run main function
setup_logging

# Run main function and detach from shell to prevent CloudShell crash
(
    main "$@"
) &
MAIN_PID=$!
echo "Export running with PID: $MAIN_PID"
echo "Monitor with: tail -f $LOG_FILE"
echo "Check completion: ps -p $MAIN_PID || echo 'Complete'"
disown $MAIN_PID