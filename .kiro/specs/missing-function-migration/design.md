# Design Document: Missing Function Migration

## Executive Summary

This design specifies the migration of 36 remaining functions (~4,174 lines) from the monolithic API handler to the decomposed handlers. Originally, 40 functions were identified as missing during the initial decomposition. Since then, 4 functions have been migrated separately (ensure_default_account, get_active_executions_for_plan, get_active_execution_for_protection_group, has_circular_dependencies_by_number), leaving 36 functions to migrate across 9 batches.

The migration follows a 9-batch approach, prioritizing critical functions first (server enrichment, cross-account support, conflict detection) and completing with lower-priority functions (import/export, cleanup).

**Key Design Principles**:
- **Incremental Migration**: 9 batches, test after each, deploy after each
- **Zero Refactoring**: Copy functions as-is, preserve all comments and code style
- **Safety First**: Test coverage 90%+, rollback capability at each batch
- **Dependency Order**: Batches ordered to satisfy function dependencies

**Estimated Effort**: 16 hours (2 days) across 9 batches

## Architecture

### Current State

**Monolithic Handler** (`archive/lambda-handlers/api-handler-monolithic-20260124/index.py`):
- 96 total functions
- 56 functions migrated to decomposed handlers during initial decomposition
- 40 functions originally identified as missing
- 4 functions migrated separately (ensure_default_account, get_active_executions_for_plan, get_active_execution_for_protection_group, has_circular_dependencies_by_number)
- 36 functions remaining to migrate
- Source of truth for missing function implementations

**Decomposed Handlers**:
- **Query Handler**: 12 functions, 256 MB, 60s timeout
- **Execution Handler**: 25 functions, 512 MB, 300s timeout
- **Data Management Handler**: 28 functions, 512 MB, 120s timeout

### Target State (After All 9 Batches)

**After Migration**:
- **Query Handler**: 16 functions (+4 from Batch 7) - 256 MB, 60s timeout
- **Execution Handler**: 37 functions (+12 from Batches 1, 4, 5, 8) - 512 MB, 300s timeout
- **Data Management Handler**: 37 functions (+9 from Batches 6, 9) - 512 MB, 120s timeout
- **Shared Modules**: 15 functions (+15 from Batches 2, 3) - Used by all handlers

**Total Functions**: 105 functions (96 from monolithic + 9 new shared utilities)

### Migration Flow

```
Monolithic Handler (40 originally missing, 4 already migrated, 36 remaining)
    ↓
Batch 1: Server Enrichment (6 functions) → execution-handler
Batch 2: Cross-Account (2 functions) → shared/cross_account.py
Batch 3: Conflict Detection (7 functions) → shared/conflict_detection.py
Batch 4: Wave Execution (4 functions) → execution-handler
Batch 5: Recovery Management (2 functions) → execution-handler
Batch 6: Validation (4 functions) → data-management-handler
Batch 7: Query Functions (4 functions) → query-handler
Batch 8: Execution Cleanup (2 functions) → execution-handler
Batch 9: Import/Export (5 functions) → data-management-handler
    ↓
Decomposed Handlers (36 functions migrated)
```

## Migration Process

### Batch Execution Workflow

Each batch follows this standardized workflow:

```
1. EXTRACT
   ├── Locate functions in monolithic handler by line number
   ├── Copy functions exactly as-is (preserve comments, style, logic)
   └── Paste into target handler at specified location

2. INTEGRATE
   ├── Add required imports to target handler
   ├── Update calling functions to use new functions
   └── Update shared module imports if creating new shared module

3. TEST
   ├── Validate Python syntax: python3 -m py_compile <file>
   ├── Run unit tests: pytest tests/python/unit/ -v
   ├── Run integration tests: pytest tests/integration/ -v
   └── Fix any test failures before proceeding

4. DEPLOY
   ├── Build Lambda packages: python3 package_lambda.py
   ├── Deploy to dev: ./scripts/deploy.sh dev --lambda-only
   └── Verify deployment success in CloudWatch

5. VALIDATE
   ├── Run manual tests for batch-specific functionality
   ├── Check CloudWatch Logs for errors
   ├── Verify no regressions in existing functionality
   └── Document completion in migration tracker

6. PROCEED or ROLLBACK
   ├── If all validations pass → Proceed to next batch
   └── If any validation fails → Rollback and fix issues
```

