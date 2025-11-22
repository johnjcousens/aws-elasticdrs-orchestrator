#!/bin/bash
# Check for common JSX corruption patterns

set -e

EXIT_CODE=0

echo "🔍 Checking for JSX corruption patterns..."

for file in "$@"; do
    if [[ ! -f "$file" ]]; then
        continue
    fi
    
    # Check 1: Unclosed JSX tags
    if grep -n '<[A-Z][a-zA-Z]*[^/>]*$' "$file" | grep -v '>' | grep -v '//' > /dev/null 2>&1; then
        echo "❌ $file: Potential unclosed JSX tag detected"
        EXIT_CODE=1
    fi
    
    # Check 2: Props outside component tags
    if grep -n '^\s\+[a-z][a-zA-Z]*=' "$file" | grep -v '<' > /dev/null 2>&1; then
        echo "⚠️  $file: Potential prop outside component"
        # Not failing, just warning
    fi
    
    # Check 3: Invalid spread operators in props
    if grep -n '\.\.\.(()' "$file" > /dev/null 2>&1; then
        echo "❌ $file: Invalid spread operator pattern detected"
        EXIT_CODE=1
    fi
    
    # Check 4: Missing closing braces in JSX
    OPEN_BRACES=$(grep -o '{' "$file" | wc -l | tr -d ' ')
    CLOSE_BRACES=$(grep -o '}' "$file" | wc -l | tr -d ' ')
    if [[ $OPEN_BRACES -ne $CLOSE_BRACES ]]; then
        echo "⚠️  $file: Mismatched braces (${OPEN_BRACES} open, ${CLOSE_BRACES} close)"
        # Not failing, could be legitimate multiline
    fi
done

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ No JSX corruption patterns detected"
fi

exit $EXIT_CODE
