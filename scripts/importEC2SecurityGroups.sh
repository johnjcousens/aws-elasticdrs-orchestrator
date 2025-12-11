#!/bin/bash
# Import and restore EC2 security group associations from CSV
# Restores security group associations to EC2 instances from exported CSV data
# with exact match approach - replaces all security groups to match CSV exactly.
#
# DESCRIPTION:
# This script imports EC2 security group associations by:
# 1. Reading CSV file exported by export-ec2-security-groups.sh
# 2. Comparing current vs desired security groups for each instance
# 3. Replacing all security groups to match CSV exactly (removes extras, adds missing)
# 4. Validating all security groups exist before making changes
# 5. Supporting dry-run mode for safe testing
# 6. Providing detailed logging and error handling
#
# USAGE:
#   ./import-ec2-security-groups.sh <CSV_FILE> [--dry-run]
#
# PARAMETERS:
#   CSV_FILE: Path to CSV file created by export-ec2-security-groups.sh
#   --dry-run: Optional flag to preview changes without applying them
#
# EXAMPLES:
#   ./import-ec2-security-groups.sh EC2SecurityGroups-20241201-143022.csv
#   # Imports security group associations from CSV file
#
#   ./import-ec2-security-groups.sh EC2SecurityGroups-20241201-143022.csv --dry-run
#   # Preview changes without applying them
#
# CSV FORMAT:
#   InstanceId,InstanceName,SecurityGroupId,SecurityGroupName,VpcId
#   i-1234567890abcdef0,WebServer1,sg-12345678,web-sg,vpc-12345678
#
# PERMISSIONS REQUIRED:
# - ec2:DescribeInstances
# - ec2:DescribeSecurityGroups
# - ec2:ModifyInstanceAttribute
#

set -uo pipefail  # Undefined vars, pipe failures (removed -e to prevent crashes)
export AWS_PAGER=""  # Disable AWS CLI pager for non-interactive use

# Configuration
LOG_FILE="ec2-sg-import-$(date +%Y%m%d-%H%M%S).log"
MAX_LOGS=5

# Parameters
CSV_FILE="${1:-}"
DRY_RUN=false

#===============================================================================
# Logging Functions
#===============================================================================
setup_logging() {
    # Clean up old logs - keep only the most recent
    if ls ec2-sg-import-*.log >/dev/null 2>&1; then
        ls -t ec2-sg-import-*.log | tail -n +$((MAX_LOGS + 1)) | xargs -r rm -f
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

log_warning() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1"
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
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured or invalid."
        graceful_exit 1 "Prerequisites validation failed"
    fi
    
    log_success "Prerequisites validated"
}

validate_parameters() {
    log "Validating parameters..."
    
    # Check for dry-run flag in all parameters
    for arg in "$@"; do
        if [[ "$arg" == "--dry-run" ]]; then
            DRY_RUN=true
            log "DRY RUN MODE - No changes will be made"
            break
        fi
    done
    
    # Validate CSV file exists
    if [[ ! -f "$CSV_FILE" ]]; then
        log_error "CSV file not found: $CSV_FILE"
        graceful_exit 1 "Parameter validation failed"
    fi
    
    # Validate CSV file format
    if ! head -n1 "$CSV_FILE" | grep -q "InstanceId,InstanceName,SecurityGroupId,SecurityGroupName,VpcId"; then
        log_error "Invalid CSV format. Expected header: InstanceId,InstanceName,SecurityGroupId,SecurityGroupName,VpcId"
        graceful_exit 1 "Parameter validation failed"
    fi
    
    log "CSV File: $CSV_FILE"
    log "Dry Run Mode: $DRY_RUN"
    log_success "Parameters validated"
}

#===============================================================================
# Import Functions
#===============================================================================
analyze_csv() {
    log "Analyzing CSV file..."
    
    # Get unique instances from CSV
    UNIQUE_INSTANCES=$(tail -n +2 "$CSV_FILE" | cut -d',' -f1 | sort -u || echo "")
    if [[ -z "$UNIQUE_INSTANCES" ]]; then
        log_error "No instances found in CSV file"
        graceful_exit 1 "CSV analysis failed"
    fi
    
    TOTAL_INSTANCES=$(echo "$UNIQUE_INSTANCES" | wc -l | xargs)
    TOTAL_CSV_ROWS=$(tail -n +2 "$CSV_FILE" | wc -l | xargs)
    
    log "CSV Analysis Results:"
    log "  Total CSV rows: $TOTAL_CSV_ROWS"
    log "  Unique instances: $TOTAL_INSTANCES"
    log "  Average SGs per instance: $((TOTAL_CSV_ROWS / TOTAL_INSTANCES))"
    
    log_success "CSV analysis completed"
}

