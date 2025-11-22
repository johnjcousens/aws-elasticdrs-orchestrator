# Safe File Editing Guide

## Purpose
This guide prevents file corruption when making code changes, especially to JSX/TSX files.

## Quick Reference: Tool Selection

| File Type | Change Type | Recommended Tool | Avoid |
|-----------|-------------|------------------|-------|
| **JSX/TSX** | Multi-line changes | `replace_in_file` | `sed` append |
| **JSX/TSX** | Single character | `sed 's/old/new/'` | Manual edits |
| **JSON/YAML** | Any changes | `replace_in_file` | `sed` |
| **Markdown** | Any changes | Either tool | - |
| **Python** | Multi-line | `replace_in_file` | `sed` append |

## Golden Rules

### 1. Verify After EVERY Edit
```bash
# Check specific lines
sed -n 'start,end p' filename.tsx

# Verify TypeScript syntax
cd frontend && npm run type-check

# Check git diff
git diff filename.tsx
```

### 2. One Change at a Time
- ❌ **Bad**: Multiple stacked sed operations
- ✅ **Good**: Single change → verify → next change

### 3. Always Have Clean Git State
```bash
# Before any complex edits:
git status  # Should be clean
git diff    # Should be empty

# After corruption:
git checkout filename.tsx  # Quick restore
```

## Tool-Specific Guidelines

### Using `replace_in_file`

**Best For:**
- Multi-line changes
- Structural modifications
- JSX/TSX prop changes

**Critical Rules:**
1. Include FULL context in SEARCH block
2. Match indentation exactly
3. Include complete lines (no truncation)
4. Test the replacement pattern first

**Example - Safe onChange Fix:**
```xml
<replace_in_file>
<path>frontend/src/components/WaveConfigEditor.tsx</path>
<diff>
------- SEARCH
                      onChange={(_event, newValue) => {
                        const pgIds = newValue.map(pg => pg.protectionGroupId);
                        handleUpdateWave(wave.waveNumber, 'protectionGroupIds', pgIds);
                      }}
=======
                      onChange={(event, newValue) => {
                        console.log('🔵 onChange fired!', { newValue });
                        const pgIds = newValue.map(pg => pg.protectionGroupId);
                        handleUpdateWave(wave.waveNumber, 'protectionGroupIds', pgIds);
                      }}
+++++++ REPLACE
</diff>
</replace_in_file>
```

### Using `sed`

**Best For:**
- Single character/word replacements
- Simple string substitutions
- Configuration file updates

**Safe Patterns:**
```bash
# ✅ Simple substitution
sed -i '' 's/_event/event/' file.tsx

# ✅ Line-specific change
sed -i '' '370s/_event/event/' file.tsx

# ⚠️ Use with caution - simple append at end
sed -i '' '$ a\new line' file.txt

# ❌ AVOID - Append in middle of JSX
sed -i '' '356 a\complex jsx code' file.tsx
```

**Dangerous Patterns to AVOID:**
```bash
# ❌ NEVER - Append in JSX props
sed -i '' '356 a\                      debug: true,' file.tsx

# ❌ NEVER - Multi-line inserts
sed -i '' '370 a\line1\nline2\nline3' file.tsx

# ❌ NEVER - Complex expressions in JSX
sed -i '' 's/$/\n    {...(() => {})}/' file.tsx
```

## JSX/TSX Specific Rules

### Why JSX is Different
- Structure-sensitive (whitespace matters)
- Requires complete expressions
- Props must be valid JavaScript
- Self-closing tags need proper syntax

### Common Corruption Patterns

**1. Broken Prop Syntax:**
```jsx
// ❌ Corrupted by sed append
<Autocomplete
  multiple
    (wave.protectionGroupIds || []).includes(pg.protectionGroupId)  // ← Missing value= 
  )}

// ✅ Correct
<Autocomplete
  multiple
  value={(protectionGroups || []).filter(pg => 
    (wave.protectionGroupIds || []).includes(pg.protectionGroupId)
  )}
```

**2. Invalid Spread in Props:**
```jsx
// ❌ Invalid JSX
<Component
  {...(() => { console.log('test'); return {}; })()}  // ← Cannot execute in JSX
/>

// ✅ Use useEffect instead
useEffect(() => {
  console.log('test');
}, [dependency]);
```

