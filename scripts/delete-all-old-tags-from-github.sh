#!/bin/bash

# Delete plain semantic version tags from GitHub
# Keep only tags with descriptions (v1.0.0-description format)

set -e

echo "========================================"
echo "Delete Plain Version Tags from GitHub"
echo "========================================"
echo ""
echo "This will delete plain version tags (v1.0.0, v2.1.0, etc.)"
echo "Only tags with descriptions will remain (v1.0.0-description)"
echo ""

# Get all tags from GitHub
ALL_TAGS=$(git ls-remote --tags origin | grep -v '\^{}' | awk '{print $2}' | sed 's|refs/tags/||')

# Filter to find plain version tags (no description)
PLAIN_TAGS=()
while IFS= read -r tag; do
    # Match ONLY plain semantic versions (v0.1.0, v1.2.3, etc.) with nothing after
    if [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        PLAIN_TAGS+=("$tag")
    fi
done <<< "$ALL_TAGS"

if [ ${#PLAIN_TAGS[@]} -eq 0 ]; then
    echo "✅ No plain version tags to delete - all tags have descriptions"
    exit 0
fi

echo "Plain version tags to delete from GitHub (${#PLAIN_TAGS[@]} total):"
for tag in "${PLAIN_TAGS[@]}"; do
    echo "  - $tag"
done
echo ""

# Confirm deletion
read -p "Delete these ${#PLAIN_TAGS[@]} plain version tags from GitHub? (yes/no): " confirm
if [[ "$confirm" != "yes" ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Deleting plain version tags from GitHub..."

# Delete each plain tag from GitHub
for tag in "${PLAIN_TAGS[@]}"; do
    echo "  Deleting: $tag"
    git push origin ":refs/tags/$tag" 2>/dev/null || echo "    (already deleted or doesn't exist)"
done

echo ""
echo "✅ Plain version tags deleted from GitHub"
echo ""
echo "Remaining tags on GitHub (with descriptions):"
git ls-remote --tags origin | grep -v '\^{}' | awk '{print $2}' | sed 's|refs/tags/||' | sort
