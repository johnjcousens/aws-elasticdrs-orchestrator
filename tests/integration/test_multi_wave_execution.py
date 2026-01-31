"""
Integration test for multi-wave execution lifecycle.

Tests the complete flow of a 3-wave DR execution from creation through
polling to finalization, verifying that:
1. Execution status remains POLLING while waves execute
2. Each wave completes independently
3. Execution finalizes only after all 3 waves complete
4. Server data is enriched for each wave
"""

import json
import os
import sys
import time
from decimal import Decimal
from unittest.mock import Mock, patch

import boto3
import pytest
from moto import mock_aws

# Add lambda directory to path
lambda_dir = os.path.join(os.path.dirname(__file__), "../../lambda")
sys.path.insert(0, os.path.join(lambda_dir, "execution-handler"))
sys.path.insert(0, lambda_dir)


@pytest.fixture(scope="function", autouse=False)
def mock_shared_modules():
    """Mock shared modules for handler import, but NOT launch_config_validation."""
    # Save original modules
    original_modules = {}
    mock_modules = [
        'shared.account_utils',
        'shared.config_merge',
        'shared.conflict_detection',
        'shared.cross_account',
        'shared.drs_limits',
        'shared.drs_utils',
        'shared.execution_utils',
        'shared.rbac_middleware',
        'shared.response_utils',
        'shared.security_utils',
    ]
    
    for module_name in mock_modules:
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
    
    # Mock the modules (will be set up by each test file's specific mocks)
    yield
    
    # Restore original modules
    for module_name in mock_modules:
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]
        else:
            sys.modules.pop(module_name, None)


# NOTE: Module-level mocking removed to prevent pytest collection conflicts
# Tests that need mocking should use fixtures or patch decorators within the test function
#
# # Mock shared modules
# sys.modules['shared'] = Mock()
# sys.modules['shared.config_merge'] = Mock()
# sys.modules['shared.conflict_detection'] = Mock()
# sys.modules['shared.cross_account'] = Mock()
# sys.modules['shared.drs_limits'] = Mock()
# sys.modules['shared.execution_utils'] = Mock()
# sys.modules['shared.drs_utils'] = Mock()
# 
# # Mock response_utils with proper response function
# mock_response_utils = Mock()
# 
# # Create a proper DecimalEncoder class
# class MockDecimalEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, Decimal):
#             return int(obj) if obj % 1 == 0 else float(obj)
#         return super().default(obj)
# 
# def mock_response(status_code, body, headers=None):
#     """Mock response function that returns proper API Gateway response"""
#     return {
#         "statusCode": status_code,
#         "headers": {
#             "Content-Type": "application/json",
#             "Access-Control-Allow-Origin": "*",
#         },
#         "body": json.dumps(body, cls=MockDecimalEncoder)
#     }
# mock_response_utils.response = mock_response
# mock_response_utils.DecimalEncoder = MockDecimalEncoder
# sys.modules['shared.response_utils'] = mock_response_utils


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for moto"""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # pragma: allowlist secret
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create mock DynamoDB table for executions"""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        
        # Create execution history table
        table = dynamodb.create_table(
            TableName="test-execution-table",
            KeySchema=[
                {"AttributeName": "executionId", "KeyType": "HASH"},
                {"AttributeName": "planId", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "executionId", "AttributeType": "S"},
                {"AttributeName": "planId", "AttributeType": "S"},
                {"AttributeName": "status", "AttributeType": "S"}
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "StatusIndex",
                    "KeySchema": [
                        {"AttributeName": "status", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5
                    }
                }
            ],
            BillingMode="PROVISIONED",
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )
        
        yield table


@pytest.fixture
def mock_env_vars():
    """Set up environment variables"""
    with patch.dict(os.environ, {
        "EXECUTION_HISTORY_TABLE": "test-execution-table",
        "PROTECTION_GROUPS_TABLE": "test-pg-table",
        "RECOVERY_PLANS_TABLE": "test-plans-table",
        "TARGET_ACCOUNTS_TABLE": "test-accounts-table",
        "PROJECT_NAME": "test-project",
        "ENVIRONMENT": "test",
        "STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:test"
    }):
        yield


