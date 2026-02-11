"""
Conflict Detection Utilities - Server Availability Validation

Prevents overlapping DR operations by detecting server conflicts across:
1. Active DynamoDB execution records (PENDING, POLLING, RUNNING, etc.)
2. Live DRS API job queries (PENDING, STARTED jobs)

KEY FUNCTIONS:
    - check_server_conflicts(): Main validation before starting execution
    - get_servers_in_active_executions(): Query DynamoDB for active servers
    - get_servers_in_active_drs_jobs(): Query DRS API for servers in jobs
    - query_drs_servers_by_tags(): Resolve Protection Group tag-based selection

CONFLICT SOURCES:
    1. Execution conflicts: Server in another active execution
    2. DRS job conflicts: Server in active DRS job (outside orchestration)

USAGE PATTERN:
    conflicts = check_server_conflicts(recovery_plan, account_context)
    if conflicts:
        return response(409, {
            "error": "SERVER_CONFLICT",
            "conflicts": conflicts
        })

WHY VALIDATE:
    - Prevents concurrent recovery of same server (data corruption risk)
    - Avoids DRS API errors from overlapping jobs
    - Ensures clean execution state

INTEGRATION POINTS:
    - execution-handler: Validates before execute_recovery_plan()
    - All functions that start DRS jobs
"""

import os
from typing import Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Import cross-account utilities
from shared.cross_account import create_drs_client

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Environment variables
PROTECTION_GROUPS_TABLE = os.environ.get("PROTECTION_GROUPS_TABLE")
RECOVERY_PLANS_TABLE = os.environ.get("RECOVERY_PLANS_TABLE")
EXECUTION_HISTORY_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE")

# DynamoDB tables - lazy initialization for Lambda cold start optimization and test mocking
_protection_groups_table = None
_recovery_plans_table = None
_execution_history_table = None


def get_protection_groups_table():
    """Lazy-load Protection Groups table to optimize Lambda cold starts and enable test mocking"""
    global _protection_groups_table
    if _protection_groups_table is None:
        _protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
    return _protection_groups_table


def get_recovery_plans_table():
    """Lazy-load Recovery Plans table to optimize Lambda cold starts and enable test mocking"""
    global _recovery_plans_table
    if _recovery_plans_table is None:
        _recovery_plans_table = dynamodb.Table(RECOVERY_PLANS_TABLE)
    return _recovery_plans_table


def get_execution_history_table():
    """Lazy-load Execution History table to optimize Lambda cold starts and enable test mocking"""
    global _execution_history_table
    if _execution_history_table is None:
        _execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    return _execution_history_table


# Execution statuses indicating active DR operations in progress
ACTIVE_EXECUTION_STATUSES = [
    "PENDING",
    "POLLING",
    "INITIATED",
    "LAUNCHING",
    "STARTED",
    "IN_PROGRESS",
    "RUNNING",
    "PAUSED",
    "CANCELLING",
]

# DRS job statuses indicating servers are actively being processed
DRS_ACTIVE_JOB_STATUSES = ["PENDING", "STARTED"]


def get_all_active_executions() -> List[Dict]:
    """Get all active executions across all plans"""
    try:
        # Try StatusIndex GSI first
        active_executions = []
        for status in ACTIVE_EXECUTION_STATUSES:
            try:
                result = get_execution_history_table().query(
                    IndexName="StatusIndex",
                    KeyConditionExpression=Key("status").eq(status),
                )
                active_executions.extend(result.get("Items", []))
            except ClientError as e:
                error_code = e.response.get("error", {}).get("Code", "")
                if error_code in [
                    "ValidationException",
                    "ResourceNotFoundException",
                ]:
                    print(f"StatusIndex GSI not available for status {status}: {error_code}")
                else:
                    print(f"DynamoDB error querying StatusIndex for {status}: {e}")
            except Exception as e:
                print(f"Unexpected error querying StatusIndex for {status}: {e}")

        # If no results from GSI, fallback to scan
        if not active_executions:
            result = get_execution_history_table().scan()
            all_executions = result.get("Items", [])
            active_executions = [e for e in all_executions if e.get("status", "").upper() in ACTIVE_EXECUTION_STATUSES]

        return active_executions
    except Exception as e:
        print(f"Error getting active executions: {e}")
        return []


