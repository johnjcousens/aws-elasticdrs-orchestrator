#!/usr/bin/env python3
"""
Fix test patches to use private variables (_table_name) instead of public ones.
"""


def fix_test_patches(file_path):
    """Replace patch.object calls to use private variables"""

    with open(file_path, "r") as f:
        content = f.read()

    # Define replacements
    replacements = [
        ('"protection_groups_table"', '"_protection_groups_table"'),
        ('"recovery_plans_table"', '"_recovery_plans_table"'),
        ('"executions_table"', '"_executions_table"'),
        ('"target_accounts_table"', '"_target_accounts_table"'),
        ('"tag_sync_config_table"', '"_tag_sync_config_table"'),
    ]

    changes_made = 0
    for old, new in replacements:
        count = content.count(old)
        if count > 0:
            print(f"Replacing {count} occurrences of {old} with {new}")
            content = content.replace(old, new)
            changes_made += count

    if changes_made > 0:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"\n✓ Fixed {changes_made} patch statements")
        return True
    else:
        print("\n✓ No patches found to fix")
        return False


if __name__ == "__main__":
    file_path = "tests/unit/test_data_management_new_operations.py"
    fix_test_patches(file_path)
