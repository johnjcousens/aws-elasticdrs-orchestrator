#!/bin/bash
# Verify TypeScript/TSX syntax for specific files

set -e

EXIT_CODE=0

echo "🔍 Verifying TypeScript syntax..."

# Check if files provided
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <file1.tsx> [file2.tsx ...]"
    exit 1
fi

# Check if in frontend directory or need to cd
if [[ -d "frontend" ]]; then
    cd frontend
fi

# Verify npm dependencies installed
if [[ ! -d "node_modules" ]]; then
    echo "⚠️  Node modules not found. Run: npm install"
    exit 1
fi

# Check each file
for file in "$@"; do
    # Remove frontend/ prefix if present
    file_clean="${file#frontend/}"
    
    if [[ ! -f "$file_clean" ]]; then
        echo "⚠️  File not found: $file_clean"
        continue
    fi
    
    echo "  Checking: $file_clean"
    
    # Run TypeScript compiler check
    if ! npx tsc --noEmit "$file_clean" 2>&1 | grep -v "error TS6053"; then
        echo "✅ $file_clean: Syntax valid"
    else
        echo "❌ $file_clean: TypeScript errors detected"
        EXIT_CODE=1
    fi
done

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ All files passed TypeScript validation"
else
    echo "❌ Some files have TypeScript errors"
fi

exit $EXIT_CODE