def get_active_executions_for_plan(plan_id: str) -> List[Dict]:
    """
    Get all active executions for a specific Recovery Plan.

    Used for conflict detection when creating/updating Recovery Plans
    or starting new executions.

    Queries the EXECUTION_HISTORY_TABLE using PlanIdIndex GSI if available,
    falls back to scan if GSI doesn't exist. Filters by ACTIVE_EXECUTION_STATUSES.

    Args:
        plan_id: Recovery Plan ID

    Returns:
        List of active execution dicts with executionId, status, startTime, etc.
        Empty list if no active executions or on error.

    Example:
        >>> executions = get_active_executions_for_plan("plan-123")
        >>> len(executions)
        2
        >>> executions[0]['status']
        'IN_PROGRESS'
    """
    try:
        if not get_execution_history_table():
            print("EXECUTION_HISTORY_TABLE not configured")
            return []

        # Try PlanIdIndex GSI first
        try:
            result = get_execution_history_table().query(
                IndexName="PlanIdIndex",
                KeyConditionExpression=Key("planId").eq(plan_id),
            )
            executions = result.get("Items", [])

            # Filter by active statuses
            active_executions = [e for e in executions if e.get("status", "").upper() in ACTIVE_EXECUTION_STATUSES]

            return active_executions

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in [
                "ValidationException",
                "ResourceNotFoundException",
            ]:
                print(f"PlanIdIndex GSI not available: {error_code}, falling back to scan")
                # Fallback to scan
                result = get_execution_history_table().scan()
                all_executions = result.get("Items", [])

                # Filter by plan ID and active status
                active_executions = [
                    e
                    for e in all_executions
                    if e.get("planId") == plan_id and e.get("status", "").upper() in ACTIVE_EXECUTION_STATUSES
                ]

                return active_executions
            else:
                raise

    except Exception as e:
        print(f"Error getting active executions for plan {plan_id}: {e}")
        return []


def query_drs_servers_by_tags(region: str, tags: Dict[str, str], account_context: Optional[Dict] = None) -> List[Dict]:
    """
    Query DRS source servers that have ALL specified tags.
    Uses AND logic - DRS source server must have all tags to be included.

    Args:
        region: AWS region to query
        tags: Dictionary of tag key-value pairs to match
        account_context: Optional dict with AccountId and AssumeRoleName for cross-account access

    Returns:
        List of matching DRS source servers
    """
    try:
        regional_drs = create_drs_client(region, account_context)

        # Get all source servers in the region
        all_servers = []
        paginator = regional_drs.get_paginator("describe_source_servers")

        for page in paginator.paginate():
            all_servers.extend(page.get("items", []))

        if not all_servers:
            return []

        # Filter servers that match ALL specified tags
        matching_servers = []

        for server in all_servers:
            # Get DRS source server tags directly from server object
            drs_tags = server.get("tags", {})

            # Check if DRS server has ALL required tags with matching values
            matches_all = True
            for tag_key, tag_value in tags.items():
                # Normalize tag key and value (strip whitespace, case-insensitive)
                normalized_required_key = tag_key.strip()
                normalized_required_value = tag_value.strip().lower()

                # Check if any DRS tag matches (case-insensitive)
                found_match = False
                for drs_key, drs_value in drs_tags.items():
                    normalized_drs_key = drs_key.strip()
                    normalized_drs_value = drs_value.strip().lower()

                    if (
                        normalized_drs_key == normalized_required_key
                        and normalized_drs_value == normalized_required_value
                    ):
                        found_match = True
                        break

                if not found_match:
                    matches_all = False
                    break

            if matches_all:
                matching_servers.append(server)

        return matching_servers

    except Exception as e:
        print(f"Error querying DRS servers by tags in {region}: {e}")
        return []


def resolve_pg_servers_for_conflict_check(
    pg_id: str, pg_cache: Dict, account_context: Optional[Dict] = None
) -> List[str]:
    """
    Resolve Protection Group to server IDs for conflict detection.

    Handles both selection methods:
    - Tag-based: Queries DRS API with serverSelectionTags
    - Explicit: Uses sourceServerIds list directly

    Uses cache to avoid repeated DRS API calls for same Protection Group.

    Args:
        pg_id: Protection Group ID to resolve
        pg_cache: Cache dict to store resolved server IDs
        account_context: Optional cross-account context

    Returns:
        List of DRS source server IDs
    """
    if pg_id in pg_cache:
        return pg_cache[pg_id]

    try:
        pg_result = get_protection_groups_table().get_item(Key={"groupId": pg_id})
        pg = pg_result.get("Item", {})

        if not pg:
            pg_cache[pg_id] = []
            return []

        region = pg.get("region", "us-east-1")
        selection_tags = pg.get("serverSelectionTags", {})
        source_server_ids = pg.get("sourceServerIds", [])

        # Extract account context from Protection Group if not provided
        if not account_context and pg.get("accountId"):
            account_context = {
                "accountId": pg.get("accountId"),
                "assumeRoleName": pg.get("assumeRoleName"),
                "externalId": pg.get("externalId"),
            }

        if selection_tags:
            # Resolve servers by tags
            resolved = query_drs_servers_by_tags(region, selection_tags, account_context)
            server_ids = [s.get("sourceServerID") for s in resolved if s.get("sourceServerID")]
        elif source_server_ids:
            # Use explicit server IDs
            server_ids = source_server_ids
        else:
            server_ids = []

        pg_cache[pg_id] = server_ids
        return server_ids

    except Exception as e:
        print(f"Error resolving PG {pg_id} for conflict check: {e}")
        pg_cache[pg_id] = []
        return []


