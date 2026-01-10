#!/bin/bash

# Repository Cleanup Script
# Removes troubleshooting files and restores clean repository state

set -e

echo "🧹 AWS DRS Orchestration Repository Cleanup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "README.md" ]] || [[ ! -d "lambda" ]] || [[ ! -d "frontend" ]]; then
    print_error "This script must be run from the repository root directory"
    exit 1
fi

# Confirm cleanup
echo ""
print_warning "This script will remove ~75 troubleshooting files from the repository."
print_warning "All files are preserved in Git history and can be recovered if needed."
echo ""
read -p "Do you want to proceed with cleanup? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Cleanup cancelled by user"
    exit 0
fi

echo ""
print_status "Starting repository cleanup..."

# Phase 1: Archive important analysis (optional)
print_status "Phase 1: Archiving important analysis documents..."
mkdir -p archive/troubleshooting-2026-01-10/

# Archive key analysis documents
if [[ -f "CRITICAL_FIX_SUMMARY.md" ]]; then
    mv CRITICAL_FIX_SUMMARY.md archive/troubleshooting-2026-01-10/
    print_success "Archived CRITICAL_FIX_SUMMARY.md"
fi

if [[ -f "EXECUTION_POLLING_ANALYSIS.md" ]]; then
    mv EXECUTION_POLLING_ANALYSIS.md archive/troubleshooting-2026-01-10/
    print_success "Archived EXECUTION_POLLING_ANALYSIS.md"
fi

if [[ -f "SYSTEMATIC_COMMIT_ANALYSIS.md" ]]; then
    mv SYSTEMATIC_COMMIT_ANALYSIS.md archive/troubleshooting-2026-01-10/
    print_success "Archived SYSTEMATIC_COMMIT_ANALYSIS.md"
fi

# Phase 2: Remove debug scripts
print_status "Phase 2: Removing debug and troubleshooting scripts..."

DEBUG_SCRIPTS=(
    "cancel_execution.py"
    "cancel_execution.sh"
    "check_missing_fields.py"
    "debug_api_response.py"
    "debug_current_execution.py"
    "debug_dynamodb_structure.py"
    "debug_execution_data.py"
    "debug_execution_stuck.py"
    "debug_recovery_instances.py"
    "debug_wave_structure.py"
    "diagnose_execution_detailed.py"
    "diagnose_execution.py"
    "execution_analysis.py"
    "fix_execution_manually.py"
    "fix_server_instance_ids.py"
    "fix_server_recovery_instances.py"
    "fix_stuck_execution.py"
    "local_test_environment.py"
    "populate_server_details.py"
    "test_api_fields.py"
    "test_enhanced_api.py"
    "test_frontend_data.py"
    "test_orchestration_locally.py"
    "test_reconcile_function.py"
    "test_reconcile_simple.py"
    "test_terminate_logic.py"
    "trigger_reconcile.py"
    "working_rbac_middleware.py"
)

removed_count=0
for file in "${DEBUG_SCRIPTS[@]}"; do
    if [[ -f "$file" ]]; then
        rm -f "$file"
        print_success "Removed $file"
        ((removed_count++))
    fi
done
print_status "Removed $removed_count debug scripts"

# Phase 3: Remove test payload files
print_status "Phase 3: Removing test payload files..."

PAYLOAD_FILES=(
    "clean-poller-payload.json"
    "current-execution-payload.json"
    "execution-poller-payload.json"
    "finder-response.json"
    "orchestration-response.json"
    "payload-base64.txt"
    "poller-payload.json"
    "poller-test-payload.json"
    "response.json"
    "test-execution-poller-payload-b64.txt"
    "test-execution-poller-payload.json"
    "test-orchestration-payload.json"
    "test-payload.json"
    "test-poller-payload.json"
)

removed_count=0
for file in "${PAYLOAD_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        rm -f "$file"
        print_success "Removed $file"
        ((removed_count++))
    fi
done
print_status "Removed $removed_count payload files"

# Phase 4: Remove temporary shell scripts
print_status "Phase 4: Removing temporary shell scripts..."