### Batch Dependencies

```
Batch 1 (Server Enrichment) ─────────────────┐
                                              │
Batch 2 (Cross-Account) ──────┬──────────────┼─→ Batch 4 (Wave Execution)
                               │              │
Batch 3 (Conflict Detection) ─┴──────────────┴─→ Batch 5 (Recovery Management)
                               │                  Batch 6 (Validation)
                               │                  Batch 7 (Query Functions)
                               │                  Batch 8 (Execution Cleanup)
                               └──────────────→ Batch 9 (Import/Export)
```

**Dependency Rules**:
- Batch 2 (Cross-Account) must complete before Batches 3, 4, 5, 6, 7
- Batch 3 (Conflict Detection) must complete before Batches 4, 9
- Batches 1, 8 have no dependencies (can be done anytime)
- Batch 9 depends on Batch 3 for conflict detection during import

### Function Extraction Guidelines

**DO**:
- ✅ Copy functions exactly as-is from monolithic handler
- ✅ Preserve all comments (even if they seem outdated)
- ✅ Preserve all code style (spacing, indentation, naming)
- ✅ Preserve all error handling and logging
- ✅ Use exact line numbers from FUNCTION_MIGRATION_PLAN.md

**DON'T**:
- ❌ Refactor code during migration
- ❌ Remove or modify comments
- ❌ Change variable names or function signatures
- ❌ Add new features or improvements
- ❌ Optimize or simplify logic

**Rationale**: Migration first, refactoring later. This minimizes risk and ensures correctness.

## Components and Interfaces

### Batch 1: Server Enrichment Functions

**Target**: execution-handler
**Location**: After `get_execution_details()` function
**Functions**: 6 functions, ~840 lines

**Component Interface**:
```python
def get_server_details_map(server_ids: List[str], region: str) -> Dict[str, Dict]:
    """
    Gets detailed server information for list of IDs.
    
    Args:
        server_ids: List of DRS source server IDs
        region: AWS region
        
    Returns:
        Dict mapping server ID to server details (name, hostname, IP, etc.)
    """
    pass

def get_recovery_instances_for_wave(wave: Dict, region: str) -> List[Dict]:
    """
    Gets recovery instance details for a wave.
    
    Args:
        wave: Wave object with serverIds
        region: AWS region
        
    Returns:
        List of recovery instance details
    """
    pass

def enrich_execution_with_server_details(execution: Dict, region: str) -> Dict:
    """
    Enriches execution data with server details.
    
    Args:
        execution: Execution object
        region: AWS region
        
    Returns:
        Enriched execution object with server metadata
    """
    pass

def reconcile_wave_status_with_drs(wave: Dict, region: str) -> Dict:
    """
    Reconciles wave status with real-time DRS data.
    
    Args:
        wave: Wave object
        region: AWS region
        
    Returns:
        Updated wave object with reconciled status
    """
    pass

def recalculate_execution_status(execution: Dict) -> str:
    """
    Recalculates overall execution status from wave statuses.
    
    Args:
        execution: Execution object with waves
        
    Returns:
        Calculated execution status (IN_PROGRESS, COMPLETED, FAILED, etc.)
    """
    pass

def get_execution_details_realtime(execution_id: str, region: str) -> Dict:
    """
    Gets real-time execution data (5-15s response time).
    
    Args:
        execution_id: Execution ID
        region: AWS region
        
    Returns:
        Execution object with real-time DRS data
    """
    pass
```

**Integration Points**:
- `get_execution_details()` calls `enrich_execution_with_server_details()`
- `get_execution_details_realtime()` calls `reconcile_wave_status_with_drs()`
- All functions use existing DRS client creation

### Batch 2: Cross-Account Support

**Target**: `lambda/shared/cross_account.py` (new file)
**Functions**: 2 functions, ~295 lines

**Component Interface**:
```python
def determine_target_account_context(event: Dict) -> Dict:
    """
    Determines target account for cross-account operations.
    
    Args:
        event: API Gateway event or direct invocation payload
        
    Returns:
        Dict with accountId, roleArn, externalId for cross-account operations
    """
    pass

def create_drs_client(region: str, account_context: Dict = None):
    """
    Creates DRS client with optional cross-account role assumption.
    
    Args:
        region: AWS region
        account_context: Optional account context from determine_target_account_context()
        
    Returns:
        boto3 DRS client (cross-account if account_context provided)
    """
    pass
```

