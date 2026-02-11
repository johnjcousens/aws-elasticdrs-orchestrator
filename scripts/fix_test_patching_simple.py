#!/usr/bin/env python3
"""
Remove dynamodb patching from tests - just reset table variables.
The @mock_aws decorator already makes boto3 use moto.
"""


# Read the file
with open("tests/unit/test_data_management_new_operations.py", "r") as f:
    lines = f.readlines()

output_lines = []
i = 0
while i < len(lines):
    line = lines[i]

    # Check if this is a dynamodb patch line
    if (
        'with patch.object(data_management_handler, "dynamodb", boto3.resource("dynamodb", region_name="us-east-1")):'
        in line
    ):
        # Skip this line and unindent the following lines
        i += 1
        # Process indented block
        while i < len(lines):
            next_line = lines[i]
            # If line starts with more indentation than the patch, unindent it
            if next_line.startswith(
                "        "
            ) and not next_line.strip().startswith("#"):
                # Remove 4 spaces of indentation
                output_lines.append(next_line[4:])
            elif next_line.strip() == "":
                output_lines.append(next_line)
            else:
                # End of indented block
                break
            i += 1
    else:
        output_lines.append(line)
        i += 1

# Write back
with open("tests/unit/test_data_management_new_operations.py", "w") as f:
    f.writelines(output_lines)

print("Fixed tests - removed dynamodb patching")
