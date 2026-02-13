# Amazon Q MCP Server Manual Configuration Guide

## Overview
This guide provides step-by-step instructions to manually add all 10 MCP servers to Amazon Q through the UI.

## Prerequisites
- All MCP servers are symlinked in `~/.amazonq/`
- Amazon Q extension is installed in Kiro

## Configuration Steps

### 1. research-documenter-mcp
**Name:** `research-documenter-mcp`

**Command:** `/Users/jocousen/.local/share/mise/installs/python/3.12.11/bin/python3.12`

**Args:** `/Users/jocousen/.amazonq/research-documenter-mcp/server.py`

**Environment Variables:**
- `PYTHONPATH` = `/Users/jocousen/.amazonq/research-documenter-mcp`

---

### 2. context-historian-mcp
**Name:** `context-historian-mcp`

**Command:** `/Users/jocousen/.local/share/mise/installs/python/3.12.11/bin/python3.12`

**Args:** `/Users/jocousen/.amazonq/context-historian-mcp/server.py`

**Environment Variables:**
- `PYTHONPATH` = `/Users/jocousen/.amazonq/context-historian-mcp`

---

### 3. cfn-linter-automation
**Name:** `cfn-linter-automation`

**Command:** `/Users/jocousen/.local/share/mise/installs/python/3.12.11/bin/python3.12`

**Args:** `/Users/jocousen/.amazonq/cfn-linter-automation/server.py`

**Environment Variables:**
- `PYTHONPATH` = `/Users/jocousen/.amazonq/cfn-linter-automation`

---

### 4. demo-cache-safe-mcp
**Name:** `demo-cache-safe-mcp`

**Command:** `/Users/jocousen/.local/share/mise/installs/python/3.12.11/bin/python3.12`

**Args:** `/Users/jocousen/.amazonq/demo-cache-safe-mcp/server.py`

**Environment Variables:**
- `PYTHONPATH` = `/Users/jocousen/.amazonq/demo-cache-safe-mcp`

---

### 5. aws-diagram-mcp
**Name:** `aws-diagram-mcp`

**Command:** `/Users/jocousen/.amazonq/aws-diagram-mcp/.venv/bin/python`

**Args (multiple, add in order):**
1. `-m`
2. `aws_diagram_mcp.server`

**Working Directory:** `/Users/jocousen/.amazonq/aws-diagram-mcp`

**Environment Variables:**
- `DIAGRAM_OUTPUT_DIR` = `/Users/jocousen/Documents/diagrams`

---

### 6. playwright-browser
**Name:** `playwright-browser`

**Command:** `node`

**Args:** `/Users/jocousen/.amazonq/playwright-browser/build/index.js`

**Environment Variables:** (none)

---

### 7. aws-iac-mcp
**Name:** `aws-iac-mcp`

**Command:** `uvx`

**Args:** `awslabs.aws-iac-mcp-server@latest`

**Environment Variables:**
- `AWS_PROFILE` = `default`
- `FASTMCP_LOG_LEVEL` = `ERROR`

---

### 8. aws-documentation-mcp
**Name:** `aws-documentation-mcp`

**Command:** `uvx`

**Args:** `awslabs.aws-documentation-mcp-server@latest`

**Environment Variables:**
- `FASTMCP_LOG_LEVEL` = `ERROR`

---

### 9. notebooklm
**Name:** `notebooklm`

**Command:** `npx`

**Args (multiple, add in order):**
1. `-y`
2. `@roomi-fields/notebooklm-mcp`

**Environment Variables:** (none)

---

### 10. builder-mcp
**Name:** `builder-mcp`

**Command:** `/Users/jocousen/.amazonq/builder-mcp`

**Args:** (none)

**Environment Variables:**
- `TOOL_PERSONALIZATION_ENABLED` = `true`
- `TOOL_PERSONALIZATION_ROLLOUT_PERCENTAGE` = `100`
- `TOOL_PERSONALIZATION_TRAINING_DAYS` = `0`
- `TOOL_PERSONALIZATION_MIN_EXECUTIONS` = `0`

---

## How to Add Each MCP

1. Open Amazon Q chat panel
2. Click "Configure MCP Servers" button
3. Click "Add Server" or "+" button
4. Fill in the fields:
   - **Name:** Copy from above
   - **Command:** Copy from above
   - **Args:** Copy from above (add multiple args separately if needed)
   - **Environment Variables:** Click "Add Variable" for each key-value pair
5. Click "Save" or "Add"
6. Repeat for all 9 remaining MCPs

## Verification

After adding all MCPs, you should see 11 total servers in the "Configure MCP Servers" dialog:
- ✅ code-explorer-mcp (already added)
- ✅ research-documenter-mcp
- ✅ context-historian-mcp
- ✅ cfn-linter-automation
- ✅ demo-cache-safe-mcp
- ✅ aws-diagram-mcp
- ✅ playwright-browser
- ✅ aws-iac-mcp
- ✅ aws-documentation-mcp
- ✅ notebooklm
- ✅ builder-mcp

## Troubleshooting

If an MCP fails to add:
1. Verify the command path exists: `ls -la <command_path>`
2. Verify the args path exists: `ls -la <args_path>`
3. Check for typos in environment variable names
4. Restart Amazon Q and try again

## Notes

- The symlinks in `~/.amazonq/` point to `/Users/jocousen/Documents/AgenticAI/MCP/`
- All Python MCPs use the same Python interpreter from mise
- AWS MCPs (aws-iac-mcp, aws-documentation-mcp) use `uvx` for automatic dependency management
- notebooklm uses `npx` for automatic dependency management
