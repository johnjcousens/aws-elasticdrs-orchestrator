#!/bin/bash
# Automates AWS Disaster Recovery Service (DRS) launch configuration updates by matching DRS source servers
# to EC2 instances based on Name tags and configuring launch-into-instance settings.
#
# DESCRIPTION:
# This script retrieves all DRS source servers from a specified region, finds matching EC2 instances
# based on Name tags, and configures DRS to launch into specific stopped EC2 instances that have
# the AWSDRS=AllowLaunchingIntoThisInstance tag. It provides comprehensive logging and error handling.
#
# USAGE:
#   ./updateDRSLaunchsettings.sh [region]
#
# EXAMPLES:
#   ./updateDRSLaunchsettings.sh                    # Uses default region (us-west-2)
#   ./updateDRSLaunchsettings.sh us-east-1          # Uses specified region
#
# REQUIREMENTS:
# - AWS CLI configured with appropriate permissions
# - jq installed for JSON parsing
# - DRS source servers with Name tags
# - Target EC2 instances in stopped state with AWSDRS=AllowLaunchingIntoThisInstance tag
#
# PERMISSIONS REQUIRED:
# - drs:DescribeSourceServers
# - drs:UpdateLaunchConfiguration
# - ec2:DescribeInstances
#
# CloudShell-friendly: Don't exit on errors, handle them gracefully
export AWS_PAGER=""

# Accept region as parameter or use default
DR_REGION="${1:-us-west-2}"

LOG_FILE="drs-update-$(date '+%Y%m%d-%H%M%S').log"

# Clean up old log files, keep only 2 most recent using find instead of ls
find . -maxdepth 1 -name "drs-update-*.log" -type f -print0 2>/dev/null | \
    xargs -0 ls -t 2>/dev/null | tail -n +3 | xargs rm -f 2>/dev/null

log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    echo "$message" >> "$LOG_FILE"
}

