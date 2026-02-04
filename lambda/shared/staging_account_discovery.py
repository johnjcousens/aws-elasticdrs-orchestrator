"""
Staging Account Discovery

Automatically discovers staging accounts configured in DRS for a target account.
"""

import boto3
from typing import Dict, List
from botocore.exceptions import ClientError
from .cross_account import get_cross_account_session

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


def discover_staging_accounts_from_drs(
    target_account_id: str,
    role_arn: str = None,
    external_id: str = None,
    regions: List[str] = None,
) -> List[Dict[str, str]]:
    """
    Discover staging accounts by querying the target account's DRS trusted accounts.

    Discovery strategy:
    1. Assume role into target account
    2. Call list-staging-accounts API in each DRS region
    3. Filter out the target account itself (DRS always includes it)
    4. Return unique trusted staging accounts found

    The list-staging-accounts API returns the trusted staging accounts
    configured for the target account in DRS.

    Args:
        target_account_id: Target account to query for trusted staging accounts
        role_arn: Cross-account role ARN (required)
        external_id: External ID for role assumption (optional)
        regions: List of regions to check (defaults to all DRS regions)

    Returns:
        List of discovered staging accounts with structure:
        [
            {
                "accountId": "777788889999",
                "accountName": "ORCHESTRATION (777788889999)",
                "roleArn": "arn:aws:iam::777788889999:role/DRSOrchestrationRole",
                "externalId": "drs-orchestration-cross-account",
                "discoveredFrom": "us-east-1"
            }
        ]
    """
    if not regions:
        # Use all DRS regions by default
        regions = DRS_REGIONS

    discovered_accounts: Dict[str, Dict] = {}

    # Assume role into target account to query its trusted staging accounts
    session = None
    if role_arn:
        try:
            session = get_cross_account_session(role_arn=role_arn, external_id=external_id)
            print(f"Assumed role into target account {target_account_id} to discover trusted staging accounts")
        except Exception as e:
            print(f"Failed to assume role for staging discovery: {e}")
            return []
    else:
        session = boto3.Session()
        print(f"Using default credentials to query target account {target_account_id}")

    # Query each region for trusted staging accounts
    for region in regions:
        try:
            drs_client = session.client("drs", region_name=region)

            # Use list-staging-accounts API to get trusted staging accounts
            paginator = drs_client.get_paginator("list_staging_accounts")

            for page in paginator.paginate():
                staging_accounts = page.get("accounts", [])

                if staging_accounts:
                    print(f"Found {len(staging_accounts)} staging accounts in region {region}")
                    print(f"Staging account IDs: {[acc.get('accountID') for acc in staging_accounts]}")

                for staging_account in staging_accounts:
                    staging_account_id = staging_account.get("accountID")

                    if staging_account_id and staging_account_id not in discovered_accounts:
                        from .account_utils import construct_role_arn

                        # Try to get the real account name/alias
                        account_name = None
                        try:
                            # Assume role into staging account to get its alias
                            staging_role_arn = construct_role_arn(staging_account_id)
                            staging_session = get_cross_account_session(
                                role_arn=staging_role_arn,
                                external_id="drs-orchestration-cross-account",
                            )
                            iam_client = staging_session.client("iam")
                            aliases = iam_client.list_account_aliases()["AccountAliases"]
                            if aliases:
                                # Format as "ALIAS (ACCOUNT_ID)"
                                account_name = f"{aliases[0]} ({staging_account_id})"
                        except Exception as e:
                            print(f"Could not fetch account alias for {staging_account_id}: {e}")

                        # Fallback to just account ID if we couldn't get the alias
                        if not account_name:
                            account_name = staging_account_id

                        discovered_accounts[staging_account_id] = {
                            "accountId": staging_account_id,
                            "accountName": account_name,
                            "roleArn": construct_role_arn(staging_account_id),
                            "externalId": "drs-orchestration-cross-account",
                            "discoveredFrom": region,
                        }

                        print(f"Discovered staging account {staging_account_id} ({account_name}) from region {region}")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in [
                "UninitializedAccountException",
                "UnrecognizedClientException",
            ]:
                # Silently skip uninitialized regions
                continue
            else:
                print(f"Error querying DRS in {region}: {e}")
        except Exception as e:
            print(f"Error querying DRS in {region}: {e}")

    result = list(discovered_accounts.values())
    print(f"Discovered {len(result)} unique staging accounts for target account {target_account_id}")
    return result
