#!/bin/bash

#
# Simple DRS Agent Deployment via SSM
#
# Usage: ./deploy-drs-agent-simple.sh <instance-ids> [account-id]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
REGION="us-east-1"
S3_BUCKET="drs-agent-deployment-160885257264"
SCRIPT_NAME="install-drs-agent-cross-account.ps1"
S3_KEY="scripts/drs/${SCRIPT_NAME}"

# Parse arguments
INSTANCE_IDS="$1"
ACCOUNT_ID="${2:-}"

if [ -z "$INSTANCE_IDS" ]; then
    echo -e "${RED}Usage: $0 <instance-ids> [account-id]${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 i-00c5c7b3cf6d8abeb,i-04d81abd203126050 891376951562"
    echo "  $0 i-00c5c7b3cf6d8abeb"
    exit 1
fi

# Convert to array
IFS=',' read -ra INSTANCE_ARRAY <<< "$INSTANCE_IDS"

echo -e "${CYAN}=== DRS Agent Deployment ===${NC}"
echo -e "${BLUE}Region:${NC} $REGION"
echo -e "${BLUE}Instances:${NC} ${#INSTANCE_ARRAY[@]}"
for instance in "${INSTANCE_ARRAY[@]}"; do
    echo -e "  - $instance"
done

if [ -n "$ACCOUNT_ID" ]; then
    echo -e "${YELLOW}Cross-Account:${NC} $ACCOUNT_ID"
else
    echo -e "${BLUE}Same-Account${NC}"
fi

echo ""

# Upload script to S3
echo -e "${CYAN}[1/3] Uploading script to S3...${NC}"
AWS_PAGER="" aws s3 cp "${SCRIPT_DIR}/${SCRIPT_NAME}" "s3://${S3_BUCKET}/${S3_KEY}" --region "$REGION"
echo -e "${GREEN}✓ Uploaded${NC}"

# Build PowerShell command
echo -e "\n${CYAN}[2/3] Sending SSM command...${NC}"

if [ -n "$ACCOUNT_ID" ]; then
    PS_CMD="Read-S3Object -BucketName '$S3_BUCKET' -Key '$S3_KEY' -File 'C:\\Temp\\$SCRIPT_NAME' -Region '$REGION'; C:\\Temp\\$SCRIPT_NAME -Region '$REGION' -AccountId '$ACCOUNT_ID' -NoPrompt \$true"
else
    PS_CMD="Read-S3Object -BucketName '$S3_BUCKET' -Key '$S3_KEY' -File 'C:\\Temp\\$SCRIPT_NAME' -Region '$REGION'; C:\\Temp\\$SCRIPT_NAME -Region '$REGION' -NoPrompt \$true"
fi

# Send command
COMMAND_ID=$(AWS_PAGER="" aws ssm send-command \
    --region "$REGION" \
    --document-name "AWS-RunPowerShellScript" \
    --instance-ids "${INSTANCE_ARRAY[@]}" \
    --parameters commands="$PS_CMD" \
    --timeout-seconds 600 \
    --query 'Command.CommandId' \
    --output text)

echo -e "${GREEN}✓ Command sent: $COMMAND_ID${NC}"

# Wait and monitor
echo -e "\n${CYAN}[3/3] Monitoring progress...${NC}"
echo -e "${YELLOW}This may take 5-10 minutes per instance${NC}"
echo ""

for instance in "${INSTANCE_ARRAY[@]}"; do
    echo -e "${BLUE}Instance: $instance${NC}"
    
    # Wait for completion
    MAX_WAIT=600  # 10 minutes
    ELAPSED=0
    
    while [ $ELAPSED -lt $MAX_WAIT ]; do
        STATUS=$(AWS_PAGER="" aws ssm get-command-invocation \
            --region "$REGION" \
            --command-id "$COMMAND_ID" \
            --instance-id "$instance" \
            --query 'Status' \
            --output text 2>/dev/null || echo "Pending")
        
        if [ "$STATUS" = "Success" ]; then
            echo -e "${GREEN}✓ Success${NC}"
            
            # Show last 10 lines of output
            OUTPUT=$(AWS_PAGER="" aws ssm get-command-invocation \
                --region "$REGION" \
                --command-id "$COMMAND_ID" \
                --instance-id "$instance" \
                --query 'StandardOutputContent' \
                --output text)
            
            echo "$OUTPUT" | tail -10
            break
            
        elif [ "$STATUS" = "Failed" ]; then
            echo -e "${RED}✗ Failed${NC}"
            
            # Show error
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
            echo -ne "${YELLOW}Status: $STATUS (${ELAPSED}s)${NC}\r"
            sleep 10
            ELAPSED=$((ELAPSED + 10))
        else
            echo -e "${YELLOW}Status: $STATUS${NC}"
            sleep 10
            ELAPSED=$((ELAPSED + 10))
        fi
    done
    
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo -e "${RED}✗ Timeout${NC}"
    fi
    
    echo ""
done

echo -e "${CYAN}=== Complete ===${NC}"
echo -e "${BLUE}Command ID:${NC} $COMMAND_ID"
echo -e "${BLUE}Console:${NC} https://console.aws.amazon.com/systems-manager/run-command/$COMMAND_ID?region=$REGION"
