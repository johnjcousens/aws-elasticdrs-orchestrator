# Global Rules Integration

This directory contains symbolic links to global Cline rules and MCP servers that are shared across all projects.

## Structure

```
.kiro/
├── steering/              # Project-specific steering rules
│   ├── product.md
│   ├── structure.md
│   └── tech.md
├── global-rules/          # Symbolic links to global Cline rules
│   ├── amazon-builder-context.md
│   ├── direct-mcp-usage.md
│   ├── mcp-architecture-alignment.md
│   ├── playwright-browser-automation.md
│   ├── safe-file-editing.md
│   ├── snapshot-workflow.md
│   └── token-threshold-management.md
└── global-mcps/           # Symbolic links to global MCP servers
    └── mcp-servers/       # Links to all MCP server implementations
```

## Global Rules

These rules are symlinked from `/Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS/Cline/Rules/`:

### 1. amazon-builder-context.md
- Amazon internal development systems (Brazil, CRUX, Coral, Apollo, Pipelines)
- Brazil workspace and package structure
- Code review (CRUX) workflows
- Package dependencies management
- Git command execution patterns
- Commit message conventions (Conventional Commits)
- Git repository integrity rules

### 2. direct-mcp-usage.md
- MCP server usage patterns and automation triggers
- Code Explorer MCP for code location and search
- Research Documenter MCP for API and library research
- Context Historian MCP for session management
- Browser Automation (Playwright MCP)
- CloudFormation Validation (CFN Linter Automation)
- Fallback strategies when MCPs fail
- Client-orchestrated integration patterns

### 3. mcp-architecture-alignment.md
- Alignment principles between rules and MCP implementations
- Implementation verification checklists
- Architecture change management
- Integration test suite (33 tests across 3 MCPs)
- Indicator pattern architecture
- Quality assurance standards

### 4. safe-file-editing.md
- Tool selection matrix for different file types
- Mandatory context requirements for replace_in_file
- Validation requirements after every edit
- Forbidden patterns (sed append in JSX/TSX, etc.)
- Recovery protocols for file corruption
- Git state requirements and critical revert lessons
- Multi-step edit workflows
- Repeated failure pattern recognition

### 5. snapshot-workflow.md
- Automated workflow for creating project snapshots
- Checkpoint creation with context-historian-mcp
- PROJECT_STATUS.md update automation
- Git repository status checking
- AWS deployment via CloudFormation (conditional)
- Automated git workflow integration
- Conventional commit message format
- Context preservation in checkpoints

### 6. token-threshold-management.md
- Token usage monitoring and optimization
- Threshold management strategies
- Context window optimization
- Memory-efficient conversation patterns

## Global MCPs

The `global-mcps/mcp-servers/` directory contains symbolic links to all MCP server implementations:

- **code-explorer-mcp**: Code location, search, and structure analysis
- **research-documenter-mcp**: API and library research with documentation
- **context-historian-mcp**: Session management and context preservation
- **playwright-browser**: Browser automation and testing
- **cfn-linter-automation**: CloudFormation template validation
- **token-monitor-mcp**: Token usage tracking and optimization
- And more...

## Usage

These rules are automatically available to Kiro when working in this project. The symbolic links ensure that:

1. **Global rules are always up-to-date**: Changes to global rules are immediately reflected in all projects
2. **Consistency across projects**: Same rules apply everywhere
3. **Easy maintenance**: Update once, apply everywhere
4. **Project-specific overrides**: Project steering rules can override global rules when needed

## Precedence

When conflicts exist between rules:

1. **Project-specific steering rules** (`.kiro/steering/*.md`) take highest precedence
2. **Global rules** (`.kiro/global-rules/*.md`) apply when no project-specific override exists
3. **System defaults** apply when neither project nor global rules specify behavior

## Maintenance

To update global rules:

1. Edit files in `/Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS/Cline/Rules/`
2. Changes are immediately reflected in all projects via symbolic links
3. No need to update individual projects

To add new global rules:

```bash
# From the global Cline directory
cd /Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS/Cline/Rules/
# Create new rule file
vim new-rule.md

# The symbolic link will automatically include it
```

## Integration with Kiro

Kiro automatically reads and applies these rules when:

- Making file edits (safe-file-editing.md)
- Using MCP servers (direct-mcp-usage.md, mcp-architecture-alignment.md)
- Creating snapshots (snapshot-workflow.md)
- Working with Amazon internal systems (amazon-builder-context.md)
- Managing token usage (token-threshold-management.md)

## Benefits

✅ **Consistency**: Same best practices across all projects
✅ **Maintainability**: Update once, apply everywhere
✅ **Safety**: Automated validation and error prevention
✅ **Efficiency**: Automated workflows reduce manual work
✅ **Context Preservation**: Session management and checkpoints
✅ **Quality**: Enforced standards and validation

## Notes

- Symbolic links are tracked in git (not the actual files)
- Global rules directory must exist for links to work
- If global rules directory is unavailable, Kiro falls back to project-specific rules only
- MCP servers must be configured in VS Code/Kiro MCP settings to be available

---

**Created**: November 30, 2024
**Purpose**: Document global rules integration for AWS DRS Orchestration project
**Maintained by**: Symbolic links to global Cline rules repository
