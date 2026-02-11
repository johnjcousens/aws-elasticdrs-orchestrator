#!/usr/bin/env python3
"""
Fix all test patches in test_data_management_new_operations.py to use dynamodb resource patching.
"""

import re

# Read the test file
with open("tests/unit/test_data_management_new_operations.py", "r") as f:
    content = f.read()

# Pattern 1: Replace all `with patch.object(data_management_handler, "_*_table", *_table):`
# with proper dynamodb resource patching
patterns_to_fix = [
    (
        r'with patch\.object\(data_management_handler, "_protection_groups_table", pg_table\):',
        'mock_dynamodb = boto3.resource("dynamodb", region_name="us-east-1")\n    \n    with patch.object(data_management_handler, "dynamodb", mock_dynamodb):',
    ),
    (
        r'with patch\.object\(data_management_handler, "_recovery_plans_table", rp_table\):',
        'mock_dynamodb = boto3.resource("dynamodb", region_name="us-east-1")\n    \n    with patch.object(data_management_handler, "dynamodb", mock_dynamodb):',
    ),
    (
        r'with patch\.object\(data_management_handler, "_executions_table", exec_table\):',
        'mock_dynamodb = boto3.resource("dynamodb", region_name="us-east-1")\n    \n    with patch.object(data_management_handler, "dynamodb", mock_dynamodb):',
    ),
    (
        r'with patch\.object\(data_management_handler, "_target_accounts_table", ta_table\):',
        'mock_dynamodb = boto3.resource("dynamodb", region_name="us-east-1")\n    \n    with patch.object(data_management_handler, "dynamodb", mock_dynamodb):',
    ),
    (
        r'with patch\.object\(data_management_handler, "_tag_sync_config_table", ts_table\):',
        'mock_dynamodb = boto3.resource("dynamodb", region_name="us-east-1")\n    \n    with patch.object(data_management_handler, "dynamodb", mock_dynamodb):',
    ),
]

for pattern, replacement in patterns_to_fix:
    content = re.sub(pattern, replacement, content)

# Write back
with open("tests/unit/test_data_management_new_operations.py", "w") as f:
    f.write(content)

print("✓ Fixed all test patches to use dynamodb resource patching")
