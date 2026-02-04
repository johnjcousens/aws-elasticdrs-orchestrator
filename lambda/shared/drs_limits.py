"""
DRS Service Limits Validation

Enforces AWS Elastic Disaster Recovery Service (DRS) hard limits to prevent
exceeding capacity during DR operations.

AWS DRS HARD LIMITS (cannot be increased):
    - MAX_SERVERS_PER_JOB: 100 servers per recovery job
    - MAX_CONCURRENT_JOBS: 20 active jobs at once
    - MAX_SERVERS_IN_ALL_JOBS: 500 servers across all active jobs
    - MAX_REPLICATING_SERVERS: 300 servers in replication state

VALIDATION FUNCTIONS:
    - validate_wave_sizes(): Check wave sizes before execution
    - validate_concurrent_jobs(): Check active job count
    - validate_servers_in_all_jobs(): Check total servers in jobs
    - validate_server_replication_states(): Check server health

USAGE PATTERN:
    1. Call validation functions before starting DR execution
    2. Return 400/429 errors if limits exceeded
    3. Provide actionable error messages to users

INTEGRATION POINTS:
    - execution-handler: Validates before execute_recovery_plan()
    - All functions that start DRS jobs

WHY VALIDATE:
    - Prevents DRS API errors during execution
    - Provides clear error messages before starting
    - Avoids partial failures mid-execution
    - Enforces AWS service quotas

Reference: https://docs.aws.amazon.com/general/latest/gr/drs.html
"""

from typing import Any, Dict, List, Optional

import boto3

# DRS Service Limits (hard limits enforced by AWS)
DRS_LIMITS = {
    "MAX_SERVERS_PER_JOB": 100,  # L-B827C881 - Hard limit, cannot be increased
    "MAX_CONCURRENT_JOBS": 20,  # L-D88FAC3A - Hard limit, cannot be increased
    "MAX_SERVERS_IN_ALL_JOBS": 500,  # L-05AFA8C6 - Hard limit, cannot be increased
    "MAX_REPLICATING_SERVERS": 300,  # L-C1D14A2B - Hard limit, cannot be increased (critical constraint)
    "MAX_SOURCE_SERVERS": 4000,  # L-E28BE5E0 - Adjustable via service quota request
    "WARNING_REPLICATING_THRESHOLD": 250,  # Alert at 83% capacity
    "CRITICAL_REPLICATING_THRESHOLD": 280,  # Block new operations at 93% capacity
}

# Valid replication states for DR recovery operations
VALID_REPLICATION_STATES = ["CONTINUOUS", "INITIAL_SYNC", "RESCAN"]

# Invalid replication states that block DR operations
INVALID_REPLICATION_STATES = [
    "DISCONNECTED",
    "STOPPED",
    "STALLED",
    "NOT_STARTED",
]


def resolve_pg_servers_for_conflict_check(pg_id: str, pg_cache: Dict) -> List[str]:
    """
    Helper function to resolve Protection Group servers.
    This is imported from conflict_detection to avoid circular imports.
    """
    from shared.conflict_detection import (
        resolve_pg_servers_for_conflict_check as resolve_func,
    )

    return resolve_func(pg_id, pg_cache)


