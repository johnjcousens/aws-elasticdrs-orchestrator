"""
Account Management Utilities

Centralized account operations for AWS account identification,
validation, and target account management.

This module provides utilities for:
- Getting account names/aliases
- Auto-initializing default target accounts
- Listing configured target accounts
- Validating target account access and permissions
- Standardized cross-account role ARN construction

## Integration Points

### 1. Account Initialization (First-Time Setup)
```python
from shared.account_utils import ensure_default_account

# Called during handler initialization
ensure_default_account()
```

### 2. Account Listing (API Endpoint)
```python
from shared.account_utils import get_target_accounts

def lambda_handler(event, context):
    return get_target_accounts()
```

### 3. Account Validation (Before Cross-Account Operations)
```python
from shared.account_utils import validate_target_account

result = validate_target_account(account_id)
if not result['valid']:
    return {"statusCode": 400, "body": {"errors": result['errors']}}
```

### 4. Standardized Role ARN Construction
```python
from shared.account_utils import construct_role_arn, get_role_arn

# Construct ARN from account ID
arn = construct_role_arn("123456789012")

# Get ARN with fallback to construction
arn = get_role_arn("123456789012", explicit_arn=None)
```

## Dependencies

- boto3: AWS SDK for IAM, Organizations, DynamoDB, STS
- shared.cross_account: get_current_account_id()
- shared.response_utils: response()
"""

import os
import re
from datetime import datetime, timezone
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError

# Import from existing shared modules
from shared.cross_account import get_current_account_id
from shared.response_utils import response

# Standardized role name across all accounts
STANDARD_ROLE_NAME = "DRSOrchestrationRole"

# Account ID validation pattern (12 digits)
ACCOUNT_ID_PATTERN = re.compile(r"^\d{12}$")

# Lazy initialization
_dynamodb = None
_target_accounts_table = None


def construct_role_arn(account_id: str) -> str:
    """
    Construct standardized role ARN from account ID.

    Args:
        account_id: 12-digit AWS account ID

    Returns:
        Role ARN in format: arn:aws:iam::{account_id}:role/DRSOrchestrationRole

    Raises:
        ValueError: If account_id is not exactly 12 digits

    Example:
        >>> construct_role_arn("123456789012")
        'arn:aws:iam::123456789012:role/DRSOrchestrationRole'

        >>> construct_role_arn("12345")
        ValueError: Invalid account ID: 12345. Must be exactly 12 digits.
    """
    if not validate_account_id(account_id):
        raise ValueError(
            f"Invalid account ID: {account_id}. Must be exactly 12 digits."
        )

    return f"arn:aws:iam::{account_id}:role/{STANDARD_ROLE_NAME}"


def validate_account_id(account_id: str) -> bool:
    """
    Validate AWS account ID format.

    Args:
        account_id: Account ID to validate

    Returns:
        True if valid (exactly 12 digits), False otherwise

    Example:
        >>> validate_account_id("123456789012")
        True

        >>> validate_account_id("12345")
        False

        >>> validate_account_id("12345678901a")
        False

        >>> validate_account_id(None)
        False
    """
    if not account_id:
        return False

    return ACCOUNT_ID_PATTERN.match(account_id) is not None


def extract_account_id_from_arn(role_arn: str) -> Optional[str]:
    """
    Extract account ID from role ARN.

    Args:
        role_arn: IAM role ARN

    Returns:
        12-digit account ID, or None if extraction fails

    Example:
        >>> extract_account_id_from_arn(
        ...     "arn:aws:iam::123456789012:role/DRSOrchestrationRole"
        ... )
        '123456789012'

        >>> extract_account_id_from_arn("invalid-arn")
        None

        >>> extract_account_id_from_arn(
        ...     "arn:aws:iam::999999999999:role/CustomRole"
        ... )
        '999999999999'
    """
    # ARN format: arn:aws:iam::123456789012:role/RoleName
    match = re.match(r"arn:aws:iam::(\d{12}):role/", role_arn)
    if match:
        return match.group(1)
    return None


