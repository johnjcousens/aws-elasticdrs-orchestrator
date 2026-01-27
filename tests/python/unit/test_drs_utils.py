"""
Unit tests for drs_utils shared utilities.

Tests DRS response normalization and EC2 enrichment functions.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda"
    ),
)

from shared.drs_utils import (
    batch_describe_ec2_instances,
    build_drs_filter,
    enrich_server_data,
    extract_recovery_instance_details,
    normalize_drs_response,
)


class TestNormalizeDrsResponse:
    """Tests for normalize_drs_response function"""

    def test_normalize_basic_fields(self):
        """Test normalization of basic DRS fields"""
        drs_data = {
            "RecoveryInstanceID": "i-123",
            "SourceServerID": "s-456",
            "JobID": "job-789",
        }

        result = normalize_drs_response(drs_data)

        assert result["recoveryInstanceId"] == "i-123"
        assert result["sourceServerId"] == "s-456"
        assert result["jobId"] == "job-789"

    def test_normalize_lowercase_variants(self):
        """Test normalization handles AWS lowercase variants"""
        drs_data = {
            "sourceServerID": "s-456",  # AWS returns lowercase 's'
            "recoveryInstanceID": "i-123",  # AWS returns lowercase 'r'
        }

        result = normalize_drs_response(drs_data)

        assert result["sourceServerId"] == "s-456"
        assert result["recoveryInstanceId"] == "i-123"

    def test_normalize_ec2_fields(self):
        """Test normalization of EC2-related fields"""
        drs_data = {
            "InstanceType": "t3.medium",
            "PrivateIpAddress": "10.0.1.50",
            "PrivateDnsName": "ip-10-0-1-50.ec2.internal",
            "State": {"Name": "running"},
        }

        result = normalize_drs_response(drs_data)

        assert result["instanceType"] == "t3.medium"
        assert result["privateIpAddress"] == "10.0.1.50"
        assert result["privateDnsName"] == "ip-10-0-1-50.ec2.internal"
        assert result["state"]["name"] == "running"

    def test_normalize_nested_objects(self):
        """Test normalization handles nested objects recursively"""
        drs_data = {
            "SourceServerID": "s-123",
            "LifeCycle": {
                "LastLaunchResult": "SUCCEEDED",
                "LaunchStatus": "LAUNCHED",
            },
        }

        result = normalize_drs_response(drs_data)

        assert result["sourceServerId"] == "s-123"
        assert result["lifeCycle"]["lastLaunchResult"] == "SUCCEEDED"
        assert result["lifeCycle"]["launchStatus"] == "LAUNCHED"

    def test_normalize_list_of_objects(self):
        """Test normalization handles lists of objects"""
        drs_data = [
            {"SourceServerID": "s-123", "LaunchStatus": "LAUNCHED"},
            {"SourceServerID": "s-456", "LaunchStatus": "PENDING"},
        ]

        result = normalize_drs_response(drs_data)

        assert len(result) == 2
        assert result[0]["sourceServerId"] == "s-123"
        assert result[0]["launchStatus"] == "LAUNCHED"
        assert result[1]["sourceServerId"] == "s-456"

    def test_normalize_non_recursive(self):
        """Test normalization with recursive=False"""
        drs_data = {
            "SourceServerID": "s-123",
            "LifeCycle": {"LaunchStatus": "LAUNCHED"},
        }

        result = normalize_drs_response(drs_data, recursive=False)

        assert result["sourceServerId"] == "s-123"
        # Nested object should not be normalized
        assert result["lifeCycle"]["LaunchStatus"] == "LAUNCHED"


class TestBatchDescribeEc2Instances:
    """Tests for batch_describe_ec2_instances function"""

    def test_batch_describe_empty_list(self):
        """Test batch describe with empty instance list"""
        ec2_client = MagicMock()

        result = batch_describe_ec2_instances([], ec2_client)

        assert result == {}
        ec2_client.describe_instances.assert_not_called()

    def test_batch_describe_success(self):
        """Test successful batch EC2 instance query"""
        ec2_client = MagicMock()
        ec2_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-123",
                            "InstanceType": "t3.medium",
                            "PrivateIpAddress": "10.0.1.50",
                            "PrivateDnsName": "ip-10-0-1-50.ec2.internal",
                            "State": {"Name": "running"},
                            "LaunchTime": "2024-01-25T10:00:00Z",
                        }
                    ]
                }
            ]
        }

        result = batch_describe_ec2_instances(["i-123"], ec2_client)

        assert "i-123" in result
        assert result["i-123"]["instanceType"] == "t3.medium"
        assert result["i-123"]["privateIpAddress"] == "10.0.1.50"
        assert result["i-123"]["privateDnsName"] == "ip-10-0-1-50.ec2.internal"
        assert result["i-123"]["state"]["Name"] == "running"

    def test_batch_describe_multiple_instances(self):
        """Test batch query with multiple instances"""
        ec2_client = MagicMock()
        ec2_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-123",
                            "InstanceType": "t3.medium",
                            "PrivateIpAddress": "10.0.1.50",
                            "PrivateDnsName": "ip-10-0-1-50.ec2.internal",
                            "State": {"Name": "running"},
                        },
                        {
                            "InstanceId": "i-456",
                            "InstanceType": "t3.large",
                            "PrivateIpAddress": "10.0.1.51",
                            "PrivateDnsName": "ip-10-0-1-51.ec2.internal",
                            "State": {"Name": "running"},
                        },
                    ]
                }
            ]
        }

        result = batch_describe_ec2_instances(["i-123", "i-456"], ec2_client)

        assert len(result) == 2
        assert "i-123" in result
        assert "i-456" in result
        assert result["i-123"]["instanceType"] == "t3.medium"
        assert result["i-456"]["instanceType"] == "t3.large"

    def test_batch_describe_instance_not_found(self):
        """Test batch query handles missing instances gracefully"""
        ec2_client = MagicMock()
        error_response = {"Error": {"Code": "InvalidInstanceID.NotFound"}}
        ec2_client.describe_instances.side_effect = ClientError(
            error_response, "DescribeInstances"
        )

        result = batch_describe_ec2_instances(["i-nonexistent"], ec2_client)

        # Should return empty dict, not raise exception
        assert result == {}

    def test_batch_describe_other_error_raises(self):
        """Test batch query raises non-NotFound errors"""
        ec2_client = MagicMock()
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        ec2_client.describe_instances.side_effect = ClientError(
            error_response, "DescribeInstances"
        )

        with pytest.raises(ClientError):
            batch_describe_ec2_instances(["i-123"], ec2_client)


class TestEnrichServerData:
    """Tests for enrich_server_data function"""

    def test_enrich_with_ec2_data(self):
        """Test enrichment adds DRS source server and EC2 recovery instance data"""
        participating_servers = [
            {
                "sourceServerID": "s-123",
                "recoveryInstanceID": "i-recovery-123",
                "LaunchStatus": "LAUNCHED",
                "LaunchTime": 1706180400,
            }
        ]

        drs_client = MagicMock()
        drs_client.describe_source_servers.return_value = {
            "items": [
                {
                    "sourceServerID": "s-123",
                    "tags": {"Name": "TestServer01"},
                    "sourceProperties": {
                        "networkInterfaces": [
                            {
                                "isPrimary": True,
                                "ips": ["10.0.1.100"],
                            }
                        ],
                        "identificationHints": {
                            "awsInstanceID": "i-source-123"
                        },
                    },
                }
            ]
        }
        
        ec2_client = MagicMock()
        ec2_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-recovery-123",
                            "InstanceType": "t3.medium",
                            "PrivateIpAddress": "10.0.2.50",
                            "PrivateDnsName": "ip-10-0-2-50.ec2.internal",
                            "State": {"Name": "running"},
                        }
                    ]
                }
            ]
        }

        result = enrich_server_data(participating_servers, drs_client, ec2_client)

        assert len(result) == 1
        server = result[0]
        assert server["sourceServerId"] == "s-123"
        assert server["recoveryInstanceId"] == "i-recovery-123"
        assert server["launchStatus"] == "LAUNCHED"
        # DRS source server enrichment
        assert server["serverName"] == "TestServer01"
        assert server["ipAddress"] == "10.0.1.100"
        assert server["sourceInstanceId"] == "i-source-123"
        # EC2 recovery instance enrichment
        assert server["instanceId"] == "i-recovery-123"
        assert server["privateIp"] == "10.0.2.50"
        assert server["hostname"] == "ip-10-0-2-50.ec2.internal"
        assert server["instanceType"] == "t3.medium"
        assert server["instanceState"] == "running"

    def test_enrich_without_ec2_data(self):
        """Test enrichment handles servers without recovery instances"""
        participating_servers = [
            {
                "sourceServerID": "s-123",
                "LaunchStatus": "PENDING",
            }
        ]

        drs_client = MagicMock()
        drs_client.describe_source_servers.return_value = {
            "items": [
                {
                    "sourceServerID": "s-123",
                    "tags": {"Name": "TestServer01"},
                    "sourceProperties": {
                        "networkInterfaces": [
                            {
                                "isPrimary": True,
                                "ips": ["10.0.1.100"],
                            }
                        ],
                        "identificationHints": {
                            "awsInstanceID": "i-source-123"
                        },
                    },
                }
            ]
        }
        ec2_client = MagicMock()

        result = enrich_server_data(participating_servers, drs_client, ec2_client)

        assert len(result) == 1
        server = result[0]
        assert server["sourceServerId"] == "s-123"
        assert server["launchStatus"] == "PENDING"
        # DRS source server data should be added
        assert server["serverName"] == "TestServer01"
        assert server["ipAddress"] == "10.0.1.100"
        # No recovery instance data
        assert "instanceId" not in server
        assert "privateIp" not in server

    def test_enrich_multiple_servers(self):
        """Test enrichment handles multiple servers"""
        participating_servers = [
            {
                "sourceServerID": "s-123",
                "recoveryInstanceID": "i-123",
                "LaunchStatus": "LAUNCHED",
            },
            {
                "sourceServerID": "s-456",
                "recoveryInstanceID": "i-456",
                "LaunchStatus": "LAUNCHED",
            },
        ]

        drs_client = MagicMock()
        ec2_client = MagicMock()
        ec2_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-123",
                            "InstanceType": "t3.medium",
                            "PrivateIpAddress": "10.0.1.50",
                            "PrivateDnsName": "ip-10-0-1-50.ec2.internal",
                            "State": {"Name": "running"},
                        },
                        {
                            "InstanceId": "i-456",
                            "InstanceType": "t3.large",
                            "PrivateIpAddress": "10.0.1.51",
                            "PrivateDnsName": "ip-10-0-1-51.ec2.internal",
                            "State": {"Name": "running"},
                        },
                    ]
                }
            ]
        }

        result = enrich_server_data(participating_servers, drs_client, ec2_client)

        assert len(result) == 2
        assert result[0]["instanceType"] == "t3.medium"
        assert result[1]["instanceType"] == "t3.large"

    def test_enrich_partial_ec2_data(self):
        """Test enrichment handles partial EC2 availability"""
        participating_servers = [
            {
                "sourceServerID": "s-123",
                "recoveryInstanceID": "i-123",
                "LaunchStatus": "LAUNCHED",
            },
            {
                "sourceServerID": "s-456",
                "recoveryInstanceID": "i-456",
                "LaunchStatus": "PENDING",
            },
        ]

        drs_client = MagicMock()
        ec2_client = MagicMock()
        # Only i-123 is available in EC2
        ec2_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-123",
                            "InstanceType": "t3.medium",
                            "PrivateIpAddress": "10.0.1.50",
                            "PrivateDnsName": "ip-10-0-1-50.ec2.internal",
                            "State": {"Name": "running"},
                        }
                    ]
                }
            ]
        }

        result = enrich_server_data(participating_servers, drs_client, ec2_client)

        assert len(result) == 2
        # First server has EC2 data
        assert result[0]["instanceType"] == "t3.medium"
        # Second server doesn't have EC2 data
        assert "instanceType" not in result[1]


class TestExtractRecoveryInstanceDetails:
    """Tests for extract_recovery_instance_details function"""

    def test_extract_basic_details(self):
        """Test extraction of basic recovery instance details"""
        drs_instance = {
            "InstanceID": "i-123",
            "RecoveryInstanceID": "ri-456",
            "SourceServerID": "s-789",
            "LaunchTime": 1706180400,
            "InstanceType": "t3.medium",
        }

        result = extract_recovery_instance_details(drs_instance)

        assert result["instanceId"] == "i-123"
        assert result["recoveryInstanceId"] == "ri-456"
        assert result["sourceServerId"] == "s-789"
        assert result["launchTime"] == 1706180400
        assert result["instanceType"] == "t3.medium"

    def test_extract_with_missing_fields(self):
        """Test extraction handles missing fields with defaults"""
        drs_instance = {
            "SourceServerID": "s-789",
        }

        result = extract_recovery_instance_details(drs_instance)

        assert result["sourceServerId"] == "s-789"
        assert result["instanceId"] == ""
        assert result["recoveryInstanceId"] == ""
        assert result["instanceType"] == ""


class TestBuildDrsFilter:
    """Tests for build_drs_filter function"""

    def test_build_filter_source_servers(self):
        """Test filter with source server IDs"""
        result = build_drs_filter(source_server_ids=["s-123", "s-456"])

        assert "sourceServerIDs" in result
        assert result["sourceServerIDs"] == ["s-123", "s-456"]

    def test_build_filter_recovery_instances(self):
        """Test filter with recovery instance IDs"""
        result = build_drs_filter(recovery_instance_ids=["ri-123", "ri-456"])

        assert "recoveryInstanceIDs" in result
        assert result["recoveryInstanceIDs"] == ["ri-123", "ri-456"]

    def test_build_filter_both(self):
        """Test filter with both source servers and recovery instances"""
        result = build_drs_filter(
            source_server_ids=["s-123"],
            recovery_instance_ids=["ri-456"],
        )

        assert "sourceServerIDs" in result
        assert "recoveryInstanceIDs" in result
        assert result["sourceServerIDs"] == ["s-123"]
        assert result["recoveryInstanceIDs"] == ["ri-456"]

    def test_build_filter_empty(self):
        """Test filter with no parameters"""
        result = build_drs_filter()

        assert result == {}
