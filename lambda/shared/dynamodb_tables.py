# Copyright Amazon.com and Affiliates. All rights reserved.
# This deliverable is considered Developed Content as defined in the AWS Service Terms.

"""
DynamoDB Table Factory

Provides lazy-initialized DynamoDB table references to eliminate the
repeated global-variable + None-check pattern found across handlers.

Usage:
    from shared.dynamodb_tables import get_table

    # Returns Table or None if env var is unset
    table = get_table("PROTECTION_GROUPS_TABLE")

    # Raises ValueError if env var is unset
    table = get_table("PROTECTION_GROUPS_TABLE", required=True)
"""

import os
from typing import Optional

import boto3

_dynamodb = None
_table_cache: dict = {}


def _get_dynamodb_resource():
    """Get or create the module-level DynamoDB resource."""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb


def get_table(env_var: str, required: bool = False) -> Optional["boto3.resources.factory.dynamodb.Table"]:
    """
    Return a lazily-initialized DynamoDB Table for the given env var.

    The table reference is cached after first creation so subsequent
    calls with the same env_var return the same object (matching the
    existing global-variable pattern this replaces).

    Args:
        env_var: Name of the environment variable holding the table name.
        required: If True, raise ValueError when the env var is unset.

    Returns:
        DynamoDB Table resource, or None if the env var is unset and
        required is False.

    Raises:
        ValueError: If required is True and the env var is not set.
    """
    if env_var in _table_cache:
        return _table_cache[env_var]

    table_name = os.environ.get(env_var)
    if not table_name:
        if required:
            raise ValueError(f"{env_var} environment variable not set")
        _table_cache[env_var] = None
        return None

    dynamodb = _get_dynamodb_resource()
    table = dynamodb.Table(table_name)
    _table_cache[env_var] = table
    return table
