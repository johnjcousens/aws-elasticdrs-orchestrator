#!/bin/bash

# AWS DRS Orchestration - Test User Creation Script
# Creates a dedicated Cognito test user for automated testing
# Usage: ./scripts/create-test-user.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load configuration from .env.test
if [ ! -f ".env.test" ]; then
    echo -e "${RED}Error: .env.test file not found${NC}"
    echo "Please create .env.test with required configuration"
    exit 1
fi

# Source environment variables
export $(grep -v '^#' .env.test | xargs)

echo -e "${GREEN}=== AWS DRS Orchestration Test User Creation ===${NC}"
echo ""

# Validate required variables
if [ -z "$COGNITO_USER_POOL_ID" ] || [ -z "$TEST_USER_USERNAME" ] || [ -z "$TEST_USER_PASSWORD" ] || [ -z "$TEST_USER_EMAIL" ]; then
    echo -e "${RED}Error: Missing required environment variables${NC}"
    echo "Required: COGNITO_USER_POOL_ID, TEST_USER_USERNAME, TEST_USER_PASSWORD, TEST_USER_EMAIL"
    exit 1
fi

echo "Configuration:"
echo "  User Pool ID: $COGNITO_USER_POOL_ID"
echo "  Username: $TEST_USER_USERNAME"
echo "  Email: $TEST_USER_EMAIL"
echo ""

# Check if user already exists
echo -e "${YELLOW}Checking if user already exists...${NC}"
if aws cognito-idp admin-get-user \
    --user-pool-id "$COGNITO_USER_POOL_ID" \
    --username "$TEST_USER_USERNAME" \
    --region "$COGNITO_REGION" 2>/dev/null; then
    
    echo -e "${YELLOW}User already exists. Do you want to delete and recreate? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deleting existing user...${NC}"
        aws cognito-idp admin-delete-user \
            --user-pool-id "$COGNITO_USER_POOL_ID" \
            --username "$TEST_USER_USERNAME" \
            --region "$COGNITO_REGION"
        echo -e "${GREEN}✓ User deleted${NC}"
    else
        echo -e "${YELLOW}Keeping existing user${NC}"
        exit 0
    fi
fi

# Create test user
echo -e "${YELLOW}Creating test user...${NC}"
aws cognito-idp admin-create-user \
    --user-pool-id "$COGNITO_USER_POOL_ID" \
    --username "$TEST_USER_USERNAME" \
    --user-attributes Name=email,Value="$TEST_USER_EMAIL" Name=email_verified,Value=true \
    --temporary-password "$TEST_USER_PASSWORD" \
    --message-action SUPPRESS \
    --region "$COGNITO_REGION"

echo -e "${GREEN}✓ User created${NC}"

# Set permanent password
echo -e "${YELLOW}Setting permanent password...${NC}"
aws cognito-idp admin-set-user-password \
    --user-pool-id "$COGNITO_USER_POOL_ID" \
    --username "$TEST_USER_USERNAME" \
    --password "$TEST_USER_PASSWORD" \
    --permanent \
    --region "$COGNITO_REGION"

echo -e "${GREEN}✓ Password set${NC}"

# Verify user creation
echo -e "${YELLOW}Verifying user...${NC}"
USER_STATUS=$(aws cognito-idp admin-get-user \
    --user-pool-id "$COGNITO_USER_POOL_ID" \
    --username "$TEST_USER_USERNAME" \
    --region "$COGNITO_REGION" \
    --query 'UserStatus' \
    --output text)

if [ "$USER_STATUS" == "CONFIRMED" ]; then
    echo -e "${GREEN}✓ User verified (Status: $USER_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠ User created but status is: $USER_STATUS${NC}"
fi

echo ""
echo -e "${GREEN}=== Test User Created Successfully ===${NC}"
echo ""
echo "Credentials for testing:"
echo "  Username: $TEST_USER_USERNAME"
echo "  Password: $TEST_USER_PASSWORD"
echo "  Email: $TEST_USER_EMAIL"
echo ""
echo -e "${YELLOW}Note: These credentials are stored in .env.test${NC}"
echo -e "${YELLOW}Do not commit .env.test to version control!${NC}"
echo ""
echo "Next steps:"
echo "  1. Run tests: npm run test:smoke"
echo "  2. Or manually test login at: $CLOUDFRONT_URL"
