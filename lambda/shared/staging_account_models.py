"""
Staging Account Data Models and DynamoDB Operations

This module provides data classes and DynamoDB helper functions for managing
staging accounts in the DR Orchestration Platform.

STAGING ACCOUNTS OVERVIEW:
- Extend DRS replication capacity beyond 300-server limit of single account
- Each staging account provides additional 300 servers of capacity
- Stored as list attribute in Target Accounts DynamoDB table
- Support cross-account DRS operations via IAM role assumption

DATA MODELS:
- StagingAccount: Individual staging account configuration
- TargetAccount: Target account with staging accounts list

CRUD OPERATIONS:
- add_staging_account(): Add staging account to target account
- remove_staging_account(): Remove staging account from target account
- get_staging_accounts(): Get all staging accounts for target account
- update_staging_accounts(): Update entire staging accounts list

VALIDATION:
- validate_staging_account_structure(): Validate staging account dict
- check_duplicate_staging_account(): Check if staging account exists

INTEGRATION POINTS:
- Data Management Lambda: add/remove operations
- Query Lambda: capacity queries across multiple accounts
- DynamoDB: Target Accounts table with stagingAccounts attribute

REQUIREMENTS VALIDATED:
- 8.1: Store staging account configuration in DynamoDB
- 8.2: Include account ID, name, role ARN, external ID
- 8.3: Retrieve staging accounts from stagingAccounts attribute
- 8.4: Update stagingAccounts attribute on add/remove
- 8.5: Default to empty list if stagingAccounts doesn't exist
"""

import os
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Lazy initialization
_dynamodb = None
_target_accounts_table = None


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


