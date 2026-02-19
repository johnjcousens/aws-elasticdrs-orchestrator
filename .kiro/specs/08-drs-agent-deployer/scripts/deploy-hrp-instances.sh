#!/bin/bash

#
# Deploy DRS Agents to HRP Instances
#
# This script handles the split deployment strategy for HRP environment:
# - 01/02 instances: Same-account replication (160885257264 → 160885257264)
# - 03/04 instances: Cross-account replication (160885257264 → 891376951562)
#

set -e

# Colors
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_SCRIPT="${SCRIPT_DIR}/deploy-drs-agent-cross-account.sh"

# Configuration
SOURCE_ACCOUNT="160885257264"
SAME_ACCOUNT_TARGET="160885257264"  # 01/02 replicate to same account
CROSS_ACCOUNT_TARGET="891376951562"  # 03/04 replicate to staging account
REGION="us-east-1"
S3_BUCKET="drs-agent-deployment-160885257264"  # Bucket in source account for scripts

# HRP Instance IDs - 01/02 (same-account replication)
WEB_01_02="i-0e83af354a1f3dbcf,i-0a0854092c66d6095"  # hrp-core-web01, hrp-core-web02
APP_01_02="i-050614a07419695c3,i-028a51b7240556e12"  # hrp-core-app01, hrp-core-app02
DB_01_02="i-0296c7a2e1f74188b,i-0b748e7b59bbd9687"   # hrp-core-db01, hrp-core-db02

# HRP Instance IDs - 03/04 (cross-account replication)
WEB_03_04="i-00c5c7b3cf6d8abeb,i-04d81abd203126050"
APP_03_04="i-0b5fcf61e94e9f599,i-0b40c1c713cfdeac8"
DB_03_04="i-0d780c0fa44ba72e9,i-0117a71b9b09d45f7"

echo -e "${CYAN}=== HRP DRS Agent Deployment ===${NC}"
echo -e "${BLUE}Source Account:${NC} $SOURCE_ACCOUNT"
echo -e "${BLUE}Region:${NC} $REGION"
echo ""
echo -e "${YELLOW}Deployment Strategy:${NC}"
echo -e "  01/02 instances → Same-account ($SAME_ACCOUNT_TARGET)"
echo -e "  03/04 instances → Cross-account ($CROSS_ACCOUNT_TARGET)"
echo ""

