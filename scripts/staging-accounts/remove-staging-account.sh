#!/bin/bash

# Remove Staging Account Script
# 
# Removes a staging account from a target account configuration.
# 
# Usage:
#   ./scripts/staging-accounts/remove-staging-account.sh <target-account-id> <staging-account-id>
# 
# Example:
#   ./scripts/staging-accounts/remove-staging-account.sh 111122223333 444455556666

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_info() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

# Check arguments
if [ $# -lt 2 ]; then
    print_error "Missing required arguments"
    echo ""
    echo "Usage: $0 <target-account-id> <staging-account-id>"
    echo ""
    echo "Arguments:"
    echo "  target-account-id      - Target account ID (12 digits)"
    echo "  staging-account-id     - Staging account ID to remove (12 digits)"
    echo ""
    echo "Example:"
    echo "  $0 111122223333 444455556666"
    exit 1
fi

TARGET_ACCOUNT_ID="$1"
STAGING_ACCOUNT_ID="$2"

# Validate account IDs
if ! [[ "$TARGET_ACCOUNT_ID" =~ ^[0-9]{12}$ ]]; then
    print_error "Target account ID must be 12 digits"
    exit 1
fi

if ! [[ "$STAGING_ACCOUNT_ID" =~ ^[0-9]{12}$ ]]; then
    print_error "Staging account ID must be 12 digits"
    exit 1
fi

# Get environment from AWS config or default to 'test'
ENVIRONMENT="${AWS_ENVIRONMENT:-test}"

# Get Lambda function name
LAMBDA_FUNCTION="aws-drs-orchestration-data-management-${ENVIRONMENT}"

print_info "Removing staging account from target account..."
print_info "Target Account: ${TARGET_ACCOUNT_ID}"
print_info "Staging Account: ${STAGING_ACCOUNT_ID}"
print_info "Environment: ${ENVIRONMENT}"
echo ""

# Confirmation prompt
read -p "Are you sure you want to remove this staging account? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    print_info "Operation cancelled"
    exit 0
fi

# Create payload
PAYLOAD=$(cat <<EOF
{
  "operation": "remove_staging_account",
  "targetAccountId": "${TARGET_ACCOUNT_ID}",
  "stagingAccountId": "${STAGING_ACCOUNT_ID}"
}
EOF
)

# Invoke Lambda function
print_info "Invoking Lambda function: ${LAMBDA_FUNCTION}"

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
SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false')
MESSAGE=$(echo "$RESPONSE" | jq -r '.message // "No message"')

if [ "$SUCCESS" = "true" ]; then
    print_success "$MESSAGE"
    echo ""
    print_info "Staging account removed successfully!"
    
    # Display remaining staging accounts
    STAGING_ACCOUNTS=$(echo "$RESPONSE" | jq -r '.stagingAccounts // []')
    if [ "$STAGING_ACCOUNTS" != "[]" ] && [ "$STAGING_ACCOUNTS" != "null" ]; then
        echo ""
        print_info "Remaining staging accounts:"
        echo "$STAGING_ACCOUNTS" | jq -r '.[] | "  - \(.accountName) (\(.accountId))"'
    else
        echo ""
        print_info "No staging accounts remaining"
    fi
    
    exit 0
else
    print_error "$MESSAGE"
    exit 1
fi
