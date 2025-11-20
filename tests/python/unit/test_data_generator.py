"""
Unit tests for test data generators.
Validates that generators produce valid data structures.
"""
import pytest
import re
from utils.test_data_generator import (
    generate_server_id,
    generate_server_ids,
    generate_recovery_plan,
    generate_execution_history,
    generate_multiple_executions,
    generate_protection_group,
    generate_random_string,
    generate_account_id,
    generate_instance_id,
    generate_job_id,
    generate_simple_plan,
    generate_complex_plan,
    generate_parallel_plan,
    generate_sequential_plan
)


class TestServerIdGeneration:
    """Test server ID generation."""
    
    def test_generate_server_id_format(self):
        """Test server ID has correct format."""
        server_id = generate_server_id()
        
        assert server_id.startswith("s-")
        assert len(server_id) == 19  # s- + 17 hex chars
        
        # Verify hex characters
        hex_part = server_id[2:]
        assert re.match(r'^[0-9a-f]{17}$', hex_part)
    
    def test_generate_server_ids_count(self):
        """Test generating multiple server IDs."""
        count = 10
        server_ids = generate_server_ids(count)
        
        assert len(server_ids) == count
        
        # Verify all are unique
        assert len(set(server_ids)) == count
    
    def test_generate_server_ids_format(self):
        """Test all generated server IDs have correct format."""
        server_ids = generate_server_ids(5)
        
        for server_id in server_ids:
            assert server_id.startswith("s-")
            assert len(server_id) == 19


class TestRecoveryPlanGeneration:
    """Test recovery plan generation."""
    
    def test_generate_recovery_plan_basic(self):
        """Test basic recovery plan generation."""
        plan = generate_recovery_plan()
        
        assert "PlanId" in plan
        assert "Waves" in plan
        assert len(plan["Waves"]) == 3  # Default wave count
    
    def test_generate_recovery_plan_custom_waves(self):
        """Test plan generation with custom wave count."""
        wave_count = 5
        plan = generate_recovery_plan(wave_count=wave_count)
        
        assert len(plan["Waves"]) == wave_count
    
    def test_generate_recovery_plan_custom_servers(self):
        """Test plan generation with custom servers per wave."""
        servers_per_wave = 4
        plan = generate_recovery_plan(servers_per_wave=servers_per_wave)
        
        for wave in plan["Waves"]:
            assert len(wave["ServerIds"]) == servers_per_wave
    
    def test_generate_recovery_plan_with_dependencies(self):
        """Test plan generation with dependencies."""
        plan = generate_recovery_plan(wave_count=3, with_dependencies=True)
        
        assert plan["Waves"][0]["Dependencies"] == []
        assert plan["Waves"][1]["Dependencies"] == ["Wave-1"]
        assert plan["Waves"][2]["Dependencies"] == ["Wave-2"]
    
    def test_generate_recovery_plan_without_dependencies(self):
        """Test plan generation without dependencies."""
        plan = generate_recovery_plan(wave_count=3, with_dependencies=False)
        
        for wave in plan["Waves"]:
            assert wave["Dependencies"] == []
    
    def test_generate_recovery_plan_execution_types(self):
        """Test plan generation with specific execution types."""
        execution_types = ["PARALLEL", "SEQUENTIAL", "PARALLEL"]
        plan = generate_recovery_plan(
            wave_count=3,
            execution_types=execution_types
        )
        
        for i, wave in enumerate(plan["Waves"]):
            assert wave["ExecutionType"] == execution_types[i]
    
    def test_generate_recovery_plan_wait_times(self):
        """Test plan generation with specific wait times."""
        wait_times = [30, 60, 90]
        plan = generate_recovery_plan(
            wave_count=3,
            wait_times=wait_times
        )
        
        for i, wave in enumerate(plan["Waves"]):
            assert wave["WaitTimeSeconds"] == wait_times[i]
    
    def test_generate_recovery_plan_parallel_execution_order(self):
        """Test parallel waves have correct execution order."""
        plan = generate_recovery_plan(
            wave_count=1,
            servers_per_wave=5,
            execution_types=["PARALLEL"]
        )
        
        wave = plan["Waves"][0]
        assert all(order == 1 for order in wave["ExecutionOrder"])
    
    def test_generate_recovery_plan_sequential_execution_order(self):
        """Test sequential waves have correct execution order."""
        servers_per_wave = 5
        plan = generate_recovery_plan(
            wave_count=1,
            servers_per_wave=servers_per_wave,
            execution_types=["SEQUENTIAL"]
        )
        
        wave = plan["Waves"][0]
        assert wave["ExecutionOrder"] == list(range(1, servers_per_wave + 1))
    
    def test_generate_recovery_plan_required_fields(self):
        """Test generated plan has all required fields."""
        plan = generate_recovery_plan()
        
        required_fields = [
            "PlanId", "PlanName", "Description", "AccountId",
            "Region", "Owner", "RPO", "RTO", "Waves",
            "CreatedDate", "LastModifiedDate"
        ]
        
        for field in required_fields:
            assert field in plan
    
    def test_generate_recovery_plan_wave_fields(self):
        """Test generated waves have all required fields."""
        plan = generate_recovery_plan()
        
        required_wave_fields = [
            "WaveNumber", "WaveName", "WaveDescription",
            "ServerIds", "ExecutionType", "ExecutionOrder",
            "Dependencies", "WaitTimeSeconds"
        ]
        
        for wave in plan["Waves"]:
            for field in required_wave_fields:
                assert field in wave


