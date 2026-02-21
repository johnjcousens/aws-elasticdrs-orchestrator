"""
Comprehensive Conflict Detection and DRS Quota Validation Tests

Tests all conflict detection scenarios and DRS service quota validations:
1. Server-level conflicts (execution, DRS jobs)
2. DRS quota violations (20 concurrent jobs, 100 per job, 500 total)
3. Protection Group resolution (tags and explicit IDs)
4. Cross-account conflict detection

Validates: Requirements 4.1, 4.2, 4.3, 9.5
"""

import json  # noqa: F401
import sys  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest.mock import MagicMock, patch, call  # noqa: F401  # noqa: F401  # noqa: F401  # noqa: F401

import pytest  # noqa: F401

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "shared"
sys.path.insert(0, str(lambda_dir))

from conflict_detection import (  # noqa: E402
    check_concurrent_jobs_limit,
    check_server_conflicts,
    check_total_servers_in_jobs_limit,
    get_servers_in_active_drs_jobs,
    get_servers_in_active_executions,
    query_drs_servers_by_tags,
    resolve_pg_servers_for_conflict_check,
    validate_wave_server_count,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_drs_client():
    """Mock DRS client with configurable responses"""
    client = MagicMock()  # noqa: F841
    return client


@pytest.fixture(autouse=True)
def reset_global_clients():
    """Reset global cached clients before each test"""
    import conflict_detection

    conflict_detection._protection_groups_table = None
    conflict_detection._recovery_plans_table = None
    conflict_detection._execution_history_table = None
    yield
    # Clean up after test
    conflict_detection._protection_groups_table = None
    conflict_detection._recovery_plans_table = None
    conflict_detection._execution_history_table = None


@pytest.fixture
def mock_dynamodb_tables():
    """Mock DynamoDB tables"""
    pg_table = MagicMock()
    rp_table = MagicMock()
    eh_table = MagicMock()

    with (
        patch("conflict_detection.get_protection_groups_table", return_value=pg_table),
        patch("conflict_detection.get_recovery_plans_table", return_value=rp_table),
        patch("conflict_detection.get_execution_history_table", return_value=eh_table),
    ):
        yield {
            "protection_groups": pg_table,
            "recovery_plans": rp_table,
            "execution_history": eh_table,
        }


@pytest.fixture
def sample_recovery_plan():
    """Sample recovery plan with 2 waves"""
    return {
        "planId": "plan-123",
        "planName": "Test Plan",
        "waves": [
            {
                "waveName": "Wave1",
                "protectionGroupId": "pg-1",
                "waveNumber": 0,
            },
            {
                "waveName": "Wave2",
                "protectionGroupId": "pg-2",
                "waveNumber": 1,
            },
        ],
    }


@pytest.fixture
def sample_protection_group():
    """Sample protection group with explicit server IDs"""
    return {
        "groupId": "pg-1",
        "groupName": "Test PG",
        "region": "us-east-1",
        "sourceServerIds": ["s-001", "s-002", "s-003"],
    }


@pytest.fixture
def sample_tag_based_pg():
    """Sample protection group with tag-based selection"""
    return {
        "groupId": "pg-tags",
        "groupName": "Tag-Based PG",
        "region": "us-west-2",
        "serverSelectionTags": {"Environment": "Production", "App": "WebApp"},
    }


# ============================================================================
# Concurrent Jobs Limit Tests (20 max)
# ============================================================================


def test_concurrent_jobs_under_limit(mock_drs_client):
    """Test concurrent jobs check when under 20 job limit"""
    # Mock 15 active jobs
    mock_drs_client.describe_jobs.return_value = {
        "items": [{"jobID": f"job-{i}", "status": "STARTED", "type": "LAUNCH"} for i in range(15)]
    }

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = check_concurrent_jobs_limit("us-east-1")  # noqa: F841

    assert result["canStartJob"] is True
    assert result["currentJobs"] == 15
    assert result["maxJobs"] == 20
    assert result["availableSlots"] == 5


def test_concurrent_jobs_at_limit(mock_drs_client):
    """Test concurrent jobs check when at 20 job limit"""
    # Mock 20 active jobs
    mock_drs_client.describe_jobs.return_value = {
        "items": [{"jobID": f"job-{i}", "status": "PENDING", "type": "LAUNCH"} for i in range(20)]
    }

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = check_concurrent_jobs_limit("us-east-1")  # noqa: F841

    assert result["canStartJob"] is False
    assert result["currentJobs"] == 20
    assert result["maxJobs"] == 20
    assert result["availableSlots"] == 0


def test_concurrent_jobs_ignores_completed(mock_drs_client):
    """Test that completed/failed jobs don't count toward limit"""
    # Mock 25 total jobs, but only 10 active
    mock_drs_client.describe_jobs.return_value = {
        "items": [{"jobID": f"job-active-{i}", "status": "STARTED", "type": "LAUNCH"} for i in range(10)]
        + [
            {
                "jobID": f"job-done-{i}",
                "status": "COMPLETED",
                "type": "LAUNCH",
            }
            for i in range(15)
        ]
    }

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = check_concurrent_jobs_limit("us-east-1")  # noqa: F841

    assert result["canStartJob"] is True
    assert result["currentJobs"] == 10
    assert result["availableSlots"] == 10


# ============================================================================
# Servers Per Job Limit Tests (100 max)
# ============================================================================


def test_wave_under_100_servers(mock_dynamodb_tables):
    """Test wave validation with 50 servers (under limit)"""
    wave = {"waveName": "Wave1", "protectionGroupId": "pg-1"}

    # Mock PG with 50 servers
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": {
            "groupId": "pg-1",
            "region": "us-east-1",
            "sourceServerIds": [f"s-{i:03d}" for i in range(50)],
        }
    }

    pg_cache = {}
    result = validate_wave_server_count(wave, pg_cache)  # noqa: F841

    assert result["valid"] is True
    assert result["serverCount"] == 50
    assert result["maxServers"] == 100


