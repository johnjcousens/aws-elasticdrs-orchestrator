#!/usr/bin/env python3
"""Fix indentation issues in test file caused by the previous script."""

from pathlib import Path


def fix_indentation():
    """Fix over-indented code in test functions."""
    test_file = Path("tests/unit/test_data_management_new_operations.py")
    content = test_file.read_text()

    # Pattern to find over-indented blocks after with statements
    # Look for lines that have 12+ spaces of indentation (should be 8 or less)
    lines = content.split("\n")
    fixed_lines = []
    in_with_block = False
    with_indent = 0

    for i, line in enumerate(lines):
        # Check if this is a with statement for getter patches
        if 'with patch.object(data_management_handler, "get_' in line:
            in_with_block = True
            with_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue

        # If we're in a with block and see excessive indentation
        if in_with_block:
            current_indent = len(line) - len(line.lstrip())

            # If line is empty or a comment, keep as is
            if not line.strip() or line.strip().startswith("#"):
                fixed_lines.append(line)
                continue

            # If we hit another with statement at same or less indent, we're still nesting
            if (
                "with patch.object" in line
                and current_indent <= with_indent + 4
            ):
                fixed_lines.append(line)
                with_indent = current_indent
                continue

            # If indentation is more than expected (with_indent + 4), reduce it
            expected_indent = with_indent + 4
            if current_indent > expected_indent and line.strip():
                # Reduce indentation to expected level
                fixed_line = " " * expected_indent + line.lstrip()
                fixed_lines.append(fixed_line)
                continue

            # Check if we're exiting the with block (dedent to function level or less)
            if current_indent <= with_indent and line.strip():
                in_with_block = False

        fixed_lines.append(line)

    # Write back
    content = "\n".join(fixed_lines)
    test_file.write_text(content)
    print(f"✓ Fixed indentation in {test_file}")


if __name__ == "__main__":
    fix_indentation()
    print("✓ Indentation fixed!")
