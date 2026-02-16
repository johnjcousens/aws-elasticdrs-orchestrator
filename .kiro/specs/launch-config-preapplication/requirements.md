# Launch Configuration Pre-Application - Requirements

## Feature Name
launch-config-preapplication

## Overview
Pre-apply and persist DRS launch configurations and launch template settings when protection groups are created or updated, eliminating the slow runtime application during wave execution. This optimization stores validated launch settings in DynamoDB so wave execution can immediately start recovery without configuration delays.

## Problem Statement
Currently, launch configurations and launch template settings are applied at runtime during wave execution, which is very slow. Each wave must:
1. Fetch launch configurations from DRS API
2. Validate settings
3. Apply configurations to each server
4. Wait for DRS to process the updates
5. Then start recovery

This adds significant latency to every wave execution, especially for large protection groups with many servers.

## User Stories

### 1. As a DR administrator
I want launch configurations to be pre-applied when I create or update a protection group, so that wave execution starts immediately without configuration delays.

**Acceptance Criteria:**
- Launch configurations are applied during protection group create/update operations
- Launch template settings are applied during protection group create/update operations
- Applied configurations are validated before persistence
- Configuration status is stored in DynamoDB for quick lookup
- Wave execution checks DynamoDB status instead of applying configs at runtime

### 2. As a DR administrator
I want to see the configuration status of my protection group, so I know if launch settings are ready for recovery.

**Acceptance Criteria:**
- Protection group details show launch configuration status
- Status indicates: "ready", "pending", "failed", or "not_configured"
- Last configuration timestamp is displayed
- Configuration errors are visible if application failed

### 3. As a DR administrator
I want to re-apply launch configurations if they fail or become outdated, so I can ensure my protection group is always ready for recovery.

**Acceptance Criteria:**
- Manual re-apply operation available via API
- Re-apply validates and updates all server configurations
- Status updates reflect the re-apply operation
- Errors are captured and displayed

### 4. As a system
I want wave execution to verify configuration status before starting recovery, so I can detect and handle configuration drift or failures.

**Acceptance Criteria:**
- Wave execution checks DynamoDB for configuration status
- If status is "ready", wave starts immediately
- If status is "pending" or "failed", wave applies configs before starting
- Configuration drift detection triggers re-application
- Status updates are atomic and consistent

### 5. As a developer
I want comprehensive test coverage for the new architecture, so I can ensure reliability and catch regressions.

**Acceptance Criteria:**
- Unit tests cover all new configuration service functions
- Property-based tests validate stateful operations
- Integration tests verify end-to-end workflows
- Performance tests validate optimization claims
- Existing tests are updated to reflect new architecture
- All three invocation methods (Frontend, API, Direct) are tested

## Technical Requirements

### 1. Multi-Invocation Support
All operations must support three invocation methods:

**Frontend via API Gateway:**
```python
# Event structure from API Gateway
{
    "httpMethod": "POST",
    "path": "/protection-groups/pg-123/apply-launch-configs",
    "headers": {"Authorization": "Bearer <cognito-token>"},
    "body": "{\"force\": false}",
    "requestContext": {
        "authorizer": {
            "claims": {"cognito:username": "user@example.com"}
        }
    }
}
```

**API-Only via API Gateway:**
```python
# Same structure as Frontend, but may use IAM auth
{
    "httpMethod": "POST",
    "path": "/protection-groups/pg-123/apply-launch-configs",
    "headers": {"Authorization": "AWS4-HMAC-SHA256 ..."},
    "body": "{\"force\": false}",
    "requestContext": {
        "identity": {"userArn": "arn:aws:iam::..."}
    }
}
```

**Direct Lambda Invocation:**
```python
# Event structure for direct invocation
{
    "operation": "apply_launch_configs",
    "groupId": "pg-123",
    "force": false,
    "invokedBy": "OrchestrationRole"
}
```

### 2. DynamoDB Schema Extension
Add launch configuration status tracking to protection groups table (camelCase convention):

```python
{
    "groupId": "pg-abc123",
    "launchConfigStatus": {
        "status": "ready",  # ready | pending | failed | not_configured
        "lastApplied": "2025-02-16T10:30:00Z",
        "appliedBy": "user@example.com",
        "serverConfigs": {
            "s-1234567890abcdef0": {
                "status": "ready",
                "lastApplied": "2025-02-16T10:30:00Z",
                "configHash": "sha256:abc123...",
                "errors": []
            }
        },
        "errors": []
    }
}
```

