"""
Shared test fixtures for API Handler Decomposition integration tests.

Provides mock data for Protection Groups, Recovery Plans, and Executions.
"""

from decimal import Decimal
from datetime import datetime, timezone


def get_mock_protection_group(group_id="pg-test-123", group_name="Test Protection Group"):
    """
    Get mock Protection Group data.
    
    Args:
        group_id: Protection Group ID
        group_name: Protection Group name
        
    Returns:
        Dict with Protection Group data matching DynamoDB schema
    """
    return {
        "groupId": group_id,
        "groupName": group_name,
        "region": "us-east-1",
        "sourceServerIds": ["s-111", "s-222", "s-333"],
        "createdAt": "2024-01-15T10:00:00Z",
        "updatedAt": "2024-01-15T10:00:00Z",
        "version": Decimal("1"),
    }


def get_mock_protection_group_with_tags(group_id="pg-tags-123", group_name="Tag-Based Protection Group"):
    """
    Get mock Protection Group with tag-based server selection.
    
    Args:
        group_id: Protection Group ID
        group_name: Protection Group name
        
    Returns:
        Dict with Protection Group data using tag selection
    """
    return {
        "groupId": group_id,
        "groupName": group_name,
        "region": "us-east-1",
        "serverSelectionTags": {
            "DR-Application": "Database",
            "DR-Tier": "Production",
        },
        "createdAt": "2024-01-15T10:00:00Z",
        "updatedAt": "2024-01-15T10:00:00Z",
        "version": Decimal("1"),
    }


def get_mock_recovery_plan(plan_id="plan-test-123", plan_name="Test Recovery Plan"):
    """
    Get mock Recovery Plan data.
    
    Args:
        plan_id: Recovery Plan ID
        plan_name: Recovery Plan name
        
    Returns:
        Dict with Recovery Plan data matching DynamoDB schema
    """
    return {
        "planId": plan_id,
        "planName": plan_name,
        "waves": [
            {
                "waveName": "Wave 1",
                "protectionGroupId": "pg-test-123",
                "pauseBeforeWave": False,
            },
            {
                "waveName": "Wave 2",
                "protectionGroupId": "pg-test-456",
                "pauseBeforeWave": True,
            },
        ],
        "createdAt": "2024-01-15T10:00:00Z",
        "updatedAt": "2024-01-15T10:00:00Z",
        "version": Decimal("1"),
    }


def get_mock_execution(execution_id="exec-test-123", plan_id="plan-test-123", status="IN_PROGRESS"):
    """
    Get mock Execution data.
    
    Args:
        execution_id: Execution ID
        plan_id: Recovery Plan ID
        status: Execution status
        
    Returns:
        Dict with Execution data matching DynamoDB schema
    """
    return {
        "executionId": execution_id,
        "planId": plan_id,
        "planName": "Test Recovery Plan",
        "status": status,
        "isDrill": True,
        "currentWave": Decimal("1"),
        "totalWaves": Decimal("2"),
        "startedAt": "2024-01-15T10:00:00Z",
        "updatedAt": "2024-01-15T10:05:00Z",
        "waves": [
            {
                "waveName": "Wave 1",
                "waveNumber": Decimal("1"),
                "status": "IN_PROGRESS",
                "serverStatuses": [
                    {
                        "sourceServerId": "s-111",
                        "launchStatus": "LAUNCHED",
                        "recoveryInstanceId": "i-recovery-111",
                    },
                    {
                        "sourceServerId": "s-222",
                        "launchStatus": "PENDING",
                    },
                ],
            },
            {
                "waveName": "Wave 2",
                "waveNumber": Decimal("2"),
                "status": "PENDING",
                "serverStatuses": [],
            },
        ],
        "stepFunctionsExecutionArn": "arn:aws:states:us-east-1:123456789012:execution:DROrchestrator:exec-test-123",
    }


def get_mock_drs_source_server(source_server_id="s-111", hostname="test-server-01"):
    """
    Get mock DRS Source Server data.
    
    Args:
        source_server_id: DRS Source Server ID
        hostname: Server hostname
        
    Returns:
        Dict with DRS Source Server data matching AWS API response
    """
    return {
        "sourceServerID": source_server_id,
        "hostname": hostname,
        "arn": f"arn:aws:drs:us-east-1:123456789012:source-server/{source_server_id}",
        "tags": {
            "Name": hostname,
            "Purpose": "Database",
            "Environment": "Production",
        },
        "dataReplicationInfo": {
            "dataReplicationState": "CONTINUOUS",
            "dataReplicationInitiation": {
                "startDateTime": "2024-01-01T00:00:00Z",
            },
            "lagDuration": "PT5M",
        },
        "lifeCycle": {
            "addedToServiceDateTime": "2024-01-01T00:00:00Z",
            "lastSeenByServiceDateTime": "2024-01-15T10:00:00Z",
        },
        "sourceProperties": {
            "cpus": [{"cores": 4}],
            "disks": [
                {
                    "deviceName": "/dev/sda1",
                    "bytes": 107374182400,
                }
            ],
            "identificationHints": {
                "hostname": hostname,
            },
            "networkInterfaces": [
                {
                    "ips": ["10.0.1.100"],
                    "isPrimary": True,
                }
            ],
            "os": {
                "fullString": "Amazon Linux 2",
            },
            "ramBytes": 17179869184,
        },
    }


