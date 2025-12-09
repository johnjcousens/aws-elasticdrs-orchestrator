#!/bin/bash
# Refresh AWS session token to prevent terminal disconnections

set -e

# Check if session is expired
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "AWS session expired. Please refresh your credentials."
    echo "Run: aws sso login --profile your-profile"
    exit 1
fi

# Show current session info
echo "Current AWS session:"
aws sts get-caller-identity --output table

# Show session expiration (if available)
if command -v jq >/dev/null 2>&1; then
    EXPIRY=$(aws configure get sso_session.expiry 2>/dev/null || echo "Unknown")
    echo "Session expires: $EXPIRY"
fi