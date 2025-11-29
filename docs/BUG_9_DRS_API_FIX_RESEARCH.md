# Bug 9: DRS API Compatibility Fix - Research & Solution

**Date**: November 28, 2025
**Session**: 57 Part 16
**Priority**: CRITICAL - All DRS operations broken

## Problem Summary

Bug 8 implementation added an invalid parameter `recoveryInstanceProperties` to the `start_recovery()` API call, causing all DRS recovery operations to fail with:
```
ParamValidationError: Unknown parameter in input: "recoveryInstanceProperties"
```

## AWS DRS API Research Findings

### 1. start_recovery() API (Confirmed from AWS Docs)

**Valid Parameters ONLY:**
```python
drs_client.start_recovery(
    isDrill=True|False,
    sourceServers=[
        {
            'sourceServerID': 'string',      # REQUIRED
            'recoverySnapshotID': 'string'   # OPTIONAL
        }
    ],
    tags={
        'string': 'string'
    }
)
```

**Key Finding**: `recoveryInstanceProperties` parameter **DOES NOT EXIST** in the DRS API.

### 2. update_launch_configuration() API (The Correct Approach)

**Purpose**: Pre-configure launch settings per source server
**When to Use**: BEFORE calling start_recovery()

**Valid Parameters:**
```python
drs_client.update_launch_configuration(
    sourceServerId='string',                               # REQUIRED
    copyPrivateIp=True|False,
    copyTags=True|False,
    launchDisposition='STOPPED'|'STARTED',
    targetInstanceTypeRightSizingMethod='BASIC'|'NONE'|'IN_AWS',
    licensing={
        'osByol': True|False
    },
    postLaunchEnabled=True|False,
    name='string'
)
```

### 3. DRS Launch Configuration Model

**How It Actually Works:**

1. **Pre-Configuration Phase** (Optional but recommended):
   - Use `update_launch_configuration()` to set per-server launch settings
   - Settings are stored persistently in DRS service
   - Each source server has its own launch configuration

2. **Recovery Execution Phase**:
   - Call `start_recovery()` with minimal parameters (just server IDs)
   - DRS automatically retrieves and applies stored launch configuration for each server
   - No need to pass launch settings at recovery time

3. **Configuration Persistence**:
   - Launch configurations persist in DRS service
   - Updated via Console UI or `update_launch_configuration()` API
   - Automatically applied during recovery/drill operations

## Root Cause Analysis

**Bug 8's Misconception:**
- Assumed launch configurations needed to be passed at recovery time
- Created invalid `recoveryInstanceProperties` parameter structure
- This parameter doesn't exist in DRS API

**Why Bug 8 Code Broke:**
```python
# INCORRECT - This parameter doesn't exist:
source_servers.append({
    'sourceServerID': server_id,
    'recoveryInstanceProperties': {  # ❌ INVALID
        'targetInstanceTypeRightSizingMethod': '...',
        'copyPrivateIp': True,
        'copyTags': True,
        'launchDisposition': '...'
    }
})
```

## Solution Design

### Option 1: Simple Fix (RECOMMENDED)
**Remove invalid parameter, rely on DRS stored configurations**

**Rationale:**
- Launch configurations are already stored per-server in DRS
- `get_server_launch_configurations()` confirms settings exist
- When `start_recovery()` is called, DRS uses stored settings automatically
- No explicit passing needed

**Implementation:**
```python
# CORRECT - Minimal parameters only:
source_servers.append({
    'sourceServerID': server_id,
    'recoverySnapshotID': snapshot_id  # Optional
})
```

### Option 2: Pre-Configuration Enhancement (Future)
**Add pre-configuration step before recovery**

**When Needed:**
- If we need to modify launch settings dynamically per wave
- If wave configurations should override server defaults
- If we want wave-specific launch behavior

**Implementation:**
```python
# 1. Pre-configure each server (optional):
for server in wave_servers:
    drs_client.update_launch_configuration(
        sourceServerId=server['id'],
        copyPrivateIp=config.get('copyPrivateIp'),
        launchDisposition=config.get('launchDisposition'),
        # etc.
    )

# 2. Then start recovery with stored settings:
drs_client.start_recovery(
    isDrill=is_drill,
    sourceServers=[
        {'sourceServerID': server['id']}
        for server in wave_servers
    ]
)
```

## Implementation Decision

**Choose Option 1 (Simple Fix) for Bug 9:**

**Reasons:**
1. ✅ Restores working functionality immediately
2. ✅ Launch configurations already exist in DRS per server
3. ✅ No additional API calls needed
4. ✅ Follows DRS API design patterns
5. ✅ Simple, clean, maintainable code

**Option 2 Enhancement** can be revisited in Phase 3 if dynamic per-wave launch configuration override is required.

## Code Changes Required

### File: lambda/index.py

**Function**: `start_drs_recovery_for_wave()` (lines 1050-1080)

**Before (BROKEN):**
```python
source_servers.append({
    'sourceServerID': server_id,
    'recoveryInstanceProperties': {  # ❌ INVALID
        'targetInstanceTypeRightSizingMethod': config.get('...'),
        'copyPrivateIp': config.get('...'),
        'copyTags': config.get('...'),
        'launchDisposition': config.get('...'),
        'bootMode': config.get('...')
    }
})
```

**After (FIXED):**
```python
source_servers.append({
    'sourceServerID': server_id
    # DRS will use stored launch configuration automatically
})
```

**Optional**: Add snapshot ID if needed:
```python
source_servers.append({
    'sourceServerID': server_id,
    'recoverySnapshotID': snapshot_id  # If specific PIT recovery needed
})
```

## Validation Plan

1. ✅ Remove invalid parameter from code
2. ✅ Validate Python syntax
3. ✅ Deploy Lambda function
4. ✅ Execute test recovery
5. ✅ Verify DRS job creation (JobId != null)
6. ✅ Confirm recovery instances launch
7. ✅ Validate launch configurations applied correctly

## Documentation Updates

- [x] Create this research document
- [ ] Update Bug 8 documentation with correct approach
- [ ] Update PROJECT_STATUS.md with resolution
- [ ] Create Bug 9 resolution commit

## References

**AWS Documentation:**
- [start-recovery API](https://docs.aws.amazon.com/cli/latest/reference/drs/start-recovery.html)
- [update-launch-configuration API](https://docs.aws.amazon.com/cli/latest/reference/drs/update-launch-configuration.html)
- [DRS Launch Settings Guide](https://docs.aws.amazon.com/drs/latest/userguide/launch-general-settings.html)

**Related Documents:**
- `docs/SESSION_57_PART_15_BUG_9_CRITICAL.md`
- `docs/BUG_8_DRS_LAUNCH_CONFIG_ENHANCEMENT.md`
- `lambda/index.py` (lines 1030-1110)

---

**Conclusion**: Bug 8's approach was fundamentally wrong due to misunderstanding of DRS API architecture. Launch configurations are pre-configured and stored per-server, not passed at recovery time. The fix is simple: remove the invalid parameter and let DRS use its stored configurations.