def get_servers_in_active_drs_jobs(region: str, account_context: Optional[Dict] = None) -> Dict[str, Dict]:
    """
    Query DRS API for servers in active LAUNCH jobs to detect conflicts.

    This provides real-time conflict detection beyond DynamoDB execution records,
    catching cases where execution records are stale or failed to update.

    Only checks LAUNCH jobs (not TERMINATE, CREATE_CONVERTED_SNAPSHOT, etc.)
    with PENDING or STARTED status.

    Args:
        region: AWS region to query
        account_context: Optional cross-account context for hub-and-spoke operations

    Returns:
        Dict mapping sourceServerId -> {jobId, jobStatus, jobType, launchStatus}
    """
    servers_in_drs_jobs = {}

    try:
        # Get DRS client for the appropriate account/region
        drs_client = create_drs_client(region, account_context)
        print(f"[DRS Job Check] Querying DRS jobs in region {region}")

        # Get all jobs (no filter = all jobs)
        jobs_response = drs_client.describe_jobs(maxResults=100)

        jobs_found = jobs_response.get("items", [])
        print(f"[DRS Job Check] Found {len(jobs_found)} total jobs in {region}")

        for job in jobs_found:
            job_id = job.get("jobID")
            job_status = job.get("status", "")
            job_type = job.get("type", "")

            print(f"[DRS Job Check] Job {job_id}: type={job_type}, status={job_status}")

            # Only check active LAUNCH jobs (not TERMINATE, CREATE_CONVERTED_SNAPSHOT, etc.)
            if job_type == "LAUNCH" and job_status in DRS_ACTIVE_JOB_STATUSES:
                # Get servers participating in this job
                for server in job.get("participatingServers", []):
                    server_id = server.get("sourceServerID")
                    if server_id:
                        servers_in_drs_jobs[server_id] = {
                            "jobId": job_id,
                            "jobStatus": job_status,
                            "jobType": job_type,
                            "launchStatus": server.get("launchStatus", "UNKNOWN"),
                        }
                        print(f"[DRS Job Check] Server {server_id} in active job {job_id}")

        print(f"[DRS Job Check] Found {len(servers_in_drs_jobs)} servers in active DRS jobs in {region}")
        return servers_in_drs_jobs

    except Exception as e:
        print(f"[DRS Job Check] Error checking DRS jobs in {region}: {e}")
        import traceback

        traceback.print_exc()
        return {}


def get_servers_in_active_executions() -> Dict[str, Dict]:  # noqa: C901
    """
    Get all servers currently in active DR executions across all Recovery Plans.

    Resolves servers from two sources:
    1. ServerStatuses in execution waves (already resolved servers)
    2. Protection Group definitions (for PAUSED/PENDING executions)

    For tag-based Protection Groups, resolves servers at check time by querying
    DRS API with selection tags.

    Returns:
        Dict mapping sourceServerId -> {executionId, planId, waveName, status}
    """
    active_executions = get_all_active_executions()
    servers_in_use = {}

    # Cache for recovery plans and protection groups
    plan_cache = {}
    pg_cache = {}

    for execution in active_executions:
        execution_id = execution.get("executionId")
        plan_id = execution.get("planId")
        exec_status = execution.get("status", "").upper()

        # First, check ServerStatuses in execution waves (already resolved servers)
        for wave in execution.get("waves", []):
            wave_name = wave.get("waveName", "Unknown")

            for server in wave.get("serverStatuses", []):
                server_id = server.get("sourceServerId")
                launch_status = server.get("launchStatus", "")
                # Track servers not yet launched
                if server_id and launch_status.upper() not in [
                    "LAUNCHED",
                    "FAILED",
                    "TERMINATED",
                ]:
                    servers_in_use[server_id] = {
                        "executionId": execution_id,
                        "planId": plan_id,
                        "waveName": wave_name,
                        "launchStatus": launch_status,
                        "executionStatus": exec_status,
                    }

        # For ALL active executions, resolve servers from the recovery plan's protection groups
        if plan_id not in plan_cache:
            try:
                plan_result = get_recovery_plans_table().get_item(Key={"planId": plan_id})
                plan_cache[plan_id] = plan_result.get("Item", {})
            except Exception as e:
                print(f"Error fetching plan {plan_id}: {e}")
                plan_cache[plan_id] = {}

        plan = plan_cache.get(plan_id, {})
        current_wave = execution.get("currentWave", 1)

        # Convert Decimal to int if needed
        if hasattr(current_wave, "__int__"):
            current_wave = int(current_wave)

        # Get execution waves to check their status
        execution_waves = {w.get("waveNumber"): w for w in execution.get("waves", [])}

        # Only consider waves that are not CANCELLED
        for idx, wave in enumerate(plan.get("waves", []), start=1):
            wave_name = wave.get("waveName", f"Wave {idx}")

            # Check if this wave is CANCELLED in the execution
            exec_wave = execution_waves.get(idx - 1)  # waveNumber is 0-indexed
            if exec_wave:
                wave_status = exec_wave.get("status", "").upper()
                if wave_status == "CANCELLED":
                    continue

            # Get Protection Group ID for this wave
            pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]

            if pg_id:
                # Resolve servers from Protection Group (handles both tags and explicit IDs)
                server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache)
                for server_id in server_ids:
                    # Only add if not already tracked (ServerStatuses takes precedence)
                    if server_id not in servers_in_use:
                        servers_in_use[server_id] = {
                            "executionId": execution_id,
                            "planId": plan_id,
                            "waveName": wave_name,
                            "waveStatus": (exec_wave.get("status", "PENDING") if exec_wave else "PENDING"),
                            "executionStatus": exec_status,
                        }

    return servers_in_use


