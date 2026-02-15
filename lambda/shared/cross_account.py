"""
Cross-Account IAM Role Assumption Utilities

Provides utilities for cross-account DR operations in hub-and-spoke architecture.
Handles IAM role assumption and DRS client creation for target accounts.

## Architecture Pattern

Hub-and-Spoke Model:
- Hub Account: DR Orchestration account (this code runs here)
- Spoke Accounts: Workload accounts containing DRS source servers
- Cross-Account Access: Hub assumes IAM role in spoke accounts via STS

## Integration Points

### 1. Recovery Plan Execution (Primary Use Case)
```python
from shared.cross_account import determine_target_account_context, create_drs_client

# Determine which account contains the DRS servers
account_context = determine_target_account_context(recovery_plan)
# Returns: {"accountId": "123456789012", "assumeRoleName": "DRSOrchestrationCrossAccountRole", "isCurrentAccount": False}  # noqa: E501

# Create DRS client for target account
drs_client = create_drs_client(region="us-east-1", account_context=account_context)

# Now use drs_client for DRS operations in target account
response = drs_client.describe_source_servers()
```

### 2. Current Account Operations (No Role Assumption)
```python
# If all Protection Groups are in current account, no role assumption occurs
account_context = determine_target_account_context(recovery_plan)
# Returns: {"accountId": "999999999999", "assumeRoleName": None, "isCurrentAccount": True}

drs_client = create_drs_client(region="us-east-1", account_context=account_context)
# Uses current account credentials (no STS assume role)
```

### 3. Direct DRS Client Creation (Without Recovery Plan)
```python
# For operations that don't involve a Recovery Plan
drs_client = create_drs_client(region="us-east-1")  # Current account
drs_client = create_drs_client(region="us-east-1", account_context=None)  # Current account

# For explicit cross-account access
account_context = {
    "accountId": "123456789012",
    "assumeRoleName": "DRSOrchestrationCrossAccountRole",
    "isCurrentAccount": False
}
drs_client = create_drs_client(region="us-east-1", account_context=account_context)
```

## Data Sources

### Protection Groups Table (DynamoDB)
- Table: `PROTECTION_GROUPS_TABLE` environment variable
- Key: `groupId` (Protection Group ID)
- Required Fields:
  - `accountId`: AWS account ID where DRS servers reside
  - `region`: AWS region for DRS operations

### Target Accounts Table (DynamoDB)
- Table: `TARGET_ACCOUNTS_TABLE` environment variable
- Key: `accountId` (AWS account ID)
- Required Fields:
  - `assumeRoleName`: IAM role name for cross-account access
  - `crossAccountRoleArn`: Full ARN (alternative to assumeRoleName)

## IAM Requirements

### Hub Account (Orchestration Account)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Resource": "arn:aws:iam::*:role/DRSOrchestrationCrossAccountRole"
    }
  ]
}
```

### Spoke Account (Workload Account)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::HUB_ACCOUNT_ID:role/DROrchestrationExecutionRole"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Error Handling

### Mixed Account Validation
Recovery Plans spanning multiple accounts are NOT supported:
```python
# This will raise ValueError
plan = {
    "waves": [
        {"protectionGroupId": "pg-account-111"},  # Account 111111111111
        {"protectionGroupId": "pg-account-222"}   # Account 222222222222
    ]
}
determine_target_account_context(plan)  # Raises ValueError
```

### Missing Cross-Account Role
If target account lacks role configuration:
```python
# Raises RuntimeError with detailed guidance
create_drs_client(region="us-east-1", account_context={
    "accountId": "123456789012",
    "assumeRoleName": "NonExistentRole",
    "isCurrentAccount": False
})
# Error includes:
# - Possible causes (role doesn't exist, trust relationship, permissions)
# - Role ARN attempted
# - Remediation steps
```

## Testing Considerations

### Test Environment Fallback
Uses `AWS_ACCOUNT_ID` environment variable when STS unavailable:
```python
os.environ["AWS_ACCOUNT_ID"] = "999999999999"
account_id = get_current_account_id()  # Returns "999999999999" in tests
```

### Lazy Initialization
DynamoDB resources initialized on first use to avoid boto3 errors during test collection.
"""

