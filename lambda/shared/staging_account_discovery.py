"""
Staging Account Discovery

Automatically discovers staging accounts configured in DRS for a target account.
"""

import boto3
from typing import Dict, List
from botocore.exceptions import ClientError
from .cross_account import get_cross_account_session


def discover_staging_accounts_from_drs(
    target_account_id: str,
    role_arn: str = None,
    external_id: str = None,
    regions: List[str] = None,
) -> List[Dict[str, str]]:
    """
    Discover staging accounts using DRS list-staging-accounts API.

    The list-staging-accounts API returns all accounts that have DRS
    replication configured, including the target account itself and any
    staging accounts. We filter out the target account to get only staging.

    Args:
        target_account_id: Target account to query
        role_arn: Cross-account role ARN (optional)
        external_id: External ID for role assumption (optional)
        regions: List of regions to check (defaults to common regions)

    Returns:
        List of discovered staging accounts with structure:
        [
            {
                "accountId": "444455556666",
                "accountName": "Staging Account 444455556666",
                "roleArn": "arn:aws:iam::444455556666:role/DRSOrchestrationRole",
                "externalId": "drs-orchestration-444455556666",
                "discoveredFrom": "us-east-1"
            }
        ]
    """
    if not regions:
        regions = [
            "us-east-1",
            "us-west-2",
            "eu-west-1",
            "ap-southeast-1",
        ]

    discovered_accounts: Dict[str, Dict] = {}

    session = None
    if role_arn:
        try:
            session = get_cross_account_session(role_arn=role_arn, external_id=external_id)
        except Exception as e:
            print(f"Failed to assume role for staging discovery: {e}")
            return []
    else:
        session = boto3.Session()

    for region in regions:
        try:
            drs_client = session.client("drs", region_name=region)

            # Use list-staging-accounts API to get all DRS-configured accounts
            response = drs_client.list_staging_accounts()
            accounts = response.get("accounts", [])

            print(f"Found {len(accounts)} DRS accounts in {region}: " f"{[acc.get('accountID') for acc in accounts]}")

            for account in accounts:
                staging_account_id = account.get("accountID")

                # Filter out the target account itself
                if (
                    staging_account_id
                    and staging_account_id != target_account_id
                    and staging_account_id not in discovered_accounts
                ):
                    from .account_utils import (
                        construct_role_arn,
                    )

                    # Try to get the real account name/alias
                    account_name = None
                    try:
                        # Assume role into staging account to get its alias
                        staging_role_arn = construct_role_arn(staging_account_id)
                        staging_session = get_cross_account_session(
                            role_arn=staging_role_arn,
                            external_id=f"drs-orchestration-{staging_account_id}",
                        )
                        iam_client = staging_session.client("iam")
                        aliases = iam_client.list_account_aliases()["AccountAliases"]
                        if aliases:
                            account_name = aliases[0]
                    except Exception as e:
                        print(f"Could not fetch account alias for {staging_account_id}: {e}")

                    # Fallback to placeholder if we couldn't get the real name
                    if not account_name:
                        account_name = f"Staging Account {staging_account_id}"

                    discovered_accounts[staging_account_id] = {
                        "accountId": staging_account_id,
                        "accountName": account_name,
                        "roleArn": construct_role_arn(staging_account_id),
                        "externalId": f"drs-orchestration-{staging_account_id}",
                        "discoveredFrom": region,
                    }

                    print(f"Discovered staging account {staging_account_id} ({account_name}) " f"in region {region}")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in [
                "UninitializedAccountException",
                "UnrecognizedClientException",
            ]:
                print(f"DRS not initialized in {region}, skipping")
                continue
            else:
                print(f"Error querying DRS in {region}: {e}")
        except Exception as e:
            print(f"Error querying DRS in {region}: {e}")

    result = list(discovered_accounts.values())
    print(f"Discovered {len(result)} unique staging accounts " f"for target account {target_account_id}")
    return result
