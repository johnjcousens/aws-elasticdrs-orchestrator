#!/usr/bin/env python3
"""
Fix all @mock_aws tests to patch getter functions instead of dynamodb resource.
"""

import re

# Read the test file
with open("tests/unit/test_data_management_new_operations.py", "r") as f:
    content = f.read()

# Remove all the dynamodb patching and table resets
# Pattern: mock_dynamodb = boto3.resource... followed by resets and patch.object(data_management_handler, "dynamodb"...)
pattern = r'    # Patch the module-level dynamodb resource.*?\n.*?mock_dynamodb = boto3\.resource\("dynamodb", region_name="us-east-1"\)\n\n(    # Reset private table variables.*?\n    data_management_handler\._tag_sync_config_table = None\n\n)*    with patch\.object\(data_management_handler, "dynamodb", mock_dynamodb\):'

replacement = '    # Patch getter functions to return moto tables\n    with patch.object(data_management_handler, "get_protection_groups_table", return_value=pg_table if "pg_table" in locals() else None), \\\n         patch.object(data_management_handler, "get_target_accounts_table", return_value=ta_table if "ta_table" in locals() else None), \\\n         patch.object(data_management_handler, "get_tag_sync_config_table", return_value=ts_table if "ts_table" in locals() else None):'

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open("tests/unit/test_data_management_new_operations.py", "w") as f:
    f.write(content)

print("✓ Fixed all @mock_aws tests to use getter function patching")
