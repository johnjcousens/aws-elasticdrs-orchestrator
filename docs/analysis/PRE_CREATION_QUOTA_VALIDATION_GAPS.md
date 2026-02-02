# Pre-Creation Quota Validation Gaps Analysis

**Date**: February 1, 2026  
**Status**: ❌ **CRITICAL GAPS IDENTIFIED**

## Executive Summary

The data management handler **DOES NOT** validate DRS service quotas when creating Protection Groups and Recovery Plans. This allows users to create configurations that will fail at execution time.

## Current State

### Protection Group Creation (`create_protection_group`)

**What IS Validated** ✅:
- Unique name (case-insensitive)
- Required fields (groupName, region)
- Server existence in DRS
- Server conflicts (not assigned to other PGs)
- Tag conflicts (for tag-based selection)
- Name length (1-64 characters)

**What IS NOT Validated** ❌:
- ❌ **100 servers per job limit** - No check if tag-based or explicit selection exceeds 100 servers
- ❌ **Server replication health** - No validation that servers are in healthy replication state

**Impact**:
- Users can create Protection Groups with 150+ servers
- These PGs will fail when used in Recovery Plans
- Error only discovered at execution time

### Recovery Plan Creation (`create_recovery_plan`)

**What IS Validated** ✅:
- Unique name (case-insensitive)
- Required fields (name, waves)
- Wave configuration (no circular dependencies)
- Protection Group existence
- Name length (1-64 characters)

**What IS NOT Validated** ❌:
- ❌ **100 servers per wave** - No check if wave's Protection Group has >100 servers
- ❌ **500 total servers across all waves** - No check if plan would exceed 500 servers
- ❌ **20 concurrent jobs limit** - No check if plan could be blocked by active jobs
- ❌ **Server conflicts** - No check if servers are in active executions/jobs

**Impact**:
- Users can create Recovery Plans with waves containing 150+ servers
- Users can create plans with 10 waves × 100 servers = 1,000 total (exceeds 500 limit)
- Plans will fail at execution time with quota violations
- No warning about potential conflicts with active operations

## Detailed Gap Analysis

### Gap 1: Protection Group - 100 Servers Per Job

**Location**: `lambda/data-management-handler/index.py` - `create_protection_group()`

**Current Code**:
```python
# If using tags, check for tag conflicts with other PGs
if has_tags:
    tag_conflicts = check_tag_conflicts_for_create(selection_tags, region)
    if tag_conflicts:
        return response(409, {"error": "TAG_CONFLICT", ...})

# If using explicit server IDs, validate they exist
if has_servers:
    # Validate servers exist in DRS
    regional_drs = boto3.client("drs", region_name=region)
    drs_response = regional_drs.describe_source_servers(...)
    
    # Check for server conflicts with other PGs
    conflicts = check_server_conflicts_for_create(source_server_ids)
    if conflicts:
        return response(409, {"error": "SERVER_CONFLICT", ...})
```

**Missing Validation**:
```python
# MISSING: Validate server count doesn't exceed 100
if has_servers and len(source_server_ids) > 100:
    return response(400, {
        "error": "QUOTA_EXCEEDED",
        "quotaType": "servers_per_job",
        "message": "Protection Group cannot contain more than 100 servers",
        "serverCount": len(source_server_ids),
        "maxServers": 100,
        "limit": "DRS Service Quota: Max 100 servers per job"
    })

# MISSING: For tag-based, resolve and count servers
if has_tags:
    resolved = query_drs_servers_by_tags(region, selection_tags, account_context)
    server_count = len(resolved)
    if server_count > 100:
        return response(400, {
            "error": "QUOTA_EXCEEDED",
            "quotaType": "servers_per_job",
            "message": "Tag selection matches more than 100 servers",
            "serverCount": server_count,
            "maxServers": 100,
            "matchingServers": [s.get("sourceServerID") for s in resolved],
            "limit": "DRS Service Quota: Max 100 servers per job"
        })
```

### Gap 2: Recovery Plan - Wave Server Count

**Location**: `lambda/data-management-handler/index.py` - `validate_waves()`

**Current Code**:
```python
def validate_waves(waves: List[Dict]) -> Optional[str]:
    """Validate wave configuration - supports both single and multi-PG formats"""
    # Check for duplicate wave numbers
    # Check for circular dependencies
    # Validate required fields
    # NO SERVER COUNT VALIDATION
    return None  # No errors
```

