#!/bin/bash

#
# Deploy Custom SSM Document for DRS Agent Installation with Cross-Account Support
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOC_FILE="${SCRIPT_DIR}/../ssm-documents/DRS-InstallAgentCrossAccount.yaml"
DOC_NAME="DRS-InstallAgentCrossAccount"
REGION="us-east-1"

echo -e "${CYAN}=== Deploy SSM Document ===${NC}"
echo -e "${BLUE}Document:${NC} $DOC_NAME"
echo -e "${BLUE}Region:${NC} $REGION"
echo ""

# Check if document exists
echo -e "${CYAN}[1/2] Checking if document exists...${NC}"
if AWS_PAGER="" aws ssm describe-document --name "$DOC_NAME" --region "$REGION" &>/dev/null; then
    echo -e "${YELLOW}Document exists - updating...${NC}"
    
    # Update document
    AWS_PAGER="" aws ssm update-document \
        --name "$DOC_NAME" \
        --content "file://$DOC_FILE" \
        --document-version '$LATEST' \
        --document-format YAML \
        --region "$REGION"
    
    # Set as default version
    LATEST_VERSION=$(AWS_PAGER="" aws ssm describe-document \
        --name "$DOC_NAME" \
        --region "$REGION" \
        --query 'Document.LatestVersion' \
        --output text)
    
    AWS_PAGER="" aws ssm update-document-default-version \
        --name "$DOC_NAME" \
        --document-version "$LATEST_VERSION" \
        --region "$REGION"
    
    echo -e "${GREEN}✓ Document updated (version $LATEST_VERSION)${NC}"
else
    echo -e "${YELLOW}Document does not exist - creating...${NC}"
    
    # Create document
    AWS_PAGER="" aws ssm create-document \
        --name "$DOC_NAME" \
        --content "file://$DOC_FILE" \
        --document-type "Command" \
        --document-format YAML \
        --region "$REGION"
    
    echo -e "${GREEN}✓ Document created${NC}"
fi

# Show document info
echo -e "\n${CYAN}[2/2] Document details:${NC}"
AWS_PAGER="" aws ssm describe-document \
    --name "$DOC_NAME" \
    --region "$REGION" \
    --query 'Document.{Name:Name,Version:LatestVersion,Status:Status,Owner:Owner}' \
    --output table

echo -e "\n${GREEN}=== Complete ===${NC}"
echo -e "${BLUE}Document Name:${NC} $DOC_NAME"
echo -e "${BLUE}Usage:${NC}"
echo -e "  # Same-account replication"
echo -e "  aws ssm send-command --document-name $DOC_NAME \\"
echo -e "    --instance-ids i-xxxxx \\"
echo -e "    --parameters Region=us-east-1"
echo ""
echo -e "  # Cross-account replication"
echo -e "  aws ssm send-command --document-name $DOC_NAME \\"
echo -e "    --instance-ids i-xxxxx \\"
echo -e "    --parameters Region=us-east-1,AccountId=891376951562"