**Integration Points**:
- All 3 handlers import: `from shared.cross_account import determine_target_account_context, create_drs_client`
- All DRS client creation calls updated to use `create_drs_client()`
- Replaces inline DRS client creation logic

### Batch 3: Conflict Detection

**Target**: `lambda/shared/conflict_detection.py` (new file)
**Functions**: 7 functions, ~545 lines

**Component Interface**:
```python
def get_servers_in_active_drs_jobs(region: str, account_context: Dict = None) -> Set[str]:
    """
    Gets servers in active DRS jobs.
    
    Args:
        region: AWS region
        account_context: Optional cross-account context
        
    Returns:
        Set of server IDs in active DRS jobs
    """
    pass

def get_all_active_executions() -> List[Dict]:
    """
    Gets all active executions from DynamoDB.
    
    Returns:
        List of active execution objects
    """
    pass

def get_servers_in_active_executions() -> Set[str]:
    """
    Gets servers in active executions.
    
    Returns:
        Set of server IDs in active executions
    """
    pass

def resolve_pg_servers_for_conflict_check(protection_group: Dict, region: str) -> Set[str]:
    """
    Resolves protection group servers for conflict checking.
    
    Args:
        protection_group: Protection group object
        region: AWS region
        
    Returns:
        Set of server IDs in protection group
    """
    pass

def check_server_conflicts(server_ids: Set[str], region: str) -> Dict:
    """
    Core conflict detection logic.
    
    Args:
        server_ids: Set of server IDs to check
        region: AWS region
        
    Returns:
        Dict with hasConflicts (bool) and conflicts (list of conflict details)
    """
    pass

def get_plans_with_conflicts(region: str) -> List[Dict]:
    """
    Gets plans with server conflicts.
    
    Args:
        region: AWS region
        
    Returns:
        List of recovery plans with conflicts
    """
    pass

def has_circular_dependencies(waves: List[Dict]) -> bool:
    """
    Detects circular dependencies by wave ID.
    
    Args:
        waves: List of wave objects with dependencies
        
    Returns:
        True if circular dependencies detected
    """
    pass
```

**Integration Points**:
- data-management-handler imports for protection group/recovery plan creation
- execution-handler imports for execution start validation
- Replaces inline conflict detection logic

### Batch 4: Wave Execution Functions

**Target**: execution-handler
**Location**: Before `start_execution()` function
**Functions**: 4 functions, ~710 lines

**Component Interface**:
```python
def check_existing_recovery_instances(server_ids: List[str], region: str) -> Dict:
    """
    Checks for existing recovery instances before execution.
    
    Args:
        server_ids: List of server IDs
        region: AWS region
        
    Returns:
        Dict with existingInstances (list) and canProceed (bool)
    """
    pass

def initiate_wave(wave: Dict, execution_id: str, region: str) -> Dict:
    """
    Initializes wave execution with DRS job creation.
    
    Args:
        wave: Wave object
        execution_id: Execution ID
        region: AWS region
        
    Returns:
        Updated wave object with DRS job IDs
    """
    pass

def get_server_launch_configurations(server_ids: List[str], region: str) -> Dict[str, Dict]:
    """
    Retrieves launch configurations for servers in a wave.
    
    Args:
        server_ids: List of server IDs
        region: AWS region
        
    Returns:
        Dict mapping server ID to launch configuration
    """
    pass

def start_drs_recovery_with_retry(server_ids: List[str], region: str, max_retries: int = 3) -> Dict:
    """
    Starts DRS recovery with automatic retry logic.
    
    Args:
        server_ids: List of server IDs
        region: AWS region
        max_retries: Maximum retry attempts
        
    Returns:
        Dict with jobId and status
    """
    pass
```

**Integration Points**:
- `start_execution()` calls these functions for wave initialization
- Uses cross-account support from Batch 2
- Uses conflict detection from Batch 3

### Batch 5: Recovery Instance Management

**Target**: execution-handler
**Location**: After termination functions
**Functions**: 2 functions, ~600 lines

