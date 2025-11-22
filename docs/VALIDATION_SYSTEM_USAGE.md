# Validation System Usage Guide

## Overview

This project now includes a comprehensive validation system to prevent file corruption during editing, especially for complex TypeScript/JSX files.

## Components

### 1. Pre-commit Hooks (.pre-commit-config.yaml)
Automatically validates files before they're committed:
- TypeScript syntax checking
- JSX corruption pattern detection
- CloudFormation linting
- Python syntax validation
- General file checks (trailing whitespace, large files, etc.)

**Installation:**
```bash
pip install pre-commit
pre-commit install
```

**Usage:** Runs automatically on `git commit`

**Bypass (emergency only):**
```bash
git commit --no-verify -m "emergency fix"
```

### 2. Validation Scripts

#### check-jsx-corruption.sh
Detects common JSX corruption patterns:
- Unclosed tags
- Props outside components
- Invalid spread operators
- Mismatched braces

**Usage:**
```bash
./scripts/check-jsx-corruption.sh <file.tsx>
```

#### verify-tsx.sh
Validates TypeScript syntax using the TypeScript compiler:

**Usage:**
```bash
./scripts/verify-tsx.sh <file.tsx>
```

#### safe-edit.sh
Complete safe editing workflow with validation:

**Usage:**
```bash
./scripts/safe-edit.sh <filename>
```

**What it does:**
1. Checks git status
2. Creates timestamped backup
3. Opens file in editor
4. Validates changes after editing
5. Shows git diff
6. Runs appropriate validators based on file type
7. Reports success/failure

### 3. NPM Scripts

**Type checking:**
```bash
cd frontend && npm run type-check
```

Validates all TypeScript files without building.

## Recommended Workflows

### Safe File Editing
```bash
# Best practice - uses safe-edit wrapper
./scripts/safe-edit.sh frontend/src/components/WaveConfigEditor.tsx

# Manual validation after editing
npm run type-check
./scripts/check-jsx-corruption.sh frontend/src/components/WaveConfigEditor.tsx
```

### Before Committing
```bash
# Check specific file
./scripts/verify-tsx.sh frontend/src/components/WaveConfigEditor.tsx

# Run all pre-commit checks manually
pre-commit run --all-files
```

### After Editing Critical Files
```bash
# 1. Validate syntax
cd frontend && npm run type-check

# 2. Test build
npm run build

# 3. If successful, commit
git add <file>
git commit -m "fix: description"
```

## File Type Support

| Extension | Validation |
|-----------|------------|
| .tsx, .jsx | JSX corruption check + TypeScript validation |
| .ts, .js | TypeScript/JavaScript syntax check |
| .py | Python syntax validation |
| .yaml, .yml | YAML validation + cfn-lint for CloudFormation |
| .json | JSON syntax validation |

## Troubleshooting

### Pre-commit Hook Fails
```bash
# See what failed
pre-commit run --all-files

# Fix issues, then retry
git add <fixed-files>
git commit
```

### TypeScript Errors
```bash
# Get detailed errors
cd frontend && npm run type-check

# Check specific file
npx tsc --noEmit src/components/WaveConfigEditor.tsx
```

### JSX Corruption Detected
```bash
# Review the specific line numbers shown
# Check for:
# - Incomplete component tags
# - Props outside component boundaries
# - Missing closing braces
```

### Safe Edit Backup Recovery
If validation fails and you need to restore:
```bash
# Find backup
ls -lt <filename>.backup.*

# Restore
cp <filename>.backup.TIMESTAMP <filename>
```

## Best Practices

1. **Always use safe-edit.sh for critical files** - Provides automatic validation
2. **Run type-check before committing** - Catches TypeScript errors early
3. **Never force-push without validation** - Pre-commit hooks exist for a reason
4. **Keep backups** - safe-edit.sh creates them automatically
5. **Test build after changes** - Syntax valid ≠ app works

## Emergency Procedures

If you absolutely must commit without validation:
```bash
git commit --no-verify -m "emergency: description"
```

**But:** Document why in the commit message and fix validation issues ASAP.

## Integration with CI/CD

The validation system integrates with deployment workflows:
1. Pre-commit hooks prevent bad commits
2. Type-check validates before build
3. Build process catches remaining issues
4. Tests validate functionality

This creates multiple safety layers to prevent deployment of broken code.
