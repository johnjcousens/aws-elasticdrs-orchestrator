#!/bin/bash

# Validate Staging Account Script
# 
# Validates staging account access and DRS initialization before adding.
# 
# Usage:
#   ./scripts/staging-accounts/validate-staging-account.sh <account-id> <role-arn> <external-id> [region]
# 
# Example:
#   ./scripts/staging-accounts/validate-staging-account.sh 444455556666 \
#     arn:aws:iam::444455556666:role/DRSOrchestrationRole-test \
#     drs-orchestration-test-444455556666 \
#     us-east-1

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✓ SUCCESS: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ INFO: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING: $1${NC}"
}

# Check arguments
if [ $# -lt 3 ]; then
    print_error "Missing required arguments"
    echo ""
    echo "Usage: $0 <account-id> <role-arn> <external-id> [region]"
    echo ""
    echo "Arguments:"
    echo "  account-id    - Staging account ID to validate (12 digits)"
    echo "  role-arn      - IAM role ARN in staging account"
    echo "  external-id   - External ID for role assumption"
    echo "  region        - AWS region (optional, default: us-east-1)"
    echo ""
    echo "Example:"
    echo "  $0 444455556666 \\"
    echo "    arn:aws:iam::444455556666:role/DRSOrchestrationRole-test \\"
    echo "    drs-orchestration-test-444455556666 \\"
    echo "    us-east-1"
    exit 1
fi

ACCOUNT_ID="$1"
ROLE_ARN="$2"
EXTERNAL_ID="$3"
REGION="${4:-us-east-1}"

# Validate account ID
if ! [[ "$ACCOUNT_ID" =~ ^[0-9]{12}$ ]]; then
    print_error "Account ID must be 12 digits"
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
LAMBDA_FUNCTION="aws-drs-orchestration-query-${ENVIRONMENT}"

echo ""
print_info "Validating staging account access..."
print_info "Account ID: ${ACCOUNT_ID}"
print_info "Role ARN: ${ROLE_ARN}"
print_info "Region: ${REGION}"
print_info "Environment: ${ENVIRONMENT}"
echo ""

# Create payload
PAYLOAD=$(cat <<EOF
{
  "operation": "validate_staging_account",
  "accountId": "${ACCOUNT_ID}",
  "roleArn": "${ROLE_ARN}",
  "externalId": "${EXTERNAL_ID}",
  "region": "${REGION}"
}
EOF
)

# Invoke Lambda function
print_info "Invoking Lambda function: ${LAMBDA_FUNCTION}"
echo ""

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
VALID=$(echo "$RESPONSE" | jq -r '.valid // false')
ROLE_ACCESSIBLE=$(echo "$RESPONSE" | jq -r '.roleAccessible // false')
DRS_INITIALIZED=$(echo "$RESPONSE" | jq -r '.drsInitialized // false')
CURRENT_SERVERS=$(echo "$RESPONSE" | jq -r '.currentServers // 0')
REPLICATING_SERVERS=$(echo "$RESPONSE" | jq -r '.replicatingServers // 0')
TOTAL_AFTER=$(echo "$RESPONSE" | jq -r '.totalAfter // 0')
ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error // ""')

# Display validation results
echo "═══════════════════════════════════════════════════════════"
echo "                  VALIDATION RESULTS"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ "$VALID" = "true" ]; then
    print_success "Validation passed"
    echo ""
    
    # Role accessibility
    if [ "$ROLE_ACCESSIBLE" = "true" ]; then
        print_success "Role is accessible"
    else
        print_error "Role is not accessible"
    fi
    
    # DRS initialization
    if [ "$DRS_INITIALIZED" = "true" ]; then
        print_success "DRS is initialized"
    else
        print_error "DRS is not initialized"
    fi
    
    echo ""
    echo "─────────────────────────────────────────────────────────"
    echo "                  CAPACITY INFORMATION"
    echo "─────────────────────────────────────────────────────────"
    echo ""
    echo "  Current Servers:       ${CURRENT_SERVERS}"
    echo "  Replicating Servers:   ${REPLICATING_SERVERS}"
    echo "  Total After Adding:    ${TOTAL_AFTER}"
    echo ""
    
    # Capacity warnings
    if [ "$REPLICATING_SERVERS" -gt 250 ]; then
        print_warning "Staging account is at or above operational limit (250 servers)"
    elif [ "$REPLICATING_SERVERS" -gt 225 ]; then
        print_warning "Staging account is approaching operational limit (${REPLICATING_SERVERS}/250 servers)"
    elif [ "$REPLICATING_SERVERS" -gt 200 ]; then
        print_info "Staging account has ${REPLICATING_SERVERS} servers (67% capacity)"
    else
        print_success "Staging account has sufficient capacity (${REPLICATING_SERVERS}/300 servers)"
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    print_success "Staging account is ready to be added!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    exit 0
else
    print_error "Validation failed"
    echo ""
    
    if [ -n "$ERROR_MSG" ]; then
        echo "Error Details:"
        echo "  ${ERROR_MSG}"
        echo ""
    fi
    
    # Role accessibility
    if [ "$ROLE_ACCESSIBLE" = "false" ]; then
        print_error "Role is not accessible"
        echo ""
        echo "Troubleshooting steps:"
        echo "  1. Verify the role ARN is correct"
        echo "  2. Verify the external ID matches"
        echo "  3. Check the role trust policy allows assumption from orchestration account"
        echo "  4. Verify IAM permissions in the staging account"
    fi
    
    # DRS initialization
    if [ "$DRS_INITIALIZED" = "false" ]; then
        print_error "DRS is not initialized in region ${REGION}"
        echo ""
        echo "To initialize DRS:"
        echo "  1. Log into the staging account (${ACCOUNT_ID})"
        echo "  2. Navigate to AWS DRS console in region ${REGION}"
        echo "  3. Click 'Get started' or 'Initialize service'"
        echo "  4. Accept the service terms"
        echo "  5. Wait for initialization to complete"
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    print_error "Staging account cannot be added until issues are resolved"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    exit 1
fi
