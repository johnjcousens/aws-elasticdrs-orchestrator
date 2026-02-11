#!/usr/bin/env python3
"""Fix test_query_handler_role_arn.py to use getter function patches."""


# Read the test file
with open("tests/unit/test_query_handler_role_arn.py", "r") as f:
    content = f.read()

# Replace all instances of patching target_accounts_table with getter function
content = content.replace(
    'patch.object(index, "target_accounts_table", mock_dynamodb_table)',
    'patch.object(index, "get_target_accounts_table", return_value=mock_dynamodb_table)',
)

content = content.replace(
    'patch.object(index, "target_accounts_table", mock_table)',
    'patch.object(index, "get_target_accounts_table", return_value=mock_table)',
)

# Write back
with open("tests/unit/test_query_handler_role_arn.py", "w") as f:
    f.write(content)

print("✓ Fixed all patches in test_query_handler_role_arn.py")