**Component Interface**:
```python
def get_termination_job_status(job_id: str, region: str) -> Dict:
    """
    Gets status of recovery instance termination job.
    
    Args:
        job_id: DRS termination job ID
        region: AWS region
        
    Returns:
        Dict with status, progress, and completion details
    """
    pass

def apply_launch_config_to_servers(server_ids: List[str], launch_config: Dict, region: str) -> Dict:
    """
    Applies launch configuration to servers before recovery.
    
    Args:
        server_ids: List of server IDs
        launch_config: Launch configuration settings
        region: AWS region
        
    Returns:
        Dict with success (bool) and failed servers (list)
    """
    pass
```

**Integration Points**:
- Termination workflow calls `get_termination_job_status()` for status tracking
- Wave execution calls `apply_launch_config_to_servers()` before recovery

### Batch 6: Validation Functions

**Target**: data-management-handler
**Location**: After existing validation functions
**Functions**: 4 functions, ~255 lines

**Component Interface**:
```python
def validate_server_replication_states(server_ids: List[str], region: str) -> Dict:
    """
    Validates server replication states before execution.
    
    Args:
        server_ids: List of server IDs
        region: AWS region
        
    Returns:
        Dict with valid (bool) and invalidServers (list with reasons)
    """
    pass

def validate_server_assignments(server_ids: List[str], protection_group_id: str) -> Dict:
    """
    Validates server assignments to protection groups.
    
    Args:
        server_ids: List of server IDs
        protection_group_id: Protection group ID
        
    Returns:
        Dict with valid (bool) and invalidAssignments (list)
    """
    pass

def validate_servers_exist_in_drs(server_ids: List[str], region: str) -> Dict:
    """
    Validates servers exist in DRS before assignment.
    
    Args:
        server_ids: List of server IDs
        region: AWS region
        
    Returns:
        Dict with valid (bool) and missingServers (list)
    """
    pass

def validate_and_get_source_servers(server_ids: List[str], region: str) -> List[Dict]:
    """
    Validates and retrieves source servers.
    
    Args:
        server_ids: List of server IDs
        region: AWS region
        
    Returns:
        List of validated source server objects
    """
    pass
```

**Integration Points**:
- Protection group creation calls validation functions
- Recovery plan creation calls validation functions

### Batch 7: Query Functions

**Target**: query-handler
**Location**: After existing query functions
**Functions**: 4 functions, ~355 lines

**Component Interface**:
```python
def query_drs_servers_by_tags(tags: Dict[str, str], region: str) -> List[Dict]:
    """
    Queries DRS servers by tags for tag-based selection.
    
    Args:
        tags: Dict of tag key-value pairs (AND logic)
        region: AWS region
        
    Returns:
        List of servers matching all tags
    """
    pass

def get_protection_group_servers(protection_group_id: str) -> List[Dict]:
    """
    Gets servers in a protection group.
    
    Args:
        protection_group_id: Protection group ID
        
    Returns:
        List of server objects in protection group
    """
    pass

def get_drs_source_server_details(server_ids: List[str], region: str) -> List[Dict]:
    """
    Gets detailed info for specific source servers.
    
    Args:
        server_ids: List of server IDs
        region: AWS region
        
    Returns:
        List of detailed server objects
    """
    pass

def validate_target_account(account_id: str) -> bool:
    """
    Validates target account exists.
    
    Args:
        account_id: AWS account ID
        
    Returns:
        True if account exists in configuration
    """
    pass
```

**Integration Points**:
- Tag resolution endpoint calls `query_drs_servers_by_tags()`
- Protection group details endpoint calls `get_protection_group_servers()`

### Batch 8: Execution Cleanup

**Target**: execution-handler
**Location**: After execution management functions
**Functions**: 2 functions, ~275 lines

**Component Interface**:
```python
def delete_completed_executions(max_age_days: int = 90) -> Dict:
    """
    Deletes old completed executions.
    
    Args:
        max_age_days: Maximum age in days for completed executions
        
    Returns:
        Dict with deletedCount and failedDeletions (list)
    """
    pass

def delete_executions_by_ids(execution_ids: List[str]) -> Dict:
    """
    Deletes specific executions by ID list.
    
    Args:
        execution_ids: List of execution IDs to delete
        
    Returns:
        Dict with deletedCount and failedDeletions (list)
    """
    pass
```

**Integration Points**:
- DELETE endpoint routing for bulk deletion
- Scheduled cleanup job (future enhancement)

### Batch 9: Import/Export Functions

**Target**: data-management-handler
**Location**: End of file
**Functions**: 5 functions, ~299 lines