TEMP_SCRIPTS=(
    "create-archive-s3-bucket.sh"
    "create-archive-test-user.sh"
    "deploy-archive-test-stack.sh"
    "deploy-archive-test.py"
    "deploy-working-archive.sh"
    "emergency-deploy-archive.sh"
    "mark_execution_failed.sh"
    "test_execution_poller_fix.sh"
    "test-archive-stack.sh"
    "test-archive-vs-current.sh"
    "verify-multi-stack-deployment.sh"
    "update-github-oidc-permissions.sh"
    "update-github-oidc-qa-permissions.sh"
)

removed_count=0
for file in "${TEMP_SCRIPTS[@]}"; do
    if [[ -f "$file" ]]; then
        rm -f "$file"
        print_success "Removed $file"
        ((removed_count++))
    fi
done
print_status "Removed $removed_count temporary scripts"

# Phase 5: Remove analysis documents
print_status "Phase 5: Removing analysis documents..."

ANALYSIS_DOCS=(
    "API_GATEWAY_SPLIT_PLAN.md"
    "COMPREHENSIVE_DRS_API_IMPLEMENTATION.md"
    "DEEP_ANALYSIS_WORKING_ARCHIVE.md"
    "DEPLOYMENT_FIX.md"
    "FRESH_STACK_DEPLOYMENT_SUMMARY.md"
    "GITHUB_SECRETS_SETUP.md"
    "MULTI_STACK_IMPLEMENTATION_SUMMARY.md"
    "ORCHESTRATION_FIX_LOG.md"
    "ORCHESTRATION_FIX_PLAN.md"
    "RESTORATION_PLAN.md"
    "WORKING_PERIOD_ANALYSIS.md"
    "WORKING_STATE_SUMMARY.md"
    "deploy-archive-properly.md"
)

removed_count=0
for file in "${ANALYSIS_DOCS[@]}"; do
    if [[ -f "$file" ]]; then
        rm -f "$file"
        print_success "Removed $file"
        ((removed_count++))
    fi
done
print_status "Removed $removed_count analysis documents"

# Phase 6: Remove reference files and miscellaneous
print_status "Phase 6: Removing reference files and miscellaneous..."

MISC_FILES=(
    "reference-App.tsx"
    "reference-ExecutionDetailsPage.tsx"
    "commit_list.txt"
    "force-update.yaml"
    "manual_cancel_commands.md"
)

removed_count=0
for file in "${MISC_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        rm -f "$file"
        print_success "Removed $file"
        ((removed_count++))
    fi
done
print_status "Removed $removed_count miscellaneous files"

# Phase 7: Remove build artifacts and test reports
print_status "Phase 7: Removing build artifacts and test reports..."

BUILD_ARTIFACTS=(
    "reference-build"
    "frontend/playwright-report"
    "frontend/test-results"
    "reports/security"
)

removed_count=0
for dir in "${BUILD_ARTIFACTS[@]}"; do
    if [[ -d "$dir" ]]; then
        rm -rf "$dir"
        print_success "Removed directory $dir"
        ((removed_count++))
    fi
done
print_status "Removed $removed_count build artifact directories"

# Clean up empty directories
print_status "Cleaning up empty directories..."
find . -type d -empty -not -path "./.git/*" -delete 2>/dev/null || true

# Summary
echo ""
print_success "Repository cleanup completed successfully!"
echo ""
print_status "Summary of changes:"
echo "  ✅ Archived important analysis documents"
echo "  ✅ Removed debug and troubleshooting scripts"
echo "  ✅ Removed test payload files"
echo "  ✅ Removed temporary shell scripts"
echo "  ✅ Removed analysis documents"
echo "  ✅ Removed reference files and miscellaneous items"
echo ""
print_status "Next steps:"
echo "  1. Review the changes: git status"
echo "  2. Commit the cleanup: git add . && git commit -m 'chore: clean up repository after troubleshooting'"
echo "  3. Push changes: ./scripts/safe-push.sh"
echo ""
print_warning "All removed files are preserved in Git history and can be recovered if needed."