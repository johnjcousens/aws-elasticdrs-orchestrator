#!/bin/bash

#
# Deploy DRS Agent to EC2 Instances via SSM
#
# This script uploads the PowerShell installer script to S3 and executes it
# on target EC2 instances using AWS Systems Manager (SSM) Run Command.
#
# Usage:
#   ./deploy-drs-agent-cross-account.sh [options]
#
# Options:
#   --instance-ids "id1,id2,id3"  Comma-separated list of instance IDs
#   --region REGION               AWS region (default: us-east-1)
#   --account-id ACCOUNT          Target account ID for cross-account replication
#   --s3-bucket BUCKET            S3 bucket for script storage (default: hrp-drs-tech-adapter-dev)
#   --dry-run                     Show what would be executed without running
#
# Examples:
#   # Install on specific instances with cross-account replication
#   ./deploy-drs-agent-cross-account.sh \
#     --instance-ids "i-00c5c7b3cf6d8abeb,i-04d81abd203126050" \
#     --account-id 891376951562
#
#   # Install on all HRP instances
#   ./deploy-drs-agent-cross-account.sh \
#     --instance-ids "i-00c5c7b3cf6d8abeb,i-04d81abd203126050,i-0b5fcf61e94e9f599,i-0b40c1c713cfdeac8,i-0d780c0fa44ba72e9,i-0117a71b9b09d45f7" \
#     --account-id 891376951562
#
#   # Use custom S3 bucket
#   ./deploy-drs-agent-cross-account.sh \
#     --instance-ids "i-00c5c7b3cf6d8abeb" \
#     --account-id 891376951562 \
#     --s3-bucket my-custom-bucket
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
REGION="us-east-1"
ACCOUNT_ID=""
INSTANCE_IDS=""
S3_BUCKET="drs-agent-deployment-160885257264"  # Default deployment bucket in source account
DRY_RUN=false
SCRIPT_NAME="install-drs-agent-cross-account.ps1"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/${SCRIPT_NAME}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --instance-ids)
            INSTANCE_IDS="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --account-id)
            ACCOUNT_ID="$2"
            shift 2
            ;;
        --s3-bucket)
            S3_BUCKET="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Validation
if [ -z "$INSTANCE_IDS" ]; then
    echo -e "${RED}Error: --instance-ids is required${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}Error: PowerShell script not found: $SCRIPT_PATH${NC}"
    exit 1
fi

# Convert comma-separated instance IDs to array
IFS=',' read -ra INSTANCE_ARRAY <<< "$INSTANCE_IDS"

echo -e "${CYAN}=== DRS Agent Deployment via SSM ===${NC}"
echo -e "${BLUE}Region:${NC} $REGION"
echo -e "${BLUE}S3 Bucket:${NC} $S3_BUCKET"
echo -e "${BLUE}Instance Count:${NC} ${#INSTANCE_ARRAY[@]}"
echo -e "${BLUE}Instance IDs:${NC}"
for instance in "${INSTANCE_ARRAY[@]}"; do
    echo -e "  - $instance"
done

if [ -n "$ACCOUNT_ID" ]; then
    echo -e "${YELLOW}Cross-Account Replication:${NC} Enabled (Target: $ACCOUNT_ID)"
else
    echo -e "${BLUE}Cross-Account Replication:${NC} Disabled (Local account)"
fi

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN MODE - No changes will be made${NC}"
fi

echo ""

# Step 1: Upload script to S3
echo -e "${CYAN}[1/4] Uploading PowerShell script to S3...${NC}"
S3_KEY="scripts/drs/${SCRIPT_NAME}"
S3_URL="s3://${S3_BUCKET}/${S3_KEY}"

if [ "$DRY_RUN" = false ]; then
    AWS_PAGER="" aws s3 cp "$SCRIPT_PATH" "$S3_URL" --region "$REGION"
    echo -e "${GREEN}✓ Uploaded to: $S3_URL${NC}"
