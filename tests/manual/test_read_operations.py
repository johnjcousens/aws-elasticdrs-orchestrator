#!/usr/bin/env python3
"""
Test Read Operations - Query Handler Read-Only Audit Task 6.3

Verifies all read operations still work after refactoring to make
query-handler strictly read-only.

Tests:
1. list_executions - List all recovery plan executions
2. get_drs_source_servers - Query DRS source servers
3. get_current_account_id - Get current AWS account
4. get_target_accounts - List target accounts
5. get_ec2_subnets - Query EC2 subnets
6. get_ec2_security_groups - Query security groups
7. get_ec2_instance_types - List instance types
8. get_ec2_instance_profiles - List IAM instance profiles
9. export_configuration - Export protection groups and recovery plans
10. get_drs_account_capacity_all_regions - Get DRS capacity metrics
"""

import json
import sys
from typing import Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

# Configuration
REGION = "us-east-1"
ACCOUNT_ID = "438465159935"
LAMBDA_FUNCTION_NAME = "aws-drs-orchestration-query-handler-qa"

# Test results
tests_passed = 0
tests_failed = 0
tests_skipped = 0
test_results = []


class Colors:
    """ANSI color codes for terminal output"""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_header(text: str) -> None:
    """Print section header"""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{text}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")


def print_test_header(test_name: str) -> None:
    """Print test header"""
    print(f"\n{Colors.BLUE}{'-' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}Test: {test_name}{Colors.NC}")
    print(f"{Colors.BLUE}{'-' * 60}{Colors.NC}")


def print_test_result(
    test_name: str, status: str, details: str = "", response_data: Optional[Dict] = None
) -> None:
    """Print test result"""
    global tests_passed, tests_failed, tests_skipped, test_results

    if status == "PASS":
        print(f"{Colors.GREEN}✓ PASS{Colors.NC}: {test_name}")
        tests_passed += 1
    elif status == "FAIL":
        print(f"{Colors.RED}✗ FAIL{Colors.NC}: {test_name}")
        if details:
            print(f"{Colors.RED}  Details: {details}{Colors.NC}")
        tests_failed += 1
    elif status == "SKIP":
        print(f"{Colors.YELLOW}⊘ SKIP{Colors.NC}: {test_name} - {details}")
        tests_skipped += 1

    # Store result
    test_results.append(
        {
            "test_name": test_name,
            "status": status,
            "details": details,
            "response_data": response_data,
        }
    )

    print()


def check_authentication() -> bool:
    """Check if AWS credentials are configured"""
    print_test_header("Authentication Check")

    try:
        sts = boto3.client("sts", region_name=REGION)
        identity = sts.get_caller_identity()

        current_account = identity["Account"]
        current_arn = identity["Arn"]

        print("Current AWS Identity:")
        print(f"  Account: {current_account}")
        print(f"  ARN: {current_arn}")
        print()

        if current_account != ACCOUNT_ID:
            print(
                f"{Colors.YELLOW}WARNING: Current account ({current_account}) "
                f"does not match expected account ({ACCOUNT_ID}){Colors.NC}\n"
            )

        print_test_result("AWS Credentials", "PASS")
        return True

    except Exception as e:
        print(f"{Colors.RED}ERROR: AWS credentials not configured{Colors.NC}")
        print(f"Details: {e}")
        print_test_result("AWS Credentials", "FAIL", str(e))
        return False


def invoke_lambda(operation: str, query_params: Dict) -> Tuple[bool, Optional[Dict], str]:
    """
    Invoke Lambda function with operation and query parameters

    Returns:
        Tuple of (success, response_data, error_message)
    """
    try:
        lambda_client = boto3.client("lambda", region_name=REGION)

        payload = {"operation": operation, "queryParams": query_params}

        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )

        # Parse response
        response_payload = json.loads(response["Payload"].read())

        # Check for Lambda errors
        if "errorType" in response_payload:
            error_type = response_payload.get("errorType", "Unknown")
            error_message = response_payload.get("errorMessage", "Unknown error")
            return False, None, f"Lambda error: {error_type} - {error_message}"

        # Check for HTTP errors
        if "statusCode" in response_payload:
            status_code = response_payload["statusCode"]
            if status_code != 200:
                body = response_payload.get("body", "Unknown error")
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except json.JSONDecodeError:
                        pass
                return False, None, f"HTTP {status_code}: {body}"

            # Parse body if it's a string
            body = response_payload.get("body", {})
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    pass

            return True, body, ""

        # Direct response (no statusCode wrapper)
        return True, response_payload, ""

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        return False, None, f"AWS error: {error_code} - {error_message}"

    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"


