# Generic Orchestration Refactoring - Design Document

**Date**: February 3, 2026  
**Status**: Ready for Implementation  
**Version**: 2.1 (Implementation Ready)

---

## Executive Summary

**Primary Objective**: Move 4 DRS-specific functions (~720 lines) from orchestration Lambda into existing handler Lambdas.

This document specifies the technical design for refactoring the orchestration Lambda by moving DRS-specific functions into the appropriate existing handler Lambdas. This creates a cleaner separation of concerns where orchestration coordinates waves while handlers perform DRS operations.

**Refactoring Strategy**: Create NEW Lambda directory alongside existing one for safe parallel development:

**Lambda Directory Structure**:
```
lambda/
├── orchestration-stepfunctions/    # EXISTING - Keep as reference (unchanged)
│   └── index.py                    # Original code with DRS functions
├── dr-orchestration-stepfunction/  # NEW - Refactored orchestration (no 's')
│   └── index.py                    # Generic orchestration (DRS code removed)
├── execution-handler/              # MODIFIED - Receives start_wave_recovery() + helper
│   └── index.py
├── query-handler/                  # MODIFIED - Receives poll_wave_status() + query function
│   └── index.py
└── shared/                         # Shared utilities (unchanged)
    ├── cross_account.py
    ├── config_merge.py
    └── ...
```

**CloudFormation Changes**:
- **NEW Lambda**: `DrOrchestrationStepFunctionFunction` (using `dr-orchestration-stepfunction.zip`)
- **EXISTING Lambda**: `OrchestrationStepFunctionsFunction` (unchanged, kept as reference)
- **Step Functions**: Update to use new Lambda ARN
- **Rollback**: Switch Step Functions back to old Lambda if issues occur

**Benefits of Parallel Approach**:
- ✅ Original code remains intact for reference
- ✅ Easy rollback by switching Step Functions Lambda ARN
- ✅ Side-by-side comparison during development
- ✅ Zero risk to existing working code
- ✅ Can delete old Lambda after successful validation

**Core Design Goal**: 
- **Generic Orchestration Lambda** - Coordinates wave execution without DRS-specific code
- **Execution Handler** - Receives `start_wave_recovery()` function from orchestration
- **Query Handler** - Receives `update_wave_status()` and `query_drs_servers_by_tags()` from orchestration
- **Clear Separation** - Orchestration coordinates, handlers execute DRS operations

**Key Design Principles:**
1. **Separation of Concerns** - Orchestration coordinates, handlers execute
2. **Zero Regression** - Existing DRS functionality unchanged
3. **No New Lambdas** - Use existing handler Lambdas
4. **Lambda Invocation** - Orchestration invokes handlers via boto3 Lambda client
5. **State Management** - Orchestration maintains execution state
6. **Backward Compatible** - DynamoDB schema unchanged, frontend unchanged

**Refactoring Scope**:
```
MOVE FROM orchestration-stepfunctions (~475 lines total):
1. start_wave_recovery()         → execution-handler (lines 745-870, ~125 lines)
2. apply_launch_config_before_recovery() → execution-handler (lines 200-350, ~150 lines)
3. update_wave_status()          → query-handler (lines 873-1219, ~346 lines)
4. query_drs_servers_by_tags()   → query-handler (lines 645-744, ~99 lines)

KEEP IN orchestration-stepfunctions:
- lambda_handler()
- begin_wave_plan()
- store_task_token()
- resume_wave()
- Wave sequencing logic
- State management
- Helper functions (get_account_context, DecimalEncoder, table getters)
```

---

## Architecture Overview

### Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ orchestration-stepfunctions                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ lambda_handler()                                        │ │
│ │ begin_wave_plan()                                       │ │
│ │ start_wave_recovery() ← DRS-specific (~200 lines)      │ │
│ │ update_wave_status() ← DRS-specific (~200 lines)       │ │
│ │ query_drs_servers_by_tags() ← DRS-specific (~50 lines) │ │
│ │ store_task_token()                                      │ │
│ │ resume_wave()                                           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│                    DRS API (boto3)                           │
└─────────────────────────────────────────────────────────────┘
```

**Issues:**
- Orchestration Lambda makes direct DRS API calls
- DRS-specific logic mixed with orchestration logic
- Violates separation of concerns

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ orchestration-stepfunctions (GENERIC)                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ lambda_handler()                                        │ │
│ │ begin_wave_plan() → invokes execution-handler          │ │
│ │ poll_wave_status() → invokes query-handler             │ │
│ │ store_task_token()                                      │ │
│ │ resume_wave() → invokes execution-handler              │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │
                          ├──────────────────────┐
                          ▼                      ▼
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│ execution-handler               │  │ query-handler                   │
│ ┌─────────────────────────────┐ │  │ ┌─────────────────────────────┐ │
│ │ start_wave_recovery()       │ │  │ │ poll_wave_status()          │ │
│ │ (moved from orchestration)  │ │  │ │ (moved from orchestration)  │ │
│ │                             │ │  │ │                             │ │
│ │ + existing DRS operations   │ │  │ │ query_servers_by_tags()     │ │
│ └─────────────────────────────┘ │  │ │ (moved from orchestration)  │ │
│              │                   │  │ │                             │ │
│              ▼                   │  │ │ + existing DRS queries      │ │
│         DRS API                  │  │ └─────────────────────────────┘ │
└─────────────────────────────────┘  │              │                   │
                                      │              ▼                   │
                                      │         DRS API                  │
                                      └─────────────────────────────────┘
```

**Benefits:**
- Orchestration Lambda has zero DRS API calls
- DRS operations live in appropriate handler Lambdas
- Clear separation of concerns
- No new Lambdas needed
- Minimal code movement (~450 lines)

---

## Function Movement Details

### 1. start_wave_recovery() → execution-handler

**Source**: `lambda/orchestration-stepfunctions/index.py` (lines 745-870)  
**Destination**: `lambda/execution-handler/index.py`  
**Size**: ~125 lines

**Function Signature**:
```python
def start_wave_recovery(state: Dict, wave_number: int) -> None:
    """
    Start DRS recovery for a wave with tag-based server resolution.
    
    Modifies state in-place (archive pattern) to update current wave tracking,
    job details, and wave results.
    
    Args:
        state: Complete state object with execution context (modified in-place)
        wave_number: Zero-based wave index to start
        
    Returns:
        None (modifies state in-place)
    """
```

**Operations**:
1. Retrieve Protection Group from DynamoDB
2. Resolve servers using tag-based discovery (`query_drs_servers_by_tags`)
3. Apply Protection Group launch configuration to DRS servers (`apply_launch_config_before_recovery`)
4. Start DRS recovery job via `drs_client.start_recovery()`
5. Update state in-place with job details and initial server statuses
6. Store wave result in DynamoDB

**Dependencies**:
- `get_protection_groups_table()` - DynamoDB table accessor (needs to be copied)
- `get_execution_history_table()` - DynamoDB table accessor (needs to be copied)
- `get_account_context()` - Extract cross-account context (needs to be copied)
- `create_drs_client()` - Create cross-account DRS client (from shared.cross_account)
- `query_drs_servers_by_tags()` - Server discovery (also being moved to query-handler)
- `apply_launch_config_before_recovery()` - Helper function (move with parent)

**Handler Integration**:
```python
# In execution-handler/index.py
def lambda_handler(event, context):
    action = event.get('action')
    
    if action == 'start_wave_recovery':
        state = event.get('state', {})
        wave_number = event.get('wave_number', 0)
        start_wave_recovery(state, wave_number)  # Modifies state in-place
        return state  # Return modified state
    # ... existing actions ...
```

### 1a. apply_launch_config_before_recovery() → execution-handler

**Source**: `lambda/orchestration-stepfunctions/index.py` (lines 200-350)  
**Destination**: `lambda/execution-handler/index.py`  
**Size**: ~150 lines

**Function Signature**:
```python
def apply_launch_config_before_recovery(
    drs_client,
    server_ids: List[str],
    launch_config: Dict,
    region: str,
    protection_group: Dict = None,
) -> None:
    """
    Apply Protection Group launch configuration to DRS servers before recovery.
    
    Updates both DRS launch settings and EC2 launch templates to ensure recovered
    instances use correct network, security, and instance configurations.
    
    Supports per-server configuration overrides via protection_group['servers'].
    
    Args:
        drs_client: Boto3 DRS client (may be cross-account)
        server_ids: List of DRS source server IDs
        launch_config: Protection Group launch configuration dict (group defaults)
        region: AWS region for EC2 operations
        protection_group: Full protection group dict with per-server configs (optional)
    """
```

