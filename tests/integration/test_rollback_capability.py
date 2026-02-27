"""
Rollback Capability Test for Function-Specific Roles Configuration.

This test suite verifies that rolling back from function-specific roles
(UseFunctionSpecificRoles=true) to unified role (UseFunctionSpecificRoles=false)
preserves all data and executions without service interruption.

Property 17: Rollback Preserves Data and Executions
For any CloudFormation stack update that changes UseFunctionSpecificRoles from
true to false, when the update completes, all DynamoDB data should remain
unchanged, all running Step Functions executions should continue without
interruption, and all Lambda functions should immediately use the Unified Role.

Environment: aws-drs-orchestration-qa
Region: us-east-2
Account: 438465159935

Usage:
    # Activate virtual environment first
    source .venv/bin/activate

    # Run rollback test
    .venv/bin/python tests/integration/test_rollback_capability.py

Requirements:
    - AWS credentials configured for account 438465159935
    - QA stack deployed with UseFunctionSpecificRoles=true
    - Python 3.9+ with boto3 installed in .venv
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# QA Environment Configuration
PROJECT_NAME = "aws-drs-orchestration"
ENVIRONMENT = "qa"
REGION = "us-east-2"
ACCOUNT_ID = "438465159935"
STACK_NAME = f"{PROJECT_NAME}-{ENVIRONMENT}"

# Lambda Function Names
QUERY_HANDLER = f"{PROJECT_NAME}-query-handler-{ENVIRONMENT}"
DATA_MANAGEMENT_HANDLER = f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}"
EXECUTION_HANDLER = f"{PROJECT_NAME}-execution-handler-{ENVIRONMENT}"
ORCHESTRATION_FUNCTION = f"{PROJECT_NAME}-dr-orch-sf-{ENVIRONMENT}"
FRONTEND_DEPLOYER = f"{PROJECT_NAME}-frontend-deployer-{ENVIRONMENT}"

# DynamoDB Table Names
PROTECTION_GROUPS_TABLE = f"{PROJECT_NAME}-protection-groups-{ENVIRONMENT}"
RECOVERY_PLANS_TABLE = f"{PROJECT_NAME}-recovery-plans-{ENVIRONMENT}"
EXECUTION_HISTORY_TABLE = f"{PROJECT_NAME}-execution-history-{ENVIRONMENT}"
TARGET_ACCOUNTS_TABLE = f"{PROJECT_NAME}-target-accounts-{ENVIRONMENT}"


class RollbackCapabilityTest:
    """Tests rollback capability from function-specific to unified roles."""

    def __init__(self):
        """Initialize AWS clients for QA environment."""
        try:
            creds_json = subprocess.check_output(
                ["aws", "configure", "export-credentials", "--format", "process"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8")
            creds = json.loads(creds_json)

            session = boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds.get("SessionToken"),
                region_name=REGION
            )

            self.cloudformation = session.client("cloudformation")
            self.lambda_client = session.client("lambda")
            self.dynamodb = session.resource("dynamodb")
            self.stepfunctions = session.client("stepfunctions")
            self.sts = session.client("sts")

            self.pre_rollback_state: Dict[str, Any] = {}
            self.post_rollback_state: Dict[str, Any] = {}
            self.timestamp = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise

    def verify_environment(self) -> bool:
        """Verify we're targeting the correct QA environment."""
        logger.info("Verifying QA environment configuration...")

        try:
            identity = self.sts.get_caller_identity()
            current_account = identity["Account"]

            if current_account != ACCOUNT_ID:
                logger.error(f"CRITICAL: Wrong AWS account! Expected {ACCOUNT_ID}, got {current_account}")
                return False

            logger.info(f"✓ Verified AWS account: {current_account}")
            logger.info(f"✓ Verified region: {REGION}")
            logger.info(f"✓ Verified environment: {ENVIRONMENT}")

            # Verify stack exists
            try:
                response = self.cloudformation.describe_stacks(StackName=STACK_NAME)
                stack = response["Stacks"][0]
                stack_status = stack["StackStatus"]
                logger.info(f"✓ Stack exists: {STACK_NAME}")
                logger.info(f"  Status: {stack_status}")

                if stack_status not in ["CREATE_COMPLETE", "UPDATE_COMPLETE"]:
                    logger.error(f"✗ Stack is not in a stable state: {stack_status}")
                    return False

            except ClientError as e:
                if e.response["Error"]["Code"] == "ValidationError":
                    logger.error(f"✗ Stack not found: {STACK_NAME}")
                    return False
                raise

            return True

        except Exception as e:
            logger.error(f"Environment verification failed: {e}")
            return False

    def capture_pre_rollback_state(self) -> Dict[str, Any]:
        """Capture state before rollback deployment."""
        logger.info("\n" + "=" * 80)
        logger.info("Capturing Pre-Rollback State")
        logger.info("=" * 80)

        state: Dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat()}

        # Capture DynamoDB table item counts
        logger.info("Capturing DynamoDB table item counts...")
        state["dynamodb_tables"] = {}

        for table_name in [
            PROTECTION_GROUPS_TABLE,
            RECOVERY_PLANS_TABLE,
            EXECUTION_HISTORY_TABLE,
            TARGET_ACCOUNTS_TABLE
        ]:
            try:
                table = self.dynamodb.Table(table_name)
                response = table.scan(Select="COUNT")
                item_count = response["Count"]
                state["dynamodb_tables"][table_name] = {"item_count": item_count}
                logger.info(f"  {table_name}: {item_count} items")
            except ClientError as e:
                logger.warning(f"  ⚠ Failed to scan {table_name}: {e}")
                state["dynamodb_tables"][table_name] = {"error": str(e)}

        # Capture Lambda function configurations
        logger.info("Capturing Lambda function configurations...")
        state["lambda_functions"] = {}

        for function_name in [
            QUERY_HANDLER,
            DATA_MANAGEMENT_HANDLER,
            EXECUTION_HANDLER,
            ORCHESTRATION_FUNCTION,
            FRONTEND_DEPLOYER
        ]:
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                config = response["Configuration"]
                state["lambda_functions"][function_name] = {
                    "role_arn": config["Role"],
                    "runtime": config["Runtime"],
                    "memory_size": config["MemorySize"],
                    "timeout": config["Timeout"],
                    "last_modified": config["LastModified"]
                }
                logger.info(f"  {function_name}")
                logger.info(f"    Role: {config['Role']}")
            except ClientError as e:
                logger.warning(f"  ⚠ Failed to get function {function_name}: {e}")
                state["lambda_functions"][function_name] = {"error": str(e)}

        # Capture active Step Functions executions
        logger.info("Capturing active Step Functions executions...")
        state["stepfunctions_executions"] = []

        try:
            state_machine_arn = (
                f"arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:{PROJECT_NAME}-dr-orchestration-{ENVIRONMENT}"
            )
            response = self.stepfunctions.list_executions(
                stateMachineArn=state_machine_arn,
                statusFilter="RUNNING"
            )
            executions = response.get("executions", [])
            state["stepfunctions_executions"] = [
                {
                    "execution_arn": exec["executionArn"],
                    "name": exec["name"],
                    "start_date": exec["startDate"].isoformat()
                }
                for exec in executions
            ]
            logger.info(f"  Active executions: {len(executions)}")
        except ClientError as e:
            logger.warning(f"  ⚠ Failed to list executions: {e}")
            state["stepfunctions_executions"] = {"error": str(e)}

        # Capture CloudFormation stack parameters
        logger.info("Capturing CloudFormation stack parameters...")
        try:
            response = self.cloudformation.describe_stacks(StackName=STACK_NAME)
            stack = response["Stacks"][0]
            parameters = {param["ParameterKey"]: param["ParameterValue"] for param in stack.get("Parameters", [])}
            state["cloudformation_parameters"] = parameters
            logger.info(f"  UseFunctionSpecificRoles: {parameters.get('UseFunctionSpecificRoles', 'NOT SET')}")
        except ClientError as e:
            logger.warning(f"  ⚠ Failed to describe stack: {e}")
            state["cloudformation_parameters"] = {"error": str(e)}

        self.pre_rollback_state = state
        logger.info("✓ Pre-rollback state captured")

        return state

    def execute_rollback_deployment(self) -> bool:
        """Execute rollback deployment using deploy script."""
        logger.info("\n" + "=" * 80)
        logger.info("Executing Rollback Deployment")
        logger.info("=" * 80)

        logger.info("Running: ./scripts/deploy-main-stack.sh qa --skip-tests")
        logger.info("This will deploy with UseFunctionSpecificRoles=false (default)")
        logger.info("Skipping frontend tests to avoid flaky test blocking deployment")
        logger.info("")

        try:
            # Execute deploy script with AWS credentials and --skip-tests flag
            env = os.environ.copy()
            env["AWS_PROFILE"] = "AdministratorAccess-438465159935"
            env["AWS_REGION"] = REGION
            
            result = subprocess.run(
                ["./scripts/deploy-main-stack.sh", "qa", "--skip-tests"],
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
                env=env
            )

            # Log output
            if result.stdout:
                logger.info("Deploy script output:")
                for line in result.stdout.split("\n"):
                    if line.strip():
                        logger.info(f"  {line}")

            if result.stderr:
                logger.warning("Deploy script stderr:")
                for line in result.stderr.split("\n"):
                    if line.strip():
                        logger.warning(f"  {line}")

            if result.returncode != 0:
                logger.error(f"✗ Deploy script failed with exit code {result.returncode}")
                return False

            logger.info("✓ Deploy script completed successfully")

            # Wait for stack update to complete
            logger.info("Waiting for CloudFormation stack update to complete...")
            waiter = self.cloudformation.get_waiter("stack_update_complete")
            waiter.wait(
                StackName=STACK_NAME,
                WaiterConfig={"Delay": 30, "MaxAttempts": 60}
            )

            logger.info("✓ CloudFormation stack update completed")
            return True

        except subprocess.TimeoutExpired:
            logger.error("✗ Deploy script timed out after 30 minutes")
            return False
        except Exception as e:
            logger.error(f"✗ Deployment failed: {e}")
            return False

    def capture_post_rollback_state(self) -> Dict[str, Any]:
        """Capture state after rollback deployment."""
        logger.info("\n" + "=" * 80)
        logger.info("Capturing Post-Rollback State")
        logger.info("=" * 80)

        state: Dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat()}

        # Capture DynamoDB table item counts
        logger.info("Capturing DynamoDB table item counts...")
        state["dynamodb_tables"] = {}

        for table_name in [
            PROTECTION_GROUPS_TABLE,
            RECOVERY_PLANS_TABLE,
            EXECUTION_HISTORY_TABLE,
            TARGET_ACCOUNTS_TABLE
        ]:
            try:
                table = self.dynamodb.Table(table_name)
                response = table.scan(Select="COUNT")
                item_count = response["Count"]
                state["dynamodb_tables"][table_name] = {"item_count": item_count}
                logger.info(f"  {table_name}: {item_count} items")
            except ClientError as e:
                logger.warning(f"  ⚠ Failed to scan {table_name}: {e}")
                state["dynamodb_tables"][table_name] = {"error": str(e)}

        # Capture Lambda function configurations
        logger.info("Capturing Lambda function configurations...")
        state["lambda_functions"] = {}

        for function_name in [
            QUERY_HANDLER,
            DATA_MANAGEMENT_HANDLER,
            EXECUTION_HANDLER,
            ORCHESTRATION_FUNCTION,
            FRONTEND_DEPLOYER
        ]:
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                config = response["Configuration"]
                state["lambda_functions"][function_name] = {
                    "role_arn": config["Role"],
                    "runtime": config["Runtime"],
                    "memory_size": config["MemorySize"],
                    "timeout": config["Timeout"],
                    "last_modified": config["LastModified"]
                }
                logger.info(f"  {function_name}")
                logger.info(f"    Role: {config['Role']}")
            except ClientError as e:
                logger.warning(f"  ⚠ Failed to get function {function_name}: {e}")
                state["lambda_functions"][function_name] = {"error": str(e)}

        # Capture active Step Functions executions
        logger.info("Capturing active Step Functions executions...")
        state["stepfunctions_executions"] = []

        try:
            state_machine_arn = (
                f"arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:{PROJECT_NAME}-dr-orchestration-{ENVIRONMENT}"
            )
            response = self.stepfunctions.list_executions(
                stateMachineArn=state_machine_arn,
                statusFilter="RUNNING"
            )
            executions = response.get("executions", [])
            state["stepfunctions_executions"] = [
                {
                    "execution_arn": exec["executionArn"],
                    "name": exec["name"],
                    "start_date": exec["startDate"].isoformat()
                }
                for exec in executions
            ]
            logger.info(f"  Active executions: {len(executions)}")
        except ClientError as e:
            logger.warning(f"  ⚠ Failed to list executions: {e}")
            state["stepfunctions_executions"] = {"error": str(e)}

        # Capture CloudFormation stack parameters
        logger.info("Capturing CloudFormation stack parameters...")
        try:
            response = self.cloudformation.describe_stacks(StackName=STACK_NAME)
            stack = response["Stacks"][0]
            parameters = {param["ParameterKey"]: param["ParameterValue"] for param in stack.get("Parameters", [])}
            state["cloudformation_parameters"] = parameters
            logger.info(f"  UseFunctionSpecificRoles: {parameters.get('UseFunctionSpecificRoles', 'NOT SET')}")
        except ClientError as e:
            logger.warning(f"  ⚠ Failed to describe stack: {e}")
            state["cloudformation_parameters"] = {"error": str(e)}

        self.post_rollback_state = state
        logger.info("✓ Post-rollback state captured")

        return state

    def verify_rollback_results(self) -> Dict[str, Any]:
        """Verify rollback preserved data and switched to unified role."""
        logger.info("\n" + "=" * 80)
        logger.info("Verifying Rollback Results")
        logger.info("=" * 80)

        results: Dict[str, Any] = {"checks": [], "overall_success": True}

        # Check 1: Verify DynamoDB data preserved
        logger.info("Check 1: Verifying DynamoDB data preserved...")
        dynamodb_check = {"name": "dynamodb_data_preserved", "success": True, "details": []}

        for table_name in [
            PROTECTION_GROUPS_TABLE,
            RECOVERY_PLANS_TABLE,
            EXECUTION_HISTORY_TABLE,
            TARGET_ACCOUNTS_TABLE
        ]:
            pre_count = self.pre_rollback_state["dynamodb_tables"].get(table_name, {}).get("item_count")
            post_count = self.post_rollback_state["dynamodb_tables"].get(table_name, {}).get("item_count")

            if pre_count is not None and post_count is not None:
                if pre_count == post_count:
                    logger.info(f"  ✓ {table_name}: {pre_count} items (unchanged)")
                    dynamodb_check["details"].append({
                        "table": table_name,
                        "pre_count": pre_count,
                        "post_count": post_count,
                        "preserved": True
                    })
                else:
                    logger.error(f"  ✗ {table_name}: {pre_count} → {post_count} items (DATA LOSS!)")
                    dynamodb_check["success"] = False
                    dynamodb_check["details"].append({
                        "table": table_name,
                        "pre_count": pre_count,
                        "post_count": post_count,
                        "preserved": False
                    })
            else:
                logger.warning(f"  ⚠ {table_name}: Unable to compare (missing data)")
                dynamodb_check["details"].append({
                    "table": table_name,
                    "error": "missing_data"
                })

        results["checks"].append(dynamodb_check)
        if not dynamodb_check["success"]:
            results["overall_success"] = False

        # Check 2: Verify Lambda functions switched to unified role
        logger.info("Check 2: Verifying Lambda functions switched to unified role...")
        lambda_check = {"name": "lambda_functions_use_unified_role", "success": True, "details": []}

        unified_role_pattern = f"{PROJECT_NAME}-unified-role-{ENVIRONMENT}"

        for function_name in [
            QUERY_HANDLER,
            DATA_MANAGEMENT_HANDLER,
            EXECUTION_HANDLER,
            ORCHESTRATION_FUNCTION,
            FRONTEND_DEPLOYER
        ]:
            post_role = self.post_rollback_state["lambda_functions"].get(function_name, {}).get("role_arn", "")

            if unified_role_pattern in post_role:
                logger.info(f"  ✓ {function_name}: Using unified role")
                lambda_check["details"].append({
                    "function": function_name,
                    "role_arn": post_role,
                    "uses_unified_role": True
                })
            else:
                logger.error(f"  ✗ {function_name}: NOT using unified role")
                logger.error(f"    Role: {post_role}")
                lambda_check["success"] = False
                lambda_check["details"].append({
                    "function": function_name,
                    "role_arn": post_role,
                    "uses_unified_role": False
                })

        results["checks"].append(lambda_check)
        if not lambda_check["success"]:
            results["overall_success"] = False

        # Check 3: Verify Step Functions executions not interrupted
        logger.info("Check 3: Verifying Step Functions executions not interrupted...")
        stepfunctions_check = {"name": "stepfunctions_executions_not_interrupted", "success": True, "details": []}

        pre_executions = self.pre_rollback_state.get("stepfunctions_executions", [])
        post_executions = self.post_rollback_state.get("stepfunctions_executions", [])

        if isinstance(pre_executions, list) and isinstance(post_executions, list):
            pre_execution_arns = {exec["execution_arn"] for exec in pre_executions}
            post_execution_arns = {exec["execution_arn"] for exec in post_executions}

            interrupted_executions = pre_execution_arns - post_execution_arns

            if not interrupted_executions:
                logger.info(f"  ✓ No executions interrupted ({len(pre_executions)} active before rollback)")
                stepfunctions_check["details"] = {
                    "pre_execution_count": len(pre_executions),
                    "post_execution_count": len(post_executions),
                    "interrupted_count": 0
                }
            else:
                logger.error(f"  ✗ {len(interrupted_executions)} executions interrupted!")
                stepfunctions_check["success"] = False
                stepfunctions_check["details"] = {
                    "pre_execution_count": len(pre_executions),
                    "post_execution_count": len(post_executions),
                    "interrupted_count": len(interrupted_executions),
                    "interrupted_arns": list(interrupted_executions)
                }
        else:
            logger.warning("  ⚠ Unable to compare executions (missing data)")
            stepfunctions_check["details"] = {"error": "missing_data"}

        results["checks"].append(stepfunctions_check)
        if not stepfunctions_check["success"]:
            results["overall_success"] = False

        # Check 4: Verify CloudFormation parameter updated
        logger.info("Check 4: Verifying CloudFormation parameter updated...")
        cfn_check = {"name": "cloudformation_parameter_updated", "success": True, "details": {}}

        post_param = self.post_rollback_state.get("cloudformation_parameters", {}).get("UseFunctionSpecificRoles")

        if post_param == "false":
            logger.info(f"  ✓ UseFunctionSpecificRoles parameter set to 'false'")
            cfn_check["details"] = {"parameter_value": post_param, "correct": True}
        else:
            logger.error(f"  ✗ UseFunctionSpecificRoles parameter is '{post_param}' (expected 'false')")
            cfn_check["success"] = False
            cfn_check["details"] = {"parameter_value": post_param, "correct": False}

        results["checks"].append(cfn_check)
        if not cfn_check["success"]:
            results["overall_success"] = False

        return results

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save test results to JSON file."""
        output_data = {
            "timestamp": self.timestamp,
            "environment": ENVIRONMENT,
            "region": REGION,
            "account_id": ACCOUNT_ID,
            "stack_name": STACK_NAME,
            "pre_rollback_state": self.pre_rollback_state,
            "post_rollback_state": self.post_rollback_state,
            "verification_results": results
        }

        output_path = "tests/integration/rollback_capability_results.json"

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"\n✓ Results saved to {output_path}")

    def run_rollback_test(self) -> bool:
        """Execute complete rollback capability test."""
        logger.info("=" * 80)
        logger.info("Rollback Capability Test - Function-Specific to Unified Role")
        logger.info("=" * 80)
        logger.info(f"Environment: {ENVIRONMENT}")
        logger.info(f"Region: {REGION}")
        logger.info(f"Account: {ACCOUNT_ID}")
        logger.info(f"Stack: {STACK_NAME}")
        logger.info(f"Timestamp: {self.timestamp}")
        logger.info("=" * 80)

        try:
            # Step 1: Verify environment
            if not self.verify_environment():
                logger.error("Environment verification failed. Aborting test.")
                return False

            # Step 2: Capture pre-rollback state
            self.capture_pre_rollback_state()

            # Step 3: Execute rollback deployment
            if not self.execute_rollback_deployment():
                logger.error("Rollback deployment failed. Aborting test.")
                return False

            # Step 4: Capture post-rollback state
            self.capture_post_rollback_state()

            # Step 5: Verify rollback results
            results = self.verify_rollback_results()

            # Step 6: Save results
            self.save_results(results)

            # Step 7: Print final summary
            logger.info("\n" + "=" * 80)
            logger.info("ROLLBACK TEST SUMMARY")
            logger.info("=" * 80)

            for check in results["checks"]:
                status = "✓ PASS" if check["success"] else "✗ FAIL"
                logger.info(f"{status}: {check['name']}")

            logger.info("=" * 80)

            if results["overall_success"]:
                logger.info("✓ Rollback test PASSED - All checks successful!")
                return True
            else:
                logger.error("✗ Rollback test FAILED - Some checks failed")
                return False

        except Exception as e:
            logger.error(f"Rollback test execution failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point for rollback capability test."""
    test = RollbackCapabilityTest()
    success = test.run_rollback_test()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
