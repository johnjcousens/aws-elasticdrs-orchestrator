"""
Unit tests for MockDRSClient.
Validates that the mock DRS client behaves correctly.
"""
import pytest
import time
from mocks.mock_drs_client import (
    MockDRSClient,
    ThrottlingException,
    ResourceNotFoundException,
    ServiceUnavailableException,
    create_mock_drs_client
)


class TestMockDRSClient:
    """Test suite for MockDRSClient."""
    
    def test_initialization(self):
        """Test mock client initializes with default test servers."""
        client = MockDRSClient()
        
        response = client.describe_source_servers()
        assert len(response["items"]) == 6
        
        # Verify server ID format
        for server in response["items"]:
            assert server["sourceServerID"].startswith("s-")
            assert len(server["sourceServerID"]) == 19
    
    def test_describe_source_servers_all(self):
        """Test describe_source_servers returns all servers."""
        client = MockDRSClient()
        
        response = client.describe_source_servers()
        
        assert "items" in response
        assert len(response["items"]) == 6
        assert response["nextToken"] is None
    
    def test_describe_source_servers_filtered(self):
        """Test describe_source_servers with filter."""
        client = MockDRSClient()
        
        server_ids = ["s-3d75cdc0d9a28a725", "s-3afa164776f93ce4f"]
        response = client.describe_source_servers(
            filters={"sourceServerIDs": server_ids}
        )
        
        assert len(response["items"]) == 2
        returned_ids = [s["sourceServerID"] for s in response["items"]]
        assert set(returned_ids) == set(server_ids)
    
    def test_describe_source_servers_nonexistent(self):
        """Test describe_source_servers with nonexistent server."""
        client = MockDRSClient()
        
        response = client.describe_source_servers(
            filters={"sourceServerIDs": ["s-nonexistent"]}
        )
        
        assert len(response["items"]) == 0
    
    def test_start_recovery_single_server(self):
        """Test start_recovery with single server."""
        client = MockDRSClient()
        
        response = client.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-3d75cdc0d9a28a725", "recoverySnapshotID": "LATEST"}
            ],
            isDrill=False
        )
        
        assert "job" in response
        job = response["job"]
        assert job["jobID"].startswith("job-")
        assert job["status"] == "PENDING"
        assert job["type"] == "LAUNCH"
        assert len(job["participatingServers"]) == 1
    
    def test_start_recovery_multiple_servers(self):
        """Test start_recovery with multiple servers."""
        client = MockDRSClient()
        
        server_ids = ["s-3d75cdc0d9a28a725", "s-3afa164776f93ce4f", "s-3c1730a9e0771ea14"]
        response = client.start_recovery(
            sourceServers=[
                {"sourceServerID": sid, "recoverySnapshotID": "LATEST"}
                for sid in server_ids
            ],
            isDrill=True
        )
        
        job = response["job"]
        assert job["type"] == "DRILL"
        assert len(job["participatingServers"]) == 3
    
    def test_start_recovery_invalid_server(self):
        """Test start_recovery with invalid server ID."""
        client = MockDRSClient()
        
        with pytest.raises(ResourceNotFoundException, match="Source server not found"):
            client.start_recovery(
                sourceServers=[
                    {"sourceServerID": "s-invalid", "recoverySnapshotID": "LATEST"}
                ]
            )
    
    def test_describe_jobs_single(self):
        """Test describe_jobs returns created job."""
        client = MockDRSClient()
        
        # Create a job
        response = client.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-3d75cdc0d9a28a725", "recoverySnapshotID": "LATEST"}
            ]
        )
        job_id = response["job"]["jobID"]
        
        # Describe the job
        jobs_response = client.describe_jobs(
            filters={"jobIDs": [job_id]}
        )
        
        assert len(jobs_response["items"]) == 1
        assert jobs_response["items"][0]["jobID"] == job_id
    
    def test_describe_jobs_all(self):
        """Test describe_jobs returns all jobs."""
        client = MockDRSClient()
        
        # Create multiple jobs
        for i in range(3):
            client.start_recovery(
                sourceServers=[
                    {"sourceServerID": "s-3d75cdc0d9a28a725", "recoverySnapshotID": "LATEST"}
                ]
            )
        
        # Describe all jobs
        response = client.describe_jobs()
        
        assert len(response["items"]) == 3
    
    def test_job_status_transitions(self):
        """Test job status transitions from PENDING to IN_PROGRESS to COMPLETED."""
        client = MockDRSClient()
        
        # Create a job
        response = client.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-3d75cdc0d9a28a725", "recoverySnapshotID": "LATEST"}
            ]
        )
        job_id = response["job"]["jobID"]
        
        # Initially PENDING
        jobs = client.describe_jobs(filters={"jobIDs": [job_id]})
        assert jobs["items"][0]["status"] == "PENDING"
        
        # Wait for IN_PROGRESS transition (5 seconds in mock)
        time.sleep(6)
        jobs = client.describe_jobs(filters={"jobIDs": [job_id]})
        assert jobs["items"][0]["status"] == "IN_PROGRESS"
        
        # Verify recovery instance ID is generated
        assert jobs["items"][0]["participatingServers"][0]["recoveryInstanceID"] is not None
        
        # Wait for COMPLETED transition (30 seconds total in mock)
        time.sleep(25)
        jobs = client.describe_jobs(filters={"jobIDs": [job_id]})
        assert jobs["items"][0]["status"] == "COMPLETED"
        assert jobs["items"][0]["endDateTime"] is not None
    
    def test_throttling_simulation(self):
        """Test throttling simulation after N calls."""
        client = MockDRSClient(
            simulate_throttling=True,
            throttle_after_calls=3
        )
        
        # First 3 calls should succeed
        for i in range(3):
            client.describe_source_servers()
        
        # 4th call should throttle
        with pytest.raises(ThrottlingException, match="Rate exceeded"):
            client.describe_source_servers()
        
        # After throttle, next call should succeed (counter reset)
        client.describe_source_servers()
    
    def test_error_simulation(self):
        """Test random error simulation."""
        client = MockDRSClient(
            simulate_errors=True,
            error_rate=1.0  # 100% error rate for testing
        )
        
        with pytest.raises(ServiceUnavailableException, match="Service temporarily unavailable"):
            client.describe_source_servers()
    
    def test_terminate_recovery_instances(self):
        """Test terminate_recovery_instances."""
        client = MockDRSClient()
        
        # Start recovery to get instance IDs
        response = client.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-3d75cdc0d9a28a725", "recoverySnapshotID": "LATEST"}
            ]
        )
        
        # Wait for instance to be created
        time.sleep(6)
        jobs = client.describe_jobs(filters={"jobIDs": [response["job"]["jobID"]]})
        instance_id = jobs["items"][0]["participatingServers"][0]["recoveryInstanceID"]
        
        # Terminate instance
        term_response = client.terminate_recovery_instances(
            recoveryInstanceIDs=[instance_id]
        )
        
        assert term_response["job"]["type"] == "TERMINATE_RECOVERY_INSTANCES"
        assert term_response["job"]["status"] == "COMPLETED"
    
    def test_add_source_server(self):
        """Test adding custom source server."""
        client = MockDRSClient()
        
        custom_server_id = "s-custom123456789ab"
        client.add_source_server(custom_server_id)
        
        response = client.describe_source_servers(
            filters={"sourceServerIDs": [custom_server_id]}
        )
        
        assert len(response["items"]) == 1
        assert response["items"][0]["sourceServerID"] == custom_server_id
    
    def test_remove_source_server(self):
        """Test removing source server."""
        client = MockDRSClient()
        
        server_id = "s-3d75cdc0d9a28a725"
        client.remove_source_server(server_id)
        
        response = client.describe_source_servers(
            filters={"sourceServerIDs": [server_id]}
        )
        
        assert len(response["items"]) == 0
    
    def test_simulate_job_failure(self):
        """Test simulating job failure."""
        client = MockDRSClient()
        
        # Create a job
        response = client.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-3d75cdc0d9a28a725", "recoverySnapshotID": "LATEST"}
            ]
        )
        job_id = response["job"]["jobID"]
        
        # Simulate failure
        error_msg = "Test failure message"
        client.simulate_job_failure(job_id, error_msg)
        
        # Verify job is failed
        jobs = client.describe_jobs(filters={"jobIDs": [job_id]})
        job = jobs["items"][0]
        assert job["status"] == "FAILED"
        assert job["statusMessage"] == error_msg
        assert job["participatingServers"][0]["launchStatus"] == "FAILED"
    
    def test_reset(self):
        """Test resetting mock state."""
        client = MockDRSClient()
        
        # Create some jobs
        client.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-3d75cdc0d9a28a725", "recoverySnapshotID": "LATEST"}
            ]
        )
        
        # Add custom server
        client.add_source_server("s-custom")
        
        # Reset
        client.reset()
        
        # Verify state is reset
        jobs = client.describe_jobs()
        assert len(jobs["items"]) == 0
        
        servers = client.describe_source_servers()
        assert len(servers["items"]) == 6  # Back to default 6
        
        # Custom server should be gone
        custom = client.describe_source_servers(filters={"sourceServerIDs": ["s-custom"]})
        assert len(custom["items"]) == 0
    
    def test_factory_function(self):
        """Test create_mock_drs_client factory function."""
        client = create_mock_drs_client(simulate_throttling=True)
        
        assert isinstance(client, MockDRSClient)
        assert client.simulate_throttling is True
    
    def test_job_has_required_fields(self):
        """Test that created jobs have all required fields."""
        client = MockDRSClient()
        
        response = client.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-3d75cdc0d9a28a725", "recoverySnapshotID": "LATEST"}
            ],
            isDrill=True
        )
        
        job = response["job"]
        required_fields = [
            "jobID", "arn", "type", "initiatedBy", "creationDateTime",
            "status", "participatingServers"
        ]
        
        for field in required_fields:
            assert field in job, f"Job missing required field: {field}"
    
    def test_server_has_required_fields(self):
        """Test that source servers have all required fields."""
        client = MockDRSClient()
        
        response = client.describe_source_servers()
        server = response["items"][0]
        
        required_fields = [
            "sourceServerID", "arn", "dataReplicationInfo",
            "lastLaunchResult", "lifeCycle", "sourceProperties"
        ]
        
        for field in required_fields:
            assert field in server, f"Server missing required field: {field}"
    
    def test_participating_server_fields(self):
        """Test participating server structure in jobs."""
        client = MockDRSClient()
        
        response = client.start_recovery(
            sourceServers=[
                {"sourceServerID": "s-3d75cdc0d9a28a725", "recoverySnapshotID": "LATEST"}
            ]
        )
        
        participating_server = response["job"]["participatingServers"][0]
        
        assert "sourceServerID" in participating_server
        assert "recoveryInstanceID" in participating_server
        assert "launchStatus" in participating_server
        assert participating_server["launchStatus"] == "PENDING"
