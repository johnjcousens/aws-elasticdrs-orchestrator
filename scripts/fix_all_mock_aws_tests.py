#!/usr/bin/env python3
"""
Fix all @mock_aws tests to properly reset table variables and dynamodb resource.
"""

import re

# Read the test file
with open("tests/unit/test_data_management_new_operations.py", "r") as f:
    content = f.read()

# Pattern to find @mock_aws tests that don't have the reset block
pattern = r'(@mock_aws\ndef test_[^(]+\([^)]*\):\n    """[^"]+"""\n)(?!    # Reset table variables)'

# Replacement with reset block
reset_block = r"""\1    # Reset table variables to use moto mocks
    data_management_handler._protection_groups_table = None
    data_management_handler._recovery_plans_table = None
    data_management_handler._executions_table = None
    data_management_handler._target_accounts_table = None
    data_management_handler._tag_sync_config_table = None
    
    # Update dynamodb resource to use moto
    data_management_handler.dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    
"""

# Apply the replacement
new_content = re.sub(pattern, reset_block, content)

# Write back
with open("tests/unit/test_data_management_new_operations.py", "w") as f:
    f.write(new_content)

print("Fixed all @mock_aws tests")
