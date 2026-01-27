"""
Pytest configuration for DR Orchestration tests.

Sets up Python path to allow imports from lambda directory.
"""

import os
import sys

# Get absolute path to project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add lambda directory to Python path for all tests
lambda_dir = os.path.join(project_root, "lambda")

# Insert at beginning of path if not already present
if lambda_dir not in sys.path:
    sys.path.insert(0, lambda_dir)
