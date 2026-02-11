#!/usr/bin/env python3
"""Fix test_target_account_addition_property.py patches."""
import re
from pathlib import Path

test_file = (
    Path(__file__).parent.parent
    / "tests"
    / "unit"
    / "test_target_account_addition_property.py"
)

with open(test_file, "r") as f:
    content = f.read()

# Replace all occurrences of patching target_accounts_table with get_target_accounts_table
old_pattern = r'with patch\.object\(data_management_handler, "target_accounts_table", table\):'
new_pattern = r'with patch.object(data_management_handler, "get_target_accounts_table", return_value=table):'

new_content = re.sub(old_pattern, new_pattern, content)

if new_content != content:
    with open(test_file, "w") as f:
        f.write(new_content)
    count = len(re.findall(old_pattern, content))
    print(
        f"✓ Fixed {count} patch.object calls in test_target_account_addition_property.py"
    )
else:
    print("✗ No changes needed")
