"""
Property Test: Validation Result Completeness

Feature: staging-accounts-management
Property 6: For any staging account validation attempt, the validation result
should include all required fields: role accessibility status (boolean), DRS
initialization status (boolean), current server count (number), replicating
server count (number), and projected combined capacity (number).

**Validates: Requirements 3.4, 1.4**

This property test ensures that validation results are always complete and
well-formed, regardless of whether validation succeeds or fails.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st
from botocore.exceptions import ClientError

# Set environment variables before importing
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts-table"
os.environ["PROTECTION_GROUPS_TABLE"] = "test-protection-groups-table"
os.environ["RECOVERY_PLANS_TABLE"] = "test-recovery-plans-table"

# Clear any existing index module to avoid conflicts
if "index" in sys.modules:
    del sys.modules["index"]

# Add query-handler to path - query-handler FIRST
query_handler_dir = (
    Path(__file__).parent.parent.parent / "lambda" / "query-handler"
)
sys.path.insert(0, str(query_handler_dir))

from index import handle_validate_staging_account


# Strategy for generating valid AWS account IDs (12 digits)
account_id_strategy = st.from_regex(r"\d{12}", fullmatch=True)

# Strategy for generating valid IAM role ARNs
role_arn_strategy = st.from_regex(
    r"arn:aws:iam::\d{12}:role/[\w+=,.@-]+", fullmatch=True
)

# Strategy for generating external IDs
external_id_strategy = st.text(min_size=1, max_size=100)

# Strategy for generating AWS regions
region_strategy = st.sampled_from([
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "eu-west-1",
    "eu-central-1",
    "ap-southeast-1",
])

# Strategy for server counts
server_count_strategy = st.integers(min_value=0, max_value=300)


@settings(max_examples=100)
@given(
    account_id=account_id_strategy,
    role_arn=role_arn_strategy,
    external_id=external_id_strategy,
    region=region_strategy,
    total_servers=server_count_strategy,
    replicating_servers=server_count_strategy,
)
def test_property_validation_result_completeness_success(
    account_id, role_arn, external_id, region, total_servers, replicating_servers
):
    """
    Property 6: Validation Result Completeness (Success Case)
    
    For any successful validation attempt, the result must include all
    required fields with correct types.
    
    Required fields for successful validation:
    - valid: True
    - roleAccessible: True
    - drsInitialized: True
    - currentServers: int >= 0
    - replicatingServers: int >= 0
    - totalAfter: int >= 0
    """
    # Ensure replicating_servers <= total_servers
    if replicating_servers > total_servers:
        replicating_servers = total_servers
    
    query_params = {
        "accountId": account_id,
        "roleArn": role_arn,
        "externalId": external_id,
        "region": region,
    }
    
    # Mock successful role assumption and DRS query
    with patch("index.boto3.client") as mock_boto3_client:
        # Mock STS client
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "token123",
            }
        }
        
        # Mock DRS client
        mock_drs = MagicMock()
        
        # Mock paginator for describe_source_servers
        mock_paginator = MagicMock()
        mock_drs.get_paginator.return_value = mock_paginator
        
        # Generate mock servers
        mock_servers = []
        for i in range(total_servers):
            replication_state = (
                "CONTINUOUS" if i < replicating_servers else "DISCONNECTED"
            )
            mock_servers.append({
                "sourceServerID": f"s-{i:08d}",
                "dataReplicationInfo": {
                    "dataReplicationState": replication_state
                },
            })
        
        mock_paginator.paginate.return_value = [{"items": mock_servers}]
        
        # Configure boto3.client to return appropriate mocks
        def client_side_effect(service, **kwargs):
            if service == "sts":
                return mock_sts
            elif service == "drs":
                return mock_drs
            return MagicMock()
        
        mock_boto3_client.side_effect = client_side_effect
        
        # Execute validation
        result = handle_validate_staging_account(query_params)
        
        # Parse response
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        
        # Verify all required fields are present
        assert "valid" in body, "Missing 'valid' field"
        assert "roleAccessible" in body, "Missing 'roleAccessible' field"
        assert "drsInitialized" in body, "Missing 'drsInitialized' field"
        assert "currentServers" in body, "Missing 'currentServers' field"
        assert (
            "replicatingServers" in body
        ), "Missing 'replicatingServers' field"
        assert "totalAfter" in body, "Missing 'totalAfter' field"
        
        # Verify field types and values
        assert body["valid"] is True, "valid should be True for success"
        assert (
            body["roleAccessible"] is True
        ), "roleAccessible should be True for success"
        assert (
            body["drsInitialized"] is True
        ), "drsInitialized should be True for success"
        
        assert isinstance(
            body["currentServers"], int
        ), "currentServers must be int"
        assert body["currentServers"] >= 0, "currentServers must be >= 0"
        assert body["currentServers"] == total_servers
        
        assert isinstance(
            body["replicatingServers"], int
        ), "replicatingServers must be int"
        assert (
            body["replicatingServers"] >= 0
        ), "replicatingServers must be >= 0"
        assert body["replicatingServers"] == replicating_servers
        
        assert isinstance(body["totalAfter"], int), "totalAfter must be int"
        assert body["totalAfter"] >= 0, "totalAfter must be >= 0"
        
        # Error field should not be present on success
        assert "error" not in body, "error field should not be present on success"


@settings(max_examples=100)
@given(
    account_id=account_id_strategy,
    role_arn=role_arn_strategy,
    external_id=external_id_strategy,
    region=region_strategy,
    error_code=st.sampled_from(["AccessDenied", "InvalidClientTokenId"]),
)
def test_property_validation_result_completeness_role_failure(
    account_id, role_arn, external_id, region, error_code
):
    """
    Property 6: Validation Result Completeness (Role Assumption Failure)
    
    For any validation attempt that fails at role assumption, the result
    must include:
    - valid: False
    - roleAccessible: False
    - error: string with descriptive message
    """
    query_params = {
        "accountId": account_id,
        "roleArn": role_arn,
        "externalId": external_id,
        "region": region,
    }
    
    # Mock failed role assumption
    with patch("index.boto3.client") as mock_boto3_client:
        mock_sts = MagicMock()
        mock_sts.assume_role.side_effect = ClientError(
            {
                "Error": {
                    "Code": error_code,
                    "Message": f"Mock {error_code} error",
                }
            },
            "AssumeRole",
        )
        
        mock_boto3_client.return_value = mock_sts
        
        # Execute validation
        result = handle_validate_staging_account(query_params)
        
        # Parse response
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        
        # Verify required fields for role failure
        assert "valid" in body, "Missing 'valid' field"
        assert "roleAccessible" in body, "Missing 'roleAccessible' field"
        assert "error" in body, "Missing 'error' field"
        
        # Verify field values
        assert body["valid"] is False, "valid should be False for role failure"
        assert (
            body["roleAccessible"] is False
        ), "roleAccessible should be False for role failure"
        
        assert isinstance(body["error"], str), "error must be string"
        assert len(body["error"]) > 0, "error message must not be empty"


@settings(max_examples=100)
@given(
    account_id=account_id_strategy,
    role_arn=role_arn_strategy,
    external_id=external_id_strategy,
    region=region_strategy,
)
def test_property_validation_result_completeness_drs_uninitialized(
    account_id, role_arn, external_id, region
):
    """
    Property 6: Validation Result Completeness (DRS Uninitialized)
    
    For any validation attempt where DRS is not initialized, the result
    must include:
    - valid: False
    - roleAccessible: True
    - drsInitialized: False
    - error: string with descriptive message
    """
    query_params = {
        "accountId": account_id,
        "roleArn": role_arn,
        "externalId": external_id,
        "region": region,
    }
    
    # Mock successful role assumption but DRS uninitialized
    with patch("index.boto3.client") as mock_boto3_client:
        # Mock STS client
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "token123",
            }
        }
        
        # Mock DRS client with UninitializedAccountException
        mock_drs = MagicMock()
        mock_paginator = MagicMock()
        mock_drs.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {
                "Error": {
                    "Code": "UninitializedAccountException",
                    "Message": "DRS is not initialized",
                }
            },
            "DescribeSourceServers",
        )
        
        # Configure boto3.client to return appropriate mocks
        def client_side_effect(service, **kwargs):
            if service == "sts":
                return mock_sts
            elif service == "drs":
                return mock_drs
            return MagicMock()
        
        mock_boto3_client.side_effect = client_side_effect
        
        # Execute validation
        result = handle_validate_staging_account(query_params)
        
        # Parse response
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        
        # Verify required fields for DRS uninitialized
        assert "valid" in body, "Missing 'valid' field"
        assert "roleAccessible" in body, "Missing 'roleAccessible' field"
        assert "drsInitialized" in body, "Missing 'drsInitialized' field"
        assert "error" in body, "Missing 'error' field"
        
        # Verify field values
        assert (
            body["valid"] is False
        ), "valid should be False for DRS uninitialized"
        assert (
            body["roleAccessible"] is True
        ), "roleAccessible should be True (role worked)"
        assert (
            body["drsInitialized"] is False
        ), "drsInitialized should be False"
        
        assert isinstance(body["error"], str), "error must be string"
        assert len(body["error"]) > 0, "error message must not be empty"
        assert (
            "not initialized" in body["error"].lower()
        ), "error should mention DRS not initialized"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
