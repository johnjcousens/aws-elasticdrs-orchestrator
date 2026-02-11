#!/usr/bin/env python3
"""
Remove incorrect patch.object calls for table variables from test file.

Tests using @mock_aws decorator don't need patch.object calls for table variables
because moto automatically mocks boto3, so the getter functions automatically use moto tables.
"""

import re


def remove_table_patches(file_path: str) -> None:
    """Remove patch.object calls for table variables and dedent code blocks."""

    with open(file_path, "r") as f:
        content = f.read()

    # Pattern to match patch.object calls for table variables
    # Matches: with patch.object(data_management_handler, "protection_groups_table", pg_table):
    # or: with patch.object(data_management_handler, "target_accounts_table", ta_table):
    table_patch_pattern = r'    with patch\.object\(data_management_handler, "[a-z_]+_table", [a-z_]+\):\n'

    # Find all occurrences
    matches = list(re.finditer(table_patch_pattern, content))
    print(f"Found {len(matches)} table patch.object calls to remove")

    # Process from end to start to maintain positions
    for match in reversed(matches):
        start = match.start()
        end = match.end()

        # Find the indented block after this with statement
        # Look for the next line and determine its indentation
        lines_after = content[end:].split("\n")

        # Remove the with statement line
        content = content[:start] + content[end:]

        # Now dedent the block that was inside the with statement
        # Find the block by looking for consistent indentation
        lines = content[start:].split("\n")

        dedented_lines = []
        in_block = True
        for i, line in enumerate(lines):
            if i == 0:
                # First line after removal
                dedented_lines.append(line)
                continue

            # Check if line is part of the block (has 8 spaces of indentation)
            if in_block and line.startswith("        ") and line.strip():
                # Dedent by 4 spaces
                dedented_lines.append(line[4:])
            elif in_block and not line.strip():
                # Empty line
                dedented_lines.append(line)
            elif in_block and not line.startswith("        "):
                # End of block
                in_block = False
                dedented_lines.append(line)
            else:
                dedented_lines.append(line)

        # Reconstruct content
        content = content[:start] + "\n".join(dedented_lines)

    # Write back
    with open(file_path, "w") as f:
        f.write(content)

    print(
        f"Removed {len(matches)} patch.object calls and dedented code blocks"
    )


if __name__ == "__main__":
    test_file = "tests/unit/test_data_management_new_operations.py"
    remove_table_patches(test_file)
    print(f"✓ Updated {test_file}")