def validate_wave_sizes(plan: Dict) -> List[Dict]:
    """
    Validate wave sizes against DRS 100 servers per job limit.

    Resolves Protection Group servers (including tag-based selection) to get
    accurate server counts. Returns list of validation errors for oversized waves.

    DRS LIMIT: Maximum 100 servers per recovery job (hard limit)

    RESOLUTION LOGIC:
    1. If wave has protectionGroupId: resolve servers from Protection Group
       - Tag-based PGs: query DRS API for matching servers
       - Explicit PGs: use sourceServerIds list
    2. If wave has serverIds: use direct server list (backward compatibility)
    3. Cache Protection Group lookups to avoid duplicate queries

    USAGE:
        errors = validate_wave_sizes(recovery_plan)
        if errors:
            return response(400, {
                "error": "WAVE_SIZE_LIMIT_EXCEEDED",
                "errors": errors
            })

    Args:
        plan: Recovery plan dict with waves array

    Returns:
        List of error dicts (empty if all waves valid):
        [
            {
                "type": "WAVE_SIZE_EXCEEDED",
                "wave": "DatabaseWave",
                "waveIndex": 1,
                "serverCount": 150,
                "limit": 100,
                "message": "Wave 'DatabaseWave' has 150 servers, exceeds limit of 100"
            }
        ]
    """
    errors = []
    pg_cache = {}

    for idx, wave in enumerate(plan.get("waves", []), start=1):
        # Get Protection Group ID for this wave
        pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]

        if pg_id:
            # Resolve servers from Protection Group tags
            server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache)
            server_count = len(server_ids)
        elif wave.get("serverIds"):
            # Direct server IDs (for backward compatibility and testing)
            server_count = len(wave.get("serverIds", []))
        else:
            server_count = 0

        if server_count > DRS_LIMITS["MAX_SERVERS_PER_JOB"]:
            errors.append(
                {
                    "type": "WAVE_SIZE_EXCEEDED",
                    "wave": wave.get("waveName", f"Wave {idx}"),
                    "waveIndex": idx,
                    "serverCount": server_count,
                    "limit": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
                    "message": f"Wave '{wave.get('waveName', f'Wave {idx}')}' has {server_count} servers, exceeds limit of {DRS_LIMITS['MAX_SERVERS_PER_JOB']}",  # noqa: E501
                }
            )

    return errors


def validate_concurrent_jobs(region: str, drs_client: Optional[Any] = None) -> Dict:
    """
    Validate current DRS job count against 20 concurrent jobs limit.

    Queries DRS DescribeJobs API for PENDING and STARTED jobs.
    Returns validation result with current count and available slots.

    DRS LIMIT: Maximum 20 concurrent jobs (hard limit)

    WHY VALIDATE: Starting a job when at limit causes DRS API error.
    Better to check proactively and provide clear error message.

    USAGE:
        # With default credentials
        result = validate_concurrent_jobs('us-east-1')

        # With assumed role credentials
        drs_client = create_drs_client(region, account_id, role_arn)
        result = validate_concurrent_jobs('us-east-1', drs_client)

        if not result['valid']:
            return response(429, {
                "error": "CONCURRENT_JOBS_LIMIT_EXCEEDED",
                "currentJobs": result['currentJobs'],
                "maxJobs": result['maxJobs']
            })

    Args:
        region: AWS region to check (e.g., 'us-east-1')
        drs_client: Optional boto3 DRS client with credentials

    Returns:
        {
            "valid": bool,              # False if at/over limit
            "currentJobs": int,         # Number of active jobs
            "maxJobs": 20,              # Hard limit
            "availableSlots": int,      # Remaining capacity
            "activeJobs": [             # List of active job details
                {
                    "jobId": "job-123",
                    "status": "STARTED",
                    "type": "LAUNCH",
                    "serverCount": 50
                }
            ],
            "message": str              # Human-readable status
        }

    SPECIAL CASES:
        - Uninitialized region: Returns valid=True, currentJobs=0
        - API error: Returns valid=True with warning message
    """
    try:
        if drs_client is None:
            regional_drs = boto3.client("drs", region_name=region)
        else:
            regional_drs = drs_client

        # Get active jobs (PENDING or STARTED status)
        active_jobs = []
        paginator = regional_drs.get_paginator("describe_jobs")

        for page in paginator.paginate():
            for job in page.get("items", []):
                if job.get("status") in ["PENDING", "STARTED"]:
                    active_jobs.append(
                        {
                            "jobId": job.get("jobID"),
                            "status": job.get("status"),
                            "type": job.get("type"),
                            "serverCount": len(job.get("participatingServers", [])),
                        }
                    )

        current_count = len(active_jobs)
        available_slots = DRS_LIMITS["MAX_CONCURRENT_JOBS"] - current_count

        return {
            "valid": current_count < DRS_LIMITS["MAX_CONCURRENT_JOBS"],
            "currentJobs": current_count,
            "maxJobs": DRS_LIMITS["MAX_CONCURRENT_JOBS"],
            "availableSlots": available_slots,
            "activeJobs": active_jobs,
            "message": (
                f"DRS has {current_count}/{DRS_LIMITS['MAX_CONCURRENT_JOBS']} active jobs"
                if current_count < DRS_LIMITS["MAX_CONCURRENT_JOBS"]
                else f"DRS concurrent job limit reached ({current_count}/{DRS_LIMITS['MAX_CONCURRENT_JOBS']})"
            ),
        }

    except Exception as e:
        error_str = str(e)
        print(f"Error checking concurrent jobs: {e}")

        # Check for uninitialized region errors
        if any(
            x in error_str
            for x in [
                "UninitializedAccountException",
                "UnrecognizedClientException",
                "security token",
            ]
        ):
            return {
                "valid": True,
                "currentJobs": 0,
                "maxJobs": DRS_LIMITS["MAX_CONCURRENT_JOBS"],
                "availableSlots": DRS_LIMITS["MAX_CONCURRENT_JOBS"],
                "notInitialized": True,
            }

        return {
            "valid": True,
            "warning": f"Could not verify concurrent jobs: {error_str}",
            "currentJobs": None,
            "maxJobs": DRS_LIMITS["MAX_CONCURRENT_JOBS"],
        }