else
    echo -e "${YELLOW}Would upload: $SCRIPT_PATH -> $S3_URL${NC}"
fi

# Step 2: Check SSM connectivity
echo -e "\n${CYAN}[2/4] Checking SSM connectivity...${NC}"
for instance in "${INSTANCE_ARRAY[@]}"; do
    if [ "$DRY_RUN" = false ]; then
        STATUS=$(AWS_PAGER="" aws ssm describe-instance-information \
            --region "$REGION" \
            --filters "Key=InstanceIds,Values=$instance" \
            --query 'InstanceInformationList[0].PingStatus' \
            --output text 2>/dev/null || echo "Unknown")
        
        if [ "$STATUS" = "Online" ]; then
            echo -e "${GREEN}✓ $instance: Online${NC}"
        else
            echo -e "${RED}✗ $instance: $STATUS${NC}"
        fi
    else
        echo -e "${YELLOW}Would check: $instance${NC}"
    fi
done

# Step 3: Build PowerShell command
echo -e "\n${CYAN}[3/4] Preparing SSM command...${NC}"

# Build PowerShell command as JSON array
if [ -n "$ACCOUNT_ID" ]; then
    ACCOUNT_PARAM="-AccountId '$ACCOUNT_ID'"
else
    ACCOUNT_PARAM=""
fi

# Create JSON file for SSM parameters with proper escaping
SSM_PARAMS_FILE=$(mktemp)
cat > "$SSM_PARAMS_FILE" << 'EOF'
{
  "commands": [
    "$ErrorActionPreference = 'Stop'",
    "$TempDir = 'C:\\Temp'",
    "if (-not (Test-Path $TempDir)) { New-Item -ItemType Directory -Path $TempDir -Force | Out-Null }",
    "Write-Host 'Downloading installation script from S3...'",
    "Read-S3Object -BucketName 'BUCKET_PLACEHOLDER' -Key 'KEY_PLACEHOLDER' -File \"$TempDir\\SCRIPT_PLACEHOLDER\" -Region 'REGION_PLACEHOLDER'",
    "Write-Host 'Executing installation script...'",
    "Set-Location $TempDir",
    ".\\SCRIPT_PLACEHOLDER -Region 'REGION_PLACEHOLDER' ACCOUNT_PLACEHOLDER -NoPrompt $true"
  ]
}
EOF

# Replace placeholders
sed -i.bak "s|BUCKET_PLACEHOLDER|$S3_BUCKET|g" "$SSM_PARAMS_FILE"
sed -i.bak "s|KEY_PLACEHOLDER|$S3_KEY|g" "$SSM_PARAMS_FILE"
sed -i.bak "s|SCRIPT_PLACEHOLDER|$SCRIPT_NAME|g" "$SSM_PARAMS_FILE"
sed -i.bak "s|REGION_PLACEHOLDER|$REGION|g" "$SSM_PARAMS_FILE"

if [ -n "$ACCOUNT_ID" ]; then
    sed -i.bak "s|ACCOUNT_PLACEHOLDER|-AccountId '$ACCOUNT_ID'|g" "$SSM_PARAMS_FILE"
else
    sed -i.bak "s|ACCOUNT_PLACEHOLDER||g" "$SSM_PARAMS_FILE"
fi

echo -e "${BLUE}PowerShell Commands:${NC}"
cat "$SSM_PARAMS_FILE" | jq -r '.commands[]' 2>/dev/null | sed 's/^/  /' || cat "$SSM_PARAMS_FILE"

# Step 4: Execute via SSM
echo -e "\n${CYAN}[4/4] Executing installation via SSM...${NC}"

