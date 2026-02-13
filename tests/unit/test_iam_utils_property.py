"""
Property-Based Tests for IAM Authorization Utilities

Tests IAM authorization logic using property-based testing with Hypothesis.
Verifies that authorization decisions are consistent, correct, and handle
edge cases properly across a wide range of inputs.

## Test Strategy

1. **Authorization Correctness**: Verify that valid principals are always authorized
   and invalid principals are always denied
2. **Principal Format Validation**: Test that various ARN formats are handled correctly
3. **Pattern Matching**: Verify that authorization patterns work consistently
4. **Edge Cases**: Test boundary conditions, malformed inputs, and unusual formats

## Property-Based Testing Benefits

- Discovers edge cases that manual tests might miss
- Verifies consistency across many input variations
- Tests invariants that should always hold true
- Provides confidence in authorization logic correctness
"""

import sys
import os

# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from hypothesis import given, strategies as st, assume, settings
from unittest.mock import Mock
import re

from shared.iam_utils import (
    extract_iam_principal,
    validate_iam_authorization,
    validate_direct_invocation_event,
)


# Strategy for generating AWS account IDs (12 digits)
aws_account_id = st.text(alphabet="0123456789", min_size=12, max_size=12)

# Strategy for generating role names
role_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", min_size=1, max_size=64
).filter(
    lambda x: x[0].isalpha()
)  # Must start with letter

# Strategy for generating user names
user_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_+=,.@", min_size=1, max_size=64
).filter(
    lambda x: x[0].isalnum()
)  # Must start with alphanumeric

# Strategy for generating session names
session_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", min_size=1, max_size=64
)


@given(account_id=aws_account_id, role=role_name)
@settings(max_examples=50)
def test_orchestration_role_always_authorized(account_id, role):
    """
    Property: Any ARN containing 'OrchestrationRole' should be authorized.

    This tests that the primary automation role pattern is consistently
    recognized regardless of account ID or exact role name variations.
    """
    # Construct IAM role ARN with OrchestrationRole
    principal = f"arn:aws:iam::{account_id}:role/{role}OrchestrationRole"

    # Should always be authorized
    assert validate_iam_authorization(principal) is True


@given(account_id=aws_account_id, role=role_name, session=session_name)
@settings(max_examples=50)
def test_assumed_orchestration_role_always_authorized(account_id, role, session):
    """
    Property: Any assumed role ARN containing 'OrchestrationRole' should be authorized.

    This tests that Step Functions and other services assuming the OrchestrationRole
    are consistently authorized.
    """
    # Construct assumed role ARN with OrchestrationRole
    principal = f"arn:aws:sts::{account_id}:assumed-role/{role}OrchestrationRole/{session}"

    # Should always be authorized
    assert validate_iam_authorization(principal) is True


@given(account_id=aws_account_id, role=role_name)
@settings(max_examples=50)
def test_step_functions_role_always_authorized(account_id, role):
    """
    Property: Any ARN containing 'StepFunctions' should be authorized.

    This tests that Step Functions execution roles are consistently recognized.
    """
    # Construct IAM role ARN with StepFunctions
    principal = f"arn:aws:iam::{account_id}:role/{role}StepFunctions"

    # Should always be authorized
    assert validate_iam_authorization(principal) is True


@given(account_id=aws_account_id, role=role_name)
@settings(max_examples=50)
def test_lambda_role_always_authorized(account_id, role):
    """
    Property: Any ARN containing 'Lambda' should be authorized.

    This tests that Lambda execution roles are consistently recognized
    for Lambda-to-Lambda invocations.
    """
    # Construct IAM role ARN with Lambda
    principal = f"arn:aws:iam::{account_id}:role/{role}Lambda"

    # Should always be authorized
    assert validate_iam_authorization(principal) is True


@given(account_id=aws_account_id, user=user_name)
@settings(max_examples=50)
def test_admin_user_always_authorized(account_id, user):
    """
    Property: Any user ARN starting with 'admin' should be authorized.

    This tests that admin users are consistently recognized for
    testing and manual operations.
    """
    # Construct IAM user ARN with admin prefix
    principal = f"arn:aws:iam::{account_id}:user/admin{user}"

    # Should always be authorized
    assert validate_iam_authorization(principal) is True