**Operations**:
1. For each server, get effective config (group defaults + per-server overrides)
2. Get DRS launch configuration to find EC2 launch template
3. Update DRS launch configuration settings (copyPrivateIp, copyTags, licensing, etc.)
4. Update EC2 launch template with network/instance settings
5. Set launch template default version to latest

**Dependencies**:
- `get_effective_launch_config()` - From shared.config_merge (for per-server overrides)
- EC2 client for launch template updates
- DRS client for launch configuration updates

**Note**: This function is called by `start_wave_recovery()` and must move with it.

### 2. update_wave_status() → query-handler

**Source**: `lambda/orchestration-stepfunctions/index.py` (lines 873-1219)  
**Destination**: `lambda/query-handler/index.py`  
**Size**: ~346 lines

**Function Signature**:
```python
def poll_wave_status(state: Dict) -> Dict:
    """
    Poll DRS job status and track server launch progress.
    
    Called repeatedly by Step Functions Wait state until wave completes or times out.
    Checks for cancellation, tracks server launch status, and manages wave transitions.
    
    Args:
        state: Complete state object with job_id, region, wave tracking
        
    Returns:
        Updated state object with wave status and completion flags
    """
```

**Operations**:
1. Check for execution cancellation (user-initiated) at start of poll cycle
2. Verify job exists and get current status via `drs_client.describe_jobs()`
3. Track individual server launch status (PENDING → IN_PROGRESS → LAUNCHED/FAILED)
4. Determine current phase (CONVERTING → LAUNCHING → LAUNCHED) from job events
5. Check completion conditions (all launched, any failed, timeout)
6. Handle wave completion: start next wave or pause/complete execution

**Dependencies**:
- `get_execution_history_table()` - DynamoDB table accessor (needs to be copied)
- `get_account_context()` - Extract cross-account context (needs to be copied)
- `create_drs_client()` - Create cross-account DRS client (from shared.cross_account)
- `DRS_JOB_STATUS_COMPLETE_STATES` - Job status constants (needs to be copied)
- `DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES` - Server status constants (needs to be copied)
- `DRS_JOB_SERVERS_COMPLETE_FAILURE_STATES` - Server status constants (needs to be copied)
- `DRS_JOB_SERVERS_WAIT_STATES` - Server status constants (needs to be copied)

**Handler Integration**:
```python
# In query-handler/index.py
def lambda_handler(event, context):
    action = event.get('action')
    
    if action == 'poll_wave_status':
        state = event.get('state', {})
        result = poll_wave_status(state)
        return result
    # ... existing actions ...
```

**Note**: This function calls `start_wave_recovery()` when moving to next wave. After refactoring, it will invoke execution-handler instead:

```python
# Inside poll_wave_status() when starting next wave
lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName=os.environ['EXECUTION_HANDLER_ARN'],
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'action': 'start_wave_recovery',
        'state': state,
        'wave_number': next_wave
    })
)
result = json.loads(response['Payload'].read())
state.update(result)
```
### 3. query_drs_servers_by_tags() → query-handler

**Source**: `lambda/orchestration-stepfunctions/index.py` (lines 645-744)  
**Destination**: `lambda/query-handler/index.py`  
**Size**: ~99 lines

**Function Signature**:
```python
def query_drs_servers_by_tags(
    region: str,
    tags: Dict[str, str],
    account_context: Dict = None
) -> List[str]:
    """
    Query DRS source servers matching ALL specified tags (AND logic).
    
    Tag-based discovery enables dynamic server resolution at execution time rather
    than static server lists. This supports auto-scaling and server changes without
    updating Protection Groups.
    
    Tag Matching Rules:
    - Server must have ALL specified tags to be included
    - Tag keys and values are case-insensitive
    - Whitespace is stripped from keys and values
    - Tags are read from DRS source server metadata, not EC2 instance tags
    
    Args:
        region: AWS region to query DRS servers
        tags: Dict of tag key-value pairs that servers must match
        account_context: Optional cross-account context for IAM role assumption
        
    Returns:
        List of DRS source server IDs matching all tags
    """
```

