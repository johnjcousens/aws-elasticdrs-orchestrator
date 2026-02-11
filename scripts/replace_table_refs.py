#!/usr/bin/env python3
"""
Replace module-level table references with lazy getter function calls.
This ensures test mocks are properly applied when tests run in batch.
"""

import re
import sys


def replace_table_references(file_path):
    """Replace all table references with getter function calls"""

    with open(file_path, "r") as f:
        content = f.read()

    # Define replacements (table_variable -> getter_function)
    replacements = [
        ("protection_groups_table", "get_protection_groups_table()"),
        ("recovery_plans_table", "get_recovery_plans_table()"),
        ("executions_table", "get_executions_table()"),
        ("target_accounts_table", "get_target_accounts_table()"),
        ("tag_sync_config_table", "get_tag_sync_config_table()"),
    ]

    # Track changes
    changes_made = 0

    for old_ref, new_ref in replacements:
        # Pattern: table_name.method_call (but not in getter function definitions)
        pattern = rf"\b{old_ref}\."

        # Count matches
        matches = re.findall(pattern, content)
        if matches:
            print(f"Found {len(matches)} references to {old_ref}")
            changes_made += len(matches)

            # Replace all occurrences
            content = re.sub(pattern, f"{new_ref}.", content)

    # Write back
    if changes_made > 0:
        with open(file_path, "w") as f:
            f.write(content)
        print(f"\n✓ Replaced {changes_made} table references")
        return True
    else:
        print("\n✓ No table references found to replace")
        return False


if __name__ == "__main__":
    file_path = "lambda/data-management-handler/index.py"
    success = replace_table_references(file_path)
    sys.exit(0 if success else 1)
