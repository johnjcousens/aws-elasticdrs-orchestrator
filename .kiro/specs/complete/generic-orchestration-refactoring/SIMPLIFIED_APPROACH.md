# Simplified Approach - Generic Orchestration Refactoring

**Date**: February 3, 2026  
**Status**: Approved

---

## What We're Actually Doing

Move 3 DRS functions (~450 lines) from orchestration Lambda into existing handler Lambdas:

```
orchestration-stepfunctions/index.py
├─ start_wave_recovery() (~200 lines)     → execution-handler
├─ update_wave_status() (~200 lines)      → query-handler
└─ query_drs_servers_by_tags() (~50 lines) → query-handler
```

Then orchestration becomes generic:
```python
# Orchestration just coordinates, handlers do DRS work
orchestration → execution-handler.start_wave_recovery()
orchestration → query-handler.poll_wave_status()
```

---

## Why This Is The Right Approach

✅ **No new Lambda** - Use existing handlers  
✅ **Orchestration is generic** - No DRS code  
✅ **DRS logic in right place** - Handlers already DRS-specific  
✅ **Minimal code movement** - Only ~450 lines  
✅ **Clear separation** - Orchestration coordinates, handlers execute  
✅ **Simple to implement** - 1-2 weeks  
✅ **Easy to test** - Existing handlers already tested  
✅ **Zero regression risk** - Handlers stay DRS-specific  

---

## What We're NOT Doing

❌ Creating new adapter Lambdas  
❌ Making handlers generic/technology-agnostic  
❌ Extracting ALL DRS code from handlers  
❌ 4-phase lifecycle architecture  
❌ Module factory pattern  
❌ Multi-technology support  

**Scope**: ONLY move 3 functions. Keep handlers DRS-specific.

---

## Architecture Before

```
┌─────────────────────────────────────┐
│ orchestration-stepfunctions         │
│ ┌─────────────────────────────────┐ │
│ │ • start_wave_recovery()         │ │ ← DRS code here
│ │ • update_wave_status()          │ │ ← DRS code here
│ │ • query_drs_servers_by_tags()   │ │ ← DRS code here
│ └─────────────────────────────────┘ │
│              │                       │
│              ▼                       │
│         DRS API (boto3)              │
└─────────────────────────────────────┘
```

**Problem**: Orchestration makes direct DRS API calls

---

## Architecture After

```
┌─────────────────────────────────────┐
│ orchestration-stepfunctions         │
│ ┌─────────────────────────────────┐ │
│ │ • begin_wave_plan()             │ │ ← Generic
│ │ • poll_wave_status()            │ │ ← Generic
│ │ • resume_wave()                 │ │ ← Generic
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
              │
              ├──────────────────┐
              ▼                  ▼
┌──────────────────────┐  ┌──────────────────────┐
│ execution-handler    │  │ query-handler        │
│ ┌──────────────────┐ │  │ ┌──────────────────┐ │
│ │ start_wave_      │ │  │ │ poll_wave_       │ │
│ │   recovery()     │ │  │ │   status()       │ │
│ │                  │ │  │ │                  │ │
│ │ + existing DRS   │ │  │ │ query_servers_   │ │
│ └──────────────────┘ │  │ │   by_tags()      │ │
│          │            │  │ │                  │ │
│          ▼            │  │ │ + existing DRS   │ │
│     DRS API           │  │ └──────────────────┘ │
└──────────────────────┘  │          │            │
                          │          ▼            │
                          │     DRS API           │
                          └──────────────────────┘
```

**Solution**: Orchestration invokes handlers, handlers call DRS API

---

## Implementation Summary

### 1. Move Functions (Tasks 1-3)

**execution-handler** receives:
- `start_wave_recovery(state, wave_number)` (~200 lines)
- `apply_launch_config_before_recovery()` helper (~150 lines)

**query-handler** receives:
- `poll_wave_status(state)` (~200 lines) - renamed from `update_wave_status`
- `query_drs_servers_by_tags(region, tags, account_context)` (~50 lines)

### 2. Update Orchestration (Task 4)

Replace direct calls with Lambda invocations:

```python
# Before
start_wave_recovery(state, 0)

# After
lambda_client.invoke(
    FunctionName=os.environ['EXECUTION_HANDLER_ARN'],
    Payload=json.dumps({
        'action': 'start_wave_recovery',
        'state': state,
        'wave_number': 0
    })
)
```

### 3. Update CloudFormation (Task 5)

Add environment variables and IAM permissions:
- `EXECUTION_HANDLER_ARN` → orchestration Lambda
- `QUERY_HANDLER_ARN` → orchestration Lambda
- `EXECUTION_HANDLER_ARN` → query-handler Lambda (for next wave)
- Lambda invoke permissions

### 4. Test Everything (Tasks 6-7)

- Unit tests for moved functions
- Integration tests for end-to-end execution
- Performance validation (±5% execution time)
- Backward compatibility tests

---

## Success Criteria

✅ Orchestration Lambda has zero DRS API calls  
✅ All 3 functions moved to appropriate handlers  
✅ All existing tests pass  
✅ Execution behavior identical  
✅ No performance degradation  
✅ Documentation updated  

---

## Timeline

**Total**: 1-2 weeks

- Week 1: Move functions, update orchestration, CloudFormation
- Week 2: Testing, validation, documentation

---

## Risk Assessment

**Low Risk** because:
- No new Lambdas (using existing handlers)
- Handlers stay DRS-specific (no refactoring)
- Minimal code movement (~450 lines)
- State management unchanged
- DynamoDB schema unchanged
- Frontend unchanged

**Rollback**: Easy - revert CloudFormation stack

---

## Next Steps

1. Review and approve this simplified approach
2. Begin implementation with Task 1 (move start_wave_recovery)
3. Test each function independently before moving to next
4. Deploy to test environment after all functions moved
5. Validate end-to-end execution
6. Document and complete

---

## Questions?

This is the cleanest, simplest solution. No adapter Lambda needed - just move 3 functions to where they logically belong.
