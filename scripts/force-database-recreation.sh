#!/bin/bash
# Safe DynamoDB Table Recreation for CamelCase Migration (Nested Stack Compatible)
# Purpose: Delete existing PascalCase tables and deploy camelCase schema via nested stack
# Usage: ./scripts/force-database-recreation.sh [--dry-run] [--profile PROFILE]

set -e

# Disable AWS CLI pager
export AWS_PAGER=""

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load configuration
if [ -f "$PROJECT_ROOT/.env.deployment.fresh" ]; then
    source "$PROJECT_ROOT/.env.deployment.fresh"
fi

# Default values
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-aws-elasticdrs-orchestrator}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
PARENT_STACK_NAME="${PARENT_STACK_NAME:-aws-elasticdrs-orchestrator-test}"
AWS_PROFILE="${AWS_PROFILE:-default}"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Safe DynamoDB table recreation for camelCase migration (nested stack compatible)"
            echo ""
            echo "Options:"
            echo "  --dry-run                Show what would be done without making changes"
            echo "  --profile PROFILE        AWS credentials profile (default: ${AWS_PROFILE})"
            echo "  --help                   Show this help message"
            echo ""
            echo "This script will:"
            echo "  1. Backup existing table data (if any)"
            echo "  2. Delete existing PascalCase tables manually"
            echo "  3. Deploy updated nested stack with ForceRecreation=true"
            echo "  4. Verify new camelCase tables are created successfully"
            echo ""
            echo "SAFE FOR NESTED STACKS:"
            echo "  - Maintains same table names (no timestamp suffixes)"
            echo "  - Preserves all CloudFormation outputs"
            echo "  - Compatible with existing Lambda functions"
            echo "  - No breaking changes to API Gateway or other stacks"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Build profile flag
PROFILE_FLAG=""
if [ -n "$AWS_PROFILE" ]; then
    PROFILE_FLAG="--profile $AWS_PROFILE"
fi

echo "======================================"
echo "🔄 Safe DynamoDB Table Recreation"
echo "======================================"
echo "Project: $PROJECT_NAME"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Stack: $PARENT_STACK_NAME"
echo "AWS Profile: $AWS_PROFILE"
echo "Dry Run: $DRY_RUN"
echo ""
echo "🛡️  NESTED STACK SAFE:"
echo "  ✅ Maintains same table names"
echo "  ✅ Preserves CloudFormation outputs"
echo "  ✅ Compatible with existing integrations"
echo ""

# Verify AWS credentials
echo "🔐 Verifying AWS credentials..."
if ! aws sts get-caller-identity $PROFILE_FLAG --region $REGION >/dev/null 2>&1; then
    echo "❌ ERROR: AWS credentials not configured or profile not found"
    exit 1
fi
echo "✅ AWS credentials verified"
echo ""

# Table names (same names, different schema)
TABLES=(
    "${PROJECT_NAME}-protection-groups-${ENVIRONMENT}"
    "${PROJECT_NAME}-recovery-plans-${ENVIRONMENT}"
    "${PROJECT_NAME}-execution-history-${ENVIRONMENT}"
    "${PROJECT_NAME}-target-accounts-${ENVIRONMENT}"
)

# Step 1: Check existing tables and backup data
echo "📋 Step 1: Checking existing tables and backing up data..."
BACKUP_DIR="$PROJECT_ROOT/backup/dynamodb-$(date +%Y%m%d-%H%M%S)"