**Operations**:
1. Create DRS client with cross-account support
2. Paginate through all source servers in region using `describe_source_servers`
3. Filter servers matching ALL specified tags (case-insensitive, AND logic)
4. Return list of matching server IDs

**Dependencies**:
- `create_drs_client()` - Create cross-account DRS client (from shared.cross_account)

**Handler Integration**:
```python
# In query-handler/index.py
def lambda_handler(event, context):
    action = event.get('action')
    
    if action == 'query_servers_by_tags':
        region = event.get('region')
        tags = event.get('tags', {})
        account_context = event.get('account_context')
        result = query_drs_servers_by_tags(region, tags, account_context)
        return {'server_ids': result}
    # ... existing actions ...
```

---

## Helper Functions and Constants

### Functions to Copy to Both Handlers

These helper functions are used by the moved functions and need to be copied to both execution-handler and query-handler:

#### get_account_context()
```python
def get_account_context(state: Dict) -> Dict:
    """
    Extract account context from state, handling both camelCase and snake_case.
    
    Supports two input formats:
    - Initial execution: camelCase (accountContext) from Step Functions input
    - Resume after pause: snake_case (account_context) from SendTaskSuccess output
    
    Returns:
        Dict containing accountId, assumeRoleName, and isCurrentAccount flags
    """
    return state.get("accountContext") or state.get("account_context", {})
```

#### DynamoDB Table Getters

These functions need to be copied to handlers that access DynamoDB:

```python
# Environment variables (add to handler)
PROTECTION_GROUPS_TABLE = os.environ.get("PROTECTION_GROUPS_TABLE")
EXECUTION_HISTORY_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE")

# AWS clients
dynamodb = boto3.resource("dynamodb")

# Lazy-loaded tables
_protection_groups_table = None
_execution_history_table = None

def get_protection_groups_table():
    """Lazy-load Protection Groups table to optimize Lambda cold starts"""
    global _protection_groups_table
    if _protection_groups_table is None:
        _protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
    return _protection_groups_table

def get_execution_history_table():
    """Lazy-load Execution History table to optimize Lambda cold starts"""
    global _execution_history_table
    if _execution_history_table is None:
        _execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    return _execution_history_table
```

**Required for**:
- execution-handler: Both table getters (reads Protection Groups, writes Execution History)
- query-handler: `get_execution_history_table()` only (reads/writes Execution History)

### Constants to Copy to query-handler

DRS job and server status constants used by `poll_wave_status()`:

```python
# DRS job status constants - determine when job polling should stop
DRS_JOB_STATUS_COMPLETE_STATES = ["COMPLETED"]
DRS_JOB_STATUS_WAIT_STATES = ["PENDING", "STARTED"]

# DRS server launch status constants - track individual server recovery progress
DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES = ["LAUNCHED"]
DRS_JOB_SERVERS_COMPLETE_FAILURE_STATES = ["FAILED", "TERMINATED"]
DRS_JOB_SERVERS_WAIT_STATES = ["PENDING", "IN_PROGRESS"]
```

---

## Orchestration Lambda Changes

### Updated Functions

#### begin_wave_plan()

**Before (Direct DRS call)**:
```python
def begin_wave_plan(event: Dict) -> Dict:
    # ... initialization ...
    
    # Start first wave directly
    if len(waves) > 0:
        start_wave_recovery(state, 0)  # Direct call
    
    return state
```

**After (Handler invocation)**:
```python
def begin_wave_plan(event: Dict) -> Dict:
    # ... initialization ...
    
    # Start first wave via execution-handler
    if len(waves) > 0:
        lambda_client = boto3.client('lambda')
        response = lambda_client.invoke(
            FunctionName=os.environ['EXECUTION_HANDLER_ARN'],
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'start_wave_recovery',
                'state': state,
                'wave_number': 0
            })
        )
        result = json.loads(response['Payload'].read())
        state.update(result)
    
    return state
```

#### New Function: poll_wave_status()

