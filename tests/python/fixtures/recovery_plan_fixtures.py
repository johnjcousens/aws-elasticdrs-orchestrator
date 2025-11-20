"""
Recovery Plan test fixtures for execution engine testing.
Provides sample recovery plans with various wave configurations.
"""
import time
from typing import Dict, List, Any


def create_single_wave_plan(
    plan_id: str = "test-plan-001",
    server_ids: List[str] = None
) -> Dict[str, Any]:
    """Create a simple recovery plan with one wave."""
    if server_ids is None:
        server_ids = ["s-test001", "s-test002"]
    
    return {
        "PlanId": plan_id,
        "PlanName": "Single Wave Test Plan",
        "Description": "Simple plan with one wave for testing",
        "AccountId": "123456789012",
        "Region": "us-east-1",
        "Owner": "test@example.com",
        "RPO": 300,
        "RTO": 900,
        "Waves": [
            {
                "WaveNumber": 1,
                "WaveName": "Database Tier",
                "WaveDescription": "Primary database servers",
                "ServerIds": server_ids,
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": list(range(1, len(server_ids) + 1)),
                "Dependencies": [],
                "WaitTimeSeconds": 0
            }
        ],
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


def create_three_wave_plan(
    plan_id: str = "test-plan-003",
    servers_per_wave: int = 2
) -> Dict[str, Any]:
    """Create a recovery plan with 3 sequential waves with dependencies."""
    return {
        "PlanId": plan_id,
        "PlanName": "Three Tier Application",
        "Description": "3-tier app with database, application, and web tiers",
        "AccountId": "123456789012",
        "Region": "us-east-1",
        "Owner": "test@example.com",
        "RPO": 300,
        "RTO": 900,
        "Waves": [
            {
                "WaveNumber": 1,
                "WaveName": "Database Tier",
                "WaveDescription": "Database servers",
                "ServerIds": [f"s-db{i:03d}" for i in range(1, servers_per_wave + 1)],
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": list(range(1, servers_per_wave + 1)),
                "Dependencies": [],
                "WaitTimeSeconds": 60
            },
            {
                "WaveNumber": 2,
                "WaveName": "Application Tier",
                "WaveDescription": "Application servers",
                "ServerIds": [f"s-app{i:03d}" for i in range(1, servers_per_wave + 1)],
                "ExecutionType": "PARALLEL",
                "ExecutionOrder": [1] * servers_per_wave,
                "Dependencies": ["Wave-1"],
                "WaitTimeSeconds": 30
            },
            {
                "WaveNumber": 3,
                "WaveName": "Web Tier",
                "WaveDescription": "Web servers",
                "ServerIds": [f"s-web{i:03d}" for i in range(1, servers_per_wave + 1)],
                "ExecutionType": "PARALLEL",
                "ExecutionOrder": [1] * servers_per_wave,
                "Dependencies": ["Wave-2"],
                "WaitTimeSeconds": 0
            }
        ],
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


def create_parallel_wave_plan(
    plan_id: str = "test-plan-parallel",
    server_count: int = 4
) -> Dict[str, Any]:
    """Create a recovery plan with parallel execution."""
    return {
        "PlanId": plan_id,
        "PlanName": "Parallel Execution Test Plan",
        "Description": "Plan with parallel server launches",
        "AccountId": "123456789012",
        "Region": "us-east-1",
        "Owner": "test@example.com",
        "RPO": 300,
        "RTO": 900,
        "Waves": [
            {
                "WaveNumber": 1,
                "WaveName": "Parallel Wave",
                "WaveDescription": "All servers launch simultaneously",
                "ServerIds": [f"s-par{i:03d}" for i in range(1, server_count + 1)],
                "ExecutionType": "PARALLEL",
                "ExecutionOrder": [1] * server_count,
                "Dependencies": [],
                "WaitTimeSeconds": 0
            }
        ],
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


def create_five_wave_plan(
    plan_id: str = "test-plan-005",
    servers_per_wave: int = 2
) -> Dict[str, Any]:
    """Create a recovery plan with 5 waves for complex dependency testing."""
    return {
        "PlanId": plan_id,
        "PlanName": "Five Wave Complex Plan",
        "Description": "Complex plan with 5 waves and mixed dependencies",
        "AccountId": "123456789012",
        "Region": "us-east-1",
        "Owner": "test@example.com",
        "RPO": 300,
        "RTO": 1800,
        "Waves": [
            {
                "WaveNumber": 1,
                "WaveName": "Foundation",
                "WaveDescription": "Core infrastructure",
                "ServerIds": [f"s-fnd{i:03d}" for i in range(1, servers_per_wave + 1)],
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": list(range(1, servers_per_wave + 1)),
                "Dependencies": [],
                "WaitTimeSeconds": 30
            },
            {
                "WaveNumber": 2,
                "WaveName": "Database",
                "WaveDescription": "Database tier",
                "ServerIds": [f"s-db{i:03d}" for i in range(1, servers_per_wave + 1)],
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": list(range(1, servers_per_wave + 1)),
                "Dependencies": ["Wave-1"],
                "WaitTimeSeconds": 60
            },
            {
                "WaveNumber": 3,
                "WaveName": "Application",
                "WaveDescription": "Application tier",
                "ServerIds": [f"s-app{i:03d}" for i in range(1, servers_per_wave + 1)],
                "ExecutionType": "PARALLEL",
                "ExecutionOrder": [1] * servers_per_wave,
                "Dependencies": ["Wave-2"],
                "WaitTimeSeconds": 45
            },
            {
                "WaveNumber": 4,
                "WaveName": "Web",
                "WaveDescription": "Web tier",
                "ServerIds": [f"s-web{i:03d}" for i in range(1, servers_per_wave + 1)],
                "ExecutionType": "PARALLEL",
                "ExecutionOrder": [1] * servers_per_wave,
                "Dependencies": ["Wave-3"],
                "WaitTimeSeconds": 30
            },
            {
                "WaveNumber": 5,
                "WaveName": "Edge",
                "WaveDescription": "Edge services and CDN",
                "ServerIds": [f"s-edg{i:03d}" for i in range(1, servers_per_wave + 1)],
                "ExecutionType": "PARALLEL",
                "ExecutionOrder": [1] * servers_per_wave,
                "Dependencies": ["Wave-4"],
                "WaitTimeSeconds": 0
            }
        ],
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


def create_mixed_execution_plan(
    plan_id: str = "test-plan-mixed"
) -> Dict[str, Any]:
    """Create a plan with mixed sequential and parallel execution types."""
    return {
        "PlanId": plan_id,
        "PlanName": "Mixed Execution Plan",
        "Description": "Plan with both sequential and parallel waves",
        "AccountId": "123456789012",
        "Region": "us-east-1",
        "Owner": "test@example.com",
        "RPO": 300,
        "RTO": 900,
        "Waves": [
            {
                "WaveNumber": 1,
                "WaveName": "Sequential Wave",
                "WaveDescription": "Servers launch one at a time",
                "ServerIds": ["s-seq001", "s-seq002", "s-seq003"],
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": [1, 2, 3],
                "Dependencies": [],
                "WaitTimeSeconds": 30
            },
            {
                "WaveNumber": 2,
                "WaveName": "Parallel Wave",
                "WaveDescription": "Servers launch simultaneously",
                "ServerIds": ["s-par001", "s-par002", "s-par003"],
                "ExecutionType": "PARALLEL",
                "ExecutionOrder": [1, 1, 1],
                "Dependencies": ["Wave-1"],
                "WaitTimeSeconds": 0
            }
        ],
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


def create_plan_with_transitive_dependencies(
    plan_id: str = "test-plan-transitive"
) -> Dict[str, Any]:
    """Create a plan with transitive dependencies (Wave 3 -> Wave 2 -> Wave 1)."""
    return {
        "PlanId": plan_id,
        "PlanName": "Transitive Dependencies Plan",
        "Description": "Plan testing transitive dependency chains",
        "AccountId": "123456789012",
        "Region": "us-east-1",
        "Owner": "test@example.com",
        "RPO": 300,
        "RTO": 900,
        "Waves": [
            {
                "WaveNumber": 1,
                "WaveName": "Base",
                "WaveDescription": "Base infrastructure",
                "ServerIds": ["s-base001"],
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": [1],
                "Dependencies": [],
                "WaitTimeSeconds": 0
            },
            {
                "WaveNumber": 2,
                "WaveName": "Middle",
                "WaveDescription": "Middle tier depends on base",
                "ServerIds": ["s-mid001"],
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": [1],
                "Dependencies": ["Wave-1"],
                "WaitTimeSeconds": 0
            },
            {
                "WaveNumber": 3,
                "WaveName": "Top",
                "WaveDescription": "Top tier depends on middle (transitive to base)",
                "ServerIds": ["s-top001"],
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": [1],
                "Dependencies": ["Wave-2"],
                "WaitTimeSeconds": 0
            }
        ],
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


def create_plan_with_wait_times(
    plan_id: str = "test-plan-waits",
    wait_times: List[int] = None
) -> Dict[str, Any]:
    """Create a plan with configurable wait times between waves."""
    if wait_times is None:
        wait_times = [60, 120, 180]
    
    return {
        "PlanId": plan_id,
        "PlanName": "Wait Time Test Plan",
        "Description": "Plan for testing wait time compliance",
        "AccountId": "123456789012",
        "Region": "us-east-1",
        "Owner": "test@example.com",
        "RPO": 300,
        "RTO": 900,
        "Waves": [
            {
                "WaveNumber": i + 1,
                "WaveName": f"Wave {i + 1}",
                "WaveDescription": f"Wave with {wait_time}s wait",
                "ServerIds": [f"s-wait{i+1:03d}"],
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": [1],
                "Dependencies": [f"Wave-{i}"] if i > 0 else [],
                "WaitTimeSeconds": wait_time
            }
            for i, wait_time in enumerate(wait_times)
        ],
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


def create_real_drs_server_plan(
    plan_id: str = "test-plan-real-drs"
) -> Dict[str, Any]:
    """Create a plan using real DRS server IDs from TEST account."""
    return {
        "PlanId": plan_id,
        "PlanName": "Real DRS Servers Plan",
        "Description": "Plan using actual DRS servers for integration testing",
        "AccountId": "***REMOVED***",
        "Region": "us-east-1",
        "Owner": "test@example.com",
        "RPO": 300,
        "RTO": 900,
        "Waves": [
            {
                "WaveNumber": 1,
                "WaveName": "Database Tier",
                "WaveDescription": "Real database servers",
                "ServerIds": ["s-3d75cdc0d9a28a725", "s-3afa164776f93ce4f"],
                "ExecutionType": "SEQUENTIAL",
                "ExecutionOrder": [1, 2],
                "Dependencies": [],
                "WaitTimeSeconds": 60
            },
            {
                "WaveNumber": 2,
                "WaveName": "Application Tier",
                "WaveDescription": "Real application servers",
                "ServerIds": ["s-3c1730a9e0771ea14", "s-3c63bb8be30d7d071"],
                "ExecutionType": "PARALLEL",
                "ExecutionOrder": [1, 1],
                "Dependencies": ["Wave-1"],
                "WaitTimeSeconds": 30
            },
            {
                "WaveNumber": 3,
                "WaveName": "Web Tier",
                "WaveDescription": "Real web servers",
                "ServerIds": ["s-3578f52ef3bdd58b4", "s-3b9401c1cd270a7a8"],
                "ExecutionType": "PARALLEL",
                "ExecutionOrder": [1, 1],
                "Dependencies": ["Wave-2"],
                "WaitTimeSeconds": 0
            }
        ],
        "CreatedDate": int(time.time()),
        "LastModifiedDate": int(time.time())
    }


# Convenience functions for common test scenarios
def get_all_fixtures() -> Dict[str, Dict[str, Any]]:
    """Return all available fixtures as a dictionary."""
    return {
        "single_wave": create_single_wave_plan(),
        "three_wave": create_three_wave_plan(),
        "five_wave": create_five_wave_plan(),
        "parallel": create_parallel_wave_plan(),
        "mixed": create_mixed_execution_plan(),
        "transitive": create_plan_with_transitive_dependencies(),
        "wait_times": create_plan_with_wait_times(),
        "real_drs": create_real_drs_server_plan()
    }


def get_fixture(name: str, **kwargs) -> Dict[str, Any]:
    """Get a fixture by name with optional parameters."""
    fixtures = {
        "single_wave": create_single_wave_plan,
        "three_wave": create_three_wave_plan,
        "five_wave": create_five_wave_plan,
        "parallel": create_parallel_wave_plan,
        "mixed": create_mixed_execution_plan,
        "transitive": create_plan_with_transitive_dependencies,
        "wait_times": create_plan_with_wait_times,
        "real_drs": create_real_drs_server_plan
    }
    
    if name not in fixtures:
        raise ValueError(f"Unknown fixture: {name}. Available: {list(fixtures.keys())}")
    return fixtures[name](**kwargs)
