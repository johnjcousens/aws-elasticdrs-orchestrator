# Documentation Improvement Task

## Overview
Improve code documentation by adding comprehensive docstrings to functions that currently have empty or missing documentation. This will help other developers understand the codebase more easily.

## Current State
- **144 empty docstrings** across main Lambda functions
- Most are placeholder `"""` with no content
- Critical functions (handlers, complex logic) need documentation first

## Priority Levels

### Priority 1: Critical Functions (Handlers & Complex Logic >50 lines)
These are the most important to document because they're entry points or contain complex business logic.

#### lambda/api-handler/index.py (6 functions)
1. **lambda_handler** (243 lines) - Main API Gateway handler
   - Needs: Purpose, event structure, response format, error handling
2. **get_plans_with_conflicts** (144 lines) - Conflict detection logic
   - Needs: Why conflicts matter, detection algorithm, return structure
3. **determine_target_account_context** (140 lines) - Multi-account routing
   - Needs: Cross-account logic, role assumption, fallback behavior
4. **get_drs_account_capacity** (123 lines) - DRS quota validation
   - Needs: Why capacity matters, quota types, validation logic
5. **get_servers_in_active_executions** (93 lines) - Active execution tracking
   - Needs: Why tracking matters, conflict prevention, data structure
6. **resolve_protection_group_tags** (56 lines) - Tag-based server discovery
   - Needs: Tag format, discovery logic, error handling

#### lambda/orchestration-stepfunctions/index.py (1 function)
1. **update_wave_status** (492 lines) - Wave status polling and updates
   - Needs: Polling logic, DRS job status mapping, state transitions, error recovery

#### lambda/execution-poller/index.py (2 functions)
1. **lambda_handler** (229 lines) - EventBridge-triggered polling
   - Needs: Polling frequency, execution discovery, callback mechanism
2. **poll_wave_status** (199 lines) - DRS job status polling
   - Needs: Status mapping, completion detection, failure handling

### Priority 2: Public Utility Functions
Helper functions that are called by multiple places.

#### lambda/api-handler/index.py (3 functions)
- **dfs** (24 lines) - Dependency graph traversal
- **default** (9 lines) - JSON serialization helper

#### lambda/orchestration-stepfunctions/index.py (4 functions)
- **get_protection_groups_table** (6 lines) - DynamoDB table accessor
- **get_recovery_plans_table** (6 lines) - DynamoDB table accessor
- **get_execution_history_table** (6 lines) - DynamoDB table accessor
- **default** (5 lines) - JSON serialization helper

#### lambda/execution-poller/index.py (2 functions)
- **update_call** (33 lines) - DynamoDB update helper
- **get_item_call** (29 lines) - DynamoDB get helper

### Priority 3: All Other Functions
Functions with empty docstrings that aren't in Priority 1 or 2.

## Documentation Standards

### Required Elements
Every docstring should include:

1. **Purpose** - One-line summary of what the function does
2. **Why it exists** - Business logic or technical reason (not just "what")
3. **Parameters** - Type, purpose, constraints
4. **Returns** - Type, structure, meaning
5. **Raises** - Expected exceptions and when they occur
6. **Examples** - For complex functions, show typical usage

### Good Docstring Example
```python
def get_plans_with_conflicts(region: str) -> Dict[str, Dict]:
    """
    Identify recovery plans with server conflicts across protection groups.
    
    Server conflicts occur when the same DRS source server is assigned to
    multiple protection groups, which would cause concurrent recovery attempts
    and DRS API failures. This function scans all plans to detect and report
    these conflicts before execution.
    
    Args:
        region: AWS region to check for conflicts
        
    Returns:
        Dict mapping plan IDs to conflict details:
        {
            "plan-123": {
                "planName": "Production Recovery",
                "conflicts": [
                    {
                        "serverId": "s-abc123",
                        "conflictingGroups": ["pg-1", "pg-2"]
                    }
                ]
            }
        }
        
    Raises:
        ClientError: When DynamoDB queries fail
        
    Example:
        >>> conflicts = get_plans_with_conflicts("us-east-1")
        >>> if conflicts:
        ...     print(f"Found conflicts in {len(conflicts)} plans")
    """
```

### Bad Docstring Example (Avoid)
```python
def get_plans_with_conflicts(region: str) -> Dict[str, Dict]:
    """Get plans with conflicts."""  # Too vague, no WHY
```

## Implementation Approach

### Phase 1: Priority 1 Functions (9 functions)
- Focus on handlers and complex business logic
- These have the highest impact on developer understanding
- Estimated effort: 2-3 hours

### Phase 2: Priority 2 Functions (9 functions)
- Document utility functions and helpers
- These are called from multiple places
- Estimated effort: 1-2 hours

### Phase 3: Priority 3 Functions (remaining)
- Complete documentation for all remaining functions
- Estimated effort: 3-4 hours

## Success Criteria
- [ ] All Priority 1 functions have comprehensive docstrings
- [ ] All Priority 2 functions have clear docstrings
- [ ] All Priority 3 functions have at least basic docstrings
- [ ] Code quality checker updated to detect empty docstrings
- [ ] Documentation follows Python PEP 257 standards

## Related Files
- `lambda/api-handler/index.py` - 90 empty docstrings
- `lambda/orchestration-stepfunctions/index.py` - 24 empty docstrings
- `lambda/execution-poller/index.py` - 30 empty docstrings
- `lambda/shared/rbac_middleware.py` - Check for empty docstrings
- `lambda/shared/security_utils.py` - Check for empty docstrings

## Notes
- Follow Development Principles: Comments should explain WHY, not WHAT
- Use active voice and be concise
- Focus on business logic and edge cases
- Include examples for complex functions
- Document error handling and recovery strategies