**Component Interface**:
```python
def export_configuration() -> Dict:
    """
    Exports protection groups and recovery plans.
    
    Returns:
        Dict with protectionGroups (list) and recoveryPlans (list)
    """
    pass

def import_configuration(config: Dict) -> Dict:
    """
    Imports protection groups and recovery plans.
    
    Args:
        config: Configuration dict with protectionGroups and recoveryPlans
        
    Returns:
        Dict with importedPGs (count), importedRPs (count), errors (list)
    """
    pass

def _get_existing_protection_groups() -> List[Dict]:
    """
    Gets existing protection groups for import.
    
    Returns:
        List of existing protection group objects
    """
    pass

def _get_existing_recovery_plans() -> List[Dict]:
    """
    Gets existing recovery plans for import.
    
    Returns:
        List of existing recovery plan objects
    """
    pass

def _get_active_execution_servers() -> Set[str]:
    """
    Gets servers in active executions for import validation.
    
    Returns:
        Set of server IDs in active executions
    """
    pass
```

**Integration Points**:
- Export endpoint calls `export_configuration()`
- Import endpoint calls `import_configuration()`
- Uses conflict detection from Batch 3

## Data Models

### Migration Batch

```python
{
    "batchNumber": 1,
    "batchName": "Server Enrichment",
    "priority": 1,
    "targetHandler": "execution-handler",
    "functionCount": 6,
    "lineCount": 840,
    "estimatedHours": 2.0,
    "dependencies": [],
    "functions": [
        {
            "name": "get_server_details_map",
            "lineNumber": 5299,
            "lineCount": 150,
            "purpose": "Gets detailed server information for list of IDs"
        }
    ],
    "status": "NOT_STARTED",
    "testsPassing": false,
    "deployed": false
}
```

### Function Migration Record

```python
{
    "functionName": "get_server_details_map",
    "sourceFile": "archive/lambda-handlers/api-handler-monolithic-20260124/index.py",
    "sourceLineNumber": 5299,
    "targetFile": "lambda/execution-handler/index.py",
    "targetLineNumber": null,  # Set after migration
    "batchNumber": 1,
    "migrationDate": null,  # Set after migration
    "testsPassing": false,
    "deployed": false,
    "comments": "Preserves all original comments and code style"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Function Preservation

*For any* migrated function, the function signature, logic, comments, and code style should be identical to the monolithic handler version.

**Validates: Requirements 10.2, 10.3**

### Property 2: Test Coverage Preservation

*For any* batch migration, all existing tests should continue to pass after migration.

**Validates: Requirements 10.6, 11.1**

### Property 3: Server Enrichment Completeness

*For any* execution details request, the response should include server names, IP addresses, and recovery instance details when available.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 4: Cross-Account Client Creation

*For any* DRS operation with target account specified, the DRS client should assume the cross-account role.

**Validates: Requirements 2.2**

### Property 5: Conflict Detection Accuracy

*For any* protection group creation or execution start, the system should detect conflicts with active executions and active DRS jobs.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 6: Wave Execution Retry

*For any* DRS API failure during wave execution, the system should retry with exponential backoff up to the retry limit.

**Validates: Requirements 4.4, 4.5**

### Property 7: Validation Rejection

*For any* server assignment with invalid replication state or non-existent server, the system should reject the operation with descriptive error.

**Validates: Requirements 6.1, 6.2, 6.4**

### Property 8: Tag Query AND Logic

*For any* tag-based query with multiple tags, the system should return only servers matching all specified tags.

**Validates: Requirements 7.1**

### Property 9: Execution Cleanup Preservation

*For any* execution cleanup operation, the system should preserve all active executions and only delete completed executions.

**Validates: Requirements 8.3**

### Property 10: Import Conflict Detection

*For any* configuration import, the system should detect conflicts with existing resources and active executions before creating resources.

**Validates: Requirements 9.3, 9.4**

## Error Handling

### Migration Errors

**Syntax Errors**:
- Validate Python syntax after each function extraction
- Run `python3 -m py_compile` on target file
- Fix syntax errors before proceeding to next function

**Import Errors**:
- Verify all imports exist in target handler
- Add missing imports from monolithic handler
- Test imports with `python3 -c "import lambda.execution_handler.index"`

**Test Failures**:
- Run full test suite after each batch
- Fix test failures before deploying
- Do not proceed to next batch until all tests pass

### Runtime Errors

**DRS API Errors**:
- Retry with exponential backoff (1s, 2s, 4s, 8s)
- Log error details with server IDs and region
- Return descriptive error to caller after retry limit

**DynamoDB Errors**:
- Retry with exponential backoff for throttling
- Log error details with table name and operation
- Return descriptive error to caller after retry limit

**Cross-Account Errors**:
- Validate account context before role assumption
- Log error details with account ID and role ARN
- Return descriptive error indicating cross-account failure

**Conflict Detection Errors**:
- Log conflict details with server IDs and conflicting resources
- Return error with list of conflicts
- Do not proceed with operation if conflicts detected

## Testing Strategy

### Unit Testing

**Test Coverage**:
- 90%+ coverage for all migrated functions
- Test each function in isolation with mocked dependencies
- Test error conditions and edge cases

**Test Organization**:
- `tests/python/unit/test_cross_account.py` - Cross-account support tests
- `tests/python/unit/test_conflict_detection.py` - Conflict detection tests
- Existing handler test files extended with new function tests

**Test Patterns**:
```python
def test_get_server_details_map_returns_server_metadata():
    """Test that get_server_details_map returns name, IP, hostname."""
    server_ids = ["s-123", "s-456"]
    region = "us-east-1"
    
    result = get_server_details_map(server_ids, region)
    
    assert "s-123" in result
    assert "name" in result["s-123"]
    assert "ipAddress" in result["s-123"]
    assert "hostname" in result["s-123"]

