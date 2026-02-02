"""
Execution State Management and Validation Utilities

Provides centralized logic for DR execution state management, validation, and progress tracking.
Used by execution-handler, API endpoints, and Step Functions for consistent state handling.

## Data Format Convention

ALL data uses camelCase (matches DynamoDB storage and API responses):
- `status`, `waveNumber`, `jobId`, `instancesTerminated`
- NO snake_case fallback patterns
- Data must be in correct format at boundaries

## Integration Points

### 1. Termination Validation (API Gateway + Frontend)
```python
from shared.execution_utils import can_terminate_execution

# Check if execution can be terminated
execution = dynamodb.get_item(Key={"executionId": "exec-123"})["Item"]
result = can_terminate_execution(execution)

if result["canTerminate"]:
    # Proceed with termination
    terminate_recovery_instances(execution)
else:
    # Return error to user
    return {"error": result["reason"]}
```

### 2. Progress Tracking (Frontend Dashboard)
```python
from shared.execution_utils import get_execution_progress

execution = dynamodb.get_item(Key={"executionId": "exec-123"})["Item"]
progress = get_execution_progress(execution)

# Display progress bar
print(f"Progress: {progress['percentComplete']}%")
print(f"Waves: {progress['completedWaves']}/{progress['totalWaves']}")
print(f"Active Wave: {progress['activeWave']}")
```

### 3. Wave Status Normalization (Step Functions)
```python
from shared.execution_utils import normalize_wave_status

wave = {"waveNumber": 1, "status": "IN_PROGRESS"}
normalized = normalize_wave_status(wave)  # Returns "in_progress"

if normalized in {"completed", "failed"}:
    # Wave finished
    proceed_to_next_wave()
```

## State Machine

### Execution Status Flow
```
PENDING → IN_PROGRESS → COMPLETED
                      ↘ FAILED
                      ↘ CANCELLED
                      ↘ PARTIAL
```

### Wave Status Flow
```
PENDING → INITIATED → LAUNCHING → RUNNING → COMPLETED
                                          ↘ FAILED
```

## Termination Rules

Execution can be terminated when ALL conditions met:
1. Execution status is terminal (COMPLETED, FAILED, CANCELLED, PARTIAL)
2. Recovery instances exist (waves have jobId)
3. Instances not already terminated (instancesTerminated != true)
4. No waves are active (all waves in terminal state)

## Status Constants

### Terminal Statuses (Execution Complete)
- `COMPLETED`: All waves succeeded
- `FAILED`: Execution failed
- `CANCELLED`: User cancelled execution
- `PARTIAL`: Some waves succeeded, some failed

### Active Statuses (Execution In Progress)
- `IN_PROGRESS`: Execution running
- `PENDING`: Waiting to start
- `RUNNING`: Active execution
- `STARTED`: Just started
- `POLLING`: Polling for completion
- `LAUNCHING`: Launching instances
- `INITIATED`: Recovery initiated

CASING CONVENTION:
- All internal data uses camelCase (status, waveNumber, jobId, etc.)
- AWS API responses are transformed to camelCase at the boundary
- NO fallback patterns - data must be in correct format
"""

from typing import Any, Dict

# Terminal statuses (UPPERCASE - matches API/DynamoDB storage)
TERMINAL_STATUSES = {"COMPLETED", "CANCELLED", "FAILED", "PARTIAL"}

# Active statuses (UPPERCASE - matches API/DynamoDB storage)
ACTIVE_STATUSES = {
    "IN_PROGRESS",
    "PENDING",
    "RUNNING",
    "STARTED",
    "POLLING",
    "LAUNCHING",
    "INITIATED",
}