**Schema Convention**: All DynamoDB attributes use camelCase (groupId, planId, executionId, launchConfigStatus) for consistency with existing tables and frontend.

### 2. Configuration Application Service
Create shared utility for applying launch configurations:

```python
# lambda/shared/launch_config_service.py

def apply_launch_configs_to_group(
    group_id: str,
    region: str,
    server_ids: List[str],
    launch_configs: Dict[str, Dict]
) -> Dict:
    """
    Apply launch configurations to all servers in a protection group.
    
    Returns:
        {
            "status": "ready" | "failed",
            "serverConfigs": {...},
            "errors": []
        }
    """
    pass

def validate_and_persist_config_status(
    group_id: str,
    config_status: Dict
) -> None:
    """Persist configuration status to DynamoDB."""
    pass

def get_config_status(group_id: str) -> Dict:
    """Retrieve configuration status from DynamoDB."""
    pass
```

### 3. Protection Group Operations Integration
Modify data-management-handler to apply configs on create/update:

- On `create_protection_group`: Apply launch configs after group creation
- On `update_protection_group`: Re-apply launch configs if servers or configs changed
- On `add_servers_to_group`: Apply launch configs to new servers
- On `remove_servers_from_group`: Update config status

### 4. Wave Execution Optimization
Modify execution-handler to check config status before starting wave:

```python
def start_wave_recovery(state: Dict, wave_number: int) -> None:
    """Start wave recovery with config status check."""
    
    # Check configuration status
    config_status = get_config_status(group_id)
    
    if config_status["status"] == "ready":
        # Start recovery immediately
        start_drs_recovery_for_wave(...)
    else:
        # Apply configs first, then start recovery
        apply_launch_configs_to_group(...)
        start_drs_recovery_for_wave(...)
```

### 5. Configuration Drift Detection
Implement hash-based drift detection:

- Calculate hash of launch configuration settings
- Store hash in DynamoDB with config status
- On wave execution, compare current config hash with stored hash
- If mismatch detected, re-apply configurations

### 6. Error Handling and Retry
- Capture configuration application errors per server
- Store errors in DynamoDB for visibility
- Implement retry logic with exponential backoff
- Provide manual re-apply operation for failed configs

## Invocation Methods

This feature must support all three invocation methods used by the DR Orchestration Platform:

### 1. Frontend via API Gateway
- User initiates operations through CloudScape UI
- API Gateway authenticates via Cognito
- API Gateway invokes Lambda with HTTP event structure
- Response formatted for frontend consumption

### 2. API-Only via API Gateway
- External systems call API endpoints directly
- API Gateway authenticates via Cognito or IAM
- Standard REST API request/response format
- Supports automation and integration scenarios

### 3. Direct Lambda Invocation
- Internal services invoke Lambda directly using OrchestrationRole
- No API Gateway involved
- Event structure matches direct invocation format
- Used by Step Functions and internal orchestration

## API Changes

### New Endpoints

#### Apply Launch Configurations
```
POST /protection-groups/{groupId}/apply-launch-configs
```

**Invocation Methods:**
- Frontend: User clicks "Apply Configurations" button
- API: `POST https://api-url/dev/protection-groups/{groupId}/apply-launch-configs`
- Direct: Lambda invocation with operation `apply_launch_configs`

Request:
```json
{
    "force": false  // Force re-apply even if status is "ready"
}
```

Response:
```json
{
    "groupId": "pg-abc123",
    "status": "ready",
    "appliedServers": 10,
    "failedServers": 0,
    "errors": []
}
```

#### Get Configuration Status
```
GET /protection-groups/{groupId}/launch-config-status
```

**Invocation Methods:**
- Frontend: Displayed in protection group details page
- API: `GET https://api-url/dev/protection-groups/{groupId}/launch-config-status`
- Direct: Lambda invocation with operation `get_launch_config_status`

Response:
```json
{
    "groupId": "pg-abc123",
    "status": "ready",
    "lastApplied": "2025-02-16T10:30:00Z",
    "appliedBy": "user@example.com",
    "serverConfigs": {
        "s-1234567890abcdef0": {
            "status": "ready",
            "lastApplied": "2025-02-16T10:30:00Z",
            "configHash": "sha256:abc123...",
            "errors": []
        }
    },
    "errors": []
}
```

### Modified Endpoints

#### Create Protection Group
Add automatic launch config application after group creation.

**Invocation Methods:**
- Frontend: User creates protection group via UI
- API: `POST https://api-url/dev/protection-groups`
- Direct: Lambda invocation with operation `create_protection_group`

**Behavior:** After successful group creation, automatically apply launch configurations to all servers.