def test_wave_at_100_servers(mock_dynamodb_tables):
    """Test wave validation with exactly 100 servers (at limit)"""
    wave = {"waveName": "Wave1", "protectionGroupId": "pg-1"}

    # Mock PG with 100 servers
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": {
            "groupId": "pg-1",
            "region": "us-east-1",
            "sourceServerIds": [f"s-{i:03d}" for i in range(100)],
        }
    }

    pg_cache = {}
    result = validate_wave_server_count(wave, pg_cache)  # noqa: F841

    assert result["valid"] is True
    assert result["serverCount"] == 100
    assert result["maxServers"] == 100


def test_wave_exceeds_100_servers(mock_dynamodb_tables):
    """Test wave validation with 150 servers (exceeds limit)"""
    wave = {"waveName": "Wave1", "protectionGroupId": "pg-1"}

    # Mock PG with 150 servers
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": {
            "groupId": "pg-1",
            "region": "us-east-1",
            "sourceServerIds": [f"s-{i:03d}" for i in range(150)],
        }
    }

    pg_cache = {}
    result = validate_wave_server_count(wave, pg_cache)  # noqa: F841

    assert result["valid"] is False
    assert result["serverCount"] == 150
    assert result["maxServers"] == 100
    assert "exceeds" in result["message"].lower()


def test_wave_with_tag_based_pg(mock_dynamodb_tables, mock_drs_client):
    """Test wave validation with tag-based Protection Group"""
    wave = {"waveName": "Wave1", "protectionGroupId": "pg-tags"}

    # Mock PG with tags
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": {
            "groupId": "pg-tags",
            "region": "us-west-2",
            "serverSelectionTags": {"Environment": "Production"},
        }
    }

    # Mock DRS API returning 75 servers matching tags
    mock_drs_client.get_paginator.return_value.paginate.return_value = [
        {
            "items": [
                {
                    "sourceServerID": f"s-{i:03d}",
                    "tags": {"Environment": "Production"},
                }
                for i in range(75)
            ]
        }
    ]

    pg_cache = {}
    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = validate_wave_server_count(wave, pg_cache)  # noqa: F841

    assert result["valid"] is True
    assert result["serverCount"] == 75


# ============================================================================
# Total Servers in Jobs Limit Tests (500 max)
# ============================================================================


def test_total_servers_under_500(mock_drs_client):
    """Test total servers check when under 500 limit"""
    # Mock 200 servers in active jobs
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": "job-1",
                "status": "STARTED",
                "type": "LAUNCH",
                "participatingServers": [{"sourceServerID": f"s-{i:03d}"} for i in range(100)],
            },
            {
                "jobID": "job-2",
                "status": "PENDING",
                "type": "LAUNCH",
                "participatingServers": [{"sourceServerID": f"s-{i:03d}"} for i in range(100, 200)],
            },
        ]
    }

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = check_total_servers_in_jobs_limit("us-east-1", 100)  # noqa: F841

    assert result["valid"] is True
    assert result["currentServers"] == 200
    assert result["newServers"] == 100
    assert result["totalAfter"] == 300
    assert result["maxServers"] == 500
    assert result["availableSlots"] == 300


