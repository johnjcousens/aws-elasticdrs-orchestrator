#!/bin/bash
set -e

echo "========================================"
echo "Complete Tag Renaming Script"
echo "========================================"
echo ""
echo "Backup branch: tags-backup-2026-01-14"
echo ""

# Delete conflicting tags first
echo "Cleaning up conflicting tags..."
git tag -d v1.3.0 2>/dev/null || true
git tag -d v1.0.0 2>/dev/null || true
git tag -d v1.1.0 2>/dev/null || true
git tag -d v1.2.0 2>/dev/null || true

echo ""
echo "Creating new semantic version tags..."
echo ""

# Phase 1: Foundation & Prototyping
echo "Phase 1: Foundation (v0.x.x)..."
git tag -a v0.1.0 $(git rev-list -n 1 phase-1-baseline) -m "v0.1.0 - Initial prototype with basic DRS integration"
git tag -a v0.2.0 $(git rev-list -n 1 working-drs-drill-integration) -m "v0.2.0 - First working DRS drill execution"
git tag -a v0.3.0 $(git rev-list -n 1 v1.0.0-step-functions-drs-discovery) -m "v0.3.0 - Step Functions orchestration prototype"

# Phase 2: Core Features
echo "Phase 2: Core Features (v0.4-v0.6)..."
git tag -a v0.4.0 $(git rev-list -n 1 v1.4) -m "v0.4.0 - Backend API and database integration"
git tag -a v0.5.0 $(git rev-list -n 1 v1.0.0-prototype-drs-working) -m "v0.5.0 - First end-to-end working prototype"
git tag -a v0.6.0 $(git rev-list -n 1 v1.5-working-prototype) -m "v0.6.0 - Enhanced prototype with improved features"

# Phase 3: Major Features
echo "Phase 3: Major Features (v1.0-v1.2)..."
git tag -a v1.0.0 $(git rev-list -n 1 v4.0-ProtoType-StepFunctionsWithPauseAndResume) -m "v1.0.0 - Wave-based orchestration with pause/resume capability"
git tag -a v1.1.0 $(git rev-list -n 1 v5.0-Prototype-UIEnhancements) -m "v1.1.0 - CloudScape Design System integration"
git tag -a v1.2.0 $(git rev-list -n 1 mvp-demo-ready) -m "v1.2.0 - Minimum viable product for demonstrations"

# Phase 4: Advanced Features
echo "Phase 4: Advanced Features (v1.3-v1.5)..."
git tag -a v1.3.0 $(git rev-list -n 1 DualModeWithTagAndCommandLineSupport) -m "v1.3.0 - Tag-based and plan-based recovery modes"
git tag -a v1.4.0 $(git rev-list -n 1 drs-launch-settings-v1) -m "v1.4.0 - Bulk DRS launch settings management"
git tag -a v1.5.0 $(git rev-list -n 1 ArchitectureDocsUpdated) -m "v1.5.0 - Comprehensive architecture documentation"

# Phase 5: Enterprise Features
echo "Phase 5: Enterprise Features (v1.6-v1.8)..."
git tag -a v1.6.0 $(git rev-list -n 1 tag-sync-prototype-28-regions) -m "v1.6.0 - Multi-region tag synchronization (28 regions)"
git tag -a v1.7.0 $(git rev-list -n 1 v1.0.0-multi-account-prototype) -m "v1.7.0 - Cross-account DRS management"
git tag -a v1.8.0 $(git rev-list -n 1 MVP-DRILL-PROTOTYPE) -m "v1.8.0 - Production-ready drill capability"

# Phase 6: Security & RBAC
echo "Phase 6: Security & RBAC (v2.0-v2.4)..."
git tag -a v2.0.0 $(git rev-list -n 1 RBAC-Prototype-with-Password-Reset-capability-v1.0) -m "v2.0.0 - Role-based access control implementation"
git tag -a v2.1.0 $(git rev-list -n 1 RBAC-Documentation-Complete-v1.1) -m "v2.1.0 - Complete RBAC documentation"
git tag -a v2.2.0 $(git rev-list -n 1 Documentation-Security-Fixes-v1.1.1) -m "v2.2.0 - Security enhancements and fixes"
git tag -a v2.3.0 $(git rev-list -n 1 GitLab-CICD-Pipeline-Alignment-v1.2.0) -m "v2.3.0 - GitLab CI/CD integration"
git tag -a v2.4.0 $(git rev-list -n 1 v2.1.0-major-doc-consolidation) -m "v2.4.0 - Major documentation overhaul"

# Phase 7: Restoration & Stability
echo "Phase 7: Restoration & Stability (v2.5-v2.9)..."
git tag -a v2.5.0 $(git rev-list -n 1 v1.6.0-working-prototype-restored) -m "v2.5.0 - Restored working functionality after refactoring"
git tag -a v2.6.0 $(git rev-list -n 1 v1.6.0-comprehensive-restoration-milestone) -m "v2.6.0 - Complete system restoration"
git tag -a v2.7.0 $(git rev-list -n 1 v1.6.1-eventbridge-restored) -m "v2.7.0 - EventBridge polling functionality restored"
git tag -a v2.8.0 $(git rev-list -n 1 v1.7.0-eventbridge-enhanced) -m "v2.8.0 - Enhanced EventBridge implementation"
git tag -a v2.9.0 $(git rev-list -n 1 v1.3.0-pre-security-fixes) -m "v2.9.0 - Stable baseline before security enhancements"

echo ""
echo "✅ All new tags created successfully!"
echo ""
echo "New tag structure:"
git tag -l "v[0-9]*" | sort -V
echo ""
echo "Next steps:"
echo "1. Review tags: git tag -l | sort -V"
echo "2. Push new tags: git push origin --tags"
echo "3. Run delete-old-tags-remote.sh to clean up old tags from GitHub"
echo ""