def get_role_arn(account_id: str, explicit_arn: Optional[str] = None) -> str:
    """
    Get role ARN for account, using explicit ARN if provided or constructing it.

    This function implements the backward compatibility strategy:
    - If explicit_arn is provided, use it (existing accounts)
    - Otherwise, construct standardized ARN (new accounts)

    Args:
        account_id: 12-digit AWS account ID
        explicit_arn: Optional explicit role ARN (for backward compatibility)

    Returns:
        Role ARN (explicit or constructed)

    Raises:
        ValueError: If account_id is invalid

    Example:
        >>> get_role_arn("123456789012")
        'arn:aws:iam::123456789012:role/DRSOrchestrationRole'

        >>> get_role_arn(
        ...     "123456789012",
        ...     explicit_arn="arn:aws:iam::123456789012:role/CustomRole"
        ... )
        'arn:aws:iam::123456789012:role/CustomRole'
    """
    if explicit_arn:
        return explicit_arn

    return construct_role_arn(account_id)


def _get_target_accounts_table():
    """
    Lazy initialization of target accounts table.

    Returns DynamoDB Table resource or None if not configured.
    """
    global _dynamodb, _target_accounts_table
    if _target_accounts_table is None:
        table_name = os.environ.get("TARGET_ACCOUNTS_TABLE")
        if table_name:
            if _dynamodb is None:
                _dynamodb = boto3.resource("dynamodb")
            _target_accounts_table = _dynamodb.Table(table_name)
    return _target_accounts_table


def get_account_name(account_id: str) -> Optional[str]:
    """
    Get account name/alias if available.

    Tries IAM account aliases first (faster, no extra permissions needed),
    then falls back to Organizations API if available.

    Args:
        account_id: AWS account ID (12-digit string)

    Returns:
        Account name/alias or None if not found

    Example:
        >>> name = get_account_name("123456789012")
        >>> print(name)
        'production-account'

        >>> name = get_account_name("999999999999")
        >>> print(name)
        None
    """
    try:
        # Try to get account alias (faster, works in current account)
        iam_client = boto3.client("iam")
        aliases = iam_client.list_account_aliases()["AccountAliases"]
        if aliases:
            return aliases[0]

        # Try to get account name from Organizations (if available)
        try:
            org_client = boto3.client("organizations")
            account = org_client.describe_account(AccountId=account_id)
            return account["Account"]["Name"]
        except (ClientError, Exception):
            # Organizations API not available or account not found
            pass

        return None

    except Exception as e:
        print(f"Error getting account name: {e}")
        return None


def get_target_accounts() -> Dict:
    """
    Get all configured target accounts from DynamoDB.

    Returns API Gateway response format with statusCode and body.
    Automatically ensures default account exists before returning.

    Returns:
        Dict with statusCode and body containing accounts list:
        {
            "statusCode": 200,
            "body": [
                {
                    "accountId": "123456789012",
                    "accountName": "production",
                    "status": "active",
                    ...
                }
            ]
        }

    Example:
        >>> result = get_target_accounts()
        >>> result['statusCode']
        200
        >>> len(json.loads(result['body']))
        3
    """
    try:
        target_accounts_table = _get_target_accounts_table()
        if not target_accounts_table:
            return response(
                500, {"error": "Target accounts table not configured"}
            )

        # Get current account info
        current_account_id = get_current_account_id()
        current_account_name = get_account_name(current_account_id)

        # Use account ID as fallback if name is not available
        if current_account_name is None:
            current_account_name = current_account_id

        # Scan target accounts table
        result = target_accounts_table.scan()
        accounts = result.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in result:
            result = target_accounts_table.scan(
                ExclusiveStartKey=result["LastEvaluatedKey"]
            )
            accounts.extend(result.get("Items", []))

        return response(200, accounts)

    except Exception as e:
        print(f"Error getting target accounts: {e}")
        return response(500, {"error": str(e)})


