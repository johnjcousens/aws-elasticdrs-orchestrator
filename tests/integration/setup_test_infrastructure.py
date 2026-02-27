"""
Test Infrastructure Setup for Functional Equivalence Testing.

This script creates test data in the QA environment for functional equivalence
testing of unified vs function-specific IAM roles.

Environment: aws-drs-orchestration-qa
Region: us-east-2
Account: 438465159935

Usage:
    # Activate virtual environment first
    source .venv/bin/activate

    # Create test infrastructure
    .venv/bin/python tests/integration/setup_test_infrastructure.py

    # Cleanup test infrastructure
    .venv/bin/python tests/integration/setup_test_infrastructure.py --cleanup

Requirements:
    - AWS credentials configured for account 438465159935
    - QA stack deployed with UseFunctionSpecificRoles=false
    - Python 3.9+ with boto3 installed in .venv
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# QA Environment Configuration
PROJECT_NAME = "aws-drs-orchestration"
ENVIRONMENT = "qa"
REGION = "us-east-2"
ACCOUNT_ID = "438465159935"

# DynamoDB Table Names
PROTECTION_GROUPS_TABLE = f"{PROJECT_NAME}-protection-groups-{ENVIRONMENT}"
RECOVERY_PLANS_TABLE = f"{PROJECT_NAME}-recovery-plans-{ENVIRONMENT}"
TARGET_ACCOUNTS_TABLE = f"{PROJECT_NAME}-target-accounts-{ENVIRONMENT}"
EXECUTION_HISTORY_TABLE = f"{PROJECT_NAME}-execution-history-{ENVIRONMENT}"


class TestInfrastructureSetup:
    """Manages test infrastructure setup and cleanup."""

    def __init__(self):
        """Initialize AWS clients for QA environment."""
        self.dynamodb = boto3.resource("dynamodb", region_name=REGION)
        self.cloudformation = boto3.client("cloudformation", region_name=REGION)
        self.sts = boto3.client("sts", region_name=REGION)

    def verify_environment(self) -> bool:
        """
        Verify we're targeting the correct QA environment.

        Returns:
            True if environment is correct, False otherwise
        """
        logger.info("Verifying QA environment configuration...")

        try:
            # Verify we're in the correct account
            identity = self.sts.get_caller_identity()
            current_account = identity["Account"]

            if current_account != ACCOUNT_ID:
                logger.error(
                    f"CRITICAL: Wrong AWS account! Expected {ACCOUNT_ID}, got {current_account}"
                )
                return False

            logger.info(f"✓ Verified AWS account: {current_account}")
            logger.info(f"✓ Verified region: {REGION}")
            logger.info(f"✓ Verified environment: {ENVIRONMENT}")

            # Verify QA stack exists
            try:
                stack_name = f"{PROJECT_NAME}-{ENVIRONMENT}"
                response = self.cloudformation.describe_stacks(StackName=stack_name)
                stack_status = response["Stacks"][0]["StackStatus"]
                logger.info(f"✓ Verified stack exists: {stack_name} ({stack_status})")

                # Check UseFunctionSpecificRoles parameter
                parameters = response["Stacks"][0].get("Parameters", [])
                use_function_specific_roles = None
                for param in parameters:
                    if param["ParameterKey"] == "UseFunctionSpecificRoles":
                        use_function_specific_roles = param["ParameterValue"]
                        break

                if use_function_specific_roles:
                    logger.info(f"  UseFunctionSpecificRoles: {use_function_specific_roles}")
                else:
                    logger.warning("  UseFunctionSpecificRoles parameter not found")

            except ClientError as e:
                if e.response["Error"]["Code"] == "ValidationError":
                    logger.error(f"✗ Stack not found: {stack_name}")
                    return False
                raise

            # Verify DynamoDB tables exist
            tables_to_verify = [
                PROTECTION_GROUPS_TABLE,
                RECOVERY_PLANS_TABLE,
                TARGET_ACCOUNTS_TABLE,
                EXECUTION_HISTORY_TABLE,
            ]

            for table_name in tables_to_verify:
                try:
                    table = self.dynamodb.Table(table_name)
                    table.load()
                    logger.info(f"✓ Verified table exists: {table_name}")
                except ClientError as e:
                    if e.response["Error"]["Code"] == "ResourceNotFoundException":
                        logger.error(f"✗ Table not found: {table_name}")
                        return False
                    raise

            return True

        except Exception as e:
            logger.error(f"Environment verification failed: {e}")
            return False

    def create_protection_groups(self) -> List[Dict[str, Any]]:
        """
        Create test protection groups in DynamoDB.

        Returns:
            List of created protection group items
        """
        logger.info("\nCreating test protection groups...")

        table = self.dynamodb.Table(PROTECTION_GROUPS_TABLE)
        timestamp = datetime.now(timezone.utc).isoformat()

        protection_groups = [
            {
                "groupId": "test-pg-001",
                "groupName": "Test Protection Group 001",
                "description": "Test group for functional equivalence testing",
                "servers": [],
                "createdAt": timestamp,
                "updatedAt": timestamp,
                "createdBy": "test-infrastructure-setup",
                "status": "active",
            },
            {
                "groupId": "test-pg-002",
                "groupName": "Test Protection Group 002",
                "description": "Test group with servers for functional equivalence testing",
                "servers": [
                    {
                        "sourceServerId": "s-test-server-001",
                        "hostname": "test-server-001.example.com",
                        "accountId": "123456789012",
                        "region": "us-east-2",
                    },
                    {
                        "sourceServerId": "s-test-server-002",
                        "hostname": "test-server-002.example.com",
                        "accountId": "123456789012",
                        "region": "us-west-2",
                    },
                ],
                "createdAt": timestamp,
                "updatedAt": timestamp,
                "createdBy": "test-infrastructure-setup",
                "status": "active",
            },
        ]

        created_groups = []
        for group in protection_groups:
            try:
                table.put_item(Item=group)
                logger.info(f"✓ Created protection group: {group['groupId']}")
                created_groups.append(group)
            except ClientError as e:
                logger.error(f"✗ Failed to create protection group {group['groupId']}: {e}")

        return created_groups

    def create_recovery_plans(self) -> List[Dict[str, Any]]:
        """
        Create test recovery plans in DynamoDB.

        Returns:
            List of created recovery plan items
        """
        logger.info("\nCreating test recovery plans...")

        table = self.dynamodb.Table(RECOVERY_PLANS_TABLE)
        timestamp = datetime.now(timezone.utc).isoformat()

        recovery_plans = [
            {
                "planId": "test-plan-001",
                "planName": "Test Recovery Plan 001",
                "description": "Test plan for functional equivalence testing",
                "protectionGroups": ["test-pg-001"],
                "waves": [
                    {
                        "waveNumber": 1,
                        "waveName": "Wave 1",
                        "groups": ["test-pg-001"],
                        "delayMinutes": 0,
                    }
                ],
                "createdAt": timestamp,
                "updatedAt": timestamp,
                "createdBy": "test-infrastructure-setup",
                "status": "active",
            },
            {
                "planId": "test-plan-002",
                "planName": "Test Recovery Plan 002",
                "description": "Test plan with multiple waves for functional equivalence testing",
                "protectionGroups": ["test-pg-001", "test-pg-002"],
                "waves": [
                    {
                        "waveNumber": 1,
                        "waveName": "Wave 1 - Critical Systems",
                        "groups": ["test-pg-001"],
                        "delayMinutes": 0,
                    },
                    {
                        "waveNumber": 2,
                        "waveName": "Wave 2 - Secondary Systems",
                        "groups": ["test-pg-002"],
                        "delayMinutes": 15,
                    },
                ],
                "createdAt": timestamp,
                "updatedAt": timestamp,
                "createdBy": "test-infrastructure-setup",
                "status": "active",
            },
        ]

        created_plans = []
        for plan in recovery_plans:
            try:
                table.put_item(Item=plan)
                logger.info(f"✓ Created recovery plan: {plan['planId']}")
                created_plans.append(plan)
            except ClientError as e:
                logger.error(f"✗ Failed to create recovery plan {plan['planId']}: {e}")

        return created_plans

    def create_target_accounts(self) -> List[Dict[str, Any]]:
        """
        Create test target accounts in DynamoDB.

        Returns:
            List of created target account items
        """
        logger.info("\nCreating test target accounts...")

        table = self.dynamodb.Table(TARGET_ACCOUNTS_TABLE)
        timestamp = datetime.now(timezone.utc).isoformat()

        target_accounts = [
            {
                "accountId": "123456789012",
                "accountName": "Test Account 001",
                "region": "us-east-2",
                "roleArn": "arn:aws:iam::123456789012:role/DRSOrchestrationRole",
                "externalId": f"{PROJECT_NAME}-{ENVIRONMENT}",
                "createdAt": timestamp,
                "updatedAt": timestamp,
                "status": "active",
            },
            {
                "accountId": "123456789013",
                "accountName": "Test Account 002",
                "region": "us-west-2",
                "roleArn": "arn:aws:iam::123456789013:role/DRSOrchestrationRole",
                "externalId": f"{PROJECT_NAME}-{ENVIRONMENT}",
                "createdAt": timestamp,
                "updatedAt": timestamp,
                "status": "active",
            },
            {
                "accountId": "123456789014",
                "accountName": "Test Account 003",
                "region": "eu-west-1",
                "roleArn": "arn:aws:iam::123456789014:role/DRSOrchestrationRole",
                "externalId": f"{PROJECT_NAME}-{ENVIRONMENT}",
                "createdAt": timestamp,
                "updatedAt": timestamp,
                "status": "active",
            },
        ]

        created_accounts = []
        for account in target_accounts:
            try:
                table.put_item(Item=account)
                logger.info(f"✓ Created target account: {account['accountId']}")
                created_accounts.append(account)
            except ClientError as e:
                logger.error(f"✗ Failed to create target account {account['accountId']}: {e}")

        return created_accounts

    def create_execution_history(self) -> List[Dict[str, Any]]:
        """
        Create test execution history in DynamoDB.

        Returns:
            List of created execution history items
        """
        logger.info("\nCreating test execution history...")

        table = self.dynamodb.Table(EXECUTION_HISTORY_TABLE)
        timestamp = datetime.now(timezone.utc).isoformat()
        execution_id = str(uuid4())

        execution_history = [
            {
                "executionId": execution_id,
                "planId": "test-plan-001",
                "planName": "Test Recovery Plan 001",
                "status": "COMPLETED",
                "startTime": timestamp,
                "endTime": timestamp,
                "initiatedBy": "test-infrastructure-setup",
                "waves": [
                    {
                        "waveNumber": 1,
                        "waveName": "Wave 1",
                        "status": "COMPLETED",
                        "startTime": timestamp,
                        "endTime": timestamp,
                    }
                ],
                "createdAt": timestamp,
                "updatedAt": timestamp,
            }
        ]

        created_history = []
        for history in execution_history:
            try:
                table.put_item(Item=history)
                logger.info(f"✓ Created execution history: {history['executionId']}")
                created_history.append(history)
            except ClientError as e:
                logger.error(f"✗ Failed to create execution history {history['executionId']}: {e}")

        return created_history

    def cleanup_test_data(self) -> None:
        """Remove all test data from DynamoDB tables."""
        logger.info("\nCleaning up test data...")

        # Cleanup protection groups
        logger.info("Removing test protection groups...")
        pg_table = self.dynamodb.Table(PROTECTION_GROUPS_TABLE)
        for group_id in ["test-pg-001", "test-pg-002"]:
            try:
                pg_table.delete_item(Key={"groupId": group_id})
                logger.info(f"✓ Deleted protection group: {group_id}")
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    logger.error(f"✗ Failed to delete protection group {group_id}: {e}")

        # Cleanup recovery plans
        logger.info("Removing test recovery plans...")
        rp_table = self.dynamodb.Table(RECOVERY_PLANS_TABLE)
        for plan_id in ["test-plan-001", "test-plan-002"]:
            try:
                rp_table.delete_item(Key={"planId": plan_id})
                logger.info(f"✓ Deleted recovery plan: {plan_id}")
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    logger.error(f"✗ Failed to delete recovery plan {plan_id}: {e}")

        # Cleanup target accounts
        logger.info("Removing test target accounts...")
        ta_table = self.dynamodb.Table(TARGET_ACCOUNTS_TABLE)
        for account_id in ["123456789012", "123456789013", "123456789014"]:
            try:
                ta_table.delete_item(Key={"accountId": account_id})
                logger.info(f"✓ Deleted target account: {account_id}")
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    logger.error(f"✗ Failed to delete target account {account_id}: {e}")

        # Cleanup execution history
        logger.info("Removing test execution history...")
        eh_table = self.dynamodb.Table(EXECUTION_HISTORY_TABLE)
        try:
            # Scan for test execution history items
            response = eh_table.scan(
                FilterExpression="attribute_exists(initiatedBy) AND initiatedBy = :initiator",
                ExpressionAttributeValues={":initiator": "test-infrastructure-setup"}
            )
            for item in response.get("Items", []):
                execution_id = item["executionId"]
                eh_table.delete_item(Key={"executionId": execution_id})
                logger.info(f"✓ Deleted execution history: {execution_id}")
        except ClientError as e:
            logger.error(f"✗ Failed to cleanup execution history: {e}")

    def setup(self) -> bool:
        """
        Create all test infrastructure.

        Returns:
            True if setup succeeded, False otherwise
        """
        logger.info("=" * 80)
        logger.info("Test Infrastructure Setup")
        logger.info("=" * 80)
        logger.info(f"Environment: {ENVIRONMENT}")
        logger.info(f"Region: {REGION}")
        logger.info(f"Account: {ACCOUNT_ID}")
        logger.info("=" * 80)

        try:
            # Step 1: Verify environment
            if not self.verify_environment():
                logger.error("Environment verification failed. Aborting setup.")
                return False

            # Step 2: Create test data
            protection_groups = self.create_protection_groups()
            recovery_plans = self.create_recovery_plans()
            target_accounts = self.create_target_accounts()
            execution_history = self.create_execution_history()

            # Step 3: Summary
            logger.info("\n" + "=" * 80)
            logger.info("SETUP SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Protection Groups Created: {len(protection_groups)}")
            logger.info(f"Recovery Plans Created: {len(recovery_plans)}")
            logger.info(f"Target Accounts Created: {len(target_accounts)}")
            logger.info(f"Execution History Created: {len(execution_history)}")
            logger.info("=" * 80)

            total_created = (
                len(protection_groups) +
                len(recovery_plans) +
                len(target_accounts) +
                len(execution_history)
            )

            if total_created > 0:
                logger.info("✓ Test infrastructure setup completed successfully!")
                return True
            else:
                logger.error("✗ No test data was created")
                return False

        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=True)
            return False

    def cleanup(self) -> bool:
        """
        Remove all test infrastructure.

        Returns:
            True if cleanup succeeded, False otherwise
        """
        logger.info("=" * 80)
        logger.info("Test Infrastructure Cleanup")
        logger.info("=" * 80)
        logger.info(f"Environment: {ENVIRONMENT}")
        logger.info(f"Region: {REGION}")
        logger.info(f"Account: {ACCOUNT_ID}")
        logger.info("=" * 80)

        try:
            # Step 1: Verify environment
            if not self.verify_environment():
                logger.error("Environment verification failed. Aborting cleanup.")
                return False

            # Step 2: Cleanup test data
            self.cleanup_test_data()

            # Step 3: Summary
            logger.info("\n" + "=" * 80)
            logger.info("✓ Test infrastructure cleanup completed successfully!")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point for test infrastructure setup."""
    parser = argparse.ArgumentParser(
        description="Setup or cleanup test infrastructure for functional equivalence testing"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove test infrastructure instead of creating it"
    )

    args = parser.parse_args()

    setup = TestInfrastructureSetup()

    if args.cleanup:
        success = setup.cleanup()
    else:
        success = setup.setup()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