def test_check_server_conflicts_detects_active_execution():
    """Test that check_server_conflicts detects servers in active executions."""
    server_ids = {"s-123", "s-456"}
    region = "us-east-1"
    
    # Mock active execution with s-123
    mock_active_execution(server_ids=["s-123"])
    
    result = check_server_conflicts(server_ids, region)
    
    assert result["hasConflicts"] is True
    assert len(result["conflicts"]) == 1
    assert "s-123" in result["conflicts"][0]["serverIds"]
```

### Integration Testing

**Test Coverage**:
- Test each batch after migration
- Test handler endpoints with real DynamoDB and DRS API (mocked)
- Test cross-handler workflows

**Test Scripts**:
- `scripts/test-query-handler.sh` - Query handler integration tests
- `scripts/test-execution-handler.sh` - Execution handler integration tests
- `scripts/test-data-management-handler.sh` - Data management handler integration tests

**Test Patterns**:
```bash
# Test server enrichment (Batch 1)
curl -X GET "https://api-dev.example.com/executions/{id}" \
  -H "Authorization: Bearer $TOKEN"
# Verify response includes server names, IPs, recovery instances

# Test conflict detection (Batch 3)
curl -X POST "https://api-dev.example.com/protection-groups" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"groupName":"Test","region":"us-east-1","serverIds":["s-123"]}'
# Verify conflict error if s-123 in active execution

# Test wave execution (Batch 4)
curl -X POST "https://api-dev.example.com/recovery-plans/{id}/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"isDrill":true}'
# Verify wave execution starts successfully
```

### End-to-End Testing

**Test Coverage**:
- Complete DR workflow: Create PG → Create RP → Execute → Terminate
- Execution details page displays complete server information
- Wave execution completes end-to-end
- Conflict detection prevents invalid operations

**Test Scenarios**:
1. **Server Enrichment E2E**:
   - Start DR execution
   - View execution details page
   - Verify server names, IPs, recovery instances displayed
   - Verify wave status reconciliation works

2. **Conflict Detection E2E**:
   - Start DR execution
   - Attempt to create protection group with same servers
   - Verify conflict error returned
   - Verify execution continues unaffected

3. **Wave Execution E2E**:
   - Create recovery plan with 3 waves
   - Start DR execution
   - Verify waves execute sequentially
   - Verify DRS recovery jobs created
   - Verify launch configurations applied

### Property-Based Testing

**Test Configuration**:
- Minimum 100 iterations per property test
- Use `hypothesis` library for Python
- Tag each test with property number and feature name

**Property Test Examples**:
```python
from hypothesis import given, strategies as st

