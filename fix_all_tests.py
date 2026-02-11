#!/usr/bin/env python3
"""
Fix all tests in test_data_management_new_operations.py by removing
the dynamodb patching and just resetting table variables.
"""

import re

# Read the file
with open("tests/unit/test_data_management_new_operations.py", "r") as f:
    content = f.read()

# Pattern 1: Remove "with patch.object(data_management_handler, "dynamodb", boto3.resource("dynamodb", region_name="us-east-1")):" lines
# and unindent the content inside
pattern1 = r'    with patch\.object\(data_management_handler, "dynamodb", boto3\.resource\("dynamodb", region_name="us-east-1"\)\):\n((?:        .*\n)*)'

def fix_patch(match):
    inner_content = match.group(1)
    # Unindent by 4 spaces
    lines = inner_content.split('\n')
    fixed_lines = []
    for line in lines:
        if line.startswith('        '):
            fixed_lines.append(line[4:])
        else:
            fixed_lines.append(line)
    return '\n'.join(fixed_lines)

content = re.sub(pattern1, fix_patch, content)

# Write back
with open("tests/unit/test_data_management_new_operations.py", "w") as f:
    f.write(content)

print("Fixed all tests - removed dynamodb patching")