def get_mock_drs_job(job_id="job-test-123", status="STARTED", job_type="LAUNCH"):
    """
    Get mock DRS Job data.
    
    Args:
        job_id: DRS Job ID
        status: Job status
        job_type: Job type (LAUNCH, TERMINATE, etc.)
        
    Returns:
        Dict with DRS Job data matching AWS API response
    """
    return {
        "jobID": job_id,
        "arn": f"arn:aws:drs:us-east-1:123456789012:job/{job_id}",
        "type": job_type,
        "status": status,
        "creationDateTime": "2024-01-15T10:00:00Z",
        "endDateTime": None if status == "STARTED" else "2024-01-15T10:10:00Z",
        "participatingServers": [
            {
                "sourceServerID": "s-111",
                "launchStatus": "LAUNCHED" if status == "COMPLETED" else "PENDING",
                "recoveryInstanceID": "i-recovery-111" if status == "COMPLETED" else None,
            },
            {
                "sourceServerID": "s-222",
                "launchStatus": "LAUNCHED" if status == "COMPLETED" else "PENDING",
                "recoveryInstanceID": "i-recovery-222" if status == "COMPLETED" else None,
            },
        ],
    }


def get_mock_recovery_instance(recovery_instance_id="i-recovery-111", source_server_id="s-111"):
    """
    Get mock Recovery Instance data.
    
    Args:
        recovery_instance_id: Recovery Instance ID
        source_server_id: Source Server ID
        
    Returns:
        Dict with Recovery Instance data matching AWS API response
    """
    return {
        "recoveryInstanceID": recovery_instance_id,
        "sourceServerID": source_server_id,
        "ec2InstanceID": recovery_instance_id,
        "ec2InstanceState": "running",
        "jobID": "job-test-123",
        "recoveryInstanceProperties": {
            "cpus": [{"cores": 4}],
            "disks": [
                {
                    "bytes": 107374182400,
                    "ebsVolumeID": "vol-123",
                }
            ],
            "identificationHints": {
                "hostname": "test-server-01",
            },
            "networkInterfaces": [
                {
                    "ips": ["10.0.2.100"],
                    "isPrimary": True,
                }
            ],
            "os": {
                "fullString": "Amazon Linux 2",
            },
            "ramBytes": 17179869184,
        },
    }


def get_mock_api_gateway_event(method="GET", path="/protection-groups", body=None, query_params=None, path_params=None):
    """
    Get mock API Gateway event.
    
    Args:
        method: HTTP method
        path: Request path
        body: Request body (dict or None)
        query_params: Query string parameters (dict or None)
        path_params: Path parameters (dict or None)
        
    Returns:
        Dict with API Gateway event structure
    """
    import json
    
    # Helper to convert Decimal to int/float for JSON serialization
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        raise TypeError
    
    event = {
        "resource": path,
        "path": path,
        "httpMethod": method,
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token",
        },
        "queryStringParameters": query_params or {},
        "pathParameters": path_params or {},
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "test-api",
            "protocol": "HTTP/1.1",
            "httpMethod": method,
            "path": path,
            "stage": "dev",
            "requestId": "test-request-id",
            "requestTime": "15/Jan/2024:10:00:00 +0000",
            "requestTimeEpoch": 1705316400000,
            "identity": {
                "sourceIp": "192.168.1.1",
                "userAgent": "test-agent",
            },
            "authorizer": {
                "claims": {
                    "sub": "test-user-id",
                    "email": "test@example.com",
                    "cognito:groups": "Administrators",
                }
            },
        },
        "body": json.dumps(body, default=decimal_default) if body else None,
        "isBase64Encoded": False,
    }
    
    return event


def get_mock_direct_invocation_event(operation, body=None, query_params=None):
    """
    Get mock direct Lambda invocation event.
    
    Args:
        operation: Operation name
        body: Request body (dict or None)
        query_params: Query parameters (dict or None)
        
    Returns:
        Dict with direct invocation event structure
    """
    event = {
        "operation": operation,
    }
    
    if body:
        event["body"] = body
    
    if query_params:
        event["queryParams"] = query_params
    
    return event


def get_mock_drs_client():
    """
    Get mock DRS client with pre-configured responses.
    
    Returns:
        MagicMock configured to respond like a real DRS client
    """
    from unittest.mock import MagicMock
    
    mock_client = MagicMock()
    
    # Configure describe_source_servers response
    mock_client.describe_source_servers.return_value = {
        "items": [
            get_mock_drs_source_server("s-1", "db-server-1"),
            get_mock_drs_source_server("s-2", "db-server-2"),
        ]
    }
    
    # Configure paginator for describe_source_servers
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [
        {
            "items": [
                get_mock_drs_source_server("s-1", "db-server-1"),
                get_mock_drs_source_server("s-2", "db-server-2"),
            ]
        }
    ]
    mock_client.get_paginator.return_value = mock_paginator
    
    # Configure describe_jobs response
    mock_client.describe_jobs.return_value = {
        "items": [
            get_mock_drs_job("job-1", "COMPLETED", "LAUNCH"),
        ]
    }
    
    # Configure describe_recovery_instances response
    mock_client.describe_recovery_instances.return_value = {
        "items": [
            get_mock_recovery_instance("i-recovery-1", "s-1"),
            get_mock_recovery_instance("i-recovery-2", "s-2"),
        ]
    }
    
    # Configure start_recovery response
    mock_client.start_recovery.return_value = {
        "job": get_mock_drs_job("job-new-1", "STARTED", "LAUNCH")
    }
    
    # Configure terminate_recovery_instances response
    mock_client.terminate_recovery_instances.return_value = {
        "job": get_mock_drs_job("job-term-1", "STARTED", "TERMINATE")
    }
    
    return mock_client