def check_concurrent_jobs_limit(region: str, account_context: Optional[Dict] = None) -> Dict:
    """
    Check if starting a new job would exceed 20 concurrent jobs limit.

    DRS Service Quota: Max 20 concurrent jobs in progress (not adjustable)

    Args:
        region: AWS region to check
        account_context: Optional cross-account context

    Returns:
        Dict with:
        - canStartJob: Boolean, True if < 20 active jobs
        - currentJobs: Number of active jobs
        - maxJobs: 20 (DRS limit)
        - availableSlots: Remaining job slots
        - activeJobIds: List of active job IDs
    """
    try:
        drs_client = create_drs_client(region, account_context)
        jobs_response = drs_client.describe_jobs(maxResults=100)

        active_jobs = [j for j in jobs_response.get("items", []) if j.get("status") in DRS_ACTIVE_JOB_STATUSES]

        current_count = len(active_jobs)
        max_jobs = 20

        return {
            "canStartJob": current_count < max_jobs,
            "currentJobs": current_count,
            "maxJobs": max_jobs,
            "availableSlots": max_jobs - current_count,
            "activeJobIds": [j.get("jobID") for j in active_jobs],
        }

    except Exception as e:
        print(f"Error checking concurrent jobs limit in {region}: {e}")
        # Return permissive result on error
        return {
            "canStartJob": True,
            "currentJobs": 0,
            "maxJobs": 20,
            "availableSlots": 20,
            "error": str(e),
        }


def validate_wave_server_count(wave: Dict, pg_cache: Dict, account_context: Optional[Dict] = None) -> Dict:
    """
    Validate wave doesn't exceed 100 servers per job limit.

    DRS Service Quota: Max 100 source servers in a single job (not adjustable)

    Args:
        wave: Wave dict with protectionGroupId
        pg_cache: Cache for Protection Group server resolution
        account_context: Optional cross-account context

    Returns:
        Dict with:
        - valid: Boolean, True if ≤ 100 servers
        - serverCount: Number of servers in wave
        - maxServers: 100 (DRS limit)
        - message: Validation message
    """
    try:
        pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]

        if not pg_id:
            return {
                "valid": True,
                "serverCount": 0,
                "maxServers": 100,
                "message": "No Protection Group specified",
            }

        server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache, account_context)
        server_count = len(server_ids)
        max_servers = 100

        return {
            "valid": server_count <= max_servers,
            "serverCount": server_count,
            "maxServers": max_servers,
            "message": (
                f"Wave has {server_count} servers"
                if server_count <= max_servers
                else f"Wave has {server_count} servers (exceeds max {max_servers})"
            ),
        }

    except Exception as e:
        print(f"Error validating wave server count: {e}")
        return {
            "valid": False,
            "serverCount": 0,
            "maxServers": 100,
            "message": f"Error validating: {str(e)}",
            "error": str(e),
        }


def check_total_servers_in_jobs_limit(
    region: str,
    new_server_count: int,
    account_context: Optional[Dict] = None,
) -> Dict:
    """
    Check if adding servers would exceed 500 total servers in jobs limit.

    DRS Service Quota: Max 500 source servers across all jobs (not adjustable)

    Args:
        region: AWS region to check
        new_server_count: Number of servers to add
        account_context: Optional cross-account context

    Returns:
        Dict with:
        - valid: Boolean, True if total ≤ 500
        - currentServers: Servers in active jobs now
        - newServers: Servers to add
        - totalAfter: Total after adding new servers
        - maxServers: 500 (DRS limit)
        - availableSlots: Remaining capacity
    """
    try:
        servers_in_jobs = get_servers_in_active_drs_jobs(region, account_context)
        current_total = len(servers_in_jobs)
        total_after = current_total + new_server_count
        max_servers = 500

        return {
            "valid": total_after <= max_servers,
            "currentServers": current_total,
            "newServers": new_server_count,
            "totalAfter": total_after,
            "maxServers": max_servers,
            "availableSlots": max_servers - current_total,
        }

    except Exception as e:
        print(f"Error checking total servers in jobs limit in {region}: {e}")
        # Return permissive result on error
        return {
            "valid": True,
            "currentServers": 0,
            "newServers": new_server_count,
            "totalAfter": new_server_count,
            "maxServers": 500,
            "availableSlots": 500,
            "error": str(e),
        }


