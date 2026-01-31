#!/bin/bash

# Add Staging Account Script
# 
# Adds a staging account to a target account configuration.
# 
# Usage:
#   ./scripts/staging-accounts/add-staging-account.sh <target-account-id> <staging-account-id> <staging-account-name> <role-arn> <external-id>
# 
# Example:
#   ./scripts/staging-accounts/add-staging-account.sh 111122223333 444455556666 STAGING_01 \
#     arn:aws:iam::444455556666:role/DRSOrchestrationRole-test \
#     drs-orchestration-test-444455556666

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

# Check arguments
if [ $# -lt 5 ]; then
    print_error "Missing required arguments"
    echo ""
    echo "Usage: $0 <target-account-id> <staging-account-id> <staging-account-name> <role-arn> <external-id>"
    echo ""
    echo "Arguments:"
    echo "  target-account-id      - Target account ID (12 digits)"
    echo "  staging-account-id     - Staging account ID to add (12 digits)"
    echo "  staging-account-name   - Friendly name for staging account"
    echo "  role-arn              - IAM role ARN in staging account"
    echo "  external-id           - External ID for role assumption"
    echo ""
    echo "Example:"
    echo "  $0 111122223333 444455556666 STAGING_01 \\"
    echo "    arn:aws:iam::444455556666:role/DRSOrchestrationRole-test \\"
    echo "    drs-orchestration-test-444455556666"
    exit 1
fi

TARGET_ACCOUNT_ID="$1"
STAGING_ACCOUNT_ID="$2"
STAGING_ACCOUNT_NAME="$3"
ROLE_ARN="$4"
EXTERNAL_ID="$5"

# Validate account IDs
if ! [[ "$TARGET_ACCOUNT_ID" =~ ^[0-9]{12}$ ]]; then
    print_error "Target account ID must be 12 digits"
    exit 1
fi

if ! [[ "$STAGING_ACCOUNT_ID" =~ ^[0-9]{12}$ ]]; then
    print_error "Staging account ID must be 12 digits"
    exit 1
fi

# Validate role ARN format
if ! [[ "$ROLE_ARN" =~ ^arn:aws:iam::[0-9]{12}:role/.+ ]]; then
    print_error "Invalid role ARN format"
    exit 1
fi

# Get environment from AWS config or default to 'test'
ENVIRONMENT="${AWS_ENVIRONMENT:-test}"

# Get Lambda function name
LAMBDA_FUNCTION="aws-drs-orchestration-data-management-${ENVIRONMENT}"

print_info "Adding staging account to target account..."
print_info "Target Account: ${TARGET_ACCOUNT_ID}"
print_info "Staging Account: ${STAGING_ACCOUNT_ID} (${STAGING_ACCOUNT_NAME})"
print_info "Role ARN: ${ROLE_ARN}"
print_info "Environment: ${ENVIRONMENT}"
echo ""

# Create payload
PAYLOAD=$(cat <<EOF
{
  "operation": "add_staging_account",
  "targetAccountId": "${TARGET_ACCOUNT_ID}",
  "stagingAccount": {
    "accountId": "${STAGING_ACCOUNT_ID}",
    "accountName": "${STAGING_ACCOUNT_NAME}",
    "roleArn": "${ROLE_ARN}",
    "externalId": "${EXTERNAL_ID}"
  }
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
    print_info "Staging account added successfully!"
    
    # Display staging accounts list
    STAGING_ACCOUNTS=$(echo "$RESPONSE" | jq -r '.stagingAccounts // []')
    if [ "$STAGING_ACCOUNTS" != "[]" ]; then
        echo ""
        print_info "Current staging accounts:"
        echo "$STAGING_ACCOUNTS" | jq -r '.[] | "  - \(.accountName) (\(.accountId))"'
    fi
    
    exit 0
else
    print_error "$MESSAGE"
    exit 1
fi
