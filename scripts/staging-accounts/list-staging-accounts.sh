#!/bin/bash

# List Staging Accounts Script
# 
# Lists all staging accounts configured for a target account.
# 
# Usage:
#   ./scripts/staging-accounts/list-staging-accounts.sh <target-account-id>
# 
# Example:
#   ./scripts/staging-accounts/list-staging-accounts.sh 111122223333

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_info() {
    echo -e "${BLUE}INFO: $1${NC}"
}

# Check arguments
if [ $# -lt 1 ]; then
    print_error "Missing required argument"
    echo ""
    echo "Usage: $0 <target-account-id>"
    echo ""
    echo "Arguments:"
    echo "  target-account-id  - Target account ID (12 digits)"
    echo ""
    echo "Example:"
    echo "  $0 111122223333"
    exit 1
fi

TARGET_ACCOUNT_ID="$1"

# Validate account ID
if ! [[ "$TARGET_ACCOUNT_ID" =~ ^[0-9]{12}$ ]]; then
    print_error "Target account ID must be 12 digits"
    exit 1
fi

# Get environment from AWS config or default to 'test'
ENVIRONMENT="${AWS_ENVIRONMENT:-test}"

# Get Lambda function name
LAMBDA_FUNCTION="aws-drs-orchestration-data-management-${ENVIRONMENT}"

print_info "Retrieving staging accounts for target account ${TARGET_ACCOUNT_ID}..."
print_info "Environment: ${ENVIRONMENT}"
echo ""

# Create payload
PAYLOAD=$(cat <<EOF
{
  "operation": "get_target_account",
  "accountId": "${TARGET_ACCOUNT_ID}"
}
EOF
)

# Invoke Lambda function
RESPONSE=$(AWS_PAGER="" aws lambda invoke \
    --function-name "${LAMBDA_FUNCTION}" \
    --payload "${PAYLOAD}" \
    --cli-binary-format raw-in-base64-out \
    /dev/stdout 2>&1)

# Check for errors
if echo "$RESPONSE" | grep -q '"errorMessage"'; then
    print_error "Lambda invocation failed"
    echo "$RESPONSE" | jq -r '.errorMessage // .error // .'
    exit 1
fi

# Parse response
ACCOUNT_NAME=$(echo "$RESPONSE" | jq -r '.accountName // "Unknown"')
STAGING_ACCOUNTS=$(echo "$RESPONSE" | jq -r '.stagingAccounts // []')

# Display results
echo "═══════════════════════════════════════════════════════════"
echo "              TARGET ACCOUNT INFORMATION"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Account ID:    ${TARGET_ACCOUNT_ID}"
echo "  Account Name:  ${ACCOUNT_NAME}"
echo ""

# Count staging accounts
STAGING_COUNT=$(echo "$STAGING_ACCOUNTS" | jq 'length')

if [ "$STAGING_COUNT" -eq 0 ]; then
    echo "─────────────────────────────────────────────────────────"
    echo "                  STAGING ACCOUNTS"
    echo "─────────────────────────────────────────────────────────"
    echo ""
    print_info "No staging accounts configured"
    echo ""
    echo "To add a staging account, use:"
    echo "  ./scripts/staging-accounts/add-staging-account.sh"
    echo ""
else
    echo "─────────────────────────────────────────────────────────"
    echo "            STAGING ACCOUNTS (${STAGING_COUNT})"
    echo "─────────────────────────────────────────────────────────"
    echo ""
    
    # Display each staging account
    echo "$STAGING_ACCOUNTS" | jq -r '.[] | 
        "  Account ID:    \(.accountId)\n" +
        "  Account Name:  \(.accountName)\n" +
        "  Role ARN:      \(.roleArn)\n" +
        "  External ID:   \(.externalId)\n" +
        "  ─────────────────────────────────────────────────────────\n"'
    
    echo ""
    print_success "Found ${STAGING_COUNT} staging account(s)"
    echo ""
fi

echo "═══════════════════════════════════════════════════════════"
echo ""

exit 0