def check_server_conflicts(plan: Dict, account_context: Optional[Dict] = None) -> List[Dict]:
    """
    Validate no servers in Recovery Plan are in active executions or DRS jobs.
    Also validates DRS job-level quotas (20 concurrent, 100 per job, 500 total).

    DUAL-SOURCE VALIDATION:
    1. DynamoDB execution records (fast, may be slightly stale)
       - Queries StatusIndex for PENDING, POLLING, RUNNING, etc.
       - Extracts servers from wave serverStatuses
    2. Live DRS API job queries (authoritative, real-time)
       - Queries DescribeJobs for PENDING, STARTED jobs
       - Detects jobs started outside orchestration

    DRS JOB QUOTA VALIDATION:
    3. Concurrent jobs limit (20 max)
    4. Servers per job limit (100 max per wave)
    5. Total servers in jobs limit (500 max across all jobs)

    WHY DUAL-SOURCE: DynamoDB may be stale if job started externally.
    DRS API is authoritative but slower. Checking both ensures accuracy.

    RESOLUTION LOGIC:
    - Tag-based Protection Groups: Queries DRS API for matching servers
    - Explicit Protection Groups: Uses sourceServerIds list
    - Caches Protection Group lookups per region

    USAGE:
        conflicts = check_server_conflicts(recovery_plan, account_context)
        if conflicts:
            return response(409, {
                "error": "SERVER_CONFLICT",
                "message": f"{len(conflicts)} server(s) in use",
                "conflicts": conflicts,
                "conflictingExecutions": [...],
                "conflictingDrsJobs": [...],
                "quotaViolations": [...]
            })

    Args:
        plan: Recovery Plan dict with waves array
        account_context: Optional {accountId, assumeRoleName} for cross-account

    Returns:
        List of conflict dicts (empty if no conflicts):
        [
            {
                "serverId": "s-123",
                "conflictSource": "execution",  # or "drs_job" or "quota_violation"
                "conflictingExecutionId": "uuid",
                "conflictingPlanId": "uuid",
                "conflictingWave": "DatabaseWave",
                "conflictingJobId": "job-456",  # if drs_job source
                "conflictingJobStatus": "STARTED",  # if drs_job source
                "quotaType": "concurrent_jobs",  # if quota_violation
                "quotaMessage": "..."  # if quota_violation
            }
        ]
    """
    print(f"[Conflict Check] Starting conflict check for plan {plan.get('planId')}")
    print(f"[Conflict Check] Account context: {account_context}")

    servers_in_use = get_servers_in_active_executions()
    print(f"[Conflict Check] Servers in active executions: {list(servers_in_use.keys())}")

    conflicts = []
    pg_cache = {}
    checked_regions = set()
    drs_servers_by_region = {}
    quota_violations = []

    # Calculate total servers across all waves for quota validation
    total_plan_servers = 0

    for wave in plan.get("waves", []):
        wave_name = wave.get("waveName", "Unknown")

        # Get Protection Group ID for this wave
        pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]
        print(f"[Conflict Check] Wave '{wave_name}' has PG: {pg_id}")

        if pg_id:
            # Get PG to find region
            pg_metadata = {}
            try:
                pg_result = get_protection_groups_table().get_item(Key={"groupId": pg_id})
                pg_metadata = pg_result.get("Item", {})
            except Exception as e:
                print(f"[Conflict Check] Error fetching PG {pg_id}: {e}")

            region = pg_metadata.get("region", "us-east-1")
            print(f"[Conflict Check] PG {pg_id} is in region {region}")

            # QUOTA CHECK 1: Validate wave doesn't exceed 100 servers per job
            wave_validation = validate_wave_server_count(wave, pg_cache, account_context)
            if not wave_validation["valid"]:
                print(f"[Conflict Check] Wave '{wave_name}' exceeds 100 servers per job limit")
                quota_violations.append(
                    {
                        "quotaType": "servers_per_job",
                        "waveName": wave_name,
                        "serverCount": wave_validation["serverCount"],
                        "maxServers": wave_validation["maxServers"],
                        "message": wave_validation["message"],
                        "conflictSource": "quota_violation",
                    }
                )

            # Accumulate total servers for cross-wave quota check
            total_plan_servers += wave_validation.get("serverCount", 0)

            # Check DRS jobs for this region (once per region)
            if region not in checked_regions:
                checked_regions.add(region)
                print(f"[Conflict Check] Checking DRS jobs in region {region}")

                # QUOTA CHECK 2: Check concurrent jobs limit (20 max)
                concurrent_jobs_check = check_concurrent_jobs_limit(region, account_context)
                if not concurrent_jobs_check["canStartJob"]:
                    print(f"[Conflict Check] Region {region} at concurrent jobs limit")
                    quota_violations.append(
                        {
                            "quotaType": "concurrent_jobs",
                            "region": region,
                            "currentJobs": concurrent_jobs_check["currentJobs"],
                            "maxJobs": concurrent_jobs_check["maxJobs"],
                            "message": f"Cannot start new job - {concurrent_jobs_check['currentJobs']}/20 concurrent jobs active",  # noqa: E501
                            "conflictSource": "quota_violation",
                        }
                    )

                drs_servers_by_region[region] = get_servers_in_active_drs_jobs(region, account_context)
                print(f"[Conflict Check] DRS servers in {region}: {list(drs_servers_by_region[region].keys())}")

            # Resolve servers from Protection Group tags
            server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache, account_context)
            print(f"[Conflict Check] Resolved {len(server_ids)} servers from PG {pg_id}: {server_ids}")

            for server_id in server_ids:
                # Check DynamoDB execution conflicts
                if server_id in servers_in_use:
                    conflict_info = servers_in_use[server_id]
                    print(f"[Conflict Check] Server {server_id} has execution conflict")
                    conflicts.append(
                        {
                            "serverId": server_id,
                            "waveName": wave_name,
                            "conflictingExecutionId": conflict_info["executionId"],
                            "conflictingPlanId": conflict_info["planId"],
                            "conflictingWaveName": conflict_info.get("waveName"),
                            "conflictingStatus": conflict_info.get("executionStatus"),
                            "conflictSource": "execution",
                        }
                    )
                # Check DRS job conflicts (even if not in DynamoDB)
                elif server_id in drs_servers_by_region.get(region, {}):
                    drs_info = drs_servers_by_region[region][server_id]
                    print(f"[Conflict Check] Server {server_id} has DRS job conflict: {drs_info['jobId']}")
                    conflicts.append(
                        {
                            "serverId": server_id,
                            "waveName": wave_name,
                            "conflictingJobId": drs_info["jobId"],
                            "conflictingJobStatus": drs_info["jobStatus"],
                            "conflictingLaunchStatus": drs_info.get("launchStatus"),
                            "conflictSource": "drs_job",
                        }
                    )

    # QUOTA CHECK 3: Validate total servers across all jobs doesn't exceed 500
    # Check each region that was touched
    for region in checked_regions:
        total_servers_check = check_total_servers_in_jobs_limit(region, total_plan_servers, account_context)
        if not total_servers_check["valid"]:
            print(f"[Conflict Check] Region {region} would exceed 500 total servers in jobs")
            quota_violations.append(
                {
                    "quotaType": "total_servers_in_jobs",
                    "region": region,
                    "currentServers": total_servers_check["currentServers"],
                    "newServers": total_servers_check["newServers"],
                    "totalAfter": total_servers_check["totalAfter"],
                    "maxServers": total_servers_check["maxServers"],
                    "message": f"Would exceed 500 servers in jobs ({total_servers_check['totalAfter']}/500)",
                    "conflictSource": "quota_violation",
                }
            )

    # Combine server conflicts and quota violations
    all_conflicts = conflicts + quota_violations

    print(f"[Conflict Check] Total conflicts found: {len(conflicts)}, quota violations: {len(quota_violations)}")
    return all_conflicts


