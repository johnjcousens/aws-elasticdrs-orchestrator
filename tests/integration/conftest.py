"""
Pytest configuration for integration tests.

Sets up AWS session with correct profile for QA environment testing.
"""

import os
import boto3
import pytest


def pytest_configure(config):
    """
    Configure pytest session with AWS credentials.
    
    Sets AWS_PROFILE environment variable before any tests run to ensure
    boto3 clients pick up the correct credentials.
    """
    # Set AWS profile for QA orchestration account
    os.environ["AWS_PROFILE"] = "438465159935_AdministratorAccess"
    
    # Force boto3 to reload credentials
    boto3.setup_default_session(profile_name="438465159935_AdministratorAccess")


@pytest.fixture(scope="session", autouse=True)
def aws_credentials():
    """
    Ensure AWS credentials are configured for all tests.
    
    This fixture runs automatically before any tests and verifies
    that AWS credentials are available.
    """
    # Verify credentials are working
    try:
        sts = boto3.client("sts", region_name="us-east-2")
        identity = sts.get_caller_identity()
        account_id = identity["Account"]
        
        # Verify we're using the correct account
        assert account_id == "438465159935", (
            f"Wrong AWS account: {account_id}. "
            f"Expected QA orchestration account 438465159935. "
            f"Please authenticate with: aws login"
        )
        
        print(f"\n✓ AWS credentials verified for account {account_id}")
        
    except Exception as e:
        pytest.fail(
            f"AWS credentials not configured or expired:\n"
            f"  Error: {e}\n"
            f"  Please authenticate with: aws login\n"
            f"  Then set profile: export AWS_PROFILE=438465159935_AdministratorAccess"
        )