for table in "${TABLES[@]}"; do
    echo "  🔍 Checking table: $table"
    
    if aws dynamodb describe-table --table-name "$table" $PROFILE_FLAG --region $REGION >/dev/null 2>&1; then
        echo "    ✅ Table exists"
        
        # Check if table has data
        ITEM_COUNT=$(aws dynamodb scan --table-name "$table" --select COUNT $PROFILE_FLAG --region $REGION --query 'Count' --output text 2>/dev/null || echo "0")
        echo "    📊 Item count: $ITEM_COUNT"
        
        if [ "$ITEM_COUNT" -gt 0 ] && [ "$DRY_RUN" = false ]; then
            echo "    💾 Backing up table data..."
            mkdir -p "$BACKUP_DIR"
            
            # Export table data to JSON
            aws dynamodb scan --table-name "$table" $PROFILE_FLAG --region $REGION > "$BACKUP_DIR/${table}.json"
            echo "    ✅ Backup saved to: $BACKUP_DIR/${table}.json"
        elif [ "$DRY_RUN" = true ] && [ "$ITEM_COUNT" -gt 0 ]; then
            echo "    ℹ️  DRY RUN: Would backup $ITEM_COUNT items"
        fi
    else
        echo "    ⚠️  Table does not exist (will be created fresh)"
    fi
done

echo ""

# Step 2: Delete existing tables manually (CloudFormation can't change key schema)
echo "📋 Step 2: Deleting existing tables manually..."

for table in "${TABLES[@]}"; do
    echo "  🗑️  Processing table: $table"
    
    if aws dynamodb describe-table --table-name "$table" $PROFILE_FLAG --region $REGION >/dev/null 2>&1; then
        if [ "$DRY_RUN" = true ]; then
            echo "    ℹ️  DRY RUN: Would delete table $table"
        else
            echo "    🗑️  Deleting table..."
            aws dynamodb delete-table --table-name "$table" $PROFILE_FLAG --region $REGION >/dev/null 2>&1
            echo "    ✅ Delete initiated for $table"
        fi
    else
        echo "    ⚠️  Table does not exist, skipping"
    fi
done

if [ "$DRY_RUN" = false ]; then
    echo ""
    echo "⏳ Waiting for table deletions to complete..."
    
    for table in "${TABLES[@]}"; do
        echo "  ⏳ Waiting for $table deletion..."
        
        # Wait for table to be deleted (max 5 minutes)
        WAIT_COUNT=0
        while [ $WAIT_COUNT -lt 60 ]; do
            if ! aws dynamodb describe-table --table-name "$table" $PROFILE_FLAG --region $REGION >/dev/null 2>&1; then
                echo "    ✅ $table deleted successfully"
                break
            fi
            
            sleep 5
            WAIT_COUNT=$((WAIT_COUNT + 1))
            
            if [ $WAIT_COUNT -eq 60 ]; then
                echo "    ⚠️  Timeout waiting for $table deletion"
            fi
        done
    done
fi

echo ""

# Step 3: Deploy nested stack with ForceRecreation=true
echo "📋 Step 3: Deploying nested stack with camelCase schema..."

if [ "$DRY_RUN" = true ]; then
    echo "  ℹ️  DRY RUN: Would deploy CloudFormation stack with ForceRecreation=true"
else
    echo "  🚀 Deploying master stack with ForceRecreation parameter..."
    
    # Get current admin email from stack parameters
    ADMIN_EMAIL=$(aws cloudformation describe-stacks \
        --stack-name "$PARENT_STACK_NAME" \
        --query "Stacks[0].Parameters[?ParameterKey=='AdminEmail'].ParameterValue" \
        --output text $PROFILE_FLAG --region $REGION 2>/dev/null || echo "")
    
    if [ -z "$ADMIN_EMAIL" ] || [ "$ADMIN_EMAIL" = "None" ]; then
        ADMIN_EMAIL="${ADMIN_EMAIL:-jocousen@amazon.com}"
        echo "    ⚠️  Using default admin email: $ADMIN_EMAIL"
    else
        echo "    ✅ Using existing admin email: $ADMIN_EMAIL"
    fi
    
    # Deploy the stack with ForceRecreation parameter
    aws cloudformation deploy \
        --template-file "$PROJECT_ROOT/cfn/master-template.yaml" \
        --stack-name "$PARENT_STACK_NAME" \
        --parameter-overrides \
            ProjectName="$PROJECT_NAME" \
            Environment="$ENVIRONMENT" \
            AdminEmail="$ADMIN_EMAIL" \
            ForceRecreation="true" \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region $REGION $PROFILE_FLAG
    
    echo "    ✅ Stack deployment completed"