def validate_servers_in_all_jobs(region: str, new_server_count: int, drs_client: Optional[Any] = None) -> Dict:
    """
    Validate total servers across all jobs against 500 server limit.

    Counts servers in active jobs, adds new server count, checks against limit.
    Prevents starting jobs that would exceed aggregate server capacity.

    DRS LIMIT: Maximum 500 servers across all active jobs (hard limit)

    WHY THIS MATTERS: Even if you have <20 jobs, total server count matters.
    Example: 10 jobs with 50 servers each = 500 servers (at limit).

    USAGE:
        # With default credentials
        result = validate_servers_in_all_jobs('us-east-1', 100)

        # With assumed role credentials
        drs_client = create_drs_client(region, account_id, role_arn)
        result = validate_servers_in_all_jobs('us-east-1', 100, drs_client)

        if not result['valid']:
            return response(429, {
                "error": "SERVERS_IN_JOBS_LIMIT_EXCEEDED",
                "currentServersInJobs": result['currentServersInJobs'],
                "newServerCount": result['newServerCount'],
                "totalAfterNew": result['totalAfterNew'],
                "maxServers": 500
            })

    Args:
        region: AWS region to check
        new_server_count: Number of servers in new job to start
        drs_client: Optional boto3 DRS client with credentials

    Returns:
        {
            "valid": bool,                  # False if would exceed limit
            "currentServersInJobs": int,    # Servers in active jobs now
            "newServerCount": int,          # Servers in new job
            "totalAfterNew": int,           # Total after starting new job
            "maxServers": 500,              # Hard limit
            "message": str                  # Human-readable status
        }

    SPECIAL CASES:
        - Uninitialized region: Returns valid=True, currentServersInJobs=0
        - API error: Returns valid=True with warning message
    """
    try:
        if drs_client is None:
            regional_drs = boto3.client("drs", region_name=region)
        else:
            regional_drs = drs_client

        # Count servers in active jobs
        servers_in_jobs = 0
        paginator = regional_drs.get_paginator("describe_jobs")

        for page in paginator.paginate():
            for job in page.get("items", []):
                if job.get("status") in ["PENDING", "STARTED"]:
                    servers_in_jobs += len(job.get("participatingServers", []))

        total_after_new = servers_in_jobs + new_server_count

        return {
            "valid": total_after_new <= DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"],
            "currentServersInJobs": servers_in_jobs,
            "newServerCount": new_server_count,
            "totalAfterNew": total_after_new,
            "maxServers": DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"],
            "message": (
                f"Would have {total_after_new}/{DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS']} servers in active jobs"
                if total_after_new <= DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"]
                else f"Would exceed max servers in all jobs ({total_after_new}/{DRS_LIMITS['MAX_SERVERS_IN_ALL_JOBS']})"
            ),
        }

    except Exception as e:
        error_str = str(e)
        print(f"Error checking servers in all jobs: {e}")

        # Check for uninitialized region errors
        if any(
            x in error_str
            for x in [
                "UninitializedAccountException",
                "UnrecognizedClientException",
                "security token",
            ]
        ):
            return {
                "valid": True,
                "currentServersInJobs": 0,
                "maxServers": DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"],
                "notInitialized": True,
            }

        return {
            "valid": True,
            "warning": f"Could not verify servers in jobs: {error_str}",
            "currentServersInJobs": None,
            "maxServers": DRS_LIMITS["MAX_SERVERS_IN_ALL_JOBS"],
        }


