"""
Unit tests for backfill scripts.

Tests the Protection Group and Recovery Plan backfill scripts
that populate accountId on existing DynamoDB items.

Validates: Requirements 2.4
"""

import importlib.util
import os
import sys
from unittest.mock import MagicMock, call, patch

import pytest


def _load_script(script_name: str):
    """
    Load a backfill script as a module using importlib.

    Scripts in the scripts/ directory are not packages, so we
    load them by file path.

    Args:
        script_name: Filename of the script (e.g. 'backfill-protection-groups.py')

    Returns:
        Loaded module object
    """
    script_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "scripts",
        script_name,
    )
    script_path = os.path.normpath(script_path)
    # Convert hyphens to underscores for valid module name
    module_name = script_name.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(
        module_name, script_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load both backfill scripts as modules
pg_backfill = _load_script("backfill-protection-groups.py")
rp_backfill = _load_script("backfill-recovery-plans.py")


# ============================================================
# Protection Group backfill: extract_account_id_from_arn
# ============================================================


class TestExtractAccountIdFromArn:
    """Tests for extract_account_id_from_arn in PG backfill."""

    def test_valid_iam_role_arn(self):
        """Valid IAM role ARN returns 12-digit account ID."""
        arn = "arn:aws:iam::123456789012:role/MyRole"
        assert pg_backfill.extract_account_id_from_arn(arn) == "123456789012"

    def test_arn_with_path(self):
        """IAM role ARN with path prefix returns account ID."""
        arn = "arn:aws:iam::999888777666:role/path/MyRole"
        assert pg_backfill.extract_account_id_from_arn(arn) == "999888777666"

    def test_non_iam_arn_returns_none(self):
        """Non-IAM ARN returns None."""
        arn = "arn:aws:s3:::my-bucket"
        assert pg_backfill.extract_account_id_from_arn(arn) is None

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        assert pg_backfill.extract_account_id_from_arn("") is None

    def test_plain_role_name_returns_none(self):
        """Plain role name (not an ARN) returns None."""
        assert pg_backfill.extract_account_id_from_arn("MyRole") is None

    def test_malformed_arn_returns_none(self):
        """Malformed ARN returns None."""
        assert pg_backfill.extract_account_id_from_arn("arn:aws:iam::abc:role/X") is None


# ============================================================
# Protection Group backfill: extract_account_id_from_source_server_arn
# ============================================================


class TestExtractAccountIdFromSourceServerArn:
    """Tests for extract_account_id_from_source_server_arn."""

    def test_valid_drs_arn(self):
        """Valid DRS source server ARN returns account ID."""
        arn = (
            "arn:aws:drs:us-east-1:111222333444:"
            "source-server/s-1234567890abcdef0"
        )
        result = pg_backfill.extract_account_id_from_source_server_arn(arn)
        assert result == "111222333444"

    def test_different_region(self):
        """DRS ARN from different region returns account ID."""
        arn = (
            "arn:aws:drs:eu-west-1:555666777888:"
            "source-server/s-abcdef1234567890a"
        )
        result = pg_backfill.extract_account_id_from_source_server_arn(arn)
        assert result == "555666777888"

    def test_non_drs_arn_returns_none(self):
        """Non-DRS ARN returns None."""
        arn = "arn:aws:ec2:us-east-1:123456789012:instance/i-abc"
        result = pg_backfill.extract_account_id_from_source_server_arn(arn)
        assert result is None

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        result = pg_backfill.extract_account_id_from_source_server_arn("")
        assert result is None

    def test_plain_server_id_returns_none(self):
        """Plain server ID (not ARN) returns None."""
        result = pg_backfill.extract_account_id_from_source_server_arn(
            "s-1234567890abcdef0"
        )
        assert result is None


# ============================================================
# Protection Group backfill: derive_account_id
# ============================================================


class TestDeriveAccountId:
    """Tests for derive_account_id in PG backfill."""

    def test_derives_from_iam_role_arn(self):
        """Derives account ID from assumeRoleName when it is an ARN."""
        item = {
            "groupId": "pg-1",
            "assumeRoleName": "arn:aws:iam::123456789012:role/DR",
        }
        assert pg_backfill.derive_account_id(item) == "123456789012"

    def test_derives_from_source_server_arn(self):
        """Derives account ID from sourceServerIds ARN."""
        item = {
            "groupId": "pg-2",
            "assumeRoleName": "PlainRoleName",
            "sourceServerIds": [
                "arn:aws:drs:us-east-1:444555666777:"
                "source-server/s-abc"
            ],
        }
        assert pg_backfill.derive_account_id(item) == "444555666777"

    def test_prefers_assume_role_over_source_server(self):
        """assumeRoleName ARN takes priority over sourceServerIds."""
        item = {
            "groupId": "pg-3",
            "assumeRoleName": "arn:aws:iam::111111111111:role/R",
            "sourceServerIds": [
                "arn:aws:drs:us-east-1:222222222222:"
                "source-server/s-x"
            ],
        }
        assert pg_backfill.derive_account_id(item) == "111111111111"

    def test_returns_none_when_no_arn_available(self):
        """Returns None when neither field contains an ARN."""
        item = {
            "groupId": "pg-4",
            "assumeRoleName": "PlainRole",
            "sourceServerIds": ["s-plain-id"],
        }
        assert pg_backfill.derive_account_id(item) is None

    def test_returns_none_for_empty_item(self):
        """Returns None for item with no relevant fields."""
        assert pg_backfill.derive_account_id({}) is None

    def test_handles_non_list_source_server_ids(self):
        """Handles sourceServerIds that is not a list."""
        item = {
            "groupId": "pg-5",
            "sourceServerIds": "not-a-list",
        }
        assert pg_backfill.derive_account_id(item) is None

    def test_skips_non_string_entries_in_source_servers(self):
        """Skips non-string entries in sourceServerIds list."""
        item = {
            "groupId": "pg-6",
            "sourceServerIds": [123, None, True],
        }
        assert pg_backfill.derive_account_id(item) is None


# ============================================================
# Protection Group backfill: run_backfill (dry-run & apply)
# ============================================================


class TestPGRunBackfill:
    """Tests for run_backfill in PG backfill script."""

    @patch.object(pg_backfill, "update_item_account_id")
    @patch.object(pg_backfill, "scan_protection_groups")
    def test_dry_run_does_not_call_update(
        self, mock_scan, mock_update
    ):
        """Dry-run mode does NOT call update_item_account_id."""
        mock_scan.return_value = [
            {
                "groupId": "pg-1",
                "groupName": "Web",
                "assumeRoleName": (
                    "arn:aws:iam::123456789012:role/DR"
                ),
            }
        ]

        updated, skipped, errored = pg_backfill.run_backfill(
            table_name="t", region="us-east-1", apply=False
        )

        mock_update.assert_not_called()
        assert updated == 1
        assert skipped == 0
        assert errored == 0

    @patch.object(pg_backfill, "update_item_account_id")
    @patch.object(pg_backfill, "scan_protection_groups")
    def test_apply_mode_calls_update(
        self, mock_scan, mock_update
    ):
        """Apply mode calls update_item_account_id correctly."""
        mock_scan.return_value = [
            {
                "groupId": "pg-1",
                "groupName": "Web",
                "assumeRoleName": (
                    "arn:aws:iam::123456789012:role/DR"
                ),
            }
        ]

        updated, skipped, errored = pg_backfill.run_backfill(
            table_name="t", region="us-east-1", apply=True
        )

        mock_update.assert_called_once_with(
            "t", "us-east-1", "pg-1", "123456789012"
        )
        assert updated == 1
        assert skipped == 0
        assert errored == 0

    @patch.object(pg_backfill, "update_item_account_id")
    @patch.object(pg_backfill, "scan_protection_groups")
    def test_skips_items_without_derivable_account(
        self, mock_scan, mock_update
    ):
        """Items where accountId cannot be derived are skipped."""
        mock_scan.return_value = [
            {
                "groupId": "pg-x",
                "groupName": "NoArn",
                "assumeRoleName": "PlainRole",
            }
        ]

        updated, skipped, errored = pg_backfill.run_backfill(
            table_name="t", region="us-east-1", apply=True
        )

        mock_update.assert_not_called()
        assert updated == 0
        assert skipped == 1
        assert errored == 0

    @patch.object(pg_backfill, "scan_protection_groups")
    def test_empty_scan_returns_zeros(self, mock_scan):
        """Empty scan result returns all zeros."""
        mock_scan.return_value = []

        updated, skipped, errored = pg_backfill.run_backfill(
            table_name="t", region="us-east-1", apply=False
        )

        assert updated == 0
        assert skipped == 0
        assert errored == 0

    @patch.object(pg_backfill, "update_item_account_id")
    @patch.object(pg_backfill, "scan_protection_groups")
    def test_apply_handles_update_error(
        self, mock_scan, mock_update
    ):
        """Apply mode counts errors when update_item fails."""
        from botocore.exceptions import ClientError

        mock_scan.return_value = [
            {
                "groupId": "pg-err",
                "groupName": "Err",
                "assumeRoleName": (
                    "arn:aws:iam::123456789012:role/DR"
                ),
            }
        ]
        mock_update.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "boom"}},
            "UpdateItem",
        )

        updated, skipped, errored = pg_backfill.run_backfill(
            table_name="t", region="us-east-1", apply=True
        )

        assert updated == 0
        assert skipped == 0
        assert errored == 1


