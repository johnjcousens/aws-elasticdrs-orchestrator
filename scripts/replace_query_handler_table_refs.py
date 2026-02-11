#!/usr/bin/env python3
"""
Replace table references in query-handler with getter function calls.
"""
import re
import sys
from pathlib import Path


def replace_table_references(file_path):
    """Replace all table references with getter function calls."""
    with open(file_path, "r") as f:
        content = f.read()

    original_content = content
    replacements = 0

    # Replace protection_groups_table
    pattern1 = r"\bprotection_groups_table\b"
    new_content = re.sub(pattern1, "get_protection_groups_table()", content)
    replacements += len(re.findall(pattern1, content))

    # Replace recovery_plans_table
    pattern2 = r"\brecovery_plans_table\b"
    new_content = re.sub(pattern2, "get_recovery_plans_table()", new_content)
    replacements += len(re.findall(pattern2, content))

    # Replace target_accounts_table
    pattern3 = r"\btarget_accounts_table\b"
    new_content = re.sub(pattern3, "get_target_accounts_table()", new_content)
    replacements += len(re.findall(pattern3, content))

    # Replace _execution_history_table (note the underscore)
    pattern4 = r"\b_execution_history_table\b"
    new_content = re.sub(
        pattern4, "get_execution_history_table()", new_content
    )
    replacements += len(re.findall(pattern4, content))

    if new_content != original_content:
        with open(file_path, "w") as f:
            f.write(new_content)
        print(f"✓ Replaced {replacements} table references in {file_path}")
        return replacements
    else:
        print(f"✗ No replacements needed in {file_path}")
        return 0


if __name__ == "__main__":
    query_handler_path = (
        Path(__file__).parent.parent / "lambda" / "query-handler" / "index.py"
    )

    if not query_handler_path.exists():
        print(f"Error: {query_handler_path} not found")
        sys.exit(1)

    total = replace_table_references(query_handler_path)
    print(f"\nTotal replacements: {total}")