**Missing Validation**:
```python
def validate_waves(waves: List[Dict]) -> Optional[str]:
    """Validate wave configuration including DRS quota limits"""
    
    # ... existing validations ...
    
    # NEW: Validate each wave doesn't exceed 100 servers per job
    pg_cache = {}
    for wave in waves:
        pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]
        if pg_id:
            # Import from conflict_detection
            from shared.conflict_detection import resolve_pg_servers_for_conflict_check
            
            server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache)
            if len(server_ids) > 100:
                wave_name = wave.get("waveName", f"Wave {wave.get('waveNumber', '?')}")
                return f"Wave '{wave_name}' contains {len(server_ids)} servers (max 100 per job)"
    
    return None
```

### Gap 3: Recovery Plan - Total Servers Across All Waves

**Location**: `lambda/data-management-handler/index.py` - `create_recovery_plan()`

**Current Code**:
```python
# Validate waves if provided
if waves:
    validation_error = validate_waves(camelcase_waves)
    if validation_error:
        return response(400, {"error": validation_error})

# Store in DynamoDB
recovery_plans_table.put_item(Item=item)
```

**Missing Validation**:
```python
# NEW: Validate total servers across all waves doesn't exceed 500
if waves:
    validation_error = validate_waves(camelcase_waves)
    if validation_error:
        return response(400, {"error": validation_error})
    
    # Calculate total servers across all waves
    pg_cache = {}
    total_servers = 0
    wave_server_counts = []
    
    for wave in camelcase_waves:
        pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]
        if pg_id:
            from shared.conflict_detection import resolve_pg_servers_for_conflict_check
            server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache)
            wave_count = len(server_ids)
            total_servers += wave_count
            wave_server_counts.append({
                "waveName": wave.get("waveName"),
                "serverCount": wave_count
            })
    
    if total_servers > 500:
        return response(400, {
            "error": "QUOTA_EXCEEDED",
            "quotaType": "total_servers_in_jobs",
            "message": f"Recovery Plan would launch {total_servers} servers (max 500 across all jobs)",
            "totalServers": total_servers,
            "maxServers": 500,
            "waveBreakdown": wave_server_counts,
            "limit": "DRS Service Quota: Max 500 servers across all concurrent jobs"
        })
```

### Gap 4: Recovery Plan - Concurrent Jobs Limit

**Location**: `lambda/data-management-handler/index.py` - `create_recovery_plan()`

**Missing Validation**:
```python
# NEW: Check if creating this plan would violate concurrent jobs limit
# This is a WARNING, not a hard block, since jobs may complete before this plan runs
from shared.conflict_detection import check_concurrent_jobs_limit

# Get region from first wave's Protection Group
first_wave = camelcase_waves[0] if camelcase_waves else {}
pg_id = first_wave.get("protectionGroupId") or (first_wave.get("protectionGroupIds", []) or [None])[0]

if pg_id:
    try:
        pg_result = protection_groups_table.get_item(Key={"groupId": pg_id})
        pg = pg_result.get("Item", {})
        region = pg.get("region", "us-east-1")
        
        # Check concurrent jobs limit
        jobs_check = check_concurrent_jobs_limit(region)
        if not jobs_check["canStartJob"]:
            # Return WARNING, not error (jobs may complete before plan runs)
            return response(200, {
                **item,
                "warning": {
                    "type": "CONCURRENT_JOBS_AT_LIMIT",
                    "message": f"Region {region} currently has {jobs_check['currentJobs']}/20 concurrent jobs active",
                    "recommendation": "Wait for active jobs to complete before executing this plan",
                    "currentJobs": jobs_check["currentJobs"],
                    "maxJobs": jobs_check["maxJobs"]
                }
            })
    except Exception as e:
        print(f"Warning: Could not check concurrent jobs limit: {e}")
```

### Gap 5: Recovery Plan - Server Conflicts

**Location**: `lambda/data-management-handler/index.py` - `create_recovery_plan()`

**Missing Validation**:
```python
# NEW: Check for server conflicts with active executions/jobs
from shared.conflict_detection import check_server_conflicts

# Build minimal plan structure for conflict check
conflict_check_plan = {
    "planId": plan_id,
    "planName": plan_name,
    "waves": camelcase_waves
}

conflicts = check_server_conflicts(conflict_check_plan)
if conflicts:
    # Return WARNING, not error (conflicts may resolve before plan runs)
    conflict_summary = {
        "execution_conflicts": len([c for c in conflicts if c.get("conflictSource") == "execution"]),
        "drs_job_conflicts": len([c for c in conflicts if c.get("conflictSource") == "drs_job"]),
        "quota_violations": len([c for c in conflicts if c.get("conflictSource") == "quota_violation"])
    }
    
    return response(200, {
        **item,
        "warning": {
            "type": "SERVER_CONFLICTS_DETECTED",
            "message": f"Some servers are currently in use by other operations",
            "recommendation": "Wait for active operations to complete before executing this plan",
            "conflicts": conflict_summary,
            "details": conflicts
        }
    })
```

## Recommended Implementation Priority

### Priority 1: CRITICAL (Block Creation) ⚠️

