"""
Unit tests for data-management-handler account context and
notification subscription lifecycle.

Validates: Requirements 1.1, 1.2, 2.1, 2.2, 4.1, 5.1,
    5.2, 5.5, 5.12
"""
import importlib
import json
import os
import sys
from contextlib import ExitStack
from unittest.mock import MagicMock, patch
import pytest

os.environ["PROTECTION_GROUPS_TABLE"] = "test-pg"
os.environ["RECOVERY_PLANS_TABLE"] = "test-rp"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-exec"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-accounts"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag-sync"
os.environ["EXECUTION_NOTIFICATIONS_TOPIC_ARN"] = (
    "arn:aws:sns:us-east-1:123456789012:test-notifications"
)
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../lambda")
)
handler_mod = importlib.import_module(
    "data-management-handler.index"
)

VALID_ACCOUNT = "123456789012"
OTHER_ACCOUNT = "999888777666"
VALID_EMAIL = "team@example.com"
NEW_EMAIL = "new-team@example.com"
SUB_ARN = (
    "arn:aws:sns:us-east-1:123456789012:"
    "test-notifications:sub-uuid-1234"
)
NEW_SUB_ARN = (
    "arn:aws:sns:us-east-1:123456789012:"
    "test-notifications:sub-uuid-5678"
)


def _api_gw_event(body, method="POST", path="/protection-groups"):
    """Build a minimal API Gateway proxy event."""
    return {
        "httpMethod": method,
        "path": path,
        "pathParameters": None,
        "queryStringParameters": None,
        "requestContext": {
            "requestId": "test-req-1",
            "apiId": "abc123",
            "identity": {
                "cognitoIdentityId": "us-east-1:id",
                "cognitoAuthenticationProvider": (
                    "cognito-idp.us-east-1.amazonaws.com/"
                    "pool,cognito-idp.us-east-1.amazonaws"
                    ".com/pool:CognitoSignIn:"
                    + VALID_ACCOUNT
                ),
            },
        },
        "body": json.dumps(body),
    }


def _direct_event(operation, body):
    """Build a direct Lambda invocation event."""
    return {"operation": operation, "body": body}


def _body(result):
    """Parse JSON body from an API Gateway response."""
    raw = result.get("body", "{}")
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


@pytest.fixture(autouse=True)
def _reset_tables():
    """Reset lazy-loaded table refs between tests."""
    handler_mod._protection_groups_table = None
    handler_mod._recovery_plans_table = None
    handler_mod._executions_table = None
    handler_mod._target_accounts_table = None
    handler_mod._tag_sync_config_table = None
    import shared.account_utils as au
    import shared.conflict_detection as cd
    au._dynamodb = None
    au._target_accounts_table = None
    cd._protection_groups_table = None
    cd._recovery_plans_table = None
    cd._execution_history_table = None
    cd.dynamodb = None
    yield
    patch.stopall()


@pytest.fixture
def pg_table():
    """Mock Protection Groups DynamoDB table."""
    tbl = MagicMock()
    tbl.scan.return_value = {"Items": []}
    tbl.get_item.return_value = {"Item": None}
    tbl.put_item.return_value = {}
    return tbl


@pytest.fixture
def rp_table():
    """Mock Recovery Plans DynamoDB table."""
    tbl = MagicMock()
    tbl.scan.return_value = {"Items": []}
    tbl.get_item.return_value = {"Item": None}
    tbl.put_item.return_value = {}
    tbl.update_item.return_value = {"Attributes": {}}
    tbl.delete_item.return_value = {}
    return tbl


@pytest.fixture
def exec_table():
    """Mock Executions DynamoDB table."""
    tbl = MagicMock()
    tbl.scan.return_value = {"Items": []}
    return tbl


def _patch_tables(pg_tbl, rp_tbl, ex_tbl):
    """Return a combined context manager patching tables."""
    stack = ExitStack()
    stack.enter_context(patch.object(
        handler_mod, "get_protection_groups_table",
        return_value=pg_tbl,
    ))
    stack.enter_context(patch.object(
        handler_mod, "get_recovery_plans_table",
        return_value=rp_tbl,
    ))
    stack.enter_context(patch.object(
        handler_mod, "get_executions_table",
        return_value=ex_tbl,
    ))
    return stack