#### Update Protection Group
Add automatic launch config re-application if servers or configs changed.

**Invocation Methods:**
- Frontend: User updates protection group via UI
- API: `PUT https://api-url/dev/protection-groups/{groupId}`
- Direct: Lambda invocation with operation `update_protection_group`

**Behavior:** If servers or launch configurations changed, re-apply configurations to affected servers.

## Performance Impact

### Before Optimization
- Wave execution time: 30-60 seconds per wave (config application)
- Total execution time for 5 waves: 2.5-5 minutes (config overhead)

### After Optimization
- Wave execution time: 5-10 seconds per wave (no config application)
- Total execution time for 5 waves: 25-50 seconds (no config overhead)
- Configuration application moved to protection group operations (one-time cost)

## Migration Strategy

### Phase 1: Add Configuration Status Tracking
- Add DynamoDB schema fields
- Implement configuration status persistence
- No behavior changes yet

### Phase 2: Apply Configs on Protection Group Operations
- Modify create/update operations to apply configs
- Store configuration status in DynamoDB
- Wave execution still applies configs (backward compatible)

### Phase 3: Optimize Wave Execution
- Modify wave execution to check config status first
- Skip config application if status is "ready"
- Apply configs only if status is not "ready"

### Phase 4: Configuration Drift Detection
- Implement hash-based drift detection
- Add manual re-apply operation
- Add configuration status to frontend

## Testing Requirements

### Unit Tests

#### New Test Files Required
1. **test_launch_config_service_unit.py**
   - Configuration application logic
   - Status persistence and retrieval
   - Hash calculation and drift detection
   - Error handling and retry logic
   - Per-server configuration tracking

2. **test_launch_config_service_property.py** (Property-Based Testing)
   - Configuration hash consistency across invocations
   - Status transitions are valid (no invalid state changes)
   - Error accumulation is monotonic (errors never disappear without re-apply)
   - Configuration application is idempotent

3. **test_data_management_launch_config_integration.py**
   - Protection group create with automatic config application
   - Protection group update with selective config re-application
   - Add/remove servers with config status updates
   - Multi-invocation method support (Frontend, API, Direct)

4. **test_execution_handler_launch_config_optimization.py**
   - Wave execution with pre-applied configs (fast path)
   - Wave execution with missing configs (fallback path)
   - Configuration drift detection during wave execution
   - Status check before recovery initiation

#### Existing Tests Requiring Updates

1. **test_data_management_operations_property.py**
   - Add property tests for launch config status in protection group operations
   - Verify config status is included in create/update responses

2. **test_data_management_new_operations.py**
   - Update protection group create tests to verify config application
   - Update protection group update tests to verify config re-application
   - Add tests for new apply_launch_configs operation

3. **test_execution_handler_start_wave.py**
   - Update wave start tests to verify config status check
   - Add tests for fast path (configs pre-applied)
   - Add tests for fallback path (configs not pre-applied)

4. **test_execution_handler_operations.py**
   - Update execution tests to verify config status in execution state
   - Add tests for configuration drift detection

5. **test_query_handler_get_server_launch_config.py**
   - Update to include configuration status in server details
   - Add tests for new get_launch_config_status operation

6. **test_shared_protection_groups.py**
   - Update protection group model tests to include LaunchConfigStatus field
   - Add validation for config status schema

### Integration Tests

#### New Integration Test Files Required
1. **test_launch_config_e2e_integration.py**
   - End-to-end protection group creation with config application
   - Wave execution with pre-applied configs
   - Configuration drift detection and re-application
   - Error scenarios and recovery
   - Multi-account configuration application

2. **test_launch_config_invocation_methods.py**
   - Frontend invocation via API Gateway (Cognito auth)
   - API-only invocation via API Gateway (IAM auth)
   - Direct Lambda invocation via OrchestrationRole
   - Verify consistent behavior across all methods

#### Existing Integration Tests Requiring Updates