@given(account_id=aws_account_id, role=role_name)
@settings(max_examples=50)
def test_random_role_without_keywords_denied(account_id, role):
    """
    Property: Random roles without authorization keywords should be denied.

    This tests that roles not matching any authorization pattern are
    consistently denied access.
    """
    # Filter out roles that would match authorization patterns
    assume(not any(keyword in role.lower() for keyword in ["orchestration", "stepfunctions", "lambda", "admin"]))

    # Construct IAM role ARN without authorization keywords
    principal = f"arn:aws:iam::{account_id}:role/{role}"

    # Should be denied
    assert validate_iam_authorization(principal) is False


@given(account_id=aws_account_id, user=user_name)
@settings(max_examples=50)
def test_random_user_without_admin_denied(account_id, user):
    """
    Property: Random users without 'admin' prefix should be denied.

    This tests that non-admin users are consistently denied access.
    """
    # Filter out users that start with admin
    assume(not user.lower().startswith("admin"))

    # Construct IAM user ARN without admin prefix
    principal = f"arn:aws:iam::{account_id}:user/{user}"

    # Should be denied
    assert validate_iam_authorization(principal) is False


@given(text=st.text(min_size=0, max_size=100))
@settings(max_examples=50)
def test_malformed_arn_always_denied(text):
    """
    Property: Malformed ARNs should always be denied.

    This tests that invalid ARN formats are consistently rejected
    regardless of content.
    """
    # Filter out text that might accidentally form valid ARN
    assume(not text.startswith("arn:aws:"))

    # Should be denied
    assert validate_iam_authorization(text) is False


@given(account_id=aws_account_id)
@settings(max_examples=50)
def test_empty_and_unknown_principals_denied(account_id):
    """
    Property: Empty and unknown principals should always be denied.

    This tests that missing or unknown principal information is
    consistently rejected.
    """
    # Test empty string
    assert validate_iam_authorization("") is False

    # Test "unknown" sentinel value
    assert validate_iam_authorization("unknown") is False

    # Test None (converted to string)
    assert validate_iam_authorization(str(None)) is False


