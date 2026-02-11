#!/usr/bin/env python3
"""Fix all error handling test patches to use getter functions."""
import re
from pathlib import Path


def fix_patches_in_file(file_path):
    """Fix all patch.object calls in a file."""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content

    # Replace protection_groups_table patches
    content = re.sub(
        r'patch\.object\(data_management_handler_index, "protection_groups_table"',
        r'patch.object(data_management_handler_index, "get_protection_groups_table", return_value',
        content,
    )

    # Replace recovery_plans_table patches
    content = re.sub(
        r'patch\.object\(data_management_handler_index, "recovery_plans_table"',
        r'patch.object(data_management_handler_index, "get_recovery_plans_table", return_value',
        content,
    )

    # Replace query_handler_index patches
    content = re.sub(
        r'patch\.object\(query_handler_index, "protection_groups_table"',
        r'patch.object(query_handler_index, "get_protection_groups_table", return_value',
        content,
    )

    content = re.sub(
        r'patch\.object\(query_handler_index, "recovery_plans_table"',
        r'patch.object(query_handler_index, "get_recovery_plans_table", return_value',
        content,
    )

    # Fix cases where we're patching with a variable but not using return_value=
    # Pattern: patch.object(module, "get_X_table", return_value, mock_table)
    # Should be: patch.object(module, "get_X_table", return_value=mock_table)
    content = re.sub(
        r'patch\.object\(([^,]+), "get_(\w+)_table", return_value, ([^)]+)\)',
        r'patch.object(\1, "get_\2_table", return_value=\3)',
        content,
    )

    if content != original_content:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"✓ Fixed patches in {file_path.name}")
        return True
    else:
        print(f"✗ No changes needed in {file_path.name}")
        return False


if __name__ == "__main__":
    test_dir = Path(__file__).parent.parent / "tests" / "unit"

    files_to_fix = [
        test_dir / "test_error_handling_data_management_handler.py",
        test_dir / "test_error_handling_query_handler.py",
        test_dir / "test_data_management_response_format.py",
    ]

    fixed_count = 0
    for file_path in files_to_fix:
        if file_path.exists():
            if fix_patches_in_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠ File not found: {file_path}")

    print(f"\nFixed {fixed_count} files")