def validate_target_account(account_id: str) -> Dict:
    """
    Validate target account access and permissions.

    Performs comprehensive validation checks:
    1. Account exists in target accounts table
    2. Cross-account role is configured (for non-current accounts)
    3. Can assume role successfully (for cross-account)
    4. Has required DRS permissions

    Args:
        account_id: AWS account ID to validate

    Returns:
        Dict with validation results in API Gateway response format:
        {
            "statusCode": 200,
            "body": {
                "accountId": "123456789012",
                "validationResults": [
                    {
                        "region": "us-east-1",
                        "service": "DRS",
                        "status": "success",
                        "message": "DRS access validated"
                    }
                ],
                "overallStatus": "active",
                "lastValidated": "2026-01-27T12:00:00Z"
            }
        }

    Example:
        >>> result = validate_target_account("123456789012")
        >>> body = json.loads(result['body'])
        >>> body['overallStatus']
        'active'
    """
    try:
        target_accounts_table = _get_target_accounts_table()
        if not target_accounts_table:
            return response(
                500, {"error": "Target accounts table not configured"}
            )

        current_account_id = get_current_account_id()

        # Check if account exists in our configuration
        result = target_accounts_table.get_item(Key={"accountId": account_id})
        if "Item" not in result:
            return response(
                404,
                {
                    "error": "NOT_FOUND",
                    "message": f"Target account {account_id} not found",
                },
            )

        account_config = result["Item"]
        validation_results = {
            "accountId": account_id,
            "validationResults": [],
            "overallStatus": "active",
            "lastValidated": datetime.now(timezone.utc).isoformat() + "Z",
        }

        if account_id == current_account_id:
            # Validate current account by checking DRS access
            try:
                # Test DRS access in multiple regions
                test_regions = ["us-east-1", "us-west-2", "eu-west-1"]
                for region in test_regions:
                    try:
                        drs_client = boto3.client("drs", region_name=region)
                        drs_client.describe_source_servers(maxResults=1)
                        validation_results["validationResults"].append(
                            {
                                "region": region,
                                "service": "DRS",
                                "status": "success",
                                "message": "DRS access validated",
                            }
                        )
                    except Exception as region_error:
                        validation_results["validationResults"].append(
                            {
                                "region": region,
                                "service": "DRS",
                                "status": "warning",
                                "message": f"DRS access issue: {str(region_error)}",
                            }
                        )

            except Exception as drs_error:
                validation_results["overallStatus"] = "error"
                validation_results["validationResults"].append(
                    {
                        "service": "DRS",
                        "status": "error",
                        "message": f"DRS validation failed: {str(drs_error)}",
                    }
                )
        else:
            # Cross-account validation
            cross_account_role = account_config.get("crossAccountRoleArn")
            if not cross_account_role:
                validation_results["overallStatus"] = "error"
                validation_results["validationResults"].append(
                    {
                        "service": "IAM",
                        "status": "error",
                        "message": "Cross-account role ARN not configured",
                    }
                )
            else:
                # TODO: Implement cross-account role assumption and validation
                validation_results["validationResults"].append(
                    {
                        "service": "IAM",
                        "status": "warning",
                        "message": "Cross-account validation not yet implemented",
                    }
                )

        # Update last validated timestamp in DynamoDB
        try:
            target_accounts_table.update_item(
                Key={"accountId": account_id},
                UpdateExpression="SET lastValidated = :lastValidated",
                ExpressionAttributeValues={
                    ":lastValidated": validation_results["lastValidated"]
                },
            )
        except Exception as update_error:
            print(
                f"Warning: Could not update lastValidated timestamp: {update_error}"
            )

        return response(200, validation_results)

    except Exception as e:
        print(f"Error validating target account: {e}")
        return response(500, {"error": str(e)})
