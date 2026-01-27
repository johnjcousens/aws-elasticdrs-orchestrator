#!/bin/bash
#
# Deployment Logging Wrapper
# Captures deployment logs for troubleshooting
#
# Usage:
#   ./scripts/log-deployment.sh <deployment-command>
#
# Example:
#   ./scripts/log-deployment.sh aws cloudformation deploy --stack-name aws-drs-orch-dev ...

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get log directory (use latest symlink or create new)
if [ -L "docs/logs/latest" ]; then
    DEPLOY_LOG_DIR="docs/logs/latest/deploy"
else
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    DEPLOY_LOG_DIR="docs/logs/runs/$TIMESTAMP/deploy"
fi

mkdir -p "$DEPLOY_LOG_DIR"

# Generate deployment ID
DEPLOY_ID="deploy_$(date +%Y%m%d_%H%M%S)"
DEPLOY_LOG="$DEPLOY_LOG_DIR/$DEPLOY_ID.log"
DEPLOY_META="$DEPLOY_LOG_DIR/$DEPLOY_ID-metadata.txt"

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  DEPLOYMENT LOGGING${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Deployment ID: $DEPLOY_ID"
echo "Log file: $DEPLOY_LOG"
echo ""

# Log deployment metadata
cat > "$DEPLOY_META" << EOF
Deployment Metadata
===================
Deployment ID: $DEPLOY_ID
Timestamp: $(date)
Command: $@
Git Branch: $(git branch --show-current 2>/dev/null || echo "unknown")
Git Commit: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
User: $(whoami)
Host: $(hostname)
Working Directory: $(pwd)

Environment Variables:
AWS_REGION: ${AWS_REGION:-not set}
AWS_PROFILE: ${AWS_PROFILE:-not set}
AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION:-not set}

EOF

# Execute deployment command and capture output
DEPLOY_START=$(date +%s)
echo -e "${BLUE}Executing deployment command...${NC}"
echo ""

if "$@" 2>&1 | tee "$DEPLOY_LOG"; then
    DEPLOY_END=$(date +%s)
    DEPLOY_DURATION=$((DEPLOY_END - DEPLOY_START))
    
    echo ""
    echo -e "${GREEN}✅ Deployment completed successfully (${DEPLOY_DURATION}s)${NC}"
    
    # Append success info to metadata
    cat >> "$DEPLOY_META" << EOF

Deployment Result
=================
Status: SUCCESS
Duration: ${DEPLOY_DURATION}s
Completed: $(date)

EOF
    
    # If CloudFormation deployment, capture stack outputs
    if [[ "$@" == *"cloudformation"* ]] && [[ "$@" == *"deploy"* ]]; then
        STACK_NAME=$(echo "$@" | grep -oP '(?<=--stack-name )\S+' || echo "unknown")
        if [ "$STACK_NAME" != "unknown" ]; then
            echo ""
            echo -e "${BLUE}Capturing CloudFormation stack outputs...${NC}"
            
            AWS_PAGER="" aws cloudformation describe-stacks \
                --stack-name "$STACK_NAME" \
                --query 'Stacks[0].Outputs' \
                --output table > "$DEPLOY_LOG_DIR/$DEPLOY_ID-stack-outputs.txt" 2>&1 || true
            
            AWS_PAGER="" aws cloudformation describe-stack-events \
                --stack-name "$STACK_NAME" \
                --max-items 50 \
                --output table > "$DEPLOY_LOG_DIR/$DEPLOY_ID-stack-events.txt" 2>&1 || true
            
            echo -e "${GREEN}✅ Stack outputs saved${NC}"
        fi
    fi
    
    exit 0
else
    DEPLOY_END=$(date +%s)
    DEPLOY_DURATION=$((DEPLOY_END - DEPLOY_START))
    
    echo ""
    echo -e "${RED}❌ Deployment failed (${DEPLOY_DURATION}s)${NC}"
    
    # Append failure info to metadata
    cat >> "$DEPLOY_META" << EOF

Deployment Result
=================
Status: FAILED
Duration: ${DEPLOY_DURATION}s
Failed: $(date)

Error Analysis
==============
$(tail -50 "$DEPLOY_LOG")

EOF
    
    # If CloudFormation deployment, capture failure details
    if [[ "$@" == *"cloudformation"* ]] && [[ "$@" == *"deploy"* ]]; then
        STACK_NAME=$(echo "$@" | grep -oP '(?<=--stack-name )\S+' || echo "unknown")
        if [ "$STACK_NAME" != "unknown" ]; then
            echo ""
            echo -e "${BLUE}Capturing CloudFormation failure details...${NC}"
            
            AWS_PAGER="" aws cloudformation describe-stack-events \
                --stack-name "$STACK_NAME" \
                --max-items 100 \
                --output table > "$DEPLOY_LOG_DIR/$DEPLOY_ID-failure-events.txt" 2>&1 || true
            
            # Get failed resources
            AWS_PAGER="" aws cloudformation describe-stack-resources \
                --stack-name "$STACK_NAME" \
                --output table > "$DEPLOY_LOG_DIR/$DEPLOY_ID-stack-resources.txt" 2>&1 || true
            
            echo -e "${YELLOW}⚠️  Failure details saved to: $DEPLOY_LOG_DIR${NC}"
        fi
    fi
    
    echo ""
    echo "📊 Deployment logs: $DEPLOY_LOG_DIR"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Review deployment log: cat $DEPLOY_LOG"
    echo "  2. Check metadata: cat $DEPLOY_META"
    if [[ "$@" == *"cloudformation"* ]]; then
        echo "  3. Review stack events: cat $DEPLOY_LOG_DIR/$DEPLOY_ID-failure-events.txt"
        echo "  4. Check stack resources: cat $DEPLOY_LOG_DIR/$DEPLOY_ID-stack-resources.txt"
    fi
    
    exit 1
fi
