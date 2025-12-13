# NotebookLM MCP Server Installation Guide for Kiro

## Overview

This guide shows how to install and configure the NotebookLM MCP server for use with Kiro AI assistant.

## Prerequisites

- Node.js 18+ installed
- Google account (free)
- Kiro AI assistant access

## Installation Steps

### 1. Install NotebookLM MCP Server

```bash
# Install globally
npm install -g @modelcontextprotocol/server-notebooklm

# Or use npx (no installation required)
npx @modelcontextprotocol/server-notebooklm --version
```

### 2. Configure MCP Client

Create or update your MCP configuration file:

**Location**: `~/.config/mcp/config.json` (or your MCP client's config location)

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-notebooklm"],
      "env": {}
    }
  }
}
```

### 3. Authentication Setup

The NotebookLM MCP server uses your Google account authentication:

1. **First run** will prompt for Google login
2. **Browser window** will open for authentication
3. **Grant permissions** to access NotebookLM
4. **Token saved** automatically for future use

### 4. Verify Installation

Test the connection:

```bash
# Test server directly
npx @modelcontextprotocol/server-notebooklm

# Should show available tools:
# - notebooklm_upload_document
# - notebooklm_create_notebook
# - notebooklm_generate_audio
```

## Available Tools

### Upload Document
```bash
# Upload PDF, text, or web page
notebooklm_upload_document --url "https://example.com" --title "My Document"
```

### Create Notebook
```bash
# Create notebook from uploaded documents
notebooklm_create_notebook --title "Project Analysis" --document_ids "doc1,doc2"
```

### Generate Audio Discussion
```bash
# Generate AI podcast-style discussion
notebooklm_generate_audio --notebook_id "notebook123"
```

## Usage with Kiro

Once configured, you can use NotebookLM through Kiro:

```
# Upload project documentation
"Upload the AWS DRS documentation to NotebookLM"

# Create analysis notebook
"Create a NotebookLM notebook analyzing our DRS architecture"

# Generate audio summary
"Generate an audio discussion about our disaster recovery solution"
```

## Troubleshooting

### Authentication Issues
```bash
# Clear cached credentials
rm -rf ~/.config/notebooklm-mcp/

# Re-authenticate
npx @modelcontextprotocol/server-notebooklm
```

### Connection Problems
```bash
# Check Node.js version
node --version  # Should be 18+

# Reinstall server
npm uninstall -g @modelcontextprotocol/server-notebooklm
npm install -g @modelcontextprotocol/server-notebooklm
```

### MCP Client Issues
- Restart your MCP client after configuration changes
- Check config file syntax with JSON validator
- Verify file paths and permissions

## Configuration Options

### Environment Variables
```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-notebooklm"],
      "env": {
        "NOTEBOOKLM_TIMEOUT": "30000",
        "NOTEBOOKLM_MAX_RETRIES": "3"
      }
    }
  }
}
```

### Advanced Configuration
```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "node",
      "args": ["/path/to/notebooklm-server/index.js"],
      "cwd": "/path/to/working/directory",
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

## Security Notes

- **Google Authentication**: Uses OAuth2 with limited scope
- **Local Storage**: Credentials stored locally, not shared
- **Network Access**: Only connects to Google NotebookLM APIs
- **No API Keys**: No additional API keys required

## Cost

- **NotebookLM**: Free with Google account
- **MCP Server**: Free and open source
- **Usage Limits**: Subject to Google's free tier limits

## Support

- **MCP Server Issues**: https://github.com/modelcontextprotocol/servers/issues
- **NotebookLM Help**: https://support.google.com/notebooklm
- **Kiro Integration**: Contact your Kiro administrator

## Next Steps

1. **Upload Documentation**: Start with project README and architecture docs
2. **Create Notebooks**: Organize documents by topic or feature
3. **Generate Summaries**: Use AI to create project overviews
4. **Share Audio**: Generate discussions for team reviews

---

*This guide enables seamless integration between Kiro AI assistant and Google NotebookLM for enhanced document analysis and knowledge management.*