# ============================================================
# 1-3  Protection Group creation - account context
# ============================================================

class TestPGCreationAccountContext:
    """PG creation with account context for both modes.

    Validates: Requirements 1.1, 1.6, 1.7
    """

    def test_api_gw_with_valid_account(
        self, pg_table, rp_table, exec_table,
    ):
        """API Gateway mode: accountId in body is stored."""
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.return_value = {
            "items": [
                {"sourceServerID": "s-12345678901234567"}
            ]
        }
        body = {
            "groupName": "TestPG",
            "region": "us-east-1",
            "accountId": VALID_ACCOUNT,
            "sourceServerIds": ["s-12345678901234567"],
        }
        event = _api_gw_event(body)
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod, "create_drs_client",
            return_value=mock_drs,
        ), patch.object(
            handler_mod,
            "check_server_conflicts_for_create",
            return_value=[],
        ):
            result = handler_mod.create_protection_group(
                event, body
            )
        assert result["statusCode"] == 201
        saved = pg_table.put_item.call_args[1]["Item"]
        assert saved["accountId"] == VALID_ACCOUNT

    def test_direct_invocation_with_valid_account(
        self, pg_table, rp_table, exec_table,
    ):
        """Direct invocation: explicit accountId stored."""
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.return_value = {
            "items": [
                {"sourceServerID": "s-12345678901234567"}
            ]
        }
        body = {
            "groupName": "DirectPG",
            "region": "us-east-1",
            "accountId": VALID_ACCOUNT,
            "sourceServerIds": ["s-12345678901234567"],
        }
        event = _direct_event(
            "create_protection_group", body
        )
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod, "create_drs_client",
            return_value=mock_drs,
        ), patch.object(
            handler_mod,
            "check_server_conflicts_for_create",
            return_value=[],
        ):
            result = handler_mod.create_protection_group(
                event, body
            )
        assert result["statusCode"] == 201
        saved = pg_table.put_item.call_args[1]["Item"]
        assert saved["accountId"] == VALID_ACCOUNT

    def test_direct_invocation_missing_account_fails(
        self, pg_table, rp_table, exec_table,
    ):
        """Direct invocation without accountId => 400."""
        body = {
            "groupName": "NoPG",
            "region": "us-east-1",
            "sourceServerIds": ["s-12345678901234567"],
        }
        event = _direct_event(
            "create_protection_group", body
        )
        with _patch_tables(
            pg_table, rp_table, exec_table
        ):
            result = handler_mod.create_protection_group(
                event, body
            )
        assert result["statusCode"] == 400
        resp = _body(result)
        assert "accountId" in resp.get("message", "")
        pg_table.put_item.assert_not_called()


# ============================================================
# 4-5  Recovery Plan creation - notification email & SNS
# ============================================================

def _make_pg_lookup(pg_table, account_id):
    """Configure pg_table.get_item to return a PG."""
    def _get_item(Key):
        gid = Key.get("groupId", "")
        if gid == "pg-aaa":
            return {
                "Item": {
                    "groupId": "pg-aaa",
                    "groupName": "PG-A",
                    "accountId": account_id,
                    "region": "us-east-1",
                    "sourceServerIds": [],
                }
            }
        return {"Item": None}
    pg_table.get_item.side_effect = _get_item


