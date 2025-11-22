#!/bin/bash
# Safe file editing wrapper with automatic validation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🛡️  Safe Edit Wrapper"
echo ""

# Check if file provided
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <filename>"
    echo ""
    echo "This wrapper helps you safely edit files with automatic validation:"
    echo "  1. Checks git status (should be clean)"
    echo "  2. Opens file in editor"
    echo "  3. Validates changes after editing"
    echo "  4. Shows git diff"
    echo "  5. Confirms syntax is valid"
    exit 1
fi

FILE="$1"

# Check if file exists
if [[ ! -f "$FILE" ]]; then
    echo -e "${RED}❌ File not found: $FILE${NC}"
    exit 1
fi

# Get file extension
EXT="${FILE##*.}"

echo "📁 File: $FILE"
echo "📝 Type: $EXT"
echo ""

# Step 1: Check git status
echo "1️⃣  Checking git status..."
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Working directory has uncommitted changes${NC}"
    echo "   Recommendation: Commit or stash changes before editing"
    read -p "   Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Working directory clean${NC}"
fi
echo ""

# Step 2: Create backup
BACKUP="${FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "2️⃣  Creating backup: $BACKUP"
cp "$FILE" "$BACKUP"
echo ""

# Step 3: Open in editor
echo "3️⃣  Opening file in editor..."
echo "   Make your changes and save"
echo "   Press Enter when done editing..."
"${EDITOR:-code}" "$FILE"
read -p ""

# Step 4: Check if file was modified
if diff -q "$FILE" "$BACKUP" > /dev/null 2>&1; then
    echo -e "${YELLOW}ℹ️  No changes made${NC}"
    rm "$BACKUP"
    exit 0
fi

echo ""
echo "4️⃣  Changes detected. Validating..."
echo ""

# Step 5: Show diff
echo "📊 Changes made:"
git diff "$FILE" | head -50
echo ""

# Step 6: Validate based on file type
VALIDATION_PASSED=true

case "$EXT" in
    tsx|jsx)
        echo "🔍 Running JSX validation..."
        if ! ./scripts/check-jsx-corruption.sh "$FILE"; then
            VALIDATION_PASSED=false
        fi
        echo ""
        
        echo "🔍 Running TypeScript validation..."
        if ! ./scripts/verify-tsx.sh "$FILE"; then
            VALIDATION_PASSED=false
        fi
        ;;
        
    ts|js)
        echo "🔍 Running TypeScript validation..."
        cd frontend && npx tsc --noEmit "$FILE" 2>&1
        if [[ $? -ne 0 ]]; then
            VALIDATION_PASSED=false
        fi
        cd ..
        ;;
        
    py)
        echo "🔍 Running Python syntax check..."
        if ! python -m py_compile "$FILE"; then
            VALIDATION_PASSED=false
        fi
        ;;
        
    yaml|yml)
        echo "🔍 Running YAML validation..."
        if [[ "$FILE" == cfn/* ]]; then
            if ! cfn-lint "$FILE" 2>&1; then
                VALIDATION_PASSED=false
            fi
        else
            if ! python -c "import yaml; yaml.safe_load(open('$FILE'))" 2>&1; then
                VALIDATION_PASSED=false
            fi
        fi
        ;;
        
    json)
        echo "🔍 Running JSON validation..."
        if ! python -m json.tool "$FILE" > /dev/null 2>&1; then
            VALIDATION_PASSED=false
        fi
        ;;
esac

echo ""

# Step 7: Report results
if [[ "$VALIDATION_PASSED" == "true" ]]; then
    echo -e "${GREEN}✅ All validations passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review the changes above"
    echo "  2. Test if needed: cd frontend && npm run build"
    echo "  3. Commit: git add $FILE && git commit -m 'fix: description'"
    rm "$BACKUP"
else
    echo -e "${RED}❌ Validation failed!${NC}"
    echo ""
    echo "Options:"
    echo "  1. Fix the issues and run validation again"
    echo "  2. Restore backup: cp $BACKUP $FILE"
    echo "  3. Revert changes: git checkout $FILE"
    echo ""
    echo "Backup preserved at: $BACKUP"
    exit 1
fi
