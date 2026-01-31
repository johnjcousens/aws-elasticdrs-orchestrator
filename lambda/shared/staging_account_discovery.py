"""
Staging Account Discovery

Automatically discovers staging accounts configured in DRS for a target account.
"""

import boto3
from typing import Dict, List, Set
from botocore.exceptions import ClientError
from .cross_account import get_cross_account_session


def discover_staging_accounts_from_drs(
    target_account_id: str,
    role_arn: str = None,
    external_id: str = None,
    regions: List[str] = None,
) -> List[Dict[str, str]]:
    """
    Discover staging accounts by querying DRS source servers.

    DRS source servers contain staging area information that includes
    the staging account ID where replication data is stored.

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
                "roleArn": "arn:aws:iam::444455556666:role/...",
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
            session = get_cross_account_session(
                role_arn=role_arn, external_id=external_id
            )
        except Exception as e:
            print(f"Failed to assume role for staging discovery: {e}")
            return []
    else:
        session = boto3.Session()

    for region in regions:
        try:
            drs_client = session.client("drs", region_name=region)

            paginator = drs_client.get_paginator("describe_source_servers")
            for page in paginator.paginate():
                servers = page.get("items", [])

                for server in servers:
                    staging_area = server.get("stagingArea", {})
                    staging_account_id = staging_area.get("stagingAccountID")

                    if (
                        staging_account_id
                        and staging_account_id != target_account_id
                        and staging_account_id not in discovered_accounts
                    ):
                        from .account_utils import construct_role_arn

                        discovered_accounts[staging_account_id] = {
                            "accountId": staging_account_id,
                            "accountName": f"Staging Account {staging_account_id}",
                            "roleArn": construct_role_arn(staging_account_id),
                            "discoveredFrom": region,
                        }

                        print(
                            f"Discovered staging account {staging_account_id} "
                            f"in region {region}"
                        )

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
    print(
        f"Discovered {len(result)} unique staging accounts "
        f"for target account {target_account_id}"
    )
    return result
