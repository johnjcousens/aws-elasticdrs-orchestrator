"""
Staging Account Discovery

Automatically discovers staging accounts by checking if the orchestration account
has DRS source servers. If it does, it should be added as a staging account to
all target accounts.

IMPORTANT: The list-staging-accounts API only returns accounts that have EXISTING
extended source servers, NOT the configured trusted accounts. Therefore, we cannot
use it for discovery. Instead, we check if the current (orchestration) account has
DRS servers, and if so, add it as a staging account to all target accounts.
"""

import boto3
from typing import Dict, List
from botocore.exceptions import ClientError

# DRS regions (all regions where DRS is available as of 2026)
DRS_REGIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-southeast-3",
    "ap-northeast-1",
    "ap-northeast-2",
    "ap-northeast-3",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "ca-central-1",
    "ap-south-1",
    "sa-east-1",
    "eu-north-1",
    "me-south-1",
    "af-south-1",
    "ap-east-1",
    "eu-south-1",
    "eu-central-2",
    "eu-south-2",
    "ap-south-2",
    "ap-southeast-4",
    "me-central-1",
    "il-central-1",
]


def check_current_account_has_drs_servers(regions: List[str] = None) -> tuple[bool, str, str]:
    """
    Check if the current (orchestration) account has DRS source servers.

    This is used to determine if the orchestration account should be added
    as a staging account to target accounts.

    Args:
        regions: List of regions to check (defaults to all DRS regions)

    Returns:
        Tuple of (has_servers, account_id, account_name):
        - has_servers: True if account has DRS servers
        - account_id: Current account ID
        - account_name: Current account name/alias
    """
    if not regions:
        regions = DRS_REGIONS

    # Get current account ID
    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]

    # Get account alias
    account_name = account_id
    try:
        iam = boto3.client("iam")
        aliases = iam.list_account_aliases()["AccountAliases"]
        if aliases:
            account_name = f"{aliases[0]} ({account_id})"
    except Exception as e:
        print(f"Could not fetch account alias: {e}")

    print(f"Checking if current account {account_name} has DRS servers...")

    # Check each region for DRS servers
    for region in regions:
        try:
            drs = boto3.client("drs", region_name=region)

            # Try to describe source servers
            response = drs.describe_source_servers(maxResults=1)
            servers = response.get("items", [])

            if servers:
                print(f"Found {len(servers)} DRS servers in region {region}")
                print(f"Current account {account_name} HAS DRS servers - should be staging account")
                return True, account_id, account_name

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "UninitializedAccountException":
                # DRS not initialized in this region - skip
                continue
            else:
                print(f"Error querying DRS in {region}: {e}")
        except Exception as e:
            print(f"Error querying {region}: {e}")

    print(f"Current account {account_name} has NO DRS servers")
    return False, account_id, account_name


def discover_staging_accounts_from_drs(
    target_account_id: str,
    role_arn: str = None,
    external_id: str = None,
    regions: List[str] = None,
) -> List[Dict[str, str]]:
    """
    Discover staging accounts by checking if the orchestration account has DRS servers.

    NEW LOGIC (2026-02-04):
    The list-staging-accounts API only returns accounts with EXISTING extended servers,
    not configured trusted accounts. Therefore, we use a different approach:

    1. Check if the current (orchestration) account has DRS source servers
    2. If yes, and it's not the target account, return it as a staging account
    3. This allows automatic discovery without manual configuration

    Args:
        target_account_id: Target account ID (to avoid adding it as its own staging)
        role_arn: Not used in new logic (kept for compatibility)
        external_id: Not used in new logic (kept for compatibility)
        regions: List of regions to check (defaults to all DRS regions)

    Returns:
        List of discovered staging accounts with structure:
        [
            {
                "accountId": "777788889999",
                "accountName": "DEMO_ONPREM (777788889999)",
                "roleArn": "arn:aws:iam::777788889999:role/DRSOrchestrationRole",
                "externalId": "drs-orchestration-cross-account",
                "discoveredFrom": "automatic"
            }
        ]
    """
    if not regions:
        regions = DRS_REGIONS

    discovered_accounts = []

    # Check if current account has DRS servers
    has_servers, current_account_id, current_account_name = check_current_account_has_drs_servers(regions)

    # If current account has servers and is not the target account, add it as staging
    if has_servers and current_account_id != target_account_id:
        from .account_utils import construct_role_arn

        staging_account = {
            "accountId": current_account_id,
            "accountName": current_account_name,
            "roleArn": construct_role_arn(current_account_id),
            "externalId": "drs-orchestration-cross-account",
            "discoveredFrom": "automatic",
        }

        discovered_accounts.append(staging_account)
        print(
            f"Discovered staging account {current_account_id} ({current_account_name}) "
            f"for target account {target_account_id}"
        )
    else:
        if current_account_id == target_account_id:
            print(f"Current account {current_account_id} is the target account - not adding as staging")
        else:
            print(f"Current account {current_account_id} has no DRS servers - not adding as staging")

    return discovered_accounts