class TestExecutionHistoryGeneration:
    """Test execution history generation."""
    
    def test_generate_execution_history_basic(self):
        """Test basic execution history generation."""
        plan_id = "test-plan-001"
        execution = generate_execution_history(plan_id)
        
        assert execution["PlanId"] == plan_id
        assert "ExecutionId" in execution
        assert "Status" in execution
    
    def test_generate_execution_history_status(self):
        """Test execution history with specific status."""
        statuses = ["RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
        
        for status in statuses:
            execution = generate_execution_history("plan-001", status=status)
            assert execution["Status"] == status
    
    def test_generate_execution_history_wave_count(self):
        """Test execution history with specific wave count."""
        wave_count = 5
        execution = generate_execution_history(
            "plan-001",
            wave_count=wave_count
        )
        
        assert len(execution["WaveStatuses"]) == wave_count
    
    def test_generate_execution_history_with_errors(self):
        """Test execution history with errors."""
        execution = generate_execution_history(
            "plan-001",
            with_errors=True
        )
        
        assert "Errors" in execution
        # Should have at least some failed servers
        assert execution["FailedServers"] > 0
    
    def test_generate_execution_history_without_errors(self):
        """Test execution history without errors."""
        execution = generate_execution_history(
            "plan-001",
            with_errors=False
        )
        
        # All servers should be successful
        assert execution["SuccessfulServers"] == execution["TotalServers"]
    
    def test_generate_execution_history_server_counts(self):
        """Test execution history has correct server counts."""
        wave_count = 3
        servers_per_wave = 4
        execution = generate_execution_history(
            "plan-001",
            wave_count=wave_count,
            servers_per_wave=servers_per_wave
        )
        
        assert execution["TotalServers"] == wave_count * servers_per_wave
        assert execution["SuccessfulServers"] + execution["FailedServers"] == execution["TotalServers"]
    
    def test_generate_execution_history_timing(self):
        """Test execution history has valid timing."""
        execution = generate_execution_history("plan-001", status="COMPLETED")
        
        assert execution["StartTime"] > 0
        assert execution["EndTime"] > execution["StartTime"]
    
    def test_generate_execution_history_running_no_end_time(self):
        """Test running execution has no end time."""
        execution = generate_execution_history("plan-001", status="RUNNING")
        
        assert execution["EndTime"] is None


class TestMultipleExecutionsGeneration:
    """Test multiple executions generation."""
    
    def test_generate_multiple_executions_count(self):
        """Test generating multiple executions."""
        count = 10
        executions = generate_multiple_executions(count)
        
        assert len(executions) == count
    
    def test_generate_multiple_executions_same_plan(self):
        """Test generating executions for same plan."""
        plan_id = "test-plan-001"
        executions = generate_multiple_executions(5, plan_id=plan_id)
        
        for execution in executions:
            assert execution["PlanId"] == plan_id
    
    def test_generate_multiple_executions_status_distribution(self):
        """Test status distribution in multiple executions."""
        count = 100
        status_distribution = {
            "COMPLETED": 0.8,
            "FAILED": 0.2
        }
        
        executions = generate_multiple_executions(
            count,
            status_distribution=status_distribution
        )
        
        completed = sum(1 for e in executions if e["Status"] == "COMPLETED")
        failed = sum(1 for e in executions if e["Status"] == "FAILED")
        
        # Allow some variance (±15%)
        assert 65 <= completed <= 95
        assert 5 <= failed <= 35


class TestProtectionGroupGeneration:
    """Test protection group generation."""
    
    def test_generate_protection_group_basic(self):
        """Test basic protection group generation."""
        pg = generate_protection_group()
        
        assert "GroupId" in pg
        assert "ServerIds" in pg
        assert len(pg["ServerIds"]) == 5  # Default count
    
    def test_generate_protection_group_custom_servers(self):
        """Test protection group with custom server count."""
        server_count = 10
        pg = generate_protection_group(server_count=server_count)
        
        assert len(pg["ServerIds"]) == server_count
    
    def test_generate_protection_group_required_fields(self):
        """Test protection group has required fields."""
        pg = generate_protection_group()
        
        required_fields = [
            "GroupId", "GroupName", "Description", "ServerIds",
            "Region", "AccountId", "Tags", "CreatedDate", "LastModifiedDate"
        ]
        
        for field in required_fields:
            assert field in pg


class TestUtilityGenerators:
    """Test utility generator functions."""
    
    def test_generate_random_string(self):
        """Test random string generation."""
        length = 15
        s = generate_random_string(length)
        
        assert len(s) == length
        assert s.isalnum()
    
    def test_generate_random_string_with_special(self):
        """Test random string with special characters."""
        s = generate_random_string(20, include_special=True)
        
        assert len(s) == 20
    
    def test_generate_account_id(self):
        """Test AWS account ID generation."""
        account_id = generate_account_id()
        
        assert len(account_id) == 12
        assert account_id.isdigit()
    
    def test_generate_instance_id(self):
        """Test EC2 instance ID generation."""
        instance_id = generate_instance_id()
        
        assert instance_id.startswith("i-")
        assert len(instance_id) == 19
        assert re.match(r'^i-[0-9a-f]{17}$', instance_id)
    
    def test_generate_job_id(self):
        """Test DRS job ID generation."""
        job_id = generate_job_id()
        
        assert job_id.startswith("job-")
        assert len(job_id) == 20  # job- + 16 hex chars
        assert re.match(r'^job-[0-9a-f]{16}$', job_id)


class TestConvenienceFunctions:
    """Test convenience functions for common scenarios."""
    
    def test_generate_simple_plan(self):
        """Test simple plan generation."""
        plan = generate_simple_plan()
        
        assert len(plan["Waves"]) == 1
        assert len(plan["Waves"][0]["ServerIds"]) == 2
    
    def test_generate_complex_plan(self):
        """Test complex plan generation."""
        plan = generate_complex_plan()
        
        assert len(plan["Waves"]) == 5
        
        # Verify dependencies
        for i in range(1, 5):
            assert plan["Waves"][i]["Dependencies"] == [f"Wave-{i}"]
    
    def test_generate_parallel_plan(self):
        """Test parallel plan generation."""
        plan = generate_parallel_plan()
        
        for wave in plan["Waves"]:
            assert wave["ExecutionType"] == "PARALLEL"
            assert all(order == 1 for order in wave["ExecutionOrder"])
    
    def test_generate_sequential_plan(self):
        """Test sequential plan generation."""
        plan = generate_sequential_plan()
        
        for wave in plan["Waves"]:
            assert wave["ExecutionType"] == "SEQUENTIAL"
            # Verify sequential ordering
            expected_order = list(range(1, len(wave["ServerIds"]) + 1))
            assert wave["ExecutionOrder"] == expected_order
