#!/bin/bash
# Creates an AMI backup of an EC2 instance and then creates a launch template using the backup AMI.
# Combines AMI backup creation with launch template generation in a single workflow.
#
# DESCRIPTION:
# This unified script performs two operations:
# 1. Creates an AMI backup of the specified instance (with retention tagging)
# 2. Creates a launch template using the backup AMI instead of the original AMI
#
# USAGE:
#   ./createEC2BackupImageAndLaunchTemplate.sh [instance-id-or-name] [region]
#
# PARAMETERS:
#   instance-id-or-name: EC2 instance ID or Name tag (default: MyServerName)
#   region: AWS region where the target instance exists (default: us-west-2)
#
# EXAMPLES:
#   ./createEC2BackupImageAndLaunchTemplate.sh
#   # Backs up MyServerName instance in us-west-2
#
#   ./createEC2BackupImageAndLaunchTemplate.sh MyDomainController
#   # Backs up MyDomainController instance in us-west-2
#
#   ./createEC2BackupImageAndLaunchTemplate.sh i-0c705b20f40469720 us-east-1
#   # Backs up specific instance ID in us-east-1 region
#
# PERMISSIONS REQUIRED:
# - ec2:DescribeInstances
# - ec2:StopInstances  
# - ec2:CreateImage
# - ec2:CreateTags
# - ec2:CreateLaunchTemplate
# - iam:PassRole (if instance has IAM profile)
#
export AWS_PAGER=""

# Accept parameters
INSTANCE_INPUT="${1:-MyServerName}"
REGION="${2:-us-west-2}"
RETENTION_DAYS=7

# Set AWS region
export AWS_DEFAULT_REGION="$REGION"

# Generate timestamps once for reuse
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
DATE_TIME=$(date '+%Y-%m-%d %H:%M:%S')

# Log file will be created after getting instance details

# Validate dependencies
if ! command -v jq >/dev/null 2>&1; then
    echo "ERROR: jq is required but not installed. Please install jq to continue."
    exit 1
fi

# Error handling function
handle_error() {
    log "ERROR: $1"
    exit 1
}

log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    if [ -n "$LOG_FILE" ]; then
        echo "$message" >> "$LOG_FILE"
    fi
}

log "Starting unified backup and launch template creation"
log "Target Instance: $INSTANCE_INPUT"
log "Target Region: $REGION"
log "Retention: $RETENTION_DAYS days"
log ""

# PHASE 1: CREATE AMI BACKUP
log "=== PHASE 1: Creating AMI Backup ==="

# Resolve instance identifier and get full instance data in one call
if [[ "$INSTANCE_INPUT" =~ ^i-[0-9a-f]{8,17}$ ]]; then
    INSTANCE_ID="$INSTANCE_INPUT"
    log "Input recognized as Instance ID: $INSTANCE_ID"
    # Get full instance data for both phases
    FULL_INSTANCE_DATA=$(aws ec2 describe-instances --region "$REGION" --instance-ids "$INSTANCE_ID" 2>/dev/null) || handle_error "Failed to describe instance $INSTANCE_ID"
else
    log "Input recognized as Name tag, searching for instance: $INSTANCE_INPUT"
    # Get instance by name tag
    FULL_INSTANCE_DATA=$(aws ec2 describe-instances --region "$REGION" \
        --filters "Name=tag:Name,Values=$INSTANCE_INPUT" "Name=instance-state-name,Values=running,stopped,stopping" 2>/dev/null) || handle_error "Failed to search for instance with name $INSTANCE_INPUT"
    
    INSTANCE_ID=$(echo "$FULL_INSTANCE_DATA" | jq -r '.Reservations[0].Instances[0].InstanceId // "None"')
    
    if [ "$INSTANCE_ID" = "None" ] || [ -z "$INSTANCE_ID" ]; then
        handle_error "No instance found with Name tag \"$INSTANCE_INPUT\""
    fi
    log "Found instance: $INSTANCE_ID"
fi

