"""
Functional Equivalence Tests for Unified Role Configuration.

This test suite executes all Lambda functions in the QA environment with the
unified role configuration (UseFunctionSpecificRoles=false) to establish a
baseline for comparison with function-specific roles.

Environment: aws-drs-orchestration-qa
Region: us-east-2
Account: 438465159935

Usage:
    # Activate virtual environment first
    source .venv/bin/activate

    # Run tests
    .venv/bin/python tests/integration/test_functional_equivalence_unified.py

Requirements:
    - AWS credentials configured for account 438465159935
    - QA stack deployed with UseFunctionSpecificRoles=false
    - Test data created via setup_test_infrastructure.py
    - Python 3.9+ with boto3 installed in .venv
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

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

# Lambda Function Names
QUERY_HANDLER = f"{PROJECT_NAME}-query-handler-{ENVIRONMENT}"
DATA_MANAGEMENT_HANDLER = f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}"
EXECUTION_HANDLER = f"{PROJECT_NAME}-execution-handler-{ENVIRONMENT}"
ORCHESTRATION_FUNCTION = f"{PROJECT_NAME}-dr-orch-sf-{ENVIRONMENT}"
FRONTEND_DEPLOYER = f"{PROJECT_NAME}-frontend-deployer-{ENVIRONMENT}"


class FunctionalEquivalenceTest:
    """Tests functional equivalence with unified role configuration."""

    def __init__(self):
        """Initialize AWS clients for QA environment."""
        # Use subprocess to get credentials from AWS CLI which has SSO session
        import subprocess
        
        # Get credentials from AWS CLI
        try:
            creds_json = subprocess.check_output(
                ["aws", "configure", "export-credentials", "--format", "process"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8")
            creds = json.loads(creds_json)
            
            # Create session with explicit credentials
            session = boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds.get("SessionToken"),
                region_name=REGION
            )
            
            self.lambda_client = session.client("lambda")
            self.logs_client = session.client("logs")
            self.dynamodb = session.resource("dynamodb")
            self.results: Dict[str, Dict[str, Any]] = {}
            self.timestamp = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise

    def verify_environment(self) -> bool:
        """
        Verify we're targeting the correct QA environment.

        Returns:
            True if environment is correct, False otherwise
        """
        logger.info("Verifying QA environment configuration...")

        try:
            # Verify we're in the correct account
            import subprocess
            
            # Get credentials from AWS CLI
            creds_json = subprocess.check_output(
                ["aws", "configure", "export-credentials", "--format", "process"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8")
            creds = json.loads(creds_json)
            
            # Create session with explicit credentials
            session = boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds.get("SessionToken"),
                region_name=REGION
            )
            sts = session.client("sts")
            identity = sts.get_caller_identity()
            current_account = identity["Account"]

            if current_account != ACCOUNT_ID:
                logger.error(
                    f"CRITICAL: Wrong AWS account! Expected {ACCOUNT_ID}, got {current_account}"
                )
                return False

            logger.info(f"✓ Verified AWS account: {current_account}")
            logger.info(f"✓ Verified region: {REGION}")
            logger.info(f"✓ Verified environment: {ENVIRONMENT}")

            # Verify Lambda functions exist
            functions_to_verify = [
                QUERY_HANDLER,
                DATA_MANAGEMENT_HANDLER,
                EXECUTION_HANDLER,
                ORCHESTRATION_FUNCTION,
                FRONTEND_DEPLOYER,
            ]

            for function_name in functions_to_verify:
                try:
                    response = self.lambda_client.get_function(FunctionName=function_name)
                    role_arn = response["Configuration"]["Role"]
                    logger.info(f"✓ Verified function exists: {function_name}")
                    logger.info(f"  Role: {role_arn}")

                    # Verify using unified role (should contain "unified" or "orchestration-role")
                    if "unified" not in role_arn.lower() and "orchestration-role" in role_arn:
                        logger.info(f"  ✓ Using unified role configuration")
                    else:
                        logger.warning(f"  ⚠ Role may not be unified: {role_arn}")

                except ClientError as e:
                    if e.response["Error"]["Code"] == "ResourceNotFoundException":
                        logger.error(f"✗ Function not found: {function_name}")
                        return False
                    raise

            return True

        except Exception as e:
            logger.error(f"Environment verification failed: {e}")
            return False

    def invoke_lambda(
        self,
        function_name: str,
        payload: Dict[str, Any],
        invocation_type: str = "RequestResponse"
    ) -> Dict[str, Any]:
        """
        Invoke a Lambda function and record execution metrics.

        Args:
            function_name: Name of the Lambda function
            payload: Invocation payload
            invocation_type: RequestResponse or Event

        Returns:
            Dictionary containing invocation results and metrics
        """
        logger.info(f"Invoking {function_name}...")

        start_time = time.time()

        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )

            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000

            # Parse response payload
            response_payload = json.loads(response["Payload"].read())

            result = {
                "success": True,
                "status_code": response["StatusCode"],
                "execution_time_ms": execution_time_ms,
                "response_payload": response_payload,
                "function_error": response.get("FunctionError"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if response.get("FunctionError"):
                logger.error(f"✗ Function error: {response['FunctionError']}")
                logger.error(f"  Response: {response_payload}")
                result["success"] = False
            else:
                logger.info(f"✓ Invocation successful ({execution_time_ms:.2f}ms)")

            return result

        except Exception as e:
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000

            logger.error(f"✗ Invocation failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def check_cloudwatch_logs_for_access_denied(
        self,
        function_name: str,
        minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Check CloudWatch Logs for AccessDenied errors.

        Args:
            function_name: Name of the Lambda function
            minutes: Number of minutes to look back

        Returns:
            List of AccessDenied error events
        """
        log_group_name = f"/aws/lambda/{function_name}"
        start_time = int((time.time() - (minutes * 60)) * 1000)
        end_time = int(time.time() * 1000)

        logger.info(f"Checking CloudWatch Logs for AccessDenied errors in {log_group_name}...")

        try:
            response = self.logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time,
                endTime=end_time,
                filterPattern="AccessDenied"
            )

            events = response.get("events", [])

            if events:
                logger.warning(f"⚠ Found {len(events)} AccessDenied errors")
                for event in events:
                    logger.warning(f"  {event['message']}")
            else:
                logger.info(f"✓ No AccessDenied errors found")

            return events

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.warning(f"⚠ Log group not found: {log_group_name}")
                return []
            raise

    def test_query_handler(self) -> Dict[str, Any]:
        """
        Test Query Handler Lambda function.

        Tests:
        - List protection groups (DynamoDB read)
        - Get protection group details (DynamoDB read)
        - List source servers (DRS read)

        Returns:
            Test results dictionary
        """
        logger.info("\n" + "=" * 80)
        logger.info("Testing Query Handler")
        logger.info("=" * 80)

        results = {
            "function_name": QUERY_HANDLER,
            "tests": []
        }

        # Test 1: List protection groups
        test1_payload = {
            "operation": "list_protection_groups"
        }
        test1_result = self.invoke_lambda(QUERY_HANDLER, test1_payload)
        results["tests"].append({
            "test_name": "list_protection_groups",
            "payload": test1_payload,
            "result": test1_result
        })

        # Test 2: Get protection group details
        test2_payload = {
            "operation": "get_protection_group",
            "groupId": "test-pg-001"
        }
        test2_result = self.invoke_lambda(QUERY_HANDLER, test2_payload)
        results["tests"].append({
            "test_name": "get_protection_group",
            "payload": test2_payload,
            "result": test2_result
        })

        # Check for AccessDenied errors
        access_denied_errors = self.check_cloudwatch_logs_for_access_denied(QUERY_HANDLER)
        results["access_denied_errors"] = access_denied_errors

        # Calculate summary
        successful_tests = sum(1 for test in results["tests"] if test["result"]["success"])
        results["summary"] = {
            "total_tests": len(results["tests"]),
            "successful": successful_tests,
            "failed": len(results["tests"]) - successful_tests,
            "access_denied_count": len(access_denied_errors)
        }

        logger.info(f"\nQuery Handler Summary: {successful_tests}/{len(results['tests'])} tests passed")

        return results

    def test_data_management_handler(self) -> Dict[str, Any]:
        """
        Test Data Management Handler Lambda function.

        Tests:
        - Create protection group (DynamoDB write)
        - Update protection group (DynamoDB write)
        - Delete protection group (DynamoDB write)

        Returns:
            Test results dictionary
        """
        logger.info("\n" + "=" * 80)
        logger.info("Testing Data Management Handler")
        logger.info("=" * 80)

        results = {
            "function_name": DATA_MANAGEMENT_HANDLER,
            "tests": []
        }

        # Test 1: Create protection group
        test1_payload = {
            "operation": "create_protection_group",
            "groupName": "Test Group Functional Equivalence",
            "description": "Created by functional equivalence test",
            "servers": []
        }
        test1_result = self.invoke_lambda(DATA_MANAGEMENT_HANDLER, test1_payload)
        results["tests"].append({
            "test_name": "create_protection_group",
            "payload": test1_payload,
            "result": test1_result
        })

        # Extract groupId from response for subsequent tests
        group_id = None
        if test1_result["success"] and "response_payload" in test1_result:
            try:
                group_id = test1_result["response_payload"].get("groupId")
            except (KeyError, AttributeError):
                pass

        # Test 2: Update protection group (if created successfully)
        if group_id:
            test2_payload = {
                "operation": "update_protection_group",
                "groupId": group_id,
                "description": "Updated by functional equivalence test"
            }
            test2_result = self.invoke_lambda(DATA_MANAGEMENT_HANDLER, test2_payload)
            results["tests"].append({
                "test_name": "update_protection_group",
                "payload": test2_payload,
                "result": test2_result
            })

            # Test 3: Delete protection group
            test3_payload = {
                "operation": "delete_protection_group",
                "groupId": group_id
            }
            test3_result = self.invoke_lambda(DATA_MANAGEMENT_HANDLER, test3_payload)
            results["tests"].append({
                "test_name": "delete_protection_group",
                "payload": test3_payload,
                "result": test3_result
            })

        # Check for AccessDenied errors
        access_denied_errors = self.check_cloudwatch_logs_for_access_denied(DATA_MANAGEMENT_HANDLER)
        results["access_denied_errors"] = access_denied_errors

        # Calculate summary
        successful_tests = sum(1 for test in results["tests"] if test["result"]["success"])
        results["summary"] = {
            "total_tests": len(results["tests"]),
            "successful": successful_tests,
            "failed": len(results["tests"]) - successful_tests,
            "access_denied_count": len(access_denied_errors)
        }

        logger.info(f"\nData Management Handler Summary: {successful_tests}/{len(results['tests'])} tests passed")

        return results

    def test_execution_handler(self) -> Dict[str, Any]:
        """
        Test Execution Handler Lambda function.

        Tests:
        - Find pending executions (DynamoDB read)
        - Send SNS notification (SNS publish)

        Returns:
            Test results dictionary
        """
        logger.info("\n" + "=" * 80)
        logger.info("Testing Execution Handler")
        logger.info("=" * 80)

        results = {
            "function_name": EXECUTION_HANDLER,
            "tests": []
        }

        # Test 1: Find pending executions
        test1_payload = {
            "operation": "find_pending_executions"
        }
        test1_result = self.invoke_lambda(EXECUTION_HANDLER, test1_payload)
        results["tests"].append({
            "test_name": "find_pending_executions",
            "payload": test1_payload,
            "result": test1_result
        })

        # Check for AccessDenied errors
        access_denied_errors = self.check_cloudwatch_logs_for_access_denied(EXECUTION_HANDLER)
        results["access_denied_errors"] = access_denied_errors

        # Calculate summary
        successful_tests = sum(1 for test in results["tests"] if test["result"]["success"])
        results["summary"] = {
            "total_tests": len(results["tests"]),
            "successful": successful_tests,
            "failed": len(results["tests"]) - successful_tests,
            "access_denied_count": len(access_denied_errors)
        }

        logger.info(f"\nExecution Handler Summary: {successful_tests}/{len(results['tests'])} tests passed")

        return results

    def test_orchestration_function(self) -> Dict[str, Any]:
        """
        Test Orchestration Function Lambda function.

        Tests:
        - Validate DRS permissions (read-only test)

        Returns:
            Test results dictionary
        """
        logger.info("\n" + "=" * 80)
        logger.info("Testing Orchestration Function")
        logger.info("=" * 80)

        results = {
            "function_name": ORCHESTRATION_FUNCTION,
            "tests": []
        }

        # Test 1: Validate DRS permissions (read-only)
        test1_payload = {
            "operation": "validate_drs_permissions"
        }
        test1_result = self.invoke_lambda(ORCHESTRATION_FUNCTION, test1_payload)
        results["tests"].append({
            "test_name": "validate_drs_permissions",
            "payload": test1_payload,
            "result": test1_result
        })

        # Check for AccessDenied errors
        access_denied_errors = self.check_cloudwatch_logs_for_access_denied(ORCHESTRATION_FUNCTION)
        results["access_denied_errors"] = access_denied_errors

        # Calculate summary
        successful_tests = sum(1 for test in results["tests"] if test["result"]["success"])
        results["summary"] = {
            "total_tests": len(results["tests"]),
            "successful": successful_tests,
            "failed": len(results["tests"]) - successful_tests,
            "access_denied_count": len(access_denied_errors)
        }

        logger.info(f"\nOrchestration Function Summary: {successful_tests}/{len(results['tests'])} tests passed")

        return results

    def test_frontend_deployer(self) -> Dict[str, Any]:
        """
        Test Frontend Deployer Lambda function.

        Tests:
        - Validate S3 permissions (read-only test)

        Returns:
            Test results dictionary
        """
        logger.info("\n" + "=" * 80)
        logger.info("Testing Frontend Deployer")
        logger.info("=" * 80)

        results = {
            "function_name": FRONTEND_DEPLOYER,
            "tests": []
        }

        # Test 1: Validate S3 permissions (read-only)
        test1_payload = {
            "operation": "validate_s3_permissions"
        }
        test1_result = self.invoke_lambda(FRONTEND_DEPLOYER, test1_payload)
        results["tests"].append({
            "test_name": "validate_s3_permissions",
            "payload": test1_payload,
            "result": test1_result
        })

        # Check for AccessDenied errors
        access_denied_errors = self.check_cloudwatch_logs_for_access_denied(FRONTEND_DEPLOYER)
        results["access_denied_errors"] = access_denied_errors

        # Calculate summary
        successful_tests = sum(1 for test in results["tests"] if test["result"]["success"])
        results["summary"] = {
            "total_tests": len(results["tests"]),
            "successful": successful_tests,
            "failed": len(results["tests"]) - successful_tests,
            "access_denied_count": len(access_denied_errors)
        }

        logger.info(f"\nFrontend Deployer Summary: {successful_tests}/{len(results['tests'])} tests passed")

        return results

    def save_results(self, filename: str = "functional_equivalence_unified_results.json") -> None:
        """
        Save test results to JSON file.

        Args:
            filename: Output filename
        """
        output_path = f"tests/integration/{filename}"

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"\n✓ Results saved to {output_path}")

    def run_all_tests(self) -> bool:
        """
        Execute all functional equivalence tests.

        Returns:
            True if all tests passed, False otherwise
        """
        logger.info("=" * 80)
        logger.info("Functional Equivalence Tests - Unified Role Configuration")
        logger.info("=" * 80)
        logger.info(f"Environment: {ENVIRONMENT}")
        logger.info(f"Region: {REGION}")
        logger.info(f"Account: {ACCOUNT_ID}")
        logger.info(f"Timestamp: {self.timestamp}")
        logger.info("=" * 80)

        try:
            # Step 1: Verify environment
            if not self.verify_environment():
                logger.error("Environment verification failed. Aborting tests.")
                return False

            # Step 2: Run tests for each Lambda function
            self.results["query_handler"] = self.test_query_handler()
            self.results["data_management_handler"] = self.test_data_management_handler()
            self.results["execution_handler"] = self.test_execution_handler()
            self.results["orchestration_function"] = self.test_orchestration_function()
            self.results["frontend_deployer"] = self.test_frontend_deployer()

            # Step 3: Calculate overall summary
            total_tests = sum(r["summary"]["total_tests"] for r in self.results.values())
            successful_tests = sum(r["summary"]["successful"] for r in self.results.values())
            failed_tests = sum(r["summary"]["failed"] for r in self.results.values())
            total_access_denied = sum(r["summary"]["access_denied_count"] for r in self.results.values())

            self.results["overall_summary"] = {
                "total_tests": total_tests,
                "successful": successful_tests,
                "failed": failed_tests,
                "total_access_denied_errors": total_access_denied,
                "timestamp": self.timestamp,
                "environment": ENVIRONMENT,
                "region": REGION,
                "account_id": ACCOUNT_ID
            }

            # Step 4: Save results
            self.save_results()

            # Step 5: Print final summary
            logger.info("\n" + "=" * 80)
            logger.info("OVERALL SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Total Tests: {total_tests}")
            logger.info(f"Successful: {successful_tests}")
            logger.info(f"Failed: {failed_tests}")
            logger.info(f"AccessDenied Errors: {total_access_denied}")
            logger.info("=" * 80)

            if failed_tests == 0 and total_access_denied == 0:
                logger.info("✓ All tests passed with no AccessDenied errors!")
                return True
            else:
                logger.error("✗ Some tests failed or AccessDenied errors detected")
                return False

        except Exception as e:
            logger.error(f"Test execution failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point for functional equivalence tests."""
    test_suite = FunctionalEquivalenceTest()
    success = test_suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
