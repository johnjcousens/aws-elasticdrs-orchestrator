"""
Unit tests for drs_limits shared utilities.

Tests DRS service limit validation logic.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add lambda directory to path for imports
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "lambda"),
)

from shared.drs_limits import (
    DRS_LIMITS,
    validate_concurrent_jobs,
    validate_servers_in_all_jobs,
    validate_wave_sizes,
)


@pytest.fixture
def sample_recovery_plan():
    """Sample Recovery Plan with waves"""
    return {
        "planId": "plan-123",
        "planName": "Test Plan",
        "waves": [
            {
                "waveName": "Wave 1",
                "protectionGroupId": "pg-123",
            },
            {
                "waveName": "Wave 2",
                "protectionGroupId": "pg-456",
            },
        ],
    }


@patch("shared.drs_limits.resolve_pg_servers_for_conflict_check")
def test_validate_wave_sizes_within_limit(mock_resolve, sample_recovery_plan):
    """Test validate_wave_sizes with waves within limit"""
    # Mock resolve to return 50 servers per wave (within 100 limit)
    mock_resolve.side_effect = [
        [f"s-{i}" for i in range(50)],  # Wave 1: 50 servers
        [f"s-{i}" for i in range(50, 80)],  # Wave 2: 30 servers
    ]

    errors = validate_wave_sizes(sample_recovery_plan)

    assert errors == []
    assert mock_resolve.call_count == 2


@patch("shared.drs_limits.resolve_pg_servers_for_conflict_check")
def test_validate_wave_sizes_exceeds_limit(mock_resolve, sample_recovery_plan):
    """Test validate_wave_sizes with wave exceeding limit"""
    # Mock resolve to return 150 servers for first wave (exceeds 100 limit)
    mock_resolve.side_effect = [
        [f"s-{i}" for i in range(150)],  # Wave 1: 150 servers (exceeds limit)
        [f"s-{i}" for i in range(50)],  # Wave 2: 50 servers
    ]

    errors = validate_wave_sizes(sample_recovery_plan)

    assert len(errors) == 1
    assert errors[0]["type"] == "WAVE_SIZE_EXCEEDED"
    assert errors[0]["wave"] == "Wave 1"
    assert errors[0]["serverCount"] == 150
    assert errors[0]["limit"] == DRS_LIMITS["MAX_SERVERS_PER_JOB"]


@patch("shared.drs_limits.resolve_pg_servers_for_conflict_check")
def test_validate_wave_sizes_multiple_waves_exceed(mock_resolve, sample_recovery_plan):
    """Test validate_wave_sizes with multiple waves exceeding limit"""
    # Mock resolve to return >100 servers for both waves
    mock_resolve.side_effect = [
        [f"s-{i}" for i in range(120)],  # Wave 1: 120 servers
        [f"s-{i}" for i in range(110)],  # Wave 2: 110 servers
    ]

    errors = validate_wave_sizes(sample_recovery_plan)

    assert len(errors) == 2
    assert errors[0]["wave"] == "Wave 1"
    assert errors[0]["serverCount"] == 120
    assert errors[1]["wave"] == "Wave 2"
    assert errors[1]["serverCount"] == 110


def test_validate_wave_sizes_with_direct_server_ids():
    """Test validate_wave_sizes with direct serverIds (backward compatibility)"""
    plan = {
        "planId": "plan-123",
        "waves": [
            {
                "waveName": "Wave 1",
                "serverIds": [f"s-{i}" for i in range(50)],
            }
        ],
    }

    errors = validate_wave_sizes(plan)

    assert errors == []


def test_validate_wave_sizes_with_direct_server_ids_exceeds():
    """Test validate_wave_sizes with direct serverIds exceeding limit"""
    plan = {
        "planId": "plan-123",
        "waves": [
            {
                "waveName": "Wave 1",
                "serverIds": [f"s-{i}" for i in range(150)],
            }
        ],
    }

    errors = validate_wave_sizes(plan)

    assert len(errors) == 1
    assert errors[0]["serverCount"] == 150


@patch("boto3.client")
def test_validate_concurrent_jobs_within_limit(mock_boto_client):
    """Test validate_concurrent_jobs with jobs within limit"""
    mock_drs = MagicMock()
    mock_boto_client.return_value = mock_drs

    # Mock paginator to return 5 active jobs
    mock_paginator = MagicMock()
    mock_drs.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {
            "items": [
                {
                    "jobID": f"job-{i}",
                    "status": "STARTED",
                    "type": "LAUNCH",
                    "participatingServers": [{"sourceServerID": f"s-{i}"}],
                }
                for i in range(5)
            ]
        }
    ]

    result = validate_concurrent_jobs("us-east-1")

    assert result["valid"] is True
    assert result["currentJobs"] == 5
    assert result["maxJobs"] == DRS_LIMITS["MAX_CONCURRENT_JOBS"]
    assert result["availableSlots"] == 15


@patch("boto3.client")
def test_validate_concurrent_jobs_at_limit(mock_boto_client):
    """Test validate_concurrent_jobs at limit"""
    mock_drs = MagicMock()
    mock_boto_client.return_value = mock_drs

    # Mock paginator to return 20 active jobs (at limit)
    mock_paginator = MagicMock()
    mock_drs.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {
            "items": [
                {
                    "jobID": f"job-{i}",
                    "status": "STARTED",
                    "type": "LAUNCH",
                    "participatingServers": [{"sourceServerID": f"s-{i}"}],
                }
                for i in range(20)
            ]
        }
    ]

    result = validate_concurrent_jobs("us-east-1")

    assert result["valid"] is False
    assert result["currentJobs"] == 20
    assert result["availableSlots"] == 0


@patch("boto3.client")
def test_validate_concurrent_jobs_uninitialized_region(mock_boto_client):
    """Test validate_concurrent_jobs with uninitialized region"""
    mock_drs = MagicMock()
    mock_boto_client.return_value = mock_drs

    # Mock paginator to raise UninitializedAccountException
    mock_paginator = MagicMock()
    mock_drs.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.side_effect = Exception("UninitializedAccountException")

    result = validate_concurrent_jobs("us-east-1")

    assert result["valid"] is True
    assert result["currentJobs"] == 0
    assert result.get("notInitialized") is True


@patch("boto3.client")
def test_validate_servers_in_all_jobs_within_limit(mock_boto_client):
    """Test validate_servers_in_all_jobs within limit"""
    mock_drs = MagicMock()
    mock_boto_client.return_value = mock_drs

    # Mock paginator to return jobs with 200 servers total
    mock_paginator = MagicMock()
    mock_drs.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {
            "items": [
                {
                    "jobID": "job-1",
                    "status": "STARTED",
                    "participatingServers": [{"sourceServerID": f"s-{i}"} for i in range(100)],
                },
                {
                    "jobID": "job-2",
                    "status": "STARTED",
                    "participatingServers": [{"sourceServerID": f"s-{i}"} for i in range(100, 200)],
                },
            ]
        }
    ]

    result = validate_servers_in_all_jobs("us-east-1", 50)

    assert result["valid"] is True
    assert result["currentServersInJobs"] == 200
    assert result["newServerCount"] == 50
    assert result["totalAfterNew"] == 250
    assert result["maxServers"] == DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"]


@patch("boto3.client")
def test_validate_servers_in_all_jobs_exceeds_limit(mock_boto_client):
    """Test validate_servers_in_all_jobs exceeding limit"""
    mock_drs = MagicMock()
    mock_boto_client.return_value = mock_drs

    # Mock paginator to return jobs with 480 servers total
    mock_paginator = MagicMock()
    mock_drs.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = [
        {
            "items": [
                {
                    "jobID": "job-1",
                    "status": "STARTED",
                    "participatingServers": [{"sourceServerID": f"s-{i}"} for i in range(480)],
                }
            ]
        }
    ]

    result = validate_servers_in_all_jobs("us-east-1", 50)

    assert result["valid"] is False
    assert result["currentServersInJobs"] == 480
    assert result["totalAfterNew"] == 530  # Exceeds 500 limit


@patch("boto3.client")
def test_validate_servers_in_all_jobs_uninitialized_region(mock_boto_client):
    """Test validate_servers_in_all_jobs with uninitialized region"""
    mock_drs = MagicMock()
    mock_boto_client.return_value = mock_drs

    # Mock paginator to raise UninitializedAccountException
    mock_paginator = MagicMock()
    mock_drs.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.side_effect = Exception("UninitializedAccountException")

    result = validate_servers_in_all_jobs("us-east-1", 50)

    assert result["valid"] is True
    assert result["currentServersInJobs"] == 0
    assert result.get("notInitialized") is True
