"""
Integration tests for cross-account ExternalId validation.

Tests STS AssumeRole with correct and incorrect ExternalId values to verify
that the target account trust policy enforces ExternalId validation.

Test Environment:
- QA stack: aws-drs-orchestration-qa in us-east-2
- Target accounts table: aws-drs-orchestration-target-accounts-qa
- Expected ExternalId format: aws-drs-orchestration-qa

Requirements Validated:
- 10.2: ExternalId required for STS AssumeRole operations
- 10.3: ExternalId must match {ProjectName}-{Environment}
- 10.4: AssumeRole fails with AccessDenied when ExternalId is incorrect
"""

import boto3
import pytest
from botocore.exceptions import ClientError


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


@pytest.fixture(scope="function")
def dynamodb_client(qa_environment):
    """DynamoDB client for QA region."""
    return boto3.client("dynamodb", region_name=qa_environment["region"])


@pytest.fixture(scope="function")
def sts_client(qa_environment):
    """STS client for QA region."""
    return boto3.client("sts", region_name=qa_environment["region"])


@pytest.fixture(scope="function")
def target_accounts(dynamodb_client, qa_environment):
    """
    Get all target accounts from DynamoDB.

    Returns list of accounts with roleArn and externalId configured.
    """
    table_name = qa_environment["target_accounts_table"]

    try:
        response = dynamodb_client.scan(TableName=table_name)
        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = dynamodb_client.scan(
                TableName=table_name, ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))

        # Convert DynamoDB format to dict
        accounts = []
        for item in items:
            account = {
                "accountId": item.get("accountId", {}).get("S", ""),
                "accountName": item.get("accountName", {}).get("S", ""),
                "roleArn": item.get("roleArn", {}).get("S", ""),
                "externalId": item.get("externalId", {}).get("S", ""),
            }
            # Only include accounts with roleArn and externalId configured
            if account["roleArn"] and account["externalId"]:
                accounts.append(account)

        return accounts

    except ClientError as e:
        pytest.fail(f"Failed to scan target accounts table: {e}")


def test_target_accounts_have_external_id(target_accounts, qa_environment):
    """
    Test that all target accounts have externalId configured.

    Validates: Requirement 10.2 - ExternalId required for cross-account operations
    """
    assert len(target_accounts) > 0, "No target accounts found in DynamoDB table"

    for account in target_accounts:
        assert account["externalId"], (
            f"Account {account['accountId']} ({account['accountName']}) "
            f"missing externalId in target accounts table"
        )
        print(
            f"✓ Account {account['accountId']} ({account['accountName']}) "
            f"has externalId: {account['externalId']}"
        )


def test_external_id_format_matches_project_environment(target_accounts, qa_environment):
    """
    Test that ExternalId format matches {ProjectName}-{Environment}.

    Validates: Requirement 10.3 - ExternalId must match pattern
    """
    expected_external_id = qa_environment["expected_external_id"]

    for account in target_accounts:
        assert account["externalId"] == expected_external_id, (
            f"Account {account['accountId']} ({account['accountName']}) "
            f"has incorrect externalId: {account['externalId']} "
            f"(expected: {expected_external_id})"
        )
        print(
            f"✓ Account {account['accountId']} ({account['accountName']}) "
            f"externalId matches expected format: {expected_external_id}"
        )


def test_assume_role_succeeds_with_correct_external_id(target_accounts, sts_client, qa_environment):
    """
    Test that STS AssumeRole succeeds with correct ExternalId.

    Validates: Requirement 10.2 - Correct ExternalId allows role assumption
    """
    if not target_accounts:
        pytest.skip("No target accounts with roleArn and externalId configured")

    # Test with first account that has roleArn and externalId
    account = target_accounts[0]
    role_arn = account["roleArn"]
    external_id = account["externalId"]

    print(f"\nTesting AssumeRole with correct ExternalId:")
    print(f"  Account: {account['accountId']} ({account['accountName']})")
    print(f"  Role ARN: {role_arn}")
    print(f"  ExternalId: {external_id}")

    try:
        response = sts_client.assume_role(
            RoleArn=role_arn, RoleSessionName="test-external-id-validation", ExternalId=external_id
        )

        # Verify we got temporary credentials
        assert "Credentials" in response, "AssumeRole response missing Credentials"
        assert "AccessKeyId" in response["Credentials"], "Missing AccessKeyId in credentials"
        assert "SecretAccessKey" in response["Credentials"], "Missing SecretAccessKey in credentials"
        assert "SessionToken" in response["Credentials"], "Missing SessionToken in credentials"

        print(f"✓ AssumeRole succeeded with correct ExternalId")
        print(f"  Session: {response['AssumedRoleUser']['AssumedRoleId']}")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        pytest.fail(
            f"AssumeRole failed with correct ExternalId:\n"
            f"  Error: {error_code}\n"
            f"  Message: {error_message}\n"
            f"  This indicates the target account trust policy may not be configured correctly"
        )


def test_assume_role_fails_with_incorrect_external_id(target_accounts, sts_client, qa_environment):
    """
    Test that STS AssumeRole fails with incorrect ExternalId.

    Validates: Requirement 10.4 - Incorrect ExternalId causes AccessDenied
    """
    if not target_accounts:
        pytest.skip("No target accounts with roleArn and externalId configured")

    # Test with first account that has roleArn and externalId
    account = target_accounts[0]
    role_arn = account["roleArn"]
    incorrect_external_id = "incorrect-external-id-12345"

    print(f"\nTesting AssumeRole with incorrect ExternalId:")
    print(f"  Account: {account['accountId']} ({account['accountName']})")
    print(f"  Role ARN: {role_arn}")
    print(f"  Incorrect ExternalId: {incorrect_external_id}")

    with pytest.raises(ClientError) as exc_info:
        sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="test-external-id-validation-negative",
            ExternalId=incorrect_external_id,
        )

    # Verify we got AccessDenied error
    error = exc_info.value
    error_code = error.response["Error"]["Code"]
    error_message = error.response["Error"]["Message"]

    assert error_code == "AccessDenied", (
        f"Expected AccessDenied error, got {error_code}. "
        f"This indicates the target account trust policy may not enforce ExternalId validation."
    )

    print(f"✓ AssumeRole correctly failed with AccessDenied")
    print(f"  Error: {error_code}")
    print(f"  Message: {error_message}")


def test_assume_role_fails_without_external_id(target_accounts, sts_client, qa_environment):
    """
    Test that STS AssumeRole fails when ExternalId is not provided.

    Validates: Requirement 10.2 - ExternalId is required (not optional)
    """
    if not target_accounts:
        pytest.skip("No target accounts with roleArn and externalId configured")

    # Test with first account that has roleArn and externalId
    account = target_accounts[0]
    role_arn = account["roleArn"]

    print(f"\nTesting AssumeRole without ExternalId:")
    print(f"  Account: {account['accountId']} ({account['accountName']})")
    print(f"  Role ARN: {role_arn}")
    print(f"  ExternalId: (not provided)")

    with pytest.raises(ClientError) as exc_info:
        sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="test-external-id-validation-missing",
            # ExternalId intentionally omitted
        )

    # Verify we got AccessDenied error
    error = exc_info.value
    error_code = error.response["Error"]["Code"]
    error_message = error.response["Error"]["Message"]

    assert error_code == "AccessDenied", (
        f"Expected AccessDenied error, got {error_code}. "
        f"This indicates the target account trust policy may not require ExternalId."
    )

    print(f"✓ AssumeRole correctly failed with AccessDenied when ExternalId not provided")
    print(f"  Error: {error_code}")
    print(f"  Message: {error_message}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