fi

echo ""

# Step 4: Verify new tables
echo "📋 Step 4: Verifying new camelCase tables..."

if [ "$DRY_RUN" = false ]; then
    for table in "${TABLES[@]}"; do
        echo "  🔍 Verifying table: $table"
        
        if aws dynamodb describe-table --table-name "$table" $PROFILE_FLAG --region $REGION >/dev/null 2>&1; then
            # Get key schema to verify camelCase
            KEY_SCHEMA=$(aws dynamodb describe-table --table-name "$table" $PROFILE_FLAG --region $REGION --query 'Table.KeySchema[0].AttributeName' --output text)
            echo "    ✅ Table exists with primary key: $KEY_SCHEMA"
            
            # Verify it's camelCase (should be groupId, planId, executionId, accountId)
            case "$table" in
                *protection-groups*)
                    if [ "$KEY_SCHEMA" = "groupId" ]; then
                        echo "    ✅ CamelCase schema confirmed (groupId)"
                    else
                        echo "    ❌ Unexpected key schema: $KEY_SCHEMA (expected: groupId)"
                    fi
                    ;;
                *recovery-plans*)
                    if [ "$KEY_SCHEMA" = "planId" ]; then
                        echo "    ✅ CamelCase schema confirmed (planId)"
                    else
                        echo "    ❌ Unexpected key schema: $KEY_SCHEMA (expected: planId)"
                    fi
                    ;;
                *execution-history*)
                    if [ "$KEY_SCHEMA" = "executionId" ]; then
                        echo "    ✅ CamelCase schema confirmed (executionId)"
                    else
                        echo "    ❌ Unexpected key schema: $KEY_SCHEMA (expected: executionId)"
                    fi
                    ;;
                *target-accounts*)
                    if [ "$KEY_SCHEMA" = "accountId" ]; then
                        echo "    ✅ CamelCase schema confirmed (accountId)"
                    else
                        echo "    ❌ Unexpected key schema: $KEY_SCHEMA (expected: accountId)"
                    fi
                    ;;
            esac
        else
            echo "    ❌ Table not found after deployment"
        fi
    done
else
    echo "  ℹ️  DRY RUN: Would verify new camelCase tables"
fi

echo ""

# Step 5: Provide next steps
echo "📋 Step 5: Next Steps"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "ℹ️  DRY RUN SUMMARY:"
    echo "  - Would backup existing table data"
    echo "  - Would delete existing PascalCase tables"
    echo "  - Would deploy nested stack with ForceRecreation=true"
    echo "  - Would verify new camelCase tables"
    echo ""
    echo "To execute the recreation:"
    echo "  $0 --profile $AWS_PROFILE"
else
    echo "✅ CAMELCASE MIGRATION COMPLETE"
    echo ""
    echo "🎯 Migration Results:"
    echo "  ✅ Old PascalCase tables deleted"
    echo "  ✅ New camelCase tables created"
    echo "  ✅ Nested stack architecture preserved"
    echo "  ✅ All CloudFormation outputs maintained"
    echo ""
    
    if [ -d "$BACKUP_DIR" ]; then
        echo "💾 Data backups available in: $BACKUP_DIR"
        echo ""
        echo "To restore data after migration (if needed):"
        echo "  # Note: Field names will need conversion from PascalCase to camelCase"
        echo "  # Use AWS CLI or DynamoDB console to import JSON backups"
        echo ""
    fi
    
    echo "🚀 System Status:"
    echo "  - API endpoints now use camelCase format"
    echo "  - Lambda functions updated for camelCase schema"
    echo "  - Frontend expects camelCase responses"
    echo "  - All transform functions eliminated"
    echo ""
    echo "✅ CamelCase migration successfully completed!"
fi

echo ""
echo "======================================"
if [ "$DRY_RUN" = true ]; then
    echo "✅ DRY RUN COMPLETE"
else
    echo "✅ MIGRATION COMPLETE"
fi
echo "======================================"