**Replaces**: Direct call to `update_wave_status()`

```python
def poll_wave_status(event: Dict) -> Dict:
    """
    Poll wave status by invoking query-handler.
    
    Args:
        event: Step Functions event with state
        
    Returns:
        Updated state object from query-handler
    """
    state = event.get("application", event)
    
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName=os.environ['QUERY_HANDLER_ARN'],
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'poll_wave_status',
            'state': state
        })
    )
    
    result = json.loads(response['Payload'].read())
    return result
```

#### resume_wave()

**Before (Direct DRS call)**:
```python
def resume_wave(event: Dict) -> Dict:
    state = event.get("application", event)
    # ... reset status ...
    
    # Start the paused wave directly
    start_wave_recovery(state, paused_before_wave)
    
    return state
```

**After (Handler invocation)**:
```python
def resume_wave(event: Dict) -> Dict:
    state = event.get("application", event)
    # ... reset status ...
    
    # Start the paused wave via execution-handler
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName=os.environ['EXECUTION_HANDLER_ARN'],
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'start_wave_recovery',
            'state': state,
            'wave_number': paused_before_wave
        })
    )
    result = json.loads(response['Payload'].read())
    state.update(result)
    
    return state
```

### Environment Variables

Add to orchestration Lambda:
```yaml
Environment:
  Variables:
    EXECUTION_HANDLER_ARN: !GetAtt ExecutionHandlerFunction.Arn
    QUERY_HANDLER_ARN: !GetAtt QueryHandlerFunction.Arn
```

Add to query-handler Lambda:
```yaml
Environment:
  Variables:
    EXECUTION_HANDLER_ARN: !GetAtt ExecutionHandlerFunction.Arn
    EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTable
```

Add to execution-handler Lambda:
```yaml
Environment:
  Variables:
    PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTable
    EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTable
```

### IAM Permissions

Add Lambda invoke permissions to orchestration role:
```yaml
- Effect: Allow
  Action:
    - lambda:InvokeFunction
  Resource:
    - !GetAtt ExecutionHandlerFunction.Arn
    - !GetAtt QueryHandlerFunction.Arn
```

Add Lambda invoke permission to query-handler role:
```yaml
- Effect: Allow
  Action:
    - lambda:InvokeFunction
  Resource:
    - !GetAtt ExecutionHandlerFunction.Arn
```

Add DynamoDB permissions to execution-handler role:
```yaml
- Effect: Allow
  Action:
    - dynamodb:GetItem
    - dynamodb:Query
  Resource:
    - !GetAtt ProtectionGroupsTable.Arn
- Effect: Allow
  Action:
    - dynamodb:UpdateItem
  Resource:
    - !GetAtt ExecutionHistoryTable.Arn
```

Add DynamoDB permissions to query-handler role:
```yaml
- Effect: Allow
  Action:
    - dynamodb:GetItem
    - dynamodb:UpdateItem
  Resource:
    - !GetAtt ExecutionHistoryTable.Arn
```

---

## State Management

### State Object Structure

The state object remains unchanged - it's passed between orchestration and handlers:

```python
{
    # Core identifiers
    "plan_id": "plan-123",
    "execution_id": "exec-456",
    "is_drill": True,
    "accountContext": {...},
    
    # Wave tracking
    "waves": [...],
    "total_waves": 3,
    "current_wave_number": 0,
    "completed_waves": 0,
    
    # Completion flags
    "all_waves_completed": False,
    "wave_completed": False,
    
    # Current wave details
    "job_id": "drsjob-abc123",
    "region": "us-east-1",
    "server_ids": ["s-001", "s-002"],
    
    # Results
    "wave_results": [...],
    
    # Status
    "status": "running",
    
    # ... other fields ...
}
```

### State Flow

```
Step Functions
      │
      ▼
orchestration.begin_wave_plan()
      │
      ├─ Creates initial state
      │
      ▼
execution-handler.start_wave_recovery()
      │
      ├─ Updates state with job_id, server_ids
      │
      ▼
orchestration (receives updated state)
      │
      ▼
Step Functions Wait (30s)
      │
      ▼
orchestration.poll_wave_status()
      │
      ▼
query-handler.poll_wave_status()
      │
      ├─ Updates state with server statuses
      ├─ Checks completion
      │
      ▼
orchestration (receives updated state)
      │
      ▼
Step Functions Choice (wave_completed?)
      │
      ├─ No → Wait 30s → poll again
      │
      └─ Yes → Next wave or complete
```