@dataclass
class StagingAccount:
    """
    Staging account configuration.

    Represents an additional AWS account configured to provide extended
    DRS replication capacity for a target account.

    Attributes:
        accountId: AWS account ID (12-digit string)
        accountName: Human-readable name for the staging account
        roleArn: IAM role ARN for cross-account access
        externalId: External ID for role assumption security
        addedAt: ISO 8601 timestamp when staging account was added
        addedBy: User/system that added the staging account
    """

    accountId: str
    accountName: str
    roleArn: str
    externalId: str
    addedAt: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z")
    addedBy: str = "system"

    def to_dict(self) -> Dict:
        """Convert to dictionary for DynamoDB storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "StagingAccount":
        """Create StagingAccount from dictionary."""
        return cls(
            accountId=data["accountId"],
            accountName=data["accountName"],
            roleArn=data["roleArn"],
            externalId=data["externalId"],
            addedAt=data.get("addedAt", datetime.now(timezone.utc).isoformat() + "Z"),
            addedBy=data.get("addedBy", "system"),
        )


@dataclass
class TargetAccount:
    """
    Target account with staging accounts configuration.

    Represents the primary AWS account where DRS recovery operations are
    performed, along with any configured staging accounts for extended
    capacity.

    Attributes:
        accountId: AWS account ID (12-digit string)
        accountName: Human-readable name for the target account
        roleArn: IAM role ARN for cross-account access (optional)
        externalId: External ID for role assumption (optional)
        stagingAccounts: List of staging account configurations
        status: Account status (active, inactive, error)
        createdAt: ISO 8601 timestamp when account was created
        updatedAt: ISO 8601 timestamp when account was last updated
        createdBy: User/system that created the account
    """

    accountId: str
    accountName: str
    roleArn: Optional[str] = None
    externalId: Optional[str] = None
    stagingAccounts: List[StagingAccount] = field(default_factory=list)
    status: str = "active"
    createdAt: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z")
    updatedAt: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z")
    createdBy: str = "system"

    def to_dict(self) -> Dict:
        """Convert to dictionary for DynamoDB storage."""
        data = asdict(self)
        # Convert StagingAccount objects to dicts
        data["stagingAccounts"] = [
            (account.to_dict() if isinstance(account, StagingAccount) else account) for account in self.stagingAccounts
        ]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "TargetAccount":
        """Create TargetAccount from dictionary."""
        staging_accounts = [
            (StagingAccount.from_dict(account) if isinstance(account, dict) else account)
            for account in data.get("stagingAccounts", [])
        ]

        return cls(
            accountId=data["accountId"],
            accountName=data["accountName"],
            roleArn=data.get("roleArn"),
            externalId=data.get("externalId"),
            stagingAccounts=staging_accounts,
            status=data.get("status", "active"),
            createdAt=data.get("createdAt", datetime.now(timezone.utc).isoformat() + "Z"),
            updatedAt=data.get("updatedAt", datetime.now(timezone.utc).isoformat() + "Z"),
            createdBy=data.get("createdBy", "system"),
        )


def validate_staging_account_structure(staging_account: Dict) -> Dict:
    """
    Validate staging account structure and required fields.

    Checks that all required fields are present and have valid formats:
    - accountId: 12-digit string
    - accountName: non-empty string
    - roleArn: valid IAM role ARN format (optional - will be constructed if not provided)
    - externalId: non-empty string

    Args:
        staging_account: Dictionary with staging account data

    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "errors": List[str]  # Empty if valid
        }

    Example:
        >>> result = validate_staging_account_structure({
        ...     "accountId": "123456789012",
        ...     "accountName": "STAGING_01",
        ...     "roleArn": "arn:aws:iam::123456789012:role/DRSRole",
        ...     "externalId": "external-id-123"
        ... })
        >>> result["valid"]
        True
    """
    errors = []

    # Check required fields (roleArn is now optional)
    required_fields = ["accountId", "accountName", "externalId"]
    for req_field in required_fields:
        if req_field not in staging_account:
            errors.append(f"Missing required field: {req_field}")
        elif not staging_account[req_field]:
            errors.append(f"Field cannot be empty: {req_field}")

    # Validate account ID format (12 digits)
    account_id = staging_account.get("accountId", "")
    if account_id and (not account_id.isdigit() or len(account_id) != 12):
        errors.append(f"Invalid account ID format: {account_id}. " "Must be 12-digit string.")

    # Validate role ARN format if provided
    role_arn = staging_account.get("roleArn", "")
    if role_arn and not role_arn.startswith("arn:aws:iam::"):
        errors.append(f"Invalid role ARN format: {role_arn}. " "Must start with 'arn:aws:iam::'.")

    return {"valid": len(errors) == 0, "errors": errors}


def check_duplicate_staging_account(target_account_id: str, staging_account_id: str) -> bool:
    """
    Check if staging account already exists for target account.

    Args:
        target_account_id: Target account ID
        staging_account_id: Staging account ID to check

    Returns:
        True if staging account already exists, False otherwise

    Raises:
        ClientError: If DynamoDB operation fails
    """
    table = _get_target_accounts_table()
    if not table:
        raise ValueError("Target accounts table not configured")

    try:
        response = table.get_item(Key={"accountId": target_account_id})

        if "Item" not in response:
            return False

        staging_accounts = response["Item"].get("stagingAccounts", [])

        # Check if staging account ID already exists
        for account in staging_accounts:
            if account.get("accountId") == staging_account_id:
                return True

        return False

    except ClientError as e:
        print(f"Error checking duplicate staging account: {e}")
        raise


def get_staging_accounts(target_account_id: str) -> List[StagingAccount]:
    """
    Get all staging accounts for a target account.

    Retrieves the stagingAccounts attribute from the Target Accounts table.
    Returns empty list if attribute doesn't exist (Requirement 8.5).

    Args:
        target_account_id: Target account ID

    Returns:
        List of StagingAccount objects (empty if none configured)

    Raises:
        ValueError: If target account not found
        ClientError: If DynamoDB operation fails

    Example:
        >>> staging_accounts = get_staging_accounts("123456789012")
        >>> len(staging_accounts)
        2
        >>> staging_accounts[0].accountName
        'STAGING_01'
    """
    table = _get_target_accounts_table()
    if not table:
        raise ValueError("Target accounts table not configured")

    try:
        response = table.get_item(Key={"accountId": target_account_id})

        if "Item" not in response:
            raise ValueError(f"Target account {target_account_id} not found")

        # Get stagingAccounts attribute, default to empty list if not present
        staging_accounts_data = response["Item"].get("stagingAccounts", [])

        # Convert to StagingAccount objects
        return [StagingAccount.from_dict(account) for account in staging_accounts_data]

    except ClientError as e:
        print(f"Error getting staging accounts: {e}")
        raise


def add_staging_account(target_account_id: str, staging_account: Dict, added_by: str = "system") -> Dict:
    """
    Add staging account to target account configuration.

    Validates staging account structure, checks for duplicates, and updates
    the Target Accounts table with the new staging account.

    Args:
        target_account_id: Target account ID
        staging_account: Dict with staging account data
        added_by: User/system adding the staging account

    Returns:
        Dict with operation results:
        {
            "success": bool,
            "message": str,
            "stagingAccounts": List[Dict]  # Updated list
        }

    Raises:
        ValueError: If validation fails or target account not found
        ClientError: If DynamoDB operation fails

    Example:
        >>> result = add_staging_account(
        ...     "123456789012",
        ...     {
        ...         "accountId": "444455556666",
        ...         "accountName": "STAGING_01",
        ...         "roleArn": "arn:aws:iam::444455556666:role/DRSRole",
        ...         "externalId": "external-id-123"
        ...     }
        ... )
        >>> result["success"]
        True
    """
    table = _get_target_accounts_table()
    if not table:
        raise ValueError("Target accounts table not configured")

    # Construct roleArn if not provided
    if not staging_account.get("roleArn"):
        from shared.account_utils import construct_role_arn

        staging_account["roleArn"] = construct_role_arn(staging_account["accountId"])
        print(
            f"Constructed standardized role ARN for staging account "
            f"{staging_account['accountId']}: {staging_account['roleArn']}"
        )
    else:
        print(
            f"Using provided role ARN for staging account "
            f"{staging_account['accountId']}: {staging_account['roleArn']}"
        )

    # Validate staging account structure
    validation = validate_staging_account_structure(staging_account)
    if not validation["valid"]:
        raise ValueError(f"Invalid staging account: {', '.join(validation['errors'])}")

    # Check for duplicate
    if check_duplicate_staging_account(target_account_id, staging_account["accountId"]):
        raise ValueError(
            f"Staging account {staging_account['accountId']} " f"already exists for target account {target_account_id}"
        )

    # Create StagingAccount object
    staging_obj = StagingAccount(
        accountId=staging_account["accountId"],
        accountName=staging_account["accountName"],
        roleArn=staging_account["roleArn"],
        externalId=staging_account["externalId"],
        addedBy=added_by,
    )

    try:
        # Get current staging accounts
        current_staging = get_staging_accounts(target_account_id)

        # Add new staging account
        current_staging.append(staging_obj)

        # Convert to dicts for DynamoDB
        staging_dicts = [account.to_dict() for account in current_staging]

        # Update DynamoDB
        now = datetime.now(timezone.utc).isoformat() + "Z"
        response = table.update_item(
            Key={"accountId": target_account_id},
            UpdateExpression=("SET stagingAccounts = :staging, updatedAt = :updated"),
            ExpressionAttributeValues={
                ":staging": staging_dicts,
                ":updated": now,
            },
            ConditionExpression="attribute_exists(accountId)",
            ReturnValues="ALL_NEW",
        )

        updated_staging = response["Attributes"].get("stagingAccounts", [])

        return {
            "success": True,
            "message": (f"Added staging account {staging_account['accountName']}"),
            "stagingAccounts": updated_staging,
        }

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ValueError(f"Target account {target_account_id} not found")
        print(f"Error adding staging account: {e}")
        raise


def remove_staging_account(target_account_id: str, staging_account_id: str) -> Dict:
    """
    Remove staging account from target account configuration.

    Args:
        target_account_id: Target account ID
        staging_account_id: Staging account ID to remove

    Returns:
        Dict with operation results:
        {
            "success": bool,
            "message": str,
            "stagingAccounts": List[Dict]  # Updated list
        }

    Raises:
        ValueError: If target account or staging account not found
        ClientError: If DynamoDB operation fails

    Example:
        >>> result = remove_staging_account(
        ...     "123456789012",
        ...     "444455556666"
        ... )
        >>> result["success"]
        True
    """
    table = _get_target_accounts_table()
    if not table:
        raise ValueError("Target accounts table not configured")

    try:
        # Get current staging accounts
        current_staging = get_staging_accounts(target_account_id)

        # Find and remove staging account
        staging_found = False
        updated_staging = []
        removed_name = ""

        for account in current_staging:
            if account.accountId == staging_account_id:
                staging_found = True
                removed_name = account.accountName
            else:
                updated_staging.append(account)

        if not staging_found:
            raise ValueError(
                f"Staging account {staging_account_id} not found " f"for target account {target_account_id}"
            )

        # Convert to dicts for DynamoDB
        staging_dicts = [account.to_dict() for account in updated_staging]

        # Update DynamoDB
        now = datetime.now(timezone.utc).isoformat() + "Z"
        response = table.update_item(
            Key={"accountId": target_account_id},
            UpdateExpression=("SET stagingAccounts = :staging, updatedAt = :updated"),
            ExpressionAttributeValues={
                ":staging": staging_dicts,
                ":updated": now,
            },
            ConditionExpression="attribute_exists(accountId)",
            ReturnValues="ALL_NEW",
        )

        updated_staging_dicts = response["Attributes"].get("stagingAccounts", [])

        return {
            "success": True,
            "message": f"Removed staging account {removed_name}",
            "stagingAccounts": updated_staging_dicts,
        }

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ValueError(f"Target account {target_account_id} not found")
        print(f"Error removing staging account: {e}")
        raise


def update_staging_accounts(target_account_id: str, staging_accounts: List[Dict]) -> Dict:
    """
    Update entire staging accounts list for target account.

    Replaces the entire stagingAccounts attribute with the provided list.
    Useful for bulk updates or reordering.

    Args:
        target_account_id: Target account ID
        staging_accounts: List of staging account dicts

    Returns:
        Dict with operation results:
        {
            "success": bool,
            "message": str,
            "stagingAccounts": List[Dict]  # Updated list
        }

    Raises:
        ValueError: If validation fails or target account not found
        ClientError: If DynamoDB operation fails
    """
    table = _get_target_accounts_table()
    if not table:
        raise ValueError("Target accounts table not configured")

    # Validate all staging accounts
    for account in staging_accounts:
        validation = validate_staging_account_structure(account)
        if not validation["valid"]:
            raise ValueError(
                f"Invalid staging account {account.get('accountId')}: " f"{', '.join(validation['errors'])}"
            )

    # Convert to StagingAccount objects
    staging_objs = [StagingAccount.from_dict(account) for account in staging_accounts]

    # Convert to dicts for DynamoDB
    staging_dicts = [account.to_dict() for account in staging_objs]

    try:
        # Update DynamoDB
        now = datetime.now(timezone.utc).isoformat() + "Z"
        response = table.update_item(
            Key={"accountId": target_account_id},
            UpdateExpression=("SET stagingAccounts = :staging, updatedAt = :updated"),
            ExpressionAttributeValues={
                ":staging": staging_dicts,
                ":updated": now,
            },
            ConditionExpression="attribute_exists(accountId)",
            ReturnValues="ALL_NEW",
        )

        updated_staging = response["Attributes"].get("stagingAccounts", [])

        return {
            "success": True,
            "message": f"Updated {len(staging_accounts)} staging accounts",
            "stagingAccounts": updated_staging,
        }

    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ValueError(f"Target account {target_account_id} not found")
        print(f"Error updating staging accounts: {e}")
        raise
