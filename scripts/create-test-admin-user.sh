#!/bin/bash
#
# Create Test Admin User
# Creates a test user in Cognito and adds them to the admin group
#
# Usage: ./scripts/create-test-admin-user.sh [email] [password]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
USER_POOL_ID="us-east-1_o9KaGhSlo"
ADMIN_GROUP="DRSOrchestrationAdmin"
DEFAULT_EMAIL="testadmin@example.com"
DEFAULT_PASSWORD="SecureTest2026#Admin"

# Parse arguments
EMAIL="${1:-$DEFAULT_EMAIL}"
PASSWORD="${2:-$DEFAULT_PASSWORD}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Creating Test Admin User${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "User Pool ID: $USER_POOL_ID"
echo "Email: $EMAIL"
echo "Admin Group: $ADMIN_GROUP"
echo ""

# Check if user already exists
echo -e "${BLUE}Checking if user exists...${NC}"
if aws cognito-idp admin-get-user \
    --user-pool-id "$USER_POOL_ID" \
    --username "$EMAIL" \
    --region us-east-1 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ User already exists${NC}"
    
    # Check if user is in admin group
    GROUPS=$(aws cognito-idp admin-list-groups-for-user \
        --user-pool-id "$USER_POOL_ID" \
        --username "$EMAIL" \
        --region us-east-1 \
        --query 'Groups[*].GroupName' \
        --output text)
    
    if echo "$GROUPS" | grep -q "$ADMIN_GROUP"; then
        echo -e "${GREEN}✓ User is already in admin group${NC}"
    else
        echo -e "${YELLOW}Adding user to admin group...${NC}"
        aws cognito-idp admin-add-user-to-group \
            --user-pool-id "$USER_POOL_ID" \
            --username "$EMAIL" \
            --group-name "$ADMIN_GROUP" \
            --region us-east-1
        echo -e "${GREEN}✓ User added to admin group${NC}"
    fi
else
    # Create user
    echo -e "${BLUE}Creating user...${NC}"
    aws cognito-idp admin-create-user \
        --user-pool-id "$USER_POOL_ID" \
        --username "$EMAIL" \
        --user-attributes Name=email,Value="$EMAIL" Name=email_verified,Value=true \
        --temporary-password "$PASSWORD" \
        --message-action SUPPRESS \
        --region us-east-1 > /dev/null
    echo -e "${GREEN}✓ User created${NC}"
    
    # Set permanent password
    echo -e "${BLUE}Setting permanent password...${NC}"
    aws cognito-idp admin-set-user-password \
        --user-pool-id "$USER_POOL_ID" \
        --username "$EMAIL" \
        --password "$PASSWORD" \
        --permanent \
        --region us-east-1 > /dev/null
    echo -e "${GREEN}✓ Password set${NC}"
    
    # Add to admin group
    echo -e "${BLUE}Adding user to admin group...${NC}"
    aws cognito-idp admin-add-user-to-group \
        --user-pool-id "$USER_POOL_ID" \
        --username "$EMAIL" \
        --group-name "$ADMIN_GROUP" \
        --region us-east-1 > /dev/null
    echo -e "${GREEN}✓ User added to admin group${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Test Admin User Ready${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Credentials:"
echo "  Email: $EMAIL"
echo "  Password: $PASSWORD"
echo "  Group: $ADMIN_GROUP"
echo ""
echo "Login URL: https://d1ksi7eif6291h.cloudfront.net"
echo "API Endpoint: https://g0ojnzzfh1.execute-api.us-east-1.amazonaws.com/dev"
echo ""
echo "Test the API:"
echo "  1. Get ID token:"
echo "     aws cognito-idp initiate-auth \\"
echo "       --auth-flow USER_PASSWORD_AUTH \\"
echo "       --client-id 4fg10r8u9ef9d2qcvj9ifainoq \\"
echo "       --auth-parameters USERNAME=$EMAIL,PASSWORD=$PASSWORD \\"
echo "       --region us-east-1 \\"
echo "       --query 'AuthenticationResult.IdToken' \\"
echo "       --output text"
echo ""
echo "  2. Test API (replace TOKEN with ID token):"
echo "     curl -H \"Authorization: Bearer TOKEN\" \\"
echo "       https://g0ojnzzfh1.execute-api.us-east-1.amazonaws.com/dev/health"
echo ""
