#!/usr/bin/env python3
"""
User Role Management Script for AWS DRS Orchestration RBAC
Manages Cognito User Pool Groups and user assignments
"""

import argparse
import json
import sys
from typing import Dict, List, Optional

import boto3

# DRS Role definitions matching CloudFormation template
DRS_ROLES = {
    "DRS-Administrator": "Full administrative access to all DRS orchestration functions",
    "DRS-Infrastructure-Admin": "Can manage DRS infrastructure, protection groups, and recovery plans",
    "DRS-Recovery-Plan-Manager": "Can create, modify, and execute recovery plans",
    "DRS-Operator": "Can execute recovery plans and perform DR operations",
    "DRS-Recovery-Plan-Viewer": "Can view recovery plans but not execute them",
    "DRS-Read-Only": "View-only access to DRS configuration and status",
}


class UserRoleManager:
    def __init__(self, user_pool_id: str, region: str = "us-east-1"):
        self.user_pool_id = user_pool_id
        self.region = region
        self.cognito = boto3.client("cognito-idp", region_name=region)

    def list_users(self) -> List[Dict]:
        """List all users in the User Pool"""
        try:
            paginator = self.cognito.get_paginator("list_users")
            users = []

            for page in paginator.paginate(UserPoolId=self.user_pool_id):
                users.extend(page["Users"])

            return users
        except Exception as e:
            print(f"Error listing users: {e}")
            return []

    def get_user_groups(self, username: str) -> List[str]:
        """Get groups for a specific user"""
        try:
            response = self.cognito.admin_list_groups_for_user(
                UserPoolId=self.user_pool_id, Username=username
            )
            return [group["GroupName"] for group in response["Groups"]]
        except Exception as e:
            print(f"Error getting user groups for {username}: {e}")
            return []

    def add_user_to_group(self, username: str, group_name: str) -> bool:
        """Add user to a group"""
        try:
            self.cognito.admin_add_user_to_group(
                UserPoolId=self.user_pool_id,
                Username=username,
                GroupName=group_name,
            )
            print(f"✅ Added user '{username}' to group '{group_name}'")
            return True
        except Exception as e:
            print(f"❌ Error adding user '{username}' to group '{group_name}': {e}")
            return False

    def remove_user_from_group(self, username: str, group_name: str) -> bool:
        """Remove user from a group"""
        try:
            self.cognito.admin_remove_user_from_group(
                UserPoolId=self.user_pool_id,
                Username=username,
                GroupName=group_name,
            )
            print(f"✅ Removed user '{username}' from group '{group_name}'")
            return True
        except Exception as e:
            print(f"❌ Error removing user '{username}' from group '{group_name}': {e}")
            return False

    def create_user(
        self,
        email: str,
        temporary_password: str,
        given_name: str = "",
        family_name: str = "",
        department: str = "",
        job_title: str = "",
    ) -> bool:
        """Create a new user"""
        try:
            user_attributes = [
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
            ]

            if given_name:
                user_attributes.append({"Name": "given_name", "Value": given_name})
            if family_name:
                user_attributes.append({"Name": "family_name", "Value": family_name})
            if department:
                user_attributes.append(
                    {"Name": "custom:department", "Value": department}
                )
            if job_title:
                user_attributes.append({"Name": "custom:job_title", "Value": job_title})

            self.cognito.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=user_attributes,
                TemporaryPassword=temporary_password,
                MessageAction="SUPPRESS",  # Don't send welcome email
            )
            print(f"✅ Created user '{email}' with temporary password")
            return True
        except Exception as e:
            print(f"❌ Error creating user '{email}': {e}")
            return False

    def set_permanent_password(self, username: str, password: str) -> bool:
        """Set permanent password for user"""
        try:
            self.cognito.admin_set_user_password(
                UserPoolId=self.user_pool_id,
                Username=username,
                Password=password,
                Permanent=True,
            )
            print(f"✅ Set permanent password for user '{username}'")
            return True
        except Exception as e:
            print(f"❌ Error setting permanent password for '{username}': {e}")
            return False

    def list_groups(self) -> List[Dict]:
        """List all groups in the User Pool"""
        try:
            response = self.cognito.list_groups(UserPoolId=self.user_pool_id)
            return response["Groups"]
        except Exception as e:
            print(f"Error listing groups: {e}")
            return []

    def display_users_and_roles(self):
        """Display all users and their assigned roles"""
        users = self.list_users()

        if not users:
            print("No users found in User Pool")
            return

        print(f"\n📋 Users in User Pool: {self.user_pool_id}")
        print("=" * 80)

        for user in users:
            username = user["Username"]
            email = next(
                (
                    attr["Value"]
                    for attr in user["Attributes"]
                    if attr["Name"] == "email"
                ),
                "N/A",
            )
            status = user["UserStatus"]

            # Get user's groups
            groups = self.get_user_groups(username)

            print(f"\n👤 User: {email}")
            print(f"   Username: {username}")
            print(f"   Status: {status}")

            if groups:
                print(f"   Roles:")
                for group in groups:
                    description = DRS_ROLES.get(group, "Unknown role")
                    print(f"     • {group}: {description}")
            else:
                print(f"   Roles: None assigned")

    def display_available_roles(self):
        """Display all available DRS roles"""
        print("\n🔐 Available DRS Roles:")
        print("=" * 60)

        for role, description in DRS_ROLES.items():
            print(f"• {role}")
            print(f"  {description}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Manage DRS Orchestration User Roles")
    parser.add_argument("--user-pool-id", required=True, help="Cognito User Pool ID")
    parser.add_argument(
        "--region", default="us-east-1", help="AWS Region (default: us-east-1)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List users command
    list_parser = subparsers.add_parser(
        "list-users", help="List all users and their roles"
    )

    # List roles command
    roles_parser = subparsers.add_parser("list-roles", help="List available roles")

    # Add user to role command
    add_parser = subparsers.add_parser("add-role", help="Add user to role")
    add_parser.add_argument("--username", required=True, help="Username (email)")
    add_parser.add_argument(
        "--role",
        required=True,
        choices=list(DRS_ROLES.keys()),
        help="Role name",
    )

    # Remove user from role command
    remove_parser = subparsers.add_parser("remove-role", help="Remove user from role")
    remove_parser.add_argument("--username", required=True, help="Username (email)")
    remove_parser.add_argument(
        "--role",
        required=True,
        choices=list(DRS_ROLES.keys()),
        help="Role name",
    )

    # Create user command
    create_parser = subparsers.add_parser("create-user", help="Create new user")
    create_parser.add_argument("--email", required=True, help="User email address")
    create_parser.add_argument(
        "--temp-password", required=True, help="Temporary password"
    )
    create_parser.add_argument("--given-name", help="First name")
    create_parser.add_argument("--family-name", help="Last name")
    create_parser.add_argument("--department", help="Department")
    create_parser.add_argument("--job-title", help="Job title")
    create_parser.add_argument(
        "--role", choices=list(DRS_ROLES.keys()), help="Initial role to assign"
    )

    # Set password command
    password_parser = subparsers.add_parser(
        "set-password", help="Set permanent password"
    )
    password_parser.add_argument("--username", required=True, help="Username (email)")
    password_parser.add_argument(
        "--password", required=True, help="New permanent password"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize manager
    manager = UserRoleManager(args.user_pool_id, args.region)

    # Execute command
    if args.command == "list-users":
        manager.display_users_and_roles()

    elif args.command == "list-roles":
        manager.display_available_roles()

    elif args.command == "add-role":
        success = manager.add_user_to_group(args.username, args.role)
        if success:
            print(
                f"\n✅ Successfully assigned role '{args.role}' to user '{args.username}'"
            )
        else:
            sys.exit(1)

    elif args.command == "remove-role":
        success = manager.remove_user_from_group(args.username, args.role)
        if success:
            print(
                f"\n✅ Successfully removed role '{args.role}' from user '{args.username}'"
            )
        else:
            sys.exit(1)

    elif args.command == "create-user":
        success = manager.create_user(
            args.email,
            args.temp_password,
            args.given_name or "",
            args.family_name or "",
            args.department or "",
            args.job_title or "",
        )

        if success and args.role:
            # Assign initial role
            manager.add_user_to_group(args.email, args.role)

        if success:
            print(f"\n✅ User '{args.email}' created successfully")
            print(f"   Temporary password: {args.temp_password}")
            print(f"   User must change password on first login")
        else:
            sys.exit(1)

    elif args.command == "set-password":
        success = manager.set_permanent_password(args.username, args.password)
        if success:
            print(f"\n✅ Password updated for user '{args.username}'")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
