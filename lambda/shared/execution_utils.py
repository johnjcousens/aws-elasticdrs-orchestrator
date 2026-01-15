"""
Execution utility functions for DRS orchestration.

Provides centralized logic for execution state management and validation.
"""

from typing import Any, Dict, List


def can_terminate_execution(execution: Dict) -> Dict[str, Any]:
    """
    Determine if execution can be terminated based on current state.
    
    Centralized logic prevents inconsistencies between frontend and backend.
    Returns metadata about termination capability and reason if blocked.
    
    Args:
        execution: Execution record from DynamoDB
        
    Returns:
        Dict with keys:
        - canTerminate (bool): Whether termination is allowed
        - reason (str|None): Explanation if termination blocked
        - hasRecoveryInstances (bool): Whether recovery instances exist
        
    Example:
        >>> execution = {'status': 'completed', 'waves': [{'jobId': 'job-123'}]}
        >>> result = can_terminate_execution(execution)
        >>> result['canTerminate']
        True
    """
    terminal_statuses = [
        "completed",
        "cancelled",
        "failed",
        "partial",
        "COMPLETED",
        "CANCELLED",
        "FAILED",
        "PARTIAL",
    ]
    active_statuses = [
        "in_progress",
        "pending",
        "running",
        "started",
        "polling",
        "launching",
        "initiated",
        "IN_PROGRESS",
        "PENDING",
        "RUNNING",
        "STARTED",
        "POLLING",
        "LAUNCHING",
        "INITIATED",
    ]

    result = {
        "canTerminate": False,
        "reason": None,
        "hasRecoveryInstances": False,
    }

    # Check terminal status
    execution_status = execution.get("status", "")
    if execution_status not in terminal_statuses:
        result["reason"] = "Execution not in terminal state"
        return result

    # Check for job IDs (indicates recovery instances exist)
    # Check both Waves (PascalCase) and waves (camelCase) for compatibility
    waves = execution.get("Waves") or execution.get("waves", [])
    has_job_id = any(
        wave.get("jobId") or wave.get("JobId") for wave in waves
    )

    if not has_job_id:
        result["reason"] = "No recovery instances found"
        return result

    result["hasRecoveryInstances"] = True

    # Check if already terminated
    if execution.get("instancesTerminated") or execution.get(
        "InstancesTerminated"
    ):
        result["reason"] = "Instances already terminated"
        return result

    # Check for active waves
    has_active = any(
        (wave.get("status") or wave.get("Status", "")) in active_statuses
        for wave in waves
    )

    if has_active:
        result["reason"] = "Waves still active"
        return result

    # All checks passed
    result["canTerminate"] = True
    return result


def normalize_wave_status(wave: Dict) -> str:
    """
    Normalize wave status to lowercase for consistent comparison.
    
    Handles both camelCase and PascalCase status fields.
    
    Args:
        wave: Wave execution record
        
    Returns:
        Normalized status string in lowercase
    """
    status = wave.get("status") or wave.get("Status", "unknown")
    return status.lower()


def get_execution_progress(execution: Dict) -> Dict[str, Any]:
    """
    Calculate execution progress metrics.
    
    Args:
        execution: Execution record from DynamoDB
        
    Returns:
        Dict with progress metrics:
        - totalWaves (int): Total number of waves
        - completedWaves (int): Number of completed waves
        - activeWave (int|None): Current active wave number
        - percentComplete (float): Completion percentage
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

    completed_statuses = ["completed", "COMPLETED", "unknown"]
    completed_waves = sum(
        1
        for wave in waves
        if normalize_wave_status(wave) in completed_statuses
    )

    active_statuses = [
        "in_progress",
        "pending",
        "running",
        "started",
        "polling",
        "launching",
        "initiated",
    ]
    active_wave = None
    for wave in waves:
        if normalize_wave_status(wave) in active_statuses:
            active_wave = wave.get("waveNumber") or wave.get("WaveNumber")
            break

    percent_complete = (
        (completed_waves / total_waves * 100) if total_waves > 0 else 0.0
    )

    return {
        "totalWaves": total_waves,
        "completedWaves": completed_waves,
        "activeWave": active_wave,
        "percentComplete": round(percent_complete, 1),
    }