# ============================================================
# Recovery Plan backfill: extract_protection_group_ids
# ============================================================


class TestExtractProtectionGroupIds:
    """Tests for extract_protection_group_ids in RP backfill."""

    def test_extracts_ids_from_waves(self):
        """Extracts PG IDs from well-formed waves."""
        plan = {
            "waves": [
                {"protectionGroupId": "pg-1"},
                {"protectionGroupId": "pg-2"},
            ]
        }
        result = rp_backfill.extract_protection_group_ids(plan)
        assert result == ["pg-1", "pg-2"]

    def test_empty_waves_returns_empty(self):
        """Empty waves list returns empty list."""
        plan = {"waves": []}
        assert rp_backfill.extract_protection_group_ids(plan) == []

    def test_missing_waves_key_returns_empty(self):
        """Missing waves key returns empty list."""
        plan = {}
        assert rp_backfill.extract_protection_group_ids(plan) == []

    def test_waves_not_a_list_returns_empty(self):
        """Non-list waves value returns empty list."""
        plan = {"waves": "not-a-list"}
        assert rp_backfill.extract_protection_group_ids(plan) == []

    def test_skips_waves_without_pg_id(self):
        """Waves missing protectionGroupId are skipped."""
        plan = {
            "waves": [
                {"protectionGroupId": "pg-1"},
                {"description": "no pg id"},
                {"protectionGroupId": ""},
            ]
        }
        result = rp_backfill.extract_protection_group_ids(plan)
        assert result == ["pg-1"]

    def test_skips_non_dict_wave_entries(self):
        """Non-dict entries in waves are skipped."""
        plan = {
            "waves": [
                "not-a-dict",
                {"protectionGroupId": "pg-1"},
                42,
            ]
        }
        result = rp_backfill.extract_protection_group_ids(plan)
        assert result == ["pg-1"]

    def test_skips_non_string_pg_id(self):
        """Non-string protectionGroupId values are skipped."""
        plan = {
            "waves": [
                {"protectionGroupId": 123},
                {"protectionGroupId": "pg-ok"},
            ]
        }
        result = rp_backfill.extract_protection_group_ids(plan)
        assert result == ["pg-ok"]


