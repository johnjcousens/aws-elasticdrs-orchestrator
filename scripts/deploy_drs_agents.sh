#!/bin/bash

# DRS Agent Deployment Script
# 
# This script automatically discovers and installs AWS DRS agents on EC2 instances
# tagged with dr:enabled=true AND dr:recovery-strategy=drs in the specified account.
#
# Usage: 
#   ./deploy_drs_agents.sh [account_id] [source_region] [target_region]
#
# Parameters:
#   account_id     - AWS account ID (default: 111122223333)
#   source_region  - Region where instances are located (default: us-east-1)
#   target_region  - Region to replicate to (default: us-west-2)
#
# Examples:
#   ./deploy_drs_agents.sh                                    # Use defaults
#   ./deploy_drs_agents.sh 111122223333                       # Specify account
#   ./deploy_drs_agents.sh 111122223333 us-east-1 us-west-2  # Full specification
#   ./deploy_drs_agents.sh 777788889999 us-east-1 us-west-2  # Different account
#
# Authentication Methods:
#   1. AWS Profile (Current): Uses {account_id}_AdministratorAccess profile
#   2. Cross-Account Role (Future): Assumes role in target account
#      - Set AWS_ROLE_ARN environment variable
#      - Example: export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/DRSOrchestrationRole"
#
# Requirements:
#   - AWS CLI configured with profile: {account_id}_AdministratorAccess
#   - Instances must be tagged with:
#     * dr:enabled=true
#     * dr:recovery-strategy=drs
#   - Instances must have SSM agent online
#   - IAM instance profile with SSM and DRS permissions:
#     * AmazonSSMManagedInstanceCore
#     * AWSElasticDisasterRecoveryAgentInstallationPolicy
#
# Cross-Account Role Requirements (for orchestration):
#   The cross-account role must have permissions for:
#   - ec2:DescribeInstances
#   - ssm:SendCommand
#   - ssm:ListCommandInvocations
#   - ssm:GetCommandInvocation
#   - drs:DescribeSourceServers
#
# Instance IAM Role Requirements:
#   The EC2 instance profile must have:
#   - AmazonSSMManagedInstanceCore (for SSM)
#   - AWSElasticDisasterRecoveryAgentInstallationPolicy (for DRS agent)
#
# Discovery Logic:
#   - Finds all running instances with both tags:
#     * dr:enabled=true
#     * dr:recovery-strategy=drs
#   - No need to specify instance IDs manually
#   - Automatically handles multiple instances across waves

# Show help if requested
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
  grep "^#" "$0" | grep -v "#!/bin/bash" | sed 's/^# //' | sed 's/^#//'
  exit 0
fi

# Usage: ./deploy_drs_agents.sh [account_id] [source_region] [target_region]
# Example: ./deploy_drs_agents.sh 111122223333 us-east-1 us-west-2

# Parse parameters
ACCOUNT_ID="${1:-111122223333}"
SOURCE_REGION="${2:-us-east-1}"
TARGET_REGION="${3:-us-west-2}"