def test_total_servers_would_exceed_500(mock_drs_client):
    """Test total servers check when adding would exceed 500"""
    # Mock 450 servers in active jobs
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": f"job-{j}",
                "status": "STARTED",
                "type": "LAUNCH",
                "participatingServers": [{"sourceServerID": f"s-{j}-{i:03d}"} for i in range(90)],
            }
            for j in range(5)
        ]
    }

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = check_total_servers_in_jobs_limit("us-east-1", 100)  # noqa: F841

    assert result["valid"] is False
    assert result["currentServers"] == 450
    assert result["newServers"] == 100
    assert result["totalAfter"] == 550
    assert result["maxServers"] == 500


def test_total_servers_at_500_limit(mock_drs_client):
    """Test total servers check when exactly at 500 limit"""
    # Mock 500 servers in active jobs
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": f"job-{j}",
                "status": "STARTED",
                "type": "LAUNCH",
                "participatingServers": [{"sourceServerID": f"s-{j}-{i:03d}"} for i in range(100)],
            }
            for j in range(5)
        ]
    }

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = check_total_servers_in_jobs_limit("us-east-1", 1)  # noqa: F841

    assert result["valid"] is False
    assert result["currentServers"] == 500
    assert result["availableSlots"] == 0


# ============================================================================
# Server Conflict Detection Tests
# ============================================================================


def test_no_conflicts_clean_state(mock_dynamodb_tables, mock_drs_client, sample_recovery_plan):
    """Test conflict check with no active executions or jobs"""
    # Mock no active executions
    mock_dynamodb_tables["execution_history"].query.return_value = {"Items": []}
    mock_dynamodb_tables["execution_history"].scan.return_value = {"Items": []}

    # Mock PGs
    mock_dynamodb_tables["protection_groups"].get_item.side_effect = [
        {
            "Item": {
                "groupId": "pg-1",
                "region": "us-east-1",
                "sourceServerIds": ["s-001", "s-002"],
            }
        },
        {
            "Item": {
                "groupId": "pg-2",
                "region": "us-east-1",
                "sourceServerIds": ["s-003", "s-004"],
            }
        },
    ]

    # Mock no active DRS jobs
    mock_drs_client.describe_jobs.return_value = {"items": []}

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        conflicts = check_server_conflicts(sample_recovery_plan)

    assert len(conflicts) == 0


def test_server_in_active_execution(mock_dynamodb_tables, mock_drs_client, sample_recovery_plan):
    """Test conflict detection when server is in another execution"""
    # Mock active execution with conflicting server
    mock_dynamodb_tables["execution_history"].query.return_value = {
        "Items": [
            {
                "executionId": "exec-999",
                "planId": "plan-other",
                "status": "IN_PROGRESS",
                "waves": [
                    {
                        "waveName": "OtherWave",
                        "serverStatuses": [
                            {
                                "sourceServerId": "s-001",
                                "launchStatus": "LAUNCHING",
                            }
                        ],
                    }
                ],
            }
        ]
    }

    # Mock PGs - need to handle multiple get_item calls
    def mock_pg_get_item(Key):
        pg_id = Key.get("groupId")
        if pg_id in ["pg-1", "pg-2"]:
            return {
                "Item": {
                    "groupId": pg_id,
                    "region": "us-east-1",
                    "sourceServerIds": ["s-001", "s-002"],
                }
            }
        return {"Item": {}}

    mock_dynamodb_tables["protection_groups"].get_item.side_effect = mock_pg_get_item

    # Mock no DRS jobs
    mock_drs_client.describe_jobs.return_value = {"items": []}

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        conflicts = check_server_conflicts(sample_recovery_plan)

    assert len(conflicts) > 0
    conflict = next(c for c in conflicts if c.get("serverId") == "s-001")
    assert conflict["conflictSource"] == "execution"
    assert conflict["conflictingExecutionId"] == "exec-999"


