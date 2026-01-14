#!/bin/bash
set -e

echo "========================================"
echo "Tag Renaming Script"
echo "========================================"
echo ""
echo "This will rename all tags to semantic versioning"
echo "Backup branch created: tags-backup-2026-01-14"
echo ""

# First, delete conflicting tags
echo "Deleting conflicting existing tags..."
git tag -d v1.3.0 2>/dev/null || true

# Get commit hashes for old tags
echo "Getting commit hashes..."

# Phase 1: Foundation & Prototyping
echo "Phase 1: Foundation & Prototyping..."
COMMIT=$(git rev-list -n 1 phase-1-baseline)
git tag -a v0.1.0 $COMMIT -m "v0.1.0 - Initial prototype with basic DRS integration"

COMMIT=$(git rev-list -n 1 working-drs-drill-integration)
git tag -a v0.2.0 $COMMIT -m "v0.2.0 - First working DRS drill execution"

COMMIT=$(git rev-list -n 1 v1.0.0-step-functions-drs-discovery)
git tag -a v0.3.0 $COMMIT -m "v0.3.0 - Step Functions orchestration prototype"

# Phase 2: Core Features
echo "Phase 2: Core Features..."
COMMIT=$(git rev-list -n 1 v1.4)
git tag -a v0.4.0 $COMMIT -m "v0.4.0 - Backend API and database integration"

COMMIT=$(git rev-list -n 1 v1.0.0-prototype-drs-working)
git tag -a v0.5.0 $COMMIT -m "v0.5.0 - First end-to-end working prototype"

COMMIT=$(git rev-list -n 1 v1.5-working-prototype)
git tag -a v0.6.0 $COMMIT -m "v0.6.0 - Enhanced prototype with improved features"

# Phase 3: Major Features
echo "Phase 3: Major Features..."
COMMIT=$(git rev-list -n 1 v4.0-ProtoType-StepFunctionsWithPauseAndResume)
git tag -a v1.0.0 $COMMIT -m "v1.0.0 - Wave-based orchestration with pause/resume capability"

COMMIT=$(git rev-list -n 1 v5.0-Prototype-UIEnhancements)
git tag -a v1.1.0 $COMMIT -m "v1.1.0 - CloudScape Design System integration"

COMMIT=$(git rev-list -n 1 mvp-demo-ready)
git tag -a v1.2.0 $COMMIT -m "v1.2.0 - Minimum viable product for demonstrations"

# Phase 4: Advanced Features
echo "Phase 4: Advanced Features..."
COMMIT=$(git rev-list -n 1 DualModeWithTagAndCommandLineSupport)
git tag -a v1.3.0 $COMMIT -m "v1.3.0 - Tag-based and plan-based recovery modes"
git tag -a v1.4.0 drs-launch-settings-v1 -m "v1.4.0 - Bulk DRS launch settings management"
git tag -a v1.5.0 ArchitectureDocsUpdated -m "v1.5.0 - Comprehensive architecture documentation"

# Phase 5: Enterprise Features
echo "Phase 5: Enterprise Features..."
git tag -a v1.6.0 tag-sync-prototype-28-regions -m "v1.6.0 - Multi-region tag synchronization (28 regions)"
git tag -a v1.7.0 v1.0.0-multi-account-prototype -m "v1.7.0 - Cross-account DRS management"
git tag -a v1.8.0 MVP-DRILL-PROTOTYPE -m "v1.8.0 - Production-ready drill capability"

# Phase 6: Security & RBAC
echo "Phase 6: Security & RBAC..."
git tag -a v2.0.0 RBAC-Prototype-with-Password-Reset-capability-v1.0 -m "v2.0.0 - Role-based access control implementation"
git tag -a v2.1.0 RBAC-Documentation-Complete-v1.1 -m "v2.1.0 - Complete RBAC documentation"
git tag -a v2.2.0 Documentation-Security-Fixes-v1.1.1 -m "v2.2.0 - Security enhancements and fixes"
git tag -a v2.3.0 GitLab-CICD-Pipeline-Alignment-v1.2.0 -m "v2.3.0 - GitLab CI/CD integration"
git tag -a v2.4.0 v2.1.0-major-doc-consolidation -m "v2.4.0 - Major documentation overhaul"

# Phase 7: Restoration & Stability
echo "Phase 7: Restoration & Stability..."
git tag -a v2.5.0 v1.6.0-working-prototype-restored -m "v2.5.0 - Restored working functionality after refactoring"
git tag -a v2.6.0 v1.6.0-comprehensive-restoration-milestone -m "v2.6.0 - Complete system restoration"
git tag -a v2.7.0 v1.6.1-eventbridge-restored -m "v2.7.0 - EventBridge polling functionality restored"
git tag -a v2.8.0 v1.7.0-eventbridge-enhanced -m "v2.8.0 - Enhanced EventBridge implementation"
git tag -a v2.9.0 v1.3.0-pre-security-fixes -m "v2.9.0 - Stable baseline before security enhancements"

echo ""
echo "✅ New tags created successfully"
echo ""
echo "Deleting old tags locally..."

# Delete old tags locally
git tag -d phase-1-baseline
git tag -d working-drs-drill-integration
git tag -d v1.0.0-step-functions-drs-discovery
git tag -d v1.1
git tag -d v1.2
git tag -d v1.3
git tag -d v1.4
git tag -d v1.0.0-prototype-drs-working
git tag -d v1.5-working-prototype
git tag -d v2.0
git tag -d v3.0
git tag -d v4.0-ProtoType-StepFunctionsWithPauseAndResume
git tag -d v5.0-Prototype-UIEnhancements
git tag -d mvp-demo-ready
git tag -d future-plans-v1
git tag -d FutureEnhancementsDocumented
git tag -d DualModeWithTagAndCommandLineSupport
git tag -d drs-launch-settings-v1
git tag -d ArchitectureDocsUpdated
git tag -d v1.0-beta
git tag -d v1.5.0
git tag -d v1.6.1
git tag -d tag-sync-prototype-28-regions
git tag -d v1.0.0-multi-account-prototype
git tag -d MVP-DRILL-PROTOTYPE
git tag -d RBAC-Prototype-with-Password-Reset-capability-v1.0
git tag -d RBAC-Documentation-Complete-v1.1
git tag -d Documentation-Security-Fixes-v1.1.1
git tag -d GitLab-CICD-Pipeline-Alignment-v1.2.0
git tag -d v2.1.0-major-doc-consolidation
git tag -d v1.6.0-working-prototype-restored
git tag -d v1.6.0-comprehensive-restoration-milestone
git tag -d v1.6.1-eventbridge-restored
git tag -d v1.7.0-eventbridge-enhanced
git tag -d v1.3.0-pre-security-fixes
git tag -d v1.3.0

echo ""
echo "✅ Old tags deleted locally"
echo ""
echo "To complete the process:"
echo "1. Review new tags: git tag -l | sort -V"
echo "2. Push new tags: git push origin --tags"
echo "3. Delete old tags from remote (see delete-old-tags-remote.sh)"
echo ""
