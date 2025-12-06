# Kiro Global Rules - Quick Reference

## Available Global Rules

### 🏗️ Amazon Builder Context
**File**: `amazon-builder-context.md`
**Use when**: Working with Amazon internal systems

Key features:
- Brazil workspace management
- CRUX code review workflows
- Package dependencies
- Git best practices
- Conventional commit messages

### 🔧 Direct MCP Usage
**File**: `direct-mcp-usage.md`
**Use when**: Kiro automatically applies based on your requests

Automatic triggers:
- "Find", "locate", "search" → Code Explorer MCP
- "Integrate", "API", "library" → Research Documenter MCP
- "Checkpoint", "snapshot" → Context Historian MCP
- URLs or "test website" → Playwright Browser MCP

### 🏛️ MCP Architecture Alignment
**File**: `mcp-architecture-alignment.md`
**Use when**: Understanding MCP integration patterns

Key concepts:
- Client-orchestrated integration
- Indicator pattern (MCPs suggest queries, Kiro orchestrates)
- 33 integration tests across 3 MCPs
- Fallback strategies

### ✏️ Safe File Editing
**File**: `safe-file-editing.md`
**Use when**: Kiro automatically applies when editing files

Critical rules:
- JSX/TSX: Use `replace_in_file` with 10+ lines context
- Always validate after edits: `npm run type-check`
- Commit simple fixes FIRST before complex edits
- If `replace_in_file` fails twice, change strategy

Tool selection matrix:
| File Type | Change Type | Required Tool |
|-----------|-------------|---------------|
| JSX/TSX | Multi-line | `replace_in_file` |
| JSX/TSX | Single word | `sed 's/old/new/'` |
| JSON/YAML | Any | `replace_in_file` |

### 📸 Snapshot Workflow
**File**: `snapshot-workflow.md`
**Use when**: You type "snapshot"

Automated workflow:
1. Export conversation to checkpoint
2. Update PROJECT_STATUS.md
3. Check git repository status
4. AWS deployment (if applicable)
5. Git commit and push
6. Create new task with preserved context

### 🎭 Playwright Browser Automation
**File**: `playwright-browser-automation.md`
**Use when**: Testing websites or browser automation

Available actions:
- Navigate to URLs
- Click elements
- Fill forms
- Take screenshots
- Verify page content

### 📊 Token Threshold Management
**File**: `token-threshold-management.md`
**Use when**: Managing conversation context

Strategies:
- Monitor token usage
- Optimize context window
- Memory-efficient patterns

## Quick Commands

### Check Global Rules
```bash
# List all global rules
ls -la .kiro/global-rules/

# Read a specific rule
cat .kiro/global-rules/safe-file-editing.md

# List available MCPs
ls -la .kiro/global-mcps/mcp-servers/
```

### Snapshot Workflow
```bash
# Just type in chat:
snapshot

# Kiro will automatically:
# 1. Create checkpoint
# 2. Update PROJECT_STATUS.md
# 3. Deploy to AWS (if applicable)
# 4. Commit and push to git
# 5. Start new task with context
```

### Safe File Editing
```bash
# Kiro automatically:
# 1. Chooses correct tool based on file type
# 2. Validates after every edit
# 3. Reverts if validation fails
# 4. Commits after successful edits
```

### MCP Usage
```bash
# Kiro automatically uses MCPs when you say:
"Find the User class"           → Code Explorer MCP
"Integrate Stripe API"          → Research Documenter MCP
"Create checkpoint"             → Context Historian MCP
"Test https://example.com"      → Playwright Browser MCP
```

## Common Patterns

### Multi-Step File Edits
```
1. Simple fix (sed) → validate → COMMIT
2. Complex change (replace_in_file) → validate → COMMIT
3. If step 2 fails, step 1 is safe (already committed)
```

### Research Integration
```
1. Research API → Research Documenter MCP
2. Find existing code → Code Explorer MCP
3. Implement integration → Safe File Editing
4. Create checkpoint → Context Historian MCP
```

### Session Management
```
1. Work on feature
2. Type "snapshot" when done
3. Kiro creates checkpoint, commits, deploys
4. New task starts with full context
5. Zero context loss
```

## Rule Precedence

1. **Project steering rules** (`.kiro/steering/*.md`) - Highest
2. **Global rules** (`.kiro/global-rules/*.md`) - Medium
3. **System defaults** - Lowest

Project rules override global rules when conflicts exist.

## Troubleshooting

### Links Not Working?
```bash
# Verify links exist
ls -la .kiro/global-rules/
ls -la .kiro/global-mcps/mcp-servers/

# Recreate if needed
ln -s "/Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS/Cline/Rules/"* .kiro/global-rules/
ln -s "/Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS/Cline/MCP" .kiro/global-mcps/mcp-servers
```

### MCP Not Available?
- Check VS Code MCP configuration
- Verify MCP server is running
- Kiro will use fallback strategies automatically

### File Edit Failed?
- Kiro automatically reverts with `git checkout`
- Analyzes failure and retries with better approach
- You don't need to do anything

## Key Takeaways

✅ **Automatic**: Rules apply automatically based on context
✅ **Safe**: Validation and recovery built-in
✅ **Efficient**: Automated workflows reduce manual work
✅ **Consistent**: Same patterns across all projects
✅ **Documented**: Comprehensive documentation available

## Learn More

- **Full documentation**: `.kiro/GLOBAL_RULES_README.md`
- **Integration summary**: `.kiro/INTEGRATION_SUMMARY.md`
- **Individual rules**: `.kiro/global-rules/*.md`
- **MCP servers**: `.kiro/global-mcps/mcp-servers/*/README.md`

---

**Quick Reference**: Keep this handy for common patterns and commands
