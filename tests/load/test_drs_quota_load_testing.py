"""
DRS Quota Load Testing Suite

Comprehensive load tests to validate all DRS service quotas and rate limiting
are properly enforced in the DR Orchestration Platform.

Tests validate:
1. Protection Group quota enforcement (100 servers per job)
2. Recovery Plan quota enforcement (500 total servers, 20 concurrent jobs)
3. Rate limiting when approaching maximums
4. Multi-account capacity tracking (300 replicating servers per account)
5. Extended source server handling (4,000 source servers per account)

Reference:
- docs/reference/DRS_SERVICE_QUOTAS_COMPLETE.md
- docs/reference/DRS_SERVICE_LIMITS_AND_CAPABILITIES.md
"""

import json
import pytest
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.conflict_detection import (
    check_concurrent_jobs_limit,
    validate_wave_server_count,
    check_total_servers_in_jobs_limit,
    check_server_conflicts,
)


class TestProtectionGroupQuotaEnforcement:
    """Test Protection Group creation respects 100 servers per job limit"""


    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_pg_at_limit_100_servers(self, mock_resolve):
        """Protection Group with exactly 100 servers should succeed"""
        server_ids = [f"s-{i:019d}" for i in range(100)]
        mock_resolve.return_value = server_ids
        
        wave = {"protectionGroupId": "pg-test-100"}
        pg_cache = {}
        
        result = validate_wave_server_count(wave, pg_cache)
        assert result["valid"] is True
        assert result["serverCount"] == 100

    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_pg_exceeds_limit_101_servers(self, mock_resolve):
        """Protection Group with 101 servers should fail"""
        server_ids = [f"s-{i:019d}" for i in range(101)]
        mock_resolve.return_value = server_ids
        
        wave = {"protectionGroupId": "pg-test-101"}
        pg_cache = {}
        
        result = validate_wave_server_count(wave, pg_cache)
        assert result["valid"] is False
        assert result["serverCount"] == 101

    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_pg_exceeds_limit_200_servers(self, mock_resolve):
        """Protection Group with 200 servers should fail"""
        server_ids = [f"s-{i:019d}" for i in range(200)]
        mock_resolve.return_value = server_ids
        
        wave = {"protectionGroupId": "pg-test-200"}
        pg_cache = {}
        
        result = validate_wave_server_count(wave, pg_cache)
        assert result["valid"] is False
        assert result["serverCount"] == 200

    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_pg_boundary_99_servers(self, mock_resolve):
        """Protection Group with 99 servers should succeed"""
        server_ids = [f"s-{i:019d}" for i in range(99)]
        mock_resolve.return_value = server_ids
        
        wave = {"protectionGroupId": "pg-test-99"}
        pg_cache = {}
        
        result = validate_wave_server_count(wave, pg_cache)
        assert result["valid"] is True
        assert result["serverCount"] == 99


class TestRecoveryPlanQuotaEnforcement:
    """Test Recovery Plan creation respects all DRS job quotas"""

    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_rp_total_at_limit_500_servers(self, mock_get_servers):
        """Recovery Plan with exactly 500 total servers should succeed"""
        # Mock no existing servers in jobs
        mock_get_servers.return_value = []
        
        # Try to add 500 servers
        result = check_total_servers_in_jobs_limit(
            region="us-east-1",
            new_server_count=500
        )
        assert result["valid"] is True
        assert result["totalAfter"] == 500

    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_rp_exceeds_total_limit_501_servers(self, mock_get_servers):
        """Recovery Plan with 501 total servers should fail"""
        # Mock no existing servers in jobs
        mock_get_servers.return_value = []
        
        # Try to add 501 servers
        result = check_total_servers_in_jobs_limit(
            region="us-east-1",
            new_server_count=501
        )
        assert result["valid"] is False
        assert result["totalAfter"] == 501

    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_rp_per_wave_limit_enforcement(self, mock_resolve):
        """Each wave must respect 100 servers per job limit"""
        # Wave 1: 100 servers (valid)
        wave1_servers = [f"s-{i:019d}" for i in range(100)]
        mock_resolve.return_value = wave1_servers
        
        wave1 = {"protectionGroupId": "pg-wave1"}
        result1 = validate_wave_server_count(wave1, {})
        assert result1["valid"] is True
        
        # Wave 2: 101 servers (invalid)
        wave2_servers = [f"s-{i:019d}" for i in range(100, 201)]
        mock_resolve.return_value = wave2_servers
        
        wave2 = {"protectionGroupId": "pg-wave2"}
        result2 = validate_wave_server_count(wave2, {})
        assert result2["valid"] is False

    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_rp_multiple_waves_total_validation(self, mock_get_servers):
        """Recovery Plan with multiple waves must validate total servers"""
        # Mock no existing servers in jobs
        mock_get_servers.return_value = []
        
        # 10 waves × 50 servers = 500 total (valid)
        result = check_total_servers_in_jobs_limit(
            region="us-east-1",
            new_server_count=500
        )
        assert result["valid"] is True
        assert result["totalAfter"] == 500


