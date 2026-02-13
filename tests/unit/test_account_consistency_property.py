"""
Property-based tests for account consistency validation.

Feature: account-context-improvements
Properties:
- Property 1: Account ID Consistency — For any set of
  Protection Groups with mixed account IDs, creating a
  Recovery Plan referencing them raises a validation error.

**Validates: Requirements 2.2, 4.1, 4.2**
"""

import importlib
import json
import os
import sys
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import (
    assume,
    given,
    settings,
    HealthCheck,
)
from hypothesis import strategies as st

# Environment variables must be set before importing handler
os.environ.setdefault("PROTECTION_GROUPS_TABLE", "test-pg")
os.environ.setdefault("RECOVERY_PLANS_TABLE", "test-rp")
os.environ.setdefault("EXECUTION_HISTORY_TABLE", "test-exec")
os.environ.setdefault("TARGET_ACCOUNTS_TABLE", "test-accounts")
os.environ.setdefault("TAG_SYNC_CONFIG_TABLE", "test-tag-sync")
os.environ.setdefault(
    "EXECUTION_NOTIFICATIONS_TOPIC_ARN",
    "arn:aws:sns:us-east-1:123456789012:test-notif",
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

handler_mod = importlib.import_module("data-management-handler.index")


# ============================================================
# Strategies
# ============================================================

account_id_strategy = st.from_regex(r"^\d{12}$", fullmatch=True)

pg_id_strategy = st.from_regex(r"^pg-[a-f0-9]{8}$", fullmatch=True)


@st.composite
def protection_group_strategy(draw):
    """Generate a Protection Group dict with account ID."""
    return {
        "groupId": draw(pg_id_strategy),
        "groupName": "PG-"
        + draw(
            st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz",
                min_size=3,
                max_size=10,
            )
        ),
        "accountId": draw(account_id_strategy),
        "region": "us-east-1",
        "sourceServerIds": [],
    }


@st.composite
def mixed_account_pg_list_strategy(draw):
    """
    Generate a list of Protection Groups where at least
    two have different account IDs.

    Returns a tuple of (plan_account_id, protection_groups)
    where plan_account_id is the account used for the
    Recovery Plan, and at least one PG has a different
    account.
    """
    # Generate the plan's account ID
    plan_account_id = draw(account_id_strategy)

    # Generate at least one PG with the plan's account
    matching_pg = draw(protection_group_strategy())
    matching_pg["accountId"] = plan_account_id

    # Generate at least one PG with a different account
    mismatched_account = draw(account_id_strategy)
    assume(mismatched_account != plan_account_id)

    mismatched_pg = draw(protection_group_strategy())
    mismatched_pg["accountId"] = mismatched_account

    # Optionally add more PGs (mixed or matching)
    extra_pgs = draw(
        st.lists(
            protection_group_strategy(),
            min_size=0,
            max_size=3,
        )
    )

    # Combine: matching first, then mismatched, then extras
    all_pgs = [matching_pg, mismatched_pg] + extra_pgs

    # Shuffle so the mismatched PG isn't always second
    shuffled = draw(st.permutations(all_pgs))

    return (plan_account_id, list(shuffled))


@st.composite
def same_account_pg_list_strategy(draw):
    """
    Generate a list of Protection Groups where all share
    the same account ID.

    Returns a tuple of (account_id, protection_groups).
    """
    account_id = draw(account_id_strategy)
    pgs = draw(
        st.lists(
            protection_group_strategy(),
            min_size=1,
            max_size=5,
        )
    )
    for pg in pgs:
        pg["accountId"] = account_id
    return (account_id, pgs)


# ============================================================
# Helpers
# ============================================================


def _reset_handler_tables():
    """Reset lazy-loaded table refs in handler module."""
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


def _build_api_gw_event(body, account_id):
    """Build an API Gateway event with Cognito identity."""
    return {
        "httpMethod": "POST",
        "path": "/recovery-plans",
        "pathParameters": None,
        "queryStringParameters": None,
        "requestContext": {
            "requestId": "test-req-prop",
            "apiId": "abc123",
            "identity": {
                "cognitoIdentityId": "us-east-1:id",
                "cognitoAuthenticationProvider": (
                    "cognito-idp.us-east-1.amazonaws.com/"
                    "pool,cognito-idp.us-east-1.amazonaws"
                    ".com/pool:CognitoSignIn:" + account_id
                ),
            },
        },
        "body": json.dumps(body),
    }


def _make_pg_lookup(pgs):
    """
    Build a DynamoDB get_item side_effect that returns
    the correct Protection Group by groupId.
    """
    pg_map = {pg["groupId"]: pg for pg in pgs}

    def _get_item(Key):
        gid = Key.get("groupId", "")
        item = pg_map.get(gid)
        return {"Item": item}

    return _get_item