def test_list_executions() -> None:
    """Test list_executions operation"""
    print_test_header("List Executions")

    success, data, error = invoke_lambda("list_executions", {})

    if not success:
        print_test_result("List Executions", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("List Executions", "FAIL", "Response is not a dictionary")
        return

    if "executions" not in data:
        print_test_result("List Executions", "FAIL", "Response missing 'executions' field")
        return

    executions = data["executions"]
    print(f"Found {len(executions)} executions")

    if executions:
        print("\nSample execution:")
        print(json.dumps(executions[0], indent=2, default=str)[:500])

    print_test_result("List Executions", "PASS", response_data=data)


def test_get_drs_source_servers() -> None:
    """Test get_drs_source_servers operation"""
    print_test_header("Get DRS Source Servers")

    success, data, error = invoke_lambda("get_drs_source_servers", {"region": REGION})

    if not success:
        print_test_result("Get DRS Source Servers", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("Get DRS Source Servers", "FAIL", "Response is not a dictionary")
        return

    if "servers" not in data:
        print_test_result("Get DRS Source Servers", "FAIL", "Response missing 'servers' field")
        return

    servers = data["servers"]
    print(f"Found {len(servers)} DRS source servers")

    if servers:
        print("\nSample server:")
        print(json.dumps(servers[0], indent=2, default=str)[:500])

    print_test_result("Get DRS Source Servers", "PASS", response_data=data)


def test_get_current_account() -> None:
    """Test get_current_account_id operation"""
    print_test_header("Get Current Account")

    success, data, error = invoke_lambda("get_current_account_id", {})

    if not success:
        print_test_result("Get Current Account", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("Get Current Account", "FAIL", "Response is not a dictionary")
        return

    if "accountId" not in data:
        print_test_result("Get Current Account", "FAIL", "Response missing 'accountId' field")
        return

    account_id = data["accountId"]
    print(f"Current Account ID: {account_id}")

    print_test_result("Get Current Account", "PASS", response_data=data)


def test_get_target_accounts() -> None:
    """Test get_target_accounts operation"""
    print_test_header("Get Target Accounts")

    success, data, error = invoke_lambda("get_target_accounts", {})

    if not success:
        print_test_result("Get Target Accounts", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("Get Target Accounts", "FAIL", "Response is not a dictionary")
        return

    if "accounts" not in data:
        print_test_result("Get Target Accounts", "FAIL", "Response missing 'accounts' field")
        return

    accounts = data["accounts"]
    print(f"Found {len(accounts)} target accounts")

    if accounts:
        print("\nSample account:")
        print(json.dumps(accounts[0], indent=2, default=str)[:500])

    print_test_result("Get Target Accounts", "PASS", response_data=data)


def test_get_ec2_subnets() -> None:
    """Test get_ec2_subnets operation"""
    print_test_header("Get EC2 Subnets")

    # First, get a VPC ID
    try:
        ec2 = boto3.client("ec2", region_name=REGION)
        vpcs = ec2.describe_vpcs()

        if not vpcs["Vpcs"]:
            print_test_result("Get EC2 Subnets", "SKIP", "No VPCs found in region")
            return

        vpc_id = vpcs["Vpcs"][0]["VpcId"]
        print(f"Using VPC: {vpc_id}")

    except Exception as e:
        print_test_result("Get EC2 Subnets", "SKIP", f"Could not get VPC ID: {e}")
        return

    success, data, error = invoke_lambda("get_ec2_subnets", {"region": REGION, "vpcId": vpc_id})

    if not success:
        print_test_result("Get EC2 Subnets", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("Get EC2 Subnets", "FAIL", "Response is not a dictionary")
        return

    if "subnets" not in data:
        print_test_result("Get EC2 Subnets", "FAIL", "Response missing 'subnets' field")
        return

    subnets = data["subnets"]
    print(f"Found {len(subnets)} subnets")

    if subnets:
        print("\nSample subnet:")
        print(json.dumps(subnets[0], indent=2, default=str)[:500])

    print_test_result("Get EC2 Subnets", "PASS", response_data=data)


def test_get_ec2_security_groups() -> None:
    """Test get_ec2_security_groups operation"""
    print_test_header("Get EC2 Security Groups")

    # First, get a VPC ID
    try:
        ec2 = boto3.client("ec2", region_name=REGION)
        vpcs = ec2.describe_vpcs()

        if not vpcs["Vpcs"]:
            print_test_result("Get EC2 Security Groups", "SKIP", "No VPCs found in region")
            return

        vpc_id = vpcs["Vpcs"][0]["VpcId"]
        print(f"Using VPC: {vpc_id}")

    except Exception as e:
        print_test_result("Get EC2 Security Groups", "SKIP", f"Could not get VPC ID: {e}")
        return

    success, data, error = invoke_lambda(
        "get_ec2_security_groups", {"region": REGION, "vpcId": vpc_id}
    )

    if not success:
        print_test_result("Get EC2 Security Groups", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("Get EC2 Security Groups", "FAIL", "Response is not a dictionary")
        return

    if "securityGroups" not in data:
        print_test_result(
            "Get EC2 Security Groups", "FAIL", "Response missing 'securityGroups' field"
        )
        return

    security_groups = data["securityGroups"]
    print(f"Found {len(security_groups)} security groups")

    if security_groups:
        print("\nSample security group:")
        print(json.dumps(security_groups[0], indent=2, default=str)[:500])

    print_test_result("Get EC2 Security Groups", "PASS", response_data=data)


def test_get_ec2_instance_types() -> None:
    """Test get_ec2_instance_types operation"""
    print_test_header("Get EC2 Instance Types")

    success, data, error = invoke_lambda("get_ec2_instance_types", {"region": REGION})

    if not success:
        print_test_result("Get EC2 Instance Types", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("Get EC2 Instance Types", "FAIL", "Response is not a dictionary")
        return

    if "instanceTypes" not in data:
        print_test_result("Get EC2 Instance Types", "FAIL", "Response missing 'instanceTypes' field")
        return

    instance_types = data["instanceTypes"]
    print(f"Found {len(instance_types)} instance types")

    if instance_types:
        print("\nSample instance types:")
        print(json.dumps(instance_types[:5], indent=2, default=str))

    print_test_result("Get EC2 Instance Types", "PASS", response_data=data)


def test_get_ec2_instance_profiles() -> None:
    """Test get_ec2_instance_profiles operation"""
    print_test_header("Get EC2 Instance Profiles")

    success, data, error = invoke_lambda("get_ec2_instance_profiles", {"region": REGION})

    if not success:
        print_test_result("Get EC2 Instance Profiles", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("Get EC2 Instance Profiles", "FAIL", "Response is not a dictionary")
        return

    if "instanceProfiles" not in data:
        print_test_result(
            "Get EC2 Instance Profiles", "FAIL", "Response missing 'instanceProfiles' field"
        )
        return

    instance_profiles = data["instanceProfiles"]
    print(f"Found {len(instance_profiles)} instance profiles")

    if instance_profiles:
        print("\nSample instance profiles:")
        print(json.dumps(instance_profiles[:3], indent=2, default=str))

    print_test_result("Get EC2 Instance Profiles", "PASS", response_data=data)


def test_export_configuration() -> None:
    """Test export_configuration operation"""
    print_test_header("Export Configuration")

    success, data, error = invoke_lambda("export_configuration", {})

    if not success:
        print_test_result("Export Configuration", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("Export Configuration", "FAIL", "Response is not a dictionary")
        return

    if "protectionGroups" not in data or "recoveryPlans" not in data:
        print_test_result(
            "Export Configuration",
            "FAIL",
            "Response missing 'protectionGroups' or 'recoveryPlans' field",
        )
        return

    protection_groups = data["protectionGroups"]
    recovery_plans = data["recoveryPlans"]

    print(f"Exported {len(protection_groups)} protection groups")
    print(f"Exported {len(recovery_plans)} recovery plans")

    print_test_result("Export Configuration", "PASS", response_data=data)


def test_get_drs_capacity() -> None:
    """Test get_drs_account_capacity_all_regions operation"""
    print_test_header("Get DRS Account Capacity (All Regions)")

    success, data, error = invoke_lambda("get_drs_account_capacity_all_regions", {})

    if not success:
        print_test_result("Get DRS Account Capacity", "FAIL", error)
        return

    # Validate response structure
    if not isinstance(data, dict):
        print_test_result("Get DRS Account Capacity", "FAIL", "Response is not a dictionary")
        return

    if "regions" not in data:
        print_test_result("Get DRS Account Capacity", "FAIL", "Response missing 'regions' field")
        return

    regions = data["regions"]
    print(f"Found capacity data for {len(regions)} regions")

    if regions:
        print("\nSample region capacity:")
        print(json.dumps(regions[0], indent=2, default=str)[:500])

    print_test_result("Get DRS Account Capacity", "PASS", response_data=data)


def print_summary() -> None:
    """Print test summary"""
    print_header("Test Summary")

    total_tests = tests_passed + tests_failed + tests_skipped

    print(f"{Colors.GREEN}Passed: {tests_passed}{Colors.NC}")
    print(f"{Colors.RED}Failed: {tests_failed}{Colors.NC}")
    print(f"{Colors.YELLOW}Skipped: {tests_skipped}{Colors.NC}")
    print(f"{Colors.BLUE}Total: {total_tests}{Colors.NC}")
    print()

    if tests_failed > 0:
        print(f"{Colors.RED}Some tests failed. Please review the output above.{Colors.NC}")
        return False
    else:
        print(f"{Colors.GREEN}All tests passed!{Colors.NC}")
        return True


def main() -> int:
    """Main test execution"""
    print_header("Query Handler Read Operations Test\nTask 6.3 - Read-Only Audit Verification")

    print(f"Region: {REGION}")
    print(f"Account: {ACCOUNT_ID}")
    print(f"Lambda Function: {LAMBDA_FUNCTION_NAME}")
    print()

    # Check authentication
    if not check_authentication():
        print(f"{Colors.RED}Authentication failed. Exiting.{Colors.NC}")
        return 1

    # Run all tests
    test_list_executions()
    test_get_drs_source_servers()
    test_get_current_account()
    test_get_target_accounts()
    test_get_ec2_subnets()
    test_get_ec2_security_groups()
    test_get_ec2_instance_types()
    test_get_ec2_instance_profiles()
    test_export_configuration()
    test_get_drs_capacity()

    # Print summary
    success = print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
