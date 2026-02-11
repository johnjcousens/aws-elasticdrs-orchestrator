#!/usr/bin/env python3
"""Fix indentation issues in test file."""


def fix_indentation(file_path: str) -> None:
    """Fix lines that have 8 spaces when they should have 4."""

    with open(file_path, "r") as f:
        lines = f.readlines()

    fixed_lines = []
    fixes = 0

    for i, line in enumerate(lines, 1):
        # Check if line starts with exactly 8 spaces followed by non-whitespace
        # and is not inside a function definition (should be 4 spaces)
        if line.startswith("        ") and not line.startswith("            "):
            # Check if previous line suggests this should be at function body level
            if i > 1:
                prev_line = lines[i - 2].rstrip()
                # If previous line is a function def, class def, or normal statement
                # then this line should be dedented
                if (
                    prev_line.endswith(":")
                    or prev_line.strip() == ""
                    or not prev_line.startswith("        ")
                ):
                    # Dedent by 4 spaces
                    fixed_lines.append(line[4:])
                    fixes += 1
                    print(f"Line {i}: Fixed indentation")
                    continue

        fixed_lines.append(line)

    with open(file_path, "w") as f:
        f.writelines(fixed_lines)

    print(f"\nFixed {fixes} indentation issues")


if __name__ == "__main__":
    fix_indentation("tests/unit/test_data_management_new_operations.py")