---

## Cross-Handler Invocation Pattern

### query-handler → execution-handler

When `poll_wave_status()` in query-handler needs to start the next wave, it invokes execution-handler:

```python
# Inside poll_wave_status() when all servers launched and next wave exists
if launched_count == total_servers and failed_count == 0:
    # ... wave completion logic ...
    
    next_wave = wave_number + 1
    waves_list = state.get("waves", [])
    
    if next_wave < len(waves_list):
        next_wave_config = waves_list[next_wave]
        pause_before = next_wave_config.get("pauseBeforeWave", False)
        
        if pause_before:
            # Pause logic (no invocation)
            state["status"] = "paused"
            state["paused_before_wave"] = next_wave
            return state
        
        # Start next wave via execution-handler
        print(f"Starting next wave: {next_wave}")
        lambda_client = boto3.client('lambda')
        response = lambda_client.invoke(
            FunctionName=os.environ['EXECUTION_HANDLER_ARN'],
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'action': 'start_wave_recovery',
                'state': state,
                'wave_number': next_wave
            })
        )
        
        # Update state with response from execution-handler
        result = json.loads(response['Payload'].read())
        state.update(result)
```

### execution-handler → query-handler

When `start_wave_recovery()` needs to query servers by tags, it invokes query-handler:

```python
# Inside start_wave_recovery() when resolving servers
selection_tags = pg.get("serverSelectionTags", {})

if selection_tags:
    print(f"Resolving servers for PG {protection_group_id} with tags: {selection_tags}")
    
    # Invoke query-handler to resolve servers
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName=os.environ['QUERY_HANDLER_ARN'],
        InvocationType='RequestResponse',
        Payload=json.dumps({
            'action': 'query_servers_by_tags',
            'region': region,
            'tags': selection_tags,
            'account_context': get_account_context(state)
        })
    )
    
    result = json.loads(response['Payload'].read())
    server_ids = result.get('server_ids', [])
    print(f"Resolved {len(server_ids)} servers from tags")
```

**Note**: The current implementation calls `query_drs_servers_by_tags()` directly. After refactoring, this becomes a Lambda invocation.

---

## Error Handling

### Handler Invocation Errors

```python
try:
    response = lambda_client.invoke(
        FunctionName=handler_arn,
        Payload=json.dumps(payload)
    )
    result = json.loads(response['Payload'].read())
    
    # Check for function error
    if response.get('FunctionError'):
        raise Exception(f"Handler error: {result}")
    
    return result
    
except Exception as e:
    logger.error(f"Error invoking handler: {e}")
    state['wave_completed'] = True
    state['status'] = 'failed'
    state['error'] = str(e)
    return state
```

### Timeout Handling

- Orchestration Lambda timeout: 120 seconds (unchanged)
- Handler invocation timeout: 300 seconds (execution-handler), 120 seconds (query-handler)
- Step Functions handles overall execution timeout (1 year max)

---

## Testing Strategy

### Unit Tests

1. **Orchestration Lambda**:
   - Test `begin_wave_plan()` invokes execution-handler correctly
   - Test `poll_wave_status()` invokes query-handler correctly
   - Test `resume_wave()` invokes execution-handler correctly
   - Mock Lambda client to verify payloads

2. **Execution Handler**:
   - Test `start_wave_recovery()` action handler
   - Test state updates are correct
   - Mock DRS client

3. **Query Handler**:
   - Test `poll_wave_status()` action handler
   - Test `query_servers_by_tags()` action handler
   - Mock DRS client

### Integration Tests

1. **End-to-End Wave Execution**:
   - Deploy to test environment
   - Execute single-wave recovery plan
   - Verify state transitions
   - Verify DynamoDB updates

2. **Multi-Wave Execution**:
   - Execute 3-wave recovery plan
   - Verify sequential wave execution
   - Verify wave results aggregation