def test_server_in_active_drs_job(mock_dynamodb_tables, mock_drs_client, sample_recovery_plan):
    """Test conflict detection when server is in active DRS job"""
    # Mock no active executions
    mock_dynamodb_tables["execution_history"].query.return_value = {"Items": []}
    mock_dynamodb_tables["execution_history"].scan.return_value = {"Items": []}

    # Mock PGs - need to handle multiple get_item calls
    def mock_pg_get_item(Key):
        pg_id = Key.get("groupId")
        if pg_id in ["pg-1", "pg-2"]:
            return {
                "Item": {
                    "groupId": pg_id,
                    "region": "us-east-1",
                    "sourceServerIds": ["s-001", "s-002"],
                }
            }
        return {"Item": {}}

    mock_dynamodb_tables["protection_groups"].get_item.side_effect = mock_pg_get_item

    # Mock active DRS job with conflicting server
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": "job-external",
                "status": "STARTED",
                "type": "LAUNCH",
                "participatingServers": [{"sourceServerID": "s-001", "launchStatus": "LAUNCHING"}],
            }
        ]
    }

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        conflicts = check_server_conflicts(sample_recovery_plan)

    assert len(conflicts) > 0
    conflict = next(c for c in conflicts if c.get("serverId") == "s-001")
    assert conflict["conflictSource"] == "drs_job"
    assert conflict["conflictingJobId"] == "job-external"


# ============================================================================
# Quota Violation Tests (Integrated)
# ============================================================================


def test_quota_violation_concurrent_jobs(mock_dynamodb_tables, mock_drs_client, sample_recovery_plan):
    """Test conflict check detects concurrent jobs limit violation"""
    # Mock no active executions
    mock_dynamodb_tables["execution_history"].query.return_value = {"Items": []}
    mock_dynamodb_tables["execution_history"].scan.return_value = {"Items": []}

    # Mock PG
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": {
            "groupId": "pg-1",
            "region": "us-east-1",
            "sourceServerIds": ["s-001"],
        }
    }

    # Mock 20 active jobs (at limit)
    mock_drs_client.describe_jobs.return_value = {
        "items": [{"jobID": f"job-{i}", "status": "STARTED", "type": "LAUNCH"} for i in range(20)]
    }

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        conflicts = check_server_conflicts(sample_recovery_plan)

    # Should have quota violation
    quota_violations = [c for c in conflicts if c.get("conflictSource") == "quota_violation"]
    assert len(quota_violations) > 0

    concurrent_violation = next(
        (v for v in quota_violations if v.get("quotaType") == "concurrent_jobs"),
        None,
    )
    assert concurrent_violation is not None
    assert concurrent_violation["currentJobs"] == 20
    assert concurrent_violation["maxJobs"] == 20


def test_quota_violation_servers_per_job(mock_dynamodb_tables, mock_drs_client, sample_recovery_plan):
    """Test conflict check detects 100 servers per job limit violation"""
    # Mock no active executions
    mock_dynamodb_tables["execution_history"].query.return_value = {"Items": []}
    mock_dynamodb_tables["execution_history"].scan.return_value = {"Items": []}

    # Mock PG with 150 servers (exceeds 100 limit) - need to handle multiple calls
    def mock_pg_get_item(Key):
        pg_id = Key.get("groupId")
        if pg_id in ["pg-1", "pg-2"]:
            return {
                "Item": {
                    "groupId": pg_id,
                    "region": "us-east-1",
                    "sourceServerIds": [f"s-{i:03d}" for i in range(150)],
                }
            }
        return {"Item": {}}

    mock_dynamodb_tables["protection_groups"].get_item.side_effect = mock_pg_get_item

    # Mock no active jobs
    mock_drs_client.describe_jobs.return_value = {"items": []}

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        conflicts = check_server_conflicts(sample_recovery_plan)

    # Should have quota violation
    quota_violations = [c for c in conflicts if c.get("conflictSource") == "quota_violation"]
    assert len(quota_violations) > 0

    per_job_violation = next(
        (v for v in quota_violations if v.get("quotaType") == "servers_per_job"),
        None,
    )
    assert per_job_violation is not None
    assert per_job_violation["serverCount"] == 150
    assert per_job_violation["maxServers"] == 100