class TestRPCreationNotification:
    """RP creation with notification email and SNS sub.

    Validates: Requirements 1.2, 2.1, 5.1, 5.2
    """

    def test_create_with_email_creates_subscription(
        self, pg_table, rp_table, exec_table,
    ):
        """Email provided => SNS subscription created."""
        _make_pg_lookup(pg_table, VALID_ACCOUNT)
        body = {
            "name": "Plan-Email",
            "accountId": VALID_ACCOUNT,
            "notificationEmail": VALID_EMAIL,
            "waves": [
                {"protectionGroupId": "pg-aaa"},
            ],
        }
        event = _api_gw_event(body, path="/recovery-plans")
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod,
            "manage_recovery_plan_subscription",
            return_value=SUB_ARN,
        ) as ms, patch.object(
            handler_mod, "validate_waves",
            return_value=None,
        ), patch(
            "shared.conflict_detection"
            ".resolve_pg_servers_for_conflict_check",
            return_value=[],
        ):
            result = handler_mod.create_recovery_plan(
                event, body
            )
        assert result["statusCode"] == 201
        resp = _body(result)
        assert resp["notificationEmail"] == VALID_EMAIL
        assert resp["snsSubscriptionArn"] == SUB_ARN
        assert resp["accountId"] == VALID_ACCOUNT
        ms.assert_called_once()
        kw = ms.call_args[1]
        assert kw["email"] == VALID_EMAIL
        assert kw["action"] == "create"

    def test_create_without_email_no_subscription(
        self, pg_table, rp_table, exec_table,
    ):
        """No email => no SNS subscription created."""
        _make_pg_lookup(pg_table, VALID_ACCOUNT)
        body = {
            "name": "Plan-NoEmail",
            "accountId": VALID_ACCOUNT,
            "waves": [
                {"protectionGroupId": "pg-aaa"},
            ],
        }
        event = _api_gw_event(body, path="/recovery-plans")
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod,
            "manage_recovery_plan_subscription",
            return_value=SUB_ARN,
        ) as ms, patch.object(
            handler_mod, "validate_waves",
            return_value=None,
        ), patch(
            "shared.conflict_detection"
            ".resolve_pg_servers_for_conflict_check",
            return_value=[],
        ):
            result = handler_mod.create_recovery_plan(
                event, body
            )
        assert result["statusCode"] == 201
        resp = _body(result)
        assert resp["notificationEmail"] == ""
        assert resp["snsSubscriptionArn"] == ""
        ms.assert_not_called()

    def test_create_stores_account_fields(
        self, pg_table, rp_table, exec_table,
    ):
        """RP stores accountId and assumeRoleName."""
        _make_pg_lookup(pg_table, VALID_ACCOUNT)
        body = {
            "name": "Plan-Account",
            "accountId": VALID_ACCOUNT,
            "assumeRoleName": "DRSRole",
            "waves": [
                {"protectionGroupId": "pg-aaa"},
            ],
        }
        event = _api_gw_event(body, path="/recovery-plans")
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod, "validate_waves",
            return_value=None,
        ), patch(
            "shared.conflict_detection"
            ".resolve_pg_servers_for_conflict_check",
            return_value=[],
        ):
            result = handler_mod.create_recovery_plan(
                event, body
            )
        assert result["statusCode"] == 201
        saved = rp_table.put_item.call_args[1]["Item"]
        assert saved["accountId"] == VALID_ACCOUNT
        assert saved["assumeRoleName"] == "DRSRole"


# ============================================================
# 6-7  Recovery Plan update - email change
# ============================================================

def _existing_plan(email="", sub_arn=""):
    """Return a mock existing Recovery Plan item."""
    return {
        "planId": "rp-111",
        "planName": "Existing Plan",
        "accountId": VALID_ACCOUNT,
        "notificationEmail": email,
        "snsSubscriptionArn": sub_arn,
        "waves": [],
        "version": 1,
        "createdDate": 1000000,
        "lastModifiedDate": 1000000,
    }


