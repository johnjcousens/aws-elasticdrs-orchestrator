"""
Property Test: Validation Error Handling

Feature: staging-accounts-management
Property 7: For any validation failure scenario (role assumption failure or
DRS not initialized), the validation result should have valid=false and
include a descriptive error message explaining the failure reason.

**Validates: Requirements 3.5, 3.6, 1.5**

This property test ensures that all validation failures are handled gracefully
with clear, actionable error messages.
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


@settings(max_examples=100)
@given(
    account_id=account_id_strategy,
    role_arn=role_arn_strategy,
    external_id=external_id_strategy,
    region=region_strategy,
    error_code=st.sampled_from([
        "AccessDenied",
        "InvalidClientTokenId",
        "InvalidParameterValue",
    ]),
)
def test_property_validation_error_handling_role_failures(
    account_id, role_arn, external_id, region, error_code
):
    """
    Property 7: Validation Error Handling (Role Assumption Failures)
    
    For any role assumption failure, the validation result must:
    1. Have valid=False
    2. Include a descriptive error message
    3. Explain the failure reason clearly
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
                    "Message": f"Mock {error_code} error message",
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
        
        # Property 7: valid must be False for any failure
        assert (
            body["valid"] is False
        ), "valid must be False for role assumption failure"
        
        # Property 7: error message must be present and descriptive
        assert "error" in body, "error field must be present for failures"
        assert isinstance(body["error"], str), "error must be a string"
        assert len(body["error"]) > 0, "error message must not be empty"
        
        # Error message should be descriptive and actionable
        error_lower = body["error"].lower()
        
        # Should mention the failure type
        assert any(
            keyword in error_lower
            for keyword in ["role", "assume", "access", "denied", "invalid"]
        ), "error should describe the failure type"
        
        # Should not expose internal implementation details
        assert (
            "traceback" not in error_lower
        ), "error should not contain traceback"
        assert (
            "exception" not in error_lower
        ), "error should not contain exception details"


@settings(max_examples=100)
@given(
    account_id=account_id_strategy,
    role_arn=role_arn_strategy,
    external_id=external_id_strategy,
    region=region_strategy,
)
def test_property_validation_error_handling_drs_uninitialized(
    account_id, role_arn, external_id, region
):
    """
    Property 7: Validation Error Handling (DRS Not Initialized)
    
    For DRS uninitialized errors, the validation result must:
    1. Have valid=False
    2. Include a descriptive error message
    3. Explain that DRS needs to be initialized
    4. Provide actionable guidance
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
                    "Message": "DRS is not initialized in this account",
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
        
        # Property 7: valid must be False for DRS uninitialized
        assert (
            body["valid"] is False
        ), "valid must be False for DRS uninitialized"
        
        # Property 7: error message must be present and descriptive
        assert "error" in body, "error field must be present for DRS failure"
        assert isinstance(body["error"], str), "error must be a string"
        assert len(body["error"]) > 0, "error message must not be empty"
        
        # Error message should explain DRS is not initialized
        error_lower = body["error"].lower()
        assert (
            "not initialized" in error_lower or "uninitialized" in error_lower
        ), "error should mention DRS is not initialized"
        
        # Should mention DRS
        assert "drs" in error_lower, "error should mention DRS"
        
        # Should provide actionable guidance
        assert (
            "initialize" in error_lower
        ), "error should suggest initializing DRS"


@settings(max_examples=50)
@given(
    account_id=account_id_strategy,
    role_arn=role_arn_strategy,
    external_id=external_id_strategy,
    region=region_strategy,
    drs_error_code=st.sampled_from([
        "ThrottlingException",
        "InternalServerException",
        "ServiceQuotaExceededException",
    ]),
)
def test_property_validation_error_handling_drs_other_errors(
    account_id, role_arn, external_id, region, drs_error_code
):
    """
    Property 7: Validation Error Handling (Other DRS Errors)
    
    For other DRS errors (throttling, internal errors, etc.), the validation
    result must:
    1. Have valid=False
    2. Include a descriptive error message
    3. Not expose sensitive internal details
    """
    query_params = {
        "accountId": account_id,
        "roleArn": role_arn,
        "externalId": external_id,
        "region": region,
    }
    
    # Mock successful role assumption but DRS error
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
        
        # Mock DRS client with error
        mock_drs = MagicMock()
        mock_paginator = MagicMock()
        mock_drs.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {
                "Error": {
                    "Code": drs_error_code,
                    "Message": f"Mock {drs_error_code} error",
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
        
        # Property 7: valid must be False for DRS errors
        assert body["valid"] is False, "valid must be False for DRS errors"
        
        # Property 7: error message must be present
        assert "error" in body, "error field must be present for DRS errors"
        assert isinstance(body["error"], str), "error must be a string"
        assert len(body["error"]) > 0, "error message must not be empty"


@settings(max_examples=50)
@given(
    account_id=st.one_of(
        st.just(""),  # Empty
        st.text(min_size=1, max_size=5),  # Too short
        st.text(min_size=13, max_size=20),  # Too long
        st.from_regex(r"[a-zA-Z]{12}", fullmatch=True),  # Non-numeric
    ),
    role_arn=role_arn_strategy,
    external_id=external_id_strategy,
    region=region_strategy,
)
def test_property_validation_error_handling_invalid_account_id(
    account_id, role_arn, external_id, region
):
    """
    Property 7: Validation Error Handling (Invalid Account ID)
    
    For invalid account ID format, the validation result must:
    1. Have valid=False
    2. Include a descriptive error message
    3. Explain the account ID format requirement
    """
    query_params = {
        "accountId": account_id,
        "roleArn": role_arn,
        "externalId": external_id,
        "region": region,
    }
    
    # Execute validation (no mocking needed - validation happens before AWS calls)
    result = handle_validate_staging_account(query_params)
    
    # Parse response
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    
    # Property 7: valid must be False for invalid input
    assert body["valid"] is False, "valid must be False for invalid account ID"
    
    # Property 7: error message must be present and descriptive
    assert "error" in body, "error field must be present for invalid input"
    assert isinstance(body["error"], str), "error must be a string"
    assert len(body["error"]) > 0, "error message must not be empty"
    
    # Error should explain the format requirement
    error_lower = body["error"].lower()
    assert (
        "account" in error_lower or "invalid" in error_lower
    ), "error should mention account ID issue"


@settings(max_examples=50)
@given(
    account_id=account_id_strategy,
    role_arn=role_arn_strategy,
    external_id=external_id_strategy,
    # Missing region - will be None
)
def test_property_validation_error_handling_missing_required_fields(
    account_id, role_arn, external_id
):
    """
    Property 7: Validation Error Handling (Missing Required Fields)
    
    For missing required fields, the validation result must:
    1. Have valid=False
    2. Include a descriptive error message
    3. Specify which field is missing
    """
    # Test with missing region
    query_params = {
        "accountId": account_id,
        "roleArn": role_arn,
        "externalId": external_id,
        # region is missing
    }
    
    # Execute validation
    result = handle_validate_staging_account(query_params)
    
    # Parse response
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    
    # Property 7: valid must be False for missing fields
    assert (
        body["valid"] is False
    ), "valid must be False for missing required field"
    
    # Property 7: error message must be present and descriptive
    assert (
        "error" in body
    ), "error field must be present for missing required field"
    assert isinstance(body["error"], str), "error must be a string"
    assert len(body["error"]) > 0, "error message must not be empty"
    
    # Error should specify which field is missing
    error_lower = body["error"].lower()
    assert (
        "missing" in error_lower or "required" in error_lower
    ), "error should mention missing field"
    assert "region" in error_lower, "error should specify region is missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
