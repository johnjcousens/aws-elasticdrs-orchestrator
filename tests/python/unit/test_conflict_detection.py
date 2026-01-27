"""
Unit tests for conflict_detection shared utilities.

Tests conflict detection logic for preventing overlapping DR operations.
"""

import os
import sys
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

# Add lambda directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda"
    ),
)

# Set environment variables before importing module
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"

from shared.conflict_detection import (
    check_server_conflicts,
    check_server_conflicts_for_create,
    check_server_conflicts_for_update,
    get_servers_in_active_executions,
)


@pytest.fixture
def mock_dynamodb_tables():
    """Mock DynamoDB tables"""
    with patch("shared.conflict_detection.protection_groups_table") as mock_pg, \
         patch("shared.conflict_detection.recovery_plans_table") as mock_rp, \
         patch("shared.conflict_detection.execution_history_table") as mock_eh:
        yield {
            "protection_groups": mock_pg,
            "recovery_plans": mock_rp,
            "execution_history": mock_eh,
        }


@pytest.fixture
def sample_protection_group():
    """Sample Protection Group"""
    return {
        "groupId": "pg-123",
        "groupName": "Test PG",
        "region": "us-east-1",
        "sourceServerIds": ["s-111", "s-222"],
    }


@pytest.fixture
def sample_recovery_plan():
    """Sample Recovery Plan"""
    return {
        "planId": "plan-123",
        "planName": "Test Plan",
        "waves": [
            {
                "waveName": "Wave 1",
                "protectionGroupId": "pg-123",
            }
        ],
    }


@pytest.fixture
def sample_execution():
    """Sample active execution"""
    return {
        "executionId": "exec-123",
        "planId": "plan-123",
        "status": "IN_PROGRESS",
        "currentWave": Decimal("1"),
        "waves": [
            {
                "waveName": "Wave 1",
                "serverStatuses": [
                    {
                        "sourceServerId": "s-111",
                        "launchStatus": "PENDING",
                    }
                ],
            }
        ],
    }


def test_check_server_conflicts_for_create_no_conflicts(mock_dynamodb_tables):
    """Test check_server_conflicts_for_create with no conflicts"""
    # Mock scan to return no existing PGs
    mock_dynamodb_tables["protection_groups"].scan.return_value = {
        "Items": []
    }

    conflicts = check_server_conflicts_for_create(["s-111", "s-222"])

    assert conflicts == []
    mock_dynamodb_tables["protection_groups"].scan.assert_called_once()


def test_check_server_conflicts_for_create_with_conflicts(mock_dynamodb_tables):
    """Test check_server_conflicts_for_create with conflicts"""
    # Mock scan to return existing PG with conflicting servers
    mock_dynamodb_tables["protection_groups"].scan.return_value = {
        "Items": [
            {
                "groupId": "pg-existing",
                "groupName": "Existing PG",
                "sourceServerIds": ["s-111", "s-333"],
            }
        ]
    }

    conflicts = check_server_conflicts_for_create(["s-111", "s-222"])

    assert len(conflicts) == 1
    assert conflicts[0]["serverId"] == "s-111"
    assert conflicts[0]["protectionGroupId"] == "pg-existing"
    assert conflicts[0]["protectionGroupName"] == "Existing PG"


def test_check_server_conflicts_for_update_excludes_current_pg(
    mock_dynamodb_tables,
):
    """Test check_server_conflicts_for_update excludes current PG"""
    # Mock scan to return current PG and another PG
    mock_dynamodb_tables["protection_groups"].scan.return_value = {
        "Items": [
            {
                "groupId": "pg-current",
                "groupName": "Current PG",
                "sourceServerIds": ["s-111"],
            },
            {
                "groupId": "pg-other",
                "groupName": "Other PG",
                "sourceServerIds": ["s-222"],
            },
        ]
    }

    conflicts = check_server_conflicts_for_update(["s-111", "s-222"], "pg-current")

    # Should only find conflict with s-222 (s-111 is in current PG, so excluded)
    assert len(conflicts) == 1
    assert conflicts[0]["serverId"] == "s-222"
    assert conflicts[0]["protectionGroupId"] == "pg-other"


def test_check_server_conflicts_for_update_no_conflicts(mock_dynamodb_tables):
    """Test check_server_conflicts_for_update with no conflicts"""
    # Mock scan to return only current PG
    mock_dynamodb_tables["protection_groups"].scan.return_value = {
        "Items": [
            {
                "groupId": "pg-current",
                "groupName": "Current PG",
                "sourceServerIds": ["s-111", "s-222"],
            }
        ]
    }

    conflicts = check_server_conflicts_for_update(["s-111", "s-222"], "pg-current")

    assert conflicts == []


