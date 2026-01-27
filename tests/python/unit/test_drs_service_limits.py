"""
Unit tests for DRS Service Limits Validation Functions

Tests the backend validation logic for AWS DRS service quotas without
requiring actual DRS infrastructure. Uses mocked boto3 clients.

AWS DRS Service Limits (as of 2025):
- MAX_SERVERS_PER_JOB: 100 (hard limit, cannot be increased)
- MAX_CONCURRENT_JOBS: 20 (hard limit)
- MAX_SERVERS_IN_ALL_JOBS: 500 (hard limit)
- MAX_REPLICATING_SERVERS: 300 (hard limit, cannot be increased)
- MAX_SOURCE_SERVERS: 4000 (soft limit, can request increase)
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Set AWS region BEFORE any boto3 imports
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Add lambda/api-handler directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lambda", "api-handler"))
# Add lambda directory to path so 'shared' module can be found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lambda"))

# Mock environment variables before importing
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-execution-history"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["STATE_MACHINE_ARN"] = "arn:aws:states:us-east-1:123456789:stateMachine:test"
os.environ["AWS_LAMBDA_FUNCTION_NAME"] = "test-query-handler"
os.environ["AWS_ACCOUNT_ID"] = "123456789012"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["PROJECT_NAME"] = "test-drs-orchestration"
os.environ["ENVIRONMENT"] = "test"

# Import DRS limits and validation functions from shared module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lambda"))
from shared.drs_limits import (
    DRS_LIMITS,
    validate_wave_sizes,
    validate_concurrent_jobs,
    validate_servers_in_all_jobs,
    validate_server_replication_states,
)


class TestDRSLimitsConstants:
    """Test DRS_LIMITS constants match AWS documented limits."""

    def test_max_servers_per_job(self):
        """MAX_SERVERS_PER_JOB should be 100."""
        assert DRS_LIMITS["MAX_SERVERS_PER_JOB"] == 100

    def test_max_concurrent_jobs(self):
        """MAX_CONCURRENT_JOBS should be 20."""
        assert DRS_LIMITS["MAX_CONCURRENT_JOBS"] == 20

    def test_max_servers_in_all_jobs(self):
        """MAX_SERVERS_IN_ALL_JOBS should be 500."""
        assert DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"] == 500

    def test_max_replicating_servers(self):
        """MAX_REPLICATING_SERVERS should be 300."""
        assert DRS_LIMITS["MAX_REPLICATING_SERVERS"] == 300

    def test_max_source_servers(self):
        """MAX_SOURCE_SERVERS should be 4000."""
        assert DRS_LIMITS["MAX_SOURCE_SERVERS"] == 4000

    def test_warning_threshold_less_than_max(self):
        """WARNING_REPLICATING_THRESHOLD should be less than MAX_REPLICATING_SERVERS."""
        assert (
            DRS_LIMITS["WARNING_REPLICATING_THRESHOLD"]
            < DRS_LIMITS["MAX_REPLICATING_SERVERS"]
        )

    def test_critical_threshold_between_warning_and_max(self):
        """CRITICAL_REPLICATING_THRESHOLD should be between WARNING and MAX."""
        assert (
            DRS_LIMITS["CRITICAL_REPLICATING_THRESHOLD"]
            > DRS_LIMITS["WARNING_REPLICATING_THRESHOLD"]
        )
        assert (
            DRS_LIMITS["CRITICAL_REPLICATING_THRESHOLD"]
            < DRS_LIMITS["MAX_REPLICATING_SERVERS"]
        )


class TestValidateWaveSizes:
    """Test validate_wave_sizes function."""

    def test_valid_wave_single_server(self):
        """Wave with 1 server should be valid."""
        plan = {"waves": [{"waveName": "Wave 1", "serverIds": ["s-123"]}]}
        errors = validate_wave_sizes(plan)
        assert len(errors) == 0

    def test_valid_wave_at_limit(self):
        """Wave with exactly 100 servers should be valid."""
        plan = {
            "waves": [
                {"waveName": "Wave 1", "serverIds": [f"s-{i}" for i in range(100)]}
            ]
        }
        errors = validate_wave_sizes(plan)
        assert len(errors) == 0

    def test_invalid_wave_over_limit(self):
        """Wave with 101 servers should return error."""
        plan = {
            "waves": [
                {"waveName": "Wave 1", "serverIds": [f"s-{i}" for i in range(101)]}
            ]
        }
        errors = validate_wave_sizes(plan)
        assert len(errors) == 1
        assert errors[0]["type"] == "WAVE_SIZE_EXCEEDED"
        assert errors[0]["serverCount"] == 101
        assert errors[0]["limit"] == 100

    def test_invalid_wave_way_over_limit(self):
        """Wave with 200 servers should return error with correct count."""
        plan = {
            "waves": [
                {"waveName": "Big Wave", "serverIds": [f"s-{i}" for i in range(200)]}
            ]
        }
        errors = validate_wave_sizes(plan)
        assert len(errors) == 1
        assert errors[0]["serverCount"] == 200
        assert "Big Wave" in errors[0]["message"]

    def test_multiple_waves_one_invalid(self):
        """Multiple waves with one exceeding limit should return one error."""
        plan = {
            "waves": [
                {"waveName": "Wave 1", "serverIds": [f"s-{i}" for i in range(50)]},
                {"waveName": "Wave 2", "serverIds": [f"s-{i}" for i in range(150)]},
                {"waveName": "Wave 3", "serverIds": [f"s-{i}" for i in range(30)]},
            ]
        }
        errors = validate_wave_sizes(plan)
        assert len(errors) == 1
        assert errors[0]["wave"] == "Wave 2"
        assert errors[0]["waveIndex"] == 2

    def test_multiple_waves_all_invalid(self):
        """Multiple waves all exceeding limit should return multiple errors."""
        plan = {
            "waves": [
                {"waveName": "Wave 1", "serverIds": [f"s-{i}" for i in range(101)]},
                {"waveName": "Wave 2", "serverIds": [f"s-{i}" for i in range(150)]},
            ]
        }
        errors = validate_wave_sizes(plan)
        assert len(errors) == 2

    def test_empty_wave(self):
        """Wave with no servers should be valid."""
        plan = {"waves": [{"waveName": "Empty Wave", "serverIds": []}]}
        errors = validate_wave_sizes(plan)
        assert len(errors) == 0

    def test_no_waves(self):
        """Plan with no waves should be valid."""
        plan = {"waves": []}
        errors = validate_wave_sizes(plan)
        assert len(errors) == 0

    def test_missing_waves_key(self):
        """Plan without waves key should be valid (empty)."""
        plan = {}
        errors = validate_wave_sizes(plan)
        assert len(errors) == 0


class TestValidateConcurrentJobs:
    """Test validate_concurrent_jobs function with mocked DRS client."""

    @patch("shared.drs_limits.boto3.client")
    def test_no_active_jobs(self, mock_boto_client):
        """Should be valid when no active jobs exist."""
        mock_drs = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"items": []}]
        mock_drs.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_drs

        result = validate_concurrent_jobs("us-east-1")

        assert result["valid"] is True
        assert result["currentJobs"] == 0
        assert result["availableSlots"] == 20

    @patch("shared.drs_limits.boto3.client")
    def test_some_active_jobs(self, mock_boto_client):
        """Should be valid when under limit."""
        mock_drs = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "jobID": "job-1",
                        "status": "PENDING",
                        "type": "LAUNCH",
                        "participatingServers": [],
                    },
                    {
                        "jobID": "job-2",
                        "status": "STARTED",
                        "type": "DRILL",
                        "participatingServers": [],
                    },
                    {
                        "jobID": "job-3",
                        "status": "COMPLETED",
                        "type": "LAUNCH",
                        "participatingServers": [],
                    },  # Not active
                ]
            }
        ]
        mock_drs.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_drs

        result = validate_concurrent_jobs("us-east-1")

        assert result["valid"] is True
        assert result["currentJobs"] == 2  # Only PENDING and STARTED
        assert result["availableSlots"] == 18

    @patch("shared.drs_limits.boto3.client")
    def test_at_limit(self, mock_boto_client):
        """Should be invalid when at limit."""
        mock_drs = MagicMock()
        mock_paginator = MagicMock()
        # Create 20 active jobs
        active_jobs = [
            {
                "jobID": f"job-{i}",
                "status": "STARTED",
                "type": "LAUNCH",
                "participatingServers": [],
            }
            for i in range(20)
        ]
        mock_paginator.paginate.return_value = [{"items": active_jobs}]
        mock_drs.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_drs

        result = validate_concurrent_jobs("us-east-1")

        assert result["valid"] is False
        assert result["currentJobs"] == 20
        assert result["availableSlots"] == 0

    @patch("shared.drs_limits.boto3.client")
    def test_api_error_returns_valid_with_warning(self, mock_boto_client):
        """Should return valid=True with warning on API error."""
        mock_drs = MagicMock()
        mock_drs.get_paginator.side_effect = Exception("API Error")
        mock_boto_client.return_value = mock_drs

        result = validate_concurrent_jobs("us-east-1")

        assert result["valid"] is True
        assert "warning" in result
        assert result["currentJobs"] is None


class TestValidateServersInAllJobs:
    """Test validate_servers_in_all_jobs function with mocked DRS client."""

    @patch("shared.drs_limits.boto3.client")
    def test_no_servers_in_jobs(self, mock_boto_client):
        """Should be valid when no servers in active jobs."""
        mock_drs = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"items": []}]
        mock_drs.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_drs

        result = validate_servers_in_all_jobs("us-east-1", 50)

        assert result["valid"] is True
        assert result["currentServersInJobs"] == 0
        assert result["totalAfterNew"] == 50

    @patch("shared.drs_limits.boto3.client")
    def test_would_exceed_limit(self, mock_boto_client):
        """Should be invalid when adding servers would exceed 500 limit."""
        mock_drs = MagicMock()
        mock_paginator = MagicMock()
        # 450 servers already in jobs
        mock_paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "jobID": "job-1",
                        "status": "STARTED",
                        "participatingServers": [
                            {"sourceServerID": f"s-{i}"} for i in range(450)
                        ],
                    }
                ]
            }
        ]
        mock_drs.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_drs

        result = validate_servers_in_all_jobs("us-east-1", 100)  # Would be 550 total

        assert result["valid"] is False
        assert result["currentServersInJobs"] == 450
        assert result["totalAfterNew"] == 550
        assert result["maxServers"] == 500

    @patch("shared.drs_limits.boto3.client")
    def test_exactly_at_limit(self, mock_boto_client):
        """Should be valid when exactly at 500 limit."""
        mock_drs = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "items": [
                    {
                        "jobID": "job-1",
                        "status": "STARTED",
                        "participatingServers": [
                            {"sourceServerID": f"s-{i}"} for i in range(400)
                        ],
                    }
                ]
            }
        ]
        mock_drs.get_paginator.return_value = mock_paginator
        mock_boto_client.return_value = mock_drs

        result = validate_servers_in_all_jobs("us-east-1", 100)  # Exactly 500

        assert result["valid"] is True
        assert result["totalAfterNew"] == 500


class TestValidateServerReplicationStates:
    """Test validate_server_replication_states function with mocked DRS client."""

    @patch("shared.drs_limits.boto3.client")
    def test_all_healthy_servers(self, mock_boto_client):
        """Should be valid when all servers have healthy replication."""
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.return_value = {
            "items": [
                {
                    "sourceServerID": "s-1",
                    "dataReplicationInfo": {
                        "dataReplicationState": "CONTINUOUS_REPLICATION"
                    },
                    "lifeCycle": {"state": "READY_FOR_TEST"},
                    "sourceProperties": {
                        "identificationHints": {"hostname": "server1"}
                    },
                },
                {
                    "sourceServerID": "s-2",
                    "dataReplicationInfo": {
                        "dataReplicationState": "CONTINUOUS_REPLICATION"
                    },
                    "lifeCycle": {"state": "READY_FOR_TEST"},
                    "sourceProperties": {
                        "identificationHints": {"hostname": "server2"}
                    },
                },
            ]
        }
        mock_boto_client.return_value = mock_drs

        result = validate_server_replication_states("us-east-1", ["s-1", "s-2"])

        assert result["valid"] is True
        assert result["healthyCount"] == 2
        assert result["unhealthyCount"] == 0

    @patch("shared.drs_limits.boto3.client")
    def test_disconnected_server(self, mock_boto_client):
        """Should be invalid when server is disconnected."""
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.return_value = {
            "items": [
                {
                    "sourceServerID": "s-1",
                    "dataReplicationInfo": {"dataReplicationState": "DISCONNECTED"},
                    "lifeCycle": {"state": "DISCONNECTED"},
                    "sourceProperties": {
                        "identificationHints": {"hostname": "server1"}
                    },
                }
            ]
        }
        mock_boto_client.return_value = mock_drs

        result = validate_server_replication_states("us-east-1", ["s-1"])

        assert result["valid"] is False
        assert result["unhealthyCount"] == 1
        assert result["unhealthyServers"][0]["serverId"] == "s-1"
        assert result["unhealthyServers"][0]["replicationState"] == "DISCONNECTED"

    @patch("shared.drs_limits.boto3.client")
    def test_empty_server_list(self, mock_boto_client):
        """Should be valid for empty server list."""
        result = validate_server_replication_states("us-east-1", [])

        assert result["valid"] is True
        assert result["healthyCount"] == 0
        assert result["unhealthyCount"] == 0

    @patch("shared.drs_limits.boto3.client")
    def test_mixed_healthy_unhealthy(self, mock_boto_client):
        """Should be invalid when some servers are unhealthy."""
        mock_drs = MagicMock()
        mock_drs.describe_source_servers.return_value = {
            "items": [
                {
                    "sourceServerID": "s-1",
                    "dataReplicationInfo": {
                        "dataReplicationState": "CONTINUOUS_REPLICATION"
                    },
                    "lifeCycle": {"state": "READY_FOR_TEST"},
                    "sourceProperties": {
                        "identificationHints": {"hostname": "healthy-server"}
                    },
                },
                {
                    "sourceServerID": "s-2",
                    "dataReplicationInfo": {"dataReplicationState": "STALLED"},
                    "lifeCycle": {"state": "READY_FOR_TEST"},
                    "sourceProperties": {
                        "identificationHints": {"hostname": "stalled-server"}
                    },
                },
            ]
        }
        mock_boto_client.return_value = mock_drs

        result = validate_server_replication_states("us-east-1", ["s-1", "s-2"])

        assert result["valid"] is False
        assert result["healthyCount"] == 1
        assert result["unhealthyCount"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
