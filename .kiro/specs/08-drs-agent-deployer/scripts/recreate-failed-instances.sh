#!/bin/bash

#
# Recreate Failed Instances and Install DRS Agents
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
AMI="ami-043cc489b5239c3de"
INSTANCE_TYPE="t3.large"
SUBNET="subnet-0de127c19dc67593e"
SECURITY_GROUP="sg-021589d4447675144"
INSTANCE_PROFILE="demo-ec2-profile"
ACCOUNT_ID="123456789012"

# Instance configurations
declare -A INSTANCES=(
    ["i-04d81abd203126050"]="hrp-core-web04-az1"
    ["i-0b5fcf61e94e9f599"]="hrp-core-app03-az1"
    ["i-0b40c1c713cfdeac8"]="hrp-core-app04-az1"
)

echo -e "${CYAN}=== Recreating Failed Instances ===${NC}"
echo ""

# Step 1: Terminate old instances
echo -e "${YELLOW}Step 1: Terminating old instances...${NC}"

for instance_id in "${!INSTANCES[@]}"; do
    name="${INSTANCES[$instance_id]}"
    echo -e "${BLUE}Terminating $name ($instance_id)...${NC}"
    
    AWS_PAGER="" aws ec2 terminate-instances \
        --region "$REGION" \
        --instance-ids "$instance_id" \
        --output json > /dev/null
    
    echo -e "${GREEN}✓ Termination initiated${NC}"
done

echo ""
echo -e "${YELLOW}Waiting 60 seconds for terminations to complete...${NC}"
sleep 60

# Step 2: Create new instances
echo ""
echo -e "${YELLOW}Step 2: Creating new instances...${NC}"

declare -A NEW_INSTANCES

for instance_id in "${!INSTANCES[@]}"; do
    name="${INSTANCES[$instance_id]}"
    echo -e "${BLUE}Creating $name...${NC}"
    
    NEW_ID=$(AWS_PAGER="" aws ec2 run-instances \
        --region "$REGION" \
        --image-id "$AMI" \
        --instance-type "$INSTANCE_TYPE" \
        --subnet-id "$SUBNET" \
        --security-group-ids "$SECURITY_GROUP" \
        --iam-instance-profile "Name=$INSTANCE_PROFILE" \
        --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$name}]" \
        --query 'Instances[0].InstanceId' \
        --output text)
    
    NEW_INSTANCES[$name]=$NEW_ID
    echo -e "${GREEN}✓ Created: $NEW_ID${NC}"
done

echo ""
echo -e "${YELLOW}Waiting 120 seconds for instances to initialize...${NC}"
sleep 120

# Step 3: Wait for instances to be running
echo ""
echo -e "${YELLOW}Step 3: Waiting for instances to be running...${NC}"

for name in "${!NEW_INSTANCES[@]}"; do
    instance_id="${NEW_INSTANCES[$name]}"
    echo -e "${BLUE}Checking $name ($instance_id)...${NC}"
    
    AWS_PAGER="" aws ec2 wait instance-running \
        --region "$REGION" \
        --instance-ids "$instance_id"
    
    echo -e "${GREEN}✓ Running${NC}"
done

# Step 4: Wait for SSM to be ready
echo ""
echo -e "${YELLOW}Step 4: Waiting for SSM agent to be ready...${NC}"
echo -e "${YELLOW}This may take 3-5 minutes...${NC}"

for name in "${!NEW_INSTANCES[@]}"; do
    instance_id="${NEW_INSTANCES[$name]}"
    echo -e "${BLUE}Waiting for SSM on $name ($instance_id)...${NC}"
    
    for i in {1..60}; do
        STATUS=$(AWS_PAGER="" aws ssm describe-instance-information \
            --region "$REGION" \
            --filters "Key=InstanceIds,Values=$instance_id" \
            --query 'InstanceInformationList[0].PingStatus' \
            --output text 2>/dev/null || echo "Unknown")
        
        if [ "$STATUS" = "Online" ]; then
            echo -e "${GREEN}✓ SSM Online${NC}"
            break
        fi
        
        if [ $((i % 6)) -eq 0 ]; then
            echo -e "${YELLOW}Still waiting... ($i/60)${NC}"
        fi
        sleep 10
    done
done

# Step 5: Install DRS agents
echo ""
echo -e "${YELLOW}Step 5: Installing DRS agents with cross-account configuration...${NC}"

for name in "${!NEW_INSTANCES[@]}"; do
    instance_id="${NEW_INSTANCES[$name]}"
    echo -e "${BLUE}Installing on $name ($instance_id)...${NC}"
    
    CMD_ID=$(AWS_PAGER="" aws ssm send-command \
        --region "$REGION" \
        --document-name "DRS-InstallAgentCrossAccount" \
        --instance-ids "$instance_id" \
        --parameters "Region=$REGION,AccountId=$ACCOUNT_ID" \
        --timeout-seconds 600 \
        --query 'Command.CommandId' \
        --output text)
    
    echo -e "${GREEN}✓ Installation started: $CMD_ID${NC}"
    echo -e "${BLUE}Console:${NC} https://console.aws.amazon.com/systems-manager/run-command/$CMD_ID?region=$REGION"
done

# Summary
echo ""
echo -e "${GREEN}=== Recreation Complete ===${NC}"
echo ""
echo -e "${CYAN}New Instance IDs:${NC}"
for name in "${!NEW_INSTANCES[@]}"; do
    instance_id="${NEW_INSTANCES[$name]}"
    echo -e "  $name: ${GREEN}$instance_id${NC}"
done

echo ""
echo -e "${YELLOW}Note: DRS agent installation takes 5-10 minutes.${NC}"
echo -e "${YELLOW}Check DRS console in staging account (123456789012) for source servers.${NC}"
echo ""
echo -e "${BLUE}Monitor installations:${NC}"
echo -e "https://console.aws.amazon.com/systems-manager/run-command?region=$REGION"