def check_server_conflicts_for_create(server_ids: List[str]) -> List[Dict]:
    """Check if any servers are already assigned to other Protection Groups"""
    conflicts = []

    # Scan all PGs
    pg_response = get_protection_groups_table().scan()
    all_pgs = pg_response.get("Items", [])

    while "LastEvaluatedKey" in pg_response:
        pg_response = get_protection_groups_table().scan(ExclusiveStartKey=pg_response["LastEvaluatedKey"])
        all_pgs.extend(pg_response.get("Items", []))

    for pg in all_pgs:
        existing_servers = pg.get("sourceServerIds", [])
        if not existing_servers:
            continue

        for server_id in server_ids:
            if server_id in existing_servers:
                conflicts.append(
                    {
                        "serverId": server_id,
                        "protectionGroupId": pg.get("groupId"),
                        "protectionGroupName": pg.get("groupName"),
                    }
                )

    return conflicts


def check_server_conflicts_for_update(server_ids: List[str], current_pg_id: str) -> List[Dict]:
    """Check if any servers are already assigned to other Protection Groups (excluding current)"""
    conflicts = []

    # Scan all PGs
    pg_response = get_protection_groups_table().scan()
    all_pgs = pg_response.get("Items", [])

    while "LastEvaluatedKey" in pg_response:
        pg_response = get_protection_groups_table().scan(ExclusiveStartKey=pg_response["LastEvaluatedKey"])
        all_pgs.extend(pg_response.get("Items", []))

    for pg in all_pgs:
        # Skip current PG
        if pg.get("groupId") == current_pg_id:
            continue

        existing_servers = pg.get("sourceServerIds", [])
        if not existing_servers:
            continue

        for server_id in server_ids:
            if server_id in existing_servers:
                conflicts.append(
                    {
                        "serverId": server_id,
                        "protectionGroupId": pg.get("groupId"),
                        "protectionGroupName": pg.get("groupName"),
                    }
                )

    return conflicts


