#!/usr/bin/env python3
"""
Add table reset lines at the start of each @mock_aws test function.
This ensures the getter functions create fresh table references using moto.
"""

import re

# Read the file
with open("tests/unit/test_data_management_new_operations.py", "r") as f:
    content = f.read()

# Find all @mock_aws test functions
pattern = r'(@mock_aws\ndef test_\w+\([^)]*\):\n    """[^"]*""")\n'


def add_resets(match):
    header = match.group(1)
    # Add reset lines after the docstring
    return (
        header
        + "\n    # Reset table variables to use moto mocks\n    data_management_handler._protection_groups_table = None\n    data_management_handler._recovery_plans_table = None\n    data_management_handler._executions_table = None\n    data_management_handler._target_accounts_table = None\n    data_management_handler._tag_sync_config_table = None\n\n"
    )


content = re.sub(pattern, add_resets, content)

# Write back
with open("tests/unit/test_data_management_new_operations.py", "w") as f:
    f.write(content)

print("Added table resets to all @mock_aws tests")