@patch("shared.conflict_detection.get_all_active_executions")
def test_get_servers_in_active_executions_from_server_statuses(
    mock_get_executions, mock_dynamodb_tables, sample_execution, sample_recovery_plan
):
    """Test get_servers_in_active_executions extracts from serverStatuses"""
    mock_get_executions.return_value = [sample_execution]
    mock_dynamodb_tables["recovery_plans"].get_item.return_value = {
        "Item": sample_recovery_plan
    }

    servers = get_servers_in_active_executions()

    assert "s-111" in servers
    assert servers["s-111"]["executionId"] == "exec-123"
    assert servers["s-111"]["planId"] == "plan-123"
    assert servers["s-111"]["launchStatus"] == "PENDING"


@patch("shared.conflict_detection.get_all_active_executions")
@patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
def test_get_servers_in_active_executions_resolves_from_pg(
    mock_resolve, mock_get_executions, mock_dynamodb_tables, sample_recovery_plan
):
    """Test get_servers_in_active_executions resolves servers from Protection Groups"""
    # Execution without serverStatuses
    execution = {
        "executionId": "exec-123",
        "planId": "plan-123",
        "status": "PENDING",
        "currentWave": Decimal("1"),
        "waves": [],
    }
    mock_get_executions.return_value = [execution]
    mock_dynamodb_tables["recovery_plans"].get_item.return_value = {
        "Item": sample_recovery_plan
    }
    mock_resolve.return_value = ["s-111", "s-222"]

    servers = get_servers_in_active_executions()

    assert "s-111" in servers
    assert "s-222" in servers
    assert servers["s-111"]["executionId"] == "exec-123"
    mock_resolve.assert_called()


@patch("shared.conflict_detection.get_servers_in_active_executions")
@patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
@patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
def test_check_server_conflicts_detects_execution_conflicts(
    mock_resolve,
    mock_drs_jobs,
    mock_active_executions,
    mock_dynamodb_tables,
    sample_recovery_plan,
    sample_protection_group,
):
    """Test check_server_conflicts detects conflicts from active executions"""
    mock_active_executions.return_value = {
        "s-111": {
            "executionId": "exec-other",
            "planId": "plan-other",
            "waveName": "Wave 1",
            "executionStatus": "IN_PROGRESS",
        }
    }
    mock_drs_jobs.return_value = {}
    mock_resolve.return_value = ["s-111", "s-222"]
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": sample_protection_group
    }

    conflicts = check_server_conflicts(sample_recovery_plan)

    assert len(conflicts) == 1
    assert conflicts[0]["serverId"] == "s-111"
    assert conflicts[0]["conflictSource"] == "execution"
    assert conflicts[0]["conflictingExecutionId"] == "exec-other"


@patch("shared.conflict_detection.get_servers_in_active_executions")
@patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
@patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
def test_check_server_conflicts_detects_drs_job_conflicts(
    mock_resolve,
    mock_drs_jobs,
    mock_active_executions,
    mock_dynamodb_tables,
    sample_recovery_plan,
    sample_protection_group,
):
    """Test check_server_conflicts detects conflicts from DRS jobs"""
    mock_active_executions.return_value = {}
    mock_drs_jobs.return_value = {
        "s-222": {
            "jobId": "job-123",
            "jobStatus": "STARTED",
            "jobType": "LAUNCH",
            "launchStatus": "PENDING",
        }
    }
    mock_resolve.return_value = ["s-111", "s-222"]
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": sample_protection_group
    }

    conflicts = check_server_conflicts(sample_recovery_plan)

    assert len(conflicts) == 1
    assert conflicts[0]["serverId"] == "s-222"
    assert conflicts[0]["conflictSource"] == "drs_job"
    assert conflicts[0]["conflictingJobId"] == "job-123"


@patch("shared.conflict_detection.get_servers_in_active_executions")
@patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
@patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
def test_check_server_conflicts_no_conflicts(
    mock_resolve,
    mock_drs_jobs,
    mock_active_executions,
    mock_dynamodb_tables,
    sample_recovery_plan,
    sample_protection_group,
):
    """Test check_server_conflicts with no conflicts"""
    mock_active_executions.return_value = {}
    mock_drs_jobs.return_value = {}
    mock_resolve.return_value = ["s-111", "s-222"]
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": sample_protection_group
    }

    conflicts = check_server_conflicts(sample_recovery_plan)

    assert conflicts == []



