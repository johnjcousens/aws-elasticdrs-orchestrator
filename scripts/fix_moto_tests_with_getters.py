#!/usr/bin/env python3
"""
Fix moto tests to use getter function patches instead of dynamodb resource patches.

This script updates all @mock_aws tests in test_data_management_new_operations.py
to patch the getter functions (get_protection_groups_table, etc.) instead of
patching the dynamodb resource.
"""

import re
from pathlib import Path


def fix_test_file():
    """Fix all tests in the file to use getter patches."""
    test_file = Path("tests/unit/test_data_management_new_operations.py")
    content = test_file.read_text()

    # Pattern to match the old patching approach
    old_pattern = r"""    # Patch the module-level dynamodb resource to use moto
    import boto3
    mock_dynamodb = boto3\.resource\("dynamodb", region_name="us-east-1"\)
    
    # Reset private table variables to force re-initialization with moto
    data_management_handler\._protection_groups_table = None
    data_management_handler\._recovery_plans_table = None
    data_management_handler\._executions_table = None
    data_management_handler\._target_accounts_table = None
    data_management_handler\._tag_sync_config_table = None
    
    with patch\.object\(data_management_handler, "dynamodb", mock_dynamodb\):"""

    # Replacement - just remove the old patching code
    new_pattern = r""""""

    # Replace all occurrences
    content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

    # Also remove duplicate dynamodb patching blocks (some tests have multiple)
    duplicate_pattern = r"""        mock_dynamodb = boto3\.resource\("dynamodb", region_name="us-east-1"\)
        
        # Reset private table variables to force re-initialization with moto
        data_management_handler\._protection_groups_table = None
        data_management_handler\._recovery_plans_table = None
        data_management_handler\._executions_table = None
        data_management_handler\._target_accounts_table = None
        data_management_handler\._tag_sync_config_table = None
    
    with patch\.object\(data_management_handler, "dynamodb", mock_dynamodb\):"""

    content = re.sub(duplicate_pattern, "", content, flags=re.MULTILINE)

    # Write back
    test_file.write_text(content)
    print(f"✓ Removed old patching code from {test_file}")

    # Now add getter patches to each test function
    add_getter_patches(test_file)


def add_getter_patches(test_file):
    """Add getter function patches to each test that needs them."""
    content = test_file.read_text()

    # Find all test functions that use @mock_aws
    test_pattern = r"(@mock_aws\ndef test_\w+\([^)]*\):.*?(?=\n@mock_aws\ndef test_|\n# =====|\Z))"
    tests = list(re.finditer(test_pattern, content, re.DOTALL))

    print(f"Found {len(tests)} @mock_aws tests")

    # Track which tests need which table patches
    test_patches = []

    for match in tests:
        test_code = match.group(1)
        test_name = re.search(r"def (test_\w+)", test_code).group(1)

        # Skip the first test - it already has the correct pattern
        if test_name == "test_update_server_launch_config_success":
            continue

        # Determine which tables this test uses
        needs_pg = (
            "pg_table" in test_code or "protection_groups" in test_code.lower()
        )
        needs_ta = (
            "ta_table" in test_code or "target_accounts" in test_code.lower()
        )
        needs_ts = "ts_table" in test_code or "tag_sync" in test_code.lower()

        # Find the last line before the test ends (usually the assert or result line)
        # We'll add the patches right after setup_dynamodb_tables() call

        if needs_pg or needs_ta or needs_ts:
            test_patches.append(
                {
                    "name": test_name,
                    "needs_pg": needs_pg,
                    "needs_ta": needs_ta,
                    "needs_ts": needs_ts,
                    "start": match.start(),
                    "end": match.end(),
                }
            )

    print(f"Need to patch {len(test_patches)} tests")

    # Now modify each test
    # We'll do this by finding the setup_dynamodb_tables() call and adding patches after it
    for patch_info in reversed(test_patches):  # Reverse to maintain positions
        test_name = patch_info["name"]

        # Find this test in the content
        test_start = content.find(f"def {test_name}(")
        if test_start == -1:
            print(f"  ✗ Could not find test {test_name}")
            continue

        # Find the setup_dynamodb_tables() call
        setup_call_pattern = r"(    (?:pg_table, ta_table, ts_table|pg_table, _, _|_, ta_table, _|_, _, ts_table|_, ta_table, ts_table) = setup_dynamodb_tables\(\))"
        setup_match = re.search(
            setup_call_pattern, content[test_start : test_start + 5000]
        )

        if not setup_match:
            print(f"  ✗ Could not find setup_dynamodb_tables() in {test_name}")
            continue

        setup_pos = test_start + setup_match.end()

        # Build the patch code
        patches = []
        if patch_info["needs_pg"]:
            patches.append("get_protection_groups_table")
        if patch_info["needs_ta"]:
            patches.append("get_target_accounts_table")
        if patch_info["needs_ts"]:
            patches.append("get_tag_sync_config_table")

        # Create the patch context managers
        patch_code = "\n\n    # Patch getter functions to return moto tables\n"

        # Build nested with statements
        indent = "    "
        for i, patch_func in enumerate(patches):
            table_var = (
                "pg_table"
                if "protection" in patch_func
                else ("ta_table" if "target" in patch_func else "ts_table")
            )
            patch_code += f'{indent}with patch.object(data_management_handler, "{patch_func}", return_value={table_var}):\n'
            indent += "    "

        # Find where to insert the closing of the patches
        # We need to indent all the remaining code in the test
        test_end = content.find("\n\n@mock_aws", setup_pos)
        if test_end == -1:
            test_end = content.find("\n\n# ====", setup_pos)
        if test_end == -1:
            test_end = len(content)

        test_body = content[setup_pos:test_end]

        # Indent the test body
        indented_body = "\n".join(
            indent + line if line.strip() else line
            for line in test_body.split("\n")
        )

        # Insert the patch code
        content = (
            content[:setup_pos]
            + patch_code
            + indented_body
            + content[test_end:]
        )

        print(f"  ✓ Patched {test_name} with {len(patches)} getter(s)")

    # Write back
    test_file.write_text(content)
    print(f"✓ Added getter patches to {len(test_patches)} tests")


if __name__ == "__main__":
    fix_test_file()
    print("\n✓ All tests fixed!")
