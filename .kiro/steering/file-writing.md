# File Writing Rules

## Don't Open Files in Editor

When creating or modifying files:

- **Just write the file** using fsWrite/strReplace tools
- **Do NOT open files in the editor window** after writing
- Opening files in editor tends to cause autocomplete issues

This applies to all file types: code, config, documentation, etc.