# Parse command line argument
case "${1:-all}" in
    web-01-02)
        echo -e "${YELLOW}Deploying to WEB 01/02 instances (same-account)${NC}"
        INSTANCES="$WEB_01_02"
        TARGET="$SAME_ACCOUNT_TARGET"
        ;;
    web-03-04)
        echo -e "${YELLOW}Deploying to WEB 03/04 instances (cross-account)${NC}"
        INSTANCES="$WEB_03_04"
        TARGET="$CROSS_ACCOUNT_TARGET"
        ;;
    app-01-02)
        echo -e "${YELLOW}Deploying to APP 01/02 instances (same-account)${NC}"
        INSTANCES="$APP_01_02"
        TARGET="$SAME_ACCOUNT_TARGET"
        ;;
    app-03-04)
        echo -e "${YELLOW}Deploying to APP 03/04 instances (cross-account)${NC}"
        INSTANCES="$APP_03_04"
        TARGET="$CROSS_ACCOUNT_TARGET"
        ;;
    db-01-02)
        echo -e "${YELLOW}Deploying to DB 01/02 instances (same-account)${NC}"
        INSTANCES="$DB_01_02"
        TARGET="$SAME_ACCOUNT_TARGET"
        ;;
    db-03-04)
        echo -e "${YELLOW}Deploying to DB 03/04 instances (cross-account)${NC}"
        INSTANCES="$DB_03_04"
        TARGET="$CROSS_ACCOUNT_TARGET"
        ;;
    all-01-02)
        echo -e "${YELLOW}Deploying to ALL 01/02 instances (same-account)${NC}"
        echo -e "${GREEN}Step 1/3: Deploying WEB 01/02...${NC}"
        "$DEPLOY_SCRIPT" \
            --instance-ids "$WEB_01_02" \
            --region "$REGION"
        
        echo -e "\n${GREEN}Step 2/3: Deploying APP 01/02...${NC}"
        "$DEPLOY_SCRIPT" \
            --instance-ids "$APP_01_02" \
            --region "$REGION"
        
        echo -e "\n${GREEN}Step 3/3: Deploying DB 01/02...${NC}"
        "$DEPLOY_SCRIPT" \
            --instance-ids "$DB_01_02" \
            --region "$REGION"
        
        echo -e "\n${GREEN}✓ All 01/02 instances deployed (same-account)${NC}"
        exit 0
        ;;
    all-03-04)
        echo -e "${YELLOW}Deploying to ALL 03/04 instances (cross-account)${NC}"
        echo -e "${GREEN}Step 1/3: Deploying WEB 03/04...${NC}"
        "$DEPLOY_SCRIPT" \
            --instance-ids "$WEB_03_04" \
            --account-id "$CROSS_ACCOUNT_TARGET" \
            --region "$REGION"
        
        echo -e "\n${GREEN}Step 2/3: Deploying APP 03/04...${NC}"
        "$DEPLOY_SCRIPT" \
            --instance-ids "$APP_03_04" \
            --account-id "$CROSS_ACCOUNT_TARGET" \
            --region "$REGION"
        
        echo -e "\n${GREEN}Step 3/3: Deploying DB 03/04...${NC}"
        "$DEPLOY_SCRIPT" \
            --instance-ids "$DB_03_04" \
            --account-id "$CROSS_ACCOUNT_TARGET" \
            --region "$REGION"
        
        echo -e "\n${GREEN}✓ All 03/04 instances deployed (cross-account)${NC}"
        exit 0
        ;;
    all)
        echo -e "${YELLOW}Deploying to ALL instances (mixed strategy)${NC}"
        echo ""
        echo -e "${CYAN}=== Phase 1: Same-Account (01/02) ===${NC}"
        $0 all-01-02
        
        echo ""
        echo -e "${CYAN}=== Phase 2: Cross-Account (03/04) ===${NC}"
        $0 all-03-04
        
        echo -e "\n${GREEN}✓ All instances deployed${NC}"
        exit 0
        ;;
    *)
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  ${GREEN}Same-Account Replication (01/02 → 160885257264):${NC}"
        echo "    web-01-02    - Deploy to web servers 01/02"
        echo "    app-01-02    - Deploy to app servers 01/02"
        echo "    db-01-02     - Deploy to database servers 01/02"
        echo "    all-01-02    - Deploy to all 01/02 servers"
        echo ""
        echo "  ${YELLOW}Cross-Account Replication (03/04 → 891376951562):${NC}"
        echo "    web-03-04    - Deploy to web servers 03/04"
        echo "    app-03-04    - Deploy to app servers 03/04"
        echo "    db-03-04     - Deploy to database servers 03/04"
        echo "    all-03-04    - Deploy to all 03/04 servers"
        echo ""
        echo "  ${CYAN}Combined:${NC}"
        echo "    all          - Deploy to all servers (both strategies)"
        exit 1
        ;;
esac

echo ""

# Execute deployment for single tier
if [ "$TARGET" = "$SAME_ACCOUNT_TARGET" ]; then
    echo -e "${GREEN}Same-account replication (no --account-id parameter)${NC}"
    "$DEPLOY_SCRIPT" \
        --instance-ids "$INSTANCES" \
        --region "$REGION"
else
    echo -e "${YELLOW}Cross-account replication to $TARGET${NC}"
    "$DEPLOY_SCRIPT" \
        --instance-ids "$INSTANCES" \
        --account-id "$TARGET" \
        --region "$REGION"
fi