def validate_max_servers_per_job(region: str, drs_client: Optional[Any] = None) -> Dict:
    """
    Get the maximum server count in any single active DRS job.

    Queries DRS DescribeJobs API for PENDING and STARTED jobs,
    finds the job with the most servers, and returns metrics.

    DRS LIMIT: Maximum 100 servers per job (hard limit)

    WHY VALIDATE: Helps identify if any single job is approaching
    the per-job limit, which could cause job failures.

    USAGE:
        # With default credentials
        result = validate_max_servers_per_job('us-east-1')

        # With assumed role credentials
        drs_client = create_drs_client(region, account_id, role_arn)
        result = validate_max_servers_per_job('us-east-1', drs_client)

        if result['maxServersInSingleJob'] > 90:
            print(f"Warning: Job {result['jobId']} has "
                  f"{result['maxServersInSingleJob']} servers")

    Args:
        region: AWS region to check (e.g., 'us-east-1')
        drs_client: Optional boto3 DRS client with credentials

    Returns:
        {
            "maxServersInSingleJob": int,  # Largest job size
            "maxAllowed": 100,             # Hard limit
            "availableSlots": int,         # Remaining capacity
            "jobId": str,                  # ID of largest job
            "status": str,                 # "OK" or "WARNING"
            "message": str                 # Human-readable status
        }

    SPECIAL CASES:
        - No active jobs: Returns maxServersInSingleJob=0
        - Uninitialized region: Returns maxServersInSingleJob=0
        - API error: Returns maxServersInSingleJob=0 with warning
    """
    try:
        if drs_client is None:
            regional_drs = boto3.client("drs", region_name=region)
        else:
            regional_drs = drs_client

        # Get active jobs (PENDING or STARTED status)
        max_servers = 0
        max_job_id = None
        paginator = regional_drs.get_paginator("describe_jobs")

        for page in paginator.paginate():
            for job in page.get("items", []):
                if job.get("status") in ["PENDING", "STARTED"]:
                    server_count = len(job.get("participatingServers", []))
                    if server_count > max_servers:
                        max_servers = server_count
                        max_job_id = job.get("jobID")

        available_slots = DRS_LIMITS["MAX_SERVERS_PER_JOB"] - max_servers
        status = "OK" if max_servers < 90 else "WARNING"

        return {
            "maxServersInSingleJob": max_servers,
            "maxAllowed": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
            "availableSlots": available_slots,
            "jobId": max_job_id,
            "status": status,
            "message": (f"Largest active job has {max_servers} servers" if max_servers > 0 else "No active jobs"),
        }

    except Exception as e:
        error_str = str(e)
        print(f"Error checking max servers per job: {e}")

        # Check for uninitialized region errors
        if any(
            x in error_str
            for x in [
                "UninitializedAccountException",
                "UnrecognizedClientException",
                "security token",
            ]
        ):
            return {
                "maxServersInSingleJob": 0,
                "maxAllowed": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
                "availableSlots": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
                "jobId": None,
                "status": "OK",
                "message": "Region not initialized",
            }

        # Return safe defaults on error
        return {
            "maxServersInSingleJob": 0,
            "maxAllowed": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
            "availableSlots": DRS_LIMITS["MAX_SERVERS_PER_JOB"],
            "jobId": None,
            "status": "OK",
            "message": f"Could not fetch per-job metrics: {error_str}",
        }