@given(st.lists(st.text(min_size=5, max_size=20), min_size=1, max_size=10))
def test_property_1_function_preservation(server_ids):
    """
    Property 1: Function Preservation
    For any list of server IDs, get_server_details_map should return
    a dict with the same keys as input server IDs.
    
    Feature: missing-function-migration, Property 1
    """
    region = "us-east-1"
    result = get_server_details_map(server_ids, region)
    
    assert set(result.keys()) == set(server_ids)

@given(st.sets(st.text(min_size=5, max_size=20), min_size=1, max_size=10))
def test_property_5_conflict_detection_accuracy(server_ids):
    """
    Property 5: Conflict Detection Accuracy
    For any set of server IDs, if any server is in an active execution,
    check_server_conflicts should detect the conflict.
    
    Feature: missing-function-migration, Property 5
    """
    region = "us-east-1"
    
    # Create active execution with first server
    first_server = list(server_ids)[0]
    mock_active_execution(server_ids=[first_server])
    
    result = check_server_conflicts(server_ids, region)
    
    assert result["hasConflicts"] is True
    assert any(first_server in conflict["serverIds"] for conflict in result["conflicts"])
```

### Deployment Testing

**Test After Each Batch**:
1. Run unit tests: `pytest tests/python/unit/ -v`
2. Run integration tests: `pytest tests/integration/ -v`
3. Deploy to dev: `./scripts/deploy.sh dev --lambda-only`
4. Run manual tests for batch-specific functionality
5. Verify no errors in CloudWatch Logs
6. Proceed to next batch only if all tests pass

**Rollback Testing**:
- Test rollback procedure for each batch
- Verify monolithic handler still works if rollback needed
- Document rollback steps in migration plan

## Deployment Strategy

### Development Environment

**Deployment Command**:
```bash
./scripts/deploy.sh dev --lambda-only
```

**Deployment Validation**:
```bash
# Verify Lambda function updated
aws lambda get-function --function-name aws-drs-orchestration-<handler>-dev \
  --query 'Configuration.[FunctionName,LastModified,CodeSize]'

# Check CloudWatch Logs
aws logs tail /aws/lambda/aws-drs-orchestration-<handler>-dev --since 5m

