#!/usr/bin/env python3
"""
Backfill Protection Groups with accountId.

Scans the Protection Groups DynamoDB table for items missing
accountId and derives it from assumeRoleName ARN or DRS source
server ARNs. Supports dry-run (default) and apply modes.

Usage:
    # Dry run (default) - shows what would be updated
    python scripts/backfill-protection-groups.py \
        --table-name aws-drs-orchestration-protection-groups-test

    # Apply changes
    python scripts/backfill-protection-groups.py \
        --table-name aws-drs-orchestration-protection-groups-test \
        --apply

    # Custom region
    python scripts/backfill-protection-groups.py \
        --table-name my-table --region eu-west-1 --apply
"""

import argparse
import logging
import re
import sys
from typing import Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

# Account ID validation pattern (12 digits)
ACCOUNT_ID_PATTERN = re.compile(r"^\d{12}$")

# ARN patterns for account ID extraction
IAM_ROLE_ARN_PATTERN = re.compile(
    r"^arn:aws:iam::(\d{12}):role/"
)
DRS_SOURCE_SERVER_ARN_PATTERN = re.compile(
    r"^arn:aws:drs:[a-z0-9-]+:(\d{12}):"
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Backfill Protection Groups with accountId "
            "derived from assumeRoleName ARN or source "
            "server ARNs."
        )
    )
    parser.add_argument(
        "--table-name",
        required=True,
        help="DynamoDB table name for Protection Groups",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Apply changes (default is dry-run)",
    )
    return parser.parse_args()


def extract_account_id_from_arn(arn: str) -> Optional[str]:
    """
    Extract 12-digit account ID from an IAM role ARN.

    Args:
        arn: IAM role ARN string

    Returns:
        12-digit account ID or None if extraction fails
    """
    match = IAM_ROLE_ARN_PATTERN.match(arn)
    if match:
        return match.group(1)
    return None


def extract_account_id_from_source_server_arn(
    arn: str,
) -> Optional[str]:
    """
    Extract 12-digit account ID from a DRS source server ARN.

    Args:
        arn: DRS source server ARN string

    Returns:
        12-digit account ID or None if extraction fails
    """
    match = DRS_SOURCE_SERVER_ARN_PATTERN.match(arn)
    if match:
        return match.group(1)
    return None


def derive_account_id(item: Dict) -> Optional[str]:
    """
    Derive accountId from Protection Group item fields.

    Attempts extraction in order:
    1. From assumeRoleName if it looks like an IAM role ARN
    2. From sourceServerIds if any contain DRS source server ARNs

    Args:
        item: DynamoDB Protection Group item

    Returns:
        Derived 12-digit account ID or None if not derivable
    """
    # Try assumeRoleName first
    assume_role = item.get("assumeRoleName", "")
    if assume_role and assume_role.startswith("arn:"):
        account_id = extract_account_id_from_arn(assume_role)
        if account_id:
            logger.debug(
                "Derived accountId %s from assumeRoleName: %s",
                account_id,
                assume_role,
            )
            return account_id

    # Try sourceServerIds
    source_server_ids = item.get("sourceServerIds", [])
    if isinstance(source_server_ids, list):
        for server_id in source_server_ids:
            if isinstance(server_id, str) and server_id.startswith(
                "arn:"
            ):
                account_id = extract_account_id_from_source_server_arn(
                    server_id
                )
                if account_id:
                    logger.debug(
                        "Derived accountId %s from "
                        "sourceServerIds: %s",
                        account_id,
                        server_id,
                    )
                    return account_id

    return None


def scan_protection_groups(
    table_name: str, region: str
) -> List[Dict]:
    """
    Scan Protection Groups table for items missing accountId.

    Handles pagination for large tables using LastEvaluatedKey.

    Args:
        table_name: DynamoDB table name
        region: AWS region

    Returns:
        List of items missing accountId
    """
    dynamodb = boto3.client("dynamodb", region_name=region)
    items_missing_account = []
    scan_kwargs = {"TableName": table_name}
    page_count = 0

    while True:
        page_count += 1
        logger.info("Scanning page %d...", page_count)

        try:
            response = dynamodb.scan(**scan_kwargs)
        except ClientError as e:
            logger.error(
                "Failed to scan table %s: %s",
                table_name,
                e.response["Error"]["Message"],
            )
            raise

        items = response.get("Items", [])
        for raw_item in items:
            item = _deserialize_item(raw_item)
            account_id = item.get("accountId", "")
            if not account_id or not account_id.strip():
                items_missing_account.append(item)

        # Handle pagination
        last_key = response.get("LastEvaluatedKey")
        if last_key:
            scan_kwargs["ExclusiveStartKey"] = last_key
        else:
            break

    if page_count > 1:
        logger.info(
            "Scanned %d pages total", page_count
        )

    return items_missing_account