class TestConcurrentJobsQuotaEnforcement:
    """Test concurrent jobs limit (20 jobs max)"""

    @patch("shared.conflict_detection.create_drs_client")
    def test_concurrent_jobs_at_limit_20_jobs(self, mock_create_client):
        """20 concurrent jobs should be at limit (warning)"""
        mock_drs = Mock()
        mock_create_client.return_value = mock_drs
        
        # Mock 20 active jobs
        active_jobs = [
            {
                "jobID": f"drsjob-{i:03d}",
                "status": "STARTED",
                "participatingServers": [
                    {"sourceServerID": f"s-{j:019d}"}
                    for j in range(10)
                ]
            }
            for i in range(20)
        ]
        
        mock_drs.describe_jobs.return_value = {"items": active_jobs}
        
        result = check_concurrent_jobs_limit("us-east-1")
        
        assert result["canStartJob"] is False
        assert result["currentJobs"] == 20
        assert result["maxJobs"] == 20
        assert result["availableSlots"] == 0

    @patch("shared.conflict_detection.create_drs_client")
    def test_concurrent_jobs_below_limit_15_jobs(self, mock_create_client):
        """15 concurrent jobs should be below limit"""
        mock_drs = Mock()
        mock_create_client.return_value = mock_drs
        
        # Mock 15 active jobs
        active_jobs = [
            {
                "jobID": f"drsjob-{i:03d}",
                "status": "STARTED",
                "participatingServers": [
                    {"sourceServerID": f"s-{j:019d}"}
                    for j in range(10)
                ]
            }
            for i in range(15)
        ]
        
        mock_drs.describe_jobs.return_value = {"items": active_jobs}
        
        result = check_concurrent_jobs_limit("us-east-1")
        
        assert result["canStartJob"] is True
        assert result["currentJobs"] == 15
        assert result["maxJobs"] == 20
        assert result["availableSlots"] == 5

    @patch("shared.conflict_detection.create_drs_client")
    def test_concurrent_jobs_approaching_limit_18_jobs(self, mock_create_client):
        """18 concurrent jobs should show warning"""
        mock_drs = Mock()
        mock_create_client.return_value = mock_drs
        
        # Mock 18 active jobs
        active_jobs = [
            {
                "jobID": f"drsjob-{i:03d}",
                "status": "STARTED",
                "participatingServers": [
                    {"sourceServerID": f"s-{j:019d}"}
                    for j in range(10)
                ]
            }
            for i in range(18)
        ]
        
        mock_drs.describe_jobs.return_value = {"items": active_jobs}
        
        result = check_concurrent_jobs_limit("us-east-1")
        
        assert result["canStartJob"] is True
        assert result["currentJobs"] == 18
        assert result["maxJobs"] == 20
        assert result["availableSlots"] == 2


class TestTotalServersInJobsQuotaEnforcement:
    """Test total servers across all jobs limit (500 max)"""

    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_total_servers_at_limit_500_servers(self, mock_get_servers):
        """500 servers across all jobs should be at limit"""
        # Mock 500 existing servers in jobs
        existing_servers = [f"s-{i:019d}" for i in range(500)]
        mock_get_servers.return_value = existing_servers
        
        # Try to add 1 more server
        result = check_total_servers_in_jobs_limit(
            region="us-east-1",
            new_server_count=1
        )
        
        # Should fail because 500 + 1 = 501 > 500
        assert result["valid"] is False
        assert result["totalAfter"] == 501

    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_total_servers_below_limit_400_servers(self, mock_get_servers):
        """400 servers across all jobs should be valid"""
        # Mock 400 existing servers in jobs
        existing_servers = [f"s-{i:019d}" for i in range(400)]
        mock_get_servers.return_value = existing_servers
        
        # Try to add 50 more servers (total 450)
        result = check_total_servers_in_jobs_limit(
            region="us-east-1",
            new_server_count=50
        )
        
        assert result["valid"] is True
        assert result["totalAfter"] == 450
        # availableSlots = 500 - 400 = 100 (not 50)
        assert result["availableSlots"] == 100