import os
from typing import Dict, Optional

import boto3

# Lazy initialization to avoid boto3 errors during test collection
_dynamodb = None
_protection_groups_table = None
_target_accounts_table = None


def _get_dynamodb_resource():
    """
    Lazy initialization of DynamoDB resource.

    Defers boto3 resource creation until first use to avoid errors during test collection.
    """
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb


def _get_protection_groups_table():
    """
    Lazy initialization of Protection Groups DynamoDB table.

    Requires PROTECTION_GROUPS_TABLE environment variable.
    Raises ValueError if environment variable not set.
    """
    global _protection_groups_table
    if _protection_groups_table is None:
        table_name = os.environ.get("PROTECTION_GROUPS_TABLE")
        if not table_name:
            raise ValueError("PROTECTION_GROUPS_TABLE environment variable not set")
        _protection_groups_table = _get_dynamodb_resource().Table(table_name)
    return _protection_groups_table


def _get_target_accounts_table():
    """
    Lazy initialization of Target Accounts DynamoDB table.

    Optional table - returns None if TARGET_ACCOUNTS_TABLE environment variable not set.
    Used to look up cross-account role configuration for spoke accounts.
    """
    global _target_accounts_table
    if _target_accounts_table is None:
        table_name = os.environ.get("TARGET_ACCOUNTS_TABLE", "")
        if table_name:
            _target_accounts_table = _get_dynamodb_resource().Table(table_name)
    return _target_accounts_table


def get_current_account_id() -> str:
    """
    Get current AWS account ID using STS GetCallerIdentity.

    Falls back to AWS_ACCOUNT_ID environment variable in test environments
    where STS may be unavailable.

    Returns:
        12-digit AWS account ID, or "unknown" if unable to determine
    """
    try:
        sts_client = boto3.client("sts")
        return sts_client.get_caller_identity()["Account"]
    except Exception as e:
        print(f"Error getting account ID: {e}")
        return "unknown"


def get_cross_account_session(role_arn: str, external_id: str = None) -> boto3.Session:
    """
    Create a boto3 Session by assuming a cross-account IAM role.

    Args:
        role_arn: Full ARN of the IAM role to assume
        external_id: Optional external ID for role assumption

    Returns:
        boto3.Session configured with temporary credentials

    Raises:
        Exception: If role assumption fails
    """
    import time

    sts_client = boto3.client("sts")
    session_name = f"drs-orchestration-{int(time.time())}"

    print(f"Assuming role: {role_arn}")

    assume_role_params = {
        "RoleArn": role_arn,
        "RoleSessionName": session_name,
    }

    if external_id:
        assume_role_params["ExternalId"] = external_id
        print("Using External ID for role assumption")

    try:
        assumed_role = sts_client.assume_role(**assume_role_params)
        credentials = assumed_role["Credentials"]

        return boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )
    except Exception as e:
        error_msg = f"Failed to assume role {role_arn}: {str(e)}"
        print(error_msg)
        raise