def _mock_tables(pg_lookup_fn):
    """
    Return an ExitStack patching handler table accessors
    with mocked DynamoDB tables.
    """
    pg_table = MagicMock()
    pg_table.get_item.side_effect = pg_lookup_fn
    pg_table.scan.return_value = {"Items": []}
    pg_table.put_item.return_value = {}

    rp_table = MagicMock()
    rp_table.scan.return_value = {"Items": []}
    rp_table.get_item.return_value = {"Item": None}
    rp_table.put_item.return_value = {}
    rp_table.update_item.return_value = {"Attributes": {}}

    exec_table = MagicMock()
    exec_table.scan.return_value = {"Items": []}

    stack = ExitStack()
    stack.enter_context(
        patch.object(
            handler_mod,
            "get_protection_groups_table",
            return_value=pg_table,
        )
    )
    stack.enter_context(
        patch.object(
            handler_mod,
            "get_recovery_plans_table",
            return_value=rp_table,
        )
    )
    stack.enter_context(
        patch.object(
            handler_mod,
            "get_executions_table",
            return_value=exec_table,
        )
    )
    return stack, rp_table


def _parse_body(result):
    """Parse JSON body from handler response."""
    raw = result.get("body", "{}")
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


# ============================================================
# Property 1: Account ID Consistency
# ============================================================


@settings(max_examples=100, deadline=None)
@given(data=mixed_account_pg_list_strategy())
@pytest.mark.property
def test_property_mixed_accounts_rejected(data):
    """
    Property 1: Account ID Consistency.

    For any set of Protection Groups with mixed account IDs,
    creating a Recovery Plan referencing them raises a
    validation error (400 with ACCOUNT_MISMATCH).

    **Validates: Requirements 2.2, 4.1, 4.2**
    """
    plan_account_id, pgs = data

    # Confirm at least two distinct account IDs exist
    unique_accounts = set(pg["accountId"] for pg in pgs)
    assume(len(unique_accounts) >= 2)

    # Ensure all PG IDs are unique
    pg_ids = [pg["groupId"] for pg in pgs]
    assume(len(pg_ids) == len(set(pg_ids)))

    _reset_handler_tables()

    # Build waves referencing each Protection Group
    waves = [{"protectionGroupId": pg["groupId"]} for pg in pgs]

    body = {
        "name": "PropTest-Mixed",
        "accountId": plan_account_id,
        "waves": waves,
    }
    event = _build_api_gw_event(body, plan_account_id)

    pg_lookup = _make_pg_lookup(pgs)
    ctx, rp_table = _mock_tables(pg_lookup)

    with ctx:
        result = handler_mod.create_recovery_plan(event, body)

    resp = _parse_body(result)

    # Must be rejected with 400
    assert result["statusCode"] == 400, (
        f"Expected 400 for mixed accounts, got "
        f"{result['statusCode']}. "
        f"Accounts: {unique_accounts}. "
        f"Response: {resp}"
    )
    assert resp.get("error") == "ACCOUNT_MISMATCH", (
        f"Expected ACCOUNT_MISMATCH error, got " f"{resp.get('error')}. Response: {resp}"
    )

    # Recovery Plan must NOT be persisted
    rp_table.put_item.assert_not_called()


@settings(max_examples=100, deadline=None)
@given(data=same_account_pg_list_strategy())
@pytest.mark.property
def test_property_same_account_accepted(data):
    """
    Property 1 (supplemental): When all Protection Groups
    share the same account ID as the Recovery Plan, creation
    succeeds (no ACCOUNT_MISMATCH error).

    **Validates: Requirements 2.2, 4.1, 4.2**
    """
    account_id, pgs = data

    # Ensure all PG IDs are unique
    pg_ids = [pg["groupId"] for pg in pgs]
    assume(len(pg_ids) == len(set(pg_ids)))

    _reset_handler_tables()

    waves = [{"protectionGroupId": pg["groupId"]} for pg in pgs]

    body = {
        "name": "PropTest-Same",
        "accountId": account_id,
        "waves": waves,
    }
    event = _build_api_gw_event(body, account_id)

    pg_lookup = _make_pg_lookup(pgs)
    ctx, rp_table = _mock_tables(pg_lookup)

    with (
        ctx,
        patch.object(
            handler_mod,
            "validate_waves",
            return_value=None,
        ),
        patch(
            "shared.conflict_detection" ".resolve_pg_servers_for_conflict_check",
            return_value=[],
        ),
        patch(
            "shared.conflict_detection" ".check_concurrent_jobs_limit",
            return_value={
                "canStartJob": True,
                "currentJobs": 0,
                "maxJobs": 20,
            },
        ),
        patch(
            "shared.conflict_detection" ".check_server_conflicts",
            return_value=[],
        ),
    ):
        result = handler_mod.create_recovery_plan(event, body)

    resp = _parse_body(result)

    # Must NOT be rejected with ACCOUNT_MISMATCH
    if result["statusCode"] == 400:
        assert resp.get("error") != "ACCOUNT_MISMATCH", (
            f"Same-account PGs should not trigger " f"ACCOUNT_MISMATCH. Account: {account_id}. " f"Response: {resp}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