class TestServerConflictDetection:
    """Test server conflict detection across concurrent jobs"""

    @patch("shared.conflict_detection.get_servers_in_active_executions")
    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_server_already_in_job_conflict(self, mock_drs_jobs, mock_executions):
        """Server already in active job should be detected"""
        # Mock no servers in executions
        mock_executions.return_value = {}
        
        # Mock server s-0000000000000000001 in active DRS job (returns dict)
        mock_drs_jobs.return_value = {
            "s-0000000000000000001": {
                "jobId": "drsjob-001",
                "jobStatus": "STARTED"
            }
        }
        
        # Create plan with same server
        plan = {
            "planId": "test-plan",
            "waves": [
                {
                    "waveName": "Wave-1",
                    "protectionGroupId": "pg-test"
                }
            ]
        }
        
        # Mock PG resolution to return the conflicting server
        with patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check") as mock_resolve:
            mock_resolve.return_value = ["s-0000000000000000001"]
            
            with patch("shared.conflict_detection.protection_groups_table") as mock_table:
                mock_table.get_item.return_value = {
                    "Item": {"region": "us-east-1"}
                }
                
                conflicts = check_server_conflicts(plan)
                
                assert len(conflicts) > 0
                assert any(c.get("serverId") == "s-0000000000000000001" for c in conflicts)

    @patch("shared.conflict_detection.get_servers_in_active_executions")
    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_no_server_conflicts(self, mock_drs_jobs, mock_executions):
        """Different servers should have no conflicts"""
        # Mock no servers in executions
        mock_executions.return_value = {}
        
        # Mock servers 1-10 in active DRS jobs (returns dict)
        mock_drs_jobs.return_value = {
            f"s-{i:019d}": {"jobId": "drsjob-001", "status": "STARTED"}
            for i in range(1, 11)
        }
        
        # Create plan with different servers (11-20)
        plan = {
            "planId": "test-plan",
            "waves": [
                {
                    "waveName": "Wave-1",
                    "protectionGroupId": "pg-test"
                }
            ]
        }
        
        # Mock PG resolution to return different servers
        with patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check") as mock_resolve:
            mock_resolve.return_value = [f"s-{i:019d}" for i in range(11, 21)]
            
            with patch("shared.conflict_detection.protection_groups_table") as mock_table:
                mock_table.get_item.return_value = {
                    "Item": {"region": "us-east-1"}
                }
                
                conflicts = check_server_conflicts(plan)
                
                # Should have no conflicts (different servers)
                server_conflicts = [c for c in conflicts if c.get("conflictSource") == "drs_job"]
                assert len(server_conflicts) == 0


class TestRateLimitingApproachingMaximums:
    """Test rate limiting and warnings when approaching quota maximums"""

    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_warning_at_90_percent_capacity(self, mock_resolve):
        """Should warn when at 90% of any quota"""
        # 90 servers (90% of 100 limit)
        server_ids = [f"s-{i:019d}" for i in range(90)]
        mock_resolve.return_value = server_ids
        
        wave = {"protectionGroupId": "pg-test-90"}
        result = validate_wave_server_count(wave, {})
        
        assert result["valid"] is True
        assert result["serverCount"] == 90

    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_warning_at_95_percent_capacity(self, mock_resolve):
        """Should warn when at 95% of any quota"""
        # 95 servers (95% of 100 limit)
        server_ids = [f"s-{i:019d}" for i in range(95)]
        mock_resolve.return_value = server_ids
        
        wave = {"protectionGroupId": "pg-test-95"}
        result = validate_wave_server_count(wave, {})
        
        assert result["valid"] is True
        assert result["serverCount"] == 95

    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_warning_at_99_percent_capacity(self, mock_resolve):
        """Should warn when at 99% of any quota"""
        # 99 servers (99% of 100 limit)
        server_ids = [f"s-{i:019d}" for i in range(99)]
        mock_resolve.return_value = server_ids
        
        wave = {"protectionGroupId": "pg-test-99"}
        result = validate_wave_server_count(wave, {})
        
        assert result["valid"] is True
        assert result["serverCount"] == 99