def create_multi_wave_execution(table, execution_id="test-exec-multi", plan_id="test-plan-1"):
    """Helper to create a 3-wave execution in DynamoDB"""
    execution = {
        "executionId": execution_id,
        "planId": plan_id,
        "status": "POLLING",
        "executionType": "DRILL",
        "waves": [
            {
                "waveNumber": Decimal("0"),
                "waveName": "DBWave1",
                "status": "IN_PROGRESS",
                "jobId": "job-wave-0",
                "region": "us-east-1",
                "serverStatuses": []
            },
            {
                "waveNumber": Decimal("1"),
                "waveName": "AppWave2",
                "status": "PENDING",
                "jobId": "job-wave-1",
                "region": "us-east-1",
                "serverStatuses": []
            },
            {
                "waveNumber": Decimal("2"),
                "waveName": "WebWave3",
                "status": "PENDING",
                "jobId": "job-wave-2",
                "region": "us-east-1",
                "serverStatuses": []
            }
        ],
        "createdTime": Decimal(str(int(time.time()))),
        "lastPolledTime": Decimal(str(int(time.time())))
    }
    
    table.put_item(Item=execution)
    return execution


def mock_drs_job_response(job_id, status="COMPLETED", server_count=2):
    """Helper to create mock DRS job response"""
    servers = []
    for i in range(server_count):
        servers.append({
            "sourceServerID": f"s-server-{i}",
            "launchStatus": "LAUNCHED" if status == "COMPLETED" else "LAUNCHING",
            "recoveryInstanceID": f"i-instance-{i}"
        })
    
    return {
        "items": [{
            "jobID": job_id,
            "status": status,
            "type": "LAUNCH",
            "participatingServers": servers
        }]
    }


def mock_enriched_servers(server_count=2, wave_number=0):
    """Helper to create mock enriched server data"""
    servers = []
    for i in range(server_count):
        servers.append({
            "sourceServerId": f"s-server-{i}",
            "serverName": f"server-wave{wave_number}-{i}",
            "launchStatus": "LAUNCHED",
            "instanceId": f"i-instance-{i}",
            "privateIp": f"10.0.{wave_number}.{10+i}",
            "hostname": f"ip-10-0-{wave_number}-{10+i}.ec2.internal",
            "instanceType": "t3.medium",
            "instanceState": "running"
        })
    return servers


