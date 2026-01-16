#!/bin/bash
# Sanitize documentation files by replacing sensitive data with placeholders

set -e

echo "=== Sanitizing Documentation Files ==="

# Define replacements
declare -A REPLACEMENTS=(
    ***REMOVED***
    ["***REMOVED***"]="{account-id}"
    
    # Email addresses
    ["***REMOVED***"]="{admin-email}"
    
    ***REMOVED***
    ["***REMOVED***"]="{api-id}"
    ["***REMOVED***"]="{api-id}"
    ["***REMOVED***"]="{api-id}"
    ["***REMOVED***"]="{api-id}"
    ["***REMOVED***"]="{api-id}"
    
    ***REMOVED***
    ["***REMOVED***"]="{distribution-id}"
    ["***REMOVED***"]="{distribution-id}"
    ["***REMOVED***"]="{distribution-id}"
    ["***REMOVED***"]="{distribution-id}"
    ["***REMOVED***"]="{cloudfront-id}"
    
    ***REMOVED***
    ["***REMOVED***"]="{region}_{pool-id}"
    ["***REMOVED***"]="{region}_{pool-id}"
    ["***REMOVED***"]="{region}_{pool-id}"
    ["***REMOVED***"]="{region}_{pool-id}"
    
    ***REMOVED***
    ["***REMOVED***"]="{client-id}"
    ["***REMOVED***"]="{client-id}"
    ["***REMOVED***"]="{client-id}"
    
    ***REMOVED***
    ["***REMOVED***"]="{region}:{identity-pool-id}"
    
    # Test credentials
    ["***REMOVED***"]="{test-username}"
    ["***REMOVED***"]="{test-password}"
    
    # Specific stack/bucket names
    ["aws-elasticdrs-orchestrator-dev"]="aws-elasticdrs-orchestrator-{environment}"
    ["aws-elasticdrs-orchestrator-test"]="aws-elasticdrs-orchestrator-{environment}"
    ["aws-elasticdrs-orchestrator-cicd-artifacts-***REMOVED***-dev"]="{project-name}-cicd-artifacts-{account-id}-{environment}"
    ["drsorchv4-fe-***REMOVED***-test"]="{project-name}-fe-{account-id}-{environment}"
)

# Find all markdown files in docs/
FILES=$(find docs/ -type f -name "*.md")

# Count files
TOTAL_FILES=$(echo "$FILES" | wc -l | tr -d ' ')
echo "Found $TOTAL_FILES documentation files to sanitize"

# Process each file
MODIFIED_COUNT=0
for file in $FILES; do
    MODIFIED=false
    
    # Create backup
    cp "$file" "$file.bak"
    
    # Apply each replacement
    for search in "${!REPLACEMENTS[@]}"; do
        replace="${REPLACEMENTS[$search]}"
        
        # Use sed to replace (macOS compatible)
        if grep -q "$search" "$file" 2>/dev/null; then
            sed -i '' "s|$search|$replace|g" "$file"
            MODIFIED=true
        fi
    done
    
    if [ "$MODIFIED" = true ]; then
        echo "✓ Sanitized: $file"
        ((MODIFIED_COUNT++))
        rm "$file.bak"
    else
        # Restore from backup if no changes
        mv "$file.bak" "$file"
    fi
done

echo ""
echo "=== Sanitization Complete ==="
echo "Modified files: $MODIFIED_COUNT / $TOTAL_FILES"
echo ""
echo "Review changes with: git diff docs/"
