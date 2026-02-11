#!/usr/bin/env python3
"""
Fix test patches in test_data_management_new_operations.py

Removes unnecessary patch.object calls for table variables since we're using
@mock_aws decorator and the reset pattern.
"""

import re

# Read the test file
with open("tests/unit/test_data_management_new_operations.py", "r") as f:
    content = f.read()

# Pattern 1: Remove patch.object lines for tables
patterns_to_remove = [
    r'\s+with patch\.object\(data_management_handler, "protection_groups_table", pg_table\):\n',
    r'\s+with patch\.object\(data_management_handler, "recovery_plans_table", rp_table\):\n',
    r'\s+with patch\.object\(data_management_handler, "executions_table", exec_table\):\n',
    r'\s+with patch\.object\(data_management_handler, "target_accounts_table", ta_table\):\n',
    r'\s+with patch\.object\(data_management_handler, "tag_sync_config_table", ts_table\):\n',
]

for pattern in patterns_to_remove:
    content = re.sub(pattern, "", content)

# Pattern 2: Fix indentation after removing with statements
# Find blocks that now have incorrect indentation
lines = content.split("\n")
fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]

    # Check if this is a line that was inside a removed with statement
    # It will have extra indentation (12 spaces instead of 8)
    if line.startswith("            ") and not line.strip().startswith("#"):
        # Check if previous line is not a with statement
        if i > 0 and "with patch" not in lines[i - 1]:
            # Reduce indentation by 4 spaces
            fixed_lines.append(line[4:])
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

    i += 1

content = "\n".join(fixed_lines)

# Write back
with open("tests/unit/test_data_management_new_operations.py", "w") as f:
    f.write(content)

print("Fixed patch.object calls and indentation")
