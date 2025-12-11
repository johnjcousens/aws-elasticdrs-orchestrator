#!/bin/bash
# Creates an on-demand AWS Backup of a specified EC2 instance after safely shutting it down.
# Supports backup retention configuration and custom backup vault selection.
#
# DESCRIPTION:
# This script safely shuts down an EC2 instance, waits for it to be fully stopped, then creates
# an on-demand AWS Backup job. It supports both instance ID and Name tag lookup, configurable
# retention periods, and custom backup vault selection. VSS is disabled for Linux compatibility.
#
# USAGE:
#   ./createOnDemandEC2Backup.sh <instance-id-or-name> [retention_days] [backup_vault]
#
# EXAMPLES:
#   ./createOnDemandEC2Backup.sh i-0c705b20f40469720
#   # Backup instance with 1-day retention in default vault
#
#   ./createOnDemandEC2Backup.sh MyDomainController 7
#   # Backup instance by name with 7-day retention
#
#   ./createOnDemandEC2Backup.sh MyServer 30 my-custom-vault
#   # Backup with 30-day retention in custom vault
#
# BACKUP FEATURES:
# - Safe instance shutdown with status verification
# - Configurable retention (1-365 days)
# - Custom backup vault support
# - VSS disabled for cross-platform compatibility
# - Comprehensive logging and error handling
#
# REQUIREMENTS:
# - AWS CLI configured with appropriate permissions
# - Target instance must exist and be accessible
# - Backup vault must exist (creates default if needed)
#
# PERMISSIONS REQUIRED:
# - ec2:DescribeInstances
# - ec2:StopInstances
# - backup:StartBackupJob
# - backup:DescribeBackupVault
# - backup:CreateBackupVault (if vault doesn't exist)
# - iam:PassRole (for backup service role)
#
# CloudShell-friendly: Don't exit on errors, handle them gracefully
export AWS_PAGER=""

# Accept parameters or use defaults
INSTANCE_INPUT="${1}"
RETENTION_DAYS="${2:-1}"
BACKUP_VAULT="${3:-ams-manual-backups}"

LOG_FILE="ec2-backup-$(date '+%Y%m%d-%H%M%S').log"

# Clean up old log files, keep only 2 most recent using find instead of ls
find . -maxdepth 1 -name "ec2-backup-*.log" -type f -print0 2>/dev/null | \
    xargs -0 ls -t 2>/dev/null | tail -n +3 | xargs rm -f 2>/dev/null

log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    echo "$message" >> "$LOG_FILE"
}

