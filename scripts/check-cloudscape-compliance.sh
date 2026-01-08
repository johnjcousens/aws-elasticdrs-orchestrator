#!/bin/bash
# CloudScape Design System Compliance Check
# Ensures frontend code uses only CloudScape components and doesn't use prohibited UI libraries

# Don't use set -e because ((var++)) returns 1 when var is 0
# We handle exit codes explicitly at the end

FRONTEND_DIR="${1:-frontend/src}"
ERRORS=0
WARNINGS=0

echo "=== CloudScape Design System Compliance Check ==="
echo "Scanning: $FRONTEND_DIR"
echo ""

# Check for prohibited UI library imports
echo "📦 Checking for prohibited UI library imports..."

check_prohibited_lib() {
    local lib="$1"
    local lib_name="$2"
    
    matches=$(grep -rn "from ['\"]${lib}" "$FRONTEND_DIR" --include="*.tsx" --include="*.ts" 2>/dev/null || true)
    
    if [ -n "$matches" ]; then
        echo ""
        echo "❌ ERROR: Found prohibited library: $lib_name ($lib)"
        echo "$matches"
        return 1
    fi
    return 0
}

# Check each prohibited library
check_prohibited_lib "@mui/material" "Material UI (MUI)" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "@material-ui" "Material UI (legacy)" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "@chakra-ui" "Chakra UI" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "antd" "Ant Design" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "@ant-design" "Ant Design" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "react-bootstrap" "React Bootstrap" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "@blueprintjs" "Blueprint.js" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "semantic-ui-react" "Semantic UI React" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "@fluentui" "Fluent UI" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "primereact" "PrimeReact" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "rsuite" "React Suite" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "grommet" "Grommet" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "rebass" "Rebass" || ERRORS=$((ERRORS + 1))
check_prohibited_lib "theme-ui" "Theme UI" || ERRORS=$((ERRORS + 1))

# Check for inline styles that should use CloudScape tokens
echo ""
echo "🎨 Checking for inline styles (should use CloudScape tokens)..."
inline_styles=$(grep -rn "style={{" "$FRONTEND_DIR" --include="*.tsx" 2>/dev/null | head -20 || true)
if [ -n "$inline_styles" ]; then
    style_count=$(echo "$inline_styles" | wc -l)
    echo "⚠️  WARNING: Found $style_count inline style declarations"
    echo "   Consider using CloudScape Box component with design tokens instead"
    echo "   Examples of inline styles found:"
    echo "$inline_styles" | head -5
    WARNINGS=$((WARNINGS + 1))
fi

# Check for CSS files that might override CloudScape styles
echo ""
echo "📄 Checking for custom CSS files..."
css_files=$(find "$FRONTEND_DIR" -name "*.css" -o -name "*.scss" -o -name "*.sass" 2>/dev/null | grep -v "node_modules" || true)
if [ -n "$css_files" ]; then
    css_count=$(echo "$css_files" | wc -l)
    echo "⚠️  WARNING: Found $css_count custom CSS files"
    echo "   CloudScape provides complete styling - custom CSS may cause inconsistencies"
    echo "$css_files"
    WARNINGS=$((WARNINGS + 1))
fi

# Check for required CloudScape imports
echo ""
echo "✅ Verifying CloudScape component usage..."
cloudscape_imports=$(grep -rn "@cloudscape-design/components" "$FRONTEND_DIR" --include="*.tsx" 2>/dev/null | wc -l || echo "0")
echo "   Found $cloudscape_imports files importing CloudScape components"

if [ "$cloudscape_imports" -eq 0 ]; then
    echo "❌ ERROR: No CloudScape component imports found!"
    ERRORS=$((ERRORS + 1))
fi

# Check for common non-CloudScape patterns
echo ""
echo "🔍 Checking for non-CloudScape patterns..."

# Check for native HTML buttons (should use CloudScape Button)
native_buttons=$(grep -rn "<button" "$FRONTEND_DIR" --include="*.tsx" 2>/dev/null | grep -v "// cloudscape-ok" || true)
if [ -n "$native_buttons" ]; then
    button_count=$(echo "$native_buttons" | wc -l)
    echo "⚠️  WARNING: Found $button_count native <button> elements"
    echo "   Use CloudScape <Button> component instead"
    echo "$native_buttons" | head -3
    WARNINGS=$((WARNINGS + 1))
fi

# Check for native HTML inputs (should use CloudScape Input/FormField)
native_inputs=$(grep -rn "<input" "$FRONTEND_DIR" --include="*.tsx" 2>/dev/null | grep -v "// cloudscape-ok" || true)
if [ -n "$native_inputs" ]; then
    input_count=$(echo "$native_inputs" | wc -l)
    echo "⚠️  WARNING: Found $input_count native <input> elements"
    echo "   Use CloudScape <Input> or <FormField> components instead"
    echo "$native_inputs" | head -3
    WARNINGS=$((WARNINGS + 1))
fi

# Check for native HTML selects (should use CloudScape Select)
native_selects=$(grep -rn "<select" "$FRONTEND_DIR" --include="*.tsx" 2>/dev/null | grep -v "// cloudscape-ok" || true)
if [ -n "$native_selects" ]; then
    select_count=$(echo "$native_selects" | wc -l)
    echo "⚠️  WARNING: Found $select_count native <select> elements"
    echo "   Use CloudScape <Select> component instead"
    echo "$native_selects" | head -3
    WARNINGS=$((WARNINGS + 1))
fi

# Check for native HTML tables (should use CloudScape Table)
native_tables=$(grep -rn "<table" "$FRONTEND_DIR" --include="*.tsx" 2>/dev/null | grep -v "// cloudscape-ok" || true)
if [ -n "$native_tables" ]; then
    table_count=$(echo "$native_tables" | wc -l)
    echo "⚠️  WARNING: Found $table_count native <table> elements"
    echo "   Use CloudScape <Table> component instead"
    echo "$native_tables" | head -3
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "=== CloudScape Compliance Summary ==="
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "❌ FAILED: $ERRORS error(s) found"
    echo "   Please remove prohibited UI libraries and use CloudScape components only"
    echo ""
    echo "📚 CloudScape Documentation: https://cloudscape.design/components/"
    echo "📖 Frontend Standards: .kiro/steering/frontend-standards.md"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "⚠️  PASSED with $WARNINGS warning(s)"
    echo "   Consider addressing warnings for better CloudScape compliance"
    exit 0
else
    echo "✅ PASSED: Full CloudScape compliance"
    exit 0
fi
