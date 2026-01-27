#!/usr/bin/env python3
"""
Update log paths in local-ci-checks.sh from reports/ to $RUN_LOG_DIR/
"""

# Read the file
with open("scripts/local-ci-checks.sh", "r") as f:
    content = f.read()

# Replace all reports/ paths with $RUN_LOG_DIR/
replacements = [
    ("reports/validation/", "$RUN_LOG_DIR/validation/"),
    ("reports/security/raw/", "$RUN_LOG_DIR/security/raw/"),
    ("reports/security/formatted/", "$RUN_LOG_DIR/security/formatted/"),
    ("reports/security/", "$RUN_LOG_DIR/security/"),
    ("reports/tests/", "$RUN_LOG_DIR/tests/"),
    ("reports/", "$RUN_LOG_DIR/"),
    # Fix relative paths for frontend
    ("../reports/", "../$RUN_LOG_DIR/"),
    ("../../reports/", "../../$RUN_LOG_DIR/"),
]

for old, new in replacements:
    content = content.replace(old, new)

# Write the updated file
with open("scripts/local-ci-checks.sh", "w") as f:
    f.write(content)

print("✅ Updated all log paths from reports/ to $RUN_LOG_DIR/")