def get_plans_with_conflicts() -> Dict[str, Dict]:  # noqa: C901
    """
    Get all recovery plans that have server conflicts with OTHER plans' active executions OR active DRS jobs.
    Returns dict mapping plan_id -> conflict info for plans that cannot be executed.

    IMPORTANT: This function is for CONFLICT DETECTION (blocking new executions), NOT for determining
    if a plan is "In Progress". A plan's own active execution is NOT a conflict.

    This is used by the frontend to gray out Drill/Recovery buttons when servers are in use by OTHER plans.
    For tag-based Protection Groups, resolves servers at check time.
    Also checks DRS directly for active LAUNCH jobs.
    """
    servers_in_use = get_servers_in_active_executions()

    # Also get servers in active DRS jobs (per region, cached)
    drs_servers_by_region = {}

    if not servers_in_use and not drs_servers_by_region:
        # Will populate drs_servers_by_region lazily per region below
        pass

    # Get all recovery plans
    try:
        result = get_recovery_plans_table().scan()
        all_plans = result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in result:
            result = get_recovery_plans_table().scan(ExclusiveStartKey=result["LastEvaluatedKey"])
            all_plans.extend(result.get("Items", []))
    except Exception as e:
        print(f"Error fetching plans for conflict check: {e}")
        return {}

    plans_with_conflicts = {}
    pg_cache = {}

    for plan in all_plans:
        plan_id = plan.get("planId")

        # Check if this plan has any servers in active executions FROM OTHER PLANS
        conflicting_servers = []
        conflicting_execution_id = None
        conflicting_plan_id = None
        conflicting_status = None

        for wave in plan.get("waves", []):
            # Get Protection Group ID for this wave
            pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]

            if pg_id:
                # Resolve servers from Protection Group tags
                server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache)

                for server_id in server_ids:
                    if server_id in servers_in_use:
                        conflict_info = servers_in_use[server_id]
                        # CRITICAL: Only count as conflict if it's ANOTHER plan's execution
                        # A plan's own active execution is NOT a conflict - it just means the plan is running
                        if conflict_info["planId"] != plan_id:
                            conflicting_servers.append(server_id)
                            conflicting_execution_id = conflict_info["executionId"]
                            conflicting_plan_id = conflict_info["planId"]
                            conflicting_status = conflict_info.get("executionStatus")

        # Also check DRS jobs for this plan's regions
        drs_conflicting_servers = []
        drs_conflicting_job_id = None
        pg_metadata_cache = {}  # Separate cache for PG metadata (region, etc.)

        for wave in plan.get("waves", []):
            pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]
            if pg_id:
                # Get PG metadata (region) - use separate cache since pg_cache stores server IDs
                if pg_id not in pg_metadata_cache:
                    try:
                        pg_result = get_protection_groups_table().get_item(Key={"groupId": pg_id})
                        pg_metadata_cache[pg_id] = pg_result.get("Item", {})
                    except Exception:
                        pg_metadata_cache[pg_id] = {}

                pg_metadata = pg_metadata_cache.get(pg_id, {})
                region = pg_metadata.get("region", "us-east-1")

                # Lazy load DRS jobs per region
                if region not in drs_servers_by_region:
                    drs_servers_by_region[region] = get_servers_in_active_drs_jobs(region)

                server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache)
                for server_id in server_ids:
                    # Skip if already in execution conflict
                    if server_id not in conflicting_servers and server_id in drs_servers_by_region.get(region, {}):
                        drs_info = drs_servers_by_region[region][server_id]
                        drs_conflicting_servers.append(server_id)
                        drs_conflicting_job_id = drs_info["jobId"]

        all_conflicting = list(set(conflicting_servers + drs_conflicting_servers))

        if all_conflicting:
            # Build reason message
            if conflicting_servers and drs_conflicting_servers:
                reason = f"{len(set(conflicting_servers))} server(s) in execution, {len(set(drs_conflicting_servers))} in DRS jobs"  # noqa: E501
            elif drs_conflicting_servers:
                reason = f"{len(set(drs_conflicting_servers))} server(s) being processed by DRS job {drs_conflicting_job_id}"  # noqa: E501
            else:
                reason = f"{len(set(conflicting_servers))} server(s) in use by another execution"

            plans_with_conflicts[plan_id] = {
                "hasConflict": True,
                "conflictingServers": all_conflicting,
                "conflictingExecutionId": conflicting_execution_id,
                "conflictingPlanId": conflicting_plan_id,
                "conflictingStatus": conflicting_status,
                "conflictingDrsJobId": drs_conflicting_job_id,
                "reason": reason,
            }

    return plans_with_conflicts


