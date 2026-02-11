#!/usr/bin/env python3
"""Remove patch.object wrappers for table variables from test file."""

import re


def remove_patch_wrappers(file_path: str) -> None:
    """Remove with patch.object(...) wrappers and dedent their contents."""

    with open(file_path, "r") as f:
        content = f.read()

    # Pattern to match the patch.object line
    # Matches: with patch.object(data_management_handler, "xxx_table", xxx_table):
    pattern = r'(\s+)with patch\.object\(data_management_handler, "[^"]+_table", [^)]+\):\n'

    changes = 0
    while True:
        match = re.search(pattern, content)
        if not match:
            break

        indent = match.group(1)
        start = match.start()
        end = match.end()

        # Find the indented block after this with statement
        # Look for lines with indent + 4 spaces
        block_indent = indent + "    "
        lines_after = content[end:].split("\n")

        # Collect the block lines
        block_lines = []
        for line in lines_after:
            if line.startswith(block_indent) or line.strip() == "":
                # Part of the block - dedent by 4 spaces
                if line.startswith(block_indent):
                    block_lines.append(line[4:])
                else:
                    block_lines.append(line)
            else:
                # End of block
                break

        # Replace the with statement and its block with just the dedented block
        block_text = "\n".join(block_lines)
        content = (
            content[:start]
            + block_text
            + "\n"
            + content[
                end + len("\n".join(lines_after[: len(block_lines)])) + 1 :
            ]
        )
        changes += 1
        print(f"Removed patch wrapper #{changes}")

    with open(file_path, "w") as f:
        f.write(content)

    print(f"\nTotal: Removed {changes} patch.object wrappers")


if __name__ == "__main__":
    remove_patch_wrappers("tests/unit/test_data_management_new_operations.py")
