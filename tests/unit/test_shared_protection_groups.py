"""
Shared Protection Group Detection and Edge Case Tests

Tests for:
1. Detection of Protection Groups shared across multiple Recovery Plans
2. Warning generation for shared PGs
3. Edge cases in conflict detection
4. DRS limit enforcement edge cases

Validates: DRS rule that only 1 concurrent job per server is allowed
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "shared"
sys.path.insert(0, str(lambda_dir))

from conflict_detection import (  # noqa: E402
    check_server_conflicts,
    get_shared_protection_groups,
    get_plan_shared_pg_warnings,
    get_servers_in_active_drs_jobs,
    get_servers_in_active_executions,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_dynamodb_tables():
    """Mock DynamoDB tables for conflict detection"""
    pg_table = MagicMock()
    rp_table = MagicMock()
    eh_table = MagicMock()
    
    with patch("conflict_detection.get_protection_groups_table", return_value=pg_table), \
         patch("conflict_detection.get_recovery_plans_table", return_value=rp_table), \
         patch("conflict_detection.get_execution_history_table", return_value=eh_table):
        yield {
            "protection_groups": pg_table,
            "recovery_plans": rp_table,
            "execution_history": eh_table,
        }


@pytest.fixture
def sample_plans_sharing_pg():
    """Two recovery plans that share the same Protection Group"""
    return [
        {
            "planId": "plan-A",
            "planName": "Plan Alpha",
            "waves": [
                {"waveName": "Wave1", "protectionGroupId": "pg-shared"},
            ],
        },
        {
            "planId": "plan-B",
            "planName": "Plan Beta",
            "waves": [
                {"waveName": "Wave1", "protectionGroupId": "pg-shared"},
                {"waveName": "Wave2", "protectionGroupId": "pg-unique"},
            ],
        },
    ]


@pytest.fixture
def sample_protection_groups():
    """Protection groups including shared and unique ones"""
    return {
        "pg-shared": {
            "groupId": "pg-shared",
            "groupName": "Shared Database Servers",
            "region": "us-east-1",
            "sourceServerIds": ["s-db-001", "s-db-002"],
        },
        "pg-unique": {
            "groupId": "pg-unique",
            "groupName": "Unique App Servers",
            "region": "us-east-1",
            "sourceServerIds": ["s-app-001"],
        },
    }


# ============================================================================
# Shared Protection Group Detection Tests
# ============================================================================


class TestSharedProtectionGroupDetection:
    """Tests for detecting PGs shared across multiple plans"""

    def test_detects_shared_protection_group(
        self, mock_dynamodb_tables, sample_plans_sharing_pg, sample_protection_groups
    ):
        """Should detect when a PG is used by multiple plans"""
        # Setup mocks
        mock_dynamodb_tables["recovery_plans"].scan.return_value = {
            "Items": sample_plans_sharing_pg
        }
        mock_dynamodb_tables["protection_groups"].get_item.side_effect = (
            lambda Key: {"Item": sample_protection_groups.get(Key["groupId"], {})}
        )

        # Execute
        shared_pgs = get_shared_protection_groups()

        # Verify
        assert "pg-shared" in shared_pgs
        assert shared_pgs["pg-shared"]["planCount"] == 2
        assert len(shared_pgs["pg-shared"]["usedByPlans"]) == 2

        # pg-unique should NOT be in shared list
        assert "pg-unique" not in shared_pgs

    def test_no_shared_pgs_when_all_unique(self, mock_dynamodb_tables):
        """Should return empty dict when no PGs are shared"""
        plans = [
            {
                "planId": "plan-1",
                "planName": "Plan 1",
                "waves": [{"waveName": "W1", "protectionGroupId": "pg-1"}],
            },
            {
                "planId": "plan-2",
                "planName": "Plan 2",
                "waves": [{"waveName": "W1", "protectionGroupId": "pg-2"}],
            },
        ]
        mock_dynamodb_tables["recovery_plans"].scan.return_value = {"Items": plans}

        shared_pgs = get_shared_protection_groups()

        assert shared_pgs == {}

    def test_same_pg_in_multiple_waves_same_plan_not_counted_twice(
        self, mock_dynamodb_tables, sample_protection_groups
    ):
        """Same PG in multiple waves of same plan should count as 1 usage"""
        plans = [
            {
                "planId": "plan-1",
                "planName": "Plan 1",
                "waves": [
                    {"waveName": "W1", "protectionGroupId": "pg-shared"},
                    {"waveName": "W2", "protectionGroupId": "pg-shared"},  # Same PG
                ],
            },
        ]
        mock_dynamodb_tables["recovery_plans"].scan.return_value = {"Items": plans}
        mock_dynamodb_tables["protection_groups"].get_item.return_value = {
            "Item": sample_protection_groups["pg-shared"]
        }

        shared_pgs = get_shared_protection_groups()

        # Only 1 plan uses it, so it's not "shared"
        assert "pg-shared" not in shared_pgs


class TestPlanSharedPGWarnings:
    """Tests for getting warnings for a specific plan"""

    def test_returns_warnings_for_plan_with_shared_pg(
        self, mock_dynamodb_tables, sample_plans_sharing_pg, sample_protection_groups
    ):
        """Should return warnings when plan uses shared PGs"""
        mock_dynamodb_tables["recovery_plans"].scan.return_value = {
            "Items": sample_plans_sharing_pg
        }
        mock_dynamodb_tables["protection_groups"].get_item.side_effect = (
            lambda Key: {"Item": sample_protection_groups.get(Key["groupId"], {})}
        )

        warnings = get_plan_shared_pg_warnings("plan-A")

        assert len(warnings) == 1
        assert warnings[0]["type"] == "SHARED_PROTECTION_GROUP"
        assert warnings[0]["protectionGroupId"] == "pg-shared"
        assert any(p["planId"] == "plan-B" for p in warnings[0]["sharedWithPlans"])

    def test_no_warnings_for_plan_with_unique_pgs(self, mock_dynamodb_tables):
        """Should return empty list when plan has no shared PGs"""
        plans = [
            {
                "planId": "plan-1",
                "planName": "Plan 1",
                "waves": [{"waveName": "W1", "protectionGroupId": "pg-1"}],
            },
            {
                "planId": "plan-2",
                "planName": "Plan 2",
                "waves": [{"waveName": "W1", "protectionGroupId": "pg-2"}],
            },
        ]
        mock_dynamodb_tables["recovery_plans"].scan.return_value = {"Items": plans}

        warnings = get_plan_shared_pg_warnings("plan-1")

        assert warnings == []


# ============================================================================
# Edge Cases: Conflict Detection
# ============================================================================


class TestConflictDetectionEdgeCases:
    """Edge cases for conflict detection"""

    def test_server_in_pending_drs_job_blocks_execution(self, mock_dynamodb_tables):
        """Server in PENDING DRS job should block new execution"""
        mock_drs_client = MagicMock()
        mock_drs_client.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "drsjob-pending",
                    "status": "PENDING",
                    "type": "LAUNCH",
                    "participatingServers": [
                        {"sourceServerID": "s-001", "launchStatus": "PENDING"}
                    ],
                }
            ]
        }

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client
        ):
            servers_in_jobs = get_servers_in_active_drs_jobs("us-east-1")

        assert "s-001" in servers_in_jobs
        assert servers_in_jobs["s-001"]["jobStatus"] == "PENDING"

    def test_server_in_started_drs_job_blocks_execution(self, mock_dynamodb_tables):
        """Server in STARTED DRS job should block new execution"""
        mock_drs_client = MagicMock()
        mock_drs_client.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "drsjob-started",
                    "status": "STARTED",
                    "type": "LAUNCH",
                    "participatingServers": [
                        {"sourceServerID": "s-002", "launchStatus": "IN_PROGRESS"}
                    ],
                }
            ]
        }

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client
        ):
            servers_in_jobs = get_servers_in_active_drs_jobs("us-east-1")

        assert "s-002" in servers_in_jobs
        assert servers_in_jobs["s-002"]["jobStatus"] == "STARTED"

    def test_server_in_completed_drs_job_does_not_block(self, mock_dynamodb_tables):
        """Server in COMPLETED DRS job should NOT block new execution"""
        mock_drs_client = MagicMock()
        mock_drs_client.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "drsjob-done",
                    "status": "COMPLETED",
                    "type": "LAUNCH",
                    "participatingServers": [
                        {"sourceServerID": "s-003", "launchStatus": "LAUNCHED"}
                    ],
                }
            ]
        }

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client
        ):
            servers_in_jobs = get_servers_in_active_drs_jobs("us-east-1")

        # COMPLETED jobs should not be in the active list
        assert "s-003" not in servers_in_jobs

    def test_execution_in_cancelling_state_still_blocks(self, mock_dynamodb_tables):
        """
        Execution in CANCELLING state STILL blocks new execution.
        CANCELLING means the execution is still active, just being cancelled.
        Servers are only released when status becomes CANCELLED (terminal).
        """
        mock_dynamodb_tables["execution_history"].scan.return_value = {
            "Items": [
                {
                    "executionId": "exec-cancelling",
                    "planId": "plan-1",
                    "status": "CANCELLING",
                    "waves": [
                        {
                            "waveName": "W1",
                            "serverStatuses": [
                                {"sourceServerId": "s-001", "launchStatus": "PENDING"},
                                {"sourceServerId": "s-002", "launchStatus": "PENDING"},
                            ],
                        }
                    ],
                }
            ]
        }

        servers = get_servers_in_active_executions()

        # CANCELLING is still active - servers are blocked until CANCELLED
        assert "s-001" in servers
        assert "s-002" in servers

    def test_execution_in_cancelled_state_does_not_block(self, mock_dynamodb_tables):
        """Execution in CANCELLED (terminal) state should NOT block new execution"""
        mock_dynamodb_tables["execution_history"].scan.return_value = {
            "Items": [
                {
                    "executionId": "exec-cancelled",
                    "planId": "plan-1",
                    "status": "CANCELLED",  # Terminal state
                    "waves": [
                        {
                            "waveName": "W1",
                            "serverStatuses": [
                                {"sourceServerId": "s-001", "launchStatus": "PENDING"},
                                {"sourceServerId": "s-002", "launchStatus": "PENDING"},
                            ],
                        }
                    ],
                }
            ]
        }

        servers = get_servers_in_active_executions()

        # CANCELLED is terminal - servers are released
        assert "s-001" not in servers
        assert "s-002" not in servers

    def test_execution_in_running_state_blocks(self, mock_dynamodb_tables):
        """Execution in RUNNING state should block new execution"""
        mock_dynamodb_tables["execution_history"].scan.return_value = {
            "Items": [
                {
                    "executionId": "exec-running",
                    "planId": "plan-1",
                    "status": "RUNNING",
                    "waves": [
                        {
                            "waveName": "W1",
                            "serverStatuses": [
                                {"sourceServerId": "s-001", "launchStatus": "IN_PROGRESS"},
                                {"sourceServerId": "s-002", "launchStatus": "IN_PROGRESS"},
                            ],
                        }
                    ],
                }
            ]
        }

        servers = get_servers_in_active_executions()

        assert "s-001" in servers
        assert "s-002" in servers
        assert servers["s-001"]["executionId"] == "exec-running"


class TestDRSLimitEdgeCases:
    """Edge cases for DRS limit enforcement"""

    def test_exactly_20_concurrent_jobs_blocks_new_job(self, mock_dynamodb_tables):
        """Exactly 20 concurrent jobs should block new job"""
        mock_drs_client = MagicMock()
        # Create 20 active jobs
        active_jobs = [
            {"jobID": f"drsjob-{i}", "status": "STARTED", "type": "LAUNCH"}
            for i in range(20)
        ]
        mock_drs_client.describe_jobs.return_value = {"items": active_jobs}

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client
        ):
            from conflict_detection import check_concurrent_jobs_limit

            result = check_concurrent_jobs_limit("us-east-1")

        assert result["canStartJob"] is False
        assert result["currentJobs"] == 20
        assert result["maxJobs"] == 20

    def test_19_concurrent_jobs_allows_new_job(self, mock_dynamodb_tables):
        """19 concurrent jobs should allow new job"""
        mock_drs_client = MagicMock()
        active_jobs = [
            {"jobID": f"drsjob-{i}", "status": "STARTED", "type": "LAUNCH"}
            for i in range(19)
        ]
        mock_drs_client.describe_jobs.return_value = {"items": active_jobs}

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client
        ):
            from conflict_detection import check_concurrent_jobs_limit

            result = check_concurrent_jobs_limit("us-east-1")

        assert result["canStartJob"] is True
        assert result["currentJobs"] == 19

    def test_exactly_100_servers_in_wave_is_valid(self, mock_dynamodb_tables):
        """Wave with exactly 100 servers should be valid"""
        from drs_limits import validate_wave_sizes

        plan = {
            "waves": [
                {
                    "waveName": "MaxWave",
                    "serverIds": [f"s-{i:03d}" for i in range(100)],
                }
            ]
        }

        errors = validate_wave_sizes(plan)

        assert errors == []

    def test_101_servers_in_wave_is_invalid(self, mock_dynamodb_tables):
        """Wave with 101 servers should be invalid"""
        from drs_limits import validate_wave_sizes

        plan = {
            "waves": [
                {
                    "waveName": "TooLargeWave",
                    "serverIds": [f"s-{i:03d}" for i in range(101)],
                }
            ]
        }

        errors = validate_wave_sizes(plan)

        assert len(errors) == 1
        assert errors[0]["type"] == "WAVE_SIZE_EXCEEDED"
        assert errors[0]["serverCount"] == 101
        assert errors[0]["limit"] == 100


class TestCriticalOneJobPerServerRule:
    """
    Tests for the MOST CRITICAL DRS rule: Only 1 concurrent job per server.

    This is the primary constraint that prevents data corruption during DR.
    DRS returns ConflictException (409) if violated.
    """

    def test_same_server_in_two_plans_blocks_second_execution(
        self, mock_dynamodb_tables
    ):
        """
        CRITICAL: If server s-001 is in Plan A (running), Plan B cannot start
        if it also contains s-001.
        """
        # Plan A is running with s-001
        mock_dynamodb_tables["execution_history"].scan.return_value = {
            "Items": [
                {
                    "executionId": "exec-A",
                    "planId": "plan-A",
                    "status": "RUNNING",
                    "waves": [
                        {
                            "waveName": "W1",
                            "serverStatuses": [
                                {"sourceServerId": "s-001", "launchStatus": "IN_PROGRESS"},
                                {"sourceServerId": "s-002", "launchStatus": "IN_PROGRESS"},
                            ],
                        }
                    ],
                }
            ]
        }

        # Plan B wants to start with s-001 (conflict!) - uses Protection Group
        plan_b = {
            "planId": "plan-B",
            "planName": "Plan B",
            "waves": [{"waveName": "W1", "protectionGroupId": "pg-b"}],
        }

        # Mock PG resolution to return s-001 and s-003
        mock_dynamodb_tables["protection_groups"].get_item.return_value = {
            "Item": {
                "groupId": "pg-b",
                "groupName": "PG B",
                "region": "us-east-1",
                "sourceServerIds": ["s-001", "s-003"],
            }
        }

        mock_drs_client = MagicMock()
        mock_drs_client.describe_jobs.return_value = {"items": []}

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client
        ):
            conflicts = check_server_conflicts(plan_b)

        # Should have conflict for s-001
        assert len(conflicts) > 0
        conflict_server_ids = [c["serverId"] for c in conflicts]
        assert "s-001" in conflict_server_ids

    def test_server_in_external_drs_job_blocks_orchestration(
        self, mock_dynamodb_tables
    ):
        """
        CRITICAL: If server is in DRS job started outside orchestration,
        we should still detect and block.
        """
        # No internal executions
        mock_dynamodb_tables["execution_history"].scan.return_value = {"Items": []}

        # But DRS has an active job for s-001 (started via console/CLI)
        mock_drs_client = MagicMock()
        mock_drs_client.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "drsjob-external",
                    "status": "STARTED",
                    "type": "LAUNCH",
                    "participatingServers": [
                        {"sourceServerID": "s-001", "launchStatus": "IN_PROGRESS"}
                    ],
                }
            ]
        }

        plan = {
            "planId": "plan-1",
            "planName": "Plan 1",
            "waves": [{"waveName": "W1", "protectionGroupId": "pg-1"}],
        }

        # Mock PG resolution
        mock_dynamodb_tables["protection_groups"].get_item.return_value = {
            "Item": {
                "groupId": "pg-1",
                "groupName": "PG 1",
                "region": "us-east-1",
                "sourceServerIds": ["s-001"],
            }
        }

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client
        ):
            conflicts = check_server_conflicts(plan)

        # Should detect DRS job conflict
        assert len(conflicts) > 0
        assert conflicts[0]["conflictSource"] == "drs_job"
        assert conflicts[0]["conflictingJobId"] == "drsjob-external"

    def test_sequential_executions_of_same_server_allowed(self, mock_dynamodb_tables):
        """
        After Plan A completes, Plan B can use the same servers.
        """
        # Plan A completed (not in active list)
        mock_dynamodb_tables["execution_history"].scan.return_value = {
            "Items": [
                {
                    "executionId": "exec-A",
                    "planId": "plan-A",
                    "status": "COMPLETED",  # Not active
                    "waves": [
                        {
                            "waveName": "W1",
                            "serverStatuses": [
                                {"sourceServerId": "s-001", "launchStatus": "LAUNCHED"},
                                {"sourceServerId": "s-002", "launchStatus": "LAUNCHED"},
                            ],
                        }
                    ],
                }
            ]
        }

        # No active DRS jobs
        mock_drs_client = MagicMock()
        mock_drs_client.describe_jobs.return_value = {"items": []}

        plan_b = {
            "planId": "plan-B",
            "planName": "Plan B",
            "waves": [{"waveName": "W1", "protectionGroupId": "pg-b"}],
        }

        mock_dynamodb_tables["protection_groups"].get_item.return_value = {
            "Item": {
                "groupId": "pg-b",
                "groupName": "PG B",
                "region": "us-east-1",
                "sourceServerIds": ["s-001", "s-002"],
            }
        }

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client
        ):
            conflicts = check_server_conflicts(plan_b)

        # No conflicts - sequential execution allowed
        assert conflicts == []


# ============================================================================
# Multi-Region Edge Cases
# ============================================================================


class TestMultiRegionConflicts:
    """Tests for multi-region conflict detection"""

    def test_same_server_different_regions_no_conflict(self, mock_dynamodb_tables):
        """
        Servers with same ID in different regions are different servers.
        (In practice, DRS server IDs are globally unique, but test the logic)
        """
        # This tests that we check the correct region
        mock_drs_client_east = MagicMock()
        mock_drs_client_east.describe_jobs.return_value = {
            "items": [
                {
                    "jobID": "drsjob-east",
                    "status": "STARTED",
                    "type": "LAUNCH",
                    "participatingServers": [
                        {"sourceServerID": "s-east-001", "launchStatus": "IN_PROGRESS"}
                    ],
                }
            ]
        }

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client_east
        ):
            servers_east = get_servers_in_active_drs_jobs("us-east-1")

        assert "s-east-001" in servers_east

        # West region has different servers
        mock_drs_client_west = MagicMock()
        mock_drs_client_west.describe_jobs.return_value = {"items": []}

        with patch(
            "conflict_detection.create_drs_client", return_value=mock_drs_client_west
        ):
            servers_west = get_servers_in_active_drs_jobs("us-west-2")

        assert "s-east-001" not in servers_west
