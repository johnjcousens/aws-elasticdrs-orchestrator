# Session 57 Part 15: Bug 9 Critical Discovery

**Date**: November 28, 2025, 9:09-9:15 PM EST  
**Duration**: 6 minutes  
**Status**: 🚨 CRITICAL PRODUCTION BUG DISCOVERED

## Critical Bug Discovery

### Bug 9: DRS API Compatibility Broken by Bug 8 Implementation

**Severity**: CRITICAL - Blocks ALL recovery operations  
**Impact**: Production-breaking - No DRS jobs can be created

### The Problem

**What happened:**
1. User started test execution: "Full-Stack-DR-Drill"
2. UI showed "Polling" status with no DRS activity
3. Investigation revealed: JobId = null, Wave status = "PARTIAL"
4. Server status: "FAILED" with parameter validation error

**Root Cause:**
```
ParamValidationError: Parameter validation failed:
Unknown parameter in sourceServers[0]: "recoveryInstanceProperties", 
must be one of: recoverySnapshotID, sourceServerID
```

**What went wrong:**
- Bug 8 enhancement added `recoveryInstanceProperties` to `start_recovery()` call
- This parameter **does not exist** in the DRS API
- DRS API only accepts: `recoverySnapshotID`, `sourceServerID`
- The implementation was based on incorrect API assumptions

### Impact Analysis

**Production Impact:**
- ✅ All previous bugs (1-7): Still working correctly
- 🚨 Bug 8: **Completely broke DRS job creation**
- ❌ **ALL recovery operations fail** with parameter validation error
- ❌ System cannot start any DRS jobs (drill or recovery)

**What Still Works:**
- UI displays properly
- Execution history tracking
- Wave dependency logic
- Database operations
- Polling infrastructure

**What's Broken:**
- Starting any DRS recovery job
- Starting any DRS drill
- Bug 8 launch configuration enhancement
- All recovery operations

### Affected Code

**File**: `lambda/index.py`  
**Function**: `start_drs_recovery_for_wave()`  
**Lines**: 1050-1080 (Bug 8 implementation)

**Problematic Code:**
```python
# Build sourceServers with per-server configurations
source_servers = []
for server_id in wave_server_ids:
    server_config = {
        'sourceServerID': server_id
    }
    
    # Add per-server configuration if available
    if server_id in launch_configs:
        config = launch_configs[server_id]
        server_config['recoveryInstanceProperties'] = {  # ❌ INVALID PARAMETER
            'targetInstanceTypeRightSizingMethod': config.get('targetInstanceTypeRightSizingMethod'),
            'copyPrivateIp': config.get('copyPrivateIp'),
            # ... more invalid parameters
        }
    
    source_servers.append(server_config)
```

### The Correct Approach

**Research needed:**
1. Check actual DRS API documentation for `start_recovery()`
2. Determine correct method for applying per-server launch configurations
3. Options:
   - Pre-configure via `update_launch_configuration()` before recovery
   - Use different API call pattern
   - Apply configurations through different mechanism

**Likely Solution:**
Launch configurations must be set **before** calling `start_recovery()` using:
- `update_launch_configuration()` API call per server
- Apply settings before initiating recovery
- `start_recovery()` then uses pre-configured settings

### Investigation Results

**Database Record:**
```json
{
  "ExecutionId": "65071ffc-1920-47df-8f50-9d23f645ae6f",
  "Status": "POLLING",
  "StartTime": "1764382173",
  "ExecutionType": "DRILL",
  "FirstWave": {
    "WaveName": "Unknown",
    "Status": "PARTIAL",
    "JobId": null,  // ❌ No job created
    "Servers": 1,
    "ServerStatus": "FAILED"
  }
}
```

**Error Details:**
```
SourceServerId: s-3578f52ef3bdd58b4
Status: FAILED
Error: ParamValidationError: Parameter validation failed:
Unknown parameter in sourceServers[0]: "recoveryInstanceProperties"
```

### UI Duration Bug

**Also discovered:** Duration showing "489616h 7m" (incorrect)  
**Cause**: Likely timestamp parsing or calculation issue  
**Priority**: LOW (cosmetic compared to Bug 9)

## Next Steps (New Session Required)

### Immediate Action Required
1. **Revert Bug 8 implementation** - Remove `recoveryInstanceProperties` parameter
2. **Research correct API usage** - How to apply launch configurations
3. **Implement proper solution** - Pre-configure or different approach
4. **Test thoroughly** - Validate DRS job creation works
5. **Redeploy Lambda** - Deploy working version immediately

### Testing Plan
1. Revert to commit before Bug 8 (9a6d8f1)
2. Verify basic DRS job creation works
3. Research and implement correct launch configuration approach
4. Test with multiple servers having different configs
5. Verify configurations are actually applied to recovery instances

## Session Outcome

**Discovered**: Critical production-blocking bug  
**Status**: System completely broken for all recovery operations  
**Action**: Emergency preservation at 80% tokens  
**Next**: Fix Bug 9 in fresh session with full context

**Files Modified**: None (investigation only)  
**Git Status**: Clean (no changes committed)

## Context Preservation

**Checkpoint**: `history/checkpoints/checkpoint_session_20251128_211507_f17dca_2025-11-28_21-15-07.md`  
**Conversation**: `history/conversations/conversation_session_20251128_211507_f17dca_2025-11-28_21-15-07_task_1764382212565.md`

---

**Critical Learning**: Always validate API parameters against actual AWS documentation before implementation. Bug 8 was implemented based on logical assumptions about how the API "should" work, not actual API specifications.
