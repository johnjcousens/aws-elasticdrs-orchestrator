#!/usr/bin/env python3
"""
Fix DynamoDB patches in test_data_management_new_operations.py

Applies the dynamodb patch pattern to all tests that need it.
"""

import re
from pathlib import Path


def fix_test_file():
    """Fix all tests in the file"""
    test_file = Path("tests/unit/test_data_management_new_operations.py")
    content = test_file.read_text()

    # Pattern to find @mock_aws decorated test functions
    test_pattern = r"(@mock_aws\ndef test_\w+\([^)]*\):.*?(?=\n@mock_aws\ndef test_|\n# =====|\Z))"

    tests = list(re.finditer(test_pattern, content, re.DOTALL))
    print(f"Found {len(tests)} @mock_aws tests")

    # Tests that already have the dynamodb patch (first test)
    already_fixed = ["test_update_server_launch_config_success"]

    modifications = []

    for match in tests:
        test_content = match.group(0)

        # Extract test name
        name_match = re.search(r"def (test_\w+)\(", test_content)
        if not name_match:
            continue
        test_name = name_match.group(1)

        # Skip if already fixed
        if test_name in already_fixed:
            print(f"  Skipping {test_name} (already fixed)")
            continue

        # Check if test uses protection groups table
        if (
            "pg_table" in test_content
            or "_protection_groups_table" in test_content
        ):
            # Check if it already has the dynamodb patch
            if (
                'patch.object(data_management_handler, "dynamodb"'
                in test_content
            ):
                print(f"  Skipping {test_name} (already has dynamodb patch)")
                continue

            # Find where to insert the patch
            # Look for the first patch.object or with statement after setup_dynamodb_tables
            setup_match = re.search(r"setup_dynamodb_tables\(\)", test_content)
            if not setup_match:
                print(
                    f"  Skipping {test_name} (no setup_dynamodb_tables call)"
                )
                continue

            # Find the first with statement after setup
            with_match = re.search(
                r"\n( +)with patch\.object\(",
                test_content[setup_match.end() :],
            )
            if not with_match:
                # Try to find result = function call
                result_match = re.search(
                    r"\n( +)result = ", test_content[setup_match.end() :]
                )
                if result_match:
                    # Insert patch before result assignment
                    insert_pos = setup_match.end() + result_match.start()
                    indent = result_match.group(1)

                    patch_code = f"\n{indent}# Patch the module-level dynamodb resource to use moto\n"
                    patch_code += f"{indent}import boto3\n"
                    patch_code += f'{indent}mock_dynamodb = boto3.resource("dynamodb", region_name="us-east-1")\n'
                    patch_code += f"{indent}\n"
                    patch_code += f'{indent}with patch.object(data_management_handler, "dynamodb", mock_dynamodb):\n'

                    # Indent the result line
                    result_line_start = insert_pos
                    result_line_end = test_content.find("\n", insert_pos + 1)
                    if result_line_end == -1:
                        result_line_end = len(test_content)
                    result_line = test_content[
                        result_line_start:result_line_end
                    ]
                    indented_result = result_line.replace(
                        f"\n{indent}", f"\n{indent}    "
                    )

                    # Find all lines until the end of the test
                    remaining_start = result_line_end
                    remaining_end = len(test_content)
                    remaining = test_content[remaining_start:remaining_end]

                    # Indent all remaining lines
                    indented_remaining = remaining.replace(
                        f"\n{indent}", f"\n{indent}    "
                    )

                    new_content = (
                        test_content[:insert_pos]
                        + patch_code
                        + indented_result
                        + indented_remaining
                    )

                    modifications.append(
                        {
                            "test_name": test_name,
                            "old_start": match.start(),
                            "old_end": match.end(),
                            "new_content": new_content,
                        }
                    )
                    print(f"  Will fix {test_name} (add dynamodb patch)")
                else:
                    print(
                        f"  Skipping {test_name} (no result assignment found)"
                    )
                continue

            # Insert patch at the with statement
            insert_pos = setup_match.end() + with_match.start()
            indent = with_match.group(1)

            patch_code = f"\n{indent}# Patch the module-level dynamodb resource to use moto\n"
            patch_code += f"{indent}import boto3\n"
            patch_code += f'{indent}mock_dynamodb = boto3.resource("dynamodb", region_name="us-east-1")\n'
            patch_code += f"{indent}\n"
            patch_code += f'{indent}with patch.object(data_management_handler, "dynamodb", mock_dynamodb):\n'

            # Indent the existing with statement
            remaining = test_content[insert_pos:]
            indented_remaining = remaining.replace(
                f"\n{indent}", f"\n{indent}    "
            )

            new_content = (
                test_content[:insert_pos]
                + patch_code
                + "    "
                + indented_remaining
            )

            modifications.append(
                {
                    "test_name": test_name,
                    "old_start": match.start(),
                    "old_end": match.end(),
                    "new_content": new_content,
                }
            )
            print(f"  Will fix {test_name} (add dynamodb patch)")

    if not modifications:
        print("\nNo modifications needed!")
        return

    # Apply modifications in reverse order to preserve positions
    new_content = content
    for mod in reversed(modifications):
        new_content = (
            new_content[: mod["old_start"]]
            + mod["new_content"]
            + new_content[mod["old_end"] :]
        )

    # Write back
    test_file.write_text(new_content)
    print(f"\nFixed {len(modifications)} tests")


if __name__ == "__main__":
    fix_test_file()