# Test API endpoints
./scripts/test-<handler>.sh
```

### Rollback Procedures

**Batch-Level Rollback**:
1. Identify failed batch number
2. Revert code changes: `git revert <commit-hash>`
3. Redeploy: `./scripts/deploy.sh dev --lambda-only`
4. Verify rollback: Run integration tests
5. Document failure reason and fix approach

**Complete Rollback** (if multiple batches fail):
1. Restore monolithic handler from archive
2. Update CloudFormation to route all endpoints to monolithic handler
3. Deploy: `./scripts/deploy.sh dev`
4. Verify all 48 endpoints work
5. Document lessons learned

### Production Deployment

**Prerequisites**:
- All 9 batches complete in dev
- All 800+ tests passing
- Manual testing complete
- Stakeholder approval obtained

**Deployment Steps**:
1. Deploy to staging environment
2. Run full test suite in staging
3. Perform manual testing in staging
4. Schedule production deployment window
5. Deploy to production: `./scripts/deploy.sh prod --lambda-only`
6. Monitor CloudWatch metrics for 24 hours
7. Verify no increase in error rates

## Monitoring and Observability

### CloudWatch Metrics

**Per-Handler Metrics**:
- Invocation count
- Error count and error rate
- Duration (p50, p95, p99)
- Throttles
- Concurrent executions

**Custom Metrics**:
- Server enrichment success rate (Batch 1)
- Cross-account operation success rate (Batch 2)
- Conflict detection accuracy (Batch 3)
- Wave execution success rate (Batch 4)
- DRS API retry count (Batch 4)

### CloudWatch Alarms

**Critical Alarms**:
- Error rate > 5% for any handler
- Duration p95 > 10 seconds for any handler
- Throttles > 0 for any handler

**Warning Alarms**:
- Error rate > 1% for any handler
- Duration p95 > 5 seconds for any handler

### Logging Strategy

**Log Levels**:
- ERROR: Function failures, DRS API errors, validation failures
- WARN: Retry attempts, missing data, deprecated usage
- INFO: Function entry/exit, major operations, batch completion
- DEBUG: Detailed execution flow, variable values (dev only)

**Log Format**:
```json
{
  "timestamp": "2026-01-24T12:00:00Z",
  "level": "INFO",
  "handler": "execution-handler",
  "function": "get_server_details_map",
  "batch": 1,
  "message": "Retrieved server details for 10 servers",
  "serverCount": 10,
  "region": "us-east-1",
  "duration_ms": 1250
}
```

## Success Criteria

### Batch Completion Criteria

Each batch is considered complete when:
- ✅ All functions extracted and integrated
- ✅ All unit tests passing (90%+ coverage)
- ✅ All integration tests passing
- ✅ Deployed to dev environment
- ✅ Manual testing complete
- ✅ No errors in CloudWatch Logs
- ✅ Batch-specific functionality verified

### Overall Migration Completion

The migration is considered complete when:
- ✅ All 9 batches complete
- ✅ All 36 functions migrated
- ✅ All 800+ tests passing
- ✅ Execution details page shows complete server information
- ✅ Wave execution works end-to-end
- ✅ Conflict detection prevents invalid operations
- ✅ Cross-account operations work
- ✅ Import/export functionality restored
- ✅ No regressions in existing functionality
- ✅ Production deployment successful

## Risk Mitigation

### Identified Risks

1. **Function Dependencies**: Some functions may depend on others not yet migrated
   - **Mitigation**: Batch order follows dependency graph

2. **Test Coverage Gaps**: Some functions may not have adequate test coverage
   - **Mitigation**: Add tests during migration, aim for 90%+ coverage

3. **Breaking Changes**: Migration may break existing functionality
   - **Mitigation**: Test after each batch, rollback capability

4. **Time Estimates**: Actual time may exceed estimates
   - **Mitigation**: Buffer time built into estimates, prioritize critical batches

5. **DRS API Changes**: DRS API behavior may differ from monolithic handler expectations
   - **Mitigation**: Extensive integration testing with real DRS API

### Contingency Plans

**If Batch Fails**:
1. Rollback code changes
2. Analyze failure root cause
3. Fix issues in isolation
4. Re-test before re-attempting batch
5. Update migration plan with lessons learned

**If Multiple Batches Fail**:
1. Pause migration
2. Conduct root cause analysis
3. Consider alternative approach
4. Update design document
5. Resume with revised plan

**If Production Deployment Fails**:
1. Immediate rollback to monolithic handler
2. Incident response team activation
3. Root cause analysis
4. Fix in dev/staging
5. Re-deploy after validation

## Future Enhancements

### Post-Migration Refactoring

After all 9 batches complete and production deployment succeeds:

1. **Code Deduplication**: Identify and eliminate duplicate code across handlers
2. **Performance Optimization**: Profile and optimize slow functions
3. **Error Handling Improvements**: Standardize error handling patterns
4. **Logging Enhancements**: Add structured logging with correlation IDs
5. **Test Coverage Improvements**: Increase coverage to 95%+

### Additional Features

1. **Scheduled Execution Cleanup**: Automated cleanup of old executions
2. **Configuration Versioning**: Track configuration changes over time
3. **Audit Logging**: Comprehensive audit trail for all operations
4. **Metrics Dashboard**: Real-time dashboard for DR operations
5. **Alerting Improvements**: More granular alerting for specific failure modes

---

## Appendix: Batch Summary

| Batch | Name | Functions | Lines | Hours | Target | Dependencies |
|-------|------|-----------|-------|-------|--------|--------------|
| 1 | Server Enrichment | 6 | 840 | 2.0 | execution-handler | None |
| 2 | Cross-Account | 2 | 295 | 1.5 | shared/cross_account.py | None |
| 3 | Conflict Detection | 7 | 545 | 2.0 | shared/conflict_detection.py | Batch 2 |
| 4 | Wave Execution | 4 | 710 | 2.5 | execution-handler | Batch 2, 3 |
| 5 | Recovery Management | 2 | 600 | 1.5 | execution-handler | Batch 1, 2 |
| 6 | Validation | 4 | 255 | 1.5 | data-management-handler | Batch 2 |
| 7 | Query Functions | 4 | 355 | 1.5 | query-handler | Batch 2 |
| 8 | Execution Cleanup | 2 | 275 | 1.0 | execution-handler | None |
| 9 | Import/Export | 5 | 299 | 2.0 | data-management-handler | Batch 3 |
| **TOTAL** | **9 Batches** | **36** | **4,174** | **16.0** | **3 handlers + 2 shared** | - |


