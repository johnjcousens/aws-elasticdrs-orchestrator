#!/bin/bash

#
# Monitor DRS Agent Deployment Progress
#

COMMAND_ID="${1:-}"
REGION="us-east-1"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ -z "$COMMAND_ID" ]; then
    echo -e "${CYAN}=== Recent SSM Commands ===${NC}"
    AWS_PAGER="" aws ssm list-commands \
        --region "$REGION" \
        --max-items 5 \
        --query 'Commands[*].[CommandId,Status,RequestedDateTime,Comment]' \
        --output table
    echo ""
    echo "Usage: $0 <command-id>"
    exit 1
fi

echo -e "${CYAN}=== Monitoring Command: $COMMAND_ID ===${NC}"
echo ""

# Get command details
AWS_PAGER="" aws ssm list-command-invocations \
    --command-id "$COMMAND_ID" \
    --region "$REGION" \
    --query 'CommandInvocations[*].[InstanceId,Status,StatusDetails]' \
    --output table

echo ""
echo -e "${BLUE}Detailed Status:${NC}"

# Get instance details
INSTANCES=$(AWS_PAGER="" aws ssm list-command-invocations \
    --command-id "$COMMAND_ID" \
    --region "$REGION" \
    --query 'CommandInvocations[*].InstanceId' \
    --output text)

for instance in $INSTANCES; do
    echo ""
    echo -e "${CYAN}Instance: $instance${NC}"
    
    STATUS=$(AWS_PAGER="" aws ssm get-command-invocation \
        --command-id "$COMMAND_ID" \
        --instance-id "$instance" \
        --region "$REGION" \
        --query 'Status' \
        --output text 2>/dev/null)
    
    if [ "$STATUS" = "Success" ]; then
        echo -e "${GREEN}✓ Success${NC}"
        
        # Show last 10 lines of output
        OUTPUT=$(AWS_PAGER="" aws ssm get-command-invocation \
            --command-id "$COMMAND_ID" \
            --instance-id "$instance" \
            --region "$REGION" \
            --query 'StandardOutputContent' \
            --output text 2>/dev/null)
        
        if [ -n "$OUTPUT" ]; then
            echo "$OUTPUT" | tail -10
        fi
        
    elif [ "$STATUS" = "Failed" ]; then
        echo -e "${RED}✗ Failed${NC}"
        
        # Show error
        ERROR=$(AWS_PAGER="" aws ssm get-command-invocation \
            --command-id "$COMMAND_ID" \
            --instance-id "$instance" \
            --region "$REGION" \
            --query 'StandardErrorContent' \
            --output text 2>/dev/null)
        
        if [ -n "$ERROR" ] && [ "$ERROR" != "None" ]; then
            echo -e "${RED}Error:${NC}"
            echo "$ERROR" | tail -20
        fi
        
        # Show output too
        OUTPUT=$(AWS_PAGER="" aws ssm get-command-invocation \
            --command-id "$COMMAND_ID" \
            --instance-id "$instance" \
            --region "$REGION" \
            --query 'StandardOutputContent' \
            --output text 2>/dev/null)
        
        if [ -n "$OUTPUT" ] && [ "$OUTPUT" != "None" ]; then
            echo -e "${YELLOW}Output:${NC}"
            echo "$OUTPUT" | tail -20
        fi
        
    elif [ "$STATUS" = "InProgress" ] || [ "$STATUS" = "Pending" ]; then
        echo -e "${YELLOW}⏳ $STATUS${NC}"
        echo "Installation in progress (typically takes 5-10 minutes)..."
    else
        echo -e "${YELLOW}Status: $STATUS${NC}"
    fi
done

echo ""
echo -e "${BLUE}Console:${NC} https://console.aws.amazon.com/systems-manager/run-command/$COMMAND_ID?region=$REGION"
