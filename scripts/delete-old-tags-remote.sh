#!/bin/bash
set -e

echo "========================================"
echo "Delete Old Tags from Remote"
echo "========================================"
echo ""
echo "⚠️  WARNING: This will delete old tags from GitHub"
echo "Backup exists at: tags-backup-2026-01-14 branch"
echo ""
read -p "Are you sure you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Deleting old tags from remote..."

# Delete old tags from remote
git push origin --delete phase-1-baseline
git push origin --delete working-drs-drill-integration
git push origin --delete v1.0.0-step-functions-drs-discovery
git push origin --delete v1.1
git push origin --delete v1.2
git push origin --delete v1.3
git push origin --delete v1.4
git push origin --delete v1.0.0-prototype-drs-working
git push origin --delete v1.5-working-prototype
git push origin --delete v2.0
git push origin --delete v3.0
git push origin --delete v4.0-ProtoType-StepFunctionsWithPauseAndResume
git push origin --delete v5.0-Prototype-UIEnhancements
git push origin --delete mvp-demo-ready
git push origin --delete future-plans-v1
git push origin --delete FutureEnhancementsDocumented
git push origin --delete DualModeWithTagAndCommandLineSupport
git push origin --delete drs-launch-settings-v1
git push origin --delete ArchitectureDocsUpdated
git push origin --delete v1.0-beta
git push origin --delete v1.5.0
git push origin --delete v1.6.1
git push origin --delete tag-sync-prototype-28-regions
git push origin --delete v1.0.0-multi-account-prototype
git push origin --delete MVP-DRILL-PROTOTYPE
git push origin --delete RBAC-Prototype-with-Password-Reset-capability-v1.0
git push origin --delete RBAC-Documentation-Complete-v1.1
git push origin --delete Documentation-Security-Fixes-v1.1.1
git push origin --delete GitLab-CICD-Pipeline-Alignment-v1.2.0
git push origin --delete v2.1.0-major-doc-consolidation
git push origin --delete v1.6.0-working-prototype-restored
git push origin --delete v1.6.0-comprehensive-restoration-milestone
git push origin --delete v1.6.1-eventbridge-restored
git push origin --delete v1.7.0-eventbridge-enhanced
git push origin --delete v1.3.0-pre-security-fixes
git push origin --delete v1.3.0

echo ""
echo "✅ Old tags deleted from remote"
echo ""