if [ "$DRY_RUN" = false ]; then
    COMMAND_ID=$(AWS_PAGER="" aws ssm send-command \
        --region "$REGION" \
        --document-name "AWS-RunPowerShellScript" \
        --instance-ids "${INSTANCE_ARRAY[@]}" \
        --parameters file://"$SSM_PARAMS_FILE" \
        --timeout-seconds 600 \
        --query 'Command.CommandId' \
        --output text)
    
    # Cleanup temp files
    rm -f "$SSM_PARAMS_FILE" "${SSM_PARAMS_FILE}.bak"
    
    echo -e "${GREEN}✓ SSM Command initiated${NC}"
    echo -e "${BLUE}Command ID:${NC} $COMMAND_ID"
    
    # Wait for completion
    echo -e "\n${CYAN}Waiting for command to complete...${NC}"
    echo -e "${YELLOW}This may take 5-10 minutes...${NC}"
    
    for instance in "${INSTANCE_ARRAY[@]}"; do
        echo -e "\n${BLUE}Instance: $instance${NC}"
        
        # Poll for completion
        MAX_ATTEMPTS=60
        ATTEMPT=0
        while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
            STATUS=$(AWS_PAGER="" aws ssm get-command-invocation \
                --region "$REGION" \
                --command-id "$COMMAND_ID" \
                --instance-id "$instance" \
                --query 'Status' \
                --output text 2>/dev/null || echo "Pending")
            
            if [ "$STATUS" = "Success" ]; then
                echo -e "${GREEN}✓ Installation completed successfully${NC}"
                
                # Get output
                OUTPUT=$(AWS_PAGER="" aws ssm get-command-invocation \
                    --region "$REGION" \
                    --command-id "$COMMAND_ID" \
                    --instance-id "$instance" \
                    --query 'StandardOutputContent' \
                    --output text)
                
                echo -e "${BLUE}Output:${NC}"
                echo "$OUTPUT" | tail -20
                break
            elif [ "$STATUS" = "Failed" ]; then
                echo -e "${RED}✗ Installation failed${NC}"
                
                # Get error output
                ERROR=$(AWS_PAGER="" aws ssm get-command-invocation \
                    --region "$REGION" \
                    --command-id "$COMMAND_ID" \
                    --instance-id "$instance" \
                    --query 'StandardErrorContent' \
                    --output text)
                
                echo -e "${RED}Error:${NC}"
                echo "$ERROR"
                break
            elif [ "$STATUS" = "InProgress" ] || [ "$STATUS" = "Pending" ]; then
                echo -ne "${YELLOW}Status: $STATUS (attempt $((ATTEMPT+1))/$MAX_ATTEMPTS)${NC}\r"
                sleep 10
                ATTEMPT=$((ATTEMPT+1))
            else
                echo -e "${YELLOW}Status: $STATUS${NC}"
                sleep 10
                ATTEMPT=$((ATTEMPT+1))
            fi
        done
        
        if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
            echo -e "${RED}✗ Timeout waiting for installation${NC}"
        fi
    done
    
    echo -e "\n${CYAN}=== Deployment Complete ===${NC}"
    echo -e "${BLUE}View full logs in SSM Console:${NC}"
    echo -e "https://console.aws.amazon.com/systems-manager/run-command/$COMMAND_ID?region=$REGION"
    
else
    echo -e "${YELLOW}Would execute SSM command on ${#INSTANCE_ARRAY[@]} instances${NC}"
fi

# Next steps
echo -e "\n${CYAN}=== Next Steps ===${NC}"
if [ -n "$ACCOUNT_ID" ]; then
    echo -e "${BLUE}1. Verify source servers in target account:${NC}"
    echo -e "   aws drs describe-source-servers --region $REGION --profile target-account"
else
    echo -e "${BLUE}1. Verify source servers:${NC}"
    echo -e "   aws drs describe-source-servers --region $REGION"
fi
echo -e "${BLUE}2. Monitor replication progress in DRS console${NC}"
echo -e "${BLUE}3. Configure launch settings for recovery instances${NC}"
echo -e "${BLUE}4. Test with drill or recovery job${NC}"
