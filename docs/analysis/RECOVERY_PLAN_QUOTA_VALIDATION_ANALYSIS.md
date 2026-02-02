# Recovery Plan Quota Validation Analysis

**Date**: February 1, 2026  
**Status**: ✅ **VALIDATED - PROTECTIONS IN PLACE**

## User Scenario

**Question**: "What if a Recovery Plan is created with 6 Protection Groups with 100 servers each with depends on sending so they all try to run?"

**Answer**: ✅ **This is BLOCKED at creation time**

## Validation Flow

### Scenario Details
- 6 waves (Protection Groups)
- 100 servers per wave
- Total: 6 × 100 = **600 servers**
- DRS Limit: **500 servers max** across all concurrent jobs

### Protection Mechanism

#### 1. Pre-Creation Validation ✅

**Location**: `lambda/data-management-handler/index.py` - `create_recovery_plan()` (lines 3427-3454)

```python
# QUOTA VALIDATION: Check total servers across all waves doesn't exceed 500
total_servers = 0
wave_server_counts = []

for wave in camelcase_waves:
    wave_name = wave.get("waveName", f"Wave {wave.get('waveNumber', '?')}")
    pg_id = wave.get("protectionGroupId") or (wave.get("protectionGroupIds", []) or [None])[0]
    
    if pg_id:
        server_ids = resolve_pg_servers_for_conflict_check(pg_id, pg_cache)
        wave_count = len(server_ids)
        total_servers += wave_count
        wave_server_counts.append({"waveName": wave_name, "serverCount": wave_count})

# Check 500 total servers limit
if total_servers > 500:
    return response(400, {
        "error": "QUOTA_EXCEEDED",
        "quotaType": "total_servers_in_jobs",
        "message": f"Recovery Plan would launch {total_servers} servers (max 500 across all jobs)",
        "totalServers": total_servers,
        "maxServers": 500,
        "waveBreakdown": wave_server_counts,
        "limit": "DRS Service Quota: Max 500 servers across all concurrent jobs (not adjustable)",
        "documentation": "https://docs.aws.amazon.com/general/latest/gr/drs.html",
        "recommendation": "Split this Recovery Plan into multiple plans or reduce the number of servers per wave"
    })
```

**Result**: ✅ **Recovery Plan creation BLOCKED with 400 error**

#### 2. Error Response

```json
{
  "statusCode": 400,
  "body": {
    "error": "QUOTA_EXCEEDED",
    "quotaType": "total_servers_in_jobs",
    "message": "Recovery Plan would launch 600 servers (max 500 across all jobs)",
    "totalServers": 600,
    "maxServers": 500,
    "waveBreakdown": [
      {"waveName": "Wave 1", "serverCount": 100},
      {"waveName": "Wave 2", "serverCount": 100},
      {"waveName": "Wave 3", "serverCount": 100},
      {"waveName": "Wave 4", "serverCount": 100},
      {"waveName": "Wave 5", "serverCount": 100},
      {"waveName": "Wave 6", "serverCount": 100}
    ],
    "limit": "DRS Service Quota: Max 500 servers across all concurrent jobs (not adjustable)",
    "documentation": "https://docs.aws.amazon.com/general/latest/gr/drs.html",
    "recommendation": "Split this Recovery Plan into multiple plans or reduce the number of servers per wave"
  }
}
```

#### 3. Runtime Validation ✅

**Location**: `lambda/shared/conflict_detection.py` - `check_server_conflicts()` (lines 700-900)

Even if a Recovery Plan somehow bypassed creation validation, the runtime conflict detection would catch it:

```python
# QUOTA CHECK 3: Total servers in jobs limit (500 max)
total_check = check_total_servers_in_jobs_limit(
    region, total_plan_servers, account_context
)
if not total_check["valid"]:
    quota_violations.append({
        "quotaType": "total_servers_in_jobs",
        "region": region,
        "totalServers": total_check["totalAfter"],
        "maxServers": total_check["maxServers"],
        "message": f"Cannot start - would exceed 500 servers in jobs limit",
        "conflictSource": "quota_violation"
    })
```

**Result**: ✅ **Execution BLOCKED with 409 conflict error**

## UI Display

### Dashboard Page ✅

**Location**: `frontend/src/pages/Dashboard.tsx`

Shows compact capacity summary with link to System Status page:
- Replicating servers capacity
- Recovery capacity  
- Link to "View Details" → System Status page

### System Status Page ✅

**Location**: `frontend/src/pages/SystemStatusPage.tsx` (lines 307-365)

Shows ALL 3 DRS job-level quotas:

1. **Concurrent Recovery Jobs** (20 max)
   - Current active jobs
   - Available job slots
   - Visual gauge

2. **Servers in Active Jobs** (500 max)
   - Current servers in jobs
   - Available server slots
   - Visual gauge

3. **Max Servers Per Job** (100 max)
   - Largest current job size
   - Maximum allowed per job
   - Visual gauge

## Test Coverage

### Load Tests ✅

**Location**: `tests/load/test_drs_quota_load_testing.py`

- ✅ `test_rp_total_at_limit_500_servers` - 500 servers accepted
- ✅ `test_rp_exceeds_total_limit_501_servers` - 501 servers rejected
- ✅ `test_rp_per_wave_limit_enforcement` - Each wave validates 100 limit
- ✅ `test_rp_multiple_waves_total_validation` - Multiple waves total validation

### Unit Tests ✅

**Location**: `tests/unit/test_conflict_detection_comprehensive.py`

- ✅ 21 comprehensive conflict detection tests
- ✅ All quota validation functions tested
- ✅ Edge cases covered

## Validation Summary

| Validation Point | Status | Location | Blocks Creation? |
|-----------------|--------|----------|------------------|
| **Pre-Creation** | ✅ Working | `data-management-handler/index.py` | ✅ YES (400 error) |
| **Runtime** | ✅ Working | `conflict_detection.py` | ✅ YES (409 error) |
| **UI Display** | ✅ Working | `SystemStatusPage.tsx` | N/A (informational) |
| **Dashboard** | ✅ Working | `Dashboard.tsx` | N/A (informational) |
| **Load Tests** | ✅ Passing | `test_drs_quota_load_testing.py` | N/A (verification) |
| **Unit Tests** | ✅ Passing | `test_conflict_detection_comprehensive.py` | N/A (verification) |

## Conclusion

✅ **The scenario you described (6 waves × 100 servers = 600 total) is FULLY PROTECTED:**

1. **Pre-creation validation** blocks Recovery Plan creation with clear error message
2. **Runtime validation** provides additional safety net during execution
3. **UI displays** show all relevant quotas on Dashboard and System Status pages
4. **Comprehensive tests** verify all validation logic works correctly

**No additional protections needed** - the system already handles this scenario correctly.

## Recommendations

### Current Implementation ✅
- All quotas validated at creation time
- Clear error messages with recommendations
- Visual quota displays in UI
- Comprehensive test coverage

### Optional Enhancements (Future)
1. **Predictive Warnings**: Show warning in UI when approaching limits (e.g., at 90% capacity)
2. **Quota Planning Tool**: Help users plan Recovery Plans within quota limits
3. **Auto-Split Suggestions**: Automatically suggest how to split large plans
4. **Capacity Forecasting**: Predict quota usage for planned executions

---

**Verified by**: Kiro AI Assistant  
**Date**: February 1, 2026  
**Status**: ✅ **PROTECTIONS VERIFIED AND WORKING**
