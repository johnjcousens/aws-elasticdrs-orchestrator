#!/bin/bash

# EMERGENCY SAFEGUARD: Prevent accidental PROJECT_NAME changes
# This script MUST be run before any deployment to prevent stack deletion

set -e

EXPECTED_PROJECT_NAME="aws-drs-orchestrator-fresh"
WORKFLOW_FILE=".github/workflows/deploy.yml"

echo "=== PROJECT_NAME SAFEGUARD CHECK ==="

# Extract current PROJECT_NAME from workflow
CURRENT_PROJECT_NAME=$(grep "PROJECT_NAME:" "$WORKFLOW_FILE" | awk '{print $2}')

echo "Expected PROJECT_NAME: $EXPECTED_PROJECT_NAME"
echo "Current PROJECT_NAME:  $CURRENT_PROJECT_NAME"

if [ "$CURRENT_PROJECT_NAME" != "$EXPECTED_PROJECT_NAME" ]; then
    echo ""
    echo "🚨 CRITICAL ERROR: PROJECT_NAME MISMATCH DETECTED 🚨"
    echo ""
    echo "This change would cause CloudFormation to:"
    echo "1. DELETE the existing working stack: $EXPECTED_PROJECT_NAME"
    echo "2. CREATE a new stack: $CURRENT_PROJECT_NAME"
    echo "3. LOSE ALL DATA including active drill executions"
    echo ""
    echo "❌ DEPLOYMENT BLOCKED FOR SAFETY"
    echo ""
    echo "If you intentionally want to change PROJECT_NAME:"
    echo "1. Update EXPECTED_PROJECT_NAME in this script"
    echo "2. Ensure no active executions are running"
    echo "3. Coordinate with team for planned migration"
    echo "4. Have rollback plan ready"
    echo ""
    exit 1
fi

echo "✅ PROJECT_NAME verification passed"
echo "✅ Safe to proceed with deployment"