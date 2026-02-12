#!/usr/bin/env python3
"""
Backfill Recovery Plans with accountId and notification fields.

Scans the Recovery Plans DynamoDB table for items missing
accountId and derives it from the first Protection Group
referenced in the plan's waves. Also adds empty defaults
for assumeRoleName, notificationEmail, and snsSubscriptionArn
if missing. Supports dry-run (default) and apply modes.

Usage:
    # Dry run (default) - shows what would be updated
    python scripts/backfill-recovery-plans.py \\
        --plans-table-name aws-drs-orchestration-recovery-plans-test \\
        --groups-table-name aws-drs-orchestration-protection-groups-test

    # Apply changes
    python scripts/backfill-recovery-plans.py \\
        --plans-table-name aws-drs-orchestration-recovery-plans-test \\
        --groups-table-name aws-drs-orchestration-protection-groups-test \\
        --apply

    # Custom region
    python scripts/backfill-recovery-plans.py \\
        --plans-table-name my-plans-table \\
        --groups-table-name my-groups-table \\
        --region eu-west-1 --apply
"""

import argparse
import logging
import sys
from typing import Dict, List, Optional, Set, Tuple

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Backfill Recovery Plans with accountId "
            "derived from Protection Groups in waves, "
            "and add empty defaults for notification "
            "fields."
        )
    )
    parser.add_argument(
        "--plans-table-name",
        required=True,
        help="DynamoDB table name for Recovery Plans",
    )
    parser.add_argument(
        "--groups-table-name",
        required=True,
        help=(
            "DynamoDB table name for Protection Groups"
        ),
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


def scan_recovery_plans(
    table_name: str, region: str
) -> List[Dict]:
    """
    Scan Recovery Plans table for items missing accountId.

    Handles pagination for large tables using LastEvaluatedKey.

    Args:
        table_name: DynamoDB table name
        region: AWS region

    Returns:
        List of items missing accountId
    """
    dynamodb = boto3.client("dynamodb", region_name=region)
    items_missing_account: List[Dict] = []
    scan_kwargs: Dict = {"TableName": table_name}
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
            if not account_id or not str(account_id).strip():
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


def get_protection_group(
    table_name: str,
    region: str,
    group_id: str,
) -> Optional[Dict]:
    """
    Fetch a single Protection Group by groupId.

    Args:
        table_name: DynamoDB table name
        region: AWS region
        group_id: Protection Group ID

    Returns:
        Deserialized Protection Group item or None
    """
    dynamodb = boto3.client("dynamodb", region_name=region)
    try:
        response = dynamodb.get_item(
            TableName=table_name,
            Key={"groupId": {"S": group_id}},
        )
    except ClientError as e:
        logger.error(
            "Failed to get Protection Group %s: %s",
            group_id,
            e.response["Error"]["Message"],
        )
        return None

    raw_item = response.get("Item")
    if not raw_item:
        return None
    return _deserialize_item(raw_item)


def extract_protection_group_ids(
    plan: Dict,
) -> List[str]:
    """
    Extract all Protection Group IDs from a plan's waves.

    Args:
        plan: Recovery Plan item

    Returns:
        List of Protection Group IDs found in waves
    """
    group_ids: List[str] = []
    waves = plan.get("waves", [])
    if not isinstance(waves, list):
        return group_ids

    for wave in waves:
        if not isinstance(wave, dict):
            continue
        pg_id = wave.get("protectionGroupId", "")
        if pg_id and isinstance(pg_id, str):
            group_ids.append(pg_id)

    return group_ids


def derive_account_id_from_groups(
    groups_table: str,
    region: str,
    group_ids: List[str],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Derive accountId and assumeRoleName from Protection Groups.

    Looks up each Protection Group and collects unique account
    IDs. Returns the account ID only if all groups agree on a
    single account. Also returns assumeRoleName from the first
    group that has one.

    Args:
        groups_table: Protection Groups DynamoDB table name
        region: AWS region
        group_ids: List of Protection Group IDs to look up

    Returns:
        Tuple of (accountId, assumeRoleName, warning_message).
        accountId is None if not derivable.
        assumeRoleName may be empty string.
        warning_message is set for mixed-account cases.
    """
    account_ids: Set[str] = set()
    assume_role_name: str = ""
    found_any = False

    for pg_id in group_ids:
        group = get_protection_group(
            groups_table, region, pg_id
        )
        if group is None:
            logger.warning(
                "Protection Group %s not found", pg_id
            )
            continue

        found_any = True
        pg_account = group.get("accountId", "")
        if pg_account and str(pg_account).strip():
            account_ids.add(str(pg_account).strip())

        # Grab assumeRoleName from first group that has it
        if not assume_role_name:
            role = group.get("assumeRoleName", "")
            if role and str(role).strip():
                assume_role_name = str(role).strip()

    if not found_any:
        return (None, "", "no Protection Groups found")

    if not account_ids:
        return (None, "", "no accountId on Protection Groups")

    if len(account_ids) > 1:
        ids_str = ", ".join(sorted(account_ids))
        return (
            None,
            "",
            f"mixed accounts across Protection Groups: "
            f"{ids_str}",
        )

    account_id = account_ids.pop()
    return (account_id, assume_role_name, None)


def update_recovery_plan(
    table_name: str,
    region: str,
    plan_id: str,
    account_id: str,
    assume_role_name: str,
) -> None:
    """
    Update a Recovery Plan with derived account context and defaults.

    Sets accountId, assumeRoleName, and adds empty defaults for
    notificationEmail and snsSubscriptionArn if missing.

    Args:
        table_name: DynamoDB table name
        region: AWS region
        plan_id: Recovery Plan ID (partition key)
        account_id: Derived account ID to set
        assume_role_name: IAM role name for cross-account
    """
    dynamodb = boto3.client("dynamodb", region_name=region)

    update_expr_parts = [
        "accountId = :aid",
        "assumeRoleName = :arn",
    ]
    expr_values: Dict = {
        ":aid": {"S": account_id},
        ":arn": {"S": assume_role_name},
    }

    # Add notificationEmail default if not present
    update_expr_parts.append(
        "notificationEmail = if_not_exists("
        "notificationEmail, :ne)"
    )
    expr_values[":ne"] = {"S": ""}

    # Add snsSubscriptionArn default if not present
    update_expr_parts.append(
        "snsSubscriptionArn = if_not_exists("
        "snsSubscriptionArn, :ssa)"
    )
    expr_values[":ssa"] = {"S": ""}

    update_expression = "SET " + ", ".join(
        update_expr_parts
    )

    dynamodb.update_item(
        TableName=table_name,
        Key={"planId": {"S": plan_id}},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expr_values,
    )


def run_backfill(
    plans_table: str,
    groups_table: str,
    region: str,
    apply: bool,
) -> Tuple[int, int, int]:
    """
    Run the Recovery Plan backfill process.

    Args:
        plans_table: Recovery Plans DynamoDB table name
        groups_table: Protection Groups DynamoDB table name
        region: AWS region
        apply: If True, write changes; if False, dry-run

    Returns:
        Tuple of (updated_count, skipped_count, error_count)
    """
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"\n=== Recovery Plan Backfill ({mode}) ===")
    print(f"Plans table:  {plans_table}")
    print(f"Groups table: {groups_table}")
    print(f"Region: {region}\n")

    # Scan for plans missing accountId
    print(
        "Scanning for Recovery Plans missing accountId..."
    )
    plans = scan_recovery_plans(plans_table, region)
    print(
        f"Found {len(plans)} plans missing accountId.\n"
    )

    if not plans:
        print(
            "Nothing to backfill. "
            "All plans have accountId."
        )
        return (0, 0, 0)

    updated = 0
    skipped = 0
    errored = 0

    for plan in plans:
        plan_id = plan.get("planId", "unknown")
        plan_name = plan.get("planName", "unnamed")

        # Extract Protection Group IDs from waves
        pg_ids = extract_protection_group_ids(plan)
        if not pg_ids:
            print(
                f"  SKIP  {plan_id} ({plan_name}) "
                f"- no Protection Groups in waves"
            )
            skipped += 1
            continue

        # Derive account from Protection Groups
        account_id, assume_role, warning = (
            derive_account_id_from_groups(
                groups_table, region, pg_ids
            )
        )

        if not account_id:
            reason = warning or "cannot derive accountId"
            print(
                f"  SKIP  {plan_id} ({plan_name}) "
                f"- {reason}"
            )
            skipped += 1
            continue

        if apply:
            try:
                update_recovery_plan(
                    plans_table,
                    region,
                    plan_id,
                    account_id,
                    assume_role,
                )
                print(
                    f"  UPDATE {plan_id} ({plan_name}) "
                    f"-> accountId={account_id}"
                    f", assumeRoleName={assume_role!r}"
                )
                updated += 1
            except ClientError as e:
                print(
                    f"  ERROR  {plan_id} ({plan_name}) "
                    f"- {e.response['Error']['Message']}"
                )
                logger.error(
                    "Failed to update %s: %s",
                    plan_id,
                    e,
                )
                errored += 1
        else:
            print(
                f"  WOULD UPDATE {plan_id} ({plan_name}) "
                f"-> accountId={account_id}"
                f", assumeRoleName={assume_role!r}"
            )
            updated += 1

    return (updated, skipped, errored)


def main() -> None:
    """Entry point for the backfill script."""
    args = parse_args()

    # Configure logging
    log_level = (
        logging.DEBUG if args.apply else logging.INFO
    )
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    updated, skipped, errored = run_backfill(
        plans_table=args.plans_table_name,
        groups_table=args.groups_table_name,
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