# Extract instance details with separate, readable jq calls
INSTANCE_OBJ=$(echo "$FULL_INSTANCE_DATA" | jq -r '.Reservations[0].Instances[0]')
CURRENT_STATE=$(echo "$INSTANCE_OBJ" | jq -r '.State.Name')
INSTANCE_NAME=$(echo "$INSTANCE_OBJ" | jq -r '.Tags[]? | select(.Key=="Name") | .Value // "NoName"')
INSTANCE_TYPE=$(echo "$INSTANCE_OBJ" | jq -r '.InstanceType')
PRIVATE_IP=$(echo "$INSTANCE_OBJ" | jq -r '.NetworkInterfaces[0].PrivateIpAddress // "null"')
SUBNET_ID=$(echo "$INSTANCE_OBJ" | jq -r '.SubnetId // "null"')
IAM_INSTANCE_PROFILE=$(echo "$INSTANCE_OBJ" | jq -r '.IamInstanceProfile.Arn // "null"')
SECURITY_GROUP_IDS=$(echo "$INSTANCE_OBJ" | jq -c '[.SecurityGroups[].GroupId]')

# Create log file with instance name and ID
LOG_FILE="${INSTANCE_NAME}-${INSTANCE_ID}-backup-and-template-${TIMESTAMP}.log"

log "Instance Name: ${INSTANCE_NAME:-"No Name tag"}"
log "Instance Type: $INSTANCE_TYPE"
log "Current State: $CURRENT_STATE"

# Ensure instance is stopped
if [ "$CURRENT_STATE" = "running" ]; then
    log "Instance is running, initiating shutdown..."
    aws ec2 stop-instances --region "$REGION" --instance-ids "$INSTANCE_ID" >/dev/null || handle_error "Failed to stop instance $INSTANCE_ID"
    log "Waiting for instance to stop..."
    aws ec2 wait instance-stopped --region "$REGION" --instance-ids "$INSTANCE_ID" || handle_error "Instance failed to stop within timeout"
    log "Instance successfully stopped"
elif [ "$CURRENT_STATE" = "stopped" ]; then
    log "Instance is already stopped"
elif [ "$CURRENT_STATE" = "stopping" ]; then
    log "Instance is stopping, waiting for completion..."
    aws ec2 wait instance-stopped --region "$REGION" --instance-ids "$INSTANCE_ID" || handle_error "Instance failed to stop within timeout"
    log "Instance stopped"
else
    handle_error "Instance is in unexpected state: $CURRENT_STATE"
fi

# Create AMI backup
AMI_NAME="backup-${INSTANCE_NAME:-$INSTANCE_ID}-${TIMESTAMP}"
DELETE_DATE=$(date -d "+$RETENTION_DAYS days" '+%Y-%m-%d' 2>/dev/null || date -v "+${RETENTION_DAYS}d" '+%Y-%m-%d')

log "Creating AMI backup..."
AMI_OUTPUT=$(aws ec2 create-image --region "$REGION" \
    --instance-id "$INSTANCE_ID" \
    --name "$AMI_NAME" \
    --description "Backup of $INSTANCE_ID created ${DATE_TIME}" \
    --no-reboot) || handle_error "Failed to create AMI backup"

AMI_ID=$(echo "$AMI_OUTPUT" | jq -r '.ImageId')
if [ "$AMI_ID" = "null" ] || [ -z "$AMI_ID" ]; then
    handle_error "Failed to extract AMI ID from create-image response"
fi

# Tag the AMI with retention info
aws ec2 create-tags --region "$REGION" --resources "$AMI_ID" --tags \
    Key=Name,Value="$AMI_NAME" \
    Key=SourceInstance,Value="$INSTANCE_ID" \
    Key=CreatedBy,Value="Unified-Backup-Script" \
    Key=RetentionDays,Value="$RETENTION_DAYS" \
    Key=DeleteAfter,Value="$DELETE_DATE" >/dev/null || handle_error "Failed to tag AMI $AMI_ID"

log "✓ AMI backup created successfully"
log "  AMI ID: $AMI_ID"
log "  AMI Name: $AMI_NAME"

# PHASE 2: CREATE LAUNCH TEMPLATE WITH BACKUP AMI
log ""
log "=== PHASE 2: Creating Launch Template with Backup AMI ==="

# Validate extracted values before proceeding
if [ "$SUBNET_ID" = "null" ] || [ -z "$SUBNET_ID" ]; then
    handle_error "Failed to extract subnet ID from instance $INSTANCE_ID"
fi
if [ "$PRIVATE_IP" = "null" ] || [ -z "$PRIVATE_IP" ]; then
    handle_error "Failed to extract private IP from instance $INSTANCE_ID"
