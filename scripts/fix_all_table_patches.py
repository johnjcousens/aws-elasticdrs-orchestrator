#!/usr/bin/env python3
"""Fix ALL test files to use getter function patches instead of direct table patches."""

from pathlib import Path

# Get all test files
test_dir = Path("tests/unit")
test_files = list(test_dir.glob("test_*.py"))

replacements = {
    # Query handler tables
    'patch.object(index, "target_accounts_table"': 'patch.object(index, "get_target_accounts_table", return_value',
    'patch.object(index, "protection_groups_table"': 'patch.object(index, "get_protection_groups_table", return_value',
    'patch.object(index, "recovery_plans_table"': 'patch.object(index, "get_recovery_plans_table", return_value',
    'patch.object(index, "execution_history_table"': 'patch.object(index, "get_execution_history_table", return_value',
    # Query handler index module
    'patch.object(query_handler_index, "target_accounts_table"': 'patch.object(query_handler_index, "get_target_accounts_table", return_value',
    'patch.object(query_handler_index, "protection_groups_table"': 'patch.object(query_handler_index, "get_protection_groups_table", return_value',
    'patch.object(query_handler_index, "recovery_plans_table"': 'patch.object(query_handler_index, "get_recovery_plans_table", return_value',
    'patch.object(query_handler_index, "execution_history_table"': 'patch.object(query_handler_index, "get_execution_history_table", return_value',
}

fixed_count = 0
files_modified = []

for test_file in test_files:
    content = test_file.read_text()
    original_content = content

    for old_pattern, new_pattern in replacements.items():
        if old_pattern in content:
            # Replace the pattern
            content = content.replace(old_pattern, new_pattern)

    if content != original_content:
        test_file.write_text(content)
        fixed_count += 1
        files_modified.append(test_file.name)

print(f"✓ Fixed {fixed_count} test files")
for filename in files_modified:
    print(f"  - {filename}")