# ============================================================
# Recovery Plan backfill: derive_account_id_from_groups
# ============================================================


class TestDeriveAccountIdFromGroups:
    """Tests for derive_account_id_from_groups in RP backfill."""

    @patch.object(rp_backfill, "get_protection_group")
    def test_single_account_returns_account_id(
        self, mock_get_pg
    ):
        """Returns account ID when all groups share one account."""
        mock_get_pg.return_value = {
            "groupId": "pg-1",
            "accountId": "111222333444",
            "assumeRoleName": "DRSRole",
        }

        account_id, role, warning = (
            rp_backfill.derive_account_id_from_groups(
                "groups-table", "us-east-1", ["pg-1"]
            )
        )

        assert account_id == "111222333444"
        assert role == "DRSRole"
        assert warning is None

    @patch.object(rp_backfill, "get_protection_group")
    def test_mixed_accounts_returns_none_with_warning(
        self, mock_get_pg
    ):
        """Returns None + warning when groups have different accounts."""
        mock_get_pg.side_effect = [
            {"groupId": "pg-1", "accountId": "111111111111"},
            {"groupId": "pg-2", "accountId": "222222222222"},
        ]

        account_id, role, warning = (
            rp_backfill.derive_account_id_from_groups(
                "groups-table", "us-east-1", ["pg-1", "pg-2"]
            )
        )

        assert account_id is None
        assert "mixed accounts" in warning

    @patch.object(rp_backfill, "get_protection_group")
    def test_no_groups_found_returns_none(
        self, mock_get_pg
    ):
        """Returns None when no Protection Groups are found."""
        mock_get_pg.return_value = None

        account_id, role, warning = (
            rp_backfill.derive_account_id_from_groups(
                "groups-table", "us-east-1", ["pg-missing"]
            )
        )

        assert account_id is None
        assert "no Protection Groups found" in warning

    @patch.object(rp_backfill, "get_protection_group")
    def test_groups_without_account_id(self, mock_get_pg):
        """Returns None when groups exist but have no accountId."""
        mock_get_pg.return_value = {
            "groupId": "pg-1",
            "accountId": "",
        }

        account_id, role, warning = (
            rp_backfill.derive_account_id_from_groups(
                "groups-table", "us-east-1", ["pg-1"]
            )
        )

        assert account_id is None
        assert "no accountId" in warning

    def test_empty_group_ids_returns_none(self):
        """Returns None when group_ids list is empty."""
        account_id, role, warning = (
            rp_backfill.derive_account_id_from_groups(
                "groups-table", "us-east-1", []
            )
        )

        assert account_id is None
        assert "no Protection Groups found" in warning

    @patch.object(rp_backfill, "get_protection_group")
    def test_grabs_assume_role_from_first_group(
        self, mock_get_pg
    ):
        """Returns assumeRoleName from the first group that has one."""
        mock_get_pg.side_effect = [
            {
                "groupId": "pg-1",
                "accountId": "111222333444",
                "assumeRoleName": "",
            },
            {
                "groupId": "pg-2",
                "accountId": "111222333444",
                "assumeRoleName": "SecondRole",
            },
        ]

        account_id, role, warning = (
            rp_backfill.derive_account_id_from_groups(
                "groups-table",
                "us-east-1",
                ["pg-1", "pg-2"],
            )
        )

        assert account_id == "111222333444"
        assert role == "SecondRole"
        assert warning is None