3. **Pause/Resume**:
   - Execute plan with pause before wave 2
   - Verify pause state
   - Resume execution
   - Verify wave 2 starts correctly

### Backward Compatibility Tests

1. **Existing API Endpoints**:
   - Test all 47 API endpoints still work
   - Verify response formats unchanged

2. **Frontend Integration**:
   - Test execution list page
   - Test execution details page
   - Test wave status display

---

## Deployment Strategy

### Phase 1: Code Changes

1. **Create new Lambda directory**: `lambda/dr-orchestration-stepfunction/`
2. Copy orchestration code from `lambda/orchestration-stepfunctions/` to new directory
3. Move 4 functions to handlers (execution-handler, query-handler)
4. Update new orchestration Lambda to invoke handlers
5. Add environment variables to CloudFormation
6. Update IAM permissions in CloudFormation
7. **Add new Lambda resource to CloudFormation**
8. **Update package_lambda.py to include new Lambda**

### CloudFormation Updates Required

#### Step 1: Create New Lambda Resource

**File**: `cfn/lambda-stack.yaml`

Add new Lambda function resource (alongside existing `OrchestrationStepFunctionsFunction`):

```yaml
# NEW: Refactored orchestration Lambda (generic, no DRS code)
DrOrchestrationStepFunctionFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-dr-orch-sf-${Environment}"
    Description: "Generic wave-based orchestration (refactored, no DRS code)"
    Runtime: python3.12
    Handler: index.lambda_handler
    Role: !Ref OrchestrationRoleArn
    Code:
      S3Bucket: !Ref SourceBucket
      S3Key: "lambda/dr-orchestration-stepfunction.zip"  # NEW package
    Timeout: 120
    MemorySize: 512
    Environment:
      Variables:
        PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
        RECOVERY_PLANS_TABLE: !Ref RecoveryPlansTableName
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
        EXECUTION_NOTIFICATIONS_TOPIC_ARN: !Ref ExecutionNotificationsTopicArn
        DRS_ALERTS_TOPIC_ARN: !Ref DRSAlertsTopicArn
        # NEW: Handler ARNs for Lambda invocation
        EXECUTION_HANDLER_ARN: !GetAtt ExecutionHandlerFunction.Arn
        QUERY_HANDLER_ARN: !GetAtt QueryHandlerFunction.Arn
    Tags:
      - Key: Project
        Value: !Ref ProjectName
      - Key: Environment
        Value: !Ref Environment

# EXISTING: Keep original Lambda as reference (unchanged)
OrchestrationStepFunctionsFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-orch-sf-${Environment}"
    Description: "Wave-based orchestration with tag-based discovery (ORIGINAL - REFERENCE)"
    # ... existing configuration unchanged ...
```

#### Step 2: Update Step Functions State Machine

**File**: `cfn/step-functions-stack.yaml`

Update the Step Functions state machine to use the NEW Lambda:

```yaml
DROrchestrationStateMachine:
  Type: AWS::StepFunctions::StateMachine
  Properties:
    # ... existing properties ...
    DefinitionSubstitutions:
      # CHANGE: Use new refactored Lambda
      OrchestrationLambdaArn: !GetAtt DrOrchestrationStepFunctionFunction.Arn
      # OLD: OrchestrationLambdaArn: !GetAtt OrchestrationStepFunctionsFunction.Arn
```

#### Step 3: Update QueryHandlerFunction Environment Variables

```yaml
QueryHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    # ... existing properties ...
    Environment:
      Variables:
        # ... existing variables ...
        # NEW: Add execution handler ARN for next wave invocation
        EXECUTION_HANDLER_ARN: !GetAtt ExecutionHandlerFunction.Arn
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
```

#### Step 4: Update ExecutionHandlerFunction Environment Variables

```yaml
ExecutionHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    # ... existing properties ...
    Environment:
      Variables:
        # ... existing variables ...
        # NEW: Add DynamoDB table access
        PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
```

#### Step 5: Update OrchestrationRole IAM Permissions

Add Lambda invoke permissions to the orchestration role:

```yaml
# Add to OrchestrationRole policies
- Effect: Allow
  Action:
    - lambda:InvokeFunction
  Resource:
    - !GetAtt ExecutionHandlerFunction.Arn
    - !GetAtt QueryHandlerFunction.Arn
```

