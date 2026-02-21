"""
Property-based tests for new data-management-handler operations.

Uses Hypothesis framework to verify universal properties hold across all inputs.
Tests Phase 4 operations (Tasks 5.1-5.13):
- update_server_launch_config (task 5.1)
- delete_server_launch_config (task 5.2)
- bulk_update_server_configs (task 5.3)
- validate_static_ip (task 5.4)
- add_target_account (task 5.5)
- update_target_account (task 5.6)
- delete_target_account (task 5.7)
- add_staging_account (task 5.8)
- remove_staging_account (task 5.9)
- trigger_tag_sync (task 5.10)
- update_tag_sync_settings (task 5.11)
- sync_extended_source_servers (task 5.12)
- import_configuration (task 5.13)

Feature: direct-lambda-invocation-mode
Requirements: 5.1-5.13, 5.16
"""

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st



# Add lambda paths for imports
data_mgmt_dir = Path(__file__).parent.parent.parent / "lambda" / "data-management-handler"
shared_dir = Path(__file__).parent.parent.parent / "lambda" / "shared"


@contextmanager
def setup_test_environment():
    """Context manager to set up test environment for each property test"""
    # Save original sys.path and modules
    original_path = sys.path.copy()
    original_index = sys.modules.get("index")

    # Remove any existing 'index' module
    if "index" in sys.modules:
        del sys.modules["index"]

    # Add data-management-handler to front of path
    sys.path.insert(0, str(data_mgmt_dir))
    sys.path.insert(1, str(shared_dir))

    # Set up environment variables
    with patch.dict(
        os.environ,
        {
            "PROTECTION_GROUPS_TABLE": "test-protection-groups",
            "RECOVERY_PLANS_TABLE": "test-recovery-plans",
            "TARGET_ACCOUNTS_TABLE": "test-target-accounts",
            "EXECUTION_HISTORY_TABLE": "test-execution-history",
            "TAG_SYNC_CONFIG_TABLE": "test-tag-sync-config",
        },
    ):
        try:
            yield
        finally:
            # Restore original state
            sys.path = original_path
            if "index" in sys.modules:
                del sys.modules["index"]
            if original_index is not None:
                sys.modules["index"] = original_index
