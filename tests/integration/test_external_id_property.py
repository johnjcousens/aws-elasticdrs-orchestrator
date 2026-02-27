"""
Property-based tests for cross-account ExternalId validation.

Property 18: Cross-Account ExternalId Validation

For any STS AssumeRole operation and any ExternalId value, when a Lambda function
attempts to assume a cross-account role, the operation should succeed if the
ExternalId matches {ProjectName}-{Environment}, and the operation should fail
with AccessDenied if the ExternalId does not match.

**Validates: Requirements 10.2, 10.3, 10.4**

Test Strategy:
- Generate various ExternalId values (correct, incorrect, empty, malformed)
- Test AssumeRole with each ExternalId value
- Verify success only when ExternalId matches expected format
- Verify AccessDenied for all other cases
"""

import boto3
import pytest
from botocore.exceptions import ClientError, ParamValidationError
from hypothesis import given, settings, strategies as st


@pytest.fixture(scope="module")
def qa_environment():
    """QA environment configuration."""
    return {
        "project_name": "aws-drs-orchestration",
        "environment": "qa",
        "region": "us-east-2",
        "target_accounts_table": "aws-drs-orchestration-target-accounts-qa",
        "expected_external_id": "aws-drs-orchestration-qa",
    }


@pytest.fixture(scope="module")
def dynamodb_client(qa_environment):
    """DynamoDB client for QA region."""
    return boto3.client("dynamodb", region_name=qa_environment["region"])


@pytest.fixture(scope="module")
def sts_client(qa_environment):
    """STS client for QA region."""
    return boto3.client("sts", region_name=qa_environment["region"])


@pytest.fixture(scope="module")
def test_account(dynamodb_client, qa_environment):
    """
    Get first target account with roleArn and externalId configured.

    Returns dict with accountId, accountName, roleArn, externalId.
    """
    table_name = qa_environment["target_accounts_table"]

    try:
        response = dynamodb_client.scan(TableName=table_name, Limit=10)
        items = response.get("Items", [])

        # Find first account with roleArn and externalId
        for item in items:
            account = {
                "accountId": item.get("accountId", {}).get("S", ""),
                "accountName": item.get("accountName", {}).get("S", ""),
                "roleArn": item.get("roleArn", {}).get("S", ""),
                "externalId": item.get("externalId", {}).get("S", ""),
            }
            if account["roleArn"] and account["externalId"]:
                return account

        pytest.skip("No target accounts with roleArn and externalId configured")

    except ClientError as e:
        pytest.fail(f"Failed to scan target accounts table: {e}")


# Strategy: Generate various ExternalId values
external_id_strategy = st.one_of(
    # Correct format
    st.just("aws-drs-orchestration-qa"),
    # Incorrect formats
    st.text(min_size=1, max_size=50).filter(lambda x: x != "aws-drs-orchestration-qa"),
    # Empty string
    st.just(""),
    # Common variations
    st.just("aws-drs-orchestration-test"),  # Wrong environment
    st.just("aws-drs-orchestration"),  # Missing environment
    st.just("orchestration-qa"),  # Missing project prefix
    st.just("AWS-DRS-ORCHESTRATION-QA"),  # Wrong case
    st.just("aws-drs-orchestration-qa-extra"),  # Extra suffix
    # Special characters
    st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "P")), min_size=1, max_size=50),
)


