"""
Unit tests for recovery plan fixtures.
Validates that all fixtures generate valid recovery plan structures.
"""
import pytest
from fixtures.recovery_plan_fixtures import (
    create_single_wave_plan,
    create_three_wave_plan,
    create_five_wave_plan,
    create_parallel_wave_plan,
    create_mixed_execution_plan,
    create_plan_with_transitive_dependencies,
    create_plan_with_wait_times,
    create_real_drs_server_plan,
    get_all_fixtures,
    get_fixture
)


class TestRecoveryPlanFixtures:
    """Test suite for recovery plan fixtures."""

    def test_single_wave_plan_structure(self):
        """Test single wave plan has correct structure."""
        plan = create_single_wave_plan()
        
        assert plan["PlanId"] == "test-plan-001"
        assert len(plan["Waves"]) == 1
        assert plan["Waves"][0]["WaveNumber"] == 1
        assert plan["Waves"][0]["ExecutionType"] == "SEQUENTIAL"
        assert len(plan["Waves"][0]["ServerIds"]) == 2

    def test_three_wave_plan_structure(self):
        """Test three wave plan has correct structure and dependencies."""
        plan = create_three_wave_plan()
        
        assert len(plan["Waves"]) == 3
        assert plan["Waves"][0]["Dependencies"] == []
        assert plan["Waves"][1]["Dependencies"] == ["Wave-1"]
        assert plan["Waves"][2]["Dependencies"] == ["Wave-2"]
        
        # Verify execution types
        assert plan["Waves"][0]["ExecutionType"] == "SEQUENTIAL"
        assert plan["Waves"][1]["ExecutionType"] == "PARALLEL"
        assert plan["Waves"][2]["ExecutionType"] == "PARALLEL"

    def test_five_wave_plan_structure(self):
        """Test five wave plan has correct structure."""
        plan = create_five_wave_plan()
        
        assert len(plan["Waves"]) == 5
        assert plan["Waves"][0]["WaveName"] == "Foundation"
        assert plan["Waves"][4]["WaveName"] == "Edge"
        
        # Verify dependency chain
        for i in range(1, 5):
            assert plan["Waves"][i]["Dependencies"] == [f"Wave-{i}"]

    def test_parallel_wave_plan(self):
        """Test parallel wave plan with custom server count."""
        server_count = 6
        plan = create_parallel_wave_plan(server_count=server_count)
        
        assert len(plan["Waves"]) == 1
        assert len(plan["Waves"][0]["ServerIds"]) == server_count
        assert plan["Waves"][0]["ExecutionType"] == "PARALLEL"
        assert all(order == 1 for order in plan["Waves"][0]["ExecutionOrder"])

    def test_mixed_execution_plan(self):
        """Test plan with mixed sequential and parallel execution."""
        plan = create_mixed_execution_plan()
        
        assert len(plan["Waves"]) == 2
        assert plan["Waves"][0]["ExecutionType"] == "SEQUENTIAL"
        assert plan["Waves"][1]["ExecutionType"] == "PARALLEL"
        assert plan["Waves"][1]["Dependencies"] == ["Wave-1"]

    def test_transitive_dependencies(self):
        """Test plan with transitive dependencies."""
        plan = create_plan_with_transitive_dependencies()
        
        assert len(plan["Waves"]) == 3
        assert plan["Waves"][0]["Dependencies"] == []
        assert plan["Waves"][1]["Dependencies"] == ["Wave-1"]
        assert plan["Waves"][2]["Dependencies"] == ["Wave-2"]

    def test_wait_times_plan(self):
        """Test plan with configurable wait times."""
        wait_times = [30, 60, 90]
        plan = create_plan_with_wait_times(wait_times=wait_times)
        
        assert len(plan["Waves"]) == 3
        for i, wait_time in enumerate(wait_times):
            assert plan["Waves"][i]["WaitTimeSeconds"] == wait_time

    def test_real_drs_server_plan(self):
        """Test plan with real DRS server IDs."""
        plan = create_real_drs_server_plan()
        
        assert plan["AccountId"] == "777788889999"
        assert plan["Region"] == "us-east-1"
        assert len(plan["Waves"]) == 3
        
        # Verify real server ID format (s-{17 hex chars})
        for wave in plan["Waves"]:
            for server_id in wave["ServerIds"]:
                assert server_id.startswith("s-")
                assert len(server_id) == 19  # s- + 17 chars

    def test_get_all_fixtures(self):
        """Test get_all_fixtures returns all fixtures."""
        fixtures = get_all_fixtures()
        
        assert len(fixtures) == 8
        assert "single_wave" in fixtures
        assert "three_wave" in fixtures
        assert "five_wave" in fixtures
        assert "parallel" in fixtures
        assert "mixed" in fixtures
        assert "transitive" in fixtures
        assert "wait_times" in fixtures
        assert "real_drs" in fixtures

    def test_get_fixture_by_name(self):
        """Test get_fixture retrieves fixtures by name."""
        plan = get_fixture("three_wave")
        assert len(plan["Waves"]) == 3

    def test_get_fixture_with_params(self):
        """Test get_fixture with custom parameters."""
        plan = get_fixture("three_wave", servers_per_wave=4)
        assert len(plan["Waves"][0]["ServerIds"]) == 4

    def test_get_fixture_invalid_name(self):
        """Test get_fixture raises error for invalid name."""
        with pytest.raises(ValueError, match="Unknown fixture"):
            get_fixture("nonexistent")

    def test_all_plans_have_required_fields(self):
        """Test all fixtures have required fields."""
        required_fields = ["PlanId", "PlanName", "Description", "AccountId", 
                          "Region", "Owner", "RPO", "RTO", "Waves", 
                          "CreatedDate", "LastModifiedDate"]
        
        fixtures = get_all_fixtures()
        for name, plan in fixtures.items():
            for field in required_fields:
                assert field in plan, f"Fixture '{name}' missing field '{field}'"

    def test_all_waves_have_required_fields(self):
        """Test all waves have required fields."""
        required_wave_fields = ["WaveNumber", "WaveName", "WaveDescription",
                               "ServerIds", "ExecutionType", "ExecutionOrder",
                               "Dependencies", "WaitTimeSeconds"]
        
        fixtures = get_all_fixtures()
        for name, plan in fixtures.items():
            for wave in plan["Waves"]:
                for field in required_wave_fields:
                    assert field in wave, f"Fixture '{name}' wave missing field '{field}'"

    def test_execution_order_matches_server_count(self):
        """Test ExecutionOrder list length matches ServerIds length."""
        fixtures = get_all_fixtures()
        for name, plan in fixtures.items():
            for wave in plan["Waves"]:
                assert len(wave["ExecutionOrder"]) == len(wave["ServerIds"]), \
                    f"Fixture '{name}' wave {wave['WaveNumber']} has mismatched ExecutionOrder"

    def test_wave_numbers_are_sequential(self):
        """Test wave numbers are sequential starting from 1."""
        fixtures = get_all_fixtures()
        for name, plan in fixtures.items():
            wave_numbers = [w["WaveNumber"] for w in plan["Waves"]]
            expected = list(range(1, len(plan["Waves"]) + 1))
            assert wave_numbers == expected, \
                f"Fixture '{name}' has non-sequential wave numbers"