# Cleanup function for temp files
cleanup() {
    rm -f "/tmp/drs_servers_$$.json" "/tmp/ec2_instances_$$.json" 2>/dev/null
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Check dependencies
check_dependencies() {
    local missing_deps=()
    
    if ! command -v aws >/dev/null 2>&1; then
        missing_deps+=("aws")
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        missing_deps+=("jq")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log "ERROR: Missing required dependencies: ${missing_deps[*]}"
        log "Please install missing tools before running this script"
        return 1 2>/dev/null || exit 1
    fi
    
    log "✓ All dependencies verified (aws, jq)"
}

# Process individual DRS source server
process_drs_server() {
    local source_server_id="$1"
    local server_name="$2"
    local server_number="$3"
    local total_servers="$4"
    
    log "========================================"
    log "Processing source server $server_number of $total_servers: $source_server_id"
    log "========================================"
    
    log "Step 2.$server_number.1: Processing server name tag for $source_server_id"
    log "  Server Name: ${server_name:-"No Name tag found"}"
   
    if [ "$server_name" = "null" ] || [ -z "$server_name" ]; then
        log "  SKIP: No Name tag found for $source_server_id, cannot match to EC2 instance"
        log "  Recommendation: Add a 'Name' tag to this DRS source server"
        return 2  # Return 2 for skipped
    fi
    
    log "  SUCCESS: Found server name $server_name for source server $source_server_id"
   
    log "Step 2.$server_number.2: Searching for matching EC2 instances with name $server_name"
    
    # Get all matching instances data in one call and cache it
    local all_matching_data
    all_matching_data=$(aws ec2 describe-instances --region "$DR_REGION" \
        --filters "Name=tag:Name,Values=$server_name" \
        --query "Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key==\`AWSDRS\`].Value|[0]]" \
        --output text 2>/dev/null)
    
    if [ -z "$all_matching_data" ]; then
        log "  SKIP: No EC2 instances found with Name tag $server_name"
        log "  Recommendation: Create an EC2 instance with Name=$server_name and AWSDRS tag"
        return 2  # Return 2 for skipped
    fi
    
    log "  Found EC2 instances with matching name:"
    local suitable_instance=""
    
    while IFS=$'\t' read -r inst_id inst_state awsdrs_value; do
        [ -z "$inst_id" ] && continue
        log "    Instance: $inst_id"
        log "      State: $inst_state"
        log "      AWSDRS Tag: ${awsdrs_value:-\"Not present\"}"
        
        if [ "$inst_state" = "stopped" ] && [ "$awsdrs_value" = "AllowLaunchingIntoThisInstance" ]; then
            log "      STATUS: ✓ Suitable for DRS launch configuration"
            suitable_instance="$inst_id"
        else
            log "      STATUS: ✗ Not suitable (needs to be stopped with AWSDRS=AllowLaunchingIntoThisInstance)"
        fi
    done <<< "$all_matching_data"
    
    log "Step 2.$server_number.3: Finding suitable target instance (stopped + AWSDRS tag)"
    
    if [ -z "$suitable_instance" ]; then
        log "  SKIP: No suitable instance found for $server_name"
        log "  Requirements: Instance must be STOPPED and have AWSDRS=AllowLaunchingIntoThisInstance tag"
        return 2  # Return 2 for skipped
    fi
    
    log "  SUCCESS: Selected target instance $suitable_instance for launch configuration"
   
    log "Step 2.$server_number.4: Updating DRS launch configuration"
    log "  Disabling conflicting settings for launch-into-instance"
    
    # Disable all conflicting settings for launch-into-instance
    log "  Disabling conflicting settings..."
    disable_error=$(aws drs update-launch-configuration --region "$DR_REGION" \
        --source-server-id "$source_server_id" \
        --no-copy-tags \
        --no-copy-private-ip \
        --target-instance-type-right-sizing-method NONE \
        --launch-disposition STOPPED 2>&1)
    
    if [ $? -eq 0 ]; then
        log "  SUCCESS: Conflicting settings disabled for $source_server_id"
    else
        log "  WARNING: Failed to disable some settings for $source_server_id"
        log "  Error details: $disable_error"
        log "  Continuing with launch-into-instance configuration..."
    fi
    
    
    log "  Configuring launch-into-instance settings:"
    log "    Source Server: $source_server_id"
    log "    Target Instance: $suitable_instance"
    log "    Server Name: $server_name"
    log "    Instance Type Right Sizing: INACTIVE"
    log "    Copy Private IP: DISABLED"
    log "    Copy Tags: DISABLED"
    log "    Launch Into Instance: ENABLED"
    log "    Start Instance Upon Launch: DISABLED (STOPPED)"
   
    launch_error=$(aws drs update-launch-configuration --region "$DR_REGION" \
        --source-server-id "$source_server_id" \
        --launch-into-instance-properties "{\"launchIntoEC2InstanceID\":\"$suitable_instance\"}" 2>&1)
    
    if [ $? -eq 0 ]; then
        log "  ✓ SUCCESS: Launch configuration updated successfully"
        log "    $server_name ($source_server_id) -> $suitable_instance"
        return 0  # Return 0 for success
    else
        log "  ✗ ERROR: Failed to update launch configuration for $source_server_id"
        log "    AWS Error: $launch_error"
        return 1  # Return 1 for failure
    fi
}

log "Starting DRS launch configuration update script"
log "Target region: $DR_REGION"
log "Log file: $LOG_FILE"
log "Script PID: $$"
log ""

log "Step 0: Checking dependencies"
check_dependencies
log "Step 1: Retrieving DRS source servers from region: $DR_REGION"

# Get source servers dynamically
TEMP_FILE="/tmp/drs_servers_$$.json"
log "Creating temporary file: $TEMP_FILE"
if ! aws drs describe-source-servers --region "$DR_REGION" > "$TEMP_FILE"; then
    log "ERROR: Failed to retrieve DRS source servers from AWS API"
    log "Check AWS credentials and region access"
    return 1 2>/dev/null || exit 1
fi
log "Successfully retrieved DRS source servers data"

# Extract server IDs and names in single operation for performance
SERVER_DATA=$(jq -r '.items[] | "\(.sourceServerID) \(.tags.Name // "null")"' "$TEMP_FILE" 2>/dev/null)
jq_exit=$?

# Validate jq parsing succeeded
if [ $jq_exit -ne 0 ] || [ -z "$SERVER_DATA" ]; then
    log "ERROR: Failed to parse DRS server data with jq"
    log "Check if DRS API response is valid JSON format"
    return 1 2>/dev/null || exit 1
fi

rm -f "$TEMP_FILE"
log "Cleaned up temporary file: $TEMP_FILE"

if [ -z "$SERVER_DATA" ]; then
    log "WARNING: No source servers found in region $DR_REGION"
    log "This could indicate no DRS servers are configured or access issues"
    return 1 2>/dev/null || exit 1
fi

SERVER_COUNT=$(echo "$SERVER_DATA" | wc -l)
log "Found $SERVER_COUNT DRS source servers to process"
log "Server data extracted from initial API call"
log ""

PROCESSED=0
SUCCESSFUL=0
SKIPPED=0
FAILED=0

# Process each server using the extracted function
while read -r SOURCE_SERVER_ID SERVER_NAME; do
    if [ -z "$SOURCE_SERVER_ID" ]; then
        continue
    fi
    PROCESSED=$((PROCESSED + 1))
    
    # Call the processing function
    process_drs_server "$SOURCE_SERVER_ID" "$SERVER_NAME" "$PROCESSED" "$SERVER_COUNT"
    result=$?
    
    case $result in
        0) SUCCESSFUL=$((SUCCESSFUL + 1)) ;;
        1) FAILED=$((FAILED + 1)) ;;
        2) SKIPPED=$((SKIPPED + 1)) ;;
    esac
   
    echo ""
done <<< "$SERVER_DATA"

log "========================================"
log "SCRIPT EXECUTION SUMMARY"
log "========================================"
log "Total source servers found: $SERVER_COUNT"
log "Successfully processed: $SUCCESSFUL"
log "Skipped (no name/no suitable instance): $SKIPPED"
log "Failed (AWS API errors): $FAILED"
log "Total processed: $PROCESSED"
log ""
if [ "$SUCCESSFUL" -gt 0 ]; then
    log "✓ $SUCCESSFUL source servers now configured for launch-into-instance"
fi
if [ "$SKIPPED" -gt 0 ]; then
    log "⚠ $SKIPPED source servers skipped - check Name tags and target instances"
fi
if [ "$FAILED" -gt 0 ]; then
    log "✗ $FAILED source servers failed - check AWS permissions and connectivity"
fi
log ""
log "Script completed at $(date '+%Y-%m-%d %H:%M:%S')"
log "Log file saved: $LOG_FILE"
