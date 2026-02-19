#!/bin/bash

#
# Uninstall existing DRS agent and reinstall with cross-account configuration
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

REGION="us-east-1"
ACCOUNT_ID="123456789012"

# Failed instances
INSTANCES=(
    "i-04d81abd203126050"  # hrp-core-web04
    "i-0b5fcf61e94e9f599"  # hrp-core-app03
    "i-0b40c1c713cfdeac8"  # hrp-core-app04
)

echo -e "${CYAN}=== Uninstalling and Reinstalling DRS Agents ===${NC}"
echo ""

# Step 1: Uninstall existing agents
echo -e "${YELLOW}Step 1: Uninstalling existing DRS agents...${NC}"

UNINSTALL_SCRIPT='
$ErrorActionPreference = "Continue"

# Check if DRS agent is installed
$uninstallPath = "C:\\Program Files\\AWS Replication Agent\\uninstall.exe"
if (Test-Path $uninstallPath) {
    Write-Host "Found DRS agent, uninstalling..."
    Start-Process -FilePath $uninstallPath -ArgumentList "/S" -Wait -NoNewWindow
    Write-Host "Uninstall complete"
    
    # Wait for uninstall to complete
    Start-Sleep -Seconds 10
    
    # Clean up any remaining files
    $agentPath = "C:\\Program Files\\AWS Replication Agent"
    if (Test-Path $agentPath) {
        Write-Host "Removing remaining files..."
        Remove-Item -Path $agentPath -Recurse -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "No DRS agent found, skipping uninstall"
}

# Clean up temp files
Remove-Item -Path "C:\\Temp\\AwsReplication*" -Force -ErrorAction SilentlyContinue

Write-Host "Cleanup complete"
'

for instance in "${INSTANCES[@]}"; do
    echo -e "${BLUE}Uninstalling on $instance...${NC}"
    
    UNINSTALL_CMD=$(AWS_PAGER="" aws ssm send-command \
        --region "$REGION" \
        --document-name "AWS-RunPowerShellScript" \
        --instance-ids "$instance" \
        --parameters "commands=[\"$UNINSTALL_SCRIPT\"]" \
        --timeout-seconds 300 \
        --query 'Command.CommandId' \
        --output text)
    
    echo -e "${GREEN}✓ Uninstall command sent: $UNINSTALL_CMD${NC}"
done

echo ""
echo -e "${YELLOW}Waiting 60 seconds for uninstalls to complete...${NC}"
sleep 60

# Step 2: Reboot instances
echo ""
echo -e "${YELLOW}Step 2: Rebooting instances...${NC}"

for instance in "${INSTANCES[@]}"; do
    echo -e "${BLUE}Rebooting $instance...${NC}"
    
    AWS_PAGER="" aws ec2 reboot-instances \
        --region "$REGION" \
        --instance-ids "$instance"
    
    echo -e "${GREEN}✓ Reboot initiated${NC}"
done

echo ""
echo -e "${YELLOW}Waiting 120 seconds for instances to reboot...${NC}"
sleep 120

# Step 3: Wait for SSM to be ready
echo ""
echo -e "${YELLOW}Step 3: Waiting for SSM to be ready...${NC}"

for instance in "${INSTANCES[@]}"; do
    echo -e "${BLUE}Checking SSM status for $instance...${NC}"
    
    for i in {1..30}; do
        STATUS=$(AWS_PAGER="" aws ssm describe-instance-information \
            --region "$REGION" \
            --filters "Key=InstanceIds,Values=$instance" \
            --query 'InstanceInformationList[0].PingStatus' \
            --output text 2>/dev/null || echo "Unknown")
        
        if [ "$STATUS" = "Online" ]; then
            echo -e "${GREEN}✓ SSM Online${NC}"
            break
        fi
        
        echo -e "${YELLOW}Waiting for SSM... ($i/30)${NC}"
        sleep 10
    done
done

# Step 4: Reinstall DRS agents
echo ""
echo -e "${YELLOW}Step 4: Reinstalling DRS agents with cross-account configuration...${NC}"

for instance in "${INSTANCES[@]}"; do
    echo -e "${BLUE}Installing on $instance...${NC}"
    
    INSTALL_CMD=$(AWS_PAGER="" aws ssm send-command \
        --region "$REGION" \
        --document-name "DRS-InstallAgentCrossAccount" \
        --instance-ids "$instance" \
        --parameters "Region=$REGION,AccountId=$ACCOUNT_ID" \
        --timeout-seconds 600 \
        --query 'Command.CommandId' \
        --output text)
    
    echo -e "${GREEN}✓ Install command sent: $INSTALL_CMD${NC}"
    echo -e "${BLUE}Console:${NC} https://console.aws.amazon.com/systems-manager/run-command/$INSTALL_CMD?region=$REGION"
done

echo ""
echo -e "${GREEN}=== Complete ===${NC}"
echo -e "${BLUE}Monitor installations in SSM Console:${NC}"
echo -e "https://console.aws.amazon.com/systems-manager/run-command?region=$REGION"
echo ""
echo -e "${YELLOW}Note: Installations take 5-10 minutes. Check DRS console for source servers.${NC}"
