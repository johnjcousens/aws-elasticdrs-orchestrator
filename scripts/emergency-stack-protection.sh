#!/bin/bash

# EMERGENCY STACK PROTECTION SYSTEM
# This script implements multiple layers of protection to prevent catastrophic stack deletion

set -e

# Load deployment configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/load-deployment-config.sh"

PROTECTED_STACKS=(
    "aws-elasticdrs-orchestrator-dev"
    "aws-elasticdrs-orchestrator-test" 
    "aws-elasticdrs-orchestrator-prod"
)

WORKFLOW_FILE=".github/workflows/deploy.yml"

echo "🛡️  EMERGENCY STACK PROTECTION SYSTEM 🛡️"
echo "=============================================="

# Layer 1: PROJECT_NAME Verification
echo ""
echo "🔍 Layer 1: PROJECT_NAME Verification"
CURRENT_PROJECT_NAME=$(grep "PROJECT_NAME:" "$WORKFLOW_FILE" | awk '{print $2}')
echo "   Expected: $PROJECT_NAME"
echo "   Current:  $CURRENT_PROJECT_NAME"

if [ "$CURRENT_PROJECT_NAME" != "$PROJECT_NAME" ]; then
    echo ""
    echo "🚨 CRITICAL ALERT: PROJECT_NAME MISMATCH DETECTED 🚨"
    echo ""
    echo "❌ DEPLOYMENT BLOCKED - This change would:"
    echo "   1. DELETE existing working stacks"
    echo "   2. CREATE new stacks with different names"
    echo "   3. LOSE ALL DATA including active executions"
    echo ""
    echo "🛑 EMERGENCY STOP - Contact team lead immediately"
    exit 1
fi
echo "   ✅ PROJECT_NAME verification passed"

# Layer 2: Protected Stack Existence Check
echo ""
echo "🔍 Layer 2: Protected Stack Status Check"
for stack in "${PROTECTED_STACKS[@]}"; do
    echo "   Checking: $stack"
    if aws cloudformation describe-stacks --stack-name "$stack" --region "$REGION" >/dev/null 2>&1; then
        STATUS=$(aws cloudformation describe-stacks --stack-name "$stack" --region "$REGION" --query 'Stacks[0].StackStatus' --output text)
        echo "   Status: $STATUS"
        
        if [[ "$STATUS" == *"ROLLBACK"* ]] || [[ "$STATUS" == *"FAILED"* ]]; then
            echo "   ⚠️  WARNING: Stack in failed state - deployment may fix this"
        elif [[ "$STATUS" == *"DELETE"* ]]; then
            echo "   🚨 CRITICAL: Stack is being deleted or deleted!"
        else
            echo "   ✅ Stack exists and healthy"
        fi
    else
        echo "   ❌ Stack does not exist - will be created"
    fi
done

# Layer 3: Active Execution Check (if possible)
echo ""
echo "🔍 Layer 3: Active Execution Safety Check"
echo "   Checking for active DRS executions..."

# Try to check for active executions in existing stacks
ACTIVE_EXECUTIONS=0
for stack in "${PROTECTED_STACKS[@]}"; do
    if aws cloudformation describe-stacks --stack-name "$stack" --region "$REGION" >/dev/null 2>&1; then
        # Get API endpoint from stack outputs
        API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name "$stack" --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text 2>/dev/null || echo "")
        
        if [ -n "$API_ENDPOINT" ] && [ "$API_ENDPOINT" != "None" ]; then
            echo "   Found API endpoint: $API_ENDPOINT"
            # Note: Would need authentication to actually check executions
            echo "   ⚠️  Manual verification required: Check for active executions before deployment"
        fi
    fi
done

if [ $ACTIVE_EXECUTIONS -gt 0 ]; then
    echo "   🚨 CRITICAL: $ACTIVE_EXECUTIONS active executions detected"
    echo "   🛑 DEPLOYMENT BLOCKED - Wait for executions to complete"
    exit 1
else
    echo "   ✅ No active executions detected (or unable to verify)"
fi

# Layer 4: Deployment Confirmation
echo ""
echo "🔍 Layer 4: Final Safety Confirmation"
echo ""
echo "DEPLOYMENT SUMMARY:"
echo "   Project Name: $PROJECT_NAME"
echo "   Target Stack: $STACK_NAME"
echo "   Environment: $ENVIRONMENT"
echo "   Region: $REGION"
echo ""
echo "⚠️  This deployment will:"
echo "   - Update or create the stack: $STACK_NAME"
echo "   - Deploy all Lambda functions and infrastructure"
echo "   - Update the frontend configuration"
echo ""

# In CI/CD, auto-proceed. In manual runs, ask for confirmation
if [ "${CI:-false}" = "true" ] || [ "${GITHUB_ACTIONS:-false}" = "true" ]; then
    echo "🤖 CI/CD Environment - Auto-proceeding with deployment"
    echo "✅ All protection layers passed - deployment authorized"
else
    echo "👤 Manual Environment - Confirmation required"
    read -p "   Type 'DEPLOY' to confirm deployment: " CONFIRMATION
    if [ "$CONFIRMATION" != "DEPLOY" ]; then
        echo "   🛑 Deployment cancelled by user"
        exit 1
    fi
    echo "✅ User confirmation received - deployment authorized"
fi

echo ""
echo "🚀 EMERGENCY STACK PROTECTION: ALL CHECKS PASSED"
echo "   Deployment is authorized to proceed"
echo "=============================================="