class TestRPUpdateEmailChange:
    """RP update with notification email changes.

    Validates: Requirements 5.5, 5.12
    """

    def test_update_email_deletes_old_creates_new(
        self, pg_table, rp_table, exec_table,
    ):
        """Changing email deletes old sub, creates new."""
        existing = _existing_plan(
            email=VALID_EMAIL, sub_arn=SUB_ARN
        )
        rp_table.get_item.return_value = {"Item": existing}
        rp_table.update_item.return_value = {
            "Attributes": {
                **existing,
                "notificationEmail": NEW_EMAIL,
                "snsSubscriptionArn": NEW_SUB_ARN,
                "version": 2,
            }
        }
        body = {"notificationEmail": NEW_EMAIL}
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod,
            "manage_recovery_plan_subscription",
            return_value=NEW_SUB_ARN,
        ) as ms, patch.object(
            handler_mod,
            "get_active_executions_for_plan",
            return_value=[],
        ):
            result = handler_mod.update_recovery_plan(
                "rp-111", body
            )
        assert result["statusCode"] == 200
        calls = ms.call_args_list
        del_calls = [
            c for c in calls
            if c[1].get("action") == "delete"
        ]
        cre_calls = [
            c for c in calls
            if c[1].get("action") == "create"
        ]
        assert len(del_calls) == 1
        assert del_calls[0][1]["email"] == VALID_EMAIL
        assert len(cre_calls) == 1
        assert cre_calls[0][1]["email"] == NEW_EMAIL

    def test_update_remove_email_clears_subscription(
        self, pg_table, rp_table, exec_table,
    ):
        """Removing email deletes sub, clears ARN."""
        existing = _existing_plan(
            email=VALID_EMAIL, sub_arn=SUB_ARN
        )
        rp_table.get_item.return_value = {"Item": existing}
        rp_table.update_item.return_value = {
            "Attributes": {
                **existing,
                "notificationEmail": "",
                "snsSubscriptionArn": "",
                "version": 2,
            }
        }
        body = {"notificationEmail": ""}
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod,
            "manage_recovery_plan_subscription",
        ) as ms, patch.object(
            handler_mod,
            "get_active_executions_for_plan",
            return_value=[],
        ):
            result = handler_mod.update_recovery_plan(
                "rp-111", body
            )
        assert result["statusCode"] == 200
        calls = ms.call_args_list
        del_calls = [
            c for c in calls
            if c[1].get("action") == "delete"
        ]
        cre_calls = [
            c for c in calls
            if c[1].get("action") == "create"
        ]
        assert len(del_calls) == 1
        assert len(cre_calls) == 0


# ============================================================
# 8  Recovery Plan deletion - subscription cleanup
# ============================================================

class TestRPDeletionSubscriptionCleanup:
    """RP deletion cleans up SNS subscription.

    Validates: Requirements 5.12
    """

    def test_delete_plan_cleans_up_subscription(
        self, pg_table, rp_table, exec_table,
    ):
        """Deleting plan with email deletes SNS sub."""
        plan_item = {
            "planId": "rp-del",
            "planName": "Delete Me",
            "accountId": VALID_ACCOUNT,
            "notificationEmail": VALID_EMAIL,
            "snsSubscriptionArn": SUB_ARN,
            "waves": [],
            "version": 1,
        }
        rp_table.get_item.return_value = {"Item": plan_item}
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod,
            "manage_recovery_plan_subscription",
        ) as ms, patch.object(
            handler_mod,
            "get_active_executions_for_plan",
            return_value=[],
        ):
            result = handler_mod.delete_recovery_plan(
                "rp-del"
            )
        assert result["statusCode"] == 200
        ms.assert_called_once_with(
            plan_id="rp-del",
            email=VALID_EMAIL,
            action="delete",
        )
        rp_table.delete_item.assert_called_once_with(
            Key={"planId": "rp-del"}
        )

    def test_delete_plan_without_email_skips_cleanup(
        self, pg_table, rp_table, exec_table,
    ):
        """Deleting plan without email skips sub cleanup."""
        plan_item = {
            "planId": "rp-noemail",
            "planName": "No Email Plan",
            "accountId": VALID_ACCOUNT,
            "notificationEmail": "",
            "snsSubscriptionArn": "",
            "waves": [],
            "version": 1,
        }
        rp_table.get_item.return_value = {"Item": plan_item}
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod,
            "manage_recovery_plan_subscription",
        ) as ms, patch.object(
            handler_mod,
            "get_active_executions_for_plan",
            return_value=[],
        ):
            result = handler_mod.delete_recovery_plan(
                "rp-noemail"
            )
        assert result["statusCode"] == 200
        ms.assert_not_called()
        rp_table.delete_item.assert_called_once()


