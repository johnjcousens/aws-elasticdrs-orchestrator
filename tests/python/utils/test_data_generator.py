"""
Test data generators for execution engine testing.
Provides functions to generate random test data for recovery plans, servers, and execution history.
"""
import random
import string
import time
import uuid
from typing import Dict, List, Any, Optional


def generate_server_id() -> str:
    """
    Generate a random DRS source server ID in format: s-{17 hex chars}
    
    Returns:
        Server ID string (e.g., "s-3d75cdc0d9a28a725")
    """
    hex_chars = ''.join(random.choices('0123456789abcdef', k=17))
    return f"s-{hex_chars}"


def generate_server_ids(count: int) -> List[str]:
    """
    Generate multiple unique server IDs.
    
    Args:
        count: Number of server IDs to generate
        
    Returns:
        List of unique server IDs
    """
    return [generate_server_id() for _ in range(count)]


def generate_recovery_plan(
    wave_count: int = 3,
    servers_per_wave: int = 2,
    execution_types: Optional[List[str]] = None,
    with_dependencies: bool = True,
    wait_times: Optional[List[int]] = None,
    plan_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a random recovery plan with configurable parameters.
    
    Args:
        wave_count: Number of waves to generate
        servers_per_wave: Number of servers per wave
        execution_types: List of execution types (SEQUENTIAL, PARALLEL) for each wave
                        If None, randomly assigns types
        with_dependencies: Whether to create sequential dependencies between waves
        wait_times: List of wait times for each wave. If None, generates random times
        plan_id: Optional plan ID. If None, generates random ID
        
    Returns:
        Dictionary representing a recovery plan
    """
    if plan_id is None:
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
    
    if execution_types is None:
        execution_types = [random.choice(["SEQUENTIAL", "PARALLEL"]) for _ in range(wave_count)]
    
    if wait_times is None:
        wait_times = [random.randint(0, 300) for _ in range(wave_count)]
    
    waves = []
    for i in range(wave_count):
        wave_number = i + 1
        execution_type = execution_types[i] if i < len(execution_types) else "SEQUENTIAL"
        wait_time = wait_times[i] if i < len(wait_times) else 0
        
        # Generate server IDs for this wave
        server_ids = generate_server_ids(servers_per_wave)
        
        # Generate execution order based on type
        if execution_type == "PARALLEL":
            execution_order = [1] * servers_per_wave
        else:  # SEQUENTIAL
            execution_order = list(range(1, servers_per_wave + 1))
        
        # Generate dependencies
        dependencies = []
        if with_dependencies and i > 0:
            dependencies = [f"Wave-{i}"]
        
        wave = {
            "WaveNumber": wave_number,
            "WaveName": f"Wave {wave_number}",
            "WaveDescription": f"Generated wave {wave_number}",
            "ServerIds": server_ids,
            "ExecutionType": execution_type,
            "ExecutionOrder": execution_order,
            "Dependencies": dependencies,
            "WaitTimeSeconds": wait_time
        }
        waves.append(wave)
    
    return {
        "PlanId": plan_id,
        "PlanName": f"Generated Plan {plan_id}",
        "Description": f"Randomly generated plan with {wave_count} waves",
        "AccountId": "123456789012",
        "Region": "us-east-1",
        "Owner": "test@example.com",
        "RPO": random.randint(60, 3600),
        "RTO": random.randint(300, 7200),
        "Waves": waves,
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


def generate_execution_history(
    plan_id: str,
    execution_id: Optional[str] = None,
    status: str = "COMPLETED",
    wave_count: int = 3,
    servers_per_wave: int = 2,
    with_errors: bool = False
) -> Dict[str, Any]:
    """
    Generate execution history record for database seeding.
    
    Args:
        plan_id: Recovery plan ID
        execution_id: Optional execution ID. If None, generates random UUID
        status: Execution status (RUNNING, COMPLETED, FAILED, CANCELLED)
        wave_count: Number of waves in the execution
        servers_per_wave: Number of servers per wave
        with_errors: Whether to include error details
        
    Returns:
        Dictionary representing an execution history record
    """
    if execution_id is None:
        execution_id = str(uuid.uuid4())
    
    start_time = int(time.time()) - random.randint(300, 3600)
    end_time = start_time + random.randint(60, 1800) if status != "RUNNING" else None
    
    # Generate wave statuses
    wave_statuses = []
    total_servers = wave_count * servers_per_wave
    failed_count = 0
    
    for i in range(wave_count):
        wave_number = i + 1
        server_results = []
        
        for j in range(servers_per_wave):
            server_id = generate_server_id()
            
            # Determine server status
            # If with_errors is True, ensure at least one failure
            should_fail = with_errors and (random.random() < 0.2 or (failed_count == 0 and i == wave_count - 1 and j == servers_per_wave - 1))
            
            if should_fail:
                server_status = "FAILED"
                error_message = f"Recovery failed for {server_id}"
                job_id = None
                failed_count += 1
            else:
                server_status = "COMPLETED"
                error_message = None
                job_id = f"job-{uuid.uuid4().hex[:16]}"
            
            server_result = {
                "ServerId": server_id,
                "Status": server_status,
                "JobId": job_id,
                "RecoveryInstanceId": f"i-{uuid.uuid4().hex[:17]}" if server_status == "COMPLETED" else None,
                "StartTime": start_time + (i * 60) + (j * 10),
                "EndTime": start_time + (i * 60) + (j * 10) + random.randint(30, 120),
                "ErrorMessage": error_message
            }
            server_results.append(server_result)
        
        wave_status = {
            "WaveNumber": wave_number,
            "Status": "FAILED" if with_errors and random.random() < 0.1 else "COMPLETED",
            "StartTime": start_time + (i * 60),
            "EndTime": start_time + (i * 60) + random.randint(60, 300),
            "ServerResults": server_results
        }
        wave_statuses.append(wave_status)
    
    execution = {
        "ExecutionId": execution_id,
        "PlanId": plan_id,
        "Status": status,
        "ExecutionType": random.choice(["RECOVERY", "DRILL"]),
        "InitiatedBy": "test@example.com",
        "StartTime": start_time,
        "EndTime": end_time,
        "WaveStatuses": wave_statuses,
        "TotalServers": wave_count * servers_per_wave,
        "SuccessfulServers": sum(
            1 for ws in wave_statuses 
            for sr in ws["ServerResults"] 
            if sr["Status"] == "COMPLETED"
        ),
        "FailedServers": sum(
            1 for ws in wave_statuses 
            for sr in ws["ServerResults"] 
            if sr["Status"] == "FAILED"
        )
    }
    
    if with_errors:
        execution["Errors"] = [
            {
                "WaveNumber": ws["WaveNumber"],
                "ServerId": sr["ServerId"],
                "ErrorMessage": sr["ErrorMessage"]
            }
            for ws in wave_statuses
            for sr in ws["ServerResults"]
            if sr["ErrorMessage"]
        ]
    
    return execution


def generate_multiple_executions(
    count: int,
    plan_id: Optional[str] = None,
    status_distribution: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Generate multiple execution history records.
    
    Args:
        count: Number of executions to generate
        plan_id: Optional plan ID to use for all executions
        status_distribution: Distribution of statuses (e.g., {"COMPLETED": 0.7, "FAILED": 0.3})
                           If None, uses default distribution
        
    Returns:
        List of execution history records
    """
    if plan_id is None:
        plan_id = f"plan-{uuid.uuid4().hex[:12]}"
    
    if status_distribution is None:
        status_distribution = {
            "COMPLETED": 0.7,
            "FAILED": 0.2,
            "RUNNING": 0.05,
            "CANCELLED": 0.05
        }
    
    # Create weighted list of statuses
    statuses = []
    for status, weight in status_distribution.items():
        statuses.extend([status] * int(weight * 100))
    
    executions = []
    for _ in range(count):
        status = random.choice(statuses)
        with_errors = status == "FAILED"
        
        execution = generate_execution_history(
            plan_id=plan_id,
            status=status,
            wave_count=random.randint(1, 5),
            servers_per_wave=random.randint(1, 4),
            with_errors=with_errors
        )
        executions.append(execution)
    
    return executions


def generate_protection_group(
    group_id: Optional[str] = None,
    server_count: int = 5
) -> Dict[str, Any]:
    """
    Generate a protection group for testing.
    
    Args:
        group_id: Optional group ID. If None, generates random ID
        server_count: Number of servers in the group
        
    Returns:
        Dictionary representing a protection group
    """
    if group_id is None:
        group_id = f"pg-{uuid.uuid4().hex[:12]}"
    
    return {
        "GroupId": group_id,
        "GroupName": f"Protection Group {group_id}",
        "Description": f"Generated protection group with {server_count} servers",
        "ServerIds": generate_server_ids(server_count),
        "Region": "us-east-1",
        "AccountId": "123456789012",
        "Tags": {
            "Environment": random.choice(["Production", "Staging", "Development"]),
            "Application": random.choice(["WebApp", "Database", "API"])
        },
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


def generate_random_string(length: int = 10, include_special: bool = False) -> str:
    """
    Generate a random string.
    
    Args:
        length: Length of the string
        include_special: Whether to include special characters
        
    Returns:
        Random string
    """
    chars = string.ascii_letters + string.digits
    if include_special:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
    
    return ''.join(random.choices(chars, k=length))


def generate_account_id() -> str:
    """
    Generate a random AWS account ID (12 digits).
    
    Returns:
        12-digit account ID string
    """
    return ''.join(random.choices(string.digits, k=12))


def generate_instance_id() -> str:
    """
    Generate a random EC2 instance ID in format: i-{17 hex chars}
    
    Returns:
        Instance ID string (e.g., "i-0123456789abcdef0")
    """
    hex_chars = ''.join(random.choices('0123456789abcdef', k=17))
    return f"i-{hex_chars}"


def generate_job_id() -> str:
    """
    Generate a random DRS job ID in format: job-{16 hex chars}
    
    Returns:
        Job ID string
    """
    hex_chars = ''.join(random.choices('0123456789abcdef', k=16))
    return f"job-{hex_chars}"


def seed_database_with_plans(
    dynamodb_table,
    count: int = 10,
    wave_range: tuple = (1, 5),
    servers_per_wave_range: tuple = (1, 4)
) -> List[Dict[str, Any]]:
    """
    Seed DynamoDB table with random recovery plans.
    
    Args:
        dynamodb_table: DynamoDB table resource
        count: Number of plans to generate
        wave_range: Tuple of (min_waves, max_waves)
        servers_per_wave_range: Tuple of (min_servers, max_servers)
        
    Returns:
        List of generated plans
    """
    plans = []
    for _ in range(count):
        wave_count = random.randint(*wave_range)
        servers_per_wave = random.randint(*servers_per_wave_range)
        
        plan = generate_recovery_plan(
            wave_count=wave_count,
            servers_per_wave=servers_per_wave
        )
        
        # Write to DynamoDB
        dynamodb_table.put_item(Item=plan)
        plans.append(plan)
    
    return plans


def seed_database_with_executions(
    dynamodb_table,
    count: int = 100,
    plan_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Seed DynamoDB table with random execution history records.
    
    Args:
        dynamodb_table: DynamoDB table resource
        count: Number of execution records to generate
        plan_ids: Optional list of plan IDs to use. If None, generates random plan IDs
        
    Returns:
        List of generated execution records
    """
    if plan_ids is None:
        plan_ids = [f"plan-{uuid.uuid4().hex[:12]}" for _ in range(count // 10)]
    
    executions = []
    for _ in range(count):
        plan_id = random.choice(plan_ids)
        
        execution = generate_execution_history(
            plan_id=plan_id,
            wave_count=random.randint(1, 5),
            servers_per_wave=random.randint(1, 4),
            with_errors=random.random() < 0.2  # 20% with errors
        )
        
        # Write to DynamoDB
        dynamodb_table.put_item(Item=execution)
        executions.append(execution)
    
    return executions


# Convenience functions for common scenarios
def generate_simple_plan() -> Dict[str, Any]:
    """Generate a simple 1-wave plan."""
    return generate_recovery_plan(wave_count=1, servers_per_wave=2)


def generate_complex_plan() -> Dict[str, Any]:
    """Generate a complex 5-wave plan with dependencies."""
    return generate_recovery_plan(
        wave_count=5,
        servers_per_wave=3,
        with_dependencies=True
    )


def generate_parallel_plan() -> Dict[str, Any]:
    """Generate a plan with all parallel waves."""
    return generate_recovery_plan(
        wave_count=3,
        servers_per_wave=4,
        execution_types=["PARALLEL"] * 3,
        with_dependencies=False
    )


def generate_sequential_plan() -> Dict[str, Any]:
    """Generate a plan with all sequential waves."""
    return generate_recovery_plan(
        wave_count=3,
        servers_per_wave=2,
        execution_types=["SEQUENTIAL"] * 3,
        with_dependencies=True
    )