def has_circular_dependencies(graph: Dict[str, List[str]]) -> bool:
    """Check for circular dependencies using DFS"""
    visited = set()
    rec_stack = set()

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if dfs(node):
                return True

    return False


def get_shared_protection_groups() -> Dict[str, Dict]:
    """
    Detect Protection Groups that are used by multiple Recovery Plans.

    This is a WARNING indicator, not a blocking condition. Shared PGs are allowed
    but users should be aware that:
    - Only ONE plan using the shared PG can execute at a time
    - Starting execution on one plan blocks all other plans sharing the PG

    Returns:
        Dict mapping pg_id -> {
            "protectionGroupId": str,
            "protectionGroupName": str,
            "usedByPlans": [{"planId": str, "planName": str}, ...],
            "serverCount": int,
            "warning": str
        }
    """
    # Get all recovery plans
    try:
        result = get_recovery_plans_table().scan()
        all_plans = result.get("Items", [])

        while "LastEvaluatedKey" in result:
            result = get_recovery_plans_table().scan(ExclusiveStartKey=result["LastEvaluatedKey"])
            all_plans.extend(result.get("Items", []))
    except Exception as e:
        print(f"Error fetching plans for shared PG check: {e}")
        return {}

    # Build map of PG -> plans that use it
    pg_to_plans: Dict[str, List[Dict]] = {}

    for plan in all_plans:
        plan_id = plan.get("planId")
        plan_name = plan.get("planName", "Unnamed Plan")

        for wave in plan.get("waves", []):
            pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]

            if pg_id:
                if pg_id not in pg_to_plans:
                    pg_to_plans[pg_id] = []

                # Avoid duplicates (same plan might use same PG in multiple waves)
                if not any(p["planId"] == plan_id for p in pg_to_plans[pg_id]):
                    pg_to_plans[pg_id].append({"planId": plan_id, "planName": plan_name})

    # Filter to only PGs used by multiple plans
    shared_pgs = {}

    for pg_id, plans in pg_to_plans.items():
        if len(plans) > 1:
            # Get PG details
            try:
                pg_result = get_protection_groups_table().get_item(Key={"groupId": pg_id})
                pg = pg_result.get("Item", {})
                pg_name = pg.get("groupName", "Unknown")
                server_count = len(pg.get("sourceServerIds", []))

                # For tag-based PGs, we'd need to resolve - use cached count if available
                if pg.get("selectionType") == "tags":
                    # Approximate - actual count resolved at execution time
                    server_count = pg.get("cachedServerCount", 0)

            except Exception:
                pg_name = "Unknown"
                server_count = 0

            plan_names = [p["planName"] for p in plans]
            shared_pgs[pg_id] = {
                "protectionGroupId": pg_id,
                "protectionGroupName": pg_name,
                "usedByPlans": plans,
                "planCount": len(plans),
                "serverCount": server_count,
                "warning": f"Protection Group '{pg_name}' is used by {len(plans)} plans: {', '.join(plan_names)}. Only one can execute at a time.",  # noqa: E501
            }

    return shared_pgs


def get_plan_shared_pg_warnings(plan_id: str) -> List[Dict]:
    """
    Get warnings for a specific plan about shared Protection Groups.

    Returns list of warnings if any PGs in this plan are shared with other plans.
    """
    shared_pgs = get_shared_protection_groups()

    warnings = []
    for pg_id, pg_info in shared_pgs.items():
        # Check if this plan uses this shared PG
        if any(p["planId"] == plan_id for p in pg_info["usedByPlans"]):
            other_plans = [p for p in pg_info["usedByPlans"] if p["planId"] != plan_id]
            if other_plans:
                other_plan_names = [p["planName"] for p in other_plans]
                warnings.append(
                    {
                        "type": "SHARED_PROTECTION_GROUP",
                        "protectionGroupId": pg_id,
                        "protectionGroupName": pg_info["protectionGroupName"],
                        "sharedWithPlans": other_plans,
                        "message": f"Protection Group '{pg_info['protectionGroupName']}' is also used by: {', '.join(other_plan_names)}",  # noqa: E501
                    }
                )

    return warnings
