#!/bin/bash

#
# Deploy DRS Agents using Custom SSM Document
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
DOC_NAME="DRS-InstallAgentCrossAccount"
REGION="us-east-1"

# HRP Instance IDs
WEB_01_02="i-0e83af354a1f3dbcf,i-0a0854092c66d6095"
APP_01_02="i-050614a07419695c3,i-028a51b7240556e12"
DB_01_02="i-0296c7a2e1f74188b,i-0b748e7b59bbd9687"

WEB_03_04="i-00c5c7b3cf6d8abeb,i-04d81abd203126050"
APP_03_04="i-0b5fcf61e94e9f599,i-0b40c1c713cfdeac8"
DB_03_04="i-0d780c0fa44ba72e9,i-0117a71b9b09d45f7"

# Parse arguments
TIER="${1:-}"

if [ -z "$TIER" ]; then
    echo -e "${CYAN}=== HRP DRS Agent Deployment (SSM Document) ===${NC}"
    echo ""
    echo "Usage: $0 <tier>"
    echo ""
    echo "Options:"
    echo "  ${GREEN}Same-Account (01/02):${NC}"
    echo "    web-01-02    - Web servers 01/02"
    echo "    app-01-02    - App servers 01/02"
    echo "    db-01-02     - DB servers 01/02"
    echo "    all-01-02    - All 01/02 servers"
    echo ""
    echo "  ${YELLOW}Cross-Account (03/04):${NC}"
    echo "    web-03-04    - Web servers 03/04"
    echo "    app-03-04    - App servers 03/04"
    echo "    db-03-04     - DB servers 03/04"
    echo "    all-03-04    - All 03/04 servers"
    echo ""
    echo "  ${CYAN}Combined:${NC}"
    echo "    all          - All servers"
    exit 1
fi

# Function to deploy
deploy() {
    local INSTANCES="$1"
    local ACCOUNT_ID="$2"
    local LABEL="$3"
    
    IFS=',' read -ra INSTANCE_ARRAY <<< "$INSTANCES"
    
    echo -e "\n${CYAN}Deploying: $LABEL${NC}"
    echo -e "${BLUE}Instances:${NC} ${#INSTANCE_ARRAY[@]}"
    
    if [ -n "$ACCOUNT_ID" ]; then
        echo -e "${YELLOW}Cross-Account:${NC} $ACCOUNT_ID"
        PARAMS="Region=$REGION,AccountId=$ACCOUNT_ID"
    else
        echo -e "${GREEN}Same-Account${NC}"
        PARAMS="Region=$REGION"
    fi
    
    # Send command
    COMMAND_ID=$(AWS_PAGER="" aws ssm send-command \
        --region "$REGION" \
        --document-name "$DOC_NAME" \
        --instance-ids "${INSTANCE_ARRAY[@]}" \
        --parameters "$PARAMS" \
        --timeout-seconds 600 \
        --query 'Command.CommandId' \
        --output text)
    
    echo -e "${GREEN}✓ Command sent: $COMMAND_ID${NC}"
    echo -e "${BLUE}Console:${NC} https://console.aws.amazon.com/systems-manager/run-command/$COMMAND_ID?region=$REGION"
}

# Execute based on tier
case "$TIER" in
    web-01-02)
        deploy "$WEB_01_02" "" "Web 01/02 (Same-Account)"
        ;;
    web-03-04)
        deploy "$WEB_03_04" "891376951562" "Web 03/04 (Cross-Account)"
        ;;
    app-01-02)
        deploy "$APP_01_02" "" "App 01/02 (Same-Account)"
        ;;
    app-03-04)
        deploy "$APP_03_04" "891376951562" "App 03/04 (Cross-Account)"
        ;;
    db-01-02)
        deploy "$DB_01_02" "" "DB 01/02 (Same-Account)"
        ;;
    db-03-04)
        deploy "$DB_03_04" "891376951562" "DB 03/04 (Cross-Account)"
        ;;
    all-01-02)
        deploy "$WEB_01_02" "" "Web 01/02 (Same-Account)"
        deploy "$APP_01_02" "" "App 01/02 (Same-Account)"
        deploy "$DB_01_02" "" "DB 01/02 (Same-Account)"
        ;;
    all-03-04)
        deploy "$WEB_03_04" "891376951562" "Web 03/04 (Cross-Account)"
        deploy "$APP_03_04" "891376951562" "App 03/04 (Cross-Account)"
        deploy "$DB_03_04" "891376951562" "DB 03/04 (Cross-Account)"
        ;;
    all)
        echo -e "${CYAN}=== Phase 1: Same-Account (01/02) ===${NC}"
        deploy "$WEB_01_02" "" "Web 01/02"
        deploy "$APP_01_02" "" "App 01/02"
        deploy "$DB_01_02" "" "DB 01/02"
        
        echo -e "\n${CYAN}=== Phase 2: Cross-Account (03/04) ===${NC}"
        deploy "$WEB_03_04" "891376951562" "Web 03/04"
        deploy "$APP_03_04" "891376951562" "App 03/04"
        deploy "$DB_03_04" "891376951562" "DB 03/04"
        ;;
    *)
        echo -e "${RED}Unknown tier: $TIER${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}=== Complete ===${NC}"
echo -e "${BLUE}Monitor progress in SSM Console:${NC}"
echo -e "https://console.aws.amazon.com/systems-manager/run-command?region=$REGION"
