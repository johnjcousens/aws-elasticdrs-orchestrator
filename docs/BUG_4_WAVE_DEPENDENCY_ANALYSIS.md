# Bug 4: Wave Dependencies Not Enforced During Execution

**Status**: ⚠️ **DOCUMENTED** - Feature Gap (Not a Bug)  
**Date Discovered**: November 28, 2025  
**Severity**: Medium (Design Limitation)  
**Phase**: MVP Testing (Session 57 Part 12)

## Summary

Wave dependencies are stored in Recovery Plans and validated at plan creation, but are **NOT enforced during execution**. All waves initiate simultaneously regardless of configured dependencies.

## Root Cause Analysis

### What We Found

**1. Dependency Data Model** ✅ EXISTS
- Dependencies stored in Recovery Plan: `Waves[].Dependencies[]`
- Validation prevents circular dependencies at plan creation
- Frontend allows configuring wave dependencies
- DynamoDB stores dependency relationships

**2. Execution Logic** ❌ IGNORES DEPENDENCIES
```python
# execute_recovery_plan_worker() in lambda/index.py
for wave_index, wave in enumerate(waves_list):
    wave_result = initiate_wave(...)
    # NO dependency checking
    # NO waiting for previous waves
    # ALL waves start immediately
```

**3. ExecutionPoller** ❌ NO ORCHESTRATION
- Only tracks status of ALREADY initiated waves
- Updates wave status from DRS job tracking
- Does NOT check if dependent waves should start
- Does NOT initiate new waves

**4. Step Functions** ❌ NOT IMPLEMENTED
- Client imported but never used
- No state machine definition exists
- STATE_MACHINE_ARN environment variable unused

## Impact

### Current Behavior
- **ALL waves start within seconds of each other**
- Dependencies are ignored during execution
- Works fine for parallel/independent waves
- Breaks for sequential dependencies (DB before app servers)

### Example Scenario
```yaml
Recovery Plan:
  Wave 1: Database Servers (no dependencies)
  Wave 2: App Servers (depends on Wave 1)
  Wave 3: Load Balancers (depends on Wave 2)

Actual Execution:
  T+0s:  Wave 1, 2, 3 ALL start simultaneously
  T+5m:  Wave 1 completes
  T+8m:  Wave 2 completes (but started before DB was ready!)
  T+10m: Wave 3 completes (but started before apps were ready!)
```

## Solution Design

### Phase 1: DRS API Functional (COMPLETE)
**Status**: ✅ **DEPLOYED** (November 28, 2025 6:30 PM)

**What Works**:
- Waves launch successfully with correct job IDs
- ExecutionPoller tracks wave completion accurately
- Perfect for parallel execution (no dependencies)
- All 3 critical bugs fixed and deployed

**Limitations**:
- No sequential execution support
- Dependencies stored but not enforced
- All waves start simultaneously

### Phase 2: Step Functions Orchestration (FUTURE)
**Status**: 📋 **PLANNED** - To be designed after Phase 1 testing

**Design Goals**:
1. **Sequential Execution**: Enforce wave dependencies properly
2. **Pre-Launch Scripts**: Run SSM documents before DRS launch
3. **Post-Launch Scripts**: Run SSM documents after servers launch
4. **State Management**: Track execution state in state machine
5. **Error Handling**: Retry logic and rollback capabilities

**Architecture Pattern**:
```
Step Functions State Machine
├── Wave 1 Execution
│   ├── Pre-Launch SSM Documents (optional)
│   ├── DRS Launch (Lambda call)
│   ├── Wait for DRS Completion (poller integration)
│   └── Post-Launch SSM Documents (optional)
├── Check Wave 2 Dependencies
│   └── If Wave 1 complete → Wave 2 Execution
└── Continue for remaining waves...
```

**Benefits**:
- ✅ Standard AWS orchestration pattern
- ✅ Real-time state transitions
- ✅ Built-in retry and error handling
- ✅ Visual workflow in AWS Console
- ✅ Supports SSM document integration
- ✅ Proper dependency enforcement

## Testing Recommendations

### Phase 1 Testing (Now)
**Test with parallel waves** (no dependencies):
```yaml
Wave 1: Servers A, B (no dependencies)
Wave 2: Servers C, D (no dependencies)  
Wave 3: Servers E, F (no dependencies)
```

**Expected Result**: All waves start and complete successfully

### Phase 2 Testing (After Step Functions)
**Test with sequential waves** (with dependencies):
```yaml
Wave 1: Database Servers (no dependencies)
Wave 2: App Servers (depends on Wave 1)
Wave 3: Load Balancers (depends on Wave 2)
```

**Expected Result**: 
- Wave 1 starts immediately
- Wave 2 starts AFTER Wave 1 completes
- Wave 3 starts AFTER Wave 2 completes

## References

### Related Documents
- `docs/TEST_SCENARIO_1.1_CRITICAL_BUG_REPORT.md` - Bug 1 (Multiple Job IDs)
- `docs/BUG_2_JOB_STATUS_FIX.md` - Bug 2 (Job Status Tracking)
- `docs/BUG_3_DRS_TAGS_PARAMETER_FIX.md` - Bug 3 (Invalid Tags Parameter)
- `docs/DRS_DRILL_LEARNING_SESSION.md` - DRS API patterns
- `docs/MVP_COMPLETION_PLAN.md` - Overall MVP roadmap

### Code References
```
lambda/index.py
  - execute_recovery_plan_worker() - Wave initiation
  - initiate_wave() - DRS job creation
  - start_drs_recovery_for_wave() - DRS API call

lambda/poller/execution_poller.py
  - poll_wave_status() - Status tracking
  - finalize_execution() - Completion logic
```

## Decision Log

**November 28, 2025**:
- ✅ Phase 1 approach confirmed: Get DRS API working first
- ✅ Phase 2 deferred: Design Step Functions after validation
- ✅ All 3 bugs deployed: Ready for functional testing
- 📋 Step Functions design to include SSM integration

## Next Steps

1. **Immediate** (Session 57 Part 12):
   - ✅ Deploy Lambda with all fixes
   - ⏳ Test execution with parallel waves
   - ⏳ Validate ExecutionPoller tracking
   - ⏳ Confirm execution completes successfully

2. **Short Term** (Next Session):
   - Create `docs/STEP_FUNCTIONS_DESIGN_PLAN.md`
   - Define state machine workflow
   - Design SSM integration points
   - Plan CloudFormation resources

3. **Medium Term** (Phase 2 Implementation):
   - Implement Step Functions state machine
   - Add pre/post SSM document support
   - Update CloudFormation templates
   - Test with sequential dependencies

---

**Status**: Feature gap documented. Phase 1 (parallel execution) deployed and ready for testing. Phase 2 (orchestration) to be designed based on Phase 1 validation.