# Set AWS profile based on account ID (unless using cross-account role)
if [ -n "$AWS_ROLE_ARN" ]; then
  echo "Using cross-account role: $AWS_ROLE_ARN"
  # Assume role and export credentials
  CREDS=$(aws sts assume-role --role-arn "$AWS_ROLE_ARN" --role-session-name "DRSAgentDeployment" --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' --output text)
  export AWS_ACCESS_KEY_ID=$(echo $CREDS | awk '{print $1}')
  export AWS_SECRET_ACCESS_KEY=$(echo $CREDS | awk '{print $2}')
  export AWS_SESSION_TOKEN=$(echo $CREDS | awk '{print $3}')
else
  export AWS_PROFILE="${ACCOUNT_ID}_AdministratorAccess"
fi

# Verify credentials
echo "Verifying AWS credentials for account $ACCOUNT_ID..."
CURRENT_ACCOUNT=$(AWS_PAGER="" aws sts get-caller-identity --query 'Account' --output text 2>/dev/null)

if [ $? -ne 0 ]; then
  echo "❌ Failed to authenticate with AWS"
  echo "Make sure profile '${AWS_PROFILE}' exists in ~/.aws/credentials"
  exit 1
fi

if [ "$CURRENT_ACCOUNT" != "$ACCOUNT_ID" ]; then
  echo "❌ Account mismatch! Expected $ACCOUNT_ID but got $CURRENT_ACCOUNT"
  exit 1
fi

echo "✅ Authenticated as account $ACCOUNT_ID"
echo ""

# Discover instances with DRS tags in the account
echo "Discovering instances with dr:enabled=true AND dr:recovery-strategy=drs..."
INSTANCE_LIST=$(AWS_PAGER="" aws ec2 describe-instances \
  --region $SOURCE_REGION \
  --filters \
    "Name=tag:dr:enabled,Values=true" \
    "Name=tag:dr:recovery-strategy,Values=drs" \
    "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],Tags[?Key==`dr:wave`].Value|[0]]' \
  --output text)

if [ -z "$INSTANCE_LIST" ]; then
  echo "❌ No instances found with dr:enabled=true AND dr:recovery-strategy=drs in $SOURCE_REGION"
  exit 1
fi

# Build instance array and display by wave
INSTANCES=()
echo ""
echo "Instances discovered by DR Wave:"
echo "================================"

declare -A WAVE_INSTANCES
while IFS=$'\t' read -r instance_id instance_name wave; do
  INSTANCES+=("$instance_id")
  wave=${wave:-"unassigned"}
  WAVE_INSTANCES[$wave]+="  - $instance_id ($instance_name)"$'\n'
done <<< "$INSTANCE_LIST"

# Display instances grouped by wave
for wave in $(echo "${!WAVE_INSTANCES[@]}" | tr ' ' '\n' | sort); do
  echo ""
  echo "DR Wave $wave:"
  echo -n "${WAVE_INSTANCES[$wave]}"
done

echo ""
echo "Found ${#INSTANCES[@]} instances to configure for DRS"
echo ""

echo "=========================================="
echo "DRS Agent Deployment Workflow"
echo "=========================================="
echo "Account: $ACCOUNT_ID"
echo "Source Region: $SOURCE_REGION"
echo "Target Region: $TARGET_REGION"
echo "Instances: ${#INSTANCES[@]}"
echo ""

# Step 1: Check EC2 instance status
echo "[1/4] Checking EC2 instance status..."
AWS_PAGER="" aws ec2 describe-instances \
  --region $SOURCE_REGION \
  --instance-ids "${INSTANCES[@]}" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' \
  --output table

echo ""
echo "Verifying all instances are running..."
RUNNING_COUNT=$(AWS_PAGER="" aws ec2 describe-instances \
  --region $SOURCE_REGION \
  --instance-ids "${INSTANCES[@]}" \
  --query 'Reservations[*].Instances[?State.Name==`running`] | length(@)' \
  --output text)

if [ "$RUNNING_COUNT" -ne "${#INSTANCES[@]}" ]; then
  echo "❌ Not all instances are running ($RUNNING_COUNT / ${#INSTANCES[@]})"
  exit 1
fi
echo "✅ All instances are running"

# Step 2: Check SSM agent registration
echo ""
echo "[2/4] Checking SSM agent registration..."
echo "Waiting for SSM agents to come online (this may take 2-5 minutes)..."
echo ""

MAX_WAIT=300  # 5 minutes
WAIT_INTERVAL=15
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
  ONLINE_COUNT=$(AWS_PAGER="" aws ssm describe-instance-information \
    --region $SOURCE_REGION \
    --filters "Key=InstanceIds,Values=$(IFS=,; echo "${INSTANCES[*]}")" \
    --query 'InstanceInformationList[?PingStatus==`Online`] | length(@)' \
    --output text)
  
  echo "[$ELAPSED seconds] SSM agents online: $ONLINE_COUNT / ${#INSTANCES[@]}"
  
  if [ "$ONLINE_COUNT" -eq "${#INSTANCES[@]}" ]; then
    echo ""
    echo "✅ All SSM agents are online!"
    break
  fi
  
  sleep $WAIT_INTERVAL
  ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ "$ONLINE_COUNT" -ne "${#INSTANCES[@]}" ]; then
  echo ""
  echo "❌ Only $ONLINE_COUNT / ${#INSTANCES[@]} SSM agents are online after $MAX_WAIT seconds"
  echo ""
  echo "SSM Agent Status:"
  AWS_PAGER="" aws ssm describe-instance-information \
    --region $SOURCE_REGION \
    --filters "Key=InstanceIds,Values=$(IFS=,; echo "${INSTANCES[*]}")" \
    --query 'InstanceInformationList[*].[InstanceId,PingStatus,PlatformType,PlatformVersion]' \
    --output table
  
  echo ""
  echo "⚠️  Proceeding anyway with available instances..."
fi

# Show detailed SSM status
echo ""
echo "SSM Agent Details:"
AWS_PAGER="" aws ssm describe-instance-information \
  --region $SOURCE_REGION \
  --filters "Key=InstanceIds,Values=$(IFS=,; echo "${INSTANCES[*]}")" \
  --query 'InstanceInformationList[*].[InstanceId,PingStatus,PlatformType,PlatformName,AgentVersion,LastPingDateTime]' \
  --output table

echo ""
echo "Proceeding with DRS agent installation..."

# Step 3: Install DRS agents using SSM document
echo ""
echo "[3/4] Installing DRS agents via SSM Run Command..."
echo "Document: AWSDisasterRecovery-InstallDRAgentOnInstance"
echo "Target Region for Replication: $TARGET_REGION"
echo ""

COMMAND_ID=$(AWS_PAGER="" aws ssm send-command \
  --region $SOURCE_REGION \
  --document-name "AWSDisasterRecovery-InstallDRAgentOnInstance" \
  --instance-ids "${INSTANCES[@]}" \
  --parameters "Region=$TARGET_REGION" \
  --comment "Install DRS agent for replication to us-west-2" \
  --query 'Command.CommandId' \
  --output text)

echo "Command ID: $COMMAND_ID"
echo ""
echo "Waiting for command execution (this may take 5-10 minutes)..."
echo ""

# Monitor command execution
MAX_WAIT=600  # 10 minutes
WAIT_INTERVAL=20
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
  STATUS=$(AWS_PAGER="" aws ssm list-command-invocations \
    --region $SOURCE_REGION \
    --command-id $COMMAND_ID \
    --details \
    --query 'CommandInvocations[*].[InstanceId,Status]' \
    --output text)
  
  SUCCESS_COUNT=$(echo "$STATUS" | grep -c "Success" || true)
  IN_PROGRESS_COUNT=$(echo "$STATUS" | grep -c "InProgress" || true)
  FAILED_COUNT=$(echo "$STATUS" | grep -c "Failed" || true)
  
  echo "[$ELAPSED seconds] Success: $SUCCESS_COUNT | In Progress: $IN_PROGRESS_COUNT | Failed: $FAILED_COUNT"
  
  if [ "$SUCCESS_COUNT" -eq "${#INSTANCES[@]}" ]; then
    echo ""
    echo "✅ All DRS agents installed successfully!"
    break
  fi
  
  if [ "$FAILED_COUNT" -gt 0 ] && [ "$IN_PROGRESS_COUNT" -eq 0 ]; then
    echo ""
    echo "❌ Some installations failed. Check details below."
    break
  fi
  
  sleep $WAIT_INTERVAL
  ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

# Show detailed command results
echo ""
echo "Command Execution Results:"
AWS_PAGER="" aws ssm list-command-invocations \
  --region $SOURCE_REGION \
  --command-id $COMMAND_ID \
  --query 'CommandInvocations[*].[InstanceId,Status,StatusDetails]' \
  --output table

# Step 4: Verify DRS source servers
echo ""
echo "[4/4] Verifying DRS source servers in $TARGET_REGION..."
echo "Waiting 30 seconds for DRS to register source servers..."
sleep 30

echo ""
echo "DRS Source Servers:"
AWS_PAGER="" aws drs describe-source-servers \
  --region $TARGET_REGION \
  --query 'items[*].[sourceServerID,arn,tags.Name,dataReplicationInfo.dataReplicationState,lastLaunchResult]' \
  --output table 2>/dev/null || echo "No source servers found yet. May take a few minutes to appear."

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Monitor DRS console: https://$TARGET_REGION.console.aws.amazon.com/drs/home?region=$TARGET_REGION#/sourceServers"
echo "2. Wait for data replication to complete (Initial Sync)"
echo "3. Configure launch settings for each source server"
echo "4. Test recovery when ready"
echo ""
echo "To check command output for a specific instance:"
echo "  aws ssm get-command-invocation --region $SOURCE_REGION --command-id $COMMAND_ID --instance-id <instance-id>"
echo ""