def determine_target_account_context(plan: Dict) -> Dict:  # noqa: C901
    """
    Determine target account for cross-account DR operations in hub-and-spoke architecture.

    Resolves which AWS account contains the DRS source servers by:
    1. Extracting AccountId from Protection Groups referenced in Recovery Plan waves
    2. Validating all Protection Groups belong to same account (mixed accounts not supported)
    3. Looking up cross-account role configuration from target accounts table
    4. Returning current account context if all servers are local

    Args:
        plan: Recovery Plan with waves containing protectionGroupId references

    Returns:
        Dict with:
        - accountId: Target AWS account ID (12-digit)
        - assumeRoleName: IAM role name for cross-account access (None if current account)
        - isCurrentAccount: Boolean indicating if target is orchestration account

    Raises:
        ValueError: If Protection Groups span multiple accounts (not supported)
        ValueError: If cross-account role configuration is missing
    """
    try:
        # Better current account detection with environment variable fallback
        try:
            current_account_id = get_current_account_id()
            if current_account_id == "unknown":
                # In test environment, use environment variable fallback
                current_account_id = os.environ.get("AWS_ACCOUNT_ID")
                if not current_account_id:
                    raise ValueError(
                        "Unable to determine current account ID and no AWS_ACCOUNT_ID environment variable set"
                    )
                print(f"Using AWS_ACCOUNT_ID environment variable for current account: {current_account_id}")
        except Exception as e:
            # In test environment, use environment variable fallback
            current_account_id = os.environ.get("AWS_ACCOUNT_ID")
            if not current_account_id:
                raise ValueError(f"Unable to determine current account ID: {e}")
            print(f"Using AWS_ACCOUNT_ID environment variable for current account: {current_account_id}")

        waves = plan.get("waves", [])

        # Collect unique account IDs from all Protection Groups in the plan
        all_target_account_ids = set()

        for wave in waves:
            pg_id = wave.get("protectionGroupId")
            if not pg_id:
                continue

            try:
                # Get Protection Group to check its AccountId
                protection_groups_table = _get_protection_groups_table()
                pg_result = protection_groups_table.get_item(Key={"groupId": pg_id})
                if "Item" in pg_result:
                    pg = pg_result["Item"]
                    account_id = pg.get("accountId")
                    if account_id and account_id.strip():
                        all_target_account_ids.add(account_id.strip())
                        print(f"Found target account {account_id} from Protection Group {pg_id}")
            except Exception as e:
                print(f"Error getting Protection Group {pg_id}: {e}")
                continue

        # Enforce mixed account validation - throw exception instead of warning
        if len(all_target_account_ids) > 1:
            raise ValueError(
                f"Recovery Plan contains Protection Groups from multiple accounts: {all_target_account_ids}. "
                f"Multi-account Recovery Plans are not supported. "
                f"Please create separate Recovery Plans for each account."
            )

        # Check if all protection groups are in current account
        if not all_target_account_ids or (
            len(all_target_account_ids) == 1 and current_account_id in all_target_account_ids
        ):
            # All protection groups are in current account (or no protection groups found)
            print(f"All Protection Groups are in current account {current_account_id}")
            return {
                "accountId": current_account_id,
                "assumeRoleName": None,  # No role assumption needed for current account
                "isCurrentAccount": True,
            }

        # Single cross-account target
        target_account_id = next(iter(all_target_account_ids))

        # Get target account configuration from target accounts table
        target_accounts_table = _get_target_accounts_table()
        if target_accounts_table:
            try:
                account_result = target_accounts_table.get_item(Key={"accountId": target_account_id})
                if "Item" in account_result:
                    account_config = account_result["Item"]
                    assume_role_name = (
                        account_config.get("assumeRoleName")
                        or account_config.get("crossAccountRoleArn", "").split("/")[-1]
                        or account_config.get("roleArn", "").split("/")[-1]
                    )
                    # Include externalId for secure cross-account role assumption
                    external_id = account_config.get("externalId")

                    print(f"Using target account {target_account_id} with role {assume_role_name}")
                    if external_id:
                        print("External ID configured for secure role assumption")

                    return {
                        "accountId": target_account_id,
                        "assumeRoleName": assume_role_name,
                        "externalId": external_id,
                        "isCurrentAccount": False,
                    }
                else:
                    print(f"WARNING: Target account {target_account_id} not found in target accounts table")
            except Exception as e:
                print(f"Error getting target account configuration for {target_account_id}: {e}")

        # Fallback: target account found but no configuration - assume standard role name
        print(f"Using target account {target_account_id} with default role name")
        return {
            "accountId": target_account_id,
            "assumeRoleName": "DRSOrchestrationCrossAccountRole",  # Default role name
            "isCurrentAccount": False,
        }

    except Exception as e:
        print(f"Error determining target account context: {e}")
        # Re-raise the exception instead of silently falling back
        raise