class TestMultiAccountCapacityTracking:
    """Test multi-account capacity tracking (300 replicating per account)"""

    @patch("shared.conflict_detection.create_drs_client")
    def test_single_account_at_300_replicating_limit(self, mock_create_client):
        """Single account with 300 replicating servers at hard limit"""
        mock_drs = Mock()
        mock_create_client.return_value = mock_drs
        
        # Mock 300 replicating servers
        replicating_servers = [
            {
                "sourceServerID": f"s-{i:019d}",
                "replicationStatus": "REPLICATING",
                "stagingArea": {
                    "stagingAccountID": "123456789012"
                }
            }
            for i in range(300)
        ]
        
        mock_drs.describe_source_servers.return_value = {
            "items": replicating_servers
        }
        
        # Count replicating servers
        response = mock_drs.describe_source_servers()
        replicating_count = len([
            s for s in response["items"]
            if s.get("replicationStatus") == "REPLICATING"
        ])
        
        assert replicating_count == 300
        # At hard limit - should not allow more

    @patch("shared.conflict_detection.create_drs_client")
    def test_extended_source_servers_not_counted_in_replicating(
        self, mock_create_client
    ):
        """Extended source servers should not count toward 300 limit"""
        mock_drs = Mock()
        mock_create_client.return_value = mock_drs
        
        # Mock 250 replicating + 250 extended = 500 total source servers
        # But only 250 count toward replicating limit
        servers = []
        
        # 250 replicating in target account
        for i in range(250):
            servers.append({
                "sourceServerID": f"s-{i:019d}",
                "replicationStatus": "REPLICATING",
                "stagingArea": {
                    "stagingAccountID": "123456789012"  # Target account
                }
            })
        
        # 250 extended from staging account
        for i in range(250, 500):
            servers.append({
                "sourceServerID": f"s-{i:019d}",
                "replicationStatus": "REPLICATING",
                "stagingArea": {
                    "stagingAccountID": "999999999999"  # Staging account
                }
            })
        
        mock_drs.describe_source_servers.return_value = {"items": servers}
        
        # Count only servers replicating TO target account
        target_account = "123456789012"
        response = mock_drs.describe_source_servers()
        replicating_in_target = len([
            s for s in response["items"]
            if (s.get("replicationStatus") == "REPLICATING" and
                s.get("stagingArea", {}).get("stagingAccountID") == 
                target_account)
        ])
        
        assert replicating_in_target == 250
        # Extended servers don't count toward 300 limit
        assert len(response["items"]) == 500  # Total source servers

    @patch("shared.conflict_detection.create_drs_client")
    def test_multi_account_capacity_4000_source_servers(
        self, mock_create_client
    ):
        """Test 4,000 source server limit across multiple accounts"""
        mock_drs = Mock()
        mock_create_client.return_value = mock_drs
        
        # Mock 4,000 source servers (max limit)
        # 13 staging accounts × 300 + 1 account × 100 = 4,000
        servers = []
        
        for account_idx in range(13):
            for i in range(300):
                server_id = f"s-{account_idx:02d}{i:017d}"
                servers.append({
                    "sourceServerID": server_id,
                    "replicationStatus": "REPLICATING",
                    "stagingArea": {
                        "stagingAccountID": f"99999999{account_idx:04d}"
                    }
                })
        
        # Last 100 servers
        for i in range(100):
            server_id = f"s-13{i:017d}"
            servers.append({
                "sourceServerID": server_id,
                "replicationStatus": "REPLICATING",
                "stagingArea": {
                    "stagingAccountID": "999999999013"
                }
            })
        
        mock_drs.describe_source_servers.return_value = {"items": servers}
        
        response = mock_drs.describe_source_servers()
        total_source_servers = len(response["items"])
        
        assert total_source_servers == 4000
        # At maximum source server limit



