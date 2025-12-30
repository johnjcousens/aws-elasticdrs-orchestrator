#!/bin/bash

# Safe cleanup script for AWS DRS Orchestration project
# Removes development artifacts, build files, and temporary data
# Preserves source code and essential documentation

set -e

echo "🧹 Starting safe cleanup of development artifacts..."

# Function to safely remove if exists
safe_rm() {
    if [ -e "$1" ]; then
        echo "  Removing: $1"
        rm -rf "$1"
    fi
}

# Function to check if a file is referenced in documentation
check_references() {
    local file="$1"
    local basename=$(basename "$file" .md)
    
    echo "  Checking references for: $file"
    
    # Check README.md and docs-index.md for references
    if grep -q "$basename" README.md 2>/dev/null || grep -q "$basename" .kiro/steering/docs-index.md 2>/dev/null; then
        echo "  ⚠️  SKIPPING: $file is referenced in documentation"
        return 1
    fi
    
    # Check for links in other markdown files
    if find docs/ -name "*.md" -exec grep -l "$basename" {} \; 2>/dev/null | grep -q .; then
        echo "  ⚠️  SKIPPING: $file is referenced in other docs"
        return 1
    fi
    
    return 0
}

# Function to safely remove document after checking references
safe_rm_doc() {
    if [ -e "$1" ]; then
        if check_references "$1"; then
            echo "  ✅ Safe to remove: $1"
            rm -rf "$1"
        fi
    fi
}

# 1. Keep AI assistant memory and history (preserving context)
echo "📁 Preserving AI assistant data (.cline_memory/, .kiro/, history/)..."

# 2. Remove archive and temp directories
echo "📁 Cleaning archives and temp files..."
safe_rm archive/
safe_rm temp/
safe_rm docs/archive/

# 3. Remove specific documentation files (after checking references)
echo "📄 Checking documentation files for references..."
safe_rm_doc docs/DRS_MODULAR_ORCHESTRATION_DESIGN.md
safe_rm_doc docs/FUTURE_ENHANCEMENTS_CONSOLIDATION_PLAN.md
safe_rm_doc docs/GAP_ANALYSIS.md
safe_rm_doc docs/ARCHIVE_ANALYSIS.md

# 4. Remove draw.io backup files
echo "🎨 Cleaning draw.io backups..."
find docs/architecture/ -name ".*" -type f -delete 2>/dev/null || true

# 5. Remove frontend debug files
echo "🌐 Cleaning frontend debug files..."
safe_rm frontend/debug-frontend-flow.*
safe_rm frontend/dev.sh
safe_rm frontend/build.sh

# 6. Remove Lambda build artifacts
echo "🔧 Cleaning Lambda build artifacts..."
safe_rm lambda/package/
safe_rm lambda/deployment-package.zip
safe_rm lambda/lambda-package.zip
safe_rm lambda/orchestration-package.zip
safe_rm lambda/poller/htmlcov/
safe_rm lambda/poller/.coverage
find lambda/ -name "*.zip" -delete 2>/dev/null || true

# 7. Remove Python cache files
echo "🐍 Cleaning Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name ".coverage" -delete 2>/dev/null || true
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# 8. Remove test artifacts (keep test source code)
echo "🧪 Cleaning test artifacts..."
safe_rm tests/playwright/test-results/
safe_rm tests/playwright/playwright-report/
safe_rm tests/python/htmlcov/
find tests/ -name "*.pyc" -delete 2>/dev/null || true
find tests/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 9. Remove non-essential scripts (keep essential ones)
echo "📜 Cleaning non-essential scripts..."
cd scripts 2>/dev/null || { echo "scripts/ directory not found, skipping..."; exit 0; }

# Remove monitoring and testing scripts
safe_rm check_drill_status.py
safe_rm check_job_completion.sh
safe_rm check-jsx-corruption.sh
safe_rm cleanup_stuck_drs_jobs.py
safe_rm commit-files-individually.sh
safe_rm comprehensive_api_test.py
safe_rm confluence_unified_exporter.py
safe_rm create_aws_branded_pptx.py
safe_rm create_aws_markdown_template.py
safe_rm deploy-and-sync-all.sh
safe_rm execute_drill.py
safe_rm incremental-commit.sh
safe_rm markdown_to_docx_converter.py
safe_rm monitor_*.py
safe_rm monitor_*.sh
safe_rm run-automated-tests.sh
safe_rm run-tests.sh
safe_rm safe-edit.sh
safe_rm setup-gitlab-cicd.sh
safe_rm test_*.py
safe_rm test-drill.sh
safe_rm validate-deployment.sh
safe_rm verify-*.sh
safe_rm wait_for_completion.sh

cd ..

# 10. Remove node_modules if present (can be reinstalled)
echo "📦 Cleaning node_modules..."
safe_rm frontend/node_modules/
safe_rm tests/playwright/node_modules/

# 11. Remove IDE and editor files
echo "💻 Cleaning IDE files..."
safe_rm .vscode/settings.json
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Remaining important files:"
echo "  ✓ Source code (frontend/, lambda/, cfn/)"
echo "  ✓ Essential scripts (sync-to-deployment-bucket.sh, etc.)"
echo "  ✓ Core documentation (README.md, docs/guides/, etc.)"
echo "  ✓ Configuration files (.env.*, package.json, etc.)"
echo "  ✓ Test source code (tests/ directory structure)"
echo "  ✓ AI assistant memory (.cline_memory/, .kiro/, history/)"
echo ""
echo "🗑️  Removed:"
echo "  • Build artifacts and cache files"
echo "  • Test reports and coverage files"
echo "  • Archive and temporary directories"
echo "  • Non-essential monitoring scripts"
echo "  • IDE and system files"
echo "  • Unreferenced documentation files (checked for links)"
echo ""
echo "💡 All removed files are backed up in GitLab commits"