def validate_server_replication_states(region: str, server_ids: List[str]) -> Dict:
    """
    Validate all servers have healthy replication for DR recovery.

    Queries DRS DescribeSourceServers API to check replication and lifecycle states.
    Returns validation result with list of unhealthy servers.

    VALID REPLICATION STATES:
        - CONTINUOUS: Ongoing replication (ready for recovery)
        - INITIAL_SYNC: First-time replication in progress
        - RESCAN: Re-scanning for changes

    INVALID REPLICATION STATES (block recovery):
        - DISCONNECTED: Agent not communicating
        - STOPPED: Replication manually stopped
        - STALLED: Replication stuck
        - NOT_STARTED: Never started replication

    WHY VALIDATE: Attempting recovery with unhealthy replication causes
    DRS API errors or launches instances with stale data.

    USAGE:
        result = validate_server_replication_states('us-east-1', server_ids)
        if not result['valid']:
            return response(400, {
                "error": "UNHEALTHY_SERVER_REPLICATION",
                "unhealthyServers": result['unhealthyServers'],
                "healthyCount": result['healthyCount'],
                "unhealthyCount": result['unhealthyCount']
            })

    Args:
        region: AWS region to check
        server_ids: List of DRS source server IDs

    Returns:
        {
            "valid": bool,              # False if any unhealthy
            "healthyCount": int,        # Number of healthy servers
            "unhealthyCount": int,      # Number of unhealthy servers
            "unhealthyServers": [       # Details of unhealthy servers
                {
                    "serverId": "s-123",
                    "hostname": "db-server-01",
                    "replicationState": "DISCONNECTED",
                    "lifecycleState": "STOPPED",
                    "reason": "Replication: DISCONNECTED, Lifecycle: STOPPED"
                }
            ],
            "message": str              # Human-readable status
        }

    BATCH PROCESSING: Processes servers in batches of 200 (DRS API limit)

    SPECIAL CASES:
        - Empty server_ids: Returns valid=True, counts=0
        - API error: Returns valid=True with warning message
    """
    if not server_ids:
        return {
            "valid": True,
            "healthyCount": 0,
            "unhealthyCount": 0,
            "unhealthyServers": [],
        }

    try:
        regional_drs = boto3.client("drs", region_name=region)

        unhealthy_servers = []
        healthy_servers = []

        # Batch describe servers (max 200 per call)
        for i in range(0, len(server_ids), 200):
            batch = server_ids[i : i + 200]

            response = regional_drs.describe_source_servers(filters={"sourceServerIDs": batch})

            for server in response.get("items", []):
                server_id = server.get("sourceServerID")
                replication_state = server.get("dataReplicationInfo", {}).get("dataReplicationState", "UNKNOWN")
                lifecycle_state = server.get("lifeCycle", {}).get("state", "UNKNOWN")

                if replication_state in INVALID_REPLICATION_STATES or lifecycle_state == "STOPPED":
                    unhealthy_servers.append(
                        {
                            "serverId": server_id,
                            "hostname": server.get("sourceProperties", {})
                            .get("identificationHints", {})
                            .get("hostname", "Unknown"),
                            "replicationState": replication_state,
                            "lifecycleState": lifecycle_state,
                            "reason": f"Replication: {replication_state}, Lifecycle: {lifecycle_state}",
                        }
                    )
                else:
                    healthy_servers.append(server_id)

        return {
            "valid": len(unhealthy_servers) == 0,
            "healthyCount": len(healthy_servers),
            "unhealthyCount": len(unhealthy_servers),
            "unhealthyServers": unhealthy_servers,
            "message": (
                f"All {len(healthy_servers)} servers have healthy replication"
                if len(unhealthy_servers) == 0
                else f"{len(unhealthy_servers)} server(s) have unhealthy replication state"
            ),
        }

    except Exception as e:
        print(f"Error checking server replication states: {e}")
        return {
            "valid": True,
            "warning": f"Could not verify server replication states: {str(e)}",
            "unhealthyServers": [],
        }