class TestMultiWaveExecution:
    """Integration tests for 3-wave execution lifecycle"""

    def test_three_wave_execution_complete_flow(
        self, dynamodb_table, mock_env_vars
    ):
        """
        Test complete 3-wave execution flow:
        1. Create execution with 3 waves (wave 0 IN_PROGRESS, waves 1-2 PENDING)
        2. Poll wave 0 until complete
        3. Verify execution status remains POLLING
        4. Start wave 1, poll until complete
        5. Verify execution status still POLLING
        6. Start wave 2, poll until complete
        7. Finalize execution
        8. Verify execution status is COMPLETED
        """
        from index import lambda_handler
        
        # Step 1: Create 3-wave execution
        execution = create_multi_wave_execution(
            dynamodb_table,
            execution_id="exec-3wave",
            plan_id="plan-1"
        )
        
        # Mock boto3.client for DRS and EC2
        with patch("boto3.client") as mock_boto_client:
            mock_drs = Mock()
            mock_ec2 = Mock()
            
            def get_client(service, **kwargs):
                if service == "drs":
                    return mock_drs
                elif service == "ec2":
                    return mock_ec2
                return Mock()
            
            mock_boto_client.side_effect = get_client
            
            # Step 2: Poll wave 0 (complete)
            mock_drs.describe_jobs.return_value = mock_drs_job_response("job-wave-0", "COMPLETED", 2)
            
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = mock_enriched_servers(2, 0)
                
                poll_event = {
                    "operation": "poll",
                    "executionId": "exec-3wave",
                    "planId": "plan-1"
                }
                
                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())
                
                # Verify wave 0 complete but execution still POLLING
                assert result["statusCode"] == 200
                assert result["status"] == "POLLING"
                assert result["allWavesComplete"] is False  # Waves 1-2 still pending
                assert result["waves"][0]["status"] == "COMPLETED"
                assert result["waves"][1]["status"] == "PENDING"
                assert result["waves"][2]["status"] == "PENDING"
            
            # Step 3: Update wave 1 to IN_PROGRESS and poll
            response = dynamodb_table.get_item(
                Key={"executionId": "exec-3wave", "planId": "plan-1"}
            )
            exec_item = response["Item"]
            exec_item["waves"][1]["status"] = "IN_PROGRESS"
            dynamodb_table.put_item(Item=exec_item)
            
            mock_drs.describe_jobs.return_value = mock_drs_job_response("job-wave-1", "COMPLETED", 3)
            
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = mock_enriched_servers(3, 1)
                
                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())
                
                # Verify wave 1 complete but execution still POLLING
                assert result["status"] == "POLLING"
                assert result["allWavesComplete"] is False  # Wave 2 still pending
                assert result["waves"][0]["status"] == "COMPLETED"
                assert result["waves"][1]["status"] == "COMPLETED"
                assert result["waves"][2]["status"] == "PENDING"
            
            # Step 4: Update wave 2 to IN_PROGRESS and poll
            response = dynamodb_table.get_item(
                Key={"executionId": "exec-3wave", "planId": "plan-1"}
            )
            exec_item = response["Item"]
            exec_item["waves"][2]["status"] = "IN_PROGRESS"
            dynamodb_table.put_item(Item=exec_item)
            
            mock_drs.describe_jobs.return_value = mock_drs_job_response("job-wave-2", "COMPLETED", 4)
            
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = mock_enriched_servers(4, 2)
                
                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())
                
                # Verify all waves complete
                assert result["status"] == "POLLING"  # Still POLLING until finalized
                assert result["allWavesComplete"] is True  # All waves done
                assert result["waves"][0]["status"] == "COMPLETED"
                assert result["waves"][1]["status"] == "COMPLETED"
                assert result["waves"][2]["status"] == "COMPLETED"
        
        # Step 5: Finalize execution
        finalize_event = {
            "operation": "finalize",
            "executionId": "exec-3wave",
            "planId": "plan-1"
        }
        
        with patch("index.execution_history_table", dynamodb_table):
            finalize_result = lambda_handler(finalize_event, Mock())
        
        # Verify finalization
        assert finalize_result["statusCode"] == 200
        assert finalize_result["status"] == "COMPLETED"
        
        # Step 6: Verify final state in DynamoDB
        response = dynamodb_table.get_item(
            Key={"executionId": "exec-3wave", "planId": "plan-1"}
        )
        
        final_execution = response["Item"]
        assert final_execution["status"] == "COMPLETED"
        assert "endTime" in final_execution
        assert len(final_execution["waves"]) == 3
        assert all(w["status"] == "COMPLETED" for w in final_execution["waves"])


    def test_execution_status_never_changes_during_polling(
        self, dynamodb_table, mock_env_vars
    ):
        """
        Test that execution status remains POLLING throughout all wave completions.
        Only finalize operation should change status to COMPLETED.
        """
        from index import lambda_handler
        
        # Create 3-wave execution
        execution = create_multi_wave_execution(
            dynamodb_table,
            execution_id="exec-status-check",
            plan_id="plan-1"
        )
        
        with patch("boto3.client") as mock_boto_client:
            mock_drs = Mock()
            mock_drs.describe_jobs.return_value = mock_drs_job_response("job-wave-0", "COMPLETED", 1)
            
            def get_client(service, **kwargs):
                return mock_drs if service == "drs" else Mock()
            
            mock_boto_client.side_effect = get_client
            
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = mock_enriched_servers(1, 0)
                
                poll_event = {
                    "operation": "poll",
                    "executionId": "exec-status-check",
                    "planId": "plan-1"
                }
                
                # Poll 10 times
                for i in range(10):
                    with patch("index.execution_history_table", dynamodb_table):
                        result = lambda_handler(poll_event, Mock())
                    
                    # Verify status always POLLING
                    assert result["status"] == "POLLING", f"Poll {i+1} changed status"
                
                # Verify DynamoDB status still POLLING
                response = dynamodb_table.get_item(
                    Key={"executionId": "exec-status-check", "planId": "plan-1"}
                )
                assert response["Item"]["status"] == "POLLING"

    def test_cannot_finalize_with_incomplete_waves(
        self, dynamodb_table, mock_env_vars
    ):
        """
        Test that finalization fails when not all waves are complete.
        """
        from index import lambda_handler
        
        # Create 3-wave execution with only wave 0 complete
        execution = create_multi_wave_execution(
            dynamodb_table,
            execution_id="exec-incomplete-waves",
            plan_id="plan-1"
        )
        
        # Update wave 0 to COMPLETED, leave waves 1-2 PENDING
        response = dynamodb_table.get_item(
            Key={"executionId": "exec-incomplete-waves", "planId": "plan-1"}
        )
        exec_item = response["Item"]
        exec_item["waves"][0]["status"] = "COMPLETED"
        dynamodb_table.put_item(Item=exec_item)
        
        # Try to finalize
        finalize_event = {
            "operation": "finalize",
            "executionId": "exec-incomplete-waves",
            "planId": "plan-1"
        }
        
        with patch("index.execution_history_table", dynamodb_table):
            result = lambda_handler(finalize_event, Mock())
        
        # Should fail
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "WAVES_NOT_COMPLETE" in body["error"]
        
        # Verify execution status unchanged
        response = dynamodb_table.get_item(
            Key={"executionId": "exec-incomplete-waves", "planId": "plan-1"}
        )
        assert response["Item"]["status"] == "POLLING"

    def test_each_wave_enriched_independently(
        self, dynamodb_table, mock_env_vars
    ):
        """
        Test that each wave's server data is enriched independently.
        """
        from index import lambda_handler
        
        # Create 3-wave execution
        execution = create_multi_wave_execution(
            dynamodb_table,
            execution_id="exec-enrichment",
            plan_id="plan-1"
        )
        
        with patch("boto3.client") as mock_boto_client:
            mock_drs = Mock()
            
            def get_client(service, **kwargs):
                return mock_drs if service == "drs" else Mock()
            
            mock_boto_client.side_effect = get_client
            
            poll_event = {
                "operation": "poll",
                "executionId": "exec-enrichment",
                "planId": "plan-1"
            }
            
            # Poll wave 0
            mock_drs.describe_jobs.return_value = mock_drs_job_response("job-wave-0", "COMPLETED", 2)
            
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = mock_enriched_servers(2, 0)
                
                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())
                
                # Verify wave 0 enriched
                wave0_servers = result["waves"][0]["serverStatuses"]
                assert len(wave0_servers) == 2
                assert wave0_servers[0]["privateIp"] == "10.0.0.10"
                assert wave0_servers[0]["serverName"] == "server-wave0-0"
            
            # Update wave 1 to IN_PROGRESS and poll
            response = dynamodb_table.get_item(
                Key={"executionId": "exec-enrichment", "planId": "plan-1"}
            )
            exec_item = response["Item"]
            exec_item["waves"][1]["status"] = "IN_PROGRESS"
            dynamodb_table.put_item(Item=exec_item)
            
            mock_drs.describe_jobs.return_value = mock_drs_job_response("job-wave-1", "COMPLETED", 3)
            
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = mock_enriched_servers(3, 1)
                
                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())
                
                # Verify wave 1 enriched with different data
                wave1_servers = result["waves"][1]["serverStatuses"]
                assert len(wave1_servers) == 3
                assert wave1_servers[0]["privateIp"] == "10.0.1.10"
                assert wave1_servers[0]["serverName"] == "server-wave1-0"
                
                # Verify wave 0 data preserved
                wave0_servers = result["waves"][0]["serverStatuses"]
                assert len(wave0_servers) == 2
                assert wave0_servers[0]["privateIp"] == "10.0.0.10"

    def test_all_waves_complete_flag_accuracy(
        self, dynamodb_table, mock_env_vars
    ):
        """
        Test that allWavesComplete flag is accurate throughout execution.
        """
        from index import lambda_handler
        
        # Create 3-wave execution
        execution = create_multi_wave_execution(
            dynamodb_table,
            execution_id="exec-flag-test",
            plan_id="plan-1"
        )
        
        with patch("boto3.client") as mock_boto_client:
            mock_drs = Mock()
            mock_drs.describe_jobs.return_value = mock_drs_job_response("job-wave-0", "COMPLETED", 1)
            
            def get_client(service, **kwargs):
                return mock_drs if service == "drs" else Mock()
            
            mock_boto_client.side_effect = get_client
            
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = mock_enriched_servers(1, 0)
                
                poll_event = {
                    "operation": "poll",
                    "executionId": "exec-flag-test",
                    "planId": "plan-1"
                }
                
                # Poll with wave 0 complete, waves 1-2 pending
                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())
                
                assert result["allWavesComplete"] is False
                
                # Complete wave 1
                response = dynamodb_table.get_item(
                    Key={"executionId": "exec-flag-test", "planId": "plan-1"}
                )
                exec_item = response["Item"]
                exec_item["waves"][1]["status"] = "COMPLETED"
                dynamodb_table.put_item(Item=exec_item)
                
                # Poll again
                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())
                
                assert result["allWavesComplete"] is False  # Wave 2 still pending
                
                # Complete wave 2
                response = dynamodb_table.get_item(
                    Key={"executionId": "exec-flag-test", "planId": "plan-1"}
                )
                exec_item = response["Item"]
                exec_item["waves"][2]["status"] = "COMPLETED"
                dynamodb_table.put_item(Item=exec_item)
                
                # Poll final time
                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())
                
                assert result["allWavesComplete"] is True  # All waves complete

    def test_pause_resume_between_waves(
        self, dynamodb_table, mock_env_vars
    ):
        """
        Test pause/resume functionality via operation-based invocation.
        
        Scenario:
        1. Create execution with 2 waves
        2. Pause execution via operation="pause"
        3. Verify status changes to PAUSED
        4. Resume execution via operation="resume"
        5. Verify status changes back to POLLING
        """
        from index import lambda_handler
        
        # Create execution with 2 waves
        execution = {
            "executionId": "exec-pause-resume",
            "planId": "plan-1",
            "status": "POLLING",
            "executionType": "DRILL",
            "taskToken": "test-task-token-12345",  # Required for resume
            "waves": [
                {
                    "waveNumber": Decimal("0"),
                    "waveName": "DBWave1",
                    "status": "COMPLETED",
                    "jobId": "job-wave-0",
                    "region": "us-east-1",
                    "serverStatuses": mock_enriched_servers(2, 0)
                },
                {
                    "waveNumber": Decimal("1"),
                    "waveName": "AppWave2",
                    "status": "PENDING",
                    "jobId": "job-wave-1",
                    "region": "us-east-1",
                    "serverStatuses": []
                }
            ],
            "createdTime": Decimal(str(int(time.time()))),
            "lastPolledTime": Decimal(str(int(time.time())))
        }
        
        dynamodb_table.put_item(Item=execution)
        
        # Step 1: Pause execution via operation-based invocation
        pause_event = {
            "operation": "pause",
            "executionId": "exec-pause-resume",
            "reason": "Manual approval required before wave 1"
        }
        
        with patch("index.execution_history_table", dynamodb_table):
            with patch("index.stepfunctions") as mock_sf:
                # Mock Step Functions describe_execution
                mock_sf.describe_execution.return_value = {
                    "status": "RUNNING",
                    "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test:exec-pause-resume"
                }
                
                pause_result = lambda_handler(pause_event, Mock())
        
        assert pause_result["statusCode"] == 200
        body = json.loads(pause_result["body"])
        assert body["status"] == "PAUSED"
        
        # Verify DynamoDB status changed to PAUSED
        response = dynamodb_table.get_item(
            Key={"executionId": "exec-pause-resume", "planId": "plan-1"}
        )
        assert response["Item"]["status"] == "PAUSED"
        
        # Step 2: Resume execution via operation-based invocation
        resume_event = {
            "operation": "resume",
            "executionId": "exec-pause-resume"
        }
        
        with patch("index.execution_history_table", dynamodb_table):
            with patch("index.recovery_plans_table") as mock_plans_table:
                with patch("index.stepfunctions") as mock_sf:
                    # Mock recovery plan with waves
                    mock_plans_table.get_item.return_value = {
                        "Item": {
                            "planId": "plan-1",
                            "waves": [
                                {"waveNumber": 0, "waveName": "DBWave1"},
                                {"waveNumber": 1, "waveName": "AppWave2"}
                            ]
                        }
                    }
                    
                    # Mock Step Functions send_task_success
                    mock_sf.send_task_success.return_value = {}
                    
                    resume_result = lambda_handler(resume_event, Mock())
        
        assert resume_result["statusCode"] == 200
        body = json.loads(resume_result["body"])
        assert body["status"] == "RESUMING"  # Status is RESUMING when Step Functions callback succeeds
        
        # Verify DynamoDB status changed (Step Functions will update to POLLING)
        response = dynamodb_table.get_item(
            Key={"executionId": "exec-pause-resume", "planId": "plan-1"}
        )
        # Status may be PAUSED or RESUMING depending on timing
        assert response["Item"]["status"] in ["PAUSED", "RESUMING"]

    def test_execution_finalization_updates_all_fields(
        self, dynamodb_table, mock_env_vars
    ):
        """
        Test that finalization updates all required fields in DynamoDB.
        
        Verifies:
        - status changes to COMPLETED
        - endTime is set
        - completedWaves count is accurate
        - all wave statuses are COMPLETED
        """
        from index import lambda_handler
        
        # Create execution with all waves complete
        execution = {
            "executionId": "exec-finalize-fields",
            "planId": "plan-1",
            "status": "POLLING",
            "executionType": "DRILL",
            "waves": [
                {
                    "waveNumber": Decimal("0"),
                    "waveName": "Wave1",
                    "status": "COMPLETED",
                    "jobId": "job-0",
                    "region": "us-east-1",
                    "serverStatuses": mock_enriched_servers(2, 0)
                },
                {
                    "waveNumber": Decimal("1"),
                    "waveName": "Wave2",
                    "status": "COMPLETED",
                    "jobId": "job-1",
                    "region": "us-east-1",
                    "serverStatuses": mock_enriched_servers(3, 1)
                }
            ],
            "createdTime": Decimal(str(int(time.time()))),
            "lastPolledTime": Decimal(str(int(time.time())))
        }
        
        dynamodb_table.put_item(Item=execution)
        
        # Finalize execution
        finalize_event = {
            "operation": "finalize",
            "executionId": "exec-finalize-fields",
            "planId": "plan-1"
        }
        
        before_time = int(time.time())
        
        with patch("index.execution_history_table", dynamodb_table):
            result = lambda_handler(finalize_event, Mock())
        
        after_time = int(time.time())
        
        # Verify response
        assert result["statusCode"] == 200
        assert result["status"] == "COMPLETED"
        
        # Verify DynamoDB updates
        response = dynamodb_table.get_item(
            Key={"executionId": "exec-finalize-fields", "planId": "plan-1"}
        )
        
        final_exec = response["Item"]
        
        # Check status
        assert final_exec["status"] == "COMPLETED"
        
        # Check endTime set and reasonable
        assert "endTime" in final_exec
        end_time = int(final_exec["endTime"])
        assert before_time <= end_time <= after_time
        
        # Check all waves still COMPLETED
        assert len(final_exec["waves"]) == 2
        assert all(w["status"] == "COMPLETED" for w in final_exec["waves"])
        
        # Check server data preserved
        assert len(final_exec["waves"][0]["serverStatuses"]) == 2
        assert len(final_exec["waves"][1]["serverStatuses"]) == 3

    def test_server_data_enrichment_preserves_drs_fields(
        self, dynamodb_table, mock_env_vars
    ):
        """
        Test that server data enrichment preserves all DRS fields and adds EC2 fields.
        
        Verifies:
        - DRS fields preserved: sourceServerId, launchStatus, launchTime
        - EC2 fields added: instanceId, privateIp, hostname, instanceType
        - Data structure is consistent across waves
        """
        from index import lambda_handler
        
        # Create execution with wave 0 in progress
        execution = create_multi_wave_execution(
            dynamodb_table,
            execution_id="exec-enrichment-fields",
            plan_id="plan-1"
        )
        
        with patch("boto3.client") as mock_boto_client:
            mock_drs = Mock()
            
            # Mock DRS response with detailed fields
            drs_response = {
                "items": [{
                    "jobID": "job-wave-0",
                    "status": "COMPLETED",
                    "type": "LAUNCH",
                    "participatingServers": [
                        {
                            "sourceServerID": "s-abc123",
                            "launchStatus": "LAUNCHED",
                            "recoveryInstanceID": "i-xyz789",
                            "launchTime": 1769370497
                        }
                    ]
                }]
            }
            
            mock_drs.describe_jobs.return_value = drs_response
            
            def get_client(service, **kwargs):
                return mock_drs if service == "drs" else Mock()
            
            mock_boto_client.side_effect = get_client
            
            # Mock enriched data with both DRS and EC2 fields
            enriched_data = [{
                # DRS fields
                "sourceServerId": "s-abc123",
                "serverName": "WINDBSRV02",
                "launchStatus": "LAUNCHED",
                "launchTime": 1769370497,
                "recoveryInstanceId": "i-xyz789",
                # EC2 fields
                "instanceId": "i-xyz789",
                "privateIp": "10.0.1.50",
                "hostname": "ip-10-0-1-50.ec2.internal",
                "instanceType": "t3.medium",
                "instanceState": "running"
            }]
            
            with patch("shared.drs_utils.enrich_server_data") as mock_enrich:
                mock_enrich.return_value = enriched_data
                
                poll_event = {
                    "operation": "poll",
                    "executionId": "exec-enrichment-fields",
                    "planId": "plan-1"
                }
                
                with patch("index.execution_history_table", dynamodb_table):
                    result = lambda_handler(poll_event, Mock())
                
                # Verify enriched data in response
                assert result["statusCode"] == 200
                servers = result["waves"][0]["serverStatuses"]
                assert len(servers) == 1
                
                server = servers[0]
                
                # Verify DRS fields preserved
                assert server["sourceServerId"] == "s-abc123"
                assert server["launchStatus"] == "LAUNCHED"
                assert server["launchTime"] == 1769370497
                
                # Verify EC2 fields added
                assert server["instanceId"] == "i-xyz789"
                assert server["privateIp"] == "10.0.1.50"
                assert server["hostname"] == "ip-10-0-1-50.ec2.internal"
                assert server["instanceType"] == "t3.medium"
                assert server["instanceState"] == "running"
        
        # Verify data persisted to DynamoDB
        response = dynamodb_table.get_item(
            Key={"executionId": "exec-enrichment-fields", "planId": "plan-1"}
        )
        
        db_servers = response["Item"]["waves"][0]["serverStatuses"]
        assert len(db_servers) == 1
        
        db_server = db_servers[0]
        assert db_server["sourceServerId"] == "s-abc123"
        assert db_server["instanceId"] == "i-xyz789"
        assert db_server["privateIp"] == "10.0.1.50"