def create_drs_client(region: str, account_context: Optional[Dict] = None):
    """
    Create DRS client with optional cross-account IAM role assumption.

    For current account operations, returns standard boto3 DRS client.
    For cross-account operations, assumes IAM role in target account using STS.

    Args:
        region: AWS region for DRS operations
        account_context: Optional dict with accountId and assumeRoleName for cross-account access

    Returns:
        boto3 DRS client configured for target account and region

    Raises:
        ValueError: If cross-account context is missing required fields
        RuntimeError: If IAM role assumption fails (with detailed error guidance)
    """
    # If no account context provided or it's current account, use current account
    if not account_context or account_context.get("isCurrentAccount", True):
        print(f"Creating DRS client for current account in region {region}")
        return boto3.client("drs", region_name=region)

    # Improved cross-account role validation and error handling
    account_id = account_context.get("accountId")
    assume_role_name = account_context.get("assumeRoleName")

    if not account_id:
        raise ValueError("Cross-account operation requires AccountId in account_context")

    if not assume_role_name:
        raise ValueError(
            f"Cross-account operation requires AssumeRoleName for account {account_id}. "
            f"Please ensure the target account is registered with a valid cross-account role."
        )

    # Skip role assumption if already using target account credentials
    current_account_id = get_current_account_id()
    if current_account_id == account_id:
        print(f"Already running with credentials for account {account_id}, " f"skipping role assumption")
        return boto3.client("drs", region_name=region)

    print(f"Creating cross-account DRS client for account {account_id} using role {assume_role_name}")

    try:
        # Build role ARN
        role_arn = f"arn:aws:iam::{account_id}:role/{assume_role_name}"
        external_id = account_context.get("externalId")

        # Use get_cross_account_session to assume role
        session = get_cross_account_session(role_arn=role_arn, external_id=external_id)

        # Create DRS client with assumed role session
        drs_client = session.client("drs", region_name=region)

        print(f"Successfully created cross-account DRS client for account {account_id}")
        return drs_client

    except Exception as e:
        # Don't fall back silently - raise clear error messages
        error_msg = f"Failed to assume cross-account role for account {account_id}: {e}"

        if "AccessDenied" in str(e):
            error_msg += (
                f"\n\nPossible causes:\n"
                f"1. Cross-account role '{assume_role_name}' does not exist in account {account_id}\n"
                f"2. Trust relationship not configured to allow this hub account\n"
                f"3. Insufficient permissions on the cross-account role\n"
                f"4. Role ARN: arn:aws:iam::{account_id}:role/{assume_role_name}\n\n"
                f"Please verify the cross-account role is deployed and configured correctly."
            )
        elif "InvalidUserID.NotFound" in str(e):
            error_msg += f"\n\nThe role '{assume_role_name}' does not exist in account {account_id}."

        print(f"Cross-account role assumption failed: {error_msg}")
        raise RuntimeError(error_msg)


def create_ec2_client(region: str, account_context: Optional[Dict] = None):
    """
    Create EC2 client with optional cross-account IAM role assumption.

    For current account operations, returns standard boto3 EC2 client.
    For cross-account operations, assumes IAM role in target account using STS.

    Args:
        region: AWS region for EC2 operations
        account_context: Optional dict with accountId and assumeRoleName for cross-account access

    Returns:
        boto3 EC2 client configured for target account and region

    Raises:
        ValueError: If cross-account context is missing required fields
        RuntimeError: If IAM role assumption fails
    """
    # If no account context provided or it's current account, use current account
    if not account_context or account_context.get("isCurrentAccount", True):
        return boto3.client("ec2", region_name=region)

    # Cross-account role validation
    account_id = account_context.get("accountId")
    assume_role_name = account_context.get("assumeRoleName")

    if not account_id:
        raise ValueError("Cross-account operation requires AccountId in account_context")

    if not assume_role_name:
        raise ValueError(f"Cross-account operation requires AssumeRoleName for account {account_id}")

    # Skip role assumption if already using target account credentials
    current_account_id = get_current_account_id()
    if current_account_id == account_id:
        return boto3.client("ec2", region_name=region)

    try:
        # Build role ARN
        role_arn = f"arn:aws:iam::{account_id}:role/{assume_role_name}"
        external_id = account_context.get("externalId")

        # Use get_cross_account_session to assume role
        session = get_cross_account_session(role_arn=role_arn, external_id=external_id)

        # Create EC2 client with assumed role session
        return session.client("ec2", region_name=region)

    except Exception as e:
        error_msg = f"Failed to assume cross-account role for EC2 in account {account_id}: {e}"
        print(error_msg)
        raise RuntimeError(error_msg)
