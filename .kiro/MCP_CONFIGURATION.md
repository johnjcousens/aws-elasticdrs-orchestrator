# MCP Configuration for AWS DRS Orchestration

**Configuration File**: `.kiro/settings/mcp.json`
**Last Updated**: November 30, 2024

## Enabled MCPs

### 1. Code Explorer MCP
**Purpose**: Code location, search, and structure analysis
**Triggers**: "find", "locate", "search", "where" + code elements

**Available Tools**:
- `find_code_element` - Find functions, classes, methods, variables, imports
- `locate_file` - Find files by name or pattern
- `explore_directory_structure` - Analyze project structure
- `get_file_with_history` - Find files with historical context
- `find_code_with_context` - Search code with pattern indicators

**Use Cases**:
- "Find the User class"
- "Where is authentication defined?"
- "Locate config.json"

### 2. Research Documenter MCP
**Purpose**: API and library research with documentation
**Triggers**: "integrate", "library", "API", "documentation", "framework"

**Available Tools**:
- `research_api_integration` - Research API implementation patterns
- `research_library_documentation` - Find library usage examples
- `research_aws_service` - AWS service integration guidance
- `generate_integration_guide` - Create step-by-step guides
- `find_best_practices` - Discover implementation best practices
- `check_previous_research` - Check for prior research
- `research_with_memory` - Research with memory enhancement

**Use Cases**:
- "Integrate Stripe API"
- "Add React Router"
- "Use AWS S3"

### 3. Context Historian MCP
**Purpose**: Session management and context preservation
**Triggers**: "checkpoint", "remember this", "save state", "snapshot"

**Available Tools**:
- `create_checkpoint` - Create comprehensive checkpoint with conversation export
- `export_conversation` - Export current conversation with metadata
- `recall_context` - Retrieve context from previous sessions
- `summarize_session` - Summarize current session activities
- `manage_session_memory` - Manage session memory and context
- `semantic_search` - Search conversation history with natural language
- `query_memory` - Query hybrid memory system
- `find_similar_sessions` - Find sessions similar to a given session
- `get_memory_stats` - Get memory system statistics
- `index_history` - Manually trigger indexing

**Use Cases**:
- "Create checkpoint"
- "Remember this decision"
- "What did we do last session?"
- Type "snapshot" for automated workflow

### 4. CFN Linter Automation
**Purpose**: CloudFormation template validation and compliance
**Triggers**: CloudFormation validation requests

**Available Tools**:
- `scan_repositories` - Discover and analyze CloudFormation content
- `apply_validation_infrastructure` - Apply validation setup
- `check_repository_compliance` - Audit against standards
- `bulk_update_repositories` - Apply updates across repos

**Use Cases**:
- "Validate CloudFormation templates"
- "Check repository compliance"
- "Scan for CFN templates"

### 5. Playwright Browser MCP
**Purpose**: Browser automation and testing
**Triggers**: URLs, "test website", "fill form", "click button"

**Available Tools**: 45+ browser automation tools including:
- `navigate` - Navigate to URLs
- `click_element` - Click elements
- `fill_input` - Fill form fields
- `take_screenshot` - Capture screenshots
- `get_element_text` - Get element text
- `evaluate_javascript` - Execute JavaScript
- And many more...

**Use Cases**:
- "Test https://example.com"
- "Fill the login form"
- "Take a screenshot of the page"

### 6. Token Monitor MCP
**Purpose**: Token usage tracking and optimization
**Configuration**:
- Primary Threshold: 75%
- Safety Threshold: 80%

**Available Tools**:
- `mcp_get_token_status` - Parse and analyze token usage
- `mcp_check_threshold_status` - Check if threshold reached
- `mcp_configure_thresholds` - Update monitoring thresholds
- `mcp_start_monitoring` - Start background monitoring
- `mcp_stop_monitoring` - Stop background monitoring
- `mcp_get_monitor_status` - Get monitoring status
- `mcp_validate_file_read` - Validate file read safety
- `mcp_validate_batch_read` - Validate batch read safety

**Use Cases**:
- Automatic token usage monitoring
- Alerts when approaching limits
- File read validation
- Context optimization suggestions

### 7. Demo Cache Safe MCP
**Purpose**: Hot-reloadable logic demonstrations
**Available Tools**:
- `mcp_process_data` - Process data with hot-reloadable logic
- `mcp_search_files` - Search files with hot-reloadable logic
- `mcp_analyze_code` - Analyze code with hot-reloadable logic

## Configuration Details

### Python MCPs
All Python-based MCPs use:
- **Python**: `/Users/jocousen/.local/share/mise/installs/python/3.12.11/bin/python3.12`
- **Base Path**: `/Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS/Cline/MCP/`

### Node.js MCPs
- **Playwright Browser**: Uses Node.js runtime

## Usage

### Automatic Triggers
MCPs are automatically invoked based on your requests:
- Code search keywords → Code Explorer MCP
- Integration requests → Research Documenter MCP
- Checkpoint requests → Context Historian MCP
- CloudFormation validation → CFN Linter Automation
- URLs or browser testing → Playwright Browser MCP
- Token monitoring → Token Monitor MCP (always active)

### Manual Invocation
You can also explicitly request MCP usage:
- "Use Code Explorer to find..."
- "Research with Research Documenter..."
- "Create checkpoint with Context Historian..."

## Fallback Strategies

If an MCP fails or times out, Kiro automatically falls back to:
- Native Kiro tools (file search, grep, etc.)
- Alternative MCPs when applicable
- Manual operations as last resort

**You'll never see MCP failures** - they're handled transparently.

## Reloading MCPs

After configuration changes:
1. **Restart Kiro** - Recommended for clean reload
2. **Reload MCP Servers** - Use Kiro command palette: "MCP: Reload Servers"
3. **Check MCP Status** - Use Kiro MCP Server view in feature panel

## Troubleshooting

### MCP Not Working?
1. Check if MCP server is running in Kiro MCP Server view
2. Verify Python/Node.js paths are correct
3. Check MCP server logs for errors
4. Restart Kiro to reload configuration

### Configuration Errors?
1. Validate JSON syntax: `python3 -m json.tool .kiro/settings/mcp.json`
2. Check file paths exist
3. Verify Python/Node.js installations

### Need More MCPs?
Additional MCPs available in global directory:
- CDK MCP Server
- CFN MCP Server
- Cost Analysis MCP Server
- Cost Explorer MCP Server
- Terraform MCP Server

To enable, add their configuration to `.kiro/settings/mcp.json` following the same pattern.

## Benefits

✅ **Automated Code Discovery**: Find code elements instantly
✅ **Research Integration**: API and library research on-demand
✅ **Context Preservation**: Never lose session context
✅ **CloudFormation Validation**: Automated template validation
✅ **Browser Testing**: Automated web testing
✅ **Token Optimization**: Prevent context overflow
✅ **Seamless Experience**: Automatic fallbacks, no failures exposed

---

**Status**: ✅ All MCPs Enabled and Ready
**Configuration**: `.kiro/settings/mcp.json`
**Global Rules**: `.kiro/global-rules/direct-mcp-usage.md`