fi
if [ "$INSTANCE_TYPE" = "null" ] || [ -z "$INSTANCE_TYPE" ]; then
    handle_error "Failed to extract instance type from instance $INSTANCE_ID"
fi
if [ "$SECURITY_GROUP_IDS" = "[]" ] || [ "$SECURITY_GROUP_IDS" = "null" ]; then
    handle_error "Failed to extract security groups from instance $INSTANCE_ID"
fi

# Create tag specifications (exclude AWS internal tags) - single jq call
TAG_SPECIFICATIONS=$(echo "$FULL_INSTANCE_DATA" | jq -c '.Reservations[0].Instances[0] | [{"ResourceType":"instance","Tags": [.Tags[] | select(.Key | test("^aws:") | not)]}]')

# Use instance name with backup suffix and timestamp for uniqueness
LAUNCH_TEMPLATE_NAME="${INSTANCE_NAME}-backup-template-${TIMESTAMP}"

log "Creating launch template with backup AMI..."
log "  Template Name: $LAUNCH_TEMPLATE_NAME"
log "  Using Backup AMI: $AMI_ID (instead of original)"
log "  Instance Type: $INSTANCE_TYPE"
log "  Subnet: $SUBNET_ID"

# Build launch template JSON using backup AMI
LAUNCH_TEMPLATE_JSON=$(jq -n \
  --arg ImageId "$AMI_ID" \
  --arg InstanceType "$INSTANCE_TYPE" \
  --arg SubnetId "$SUBNET_ID" \
  --arg PrivateIp "$PRIVATE_IP" \
  --argjson SecurityGroupIds "$SECURITY_GROUP_IDS" \
  --argjson TagSpecifications "$TAG_SPECIFICATIONS" \
  '{
    "ImageId": $ImageId,
    "InstanceType": $InstanceType,
    "NetworkInterfaces": [{
      "DeviceIndex": 0,
      "SubnetId": $SubnetId,
      "AssociatePublicIpAddress": false,
      "Groups": $SecurityGroupIds,
      "PrivateIpAddresses": [{
        "Primary": true,
        "PrivateIpAddress": $PrivateIp
      }]
    }],
    "TagSpecifications": $TagSpecifications
  }')

# Add IAM instance profile if present
if [ "$IAM_INSTANCE_PROFILE" != "null" ] && [ -n "$IAM_INSTANCE_PROFILE" ]; then
    LAUNCH_TEMPLATE_JSON=$(echo "$LAUNCH_TEMPLATE_JSON" | jq --arg IamArn "$IAM_INSTANCE_PROFILE" '. + {"IamInstanceProfile": {"Arn": $IamArn}}')
fi

# Create launch template
aws ec2 create-launch-template --region "$REGION" --launch-template-name "$LAUNCH_TEMPLATE_NAME" \
  --version-description "Created from backup AMI $AMI_ID of instance $INSTANCE_ID on ${DATE_TIME}" \
  --launch-template-data "$LAUNCH_TEMPLATE_JSON" >/dev/null 2>&1 || handle_error "Failed to create launch template $LAUNCH_TEMPLATE_NAME"

log "✓ Launch template created successfully"

log ""
log "========================================"
log "UNIFIED BACKUP & TEMPLATE SUMMARY"
log "========================================"
log "Source Instance: ${INSTANCE_NAME:-$INSTANCE_ID} ($INSTANCE_ID)"
log ""
log "AMI BACKUP:"
log "  AMI ID: $AMI_ID"
log "  AMI Name: $AMI_NAME"
log "  Retention: $RETENTION_DAYS days (delete after $DELETE_DATE)"
log ""
log "LAUNCH TEMPLATE:"
log "  Template Name: $LAUNCH_TEMPLATE_NAME"
log "  Uses Backup AMI: $AMI_ID"
log "  Instance Type: $INSTANCE_TYPE"
log "  Network: $SUBNET_ID ($PRIVATE_IP)"
log ""
log "✓ Both backup AMI and launch template created successfully"
log "⚠ Instance remains stopped - start manually when ready"
log "📋 Launch template ready for Auto Scaling Groups or manual launches"
log ""
log "Script completed at ${DATE_TIME}"
log "Log file saved: $LOG_FILE"

echo "AMI_ID=$AMI_ID"
echo "LAUNCH_TEMPLATE_NAME=$LAUNCH_TEMPLATE_NAME"
echo "DELETE_AFTER=$DELETE_DATE"