process_instances() {
    log "Processing $TOTAL_INSTANCES unique instances..."
    local current_instance=0
    local errors=0
    local instances_modified=0
    local instances_skipped=0
    local total_sgs_added=0

    for instance_id in $UNIQUE_INSTANCES; do
        ((current_instance++))
        
        # Get instance name from first CSV entry
        local instance_name
        instance_name=$(grep "^$instance_id," "$CSV_FILE" | head -n1 | cut -d',' -f2 || echo "(unknown)")
        
        log "[$current_instance/$TOTAL_INSTANCES] Processing $instance_id ($instance_name)"
        
        # Verify instance exists and get current state
        local instance_info
        instance_info=$(aws ec2 describe-instances \
            --instance-ids "$instance_id" \
            --query 'Reservations[0].Instances[0].[State.Name,SecurityGroups[].GroupId]' \
            --output text 2>/dev/null) || {
            log_error "  Instance $instance_id not found or inaccessible"
            ((errors++))
            continue
        }
        
        # Parse instance state and current security groups
        local instance_state current_sgs
        instance_state=$(echo "$instance_info" | head -n1)
        current_sgs=$(echo "$instance_info" | tail -n +2 | tr '\n' ' ' | xargs || echo "")
        
        log "  Instance state: $instance_state"
        log "  Current security groups: $current_sgs"
        
        # Get all security groups for this instance from CSV
        local desired_sgs
        desired_sgs=$(grep "^$instance_id," "$CSV_FILE" | cut -d',' -f3 | sort | tr '\n' ' ' | xargs || echo "")
        log "  Desired security groups: $desired_sgs"
        
        # Sort both for proper comparison
        local current_sgs_sorted desired_sgs_sorted
        current_sgs_sorted=$(echo "$current_sgs" | tr ' ' '\n' | sort | tr '\n' ' ' | xargs || echo "")
        desired_sgs_sorted=$(echo "$desired_sgs" | tr ' ' '\n' | sort | tr '\n' ' ' | xargs || echo "")
        
        # Skip if security groups already match exactly
        if [[ "$current_sgs_sorted" == "$desired_sgs_sorted" ]]; then
            log "  No changes needed - security groups already match exactly"
            ((instances_skipped++))
            continue
        fi
        
        # Find differences
        local missing_sgs="" extra_sgs=""
        
        # Find missing (in desired but not current)
        for sg in $desired_sgs; do
            if [[ ! " $current_sgs " =~ " $sg " ]]; then
                missing_sgs="$missing_sgs $sg"
            fi
        done
        
        # Find extra (in current but not desired)
        for sg in $current_sgs; do
            if [[ ! " $desired_sgs " =~ " $sg " ]]; then
                extra_sgs="$extra_sgs $sg"
            fi
        done
        
        missing_sgs=$(echo "$missing_sgs" | xargs || echo "")
        extra_sgs=$(echo "$extra_sgs" | xargs || echo "")
        
        # Log changes
        if [[ -n "$missing_sgs" ]]; then
            log "  Missing security groups: $missing_sgs"
        fi
        if [[ -n "$extra_sgs" ]]; then
            log "  Extra security groups (will be removed): $extra_sgs"
        fi
        
        # Verify all desired security groups exist
        local invalid_sgs=""
        for sg in $desired_sgs; do
            if ! aws ec2 describe-security-groups --group-ids "$sg" >/dev/null 2>&1; then
                invalid_sgs="$invalid_sgs $sg"
            fi
        done
        
        if [[ -n "$invalid_sgs" ]]; then
            log_error "  Security groups not found:$invalid_sgs"
            ((errors++))
            continue
        fi
        
        # Apply security group changes (replace all with desired)
        if [[ "$DRY_RUN" == "true" ]]; then
            log "  DRY RUN: Would replace security groups [$current_sgs] with [$desired_sgs]"
            ((instances_modified++))
        else
            log "  Replacing security groups with exact CSV match..."
            if aws ec2 modify-instance-attribute \
                --instance-id "$instance_id" \
                --groups $desired_sgs 2>/dev/null; then
                log_success "  Replaced security groups: now [$desired_sgs]"
                ((instances_modified++))
            else
                log_error "  Failed to replace security groups"
                ((errors++))
                continue
            fi
        fi
    done
    
    # Process summary
    log "Import processing completed:"
    log "  Instances processed: $current_instance"
    log "  Instances modified: $instances_modified"
    log "  Instances skipped (no changes): $instances_skipped"
    log "  Instances with exact matches: $instances_modified"
    log "  Errors encountered: $errors"
    
    if [[ $errors -gt 0 ]]; then
        log_error "Import completed with $errors errors"
        return 1
    fi
    
    log_success "All instances processed successfully"
    return 0
}

#===============================================================================
# Main Execution
#===============================================================================
main() {
    log "Starting EC2 Security Groups import script"
    log "Log file: $LOG_FILE"
    
    # Check if CSV file parameter was provided
    if [[ $# -lt 1 ]] || [[ -z "$CSV_FILE" ]]; then
        log_error "Missing required parameter: CSV_FILE"
        echo "Usage: $0 <CSV_FILE> [--dry-run]"
        echo "Example: $0 EC2SecurityGroups-20241201-143022.csv"
        echo "Example: $0 EC2SecurityGroups-20241201-143022.csv --dry-run"
        graceful_exit 1 "Parameter validation failed"
    fi
    
    validate_prerequisites
    validate_parameters "$@"
    analyze_csv
    
    if process_instances; then
        log_success "Import completed successfully!"
        
        echo ""
        echo "=== IMPORT SUMMARY ==="
        echo "CSV File: $CSV_FILE"
        echo "Total Instances: $TOTAL_INSTANCES"
        echo "Mode: $([ "$DRY_RUN" = "true" ] && echo "DRY RUN" || echo "LIVE")"
        echo "Log File: $LOG_FILE"
        echo ""
        
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "This was a dry run - no actual changes were made."
            echo "Remove --dry-run flag to apply changes."
            echo ""
            echo "Next Steps:"
            echo "1. Review the dry run results above"
            echo "2. Run without --dry-run to apply changes"
            echo "3. Check log file for details: $LOG_FILE"
        else
            echo "Security group associations have been restored."
            echo ""
            echo "Next Steps:"
            echo "1. Verify instances have correct security groups"
            echo "2. Test connectivity and access as needed"
            echo "3. Check log file for details: $LOG_FILE"
        fi
        
        graceful_exit 0 "Import completed successfully"
    else
        graceful_exit 1 "Import completed with errors"
    fi
}

# Initialize logging and run main function
setup_logging
main "$@"