These validations should **BLOCK** creation because they represent hard DRS limits:

1. **Protection Group - 100 servers limit** ⚠️
   - Block if explicit server IDs > 100
   - Block if tag-based selection resolves to > 100 servers
   - Error code: `QUOTA_EXCEEDED`
   - HTTP Status: 400

2. **Recovery Plan - 100 servers per wave** ⚠️
   - Block if any wave's Protection Group has > 100 servers
   - Error code: `QUOTA_EXCEEDED`
   - HTTP Status: 400

3. **Recovery Plan - 500 total servers** ⚠️
   - Block if total servers across all waves > 500
   - Error code: `QUOTA_EXCEEDED`
   - HTTP Status: 400

### Priority 2: WARNING (Allow with Warning) ⚡

These validations should **WARN** but allow creation because conditions may change:

4. **Recovery Plan - Concurrent jobs limit** ⚡
   - Warn if region currently at 20 concurrent jobs
   - Return 200 with warning object
   - Jobs may complete before plan executes

5. **Recovery Plan - Server conflicts** ⚡
   - Warn if servers are in active executions/jobs
   - Return 200 with warning object
   - Conflicts may resolve before plan executes

## Implementation Files

### Files to Modify

1. **`lambda/data-management-handler/index.py`**
   - `create_protection_group()` - Add 100 server validation
   - `validate_waves()` - Add per-wave 100 server validation
   - `create_recovery_plan()` - Add total 500 server validation
   - `create_recovery_plan()` - Add concurrent jobs warning
   - `create_recovery_plan()` - Add server conflicts warning

2. **`lambda/shared/conflict_detection.py`**
   - Already has all needed functions:
     - `validate_wave_server_count()`
     - `check_total_servers_in_jobs_limit()`
     - `check_concurrent_jobs_limit()`
     - `check_server_conflicts()`
     - `resolve_pg_servers_for_conflict_check()`

### New Test Files Needed

1. **`tests/unit/test_protection_group_quota_validation.py`**
   - Test PG creation with > 100 explicit servers (should fail)
   - Test PG creation with tag selection > 100 servers (should fail)
   - Test PG creation with exactly 100 servers (should succeed)

2. **`tests/unit/test_recovery_plan_quota_validation.py`**
   - Test RP creation with wave > 100 servers (should fail)
   - Test RP creation with total > 500 servers (should fail)
   - Test RP creation with concurrent jobs at limit (should warn)
   - Test RP creation with server conflicts (should warn)

## Error Response Format

### Hard Block (400 Bad Request)

```json
{
  "error": "QUOTA_EXCEEDED",
  "quotaType": "servers_per_job",
  "message": "Protection Group cannot contain more than 100 servers",
  "serverCount": 150,
  "maxServers": 100,
  "limit": "DRS Service Quota: Max 100 servers per job (not adjustable)",
  "documentation": "https://docs.aws.amazon.com/general/latest/gr/drs.html"
}
```

### Warning (200 OK with warning)

```json
{
  "planId": "uuid",
  "planName": "Production DR Plan",
  "waves": [...],
  "warning": {
    "type": "CONCURRENT_JOBS_AT_LIMIT",
    "message": "Region us-east-1 currently has 20/20 concurrent jobs active",
    "recommendation": "Wait for active jobs to complete before executing this plan",
    "currentJobs": 20,
    "maxJobs": 20,
    "canExecuteNow": false
  }
}
```

## Frontend Impact

### Protection Group Dialog

**Current**: No validation feedback until execution

**Needed**:
- Show server count when selecting servers
- Show "X/100 servers selected" counter
- Disable "Create" button if > 100 servers
- Show error message: "Cannot exceed 100 servers per Protection Group"

### Recovery Plan Dialog

**Current**: No validation feedback until execution

**Needed**:
- Show server count per wave
- Show total server count across all waves
- Show "Total: X/500 servers" counter
- Disable "Create" button if any wave > 100 or total > 500
- Show warning icon if concurrent jobs at limit
- Show warning icon if server conflicts detected

## Related Documentation

- [Conflict Detection Validation Complete](CONFLICT_DETECTION_VALIDATION_COMPLETE.md)
- [DRS Service Quotas Complete](DRS_SERVICE_QUOTAS_COMPLETE.md)
- [DRS Service Limits and Capabilities](DRS_SERVICE_LIMITS_AND_CAPABILITIES.md)

## Conclusion

**Status**: ❌ **CRITICAL GAPS EXIST**

The data management handler lacks pre-creation quota validation, allowing users to create configurations that will fail at execution time. This creates a poor user experience and wastes time troubleshooting execution failures that could have been prevented at creation time.

**Recommendation**: Implement Priority 1 validations immediately to block creation of invalid configurations.