#### Step 6: Update QueryHandlerRole IAM Permissions

```yaml
# Add to QueryHandlerRole policies
- Effect: Allow
  Action:
    - lambda:InvokeFunction
  Resource:
    - !GetAtt ExecutionHandlerFunction.Arn
- Effect: Allow
  Action:
    - dynamodb:GetItem
    - dynamodb:UpdateItem
  Resource:
    - !GetAtt ExecutionHistoryTable.Arn
```

#### Step 7: Update ExecutionHandlerRole IAM Permissions

```yaml
# Add to ExecutionHandlerRole policies
- Effect: Allow
  Action:
    - dynamodb:GetItem
    - dynamodb:Query
  Resource:
    - !GetAtt ProtectionGroupsTable.Arn
- Effect: Allow
  Action:
    - dynamodb:UpdateItem
  Resource:
    - !GetAtt ExecutionHistoryTable.Arn
```

#### Step 8: Update package_lambda.py

**File**: `package_lambda.py`

Add new Lambda to the packaging list:

```python
lambdas = [
    ("query-handler", False),
    ("data-management-handler", False),
    ("execution-handler", False),
    ("frontend-deployer", True),
    ("notification-formatter", False),
    ("orchestration-stepfunctions", False),  # KEEP: Original (reference)
    ("dr-orchestration-stepfunction", False),  # NEW: Refactored (no 's')
]
```

### Rollback Strategy

If issues occur with the new Lambda:

1. **Immediate Rollback**: Update Step Functions to use original Lambda:
   ```yaml
   DefinitionSubstitutions:
     OrchestrationLambdaArn: !GetAtt OrchestrationStepFunctionsFunction.Arn
   ```

2. **Deploy CloudFormation**: `./scripts/deploy.sh test`

3. **Verify**: Original Lambda is back in use

### Cleanup After Success

Once refactored Lambda is validated (after 1-2 weeks):

1. Remove `OrchestrationStepFunctionsFunction` from CloudFormation
2. Remove `lambda/orchestration-stepfunctions/` directory
3. Remove from `package_lambda.py`

### Phase 2: Testing

1. Run unit tests locally
2. Deploy to test environment
3. Run integration tests
4. Verify backward compatibility

### Phase 3: Production Rollout

1. Deploy to test environment first
2. Monitor for 24 hours
3. Deploy to production
4. Monitor CloudWatch metrics

### Rollback Plan

If issues occur:
1. Revert CloudFormation stack to previous version
2. Old code is still in git history
3. No data migration needed (DynamoDB schema unchanged)

---

## Success Criteria

- [ ] Orchestration Lambda has zero DRS API calls
- [ ] All 4 functions moved to appropriate handlers:
  - [ ] `start_wave_recovery()` (~125 lines) → execution-handler
  - [ ] `apply_launch_config_before_recovery()` (~150 lines) → execution-handler
  - [ ] `update_wave_status()` (~346 lines) → query-handler
  - [ ] `query_drs_servers_by_tags()` (~99 lines) → query-handler
- [ ] Helper functions copied to handlers:
  - [ ] `get_account_context()` → both handlers
  - [ ] DynamoDB table getters → both handlers
  - [ ] DRS status constants → query-handler
- [ ] All existing tests pass
- [ ] Integration tests pass
- [ ] Execution behavior identical to before
- [ ] DynamoDB schema unchanged
- [ ] Frontend works without changes
- [ ] CloudWatch logs show handler invocations
- [ ] No performance degradation (±5% execution time)
- [ ] Environment variables configured correctly
- [ ] IAM permissions updated correctly

---

## Out of Scope

**NOT doing in this refactoring:**
- Creating new adapter Lambdas
- Making handlers generic/technology-agnostic
- Extracting ALL DRS code from handlers
- 4-phase lifecycle architecture
- Module factory pattern
- Multi-technology support

**Scope**: ONLY move 4 functions (~720 lines total) from orchestration to handlers:
- `start_wave_recovery()` + `apply_launch_config_before_recovery()` → execution-handler (~275 lines)
- `update_wave_status()` + `query_drs_servers_by_tags()` → query-handler (~445 lines)
