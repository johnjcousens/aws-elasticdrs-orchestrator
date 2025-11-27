#!/bin/bash
# Commit modified files individually with verbose commit messages
# Purpose: Enable surgical rollbacks per file for safe DevOps practices
# Usage: ./scripts/commit-files-individually.sh

set -e  # Exit on error

echo "======================================"
echo "Individual File Commit Script"
echo "======================================"
echo "Purpose: Commit each file separately for granular rollback capability"
echo ""

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "❌ ERROR: Not in a git repository"
    exit 1
fi

# Get list of modified and new files
MODIFIED_FILES=$(git status --porcelain | grep '^[AM]' | awk '{print $2}')
DELETED_FILES=$(git status --porcelain | grep '^D' | awk '{print $2}')

if [ -z "$MODIFIED_FILES" ] && [ -z "$DELETED_FILES" ]; then
    echo "✅ No files to commit (working directory clean)"
    exit 0
fi

echo "Files to commit:"
echo "$MODIFIED_FILES" | while read file; do
    if [ -n "$file" ]; then
        echo "  📝 Modified: $file"
    fi
done
echo "$DELETED_FILES" | while read file; do
    if [ -n "$file" ]; then
        echo "  🗑️  Deleted: $file"
    fi
done
echo ""

# Function to determine commit type based on file path
get_commit_type() {
    local file="$1"
    
    case "$file" in
        frontend/src/components/*)
            echo "feat(frontend)"
            ;;
        frontend/src/types/*)
            echo "refactor(types)"
            ;;
        frontend/src/services/*)
            echo "feat(services)"
            ;;
        cfn/*)
            echo "feat(cfn)"
            ;;
        lambda/*)
            echo "feat(lambda)"
            ;;
        scripts/*)
            echo "feat(scripts)"
            ;;
        docs/*)
            echo "docs"
            ;;
        README.md|*.md)
            echo "docs"
            ;;
        .gitignore|Makefile)
            echo "chore(config)"
            ;;
        *)
            echo "chore"
            ;;
    esac
}

# Function to generate commit message
generate_commit_message() {
    local file="$1"
    local action="$2"  # "add", "modify", or "delete"
    local commit_type=$(get_commit_type "$file")
    local filename=$(basename "$file")
    local dirname=$(dirname "$file")
    
    case "$action" in
        add)
            echo "${commit_type}: Add ${filename} to ${dirname}

Created: ${file}
Purpose: New file for deployment sync automation
Type: ${action}

File details:
- Location: ${dirname}
- Name: ${filename}
- Action: Created new file"
            ;;
        modify)
            echo "${commit_type}: Update ${filename} in ${dirname}

Modified: ${file}
Purpose: Update for deployment sync automation
Type: ${action}

Changes:
- File: ${filename}
- Location: ${dirname}
- Action: Modified existing file"
            ;;
        delete)
            echo "${commit_type}: Remove ${filename} from ${dirname}

Deleted: ${file}
Purpose: Cleanup for deployment sync automation
Type: ${action}

File details:
- Was in: ${dirname}
- Name: ${filename}
- Action: Removed file"
            ;;
    esac
}

# Commit modified files individually
echo "Committing modified files..."
echo ""

COMMIT_COUNT=0

# Process modified/added files
echo "$MODIFIED_FILES" | while read file; do
    if [ -z "$file" ]; then
        continue
    fi
    
    # Determine if file is new or modified
    if git ls-files --error-unmatch "$file" > /dev/null 2>&1; then
        ACTION="modify"
    else
        ACTION="add"
    fi
    
    # Generate commit message
    COMMIT_MSG=$(generate_commit_message "$file" "$ACTION")
    
    # Stage and commit file
    echo "  📝 Committing: $file"
    git add "$file"
    git commit -m "$COMMIT_MSG"
    
    COMMIT_COUNT=$((COMMIT_COUNT + 1))
    echo "    ✅ Committed with $ACTION action"
    echo ""
done

# Process deleted files
echo "$DELETED_FILES" | while read file; do
    if [ -z "$file" ]; then
        continue
    fi
    
    # Generate commit message
    COMMIT_MSG=$(generate_commit_message "$file" "delete")
    
    # Stage and commit deletion
    echo "  🗑️  Committing deletion: $file"
    git add "$file"
    git commit -m "$COMMIT_MSG"
    
    COMMIT_COUNT=$((COMMIT_COUNT + 1))
    echo "    ✅ Committed deletion"
    echo ""
done

echo "======================================"
echo "✅ Individual File Commits Complete!"
echo "======================================"
echo ""
echo "Total commits created: $COMMIT_COUNT"
echo ""
echo "Benefits:"
echo "  ✅ Each file has its own commit"
echo "  ✅ Verbose commit messages for audit trail"
echo "  ✅ Easy rollback per file (git revert <commit>)"
echo "  ✅ Clear history for debugging"
echo ""
echo "To rollback a specific file:"
echo "  git log --oneline -- <file>"
echo "  git revert <commit-hash>"
echo ""
