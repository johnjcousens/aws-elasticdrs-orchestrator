#!/usr/bin/env python3
"""
Add Current Account as Target Account

This script adds the current AWS account (where the solution is deployed)
as a target account in the DRS Orchestration system. This is the most
common setup where DRS source servers are in the same account as the solution.

Usage:
    python3 scripts/add-current-account.py [--account-name "My Account"]
"""

import argparse
import sys
from datetime import datetime

import boto3


def get_current_account_id():
    """Get the current AWS account ID"""
    try:
        sts = boto3.client("sts")
        response = sts.get_caller_identity()
        return response["Account"]
    except Exception as e:
        print(f"Error getting current account ID: {e}")
        return None


def get_account_name(account_id):
    """Try to get a friendly name for the account"""
    try:
        # Try to get account alias
        iam = boto3.client("iam")
        response = iam.list_account_aliases()
        aliases = response.get("AccountAliases", [])
        if aliases:
            return aliases[0]
    except Exception:  # noqa: E722
        pass

    try:
        # Try to get account name from Organizations (if available)
        orgs = boto3.client("organizations")
        response = orgs.describe_account(AccountId=account_id)
        return response["Account"]["Name"]
    except Exception:  # noqa: E722
        pass

    return None


def add_target_account(table_name, account_id, account_name=None):
    """Add the account to the target accounts table"""
    try:
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.Table(table_name)

        # Check if account already exists
        try:
            response = table.get_item(Key={"AccountId": account_id})
            if "Item" in response:
                print(f"✅ Account {account_id} already exists as a target account")
                return True
        except Exception as e:
            print(f"Error checking existing account: {e}")

        # Create the account item
        item = {
            "AccountId": account_id,
            "IsCurrentAccount": True,
            "Status": "active",
            "CreatedAt": datetime.utcnow().isoformat() + "Z",
            "LastValidated": datetime.utcnow().isoformat() + "Z",
        }

        if account_name:
            item["AccountName"] = account_name

        # Add to DynamoDB
        table.put_item(Item=item)

        account_display = (
            f"{account_name} ({account_id})" if account_name else account_id
        )
        print(f"✅ Successfully added {account_display} as a target account")
        print("   - No cross-account role required (same account)")
        print("   - Status: Active")
        print("   - You can now use the Dashboard and all DRS orchestration features")

        return True

    except Exception as e:
        print(f"❌ Error adding target account: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add current AWS account as a target account"
    )
    parser.add_argument("--account-name", help="Friendly name for the account")
    parser.add_argument(
        "--table-name",
        help="DynamoDB table name (auto-detected if not provided)",
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )

    args = parser.parse_args()

    # Set region
    boto3.setup_default_session(region_name=args.region)

    print("🔍 Adding current AWS account as target account...")

    # Get current account ID
    account_id = get_current_account_id()
    if not account_id:
        print("❌ Failed to get current account ID")
        sys.exit(1)

    print(f"📋 Current Account ID: {account_id}")

    # Get account name
    account_name = args.account_name
    if not account_name:
        detected_name = get_account_name(account_id)
        if detected_name:
            account_name = detected_name
            print(f"📋 Detected Account Name: {account_name}")
        else:
            print("📋 No account name detected (will use Account ID only)")

    # Determine table name
    table_name = args.table_name
    if not table_name:
        # Try to detect from environment or use default pattern
        table_name = "aws-elasticdrs-orchestrator-target-accounts-dev"
        print(f"📋 Using table name: {table_name}")

    # Add the account
    success = add_target_account(table_name, account_id, account_name)

    if success:
        print("\n🎉 Setup complete!")
        print("   1. Refresh your browser")
        print("   2. The Dashboard should now load without errors")
        print("   3. You can start creating Protection Groups and Recovery Plans")
        print("\n💡 Next steps:")
        print("   - Go to Protection Groups to discover your DRS source servers")
        print("   - Create Recovery Plans to orchestrate disaster recovery")
        print("   - Use the Settings gear icon to manage additional target accounts")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