# ============================================================
# Recovery Plan backfill: run_backfill (dry-run & apply)
# ============================================================


class TestRPRunBackfill:
    """Tests for run_backfill in RP backfill script."""

    @patch.object(rp_backfill, "update_recovery_plan")
    @patch.object(rp_backfill, "derive_account_id_from_groups")
    @patch.object(rp_backfill, "scan_recovery_plans")
    def test_dry_run_does_not_call_update(
        self, mock_scan, mock_derive, mock_update
    ):
        """Dry-run mode does NOT call update_recovery_plan."""
        mock_scan.return_value = [
            {
                "planId": "plan-1",
                "planName": "DR Plan",
                "waves": [{"protectionGroupId": "pg-1"}],
            }
        ]
        mock_derive.return_value = (
            "123456789012",
            "DRSRole",
            None,
        )

        updated, skipped, errored = rp_backfill.run_backfill(
            plans_table="p",
            groups_table="g",
            region="us-east-1",
            apply=False,
        )

        mock_update.assert_not_called()
        assert updated == 1
        assert skipped == 0
        assert errored == 0

    @patch.object(rp_backfill, "update_recovery_plan")
    @patch.object(rp_backfill, "derive_account_id_from_groups")
    @patch.object(rp_backfill, "scan_recovery_plans")
    def test_apply_mode_calls_update(
        self, mock_scan, mock_derive, mock_update
    ):
        """Apply mode calls update_recovery_plan correctly."""
        mock_scan.return_value = [
            {
                "planId": "plan-1",
                "planName": "DR Plan",
                "waves": [{"protectionGroupId": "pg-1"}],
            }
        ]
        mock_derive.return_value = (
            "123456789012",
            "DRSRole",
            None,
        )

        updated, skipped, errored = rp_backfill.run_backfill(
            plans_table="p",
            groups_table="g",
            region="us-east-1",
            apply=True,
        )

        mock_update.assert_called_once_with(
            "p", "us-east-1", "plan-1", "123456789012", "DRSRole"
        )
        assert updated == 1
        assert skipped == 0
        assert errored == 0

    @patch.object(rp_backfill, "update_recovery_plan")
    @patch.object(rp_backfill, "scan_recovery_plans")
    def test_skips_plan_with_no_waves(
        self, mock_scan, mock_update
    ):
        """Plans with no Protection Groups in waves are skipped."""
        mock_scan.return_value = [
            {
                "planId": "plan-empty",
                "planName": "Empty",
                "waves": [],
            }
        ]

        updated, skipped, errored = rp_backfill.run_backfill(
            plans_table="p",
            groups_table="g",
            region="us-east-1",
            apply=True,
        )

        mock_update.assert_not_called()
        assert updated == 0
        assert skipped == 1
        assert errored == 0

    @patch.object(rp_backfill, "update_recovery_plan")
    @patch.object(rp_backfill, "derive_account_id_from_groups")
    @patch.object(rp_backfill, "scan_recovery_plans")
    def test_skips_plan_with_missing_protection_groups(
        self, mock_scan, mock_derive, mock_update
    ):
        """Plans whose PGs cannot be found are skipped."""
        mock_scan.return_value = [
            {
                "planId": "plan-miss",
                "planName": "Missing PG",
                "waves": [{"protectionGroupId": "pg-gone"}],
            }
        ]
        mock_derive.return_value = (
            None,
            "",
            "no Protection Groups found",
        )

        updated, skipped, errored = rp_backfill.run_backfill(
            plans_table="p",
            groups_table="g",
            region="us-east-1",
            apply=True,
        )

        mock_update.assert_not_called()
        assert updated == 0
        assert skipped == 1
        assert errored == 0

    @patch.object(rp_backfill, "update_recovery_plan")
    @patch.object(rp_backfill, "derive_account_id_from_groups")
    @patch.object(rp_backfill, "scan_recovery_plans")
    def test_skips_plan_with_mixed_accounts(
        self, mock_scan, mock_derive, mock_update
    ):
        """Plans with mixed-account PGs are skipped."""
        mock_scan.return_value = [
            {
                "planId": "plan-mix",
                "planName": "Mixed",
                "waves": [
                    {"protectionGroupId": "pg-1"},
                    {"protectionGroupId": "pg-2"},
                ],
            }
        ]
        mock_derive.return_value = (
            None,
            "",
            "mixed accounts across Protection Groups: "
            "111111111111, 222222222222",
        )

        updated, skipped, errored = rp_backfill.run_backfill(
            plans_table="p",
            groups_table="g",
            region="us-east-1",
            apply=True,
        )

        mock_update.assert_not_called()
        assert updated == 0
        assert skipped == 1
        assert errored == 0

    @patch.object(rp_backfill, "scan_recovery_plans")
    def test_empty_scan_returns_zeros(self, mock_scan):
        """Empty scan result returns all zeros."""
        mock_scan.return_value = []

        updated, skipped, errored = rp_backfill.run_backfill(
            plans_table="p",
            groups_table="g",
            region="us-east-1",
            apply=False,
        )

        assert updated == 0
        assert skipped == 0
        assert errored == 0

    @patch.object(rp_backfill, "update_recovery_plan")
    @patch.object(rp_backfill, "derive_account_id_from_groups")
    @patch.object(rp_backfill, "scan_recovery_plans")
    def test_apply_handles_update_error(
        self, mock_scan, mock_derive, mock_update
    ):
        """Apply mode counts errors when update fails."""
        from botocore.exceptions import ClientError

        mock_scan.return_value = [
            {
                "planId": "plan-err",
                "planName": "Err",
                "waves": [{"protectionGroupId": "pg-1"}],
            }
        ]
        mock_derive.return_value = (
            "123456789012",
            "DRSRole",
            None,
        )
        mock_update.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "boom"}},
            "UpdateItem",
        )

        updated, skipped, errored = rp_backfill.run_backfill(
            plans_table="p",
            groups_table="g",
            region="us-east-1",
            apply=True,
        )

        assert updated == 0
        assert skipped == 0
        assert errored == 1

    @patch.object(rp_backfill, "update_recovery_plan")
    @patch.object(rp_backfill, "derive_account_id_from_groups")
    @patch.object(rp_backfill, "scan_recovery_plans")
    def test_plan_with_no_waves_key(
        self, mock_scan, mock_derive, mock_update
    ):
        """Plan missing the waves key entirely is skipped."""
        mock_scan.return_value = [
            {
                "planId": "plan-nowaves",
                "planName": "No Waves",
            }
        ]

        updated, skipped, errored = rp_backfill.run_backfill(
            plans_table="p",
            groups_table="g",
            region="us-east-1",
            apply=True,
        )

        mock_update.assert_not_called()
        mock_derive.assert_not_called()
        assert updated == 0
        assert skipped == 1
        assert errored == 0