# Cleanup function for temp files
cleanup() {
    rm -f "/tmp/instance_$$.json" 2>/dev/null
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



# Validate input parameters
if [ -z "$INSTANCE_INPUT" ]; then
    log "ERROR: Instance ID or Name tag is required"
    log "Usage: $0 <instance-id-or-name> [retention_days] [backup_vault]"
    return 1 2>/dev/null || exit 1
fi

# Validate retention days
if ! [[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]] || [ "$RETENTION_DAYS" -lt 1 ] || [ "$RETENTION_DAYS" -gt 365 ]; then
    log "ERROR: Retention days must be between 1 and 365"
    return 1 2>/dev/null || exit 1
fi

log "Starting EC2 on-demand backup script"
log "Target: $INSTANCE_INPUT"
log "Retention: $RETENTION_DAYS days"
log "Backup Vault: $BACKUP_VAULT"
log "Log file: $LOG_FILE"
log "Script PID: $$"
log ""

log "Step 0: Checking dependencies"
check_dependencies

log "Step 1: Resolving instance identifier"

# Determine if input is instance ID or Name tag
if [[ "$INSTANCE_INPUT" =~ ^i-[0-9a-f]{8,17}$ ]]; then
    INSTANCE_ID="$INSTANCE_INPUT"
    log "  Input recognized as Instance ID: $INSTANCE_ID"
else
    log "  Input recognized as Name tag, searching for instance: $INSTANCE_INPUT"
    INSTANCE_ID=$(aws ec2 describe-instances \
        --filters "Name=tag:Name,Values=$INSTANCE_INPUT" "Name=instance-state-name,Values=running,stopped,stopping" \
        --query 'Reservations[0].Instances[0].InstanceId' --output text 2>/dev/null)
    
    if [ "$INSTANCE_ID" = "None" ] || [ -z "$INSTANCE_ID" ]; then
        log "ERROR: No instance found with Name tag '$INSTANCE_INPUT'"
        return 1 2>/dev/null || exit 1
    fi
    log "  Found instance: $INSTANCE_ID"
fi

log "Step 2: Retrieving instance details"

# Get instance details
TEMP_FILE="/tmp/instance_$$.json"
if ! aws ec2 describe-instances --instance-ids "$INSTANCE_ID" > "$TEMP_FILE" 2>/dev/null; then
    log "ERROR: Failed to retrieve instance details for $INSTANCE_ID"
    return 1 2>/dev/null || exit 1
fi

# Extract instance information
INSTANCE_DATA=$(jq -r '.Reservations[0].Instances[0] | 
    "\(.State.Name) \(.Tags[]? | select(.Key=="Name") | .Value // "null") \(.InstanceType) \(.Placement.AvailabilityZone)"' "$TEMP_FILE")

read -r CURRENT_STATE INSTANCE_NAME INSTANCE_TYPE AZ <<< "$INSTANCE_DATA"

log "  Instance ID: $INSTANCE_ID"
log "  Instance Name: ${INSTANCE_NAME:-"No Name tag"}"
log "  Instance Type: $INSTANCE_TYPE"
log "  Availability Zone: $AZ"
log "  Current State: $CURRENT_STATE"

log "Step 3: Ensuring instance is stopped"

if [ "$CURRENT_STATE" = "running" ]; then
    log "  Instance is running, initiating shutdown..."
    if aws ec2 stop-instances --instance-ids "$INSTANCE_ID" >/dev/null 2>&1; then
        log "  ✓ Shutdown command sent successfully"
    else
        log "ERROR: Failed to send shutdown command to $INSTANCE_ID"
        return 1 2>/dev/null || exit 1
    fi
    
    log "  Waiting for instance to stop (this may take several minutes)..."
    WAIT_COUNT=0
    MAX_WAIT=300  # 5 minutes maximum wait
    
    while [ "$CURRENT_STATE" != "stopped" ] && [ $WAIT_COUNT -lt $MAX_WAIT ]; do
        sleep 10
        WAIT_COUNT=$((WAIT_COUNT + 10))
        CURRENT_STATE=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
            --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null)
        log "    Status: $CURRENT_STATE (waited ${WAIT_COUNT}s)"
    done
    
    if [ "$CURRENT_STATE" != "stopped" ]; then
        log "ERROR: Instance did not stop within $MAX_WAIT seconds"
        log "Current state: $CURRENT_STATE"
        return 1 2>/dev/null || exit 1
    fi
    
    log "  ✓ Instance successfully stopped"
elif [ "$CURRENT_STATE" = "stopped" ]; then
    log "  ✓ Instance is already stopped"
elif [ "$CURRENT_STATE" = "stopping" ]; then
    log "  Instance is currently stopping, waiting for completion..."
    if timeout 300 aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID" 2>/dev/null; then
        log "  ✓ Instance stopped"
    else
        log "ERROR: Timeout waiting for instance to stop or wait command failed"
        log "Check instance status manually before proceeding"
        return 1 2>/dev/null || exit 1
    fi
else
    log "ERROR: Instance is in unexpected state: $CURRENT_STATE"
    log "Expected states: running, stopped, or stopping"
    return 1 2>/dev/null || exit 1
fi

log "Step 4: Verifying backup vault"

# Check if backup vault exists
if aws backup describe-backup-vault --backup-vault-name "$BACKUP_VAULT" >/dev/null 2>&1; then
    log "  ✓ Backup vault '$BACKUP_VAULT' exists"
else
    log "  Backup vault '$BACKUP_VAULT' not found, creating..."
    if aws backup create-backup-vault --backup-vault-name "$BACKUP_VAULT" >/dev/null 2>&1; then
        log "  ✓ Created backup vault '$BACKUP_VAULT'"
    else
        log "ERROR: Failed to create backup vault '$BACKUP_VAULT'"
        return 1 2>/dev/null || exit 1
    fi
fi

log "Step 5: Creating backup job"

# Cache AWS account info to avoid multiple API calls
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ -z "$AWS_ACCOUNT_ID" ]; then
    log "ERROR: Failed to retrieve AWS account ID"
    log "Check AWS credentials and permissions"
    return 1 2>/dev/null || exit 1
fi

# Generate backup job name
BACKUP_JOB_ID="manual-backup-$(echo "$INSTANCE_ID" | tr -d '-')-$(date '+%Y%m%d-%H%M%S')"
RESOURCE_ARN="arn:aws:ec2:$AWS_REGION:$AWS_ACCOUNT_ID:instance/$INSTANCE_ID"

log "  Backup Job ID: $BACKUP_JOB_ID"
log "  Resource ARN: $RESOURCE_ARN"
log "  Retention: $RETENTION_DAYS days"

# Start backup job using cached account ID
if aws backup start-backup-job \
    --backup-vault-name "$BACKUP_VAULT" \
    --resource-arn "$RESOURCE_ARN" \
    --iam-role-arn "arn:aws:iam::$AWS_ACCOUNT_ID:role/service-role/AWSBackupDefaultServiceRole" \
    --backup-job-id "$BACKUP_JOB_ID" \
    --complete-window-minutes 120 \
    --lifecycle "DeleteAfterDays=$RETENTION_DAYS" >/dev/null 2>&1; then
    
    log "  ✓ SUCCESS: Backup job started successfully"
    log "    Job ID: $BACKUP_JOB_ID"
    log "    Vault: $BACKUP_VAULT"
    log "    Retention: $RETENTION_DAYS days"
else
    log "ERROR: Failed to start backup job"
    log "Check AWS permissions and backup service role"
    return 1 2>/dev/null || exit 1
fi

log ""
log "========================================"
log "BACKUP JOB SUMMARY"
log "========================================"
log "Instance: ${INSTANCE_NAME:-$INSTANCE_ID} ($INSTANCE_ID)"
log "Backup Job ID: $BACKUP_JOB_ID"
log "Backup Vault: $BACKUP_VAULT"
log "Retention Period: $RETENTION_DAYS days"
log "Completion Window: 120 minutes"
log "VSS Enabled: No (disabled for compatibility)"
log ""
log "✓ Backup job initiated successfully"
log "⚠ Instance remains stopped - start manually when backup completes"
log "📊 Monitor backup progress in AWS Backup console"
log ""
log "Script completed at $(date '+%Y-%m-%d %H:%M:%S')"
log "Log file saved: $LOG_FILE"