@given(external_id=external_id_strategy)
@settings(max_examples=20, deadline=10000)  # 10 second timeout per example
def test_property_external_id_validation(external_id, test_account, sts_client, qa_environment):
    """
    Property 18: Cross-Account ExternalId Validation

    For any ExternalId value, AssumeRole should succeed only when ExternalId
    matches the expected format {ProjectName}-{Environment}.

    **Validates: Requirements 10.2, 10.3, 10.4**
    """
    role_arn = test_account["roleArn"]
    expected_external_id = qa_environment["expected_external_id"]

    print(f"\nTesting ExternalId: '{external_id}'")
    print(f"  Expected: '{expected_external_id}'")
    print(f"  Match: {external_id == expected_external_id}")

    try:
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"test-property-{hash(external_id) % 10000}",
            ExternalId=external_id,
        )

        # If AssumeRole succeeded, verify it was with correct ExternalId
        assert external_id == expected_external_id, (
            f"AssumeRole succeeded with incorrect ExternalId: '{external_id}'. "
            f"Expected only '{expected_external_id}' to succeed. "
            f"This indicates the target account trust policy is not enforcing ExternalId validation."
        )

        print(f"  ✓ AssumeRole succeeded (correct ExternalId)")

    except ParamValidationError as e:
        # Botocore validates parameters before sending to AWS
        # ExternalId must be 2-1224 characters
        if external_id == expected_external_id:
            pytest.fail(
                f"Parameter validation failed for correct ExternalId: '{external_id}'\n"
                f"  Error: {str(e)}\n"
                f"  This should not happen with the correct ExternalId"
            )

        print(f"  ✓ AssumeRole correctly failed with ParamValidationError (invalid ExternalId format)")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        # If AssumeRole failed, verify it was because ExternalId was incorrect
        if external_id == expected_external_id:
            pytest.fail(
                f"AssumeRole failed with correct ExternalId: '{external_id}'\n"
                f"  Error: {error_code}\n"
                f"  Message: {e.response['Error']['Message']}\n"
                f"  This indicates the target account trust policy may not be configured correctly"
            )

        # Verify we got AccessDenied or ValidationError
        # ValidationError occurs when ExternalId format is invalid (e.g., too short, invalid characters)
        # AccessDenied occurs when ExternalId format is valid but doesn't match trust policy
        assert error_code in ["AccessDenied", "ValidationError"], (
            f"Expected AccessDenied or ValidationError for incorrect ExternalId '{external_id}', "
            f"but got {error_code}: {e.response['Error']['Message']}"
        )

        print(f"  ✓ AssumeRole correctly failed with {error_code} (incorrect ExternalId)")


@given(
    project_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("Ll", "Nd"))),
    environment=st.sampled_from(["dev", "test", "qa", "staging", "prod"]),
)
@settings(max_examples=10, deadline=10000)
def test_property_external_id_format_generation(project_name, environment, test_account, sts_client):
    """
    Property: ExternalId format {ProjectName}-{Environment} validation.

    Tests that only the exact format matches, and variations fail.

    **Validates: Requirement 10.3**
    """
    role_arn = test_account["roleArn"]
    expected_external_id = "aws-drs-orchestration-qa"

    # Generate ExternalId in format {ProjectName}-{Environment}
    generated_external_id = f"{project_name}-{environment}"

    print(f"\nTesting generated ExternalId: '{generated_external_id}'")
    print(f"  Expected: '{expected_external_id}'")
    print(f"  Match: {generated_external_id == expected_external_id}")

    try:
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"test-format-{hash(generated_external_id) % 10000}",
            ExternalId=generated_external_id,
        )

        # If AssumeRole succeeded, verify it was with correct ExternalId
        assert generated_external_id == expected_external_id, (
            f"AssumeRole succeeded with incorrect ExternalId: '{generated_external_id}'. "
            f"Expected only '{expected_external_id}' to succeed."
        )

        print(f"  ✓ AssumeRole succeeded (correct format)")

    except ParamValidationError as e:
        # Botocore validates parameters before sending to AWS
        # ExternalId must be 2-1224 characters
        if generated_external_id == expected_external_id:
            pytest.fail(
                f"Parameter validation failed for correct ExternalId: '{generated_external_id}'\n"
                f"  Error: {str(e)}\n"
                f"  This should not happen with the correct ExternalId"
            )

        print(f"  ✓ AssumeRole correctly failed with ParamValidationError (invalid format)")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        # If AssumeRole failed, verify it was because ExternalId was incorrect
        if generated_external_id == expected_external_id:
            pytest.fail(
                f"AssumeRole failed with correct ExternalId: '{generated_external_id}'\n"
                f"  Error: {error_code}\n"
                f"  Message: {e.response['Error']['Message']}"
            )

        # Verify we got AccessDenied or ValidationError
        # ValidationError occurs when ExternalId format is invalid (e.g., too short, invalid characters)
        # AccessDenied occurs when ExternalId format is valid but doesn't match trust policy
        assert error_code in ["AccessDenied", "ValidationError"], (
            f"Expected AccessDenied or ValidationError for incorrect ExternalId '{generated_external_id}', "
            f"but got {error_code}"
        )

        print(f"  ✓ AssumeRole correctly failed with {error_code} (incorrect format)")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