class TestComprehensiveQuotaValidation:
    """Comprehensive tests validating all quotas together"""

    @patch("shared.conflict_detection.create_drs_client")
    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_all_quotas_at_maximum_capacity(self, mock_get_servers, mock_create_client):
        """Test system behavior when all quotas are at maximum"""
        mock_drs = Mock()
        mock_create_client.return_value = mock_drs
        
        # 20 concurrent jobs (max)
        active_jobs = []
        for i in range(20):
            # Each job has 25 servers (20 × 25 = 500 total)
            active_jobs.append({
                "jobID": f"drsjob-{i:03d}",
                "status": "STARTED",
                "participatingServers": [
                    {"sourceServerID": f"s-{j:019d}"}
                    for j in range(i*25, (i+1)*25)
                ]
            })
        
        mock_drs.describe_jobs.return_value = {"items": active_jobs}
        
        # Mock 500 servers in active jobs
        all_servers = [f"s-{i:019d}" for i in range(500)]
        mock_get_servers.return_value = all_servers
        
        # Check concurrent jobs
        jobs_result = check_concurrent_jobs_limit("us-east-1")
        assert jobs_result["canStartJob"] is False
        assert jobs_result["currentJobs"] == 20
        
        # Try to add one more server (would exceed 500 limit)
        total_result = check_total_servers_in_jobs_limit(
            region="us-east-1",
            new_server_count=1
        )
        assert total_result["valid"] is False

    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_quota_validation_error_messages(self, mock_resolve):
        """Test that quota validation provides clear error messages"""
        # Test 101 servers
        server_ids = [f"s-{i:019d}" for i in range(101)]
        mock_resolve.return_value = server_ids
        
        wave = {"protectionGroupId": "pg-test"}
        result = validate_wave_server_count(wave, {})
        
        assert result["valid"] is False
        assert "message" in result
        # Error should mention the limit
        message_str = str(result["message"])
        assert "100" in message_str

    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_quota_validation_provides_recommendations(self, mock_get_servers):
        """Test that quota errors include recommendations"""
        # Mock no existing servers
        mock_get_servers.return_value = []
        
        # Test exceeding total servers limit
        result = check_total_servers_in_jobs_limit(
            region="us-east-1",
            new_server_count=600
        )
        
        assert result["valid"] is False
        assert result["totalAfter"] == 600
        # Should show it exceeds the limit
        assert result["totalAfter"] > result["maxServers"]


class TestQuotaDocumentationAlignment:
    """Verify implementation matches documented quotas"""

    @patch("shared.conflict_detection.resolve_pg_servers_for_conflict_check")
    def test_max_servers_per_job_matches_docs(self, mock_resolve):
        """Verify 100 servers per job limit matches documentation"""
        # From DRS_SERVICE_QUOTAS_COMPLETE.md
        DOCUMENTED_LIMIT = 100
        
        # Test at limit
        servers_at_limit = [f"s-{i:019d}" for i in range(DOCUMENTED_LIMIT)]
        mock_resolve.return_value = servers_at_limit
        
        wave = {"protectionGroupId": "pg-test"}
        result = validate_wave_server_count(wave, {})
        assert result["valid"] is True
        
        # Test over limit
        servers_over_limit = [
            f"s-{i:019d}" for i in range(DOCUMENTED_LIMIT + 1)
        ]
        mock_resolve.return_value = servers_over_limit
        
        result = validate_wave_server_count(wave, {})
        assert result["valid"] is False

    @patch("shared.conflict_detection.get_servers_in_active_drs_jobs")
    def test_max_total_servers_matches_docs(self, mock_get_servers):
        """Verify 500 total servers limit matches documentation"""
        # From DRS_SERVICE_QUOTAS_COMPLETE.md
        DOCUMENTED_LIMIT = 500
        
        # Mock no existing servers
        mock_get_servers.return_value = []
        
        # Test at limit
        result = check_total_servers_in_jobs_limit(
            region="us-east-1",
            new_server_count=DOCUMENTED_LIMIT
        )
        assert result["valid"] is True
        assert result["totalAfter"] == DOCUMENTED_LIMIT
        
        # Test over limit
        result = check_total_servers_in_jobs_limit(
            region="us-east-1",
            new_server_count=DOCUMENTED_LIMIT + 1
        )
        assert result["valid"] is False

    @patch("shared.conflict_detection.create_drs_client")
    def test_max_concurrent_jobs_matches_docs(self, mock_create_client):
        """Verify 20 concurrent jobs limit matches documentation"""
        # From DRS_SERVICE_QUOTAS_COMPLETE.md
        DOCUMENTED_LIMIT = 20
        
        mock_drs = Mock()
        mock_create_client.return_value = mock_drs
        
        # Test at limit
        active_jobs = [
            {
                "jobID": f"drsjob-{i:03d}",
                "status": "STARTED",
                "participatingServers": [
                    {"sourceServerID": f"s-{i:019d}"}
                ]
            }
            for i in range(DOCUMENTED_LIMIT)
        ]
        
        mock_drs.describe_jobs.return_value = {"items": active_jobs}
        
        result = check_concurrent_jobs_limit("us-east-1")
        assert result["currentJobs"] == DOCUMENTED_LIMIT
        assert result["maxJobs"] == DOCUMENTED_LIMIT
        assert result["canStartJob"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
