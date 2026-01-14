#!/bin/bash
set -e

echo "========================================"
echo "Cleanup Old Tags"
echo "========================================"
echo ""
echo "This will delete old non-semantic version tags"
echo "New semantic versions (v0.x.x - v3.0.0) will be kept"
echo ""

# List of old tags to delete
OLD_TAGS=(
    "ad-pki-production-baseline-2025-11"
    "ArchitectureDocsUpdated"
    "Best-Known-Config"
    "Documentation-Security-Fixes-v1.1.1"
    "DualModeWithTagAndCommandLineSupport"
    "drs-launch-settings-v1"
    "FutureEnhancementsDocumented"
    "future-plans-v1"
    "GitLab-CICD-Pipeline-Alignment-v1.2.0"
    "MVP-DRILL-PROTOTYPE"
    "mvp-demo-ready"
    "phase-1-baseline"
    "RBAC-Documentation-Complete-v1.1"
    "RBAC-Prototype-with-Password-Reset-capability-v1.0"
    "tag-sync-prototype-28-regions"
    "v1.5.0"
    "v1.6.0-comprehensive-restoration-milestone"
    "v1.6.0-working-prototype-restored"
    "v1.6.1"
    "v1.6.1-eventbridge-restored"
    "v1.7.0-eventbridge-enhanced"
    "v2.0"
    "v2.1.0-major-doc-consolidation"
    "v3.0"
    "v4.0-ProtoType-StepFunctionsWithPauseAndResume"
    "v5.0-Prototype-UIEnhancements"
    "working-drs-drill-integration"
)

echo "Deleting old tags locally..."
for tag in "${OLD_TAGS[@]}"; do
    git tag -d "$tag" 2>/dev/null && echo "  ✓ Deleted: $tag" || echo "  - Not found: $tag"
done

echo ""
echo "Deleting old tags from remote..."
for tag in "${OLD_TAGS[@]}"; do
    git push origin --delete "$tag" 2>/dev/null && echo "  ✓ Deleted from remote: $tag" || echo "  - Not found on remote: $tag"
done

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Final tag structure:"
git tag -l | grep "^v[0-9]" | sort -V
echo ""