def can_terminate_execution(execution: Dict) -> Dict[str, Any]:
    """
    Determine if execution can be terminated based on current state.

    Centralized termination logic ensures consistency between frontend UI,
    API endpoints, and Step Functions. Prevents premature termination of
    active executions and duplicate termination attempts.

    Termination Requirements (ALL must be true):
    1. Execution in terminal state (COMPLETED, FAILED, CANCELLED, PARTIAL)
    2. Recovery instances exist (waves have jobId from DRS)
    3. Instances not already terminated (instancesTerminated != true)
    4. No waves are active (all waves in terminal state)

    Args:
        execution: Execution record from DynamoDB with camelCase fields:
            - status: Execution status (UPPERCASE)
            - waves: List of wave records with status and jobId
            - instancesTerminated: Boolean flag

    Returns:
        Dict with termination decision:
        - canTerminate (bool): Whether termination is allowed
        - reason (str|None): Explanation if termination blocked
        - hasRecoveryInstances (bool): Whether recovery instances exist

    Example:
        >>> execution = {
        ...     'status': 'COMPLETED',
        ...     'waves': [{'waveNumber': 1, 'status': 'COMPLETED', 'jobId': 'job-123'}],
        ...     'instancesTerminated': False
        ... }
        >>> result = can_terminate_execution(execution)
        >>> result['canTerminate']
        True
        >>> result['hasRecoveryInstances']
        True
    """
    result = {
        "canTerminate": False,
        "reason": None,
        "hasRecoveryInstances": False,
    }

    # Check terminal status (normalize to uppercase for comparison)
    execution_status = execution.get("status", "").upper()
    if execution_status not in TERMINAL_STATUSES:
        result["reason"] = "Execution not in terminal state"
        return result

    # Check for job IDs (indicates recovery instances exist)
    # Data is in camelCase - no fallback needed
    waves = execution.get("waves", [])
    has_job_id = any(wave.get("jobId") for wave in waves)

    if not has_job_id:
        result["reason"] = "No recovery instances found"
        return result

    result["hasRecoveryInstances"] = True

    # Check if already terminated
    if execution.get("instancesTerminated"):
        result["reason"] = "Instances already terminated"
        return result

    # Check for active waves (normalize to uppercase for comparison)
    has_active = any(wave.get("status", "").upper() in ACTIVE_STATUSES for wave in waves)

    if has_active:
        result["reason"] = "Waves still active"
        return result

    # All checks passed
    result["canTerminate"] = True
    return result


def normalize_wave_status(wave: Dict) -> str:
    """
    Normalize wave status to lowercase for consistent comparison.

    DynamoDB stores statuses in UPPERCASE, but comparison logic uses lowercase.
    This function provides consistent normalization across all code paths.

    Args:
        wave: Wave execution record with camelCase fields:
            - status: Wave status (UPPERCASE in DynamoDB)

    Returns:
        Normalized status string in lowercase (e.g., "in_progress", "completed")

    Example:
        >>> wave = {"waveNumber": 1, "status": "IN_PROGRESS"}
        >>> normalize_wave_status(wave)
        'in_progress'
    """
    status = wave.get("status", "unknown")
    return status.lower()


def get_execution_progress(execution: Dict) -> Dict[str, Any]:
    """
    Calculate execution progress metrics for dashboard display.

    Provides real-time progress tracking for frontend dashboards and monitoring.
    Calculates completion percentage, identifies active wave, and counts completed waves.

    Args:
        execution: Execution record from DynamoDB with camelCase fields:
            - waves: List of wave records with status and waveNumber

    Returns:
        Dict with progress metrics:
        - totalWaves (int): Total number of waves in execution
        - completedWaves (int): Number of completed waves
        - activeWave (int|None): Wave number currently executing (None if none active)
        - percentComplete (float): Completion percentage (0.0-100.0)

    Example:
        >>> execution = {
        ...     'waves': [
        ...         {'waveNumber': 1, 'status': 'COMPLETED'},
        ...         {'waveNumber': 2, 'status': 'IN_PROGRESS'},
        ...         {'waveNumber': 3, 'status': 'PENDING'}
        ...     ]
        ... }
        >>> progress = get_execution_progress(execution)
        >>> progress['percentComplete']
        33.3
        >>> progress['activeWave']
        2
    """
    waves = execution.get("waves", [])
    total_waves = len(waves)

    if total_waves == 0:
        return {
            "totalWaves": 0,
            "completedWaves": 0,
            "activeWave": None,
            "percentComplete": 0.0,
        }

    completed_statuses = {"completed", "unknown"}
    completed_waves = sum(1 for wave in waves if normalize_wave_status(wave) in completed_statuses)

    active_statuses = {
        "in_progress",
        "pending",
        "running",
        "started",
        "polling",
        "launching",
        "initiated",
    }
    active_wave = None
    for wave in waves:
        if normalize_wave_status(wave) in active_statuses:
            active_wave = wave.get("waveNumber")
            break

    percent_complete = (completed_waves / total_waves * 100) if total_waves > 0 else 0.0

    return {
        "totalWaves": total_waves,
        "completedWaves": completed_waves,
        "activeWave": active_wave,
        "percentComplete": round(percent_complete, 1),
    }
