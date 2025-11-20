"""
Mock DRS (Elastic Disaster Recovery) client for unit testing.
Simulates DRS API behavior without making real AWS API calls.
"""
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class ThrottlingException(Exception):
    """Simulates DRS API throttling error."""
    pass


class ResourceNotFoundException(Exception):
    """Simulates DRS resource not found error."""
    pass


class ValidationException(Exception):
    """Simulates DRS validation error."""
    pass


class ServiceUnavailableException(Exception):
    """Simulates DRS service unavailable error."""
    pass


class MockDRSClient:
    """
    Mock DRS client that simulates AWS Elastic Disaster Recovery API.
    
    Supports:
    - describe_source_servers with realistic responses
    - start_recovery with job ID generation
    - describe_jobs with status transitions (PENDING → IN_PROGRESS → COMPLETED)
    - Throttling and error simulation
    """
    
    def __init__(
        self,
        simulate_throttling: bool = False,
        throttle_after_calls: int = 10,
        simulate_errors: bool = False,
        error_rate: float = 0.0
    ):
        """
        Initialize mock DRS client.
        
        Args:
            simulate_throttling: Enable throttling simulation
            throttle_after_calls: Number of calls before throttling
            simulate_errors: Enable random error simulation
            error_rate: Probability of errors (0.0 to 1.0)
        """
        self.simulate_throttling = simulate_throttling
        self.throttle_after_calls = throttle_after_calls
        self.simulate_errors = simulate_errors
        self.error_rate = error_rate
        
        # Track API calls for throttling simulation
        self.call_count = 0
        
        # Mock data stores
        self.source_servers: Dict[str, Dict[str, Any]] = {}
        self.recovery_jobs: Dict[str, Dict[str, Any]] = {}
        
        # Initialize with default test servers
        self._initialize_test_servers()
    
    def _initialize_test_servers(self):
        """Initialize mock source servers for testing."""
        test_servers = [
            "s-3d75cdc0d9a28a725",
            "s-3afa164776f93ce4f",
            "s-3c1730a9e0771ea14",
            "s-3c63bb8be30d7d071",
            "s-3578f52ef3bdd58b4",
            "s-3b9401c1cd270a7a8"
        ]
        
        for server_id in test_servers:
            self.source_servers[server_id] = {
                "sourceServerID": server_id,
                "arn": f"arn:aws:drs:us-east-1:123456789012:source-server/{server_id}",
                "tags": {},
                "dataReplicationInfo": {
                    "dataReplicationState": "CONTINUOUS",
                    "dataReplicationInitiation": {
                        "startDateTime": "2025-01-01T00:00:00Z"
                    }
                },
                "lastLaunchResult": "NOT_STARTED",
                "lifeCycle": {
                    "addedToServiceDateTime": "2025-01-01T00:00:00Z"
                },
                "replicationDirection": "FAILOVER",
                "sourceProperties": {
                    "cpus": [{"cores": 2}],
                    "disks": [{"bytes": 107374182400}],
                    "identificationHints": {
                        "hostname": f"server-{server_id[-8:]}"
                    },
                    "lastUpdatedDateTime": "2025-01-01T00:00:00Z",
                    "networkInterfaces": [
                        {"ips": ["10.0.1.100"], "isPrimary": True}
                    ],
                    "os": {"fullString": "Microsoft Windows Server 2019"},
                    "ramBytes": 8589934592,
                    "recommendedInstanceType": "t3.large"
                }
            }
    
    def _check_throttling(self):
        """Check if request should be throttled."""
        if self.simulate_throttling:
            self.call_count += 1
            if self.call_count > self.throttle_after_calls:
                self.call_count = 0  # Reset for next cycle
                raise ThrottlingException("Rate exceeded")
    
    def _check_random_error(self):
        """Simulate random errors based on error_rate."""
        if self.simulate_errors and self.error_rate > 0:
            import random
            if random.random() < self.error_rate:
                raise ServiceUnavailableException("Service temporarily unavailable")
    
    def describe_source_servers(
        self,
        filters: Optional[Dict[str, List[str]]] = None,
        maxResults: int = 200,
        nextToken: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mock describe_source_servers API call.
        
        Args:
            filters: Filter by sourceServerIDs or other criteria
            maxResults: Maximum number of results to return
            nextToken: Pagination token
            
        Returns:
            Dictionary with 'items' list of source servers
        """
        self._check_throttling()
        self._check_random_error()
        
        # Filter servers if requested
        if filters and "sourceServerIDs" in filters:
            server_ids = filters["sourceServerIDs"]
            items = [
                self.source_servers[sid]
                for sid in server_ids
                if sid in self.source_servers
            ]
        else:
            items = list(self.source_servers.values())
        
        # Apply pagination
        items = items[:maxResults]
        
        return {
            "items": items,
            "nextToken": None  # Simplified: no pagination in mock
        }
    
    def start_recovery(
        self,
        sourceServers: List[Dict[str, str]],
        isDrill: bool = False,
        tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Mock start_recovery API call.
        
        Args:
            sourceServers: List of source servers to recover
            isDrill: Whether this is a drill (non-disruptive test)
            tags: Tags to apply to recovery job
            
        Returns:
            Dictionary with recovery job information
        """
        self._check_throttling()
        self._check_random_error()
        
        # Validate source servers exist
        for server in sourceServers:
            server_id = server.get("sourceServerID")
            recovery_snapshot_id = server.get("recoverySnapshotID", "LATEST")
            
            if server_id not in self.source_servers:
                raise ResourceNotFoundException(
                    f"Source server not found: {server_id}"
                )
            
            if recovery_snapshot_id != "LATEST":
                # In real DRS, you can specify snapshot IDs
                # For mock, we only support LATEST
                pass
        
        # Generate job ID
        job_id = f"job-{uuid.uuid4().hex[:16]}"
        
        # Create recovery job
        job = {
            "jobID": job_id,
            "arn": f"arn:aws:drs:us-east-1:123456789012:job/{job_id}",
            "type": "LAUNCH" if not isDrill else "DRILL",
            "initiatedBy": "START_RECOVERY",
            "creationDateTime": datetime.utcnow().isoformat() + "Z",
            "endDateTime": None,
            "status": "PENDING",
            "participatingServers": [
                {
                    "sourceServerID": server["sourceServerID"],
                    "recoveryInstanceID": None,
                    "launchStatus": "PENDING"
                }
                for server in sourceServers
            ],
            "tags": tags or {}
        }
        
        self.recovery_jobs[job_id] = job
        
        # Schedule status transitions (simulated)
        self._schedule_job_transitions(job_id)
        
        return {"job": job}
    
    def _schedule_job_transitions(self, job_id: str):
        """
        Simulate job status transitions over time.
        In real implementation, this would happen asynchronously.
        For testing, we'll track transition times.
        """
        job = self.recovery_jobs[job_id]
        creation_time = datetime.fromisoformat(job["creationDateTime"].replace("Z", ""))
        
        # Store transition schedule
        job["_transitions"] = {
            "in_progress_at": creation_time + timedelta(seconds=5),
            "completed_at": creation_time + timedelta(seconds=30)
        }
    
    def describe_jobs(
        self,
        filters: Optional[Dict[str, List[str]]] = None,
        maxResults: int = 200,
        nextToken: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mock describe_jobs API call.
        
        Args:
            filters: Filter by jobIDs or other criteria
            maxResults: Maximum number of results
            nextToken: Pagination token
            
        Returns:
            Dictionary with 'items' list of jobs
        """
        self._check_throttling()
        self._check_random_error()
        
        # Update job statuses based on time
        self._update_job_statuses()
        
        # Filter jobs if requested
        if filters and "jobIDs" in filters:
            job_ids = filters["jobIDs"]
            items = [
                self.recovery_jobs[jid]
                for jid in job_ids
                if jid in self.recovery_jobs
            ]
        else:
            items = list(self.recovery_jobs.values())
        
        # Remove internal fields
        items = [
            {k: v for k, v in job.items() if not k.startswith("_")}
            for job in items
        ]
        
        # Apply pagination
        items = items[:maxResults]
        
        return {
            "items": items,
            "nextToken": None
        }
    
    def _update_job_statuses(self):
        """Update job statuses based on elapsed time."""
        now = datetime.utcnow()
        
        for job_id, job in self.recovery_jobs.items():
            if "_transitions" not in job:
                continue
            
            transitions = job["_transitions"]
            
            # Transition to IN_PROGRESS
            if (job["status"] == "PENDING" and 
                now >= transitions["in_progress_at"]):
                job["status"] = "IN_PROGRESS"
                for server in job["participatingServers"]:
                    server["launchStatus"] = "IN_PROGRESS"
                    # Generate mock recovery instance ID
                    server["recoveryInstanceID"] = f"i-{uuid.uuid4().hex[:17]}"
            
            # Transition to COMPLETED
            if (job["status"] == "IN_PROGRESS" and 
                now >= transitions["completed_at"]):
                job["status"] = "COMPLETED"
                job["endDateTime"] = now.isoformat() + "Z"
                for server in job["participatingServers"]:
                    server["launchStatus"] = "LAUNCHED"
    
    def terminate_recovery_instances(
        self,
        recoveryInstanceIDs: List[str]
    ) -> Dict[str, Any]:
        """
        Mock terminate_recovery_instances API call.
        
        Args:
            recoveryInstanceIDs: List of recovery instance IDs to terminate
            
        Returns:
            Dictionary with termination job information
        """
        self._check_throttling()
        self._check_random_error()
        
        job_id = f"job-{uuid.uuid4().hex[:16]}"
        
        job = {
            "jobID": job_id,
            "type": "TERMINATE_RECOVERY_INSTANCES",
            "status": "COMPLETED",
            "creationDateTime": datetime.utcnow().isoformat() + "Z",
            "endDateTime": datetime.utcnow().isoformat() + "Z"
        }
        
        self.recovery_jobs[job_id] = job
        
        return {"job": job}
    
    def add_source_server(self, server_id: str, server_data: Optional[Dict[str, Any]] = None):
        """
        Add a source server to the mock (for testing).
        
        Args:
            server_id: Source server ID
            server_data: Optional server data (will use defaults if not provided)
        """
        if server_data:
            self.source_servers[server_id] = server_data
        else:
            self.source_servers[server_id] = {
                "sourceServerID": server_id,
                "arn": f"arn:aws:drs:us-east-1:123456789012:source-server/{server_id}",
                "dataReplicationInfo": {
                    "dataReplicationState": "CONTINUOUS"
                },
                "lastLaunchResult": "NOT_STARTED"
            }
    
    def remove_source_server(self, server_id: str):
        """Remove a source server from the mock (for testing)."""
        if server_id in self.source_servers:
            del self.source_servers[server_id]
    
    def simulate_job_failure(self, job_id: str, error_message: str = "Recovery failed"):
        """
        Simulate a job failure (for testing error scenarios).
        
        Args:
            job_id: Job ID to fail
            error_message: Error message to set
        """
        if job_id in self.recovery_jobs:
            job = self.recovery_jobs[job_id]
            job["status"] = "FAILED"
            job["endDateTime"] = datetime.utcnow().isoformat() + "Z"
            job["statusMessage"] = error_message
            
            for server in job["participatingServers"]:
                server["launchStatus"] = "FAILED"
    
    def reset(self):
        """Reset mock state (for testing)."""
        self.call_count = 0
        self.recovery_jobs.clear()
        self.source_servers.clear()
        self._initialize_test_servers()


def create_mock_drs_client(**kwargs) -> MockDRSClient:
    """
    Factory function to create a mock DRS client.
    
    Args:
        **kwargs: Arguments to pass to MockDRSClient constructor
        
    Returns:
        MockDRSClient instance
    """
    return MockDRSClient(**kwargs)