def test_quota_violation_total_servers_in_jobs(mock_dynamodb_tables, mock_drs_client, sample_recovery_plan):
    """Test conflict check detects 500 total servers limit violation"""
    # Mock no active executions
    mock_dynamodb_tables["execution_history"].query.return_value = {"Items": []}
    mock_dynamodb_tables["execution_history"].scan.return_value = {"Items": []}

    # Mock PG with 100 servers - need to handle multiple calls
    def mock_pg_get_item(Key):
        pg_id = Key.get("groupId")
        if pg_id in ["pg-1", "pg-2"]:
            return {
                "Item": {
                    "groupId": pg_id,
                    "region": "us-east-1",
                    "sourceServerIds": [f"s-{i:03d}" for i in range(100)],
                }
            }
        return {"Item": {}}

    mock_dynamodb_tables["protection_groups"].get_item.side_effect = mock_pg_get_item

    # Mock 450 servers already in active jobs
    mock_drs_client.describe_jobs.return_value = {
        "items": [
            {
                "jobID": f"job-{j}",
                "status": "STARTED",
                "type": "LAUNCH",
                "participatingServers": [{"sourceServerID": f"s-existing-{j}-{i:03d}"} for i in range(90)],
            }
            for j in range(5)
        ]
    }

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        conflicts = check_server_conflicts(sample_recovery_plan)

    # Should have quota violation (450 + 200 = 650 > 500)
    # Note: Recovery plan has 2 waves, each with 100 servers = 200 total
    quota_violations = [c for c in conflicts if c.get("conflictSource") == "quota_violation"]
    assert len(quota_violations) > 0

    total_violation = next(
        (v for v in quota_violations if v.get("quotaType") == "total_servers_in_jobs"),
        None,
    )
    assert total_violation is not None
    assert total_violation["currentServers"] == 450
    assert total_violation["totalAfter"] == 650  # 450 + 200 (2 waves × 100)
    assert total_violation["maxServers"] == 500


# ============================================================================
# Tag-Based Protection Group Tests
# ============================================================================


def test_query_drs_servers_by_tags_exact_match(mock_drs_client):
    """Test tag-based server query with exact tag matches"""
    # Mock DRS servers with various tags
    mock_drs_client.get_paginator.return_value.paginate.return_value = [
        {
            "items": [
                {
                    "sourceServerID": "s-001",
                    "tags": {"Environment": "Production", "App": "WebApp"},
                },
                {
                    "sourceServerID": "s-002",
                    "tags": {"Environment": "Production", "App": "Database"},
                },
                {
                    "sourceServerID": "s-003",
                    "tags": {"Environment": "Development", "App": "WebApp"},
                },
            ]
        }
    ]

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = query_drs_servers_by_tags("us-east-1", {"Environment": "Production", "App": "WebApp"})  # noqa: F841

    # Should only match s-001 (has both tags)
    assert len(result) == 1
    assert result[0]["sourceServerID"] == "s-001"


def test_query_drs_servers_by_tags_case_insensitive(mock_drs_client):
    """Test tag-based query is case-insensitive for values"""
    mock_drs_client.get_paginator.return_value.paginate.return_value = [
        {
            "items": [
                {
                    "sourceServerID": "s-001",
                    "tags": {"Environment": "PRODUCTION"},
                },
                {
                    "sourceServerID": "s-002",
                    "tags": {"Environment": "production"},
                },
            ]
        }
    ]

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = query_drs_servers_by_tags("us-east-1", {"Environment": "Production"})  # noqa: F841

    # Should match both (case-insensitive)
    assert len(result) == 2


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


def test_conflict_check_handles_drs_api_error(mock_dynamodb_tables, mock_drs_client, sample_recovery_plan):
    """Test conflict check handles DRS API errors gracefully"""
    # Mock no active executions
    mock_dynamodb_tables["execution_history"].query.return_value = {"Items": []}
    mock_dynamodb_tables["execution_history"].scan.return_value = {"Items": []}

    # Mock PG
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {
        "Item": {
            "groupId": "pg-1",
            "region": "us-east-1",
            "sourceServerIds": ["s-001"],
        }
    }

    # Mock DRS API error
    mock_drs_client.describe_jobs.side_effect = Exception("DRS API unavailable")

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        # Should not raise exception
        conflicts = check_server_conflicts(sample_recovery_plan)

    # Should return permissive result (no quota violations due to error)
    assert isinstance(conflicts, list)


def test_wave_validation_with_no_pg(mock_dynamodb_tables):
    """Test wave validation when Protection Group doesn't exist"""
    wave = {"waveName": "Wave1", "protectionGroupId": "pg-nonexistent"}

    # Mock PG not found
    mock_dynamodb_tables["protection_groups"].get_item.return_value = {}

    pg_cache = {}
    result = validate_wave_server_count(wave, pg_cache)  # noqa: F841

    # Should handle gracefully
    assert result["serverCount"] == 0


def test_concurrent_jobs_check_with_api_error(mock_drs_client):
    """Test concurrent jobs check handles API errors gracefully"""
    mock_drs_client.describe_jobs.side_effect = Exception("API Error")

    with patch("conflict_detection.create_drs_client", return_value=mock_drs_client):
        result = check_concurrent_jobs_limit("us-east-1")  # noqa: F841

    # Should return permissive result
    assert result["canStartJob"] is True
    assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