@patch("shared.conflict_detection.get_servers_in_active_executions")
@patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
@patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
def test_get_plans_with_conflicts_detects_execution_conflicts(
    mock_resolve,
    mock_drs_jobs,
    mock_active_executions,
    mock_dynamodb_tables,
    sample_recovery_plan,
    sample_protection_group,
):
    """Test get_plans_with_conflicts detects plans with server conflicts"""
    from shared.conflict_detection import get_plans_with_conflicts

    mock_active_executions.return_value = {
        "s-111": {
            "executionId": "exec-other",
            "planId": "plan-other",
            "waveName": "Wave 1",
            "executionStatus": "IN_PROGRESS",
        }
    }
    mock_drs_jobs.return_value = {}
    mock_resolve.return_value = ["s-111", "s-222"]
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": sample_protection_group
    }
    mock_dynamodb_tables["recovery_plans"].scan.return_value = {
        "Items": [sample_recovery_plan]
    }

    plans_with_conflicts = get_plans_with_conflicts()

    assert "plan-123" in plans_with_conflicts
    assert plans_with_conflicts["plan-123"]["hasConflict"] is True
    assert "s-111" in plans_with_conflicts["plan-123"]["conflictingServers"]


@patch("shared.conflict_detection.get_servers_in_active_executions")
@patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
@patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
def test_get_plans_with_conflicts_detects_drs_job_conflicts(
    mock_resolve,
    mock_drs_jobs,
    mock_active_executions,
    mock_dynamodb_tables,
    sample_recovery_plan,
    sample_protection_group,
):
    """Test get_plans_with_conflicts detects DRS job conflicts"""
    from shared.conflict_detection import get_plans_with_conflicts

    mock_active_executions.return_value = {}
    mock_drs_jobs.return_value = {
        "s-222": {
            "jobId": "job-123",
            "jobStatus": "STARTED",
            "jobType": "LAUNCH",
            "launchStatus": "PENDING",
        }
    }
    mock_resolve.return_value = ["s-111", "s-222"]
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": sample_protection_group
    }
    mock_dynamodb_tables["recovery_plans"].scan.return_value = {
        "Items": [sample_recovery_plan]
    }

    plans_with_conflicts = get_plans_with_conflicts()

    assert "plan-123" in plans_with_conflicts
    assert plans_with_conflicts["plan-123"]["hasConflict"] is True
    assert "s-222" in plans_with_conflicts["plan-123"]["conflictingServers"]
    assert plans_with_conflicts["plan-123"]["conflictingDrsJobId"] == "job-123"


@patch("shared.conflict_detection.get_servers_in_active_executions")
@patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
@patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
def test_get_plans_with_conflicts_no_conflicts(
    mock_resolve,
    mock_drs_jobs,
    mock_active_executions,
    mock_dynamodb_tables,
    sample_recovery_plan,
    sample_protection_group,
):
    """Test get_plans_with_conflicts returns empty dict when no conflicts"""
    from shared.conflict_detection import get_plans_with_conflicts

    mock_active_executions.return_value = {}
    mock_drs_jobs.return_value = {}
    mock_resolve.return_value = ["s-111", "s-222"]
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": sample_protection_group
    }
    mock_dynamodb_tables["recovery_plans"].scan.return_value = {
        "Items": [sample_recovery_plan]
    }

    plans_with_conflicts = get_plans_with_conflicts()

    assert plans_with_conflicts == {}


def test_has_circular_dependencies_detects_simple_cycle():
    """Test has_circular_dependencies detects simple circular dependency"""
    from shared.conflict_detection import has_circular_dependencies

    # A -> B -> A (simple cycle)
    graph = {
        "A": ["B"],
        "B": ["A"],
    }

    assert has_circular_dependencies(graph) is True


def test_has_circular_dependencies_detects_complex_cycle():
    """Test has_circular_dependencies detects complex circular dependency"""
    from shared.conflict_detection import has_circular_dependencies

    # A -> B -> C -> A (complex cycle)
    graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"],
    }

    assert has_circular_dependencies(graph) is True


def test_has_circular_dependencies_no_cycle():
    """Test has_circular_dependencies returns False for acyclic graph"""
    from shared.conflict_detection import has_circular_dependencies

    # A -> B -> C (no cycle)
    graph = {
        "A": ["B"],
        "B": ["C"],
        "C": [],
    }

    assert has_circular_dependencies(graph) is False


def test_has_circular_dependencies_empty_graph():
    """Test has_circular_dependencies handles empty graph"""
    from shared.conflict_detection import has_circular_dependencies

    graph = {}

    assert has_circular_dependencies(graph) is False


def test_has_circular_dependencies_self_loop():
    """Test has_circular_dependencies detects self-loop"""
    from shared.conflict_detection import has_circular_dependencies

    # A -> A (self-loop)
    graph = {
        "A": ["A"],
    }

    assert has_circular_dependencies(graph) is True