**3. Missing Closing Tags:**
```jsx
// ❌ Corrupted
<Component
  prop1={value}
  prop2={value}
// Missing closing />

// ✅ Complete
<Component
  prop1={value}
  prop2={value}
/>
```

## Verification Checklist

### After EVERY file edit:

- [ ] **Run syntax check**: `cd frontend && npm run type-check`
- [ ] **View the change**: `sed -n 'start,end p' filename.tsx`
- [ ] **Check git diff**: `git diff filename.tsx`
- [ ] **Build if critical**: `cd frontend && npm run build`

### Before deployment:

- [ ] **Full TypeScript check**: `npm run type-check`
- [ ] **Full build**: `npm run build`
- [ ] **Git commit**: Changes saved
- [ ] **Clean working tree**: `git status` shows clean

## Recovery Procedures

### Quick Recovery (Git)
```bash
# Restore single file
git checkout frontend/src/components/WaveConfigEditor.tsx

# Restore all changes
git reset --hard HEAD
```

### Manual Fix Required
```bash
# 1. Check what's broken
cd frontend && npm run type-check

# 2. View the damage
git diff filename.tsx

# 3. Decision:
#    - Small corruption: Fix manually
#    - Large corruption: git checkout, start over
```

## Pre-Commit Validation

The project includes pre-commit hooks that automatically:
- Validate TypeScript syntax
- Check for common corruption patterns
- Prevent commits with broken code

**To skip in emergency** (not recommended):
```bash
git commit --no-verify -m "emergency fix"
```

## Helper Scripts

### `scripts/safe-edit.sh`
Wrapper for safe file editing with automatic validation:
```bash
./scripts/safe-edit.sh filename.tsx
```

### `scripts/verify-tsx.sh`
Quick TypeScript syntax check:
```bash
./scripts/verify-tsx.sh frontend/src/components/WaveConfigEditor.tsx
```

## Real-World Examples

### Example 1: Simple Parameter Rename
```bash
# ✅ Safe approach
sed -i '' 's/_event/event/g' frontend/src/components/WaveConfigEditor.tsx
cd frontend && npm run type-check
git diff frontend/src/components/WaveConfigEditor.tsx
```

### Example 2: Adding Console Log
```bash
# ❌ Dangerous - sed append in JSX
sed -i '' '371 a\        console.log("test");' file.tsx

# ✅ Safe - use replace_in_file with full context
# (See replace_in_file examples above)
```

### Example 3: Multi-line JSX Change
```bash
# Always use replace_in_file for multi-line JSX
# Never stack sed operations
# Verify after each change
```

## When Things Go Wrong

### Symptoms of Corruption
- TypeScript errors: "Expected '>' but found"
- Missing closing tags
- Props appearing outside components
- Function calls in wrong locations

### Diagnosis Steps
1. Run `npm run type-check` to see all errors
2. Check `git diff` to see what changed
3. Look for incomplete JSX structures
4. Identify which edit caused the issue

### Fix Strategy
1. **Minor**: Fix manually if < 5 lines affected
2. **Major**: `git checkout filename`, start over
3. **Prevention**: Document what went wrong, update this guide

## Best Practices Summary

1. ✅ **Choose right tool** for file type
2. ✅ **Verify after each change** with type-check
3. ✅ **One change at a time** - no stacking
4. ✅ **Clean git state** before complex edits
5. ✅ **Full context** in replace_in_file blocks
6. ❌ **Never** use sed append in JSX
7. ❌ **Never** stack multiple sed operations
8. ❌ **Never** skip verification steps

## Project-Specific Notes

### WaveConfigEditor.tsx
- 460+ lines, complex nested JSX
- Use replace_in_file for ALL multi-line changes
- Always include full prop context
- Test build after any change

### RecoveryPlanDialog.tsx
- Similar complexity to WaveConfigEditor
- Same safety rules apply
- Multiple nested components

### API Files (lambda/index.py)
- Python is more forgiving than JSX
- Still verify syntax after changes
- Use replace_in_file for functions

---

**Last Updated**: November 22, 2024  
**Related**: `.pre-commit-config.yaml`, `scripts/safe-edit.sh`