def _deserialize_item(raw_item: Dict) -> Dict:
    """
    Deserialize a DynamoDB item from low-level format.

    Converts DynamoDB type descriptors (S, N, L, etc.)
    to plain Python types.

    Args:
        raw_item: DynamoDB item in wire format

    Returns:
        Plain Python dictionary
    """
    from boto3.dynamodb.types import TypeDeserializer
    deserializer = TypeDeserializer()
    return {
        k: deserializer.deserialize(v)
        for k, v in raw_item.items()
    }


def update_item_account_id(
    table_name: str,
    region: str,
    group_id: str,
    account_id: str,
) -> None:
    """
    Update a Protection Group item with derived accountId.

    Args:
        table_name: DynamoDB table name
        region: AWS region
        group_id: Protection Group ID (partition key)
        account_id: Derived account ID to set
    """
    dynamodb = boto3.client("dynamodb", region_name=region)
    dynamodb.update_item(
        TableName=table_name,
        Key={"groupId": {"S": group_id}},
        UpdateExpression="SET accountId = :aid",
        ExpressionAttributeValues={
            ":aid": {"S": account_id}
        },
    )


def run_backfill(
    table_name: str, region: str, apply: bool
) -> Tuple[int, int, int]:
    """
    Run the backfill process.

    Args:
        table_name: DynamoDB table name
        region: AWS region
        apply: If True, write changes; if False, dry-run

    Returns:
        Tuple of (updated_count, skipped_count, error_count)
    """
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"\n=== Protection Group Backfill ({mode}) ===")
    print(f"Table: {table_name}")
    print(f"Region: {region}\n")

    # Scan for items missing accountId
    print("Scanning for Protection Groups missing accountId...")
    items = scan_protection_groups(table_name, region)
    print(f"Found {len(items)} items missing accountId.\n")

    if not items:
        print("Nothing to backfill. All items have accountId.")
        return (0, 0, 0)

    updated = 0
    skipped = 0
    errored = 0

    for item in items:
        group_id = item.get("groupId", "unknown")
        group_name = item.get("groupName", "unnamed")
        derived_id = derive_account_id(item)

        if not derived_id:
            print(
                f"  SKIP  {group_id} ({group_name}) "
                f"- cannot derive accountId"
            )
            skipped += 1
            continue

        if apply:
            try:
                update_item_account_id(
                    table_name, region, group_id, derived_id
                )
                print(
                    f"  UPDATE {group_id} ({group_name}) "
                    f"-> accountId={derived_id}"
                )
                updated += 1
            except ClientError as e:
                print(
                    f"  ERROR  {group_id} ({group_name}) "
                    f"- {e.response['Error']['Message']}"
                )
                logger.error(
                    "Failed to update %s: %s",
                    group_id,
                    e,
                )
                errored += 1
        else:
            print(
                f"  WOULD UPDATE {group_id} ({group_name}) "
                f"-> accountId={derived_id}"
            )
            updated += 1

    return (updated, skipped, errored)


def main() -> None:
    """Entry point for the backfill script."""
    args = parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.apply else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    updated, skipped, errored = run_backfill(
        table_name=args.table_name,
        region=args.region,
        apply=args.apply,
    )

    # Print summary
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"\n=== Summary ({mode}) ===")
    print(f"  Updated: {updated}")
    print(f"  Skipped: {skipped}")
    print(f"  Errored: {errored}")
    print(f"  Total:   {updated + skipped + errored}")

    if not args.apply and updated > 0:
        print(
            "\nRe-run with --apply to write changes."
        )

    if errored > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
