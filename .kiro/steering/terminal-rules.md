# Terminal and Output Rules

## CRITICAL: Minimize All Output

To avoid exhausting tokens and crashing the terminal, follow these rules strictly.

## Output Suppression

### Redirect Output to /dev/null
```bash
# Suppress stdout
command > /dev/null

# Suppress stderr
command 2>/dev/null

# Suppress both
command > /dev/null 2>&1
```

### Use Quiet/Silent Flags
```bash
# Git
git --no-pager push -q
git --no-pager pull -q
git --no-pager fetch -q

# npm
npm install --silent
npm run build --silent

# AWS CLI
AWS_PAGER="" aws s3 sync ... --quiet
```

### Limit Output
```bash
# Only show last N lines
command | tail -5

# Only show first N lines
command | head -5

# Count instead of list
command | wc -l
```

## Git Commands

### Always Use
```bash
git --no-pager status -s          # Short status
git --no-pager log --oneline -5   # Compact log
git --no-pager diff --stat        # Summary only
git --no-pager push -q            # Quiet push
git --no-pager pull -q            # Quiet pull
```

### Long Commit Messages
```bash
# NEVER use: git commit -m "long message..."
# ALWAYS use temp file:
# 1. fsWrite to .git_commit_msg.txt
# 2. git --no-pager commit -F .git_commit_msg.txt
# 3. rm .git_commit_msg.txt
```

## AWS CLI Commands

### Always Use
```bash
AWS_PAGER="" aws ...              # Disable pager
--output text                     # Minimal output format
--query 'field'                   # Extract specific fields
--no-cli-pager                    # Alternative pager disable
```

### Suppress Verbose Output
```bash
# S3 sync quietly
AWS_PAGER="" aws s3 sync ... --quiet > /dev/null 2>&1

# CloudFormation deploy (capture only status)
AWS_PAGER="" aws cloudformation deploy ... > /dev/null 2>&1
echo $?  # Just check exit code
```

## Chat Window Rules

### MINIMIZE Responses
- Don't repeat what you're about to do
- Don't explain each step
- Don't show file contents after writing
- Report only final summary

### Work Silently
- Make edits without commentary
- Batch multiple file edits
- Report completion, not progress

### Summary Format
```
✅ Done: [brief description]
```

## Terminal Connection Rules

### Avoid Disconnection
1. **No long inline arguments** - Use temp files
2. **No command chaining** - No `&&`, `||`, `;`
3. **No `cd` command** - Use `path` parameter
4. **No interactive commands** - No `less`, `vim`, `nano`
5. **No watch/follow modes** - No `-f`, `--watch`, `--follow`

### Pager Prevention
```bash
# Git - always prefix
git --no-pager ...

# AWS CLI - always set
AWS_PAGER="" aws ...

# General - pipe to cat if needed
command | cat
```

## File Operations

### Don't Open in Editor
- Use fsWrite/strReplace only
- Never open files in editor window
- Avoid autocomplete issues

### Batch Operations
- Combine related edits
- Use strReplace for targeted changes
- Minimize file read/write cycles