1. **tests/integration/** (if exists)
   - Update any protection group integration tests
   - Update any wave execution integration tests
   - Verify backward compatibility with existing executions

### Performance Tests

#### New Performance Test Files Required
1. **test_launch_config_performance.py**
   - Measure wave execution time before/after optimization
   - Verify configuration application doesn't slow down group operations
   - Test with large protection groups (100+ servers)
   - Measure configuration application time during group create/update
   - Compare runtime config application vs pre-applied configs

#### Performance Benchmarks
- **Before Optimization**: Wave execution 30-60s per wave
- **After Optimization**: Wave execution 5-10s per wave
- **Target**: 80% reduction in wave execution time
- **Configuration Application**: < 5s for 10 servers, < 30s for 100 servers

### Test Coverage Requirements
- **Unit Test Coverage**: > 90% for new code
- **Integration Test Coverage**: All critical paths covered
- **Property-Based Test Coverage**: All stateful operations covered
- **Performance Test Coverage**: All optimization claims validated

### Test Execution Strategy
1. Run unit tests on every commit
2. Run integration tests on every PR
3. Run performance tests weekly and before releases
4. Run property-based tests with extended iterations before releases

## Security Considerations

- Configuration status includes sensitive launch settings
- Ensure proper access control for configuration operations
- Validate all configuration changes before application
- Audit log all configuration applications

## Documentation Requirements

- Update API documentation with new endpoints
- Document configuration status schema
- Add troubleshooting guide for configuration failures
- Update deployment guide with migration steps

## Success Metrics

- Wave execution time reduced by 80% (from 30-60s to 5-10s per wave)
- Configuration application success rate > 99%
- Zero configuration drift incidents
- User satisfaction with recovery speed improvement

## Dependencies

- DynamoDB table schema update
- Existing launch configuration validation utilities
- Existing DRS API integration
- Protection group management operations

## Risks and Mitigations

### Risk: Configuration drift between pre-application and execution
**Mitigation**: Implement hash-based drift detection and automatic re-application

### Risk: Configuration application failures during group operations
**Mitigation**: Store errors in DynamoDB, provide manual re-apply operation, continue with group creation even if config application fails

### Risk: Backward compatibility with existing executions
**Mitigation**: Phase 3 implementation checks config status and falls back to runtime application if needed

## Version Control Best Practices

### Commit and Push Frequently
To enable granular rollback of changes during implementation:

1. **Commit after each logical unit of work**
   - After creating a new function or class
   - After completing a test file
   - After fixing a bug or issue
   - After updating documentation

2. **Push commits immediately after creation**
   - Enables rollback to any previous state
   - Provides backup of work in progress
   - Allows easy identification of problematic changes
   - Facilitates code review at granular level

3. **Use descriptive commit messages**
   - Follow Conventional Commits format
   - Include scope and brief description
   - Example: `feat(launch-config): add config status persistence`
   - Example: `test(launch-config): add property tests for status transitions`
   - Example: `fix(launch-config): handle DRS API timeout during config apply`

4. **Commit granularity guidelines**
   - One function/class per commit (for new code)
   - One test file per commit
   - One bug fix per commit
   - One documentation update per commit
   - Avoid combining unrelated changes in single commit

5. **Benefits of frequent commits**
   - Easy to identify which change introduced a bug
   - Simple to revert specific changes without losing other work
   - Clear history of implementation progress
   - Enables bisecting to find problematic commits
   - Reduces risk of losing work

### Example Commit Sequence
```bash
# 1. Add DynamoDB schema extension
git add lambda/shared/models.py
git commit -m "feat(launch-config): add LaunchConfigStatus to protection group schema"
git push origin main

# 2. Add configuration service
git add lambda/shared/launch_config_service.py
git commit -m "feat(launch-config): add launch config application service"
git push origin main

# 3. Add unit tests
git add tests/unit/test_launch_config_service_unit.py
git commit -m "test(launch-config): add unit tests for config service"
git push origin main

# 4. Add property-based tests
git add tests/unit/test_launch_config_service_property.py
git commit -m "test(launch-config): add property tests for config status transitions"
git push origin main

# 5. Integrate with data management handler
git add lambda/data-management-handler/index.py
git commit -m "feat(launch-config): integrate config application with protection group create"
git push origin main
```

## Design Decisions

1. **Configuration application timing during group operations**
   - **Decision**: Synchronous for immediate feedback, with timeout and fallback to async
   - **Rationale**: Users get immediate confirmation of configuration status, with graceful degradation for slow operations

2. **Configuration status freshness**
   - **Decision**: 24 hours, with manual re-apply option
   - **Rationale**: Balances performance (avoiding unnecessary re-application) with safety (detecting drift within reasonable timeframe)

3. **Partial configuration application support**
   - **Decision**: Yes, store per-server status and allow partial success
   - **Rationale**: Enables visibility into which servers succeeded/failed, allows group creation to proceed even if some servers fail

4. **DRS API unavailability handling**
   - **Decision**: Mark status as "pending", retry with exponential backoff, allow group creation to succeed
   - **Rationale**: Ensures group creation isn't blocked by temporary DRS API issues, with automatic retry for eventual consistency