# ============================================================
# 9  Account consistency validation across waves
# ============================================================

class TestAccountConsistencyValidation:
    """RP creation fails when PGs have different accounts.

    Validates: Requirements 2.2, 4.1
    """

    def _make_multi_pg_lookup(self, pg_table):
        """PGs with different accounts."""
        def _get_item(Key):
            gid = Key.get("groupId", "")
            if gid == "pg-acct1":
                return {
                    "Item": {
                        "groupId": "pg-acct1",
                        "groupName": "PG-Acct1",
                        "accountId": VALID_ACCOUNT,
                        "region": "us-east-1",
                        "sourceServerIds": [],
                    }
                }
            if gid == "pg-acct2":
                return {
                    "Item": {
                        "groupId": "pg-acct2",
                        "groupName": "PG-Acct2",
                        "accountId": OTHER_ACCOUNT,
                        "region": "us-east-1",
                        "sourceServerIds": [],
                    }
                }
            return {"Item": None}
        pg_table.get_item.side_effect = _get_item

    def test_mixed_accounts_rejected(
        self, pg_table, rp_table, exec_table,
    ):
        """Waves with PGs from different accounts => 400."""
        self._make_multi_pg_lookup(pg_table)
        body = {
            "name": "Mixed-Plan",
            "accountId": VALID_ACCOUNT,
            "waves": [
                {"protectionGroupId": "pg-acct1"},
                {"protectionGroupId": "pg-acct2"},
            ],
        }
        event = _api_gw_event(body, path="/recovery-plans")
        with _patch_tables(
            pg_table, rp_table, exec_table
        ):
            result = handler_mod.create_recovery_plan(
                event, body
            )
        assert result["statusCode"] == 400
        resp = _body(result)
        assert resp["error"] == "ACCOUNT_MISMATCH"
        assert OTHER_ACCOUNT in resp["message"]
        rp_table.put_item.assert_not_called()

    def test_same_account_accepted(
        self, pg_table, rp_table, exec_table,
    ):
        """Waves with PGs from same account => success."""
        def _get_item(Key):
            gid = Key.get("groupId", "")
            if gid in ("pg-a", "pg-b"):
                return {
                    "Item": {
                        "groupId": gid,
                        "groupName": "PG-" + gid,
                        "accountId": VALID_ACCOUNT,
                        "region": "us-east-1",
                        "sourceServerIds": [],
                    }
                }
            return {"Item": None}
        pg_table.get_item.side_effect = _get_item
        body = {
            "name": "Same-Acct-Plan",
            "accountId": VALID_ACCOUNT,
            "waves": [
                {"protectionGroupId": "pg-a"},
                {"protectionGroupId": "pg-b"},
            ],
        }
        event = _api_gw_event(body, path="/recovery-plans")
        with _patch_tables(
            pg_table, rp_table, exec_table
        ), patch.object(
            handler_mod, "validate_waves",
            return_value=None,
        ), patch(
            "shared.conflict_detection"
            ".resolve_pg_servers_for_conflict_check",
            return_value=[],
        ):
            result = handler_mod.create_recovery_plan(
                event, body
            )
        assert result["statusCode"] == 201
        saved = rp_table.put_item.call_args[1]["Item"]
        assert saved["accountId"] == VALID_ACCOUNT

    def test_pg_not_found_returns_error(
        self, pg_table, rp_table, exec_table,
    ):
        """Wave referencing non-existent PG returns 400."""
        pg_table.get_item.return_value = {"Item": None}
        body = {
            "name": "Missing-PG-Plan",
            "accountId": VALID_ACCOUNT,
            "waves": [
                {"protectionGroupId": "pg-missing"},
            ],
        }
        event = _api_gw_event(body, path="/recovery-plans")
        with _patch_tables(
            pg_table, rp_table, exec_table
        ):
            result = handler_mod.create_recovery_plan(
                event, body
            )
        assert result["statusCode"] == 400
        resp = _body(result)
        assert resp["error"] == "PG_NOT_FOUND"
        rp_table.put_item.assert_not_called()