@given(
    account_id=aws_account_id,
    role=role_name,
    region=st.sampled_from(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
)
@settings(max_examples=50)
def test_lambda_function_arn_always_authorized(account_id, role, region):
    """
    Property: Lambda function ARNs should always be authorized.

    This tests that Lambda-to-Lambda invocations are consistently
    authorized regardless of region or function name.
    """
    # Construct Lambda function ARN
    principal = f"arn:aws:lambda:{region}:{account_id}:function:{role}"

    # Should always be authorized
    assert validate_iam_authorization(principal) is True


@given(
    account_id=aws_account_id,
    service=st.sampled_from(["states.amazonaws.com", "events.amazonaws.com", "lambda.amazonaws.com"]),
)
@settings(max_examples=50)
def test_service_role_always_authorized(account_id, service):
    """
    Property: AWS service roles should always be authorized.

    This tests that service-linked roles are consistently recognized.
    """
    # Construct service role ARN
    principal = f"arn:aws:iam::{account_id}:role/aws-service-role/{service}/AWSServiceRole"

    # Should always be authorized
    assert validate_iam_authorization(principal) is True


@given(arn_type=st.sampled_from(["iam", "sts"]), account_id=aws_account_id, role=role_name)
@settings(max_examples=50)
def test_authorization_case_insensitive(arn_type, account_id, role):
    """
    Property: Authorization should be case-insensitive for role names.

    This tests that OrchestrationRole, orchestrationrole, ORCHESTRATIONROLE
    are all recognized consistently.
    """
    # For sts, use assumed-role format
    if arn_type == "sts":
        cases = [
            f"arn:aws:{arn_type}::{account_id}:assumed-role/{role}OrchestrationRole/session",
            f"arn:aws:{arn_type}::{account_id}:assumed-role/{role}orchestrationrole/session",
            f"arn:aws:{arn_type}::{account_id}:assumed-role/{role}ORCHESTRATIONROLE/session",
            f"arn:aws:{arn_type}::{account_id}:assumed-role/{role}OrChEsTrAtIoNrOlE/session",
        ]
    else:
        cases = [
            f"arn:aws:{arn_type}::{account_id}:role/{role}OrchestrationRole",
            f"arn:aws:{arn_type}::{account_id}:role/{role}orchestrationrole",
            f"arn:aws:{arn_type}::{account_id}:role/{role}ORCHESTRATIONROLE",
            f"arn:aws:{arn_type}::{account_id}:role/{role}OrChEsTrAtIoNrOlE",
        ]

    # All should have same authorization result (all should be True)
    results = [validate_iam_authorization(principal) for principal in cases]
    assert all(results), f"Case-insensitive authorization failed for role: {role}, results: {results}"


@given(account_id=aws_account_id, role=role_name)
@settings(max_examples=50)
def test_extract_principal_from_context(account_id, role):
    """
    Property: extract_iam_principal should always return a string.

    This tests that principal extraction handles various context
    formats consistently.
    """
    # Create mock context with invoked_function_arn
    context = Mock()
    context.invoked_function_arn = f"arn:aws:lambda:us-east-1:{account_id}:function:{role}"

    # Mock identity to return None (no user_arn)
    context.identity = None

    # Extract principal
    principal = extract_iam_principal(context)

    # Should return a string
    assert isinstance(principal, str)
    assert len(principal) > 0

    # Should return the invoked_function_arn
    assert principal == context.invoked_function_arn


@given(
    operation=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    params=st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(st.text(), st.integers(), st.booleans(), st.none()),
        max_size=10,
    ),
)
@settings(max_examples=50)
def test_valid_direct_invocation_event(operation, params):
    """
    Property: Events with 'operation' field should be valid direct invocations.

    This tests that event validation correctly identifies direct invocation
    events regardless of additional parameters.
    """
    # Create event with operation
    event = {"operation": operation, "queryParams": params}

    # Should be valid
    assert validate_direct_invocation_event(event) is True


@given(
    params=st.dictionaries(
        keys=st.text(min_size=1, max_size=50).filter(lambda x: x != "operation"),
        values=st.one_of(st.text(), st.integers(), st.booleans()),
        max_size=10,
    )
)
@settings(max_examples=50)
def test_invalid_direct_invocation_event_without_operation(params):
    """
    Property: Events without 'operation' field should be invalid.

    This tests that event validation correctly rejects events that
    don't have the required operation field.
    """
    # Create event without operation
    event = params

    # Should be invalid
    assert validate_direct_invocation_event(event) is False


@given(operation=st.one_of(st.none(), st.just(""), st.just("   ")))
@settings(max_examples=30)
def test_invalid_direct_invocation_event_with_empty_operation(operation):
    """
    Property: Events with empty/null operation should be invalid.

    This tests that event validation rejects events with missing
    or empty operation values.
    """
    # Create event with empty operation
    event = {"operation": operation}

    # Should be invalid
    assert validate_direct_invocation_event(event) is False


@given(account_id=aws_account_id, role1=role_name, role2=role_name)
@settings(max_examples=50)
def test_authorization_deterministic(account_id, role1, role2):
    """
    Property: Authorization should be deterministic for same principal.

    This tests that calling validate_iam_authorization multiple times
    with the same principal always returns the same result.
    """
    # Create two identical principals
    principal1 = f"arn:aws:iam::{account_id}:role/{role1}OrchestrationRole"
    principal2 = f"arn:aws:iam::{account_id}:role/{role1}OrchestrationRole"

    # Should return same result
    result1 = validate_iam_authorization(principal1)
    result2 = validate_iam_authorization(principal2)
    assert result1 == result2

    # Different principals may have different results
    principal3 = f"arn:aws:iam::{account_id}:role/{role2}"
    result3 = validate_iam_authorization(principal3)
    # No assertion - just testing determinism


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
